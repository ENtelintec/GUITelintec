# PDF de Norma 035 desde `evaluation` y fin del shim (`P-016`)

> 2026-10-27. Decisiones del grill del mismo día → [`plan_back_sin_bloqueo_2026_10_27.md`](planes/plan_back_sin_bloqueo_2026_10_27.md). Sin DDL. Mismo endpoint (`POST /rrhh/download/quizz/report`); cambia el PDF que devuelve y lo que se guarda en la encuesta.

Hasta hoy, todos los PDFs de encuestas leían un shape viejo (`results`/`recommendations`). Lo armaba `_legacy_shape_from_evaluation` a partir del resultado del motor (ver [`encuestas_refactor.md`](encuestas_refactor.md)). El PDF de Norma 035 tenía estos defectos:
- cuerpo en Times;
- la fecha impresa donde iba el entrevistador;
- una etiqueta en inglés ("Your final result is:");
- dicts impresos como texto de Python;
- siempre las acciones de la primera categoría.

## Qué cambió

- **Norma 035 (tipos 1 y 2): PDF nuevo dedicado** ([`QuizzNorm35.py`](../templates/forms/QuizzNorm35.py), `FileNorma035PDF`), que lee `evaluation` directo. Formato de la casa (cuadrícula celeste, Helvetica, FO-GRH-08, pie con página y folio):
  1. **Datos:** trabajador, puesto, fecha de aplicación, entrevistador, fecha de ingreso y encuesta.
  2. **Resultado general:**
     - calificación final y nivel de riesgo;
     - "Necesidad de acción": el `action_summary` del nivel en la rúbrica;
     - las acciones del nivel.
  3. **Desglose** categoría → dominio → dimensión, con puntaje y nivel:
     - la categoría va en celeste y el dominio en negritas;
     - la dimensión va con sangría y sin nivel, porque la rúbrica no le da bandas.
  4. **Acciones por categoría según su nivel:**
     - en **medio, alto o muy alto**, la lista de acciones propia de la categoría;
     - en **nulo o bajo**, la "necesidad de acción" del nivel (p. ej. "El riesgo resulta despreciable…").
     - Antes salían siempre las acciones de la primera categoría.
  5. **Anexo, en hoja aparte:** las respuestas como evidencia, en tabla Pregunta | Respuesta (la sección y una fila por subpregunta, con la opción en texto). Sustituye la matriz de X/O de 5 a 7 páginas.
- **Salida (0), clima (3) y la perspectiva individual de eva 360 (4) pasan al PDF genérico** ([`QuizzGenericReport.py`](../templates/forms/QuizzGenericReport.py)), que ya leía `evaluation`:
  - salida, como tabla Pregunta | Respuesta;
  - clima y eva 360, con resultado y desglose.
  - El genérico gana "Fecha de ingreso" y "Fecha de baja" en los datos. Un `"None"` guardado por el front no se imprime.
- **`results` y `recommendations` ya no se escriben** en el `data_raw` de la encuesta; solo `evaluation`, como antes. Las encuestas que ya los tienen se quedan así, sin DML. El front no los lee (revisado en `telintec_webapp` el 2026-10-27).
- **Tipo sin rúbrica → 400** `"No hay rubrica para el tipo de encuesta <tipo>"`. Antes, un tipo con generador propio sin rúbrica sacaba un PDF con ceros; hoy los tipos 0–4 tienen rúbrica en BD.

**Se borró:**
- `_legacy_shape_from_evaluation` y sus valores por defecto;
- `static/FramesClasses.py` (`dict_typer_quizz_generator`);
- los generadores `QuizzNor035_v1`/`QuizzNor035_50Plus`, `ClimaLaboral.py`, `Eva360.py` y `QuizzSalida.py`;
- en `PDFGenerator.py`: `display_result`, `display_recommendations`, `create_datos_personales` y `draw_option`. `wrap_text` se queda porque lo usa `BarCodeGenerator`.
- `create_report_encuesta` y `Norm35Formatter` de `Functions_Files.py`: el Excel `report_norm35.xlsx`, que nadie llamaba y leía un `c_dim` que el shim nunca producía.

## Capas tocadas

| Capa | Archivo | Cambio |
|---|---|---|
| Motor | [`quizz_eval_engine.py`](../templates/resources/midleware/quizz_eval_engine.py) | `answered_sections(data_raw)` pública (preguntas con la respuesta en texto); `_evaluate_qualitative` la usa |
| Midleware | [`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) | `generate_pdf_from_json` reescrito: rúbrica → `evaluate` → persiste `evaluation` (solo con id) → Norma 035 dedicado o genérico; sin shim |
| PDF | [`QuizzNorm35.py`](../templates/forms/QuizzNorm35.py) | `FileNorma035PDF(dict_data)` con helpers `_n35_*` (reemplaza a los dos generadores viejos) |
| PDF | [`QuizzGenericReport.py`](../templates/forms/QuizzGenericReport.py) | solo el docstring: ahora es el PDF de todo lo que no es Norma 035 |
| PDF / misc | [`PDFGenerator.py`](../templates/forms/PDFGenerator.py), [`Functions_Files.py`](../templates/misc/Functions_Files.py) | borrado lo que solo usaban los generadores viejos y el Excel |

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)**. Departamento `rrhh`.
**Base:** `/GUI/api/v1/rrhh`.

### `POST /download/quizz/report`: sin cambio de request

```jsonc
{ "id": 123,                       // id real de la encuesta (obligatorio, distinto de 0): ahí se guarda `evaluation`
  "body": { "title": "...", "emp_destiny": 34, "emp_origin": 7, "date_limit": "2026-10-31",
            "metadata": { "type_quizz": 1, "name_emp": "...", "position": "...", "date": "2026-10-20",
                          "interviewer": "...", "admision": "2022-11-01", "departure": "" } },
  "data_raw": "{...respuestas como JSON string...}" }
```

| Status | Content-Type | Cuerpo |
|---|---|---|
| **200** | `application/pdf` | blob adjunto (`quiz_report_<uuid>.pdf`). [`encuestas_refactor.md`](encuestas_refactor.md) decía 201; la ruta responde 200 con `send_file` |
| **400** | JSON | `{"data": null, "msg": "No hay rubrica para el tipo de encuesta 9", "error": null}` · `{"data": null, "msg": "Error al generar el pdf", "error": null}` · validación: `{"data": null, "msg": "Estructura de datos inválida", "error": {...por campo...}}` |
| **401** | JSON | `{"error": "No autorizado. Token invalido"}` |

**Gotchas:**
- Pedirlo con `responseType: "blob"` y decidir por status.
- `metadata.departure` vacío va como `""`: `"None"` no pasa la validación de fecha.
- Después del 200, el `data_raw` guardado trae `evaluation`, y ya no `results` ni `recommendations` (las encuestas viejas pueden traerlos todavía). La UI de resultados sigue en `GET /quizz/<id_task>/evaluation`.
- Norma 035 sale de 4 a 6 hojas: el resultado y el desglose arriba, el anexo de respuestas al final.

## Verificación

`Tests/tester_quizz_pdf.py` (gitignored), por la ruta con `app.test_client()`, contra la BD dev: **16/16**. Datos usados:
- la Norma 035 contestada real de la BD de test (task 24, solo lectura);
- la encuesta de salida real de dev (task 20);
- v2, clima y eva 360 sintéticos sobre el cuestionario real de la BD.

Comprobado:
- **Norma 035 v1:**
  - calificación y nivel iguales a los del motor, entrevistador impreso y las 4 categorías;
  - acciones por categoría y anexo con SI/NO resueltos;
  - sin Times ni el texto en inglés.
- **Persistencia** sobre la task 7 de dev: solo `evaluation` (igual a la del motor), sin `results`/`recommendations`. Body y `data_raw` restaurados byte a byte.
- **Otros tipos:**
  - v2 con sus 5 categorías;
  - salida como Pregunta | Respuesta con fecha de ingreso;
  - clima y eva 360 individual en el genérico;
  - tipo sin rúbrica → 400.
- **Regresión:** `tester_eva360_pdf.py` 13/13 y `GET /quizz/20/evaluation` (salida) igual.
- Las páginas se revisaron renderizadas. `pyrefly`: sin errores nuevos en los archivos tocados.

## Al modificar

- **Tipo nuevo con PDF dedicado:** agregarlo en `generate_pdf_from_json` igual que `NORMA035_TYPES`; lo demás cae al genérico.
- **Rúbrica de Norma 035** (BD `quizz_models`): el PDF lee `levels[clave].action_summary` y `actions`, y las `actions` de cada categoría. Los niveles que piden intervención están en `N35_ACTION_LEVELS`.
- **Shape de respuestas:** el anexo usa `answered_sections`, igual que el modo cualitativo. Si se normaliza la captura (`P-015`), se ajusta ahí y no en el PDF.
