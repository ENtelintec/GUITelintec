# Eva 360 — proceso multi-evaluador sobre `tasks_gui`

> **Actualización 2026-08-07**: la tabla `tasks_gui` ahora es `sql_telintec_mod_rrhh.quizz_tasks` y las rutas `/misc/task/*` y `/misc/download/quizz/*` se movieron a `/rrhh/...` en corte duro — los shapes de este doc siguen válidos, solo cambia el prefijo. Ver [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md) y [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md).

> Segundo incremento del refactor de encuestas (ver [`encuestas_refactor.md`](../Docs/encuestas_refactor.md)). Eva 360 rompe el modelo "una task = una encuesta = una persona": es **una evaluación de una persona compuesta por N cuestionarios idénticos (2-4) que llenan evaluadores distintos** (self | superior | peer | subordinate), más una **task de control** para RH. Todo sobre `tasks_gui` (sin esquema nuevo), ligado por `metadata.evaluation_id` (UUID generado por el back). Puramente numérico: 9 competencias × 1-5 = 45 máx → escalado a 100; **sin niveles/semáforo** (a diferencia de Norma 035).

## Modelo

```
Proceso eva 360 (evaluation_id = UUID)
├── task CONTROL  → emp_destiny = RH (creador). metadata: eva360_kind:"control",
│                   evaluated_emp_id, name_emp, expected_roles:[...], status_eval:"open|complete"
└── N tasks EVALUADOR (una por rol) → emp_destiny = evaluador. metadata: eva360_role,
                    evaluated_emp_id, name_emp, evaluation_id. El rol self → emp = evaluado.
```

- Título control: `"eva360 control"` (sin "quizz" → **no aparece** en `GET /quizzes`); título evaluador: `"quizz eva360 <rol>"` (sí aparece, y en la lista de tasks del evaluador `GET /misc/task/<emp_id>`).
- Cada evaluador **llena su task por el CRUD existente** (`PUT /misc/task/quizz`) — no hay endpoint de captura nuevo.
- Una perspectiva cuenta como **respondida solo si las 9 competencias tienen respuesta** (un parcial bajaría el score escalado). El **promedio general va sobre las respondidas** (no sobre 4 fijo); se exponen `assigned` vs `answered`.
- Agregación: por perspectiva `suma(9 ítems)→÷45×100`; general = media de los `score_100` respondidos (peso igual, la auto cuenta como una más); por competencia: crudos 1-5 `by_role` + `average` + `distribution` (frecuencia de cada valor 1..5 entre los evaluadores).

## Capas tocadas

| Capa | Archivo | Cambio |
|---|---|---|
| Motor | [`quizz_eval_engine.py`](../templates/resources/midleware/quizz_eval_engine.py) | `flatten_per_question` (layout `per_question`: la llave del JSON es el nº de ítem, `answer` escalar), `scale` (`{max,to}` → `total.scaled`), y el agregador **`evaluate_eva360(perspectives, ...)`** |
| Config | [`files/rubrics/4.json`](../files/rubrics/4.json) | Rúbrica de la perspectiva individual: 9 competencias (ítems 4-12), `values:[5,4,3,2,1]` (índice 0 = "5 &#124;"), `scale:{max:45,to:100}`, sin bandas |
| Template | [`files/quizz_eva_360.json`](../files/quizz_eva_360.json) | **Fix: pregunta 12 duplicada eliminada** ("Manejo de su Equipo de Trabajo" estaba 2×; con ella el máx daba 50, no 45) y **renumerada** 13→12 (llaves contiguas 0..12 — `Eva360.py` itera `range(len)` sin guard y habría tronado). Corte duro: eva 360 nunca fue funcional, no hay tasks en vuelo |
| Controller | [`tasks_controller.py`](../templates/controllers/misc/tasks_controller.py) | `get_tasks_by_eva360_group(evaluation_id)` — `WHERE body->>'$.metadata.evaluation_id' = %s` |
| Midleware | [`MD_Eva360.py`](../templates/resources/midleware/MD_Eva360.py) (**nuevo**) | `create_eva360_process` (valida roles, genera UUID, crea control + N raters, notifica a cada evaluador), `get_eva360_process`, `get_eva360_result`, `complete_eva360_process` |
| Modelos | [`api_models.py`](../static/Models/api_models.py) | `Eva360CreateForm`/`Eva360RaterForm` + `eva360_create_model`/`eva360_rater_model`; **`MetadataTasksForm` y `metadata_task_model` ganan** `evaluation_id`, `eva360_role`, `eva360_kind`, `status_eval`, `expected_roles` — **crítico**: sin declararlos, el `PUT /misc/task/quizz` (que valida metadata con ese form) **borraría el linking** al primer guardado de respuestas (verificado que sobreviven) |
| HTTP | [`rs_RRHH.py`](../templates/resources/rs_RRHH.py) | 4 rutas nuevas bajo `/GUI/api/v1/rrhh`: `POST /eva360`, `GET /eva360/<evaluation_id>`, `GET /eva360/<evaluation_id>/result`, `PUT /eva360/<evaluation_id>/complete` |

---

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)**. Departamento: `rrhh`.
**Base:** `/GUI/api/v1/rrhh` · **Envelope:** `{data, msg, error}`.

### `POST /eva360` — crear el proceso (RH)
```jsonc
// request
{ "evaluated_emp": 101, "evaluated_name": "Juan Perez", "date_limit": "2026-08-31",
  "raters": [ { "role": "self" },                       // emp_id se toma del evaluado
              { "role": "superior", "emp_id": 7 },
              { "role": "peer", "emp_id": 8 },
              { "role": "subordinate", "emp_id": 3 } ] }
// 201
{ "data": { "evaluation_id": "634903fa…", "id_control": 501,
            "raters": [ {"role":"self","emp_id":101,"id_task":502}, … ] },
  "msg": "Proceso eva 360 creado (…) con 4 evaluadores", "error": null }
// 400 — validación: rol inválido/duplicado, falta emp_id, sin raters (msg lo dice); o
//        creación parcial: data trae lo creado y error es LISTA de fallos por rol
```
Roles válidos: `self | superior | peer | subordinate`, **uno por rol** (2-4). El back genera `evaluation_id` y arma todo el linking — **el front nunca escribe metadata de eva 360**.

### Llenado (cada evaluador) — flujo existente, sin API nueva
El evaluador ve su task (`GET /misc/task/<emp_id>`, título `"quizz eva360 <rol>"`), el front carga el template (`GET /misc/download/quizz/4`) y guarda respuestas con `PUT /misc/task/quizz`. **Shape de respuestas** (per-question): `data_raw = { "4": {"answer": <índice 0-4>}, …, "12": {"answer": …} }` — índice 0 = la opción "5 | …" (mejor), índice 4 = "1 | …" (peor). Al re-mandar `body`, **conservar `metadata` tal cual llegó** (trae el linking).

### `GET /eva360/<evaluation_id>` — detalle para RH
```jsonc
// 200
{ "data": { "evaluation_id": "…", "id_control": 501, "evaluated_emp": 101,
            "evaluated_name": "Juan Perez", "expected_roles": ["self","superior","peer","subordinate"],
            "status_eval": "open",
            "raters": [ { "id_task": 502, "role": "self", "emp_destiny": 101, "answered": true }, … ] },
  "msg": null, "error": null }
```
`answered` = las 9 competencias contestadas (un parcial cuenta como `false`).

### `GET /eva360/<evaluation_id>/result` — el agregado (UI de resultados)
```jsonc
// 200
{ "data": {
    "type": 4, "evaluation_id": "…", "evaluated_emp": 101, "evaluated_name": "Juan Perez",
    "status_eval": "open",
    "assigned": 4, "answered": 3,                       // "3 de 4 respondidas"
    "general": { "score_100": 80.0 },                   // media de las respondidas; null si 0 respondidas
    "by_perspective": { "self":     { "score_100": 100.0, "raw_total": 45 },
                        "superior": { "score_100": 80.0,  "raw_total": 36 },
                        "peer":     { "score_100": 60.0,  "raw_total": 27 } },   // solo respondidas
    "competencies": [
      { "id": "q4", "label": "Organizacion",
        "by_role": { "self": 5, "superior": 4, "peer": 3 },   // crudos 1-5, solo respondidas
        "average": 4.0,
        "distribution": { "1": 0, "2": 0, "3": 1, "4": 1, "5": 1 } },            // frecuencias
      /* … 9 competencias … */ ] },
  "msg": null, "error": null }
// 404 proceso inexistente · 400 sin rúbrica
```
**Gotchas:** un rol pendiente **no aparece** en `by_perspective` ni en `by_role` (no viene con `null` — ausencia = pendiente; cruzar contra `expected_roles` del detalle); `general.score_100` es `null` con 0 respondidas; el radar/barras comparativas los dibuja el front desde `competencies`.

### `PUT /eva360/<evaluation_id>/complete` — RH cierra el proceso
Sin body. Idempotente. `200 → { "data": {"evaluation_id":"…","status_eval":"complete"}, "msg": "…", "error": null }`. Solo marca `status_eval` (señal de que el reporte es definitivo aunque falte alguna perspectiva); **no bloquea** el llenado ni recalcula nada.

---

## Verificación
Sin framework de tests (gitignored): validado offline con el motor real y el midleware con controller monkeypatcheado — escalado (45→100/36→80/27→60), general 3-de-4 = 80.0, `by_role`/`distribution` exactos, validaciones del create (rol inválido/duplicado/sin emp_id), linking sobrevive el `TaskUpdateForm` del PUT, rutas registradas, pyrefly limpio en las 4 capas.

## Pendientes
- ~~**Clima laboral (tipo 3)**~~ — hecho: rúbrica % positivo + agregado organizacional en [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md).
- **Salida (tipo 0)** — rúbrica cualitativa (`mode:"qualitative"`).
- **PDF de eva 360** — `Eva360.py` sigue imprimiendo el cuestionario individual; falta un reporte del proceso agregado (radar/tabla comparativa, skill `pdf-design`).
- El fix de la Q12 duplicada asume corte duro; si apareciera una task eva 360 vieja con 14 preguntas, su `data_raw` tendría la Comunicación en la llave 13 (la rúbrica la leería en 12) — no hay tasks así en dev/prod.
