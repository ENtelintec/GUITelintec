# Encuesta de salida (tipo 0) — rúbrica cualitativa y respuestas resueltas a texto

> Arrastre del mes 1 cerrado en S1 del [`plan_mes_2.md`](plan_mes_2.md) (2026-09-07). Era el único tipo del seed sin rúbrica: `GET /quizz/<id>/evaluation` respondía `data: null` ("no hay rúbrica") y la UI de resultados no tenía nada que pintar. El motor ya soportaba `mode: "qualitative"` ([`encuestas_refactor.md`](encuestas_refactor.md)); faltaba **la rúbrica del tipo 0** y que la salida cualitativa fuera legible: el `data_raw` guarda índices (`answer: 1`, `[[0, 1], ...]`), no etiquetas.

## Qué cambió

| Capa | Archivo | Cambio |
|---|---|---|
| **Motor** | [`quizz_eval_engine.py`](../templates/resources/midleware/quizz_eval_engine.py) | `_evaluate_qualitative` resuelve cada respuesta a **texto** con las `options`/`subquestions` que la captura embebe en la propia sección (`_resolve_answer_text`, nuevo): widget `1` → etiquetas separadas por coma, `2` → etiqueta, `3` (matriz) → `"subpregunta: etiqueta; ..."` + `details`, `5` → el texto. Ordena por llave numérica y salta llaves auxiliares sin `question` (`evaluation`/`results`). Índices fuera de rango no truenan (imprime el crudo). |
| **Datos** | [`files/rubrics/0.json`](../files/rubrics/0.json) (nuevo, fuente del seed) · [`seed_quizz_models.py`](../scripts_db_handle/seed_quizz_models.py) (tipo 0 ahora con rúbrica) · [`salida_rubrica_tipo0.sql`](../scripts_db_handle/salida_rubrica_tipo0.sql) (DML para test/prod, idempotente) | Rúbrica mínima `{"type": 0, "mode": "qualitative", ...}`. **En dev ya aplicada** vía `update_quizz_model_api` (pasa `validate_rubric` + dry-run). |
| **PDF / CRUD** | — | Sin cambios: el tipo 0 conserva su generador dedicado `QuizzSalidaPDF` (la evaluación cualitativa cae en la rama de defaults de `generate_pdf_from_json`), y el genérico `QuizzGenericReport` ya pintaba `question`/`answer` (ahora legibles). |

## Contrato mínimo para el front

- `GET /GUI/api/v1/rrhh/quizz/<id_task>/evaluation` (permiso `rrhh`, `Authorization` con el JWT crudo). Para el tipo 0 ahora responde `200` con `data`:
```json
{"type": 0, "mode": "qualitative",
 "qualitative": [
   {"key": "0", "question": "Q1. Cuales son sus motivos para dejar su empleo actual?...", "type": 1, "answer": "Cambio de Residencia, Mejor sueldo", "answer_raw": [10, 4]},
   {"key": "1", "question": "Q2. Cuanto tiempo lleva pensando en dejar su empleo actual?", "type": 2, "answer": "Un mes o menos", "answer_raw": 0},
   {"key": "2", "question": "Q3. Cuál es su grado de satisfacción...", "type": 3, "answer": "Salario: Satisfecho; Formación: Satisfecho; ...", "answer_raw": [[0, 1], [1, 1]],
    "details": [{"subquestion": "Salario", "answer": "Satisfecho"}, {"subquestion": "Formación", "answer": "Satisfecho"}]},
   {"key": "9", "question": "Q10. ¿Tiene alguna observación...?", "type": 5, "answer": "", "answer_raw": ""}
 ]}
```
- Ramificar por `mode`: `"qualitative"` no trae `total` ni `breakdown`. Render: tabla pregunta/respuesta usando `answer` (ya texto); `details` solo existe en matrices (`type: 3`) para pintarlas como sub-tabla; `answer_raw` es el crudo por si la UI quiere resaltar la opción elegida. Encuesta sin contestar → `qualitative: []` (mostrar "sin respuestas").
- `POST /download/quizz/report` para tipo 0: sin cambio (PDF dedicado, `201` blob / envelope 4xx).
- Test/prod: correr [`salida_rubrica_tipo0.sql`](../scripts_db_handle/salida_rubrica_tipo0.sql) (o `PUT /quizz/models/0` con la rúbrica) antes de integrar; hasta entonces siguen respondiendo `data: null`.

## Verificación

Dev (2026-09-07): rúbrica aplicada por API; `get_quizz_evaluation` de las 2 tasks contestadas de salida devuelve 10 entradas con etiquetas resueltas (multiselección, opción única, 3 matrices con `details`, texto), task vacía → `[]`; PDF dedicado sigue generándose (`201`).

## Pendientes

- **[front]** Pintar el modo cualitativo en la UI de resultados (hoy la UI ramifica por `data: null`).
- **[back]** Correr el DML en test/prod.
