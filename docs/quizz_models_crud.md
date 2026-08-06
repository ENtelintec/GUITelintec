# CRUD de modelos de encuesta (template + rúbrica) — `/rrhh/quizz/models`

> Segundo incremento del refactor de encuestas ([`encuestas_refactor.md`](encuestas_refactor.md)). RH ahora puede **crear, editar y retirar encuestas por API** sin tocar código ni redeploy: el modelo de encuesta (el par **template** = cuestionario que el front renderiza + **rúbrica** = config del motor de evaluación) deja los archivos del repo y pasa a la BD, en el **esquema nuevo `sql_telintec_mod_rrhh`** — primer paso hacia la estructura de un esquema por departamento. Verificado ciclo completo contra BD dev (26 checks) + PDFs renderizados.

## Qué cambia

- **Store**: tabla `sql_telintec_mod_rrhh.quizz_models` (`type_q` PK AUTO_INCREMENT, `name`, `template` JSON, `rubric` JSON nullable, `status`, `protected`, `created_by`, `timestamp`, `updated_at`, `history`). DDL a mano en [`scripts_db_handle/quizz_models.sql`](../scripts_db_handle/quizz_models.sql) (incluye el `CREATE SCHEMA` y el recordatorio de `GRANT`); seed de los 5 tipos históricos con [`scripts_db_handle/seed_quizz_models.py`](../scripts_db_handle/seed_quizz_models.py) (idempotente, `--dry`; el tipo `0` se inserta con id auto y se reasigna vía `UPDATE` porque un `0` explícito en AUTO_INCREMENT significa "asigna el siguiente" salvo `NO_AUTO_VALUE_ON_ZERO`, y `execute_sql` abre conexión por llamada). Los `files/quizz_*.json` y `files/rubrics/*.json` quedan como fuente del seed, **no se leen en runtime**.
- **Ciclo de vida** (`status`): `0 BORRADOR` → `1 ACTIVA` → `2 ARCHIVADA`, transiciones `0→1` (publicar, re-valida template), `1→2`, `2→1` vía `PUT /status`. Ver reglas abajo.
- **Corte duro de los read paths**: `load_rubric`/`evaluate_task` del motor ahora leen la columna `rubric` de la BD (firma nueva con `data_token` para el switching a BD de test; threading por `get_quizz_evaluation`, `get_quizz_group_evaluation`, `generate_pdf_from_json` y los 2 call sites de `MD_Eva360`). `GET /misc/download/quizz/<type_q>` conserva ruta y shape pero sirve el template desde BD. `create_task_from_api` toma template+status de BD y **rechaza con 400 los tipos no ACTIVOS o inexistentes** (antes un tipo desconocido daba `KeyError` → 500).
- **Retirados**: `quizzes_RRHH` y `quizzes_dir_path`/`rubrics_dir_path` de `static/constants.py` (los tres registros paralelos del mismo catálogo), y la función muerta `extract_data_encuesta` de `Functions_Files.py` (sin callers).
- **Validación al guardar** (tres capas): template **dura** (dict de entradas numéricas con `question` str, `type` del catálogo de widgets, `options`/`subquestions` listas, `items` par `[desde,hasta]`); rúbrica **dura** = `validate_rubric` estructural nueva en el motor (modos, `item_maps`, bandas `[key,low,high]` cuya key exista en `levels`, árbol recursivo, `scale`, `total_agg`) + **dry-run** (`dry_run_rubric`: respuestas sintéticas desde los `item_maps` —cada ítem contesta la primera opción con valor no-null— → `evaluate()` debe producir `total`/`breakdown` y puntuar algo); consistencia template↔rúbrica **solo advertencias** (`warnings` en la respuesta, no bloquean: ítem máximo vs preguntas estimadas, ítems sin llave en layout `per_question`, matrices con `per_question`).
- **PDF genérico de resumen** ([`templates/forms/QuizzGenericReport.py`](../templates/forms/QuizzGenericReport.py), formato `pdf-design`): fallback de `POST /rrhh/download/quizz/report` para cualquier tipo **sin** generador dedicado en `dict_typer_quizz_generator` — renderiza el shape uniforme (`total` + `breakdown` recursivo con sangría + recomendaciones; modo cualitativo = tabla Pregunta|Respuesta). Los tipos 0–4 conservan sus PDFs actuales. Sin generador **y** sin rúbrica → 400 con mensaje claro.

**Hallazgo importante**: `create_task` **descarta** el template (`data_raw` nace `{}` y el body no lo embebe) — no existe snapshot por task. La captura y la evaluación siempre mapean contra el template **vivo**, y por eso el candado de template en ACTIVA no es cosmético: es la única protección del historial.

## Las 4 capas (+ config)

| Capa | Archivo | Cambio |
|---|---|---|
| **DDL/seed** | [`scripts_db_handle/quizz_models.sql`](../scripts_db_handle/quizz_models.sql), [`seed_quizz_models.py`](../scripts_db_handle/seed_quizz_models.py) | Esquema + tabla nuevos; seed 0–4 (`status=1`; Norma 035 con `protected=1`; salida sin rúbrica). |
| **Controller** (nuevo) | [`templates/controllers/rrhh/quizz_models_controller.py`](../templates/controllers/rrhh/quizz_models_controller.py) | CRUD SQL: listado ligero (sin JSONs pesados), detalle, rubric-only/template-only para el motor y la captura, `UPDATE` parcial con whitelist, `count_tasks_by_type_quizz` (total + contestadas vía `body->>'$.metadata.type_quizz'`). |
| **Motor** | [`templates/resources/midleware/quizz_eval_engine.py`](../templates/resources/midleware/quizz_eval_engine.py) | `load_rubric(type_q, data_token)`/`evaluate_task(..., data_token)` leen BD; nuevas `validate_rubric` y `dry_run_rubric`. |
| **Orquestación** (nuevo) | [`templates/resources/midleware/MD_QuizzModels.py`](../templates/resources/midleware/MD_QuizzModels.py) | Ciclo de vida completo, candados, validaciones, warnings, history, catálogos; `get_quizz_template_api` (compat de misc). |
| **Modelos** (nuevo) | [`static/Models/api_quizz_models_models.py`](../static/Models/api_quizz_models_models.py) | `api.model` + WTForms. `template`/`rubric` NO pasan por el form (WTForms no modela dicts): el midleware los toma del `ns.payload` crudo y los valida él. |
| **HTTP** | [`templates/resources/rs_RRHH.py`](../templates/resources/rs_RRHH.py), [`rs_Misc.py`](../templates/resources/rs_Misc.py), [`Functions_DB_midleware.py`](../templates/resources/midleware/Functions_DB_midleware.py) | 6 rutas nuevas en `rrhh`; download de misc a BD; `create_task_from_api` valida modelo ACTIVO. |
| **PDF** (nuevo) | [`templates/forms/QuizzGenericReport.py`](../templates/forms/QuizzGenericReport.py) | Reporte genérico del shape uniforme (helpers `_qz_*` propios). |

## Reglas del ciclo de vida

| Status | ¿Se contesta? | template | rubric / name | DELETE físico |
|---|---|---|---|---|
| `0` BORRADOR | **No** (`create_task` → 400) | editable | editables (rubric se puede quitar con `null`) | libre |
| `1` ACTIVA | Sí | **bloqueado** (cambiar preguntas = modelo nuevo) | editables (quitar rubric → 400) | solo sin tasks |
| `2` ARCHIVADA | No | bloqueado | editables | solo sin tasks |

- Editar la rúbrica de un tipo con historial **re-interpreta retroactivamente** sus resultados (la evaluación es on-read) — es deliberado: corregir una banda mal calibrada corrige los resultados. "Versión nueva con otras preguntas" = crear modelo nuevo y archivar el viejo (mismo precedente que Norma 035 v1/v2).
- `protected=1` (Norma 035, tipos 1 y 2): **jamás** borrable; editable y archivable como cualquiera.
- DELETE físico exige: no protected **y** 0 tasks del tipo en `tasks_gui` (cualquier task, contestada o no — sin el modelo su historial dejaría de evaluarse). Con tasks → 400 sugiriendo archivar.
- Cada cambio queda en `history` (`[{user, action, date, comment}]`); `updated_at` lo mantiene MySQL.

---

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)**. Departamento: `rrhh`.
**Base:** `/GUI/api/v1/rrhh` (salvo el download de captura, que sigue en `/GUI/api/v1/misc`).
**Envelope:** `{ "data": ..., "msg": ..., "error": ... }` en todos los endpoints de este doc.

### `GET /rrhh/quizz/models` — listado (el picker y la pantalla de administración)
Query params: sin params → **solo ACTIVAS** (úsalo para el picker de "crear encuesta", reemplaza los 5 tipos hardcodeados); `?all=1` → todos los status (pantalla de administración); `?status=N` → ese status.
Listado **ligero** (sin template/rúbrica; pedir el detalle para eso):

```jsonc
// 200
{ "data": [
    { "type_q": 3, "name": "Encuesta de clima laboral", "status": 1, "status_label": "ACTIVA",
      "protected": 0, "created_by": 34, "timestamp": "2026-08-05T13:00:00", "updated_at": null,
      "has_rubric": true, "n_entries": 1 }
  ], "msg": "5 modelos", "error": null }
```

### `GET /rrhh/quizz/models/catalogs`
`status`, `widget_types` (catálogo del campo `type` de cada entrada del template — lo que la UI de captura debe saber renderizar), `response_layouts`, `transitions` y `rules` (texto de las reglas del ciclo de vida). Formato `{code, label}`.

### `GET /rrhh/quizz/models/<type_q>` — detalle
Todo: `template`, `rubric` (puede ser `null`), `history`, `status`/`status_label`, `protected`, y los conteos `tasks_total` / `tasks_answered` / `has_answered_tasks` (para que la UI muestre por qué el template está bloqueado o si el DELETE va a rechazarse). `404` si no existe.

### `POST /rrhh/quizz/models` — crear (nace en BORRADOR)
```jsonc
// body
{ "name": "Encuesta de seguridad 2026",
  "template": { "0": { "question": "Sección A", "subquestions": ["p1","p2"],
                        "options": ["Siempre","Nunca"], "answer": "", "type": 3 } },
  "rubric": { /* opcional; esquema en encuestas_refactor.md */ } }

// 201 — warnings = consistencia template↔rúbrica (NO bloquean, mostrarlas)
{ "data": { "type_q": 6, "status": 0, "warnings": [] },
  "msg": "Modelo de encuesta creado en borrador (tipo 6: Encuesta de seguridad 2026)", "error": null }

// 400 — template o rúbrica inválidos (error = lista de strings por campo)
{ "data": null, "msg": "Rúbrica inválida",
  "error": ["bands_total[0]: la key 'inexistente' no existe en levels"] }
```
El `type_q` lo asigna el back (AUTO_INCREMENT, ≥ 5) y **sella `rubric.type`** él mismo — el front no manda `type` en la rúbrica. Un modelo recién creado **no aparece** en el picker hasta publicarlo.

### `PUT /rrhh/quizz/models/<type_q>` — edición **parcial**
Solo se escriben las llaves presentes en el JSON (`name`, `template`, `rubric`). Respuesta `200` con `{type_q, warnings}`. Errores 400 que la UI debe manejar: template con el modelo publicado (mensaje explica crear modelo nuevo); `"rubric": null` fuera de borrador; `"status"` en este PUT (usar `/status`); body sin ninguna de las 3 llaves.

### `PUT /rrhh/quizz/models/<type_q>/status` — ciclo de vida
Body `{"status": N}`. Transiciones válidas: `0→1` (publicar; re-valida el template), `1→2` (archivar), `2→1` (reactivar). Mismo status → `200` idempotente. Otra transición → `400` con las opciones válidas en `msg`.

### `DELETE /rrhh/quizz/models/<type_q>`
Sin body. `200` con `{type_q}`; `400` si es protected o tiene tasks (el `msg` trae el conteo y sugiere archivar); `404` si no existe. El "borrar" cotidiano de la UI debería ser **archivar**.

### `GET /misc/download/quizz/<type_q>` — captura (SIN cambios de contrato)
Misma ruta y shape de siempre (`{"data": <template>, ...}`), ahora desde BD. Sirve cualquier status (para previsualizar borradores); la disponibilidad real la controla el alta de tasks: **crear una encuesta de un tipo no ACTIVO → 400** con `msg` claro (caso nuevo que la UI de asignación debe mostrar).

### Catálogo de widgets del template (campo `type` de cada entrada)

| `type` | Render | Produce en `data_raw` |
|---|---|---|
| `1` | Selección múltiple (checkbox) | lista de índices/opciones |
| `2` | Opción única (radio) | índice de opción |
| `3` | Matriz: misma escala `options` para cada `subquestion` | lista `answer` posicional (layout secciones) |
| `5` | Texto abierto | string |

Entrada del template: `{ "question": str, "subquestions": [str], "options": [str], "answer": "" , "type": int }`, llaves del dict numéricas (`"0"`, `"1"`, …). Opcional `items: [desde, hasta]` para ligar la sección a los números de ítem de la rúbrica (layout Norma 035). La rúbrica declara cómo leer las respuestas en `scoring.response_layout`: `sections` (default) o `per_question` — debe corresponder al layout del template (si no, llega warning).

**Gotchas:**
- `warnings` en POST/PUT son avisos de consistencia — mostrar al usuario, el guardado ya ocurrió.
- La rúbrica es opcional al crear: sin ella el tipo se captura pero `GET /quizz/<id>/evaluation` responde `data: null` con `msg` "no hay rúbrica…". Agregar la rúbrica después la vuelve evaluable **incluyendo lo ya contestado** (on-read).
- El shape del `evaluation` que consume la UI de resultados no cambió (ver [`encuestas_refactor.md`](encuestas_refactor.md)); un tipo nuevo con rúbrica funciona en `GET /quizz/<id>/evaluation` y en el PDF (`POST /download/quizz/report` ahora devuelve el **PDF genérico de resumen** para tipos sin PDF dedicado). `GET /quizzes/summary/<type_q>` es config-driven y *debería* servir para tipos nuevos con rúbrica estilo clima, pero no está contractualmente garantizado — probar por tipo.

---

## Al modificar

- **Columna nueva en la tabla** → DDL + `SELECT_COLUMNS`/`LIST_COLUMNS` del controller (los dicts se mapean por posición con esas tuplas) + `_row_to_detail`/`_row_to_list_item` + este doc.
- **Widget nuevo** → `QM_WIDGET_TYPES` en `MD_QuizzModels.py` (la validación dura del template rechaza `type`s fuera del catálogo) + render en el front + fila en la tabla de arriba.
- **Transición nueva del ciclo de vida** → `QM_TRANSITIONS` (par `(desde, hasta) → etiqueta de history`); las reglas de candado viven en `update_quizz_model_api` (template/rubric) y `create_task_from_api` (contestabilidad).
- **Regla nueva de rúbrica en el motor** → reflejarla en `validate_rubric` (y si aplica en `dry_run_rubric`), o las rúbricas inválidas volverán a llegar a la BD.
- El seed **no se re-corre** en operación normal (es idempotente si hiciera falta); los archivos de `files/` ya no son fuente de verdad — un cambio de rúbrica de producción se hace por API (o SQL directo), no editando el JSON del repo.

## Pendientes

- **[front] Pantalla de administración de modelos** (listado `?all=1`, editor de template/rúbrica JSON, publicar/archivar, warnings).
- **[back] PDFs dedicados por encuesta** cuando RH pida un formato específico (el genérico cubre el resumen; el rediseño de Norma 035 sobre `evaluation` sigue pendiente en [`encuestas_refactor.md`](encuestas_refactor.md)).
- **[back] Editor amigable de rúbricas** (hoy la rúbrica se captura como JSON crudo; si RH la usa seguido, un builder con validación en vivo).
- **[back] Verificar `GET /quizzes/summary/<type_q>`** con el primer tipo nuevo real que lo necesite (hoy solo garantizado para clima).
