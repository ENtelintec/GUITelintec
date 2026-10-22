# Reglas OCD: `client_po_number` obligatorio y único, `due_date`, `delivery_date` por partida y licitación ganada → OCD (`PUT /quotation/ocd`)

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (40/40 checks HTTP, `Tests/tester_ocd_rules.py`; regresión en verde: `tester_quotation_ocd` 35/35, `tester_tenders` 61/61, `tester_quotation_put_metadata` 18/18, `tester_quotation_costs` 37/37, `tester_quotation_cost_suggest` 22/22, `tester_delivery_control` 71/71, `tester_remission_pdf_ocd` 17/17). Sin DDL: todo vive en `quotations.metadata` y `quotation_items.extra_info` (JSON).**

Fase **F4** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "dos casos para generar OCD: desde una cotización de Telintec y desde una licitación ganada", "EXIROS opcional en OCD, el identificador de orden de compra obligatorio, equivalente a un número de contrato marco", "guardar fecha de entrega por item", "la fecha de vencimiento es el tiempo de entrega de la OCD"). Extiende [`quotation_ocd.md`](quotation_ocd.md) (F1 del plan anterior) y [`tenders_control.md`](tenders_control.md).

## Qué cambia

- **`client_po_number` obligatorio en una OCD**: `POST /quotation` con `document_type = ocd` y `PUT /quotation/ocd` responden 400 si el número resultante queda vacío. En un `PUT /quotation/ocd` que solo ajusta otra llave, vacío sigue significando "conservar", pero la OCD nunca puede quedar sin él. `pedido_exiros` de la remisión **sigue opcional**.
- **Único global entre OCD, como un número de contrato marco**: 409 si otra OCD ya usa el mismo `client_po_number`, comparado sin mayúsculas ni espacios al borde (`UPPER(TRIM(...))`, como la collation de `tender_number`). Vive en `metadata` JSON, así que el candado va en código (`find_ocd_by_client_po_number`), no en un `UNIQUE`. Aplica en `POST /quotation`, `PUT /quotation/ocd` y en el `PUT /quotation` grande **solo cuando cambia** la marca o el número (una OCD vieja sin número sigue editando partidas hasta que alguien toque el número o pase por `/ocd`).
- **`due_date`** (`YYYY-MM-DD`): sexta llave OCD de `metadata`, **capturada**, = vencimiento de la OCD = tiempo de entrega comprometido. `delivery_time` (texto) se conserva solo para el PDF. Aceptada en `POST /quotation`, `PUT /quotation` (conservada si no viene) y `PUT /quotation/ocd`; el GET la expone siempre (`""` en las viejas). La F5 la llevará al control de entregas (`days_to_due`, `validity_status`, aviso).
- **`delivery_date` por partida** (`YYYY-MM-DD`, opcional) en `quotation_items.extra_info`, aceptada en `POST`/`PUT /quotation`, `PUT /tender/items` y en el import de Excel (columna `FECHA ENTREGA` / `FECHA DE ENTREGA` / `ENTREGA`, fechas o texto `YYYY-MM-DD` / `DD/MM/YYYY`). Reglas: formato válido (400) y **nunca posterior a `due_date`** cuando la cotización lo tiene (400 listando partidas). Como las secciones, es **overwrite completo**: omitirla en un `PUT` la borra. Un `due_date` nuevo por `/ocd` que quede antes de fechas ya guardadas → 400 listando partidas. `GET /quotation/<id>` la devuelve en `products[].delivery_date` (`null` sin fecha).
- **Licitación ganada → OCD sobre su misma cotización interna**: `PUT /quotation/ocd` acepta una cotización `status 3` cuando su licitación está **asignada (`status 1`) y sin `contract_id`**; la cotización conserva `status 3`, `quotation_code = tender_number` (sin folio nuevo) y toma `tenders.po_number` como `client_po_number` por default (si la licitación no lo tiene y no viene en el body → 400 pidiéndolo). **Exclusión** en los dos sentidos: licitación con contrato → `/ocd` 400; licitación convertida a OCD → `POST /contract` 400 ("ya es una OCD"). Los catálogos de contrato (`status 1/2`) siguen sin convertirse. Descartado clonar la cotización (duplicaba partidas y análisis F6, y necesitaba DDL).
- `GET /tenders` y `GET /tender/<id>` ganan `document_type` (`quotation` | `ocd`) y `client_po_number` de su cotización interna (append-only).

## Capas tocadas

```
controller  contracts/quotations_controller.py   get_quotation: 'delivery_date' al FINAL del JSON_OBJECT (ambas ramas) · find_ocd_by_client_po_number · get_quotation_items_delivery_dates (nuevos)
controller  contracts/tenders_controller.py      TENDER_COLUMNS + document_type / client_po_number (append-only) · _SELECT lee q.metadata
midleware   Functions_midleware_admin.py         _OCD_DEFAULTS.due_date · _merge_ocd_keys valida due_date · _ocd_rule_errors / _ocd_conflict_envelope · items_delivery_date_errors / _stored_delivery_dates_after
                                                 _item_quotation_values escribe extra_info.delivery_date · create_quotation_from_api / update_quoation_from_api (reglas + fechas)
                                                 update_quotation_ocd_from_api (status 3 → licitación ganada, po default, 409, due_date vs partidas) · _tender_for_contract (exclusión OCD)
midleware   MD_Tenders.py                        _tender_to_dict (document_type, client_po_number) · update_tender_items_from_api valida delivery_date contra due_date
methods     Functions_Aux_Admin.py               read_exel_products_partidas: columna de fecha de entrega → products[].delivery_date
models      api_contracts_models.py              due_date en MetadataQuotationForm / QuotationOcdForm + api.model · delivery_date en ProductsPost/PutQuotationForm + api.model
```

`get_quotation` sigue con las primeras 12 llaves intactas (load-bearing para `compare_file_quotation`); `delivery_date` va al final.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permiso `administracion` en todo.
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400/409 de midleware, objeto por campo en 400 de form. 401: `{"error": "..."}` sin envelope.

### `PUT /quotation/ocd` — cambios

```json
{ "id_quotation": 51, "client_po_number": "4500123456", "currency": "MXN", "due_date": "2026-12-15", "approved_date": "2026-11-20" }
```

| Campo | Tipo | Notas |
|---|---|---|
| `client_po_number` | string | **obligatorio** para que la OCD exista (vacío = conservar el guardado; si no hay guardado → 400). Único global entre OCD |
| `due_date` | `YYYY-MM-DD` | vencimiento de la OCD; vacío conserva |
| `document_type`, `currency`, `delivery_time`, `approved_date` | | igual que [`quotation_ocd.md`](quotation_ocd.md) |

| Código | Cuándo | Ejemplo |
|---|---|---|
| **200** | aplicado | `data: {"id_quotation": 51, "document_type": "ocd", "client_po_number": "4500123456", "currency": "MXN", "delivery_time": "", "approved_date": "2026-11-20", "due_date": "2026-12-15", "changed": ["document_type", "client_po_number", "due_date"], "status": 0, "id_tender": null}` |
| **200** | licitación ganada convertida | igual, con `status: 3`, `id_tender: 7` y `client_po_number` = `po_number` de la licitación si no se mandó |
| **400** | sin número | `msg: "Datos OCD inválidos"` · `error: ["client_po_number es obligatorio en una OCD (identificador de la orden de compra del cliente)"]` |
| **400** | `due_date` inválida / anterior a fechas de partidas | `error: ["due_date: se esperaba una fecha YYYY-MM-DD"]` · `msg: "El vencimiento es anterior a fechas de entrega ya capturadas en las partidas"` + `error: ["partida 1: delivery_date 2027-01-10 es posterior al nuevo due_date 2026-12-31"]` |
| **400** | licitación no ganada / con contrato / catálogo de contrato | `msg: "La licitación no puede convertirse en OCD"` · `error: ["la licitación TL-2026-07 no está asignada (status 0); solo una licitación ganada se convierte en OCD"]` · `["... ya tiene el contrato 12; no puede ser también OCD"]` · `msg: "Solo una cotización de preventa o una licitación ganada se convierte en OCD"` |
| **409** | número repetido | `data: {"id_quotation": 51, "client_po_number": "4500123456", "conflict_quotation_id": 48}` · `msg: "Ya existe la OCD 48 con el identificador de orden de compra '4500123456'"` |
| **404** | cotización inexistente | |

### `POST /quotation` · `PUT /quotation` — cambios

- `metadata.due_date` (opcional, `YYYY-MM-DD`). En el `PUT` se conserva si no viene.
- `products[].delivery_date` (opcional, `YYYY-MM-DD`). **Overwrite completo**: re-enviar la que vino del GET; omitirla la borra.
- `POST` con `document_type: "ocd"`: `client_po_number` obligatorio (400) y único (409, mismo envelope que arriba). `PUT` grande: mismas reglas solo si cambia `document_type` o `client_po_number`.
- 400 `msg: "Fechas de entrega de partidas inválidas"` · `error: ["partida 2: delivery_date '15/12/2026' no es una fecha YYYY-MM-DD", "partida 1: delivery_date 2026-12-20 es posterior al vencimiento de la OCD (due_date 2026-12-15)"]`. Nada se escribe.

### `GET /quotation/<id>` · `GET /quotation/-1` — cambios

`metadata.due_date` siempre presente (`""` si no hay) y `products[].delivery_date` (`"2026-12-01"` | `null`).

### `PUT /tender/items` — cambio

`products[].delivery_date` con la misma validación contra el `due_date` de la cotización interna (400 `"Fechas de entrega de partidas inválidas"`).

### `GET /tenders` · `GET /tender/<id>` — cambio

Cada licitación trae `document_type` (`"quotation"` | `"ocd"`) y `client_po_number` (`""` si no hay). Con `"ocd"` el botón "Crear contrato" se oculta (el back responde 400) y el de "Convertir a OCD" ya no aplica; al revés, con `contract_id` se oculta "Convertir a OCD".

### `POST /contract` — cambio

Sobre la cotización interna de una licitación ya convertida a OCD → 400 `msg: "La licitación no puede pasar a contrato"` · `error: ["la licitación TL-2026-07 ya es una OCD (cotización 51); no se crea contrato"]`.

### `POST /contract/items/file` — cambio

Si el Excel trae una columna `FECHA ENTREGA` / `FECHA DE ENTREGA` / `ENTREGA`, cada partida sale con `delivery_date` (`YYYY-MM-DD` o `""`); el front la re-envía en `products[]`.

### Gotchas

- El 409 trae `data.conflict_quotation_id` para enlazar a la otra OCD; el número se compara sin mayúsculas ni espacios al borde pero **se guarda como lo mandó el usuario** (solo `strip`).
- Una licitación convertida a OCD sigue siendo `status 3`: sus partidas se editan con `PUT /tender/items`, no con `PUT /quotation` (400 como hoy); el control de entregas se crea con `POST /deliveryControl {quotation_id}` igual que con una OCD de preventa.
- Revertir (`document_type: "quotation"`) la cotización de una licitación está permitido mientras no tenga control de entregas activo; después vuelve a poder ir a contrato.
- `delivery_date` sin `due_date` en la cabecera se acepta (solo se valida el formato).

## Al modificar

- **Llave OCD nueva**: `_OCD_DEFAULTS` + validación en `_merge_ocd_keys` + los dos forms y los dos `api.model`; el GET, el merge y `changed` la toman de ahí.
- **Unicidad por cliente en vez de global** (si administración cambia de opinión): agregar `AND JSON_EXTRACT(metadata, '$.client_id') = %s` en `find_ocd_by_client_po_number` y pasar el `client_id` desde `_ocd_rule_errors`.
- **Bloquear la reversión de una licitación convertida**: en `update_quotation_ocd_from_api`, junto al guard del control de entregas, rechazar `document_type: quotation` cuando `tender` no sea `None`.
- **Fechas de partidas en el control de entregas** (F5): leerlas con `get_quotation_items_delivery_dates` o agregar `extra_info->>'$.delivery_date'` a la query de `_compute_items`; no duplicar la validación de formato (ya está en `items_delivery_date_errors`).
- Si `delivery_date` dejara de ser overwrite (merge por llave), cambiar `_item_quotation_values` y `update_item_quotation` juntos: hoy `extra_info` se reescribe completo en cada `PUT`.
