# Control de saldos: vigencia derivada (`validity_status` + `?validity_status=`) y monto de remisión (`remission_amount` > 0, saldo en el 200 de `PUT /remissionBalance`)

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (33/33 checks HTTP, `Tests/tester_balance_vencido.py`; regresión en verde: `tester_balance_vigencia` 30/30, `tester_balance_movement` 31/31, `tester_balance_movement_put` 34/34, `tester_control_saldos_sin_contrato` 50/50, `tester_remission_cancel` 32/32, `tester_delivery_control` 71/71). Sin DDL.**

Fase **F1** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "cuando un contrato se vence se marca como vencido", "selector de control de saldos de contrato vencido", "cambia de monto la remisión, validar el saldo"). Extiende [`control_saldos_vigencia.md`](control_saldos_vigencia.md) (`days_to_end`, `?expiring_days=`) y [`remission_cancel.md`](remission_cancel.md) (`consumed_amount` / `available_amount` por exclusión).

## Qué cambia

- **`validity_status`** (int) y **`validity_label`** en cada control, lista y detalle: `0` VIGENTE (sin `end_date` o a más de 60 días) · `1` POR VENCER (`end_date` a 60 días o menos) · `2` VENCIDO (`end_date` anterior a hoy). **Derivado de `end_date` en cada lectura, nunca almacenado**; `days_to_end` sigue igual. Regla de estados numéricos del repo: el front mapea etiqueta y color.
- **Filtro `?validity_status=`** en `GET /balanceControl`: un valor o lista (`1,2`); fuera de 0..2 → 400. Se combina con los demás filtros (`client_id`, `is_active`, `expiring_days`…).
- **Vencido no bloquea nada**: el control sigue `is_active = 1`, acepta remisiones y movimientos; una VIGENCIA (`type 3`) lo regresa a `0`. El `POST /balanceControl/movement` devuelve `validity_status` junto a `days_to_end`.
- `GET /balanceControl/catalogs` gana `validity_statuses` y `expiring_days` (60, el umbral; el mismo que usará el primer aviso del barrido de la F2).
- **`PUT /remissionBalance`**: `remission_amount` capturado **debe ser mayor a 0** (`0` o negativo → 400, nada se escribe); `null` sigue permitido (remisión sin monto cerrado: no consume). El 200 devuelve `remission_amount` escrito y **`balance_control`** (saldo resultante del control al que pertenece la remisión: contratado, consumido, disponible, días y vigencia) para repintar sin re-GET; `null` si la remisión no está en ningún control.
- **Sin candado contra el contratado** (decisión del grill): el saldo sigue al cambio por exclusión en lectura, hacia arriba o hacia abajo; un monto mayor al disponible deja `available_amount` negativo y Cobranza lo corrige con una INYECCIÓN. El monto que consume saldo sigue siendo `remission_amount` (Control de saldos), no las partidas ni `total_sin_iva`.

## Capas tocadas

```
controller  purchases/balance_control_controller.py  VALIDITY_EXPIRING_DAYS = 60 · _VALIDITY_SQL (cláusulas constantes por valor) · get_balance_controls(validity_statuses=)
midleware   MD_BalanceControl.py                     VALIDITY_STATUSES · validity_status_from_days · _control_to_dict (validity_status/label) · catalogs · listado valida ?validity_status
                                                     POST /movement devuelve validity_status · balance_snapshot(id_control) (nuevo, lo usa remisiones)
midleware   MD_Admin_Collections.py                  update_remission_balance_from_api: remission_amount <= 0 -> 400; 200 con remission_amount + balance_control
routes      rs_Admin_collections.py                  GET /balanceControl lee ?validity_status (swagger)
```

Sin cambios en forms ni `api.model`: `remission_amount` ya era `FloatField` opcional; la validación de signo va en el midleware para dar el mensaje correcto (WTForms trata `0` como vacío).

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Lecturas de controles: `administracion` / `purchases`; `PUT /remissionBalance`: `administracion` / `purchases` (sin cambio).
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400 de midleware, objeto por campo en 400 de form. 401: `{"error": "..."}` sin envelope.

### `GET /balanceControl` · `GET /balanceControl/<id>` — cambios

Cada control (lista y detalle) gana:

```json
{ "id_control": 6, "end_date": "2026-11-15", "days_to_end": 24, "validity_status": 1, "validity_label": "POR VENCER",
  "contracted_amount": 1500000.0, "consumed_amount": 812000.0, "available_amount": 688000.0, "is_active": 1, "...": "..." }
```

| `validity_status` | `validity_label` | Cuándo |
|---|---|---|
| `0` | `VIGENTE` | sin `end_date`, o `days_to_end > 60` |
| `1` | `POR VENCER` | `0 ≤ days_to_end ≤ 60` |
| `2` | `VENCIDO` | `days_to_end < 0` |

Query nuevo en la lista: **`?validity_status=2`** (solo vencidos), **`?validity_status=1,2`** (por vencer y vencidos), `?validity_status=0,1,2` (= sin filtro). Combina con `client_id`, `contract_id`, `has_contract`, `format_id`, `is_active`/`all`, `expiring_days`.

| Código | Cuándo | Ejemplo |
|---|---|---|
| **200** | lista filtrada | `data: [{...}]` |
| **400** | valor fuera de 0..2 o no numérico | `msg: "validity_status inválido"` · `error: ["validity_status debe ser 0 (VIGENTE), 1 (POR VENCER) o 2 (VENCIDO), uno o lista; recibido '5'"]` |

`GET /balanceControl/catalogs` → `data.validity_statuses: [{"code": 0, "label": "VIGENTE"}, {"code": 1, "label": "POR VENCER"}, {"code": 2, "label": "VENCIDO"}]` y `data.expiring_days: 60`.

`POST /balanceControl/movement` → el 201 trae `validity_status` junto a `days_to_end` (tras una VIGENCIA sobre un vencido: `0`).

### `PUT /remissionBalance` — cambios

Body igual que antes (`{"metadata": {"id": 71, "remission_amount": 250000, ...}}`).

| Código | Cuándo | Respuesta |
|---|---|---|
| **200** | guardado; remisión en un control | `data: {"id_remission": 71, "remission_amount": 250000.0, "balance_control": {"id_control": 6, "is_active": true, "contracted_amount": 1500000.0, "consumed_amount": 812000.0, "available_amount": 688000.0, "days_to_end": 24, "validity_status": 1}}` |
| **200** | guardado; remisión sin control | `data: {"id_remission": 71, "remission_amount": 250000.0, "balance_control": null}` |
| **200** | `remission_amount: null` | se vacía el monto; `balance_control.consumed_amount` ya no lo suma |
| **400** | `remission_amount` `0` o negativo | `msg: "Monto de remisión inválido"` · `error: ["remission_amount debe ser mayor a 0 (recibido: 0)"]`; nada se escribe |
| **400** | remisión cancelada / inexistente / `custom_fields` inválidos | igual que antes |

`balance_control.consumed_amount` ya incluye el monto recién escrito (se lee después del `UPDATE`). Si el `PUT` no trae `remission_amount`, no se valida el monto y `balance_control` igual viene (saldo vigente del control).

### Gotchas

- `validity_status` se calcula con la fecha del servidor de BD (`CURDATE()`), como `days_to_end`; no con la del navegador.
- `?expiring_days=30` sigue mezclando por vencer y vencidos; para el selector "vencidos" usar `validity_status=2`.
- Un control **cancelado** (`is_active = 0`) también trae `validity_status`; el front decide si lo muestra.
- `available_amount` **puede ser negativo** a propósito (sin candado); es señal para inyectar saldo, no un error del API.

## Al modificar

- **Cambiar el umbral de "por vencer"**: solo `VALIDITY_EXPIRING_DAYS` en el controller (SQL y Python lo leen de ahí; el catálogo lo expone). El barrido de la F2 debe usar la misma constante para el primer aviso.
- **Un cuarto estado** (p. ej. "sin fecha" aparte de vigente): agregar la cláusula a `_VALIDITY_SQL`, el valor a `VALIDITY_STATUSES` y la rama a `validity_status_from_days`; los tres deben coincidir.
- **Poner un candado contra el contratado** (si Cobranza cambia de opinión): en `update_remission_balance_from_api`, después de validar el signo, leer `balance_snapshot(result_ra[20])` y comparar `consumed - monto_anterior + monto_nuevo` contra `contracted_amount`; hoy está descartado a propósito (grill 2026-10-22).
- `balance_snapshot` es la lectura ligera del saldo para cualquier endpoint de remisiones que quiera devolverlo; no duplicar la suma en SQL fuera de `_SELECT_CONTROL`.
- Docstrings de este módulo **sin llaves `{...}`**: el editor del usuario convierte un docstring con llaves en una f-string inválida (`""f"..."`) y rompe el import; por eso tres docstrings se reescribieron con paréntesis.
