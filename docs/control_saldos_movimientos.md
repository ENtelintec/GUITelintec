# Control de saldos: inyección y ajuste de saldo (`POST /balanceControl/movement`)

Fecha: 2026-09-17 · **Estado: hecho y verificado contra dev (31/31 checks HTTP, `Tests/tester_balance_movement.py`). Sin DDL: usa `balance_control_movements` de [`control_saldos.sql`](../scripts_db_handle/control_saldos.sql).**

Cierra el pendiente "endpoint de inyección/ajuste de saldo" de [`control_saldos_cabecera.md`](control_saldos_cabecera.md). Ahí quedó decidido que `contracted_amount` solo se fija en el `POST` del control (movimiento `INICIAL`), que el `PUT` de cabecera lo rechaza y que la tabla de movimientos es **inmutable** (solo `INSERT`). Este endpoint es la única forma de mover el saldo después.

> El pendiente esperaba la maqueta F2 del front para tres decisiones (montos negativos, adjunto, quién puede). Se tomaron **defaults** y quedan escritos abajo; si la maqueta decide distinto, se ajustan aquí (ninguno requiere DDL).

## Reglas

| Tema | Decisión |
|---|---|
| Tipos | `1` **INYECCION**: `amount > 0`. `2` **AJUSTE**: `amount != 0`, negativo resta. El `0` INICIAL no se acepta (solo lo escribe el `POST /balanceControl`). |
| Saldo resultante | `previous_balance + amount`; **nunca `< 0`** → 400. Llegar exactamente a `0` sí es válido. |
| Control cancelado | 400 (`is_active = 0`). Inexistente → 404. |
| Bloqueo optimista | Dos capas. (a) Opcional del front: `expected_balance` = saldo que tenía en pantalla; si ya no coincide → **409** con `data.current_balance` para repintar. (b) Siempre en BD: el `UPDATE` de la cabecera lleva `AND contracted_amount = <leído> AND is_active = 1`; 0 filas → **409** (otro movimiento ganó la carrera o se canceló en medio). En ambos casos **no se inserta nada**: recargar y reintentar. |
| Orden de escritura | 1) `UPDATE` optimista del monto + `history`; 2) `INSERT` del movimiento. Si el 2 falla, se revierte el monto con otro `UPDATE` optimista (best-effort, a log) y responde 400 "el saldo no cambió". Nunca `UPDATE`/`DELETE` sobre movimientos. |
| Usuario | `user_id`/`user_name` del token (snapshot). |
| Adjunto | **No por ahora**. `reason` (motivo) y `document` (folio de pedido/adenda) opcionales; `extra_info` del movimiento queda libre para adjuntos futuros sin DDL. |
| Permisos | Solo `administracion` (misma regla que todas las escrituras de saldos). |
| Precisión | Todo en `Decimal` a 2 decimales (`contracted_amount` es `DECIMAL(15,2)`); la respuesta devuelve floats. |

## Las capas tocadas

```
controller  purchases/balance_control_controller.py  update_balance_control_amount_optimistic  (nuevo: UPDATE con WHERE contracted_amount = %s AND is_active = 1, type_sql 3)
midleware   MD_BalanceControl.py                     create_balance_movement_from_api + _money   (nuevo)
models      api_balance_control_models.py            balance_control_movement_model + BalanceControlMovementForm (nuevos)
routes      rs_Admin_collections.py                  POST /balanceControl/movement (_BC_WRITE)
```

`amount` va **sin `InputRequired`** en el form: WTForms trata `0` como vacío y respondería "amount requerido" en lugar del mensaje de AJUSTE; el midleware valida `None`/`0` con el texto correcto.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permiso `administracion`.
- **Base**: `/GUI/api/v1/admin/collections`.
- **Respuesta**: siempre `{data, msg, error}`; `error` es `null` en éxito, lista de strings en 400 de validación.

### `POST /balanceControl/movement`

```json
{
  "id_control": 6,
  "type": 1,
  "amount": 250000.00,
  "movement_date": "2026-09-15",
  "reason": "Adenda 2 al contrato",
  "document": "4500123456",
  "expected_balance": 1250000.00
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id_control` | int | sí | control **activo** |
| `type` | int | sí | `1` INYECCION · `2` AJUSTE |
| `amount` | number | sí | `> 0` en 1; `!= 0` en 2 (negativo resta) |
| `movement_date` | `YYYY-MM-DD` | no | default hoy |
| `reason` | string | no | motivo |
| `document` | string | no | folio de pedido / adenda |
| `expected_balance` | number | no | saldo en pantalla; recomendado mandarlo siempre |

| Código | Cuándo | `data` / ejemplo |
|---|---|---|
| **201** | registrado | `{"id_control": 6, "id_movement": 12, "type": 1, "type_label": "INYECCION", "movement_date": "2026-09-15", "amount": 250000.0, "previous_balance": 1250000.0, "resulting_balance": 1500000.0, "contracted_amount": 1500000.0}` · `msg`: `"INYECCION registrada en el control (ID 6): saldo 1250000.00 -> 1500000.00 (movimiento ID 12)"` |
| **400** | validación | `data: null`, `error: ["una INYECCION debe tener amount > 0"]` / `["el saldo resultante no puede ser negativo (actual 1200.00, movimiento -1500.00)"]` / `["movement_date: se esperaba una fecha YYYY-MM-DD"]` / `{"type": ["type debe ser 1 (INYECCION) o 2 (AJUSTE)"]}` (este último viene del form, `error` es objeto) |
| **400** | control cancelado | `msg: "El control está cancelado (ID 6); no admite movimientos"` |
| **404** | control inexistente | `msg: "No existe el control (ID 999)"` |
| **409** | `expected_balance` desfasado | `data: {"id_control": 6, "current_balance": 1300000.0}` · `msg: "El saldo del control cambió (actual 1300000.00); recarga y vuelve a intentar"` |
| **409** | carrera perdida en BD | `data: {"id_control": 6}` · `msg: "...cambió mientras se registraba el movimiento..."` |
| **401** | sin permiso `administracion` | `{"error": "..."}` (sin envelope) |

Tras el 201 no hace falta re-`GET`: `data.contracted_amount` es el saldo nuevo de la cabecera. `GET /balanceControl/<id>` sigue trayendo `movements` (más reciente primero, con `type_label`, `user_name`, `previous_balance`/`resulting_balance` encadenados) y una entrada nueva en `history` (`action: "Movimiento de saldo (INYECCION)"`).

### Gotchas

- Mandar `expected_balance` evita el caso feo: con dos capturistas sobre el mismo control, el segundo recibe 409 en vez de aplicar su monto sobre un saldo que ya no veía.
- `amount` con más de 2 decimales se redondea (`Decimal.quantize`), igual que la columna.
- Los montos en `msg` van con 2 decimales como texto (`1250000.00`); los de `data` son números.

## Al modificar

- **Adjunto por movimiento**: guardar en `extra_info` del movimiento (ya se acepta un dict `extra_info` en el body, sin validar) o un endpoint multipart aparte; no hace falta DDL.
- **Tipo nuevo de movimiento**: `MOVEMENT_TYPES` en el midleware, `AnyOf` del form, la validación de signo en `create_balance_movement_from_api` y el catálogo (`/balanceControl/catalogs` ya lo expone desde `MOVEMENT_TYPES`).
- No agregar `UPDATE`/`DELETE` sobre `balance_control_movements`: una corrección es un `AJUSTE` nuevo.
