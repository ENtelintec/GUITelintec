# Dashboard de RH — `GET /dashboard/rrhh/summary` + `POST /dashboard/rrhh/series`

> Punto 4 del [`plan_mes_2.md`](plan_mes_2.md) (Anexo D), adelantado de S3 a S1 (2026-09-10). Back completo con contrato; la pantalla del front va en S4. **Fichajes quedan fuera** del dashboard por decisión del usuario (las series `faltas`/`retardos` del anexo se caen; `metric` sigue extensible).

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Dashboards.py`](../templates/resources/rs_Dashboards.py) | Dos rutas nuevas en el namespace existente `GUI/api/v1/dashboard`, permiso `rrhh`: `GET /rrhh/summary` y `POST /rrhh/series`. |
| **Orquestación** (nuevo) | [`MD_DashboardRRHH.py`](../templates/resources/midleware/MD_DashboardRRHH.py) | Reglas de cada tile y de las series sobre filas crudas: parseo de fechas mezcladas, buckets de vencimiento médico, días pendientes de vacaciones, headcount histórico. Sin caché. |
| **DB** (nuevo) | [`dashboard_rrhh_controller.py`](../templates/controllers/rrhh/dashboard_rrhh_controller.py) | 5 SELECT sin efectos: catálogo de departamentos, ciclo de vida de todos los empleados, exámenes de activos (LEFT JOIN), vacaciones de activos, conteos de tasks por modelo de encuesta. |
| **Modelos** | [`api_dashboards_models.py`](../static/Models/api_dashboards_models.py) | `rrhh_series_model` + `RRHHSeriesForm` (`metric`, `date_from`, `date_to`, `group_by` opcional). El `summary` no lleva body. |

## Reglas de negocio (qué significa cada número)

- **El `status` del empleado manda.** Activo = `employees.status = 'activo'`. Dev tiene 11 activos con una fecha de baja vieja en `departure` (reingresos sin limpiar): **no** cuentan como baja y sí en headcount; salen en `data_quality.active_with_departure` para que RH los limpie. Un inactivo sin fecha de baja legible no se puede ubicar en el tiempo: no cuenta como baja de ningún mes ni en el headcount histórico (`data_quality.inactive_without_departure_ids`).
- **Altas** = `date_admission` dentro del mes (cualquier status). **Bajas** = inactivos con `departure.date` dentro del mes. `departure` es JSON con formatos mezclados (`YYYY-MM-DD`, `DD/MM/YYYY`, con hora, `""`, `"None"`, `null`); todo se parsea en Python y lo ilegible va a `data_quality.departures_unparsed`.
- **Exámenes médicos** (solo activos): vencimiento = última fecha de `renovacion` + periodo por `aptitude_actual` según el catálogo `aptitude` (1 → 365 días, 2 → 180, 3 → 90). Buckets por `days_left` respecto a **hoy** (no al mes pedido): `vencidos` (< 0), `d30` (0..30), `d60` (31..60), `d90` (61..90), `al_dia` (> 90), `no_apto` (aptitud 4), `sin_periodo` (aptitud 0 o nula), `sin_examen` (sin fila o sin fechas). Cada activo cae en exactamente un bucket: la suma es `total_activos`. Si un empleado tuviera más de un examen, gana el de fecha más reciente.
- **Vacaciones** (solo activos): el `status` de cada periodo de `seniority` es **texto libre** de RH; pendiente = `"<n> PTE"`, `"PTES"`, `"PTS"`, `"4PTE"`, `"PTE"` sin número (cuenta como pendiente con `days: null` y `days_unknown: true`) o un **número solo** (`"9"`). `"Tomadas"`, `"SI"`, `"PERDIDOS"` no son pendientes. `next_30_days` sale de las `dates` capturadas por periodo (hoy en dev nadie las llena: llega vacío hasta que se capturen).
- **Encuestas**: un renglón por modelo (`quizz_models`, todos los status) con tasks del tipo; `answered` = `data_raw` no vacío (mismo criterio que la migración de versiones); las tasks de **control** de eva 360 no se cuentan; `assigned_in_period` = creadas dentro del mes pedido.
- **Cumpleaños**: activos con `MONTH(birthday)` = mes pedido, `age` = edad que cumple ese año.
- **Series**: `altas_bajas` (dos series alineadas con `labels`) y `headcount` (activos al cierre de cada mes: ingresó en o antes y, si hoy está inactivo, salió después; por departamento = al cierre de `date_to`). `group_by=month` genera **todos** los meses del rango aunque valgan 0; `department` usa el catálogo completo de `departments` (labels estables) y agrega "Sin departamento" solo si hace falta. Tope 120 meses.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`). Permiso `rrhh` (o `administrator`). Base `/GUI/api/v1/dashboard`. Envelope `{data, msg, error}`; `401` token/permiso, `400` validación. En `summary`, `error` es `null` o una **lista** de tiles que no se pudieron calcular (el resto de `data` llega igual y ese tile viene `null`).
- Todo agregado trae **ids** (y `items` con nombre) para que el click del tile lleve a la lista filtrada sin otra llamada. Los `items` van ordenados como conviene pintarlos (urgencia, día, días pendientes).

### `GET /rrhh/summary[?month=YYYY-MM]`

`month` opcional, default el mes actual (zona `America/Mexico_City`). Aplica a altas/bajas, cumpleaños y `quizzes.assigned_in_period`; headcount, médicos y vacaciones son **al día de hoy** (`period.as_of`).

```json
// 200 (recortado a 1-3 elementos por lista; ejemplo real de dev para 2024-07)
{"data": {
  "period": {"month": "2024-07", "date_from": "2024-07-01", "date_to": "2024-07-31", "as_of": "2026-09-10"},
  "headcount": {"total": 64, "by_department": [{"department_id": 2, "department": "Operaciones", "count": 44}, {"department_id": 3, "department": "Administración", "count": 8}]},
  "movements_month": {"altas": 10, "bajas": 22, "altas_ids": [89, 98, 93], "bajas_ids": [2, 11, 59],
    "altas_items": [{"emp_id": 89, "name": "EDER LARA DE LA ROSA", "department_id": 2, "department": "Operaciones", "date": "2024-07-01"}],
    "bajas_items": [{"emp_id": 2, "name": "ALFREDO RIVERA BORJA", "department_id": 2, "department": "Operaciones", "date": "2024-07-05", "status": "inactivo"}]},
  "medical_expiring": {
    "vencidos": {"count": 15, "ids": [17, 69, 52], "items": [{"emp_id": 17, "name": "EMMANUEL GUZMAN CASTILLO", "examen_id": 26, "aptitude": 2, "last_date": "2023-07-08", "due_date": "2024-01-04", "days_left": -980, "period_days": 180}]},
    "d30": {"count": 0, "ids": [], "items": []}, "d60": {"count": 0, "ids": [], "items": []}, "d90": {"count": 0, "ids": [], "items": []},
    "al_dia": {"count": 0, "ids": [], "items": []}, "no_apto": {"count": 0, "ids": [], "items": []}, "sin_periodo": {"count": 0, "ids": [], "items": []},
    "sin_examen": {"count": 49, "ids": [85, 3, 4], "items": [{"emp_id": 85, "name": "ALEJANDRA BARRIGUETE CARDONA", "examen_id": null, "aptitude": null, "last_date": null, "due_date": null, "days_left": null}]},
    "as_of": "2026-09-10", "total_activos": 64, "period_days": {"1": 365, "2": 180, "3": 90}},
  "vacations": {"employees_with_pending": 40, "pending_days_total": 371, "ids": [29, 38, 18],
    "items": [{"emp_id": 29, "name": "ISBELIA CAROLINA TORRES MORENO", "date_admission": "2018-01-26", "pending_days": 22, "days_unknown": false, "periods": [{"year": "6", "status": "22 PTE", "days": 22}]}],
    "next_30_days": {"count": 0, "ids": [], "items": [], "until": "2026-10-10"}},
  "quizzes": [{"type_q": 0, "name": "Encuesta de Salida", "model_status": 1, "assigned": 9, "answered": 2, "pending": 7, "assigned_in_period": 0},
              {"type_q": 1, "name": "Encuesta de Norma_035_50", "model_status": 1, "assigned": 3, "answered": 0, "pending": 3, "assigned_in_period": 0}],
  "birthdays_month": [{"emp_id": 50, "name": "OSCAR IGNACIO MARISCAL LEAL", "department_id": 3, "department": "Administración", "day": 2, "date": "2024-07-02", "age": 24}],
  "data_quality": {"departures_unparsed": [], "active_with_departure": [{"emp_id": 3, "name": "ANDRES ALEJANDRO MACHORRO CLETO", "departure": "2024-07-05"}],
                   "inactive_without_departure_ids": [7, 39, 49], "without_admission_ids": [], "active_without_birthday_ids": [12, 17, 18]}},
 "msg": "Resumen RH 2024-07: 64 activos, 10 altas y 22 bajas en el mes", "error": null}
// 400 {"data": null, "msg": "month debe tener el formato YYYY-MM", "error": null}
// 401 {"error": "No autorizado. Token invalido"}
```

Tiles sugeridos y su fuente: **Plantilla** `headcount.total` + barras `by_department` · **Altas / Bajas del mes** `movements_month` (click → ids) · **Exámenes por vencer** `vencidos` en rojo, `d30`/`d60`/`d90` en semáforo, `sin_examen` como pendiente de RH · **Vacaciones pendientes** `employees_with_pending` y `pending_days_total` (`items[].days_unknown` = marcar "sin cantidad") · **Encuestas** `answered/assigned` por modelo · **Cumpleaños** lista del mes · **Calidad de datos** (opcional, para RH): conteos de `data_quality`.

### `POST /rrhh/series`

Body `{"metric": "altas_bajas" | "headcount", "date_from": "YYYY-MM-DD", "date_to": "YYYY-MM-DD", "group_by"?: "month" | "department"}` (fechas inclusivas; `group_by` ausente o `null` → `month`; `metric` sin distinguir mayúsculas).

```json
// 200 altas_bajas por mes
{"data": {"metric": "altas_bajas", "group_by": "month", "date_from": "2024-01-01", "date_to": "2024-12-31",
          "labels": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"],
          "series": [{"name": "altas", "values": [0, 0, 0, 9, 3, 3, 10, 2, 2, 4, 0, 1]}, {"name": "bajas", "values": [0, 0, 0, 2, 1, 0, 22, 0, 0, 6, 1, 0]}]},
 "msg": "altas_bajas por mes, 2024-01-01 → 2024-12-31 (12 puntos)", "error": null}
// 200 headcount por departamento (al cierre de date_to): labels = nombres del catálogo, series = [{"name": "activos", "values": [...]}]
// 400 {"data": null, "msg": "metric inválida: faltas", "error": "metric ∈ ['altas_bajas', 'headcount']"}
// 400 group_by inválido · date_from > date_to · fecha ilegible · rango > 120 meses · form: {"data": null, "msg": "Estructura de datos inválida", "error": {"date_from": ["This field is required."]}}
```

`labels` y cada `series[].values` tienen siempre la misma longitud: pintar directo. Un KPI nuevo será un `metric` nuevo con el mismo shape.

### Gotchas

- `month` es `YYYY-MM` (no `MM-YYYY`); un mes futuro es válido (altas/bajas en 0, cumpleaños del mes).
- Médicos y vacaciones **no** cambian con `month`: son estado actual.
- `vacations.items[].periods[].year` es la **llave** del JSON de `seniority` (año de antigüedad, string), no un año calendario.
- `quizzes` incluye modelos en borrador o archivados (`model_status` 0/1/2) para que el conteo histórico no desaparezca al archivar una versión.
- `birthdays_month[].date` cae al último día del mes si el cumpleaños es 29-feb en año no bisiesto (`day` conserva el 29).

## Verificación

Dev (2026-09-10, **98 checks** de midleware + **10 por HTTP** con el test client y JWT firmado; solo lecturas): parseo de fechas mezcladas y de `month`; heurística de vacaciones contra los 33 valores distintos de `status` en dev; headcount = 64 activos y suma por departamento; altas/bajas de 2024-07 contra SQL directo (10/22, tras excluir los 11 activos con fecha de baja vieja); baja en formato `DD/MM/YYYY` ubicada en su mes; cumpleaños del mes = BD y ordenados; los 8 buckets médicos particionan a los activos, `days_left` dentro de cada rango y `due_date = última + periodo` cotejado contra la fila; vacaciones = cruce manual (40 empleados, 371 días); encuestas por tipo = conteos SQL (con exclusión de control eva 360) y `assigned_in_period` de 2025-03 = 17; series por mes/departamento cuadran con los totales anuales, headcount del último mes = activos actuales; `400` de metric/group_by/fechas/rango/form; `401` sin token y con permiso `almacen`. `pyrefly check` sin errores nuevos (188 base); `app` registra las 2 rutas.

## Al modificar

- **KPI nuevo en `series`** → agregarlo a `SERIES_METRICS` y una rama en `get_rrhh_series_api` que devuelva `labels` + `series[{name, values}]`; el front no cambia.
- **Tile nuevo en `summary`** → función `_<tile>_block` que devuelva `(data, error_str|None)` y se registre en `get_rrhh_summary_api` con el patrón no-fatal (error a la lista, tile en `null`).
- **Periodicidad médica** → `MEDICAL_PERIOD_DAYS` / `medical_due` en `Functions_Aux_RH.py` (regla compartida con `GET /rrhh/employees/medical/all` y el daemon, ver [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md)); los buckets `d30/d60/d90` en `MEDICAL_BUCKETS` de este módulo.
- **Si RH estructura el `status` de vacaciones** (p.ej. días pendientes como entero en `seniority`), reemplazar `_vacation_pending_days` y borrar la heurística; el shape del tile no cambia.
- Cualquier columna nueva en los SELECT del controller → también en la tupla `*_COLUMNS` correspondiente (el midleware mapea por posición con `zip`).

## Pendientes

- **[front]** Pantalla del dashboard (S4 del plan): tiles clicables a la lista filtrada + 2 gráficas de `series`.
- **[admin/RH]** Limpiar los 11 activos con fecha de baja arrastrada y los inactivos sin fecha de baja (`data_quality`); capturar `dates` en vacaciones para que `next_30_days` tenga datos.
- ~~**[back]** `fetch_medicals` nunca emitía avisos de vencimiento (aptitud entera vs `"APTO 1"`), ni el daemon~~ — corregido el mismo día → [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md).
