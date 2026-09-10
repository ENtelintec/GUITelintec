# Almacén multisede — Fase 3: traslados principal → sede (crear, cancelar, listar, detalle, recibir)

> Fase 3 del [`almacen_multisede_plan.md`](almacen_multisede_plan.md), adelantada de S3 a S1 del [`plan_mes_2.md`](plan_mes_2.md) (2026-09-10). Cierra el ciclo de la sede sobre [`almacen_multisede_f1.md`](almacen_multisede_f1.md) (catálogo, consolidado con `in_transit`) y [`almacen_multisede_f2.md`](almacen_multisede_f2.md) (kardex y stock por sede). **Dos pasos con estado en tránsito**: el principal registra el envío (genera **sus** salidas y descuenta **su** stock), la sede confirma la recepción **una sola vez** capturando lo realmente recibido (genera **sus** entradas y suma **su** stock). Las diferencias **no se ajustan solas en ningún lado**: quedan en el traslado (enviado vs recibido) para que el principal las resuelva a mano.

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Almacen.py`](../templates/resources/rs_Almacen.py) · [`rs_Sucursal.py`](../templates/resources/rs_Sucursal.py) | Principal (`almacen`): `POST /transfer`, `PUT /transfer/cancel`, `GET /transfers`, `GET /transfer/<id>`. Sede: `GET /transfers`, `GET /transfer/<id>` (lectores), `PUT /transfer/receive` (solo permiso de sede). |
| **Orquestación** | [`MD_Multisede.py`](../templates/resources/midleware/MD_Multisede.py) · [`MD_Sucursal.py`](../templates/resources/midleware/MD_Sucursal.py) | Principal: `create_transfer_api`, `cancel_transfer_api`, `fetch_transfers_api`, `get_transfer_api` + helpers compartidos `_row_to_transfer`, `_enrich_transfer_items`, `_load_transfer`, `_parse_transfer_filters`, `_next_folio`. Sede: `fetch_sede_transfers_api`, `get_sede_transfer_api`, `receive_transfer_api` (+ `_parse_received_items`). |
| **DB** | [`warehouses_controller.py`](../templates/controllers/product/warehouses_controller.py) (sección "Traslados") | `get_next_transfer_folio_db` (max+1 sobre `TRS-####`), `insert_transfer_db`, `get_transfer_db`/`get_transfers_db` (JOIN doble a `warehouses_amc` para nombres; filtros param-or-NULL), `update_transfer_fields_db` (whitelist), `delete_transfer_db` (solo reversa interna), `get_products_brief_db`, `get_product_stock_and_reserved_db`. Los movimientos se insertan con `insert_warehouse_movement_db` (id_warehouse `NULL` = principal) y el stock del principal con `update_stock_db(just_add=True)` de siempre. |
| **Modelos** | [`api_multisede_models.py`](../static/Models/api_multisede_models.py) · [`api_sucursal_models.py`](../static/Models/api_sucursal_models.py) | `transfer_post_model` (+`transfer_item_model`) / `TransferPostForm`, `transfer_cancel_model` / `TransferCancelForm`, `transfer_receive_model` (+item) / `TransferReceiveForm`. **`items` viaja por `ns.payload` crudo** (lista de objetos; WTForms no modela listas anidadas) y lo valida el midleware. |

### Reglas

- **Crear** (`almacen`): destino = sede secundaria **activa**; v1 el origen es siempre la principal (`id_warehouse_origin` distinto → `400`). Items sin repetidos, `quantity > 0`. Se valida contra el **stock disponible** del principal = `stock − reservado` (reservas `status 0` de `product_reservations`, las de SM); si falta, `400` con el detalle por producto en `error`. Luego: folio `TRS-####` consecutivo → fila en `warehouse_transfers_amc` (status 0) → **una salida por item** en el kardex del principal (`id_warehouse NULL`, `extra_info {reference: folio, id_transfer, comment, user}`) → `products_amc.stock -= quantity`. Notifica a `sucursal-<dest>`.
- **Cancelar** (`almacen`): solo en tránsito (`status 0`). **Reversa automática**: una entrada por item en el principal (`extra_info.comment` "Reversa por cancelación…") + reintegro de stock, `status 3`. Aquí sí es automático porque el material nunca llegó.
- **Recibir** (`sucursal-<dest>`): solo en tránsito, **una sola vez**. El body debe traer **exactamente** los productos del traslado (faltantes o extras → `400`; "no llegó nada" = `quantity_received: 0`). Por item con cantidad > 0: entrada en el kardex de la sede (`id_warehouse = dest`, `extra_info {reference: folio, id_transfer}`) + suma en `warehouse_stock_amc`. Cierra en **1 RECIBIDO** (todo exacto) o **2 RECIBIDO CON DIFERENCIAS**; guarda `quantity_received`/`receive_comment` por item, `received_by`, `received_at`, history. **El stock del principal no se toca** por la diferencia. Notifica a `almacen`.
- **Entradas de traslado protegidas**: desde F2 el CRUD de la sede rechaza editarlas/borrarlas (`editable: false`, `id_transfer`).
- **Atomicidad**: sin transacciones entre llamadas. Orden defensivo traslado → movimientos → stock; si algo falla a la mitad, reversa best-effort (movimientos borrados, stock devuelto, traslado borrado en el alta / intacto en cancelar y recibir) y `400` con el detalle. Mismo patrón no-fatal del repo.
- Catálogo de status en `GET /almacen/warehouses/catalogs` (`transfer_status`). Todas las respuestas traen `status` **integer** + `status_label`.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`). Envelope `{data, msg, error}`. Status: `0` EN TRÁNSITO · `1` RECIBIDO · `2` RECIBIDO CON DIFERENCIAS · `3` CANCELADO.
- **Principal**: base `/GUI/api/v1/almacen`, permiso `almacen`. **Sede**: base `/GUI/api/v1/sucursal`; lecturas con permiso de sede o `almacen`/`administracion` (+`id_warehouse`), recepción **solo** con `Sucursal-<dest>`.

### Objeto traslado (listado y detalle, ambos lados)

```json
{"id_transfer": 7, "folio": "TRS-0007", "id_warehouse_origin": 1, "origin_name": "Almacén Principal", "id_warehouse_dest": 2, "dest_name": "Sucursal 2",
 "status": 2, "status_label": "RECIBIDO CON DIFERENCIAS", "comment": "camión 1", "created_by": 36, "received_by": 34,
 "created_at": "2026-09-10T09:12:00", "received_at": "2026-09-10 11:40:00",
 "items": [{"id_product": 1, "sku": "10010000001", "name": "ABRAZADERA CLIP 1/2", "udm": "PIEZA ", "quantity_sent": 3.0, "quantity_received": 2.0, "difference": -1.0, "comment": "caja 1", "receive_comment": "1 dañado"},
           {"id_product": 2, "sku": "10010000002", "name": "ABRAZADERA UNICANAL 1/2\\"", "udm": "PIEZA ", "quantity_sent": 2.5, "quantity_received": 2.5, "difference": 0.0, "comment": "", "receive_comment": ""}],
 "totals": {"items": 2, "quantity_sent": 5.5, "quantity_received": 4.5, "items_with_difference": 1},
 "history": [{"timestamp": "...", "user": 36, "action": "Envío", "comment": "..."}, {"timestamp": "...", "user": 34, "action": "Recepción", "comment": "..."}]}
```
En tránsito: `quantity_received`/`difference` en `null`, `totals.quantity_received: null`, `received_by`/`received_at` `null`. `difference` = recibido − enviado (negativo = faltó). La UI de seguimiento pinta `items_with_difference > 0` como pendiente de resolver por el principal.

### `POST /almacen/transfer`

Body `{"id_warehouse_dest": 2, "items": [{"id_product": 1, "quantity": 3, "comment": "caja 1"}, {"id_product": 2, "quantity": 2.5}], "comment": "camión 1"}`.
```json
// 201
{"data": {"id_transfer": 7, "folio": "TRS-0007", "status": 0, "status_label": "EN TRÁNSITO", "id_warehouse_dest": 2,
          "items": [{"id_product": 1, "name": "ABRAZADERA CLIP 1/2", "quantity_sent": 3.0, "id_movement": 6910, "stock_main_after": 12.0}, {"...": "..."}]},
 "msg": "Traslado TRS-0007 (id 7) enviado a Sucursal 2: ABRAZADERA CLIP 1/2 x3, ... [emp 36]", "error": null}
// 400 stock: {"data": null, "msg": "Stock insuficiente en el principal: ABRAZADERA CLIP 1/2 (producto 1): disponible 15 (stock 15 - reservado 0), se piden 16", "error": ["<una línea por producto corto>"]}
// 400 items vacío / quantity <= 0 / producto repetido / destino principal o de baja / origen distinto del principal · 404 producto o sede inexistente
```
`stock_main_after` sirve para repintar el inventario del principal sin re-`GET`.

### `PUT /almacen/transfer/cancel`

Body `{"id_transfer": 7, "reason": "el camión regresó"}` (`reason` opcional).
```json
// 200 {"data": {"id_transfer": 7, "folio": "TRS-0007", "status": 3, "status_label": "CANCELADO", "reversed_movements": [6912, 6913]}, "msg": "Traslado TRS-0007 cancelado; 2 item(s) reintegrados al principal [emp 36]", "error": null}
// 400 {"data": null, "msg": "El traslado TRS-0007 está en RECIBIDO CON DIFERENCIAS: solo se cancela en tránsito", "error": null} · 404 inexistente
```

### `GET /almacen/transfers?status=&id_warehouse_dest=&date_from=&date_to=&limit=`

`data` = lista de objetos traslado (enriquecidos), más recientes primero; `limit` default 200, máx 2000; fechas `YYYY-MM-DD` inclusivas sobre la creación. `status` fuera de 0..3 → `400`.

### `GET /almacen/transfer/<id_transfer>`

`data` = objeto traslado. `404` si no existe.

### `GET /sucursal/transfers?status=&date_from=&date_to=&limit=[&id_warehouse=]`

```json
{"data": {"warehouse": {"id_warehouse": 2, "name": "Sucursal 2"}, "transfers": [ {"...objeto traslado..."} ]}, "msg": "3 traslados (1 en tránsito)", "error": null}
```
Solo los traslados **hacia** la sede. La bandeja de recepción es `status=0`.

### `GET /sucursal/transfer/<id_transfer>`

`data` = objeto traslado; `403` si el destino es otra sede; `404` si no existe.

### `PUT /sucursal/transfer/receive`

Body `{"id_transfer": 7, "items": [{"id_product": 1, "quantity_received": 2, "comment": "1 dañado"}, {"id_product": 2, "quantity_received": 2.5}], "comment": "llegó a las 11"}` — **todos** los productos del traslado, `quantity_received >= 0`.
```json
// 200 con diferencias
{"data": {"id_transfer": 7, "folio": "TRS-0007", "status": 2, "status_label": "RECIBIDO CON DIFERENCIAS", "id_warehouse": 2, "received_at": "2026-09-10 11:40:00",
          "movements": [6914, 6915], "differences": [{"id_product": 1, "quantity_sent": 3.0, "quantity_received": 2.0, "difference": -1.0}]},
 "msg": "Traslado TRS-0007 recibido en Sucursal 2 (RECIBIDO CON DIFERENCIAS): 2 entrada(s), producto 1: enviado 3, recibido 2 [emp 34]", "error": null}
// 200 exacto: "status": 1, "differences": []
// 400 {"data": null, "msg": "faltan los productos [2] (manda quantity_received 0 si no llegaron)", "error": null} · "los productos [12345] no son parte del traslado" · negativo · ya recibido/cancelado ("la recepción se confirma una sola vez") · 403 otra sede o permiso del principal · 404
```
Las entradas creadas aparecen en `GET /sucursal/movements/entrada` con `editable: false` y `reference` = folio.

### Gotchas

- La UI de "crear traslado" del principal debe mostrar el **disponible** (`stock − reservado`), no el stock: el `GET /almacen/inventory/products/*` ya trae `avaliable_stock`.
- Un envío en dos camiones = dos traslados (una sola confirmación por traslado).
- Reintentar un `POST` tras un `400` de reversa es seguro: el folio se recalcula y nada quedó a medias.
- `comment` por item se guarda en el traslado y se copia al `extra_info.comment` de la salida del principal; `receive_comment` a la entrada de la sede.

## Verificación

Dev (2026-09-10, 50 checks; traslados, movimientos, stock de sede y stock del principal restaurados al final, conteo del kardex del principal idéntico al inicio): forms, `items` vacío / cantidad 0 / sin cantidad / repetido / más que el stock (con detalle en `error`) / producto inexistente / destino principal / destino inexistente / origen distinto → `400`/`404`; alta con 2 items (folio `TRS-0001`, stock del principal descontado, 2 salidas con `reference` = folio e `id_transfer`), segundo folio consecutivo, listado con filtros y `status` inválido, detalle enriquecido con `totals`, consolidado con `in_transit` = 4; lado sede: listado (con conteo en tránsito), sede inexistente `404`, sede ajena `403`, detalle `403`/`200`, supervisión del principal; recepción: faltantes / extras / negativo / otra sede / `almacen` → `400`/`403`; recepción con diferencias → `status 2`, stock de sede sumado, principal intacto, detalle con `quantity_received`/`difference`/`receive_comment`/`received_by`/`received_at`/history; segunda recepción `400`; entradas de traslado `editable: false` y protegidas en PUT/DELETE; cancelar recibido `400`, cancelar en tránsito → `status 3` con reintegro y entrada de reversa, cancelar dos veces `400`, inexistente `404`, recibir cancelado `400`, filtro por status 3 y por fecha. `pyrefly check` sin errores nuevos; `app` importa y registra las 7 rutas.

## Al modificar

- **Origen distinto del principal** (sede→principal o sede↔sede): quitar el `400` de `create_transfer_api`, descontar de `warehouse_stock_amc` del origen (con `add_warehouse_stock_db` negativo y validación) y decidir quién confirma; el modelo ya lo soporta.
- **Recepciones parciales múltiples**: hoy `receive_transfer_api` exige `status 0` y cierra; habría que acumular `quantity_received` y un status intermedio.
- **Status nuevo** → `WH_TRANSFER_STATUS` (catálogo y labels salen de ahí).
- **Columna nueva en `warehouse_transfers_amc`** → DDL + `TRANSFER_COLUMNS` (posicional, y el `SELECT` con los JOIN) + `_TRANSFER_UPDATABLE` si se escribe.

## Pendientes

- **[front]** Sede (S4): bandeja de recepción (`status=0`) + formulario de recibido por item; y formulario mínimo de "crear traslado" en el principal para probar punta a punta. Seguimiento enviado-vs-recibido y cancelar en el principal quedan **fuera del mes 2** (contrato listo).
- **[back]** F4 (solo si sobra): exports y dashboard de sede; fix del DELETE del principal para revertir stock (**no entra en el mes 2**, avisar a operación).
- **[admin]** Procedimiento de discrepancias: quién resuelve un `RECIBIDO CON DIFERENCIAS` en el principal y con qué movimiento (reingreso vs merma).
