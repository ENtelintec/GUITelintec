# Cotizaciones CISCO FO-PRE-02 (`GET·POST·PUT /quotation/cisco`): mismas tablas, `metadata.format = "cisco"`

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (46/46 checks, `Tests/tester_quotation_cisco.py`; folio, OCD, licitaciones, PUT metadata y costos en verde). Sin DDL. PDF FO-PRE-02 después (`P-169`).**

Fase **F10** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (duda 2.4 del front del 2026-10-19, propuesta en `WebApps/telintec_webapp/docs/backend/cotizacion-cisco-contrato-propuesta.md`; decisión del 2026-10-22: entra, con las rutas que el front ya construyó). Extiende [`quotation_ocd.md`](quotation_ocd.md) (conversión a OCD), [`quotation_cost_analysis.md`](quotation_cost_analysis.md) (la hoja "ANÁLISIS DE COSTOS CISCO" ya la cubre `PUT /quotation/costAnalysis`) y [`folio_sugerido_cotizaciones.md`](folio_sugerido_cotizaciones.md).

## Qué cambia

- **Mismas tablas** `quotations` / `quotation_items`. La CISCO se distingue por **`metadata.format = "cisco"`** (FO-PRE-02; ausente o `""` = FO-PRE-01), **separado** de `document_type` (`quotation` | `ocd`): una CISCO se convierte en OCD con `PUT /quotation/ocd` igual que una de preventa y **no pierde el formato**.
- **Cabecera**: la de preventa (`MetadataQuotationForm`) más **`concept` obligatorio** y **`currency` obligatoria** (`MXN` | `USD`); `delivery_time` (texto) es el tiempo de entrega general. `limit_date` < `emission` → 400.
- **Partidas** en `quotation_items`: `n_parte` → columna `n_part`; `partida` **se deriva del orden** del payload (entre las vivas); `udm` opcional (se guarda `PZA` si no viene). Lo propio de CISCO va en **`extra_info`**: `item` (texto `1`, `1.1`, `2`; único en la cotización), `smart_account` (bool), `service_months` (int > 0 o `null`), `delivery_time` (texto). Como las secciones y `delivery_date`, el `extra_info` de la partida es **overwrite completo** en cada PUT.
- **Rutas nuevas** como envoltorios delgados del mismo midleware: `GET /quotation/cisco/-1`, `GET /quotation/cisco/<id>` (404 si no existe o no es CISCO), `POST /quotation/cisco`, `PUT /quotation/cisco` (mismo upsert por `qa_item_id` que `PUT /quotation`, con `data.items`). Validación **en lista** (400) antes de escribir.
- **`GET /quotation/-1` las excluye por default**. `?format=cisco` → solo CISCO; `?format=all` → todas; sin `format` pero con `?document_type=ocd` → **sí salen** las CISCO ya convertidas (Cobranza ve todas las OCD). `GET /quotation/<id>` por id no restringe.
- **`PUT /quotation` (grande) sobre una CISCO → 400** "se editan con PUT /quotation/cisco": su form no declara `concept` ni `item` y, por el overwrite, las borraría. `PUT /quotation/cisco` sobre una no CISCO → 404. `DELETE /quotation` y `PUT /quotation/ocd` sirven para las dos.
- **Los GET de cotizaciones** (`/quotation/<id>`, `/quotation/-1`, también en las de preventa) exponen al final de cada producto `item`, `smart_account`, `service_months`, `delivery_time` (`null` fuera de CISCO) y `metadata.format` / `metadata.concept` siempre presentes (`""` si no aplican).
- **`quotation_code` sin candado** en CISCO (como preventa): el 409 del folio es solo de OCD ([`folio_sugerido_cotizaciones.md`](folio_sugerido_cotizaciones.md)); el folio sugerido es `GET /quotation/folio?format=cisco` → `COT-CISCO-AAAA-NNN`.

### Respuestas a las 4 preguntas del front

1. Mismas tablas con `metadata.format = "cisco"`; sin tabla aparte.
2. `quotation_code` **sin candado** en CISCO ni preventa (lo histórico tiene repetidos); único solo al marcar una OCD (409).
3. PDF FO-PRE-02 **después** (`P-169`, `iso_formats` id 15); mientras, `GET /quotation/download/pdf/<id>` imprime el FO-PRE-01.
4. Sí se convierte a OCD con `PUT /quotation/ocd` (mismo body y reglas: `client_po_number` obligatorio y único, `due_date`); conserva `format = cisco` y aparece en `GET /quotation/-1?document_type=ocd`.

## Capas tocadas

```
rs          rs_Admin_presales.py                 GET /quotation/cisco/<id_q> · POST·PUT /quotation/cisco · ?format= en GET /quotation/<id_q>
midleware   MD_QuotationCisco.py (nuevo)         cisco_header_errors · cisco_items_errors · _cisco_to_standard · _products_out ·
                                                 get_quotations_cisco_api · create_quotation_cisco_api · update_quotation_cisco_api
midleware   Functions_midleware_admin.py         get_quotations(fmt=) (filtro + 404) · _normalize_quotation_metadata_out (format/concept) ·
                                                 _item_quotation_values (llaves CISCO en extra_info solo si viene `item`) · update_quoation_from_api(fmt=) (guard)
controller  quotations_controller.py             get_quotation: item / smart_account / service_months / delivery_time al final de cada JSON_OBJECT
models      api_quotation_cisco_models.py (nuevo) MetadataQuotationCiscoForm (hereda) · ProductsQuotationCiscoForm · QuotationCiscoInsertForm / UpdateForm · api.model
```

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales` (permiso `administracion`). **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, **lista de strings** en 400/404 de midleware, **objeto por campo** en 400 de form (`{"products": [{"n_parte": ["This field is required."]}]}`). 401: `{"error": "..."}` sin envelope.

### `POST /quotation/cisco`

```json
{
  "metadata": {"emission": "2026-10-19", "limit_date": "2026-11-19", "quotation_code": "COT-CISCO-2026-001",
               "company": "TERNIUM", "user": "Ana", "phone": "8100000000", "email": "ana@ternium.com",
               "planta": "Pesquería", "area": "Redes", "location": "NL", "client_id": 4, "emp_id": 36,
               "concept": "Switches de acceso", "currency": "USD", "delivery_time": "4 a 6 semanas"},
  "products": [
    {"item": "1", "n_parte": "C9300-48P-E", "smart_account": false, "description": "Catalyst 9300 48 puertos PoE+",
     "service_months": null, "delivery_time": "6 semanas", "quantity": 2, "price_unit": 5120.0},
    {"item": "1.1", "n_parte": "CON-SNT-C930048E", "smart_account": true, "description": "Smartnet 8x5xNBD",
     "service_months": 36, "delivery_time": "", "quantity": 2, "price_unit": 610.0}
  ]
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `metadata.concept` | string | obligatorio |
| `metadata.currency` | `MXN` \| `USD` | obligatorio |
| `metadata.delivery_time` | string | opcional |
| `metadata.document_type` / `client_po_number` / `due_date` | | opcionales, como en preventa (una CISCO puede nacer OCD) |
| `products[].item` | string `^\d+(\.\d+)?$` | único entre las partidas vivas |
| `products[].n_parte`, `description` | string | obligatorios |
| `products[].smart_account` | bool | default `false` |
| `products[].service_months` | int > 0 o `null` | |
| `products[].delivery_time` | string | opcional |
| `products[].quantity` | int > 0 | |
| `products[].price_unit` | número ≥ 0 | sin IVA |
| `products[].udm`, `delivery_date` | | opcionales (`PZA`; fecha ≤ `due_date` si es OCD) |

| Código | Cuándo | Ejemplo |
|---|---|---|
| **201** | creada | `data: {"id_quotation": 31}` · `msg: "Cotización creada correctamente (ID 31)"` |
| **400** (form) | falta `concept`, `n_parte`, `currency` inválida… | `msg: "Estructura de datos inválida"` · `error: {"metadata": {"concept": ["This field is required."]}}` |
| **400** (lista) | reglas CISCO | `msg: "Cotización CISCO inválida"` · `error: ["partida 2: item '1' repetido (partida 1)", "partida 3: quantity debe ser un entero mayor a 0", "limit_date (2026-10-01) no puede ser anterior a emission (2026-10-19)"]` |
| **400 / 409** | nació como OCD | mismas reglas de `client_po_number` y folio que [`ocd_reglas_po_vencimiento.md`](ocd_reglas_po_vencimiento.md) |

### `PUT /quotation/cisco`

`{"id": 31, "metadata": {…}, "products": [ … ]}`: cabecera completa (misma forma) y **todas** las partidas: con `qa_item_id` → actualiza; sin él / `0` / `null` → crea; `"is_erased": 1` → borra (una borrada no cuenta para la unicidad de `item` ni para la numeración). `partida` se recalcula por el orden del payload.

| Código | Cuándo | Respuesta |
|---|---|---|
| **200** | guardada | `data: {"id_quotation": 31, "items": [{"index": 0, "partida": 1, "qa_item_id": 900, "action": "updated"}, {"index": 1, "partida": 0, "qa_item_id": 901, "action": "deleted"}, {"index": 2, "partida": 2, "qa_item_id": 905, "action": "created"}]}` |
| **400** | reglas CISCO / control de entregas activo (si ya es OCD) / `delivery_date` > `due_date` | lista |
| **404** | no existe o no es CISCO | `msg: "No se encontró la cotización CISCO (ID 31)"` |

### `GET /quotation/cisco/-1` · `GET /quotation/cisco/<id>`

`data` es **siempre una lista** (una entrada en el GET por id). Cada entrada: `id`, `creation`, `timestamps`, `metadata` (con `format: "cisco"`, `concept`, `currency`, `delivery_time`, `document_type`…), `products` ordenados por `partida` y **`total`** general sin IVA.

```json
{"data": [{"id": 31, "creation": "2026-10-19 10:00:00", "total": 11460.0,
           "metadata": {"quotation_code": "COT-CISCO-2026-001", "format": "cisco", "document_type": "quotation",
                        "concept": "Switches de acceso", "currency": "USD", "delivery_time": "4 a 6 semanas", "...": "..."},
           "products": [{"qa_item_id": 900, "partida": 1, "item": "1", "n_parte": "C9300-48P-E", "n_part": "C9300-48P-E",
                         "smart_account": false, "description": "Catalyst 9300 48 puertos PoE+", "service_months": null,
                         "delivery_time": "6 semanas", "quantity": 2, "price_unit": 5120.0, "total": 10240.0, "udm": "PZA",
                         "delivery_date": null, "...": "..."}]}],
 "msg": null, "error": null}
```

404 en el GET por id si no existe o no es CISCO (`error: "Quotation not found"`). `?with_costs=1` no aplica en estas rutas (usar `GET /quotation/<id>?with_costs=1`, que también devuelve las CISCO).

### `GET /quotation/-1` — cambio

| `format` | `document_type` | Devuelve |
|---|---|---|
| ausente | ausente / `quotation` | preventa **sin** CISCO (comportamiento de hoy para Preventa) |
| ausente | `ocd` | **todas** las OCD, CISCO incluidas |
| `cisco` | cualquiera | solo CISCO (combinable con `status` y `document_type`) |
| `all` | cualquiera | todas |
| otro | | 400 `msg: "format debe ser cisco o all"` |

### Gotchas

- `smart_account` sale como **bool** y `service_months` como entero o `null` (JSON nativo en `extra_info`); `n_parte` y `n_part` traen lo mismo (alias).
- El `PUT` es overwrite por partida: mandar una partida sin `smart_account` la deja en `false`; sin `delivery_time` la vacía.
- `item` se guarda como lo mandó el usuario tras `strip` (`"01"` y `"1"` son distintos); el orden visual lo decide el front (el back no ordena por `item`, solo numera `partida`).
- Una CISCO convertida en OCD con control de entregas activo tiene las mismas restricciones de partidas que cualquier OCD ([`control_entregas.md`](control_entregas.md)): quitar una partida entregada → 400.

## Al modificar

- **PDF FO-PRE-02 (`P-169`)**: en la descarga de PDF de cotización ramificar por `metadata.format == "cisco"` hacia una plantilla nueva (reportlab, skill `pdf-design`); los datos ya están: `concept`, `currency`, `delivery_time`, y por partida `item`, `n_part`, `smart_account`, `service_months`, `delivery_time`, `quantity`, `price_unit`.
- **Otro formato** (p. ej. `format = "servicios"`): agregar el valor a `QUOTATION_FORMATS` (`Functions_midleware_admin`), su prefijo a `QUOTATION_FOLIO_PREFIXES` y, si sus partidas difieren, un módulo `MD_Quotation<Formato>.py` gemelo de `MD_QuotationCisco`; `get_quotations(fmt=)` y el guard de `update_quoation_from_api` ya son genéricos.
- **Permitir el `PUT /quotation` grande sobre CISCO**: quitar el guard en `update_quoation_from_api` y hacer que `ProductsPutQuotationForm` declare `item`/`smart_account`/`service_months`/`delivery_time` (si no, el overwrite las borra).
- **Validar `item` en el form** (400 por campo en vez de lista): `Regexp(r"^\d+(\.\d+)?$")` en `ProductsQuotationCiscoForm.item`; la unicidad sigue en `cisco_items_errors`.

## Notas posteriores

- **2026-10-22 — PDF FO-PRE-02 (`P-169`)**: `GET /quotation/cisco/download/pdf/<id>` → [`cotizacion_cisco_pdf.md`](cotizacion_cisco_pdf.md). **Corrección**: la respuesta 3 y el "Al modificar" de este doc suponían un `GET /quotation/download/pdf/<id>` que imprimía el FO-PRE-01; **esa ruta nunca existió** y el back no genera PDF de cotización de preventa. De paso, `GET /quotation/cisco/<id>` (y `GET /quotation/<id>`) con un id inexistente respondía **400**; ahora **404**, como dice la tabla de arriba.
