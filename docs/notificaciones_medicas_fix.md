# Exámenes médicos — avisos de vencimiento que nunca se emitían (`GET /rrhh/employees/medical/all` + daemon)

> Bug encontrado al construir el [`dashboard_rrhh.md`](dashboard_rrhh.md) (2026-09-10) y corregido a petición del usuario el mismo día. Sin cambio de esquema ni de rutas.

## El bug (dos sitios, misma clase)

1. **`fetch_medicals`** (`Functions_midleware_RRHH.py`, detrás de `GET /rrhh/employees/medical/all`): la tabla de límites estaba indexada por `"APTO 1"`, `"APTO 2"`… pero `examenes_med.aptitude_actual` es un **entero** (1..4, catálogo `sql_telintec_mod_rrhh.aptitude`). `apt_actual in limits` era siempre `False`, así que los mensajes `[CRÍTICO]`/`[AVISO]` de `error` **nunca salían** y el endpoint respondía siempre `error: null`. Además `extra_info.get("allergies")` no leía los registros viejos, que traen la llave `alergies`.
2. **`MedicalNotifications`** (`templates/daemons/NotificationsSearch.py`, disparado una vez al día por `GET /dashboard/notifications/medicals`): decidía con `hoy.year - última.year > 15`, o sea, avisaba solo tras **15 años** sin examen; y `item["dates"][-1]` tronaba con la lista vacía, dejando la bandera `flag_medical` en `False` (el endpoint respondía "ya se está realizando la búsqueda" para siempre).

Resultado: RH no recibía ninguna notificación de exámenes vencidos. En dev hay **15 activos vencidos** hoy.

## Qué cambió

| Capa | Archivo | Cambio |
|---|---|---|
| **Regla compartida** (nueva) | [`Functions_Aux_RH.py`](../templates/resources/methods/Functions_Aux_RH.py) | `MEDICAL_PERIOD_DAYS = {1: 365, 2: 180, 3: 90}`, `MEDICAL_NO_APTO = 4`, `MEDICAL_WARNING_DAYS = 30`; `normalize_aptitude` (int, float, `"2"`, `"APTO 2"` → int); `last_medical_date` (máximo legible de `renovacion`); **`medical_due(aptitude, last_date, today)`** → `{alert, period_days, due_date, days_left}` con `alert` ∈ `vencido` · `por_vencer` (0..30 días) · `al_dia` · `no_apto` · `sin_periodo` (aptitud 0/desconocida) · `sin_fecha`. |
| **Orquestación** | [`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) `fetch_medicals` | Usa `medical_due`; cada registro gana `alert`, `last_date`, `due_date`, `days_left`, `period_days` (aditivo, el shape previo se conserva); mensajes en `error` **solo de empleados ACTIVOS** con `vencido`/`por_vencer`/`no_apto`; `allergies` lee también `alergies`; JSON de `aptitud`/`renovacion`/`extra_info` con parseo defensivo. |
| **Daemon** | [`NotificationsSearch.py`](../templates/daemons/NotificationsSearch.py) | `build_medical_notifications(items)` arma una línea por activo con alerta a partir de los campos calculados (sin pandas, sin `dates[-1]`); `MedicalNotifications` no inserta nada si no hay alertas; `run()` restablece `flag_medical` en `finally`. |
| **Dashboard** | [`MD_DashboardRRHH.py`](../templates/resources/midleware/MD_DashboardRRHH.py) | Su bucket médico ahora llama a la misma `medical_due` (antes tenía copia local de la tabla); los buckets `d30/d60/d90` siguen siendo un refinamiento de `por_vencer`/`al_dia`. |

Con esto hay **una sola fuente** de la periodicidad para los tres consumidores.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`), permiso `rrhh`. Envelope `{data, msg, error}`.

### `GET /rrhh/employees/medical/all` (misma ruta, campos nuevos)

```json
// 200
{"data": [{"exist": true, "id_exam": 2, "name": "ALCEDA ORTIZ NICOLE STTEFHANO", "blood": "B+", "status": "ACTIVO",
           "aptitudes": [1, 1.0], "dates": ["2024-02-15 00:00:00", "2025-02-12 00:00:00"], "apt_last": 1, "emp_id": 86,
           "allergies": "", "observations": "",
           "alert": "vencido", "last_date": "2025-02-12", "due_date": "2026-02-12", "days_left": -210, "period_days": 365}],
 "msg": null,
 "error": ["[CRÍTICO] El empleado ALCEDA ORTIZ NICOLE STTEFHANO requiere revisión: aptitud 1, última fecha 2025-02-12, venció el 2026-02-12 (hace 210 días, límite de 365 días)."]}
```

- `alert` es el campo para pintar: `vencido` rojo · `por_vencer` ámbar (`days_left` 0..30) · `al_dia` · `no_apto` · `sin_periodo` (aptitud sin periodicidad: capturar aptitud) · `sin_fecha` (sin examen legible). `due_date`/`days_left`/`period_days` vienen `null` fuera de `vencido`/`por_vencer`/`al_dia`.
- **`error` ya no es siempre `null`**: cuando hay activos con alerta trae la lista de mensajes (era el contrato original, solo que nunca se cumplía). Un `200` con `error` lista **no es un fallo**; el front que trataba `error != null` como error debe leer `data` igual.
- El listado sigue trayendo solo exámenes de empleados **activos** (filtro del controller `get_all_examenes`, sin cambio).

### `GET /dashboard/notifications/medicals` (sin cambio de contrato)

`201` "Buscando notificaciones médicas" la primera vez del día, `200` después. La notificación in-app que crea (permiso `rrhh`, título "Notificaciones de sistema") ahora lista **una línea por activo** vencido, por vencer o NO APTO; si no hay ninguno, no se inserta nada.

## Verificación

Dev (2026-09-10; la notificación de prueba se borró y `files/flags_daemons.json` quedó como estaba): **50 checks** de midleware — `normalize_aptitude` con 10 formas, `last_medical_date` con lista/JSON crudo/vacío/basura, `medical_due` en los bordes (−210, 0, 10, 30, 31 días; aptitud 4 con y sin fecha; 0/None), `fetch_medicals` = 15 exámenes de activos con los 5 campos nuevos y los 11 previos, 15 mensajes en `error` (antes `null`) solo de activos, `due_date` cotejado contra la fila de BD, `allergies` con la llave vieja, **dashboard `vencidos` == `fetch_medicals` `vencido`** (mismos 15 ids), daemon con inserción real y limpieza — más **9 por HTTP** (endpoint con lista de avisos, disparo del daemon `201` → notificación con 15 líneas → bandera restablecida → segunda llamada `200`). Smoke del dashboard sigue 98/98; `pyrefly check` en la base (188).

## Al modificar

- **Periodicidad o umbral de aviso** → solo `MEDICAL_PERIOD_DAYS` / `MEDICAL_WARNING_DAYS` en `Functions_Aux_RH.py`; los tres consumidores lo heredan.
- **Aptitud nueva en el catálogo `aptitude`** → agregar su periodo a `MEDICAL_PERIOD_DAYS` (sin él cae en `sin_periodo`, no truena).
- El daemon depende de que `fetch_medicals` devuelva `alert`; si se cambia el shape, actualizar `build_medical_notifications`.

## Pendientes

- **[front]** Pintar `alert`/`due_date` en la pantalla de exámenes médicos y dejar de tratar `error` lista como fallo.
- **[back]** Corregir el doble nombre `alergies`/`allergies` en BD (migrar la llave vieja) cuando se toque el CRUD de exámenes.
