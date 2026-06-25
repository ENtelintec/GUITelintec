# Separación de `unit_price`: sugerido (cotización) vs real (remisión)

## Contexto

Los ítems de cotizaciones de actividad y de remisiones **comparten la misma fila** en
[`quotation_activity_items`](../templates/controllers/presales/remisions_controller.py). Al crear una
remisión, la fila del ítem de cotización se reutiliza: se le asigna `report_id` y se sobrescribía
`unit_price`. Eso hacía que el precio **sugerido** de la cotización se perdiera, porque `unit_price`
pasaba a ser el precio **real** de la remisión.

## Cambio

El precio sugerido de la cotización ahora se conserva en
`quotation_activity_items.extra_info["unit_price_quotation"]` (columna JSON de la tabla de ítems).
La columna principal `unit_price` representa siempre "el actual": el sugerido mientras no haya
remisión, y el precio real una vez creada la remisión.

Reglas resueltas:

- **Sugerido siempre desde la cotización**: al crear/editar una cotización se escribe
  `extra_info["unit_price_quotation"] = unit_price`.
- **Remisión preserva, no recibe**: el form de remisión sigue mandando un solo `unit_price` (el real).
  El backend lee la fila existente y conserva `unit_price_quotation`; solo escribe `unit_price = real`.
- **Protección del precio real**: al editar una cotización cuyo ítem **ya tiene `report_id`**
  (ya existe remisión), la edición solo actualiza `extra_info["unit_price_quotation"]` y **no** toca
  `unit_price` (no pisa el real). Si el ítem no tiene `report_id`, actualiza ambos.
- **Ítem sin cotización** (creado directo en remisión, `quotation_id=NULL`):
  `extra_info["unit_price_quotation"] = 0`.
- **Exposición**: los GET de cotización y remisión devuelven `unit_price_quotation` **plano** en cada
  ítem (junto a `unit_price`).

## Capas tocadas

### DB — [`templates/controllers/presales/remisions_controller.py`](../templates/controllers/presales/remisions_controller.py)
- `insert_quotation_activity_item` / `update_quotation_activity_item`: nuevo parámetro
  `extra_info: dict | None`, se persiste en la columna `extra_info`. El llamador decide el `unit_price`
  a escribir (así protege el real) y entrega el `extra_info` ya resuelto.
- `get_quotation_activity_items`, `get_quotation_activity_by_id`, `get_remission_by_id`: agregan
  `extra_info` al SELECT / `JSON_OBJECT` de ítems.

### Orquestación — [`templates/resources/midleware/MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py)
- Helpers: `_coerce_extra_info` (acepta dict anidado o str) y
  `_flatten_items_unit_price_quotation` (expone el campo plano en los GET).
- `create_quotation_activity_from_api` / `update_quotation_activity_from_api`: escriben
  `unit_price_quotation`; el update protege el real cuando el ítem ya tiene `report_id`.
- `create_remission_from_api` / `update_remission_from_api`: preservan `unit_price_quotation` de la
  fila existente y ponen `unit_price = real`; los ítems nuevos arrancan con `unit_price_quotation = 0`.
- `get_quotations_from_api` / `get_remission_from_api`: aplanan `unit_price_quotation` por ítem.

### Forms/models
Sin cambios: el frontend de remisión sigue mandando un solo `unit_price`; el sugerido se preserva
desde la BD.

## Al modificar

- El `unit_price` que se escribe en `update_quotation_activity_item` lo decide la midleware, no el
  controller. Si cambias la lógica de protección del real, hazlo en la midleware.
- `extra_info` del ítem puede llegar como dict (anidado en `JSON_OBJECT`/`JSON_ARRAYAGG`) o como str
  (en `fetchall` crudo). Usa `_coerce_extra_info` antes de leerlo.
- La columna `extra_info` de `quotation_activity_items` es distinta de la `extra_info` de
  `activity_reports` (esa guarda metadata de la remisión: pedido, remito, fechas, etc.).

## Pendiente a futuro

~~Historial de remisiones por ítem~~ — implementado en
[`remission_history_changes.md`](remission_history_changes.md): el `history` de la remisión ahora
registra un `changes` resumido (metadata + items con prev/actual), incluyendo cambios de
`unit_price`/`unit_price_quotation`.
