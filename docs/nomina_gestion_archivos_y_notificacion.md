# Nómina — gestión de archivos (reemplazar / eliminar), notificación in-app y extract de XML

> Pieza 1 del [`plan_mes_2.md`](plan_mes_2.md) (S1, 2026-09-07). Completa el flujo de nómina sobre S3 de [`payroll_s3_upload.md`](payroll_s3_upload.md): el front nuevo hace **carga por periodo simulada** (RH asigna archivo→empleado en pantalla e itera el `POST` un archivo por request), y necesitaba **reemplazar**, **eliminar**, **avisar al empleado** dentro del sistema y, opcionalmente, **sugerir** empleado/periodo leyendo el XML del CFDI. `POST /payroll/mail` queda **deprecado**: creaba un borrador en Outlook (Graph) bajando adjuntos de SharePoint, donde ya no viven.

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_RRHH.py`](../templates/resources/rs_RRHH.py) | Rutas nuevas `DELETE /payroll/files`, `POST /payroll/notify`, `POST /payroll/files/extract`; `/payroll/mail` marcado deprecado (sigue montado). |
| **Orquestación** | [`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) | `create_payroll_file_attachment_api` gana **reemplazo** (borra el objeto anterior del mismo `key`+`kind` si cambió el nombre); nuevos `delete_payroll_file_api`, `notify_payroll_file_api`, `extract_payroll_xml_api`; helpers `_load_payroll_index`, `_payroll_s3_delete`, `_normalize_payroll_period`. **Quitado el guard muerto** `flags_daemons["update_files_nomina"]` de `create_mail_payroll` y `update_payroll_list_employees` (el daemon de SharePoint ya no existe y el flag bloqueaba la sincronización). |
| **DB** | [`payroll_controller.py`](../templates/controllers/payroll/payroll_controller.py) (sin cambios) · [`us_controller.py`](../templates/controllers/employees/us_controller.py) `get_user_by_emp_id` (nuevo) · [`employees_controller.py`](../templates/controllers/employees/employees_controller.py) `find_employee_for_payroll` (nuevo) | El índice sigue siendo `payroll.files_data` JSON (`[año][mes][key][pdf\|xml]`); la notificación va a `notifications_gui` con `receiver_id = emp_id`. |
| **Modelos** | [`api_payroll_models.py`](../static/Models/api_payroll_models.py) | `delete_payroll_file_model`/`DeletePayrollFileForm`, `notify_payroll_model`/`NotifyPayrollForm`, `extract_xml_parser`. |

### Reglas

- **Reemplazar = el `POST` de siempre.** Mismo `key` + mismo tipo (`pdf`/`xml`) con **otro** nombre de archivo → se sube el nuevo, se apunta el índice y se borra el objeto anterior de S3 best-effort (`msg` lo dice; si S3 falla, `error` trae el motivo y el índice ya apunta al nuevo). Con el **mismo** nombre, S3 lo pisa en el upload (misma llave), no hay borrado extra.
- **Eliminar**: BD primero, S3 después. Si S3 falla → `200` con `s3_deleted: false` + motivo en `error`; el índice **nunca** queda apuntando a un objeto que se intentó borrar. El `key` desaparece del mes si queda vacío, el mes del año y el año del índice.
- **Notificar**: crea una notificación in-app al empleado (`receiver_id = emp_id`, `app: []` para que no la vean por permiso, `payload` con año/mes/key/files). Si el empleado **no tiene usuario** en `users_system` → `201` con `notified: false` y `reason` (no hay a quién notificar; es la razón de la 2ª etapa por correo). `channels` acepta `"email"` desde hoy pero lo reporta en `channels_pending` (SES, 2ª etapa) sin cambiar el contrato.
- **Extract**: solo **sugiere**. Empleado por `NumEmpleado` numérico igual a `employee_id` (exacto, `match_by: "num_empleado"`) o por nombre del receptor con `get_employee_id_name` (fulltext, `match_by: "nombre"`); año/mes sugeridos desde `FechaPago`. No sube ni guarda nada.
- **De paso**: `get_employee_id_name` y `get_id_employee` **siempre devolvían `None`** (comparaban `e is not None` cuando `execute_sql` devuelve el error como el string `"None"`); corregidos. Beneficia también a los callers de fichajes (ahora sí resuelven nombres de los archivos). `Functions_Files.py:1199` llamaba a `get_employee_id_name(name)` sin `data_token` (TypeError latente) → `(name, None)`.
- Sin `history` dentro de `files_data`: `get_files_list_nomina` itera sus llaves como años, una llave extra rompería el listado. El rastro va a `log_file_rh`.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`). Permiso `rrhh` en todo lo de abajo; el lado empleado (`/common/payroll/employee/*`) ya existía y es auto-acceso.
- **Base**: `/GUI/api/v1/rrhh`. Envelope `{data, msg, error}`. Multipart = **un archivo por request**.
- `month` se normaliza a 2 dígitos (`9` → `"09"`); las quincenas se distinguen por `key` (convención del front, p.ej. `2026-09-Q1`); el par pdf+xml son dos `POST` con el mismo `key`.

### `POST /payroll/files/update` (existente, ahora reemplaza)

Multipart `file` (pdf/xml) + form `year`, `month`, `emp_id`, `key`. `201`:
```json
{"data": "payroll/2026/09/34/recibo.pdf", "msg": "Archivo de nomina recibo.pdf (pdf) subido para el empleado 34 en 2026/09 (key 2026-09-Q1); reemplaza a payroll/2026/09/34/recibo_viejo.pdf (Objeto eliminado de S3)", "error": null}
```
`error` ≠ `null` solo si el borrado del anterior en S3 falló (el índice ya apunta al nuevo). `400` extensión inválida / campos faltantes / S3.

### `DELETE /payroll/files`

Body JSON `{"emp_id": 34, "year": 2026, "month": 9, "key": "2026-09-Q1", "kind": "pdf"}` — `kind` ∈ `"pdf" | "xml" | "both"`; ausente o `null` = `both`.
```json
// 200
{"data": {"emp_id": 34, "year": "2026", "month": "09", "key": "2026-09-Q1", "deleted": ["payroll/2026/09/34/recibo.pdf"], "s3_deleted": true, "files_data": {"2026": {"09": {"2026-09-Q1": {"xml": "payroll/2026/09/34/recibo.xml"}}}}},
 "msg": "Nómina 2026-09-Q1 de 09/2026 del empleado 34: pdf eliminado del índice (Objeto eliminado de S3)", "error": null}
// 200 con S3 caído: mismo shape, "s3_deleted": false y "error": "<motivo>"
// 400 {"data": null, "msg": "La nómina 2026-09-Q1 de 09/2026 no tiene archivo pdf", "error": null}   (o "No existe la nómina ...", o kind inválido)
// 404 {"data": null, "msg": "El empleado 999 no tiene registro de nómina", "error": ...}
```
`data.files_data` es el índice **ya actualizado** del empleado: repintar sin re-`GET`.

### `POST /payroll/notify`

Body `{"emp_id": 34, "year": 2026, "month": 9, "key": "2026-09-Q1", "message": "opcional", "channels": ["app"]}` — `channels` ausente/`[]` = `["app"]`; válidos `app`, `email`.
```json
// 201 notificado
{"data": {"emp_id": 34, "year": "2026", "month": "09", "key": "2026-09-Q1", "notified": true, "id_notification": 4855, "reason": null, "channels_sent": ["app"], "channels_pending": []},
 "msg": "Empleado 34 notificado de la nómina 2026-09-Q1 (09/2026)", "error": null}
// 201 sin usuario (NO es error: mostrar reason por empleado)
{"data": {"...": "...", "notified": false, "id_notification": null, "reason": "El empleado 12 no tiene usuario en el sistema: no puede recibir la notificación", "channels_sent": [], "channels_pending": []}, "msg": "Nómina ... sin notificar. El empleado 12 no tiene usuario ...", "error": null}
// 400 key sin archivos / canal inválido · 404 empleado sin fila de nómina
```
Con `"channels": ["app", "email"]` hoy responde `channels_pending: ["email"]` (2ª etapa). El empleado ve la notificación en `GET /misc/notifications/employee/<emp_id>&0` (title `Recibo de nómina disponible`, `payload.files` con los keys S3 para bajar con `POST /common/payroll/employee/file`).

### `POST /payroll/files/extract`

Multipart `file` = XML del CFDI. `200`:
```json
{"data": {"filename": "nomina.xml", "rfc": "XAXX010101000", "curp": "...", "num_empleado": "34", "nombre": "JUAN PEREZ LOPEZ",
          "periodo": {"inicio": "2026-09-01", "fin": "2026-09-15", "pago": "2026-09-15", "dias": "15", "tipo": "O"},
          "year_sugerido": 2026, "month_sugerido": 9, "emp_id_sugerido": 34, "match_by": "num_empleado", "nombre_sugerido": "Juan Perez Lopez"},
 "msg": "XML nomina.xml: JUAN PEREZ LOPEZ -> empleado sugerido 34", "error": null}
```
`emp_id_sugerido: null` + `match_by: null` = sin coincidencia (RH asigna a mano). `400` si no es `.xml` o no parsea como CFDI. Es una **sugerencia**: el front debe dejar corregirla antes del `POST` de subida.

### Deprecado

`POST /payroll/mail` sigue montado pero **no debe llamarse**: baja de SharePoint (falla) y solo crea un borrador en Outlook. Lo sustituye `/payroll/notify` y, en 2ª etapa, el correo por SES bajo el mismo endpoint (`channels: ["email"]`).

## Verificación

Smoke contra BD dev (2026-09-07) con S3 simulado (sin tocar el bucket) y el índice del empleado restaurado al final: 21 checks — subir/reemplazar (borra el anterior solo si cambió el nombre), forms (`kind` ausente/`null`/inválido), notificar con usuario (fila real en `notifications_gui`, luego borrada) y sin usuario, key inexistente, canal inválido, empleado sin fila, borrar pdf/both/inexistente, S3 caído → `200` con `s3_deleted: false`. Extract con un CFDI sintético: match por `NumEmpleado` y por nombre, XML roto → `400`, pdf → `400`. `pyrefly check` sin errores nuevos.

## Al modificar

- **Canal nuevo** (`email` real): agregar a `_PAYROLL_NOTIFY_CHANNELS` y su rama en `notify_payroll_file_api`; el contrato (`channels_sent`/`channels_pending`) ya lo contempla.
- **Cambiar la llave S3** (`payroll/<año>/<mes>/<emp>/<archivo>`): solo la construye `create_payroll_file_attachment_api`; borrado, notificación y descarga leen la llave del índice, no la recalculan.
- El índice `files_data` es **solo** `{año: {mes: {key: {pdf, xml}}}}`: no meter llaves de otro tipo (rompe `get_files_list_nomina`).

## Pendientes

- **[back]** Correo por SES (2ª etapa): mismo `POST /payroll/notify` con `channels: ["email"]`; retirar `/payroll/mail` y `create_mail_draft_with_attachment`.
- **[front]** Pantallas de carga por periodo, reemplazar/eliminar, notificar (+ mostrar `notified: false` por empleado) y lado empleado; link de WhatsApp (3ª etapa) armado en el front.
