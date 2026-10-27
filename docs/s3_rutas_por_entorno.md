# Rutas S3 separadas por entorno (`P-177`)

> 2026-10-27. Decisiones del grill del mismo día → [`plan_back_sin_bloqueo_2026_10_27.md`](planes/plan_back_sin_bloqueo_2026_10_27.md). Sin DDL. Ningún request cambia; cambian las rutas que devuelven las subidas nuevas y qué objetos borra cada entorno.

dev, test y prod suben a los **mismos buckets** (`S3_RH_BUCKET`, `S3_ADMIN_BUCKET`, `S3_CH_BUCKET`) y los ids se repiten entre las 3 BDs. Antes de este cambio, una prueba en dev con un `emp_id` y un nombre de archivo reales sobrescribía el recibo de prod, y borrarlo en dev lo borraba en prod. Lo mismo valía para fotos de CDA, anexos de remisión, de SM y de vales.

## La regla

1. **Toda llave nueva lleva el entorno** justo después de su carpeta raíz: `<raíz>/<entorno>/<resto>`. `<entorno>` = `test` si el token es de tester (BD de pruebas); si no, `environment` de [`constants.py`](../static/constants.py) (`dev` | `prod`). Prod también lleva su prefijo.
2. **Las llaves viejas siguen funcionando.** Cada registro guarda la ruta completa del objeto, y descargas, reemplazos y borrados leen esa ruta guardada; nadie la reconstruye ni lista el bucket (verificado: no hay `list_objects` en el API).
3. **Quién borra qué objeto:** cada entorno borra solo las llaves con su prefijo; una llave vieja (sin entorno) solo la borra **prod**; una de otro entorno, nunca. Quien no puede borrar quita la entrada de su lista y deja el objeto, con una línea en el log (`S3 sin borrar ...`); la conciliación lo reporta.
4. **"Mismo archivo" = mismo nombre dentro del mismo registro** (CDA, remisiones, vales). Volver a subir un archivo cuya entrada tiene la ruta vieja lo reemplaza en la lista (no lo duplica), así que corregir una firma volviéndola a subir sigue funcionando. El objeto de la ruta vieja se borra solo si la regla 3 lo permite.

| Módulo | Ruta nueva | Antes |
|---|---|---|
| Nómina (`S3_RH_BUCKET`) | `payroll/<entorno>/<año>/<mes>/<emp_id>/<quincena>/<archivo>` | `payroll/<año>/<mes>/<emp_id>/<archivo>` |
| Check-in (`S3_RH_BUCKET`) | `checkins/<entorno>/<emp_id>/<fecha>/<epoch_ms>-<type>.<ext>` | sin `<entorno>` |
| Fotos de CDA (`S3_ADMIN_BUCKET`) | `cda/<entorno>/vehicles/<id>/<archivo>` | `cda/vehicles/<id>/<archivo>` |
| Anexos de remisión (`S3_ADMIN_BUCKET`) | `reportActivity/<entorno>/<Y/m/d>/<id_report>/<archivo>` | sin `<entorno>` (y las más viejas, sin `<id_report>`) |
| Anexos de SM (`S3_ADMIN_BUCKET`) | `smData/<entorno>/<Y/m/d>/<id_sm>/<archivo>` | `smData/<Y/m/d>/<archivo>` |
| Vales (`S3_CH_BUCKET`) | `checklistV` \| `eppVoucher` \| `toolsVoucher` + `/<entorno>/<Y/m/d>/<id>-<archivo>` | sin `<entorno>` |

Dos arreglos de paso:

- **Nómina:** la quincena (`key`, p. ej. `2026-10-Q1`) entra a la ruta, limpia con `secure_filename` (es texto libre; `ZZ/../Q9` → `ZZ_.._Q9`). El mismo nombre en Q1 y Q2 ya no comparte objeto.
- **SM:** la ruta gana el id de la SM. Sin él, dos SMs del mismo día con un anexo del mismo nombre compartían objeto, también en prod.

## Capas tocadas

| Capa | Archivo | Cambio |
|---|---|---|
| Aux (nuevo) | [`Functions_Aux_S3.py`](../templates/resources/methods/Functions_Aux_S3.py) | `s3_environment`, `s3_env_key`, `s3_key_environment`, `s3_can_delete` |
| Midleware | [`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) | ruta de nómina con entorno y quincena; `_payroll_s3_delete` aplica la regla 3 |
| Midleware | [`MD_CDA.py`](../templates/resources/midleware/MD_CDA.py) | ruta con entorno; reemplazo por `filename`; `_delete_photo_objects` con la regla 3 (alta y borrado) |
| Midleware | [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py) | ruta con entorno; reemplazo por `filename`; `_remission_key_belongs_to_report` reconoce las dos formas con id; `_remission_key_deletable` = del reporte + regla 3 |
| Aux | [`Functions_Aux_Vouchers.py`](../templates/resources/methods/Functions_Aux_Vouchers.py) | ruta con entorno; reemplazo por `filename`; `_delete_voucher_objects` con la regla 3 (alta y borrado) |
| Midleware | [`MD_SM.py`](../templates/resources/midleware/MD_SM.py), [`MD_Checkin.py`](../templates/resources/midleware/MD_Checkin.py) | ruta con entorno (SM, además, con su id); no reemplazan ni borran objetos |
| Modelos | [`api_payroll_models.py`](../static/Models/api_payroll_models.py) | ejemplos de swagger con la ruta nueva |
| Script local | `scripts_db_handle/nomina_s3_conciliacion.py` (gitignored) | un objeto con entorno es huérfano si **su** BD no lo referencia (`referencias_ajenas` si lo referencia otra); los viejos, si ninguna de las 3; conteo de huérfanos por entorno |

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)**, como siempre. **Ningún request cambia** (mismos campos, mismo multipart de un archivo por request) y el envelope sigue siendo `{data, msg, error}`.

Lo que cambia en las respuestas:

- **Las rutas S3 que devuelven las subidas traen el entorno.** Tratarlas como texto opaco: no partirlas ni armarlas en el front. Ejemplos en dev:
  - `POST /GUI/api/v1/rrhh/payroll/files/update` → `201 {"data": "payroll/dev/2026/10/77/2026-10-Q1/recibo.pdf", ...}`
  - `POST /GUI/api/v1/common/checkin` → `201 {"data": {"photo_key": "checkins/dev/36/2026-10-27/1793000000000-0.jpg", ...}}`
  - Anexo de remisión → `201 {"data": {"path": "reportActivity/dev/2026/10/27/50/firma-recibido.png", "replaced": true, ...}}`
- **Descarga de recibos** (`POST /GUI/api/v1/common/payroll/employee/file`): se sigue mandando la ruta tal como viene del índice (`pdf`/`xml`). Las viejas sin entorno y las nuevas funcionan igual.
- **Reemplazo por nombre:** volver a subir un anexo (remisión, vale) o foto (CDA) con el mismo nombre lo reemplaza aunque el anterior se haya subido con la ruta vieja. Ya no aparecen dos entradas con el mismo nombre. En remisión, `data.replaced` es `true`.
- **Borrados que no tocan S3:** en dev y test, borrar una entrada con ruta vieja responde **200 con `s3_deleted: false`**. Se quitó de la lista y el objeto se queda porque puede ser de prod. No es error y no hay que reintentar. Ejemplo de remisión:
  ```json
  {"data": {"id_report": 50, "filename": "foto.jpg", "s3_deleted": false,
            "s3_detail": "Llave heredada (sin id de reporte) o de otro entorno: el objeto se conserva en S3"},
   "msg": "...", "error": null}
  ```
  En nómina, el mismo caso trae en `msg` "se conserva en S3: la ruta es de otro entorno o anterior a P-177 (solo prod la borra)".

## Verificación

Testers en `Tests/` (gitignored), con S3 simulado:

- `tester_nomina_huerfanos.py` contra la BD dev (emp 34, año 2099, índice restaurado byte a byte): **44/44**. Cubre:
  - Q1 y Q2 con el mismo nombre son objetos distintos.
  - Dev reemplaza o borra una llave vieja sin tocar el objeto.
  - Prod borra la vieja, pero nunca una de dev, y sube bajo `payroll/prod/`.
  - La quincena con `/` sale limpia.
- `tester_s3_entorno.py` (nuevo, lógica pura con BD simulada): **24/24**. Cubre:
  - La matriz de `s3_can_delete` (11 casos).
  - Remisión con firma vieja con y sin id (dev no borra; prod borra solo la que tiene id).
  - Vales y CDA: reemplazo por nombre y borrado.
  - Token de tester → `test`.
- Regresión:

  | Tester | Resultado |
  |---|---|
  | CDA | 43/43 |
  | check-in | 37/37 |
  | remisiones (CAS) | 19/19 |
  | remisiones (sin anexos) | 25/25 |
  | vales EPP/herramientas | 29/29 |
  | vales vehicular | 31/31 |
  | vales PUT | 49/49 |
  | SM | 30/30 |
  | descarga de nómina | 19/19, con llaves viejas |

  Los testers de CDA y check-in solo cambiaron la ruta esperada. El de descarga ganó un id de respaldo porque dev ya no tiene empleados sin fila de nómina.
- `pyrefly check --python-version 3.11` sobre los archivos tocados: sin errores nuevos (los 22 que reporta están en líneas que este cambio no toca).

## Al modificar

- **Subida nueva a S3:** armar la llave con `s3_env_key(<raíz>, <resto>, data_token)` y guardar la ruta completa en el registro. Nunca reconstruirla al leer.
- **Borrar un objeto:** pasar antes por `s3_can_delete(key, data_token)`. Si devuelve `False`, quitar la entrada del índice y dejar el objeto.
- **Reemplazo "mismo archivo":** comparar por nombre dentro del registro, no por ruta. La ruta cambia con el entorno.
- **Nueva raíz o bucket:** si algún día se lista el bucket por prefijo (como la conciliación), contemplar las dos formas: con entorno en el segundo segmento y sin él.
- **Valor nuevo de `environment`:** agregarlo a `S3_ENVIRONMENTS`, o sus llaves se tratarán como viejas.
