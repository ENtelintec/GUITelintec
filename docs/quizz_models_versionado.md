# Modelos de encuesta — versionado (clonar, publicar-archiva, migrar pendientes) y candado por tasks

> Pieza 2 del [`plan_mes_2.md`](plan_mes_2.md) (S1, 2026-09-07). Back del **constructor visual de encuestas**: RH necesita "cambiar las preguntas de una encuesta" y "crear una a partir de otra". Sobre el CRUD de [`quizz_models_crud.md`](quizz_models_crud.md) cambian tres cosas: el **candado del template pasa de status a tasks**, aparece el **versionado por clonación** (`replaces`/`replaced_by`, publicar la nueva archiva la vieja) y la **migración de encuestas pendientes** a la versión nueva. **Requiere DDL** ([`scripts_db_handle/quizz_models_versions.sql`](../scripts_db_handle/quizz_models_versions.sql), 2 columnas NULL): sin él, todo `/quizz/models` responde `400` "Unknown column 'replaces'".

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_RRHH.py`](../templates/resources/rs_RRHH.py) | Rutas nuevas `POST /quizz/models/<type_q>/clone`, `PUT /quizz/models/<type_q>/migrate-tasks`; `PUT /status` acepta `migrate_pending`. |
| **Orquestación** | [`MD_QuizzModels.py`](../templates/resources/midleware/MD_QuizzModels.py) | `update_quizz_model_api` con candado por `tasks_total` (template y quitar rúbrica); `update_quizz_model_status_api` archiva al origen al publicar, migra pendientes, guarda `replaced_by` y protege la reactivación; nuevos `clone_quizz_model_api`, `migrate_quizz_tasks_api`, helpers `_tasks_total`, `_next_version_name`, `_migrate_pending`; `rules` del catálogo actualizadas. |
| **DB** | [`quizz_models_controller.py`](../templates/controllers/rrhh/quizz_models_controller.py) · [`tasks_controller.py`](../templates/controllers/misc/tasks_controller.py) | `SELECT_COLUMNS`/`LIST_COLUMNS`/`_UPDATABLE_COLS` + INSERT ganan `replaces`/`replaced_by` (**al final**, los mapeos son posicionales). Nuevos `count_tasks_for_migration` y `migrate_pending_tasks_type` (`JSON_SET` sobre `body.metadata.type_quizz` + `migrated_from`). |
| **Modelos** | [`api_quizz_models_models.py`](../static/Models/api_quizz_models_models.py) · [`api_models.py`](../static/Models/api_models.py) | `quizz_model_clone_model`/`QuizzModelCloneForm`, `quizz_model_migrate_model`/`QuizzModelMigrateForm`, `migrate_pending` en status; `MetadataTasksForm` + `metadata_task_model` declaran **`migrated_from`** (sin eso el `PUT /task/quizz` lo borraría al validar). |

## Reglas (reemplazan la tabla de ciclo de vida de `quizz_models_crud.md`)

| Regla | Antes | Ahora |
|---|---|---|
| Editar `template` | solo BORRADOR | **cualquier status mientras `tasks_total = 0`** (ninguna encuesta asignada, contestada o no). Con tasks → `400` "clona". Razón: no hay snapshot por task, lo que protege el historial es que existan tasks, no el status |
| Quitar `rubric` (`null`) | solo BORRADOR | solo sin tasks (misma razón) |
| "Cambiar preguntas" con tasks | crear modelo nuevo a mano | **`POST /clone`** → borrador con `replaces` → editar → `PUT /status {1}` |
| Publicar un clon (`0→1` con `replaces`) | — | si el origen está **ACTIVO se archiva solo** (`status 2`, `replaced_by = nuevo`, history en ambos); si el origen está en borrador/archivado solo se deja el enlace `replaced_by`. Con `migrate_pending: true` además se migran sus pendientes |
| Reactivar (`2→1`) un modelo con `replaced_by` | libre | **`400` si la versión que lo reemplazó sigue ACTIVA** (archívala primero); si ya no lo está, se reactiva y se limpia `replaced_by` (rollback a la versión anterior) |
| Migrar encuestas | — | solo **pendientes** (`data_raw` vacío) y **sin `evaluation_id`** (eva 360 lleva el linking del proceso); las contestadas jamás (sus respuestas mapean al template viejo). Deja `metadata.migrated_from = <tipo viejo>` |

Notas: `protected=1` (Norma 035) se puede clonar y archivar como cualquiera (no borrar). El nombre por defecto del clon es `"<nombre> (v2)"` / `(v3)`… (`_next_version_name`). El `type` de la rúbrica clonada se re-sella al id nuevo. El clon deja rastro `"Clonado hacia la versión N"` en el history del origen.

## Contrato mínimo para el front

- **Auth**: `Authorization` con el **JWT crudo** (sin `Bearer`), permiso `rrhh`. Base `/GUI/api/v1/rrhh`. Envelope `{data, msg, error}`.
- `GET /quizz/models` (`?all=1`) y `GET /quizz/models/<type_q>` ganan `replaces` (int | null) y `replaced_by` (int | null) — con ellos la UI agrupa versiones y explica "archivada por la v2".

### `PUT /quizz/models/<type_q>` (candado nuevo)

Igual que antes; el `400` de template cambia de motivo:
```json
{"data": null, "msg": "El template está bloqueado: el modelo 3 (ACTIVA) tiene 7 encuesta(s) asignadas y sus respuestas mapean contra este template. Para cambiar preguntas clona el modelo (POST /rrhh/quizz/models/<id>/clone) y publica la versión nueva.", "error": null}
```
El detalle trae `tasks_total`: si es `0`, el editor visual puede habilitar la edición de preguntas aunque esté ACTIVA.

### `POST /quizz/models/<type_q>/clone`

Body opcional `{"name": "Clima laboral 2027"}` (o `{}`).
```json
// 201
{"data": {"type_q": 8, "replaces": 3, "name": "Encuesta de clima laboral (v2)", "status": 0, "has_rubric": true, "warnings": []},
 "msg": "Modelo de encuesta 3 clonado como 8 (Encuesta de clima laboral (v2)) en borrador", "error": null}
// 404 modelo inexistente
```
Después: editar el template del `8` con `PUT` (sin tasks → libre), y publicar.

### `PUT /quizz/models/<type_q>/status`

Body `{"status": 1, "migrate_pending": true}` (`migrate_pending` opcional, default `false`; solo tiene efecto al publicar un modelo con `replaces`).
```json
// 200 publicar un clon (archiva al 3 y migra sus pendientes)
{"data": {"type_q": 8, "status": 1, "archived": 3, "migrated": 4, "skipped_answered": 12, "skipped_eva360": 0},
 "msg": "Publicación del modelo de encuesta 8 (...); versión anterior 3 archivada; 4 encuesta(s) pendiente(s) migradas (12 contestadas y 0 de eva 360 conservadas)", "error": null}
// 200 publicar sin replaces: {"type_q": 9, "status": 1, "archived": null} (sin llaves de migración)
// 200 con fallo parcial: "error" trae el motivo (p.ej. no se pudo archivar la anterior) y el status nuevo ya quedó aplicado
// 400 reactivar una versión reemplazada cuya nueva sigue activa:
{"data": null, "msg": "El modelo 3 fue reemplazado por la versión 8 (...), que sigue ACTIVA. Archívala primero para volver a esta versión.", "error": null}
```
UI: al publicar un modelo con `replaces`, mostrar el checkbox **"migrar encuestas pendientes a esta versión"**, desmarcado por defecto.

### `PUT /quizz/models/<type_q>/migrate-tasks`

Body `{"from_type": 3, "only_pending": true}` (`only_pending` ausente/`null` = `true`; `false` → `400`). El destino debe estar ACTIVO.
```json
// 200
{"data": {"from_type": 3, "to_type": 8, "migrated": 4, "skipped_answered": 12, "skipped_eva360": 0},
 "msg": "4 encuesta(s) pendiente(s) migradas de 3 a 8; 12 contestadas y 0 de eva 360 conservadas", "error": null}
// 400 destino no ACTIVO / from_type == destino / only_pending false · 404 modelo (origen o destino) inexistente
```
Las tasks migradas conservan todo su `metadata` y ganan `migrated_from`; el empleado ve el cuestionario nuevo en `GET /download/quizz/8`.

### Gotchas

- Sin el DDL corrido en la BD contra la que se integra, **todo** `/quizz/models` da `400` con "Unknown column 'replaces'": es la señal de que falta [`quizz_models_versions.sql`](../scripts_db_handle/quizz_models_versions.sql).
- `migrated: 0` no es error: no había pendientes.
- `replaces` apunta a un id que puede ya no existir (DELETE físico sin tasks): mostrar "versión eliminada".

## Verificación

Contra BD dev (2026-09-07), lo que no depende del DDL: forms (`migrate_pending` default `false`/`true`, clone vacío, `MetadataTasksForm` conserva `migrated_from`), `_next_version_name`, y la migración con 3 tasks desechables de un tipo ficticio (1 pendiente, 1 contestada, 1 eva 360 pendiente): conteo `(1,1,1)`, migra exactamente la pendiente (tipo como **número** JSON, `migrated_from` sellado), contadores antes/después, el `metadata` real sigue validando; tasks borradas al final. `app` importa y `pyrefly check` sin errores nuevos. **Ciclo completo tras el DDL en dev (mismo día, 32 checks, modelos y tasks desechables borrados al final)**: crear+publicar origen → template editable en ACTIVA sin tasks → con 2 tasks (1 pendiente, 1 contestada) template y quitar rúbrica → `400`, name → `200` → clonar (`(v2)`, rúbrica re-sellada, history en ambos; clon del clon → `(v3)`) → editar template del clon → publicar con `migrate_pending` (origen archivado con `replaced_by`, 1 pendiente migrada con `migrated_from`, contestada conservada; listado y picker correctos) → reactivar origen `400` → `migrate-tasks` (destino archivado `400`, from==to `400`, `only_pending:false` `400`, repetir `migrated:0`, origen inexistente `404`) → archivar clon → reactivar origen `200` con `replaced_by` limpio → migrar de vuelta → borrar clon `200`, borrar origen con tasks `400`.

## Al modificar

- **Columna nueva** en `quizz_models` → DDL + `SELECT_COLUMNS`/`LIST_COLUMNS` **al final** + `_UPDATABLE_COLS` si se escribe + este doc.
- **Otra regla de candado** → `_tasks_total` es el único punto: hoy cuenta cualquier task del tipo; si un día hay snapshot por task, ahí se relaja.
- **Migrar contestadas** (si el template nuevo fuera compatible) → nueva rama en `migrate_pending_tasks_type` + quitar el `400` de `only_pending: false`; hoy es deliberadamente imposible.

## Pendientes

- **[back]** Correr el DDL en test/prod antes del deploy del mes 2 (dev ya, 2026-09-07).
- **[front]** Constructor visual (S2–S3): listado por versiones, clonar, editor de template, pestaña avanzada de rúbrica, publicar con checkbox de migrar.
- **[back]** Actualizar la tabla de ciclo de vida de [`quizz_models_crud.md`](quizz_models_crud.md) apunta aquí (hecho: nota al inicio de ese doc).
