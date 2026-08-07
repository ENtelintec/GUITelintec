# Migración de esquemas RRHH → `sql_telintec_mod_rrhh`

> Plan por fases para mover las tablas del dominio RRHH desde `sql_telintec` hacia el esquema por departamento `sql_telintec_mod_rrhh` (creado en [`quizz_models_crud.md`](quizz_models_crud.md)). **Fase 1 (encuestas) ejecutada 2026-08-07**; la **Fase 2 se adelantó** (estaba post-mes) como tarea de fondo del back mientras el front integra encuestas — decidido en la segunda sesión de grill del 2026-08-07 (la primera cerró el plan general).

## Decisiones acordadas

| Tema | Decisión |
|---|---|
| **Alcance del mes** | Plan completo documentado; ejecución solo de la Fase 1 (encuestas) |
| **`tasks_gui`** | Se mueve **y se renombra** a `quizz_tasks` (simétrica con `quizz_models`). En dev y prod el 100% de sus filas son quizzes (verificado 2026-08-07) |
| **Regla de tasks** | De ahora en adelante, cualquier tabla de tasks se divide **por departamento que asigna**; `quizz_tasks` es la de RRHH |
| **Corte** | **Vista puente**: `RENAME TABLE` + `CREATE VIEW` con el nombre viejo; el código viejo sigue funcionando y el DDL se desacopla de los deploys. Drop diferido |
| **Tablas compartidas** | `employees`, `departments`, `users_system` = **núcleo compartido**, se quedan en `sql_telintec`. Moverlas a un hipotético `mod_core` es otra iniciativa, no esta |
| **Calendario Fase 1** | Viaja **junto con la consolidación de namespaces** `misc`+`rrhh` ([`pendientes.md`](pendientes.md)), en S2 del [`plan_rh_mes.md`](plan_rh_mes.md), como un solo lote |
| **Fases 2+ (post-mes)** | Las 5 tablas RRHH-privadas en **un solo lote** (un DDL, un barrido, una regresión con la hoja de comprobación). *Actualización 2026-08-07: se adelantó — ver decisiones de la Fase 2 abajo* |
| **DDL** | Todo DDL se entrega como script en [`scripts_db_handle/`](../scripts_db_handle/) y **lo revisa/ejecuta el usuario**; ningún agente corre DDL |

## Por qué la vista puente (restricción de los 3 entornos)

`execute_sql` ([connection.py](../templates/database/connection.py)) honra `is_tester` en **cualquier** despliegue: la BD de test la comparten a la vez el código local (dev) y el de prod. Un rename seco en test rompe a la versión que aún no se actualiza. La vista puente (`CREATE VIEW sql_telintec.tasks_gui AS SELECT * FROM ...quizz_tasks`, actualizable, `SQL SECURITY INVOKER`) deja al código viejo operando mientras cada despliegue se actualiza a su ritmo. Además la conexión no fija `database=` — todas las queries califican `esquema.tabla` — así que migrar = mover tabla + actualizar literales; no se toca configuración.

## Fase 1 — Encuestas (este mes, S2)

> **Estado (2026-08-07): ejecutada.** DDL corrido por el usuario en las 3 BDs (verificado: tabla + vista con conteos iguales en dev/test/prod), literales y docstrings actualizados, y consolidación de namespaces en el mismo lote ([`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md)). Smoke completo verde contra dev. **Solo queda el Paso 3**: `DROP` de las vistas puente en las 3 BDs cuando prod ya corra este código (trackeado en [`pendientes.md`](pendientes.md)).

`sql_telintec.tasks_gui` → `sql_telintec_mod_rrhh.quizz_tasks`. DDL en [`scripts_db_handle/migracion_quizz_tasks.sql`](../scripts_db_handle/migracion_quizz_tasks.sql) (RENAME + vista + rollback + drop diferido). La tabla es autocontenida: sin FKs entrantes/salientes, sin vistas, sin triggers, sin rutinas/eventos que la mencionen (verificado en dev).

**Barrida de literales (7 en 2 archivos):**

- [`tasks_controller.py`](../templates/controllers/misc/tasks_controller.py) — 6 literales (INSERT/UPDATE/DELETE/3 SELECT).
- [`quizz_models_controller.py`](../templates/controllers/rrhh/quizz_models_controller.py) — 1 literal (conteo de tasks por tipo del guard de DELETE).
- Docstrings que mencionan `tasks_gui` (no ejecutan SQL, actualizar de paso): [`MD_Eva360.py`](../templates/resources/midleware/MD_Eva360.py), [`MD_QuizzModels.py`](../templates/resources/midleware/MD_QuizzModels.py), y el header de [`quizz_models.sql`](../scripts_db_handle/quizz_models.sql).

Los daemons y `methods/` no tienen SQL propio (verificado): el radio queda contenido en controllers.

**Runbook** (aplica igual a fases futuras):

1. Entregar el `.sql` → **revisión del usuario** (regla fija).
2. Usuario corre el DDL en **las 3 BDs** (dev, test, prod) en una misma sesión — la vista protege al código viejo, incluido prod.
3. Merge del lote de código (literales + consolidación de namespaces), smoke vs dev, hoja del tester vs test, deploy de prod.
4. Periodo de gracia → usuario corre el **DROP de la vista** en las 3 BDs (bloque diferido del mismo script).

**Verificación por fase:** `COUNT(*)` pre/post por tabla (vía vista y vía tabla nueva, deben coincidir) · `grep` cero de `sql_telintec.tasks_gui` en `*.py` · `pyrefly check` · smoke de endpoints de encuestas vs dev · re-corrida de la sección correspondiente de la hoja de comprobación por el tester.

**Rollback:** mientras la vista exista, revertir = `DROP VIEW` + `RENAME` de vuelta (bloque comentado en el script).

## Fase 2 — Tablas RRHH-privadas (adelantada, un solo lote)

> **Estado (2026-08-07): ejecutada.** Estaba planeada post-mes; se adelantó como **tarea de fondo** (grill, segunda sesión 2026-08-07) porque el back ya cumplió S2 y clima/eva360 — el soporte al front y la encuesta de salida(0) siguen teniendo prioridad. **DDL corrido por el usuario en las 3 BDs el mismo día** ([`scripts_db_handle/migracion_fase2_rrhh.sql`](../scripts_db_handle/migracion_fase2_rrhh.sql); verificado: 6 vistas + 6 tablas en `mod_rrhh` con conteos idénticos, FKs siguieron el `RENAME` — `employees` cross-schema, `aptitude` intra), **barrido hecho** (89 reemplazos = las 86 líneas, 3 con doble mención en JOINs; grep-cero de refs viejas; `pyrefly` sin errores nuevos) y **smoke verde vs dev**: lecturas por las 6 rutas nuevas incluidos los JOIN cross-schema, más ciclo INSERT→UPDATE→SELECT→DELETE en `bitacora_rh`. En el mismo lote se corrió el seed de `quizz_models` en test (5 modelos ACTIVA — desbloquea encuestas con `is_tester`). **Falta**: re-corrida del tester de las secciones afectadas de la hoja vs test, deploy de prod del tren S2+Fase2, y el `DROP` diferido de las 7 vistas ([`pendientes.md`](pendientes.md)).

**Decisiones del grill de Fase 2 (2026-08-07):**

| Tema | Decisión |
|---|---|
| **Calendario** | Adelantar como tarea de fondo; soporte al front y salida(0) van primero. Viable porque Fase 2 es invisible al front (cero cambios de contrato) |
| **Tren de deploy** | **Mismo tren que el lote S2** (prod aún no lo deploya): DDL de Fase 2 ya, un solo deploy de prod con Fase1+Fase2, una sola ventana de gracia y un solo `DROP` de las **7** vistas puente (`tasks_gui` + estas 6) |
| **Regresión** | Smoke del back vs dev (lectura+escritura por tabla, vía vista y vía tabla nueva) + el tester re-corre **solo las secciones afectadas** de la hoja (médicos, fichajes, bitácora RH, vacaciones, nómina) vs test **antes del deploy de prod**, sin bloquear sus UIs |
| **Nombres** | **Idénticos** (sin renombrar `bitacora_rh` ni nada): el barrido queda en puro cambio de prefijo y no hay razón de simetría como en Fase 1 |
| **Consumidores externos de BD** | No existen (confirmado por el usuario): solo esta API toca MySQL → el `DROP` diferido es seguro; las 6 tablas llevan vista puente igual (incluida `aptitude`, por uniformidad y costo cero) |
| **Secuencia** | `.sql` + docs ahora; barrido de los 86 literales cuando el DDL haya corrido (al menos en dev) |

**Re-verificación pre-DDL (2026-08-07, exigida por "Al modificar" — hecha contra las 3 BDs, no solo dev):** conteos de refs re-generados e **idénticos a la tabla de abajo** (86 líneas en 6 controllers; ojo: 2 líneas de `vacations_controller` tienen JOIN que menciona `examenes_med` y `vacations` a la vez); cero refs sin calificar (todo va como `sql_telintec.<tabla>`); daemons sin SQL (el match de `payroll` en `NotificationsSearch.py` es un `case` con `print` stub); FKs exactamente las esperadas (ver abajo; `fichajes` sin FK); cero triggers/vistas/rutinas/eventos sobre las 6; tablas de 0–90 filas (`RENAME` metadata-only). **Grants: no-problema de facto** — el usuario de app en test/prod (`adminTelintec`) tiene privilegios globales (`SHOW GRANTS` verificado), así que las vistas `INVOKER` operan sin GRANT adicional (la de `tasks_gui` ya funciona con las credenciales de la app en los 3 entornos, conteos vista=tabla verificados). *Higiene aparte (fuera de alcance): un usuario de app con privilegios globales merece su propia iniciativa de acotamiento.*

Nadie fuera de los controllers de RRHH las toca (verificado por grep). Un DDL (multi-`RENAME` atómico + 6 vistas puente), un barrido de **86 literales en 6 controllers**, una regresión con la hoja (secciones afectadas):

| Tabla | Refs | Archivos |
|---|---|---|
| `examenes_med` | 23 | [`em_controller.py`](../templates/controllers/employees/em_controller.py) (17), [`employees_controller.py`](../templates/controllers/employees/employees_controller.py) (4), [`vacations_controller.py`](../templates/controllers/employees/vacations_controller.py) (2) |
| `fichajes` | 30 | [`fichajes_controller.py`](../templates/controllers/fichajes/fichajes_controller.py) |
| `bitacora_rh` | 16 | [`bitacora_rh_controller.py`](../templates/controllers/employees/bitacora_rh_controller.py) |
| `vacations` | 9 | [`vacations_controller.py`](../templates/controllers/employees/vacations_controller.py) |
| `payroll` | 8 | [`payroll_controller.py`](../templates/controllers/payroll/payroll_controller.py) |
| `aptitude` | 0 | catálogo puro de BD (solo lo referencia el FK de `examenes_med`); viaja en el lote con costo cero de código |

**FKs:** `examenes_med`/`vacations`/`bitacora_rh`/`payroll` tienen FK hacia `sql_telintec.employees` — `RENAME TABLE` las conserva y actualiza, quedan **cross-schema** (soportado por InnoDB; ya pasa con `mod_admin`). `examenes_med`→`aptitude` queda intra-esquema porque `aptitude` se mueve en el mismo `RENAME`. Sin rutinas ni eventos que mencionen estas tablas (re-verificado 2026-08-07 en las 3 BDs). El DDL está escrito en [`migracion_fase2_rrhh.sql`](../scripts_db_handle/migracion_fase2_rrhh.sql) (RENAME atómico + 6 vistas + verificación de conteos + rollback + drop diferido) y sigue el runbook de arriba.

## Fuera de alcance (núcleo compartido)

`employees` (la usan heads/SM/orders además de RRHH), `departments` (contracts/heads) y `users_system` (login de toda la app) **se quedan en `sql_telintec`**. Cualquier movimiento futuro sería una iniciativa `mod_core` aparte.

## Reglas de diseño que deja este plan

- **Toda tabla nueva de RRHH nace en `sql_telintec_mod_rrhh`** (como ya se hizo con `quizz_models`).
- **Tasks por departamento asignador**: si otro departamento necesita tasks, tabla propia en su esquema — no se comparte `quizz_tasks`.
- **Todo DDL**: script en `scripts_db_handle/`, revisión y ejecución del usuario, jamás automático.
- Recordatorio de grants: el usuario MySQL de la app necesita `SELECT/INSERT/UPDATE/DELETE` sobre `sql_telintec_mod_rrhh.*` en test/prod; la vista es `SQL SECURITY INVOKER`, así que sin ese grant el código viejo también fallaría. **Verificado 2026-08-07: satisfecho de facto** — `adminTelintec` (test/prod) tiene privilegios globales `ON *.*`, no hay GRANT que correr. (Acotar ese usuario sería una iniciativa de higiene aparte.)

## Contrato mínimo para el front

**Ninguno — cero cambios de contrato.** La migración es invisible al front: ningún endpoint cambia ruta, request, response ni auth. (La consolidación de namespaces `misc`+`rrhh` que viaja en el mismo lote **sí** cambiará rutas; su contrato irá en el doc de esa consolidación, no en este.)

## Al modificar

- Código nuevo de encuestas: referenciar **siempre** `sql_telintec_mod_rrhh.quizz_tasks`; la vista `sql_telintec.tasks_gui` es temporal y desaparece en el Paso 3 — no escribir código nuevo contra ella.
- Si se agrega una tabla RRHH nueva antes de la Fase 2, nace directo en `mod_rrhh` (no engordar la lista de la Fase 2).
- Al ejecutar la Fase 2: regenerar los conteos de refs con grep (los de la tabla de arriba son del 2026-08-07) y verificar de nuevo FKs/vistas/triggers en `information_schema` antes de escribir el DDL.
- Al cerrar cada fase (drop de vistas incluido), reflejarlo en [`pendientes.md`](pendientes.md).
