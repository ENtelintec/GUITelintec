# Remisión de OCD: los seis campos de texto opcionales y marca "sin anexos" (`PUT /remission/noAttachments`)

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (25/25 checks HTTP, `Tests/tester_remission_no_attachments.py`, con S3 simulado; regresión en verde: `tester_remission_cancel` 32/32, `tester_control_saldos_sin_contrato` 50/50, `tester_remission_files_cas` 19/19, `tester_delivery_control` 71/71, `tester_remission_pdf_ocd` 17/17, `tester_balance_vencido` 33/33). Sin DDL.**

Fase **F6** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "no se necesita actividad, descripción general, área y ubicación en las remisiones de órdenes de compra directa" y "agregar una opción a las remisiones de que no hay anexos"). Extiende [`control_table_operaciones_y_campos_admin.md`](control_table_operaciones_y_campos_admin.md) (campos del módulo que el back no exige) y [`remission_combined_pdf.md`](remission_combined_pdf.md) / [`remission_anexos_sin_carrera.md`](remission_anexos_sin_carrera.md) (anexos en `activity_reports.files`).

## Qué cambia

- **Seis campos opcionales en el back**: `plant`, `activity`, `location`, `general_description`, `comments` y `area` dejan de ser `InputRequired` en `POST`/`PUT /remission` y `POST`/`PUT /remissionControlTable` (default `""`). El back **no distingue flujos**: el front los exige en pantalla cuando la remisión tiene contrato (flujo Ternium) y los oculta en una remisión de OCD. Los obligatorios de siempre (`date`, `folio`, `client_id`) no cambian. Las columnas ya eran NULL-ables; el PDF y los GET ya toleraban vacíos.
- **Marca "sin anexos"**: `extra_info.no_attachments` (bool), para que la pantalla recuerde la decisión de administración y deje de pedir anexos. Nuevo **`PUT /remission/noAttachments {id, no_attachments}`**, **solo `administracion`**. Reglas:
  - marcar `true` con anexos reales (cualquier archivo de `files` que no sea firma) → **400** listando los archivos;
  - repetir el mismo valor → 200 sin escribir (idempotente); sobre una remisión cancelada → 400; inexistente → 404;
  - cada cambio deja una entrada en `history` con `changes.metadata[{field: "no_attachments", before, after}]`;
  - **subir un anexo que no sea firma a una remisión marcada quita la marca sola** (history propio, `no_attachments_cleared: true` en el 201 de la subida) en vez de rechazar la subida; las firmas no la tocan;
  - los demás módulos (`PUT /remissionBalance`, `/remissionControlTable`, `/remission`) **no la borran**: escriben solo sus llaves de `extra_info` ([`remission_atomic_writes.md`](remission_atomic_writes.md)).
- **`GET /remission-<id>`** expone `no_attachments` (bool, `false` si la llave no existe) en cada fila. Sin efecto en el PDF (`?full=1` sigue combinando lo que haya), en saldos ni en entregas.

## Capas tocadas

```
models      api_purchases_models.py          MetadataControlTableRemissionForm: plant/activity/location/general_description/comments opcionales · MetadataActivityReportForm.area opcional
                                             basic_control_table_report_model / basic_metadata_activity_model: required=False en los mismos
                                             report_activity_no_attachments_model + ReportActivityNoAttachmentsForm (nuevos)
midleware   MD_Admin_Collections.py          set_remission_no_attachments_from_api (nuevo) · GET aplana no_attachments · create_activity_report_attachment_api quita la marca al adjuntar
routes      rs_Admin_collections.py          PUT /remission/noAttachments (administracion)
```

La presencia de `no_attachments` en el JSON la exige el midleware (recibe el payload crudo): un `BooleanField` no distingue ausente de `false`, y una omisión no debe desmarcar por accidente.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400 de midleware, objeto por campo en 400 de form. 401: `{"error": "..."}` sin envelope.

### `POST`/`PUT /remission` · `POST`/`PUT /remissionControlTable` — cambios

`plant`, `activity`, `location`, `general_description`, `comments` y `area` pueden **omitirse o ir vacíos**; el back guarda `""`. Para una remisión de OCD basta `metadata: {date, folio, client_id, delivery_control_id?}` (+ `items` con `item_contract_id` en `POST /remission`). Permisos sin cambio. El front decide por flujo: con `contract_id`, exigirlos en pantalla como hoy.

### `PUT /remission/noAttachments` — nuevo (solo `administracion`)

```json
{ "id": 71, "no_attachments": true }
```

| Código | Cuándo | Respuesta |
|---|---|---|
| **200** | marcada / desmarcada | `data: {"id_remission": 71, "no_attachments": true, "attachments_count": 0}` · `msg: "Remisión 71 (folio TL-0045-001) marcada como sin anexos"` |
| **200** | ya tenía ese valor (nada se escribe) | `msg: "La remisión 71 ya estaba marcada como sin anexos"` |
| **400** | `true` con anexos reales | `data: {"id_remission": 71, "no_attachments": false, "attachments": ["foto-evidencia.jpg"]}` · `msg: "La remisión 71 ya tiene 1 anexo(s); no se puede marcar sin anexos"` · `error: ["anexo: foto-evidencia.jpg"]` |
| **400** | falta `no_attachments` en el body | `error: ["no_attachments (true|false) es obligatorio"]` |
| **400** | remisión cancelada | `msg: "La remisión 71 está cancelada; no se puede marcar sin anexos"` |
| **404** | remisión inexistente | `msg: "No se encontró la remisión (ID 999)"` |
| **401** | sin `administracion` | `{"error": "..."}` |

### `POST /remission/attachment-<id>` — cambio

El 201 gana `data.no_attachments_cleared` (bool): `true` cuando el anexo subido quitó la marca (solo anexos que no sean firma). El front repinta la casilla con ese valor o con el `no_attachments` del siguiente GET.

### `GET /remission-<id>` — cambio

Cada fila trae `no_attachments` (bool). Con la marca en `true` la pantalla no pide anexos ni los señala como faltantes.

### Gotchas

- Las **firmas** (`category: firma` o nombre `firma-*`) no cuentan como anexos: una remisión firmada sin reporte puede marcarse "sin anexos".
- Si administración marca y después Operaciones sube el reporte, la marca desaparece sola; para volver a marcar hay que **borrar** el anexo primero (`DELETE /remission/attachment-<id>`), y el back volverá a responder 400 mientras exista.
- Una remisión cancelada conserva el valor que tenía; no se puede cambiar.

## Al modificar

- **Qué cuenta como anexo real**: un solo lugar, `_classify_remission_file` (categoría efectiva); `set_remission_no_attachments_from_api` y el hook de subida comparan contra `"firma"`.
- **Pedir motivo** (si administración lo quiere después): agregar `reason` al form y al modelo, guardarlo en `extra_info.no_attachments_reason` en el mismo `patch_activity_report` y mostrarlo en el GET; sin DDL.
- **Borrar un anexo no re-marca** a propósito (decisión 2026-10-22: la marca la pone administración). Si se quisiera, iría en `delete_activity_report_attachment_api` con la misma receta del hook de subida.
- Volver a exigir alguno de los seis campos para un flujo: hacerlo en el **front**; en el back solo volvería como validación condicional por `contract_id`, que se descartó en el grill.
