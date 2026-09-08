# Almacén multisede — Fase 0 (DDL + permiso) y Fase 1 (candado del kardex, catálogo de sedes, consolidado)

> Primeras dos fases del [`almacen_multisede_plan.md`](almacen_multisede_plan.md), S1 del [`plan_mes_2.md`](plan_mes_2.md) (2026-09-07). **F0**: DDL [`scripts_db_handle/almacen_multisede.sql`](../scripts_db_handle/almacen_multisede.sql) (3 tablas + `id_warehouse` en el kardex + seed de 2 sedes; **corrido en dev** por el usuario el mismo día, test/prod pendientes) y permiso `App.Department.Sucursal-2` en [`permissions_models.json`](../static/permissions_models.json). **F1**: candado `id_warehouse IS NULL` en **todas** las lecturas del kardex del principal, CRUD del catálogo de sedes e inventario consolidado por producto. Los endpoints actuales de `/almacen` no cambian de contrato: siguen significando "sede principal".

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Almacen.py`](../templates/resources/rs_Almacen.py) | Rutas nuevas `GET /warehouses`, `GET /warehouses/catalogs`, `GET /warehouse/<id>`, `POST/PUT /warehouse`, `GET /inventory/consolidated`. |
| **Orquestación** (nuevo) | [`MD_Multisede.py`](../templates/resources/midleware/MD_Multisede.py) | Lado principal: `fetch_warehouses_api`, `get_warehouse_api`, `create_warehouse_api`, `update_warehouse_api` (parcial, merge de `extra_info`), `get_multisede_catalogs_api`, `get_consolidated_inventory_api`; catálogo `WH_TRANSFER_STATUS` (F3); **`verify_warehouse_permission(data_token, id_warehouse)`** para el namespace `sucursal` de F2 (match exacto del sufijo `Sucursal-<id>`; `administrator` pasa). |
| **DB** (nuevo) | [`warehouses_controller.py`](../templates/controllers/product/warehouses_controller.py) | `get_warehouses_db`/`get_warehouse_db`/`get_main_warehouse_db`/`insert_warehouse_db`/`update_warehouse_fields_db` (whitelist) y `get_consolidated_stock_db` (stock principal + `JSON_ARRAYAGG` por sede + en tránsito con `JSON_TABLE` sobre `items` de traslados en status 0). |
| **DB** (candado) | [`movements_controller.py`](../templates/controllers/product/movements_controller.py) | Las **11** lecturas de `product_movements_amc` filtran `id_warehouse IS NULL` (listados de entradas/salidas/todos, EPP, exports, conciliación OC, dashboard, `get_product_movement_amc`). Cabecera del archivo con la regla. |
| **Modelos** (nuevo) | [`api_multisede_models.py`](../static/Models/api_multisede_models.py) | `warehouse_post_model`/`WarehousePostForm`, `warehouse_put_model`/`WarehousePutForm` (`extra_info`/`is_active` del payload crudo). |

### De paso (bugs pre-existentes destapados por el candado)

- **La gráfica del dashboard `POST /dashboard/inventory/movements` fallaba siempre**: `Functions_AuxPlots.get_data_movements_type` llamaba `get_movements_type(type_m, n_elements, data_token)` con los argumentos cruzados (la firma es `(type_m, data_token, limit)`) y el controller mandaba 3 valores para 2 marcadores. Corregidos ambos; ahora devuelve datos.
- `get_product_movement_amc` (sin callers) mandaba 4 parámetros para 3 marcadores cuando `date` era `None`.

### Reglas

- **Exactamente una sede principal** (`is_main=1`, fila 1 del seed): la API no la crea (`is_main` en el POST → `400`), no la da de baja ni edita `is_main`.
- **Baja de sede = suave** (`is_active=0`, reactivable); no hay DELETE físico. `GET /warehouses` default solo activas; `?all=1` todas.
- `name` **único** (`UNIQUE` en BD; duplicado → `400` "Ya existe una sede con el nombre…").
- `extra_info` se **mergea por llave** en el PUT (`null` en una llave la quita); capturar cualquier dato limpia el `placeholder` del seed. Sirve para que administración corrija "Sucursal 2" cuando entregue los datos, sin DDL.
- **Consolidado**: `stock_main` = `products_amc.stock`; `by_warehouse` = filas de `warehouse_stock_amc` (solo sedes secundarias, vacío si no hay); `in_transit` = suma de `quantity_sent` de traslados **en tránsito** (status 0); `stock_total = main + sedes + en tránsito`. `only_multisede=1` filtra a productos con stock en sede o en tránsito.
- Permisos: catálogo `["administracion", "almacen"]`; consolidado `almacen`.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`). Base `/GUI/api/v1/almacen`. Envelope `{data, msg, error}`.

### `GET /warehouses` · `GET /warehouse/<id_warehouse>`

```json
// 200 (lista; ?all=1 incluye is_active 0)
{"data": [
  {"id_warehouse": 1, "name": "Almacén Principal", "is_main": 1, "is_active": 1, "extra_info": {"address": "", "manager": "", "placeholder": false}, "history": [...], "created_at": "2026-09-07T12:00:00", "updated_at": null},
  {"id_warehouse": 2, "name": "Sucursal 2", "is_main": 0, "is_active": 1, "extra_info": {"address": "", "manager": "", "placeholder": true}, "history": [...], "created_at": "...", "updated_at": null}
 ], "msg": "2 sedes", "error": null}
// detalle: mismo objeto en data · 404 {"data": null, "msg": "No existe la sede 9", "error": "No encontrado"}
```
`extra_info.placeholder: true` = datos de la sede aún no capturados (mostrar aviso).

### `POST /warehouse`

Body `{"name": "Sucursal Monterrey", "extra_info": {"address": "…", "manager": "…", "phone": "…"}}` (`extra_info` opcional, dict libre).
```json
// 201 {"data": {"id_warehouse": 3, "name": "Sucursal Monterrey"}, "msg": "Sede 3 (Sucursal Monterrey) creada", "error": null}
// 400 nombre vacío / duplicado / extra_info no objeto / is_main
```
Alta = dar el permiso `App.Department.Sucursal-<id_warehouse>` a los usuarios de esa sede (alta del permiso en `permissions_models.json`, fuera del API).

### `PUT /warehouse` (parcial)

Body `{"id_warehouse": 2, "name"?: "…", "is_active"?: 0|1, "extra_info"?: {"phone": "555", "manager": null}}` — solo se aplica lo presente.
```json
// 200 {"data": {"id_warehouse": 2}, "msg": "Sede 2 (Sucursal 2) actualizada: extra_info (phone, manager)", "error": null}
// 200 sin cambios efectivos: {"data": {"id_warehouse": 2}, "msg": "Sin cambios", "error": null}
// 400 "La sede principal no se puede dar de baja" · nombre duplicado/vacío · is_active fuera de 0/1 · is_main · 404 id inexistente
```

### `GET /warehouses/catalogs`

`data.transfer_status` `[{code, label}]` (0 EN TRÁNSITO, 1 RECIBIDO, 2 RECIBIDO CON DIFERENCIAS, 3 CANCELADO — lo usa F3) y `data.rules` (texto).

### `GET /inventory/consolidated?search=<sku|nombre>&only_multisede=1`

```json
{"data": [
  {"id_product": 1, "sku": "10010000001", "name": "ABRAZADERA CLIP 1/2", "udm": "PIEZA ",
   "stock_main": 15.0, "by_warehouse": [{"id_warehouse": 2, "name": "Sucursal 2", "stock": 7.5}],
   "stock_sedes": 7.5, "in_transit": 5.0, "stock_total": 27.5}
 ], "msg": "1 productos", "error": null}
```
Sin filtros devuelve **todo el catálogo** (~1.2k filas en dev; `by_warehouse: []` e `in_transit: 0` en casi todos hoy). Para la pantalla del consolidado conviene arrancar con `only_multisede=1` o `search`.

### Gotchas

- Todo lo que ya existía bajo `/almacen` sigue leyendo **solo el principal**; una sede no aparece en `/movements/*` ni en `/inventory/products/*` — su operación va por el namespace `sucursal` (F2).
- Sin el DDL corrido en la BD contra la que se integra, `/warehouses` y `/inventory/consolidated` responden `400` con "Table … doesn't exist" y **los listados del kardex** con "Unknown column 'id_warehouse'": correr [`almacen_multisede.sql`](../scripts_db_handle/almacen_multisede.sql) antes.

## Verificación

Dev (2026-09-07): las 11 lecturas del kardex responden con el filtro (entradas 3008, salidas 3494, todos 6502, EPP 201, dashboard 5) y la gráfica del dashboard vuelve a dar datos. Smoke de F1 (27 checks, datos temporales borrados al final): listado/detalle/404, alta, nombre duplicado, `is_main` rechazado, `extra_info` no-dict, merge de `extra_info` (+llave, −llave, `placeholder` a `false`), renombrar, "Sin cambios", baja suave (excluida del default, incluida con `all=1`), reactivar, baja del principal `400`, `is_main` en PUT `400`, catálogos, `verify_warehouse_permission` (exacto por sufijo, `Sucursal-22` no abre la 2, `administrator` pasa), consolidado con stock temporal en sede 2 y traslado en tránsito (`stock_main`/`by_warehouse`/`in_transit`/`stock_total` correctos), `only_multisede`. `pyrefly check` sin errores nuevos; `app` importa.

## Al modificar

- **Lectura nueva del kardex** en cualquier archivo: decidir explícitamente qué sede lee (`id_warehouse IS NULL` = principal; `= %s` = sede). La cabecera de `movements_controller.py` lo recuerda.
- **Columna nueva en `warehouses_amc`** → DDL + `WAREHOUSE_COLUMNS` (posicional) + `_UPDATABLE_COLS` si se escribe + `_row_to_warehouse`.
- **Estatus nuevo de traslado** → `WH_TRANSFER_STATUS` (el catálogo lo expone solo).

## Pendientes

- **[back]** DDL en test/prod (F0). F2: namespace `sucursal` (movimientos libres con stock por sede, inventario de sede, ver principal). F3: traslados. F4: exports/dashboard de sede + fix del DELETE del principal (**no entra en el mes 2**).
- **[front]** Consolidado y catálogo de sedes quedan **fuera del mes 2** por decisión del plan (primero inventario/movimientos de sede y recepción); el contrato ya está para cuando entren.
- **[admin]** Datos reales de la sede 2 (nombre, encargado): capturarlos con `PUT /warehouse` cuando administración los entregue.
