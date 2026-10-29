# RRHH: DML de calidad de datos (`employees`) y una sola llave `allergies` en exámenes

Fecha: 2026-10-12 · **Estado: scripts entregados, pendientes de correr por el usuario en dev, test y prod.** Sin cambios de código. Puntos 3 y 4 del Bloque A de [`planes/plan_accion_2026_10.md`](planes/plan_accion_2026_10.md).

Cierra la parte **mecánica** del pendiente de calidad de datos que dejó [`dashboard_rrhh.md`](dashboard_rrhh.md) (`data_quality` del `GET /dashboard/rrhh/summary`) y el doble nombre `alergies`/`allergies` de [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md). Lo que necesita una decisión de RH **no** se toca por script: se corrige desde la pantalla de empleados con el listado de abajo.

## Scripts

| Script | Qué hace | Verificado en solo lectura (2026-10-12) |
|---|---|---|
| [`scripts_db_handle/rh_calidad_datos_empleados.sql`](../scripts_db_handle/rh_calidad_datos_empleados.sql) | **A)** `status` NULL → `'activo'` si no hay fecha de baja (`departure` NULL o `date` ∈ `''`/`'None'`/`'null'`), `'inactivo'` si la hay. **B)** `puesto = 'None'` (el `str(None)` de Python) → NULL. Al final, 3 consultas de solo lectura con el listado para RH | dev: 1 `status` NULL (empleado 123, alta 2025-12-05, sin baja → `activo`) + 2 `puesto` `'None'` (7 y 39). test: 0 + 2 (7 y 39) |
| [`scripts_db_handle/examenes_med_allergies_key.sql`](../scripts_db_handle/examenes_med_allergies_key.sql) | **Bloque 1 (DML)**: renombra `extra_info.alergies` → `allergies` conservando el valor; si una fila trae las dos, gana la nueva. **Bloque 2 (DDL, revisar)**: el `DEFAULT` de la columna sigue siendo `{"alergies": "", "observations": ""}`, así que una fila insertada sin `extra_info` volvería a nacer con la llave vieja; se cambia a `allergies` | dev: 49 filas con la llave vieja, 0 con la nueva, 0 con ambas. test: 49 viejas + 1 nueva. La expresión de renombrado se probó con `SELECT` sobre las filas reales |

Ambos son idempotentes: una segunda corrida afecta 0 filas. Prod no se cotejó (sin acceso de lectura desde dev); los scripts traen el `SELECT` de "antes" para ver qué tocan.

## Decisiones tomadas (confirmar con RH si no convence)

- **`status` NULL sin fecha de baja = `activo`.** Es el caso del 123 en dev: alta reciente y sin `departure`. Con fecha de baja el script pone `inactivo`. Si RH prefiere revisar uno por uno, correr solo el `SELECT` de "antes".
- **`puesto` `'None'` → NULL**, no `''`. La columna es `DEFAULT NULL`; las 13 filas con `''` (ids 90–107) se dejan como están: no son texto basura y el pendiente no las pedía.
- **`departure.date = "None"`** (7 y 39) no se toca: esos dos son inactivos **sin** fecha de baja real; RH debe capturarla (están en el listado).

## Listado para RH (dev, 2026-10-12)

Es lo mismo que `data_quality` del `summary`; en prod sale con las 3 consultas del final de `rh_calidad_datos_empleados.sql`.

- **Activos con fecha de baja arrastrada (11)** — decidir si se vacía `departure` (reingreso) o si el status es el equivocado: 3, 4, 13, 36, 86 (baja 2024-07-05) · 45, 92 (2024-07-09) · 94, 97, 104 (2024-07-26) · 113 (2024-10-29).
- **Inactivos sin fecha de baja (9)** — capturarla: 7, 39, 49, 60, 87, 111, 116, 118 y el 123 (que tras el script A pasa a activo y sale de esta lista).
- **Activos sin cumpleaños (21)** — el tile de cumpleaños los omite: 12, 17, 18, 20, 21, 24, 26, 28, 30, 32, 33, 34, 35, 38, 42, 44, 46, 55, 67, 79, 80.
- **Vacaciones sin `dates`** — el tile `next_30_days` llega vacío hasta que se capturen.

## Al modificar

- El lector de exámenes (`fetch_medicals` en `Functions_midleware_RRHH.py`) sigue tolerando `alergies` como fallback. **Quitar el fallback solo después** de correr el Bloque 1 y el Bloque 2 en las **3 BDs** (anotarlo aquí en `Notas posteriores`).
- Si aparece otro `'None'` textual en `employees` (viene de la GUI tkinter vieja, que hacía `str(None)`), agregar la columna al script B; el alta/edición por API ya no lo generan.
- `data_quality` del dashboard es la fuente para repetir este listado; no hace falta otra consulta.

## Pendientes

- **[usuario]** Correr `rh_calidad_datos_empleados.sql` y `examenes_med_allergies_key.sql` (Bloque 1 DML + Bloque 2 DDL) en dev, test y prod; pegar aquí el "antes/después".
- **[admin/RH]** Corregir desde la pantalla de empleados los 11 + 9 + 21 del listado y capturar `dates` de vacaciones.
- **[back]** Quitar el fallback `alergies` del lector cuando el DML esté en las 3 BDs.

## Notas posteriores

- **2026-10-28 — bloque 2 de `examenes_med_allergies_key.sql` corregido (`P-042`).** En test el bloque 1 corrió (0 llaves viejas, 50 nuevas) y el bloque 2 falló con el error 1101 ("BLOB, TEXT, GEOMETRY or JSON column 'extra_info' can't have a default value"): en MySQL 8.4, `ALTER COLUMN ... SET DEFAULT` no acepta una columna JSON aunque el valor vaya entre paréntesis. El script ahora redefine la columna con `MODIFY COLUMN extra_info JSON NULL DEFAULT ('{"allergies": "", "observations": ""}')`, la misma definición que muestra `SHOW CREATE TABLE` en dev y test (json, nullable, sin comentario) con la llave cambiada. Dev sigue con 49 llaves viejas y el DEFAULT viejo en las dos BDs.
- **2026-10-28 — `P-042` cerrado y fallback quitado.** El usuario corrió los dos bloques en las 3 BDs. verificado en solo lectura en dev y test el 2026-10-28; prod, según el usuario (el modo automático no deja leer su BD): 0 llaves `alergies` (dev 49 `allergies`, test 50) y el DEFAULT de `extra_info` ya trae `allergies`. `fetch_medicals` ([`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py)) lee solo `allergies`; en dev la API coincide con la BD (15 registros). `rh_calidad_datos_empleados.sql` (`P-039`) sigue sin correr: dev 3 filas, test 2.
