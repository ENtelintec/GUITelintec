# Control de entregas: vencimiento de la OCD (`due_date`, `days_to_due`, `validity_status`), fechas por partida y conteos de partidas en la lista

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (26/26 checks HTTP, `Tests/tester_delivery_vencimiento.py`; regresión en verde: `tester_delivery_control` 71/71, `tester_ocd_rules` 40/40, `tester_remission_pdf_ocd` 17/17, `tester_balance_vencido` 33/33, `tester_remission_cancel` 32/32). Sin DDL: todo se deriva en lectura de `quotations.metadata.due_date` y `quotation_items.extra_info.delivery_date`.**

Fase **F5** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "la fecha de vencimiento es el tiempo de entrega de la OCD", "agregar un indicador de cantidades faltantes y las ya entregadas; a lado del avance un icono que liste los entregados y faltantes"). Extiende [`control_entregas.md`](control_entregas.md) (F2 del plan anterior) y usa las llaves de [`ocd_reglas_po_vencimiento.md`](ocd_reglas_po_vencimiento.md) (F4). Mismo patrón de vigencia que [`control_saldos_vencido_y_monto.md`](control_saldos_vencido_y_monto.md).

## Qué cambia

- **Cabecera** (lista y detalle): `due_date` (de la cotización OCD, `null` si no tiene), `days_to_due` (negativo = vencido, `null` sin fecha) y **`validity_status` derivado** `0` VIGENTE (sin fecha o a más de 60 días) · `1` POR VENCER (≤ 60 días) · `2` VENCIDO, con `validity_label`. Umbral = `VALIDITY_EXPIRING_DAYS` de saldos (60). **Nunca se almacena y no bloquea nada**: un control vencido sigue aceptando remisiones; cambiar `due_date` con `PUT /quotation/ocd` lo regresa a vigente.
- **Filtro `?validity_status=`** en `GET /deliveryControl` (un valor o lista `1,2`; fuera de 0..2 → 400). Se aplica en Python porque `due_date` vive en el JSON de la cotización; combina con `quotation_id`, `client_id`, `status`, `all`.
- **Por partida** (detalle): `delivery_date` (`YYYY-MM-DD` | `null`), `days_to_delivery` y **`overdue`** = pendiente > 0 **y** fecha pasada (una partida entregada completa nunca está atrasada aunque su fecha haya pasado).
- **Conteos**: `totals` del **detalle** gana `items_pending` e `items_overdue` (ya traía `items_count` / `items_complete`); `totals` de la **lista** gana `items_count`, `items_complete`, `items_pending`, calculados en la misma query agregada (sin consulta extra). El icono junto al avance muestra los conteos y carga el detalle al hacer clic para listar las partidas; no hay endpoint nuevo.
- `GET /deliveryControl/catalogs` gana `validity_statuses` y `expiring_days`.
- `days_to_due` / `days_to_delivery` se calculan con la fecha del servidor del API en `America/Mexico_City` (`_now()`), no con la del navegador ni con `CURDATE()` de la BD (saldos usa la BD; la diferencia solo aparece en el cambio de día).

## Capas tocadas

```
controller  purchases/delivery_control_controller.py   CONTROL_COLUMNS + quotation_due_date (append-only) · ORDER_ITEM_COLUMNS + delivery_date vía _ORDER_ITEM_EXPRS
                                                        get_delivery_totals_by_quotations: + items_count, items_complete (índices 6, 7)
midleware   MD_DeliveryControl.py                       _days_to · _control_to_dict (due_date, days_to_due, validity_status/label) · _compute_items (delivery_date, days_to_delivery, overdue; items_pending/items_overdue)
                                                        get_delivery_controls_from_api (?validity_status, conteos en totals) · catalogs
routes      rs_Admin_collections.py                     GET /deliveryControl lee ?validity_status (swagger)
```

Reusa `VALIDITY_STATUSES` y `validity_status_from_days` de `MD_BalanceControl` y `VALIDITY_EXPIRING_DAYS` del controller de saldos: un solo umbral para los dos controles y para el barrido de avisos (F2).

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Lecturas `administracion` / `purchases` (sin cambio).
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400 de midleware. 401: `{"error": "..."}` sin envelope.

### `GET /deliveryControl` (lista) — cambios

Query nuevo **`validity_status`** (`2`, `1,2`, `0,1,2`). 400 `msg: "validity_status inválido"` · `error: ["validity_status debe ser 0 (VIGENTE), 1 (POR VENCER) o 2 (VENCIDO), uno o lista; recibido '7'"]`.

Cada fila gana:

```json
{ "id_control": 3, "due_date": "2026-12-15", "days_to_due": 24, "validity_status": 1, "validity_label": "POR VENCER",
  "totals": { "ordered_qty": 20005, "delivered_qty": 15000, "pending_qty": 5005, "progress_pct": 74.85, "last_delivery_date": "2026-11-20",
              "items_count": 3, "items_complete": 1, "items_pending": 2, "...": "..." } }
```

| `validity_status` | `validity_label` | Cuándo |
|---|---|---|
| `0` | `VIGENTE` | sin `due_date`, o `days_to_due > 60` |
| `1` | `POR VENCER` | `0 ≤ days_to_due ≤ 60` |
| `2` | `VENCIDO` | `days_to_due < 0` |

### `GET /deliveryControl/<id>` (detalle) — cambios

Cabecera con las mismas llaves de vencimiento. Por partida:

```json
"items": [{"id": 900, "partida": 1, "ordered_qty": 10, "delivered_qty": 10, "pending_qty": 0, "complete": true,
           "delivery_date": "2026-11-01", "days_to_delivery": -3, "overdue": false},
          {"id": 901, "partida": 2, "ordered_qty": 5, "delivered_qty": 0, "pending_qty": 5, "complete": false,
           "delivery_date": "2026-11-01", "days_to_delivery": -3, "overdue": true},
          {"id": 902, "partida": 3, "ordered_qty": 2, "delivered_qty": 0, "pending_qty": 2, "complete": false,
           "delivery_date": null, "days_to_delivery": null, "overdue": false}],
"totals": {"items_count": 3, "items_complete": 1, "items_pending": 2, "items_overdue": 1, "...": "..."}
```

Para el popover del icono: ordenar `items` con `overdue` primero, luego `pending_qty > 0`, luego completas; `pending_qty` y `delivered_qty` ya vienen por partida.

### `GET /deliveryControl/catalogs` — cambio

`data.validity_statuses: [{"code": 0, "label": "VIGENTE"}, {"code": 1, "label": "POR VENCER"}, {"code": 2, "label": "VENCIDO"}]` y `data.expiring_days: 60`.

### Gotchas

- `due_date` se **edita en la cotización** (`PUT /quotation/ocd`, [`ocd_reglas_po_vencimiento.md`](ocd_reglas_po_vencimiento.md)), no en el control: el control solo lo refleja. Lo mismo para `delivery_date` de cada partida (`PUT /quotation` / `PUT /tender/items`).
- `items_complete` de la lista y del detalle usan la misma tolerancia (`1e-6`); un control con `status` puesto a mano en `1` COMPLETO puede traer `items_pending > 0` hasta el siguiente recálculo (regla ya documentada en F2).
- Un control **cancelado** también trae `validity_status`; el front decide si lo pinta.
- Sin `due_date` el control es **vigente** (`0`) y entra en `?validity_status=0`.

## Al modificar

- **Cambiar el umbral**: solo `VALIDITY_EXPIRING_DAYS` en `balance_control_controller.py` (lo leen saldos, entregas, catálogos y el barrido).
- **Filtro en SQL en vez de Python** (si la lista crece): `due_date` tendría que salir de `metadata` a columna o usar `STR_TO_DATE(q.metadata->>'$.due_date', '%%Y-%%m-%%d')` (escapar `%` porque la query lleva parámetros).
- **Columnas nuevas de partida**: agregarlas a `ORDER_ITEM_COLUMNS` (append-only) y, si no son columna física, su expresión a `_ORDER_ITEM_EXPRS`; recordar `_RESERVED_KEYS` para las columnas dinámicas.
- **Aviso de OCD por vencer** (F2): leer `days_to_due` de `_control_to_dict` sobre los controles abiertos (`status 0`) y marcar en `delivery_controls.extra_info.notified`; no recalcular aquí.
