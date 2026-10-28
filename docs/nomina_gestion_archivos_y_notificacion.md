# Nómina — gestión de archivos (reemplazar / eliminar), notificación in-app y extract de XML

> Pieza 1 del [`plan_mes_2.md`](planes/archivo/plan_mes_2.md) (S1, 2026-09-07). Completa el flujo de nómina sobre S3 de [`payroll_s3_upload.md`](payroll_s3_upload.md): el front nuevo hace **carga por periodo simulada** (RH asigna archivo→empleado en pantalla e itera el `POST` un archivo por request), y necesitaba **reemplazar**, **eliminar**, **avisar al empleado** dentro del sistema y, opcionalmente, **sugerir** empleado/periodo leyendo el XML del CFDI. `POST /payroll/mail` queda **deprecado**: creaba un borrador en Outlook (Graph) bajando adjuntos de SharePoint, donde ya no viven.

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
{"data": {"filename": "nomina.xml", "rfc": "XAXX010101000", "curp": "...", "num_empleado": "581", "nombre": "JUAN PEREZ LOPEZ",
          "periodo": {"inicio": "2026-09-01", "fin": "2026-09-15", "pago": "2026-09-15", "dias": "15", "tipo": "O"},
          "year_sugerido": 2026, "month_sugerido": 9, "emp_id_sugerido": 34, "match_by": "rfc", "nombre_sugerido": "Juan Perez Lopez"},
 "msg": "XML nomina.xml: JUAN PEREZ LOPEZ -> empleado sugerido 34", "error": null}
```
`emp_id_sugerido: null` + `match_by: null` = sin coincidencia (RH asigna a mano). `400` si no es `.xml` o no parsea como CFDI. Es una **sugerencia**: el front debe dejar corregirla antes del `POST` de subida.

`match_by` ∈ `"rfc"` (exacto) · `"curp"` (exacto) · `"nombre"` (aproximado) · `null`. Desde el 2026-10-28 ya no sale `"num_empleado"`: ese campo es el número del proveedor de nómina, no el `employee_id`, y queda solo como dato informativo (ver Notas posteriores).

### Deprecado

`POST /payroll/mail` **retirado el 2026-09-17** (responde 404; ver [`nomina_correo_ses.md`](nomina_correo_ses.md)). Hasta entonces seguía montado pero no debía llamarse: baja de SharePoint (falla) y solo crea un borrador en Outlook. Lo sustituye `/payroll/notify` y, en 2ª etapa, el correo por SES bajo el mismo endpoint (`channels: ["email"]`).

## Verificación

Smoke contra BD dev (2026-09-07) con S3 simulado (sin tocar el bucket) y el índice del empleado restaurado al final: 21 checks — subir/reemplazar (borra el anterior solo si cambió el nombre), forms (`kind` ausente/`null`/inválido), notificar con usuario (fila real en `notifications_gui`, luego borrada) y sin usuario, key inexistente, canal inválido, empleado sin fila, borrar pdf/both/inexistente, S3 caído → `200` con `s3_deleted: false`. Extract con un CFDI sintético: match por `NumEmpleado` y por nombre, XML roto → `400`, pdf → `400`. `pyrefly check` sin errores nuevos.

## Al modificar

- **Canal nuevo** (`email` real): agregar a `_PAYROLL_NOTIFY_CHANNELS` y su rama en `notify_payroll_file_api`; el contrato (`channels_sent`/`channels_pending`) ya lo contempla.
- **Cambiar la llave S3** (`payroll/<año>/<mes>/<emp>/<archivo>`): solo la construye `create_payroll_file_attachment_api`; borrado, notificación y descarga leen la llave del índice, no la recalculan.
- El índice `files_data` es **solo** `{año: {mes: {key: {pdf, xml}}}}`: no meter llaves de otro tipo (rompe `get_files_list_nomina`).

## Pendientes

- ~~**[back]** Correo por SES (2ª etapa)~~ — hecho (2026-09-17): [`nomina_correo_ses.md`](nomina_correo_ses.md); `/payroll/mail` y `create_mail_draft_with_attachment` retirados.
- ~~**[front]** Pantallas de carga por periodo, reemplazar/eliminar, notificar (+ mostrar `notified: false` por empleado) y lado empleado; link de WhatsApp (3ª etapa) armado en el front.~~ — hecho (`P-032`/`P-037`, front, 2026-10-12; ver Notas posteriores).
- ~~**[RH]** Formato en que llegan los archivos del proveedor (`P-136`).~~ — cerrado por decisión (2026-10-28): un PDF y un XML por empleado, nunca todos juntos.
- **[front]** Avisos en la carga masiva (dos grupos asignados al mismo empleado, XML de otro periodo, origen por RFC o CURP) y prueba con un lote real de varios empleados (`P-210`).
- ~~**[RH]** ¿Acuse de recibo del empleado en Mi nómina? (`P-211`).~~ — cerrado por decisión (2026-10-28): no hace falta.

## Notas posteriores

- **2026-10-12** (front, `P-032`/`P-037`): pantallas hechas. RH tiene la pantalla **Nómina** (`/dashboard/rrhh/nomina`) con carga masiva: cada XML pasa por `POST /payroll/files/extract` para sugerir el empleado, el PDF se empareja con su XML por nombre y se sube un archivo por request. También reemplazar, eliminar, notificar, "Notificar a todos" y el link de WhatsApp. El empleado tiene **Mi nómina** con la bandeja de avisos. El canal `email` está oculto hasta `P-036`. **Pregunta abierta para RH** (`P-136`): la carga supone un PDF y un XML por empleado; si el proveedor manda un solo PDF con todos los recibos, no lo cubre.
- **2026-10-13**: la descarga del empleado (`POST /common/payroll/employee/file`) ahora valida que las llaves sean del índice del `emp_id`, acepta solo `pdf` o solo `xml` y arma el zip por request → [`nomina_descarga_recibo.md`](nomina_descarga_recibo.md).
- **2026-10-23** (`P-175`): cambia el orden de la subida. El índice se lee antes de subir: sin fila responde **404** (antes 201 sin indexar) y con la BD caída tampoco sube. El anterior se borra **después** de guardar el índice. Si el `UPDATE` falla, el 400 trae `data: null` y el objeto nuevo se retira de S3. Además, el reemplazo y el `DELETE` ya no borran de S3 una llave que otro `key` del índice sigue usando. La regla "el índice nunca queda apuntando a un objeto que se intentó borrar" ahora también vale para el reemplazo → [`nomina_s3_huerfanos.md`](nomina_s3_huerfanos.md).
- **2026-10-27 — rutas S3 con entorno (`P-177`).** Las subidas nuevas van a `payroll/<entorno>/<año>/<mes>/<emp_id>/<quincena>/<archivo>`; las rutas guardadas antes siguen funcionando. El mismo nombre en Q1 y Q2 ya no comparte objeto. En dev y test, una entrada con ruta vieja se quita de la lista sin borrar el objeto (puede ser de prod; solo prod la borra) → [`s3_rutas_por_entorno.md`](s3_rutas_por_entorno.md).
- **2026-10-28 — revisión de la carga masiva con varios empleados (`P-210`).** El flujo es el de la nota del 2026-10-12: el front agrupa por nombre de archivo sin extensión (sin distinguir mayúsculas), manda cada XML, uno por uno, a `POST /payroll/files/extract` y sube un archivo por request, también en secuencia. Puntos encontrados:
  - **La sugerencia por nombre era aproximada.** `get_employee_id_name` usa `MATCH … AGAINST` en modo natural sobre `name` y `l_name`, sin ordenar por relevancia ni filtrar a los activos, y basta que coincida una palabra. Dos empleados que comparten nombre o apellido podían dar el equivocado. Se corrigió el mismo día con recibos reales; ver la nota siguiente.
  - **El front no avisa en dos casos.** Cuando dos grupos caen en el mismo empleado, el segundo reemplaza al primero en la quincena. Y tampoco compara el periodo del XML (`periodo`, `year_sugerido`, `month_sugerido`) con la quincena elegida. Los dos avisos quedan en `P-210`.
  - **La subida tiene que seguir en secuencia.** `create_payroll_file_attachment_api` lee el índice `files_data`, lo modifica y lo guarda completo (`update_payroll`). Si se subieran en paralelo el PDF y el XML de un mismo empleado, uno borraría al otro del índice. Si algún día se paraleliza, hay que pasar a `JSON_SET` atómico o agrupar por empleado.
- **2026-10-28 — emparejamiento por RFC y CURP, probado con recibos reales.** El usuario compartió dos recibos suyos (PDF y XML de la primera y la segunda quincena de junio de 2024; están en `scripts_db_handle/`, que está en `.gitignore`). Encontrado:
  - **`NumEmpleado` es el número del proveedor de nómina, no nuestro `employee_id`.** En los recibos sale 581 y el empleado es el 16. En dev los ids llegan hasta 123, así que hoy no chocaba con nadie. Pero la regla vieja (`NumEmpleado == employee_id`) habría sugerido a otra persona, marcada como "Por número de empleado", en cuanto un número del proveedor coincidiera con uno nuestro. **Se quitó.**
  - **El RFC y la CURP del XML coinciden exactamente con `employees.RFC` y `employees.CURP`.** En dev, 59 de 64 activos tienen ambos válidos y ningún RFC se repite entre activos.
  - **Formato:** un PDF y un XML por recibo, nombrados con el UUID del CFDI. El PDF va en mayúsculas y el XML en minúsculas, y la agrupación del front los empareja porque compara en minúsculas.
  - **Cambio en el API:** [`find_employee_for_payroll`](../templates/controllers/employees/employees_controller.py) busca así:
    1. RFC exacto;
    2. CURP exacta;
    3. el nombre, solo entre activos, ordenado por relevancia; si los dos primeros empatan, no sugiere a nadie.
    
    En RFC y CURP gana el activo: si solo hay un inactivo, lo sugiere y el front lo pinta "Sin coincidencia"; si hay dos activos con el mismo dato, pasa al siguiente criterio. `get_employee_id_name` no cambia, porque también lo usan fichajes y `Functions_Files`.
  - **Contrato:** `match_by` ahora vale `"rfc"`, `"curp"`, `"nombre"` o `null`. Ya no sale `"num_empleado"`, y el campo `num_empleado` sigue en la respuesta solo como dato informativo. El front tiene que mostrar "Por RFC" y "Por CURP" en la columna Origen: hoy un valor que no conoce lo pinta como "Asignado a mano". Va en `P-210`.
  - **Verificación:** `Tests/tester_nomina_match.py` da 20/20 contra dev.
    - Los dos recibos reales salen como empleado 16 por RFC, también por HTTP.
    - Variantes en memoria (en un directorio temporal que se borra): con RFC desconocido sale por CURP; con RFC y CURP desconocidos, por nombre; un `NumEmpleado` igual a un id existente se ignora; sin nada conocido no sugiere a nadie; el RFC de otro activo, en minúsculas y con espacios, le gana a la CURP y al nombre; con el RFC de un inactivo lo sugiere a él.
    - Con `execute_sql` en stub: el desempate y la BD caída.
    - pyrefly: 166 errores, sin cambio.
- **2026-10-28 — el PDF del recibo.** Se revisó el PDF de la primera quincena de junio de 2024 (`91F042D3-E911-471F-A624-11C821798101.pdf`, en `scripts_db_handle/`). Encontrado:
  - **Es la representación impresa del CFDI**, generada en **CONTPAQi Nóminas** (lo dice el pie). Tiene una sola hoja. RFC, CURP, `NumEmpleado` 581, periodo y neto coinciden con su XML. El "proveedor" de `P-136` es, entonces, el lote que RH exporta de CONTPAQi. **Decisión del usuario (mismo día):** llega un PDF y un XML por empleado, nunca todos juntos; `P-136` cerrado. La prueba con un lote real de varios empleados pasa a `P-210`.
  - **El API no lee el PDF:** lo guarda tal cual. La sugerencia de empleado y periodo sale solo del XML, así que un grupo que llegue sin XML se asigna a mano.
  - **La fecha del CFDI no es la del periodo.** El recibo de la segunda quincena se timbró el 2024-07-03 con `FechaPago` 2024-06-30. El extract toma año y mes de `FechaPago` y sugiere junio, que es lo correcto.
  - **Firma del empleado.** El recibo trae un renglón para la firma y una leyenda de conformidad. Mi nómina no tiene nada equivalente: `download_nomina_docs` no registra las descargas, y el `status` de la notificación solo dice que se leyó el aviso. **Decisión del usuario (mismo día):** no hace falta saber si el empleado recibió o descargó el archivo, así que nada cambia; `P-211` cerrado.
- **2026-10-28 — la carga masiva pierde los archivos de la selección anterior (`P-215`, front).** Reportado por el usuario: si RH elige primero los PDF y después, en otra selección, los XML, la lista se queda solo con los XML y los PDF desaparecen. Pasa porque `procesar` en `CargaNominaPeriodo.tsx` agrupa solo los archivos de la selección actual y termina con `setAsignaciones(salida)`, que reemplaza la lista. Lo esperado: **acumular** las selecciones hasta que RH suba o limpie.
  - Juntar lo nuevo con lo que ya estaba, por nombre base. Un XML que llega para un grupo que solo tenía PDF completa ese grupo, y ahí sí se lee el XML para sugerir al empleado.
  - Si RH ya eligió al empleado a mano, la sugerencia no lo cambia.
  - Un archivo repetido (mismo nombre base y tipo) reemplaza al anterior, sin duplicar el grupo.
  - Los ignorados también se acumulan, y hace falta un botón "Limpiar" para empezar de cero.
  - No toca al back: cada `POST /payroll/files/extract` es por XML y la subida es un archivo por request.
