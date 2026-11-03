# Retiro de Fichajes de RH y de SharePoint (6 endpoints a 404, `Office365-REST-Python-Client` fuera)

Fecha: 2026-10-29 · **Estado: back hecho y verificado en dev** (`import wsgi` sin cargar `office365`; `GET /GUI/health` y `/swagger.json` en 200; los 6 endpoints responden 404; las 5 rutas `/bitacora/fichaje*` siguen montadas; `pyrefly check` sin errores nuevos contra `c6cae15`, 29 menos). Falta el front (`P-227`) y la limpieza en el servidor (`P-229`).

Decisión del usuario: `templates/Functions_Sharepoint.py` sobra en el repo, y con él **todo lo de Fichajes de RH**. El código retirado de fichajes **no se borra todavía**: queda fuera de git en `C:\Users\L03508427\PycharmProjects\GUITelintec_legacy\fichajes\` (README, bloques extraídos de `c6cae15` y el `.patch` del cambio) y se borra cuando exista la implementación nueva (`P-228`).

## Por qué

- **SharePoint ya no se usaba.** Nómina vive en S3 desde [`payroll_s3_upload.md`](payroll_s3_upload.md). Lo único que seguía llamando a `Functions_Sharepoint.py` era `update_data_docs_nomina` (solo la llamaba el daemon `UpdaterSharepointNomina`, que nadie arrancaba) y la pantalla de Fichajes.
- **La pantalla de Fichajes estaba rota.** `GET /rrhh/fichajes/files` listaba los Excel del biométrico en SharePoint y daba 400 desde la prueba del front del 2026-08-07. `POST /rrhh/upload/fichaje/file` guardaba en `files/contracts`, así que el archivo subido nunca salía en la lista.
- La asistencia desde la app ya es el check-in con foto ([`checkin_foto.md`](checkin_foto.md)). Fichajes se rehace después con código nuevo.

## Qué se retiró

| Método y ruta (`/GUI/api/v1`) | Permiso que lo abría | Qué hacía |
|---|---|---|
| `GET /rrhh/fichajes/files` | `App.Department.RRHH` | Lista de Excel `Fichaje_<fecha>` / `Ternium_<fecha>` en SharePoint |
| `POST /rrhh/fichajes/data/fromfiles` | `App.Department.RRHH` | Bajaba esos Excel y calculaba faltas, retardos y extras contra la bitácora |
| `POST /rrhh/upload/fichaje/file` | `App.Department.RRHH` | Subida (a la carpeta equivocada) |
| `GET /rrhh/employees/fichaje/all` | `App.Department.RRHH` | Resumen por empleado de la tabla `fichajes` (caché `fichajes_resume_cache.pkl`) |
| `GET /rrhh/employee/fichaje/<id_emp>` | `App.Department.RRHH` | Lo mismo para un empleado |
| `POST /dashboard/fichaje/emp` | `App.Department.RRHH`, `App.Department.Director` | Gráfica de eventos por empleado; el front web no lo llamaba |

## Las 4 capas

```
HTTP    rs_RRHH.py        5 rutas de fichajes fuera
        rs_Dashboards.py  /fichaje/emp fuera
mid     Functions_midleware_RRHH.py       fuera get_fichaje_data, fetch_fichaje(s)_*, get_files_fichaje y auxiliares;
                                          también update_data_docs_nomina, update_files_data_nominas y el stub upload_nomina_doc
        Functions_midleware_dashboard.py  fuera get_data_chart_fichaje_emp
        misc/Functions_Files.py           fuera 35 funciones del análisis de fichajes (Excel, Ternium, contratos OCT, cachés)
        misc/Functions_AuxFiles.py        fuera get_pairs_nomina_docs (nómina en SharePoint)
        Functions_Sharepoint.py, misc/Functions_Files_RH.py, daemons/Files_handling.py   borrados
modelos api_fichajes_models.py (queda expected_files, que usan Admin_DB y presales), api_dashboards_models.py,
        api_models.py (date_filter_fichaje)
config  constants.py: domain_path, index_file_nominas y 10 constantes de fichajes (rutas, patrones, formato de fecha);
        requirements.txt / constraints.txt
```

Ninguna tabla cambia. Sin DDL.

## Qué se queda

- **Bitácora completa.** `/bitacora/fichaje/table|event|multiple` y `/bitacora/fichajes/extra|extra/aprove` guardan sus eventos en `sql_telintec_mod_rrhh.fichajes`. Usan el caché de resumen: `get_fichajes_resume_cache`, `update_fichajes_resume_cache` y `get_cumulative_data_fichajes_dict` siguen en `Functions_Files.py`. El front las usa en la bitácora y en las confirmaciones de horas extra.
- [`fichajes_controller.py`](../templates/controllers/fichajes/fichajes_controller.py), que también usan las tools del chatbot.
- `get_data_xml_file_nomina`, que lee el XML en `POST /payroll/files/extract`.
- `xlrd`, que sigue haciendo falta para el `.xls` de `get_data_encuesta`.
- Las 4 llaves de SharePoint de `files/settings.json` (`url_shrpt`, `folder_rrhh`, `folder_nominas`, `folder_checador`). Ya nadie las lee, pero el archivo es configuración de runtime y no se tocó.

## Dependencias

Sale `Office365-REST-Python-Client==2.5.11` de [`requirements.txt`](../requirements.txt). Con ella salen de [`constraints.txt`](../constraints.txt) las transitivas que solo ella traía: `msal`, `requests` y `charset-normalizer`. Verificado con `pip install --dry-run --report` para Linux y Python 3.11 (`--platform manylinux2014_x86_64 --python-version 3.11`), antes y después: el resultado pasa de 61 a 57 paquetes, sin cambios de versión. `requests` solo la importan [`Functions_Observer.py`](../templates/Functions_Observer.py), que está huérfano, y `scripts_db_handle/codigo_lambda.py`, que no es del API.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1`. **Auth**: `Authorization: <JWT crudo>`, **sin** `Bearer`. Para estas rutas ya no importa: el 404 sale antes de revisar el token.
- **Los 6 endpoints de la tabla de arriba responden `404` con `text/html`**: la página de Flask, **no** el envelope `{data,msg,error}`. No intentar parsear JSON.

  ```
  GET /GUI/api/v1/rrhh/employees/fichaje/all
  Authorization: eyJhbGciOi...
  → 404  Content-Type: text/html; charset=utf-8
     <!doctype html> ... <title>404 Not Found</title> ...
  ```

- **Qué quitar del front (`P-227`)**: la pantalla `/dashboard/rrhh/fichajes` (`src/app/dashboard/rrhh/fichajes/page.tsx`), `src/components/rrhh/fichajes/*`, `src/lib/api-rh-fichajes.ts`, `src/hooks/useRHFichajes.ts`, `src/lib/utils-rh-fichajes.ts`, `src/types/rrhh-fichajes.ts` y la entrada de `src/constants/nav.ts`.
- **No cambia**: la bitácora (`src/lib/api-logs.ts`, `src/hooks/useLogs.ts`) ni las confirmaciones de extras (`src/lib/api-confirmations.ts`). Mismas rutas, mismo contrato.

## En el servidor (`P-229`)

Después de desplegar: quitar `TENANT_SHRPT`, `CLIENT_ID_SHRPT` y `CERT_THUMBPRINT_SHRPT` del `.env` de prod y borrar `domain.pem` (el certificado de la app de SharePoint; nada más lo lee). Conviene dar de baja también el registro de esa app en Azure. `Office365-REST-Python-Client`, `msal`, `requests` y `charset-normalizer` siguen instalados en `envg2` sin que nadie los importe. Salen solos la próxima vez que se cree el venv desde `requirements.txt` (sin `pip uninstall` en caliente; ver [`dependencias_python.md`](dependencias_python.md)).

## Al modificar

- **Fichajes nuevo**: partir de cero sobre lo que se decida (biométrico, check-in u otro). El legacy está para consultar la lógica de faltas, retardos y tolerancias, no para restaurarlo. Al quedar el nuevo en prod, borrar `GUITelintec_legacy\fichajes\` y cerrar `P-228`.
- **No mover la bitácora junto con esto**: su tabla se llama `fichajes`, pero es otra funcionalidad y está en uso.
- **SharePoint de vuelta**: el cliente viejo está en el legacy y en git (`git show c6cae15:templates/Functions_Sharepoint.py`). La dependencia regresa a `requirements.txt` y hay que regenerar `constraints.txt`.

## Notas posteriores

- **2026-11-03 — Se puede desplegar en cualquier momento.** El usuario confirmó que Fichajes de RH no está en uso en prod; lo que sí se usa son los check-ins, que no cambian. Por eso el despliegue del retiro no espera a `P-227`.
