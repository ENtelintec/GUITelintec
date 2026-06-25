# Rastreo de entregas de SM al crear/actualizar una Orden de Compra

Cuando se crea o actualiza una Orden de Compra (OC), ahora se **rastrean los
cambios hacia los `deliveries` de los items de SM** relacionados. Para cada item
de la OC con un `id_item_sm` válido, se localiza (o crea) el `delivery`
correspondiente dentro del item de SM y se mapean `folio`, `folio_supplier` y
`time_delivery`. El cambio queda registrado en el `history` de la SM.

## El vínculo OC ↔ SM

- Cada **item de OC** (`purchase_order_items`) lleva `extra_info.id_item_sm`, que
  apunta a `sm_items.id_item` (lo arma
  [`create_extra_info_product_from_data`](../templates/resources/midleware/MD_Purchases.py)).
- Cada **item de SM** (`sm_items`) tiene una columna JSON `deliveries` (lista).
  El esquema de cada delivery está en
  [`DeliveriesForm`](../static/Models/api_sm_models.py): `quantity`, `timestamp`,
  `comment`, `state`, `folio`, `color`, `id_order`, `folio_supplier`.
- El match del `delivery` dentro del item es por `delivery.id_order == id_order`
  de la OC.

## Las capas tocadas

```
HTTP   rs_Admin_collections.py  /order (post/put)           -> sin cambios (ya invocan el midleware)
mid    MD_Purchases.py  sync_sm_deliveries_from_po           -> NUEVO helper, llamado desde create/update
DB     sm_controller.py  get_sm_item_deliveries_db /         -> NUEVOS controllers (lectura + escritura)
                         update_deliveries_sm_item_db
```

## Comportamiento (`sync_sm_deliveries_from_po`)

Se invoca desde
[`create_purchaser_order_api`](../templates/resources/midleware/MD_Purchases.py) (con
el `id_order` recién insertado) y
[`update_purchase_order_api`](../templates/resources/midleware/MD_Purchases.py) (con
`data["id"]`), **siempre**, sin condicionar por status, después de escribir la OC
y sus items.

Por cada item de `data["items"]`:

1. `id_item_sm = item["id_item_sm"]`; si es `≤ 0`/`None` → se omite.
2. Lectura ligera con `get_sm_item_deliveries_db(id_item_sm)`:
   `SELECT smi.id_item, smi.id_sm, smi.deliveries, mr.history` (JOIN
   `materials_request`). Solo trae lo necesario, **no** el agregado pesado de
   `get_sm_from_item`.
3. Se busca el `delivery` con `id_order == po_id`.
   - **Existe** → se actualiza.
   - **No existe** (caso típico al crear) → se **agrega** uno nuevo con
     `quantity = item["quantity"]`, `timestamp = ahora`, `state = 0`,
     `color = "#ffffff"`.
4. En ese delivery se escribe:
   - `id_order` ← `po_id`
   - `folio` ← `data["folio"]` (sobrescribe)
   - `folio_supplier` ← `data["folio_supplier"]` (PO-level `extra_info`, sobrescribe)
   - `comment` ← se **inserta/reemplaza** el segmento `[Entrega estimada: <time_delivery>]`
     conservando el resto del comment (idempotente entre updates — ver abajo).
5. Persistencia con `update_deliveries_sm_item_db(deliveries, id_item, history, sm_id)`:
   `UPDATE sm_items SET deliveries=%s WHERE id_item=%s` y luego
   `UPDATE materials_request SET history=%s WHERE sm_id=%s` (mismo patrón que
   [`update_extra_info_sm_item_db`](../templates/controllers/material_request/sm_controller.py)).
   **Solo** se toca la columna `deliveries`; nunca `state_delivery`,
   `state_quantity` ni otras.

### Fuentes de los campos (nivel OC)

`folio`, `folio_supplier` y `time_delivery` son **únicos por OC** (no por item):
`data["folio"]`, `data["folio_supplier"]` (de `extra_info` PO-level) y
`data["time_delivery"]`.

### Idempotencia del comment

`time_delivery` se **anexa** al `comment` del delivery, pero como el mismo
delivery se vuelve a tocar en cada update de la OC, el append usa un segmento
marcado con prefijo y se reemplaza en lugar de duplicar:

```python
DELIVERY_COMMENT_PREFIX = "Entrega estimada"
# "<texto previo> [Entrega estimada: 2026-07-01]"
```

El texto libre previo del comment se conserva; solo el segmento entre corchetes
se actualiza.

## Manejo de errores (no fatal)

La OC ya quedó guardada cuando corre el sync, así que un fallo de rastreo **no**
cambia el código HTTP (la OC sigue `200`/`201`). Cada resultado/fallo se devuelve
como mensaje (en español) que se **anexa a `msg`**, se escribe en `log_file_po` y
viaja en la notificación. El campo `error` del envelope no se altera por el sync.

## Al modificar

- Si cambia el esquema del `delivery`, revisar
  [`DeliveriesForm`](../static/Models/api_sm_models.py) y `deliveries_item_model`
  además del helper.
- El match del delivery depende de `id_order`. Si se quisiera matchear también
  por `folio` (p.ej. deliveries creados por el GUI antes de existir la OC), hay
  que ajustar la búsqueda en `sync_sm_deliveries_from_po`.
- `folio`/`folio_supplier` se **sobrescriben**; `time_delivery` se inserta como
  segmento marcado en `comment`. No mezclar los modos sin actualizar este doc.
- Cualquier columna distinta de `deliveries` que se quiera sincronizar exige
  ampliar `update_deliveries_sm_item_db` (no reutilizar `update_items_sm`, que
  necesita el item completo y pisaría columnas).
