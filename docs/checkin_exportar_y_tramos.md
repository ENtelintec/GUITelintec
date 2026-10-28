# Check-in: horas por tramos y exportar a Excel / PDF con foto (`GET /rrhh/checkins/download/excel` · `/pdf`)

Fecha: 2026-10-28 · **Estado: back hecho y verificado contra dev (30/30 `Tests/tester_checkin_export.py` con S3 simulado y fotos JPEG reales; regresión 37/37 `Tests/tester_checkin.py`). PDF revisado a ojo (real de 1 página y sintético de 10 páginas con nombres largos). Falta el front (`P-213`).**

Junta con RH del 2026-10-28 sobre el check-in de [`checkin_foto.md`](checkin_foto.md). Pidieron:

1. **Guardar todos los registros del día.** Ya se guardaban: ni el back ni el front limitan a uno por día. Lo que fallaba con varios registros era el **cálculo de horas**: iba de la primera entrada a la última salida, así que una salida a comer contaba como tiempo trabajado. Decisión: **horas por tramos**.
2. **Exportar**: Excel solo con datos y PDF con la foto. Decisión: el Excel lleva dos hojas (registros y resumen); el PDF admite hasta 200 registros.
3. **Mapa y visor de foto en el front.** El back ya entrega `lat`/`lon`/`accuracy` y la foto. Decisión: **Leaflet + OpenStreetMap** (gratis, sin API key). Es trabajo solo del front (`P-213`).

Sin DDL: todo sale de la tabla `checkins` que ya existe.

## Horas por tramos (`build_daily_summary`)

Por empleado y día, sobre los eventos **válidos** en orden cronológico (empate por `id`):

| Evento | Qué hace |
|---|---|
| ENTRADA sin tramo abierto | abre un tramo |
| ENTRADA con un tramo abierto | el abierto queda **sin salida** y se abre otro (doble entrada: RH anula la que sobra) |
| SALIDA con tramo abierto | lo cierra |
| SALIDA sin tramo abierto | queda como tramo **sin entrada** |
| Al final del día, tramo abierto | queda **sin salida** |

| Campo de `summary[]` | Antes del 2026-10-28 | Ahora |
|---|---|---|
| `hours` | primera ENTRADA → última SALIDA | **suma de los tramos cerrados** (descuenta comida y salidas intermedias); `null` si no hay tramo cerrado |
| `span_hours` | — | **nuevo**: primera ENTRADA → última SALIDA posterior (el `hours` de antes) |
| `segments` | — | **nuevo**: `[{"in": "08:00", "out": "13:00", "hours": 5.0}, {"in": "14:00", "out": null, "hours": null}]` |
| `incomplete` | falta la primera entrada o la última salida | **algún tramo sin entrada o sin salida** |
| `first_in`, `last_out`, `events_count`, orden | — | sin cambio |

Ejemplo: `08:00 E · 13:00 S · 14:00 E` (olvidó la última salida). Antes: `hours: 5`, `incomplete: false`. Ahora: `hours: 5`, `incomplete: true`.

Aplica a `GET /rrhh/checkins` y a `GET /common/checkin/me`, que comparten el resumen.

## Exportar (RH)

| Tema | Regla |
|---|---|
| Filtros | **Los mismos de `GET /rrhh/checkins`**: `emp_id` opcional, `date_from`/`date_to` (default últimos 30 días, máximo 366), `all=1` incluye anulados. |
| Orden | Por empleado (nombre) y cronológico ascendente, en las dos hojas y en el PDF. La pantalla ordena distinto (más reciente primero). |
| Excel | Hoja **Registros**: ID, empleado, fecha, hora, tipo, estado, origen (App / Manual RH), lat, lon, precisión, link "Ver mapa" (Google Maps), foto Sí/No, dispositivo, registrado. Hoja **Resumen**: primera entrada, última salida, tramos en texto (`08:00–13:00, 14:00–sin salida`), horas trabajadas, permanencia, registros, incompleto. Sin fotos. Tope **5 000** registros. |
| PDF | Vertical, cuadrícula celeste (skill `pdf-design`), encabezado **FO-GRH-08** (`iso_form=1`, el mismo de los reportes de RH; confirmado por el usuario el 2026-10-28). Página 1: metadata (periodo, empleado, registros, anulados, días, horas trabajadas, fotos incluidas, generado). Luego **Resumen por día** y **Registros**, con la foto en cada fila y la ubicación clicable a Google Maps. Tope **200** registros (con foto o sin ella, anulados incluidos con `all=1`). |
| Fotos del PDF | Se bajan de S3 en paralelo (8 hilos) y se reducen a 400 px por el lado mayor (JPEG, con la rotación EXIF aplicada). Si una foto no baja o no abre, el PDF dice "Foto no disponible" y no truena; los manuales dicen "Manual (sin foto)". 60 registros con foto pesan unos 230 KB. |
| Archivos | En memoria (sin temporales en disco). Nombre: `checkins[_emp<id>]_<date_from>_<date_to>.xlsx` / `.pdf`. |
| Sin registros | **404**: no se entrega un archivo vacío. |

## Capas tocadas

```
midleware   resources/midleware/MD_Checkin.py      build_daily_summary por tramos (_pair_segments) · _rh_filters (compartido con GET /checkins)
                                                    export_checkins_excel_api (xlsxwriter) · export_checkins_pdf_api · _load_thumbnails (S3 + Pillow)
forms       forms/CheckinsPDF.py                    (nuevo) FileCheckinsPDF + helpers _ck_*
routes      rs_RRHH.py                              GET /checkins/download/excel · GET /checkins/download/pdf
```

Sin cambios en el controller, ni en los modelos (son GET con query string), ni en `requirements.txt` (`xlsxwriter`, `reportlab` y `Pillow` ya estaban).

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/rrhh`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. **Permiso exacto**: `App.Department.RRHH` (o `App.Department.Administrator`), el mismo de `GET /rrhh/checkins`.
- **Descargas**: **blob en 200; JSON `{data, msg, error}` en 4xx.** El front decide por el status. 401: `{"error": "..."}` sin envelope.

### `GET /checkins/download/excel?emp_id&date_from&date_to&all=1`

| Código | Respuesta |
|---|---|
| **200** | `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` · `Content-Disposition: attachment; filename=checkins_emp36_2026-10-01_2026-10-28.xlsx` |
| **400** | `{"data": null, "msg": "emp_id inválido", "error": ["emp_id debe ser entero"]}` · `{"msg": "Rango inválido", "error": ["date_from no puede ser posterior a date_to"]}` · `{"msg": "Demasiados registros para exportar (más de 5000)", "error": ["el archivo admite hasta 5000 registros: acota el rango de fechas o elige un empleado"]}` |
| **404** | `{"data": null, "msg": "No hay registros en el rango", "error": "sin registros"}` |
| **401** | token sin el permiso |

### `GET /checkins/download/pdf?emp_id&date_from&date_to&all=1`

Igual que el Excel, con `Content-Type: application/pdf`, nombre `.pdf` y tope **200**: `{"msg": "Demasiados registros para exportar (más de 200)", "error": ["el archivo admite hasta 200 registros: acota el rango de fechas o elige un empleado"]}`. Puede tardar unos segundos (baja las fotos de S3): mostrar un indicador de carga.

### Resumen (`GET /rrhh/checkins` y `GET /common/checkin/me`)

Cada elemento de `summary[]` trae ahora:

```json
{"emp_id": 36, "emp_name": "ANA PÉREZ", "date": "2026-10-22", "first_in": "08:03", "last_out": "17:40",
 "hours": 8.62, "span_hours": 9.62,
 "segments": [{"in": "08:03", "out": "13:00", "hours": 4.95}, {"in": "14:00", "out": "17:40", "hours": 3.67}],
 "events_count": 4, "incomplete": false}
```

### Gotchas

- Los botones de exportar deben mandar **los mismos filtros que la tabla en pantalla**. Sin `date_from`/`date_to`, el back usa los últimos 30 días.
- `all` es verdadero con `1`, `true` o `yes`; cualquier otro valor (incluido `0`) excluye los anulados.
- `hours` puede traer horas en un día `incomplete: true` (los tramos que sí cerraron). La pantalla de RH hoy pinta `hours` en la columna Horas: con el cambio, un día incompleto ya no sale con "—" si tiene algún tramo cerrado.
- Un turno que cruza la medianoche queda partido en dos días incompletos (la entrada en uno y la salida en el otro), igual que antes.
- El nombre del archivo viene en `Content-Disposition`; si el front arma el suyo, que lleve el rango.

## Al modificar

- **Otro tope del PDF**: `EXPORT_PDF_LIMIT` en `MD_Checkin.py`. Subirlo alarga la descarga (cada foto es un `get_object`) y el tiempo del worker.
- **Motivo de la anulación o del manual en el Excel**: hoy no sale, porque el listado no selecciona `history` (la regla del sort buffer de [`checkin_foto.md`](checkin_foto.md)). Habría que leerlo con un segundo SELECT por id, sin `ORDER BY`.
- **Código ISO propio para el reporte**: si RH da uno, se da de alta en `iso_formats` (id explícito, en las 3 BDs) y se cambia `_CK_ISO_FORM` en `CheckinsPDF.py` (y se agrega a `ISO_FORM_IDS_IN_CODE`).
- **Exportar para el empleado** (`/common`): no se pidió. Sería la misma función con `emp_id` del token.
- **Retardos / tolerancias**: siguen en `build_daily_summary`, ahora sobre `segments`.

## Pendientes

- **[front]** `P-213`: en `/dashboard/rrhh/checkins`, los tramos del día en el resumen, los dos botones de exportar con los filtros de la pantalla, y un **mapa Leaflet + OpenStreetMap** con los registros filtrados que tengan ubicación. El marcador abre la foto (el `FotoCheckinDialog` de hoy) y se puede dibujar un círculo con radio `accuracy`. La atribución "© OpenStreetMap contributors" es obligatoria.
- **[front]** `P-214`: las fotos de ~4 MB no suben. Detalle en [`checkin_foto.md`](checkin_foto.md#notas-posteriores).
