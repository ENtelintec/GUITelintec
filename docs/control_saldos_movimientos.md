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

## Notas posteriores

- **2026-09-28** — El ledger gana la vigencia: tipo `3 = VIGENCIA`, columnas `previous_end_date`/`new_end_date`, `new_end_date` opcional en 1/2, `changed` por fila, `PUT /balanceControl` deja de escribir `end_date`, `days_to_end` + `?expiring_days=`. Ver [`control_saldos_vigencia.md`](control_saldos_vigencia.md). El `amount` pasa a ser opcional en el `api.model` (obligatorio en 1/2 lo valida el midleware).

- **2026-10-16** — **`PUT /balanceControl/movement`: corrección de captura (fecha de autorización y motivo).** Verificado contra dev (34/34 checks, `Tests/tester_balance_movement_put.py`; `tester_balance_movement.py` sigue 31/31). Sin DDL.

  Cobranza necesitaba corregir la **fecha de autorización** (`movement_date`) y el **motivo** (`reason`) de un movimiento ya capturado sin registrar un AJUSTE. La regla "no `UPDATE` sobre `balance_control_movements`" queda con **una sola excepción acotada**: el `PUT` escribe únicamente esas dos columnas. Todo lo que afecta el saldo o la vigencia sigue inmutable: `amount`, `type`, `previous_balance`/`resulting_balance`, `previous_end_date`/`new_end_date`, `document`, `user_*`, `timestamp` y `id_control`; si alguna de esas llaves viene en el body **se ignora en silencio** (no responde 400) y la cabecera (`contracted_amount`, `end_date`) no se toca. Un error de monto o de fecha de fin se corrige, como antes, con otro movimiento.

  Capas: `balance_control_controller.get_balance_control_movement_by_id` + `update_balance_control_movement_fields` (UPDATE solo de `movement_date, reason`) · `MD_BalanceControl.update_balance_movement_from_api(data, raw_payload, data_token)` (recibe el JSON crudo para distinguir "llave ausente" de "llave vacía") · `api_balance_control_models.balance_control_movement_put_model` + `BalanceControlMovementPutForm` · método `put` en la clase `BalanceControlMovement` de `rs_Admin_collections.py` (permiso `_BC_WRITE`).

  Historial: cada corrección efectiva agrega una entrada al `history` de la cabecera, misma forma que las de movimiento: `{"user", "action": "Corrección de movimiento (INYECCION ID 12)", "date", "comment", "id_movement", "changes": [{"field", "before", "after"}]}` — `changes` lleva **solo lo que realmente cambió** (la llave se llama `changes`, igual que en las entradas del POST, para que el front la pinte con el mismo código). Orden de escritura: 1) `history` de la cabecera, 2) `UPDATE` del movimiento; si el 2 falla se quita la entrada (best-effort, a log) y responde 400 "nada cambió". Si los valores enviados son iguales a los guardados, responde **200 sin escribir ni agregar historial** (`msg` "Sin cambios…").

  ### Contrato mínimo para el front

  - **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permiso `administracion` (el mismo del POST).
  - **Base**: `/GUI/api/v1/admin/collections`. Respuesta siempre `{data, msg, error}`; `error` es `null` en éxito, lista de strings en 400 de midleware, objeto por campo en 400 de form. El 401 viene sin envelope: `{"error": "..."}`.

  #### `PUT /balanceControl/movement`

  ```json
  { "id_movement": 12, "movement_date": "2026-09-16", "reason": "Adenda 2 al contrato (corregido)" }
  ```

  | Campo | Tipo | Obligatorio | Notas |
  |---|---|---|---|
  | `id_movement` | int | sí | el `id_movement` que trae `movements[]` del `GET /balanceControl/<id>`; su control debe estar **activo** |
  | `movement_date` | `YYYY-MM-DD` | al menos uno de los dos | fecha de autorización corregida; **no puede ir vacía** (omítela para no cambiarla) |
  | `reason` | string \| null | al menos uno de los dos | motivo corregido (se hace `strip`); `""` o `null` lo **vacía** (queda `null`) |

  Cualquier otra llave (`amount`, `type`, `new_end_date`, `document`, `id_control`, `expected_balance`, …) **se ignora**; no hay 400 por mandarla, pero no cambia nada.

  | Código | Cuándo | Ejemplo |
  |---|---|---|
  | **200** | corregido | `data`: `{"id_movement": 12, "id_control": 6, "control_id": 6, "type": 1, "type_label": "INYECCION", "movement_date": "2026-09-16", "amount": 250000.0, "previous_balance": 1250000.0, "resulting_balance": 1500000.0, "user_id": 9999, "user_name": "QA Saldos", "reason": "Adenda 2 al contrato (corregido)", "document": "4500123456", "timestamp": "2026-09-17 10:21:03", "extra_info": {}, "previous_end_date": null, "new_end_date": null, "changed": ["amount"]}` · `msg`: `"Movimiento corregido (ID 12, control ID 6): movement_date 2026-09-15 -> 2026-09-16; reason Adenda 2 al contrato -> Adenda 2 al contrato (corregido)"` |
  | **200** | sin cambios (mismos valores) | mismo `data` (el movimiento tal cual está) · `msg`: `"Sin cambios en el movimiento (ID 12); nada que guardar"` · **no** se agrega historial |
  | **400** | ninguno de los dos campos | `data: null` · `msg: "Nada que corregir: manda movement_date y/o reason"` · `error: ["se requiere al menos uno de movement_date / reason"]` |
  | **400** | fecha inválida | `msg: "Corrección inválida"` · `error: ["movement_date: se esperaba una fecha YYYY-MM-DD"]` · con `"movement_date": ""` → `["movement_date no puede quedar vacía (omítela para no cambiarla)"]` |
  | **400** | sin `id_movement` | `msg: "Estructura de datos inválida"` · `error: {"id_movement": ["id_movement requerido"]}` (form) |
  | **400** | control cancelado | `msg: "El control está cancelado (ID 6); no admite correcciones de movimientos"` · `error: "Control cancelado"` |
  | **404** | movimiento inexistente | `msg: "No existe el movimiento (ID 999)"` · `error: "Movimiento no encontrado"` |
  | **401** | sin permiso `administracion` | `{"error": "..."}` |

  `data` del 200 tiene **exactamente el shape de una fila de `movements[]`** del detalle (`type_label`, `changed`, `user_name`, `previous_end_date`/`new_end_date`, …) más `control_id`: basta reemplazar esa fila en la tabla sin re-`GET`. Si la pantalla también muestra `history`, hay que releer el detalle (o anexar localmente una entrada con `changes`) solo cuando el `msg` no empiece con `"Sin cambios"`.

  #### Gotchas

  - `movement_date` es la fecha en que el cliente **autorizó** el cambio (la del lápiz); `timestamp` (cuándo se capturó) no se toca ni se puede editar.
  - Mandar `"reason": ""` **borra** el motivo; para no tocarlo, no mandar la llave.
  - El PUT no lleva `expected_balance` ni 409: no mueve saldo, así que no compite con otro movimiento.
  - El movimiento `INICIAL` (type 0) también se puede corregir (fecha/motivo); el saldo inicial no.
