# Payroll file upload → S3 (`/payroll/files/update`)

Endpoint que sube archivos de nómina (pdf/xml) a un bucket S3 de RH.
Reemplaza el flujo anterior que escaneaba SharePoint con un daemon.

## Endpoint

`POST /GUI/api/v1/rrhh/payroll/files/update` — `multipart/form-data`, depto `rrhh`.

| Campo | Tipo | Notas |
|-------|------|-------|
| `file` | archivo | **pdf o xml únicamente** (se rechaza lo demás con 400) |
| `year` | form | ej. `2025` |
| `month` | form | numérico, se normaliza a 2 dígitos `01`–`12` |
| `emp_id`| form | id del empleado |
| `key`   | form | identificador de la nómina; agrupa el par pdf+xml |

Un archivo por request. El tipo (pdf/xml) se detecta por la extensión.
Para subir el par, se hacen 2 requests con el mismo `key` (uno xml, uno pdf).

Respuesta: `{"data": <s3_key>, "msg": ...}` con `201` en éxito.

## S3

- Bucket: `secrets.get("S3_RH_BUCKET")` (clave en `.env`).
- Key: `payroll/<year>/<month>/<emp_id>/<filename>`.
- Prefijo `payroll/` para separar de otros archivos de RH en el mismo bucket.

## Índice en BD

Tras subir, se actualiza el registro del empleado en la tabla `payroll`
(columna `files_data`, JSON) vía `update_payroll`:

```
files_data[year][month][key][<pdf|xml>] = "payroll/<year>/<month>/<emp_id>/<filename>"
```

Así `/payroll/files/list/<emp_id>` y el envío de correos siguen encontrando los archivos.

## Descarga (migrada a S3)

`POST /GUI/api/v1/common/payroll/employee/file` → `download_nomina_docs`.
Body JSON (`RequestFileForm`): `emp_id`, `pdf`, `xml`, donde `pdf`/`xml` son los
**keys S3** que devuelve el endpoint de listado (`files_data[year][month][key]`).
Descarga ambos desde `S3_RH_BUCKET`, los empaqueta en zip y responde `send_file`.
Si un key viene vacío o falla la descarga, se omite; si no baja ninguno → 400.

## Capas tocadas

- `static/Models/api_payroll_models.py` — `update_files_parser` (api.parser multipart). Se eliminó `update_files_model` / `UpdateFilesForm`.
- `templates/resources/midleware/Functions_midleware_RRHH.py` — `create_payroll_file_attachment_api` (subida) y `download_nomina_docs` migrado a S3. Se eliminó `update_files_payroll` (daemon SharePoint).
- `templates/resources/rs_RRHH.py` — `FilesPayroll.post` lee `request.files`/`request.form` (patrón de `UploadActivityReportAttachment`). Se quitó el trigger del daemon y el guard `update_files_nomina`.
- `templates/resources/rs_Common.py` — `DownloadFilesPayroll` sin cambios (contrato igual; solo cambió la fuente en el midleware).

## Pendiente / notas

- `.env` debe tener `S3_RH_BUCKET` (reiniciar app tras editar `.env`).
- La clase daemon `UpdaterSharepointNomina` queda sin uso pero no se borró.
- **Pendiente**: `create_mail_payroll` aún descarga adjuntos desde SharePoint
  (`download_files_site`); migrarlo a S3 es un cambio aparte. La BD ya guarda
  el key S3, así que recibirá keys S3 que no existen en SharePoint hasta migrar.
