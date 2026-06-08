# Generación de folios de órdenes de compra desde el `code` del contrato

La generación de folios de OC ([`generate_folios_po`](../templates/resources/midleware/MD_Purchases.py))
obtenía el código del contrato **parseando `metadata->'$.contract_number'`** y, a
partir de él, sus últimos 4 dígitos. Este documento describe el estado actual tras
mover esa fuente a la columna `code` del contrato y corregir el cálculo del
consecutivo.

## El endpoint

```
HTTP   rs_Admin_collections.py  GET /purchase/folio/<string:folio>   -> FolioPO
mid    MD_Purchases.py          generate_folios_po(reference, data_token)
DB     contracts_controller.py  get_contracts_abreviations_db(data_token)
DB     orders_controller.py     get_folios_po_from_pattern(patterns, data_token)
```

`reference` es el **folio SM** entrante, con formato `SM-0701-194`:
`reference_parts = reference.lower().split("-")` → `["sm", "0701", "194"]`.
El segmento intermedio (`0701`) es el código del contrato/área; el último (`194`)
viaja al folio maestro.

## La fuente del código del contrato

`get_contracts_abreviations_db` devuelve un `UNION` de tres orígenes, todos
**igual de válidos** como patrón de folio:

| Origen | `item[0]` | `item[3]` | `item[4]` | `item[5]` |
|---|---|---|---|---|
| `contracts` | `metadata->'$.abbreviation_sm'` | `abbreviation` | `1` | **`code`** |
| `departments` | `abbreviation` | `''` | `0` | `''` |
| `areas` | `abbreviation` | `''` | `0` | `''` |

- **Antes:** para contratos (`item[4] == 1`) se hacía
  `json.loads(item[2])["contract_number"][-4:]`.
- **Ahora:** se usa la columna existente **`code`** (un `VARCHAR` que ya guarda el
  número de contrato completo, poblado por `create_contract`/`update_contract`),
  expuesta como sexta columna `item[5]`. El código de matcheo son sus **últimos 4
  dígitos**: `item[5][-4:]`. Si `code` viene vacío/`NULL` el contrato se **omite**
  (igual que el viejo guard de `contract_number == ""`).

Los brazos de `departments`/`areas` se rellenan con `''` para que el conteo de
columnas del `UNION` cuadre. Es un cambio **no rompedor**: los otros consumidores
de `get_contracts_abreviations_db`
([`get_iddentifiers`, `get_contracts_abreviations`](../templates/resources/midleware/Functions_midleware_admin.py))
solo leen `item[0]`–`item[4]`.

El matcheo de **departamentos y áreas no cambió** — solo se modificó cómo se
obtiene el código del contrato.

## Los tres folios y el consecutivo

A partir del `reference` se arman tres patrones y se consultan los folios de OC
existentes vía `get_folios_po_from_pattern` (LIKE `%patrón%`):

| Folio | Patrón | Salida (`SM-0701-194`) |
|---|---|---|
| normal | `OC-GC` + `0701-194` | `OC-GC0701-194-001` |
| maestro | `OCM-GC` + `0701` | `OCM-GC0701-001-<initial>194` |
| cotfc | `OC-GCCOTFC-` + `0701-194` | `OC-GCCOTFC-0701-194-001` |

`<initial>` es `dict_abbs[reference_parts[-2]]["initial"]`, que para un contrato es
su columna `abbreviation`.

### Cálculo del consecutivo (corregido)

El código anterior iteraba sobre **cada** OC existente y agregaba **una salida por
fila** con el conteo de esa fila `+ 1` (consecutivos incorrectos / duplicados), y
cuando no existía ninguna OC devolvía los folios base **sin** sufijo numérico.

Ahora, por cada uno de los tres patrones, se recorren todos los folios que lo
contienen, se extrae el entero consecutivo final y se toma el **máximo**; la salida
es **un** folio por patrón en `max + 1` (con `:03d`). Sin coincidencias → arranca en
`-001`. **Siempre** devuelve 3 folios. El patrón `cotfc` se evalúa primero para
evitar clasificación errónea por solapamiento de prefijos.

## Listado de OC sin items

[`get_purchase_orders(status, created_by, data_token)`](../templates/controllers/order/orders_controller.py)
es un listado **de propósito general** que refleja las columnas de
`get_purchase_orders_with_items` **menos** el arreglo de items (`JSON_ARRAYAGG`) y
sin `GROUP BY` — para consumidores que necesitan las cabeceras de orden sin el
costo de agregar items. El cálculo del consecutivo **no** lo usa: sigue con
`get_folios_po_from_pattern`, que ya devuelve solo `(id_order, folio)` filtrado.

## Consistencia en `contracts_controller.py`

Para evitar divergencias entre `code` y `metadata->'$.contract_number'`, las demás
búsquedas por últimos 4 dígitos del controlador también se alinearon a `code`:

- `get_items_contract_string` → `WHERE RIGHT(c.code, 4) = %s` (se conserva el
  `OR JSON_EXTRACT(c.metadata, '$.abbreviation_sm') = %s`).
- `get_contract_and_items_from_number` → `WHERE RIGHT(c.code, 4) = %s`.

## Al modificar

- El código del contrato sale de la columna **`code`** (no de `metadata`). Si se
  agrega otra fuente de patrones al `UNION`, debe traer las **6 columnas** y rellenar
  con `''` las que no apliquen, o se rompen los índices `item[0..5]`.
- El consecutivo se calcula con `max + 1` por patrón; no volver al `append` por fila.
- `generate_folios_po` siempre regresa exactamente 3 folios (normal, maestro, cotfc).
