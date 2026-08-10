# Consolidación de namespaces de encuestas (`misc` → `rrhh`)

> Los 3 recursos de encuestas que vivían en `GUI/api/v1/misc` se mueven a `GUI/api/v1/rrhh` en **corte duro** (las rutas viejas responden 404). Con esto **todos** los endpoints de encuestas viven bajo `rrhh`. Viaja en el mismo lote S2 que la Fase 1 de la migración de esquema ([`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md): `tasks_gui` → `sql_telintec_mod_rrhh.quizz_tasks`, DDL ya corrido en dev/test/prod con vista puente). Cierra el pendiente "Consolidar namespaces" de [`encuestas_refactor.md`](encuestas_refactor.md).

## Qué cambió (4 capas)

- **HTTP** ([`rs_Misc.py`](../templates/resources/rs_Misc.py) → [`rs_RRHH.py`](../templates/resources/rs_RRHH.py)): las clases `Task`/`TaskGui`/`DownloadFileQuizz` salen de `misc` y entran a `rrhh` como `TaskQuizz`/`TasksByEmployee`/`DownloadFileQuizz`, **misma lógica, mismos forms, misma auth**. `misc` conserva lo no-encuesta (notificaciones, AV, dashboard, settings).
- **Orquestación**: `get_task_by_id_employee` se muda de [`Functions_midleware_misc.py`](../templates/resources/midleware/Functions_midleware_misc.py) a [`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) (idéntica; ahí viven las demás funciones de encuestas). `create/update/delete_task_from_api` y `get_quizz_template_api` no se mueven, solo cambia quién las importa.
- **DB** ([`tasks_controller.py`](../templates/controllers/misc/tasks_controller.py), [`quizz_models_controller.py`](../templates/controllers/rrhh/quizz_models_controller.py)): los 7 literales `sql_telintec.tasks_gui` → `sql_telintec_mod_rrhh.quizz_tasks` (la migración Fase 1).
- **Modelos**: sin cambios — los forms (`TaskInsertForm`/`TaskUpdateForm`/`TaskDeleteForm`) y `api.model` son los mismos, solo se importan ahora desde `rs_RRHH`.

Verificado contra BD dev: ciclo completo POST→GET→PUT→DELETE por las rutas nuevas (ejercita los 4 SQL contra `quizz_tasks`), rutas viejas 404, `misc` restante vivo, pyrefly sin errores nuevos (191 = línea base).

## Contrato mínimo para el front

**Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Base: `/GUI/api/v1`.

**Solo cambia el prefijo del namespace** — request, response, códigos de estado y permisos son **idénticos** a los documentados en [`eva360_evaluation.md`](eva360_evaluation.md) y [`encuestas_refactor.md`](encuestas_refactor.md):

| Ruta vieja (ahora 404) | Ruta nueva | Métodos | Permiso |
|---|---|---|---|
| `/misc/task/quizz` | `/rrhh/task/quizz` | `POST` (asignar) · `PUT` (capturar) · `DELETE` | `rrhh` (PUT también `common`) |
| `/misc/task/<emp_id>` | `/rrhh/task/<emp_id>` | `GET` (tasks del empleado) | auto-acceso: el `emp_id` del token puede ver las suyas |
| `/misc/download/quizz/<type_q>` | `/rrhh/download/quizz/<type_q>` | `GET` (template del cuestionario) | `rrhh` **y `common`** (2026-08-10: el empleado que contesta necesita el template para renderizar la captura; antes solo `rrhh` bloqueaba el flujo de captura con token de empleado) |

Shapes de referencia (sin cambios):

- `POST /rrhh/task/quizz` — `{"title": "quizz ...", "emp_destiny": N, "emp_origin": N, "date_limit": "YYYY-MM-DD", "metadata": {"name_emp": "...", "id_emp": N, "type_quizz": T, ...}, "data_raw": "{}"}` → `201 {"data": {"id_task": N}, "msg": "Tarea creada correctamente (ID N)", "error": null}`. Exige modelo de encuesta **ACTIVO** (si no → `400` con `msg` explicativo).
- `PUT /rrhh/task/quizz` — `{"id": N, "body": {…body del GET…, "status": 1}, "data_raw": "{\"4\":{\"answer\":0}}"}` → `200`. **Conservar `metadata` intacta** al re-mandar el `body` (trae el linking de eva360).
- `DELETE /rrhh/task/quizz` — `{"id": N}` → `200`.
- `GET /rrhh/task/<emp_id>` → `200 {"data": [{"id", "body", "data_raw", "timestamp"}], "msg": null, "error": null}`.

**Gotcha del PUT (preexistente, aplica igual que antes)**: si el `metadata` que regresa el GET trae campos de fecha vacíos (`date`, `admision`, `departure` en `null` o `""`), hay que **omitir esas llaves** al re-mandarlo — el validador rechaza fecha vacía con `400 {"errors": {"body": {"metadata": {"date": ["Not a valid date value."]}}}}`. Omitir la llave pasa; mandarla vacía no.

## Al modificar

- Endpoint nuevo de encuestas → siempre en `rs_RRHH.py`; `misc` ya no debe ganar rutas de encuestas.
- Los docs históricos ([`eva360_evaluation.md`](eva360_evaluation.md), [`encuestas_refactor.md`](encuestas_refactor.md), [`quizz_models_crud.md`](quizz_models_crud.md)) siguen mencionando `/misc/...` en sus contratos: valen los shapes, **el prefijo es `rrhh`** (tabla de arriba).
- El `DROP` de las vistas puente de la migración queda pendiente hasta que prod corra este código (ver [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md) y `pendientes.md`).
