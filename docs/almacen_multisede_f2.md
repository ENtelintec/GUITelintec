# Almacén multisede — Fase 2: namespace `sucursal` (inventario de sede, stock del principal, movimientos libres)

> Fase 2 del [`almacen_multisede_plan.md`](almacen_multisede_plan.md), adelantada de S2 a S1 del [`plan_mes_2.md`](plan_mes_2.md) (2026-09-08). Es lo que el front de la sede consume **primero** según el plan: inventario y movimientos. Sobre la F0/F1 de [`almacen_multisede_f1.md`](almacen_multisede_f1.md): DDL ya corrido en las 3 BDs. Las entradas nacidas de un traslado (F3) ya quedan protegidas desde ahora.

## Qué cambió (4 capas nuevas + registro)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** (nuevo) | [`rs_Sucursal.py`](../templates/resources/rs_Sucursal.py) + registro en [`app.py`](../app.py) | `Namespace("GUI/api/v1/sucursal")`: `GET /inventory`, `GET /inventory/main`, `GET /movements/<type_m>`, `POST/PUT/DELETE /movement`. |
| **Orquestación** (nuevo) | [`MD_Sucursal.py`](../templates/resources/midleware/MD_Sucursal.py) | `_resolve_warehouse` (sede desde el permiso o `id_warehouse`, 403 si es ajena, 400 si es la principal o está de baja), inventario, kardex, y el CRUD de movimientos con stock por sede (`create_/update_/delete_sede_movement_api`). Log nuevo `log_file_sucursal` (`files/logs/sucursal`). |
| **DB** | [`warehouses_controller.py`](../templates/controllers/product/warehouses_controller.py) (sección "Lado SEDE") | `get_warehouse_inventory_db`, `get_main_inventory_db`, `get_warehouse_stock_db`, `add_warehouse_stock_db` (upsert atómico `stock = stock + delta`), `get_warehouse_movements_db`/`get_warehouse_movement_db`, `insert_/update_/delete_warehouse_movement_db` (acotados a `id_warehouse`). |
| **Modelos** (nuevo) | [`api_sucursal_models.py`](../static/Models/api_sucursal_models.py) | `sucursal_movement_post/put/delete_model` + `SucursalMovementPost/Put/DeleteForm`. |

### Reglas

- **Qué sede opera**: del permiso `App.Department.Sucursal-<id>`. Con **un solo** permiso de sede, `id_warehouse` es opcional en todo; con varios, obligatorio. Un id ajeno → `403`. Lecturas (`/inventory`, `/inventory/main`, `/movements/*`) también para `almacen`/`administracion` (supervisión desde el principal) mandando `id_warehouse`; **escrituras solo con permiso de sede**. La sede principal no opera por aquí (`400`: usa `/almacen`); una sede dada de baja se lee pero no se escribe.
- **Stock por sede** en `warehouse_stock_amc`; la fila nace con el primer movimiento (upsert). **Nunca negativo**: `POST` salida valida stock suficiente; `PUT` compensa por diferencia (efecto nuevo − efecto viejo, donde efecto = +cantidad entrada / −cantidad salida) y rechaza si deja negativo; `DELETE` **revierte** el efecto y rechaza borrar una entrada ya consumida.
- **Kardex único**: los movimientos de sede se insertan en `product_movements_amc` con `id_warehouse` = sede y `sm_id` NULL (las SMs se despachan solo del principal). `extra_info` = `{reference (mayúsculas), comment, user}` (+ `updated_by` al editar). El principal no ve estos movimientos (candado de F1).
- **Movimientos de traslado** (`extra_info.id_transfer`, los creará F3) se listan con `editable: false` y **no** se editan ni borran desde la sede (`400`).
- Sin transacciones entre llamadas: `POST` escribe el movimiento y luego el stock; si el stock falla, borra el movimiento best-effort y responde `400`. En `PUT`/`DELETE` el ajuste de stock va después del movimiento; si falla, `200` con el detalle en `error` (mismo patrón no-fatal del repo).

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`). Base `/GUI/api/v1/sucursal`. Envelope `{data, msg, error}`. El front de la sede **no manda** `id_warehouse` si el usuario tiene una sola sede.
- Códigos comunes: `401` token · `403` sede ajena / sin permiso de sede / `almacen` intentando escribir · `404` sede o movimiento inexistente · `400` validación, stock insuficiente, sede principal, sede de baja, movimiento de traslado.

### `GET /inventory?search=&only_with_stock=1[&id_warehouse=]`

```json
{"data": {"warehouse": {"id_warehouse": 2, "name": "Sucursal 2"},
          "products": [{"id_product": 1, "sku": "10010000001", "name": "ABRAZADERA CLIP 1/2", "udm": "PIEZA ", "category_name": "CANALIZACIÓN",
                        "stock": 10.0, "stock_main": 15.0, "is_tool": 0, "is_internal": 0, "name_short": null}]},
 "msg": "1 productos", "error": null}
```
`stock` = de la sede; `stock_main` = del principal (solo lectura, mismo renglón para no pedir dos listas). Sin filtros devuelve todo el catálogo (~1.2k) con `stock: 0` en lo que la sede no tiene: arrancar con `only_with_stock=1`.

### `GET /inventory/main?search=&only_with_stock=1`

Misma forma de producto pero `data` es la lista directa y `stock` = `stock_main` (el principal). Solo lectura.

### `GET /movements/<type_m>?date_from=&date_to=&limit=[&id_warehouse=]`

`type_m` ∈ `entrada | salida | all`; fechas `YYYY-MM-DD` inclusivas; `limit` default 500, máx 5000 (más recientes primero).
```json
{"data": {"warehouse": {"id_warehouse": 2, "name": "Sucursal 2"},
          "movements": [{"id_movement": 6876, "id_product": 1, "sku": "10010000001", "name": "ABRAZADERA CLIP 1/2", "udm": "PIEZA ",
                         "movement_type": "salida", "quantity": 2.5, "movement_date": "2026-09-01 00:00:00", "sm_id": null,
                         "id_warehouse": 2, "reference": "FAC-1", "comment": "inicial", "user": 34, "id_transfer": null, "editable": true,
                         "extra_info": {"reference": "FAC-1", "comment": "inicial", "user": 34}}]},
 "msg": "1 movimientos", "error": null}
```
`editable: false` (con `id_transfer`) = nació de un traslado: la UI oculta editar/borrar.

### `POST /movement`

Body `{"id_product": 1, "movement_type": "entrada", "quantity": 12.5, "movement_date"?: "2026-09-08" | "2026-09-08 10:30:00", "reference"?: "FAC-1", "comment"?: "...", "id_warehouse"?: 2}`.
```json
// 201
{"data": {"id_movement": 6875, "id_warehouse": 2, "id_product": 1, "movement_type": "entrada", "quantity": 12.5, "movement_date": "2026-09-08 10:30:00", "stock_before": 0.0, "stock_after": 12.5},
 "msg": "Sede 2 (Sucursal 2): entrada de 12.5 de ABRAZADERA CLIP 1/2 (producto 1), stock 0 -> 12.5 ref FAC-1 [emp 34]", "error": null}
// 400 {"data": null, "msg": "Stock insuficiente en la sede 2 para ABRAZADERA CLIP 1/2: hay 12.5, se quieren sacar 20", "error": null}
// 400 quantity <= 0 · movement_type fuera de entrada|salida · movement_date inválida · 404 producto inexistente
```
La respuesta trae `stock_before`/`stock_after`: repintar el renglón sin re-`GET`.

### `PUT /movement` (parcial)

Body `{"id_movement": 6876, "quantity"?: 4, "movement_type"?: "entrada", "movement_date"?: "...", "reference"?: "...", "comment"?: "..."}` — solo lo presente se aplica; la sede sale del propio movimiento.
```json
// 200 {"data": {"id_movement": 6876, "id_warehouse": 2, "stock_before": 10.0, "stock_after": 8.5, "stock_delta": -1.5}, "msg": "Sede 2: movimiento 6876 actualizado (cantidad 2.5 -> 4), stock del producto 1 10 -> 8.5 [emp 34]", "error": null}
// 200 sin cambios efectivos: {"data": {"id_movement": 6876}, "msg": "Sin cambios", "error": null}
// 400 "El cambio dejaría el stock de la sede en negativo (16.5 -104): ..." · movimiento de traslado · movimiento del principal · 403 otra sede · 404
```

### `DELETE /movement`

Body `{"id_movement": 6876}`.
```json
// 200 {"data": {"id_movement": 6876, "id_warehouse": 2, "stock_before": 19.5, "stock_after": 15.5}, "msg": "Sede 2: movimiento 6876 (entrada de 4 del producto 1) borrado, stock 19.5 -> 15.5 [emp 34]", "error": null}
// 400 {"data": null, "msg": "No se puede borrar la entrada de 12.5: el stock de la sede quedaría en negativo (0.5 -12.5); parte ya se consumió", "error": null}
// 400 movimiento de traslado · 403 otra sede · 404
```

### Gotchas

- `movement_date` acepta `YYYY-MM-DD` (queda `00:00:00`) o `YYYY-MM-DD HH:MM:SS`; ausente = ahora.
- `reference` se guarda en **mayúsculas** (misma convención que el principal, la usa la conciliación OC).
- El catálogo es compartido: la sede **no crea productos**. Si un SKU no existe, lo da de alta el principal.
- El inventario inicial de la sede se captura como entradas libres (o llegará por traslado en F3).

## Verificación

Dev (2026-09-08, 46 checks, datos de la sede 2 borrados al final; stock y kardex del principal verificados intactos): resolución de sede por permiso (inferida, ajena `403`, `almacen` lee con id y no escribe, principal `400`, inexistente `404`, id inválido `400`, `basic` `403`), forms, entrada/salida con stock 0→12.5→10, salida mayor al stock `400`, cantidad 0 / tipo inválido / producto inexistente / fecha inválida, kardex con filtros de tipo, fechas y `limit`, inventario `only_with_stock` con `stock_main`, inventario del principal por `search`, PUT por diferencia (cantidad, cambio de tipo, negativo `400`, solo referencia sin delta, sin cambios, otra sede `403`, inexistente `404`, movimiento del principal `400`), protección de traslado en kardex/PUT/DELETE, DELETE con reversa (entrada consumida `400`, orden correcto sí). `pyrefly check` sin errores nuevos; `app` importa y registra las 4 rutas.

## Al modificar

- **Campo nuevo en un movimiento de sede** → `extra_info` (sin DDL) + `_row_to_movement` + este doc; si es columna real, también `SEDE_MOVEMENT_COLUMNS` (posicional) y `_SEDE_MOVEMENT_UPDATABLE`.
- **F3 (recepción de traslados)** debe insertar sus entradas con `extra_info.id_transfer` y sumar stock con `add_warehouse_stock_db`; la protección contra PUT/DELETE ya está.
- **Permisos**: el namespace abre con substring `sucursal`; la sede concreta la valida `_resolve_warehouse` → `verify_warehouse_permission` (`MD_Multisede.py`). Un permiso nuevo de sede es `App.Department.Sucursal-<id>` en `permissions_models.json`, nada más.

## Pendientes

- **[front]** Pantallas de la sede (S3): inventario (`only_with_stock` + buscador, columna del principal) y movimientos (kardex + alta/edición/borrado con `stock_before/after`).
- **[back]** F3 traslados (crear/cancelar/listar en `/almacen`, listar/recibir en `/sucursal`). F4 exports y dashboard de sede.
