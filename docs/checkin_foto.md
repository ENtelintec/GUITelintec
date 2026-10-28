# Check-in con foto (tipo Wellhub): `POST /common/checkin`, `GET /common/checkin/me`, `GET /rrhh/checkins`, manuales y anulación de RH

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (37/37, `Tests/tester_checkin.py`, S3 simulado). DDL [`checkins.sql`](../scripts_db_handle/checkins.sql) corrido en dev, test y prod (`P-165`, ver [Notas posteriores](#notas-posteriores)).**

Fase **F8** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "hacer check-in tipo Wellhub con foto"). Decisiones del grill: entra ya, para **todo el personal**, como **respaldo cuando el biométrico no esté**; **simple**: sin alternancia forzada, sin geocerca ni validación facial; **RH hace todas las correcciones**; **resumen por día calculado en lectura**; lo que hay de `fichajes` (Excel del biométrico de Ternium) se ignora. Fotos con la receta de [`cda_alertas_y_fotos.md`](cda_alertas_y_fotos.md) (S3 + blob), ahora en el bucket de RH.

## Modelo

```
sql_telintec_mod_rrhh.checkins   (scripts_db_handle/checkins.sql)
  id · emp_id (-> employees.employee_id, índice) · type TINYINT (0 ENTRADA · 1 SALIDA)
  timestamp DATETIME (hora del SERVIDOR, America/Mexico_City; en manuales la que captura RH)
  lat / lon DECIMAL(10,7) NULL · accuracy DECIMAL(8,2) NULL
  photo_key VARCHAR(255) NULL   (S3_RH_BUCKET: checkins/<emp_id>/<YYYY-MM-DD>/<epoch_ms>-<type>.<ext>; NULL solo en manuales)
  is_manual TINYINT (`manual` es palabra reservada en MySQL 8.4+/9; el JSON del API sigue diciendo `manual`) · status TINYINT (0 VALIDO · 1 ANULADO) · created_by · device_info · history JSON · extra_info JSON · created_at
```

Catálogos en Python (`CHECKIN_TYPES`, `CHECKIN_STATUSES`), expuestos en `GET /common/checkin/catalogs`. Nada agregado se persiste: las horas por día salen de los eventos válidos en cada lectura.

## Reglas

| Tema | Regla |
|---|---|
| Quién registra | Cualquier empleado con permiso `common` o `basic`, **solo sobre sí mismo** (`emp_id` del token; 404 si ese empleado no existe). |
| Foto | **Obligatoria**, una por request (multipart `file`, jpg/jpeg/png/webp). Se sube a S3 antes del `INSERT`; si el `INSERT` falla, la foto queda en S3 y se responde 400 (sin registro). |
| Hora | La pone el **servidor** (`America/Mexico_City`); el celular no manda hora. |
| Ubicación | `lat`/`lon` opcionales pero **juntas**, con rango; `accuracy` en metros opcional. |
| Alternancia | **No se exige**: dos entradas seguidas o una salida sin entrada se aceptan (decisión 2026-10-22, "algo simple"); el resumen las refleja como incompletas. |
| Correcciones | Solo **RH** (`rrhh`): `PUT /rrhh/checkin/cancel {id, reason}` (status 1, history; no se borra; repetido → 400) y `POST /rrhh/checkin {emp_id, type, timestamp, reason}` (manual, sin foto, `manual = 1`, hora no futura, motivo obligatorio). El empleado no edita ni borra. |
| Resumen | Por empleado y día sobre eventos **válidos**: `first_in` = primera ENTRADA, `last_out` = última SALIDA posterior a ella, `hours` = diferencia (2 decimales), `events_count`, `incomplete` = falta alguna de las dos. Sin retardos ni tolerancias (v1). |
| Rangos | `date_from`/`date_to` (`YYYY-MM-DD`, inclusivos sobre la fecha del evento); default **últimos 30 días**; máximo 366; tope de 5 000 eventos con `meta.truncated`. Sin `all=1` solo válidos. |
| Fotos | `GET /rrhh/checkin/<id>/photo` (RH, cualquiera) y `GET /common/checkin/<id>/photo` (solo propia → 403 ajena): blob en 200; 404 en manuales. |
| Lista sin JSON en el `ORDER BY` | El listado no selecciona `history`/`extra_info` (solo el detalle), por la regla del sort buffer. |

## Capas tocadas

```
DDL         scripts_db_handle/checkins.sql                       (nuevo) tabla + índices; FK opcional al final (una sola vez)
controller  controllers/employees/checkins_controller.py          (nuevo) insert · get_by_id (detalle) · get_checkins (rango, param-or-NULL) · cancel · delete (solo pruebas)
midleware   resources/midleware/MD_Checkin.py                     (nuevo) create_checkin_api · get_my_checkins_api · get_checkins_api · build_daily_summary · create_manual_checkin_api · cancel_checkin_api · download_checkin_photo_api · catálogos
models      static/Models/api_checkin_models.py                   (nuevo) expected_files_checkin (parser multipart) · CheckinManualForm / CheckinCancelForm + api.model
routes      rs_Common.py                                           POST /checkin · GET /checkin/me · GET /checkin/catalogs · GET /checkin/<id>/photo
routes      rs_RRHH.py                                             GET /checkins · POST /checkin · PUT /checkin/cancel · GET /checkin/<id>/photo
```

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/common` (empleado, permiso `common` o `basic`) y `/GUI/api/v1/rrhh` (RH, permiso `rrhh`). **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Respuesta**: JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400 de midleware, objeto por campo en 400 de form. 401: `{"error": "..."}` sin envelope. **Fotos: blob en 200, envelope en 4xx** (el front decide por el status).

### `POST /common/checkin` — multipart (una foto por request)

| Campo (form) | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `file` | archivo | **sí** | jpg / jpeg / png / webp |
| `type` | `0` \| `1` | **sí** | 0 ENTRADA · 1 SALIDA |
| `lat`, `lon` | number | no | juntas; `-90..90` / `-180..180` |
| `accuracy` | number | no | metros |
| `device_info` | string ≤ 255 | no | default: `User-Agent` |

| Código | Cuándo | Ejemplo |
|---|---|---|
| **201** | registrado | `data: {"id": 120, "emp_id": 36, "type": 0, "type_label": "ENTRADA", "timestamp": "2026-10-22 08:03:11", "lat": 25.6866, "lon": -100.3161, "accuracy": 12.5, "photo_key": "checkins/36/2026-10-22/1792700000000-0.jpg", "employee_status": "activo"}` |
| **400** | sin foto / extensión / `type` / ubicación | `msg: "La foto es obligatoria"` · `error: ["file: se requiere una imagen jpg, jpeg, png, webp (recibido: 'nada')"]` · `error: ["type debe ser 0 (ENTRADA) o 1 (SALIDA)"]` · `msg: "Ubicación inválida"` · `error: ["lat y lon van juntas"]` |
| **400** | S3 / BD | `msg: "Error al subir la foto a S3"` · `msg: "La foto se subió pero no se pudo guardar el registro"` |
| **404** | el `emp_id` del token no existe | |

### `GET /common/checkin/me?date_from&date_to&all=1`

```json
"data": {"emp_id": 36, "date_from": "2026-09-22", "date_to": "2026-10-22",
         "events": [{"id": 121, "emp_id": 36, "emp_name": "ANA PÉREZ", "type": 1, "type_label": "SALIDA", "timestamp": "2026-10-22 17:40:02",
                     "lat": null, "lon": null, "accuracy": null, "photo_key": "checkins/36/...", "has_photo": true, "manual": false,
                     "status": 0, "status_label": "VALIDO", "created_by": 36, "device_info": "Mozilla/5.0 ...", "created_at": "2026-10-22 17:40:02"}],
         "summary": [{"emp_id": 36, "emp_name": "ANA PÉREZ", "date": "2026-10-22", "first_in": "08:03", "last_out": "17:40", "hours": 9.62, "events_count": 2, "incomplete": false}]}
```

400 `msg: "Rango inválido"` con el motivo (`"date_from / date_to deben ser fechas YYYY-MM-DD"`, `"date_from no puede ser posterior a date_to"`, `"el rango no puede superar 366 días"`).

### `GET /rrhh/checkins?emp_id&date_from&date_to&all=1` (RH)

Mismo shape que `/me` para todos los empleados (o uno con `emp_id`), más `meta: {returned, limit: 5000, truncated}`. `summary` viene ordenado por fecha descendente y empleado.

### `POST /rrhh/checkin` (manual, RH)

`{"emp_id": 36, "type": 0, "timestamp": "2026-10-21 08:05:00", "reason": "Olvidó registrar la entrada"}` → **201** `data: {"id": 130, "emp_id": 36, "type": 0, "type_label": "ENTRADA", "timestamp": "2026-10-21 08:05:00", "manual": true, "photo_key": null}` · 400 `timestamp` inválido o **futuro**, `type` inválido, sin `reason` · 404 empleado inexistente.

### `PUT /rrhh/checkin/cancel` (RH)

`{"id": 130, "reason": "Registro duplicado"}` → **200** `data: {"id": 130, "emp_id": 36, "status": 1, "status_label": "ANULADO"}` · 400 ya anulado o sin motivo · 404.

### Fotos

`GET /rrhh/checkin/<id>/photo` y `GET /common/checkin/<id>/photo` (solo propia) → **blob** (`image/*`, `as_attachment`) en 200; 404 si no existe o es manual; 403 (common) si es de otro empleado.

### `GET /common/checkin/catalogs`

`{"types": [{"code": 0, "label": "ENTRADA"}, {"code": 1, "label": "SALIDA"}], "statuses": [{"code": 0, "label": "VALIDO"}, {"code": 1, "label": "ANULADO"}], "photo_extensions": [...], "default_range_days": 30}`.

### Gotchas

- La cámara del navegador entrega la foto como `File`; mandarla en `file` con su nombre y extensión real (`selfie.jpg`), no como base64.
- La hora que ve el empleado en la respuesta es la del servidor; si el celular tiene otra hora, manda la del servidor.
- Un evento anulado desaparece del resumen pero sigue en `events` con `all=1`.
- `emp_name` sale de `employees`; si el empleado se borra, viene vacío.

## Al modificar

- **Alternancia** (si RH la pide después): en `create_checkin_api`, leer el último evento válido del día (`get_checkins(emp_id, hoy, hoy, 0, 1)`) y rechazar el mismo `type` con 400.
- **Geocerca**: validar `lat`/`lon` contra una lista de sedes (`warehouses_amc` tiene nombre, no coordenadas: habría que agregarlas en `extra_info`) y responder 400 o solo marcar `extra_info.outside = true`.
- **Retardos / tolerancias**: `build_daily_summary` es el único lugar; agregar el horario del empleado (hoy no existe en `employees`) y una llave `late_minutes`.
- **Horas persistidas / exportar a nómina**: hoy nada se guarda agregado; si hace falta, una tabla `checkin_days` alimentada por un barrido (receta de `MD_BalanceAlerts`), no en lectura.
- **Reemplazar `fichajes`**: fuera de alcance; si algún día se unifica, el Excel de Ternium entraría como eventos `manual = 1` con `extra_info.source = "ternium"`.

## Notas posteriores

- **2026-10-22 — DDL y verificación completa**: `checkins.sql` corrido en dev, test y prod. En solo lectura, las 3 tablas son idénticas al script: 15 columnas, índices `idx_checkins_emp_ts` / `_ts` / `_status`, `fk_checkins_employee` (RESTRICT al borrar, CASCADE al actualizar) y 0 filas. `Tests/tester_checkin.py` contra dev, ya con la tabla: **37/37**, incluidas altas con foto, manual de RH, anulación, `history`, fotos propias/ajenas y resumen por día. Cierra `P-164` y `P-165`; queda el front (`P-166`).
- **2026-10-27 — rutas S3 con entorno (`P-177`).** Las subidas nuevas van a `checkins/<entorno>/<emp_id>/<fecha>/<epoch_ms>-<type>.<ext>`; las rutas guardadas antes siguen funcionando. El ejemplo `photo_key` de este doc es del formato anterior. → [`s3_rutas_por_entorno.md`](s3_rutas_por_entorno.md).
- **2026-10-27 — front cerrado (`P-166`).** Pantalla del empleado en `/dashboard/comun/checkin` y consulta de RH en `/dashboard/rrhh/checkins` (con registro manual), contra este contrato sin cambios. La usuaria las probó en computadora y en un celular Android por red local, con cámara y ubicación.
- **2026-10-28 — junta con RH: horas por tramos y exportar.** Cambia la regla **Resumen** de este doc: `hours` es ahora la suma de los tramos entrada → salida (descuenta la comida); el valor de antes pasa a `span_hours`, y salen `segments` y una regla nueva de `incomplete`. Además, nuevos `GET /rrhh/checkins/download/excel` y `/pdf` (con foto). → [`checkin_exportar_y_tramos.md`](checkin_exportar_y_tramos.md). El mapa del front es `P-213`.
- **2026-10-28 — fotos de ~4 MB no suben (`P-214`, front).** El API no tiene tope de tamaño (no hay `MAX_CONTENT_LENGTH` en `app.py`), así que el límite está en algo intermedio: el rewrite de Next (`/GUI/api/v1/*`) o un proxy del servidor. No se averiguó cuál; un `413` indica que es el proxy. La solución que no depende de eso es **reducir la foto en el navegador antes de subirla**: `createImageBitmap` + `canvas`, lado mayor de unos 1600 px, `toBlob('image/jpeg', 0.8)` (queda en unos cientos de KB), y mandarla como `selfie-<ts>.jpg` (el back decide por la extensión). De paso, la subida es más rápida con datos móviles. El PDF reduce las fotos por su lado, así que no depende de esto.
