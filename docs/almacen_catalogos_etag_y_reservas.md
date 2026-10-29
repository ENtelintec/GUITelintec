# Catálogos con ETag, reservas con filtro y consolidado acotado — `GET /sm/products/<contract>` (+ inventario, reservas, consolidado)

Fecha: 2026-10-28 · **Estado: hecho y verificado contra dev (50/50 `Tests/tester_catalogos_etag_reservas.py`; las reservas, con token de tester contra la BD de test, solo lectura). Regresión en verde: kardex ETag 54/54, lecturas completas 27/27, permisos de almacén 18/18 y de SM 10/10, multisede resolve 64/64.**

Son los cuatro listados sin tope que dejó [`almacen_lecturas_completas.md`](almacen_lecturas_completas.md) (`P-201` a `P-204`). Decisiones del usuario del 2026-10-28:

| Pendiente | Endpoint | Decisión | Cambia contrato |
|---|---|---|---|
| `P-204` | `GET /sm/products/<contract>` | **ETag + 304**, como el kardex | no |
| `P-202` | `GET /almacen/inventory/products/<type_p>`, `GET /sucursal/inventory`, `GET /sucursal/inventory/main` | **ETag + 304** | no |
| `P-201` | `GET /almacen/reservations` | **`?status=` y `?limit=` opcionales + `meta`**; el default sigue siendo "todas" (hasta el tope) | solo agrega `meta` y dos parámetros opcionales |
| `P-203` | `GET /almacen/inventory/consolidated` | **sin `search`, aplica `only_multisede`**; el catálogo completo con `all=1` | sí, el default (el front todavía no lo usa) |

Sin DDL.

## ETag + 304 (`P-204`, `P-202`)

El mismo mecanismo de [`almacen_kardex_etag.md`](almacen_kardex_etag.md): ETag débil con la huella `blake2b` del cuerpo y `Cache-Control: private, no-cache`. Solo los 200 lo llevan. Si el navegador manda `If-None-Match` y coincide, la respuesta es 304 sin cuerpo y `fetch` le entrega a JS el 200 que tenía guardado. La BD se sigue consultando en cada carga: el ahorro es de red (en prod, 61 KB comprimidos del formulario de SM y 84 KB del inventario por carga).

La función se movió de `MD_Kardex.kardex_conditional` a [`methods/Functions_Aux_Http.py`](../templates/resources/methods/Functions_Aux_Http.py) con el nombre `etag_conditional`, porque ya no es solo del kardex. `kardex_conditional` se queda como alias.

**Orden de las filas:** las dos consultas de productos (`get_products_w_reservations`, `get_all_products_db_tool_internal`) no tienen `ORDER BY`. No se les agregó porque seleccionan columnas JSON (`codes`, `locations`, `extra_info`), y ordenar las metería al sort buffer (regla de [`contracts_products_sort_memory_fix.md`](contracts_products_sort_memory_fix.md)). El orden lo da el plan de la consulta, y el tester comprueba que el ETag es estable entre llamadas. Si un día cambiara de una llamada a otra, solo se perdería el 304: nunca se sirven datos viejos.

## Reservas (`P-201`)

| Parámetro | Regla |
|---|---|
| `status` | entero opcional (`0` = pendiente, el que usan SM y los traslados). Sin él, todas. No entero → 400. |
| `limit` | entero opcional, se ajusta a `1..1000`; default `1000`. Más recientes primero (`reservation_id DESC`). No entero → 400. |
| `meta` | `{"status", "returned", "limit", "truncated"}`. La consulta pide `limit + 1` filas para saber si recortó. |

El `ORDER BY reservation_id DESC` va sobre la llave primaria con `LIMIT`, así que MySQL recorre el índice y no ordena el `history` JSON en el buffer.

## Consolidado (`P-203`)

| Request | Qué devuelve |
|---|---|
| sin parámetros | solo productos con stock en alguna sede secundaria o en tránsito (`only_multisede`); `msg` termina en `(solo con stock en sedes o en tránsito)` |
| `all=1` | el catálogo completo, con las dos subconsultas por producto |
| `search=<texto>` | lo que coincide por sku o nombre, sin `only_multisede` |
| `only_multisede=1` | siempre aplica, aunque vengan `search` o `all` |

Hoy en dev y en test ningún producto tiene stock de sede, así que el default responde 0 productos (el completo: 1,234 en dev y 1,121 en test). El filtro es la misma condición SQL de `only_multisede=1` que se verificó en F1 ([`almacen_multisede_f1.md`](almacen_multisede_f1.md)).

## Capas tocadas

```
methods     resources/methods/Functions_Aux_Http.py        (nuevo) etag_conditional (antes MD_Kardex.kardex_conditional, que queda como alias)
routes      rs_SM.py                                        GET /products/<contract> con ETag
            rs_Almacen.py                                   GET /inventory/products/<type_p> con ETag · /reservations lee status y limit · /inventory/consolidated lee all · kardex con etag_conditional
            rs_Sucursal.py                                  GET /inventory y /inventory/main con ETag · kardex de sede con etag_conditional
midleware   Functions_midleware_almacen.py                  get_reservations_db(params, data_token) + meta
            MD_Multisede.py                                 get_consolidated_inventory_api: default only_multisede sin search
controller  controllers/product/reservations_controller.py  get_all_reservations(status, limit, data_token): param-or-NULL + LIMIT
```

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Respuestas: JSON `{data, msg, error}`; 401 `{"error": "..."}` sin envelope.
- **Permisos exactos** (sin cambio; `App.Department.Administrator` siempre pasa):
  - `GET /GUI/api/v1/sm/products/<contract>`: `App.Department.SM`, `App.Department.SM-URGENT`.
  - `GET /GUI/api/v1/almacen/inventory/products/<type_p>` y `/almacen/inventory/consolidated`: `App.Department.ALMACEN`, `App.Department.ALMACEN-VISUAL`.
  - `GET /GUI/api/v1/almacen/reservations`: `App.Department.ALMACEN`, `App.Department.ALMACEN-VISUAL`, `App.Department.Administracion`.
  - `GET /GUI/api/v1/sucursal/inventory` y `/sucursal/inventory/main`: `App.Department.Sucursal-<id>` de la sede, o `App.Department.ALMACEN`, `App.Department.ALMACEN-VISUAL`, `App.Department.Administracion`.

### ETag (SM, inventario, sucursal): el front no cambia

`200` con `ETag: W/"…"` y `Cache-Control: private, no-cache` · `304` sin cuerpo cuando el navegador manda `If-None-Match` y no hubo cambios (en JS, `response.status` es `200` y `response.json()` trae el cuerpo guardado) · `400`/`401` sin `ETag`. No usar `cache: "no-store"`, `cache: "reload"` ni parámetros anti-caché (`?_=timestamp`): con ellos el navegador no manda `If-None-Match`.

### `GET /almacen/reservations?status=0&limit=200`

```json
// 200
{"data": [{"reservation_id": 12, "id_product": 301, "id_sm": 88, "quantity": 4, "status": 0, "history": [...], "folio": "SM-0088"}],
 "msg": null, "error": null,
 "meta": {"status": 0, "returned": 1, "limit": 200, "truncated": false}}
// 400
{"data": [], "msg": "Filtro inválido", "error": ["status y limit deben ser enteros"]}
```

Sin parámetros responde como antes (todas, hasta 1,000) más `meta`. Para la pantalla de reservas: pedir `?status=0` por defecto y avisar si `meta.truncated` es `true` (`P-201`, front).

### `GET /almacen/inventory/consolidated`

Sin parámetros ya **no** trae el catálogo completo: solo lo que tiene stock en sedes o en tránsito. Para la vista completa, `?all=1`; para buscar, `?search=`. El resto del shape no cambia. `msg`: `"0 productos (solo con stock en sedes o en tránsito)"` o `"1234 productos"`.

## Al modificar

- **Otro GET que se recargue seguido**: `return etag_conditional(data_out, code, request.if_none_match)` en el Resource y `responses={304: ...}` en el `@ns.doc`. No meter en el cuerpo nada que cambie en cada llamada (hora de generación, contadores).
- **Otro listado sobre una tabla que crece**: `limit` + 1 en la consulta y `meta.truncated`, como aquí y en el kardex.
- **Si el consolidado necesita paginar** cuando multisede crezca: `limit`/`offset` sobre `ORDER BY p.name`; hoy no hace falta.

## Al desplegar

Comprobar a través de nginx, con un token de lectura: `curl -sD - -o /dev/null -H "Authorization: <jwt>" -H "Accept-Encoding: gzip" https://appinterna.telintec.mx/GUI/api/v1/almacen/inventory/products/all` debe traer `ETag: W/"…"`; repetirlo con `-H 'If-None-Match: W/"…"'` debe dar `304`. Lo mismo con `/sm/products/all` y un token con `SM`.
