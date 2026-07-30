# Import de ítems de contrato desde Excel: parser tolerante, errores detallados y secciones

Cambios sobre el flujo `POST /admin/presales/contract/items/file` (parser de partidas desde Excel) y su persistencia en `quotation_items`. Tres bloques:

1. **Parser tolerante multi-plantilla** — el mismo parser lee la plantilla de *partidas de contrato* y la de *remisión* (CCTV Puebla, CERRAMIENTOS), resolviendo columnas por alias.
2. **Errores detallados** — el endpoint dejó de responder `500` genérico / falso `200` vacío; ahora distingue archivo ilegible, plantilla no reconocida y 0 partidas, con detalle al cliente y al log.
3. **Secciones (Fase 1 + 2 + 3)** — un Excel con varias secciones (p.ej. dos plantas: `CERRAMIENTO AM2` / `CERRAMIENTO LARGOS NORTE`) se carga como grupos con `section_index`; la sección persiste en `quotation_items` (columna nueva `section_index` + `extra_info` JSON), se expone en los GET, y el enlace **SM ↔ ítem** matchea por `(contract_id, section_index, partida)` (Fase 3).

## Capas tocadas

| Capa | Archivo | Qué cambió |
|------|---------|-----------|
| Parser | [`Functions_Aux_Admin.py`](../templates/resources/methods/Functions_Aux_Admin.py) | `read_exel_products_partidas`: auto-detección de la fila de encabezados, alias de columnas, detección de secciones (título en `POS.` o `DESCRIPCIÓN`), `section_index`, tupla `(groups, diagnostics)`. Helpers `_is_int_like`, `_find_partidas_header_row`. |
| Midleware | [`Functions_midleware_admin.py`](../templates/resources/midleware/Functions_midleware_admin.py) | `items_contract_from_file`: 4 ramas de error/éxito con detalle + log. `_item_quotation_values`: agrega `section_index` + `extra_info`. |
| Controller | [`quotations_controller.py`](../templates/controllers/contracts/quotations_controller.py) | `create_item_quotation`/`create_items_quotation`/`update_item_quotation`: columnas `section_index` + `extra_info`. `get_quotation`: **append** de `section_index`/`section_title`/`section_type`. |
| Controller | [`contracts_controller.py`](../templates/controllers/contracts/contracts_controller.py) | `get_contracts_with_items` (`/contracts/products`): **append** de las 3 llaves de sección. |
| Modelos/forms | [`api_contracts_models.py`](../static/Models/api_contracts_models.py) | `products_quotation_model`/`_put_model` (api.model) y `ProductsPostQuotationForm`/`ProductsPutQuotationForm` (WTForms): 3 campos nuevos opcionales. |
| Schema | [`scripts_db_handle/quotation_items_sections.sql`](../scripts_db_handle/quotation_items_sections.sql) | DDL a mano: `section_index INT NOT NULL DEFAULT 0`, `extra_info JSON NULL`, índice `(contract_id, section_index, partida)`. |

## Por qué la posición de header no era fija

El parser tenía `header=20` hardcodeado. La fila de encabezados **no está en la misma posición** entre plantillas (CCTV Puebla: fila 20; CERRAMIENTOS: fila 18). Con `header=20` en CERRAMIENTOS se leía la primera fila de ítems como encabezado → columnas basura → 0 partidas. Ahora `_find_partidas_header_row` busca la primera fila que contenga `POS./PARTIDA` + `DESCRIP*` + `PRECIO*` y la usa como encabezado.

## Secciones: modelo y llave

- Una **sección** es un bloque de ítems bajo un título; el título puede venir en la columna `DESCRIPCIÓN` (plantilla de contrato) **o** en `POS.` (plantilla de remisión, fila sin precio ni unidad).
- La `POS.` **reinicia por sección** (1..N en cada una), así que `partida` **no es única** dentro del contrato. `section_index` (entero 0-based, orden de aparición) es el discriminador: la llave real es `(contract_id, section_index, partida)`.
- `section_type` **siempre** sale del parser como `"general"` (no infiere planta/reajuste); el front/humano reclasifica. `section_title`/`section_type` viven en `extra_info` JSON; `section_index` es columna propia (indexable).
- `get_quotation` expone las 3 llaves **al final** del `JSON_OBJECT`: sus primeras 12 llaves tienen orden *load-bearing* para `compare_file_quotation` (compara por posición índices 0..11); agregar al final es inerte para ese compare.

### Enlace SM ↔ ítem section-aware (Fase 3, hecho)

`check_for_partidas_updates` (en `MD_SM.py`) ahora indexa los ítems del contrato por `(section_index, partida)` y llama a `update_quotation_item_partida_from_sm(contract_id, section_index, partida, id_inventory, ...)`, cuyo `WHERE` incluye `AND section_index = %s`. Así un contrato **multi-sección** ya puede enlazarse a SM sin que la `partida` repetida entre secciones pegue en varias filas. Los productos de SM cargan `section_index` (default 0). `get_items_quotation_from_cotract` gana `section_index` (índice 4, al final, para no mover los índices posicionales que consume `check_for_partidas_updates`).

**Backfill: no requerido.** El DDL dejó todos los `quotation_items` existentes en `section_index = 0` y los productos de SW legacy resuelven `section_index` con default 0, así que los contratos de una sola sección (todo lo existente + CCTV) siguen funcionando sin cambios. De paso, la coerción a int de la llave corrige un mismatch latente str/int del path PUT (partida como string) que disparaba UPDATEs redundantes.

**`GET /sm/products/<contract>`** (`get_products_sm`) alimenta el selector de partidas del front de SM. Ahora **expone `section_index`** en cada ítem del bucket `contract` y emite **una fila por `(partida, section_index)`** (antes `ids_in_contract` mapeaba `id_inventory → partida` y se sobrescribía: un producto usado en varias partidas/secciones perdía entradas — bug preexistente aun en una sola sección). `get_items_contract_string` gana `section_index` (índice 5, al final; único consumidor). Así el front puede re-enviar `section_index` en el ítem de SM y cerrar el círculo de Fase 3.

---

## Contrato mínimo para el front

**Auth (todos):** header `Authorization` con el **JWT crudo** (NO `Bearer <token>`).
**Base:** `/GUI/api/v1/admin/presales`. **Envelope:** `{data, msg, error}` (JSON, UTF-8).

### 1) Importar partidas desde Excel

`POST /admin/presales/contract/items/file` — multipart, campo `file` (un `.xlsx`, tabla de partidas cuyos encabezados incluyan `POS./PARTIDA` + `DESCRIPCIÓN` + `PRECIO`).

**200 — éxito:**
```json
{
  "data": [
    {
      "section_index": 0,
      "section_title": "REFACCIONES DE SIST. CERRAMIENTO AM2",
      "section_type": "general",
      "group_title": "REFACCIONES DE SIST. CERRAMIENTO AM2",
      "items": [
        {"partida": 1, "section_index": 0, "section_title": "REFACCIONES DE SIST. CERRAMIENTO AM2",
         "section_type": "general", "quantity": 0, "udm": "PZA", "price_unit": 3000,
         "type_p": "", "marca": "", "n_parte": "", "description": "Puerta abatible...",
         "description_small": "", "id": null, "comment": ""}
      ]
    },
    {"section_index": 1, "section_title": "REFACCIONES/SRV CERRAMIENTO LARGOS NORTE", "section_type": "general", "group_title": "...", "items": [ {"partida": 1, "section_index": 1, "...": "..."} ]}
  ],
  "msg": "118 partidas cargadas en 2 sección(es) (12 filas ignoradas)",
  "error": null
}
```
Notas:
- `data` es una **lista de secciones**. Un archivo sin secciones explícitas devuelve 1 sección `section_index=0`, `section_title="General"`.
- `partida` **reinicia por sección**; usa `(section_index, partida)` como llave, no `partida` sola.
- `id` es el `id_inventory` resuelto por SKU (solo cuando la plantilla trae columna `UDM`/`Nro. Parte`); en remisiones viene `null`.
- Al crear/editar el contrato, **re-envía `section_index`/`section_title`/`section_type` tal cual** en cada ítem (ver punto 3).

**400 — archivo ilegible / sin encabezados:**
```json
{"data": null, "msg": "No se pudo leer el archivo Excel",
 "error": "No se pudo leer el archivo Excel. Debe ser .xlsx con una tabla de partidas cuyos encabezados incluyan POS./PARTIDA + DESCRIPCIÓN + PRECIO. Detalle: ..."}
```
**400 — plantilla no reconocida** (`msg: "Plantilla de Excel no reconocida"`) y **400 — sin partidas** (`msg: "El archivo no contiene partidas válidas"`, con conteo de filas/secciones/ignoradas en `error`).

### 2) Leer cotización / contrato con ítems

`GET /admin/presales/quotation/<id_q>` — `data[i].products[j]` ahora incluye:
```json
{"qa_item_id": 3269, "partida": 1, "udm": "PZA", "brand": "", "type_p": "", "n_part": "",
 "quantity": 2, "revision": 0, "price_unit": 100.0, "description": "...", "description_small": "",
 "id_inventory": null, "section_index": 0, "section_title": "SEC A", "section_type": "general"}
```
`GET /admin/presales/contracts/products` — cada `items[j]` gana `section_index`/`section_title`/`section_type` igual. Ítems viejos (sin `extra_info`) devuelven `section_index=0`, `section_title="General"`, `section_type="general"`.

### 3) Crear / actualizar ítems de contrato o cotización

`PUT /admin/presales/contract` y `PUT /admin/presales/quotation` — cada ítem de `products` acepta 3 campos **opcionales**:

| Campo | Tipo | Default | Nota |
|-------|------|---------|------|
| `section_index` | int | `0` | Discriminador de sección. `null`/ausente → `0`. |
| `section_title` | string | `"General"` | **Overwrite completo**: como el resto de campos, omitirlo lo reescribe a `"General"`. Re-envía el valor del GET. |
| `section_type` | string | `"general"` | `general` \| `planta` \| `reajuste`. |

El upsert por `qa_item_id` no cambia (`null`/`0`/ausente → crea; `is_erased == 1` → borra). `partida` sigue siendo requerido.

### 4) Ítems de SM (enlace con partidas de contrato)

`GET /sm/products/<contract>` — el selector de partidas. `data.contract[j]` ahora incluye `section_index`, y un producto usado en varias partidas/secciones aparece **una vez por par `(partida, section_index)`**:
```json
{"data": {"contract": [
   {"id": 49, "name": "...", "udm": "PZA", "stock": 3, "partida": 5, "section_index": 0, "reserved": 0, "available_stock": 3, "sku": "...", "sku_fabricante": "..."},
   {"id": 49, "name": "...", "partida": 3, "section_index": 1, "...": "..."}
], "normal": [ {"...": "...", "partida": ""} ]}, "msg": null, "error": null}
```
(El bucket `normal` no lleva `section_index`.)

Al crear/actualizar una SM (`POST /sm/add`, `PUT /sm/...`), cada ítem de `items` que apunte a una partida de contrato debe incluir **`section_index`** (int, default `0`) junto con `partida` — reenviando el `section_index` que vino en `data.contract[j]` — para que el enlace SM ↔ ítem resuelva la partida correcta en contratos multi-sección. Contratos de una sola sección: omitir `section_index` (default `0`) sigue funcionando.

---

## Al modificar

- **`get_quotation` / `get_contracts_with_items`**: las 3 llaves de sección van **al final** del `JSON_OBJECT`. No las insertes entre `qa_item_id`..`id_inventory`: `compare_file_quotation` lee esas 12 posiciones por índice.
- **`section_title`/`section_type`** viven en `extra_info` (JSON), `section_index` es columna. Si agregas más campos sueltos del ítem, ponlos en `extra_info` y aplánalos con `extra_info->>'$.<clave>'` (con `COALESCE` a un default) en los GET.
- **`_item_quotation_values`** es el único punto que traduce payload → columnas; los 3 controllers de escritura leen `item.get("section_index", 0)` / `item.get("extra_info")` para tolerar callers que no los manden.
- **`get_items_quotation_from_cotract`** devuelve `section_index` en el **índice 4** (al final): `check_for_partidas_updates` indexa el resto por posición (`item[1]`=partida, `item[2]`=id_inventory). No reordenes esa `SELECT`.
- **Match SM section-aware**: la llave es `(contract_id, section_index, partida)`. Si el front no manda `section_index` en el ítem de SM, resuelve a `0` (compatible con contratos de una sección). Los ítems de SM de `data["items"]` se validan con `ItemsFormSMPost`/`ItemsFormSMPUT` (ambos tienen `section_index`).
- **`get_items_contract_string`** devuelve `section_index` en el **índice 5** (al final); único consumidor `get_products_sm`, que indexa `item[3]`=partida, `item[4]`=id_inventory por posición. No reordenes esa `SELECT`. `get_products_sm` emite una fila por `(partida, section_index)` (dict `id_inventory → lista de pares`).
