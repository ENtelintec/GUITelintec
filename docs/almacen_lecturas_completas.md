# Auditoría de lecturas completas en `controllers/product` — `GET /almacen/codes/generate`

> `P-129`, decidido en el grill del 2026-10-27 ([`plan_back_sin_bloqueo_2026_10_27.md`](planes/plan_back_sin_bloqueo_2026_10_27.md)). Viene de [`almacen_kardex_ventana.md`](almacen_kardex_ventana.md), que acotó el kardex y dejó pendiente revisar el resto. Revisé las **46 funciones con SELECT** de [`templates/controllers/product/`](../templates/controllers/product/) para separar los catálogos legítimos de los listados que crecen sin tope. Los arreglos que no cambian contrato quedaron hechos: el código nuevo de SKU se calcula en la BD (lee 1 fila en vez de la tabla) y se borraron 8 funciones sin llamadas. Los listados que necesitan cambiar de contrato quedaron como pendientes nuevos, cada uno con su parte de front: `P-201` a `P-204`. Sin DDL.

## Decisiones (grill)

| Decisión | Resultado |
|---|---|
| Alcance | Las lecturas de `controllers/product` (movimientos, productos, reservas, sedes). Las entradas de la conciliación de OC ya se acotaron con `P-115` ([`po_match_cantidades.md`](po_match_cantidades.md)). |
| Arreglos sin cambio de contrato | `get_last_sku` lee una fila; se borran las 6 funciones con SELECT sin llamadas y las 2 auxiliares sin llamadas (`Aux_Inventory.fetch_all_movements`, `Functions_AuxFiles.get_all_sm_products`). |
| Listados que cambiarían contrato | Pendientes nuevos con su parte de front: reservas, inventario con `LIKE '%'`, consolidado y productos de SM. |
| Chatbot | Las funciones que solo usa `Functions_tools_openAI.py` **no se tocan** (archivos de OpenAI congelados). |

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | — | Sin cambios. |
| **Orquestación** | [`Functions_midleware_almacen.py`](../templates/resources/midleware/Functions_midleware_almacen.py) | `get_new_code_products` toma el máximo de `get_max_sku_number` en vez de recorrer todos los SKU en Python. |
| **DB** | [`products_controller.py`](../templates/controllers/product/products_controller.py) | `get_last_sku` (`SELECT sku ... ORDER BY sku DESC`, toda la tabla) → `get_max_sku_number(skip_chars)`: `MAX(CAST(SUBSTRING(sku, 5) AS UNSIGNED))` solo sobre los sufijos de puros dígitos (`REGEXP '^[0-9]+$'`), una fila. Borradas `get_all_suppliers` y `get_stock_db_products`. |
| | [`movements_controller.py`](../templates/controllers/product/movements_controller.py) | Borradas `get_ins_db`, `get_outs_db`, `get_outs_db_detail` y `get_movements_type_db`. |
| | [`Aux_Inventory.py`](../templates/resources/methods/Aux_Inventory.py) · [`Functions_AuxFiles.py`](../templates/misc/Functions_AuxFiles.py) | Borradas `fetch_all_movements` y `get_all_sm_products`, junto con los imports que solo ellas usaban. |
| **Modelos** | — | Sin cambios. |

### El código nuevo de SKU

`get_new_code_products` **no** usaba la primera fila del `ORDER BY sku DESC`. Recorría todos los SKU, les quitaba los primeros 4 caracteres (fueran o no `1001`), descartaba lo que no quedara en puros dígitos y se quedaba con el máximo. Un `LIMIT 1` sobre el mismo orden no era equivalente: un SKU con letras (`ZZZ…`) queda primero en el orden descendente, el máximo saldría 0 y el código nuevo repetiría uno existente. Por eso el SQL reproduce la misma cuenta:

- `SUBSTRING(sku, 5)` es el `sku[4:]` de Python;
- `REGEXP '^[0-9]+$'` deja fuera lo mismo que el `int()` + `isdigit()` de antes: sufijo vacío, espacios, signos y letras;
- un SKU con otro prefijo (`XXXX0000999`) también cuenta, igual que antes;
- si ningún SKU califica, `MAX` da `NULL` y el siguiente código es `10010000001`, igual que antes.

La BD sigue recorriendo la tabla (no hay índice que sirva para `SUBSTRING`), pero devuelve una fila en vez de 1,234.

## Inventario de las 46 funciones

Conteos de dev (copia de prod del 2026-10-09). Prod no se consultó en esta revisión.

**Acotadas por id, lista de ids, filtro o agregado (sin acción):** `get_stock_db`, `get_product_barcode_data`, `get_products_stock_from_ids`, `get_product_by_sku_manufacture` (por código del fabricante), `get_warehouse_db`, `get_main_warehouse_db` (`LIMIT 1`), `get_warehouse_stock_db`, `get_warehouse_movement_db`, `get_transfer_db`, `get_next_transfer_folio_db` (`MAX`), `get_products_brief_db`, `get_product_stock_and_reserved_db` y `get_movements_type` (top N del dashboard: agrega todo el historial, pero devuelve N filas).

**Con ventana y tope (sin acción):** `get_kardex_main_db` y `get_warehouse_movements_db` (kardex, [`almacen_kardex_ventana.md`](almacen_kardex_ventana.md)), `get_transfers_db` (traslados, `limit` + `meta.truncated`), `get_ins_db_detail` (entradas de la conciliación de OC, desde la OC más vieja: `P-115`).

**Archivos (sin tope a propósito):** `get_all_movements_db_detail` y `get_epp_movements_db_detail` (descargas PDF/Excel de movimientos, el rango va en SQL); `get_all_products_db_old` (descargas del inventario).

**Catálogos legítimos (sin acción):**

| Función | Endpoint | Tamaño en dev |
|---|---|---|
| `get_all_categories_db` | `GET /almacen/inventory/categories/all` | 38 categorías |
| `get_warehouses_db` | `GET /almacen/warehouses` | sedes (filtro `is_active`) |
| `get_all_epp_inventory` | `GET /almacen/inventory/epp` | 55 productos, 18 KB |
| `get_skus` | carga masiva de productos desde Excel | 1,234 filas × 3 columnas: hacen falta todas para decidir alta o actualización |

**Deprecados (se van con `P-126`):** `get_movements_type_db_all` y `get_epp_movements_db` traen todo el historial para `GET /movements/<type_m>` y `GET /movements/epp/<type_m>`; se borran al retirar esas rutas.

**Solo chatbot (no se tocan):** `get_product_movement_amc`, `get_product_categories`, `get_products_almacen`, `get_high_stock_products`, `get_low_stock_products`, `get_no_stock_products` y `get_supply_inv_amc`.

**Arreglado:** `get_last_sku` → `get_max_sku_number` (arriba).

**Borradas (sin llamadas):** `get_ins_db`, `get_outs_db`, `get_outs_db_detail`, `get_movements_type_db`, `get_all_suppliers`, `get_stock_db_products` (`WHERE id_product LIKE '%'`), y las auxiliares `fetch_all_movements` y `get_all_sm_products`. Ningún nombre aparecía fuera de su propia definición, ni siquiera en un import.

**Listados sin tope que cambiarían contrato → pendientes nuevos:**

| Pendiente | Función | Endpoint | En dev | Qué falta |
|---|---|---|---|---|
| `P-201` | `get_all_reservations` | `GET /almacen/reservations` | 0 reservas (4 en test) | Hoy es chica, pero trae **todo el historial**, con todos los estados y su `history`, y crece con cada SM. Back: `?status=` + ventana/`limit` con `meta.truncated`. Front: pedir solo pendientes por defecto. |
| `P-202` | `get_all_products_db_tool_internal` | `GET /almacen/inventory/products/all` | 1,234 productos, 464 KB | `type_p` sin `tool`/`internal` → `LIKE '%'` en los dos campos = catálogo entero con reservas en cada carga. Mismo caso: `GET /sucursal/inventory` y `/sucursal/inventory/main`. Opciones: ETag + 304 como el kardex (sin cambio de contrato) o búsqueda/paginación en el API (cambia contrato). |
| `P-203` | `get_consolidated_stock_db` | `GET /almacen/inventory/consolidated` | 1,234 productos, 227 KB | Sin `search` ni `only_multisede` devuelve todo el catálogo, con dos subconsultas por producto (stock por sede y en tránsito vía `JSON_TABLE`). El front todavía no lo usa (segunda etapa de `P-049`), así que el default se puede cambiar sin romper a nadie (`only_multisede=1` o `search` obligatorio). Hay que decidirlo antes de que lo consuma. |
| `P-204` | `get_products_w_reservations` | `GET /sm/products/<contract>` | 1,234 productos en `normal`, 224 KB | El catálogo entero con reservas cada vez que se abre el formulario de SM. Opciones: ETag + 304 o búsqueda en el API. |

## Contrato mínimo para el front

`GET /almacen/codes/generate` **no cambia**: misma respuesta, mismo cálculo. Solo cambia lo que la BD le manda al API.

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`; `jwt.decode` sobre el header tal cual). Base `/GUI/api/v1/almacen`. Sin query ni body.
- **Permisos exactos**: `App.Department.ALMACEN` o `App.Department.ALMACEN-VISUAL` (`App.Department.Administrator` siempre pasa).

```json
// 200: siguiente código libre (prefijo 1001 + 7 dígitos)
{"data": "10010001237", "msg": null, "error": null}
// 400: falló la consulta
{"data": null, "msg": "No se pudo generar el codigo", "error": "<error de la BD>"}
// 401
{"error": "No autorizado. Token invalido"}
```

- **Gotcha**: el código no se reserva. Dos altas simultáneas pueden recibir el mismo, y la segunda falla en la BD porque `sku` tiene llave única (`products_amc_pk`). El front debe volver a pedir un código y reintentar. Esto ya pasaba antes.

Los pendientes `P-201` a `P-204` cambiarán contratos. Cada uno llevará su propio bloque de contrato al hacerse.

## Verificación

Dev (2026-10-28), `Tests/tester_lecturas_completas.py`, **27/27**:

- `GET /almacen/codes/generate` da el mismo código que la cuenta vieja en Python, tanto en dev (`10010001237`, 1,234 SKU) como en test con token de tester (`10010001123`, 1,121 SKU);
- `get_max_sku_number` devuelve una sola fila;
- la misma expresión SQL coincide con la cuenta vieja en 8 casos borde sobre una tabla derivada (sufijo vacío, SKU corto, otro prefijo, espacios, signos, letras, un SKU con letras primero en el orden, ninguno que califique, tabla vacía);
- las 9 funciones borradas o renombradas ya no existen y los módulos importan.

Regresión:

- `Tests/tester_po_match_cantidades.py` 41/41. Su revisión de "partida nueva con `order_id`" daba un falso positivo cuando una OC de prueba tomaba el mismo id que la solicitud de prueba; se acotó a la partida de prueba.
- `Tests/tester_permisos_almacen.py` 18/18, `Tests/tester_permisos_sm.py` 10/10, `Tests/tester_kardex_etag.py` 54/54.
- `pyrefly check --python-version 3.11`: 169 → 166 errores (los 3 que se fueron estaban en código borrado).

## Al modificar

- Un listado nuevo sobre una tabla que crece (movimientos, reservas, traslados) nace con ventana, `limit` y `meta.truncated` ([`MD_Kardex.py`](../templates/resources/midleware/MD_Kardex.py)). Un catálogo (productos, categorías, sedes) puede ir completo, pero conviene ETag si se recarga seguido.
- `WHERE col LIKE '%'` no acota nada: si el filtro es opcional, usar `(%s IS NULL OR col = %s)`.
- Si cambia el formato del SKU (prefijo o largo), cambiar `prefix`/`code_length` en `get_new_code_products`; `get_max_sku_number` recibe cuántos caracteres saltar.

## Notas posteriores

- **2026-10-28** — Los dos deprecados (`get_movements_type_db_all` y `get_epp_movements_db`) se borraron junto con sus rutas al cerrar `P-126`. Las funciones con SELECT de `controllers/product` bajan de 46 a 44. → [`almacen_kardex_ventana.md`](almacen_kardex_ventana.md)
- **2026-10-28 — Tamaños en prod.** Medidos por HTTP con un token de solo lectura (`ALMACEN-VISUAL`, que dio el usuario), sin consultar la BD. Prod tiene **1,995 productos**, contra 1,234 de la copia de dev. nginx comprime las respuestas grandes; la de reservas, por chica, viaja sin comprimir.

  | Pendiente | Endpoint | Filas | Sin comprimir | Por la red |
  |---|---|---|---|---|
  | `P-201` | `GET /almacen/reservations` | 3 (todas pendientes) | 759 B | 759 B |
  | `P-202` | `GET /almacen/inventory/products/all` | 1,995 | 835 KB | 84 KB |
  | `P-203` | `GET /almacen/inventory/consolidated` | 1,995 | 403 KB | 49 KB |
  | `P-204` | `GET /sm/products/all` | 1,995 (en `normal`) | 399 KB | 61 KB (medido después con un token con `SM`) |
  | (referencia) | `GET /almacen/kardex`, ventana por defecto | 2,094 movimientos | 462 KB | 51 KB |

  `P-201` hoy no tiene urgencia. `P-202` es el más pesado: 84 KB por la red en cada carga.
- **2026-10-28 (noche) — `codes/generate` verificado en prod** (`P-205`, token `ALMACEN-VISUAL`). Responde 200 con `10010001998`: el máximo de la parte numérica del SKU (1997) más uno, ya calculado por la BD. No se cotejó contra la cuenta vieja en Python porque no hay lectura directa de la BD de prod; con 1,995 productos el valor es coherente.
