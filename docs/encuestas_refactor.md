# Refactor de encuestas — motor de evaluación config-driven

> Primer incremento del refactor de encuestas (ver [`plan_rh_mes.md`](../Docs/plan_rh_mes.md)). Se reemplaza el scoring/interpretación hardcodeado por tipo con un **motor config-driven** que aplica una **rúbrica en datos** (`files/rubrics/<tipo>.json`). El tipo de encuesta deja de vivir en el código. Solo Norma 035 (tipos 1 y 2) está migrado; clima laboral (3) y eva 360 (4) quedan pendientes de su rúbrica (documento en revisión); salida (0) es cualitativa.

## El problema de fondo que se corrige

El scoring viejo (`calculate_results_quizzes`) calculaba **sumas numéricas** pero **nunca aplicaba los umbrales** que ya vivían en `conversions_quizzes.json` (`rangos`/`calificaciones`). Luego `recommendations_results_quizzes` recibía ese entero y hacía `dict["c_final_r"].get(63, default)` contra llaves de texto (`"MUY ALTO"`…) → **nunca hacía match → las recomendaciones siempre caían al default**. La interpretación estaba rota incluso para Norma 035. El motor nuevo hace la clasificación *puntaje → nivel → interpretación* que faltaba.

## Las 4 capas (+ config)

| Capa | Archivo | Cambio |
|---|---|---|
| **Motor** (nuevo) | [`templates/resources/midleware/quizz_eval_engine.py`](../templates/resources/midleware/quizz_eval_engine.py) | Motor puro config-driven: `evaluate(data_raw, rubric)`, `evaluate_task(data_raw, type_q)`, `classify`, `flatten_responses`, `score_items`. Sin `match` por tipo. |
| **Config** (nuevo) | [`files/rubrics/1.json`](../files/rubrics/1.json), [`files/rubrics/2.json`](../files/rubrics/2.json) | Rúbricas Norma 035 v1/v2 en esquema canónico. Migradas por script desde `conversions_quizzes.json` (bandas posicionales → explícitas). |
| **Constantes** | [`static/constants.py`](../static/constants.py) | `+ rubrics_dir_path = "files/rubrics/"`. |
| **Orquestación** | [`templates/resources/midleware/Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) | `generate_pdf_from_json` ahora evalúa con el motor, guarda el resultado uniforme en `data_raw["evaluation"]` y deriva el shape legacy vía `_legacy_shape_from_evaluation` (shim) para que el PDF actual siga funcionando. Nueva `get_quizz_evaluation(id_task, data_token)` evalúa una encuesta por id **on-read** (sin persistir ni generar PDF). `calculate_results_quizzes`/`recommendations_results_quizzes` quedan **deprecadas** (sin callers). |
| **HTTP** | [`templates/resources/rs_RRHH.py`](../templates/resources/rs_RRHH.py) | Nueva ruta `GET /quizz/<int:id_task>/evaluation` (clase `QuizzEvaluation`). `GET /quizzes` y `POST /download/quizz/report` ya exponen `data_raw` (por ende `evaluation`). |

### Fixes incidentales
- **Bug `id=0`**: `RequestFileReportQuizzForm.id` default `0` hacía `update_task(0, …)` (pisaba la fila 0). Ahora solo persiste con `id` válido.
- **Concurrencia del PDF**: se generaba siempre `files/quizz_out/temp_quiz.pdf` (los requests paralelos se pisaban). Ahora nombre único por request (`quiz_report_<uuid>.pdf`).
- **`print()` → `write_log_file`** en el path de generación.
- **`KeyError` en tipos sin generador**: `dict_typer_quizz_generator.get(tipo)` con guard, en vez de indexado directo.

## El esquema de la rúbrica (input, `files/rubrics/<tipo>.json`)

```jsonc
{
  "type": 1, "name": "Norma 035 (<=50) v1", "mode": "scored",
  "scoring": {
    "answer_kind": "option_index",
    "item_maps": [
      { "items": [18,...,33], "values": [0,1,2,3,4], "na_value": 0 },
      { "items": [1,...,46],  "values": [4,3,2,1,0], "na_value": 0 }
    ]
  },
  "bands_total": [ ["nulo",null,20], ["bajo",20,45], ["medio",45,70], ["alto",70,90], ["muy_alto",90,null] ],
  "tree": [ { "id":"c0","kind":"categoria","label":"...","agg":"sum","bands":[...],
             "actions":[...], "children":[ { "kind":"dominio",... "children":[ {"kind":"dimension","items":[2]} ] } ] } ],
  "levels": { "muy_alto": {"label":"Muy alto","actions":[...]}, "nulo": {"label":"Nulo","actions":[...]} }
}
```
Una banda `[key, low, high]` aplica si `(low is None or score >= low) and (high is None or score < high)`. **Ajustar una rúbrica = editar este JSON**, sin tocar código ni redeploy.

---

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)** — `jwt.decode` sobre el header tal cual. Departamento requerido: `rrhh`.
**Base:** `/GUI/api/v1/rrhh`
**Envelope:** JSON `{ "data": ..., "msg": ..., "error": ... }`. Las descargas de archivo devuelven **blob binario en 200/201** y el envelope JSON en 4xx (el front ramifica por status).

### `GET /GUI/api/v1/rrhh/quizzes`
Lista todas las encuestas. Cada item trae `data_raw`, que incluye `evaluation` (shape uniforme) **si ya fue evaluada** (hoy la evaluación se computa al generar el reporte — ver nota abajo).

```jsonc
// 200
{ "data": [ { "id": 123, "body": {...}, "data_raw": { /* respuestas + "evaluation": {...} */ }, "timestamp": "2026-07-27 10:00:00" } ],
  "msg": null, "error": null }
```

### `POST /GUI/api/v1/rrhh/download/quizz/report`
Body: `{ "id": 123, "body": { "metadata": {...} }, "data_raw": {...} }`. Computa la evaluación, la persiste en `data_raw["evaluation"]`, y **devuelve el PDF** (blob) en 201. En error: `{ "data": null, "msg": "Error al generar el pdf", "error": null }`, 400.

### `GET /GUI/api/v1/rrhh/quizz/<int:id_task>/evaluation`
Evalúa una encuesta por su id **on-read** (determinista desde `data_raw` + rúbrica, siempre fresco; no persiste ni genera PDF). **Este es el endpoint que consume la UI de resultados.**

```jsonc
// 200 OK — evaluación calculada
{ "data": { /* shape uniforme, ver abajo */ }, "msg": null, "error": null }

// 200 OK — tipo aún sin rúbrica (clima/eva360 pendientes, o salida)
{ "data": null, "msg": "No hay rubrica para el tipo de encuesta 3 (pendiente de migracion)", "error": null }

// 404 — id no existe
{ "data": null, "msg": "Encuesta 999 no encontrada", "error": null }

// 400 — la tarea no es una encuesta (sin metadata.type_quizz)
{ "data": null, "msg": "La tarea 123 no es una encuesta (sin type_quizz)", "error": null }
```
El front debe **ramificar por `data`**: si `data` es `null`, mostrar el `msg` (aún no evaluable); si trae objeto, renderizar el `breakdown`.

### El shape uniforme `evaluation` (lo que renderiza la UI de resultados)
**Mismo shape para todos los tipos** → un solo componente recursivo sobre `breakdown`:

```jsonc
{
  "type": 1, "mode": "scored",
  "total": {
    "score": 64,
    "level": { "key": "medio", "label": "Medio" },
    "actions": ["Revisión de la política de prevención…", "Promover un entorno organizacional favorable…"]
  },
  "breakdown": [
    { "id": "c1", "kind": "categoria", "label": "Factores propios de la actividad",
      "score": 28, "level": { "key": "medio", "label": "Medio" },
      "actions": ["Definir objetivos y metas…"],          // recomendaciones fijas de la categoría (opcional)
      "children": [
        { "id": "c1_d1", "kind": "dominio", "label": "Falta de control sobre el trabajo",
          "score": 28, "level": { "key": "muy_alto", "label": "Muy alto" },
          "children": [
            { "id": "c1_d1_m0", "kind": "dimension", "label": "Falta de control y autonomía", "score": 12 }
          ] }
      ] }
  ],
  "detail": { "1": 0, "18": 4, "19": 4 }                   // puntaje por ítem (auditoría/PDF)
}
```
Modo cualitativo (salida): `{ "type": 0, "mode": "qualitative", "qualitative": [ { "question": "...", "answer": "..." } ] }` — sin `total`/`breakdown`.

**Gotchas para el front:**
- `level` puede faltar en un nodo si no tiene bandas definidas (dimensiones no clasifican, solo traen `score`). Renderizar defensivamente con `?.`.
- `actions` en un nodo es opcional (solo categorías con recomendaciones fijas).
- `total.actions` son las recomendaciones **por nivel de riesgo** del puntaje final.
- `kind` ∈ `categoria | dominio | dimension` (y a futuro `factor` para clima/eva360). No hardcodear la profundidad: recorrer `children`.

---

## Pendientes
- **Rúbricas de clima laboral (3) y eva 360 (4)** — documento en revisión. El motor ya las soporta por config; eva 360 probablemente requiera `agg:"avg"` + múltiples evaluadores (a confirmar con la rúbrica).
- **Rúbrica de salida (0)** — `mode:"qualitative"`, captura + reporte sin score.
- **Normalizar el shape de respuestas** (`data_raw`) — hoy heterogéneo (`answer` a veces `""`, `0`, `[label,idx]`); `flatten_responses` es el puente. Fijar el contrato de la UI de captura lo simplifica.
- **Rediseño del PDF** para leer `evaluation` directo y quitar el shim `_legacy_shape_from_evaluation` (aplicar skill `pdf-design`).
- **Borrar** `calculate_results_quizzes`/`recommendations_results_quizzes` (deprecadas, sin callers).
