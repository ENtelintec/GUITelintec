# `PUT /contract` y `PUT /quotation` devuelven el resultado por item (`data.items`) y `comment` sale del contrato

Fecha: 2026-10-09 · **Estado: hecho y verificado contra dev (21/21 checks, `Tests/tester_items_put_ids.py`; regresión: `tester_quotation_ocd` 35/35, `tester_delivery_control` 71/71, `tester_quotation_costs` 37/37).** Sin DDL.

Cierra dos pendientes de [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md):

1. **El `PUT` no devolvía los `qa_item_id` creados.** El front tenía que hacer otro `GET` para refrescar el grid; si guardaba dos veces sin recargar, los items nuevos se creaban **otra vez**.
2. **`comment` era un campo fantasma**: los forms y el swagger lo aceptaban y ningún SQL lo escribía. Decisión del usuario (2026-10-09): **quitarlo**.

## Capas tocadas

```
modelos  api_contracts_models.py       sin `comment` en ProductsPostQuotationForm / ProductsPutQuotationForm
                                       ni en products_quotation_model / products_quotation_put_model
mid      Functions_midleware_admin.py  _item_result / _items_created_out; update_items_quotation_from_api
                                       devuelve un 5º valor (items_out); los 2 PUT lo ponen en data.items
```

Controllers sin cambios. Los `comment` de `timestamps` (`TimestampsAdminForm`, `TimestampsCompleteForm`, `timestamp_model_admin`) **siguen**: esos sí se guardan.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Respuestas JSON `{data, msg, error}`.
- **Request**: igual que antes (ver [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md)). `comment` en un item **ya no está en el contrato**. Si se manda, se ignora sin error, como siempre.
- **Respuesta 200**: `data` gana **`items`**, con una entrada por cada elemento de `products` del request **en el mismo orden**:

  | llave | qué es |
  |---|---|
  | `index` | posición en `products` del request (0-based): **mapear por aquí** |
  | `partida` | la `partida` que se mandó |
  | `qa_item_id` | id resultante: el nuevo si se creó, el mismo si se actualizó o borró, `null` si se saltó o falló al crear |
  | `action` | `created` · `updated` · `deleted` · `skipped` (fila con `is_erased: 1` que nunca se guardó) · `error` |

  `PUT /quotation`:

  ```json
  {
    "data": {
      "id_quotation": 51,
      "items": [
        {"index": 0, "partida": 1, "qa_item_id": 812, "action": "updated"},
        {"index": 1, "partida": 2, "qa_item_id": 813, "action": "deleted"},
        {"index": 2, "partida": 3, "qa_item_id": 815, "action": "created"},
        {"index": 3, "partida": 5, "qa_item_id": null, "action": "skipped"}
      ]
    },
    "msg": "Cotización actualizada correctamente (ID 51). Items: 1 creado(s), 1 actualizado(s), 1 eliminado(s)",
    "error": null
  }
  ```

  `PUT /contract`: `data = {"id_contract": 11, "id_quotation": 52, "items": [...]}`. Sin `products` → `"items": []`.
- **Cómo usarlo**: después del 200, para cada `items[i]` con `action` `created`/`updated`, poner `products[index].qa_item_id = qa_item_id`; quitar del grid los `deleted` y los `skipped`. Así el siguiente guardado actualiza en vez de duplicar, sin otro `GET`.
- Un `qa_item_id` ajeno (de otra cotización) se **recrea**: vuelve `action: "created"` con un id **nuevo**.
- **200 con fallos parciales**: los fallidos vienen con `action: "error"` en `items`, y `error` sigue siendo la lista de mensajes de esos items. Si fallan **todos**, la respuesta es 400 con `data: null`, igual que antes.

## Al modificar

- Cualquier rama nueva del upsert agrega su entrada con `_item_result(index, product, qa_item_id, action)`: `items` siempre tiene `len(products)` entradas y en orden.
- **No** agregar `items` ni llaves al `JSON_OBJECT` de `get_quotation`: su orden es load-bearing para `compare_file_quotation` (ver el doc de upsert).
- Si algún día un item necesita comentario, va en `quotation_items.extra_info` (sin DDL), en los forms **y** en `_item_quotation_values`. Hoy no existe.

## Verificación

Contra BD dev (2026-10-09), [`Tests/tester_items_put_ids.py`](../Tests/tester_items_put_ids.py) (gitignored), **21/21**. Crea una cotización y un contrato temporales (con su cotización) y los borra al final. Cubre:

- **`PUT /quotation`** con las 5 ramas: actualizar, borrar, crear con `null` y con `0`, saltar fila nunca guardada y recrear un id ajeno. Cada `qa_item_id` se cruza contra el `GET` con su `partida`.
- **Segundo guardado** con los ids devueltos (y un `comment` legado en cada item) → todo `updated`, sin duplicar.
- **`PUT /contract`** (actualizar/borrar/crear) y `PUT /contract` sin `products` → `items: []`.

`pyrefly`: 0 errores en los 2 archivos.
