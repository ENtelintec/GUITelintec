# Kardex acotado por fecha — `GET /almacen/kardex`, `/kardex/epp` y ventana en `/sucursal/movements`

> Grill 2026-10-12. Los GET de movimientos del principal (`/movements/<type_m>`, `/movements/epp/<type_m>`) traen **todo el histórico** en cada refresco (prod: 18,209 filas ≈ 5.4 MB planos; ~930 movimientos nuevos al mes). Este cambio sirve un kardex nuevo acotado por fecha con tope de filas y el producto normalizado fuera de cada movimiento, alinea el kardex de sede a la misma ventana y mueve a SQL el filtro de fechas de las descargas PDF/Excel. Los endpoints viejos quedan intactos y **deprecados** hasta que el front migre (`P-126`). Va junto con el pool de conexiones ([`db_connection_pool.md`](db_connection_pool.md)) y un índice compuesto para revisión (`P-127`).

## Decisiones (grill)

| Decisión | Resultado |
|---|---|
| Alcance | Kardex principal + EPP, descargas PDF/Excel y kardex de sede. |
| Compatibilidad | **Endpoint nuevo** (`/kardex`, prefijo que no choca con `/movements/<type_m>`); los viejos no cambian. Misma info por fila, reorganizada. |
| Ventana por defecto | **3 meses calendario** (`relativedelta(months=3)`) anclados en `date_to` si viene, si no en hoy (`America/Mexico_City`). 6 meses eran 5,590 filas en prod (1.6 MB y por encima del tope). |
| Histórico antiguo | Solo con `date_from` explícito. No hay `all=1`. |
| Tope | `limit` opcional, **máx y default 5,000**; `meta.truncated` avisa (se piden `limit + 1` filas, exacto). Sede pierde su default 500. |
| Forma de `data` | **Normalizada**: `movements` solo con campos del movimiento + `products` por `id_product` (medido en dev: 294 → 185 B/fila; columnar no valía la pena tras gzip). |
| gzip | Lo hace **nginx** en prod (verificado por el usuario, `application/json` incluido). No se agrega `flask-compress`. |
| Descargas | Mismo contrato; el rango `date_init`/`date_end` va a SQL. Sin tope: son archivos. |

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Almacen.py`](../templates/resources/rs_Almacen.py) | `GET /kardex` (`almacen`) y `GET /kardex/epp` (`epp`), query params `type_m`, `date_from`, `date_to`, `limit`. `@ns.deprecated` en `GET /movements/<type_m>` y `GET /movements/epp/<type_m>`. [`rs_Sucursal.py`](../templates/resources/rs_Sucursal.py): solo la doc de params. |
| **Orquestación** (nuevo) | [`MD_Kardex.py`](../templates/resources/midleware/MD_Kardex.py) | `resolve_kardex_window` (parseo estricto `YYYY-MM-DD`, ventana por defecto, `limit` acotado) → `KardexWindow`; `kardex_meta` (recorte a `limit` + bloque `meta`); `get_kardex_api` (principal/EPP, normaliza producto). [`MD_Sucursal.py`](../templates/resources/midleware/MD_Sucursal.py): `get_sede_movements_api` usa la misma ventana y saca `sku`/`name`/`udm` a `data.products`. [`Functions_midleware_almacen.py`](../templates/resources/midleware/Functions_midleware_almacen.py): `retrieve_data_movement_file` pasa el rango a la BD. |
| **DB** | [`movements_controller.py`](../templates/controllers/product/movements_controller.py) | `get_kardex_main_db` (nueva); `get_all_movements_db_detail` / `get_epp_movements_db_detail` aceptan `date_from`/`date_to` (`_date_range_sql`). [`warehouses_controller.py`](../templates/controllers/product/warehouses_controller.py): `get_warehouse_movements_db` con cota exclusiva en vez de `DATE()`. |
| **Modelos** | — | Sin forms: todo es query string. |

### Reglas

- **Predicados sobre la columna, nunca `DATE(movement_date)`**: `movement_date >= 'YYYY-MM-DD 00:00:00' AND movement_date < 'día siguiente 00:00:00'` (inclusivo para el usuario, sargable para MySQL). Así en el kardex, en la sede y en las descargas (`<= 23:59:59`).
- `date_from` siempre llega resuelto al controlador (explícito o por defecto); `date_to` puede ser `None` (sin cota superior).
- `id_product` del movimiento es el de la tabla de movimientos (`m.id_product`), **no** el del `LEFT JOIN` como en el viejo: un movimiento de un producto borrado trae su id real y `products[id]` con `sku`/`supplier`/`sku_fabricante`/`description` en `null`. En dev son 2,491 movimientos (665 en la ventana por defecto) que el viejo devolvía con `id_product: null`.
- `type_m` inválido → `400` (el viejo lo trataba como `all`).
- Descargas: el `INNER JOIN` con `products_amc` que ya existía sigue dejando fuera los movimientos de productos borrados (mayo 2026 en dev: 936 movimientos, 731 en el Excel). No es de este cambio; se anota para no perseguirlo de nuevo.
- `meta.default_window: true` = el front no mandó `date_from`: si la tabla sale vacía, ofrecer "ver más antiguos" en vez de "sin movimientos".

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`; `jwt.decode` sobre el header tal cual). Base `/GUI/api/v1/almacen` (sede: `/GUI/api/v1/sucursal`). Envelope `{data, msg, error}` **+ `meta`** (llave hermana, solo en estos GET). Todo query string; sin body.
- Códigos: `200` · `400` validación (`data: null`, el motivo en `msg`) · `401` token / sin permiso (`almacen` para `/kardex`, `epp` para `/kardex/epp`).
- **Migración desde `/movements/<type_m>`**: `GET /movements/all` → `GET /kardex` (o `?type_m=entrada|salida`); `GET /movements/epp/all` → `GET /kardex/epp`. La fila vieja se reconstruye como `{...movement, ...products[movement.id_product]}` (verificado campo a campo en dev, salvo `id_product` de productos borrados, ver Reglas). Pedir rangos explícitos solo cuando el usuario lo pida; no recorrer todo el histórico en bucle.

### `GET /kardex?type_m=&date_from=&date_to=&limit=` · `GET /kardex/epp?...`

| Param | Tipo | Default | Notas |
|---|---|---|---|
| `type_m` | `entrada` \| `salida` \| `all` | `all` | Otro valor → `400`. |
| `date_from` | `YYYY-MM-DD` | `date_to` (o hoy) − 3 meses calendario | Inclusivo. Para histórico antiguo mandarlo explícito. |
| `date_to` | `YYYY-MM-DD` | sin cota | Inclusivo (hasta 23:59:59). `date_from > date_to` → `400`. |
| `limit` | int | 5000 | Se acota a `1..5000`; no entero → `400`. |

```json
// 200
{"data": {
   "movements": [
     {"id": 18692, "id_product": 2088, "type_m": "salida", "quantity": 2.0,
      "movement_date": "2026-10-09 10:35:53", "sm_id": 1532, "reference": "SM-1532"}
   ],
   "products": {
     "2088": {"sku": "10010002088", "supplier": "TRUPER", "sku_fabricante": "TR-1234", "description": "ABRAZADERA CLIP 1/2"}
   }},
 "meta": {"date_from": "2026-07-12", "date_to": null, "default_window": true, "limit": 5000, "count": 2517, "truncated": false},
 "msg": "2517 movimientos del 2026-07-12 al hoy", "error": null}
```
- Las llaves de `products` son **strings** (JSON) aunque `id_product` sea entero.
- `truncated: true` = había más filas que `limit` dentro de la ventana; las devueltas son las más recientes. `msg` termina en "(recortado al tope)". Para traer el resto: acotar `date_to` a la fecha más antigua recibida.
- `GET /kardex?date_to=2026-05-31` → ventana `2026-02-28..2026-05-31` (`default_window: true`).

```json
// 400
{"data": null, "msg": "date_from inválida: '2026-13-01' (formato YYYY-MM-DD)", "error": null}
{"data": null, "msg": "type_m inválido: 'entradas' (entrada | salida | all)", "error": null}
// 401
{"data": null, "msg": null, "error": "No autorizado. Token invalido"}
```

### `GET /sucursal/movements/<type_m>?date_from=&date_to=&limit=[&id_warehouse=]`

Misma ventana, mismos `400` y mismo `meta`. `data` conserva `warehouse` y gana `products`; cada movimiento **deja de traer** `sku`, `name`, `udm` (van en `products[id_product]`) y conserva el resto (`reference`, `comment`, `user`, `id_transfer`, `editable`, `extra_info`, `id_warehouse`).
```json
{"data": {"warehouse": {"id_warehouse": 2, "name": "Sucursal 2"},
          "movements": [{"id_movement": 6876, "id_product": 1, "movement_type": "salida", "quantity": 2.5, "movement_date": "2026-09-01 00:00:00",
                         "sm_id": null, "id_warehouse": 2, "reference": "FAC-1", "comment": "inicial", "user": 34, "id_transfer": null, "editable": true,
                         "extra_info": {"reference": "FAC-1", "comment": "inicial", "user": 34}}],
          "products": {"1": {"sku": "10010000001", "name": "ABRAZADERA CLIP 1/2", "udm": "PIEZA "}}},
 "meta": {"date_from": "2026-07-12", "date_to": null, "default_window": true, "limit": 5000, "count": 1, "truncated": false},
 "msg": "1 movimientos del 2026-07-12 al hoy", "error": null}
```

### Descargas `POST /file/download/movements/{pdf,excel}` y `eppmovements/*`

Sin cambio de contrato (`{"date_init", "date_end", "type"}`, blob en `200`, envelope JSON en `4xx`); solo cambia que la BD ya no entrega la tabla completa.

## Verificación

Dev (2026-10-12, con datos actualizados de prod: 18,209 movimientos; 31 checks con `app.test_client()`): kardex default = las 2,517 filas del viejo con fecha ≥ hoy−3m, reconstrucción `{...movement, ...products[id]}` igual campo a campo (665 difieren solo en `id_product` null del viejo), orden por fecha desc, rango explícito de mayo (`salida`: 514 = 514), `date_to` inclusivo, ventana anclada en `date_to`, `limit=10` → `truncated`, `limit=99999` → 5,000 recortado, `limit=0` → 1, los cinco `400` de validación, `401` sin token y `/kardex/epp` con token solo `almacen`, EPP = viejo EPP en ventana (123 = 123), sede con `products` + `meta` y sin campos de producto en cada fila, Excel/PDF de mayo (EPP 47 = 47; principal 731 por el `INNER JOIN` previo), fechas del Excel dentro del rango. **Peso**: 5,253,119 B (viejo) → 516,657 B (kardex default), 9.8 %. `pyrefly check`: 184 → 178 errores (ninguno en lo tocado). `EXPLAIN` actual: `idx_movements_warehouse` + filesort (9,148 filas leídas); el índice compuesto queda en `P-127`.

## Al modificar

- Un campo nuevo del movimiento va en `get_kardex_main_db` + el dict de `get_kardex_api`; uno del producto va en `products` (una vez por id), nunca en cada movimiento.
- Cambiar meses o tope: `KARDEX_DEFAULT_MONTHS` / `KARDEX_MAX_LIMIT` en `MD_Kardex.py` (los tres GET los comparten). Si el tope sube, revisar que un trimestre de prod siga cabiendo (hoy ≈ 2,800 filas).
- No volver a `DATE(movement_date)` en un `WHERE`: mata el índice. Cota superior siempre exclusiva al día siguiente.
- Los viejos `/movements/*` se retiran cuando el front confirme `P-126` (quitar rutas + `get_all_movements` / `get_epp_movements` + `get_movements_type_db_all` / `get_epp_movements_db`).

## Notas posteriores

- **2026-10-12** — La primera versión del DDL usaba `PREPARE ... FROM @sql` para ser re-ejecutable; tras una corrida en dev que no dejó el índice (cotejadas las 3 BDs en solo lectura: ninguna lo tenía), se reescribió con sentencias planas (`ADD INDEX` y luego `DROP INDEX idx_movements_warehouse`, en ese orden por la FK `fk_movements_warehouse`). **No es re-ejecutable** (1061 / 1091 en una segunda corrida); el paso 0 del script muestra el estado antes de correr.
- **2026-10-12 (dev)** — DDL corrido una vez: `idx_movements_warehouse_date` presente, `idx_movements_warehouse` fuera, FK `fk_movements_warehouse` intacta. `EXPLAIN` del principal: `range`, 2,517 filas leídas (= devueltas), `Backward index scan`, sin filesort; el optimizador elige `idx_movement_date` para `id_warehouse IS NULL` y el compuesto para la sede (`id_warehouse = 2`). Batería 31/31 sobre el índice nuevo.
- **2026-10-12 (test y prod)** — DDL corrido por el usuario; cotejadas las 3 BDs en solo lectura con el mismo esquema (compuesto presente, viejo fuera, FK intacta). `P-127` cerrado. En prod el `GET /movements/<type_m>` viejo también se beneficia: `ref` sobre el compuesto con `Backward index scan` y sin filesort (8,676 filas estimadas); un índice no altera resultados, solo el plan, así que el front actual no nota nada.

- **2026-10-16** (`P-126`): el front ya consume el kardex en las 3 pantallas (Movimientos, Entrada, Salida, con barra de rango) y pidió retirar `GET /movements/<type_m>` y `/movements/epp/<type_m>`. **Decisión del usuario: no se retiran hasta que confirme el despliegue** del front en prod; siguen deprecados en swagger e intactos.
