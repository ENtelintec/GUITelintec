# Campos por módulo en remisiones y endpoint de control de saldos

Implementa los requerimientos de [`campos_remisiones.md`](campos_remisiones.md): cada módulo del front
(REMISIONES, Control de Reportes con sus bloques operaciones/administración, y CONTROL SALDOS) escribe su
propio set de campos sobre la **misma fila** de `activity_reports`, acumulándolos en la columna JSON
`extra_info`. Se agrega el endpoint `PUT /remissionBalance` para control de saldos.

## Mapeo módulo → endpoint

| Módulo del front | Endpoint | Verbos |
| --- | --- | --- |
| REMISIONES | `/admin/collections/remission` | POST / PUT / DELETE |
| Control de Reportes (operaciones + administración) | `/admin/collections/remissionControlTable` | POST / PUT |
| CONTROL SALDOS | `/admin/collections/remissionBalance` | **solo PUT** (no crea remisiones) |
| Lectura (todos los módulos) | `GET /admin/collections/remission-<id>` | un solo GET expone todo `extra_info` aplanado; cada front filtra lo suyo |

## Capas tocadas

1. **HTTP** — [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py): ruta nueva
   `/remissionBalance` (PUT); `POST /remissionControlTable` ahora llama a
   `create_remission_control_table_from_api` (antes llamaba a `create_remission_from_api`, que accede a
   `data["items"]` y tronaba con `KeyError` porque el form de control table no tiene items); los PUT pasan
   `raw_metadata = ns.payload.get("metadata") or {}` al midleware para el merge por llaves presentes.
2. **Orchestración** — [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py):
   mapas de llaves por módulo (`_REMISSION_EXTRA_KEY_MAP`, `_CONTROL_EXTRA_KEY_MAP`,
   `_BALANCE_EXTRA_KEY_MAP`), helper `_extra_info_updates`, función nueva
   `update_remission_balance_from_api`; se eliminó `create_extra_info_remision`.
3. **DB** — sin cambios de esquema ni de controllers: todo va a la columna `extra_info` (JSON) existente.
4. **Validación/swagger** — [`api_purchases_models.py`](../static/Models/api_purchases_models.py): campos
   nuevos opcionales en los forms de remisión/control table, forms nuevos
   `MetadataRemissionBalanceForm`/`RemissionBalanceUpdateForm` y sus `api.model` espejo.

## Reglas de escritura sobre `extra_info`

- **Ningún campo nuevo es obligatorio en el back** (solo se valida tipo); el front decide cuándo exigirlos.
  Los campos de estatus llegan como **integer** (0, 1, 2, …); el catálogo de etiquetas vive en el front.
- **Merge por módulo**: cada endpoint escribe únicamente las llaves de su mapa y preserva las demás
  (así los módulos se acumulan sin pisarse). El PUT de `/remission` antes reemplazaba `extra_info`
  completo — eso borraba lo capturado por control/saldos; ahora mergea.
- **Merge por llaves presentes (solo PUT)**: `_extra_info_updates` revisa el JSON crudo (`raw_metadata`);
  una llave que el front no incluyó **no se toca**, y enviarla como `""`/`null` la vacía a propósito.
  En POST se escriben todas las llaves del módulo (no hay nada previo que preservar).
- `/remissionBalance` **no toca columnas base** (`date`, `folio`, `client_id`, …): las reenvía tal cual
  desde la fila leída; solo el `extra_info` mergeado y el `history` cambian.

## Nombres canónicos (resolución de alias del doc de requerimientos)

Llave del payload → llave canónica en `extra_info` (el GET la expone aplanada con el nombre canónico):

| Concepto en el doc | Payload API | Canónico en `extra_info` | Notas |
| --- | --- | --- | --- |
| Total sin IVA (`totalSinIva / totalsiniva`) | `totalSinIva` | `total_sin_iva` | number |
| Estatus de reporte (`statusReport`) | `statusReport` | `status_report` | integer |
| Monto remisión / Proyección saldo (`remission_amount / projection_balance`) | `projection_balance` | `projection_balance` | un solo campo; `remission_amount` no existe |
| OT / Número de tickets (`ot_ticket_number`) | — | — | **no se guarda**: es columna combinada de display; el front la arma con `ot` + `ticket_number` |
| OT | `ot` | `ot` | separado de tickets |
| Número de tickets | `ticket_number` | `ticket_number` | separado de OT |
| Solicitante / Coordinador | `requester_coordinator` | `requester_coordinator` | campo aparte de `coordinator` |
| Coordinador | `coordinator` | `coordinator` | |
| No. cotización (texto de saldos) | `quotation_number` | `quotation_number` | texto libre, independiente del FK `quotation_id` |
| Monto de cotización | `quotation_amount` | `quotation_amount` | number |
| Remitos (saldos) | `remitos` | `remitos` | distinto de `remito` (remisión) |
| Campos por contrato | — | — | no es un objeto passthrough: indica que el campo depende del contrato; si el contrato no lo maneja, llega vacío |

El resto de campos usa el mismo nombre en payload y en `extra_info`.

### Set de llaves por endpoint

- **`/remission`** (`_REMISSION_EXTRA_KEY_MAP`): `pedido`, `pedido_exiros`, `activity`, `remision`,
  `remito`, `date_delivery`, `user`, `user_id`, `project`, `project_description`, `request_date`,
  `infra_responsible`, `remission_sent_date`.
- **`/remissionControlTable`** (`_CONTROL_EXTRA_KEY_MAP`): `pedido`, `activity`, `remision`, `remito`,
  `user`, `user_id`, `total_sin_iva`, `status_report`, `date_report`, `date_sign`, `date_office`,
  `received_date`, `status_rep_admi`, `remission_sent_date`, `remission_sent_by`, `remission_total`.
- **`/remissionBalance`** (`_BALANCE_EXTRA_KEY_MAP`): `pedido`, `remision`, `remito`, `remitos`,
  `request_date`, `infra_responsible`, `remission_status`, `remission_sent_date`, `remission_send_time`,
  `remission_upload_date`, `remission_upload_time`, `hes_status`, `hes_number`, `hes_release_date`,
  `hes_balance`, `projection_balance`, `committed_balance`, `invoiced_balance`, `observations`,
  `month_period`, `requester_coordinator`, `coordinator`, `ceco_fap`, `sgd_number`, `sgd_upload_date`,
  `sgd_upload_time`, `general_status`, `ot`, `ticket_number`, `quotation_number`, `quotation_amount`,
  `activity_end_date`.

Las llaves compartidas entre módulos (`pedido`, `remision`, `remito`, `remission_sent_date`, …) son el
mismo concepto: gana la última escritura del módulo que las envíe (last-write-wins).

## Historial

`PUT /remissionBalance` agrega una entrada al `history` de la remisión ("Actualización de control de
saldos.") con el diff curado de `changes.metadata` (mismo formato de
[`remission_history_changes.md`](remission_history_changes.md)). Todos los campos canónicos nuevos se
agregaron a `_HISTORY_EXTRA_FIELDS`/`_HISTORY_META_FIELDS`, por lo que los diffs de los tres endpoints los
vigilan; los numéricos/estatus se normalizan a float en `_HISTORY_NUMERIC_FIELDS`.

## Bugs corregidos de paso

- `POST /remissionControlTable` tronaba con `KeyError: 'items'` (llamaba al midleware equivocado).
- `extra_info["project"]` se guardaba como tupla (`(valor,)`) por una coma extra; el GET normaliza los
  registros legados que quedaron como lista.
- `quotation_id or quotation_id > 0` lanzaba `TypeError` cuando `quotation_id` era `None`
  (ahora `and`), en el PUT de `/remission` y el create de control table.
- El swagger de `basic_metadata_activity_model` pasaba su dict de campos al parámetro `mask` de
  `api.model` (dos dicts posicionales); ahora usa `api.inherit`.

## Al modificar

- **Agregar un campo nuevo a un módulo**: agregarlo en 4 lugares — el WTForms del endpoint, su `api.model`
  espejo, el mapa `_*_EXTRA_KEY_MAP` del módulo (payload → canónico) y, si debe vigilarse en el historial,
  `_HISTORY_EXTRA_FIELDS` (más `_HISTORY_NUMERIC_FIELDS` si es numérico). Para exponerlo en el GET,
  agregarlo a `_GET_EXTRA_STRING_FIELDS` o `_GET_EXTRA_NUMERIC_FIELDS`.
- **No** volver a reemplazar `extra_info` completo en ningún update: siempre `dict(old)` + `update(...)`.
- Si un PUT nuevo necesita merge parcial, recibir `raw_metadata` desde el resource y pasarlo a
  `_extra_info_updates`; con `raw_metadata=None` se escriben todas las llaves del mapa (comportamiento de
  POST).
