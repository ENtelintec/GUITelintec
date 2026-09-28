# Control de Entregas por OCD: `POST /deliveryControl`, partidas pedido / entregado / pendiente y sobre-entrega

Fecha: 2026-09-28 · **Estado: hecho y verificado contra dev (71/71 checks HTTP, `Tests/tester_delivery_control.py`). DDL [`control_entregas_ocd_membresia.sql`](../scripts_db_handle/control_entregas_ocd_membresia.sql) corrido en dev por el usuario; test y prod pendientes.**

Fase **F2** del plan [`planes/control_entregas_ocd_plan.md`](planes/control_entregas_ocd_plan.md). Se apoya en la F1 ([`quotation_ocd.md`](quotation_ocd.md): la cotización marcada `document_type: "ocd"`) y en las tablas de [`control_entregas_ocd.sql`](../scripts_db_handle/control_entregas_ocd.sql) (F0, corrido en dev el 2026-09-28 con FKs).

> **Orden obligatorio: DDL antes que el código.** `get_remission_by_id` ya selecciona `ar.delivery_control_id`: con este código y sin la columna, **todos** los endpoints de remisiones responden 400 `Unknown column`. Correr `control_entregas_ocd_membresia.sql` en dev → test → prod antes de desplegar.

## Por qué una columna (ajuste al plan)

El plan decía "membresía derivada de `activity_reports.quotation_id`". Al implementar se comprobó (FK en BD) que **`activity_reports.quotation_id` apunta a `quotations_activities`** (la "actividad de cotización" de admin/collections, `POST /activity/quotation`), **no a `quotations`** (donde vive la marca OCD). Los **items** de remisión sí apuntan a las partidas de presales (`quotation_activity_items.item_c_id → quotation_items.id`), así que la derivación *por partida* del plan se sostiene; la membresía de cabecera no. Solución: columna explícita **`activity_reports.delivery_control_id`**, igual que `balance_control_id` en saldos, con auto-enlace y un endpoint `add/remove`. Descartado guardarla en `extra_info` (JSON sin índice, y saldos ya sentó el precedente de columna).

Consecuencia que hay que tener clara: **lo entregado se deriva de los items, la membresía de la columna**. Una remisión retirada del control que conserve items apuntando a las partidas sigue contando como entregado (los bienes se entregaron contra esa OCD); solo desaparece de la lista `remissions` del detalle y de los valores por remisión. La regla de sobre-entrega también es por items, tenga o no membresía la remisión.

## Reglas

| Tema | Regla |
|---|---|
| Alta | `POST /deliveryControl {quotation_id}`: la cotización debe existir (404) y ser OCD (400 "conviértela primero"); **un control no cancelado por cotización** (409). `title` default = `quotation_code`; `client_po_number` y `currency` default = los de la cotización; `client_id` siempre de la cotización. |
| Auto-adopción | Al crear: remisiones del mismo cliente, libres (sin control o en uno cancelado) y con ≥ 1 item apuntando a una partida de la cotización, más las de `remissions[]` (validadas todas antes de escribir: existir, mismo cliente, no estar en otro control activo). |
| Auto-enlace de remisiones nuevas | `POST /remission`: `metadata.delivery_control_id` explícito (validado: existe, activo, mismo cliente → si no, 400) o, si no viene, el **único** control activo al que apuntan sus items (`item_contract_id`); items de dos OCD distintas → 400 pidiendo el explícito. `POST /remissionControlTable` (sin items): solo el explícito. |
| Derivados | Por partida: `ordered_qty` (`quotation_items.quantity`), `delivered_qty` = Σ `quotation_activity_items.quantity` con ese `item_c_id` y remisión `status <> 3`, `pending_qty`, montos (`price_unit` de la partida para lo pedido; `line_total` real de la remisión para lo entregado), `remissions_count`, `last_delivery_date`, `complete`. Totales y `progress_pct` (por monto; por cantidad si el monto pedido es 0). Nunca se almacenan. |
| Sobre-entrega | `POST`/`PUT /remission`: si una partida cuya cotización tiene control activo quedaría con entregado > pedido → **400** listando partidas; nada se escribe. En el PUT se suman los items del payload (menos `is_erased`) + los existentes que el payload no menciona, excluyendo la propia remisión de lo ya entregado. Sin control activo no hay regla. |
| Fuera de la orden | Items sin `item_c_id` (o de otra cotización) se aceptan; el detalle los lista en `off_order_items` con `off_order_amount`. |
| `item_c_id` en el PUT | `PUT /remission` ahora **conserva** el enlace a la partida cuando el item viene sin `item_contract_id` (antes lo ponía en NULL). El `POST` convierte `0` → NULL (antes reventaba la FK). |
| Candado de cliente | `PUT /remission` / `PUT /remissionControlTable` que cambien `client_id` de una remisión en un control **activo** → 400 (retirarla primero con `/remissions`). |
| Status | `0` ABIERTO · `1` COMPLETO · `2` CANCELADO. El back recalcula 0↔1 tras cada `POST`/`PUT /remission` y `add`/`remove` (`refresh_delivery_control_status`); el `PUT` de cabecera admite fijar 0/1 a mano (queda hasta el próximo recálculo); 2 solo por `/cancel`. |
| Cancel | Suave (`status = 2`), no toca remisiones (conservan `delivery_control_id`; el GET de remisiones expone `delivery_control_active: false`); levanta las reglas de sobre-entrega y de change order; permite crear un control nuevo, que re-adopta las remisiones del cancelado. |
| Change orders en la cotización | Con control activo: `PUT /quotation` puede agregar partidas y subir cantidades; **quitar una partida con entregas o bajarla por debajo de lo entregado → 400**; `DELETE /quotation` → 400; `PUT /quotation/ocd` con `document_type: quotation` → 400. |
| Columnas dinámicas | `custom_fields` mismo contrato que saldos (`{key,label,value_type,comment}`, tipos `text|number|date|boolean`, keys reservadas = columnas del control y del detalle). Los **valores** van por remisión en `activity_reports.extra_info.delivery_fields` vía `PUT /deliveryControl/values`; quitar una columna barre sus valores (`JSON_REMOVE`). |
| Permisos | Lecturas `administracion` + `purchases`; escrituras solo `administracion`. `almacen` y `operaciones` no (pendiente `operaciones`). |

## Capas tocadas

```
controller  purchases/delivery_control_controller.py   (nuevo) cabecera + derivados + membresía + delivery_fields
controller  presales/remisions_controller.py           insert_remission(delivery_control_id) · get_remission_by_id: índices 22/23 + filtro delivery_control_id
midleware   MD_DeliveryControl.py                      (nuevo) *_from_api + check_over_delivery / resolve_delivery_control_for_remission / delivery_control_lock_error / refresh_delivery_control_status / quotation_change_order_errors
midleware   MD_Admin_Collections.py                    POST/PUT /remission y /remissionControlTable: sobre-entrega, auto-enlace, candado, refresh; GET expone delivery_control_id/active
midleware   Functions_midleware_admin.py               PUT /quotation (change orders) · DELETE /quotation y PUT /quotation/ocd (guard con control activo)
models      api_delivery_control_models.py             (nuevo) forms + api.model; reusa BalanceControlCustomFieldForm
models      api_purchases_models.py                    metadata.delivery_control_id en los forms de remisión + api.model
routes      rs_Admin_collections.py                    /deliveryControl (GET/POST/PUT), /catalogs, /fields, /values, /remissions, /cancel, /<id>; GET /remission-<id> lee ?delivery_control_id
DDL         control_entregas_ocd_membresia.sql         activity_reports.delivery_control_id (+ FK opcional)
```

`get_remission_by_id` es **append-only**: índices 22 (`delivery_control_id`) y 23 (`status` del control); los call sites que indexan por posición no cambian.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `).
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings (midleware) u objeto por campo (form) en 400. 401: `{"error": "..."}`.
- Permisos: GETs `administracion`/`purchases`; POST/PUT `administracion`.

### `POST /deliveryControl`

```json
{ "quotation_id": 51, "title": "OCD fibra óptica Guerrero", "client_po_number": "3716578048", "currency": "MXN",
  "remissions": [71], "custom_fields": [{"key": "guia_embarque", "label": "Guía", "value_type": "text", "comment": ""}] }
```

| Código | Cuándo | `data` |
|---|---|---|
| **201** | creado | `{"id_control": 3, "adopted_remissions": [71, 72], "status": 0}` (`error` puede traer lista de parciales de la auto-adopción) |
| **400** | cotización no OCD · `remissions[]` inválidas (lista `["remisión 9: cliente distinto (12 ≠ 40)", …]`) · `custom_fields` inválidas | `null` |
| **404** | cotización inexistente | `null` |
| **409** | ya hay control activo | `{"id_control": 3}` |

### `GET /deliveryControl` (lista) · `GET /deliveryControl/<id>` (detalle)

Lista: query `quotation_id`, `client_id`, `status` (0/1/2), `all=1` (sin `status` ni `all`: solo no cancelados). Cada fila = cabecera (`id_control`, `quotation_id`, `quotation_code`, `client_id`, `client_name`, `title`, `client_po_number`, `currency`, `status`, `status_label`, `is_active`, `custom_fields`, `remissions_count`, `history`) + `totals: {ordered_qty, ordered_amount, delivered_qty, delivered_amount, pending_qty, pending_amount, progress_pct, last_delivery_date}`.

Detalle: lo anterior más

```json
"items": [{"id": 900, "partida": 1, "section_index": 0, "udm": "m", "description": "Fibra óptica…", "n_part": null, "brand": null,
           "ordered_qty": 20000, "delivered_qty": 15000, "pending_qty": 5000, "unit_price": 12.5,
           "ordered_amount": 250000, "delivered_amount": 187500, "pending_amount": 62500,
           "remissions_count": 1, "last_delivery_date": "2026-09-10", "complete": false}],
"off_order_items": [{"qa_item_id": 55, "report_id": 73, "folio": "TL-0045-003", "description": "Cinta", "udm": "pz", "quantity": 2, "unit_price": 30, "line_total": 60, "item_c_id": null}],
"off_order_amount": 60,
"remissions": [{"id": 71, "folio": "TL-0045-001", "date": "2026-09-10", "status": 0, "cancelled": false, "amount": 187500, "on_order_amount": 187500, "delivery_fields": {"guia_embarque": "GE-1123"}}],
"totals": {"ordered_qty": 20005, "ordered_amount": 250500, "delivered_qty": 15000, "delivered_amount": 187500, "pending_qty": 5005, "pending_amount": 63000, "items_count": 2, "items_complete": 0, "progress_pct": 74.85, "complete": false}
```

`items[].id` es `quotation_items.id` = el `item_contract_id` que la remisión debe mandar por item. 404 si el control no existe.

### `PUT /deliveryControl` (parcial)

`{"id_control": 3, "title": "…", "client_po_number": "…", "currency": "USD", "status": 1}` → 200 `{"id_control": 3, "changes": [{"field": "status", "before": 0, "after": 1}], "status": 1, "status_label": "COMPLETO"}`. 400: control cancelado, `title` vacío, `status` fuera de 0/1.

### `PUT /deliveryControl/fields` · `PUT /deliveryControl/values`

- `fields`: `{"id_control": 3, "custom_fields": [...]}` lista **completa** → 200 `{"custom_fields", "added", "removed", "remissions_swept"}`.
- `values`: `{"id_control": 3, "id_remission": 71, "values": {"guia_embarque": "GE-1123", "parcial": true}}` → 200 `{"delivery_fields": {…}}` (el objeto completo tras el merge; `null`/`""` vacía la llave). 400: llave no declarada, tipo inválido, remisión fuera del control, control cancelado. 404: remisión inexistente.

### `PUT /deliveryControl/remissions`

`{"id_control": 3, "add": [73], "remove": [71]}` → 200 `{"added": [73], "removed": [71], "remissions_count": 2, "status": 0}`. Validación completa antes de escribir (todo o nada): inexistente, cliente distinto, en otro control activo, `remove` de una que no está, ambas vacías, mismo id en ambas, control cancelado → 400 con lista.

### `PUT /deliveryControl/cancel`

`{"id_control": 3, "comment": "…"}` → 200 (`msg` "ya estaba cancelado" si repite). `GET /deliveryControl/catalogs` → `{statuses, value_types, currencies}`.

### Cambios en remisiones

- `POST /remission` / `POST /remissionControlTable`: `metadata.delivery_control_id` opcional. Respuesta 201 gana `delivery_control_id` y `delivery_control_status`. **400 nuevo** `"La remisión excede lo pedido en la OCD"` con `error: ["partida 1 (Fibra óptica…): pedido 20000, entregado 15000, esta remisión 6000 (excede por 1000)"]`, y `"Control de entregas no válido"` cuando el explícito no existe / está cancelado / es de otro cliente / los items apuntan a dos OCD.
- `PUT /remission`: mismo 400 de sobre-entrega; 400 si cambia `client_id` con control activo; respuesta trae `delivery_control_id` y `delivery_control_status`. Item sin `item_contract_id` conserva su partida.
- `GET /remission-<id>`: cada fila gana `delivery_control_id` (int|null) y `delivery_control_active` (bool|null); filtro `?delivery_control_id=3`.

### Cambios en cotizaciones (`/admin/presales`)

`PUT /quotation` → 400 `"La cotización tiene un control de entregas activo"` con `error: ["partida 1: cantidad 10000 menor a lo entregado 20000 (control de entregas 3)"]`; `DELETE /quotation` y `PUT /quotation/ocd {document_type: "quotation"}` → 400 con `data.delivery_control_id`.

### Gotchas

- El front debe mandar `item_contract_id = items[].id` del detalle para que la entrega cuente contra la partida; sin él, el item cae en "fuera de la orden".
- `status` del control puede volver a 0 solo después de que alguien lo puso en 1 a mano si entra o cambia una remisión: el recálculo manda.
- Retirar una remisión del control no "des-entrega" nada (ver *Por qué una columna*). Para que deje de contar, cancelarla (F3) o quitarle el `item_contract_id` a sus items.

## Al modificar

- **Cambiar qué cuenta como entregado**: `get_delivered_by_item` / `get_delivery_totals_by_quotations` (controller) son las dos únicas queries; la F3 (cancelar remisión) ya queda cubierta porque filtran `ar.status <> 3`.
- **Nueva regla de adopción**: `_check_attachable` (un solo lugar para POST y `/remissions`).
- **Llaves nuevas en el detalle** → agregarlas a `_RESERVED_KEYS` para que ninguna columna dinámica choque.
- `get_remission_by_id`: cualquier columna nueva va **al final** (índice 24+) y se documenta en el comentario de índices.
- Membresía nunca por `activity_reports.quotation_id` (es la QA); siempre `delivery_control_id`.
