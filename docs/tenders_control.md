# Control de licitaciones FO-PRE-04 (`/admin/presales/tenders`, `/tender`, `/tender/items`)

Fecha: 2026-10-19 · **Estado: implementado y verificado contra dev** (61/61 checks HTTP en `Tests/tester_tenders.py`, más la regresión de cotizaciones, OCD, costos y entregas; ver [Verificación](#verificación)). El grill del 2026-10-19 quedó cerrado. El DDL [`licitaciones.sql`](../scripts_db_handle/licitaciones.sql) está corrido en dev, test y prod, con el mismo esquema en las 3 (verificado en solo lectura el 2026-10-19, `P-146`). Falta el front (`P-147`).

Origen: junta con el front del 2026-10-19 y su propuesta `WebApps/telintec_webapp/docs/backend/licitaciones-contrato-propuesta.md`. El front ya hizo las pantallas (Preventa → Control de licitaciones) contra esa propuesta. **Este doc la sustituye.** Cambian las rutas, el estado y el alcance pasan a números, y se agregan las partidas y el contrato. La adaptación del front es `P-147`.

## Modelo

Una licitación es **una fila en `tenders`** (el control del Excel) más **una cotización interna** en `quotations` con `metadata.status = 3`, que guarda sus partidas en `quotation_items`. Las partidas de un contrato vienen de las de su licitación. En una cotización de preventa, en cambio, "partida" es solo el número de renglón.

```
tenders ──quotation_id (1:1)──▶ quotations (metadata.status = 3) ──▶ quotation_items (partidas)
   │                                                                    └─▶ quotation_item_costs / _supplier_quotes (análisis F6)
   └──contract_id (1:1, solo status 1)──▶ contracts (quotation_id = la misma cotización)
```

- **Contrato sin licitación:** igual que hoy. "Nuevo contrato" crea su cotización `status 2` y no se crea fila dummy en `tenders`. Si después aparece la licitación real de un contrato histórico, se captura y se liga con `PUT /tender` (`contract_id`).
- **Análisis de costos:** es el de F6 ([`quotation_cost_analysis.md`](quotation_cost_analysis.md)) **sin cambios de modelo**, colgado de la partida. Por eso sirve igual para cotización, OCD y licitación. El concepto: por cada item se comparan precios de varios proveedores (`suppliers`, con `is_selected` para el elegido), se guardan los valores decididos (costo y `% ganancia`, de donde sale `unit_price_profit`) y `apply_prices` los pasa a `price_unit`, que alimenta el total.

### `quotations.metadata.status` (primera vez documentado)

| Valor | Qué es | Quién lo escribe |
|---|---|---|
| `0` | Cotización de preventa | `create_quotation` (default), `POST /quotation` |
| `1` | Catálogo de contrato | `PUT /contract`, rama legacy sin `quotation_id` |
| `2` | Catálogo creado por "Nuevo contrato" | `POST /contract` con `quotation_id = 0` |
| `3` | **Partidas de licitación** (nuevo) | `POST /tender` |

### Tabla `tenders` ([`licitaciones.sql`](../scripts_db_handle/licitaciones.sql))

| Bloque | Columnas |
|---|---|
| Levantamiento | `tender_number` VARCHAR(60) **UNIQUE global**, `client_id` FK → `customers_amc`, `description`, `scope` TINYINT, `buyer_user`, `field_user` |
| Licitación | `invitation_date`, `closing_date`, `amount_usd`, `amount_mxn` (DECIMAL, capturados) |
| Respuesta | `status` TINYINT default 0, `po_number`, `response_date` |
| Indicador | `submitted_date` |
| Vínculos | `quotation_id` NOT NULL UNIQUE FK → `quotations` (RESTRICT), `contract_id` NULL UNIQUE FK → `contracts` (SET NULL) |
| Auditoría | `created_by`, `created_at`, `updated_at`, `history` JSON, `extra_info` JSON |

Lo que el Excel calcula (días disponibles, "¿está dentro de lo deseado?" y la hoja INDICADOR) **no se guarda**: lo calcula el front.

## Reglas

| Tema | Regla |
|---|---|
| `tender_number` | Se recorta y debe tener de 1 a 60 caracteres, sin restringir cuáles. Es único global; mayúsculas y minúsculas chocan por la collation `general_ci`. Lo captura el usuario: el número del cliente, o un alfanumérico propio que no choque. El back **no** genera folio. Repetido → 409. |
| Cliente | Obligatorio y existente en `customers_amc` (el usuario lo da de alta antes). No se puede cambiar si hay contrato ligado. |
| Fechas | `closing_date ≥ invitation_date`; `submitted_date ≥ invitation_date`. |
| Montos | `≥ 0` o `null`. Son el monto **ofertado**. El back nunca los recalcula; el GET agrega `items_total` (Σ `quantity × price_unit` de las partidas) para comparar. |
| `currency` | Opcional, `MXN` (default) o `USD`. Es la moneda de las **partidas** y vive solo en la cotización interna (`metadata.currency`), no en `tenders`. El GET la devuelve junto a `items_total`. Se agregó al implementar para que una licitación en dólares no quede marcada en MXN. |
| `status` / OC / contrato | `po_number` y `contract_id` solo con `status = 1`. Un `PUT` que saque la licitación de `1` con OC o contrato guardados debe mandarlos en `null`; si no, 400. |
| `contract_id` (liga manual) | El contrato existe, es del mismo cliente y no está ligado a otra licitación (si lo está, 409). |
| `PUT` parcial | Llegan `id_tender` y solo lo que cambia. Las reglas se validan con los valores **resultantes** (lo guardado más lo que llega). Cada cambio agrega una entrada `changes` al `history`. |
| Sincronía con la cotización | El `POST` crea la cotización con `quotation_code = tender_number`, `client_id`, `company` (nombre del cliente), `user = buyer_user`, `emission = invitation_date`, `limit_date = closing_date` y `emp_id` del token; el resto de la metadata va vacío más los defaults OCD. El `PUT` reescribe esas mismas llaves con `JSON_SET` cuando cambian. |
| Atomicidad | `execute_sql` no tiene transacciones. El `POST` valida todo, crea la cotización y luego la licitación; si la licitación falla, por ejemplo por una carrera en el `UNIQUE`, borra la cotización y responde 409/400. |
| Borrado | No hay. `status = 3` (cancelada) cubre el caso. |
| Permisos | Solo `administracion` en lectura y escritura (Administrador pasa siempre). |

### Licitación ganada → contrato (`POST /contract`)

Revisé todos los caminos que crean contratos: hay un solo punto de creación (`create_contract_from_api`) y una rama legacy en el `PUT`.

| Camino | Comportamiento |
|---|---|
| `POST /contract` con `quotation_id = 0` ("Nuevo contrato") | **Igual que hoy**: crea cotización `status 2` + partidas + contrato. |
| `POST /contract` con `quotation_id` de una cotización que **no** es de licitación | **Igual que hoy**: contrato sobre esa cotización; las partidas salen de `products` y las existentes no se tocan. |
| `POST /contract` con `quotation_id` de una **licitación** (`status 3`) | **Nuevo.** Antes de crear nada valida que la licitación esté en `status 1`, sin contrato y con el mismo `client_id`; si no, 400. Luego crea el contrato, pone `contract_id` a las partidas existentes (`WHERE quotation_id = … AND contract_id IS NULL`, para que SM las vea), agrega como partidas nuevas los `products` que lleguen y liga `tenders.contract_id`. La cotización **conserva** `status 3`. |
| `PUT /contract` legacy sin `quotation_id` | **Igual que hoy**: crea cotización `status 1`. |

Fixes que entraron de paso en `create_contract_from_api`, sin cambiar el comportamiento cuando todo sale bien:

- **`abbreviation` no se guardaba.** `create_contract(...)` se llamaba con argumentos posicionales y `abbreviation` caía en el lugar de `data_token`: el contrato nacía sin abreviatura y un token `is_tester` escribía en la BD de dev. Ahora van por nombre. Verificado: `POST /contract` guarda `abbreviation`.
- **Reversa.** Si el contrato o todas sus partidas fallan, solo se borra la cotización que creó **ese mismo request**; antes intentaba borrar también una cotización que ya existía. Además, ahora borra primero el contrato y después la cotización. Antes era al revés, y el borrado de la cotización fallaba por la FK `contracts.quotation_id`.

### Guardas nuevas en endpoints de cotización

| Endpoint | Cambio |
|---|---|
| `PUT /quotation` sobre `status 3` | 400: "las partidas de una licitación se editan con `PUT /tender/items`". Su form exige `phone`/`email`/`planta`/… que la licitación no tiene. |
| `DELETE /quotation` sobre `status 3` | 400 **antes** de borrar nada. Hoy borra primero las partidas, y la FK de `tenders` haría fallar el segundo paso con las partidas ya perdidas. |
| `PUT /quotation/ocd` sobre `status ≠ 0` | 400. Ni una licitación ni un catálogo de contrato se convierten en OCD; responde la duda 2.3-3 del front. |
| `GET /quotation/-1?status=` | Filtro opcional, un valor o una lista (`0` o `0,3`). Sin el parámetro, todo igual que hoy. Responde la duda 2.3-1 del front. |

## Decisiones del grill (2026-10-19)

1. **Entra ahora.** Era `P-123` "sin tarea"; Preventa decidió que entra y el front ya tiene las pantallas.
2. **Rutas en el namespace existente** `GUI/api/v1/admin/presales`, con el estilo plural/singular de `/sgi/formats`, no el `-1` legacy.
3. **`tender_number` único global** y capturado. Si el cliente da número, se usa ese; si no, Preventa escribe un alfanumérico propio.
4. **Cuatro estados, numéricos.** Cubren los 2 del Excel y dejan margen si cambia el formato. Regla general desde hoy: los estados siempre con mapeo numérico.
5. **El alcance también es numérico** (0–4, en el orden del Excel). No se usa bitmask porque el Excel solo permite esas 5 combinaciones.
6. **Permiso: solo `administracion`.**
7. **Cliente obligatorio del catálogo**, con FK. No hay texto libre para prospectos.
8. **Tabla propia `tenders`**, no llaves en `quotations.metadata` como las OCD, por cinco razones: `UNIQUE` real; FKs (cliente, y un contrato ↔ una licitación); ciclo de vida con reglas y columnas tipadas; no compartir el JSON que reescribe `PUT /quotation`; consultas e indicador directos.
9. **Las partidas viven en `quotation_items`**, a través de la cotización interna `status 3` que crea el back. Solo se editan con `PUT /tender/items`.
10. **Análisis de costos = F6 tal cual.** Se descartó una cabecera `cost_analyses` con `quotation_id XOR tender_id` (propuesta intermedia del grill), porque al vivir las partidas en `quotation_items` ya no hace falta. Las pantallas de análisis del front no siguen el concepto y se rehacen (`P-148`).
11. **Montos capturados más `items_total` calculado.** El back no sobreescribe montos.
12. **Licitación ganada → contrato** por `POST /contract` con `quotation_id`. Un contrato sin licitación se crea como hoy, sin fila dummy.
13. **Sin anexos en esta versión.** Si se piden, irán como `extra_info.files` con el patrón de S3 de remisiones y vales.

## Capas tocadas

```
DDL         scripts_db_handle/licitaciones.sql                     (nuevo) tabla tenders con FKs
controller  templates/controllers/contracts/tenders_controller.py  (nuevo) SELECT (join cliente/contrato, items_count/items_total por subconsulta), INSERT, UPDATE parcial
controller  templates/controllers/contracts/quotations_controller.py  set_quotation_metadata_keys (JSON_SET) · assign_contract_to_quotation_items
midleware   templates/resources/midleware/MD_Tenders.py           (nuevo) validar → cotización interna → tender (compensación); PUT parcial + sync + history; items (reusa update_items_quotation_from_api); lectura con products/cost_totals
midleware   templates/resources/midleware/Functions_midleware_admin.py  guardas status 3 / ≠ 0; get_quotations(status=); rama quotation_id ≠ 0 de create_contract_from_api; data_token en create_contract
models      static/Models/api_tenders_models.py                    (nuevo) TenderPostForm / TenderPutForm / TenderItemsForm + api.model
routes      templates/resources/rs_Admin_presales.py               /tenders, /tender, /tender/<int:id_tender>, /tender/items; GET /quotation/<id_q> lee ?status
```

## Contrato mínimo para el front

- **Base:** `/GUI/api/v1/admin/presales`.
- **Auth:** header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permiso `administracion`.
- **Respuesta:** siempre `{data, msg, error}`. En éxito `error` es `null`; en un 400 de reglas es una lista de strings; en un 400 de form es un objeto por campo.

### Catálogos (numéricos; las etiquetas las pone el front)

| `status` | | `scope` | |
|---|---|---|---|
| `0` | En espera de respuesta (default) | `0` | Suministro |
| `1` | Asignada (la única con `po_number` y `contract_id`) | `1` | Instalación |
| `2` | No asignada | `2` | Mantenimiento |
| `3` | Cancelada | `3` | Suministro e instalación |
| | | `4` | Suministro, instalación y mantenimiento |

### `GET /tenders`

Query opcionales: `status` (`1` o lista `0,1`), `client_id`, `date_from`/`date_to` (`YYYY-MM-DD`, sobre `closing_date`) y `has_contract` (`1` = con contrato, `0` = sin contrato; si no se manda, no filtra). Orden: `invitation_date` descendente y luego `id_tender` descendente.

```json
// 200
{"data": [{"id_tender": 1, "tender_number": "LIC-2026-001", "client_id": 4, "client_name": "TERNIUM MEXICO",
           "description": "Cableado de nave 3", "scope": 3, "buyer_user": "Ana Pérez", "field_user": null,
           "invitation_date": "2026-10-01", "closing_date": "2026-10-15", "amount_usd": null, "amount_mxn": 185000.0,
           "status": 1, "po_number": "OC-4500123", "response_date": "2026-10-20", "submitted_date": "2026-10-14",
           "quotation_id": 31, "items_count": 12, "items_total": 179850.0, "currency": "MXN",
           "contract_id": 11, "contract_code": "6700380001", "contract_identifier": "CABLEADO NAVE 3",
           "created_by": 36, "created_at": "2026-10-01 09:12:00", "updated_at": "2026-10-20 11:03:10"}],
 "msg": null, "error": null}
```

`items_total` está en la moneda de la cotización interna (`currency`, default MXN). `contract_*` vale `null` sin contrato. Para mostrar el contrato, usar `contract_identifier` y caer a `contract_code` si no hay.

### `GET /tender/<id_tender>`

Devuelve la misma fila más `history`, `products` (las partidas, con el mismo shape que `products` de `GET /quotation/<id>`, `qa_item_id` incluido; `[]` sin partidas, no el renglón vacío que da `GET /quotation`), `cost_totals` (`items_count`, `items_analyzed`, `total_cost_mxn`, `total_with_profit_mxn`, `profit_mxn`) y `exchange_rate`. Con `?with_costs=1`, cada producto trae además su `cost_analysis`, igual que en `GET /quotation/<id>?with_costs=1`. Si no existe, 404 con `{"data": null, "msg": "No se encontró la licitación (ID 99)", "error": null}`.

### `POST /tender`

```json
{"tender_number": "LIC-2026-001", "client_id": 4, "description": "Cableado de nave 3", "scope": 3,
 "buyer_user": "Ana Pérez", "field_user": null, "invitation_date": "2026-10-01", "closing_date": "2026-10-15",
 "amount_usd": null, "amount_mxn": 185000, "status": 0, "po_number": null, "response_date": null, "submitted_date": null}
```

Obligatorios: `tender_number`, `client_id`, `description`, `scope`, `invitation_date` y `closing_date`. `status` vale 0 si no se manda. `currency` (`MXN`/`USD`) es opcional. `contract_id` se acepta con las mismas reglas que en el `PUT`.

| Código | Cuándo | Cuerpo |
|---|---|---|
| **201** | creada | `{"data": {"id_tender": 1, "id_quotation": 31}, "msg": "Licitación LIC-2026-001 creada", "error": null}` |
| **409** | número repetido | `{"data": {"id_tender": 1}, "msg": "La licitación LIC-2026-001 ya existe", "error": null}` |
| **400** | reglas | `{"data": null, "msg": "Datos inválidos", "error": ["closing_date antes de invitation_date", "scope fuera de catálogo (0-4)", "po_number solo con status 1"]}` |

### `PUT /tender`

Es parcial: `{"id_tender": 1, ...solo lo que cambia}`. `null` borra un opcional.

```json
{"id_tender": 1, "status": 1, "po_number": "OC-4500123", "response_date": "2026-10-20", "submitted_date": "2026-10-14"}
```

| Código | Cuándo | Cuerpo |
|---|---|---|
| **200** | aplicado | `data` = la fila completa (shape del listado). Si no cambió nada: `msg: "Sin cambios"`. Si la sincronía con la cotización interna falla, la licitación sí se guarda y `error` trae el aviso. |
| **400** | reglas sobre los valores resultantes | p. ej. `["status 0 con po_number guardado: manda po_number: null", "el cliente no se cambia con contrato ligado"]` |
| **404** | no existe | `data: null` |
| **409** | `tender_number` ya usado, o `contract_id` ligado a otra licitación | `{"data": {"id_tender": 7}, ...}` |

### `PUT /tender/items`

Así se capturan y editan las partidas. `products` tiene **el mismo shape que en `PUT /quotation`** (`qa_item_id` (0 o null = crear), `partida`, `section_index`, `udm`, `n_parte`, `marca`, `type_p`, `description`, `description_small`, `quantity`, `price_unit`, `is_erased`, …). Las partidas no mencionadas no se tocan.

```json
{"id_tender": 1, "products": [{"qa_item_id": 0, "partida": 10, "udm": "PZA", "description": "Cable UTP cat 6", "quantity": 500, "price_unit": 0},
                              {"qa_item_id": 902, "partida": 20, "udm": "SERV", "quantity": 1, "is_erased": 1}]}
```

- **200:** `data.items` = `[{"index": 0, "partida": 10, "qa_item_id": 950, "action": "created"}, {"index": 1, "partida": 20, "qa_item_id": 902, "action": "deleted"}]`, igual que `PUT /quotation` ([`contract_items_put_resultado.md`](contract_items_put_resultado.md)).
- Las reglas por partida son las de `PUT /quotation`: un `qa_item_id` que no es de esta licitación **se crea de nuevo** y queda en el log; `is_erased: 1` con `qa_item_id` 0 se ignora (`skipped`). Si ya existe contrato, la partida nueva nace con su `contract_id`.
- **400:** ninguna partida se pudo guardar, o estructura inválida. **404:** la licitación no existe. Si fallan solo algunas, la respuesta es 200 con `error` = lista de los errores.
- **Importar de Excel:** `POST /quotation/items/file` solo parsea el archivo y devuelve las partidas; el front las manda después a `PUT /tender/items`.
- **Precios desde el análisis:** `PUT /quotation/costAnalysis` con `id_quotation = quotation_id` de la licitación y `apply_prices: true` ([`quotation_cost_analysis.md`](quotation_cost_analysis.md)). Las sugerencias por `n_part` (`/costAnalysis/suggest`) funcionan igual.

### Crear el contrato de una licitación ganada

`POST /contract` como hoy, pero con `quotation_id` = el `quotation_id` de la licitación. `products` puede ir vacío, porque las partidas ya existen; si llega alguno, se agrega como partida nueva. Responde 400 si la licitación no está en `status 1`, si ya tiene contrato o si el `client_id` del contrato no coincide con el de la licitación. En éxito, la licitación queda con `contract_id`, y su `GET` lo muestra.

### Cambios en endpoints de cotización que ya usa el front

- `GET /quotation/-1?status=0`: Preventa recibe solo sus cotizaciones; las licitaciones y los catálogos de contrato quedan fuera.
- `PUT /quotation` y `DELETE /quotation` sobre la cotización de una licitación (`status 3`) → 400.
- `PUT /quotation/ocd` sobre `status ≠ 0` → 400 ("solo una cotización de preventa se convierte en OCD").

### Gotchas

- `status` y `scope` son **números**. Mandar `"en_espera"` responde 400.
- "En tiempo" lo calcula el front: `submitted_date ≤ closing_date` es "en tiempo"; posterior es "fuera de tiempo"; sin fecha es **pendiente**. El Excel lo tiene al revés y marca "en tiempo" las celdas vacías.
- `items_total` no es el monto de la licitación: `amount_mxn`/`amount_usd` son lo ofertado y el back no los toca.
- `has_contract=0` filtra las que no tienen contrato; para no filtrar, no se manda el parámetro.

## Al modificar

- **Nuevo valor de `quotations.metadata.status`:** agregarlo a la tabla de arriba y revisar las guardas (`PUT /quotation`, `DELETE`, `/ocd`) y el filtro `?status=`.
- **Nuevo camino que cree contratos:** respetar la regla de la licitación (`status 1`, sin contrato, mismo cliente, `contract_id` a las partidas y liga en `tenders`).
- **Nuevo campo de la licitación que también viva en la cotización:** agregarlo a la sincronía del `POST`/`PUT` (`JSON_SET`, sin reescribir la metadata entera).
- **Nuevo estado o alcance:** se agrega a la tupla del módulo y al front, sin DDL. Si cambian los números de 2 o más estados, avisar al front.
- Las columnas del `SELECT` de `tenders` se agregan siempre al final (append-only): el midleware mapea por posición, como en `balance_control_controller.py`.

## Verificación

2026-10-19, contra dev, con `Tests/tester_tenders.py` (`test_client`, datos temporales `TST-LIC-*` que se borran al final): **61/61**. Cubre:

- **Permisos y validaciones del POST:** obligatorios, catálogos, fechas, OC sin asignar, cliente inexistente, moneda, montos negativos.
- **Alta:** 409 por número repetido (también en minúsculas) sin dejar cotización huérfana.
- **Lectura y partidas:** filtros del listado; detalle con partidas y totales; alta, edición y borrado de partidas; `items_total`.
- **Guardas de cotización:** `PUT`/`DELETE /quotation` y `/ocd` sobre la licitación; filtro `?status=`; análisis F6 sobre la cotización interna con y sin `with_costs`.
- **`PUT` parcial:** "sin cambios" y la sincronía de `quotation_code`, `user`, `limit_date`, `currency`, `client_id` y `company`.
- **Estados y contrato:** 409 de número y de contrato ya ligado; OC y contrato solo con `status 1`; liga manual y desligar.
- **Licitación → contrato:** no asignada (400), otro cliente (400), ok (201: partidas existentes y nuevas con `contract_id`, `abbreviation` guardada, la cotización conserva `status 3`), un segundo contrato (400), y una partida nueva después del contrato que nace con `contract_id`.
- **Regresión de `POST /contract`:** "Nuevo contrato" (`status 2`, partidas con `contract_id`) y contrato sobre una cotización de preventa (partidas existentes sin tocar, igual que hoy). El `PUT /contract` legacy no se modificó.

Regresión de los testers existentes, sin cambios: `tester_quotation_costs` 37/37, `tester_quotation_ocd` 35/35, `tester_quotation_put_metadata` 18/18, `tester_quotation_cost_suggest` 22/22 y `tester_delivery_control` 71/71.

## Pendientes

`P-123` (back: hecho 2026-10-19), `P-146` (DDL en las 3 BDs: hecho 2026-10-19), `P-147` (front: adaptar las pantallas a este contrato), `P-148` (front: rehacer el análisis de costos según el concepto), `P-150` (back: copias huérfanas de catálogo en `quotations`) → [`pendientes.md`](pendientes.md).

## Notas posteriores

- **2026-10-22** (junta con Administración, F4 del [`plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md)): una licitación **ganada** (`status 1`, sin contrato) también puede convertirse en **OCD** con `PUT /quotation/ocd` sobre su cotización interna (conserva `status 3`, `tender_number` como folio, `po_number` como `client_po_number`); es **exclusivo** con `POST /contract` (400 en ambos sentidos). `GET /tender(s)` gana `document_type` y `client_po_number`; `PUT /tender/items` acepta `delivery_date` por partida. La guarda "`PUT /quotation/ocd` sobre `status ≠ 0` → 400" de este doc queda solo para los catálogos de contrato (1/2). Detalle → [`ocd_reglas_po_vencimiento.md`](ocd_reglas_po_vencimiento.md).
