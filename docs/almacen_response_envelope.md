# Envelope de respuesta `{data, msg, error}` en los endpoints de Almacén

Alineación de los endpoints de [`rs_Almacen.py`](../templates/resources/rs_Almacen.py)
(`/GUI/api/v1/almacen/*`) al envelope `{data, msg, error}` descrito en
[`contract_crud_response_envelope.md`](contract_crud_response_envelope.md) y
[`sm_response_envelope.md`](sm_response_envelope.md).

Igual que en SM, la prioridad fue **mantener compatibilidad con los clientes GUI**:
los **GET** son los más críticos del éxito porque el front los **mapea a estructuras
tipadas**, así que su `data` de éxito se conserva **intacto** (sin renombrar, quitar
ni re-tipar claves) y solo se envuelve con `msg/error: None`. En **escrituras** sí se
reestructuró el `data` a `{"id_*": N}` (confirmado que el cliente no lee el `data` de
respuesta de escritura). El front solo **muestra** los errores tal cual los recibe,
por lo que en los endpoints masivos se sacaron los errores del `data` hacia `error`.

## Las 2 capas tocadas

```
HTTP    rs_Almacen.py                     /GUI/api/v1/almacen/*  (resource: validación, passthrough)
mid     midleware/Functions_midleware_almacen.py  *_from_api / *_db / *_amc  (lógica + forma de respuesta)
```

La capa DB (`controllers/product/*`, `controllers/supplier/*`,
`controllers/product/reservations_controller.py`) y la de validación (`*Form`) **no
se tocaron**.

## Arquitectura: envelope convergido al midleware

Antes el envelope se construía **en el resource** para casi todos los endpoints
(movements, products, categories, suppliers, codes, epp), mientras que reservations
ya devolvía un dict desde el midleware. Se **unificó**: cada función de midleware
devuelve ahora `(dict, code)` con las 3 claves, y el resource quedó como
**passthrough** limpio (`data_out, code = fn(...); return data_out, code`). Esto
elimina las tuplas invertidas y los wrappers inline `{"msg": "Ok" if ... else
"Error"}`.

## Regla aplicada

| Campo | Éxito lectura (GET) | Éxito escritura | Error |
|---|---|---|---|
| `data` | **valor actual intacto** (lista/obj que el front mapea) | `{"id_<entidad>": N}` | `[]`/`None` según el tipo del éxito |
| `msg` | `None` | español-con-ID (`"Producto creado correctamente (ID N)"`) | texto corto en español |
| `error` | `None` | `None` (o detalle de marca/parcial) | detalle técnico (`error` / lista) |

- El `400` de validación de form se unificó a
  `{"data": None, "msg": "Estructura de datos invalida", "error": validator.errors}`
  (antes `{"data": validator.errors, "msg": "Error at structure"}`). Helper
  `_invalid_structure()` en el resource.
- El `401` de token se dejó **exactamente** como estaba (patrón global). `GetMovements`
  conserva su `data: []`; el resto su `{"error": ...}`.
- Claves de id en **inglés** (`id_movement`, `id_product`, `id_reservation`), sin clave
  hermana de nivel superior. En update/delete el id sale del **payload** (no del
  rowcount).

## Tuplas invertidas corregidas

`get_categories_db` y `get_suppliers_db` retornaban `(code, data)` (orden inverso al
resto). Al converger el envelope al midleware se normalizaron a `(dict, code)`,
eliminando el foot-gun.

## Side-effect de marca (`update_brand_procedure`)

El POST/PUT de `/inventory/product` ejecutaba `update_brand_procedure` **en el
resource** y concatenaba su `msg_list` al `msg` de salida. Se **movió al midleware**
(`insert_product_db` / `update_product_amc` vía helper `_register_product_brand`),
manteniendo que lee `supplier_name`/`brand` al **nivel superior** de `data` (igual que
antes). El detalle de marca ahora va a `error` **solo si la marca falla**; el `msg`
queda limpio español-con-ID. El detalle completo sigue yendo al log/notificación.

## Endpoints masivos (errores → `error`)

`/multiple/movements`, `/inventory/multiple/products` y `/file/upload/*` enterraban
sus fallos **dentro del `data`** (`errors_insert`/`errors_movements`/...) y devolvían
`200` siempre. Se reestructuró: las listas positivas (`inserted`/`updated`/
`movements`) quedan en `data`, los `errors_*` se sacan a `error` (concatenados, `None`
si vacío) y `msg` lleva un resumen en español. `200` en éxito total/parcial; `400`
solo en fallo total (p. ej. stock negativo o fallo total de inserción). Helper
`_split_bulk_result()` separa positivos de errores.

## Bugs corregidos

- **`insert_multiple_products_from_api`:** `data_out["errors"].append(...)` →
  **KeyError** (la clave era `errors_movements`). Corregido.
- **`insert_new_product`:** mismo `data_out["errors"]` **KeyError** + `errors_movements`
  nunca inicializada (solo `inserted/errors_insert/movements`). Corregido (clave
  agregada + uso correcto).
- **`update_old_products`:** `item.get["quantity_move"]` — subíndice del **método**
  `.get` → **TypeError**. Además `item` es un **string de sku** (viene de
  `update_items.append(item[0])`), no un dict, así que el `quantity_move` real es el
  elemento de `new_input_quantity` que el `zip` descartaba como `_`. Corregido para
  usar `qty_move` del zip.
- **`update_movement`:** una rama devolvía `{"data": [...], "error": ...}, 400` (dict)
  mientras el resto retornaba tuplas `(flag, result)` que el resource desempacaba como
  `flag, result` → rama rota. Normalizada al envelope.
- Mensajes de error traducidos a español (`"error at retrieving data"` →
  `"No se pudieron obtener ..."`, etc.).

## Tabla de seguimiento

| Ruta | Métodos | Función midleware | Tratamiento | Estado |
|---|---|---|---|---|
| `/movements/<type_m>` | GET | `get_all_movements` | éxito intacto + `msg/error: None`; error `data: []` español | ✅ |
| `/movement` | POST·PUT·DELETE | `insert/update/delete_movement(_amc)` | escritura `data: {"id_movement": N}`; **bug dict-return corregido**; español-con-ID | ✅ |
| `/multiple/movements` | POST | `insert_multiple_movements_from_api` | masivo: positivos en `data`, errores en `error`; `400` en stock negativo/fallo total | ✅ |
| `/inventory/products/<type_p>` | GET | `get_all_products_DB` | éxito intacto + `msg/error: None`; error `data: []` | ✅ |
| `/inventory/product` | POST·PUT·DELETE | `insert_product_db / update_product_amc / delete_product_from_api` | `data: {"id_product": N}`; marca → `error`; update/delete id del payload | ✅ |
| `/inventory/multiple/products` | POST | `insert_and_update_multiple_products_from_api` | masivo: `data: {insert, update}`, errores en `error` | ✅ |
| `/inventory/categories/all` | GET | `get_categories_db` | **tupla invertida corregida**; éxito intacto + `msg/error: None` | ✅ |
| `/inventory/suppliers/allSuppliers` | GET | `get_suppliers_db` | **tupla invertida corregida**; éxito intacto + `msg/error: None` | ✅ |
| `/codes/generate` | GET | `get_new_code_products` | éxito `data: <code>` + `msg/error: None`; error `data: None` | ✅ |
| `/file/upload/{regular,tool,internal}` | POST | `upload_product_db_from_file` | masivo: envelope desde midleware; try/except → español; validación de archivo en español | ✅ |
| `/file/download/products/{pdf,excel}` | GET | `create_file_inventory_{pdf,excel}` | éxito `send_file` intacto; error envelope español | ✅ |
| `/file/download/movements/{pdf,excel}` | POST | `create_file_movements_amc` | éxito `send_file`; error envelope español | ✅ |
| `/file/download/barcode` | POST | `create_pdf_barcode` | éxito `send_file`; error envelope español | ✅ |
| `/file/download/barcode/multiple` | POST | `create_pdf_barcode_multiple` | éxito `send_file`; error envelope español | ✅ |
| `/inventory/epp` | GET | `get_epp_db` | éxito intacto + `msg/error: None`; error `data: []` | ✅ |
| `/movements/epp/<type_m>` | GET | `get_epp_movements` | éxito intacto + `msg/error: None`; error `data: []` | ✅ |
| `/file/download/eppmovements/{pdf,excel}` | POST | `create_file_movements_amc` (epp=1) | éxito `send_file`; error envelope español | ✅ |
| `/reservation` | POST·PUT·DELETE | `create/update/delete_reservation_from_api` | `data: {"id_reservation": N}`; **códigos update/delete 201→200**; `msg` agregado español-con-ID | ✅ |
| `/reservations` | GET | `get_reservations_db` | éxito intacto + `msg/error: None`; error `data: []` | ✅ |

## Al modificar

- Mantener las **3 claves** `{data, msg, error}` en toda rama nueva (`error: None` en
  éxito).
- **GET = no tocar la forma del `data` de éxito** (el front lo mapea a estructuras).
  Solo envolver con `msg/error`. En error: `data` vacío del tipo del éxito (`[]` para
  listas, `None` para objeto/string), `msg` corto en español, detalle en `error`.
- En **escritura** exponer el id como `{"id_<entidad>": N}` (inglés, sin clave
  hermana). El detalle largo de auditoría va al log y la notificación, no al `msg`.
- En endpoints **masivos**, los errores van a `error` (lista), nunca enterrados en
  `data`; `200` en parcial, `400` solo en fallo total.
- No re-agregar `@ns.marshal_with`: filtra el envelope y oculta errores lógicos.
- El `401` de token no se toca (patrón global).
- `get_categories_db`/`get_suppliers_db` ya están en orden `(dict, code)`; no volver a
  invertirlas.
- **`"error": error`, no `str(error)`** — el `error` de `execute_sql` ya es `str` y el
  `str()` redundante dispara el warning `Unnecessary str() call` de pyrefly. `str(...)`
  solo para el `Exception` de un `except` (`str(e)`) y para `result` (union-typado).
  Igual en f-strings: `f"...{error}"`.
