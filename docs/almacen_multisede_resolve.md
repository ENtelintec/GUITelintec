# Almacén multisede — resolver diferencias de un traslado, lectura directa de un movimiento de sede, `meta` en listados y formatos

> Cierra `P-047` sobre [`almacen_multisede_f3.md`](almacen_multisede_f3.md) (2026-10-16). Un traslado recibido con menos piezas quedaba en `2 RECIBIDO CON DIFERENCIAS` para siempre: al enviar se descontó del principal, al recibir entró solo lo capturado y la pieza faltante no estaba en ningún lado. Ahora el principal decide por renglón **reingreso** (entrada al principal por la diferencia) o **merma** (solo registro) y el traslado pasa a `4 DIFERENCIA RESUELTA`. De paso, lo que pidió el front del lote 5: `GET /sucursal/movement/<id>`, `meta.truncated` en los listados de traslados y formatos normalizados (fechas con `format_timestamps`, `udm` sin espacios). **Sin DDL**: la resolución vive en los JSON `items` / `history` de `warehouse_transfers_amc`.

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Almacen.py`](../templates/resources/rs_Almacen.py) · [`rs_Sucursal.py`](../templates/resources/rs_Sucursal.py) | Principal (`almacen`): `PUT /transfer/<int:id_transfer>/resolve` (`TransferResolveForm` + `items` por `ns.payload` crudo). Sede (lectores `sucursal` / `almacen` / `administracion`): `GET /movement/<int:id_movement>`. Docs swagger de `/transfers` con el status 4 y `meta.truncated`. |
| **Orquestación** | [`MD_Multisede.py`](../templates/resources/midleware/MD_Multisede.py) · [`MD_Sucursal.py`](../templates/resources/midleware/MD_Sucursal.py) | `WH_TRANSFER_STATUS[4]`, `RESOLVE_ACTIONS`, `resolve_transfer_api` (+ `_parse_resolve_items`), `query_transfers` (`limit + 1` → `meta`) usado por `fetch_transfers_api` y `fetch_sede_transfers_api`, `_enrich_transfer_items` con `resolution` por item y `totals.items_resolved`, `_json_safe` con `format_timestamps`, `_clean_udm`. Sede: `get_sede_movement_api`; `_row_to_movement` / `_row_to_inventory` limpian `udm`. |
| **DB** | [`warehouses_controller.py`](../templates/controllers/product/warehouses_controller.py) | Sin cambios: el reingreso reutiliza `insert_warehouse_movement_db(None, …)` + `update_stock_db(just_add=True)` (la misma pareja de la reversa de cancelar) y la resolución se guarda con `update_transfer_fields_db`. |
| **Modelos** | [`api_multisede_models.py`](../static/Models/api_multisede_models.py) | `transfer_resolve_model` (+ `transfer_resolve_item_model`) / `TransferResolveForm` (solo `comment`; `items` lo valida el midleware). |

### Reglas de la resolución

- Solo un traslado en **status 2**; `404` inexistente, `400` en cualquier otro status (incluido el 4: se resuelve **una sola vez**). Permiso `almacen` (el administrador pasa siempre).
- **Faltante** por renglón = `quantity_sent − quantity_received > 0`. El body debe traer **exactamente** esos productos (faltan o sobran → `400`), cada uno con `action` ∈ `reingreso | merma`; `comment` por renglón y general opcionales.
- **`reingreso`**: una **entrada** en el kardex del principal (`id_warehouse NULL`) por la diferencia, fecha = ahora, `extra_info {reference: folio, id_transfer, resolution: "reingreso", comment: "Reingreso por diferencia del traslado TRS-####[: comentario]", user}` + `products_amc.stock += diferencia`. En `GET /almacen/kardex` aparece con `reference` = folio.
- **`merma`**: **no** crea movimiento (el stock ya salió del principal al enviar y nunca entró a la sede); solo queda registrada en el traslado.
- Persistencia: `items[i].resolution = {action, quantity, comment, movement_id | null, user, timestamp}`, `history += {action: "Resolución de diferencias", user, timestamp, comment}` y `status = 4`. Los ids de usuario (`created_by`, `received_by`, `history[].user`, `resolution.user`) **se quedan como ids**: no se resuelven nombres.
- Sin transacciones entre llamadas (mismo patrón de F3): reingresos → cierre del traslado; si algo falla, los reingresos se borran y el stock se devuelve, el traslado sigue en 2 y responde `400` con el detalle. Notifica a `sucursal-<dest>`.
- `GET /almacen/inventory/consolidated` ya no cuenta como `in_transit` nada de un traslado 2/4 (solo status 0), así que el stock total vuelve a cuadrar tras un reingreso.

### Formatos (aplican a traslados, sedes y movimientos de sede)

- Todas las fechas/timestamps salen con `format_timestamps` (`YYYY-MM-DD HH:MM:SS`, con espacio). Antes `created_at` de traslados y sedes salía con `T` (`isoformat`) y `received_at` con espacio.
- `udm` sin espacios al final (`"PIEZA"`, antes `"PIEZA "`) en items de traslado, kardex de sede (`products[id].udm`), `GET /sucursal/movement/<id>` e inventario de sede / principal vía `/sucursal`. El consolidado y los endpoints viejos de `/almacen` no cambian.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`); `401` si falta o no tiene el permiso del namespace. Envelope `{data, msg, error}` (+ `meta` en listados). Status: `0` EN TRÁNSITO · `1` RECIBIDO · `2` RECIBIDO CON DIFERENCIAS · `3` CANCELADO · **`4` DIFERENCIA RESUELTA** (también en `GET /almacen/warehouses/catalogs` → `transfer_status`).
- **Principal**: base `/GUI/api/v1/almacen`, permiso `almacen` (administrador siempre). **Sede**: base `/GUI/api/v1/sucursal`.

### `PUT /almacen/transfer/<id_transfer>/resolve`

Body `{"items": [{"id_product": 1, "action": "reingreso", "comment": "regresó en el 2do camión"}, {"id_product": 2, "action": "merma", "comment": "se dañó"}], "comment": "resuelto por QA"}` — **todos** los productos con `difference < 0` del traslado, ninguno más; `comment` opcionales.

```json
// 200 — el traslado completo, mismo shape que GET /almacen/transfer/<id>
{"data": {"id_transfer": 7, "folio": "TRS-0007", "id_warehouse_origin": 1, "origin_name": "Almacén Principal", "id_warehouse_dest": 2, "dest_name": "Sucursal 2",
          "status": 4, "status_label": "DIFERENCIA RESUELTA", "comment": "camión 1", "created_by": 36, "received_by": 34,
          "created_at": "2026-10-16 09:12:00", "received_at": "2026-10-16 11:40:00",
          "items": [{"id_product": 1, "sku": "10010000001", "name": "ABRAZADERA CLIP 1/2", "udm": "PIEZA", "quantity_sent": 3.0, "quantity_received": 1.0, "difference": -2.0,
                     "comment": "caja 1", "receive_comment": "faltaron 2",
                     "resolution": {"action": "reingreso", "quantity": 2.0, "comment": "regresó en el 2do camión", "movement_id": 6999, "user": 36, "timestamp": "2026-10-16 12:05:10"}},
                    {"id_product": 2, "sku": "10010000002", "name": "ABRAZADERA UNICANAL 1/2\"", "udm": "PIEZA", "quantity_sent": 2.5, "quantity_received": 1.5, "difference": -1.0,
                     "comment": "", "receive_comment": "",
                     "resolution": {"action": "merma", "quantity": 1.0, "comment": "se dañó", "movement_id": null, "user": 36, "timestamp": "2026-10-16 12:05:10"}},
                    {"id_product": 3, "sku": "10010000003", "name": "...", "udm": "PIEZA", "quantity_sent": 2.0, "quantity_received": 2.0, "difference": 0.0, "comment": "", "receive_comment": "", "resolution": null}],
          "totals": {"items": 3, "quantity_sent": 7.5, "quantity_received": 4.5, "items_with_difference": 2, "items_resolved": 2},
          "history": [{"timestamp": "2026-10-16 09:12:00", "user": 36, "action": "Envío", "comment": "..."},
                      {"timestamp": "2026-10-16 11:40:00", "user": 34, "action": "Recepción", "comment": "..."},
                      {"timestamp": "2026-10-16 12:05:10", "user": 36, "action": "Resolución de diferencias", "comment": "Faltantes resueltos (producto 1: reingreso x2; producto 2: merma x1). resuelto por QA."}]},
 "msg": "Traslado TRS-0007 (DIFERENCIA RESUELTA): producto 1: reingreso x2; producto 2: merma x1; 1 reingreso(s) al principal [emp 36]", "error": null}
```
```json
// 400 status distinto de 2 (en tránsito, recibido exacto, cancelado o ya resuelto)
{"data": null, "msg": "El traslado TRS-0007 está en DIFERENCIA RESUELTA: solo se resuelve en RECIBIDO CON DIFERENCIAS", "error": null}
// 400 items incompletos / de más
{"data": null, "msg": "faltan los productos con diferencia [2]", "error": null}
{"data": null, "msg": "los productos [3] no tienen diferencia en este traslado", "error": null}
// 400 action / estructura
{"data": null, "msg": "items[0] (producto 1): action inválida 'devolver' (reingreso | merma)", "error": null}
{"data": null, "msg": "items[0]: id_product y action son obligatorios", "error": null}
{"data": null, "msg": "El producto 1 viene repetido en items", "error": null}
{"data": null, "msg": "items debe ser una lista con la acción por producto faltante", "error": null}
// 400 falla a la mitad (se revirtió, sigue en status 2): {"data": null, "msg": "La resolución del traslado TRS-0007 falló y se revirtió (...)", "error": "<detalle>"}
// 404 {"data": null, "msg": "No existe el traslado 999", "error": "No encontrado"}
// 401 sin permiso almacen (un token solo de sede también da 401): {"error": "No autorizado. Token invalido"}
```
`items[].resolution` y `totals.items_resolved` ya vienen (en `null` / `0`) en **todos** los `GET` de traslados (principal y sede) desde ahora; `difference` no cambia tras resolver (sigue siendo recibido − enviado). La UI de seguimiento: `status 2` → botón "resolver" con un renglón por item con `difference < 0`; `status 4` → mostrar `resolution.action` por renglón.

### `GET /sucursal/movement/<id_movement>`

Lectores: permiso `Sucursal-<sede del movimiento>`, o `almacen` / `administracion` / administrador. `data.movement` tiene **exactamente las mismas llaves y valores** que una fila de `data.movements` en `GET /sucursal/movements/<type_m>`; el producto va aparte en `data.product` (como `products[id]` del listado).
```json
// 200
{"data": {"warehouse": {"id_warehouse": 2, "name": "Sucursal 2"},
          "movement": {"id_movement": 6914, "id_product": 1, "movement_type": "entrada", "quantity": 1.0, "movement_date": "2026-10-16 11:40:00", "sm_id": null, "id_warehouse": 2,
                       "reference": "TRS-0007", "comment": "faltaron 2", "user": 34, "id_transfer": 7, "editable": false,
                       "extra_info": {"reference": "TRS-0007", "id_transfer": 7, "comment": "faltaron 2", "user": 34}},
          "product": {"sku": "10010000001", "name": "ABRAZADERA CLIP 1/2", "udm": "PIEZA"}},
 "msg": null, "error": null}
// 403 movimiento de otra sede: {"data": null, "msg": "Sin permiso para operar la sede 3", "error": null}
// 404 {"data": null, "msg": "No existe el movimiento 999999", "error": "No encontrado"}
// 400 movimiento del principal (id_warehouse NULL): {"data": null, "msg": "El movimiento 6999 es de la sede principal: se edita por /almacen", "error": null}
// 401 token sin sucursal/almacen/administracion
```

### `meta` en `GET /almacen/transfers` y `GET /sucursal/transfers`

Mismos filtros de siempre (`status` ahora `0..4`; `limit` default 200, máx 2000). Se pide `limit + 1` a la BD: si vuelve la fila de más, `truncated: true` y `msg` termina en "(recortado al tope)". Las devueltas son las más recientes; para el resto, acotar `date_to`.
```json
// GET /almacen/transfers?limit=1
{"data": [ {"...objeto traslado..."} ], "meta": {"limit": 1, "returned": 1, "truncated": true}, "msg": "1 traslados (recortado al tope)", "error": null}
// GET /sucursal/transfers (sede)
{"data": {"warehouse": {"id_warehouse": 2, "name": "Sucursal 2"}, "transfers": [ ... ]}, "meta": {"limit": 200, "returned": 3, "truncated": false}, "msg": "3 traslados (1 en tránsito)", "error": null}
// 400 {"data": null, "msg": "status inválido: 5 (0..4)", "error": null} · {"data": null, "msg": "limit inválido: abc", "error": null}
```

### Gotchas

- `created_at` / `received_at` / `history[].timestamp` / `resolution.timestamp` / `movement_date`: siempre `YYYY-MM-DD HH:MM:SS` (antes `created_at` traía `T`). `udm` ya viene sin espacios: quitar los `.trim()` defensivos no hace daño, dejarlos tampoco.
- Los ids de usuario no se resuelven a nombres en ningún campo de traslados; si la UI necesita el nombre, lo toma del catálogo de empleados que ya consume.
- Un traslado en `4` **no** se cancela ni se vuelve a recibir ni a resolver. La merma no deja huella en el kardex del principal: para auditoría se consulta el traslado (`resolution`), no el kardex.
- `GET /almacen/kardex`: la entrada de reingreso trae `reference` = folio `TRS-####` (el `extra_info->'$.reference'`), igual que las salidas del envío y las entradas de reversa de una cancelación; se distinguen por `movement_type` y, en la fila de BD, por `extra_info.resolution`.

## Verificación

Dev (2026-10-16, `Tests/tester_multisede_resolve.py`, 64 checks, 3 productos temporales `TST-RES-*` y 2 traslados hacia la sede 2 borrados al final junto con sus movimientos, stock de sede y notificaciones): alta de dos traslados y descuento del principal; `resolve` en tránsito / inexistente / token de sede / `basic` → `400`/`404`/`401`; recepción con diferencias (status 2, 3 entradas en la sede, `received_at` con formato) y exacta (status 1); detalle con fechas con espacio, `udm` limpio, ids de usuario, `history` con formato, `resolution: null`, `items_with_difference 2`; `400` por faltante, sobrante, action inválida, repetido, vacío, sin action y en status 1 (sin tocar stock); `resolve` OK → status 4, **mismo shape** (llaves) que `GET /transfer/<id>`, `resolution` de reingreso con `movement_id` y de merma sin él, `items_resolved 2`, history, stock del principal +2 solo en el reingreso, un único movimiento nuevo en el principal (entrada x2, `id_warehouse NULL`, `extra_info.id_transfer/reference/resolution`) visible en `GET /almacen/kardex`; segundo `resolve` → `400`; la sede ve el status 4; `meta` con `limit=1` → `truncated` en ambos listados, `status=5` y `limit=abc` → `400`, catálogo con el 4; `GET /sucursal/movement/<id>`: mismas llaves y valores que la fila del kardex, `product` con `udm` limpio, `almacen` lee, sede ajena `403`, inexistente `404`, movimiento del principal `400`, `basic` `401`; `udm` limpio en kardex e inventario de sede. `pyrefly check` sobre los 5 archivos tocados: 1 error pre-existente (`rs_Almacen.py:654`, `send_file`), ninguno nuevo; `app` importa y registra las 2 rutas nuevas.

## Al modificar

- **Acción nueva de resolución** (p. ej. "reenvío"): agregar a `RESOLVE_ACTIONS`, su rama en el `for` de `resolve_transfer_api` (si crea movimiento, seguir la pareja `insert_warehouse_movement_db` + `update_stock_db` y registrar el id en `resolution.movement_id` para la reversa) y este doc.
- **Resolución parcial / por partes**: hoy exige todos los faltantes de una vez y cierra en 4. Para resolver por renglón habría que saltar los items ya resueltos (`pending` ya ignora los que traen `resolution`) y mover el status a 4 solo cuando no quede ninguno pendiente.
- **Status nuevo** → `WH_TRANSFER_STATUS` (catálogo, labels, rango del filtro `status` y `_RECEIVED_STATUSES` si la sede ya confirmó en ese status).
- **Campo nuevo en `resolution`** → solo el dict de `resolve_transfer_api` y este contrato; es JSON dentro de `items`, sin DDL.
- **Default o tope del listado** → `TRANSFERS_DEFAULT_LIMIT` / `TRANSFERS_MAX_LIMIT` en `MD_Multisede.py` (lo comparten principal y sede vía `query_transfers`).
- **Formato de fechas**: todo pasa por `_json_safe` de `MD_Multisede.py` (traslados, sedes) y `MD_Sucursal.py` (movimientos). No volver a `isoformat()` en datetimes.

## Pendientes

- **[front]** Pantalla de seguimiento del principal: resolver `status 2` (un renglón por faltante con `reingreso | merma`) y mostrar `resolution` en `status 4`; consumir `meta.truncated` en los listados.
- **[admin]** Quién captura la resolución en el principal (`P-047` queda cerrado en el back con este endpoint; el procedimiento lo define administración).
