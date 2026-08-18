# Clima laboral (tipo 3) — rúbrica % positivo + resultado organizacional

> Cierra el pendiente "clima laboral (3) pendiente de rúbrica" del refactor de encuestas ([`encuestas_refactor.md`](encuestas_refactor.md)). RH renovó el cuestionario (45 preguntas, una sola sección, escala Likert de 5 opciones) y entregó el criterio de evaluación: % de percepción positiva por categoría (9 categorías) + total organizacional, con bandas Excelente/Bueno/Adecuado/Necesita mejora. Todo entra como **config** (`files/rubrics/3.json`); el motor solo ganó capacidades genéricas.

## El criterio de RH, traducido a la rúbrica

- **Escala**: `0` Totalmente de acuerdo, `1` De acuerdo, `2` Neutral, `3` En desacuerdo, `4` Totalmente en desacuerdo (índice = posición en `options` de la plantilla).
- **Fórmula por categoría**: `% = positivas / (positivas + negativas) × 100`. Positivas = opciones 0/1, negativas = 3/4; **Neutral se anula** (no cuenta para ningún lado, tampoco en el denominador). En la rúbrica: `values: [100, 100, null, 0, 0]` + `agg: "avg"` — el promedio de 100s y 0s excluyendo `null` ES esa fórmula.
- **Total organizacional** = promedio simple de los % de las 9 categorías (validado contra la tabla 2025 de RH: 85.4). En la rúbrica: `total_agg: "avg_breakdown"`.
- **Bandas** (contiguas, mismas por categoría y total): `< 80` necesita_mejora, `80–<85` adecuado, `85–90` bueno (el 90.0 exacto es bueno), `> 90` excelente. El borde se implementa con `high: 90.01` (los scores van redondeados a 2 decimales).
- **Mapeo pregunta → categoría: cíclico mod 9.** El cuestionario recorre las 9 categorías en orden y repite el ciclo 5 veces: pregunta N (1-based) → categoría `((N-1) mod 9) + 1`. Orden: Liderazgo, Reconocimiento/Motivación, Comunicación interna, Relación con compañeros, Capacitación/Desarrollo profesional, Condiciones laborales-Seguridad, Jornada-Carga laboral, Conocimiento del puesto, Sentido de pertenencia-Cultura. 5 ítems por categoría; el detalle vive en `tree[].items` de la rúbrica (editable en datos si RH reubica alguna).
- **Pregunta 34 invertida**: "¿Con qué frecuencia sientes que tienes que trabajar bajo presión…?" — estar *de acuerdo* es percepción negativa, así que va en un `item_map` aparte con `values: [0, 0, null, 100, 100]`. Si RH decide contarla directa, es editar ese map en el JSON.
- **Categoría 100% neutral** (solo evaluación individual, 5 ítems): `score: null`, sin `level`, y **no** entra al promedio del total. Un total sin ninguna categoría clasificable también queda `null`.

## Capas tocadas

| Capa | Archivo | Cambio |
|---|---|---|
| Config (nuevo) | [`files/rubrics/3.json`](../files/rubrics/3.json) | Rúbrica clima: 2 item_maps (normal + invertida 34), árbol de 9 categorías `agg:"avg"`, `total_agg:"avg_breakdown"`, bandas y niveles con acciones. |
| Plantilla | [`files/quizz_clima_laboral.json`](../files/quizz_clima_laboral.json) | Cuestionario nuevo de RH (45 subpreguntas, 1 sección). **Fix crítico**: el archivo commiteado era JSON inválido (un `50` pegado tras la última subpregunta) → `GET /misc/download/quizz/3` devolvía 400 siempre. |
| Motor | [`templates/resources/midleware/quizz_eval_engine.py`](../templates/resources/midleware/quizz_eval_engine.py) | 5 capacidades genéricas (abajo). Sin cambios de contrato para Norma 035 / eva 360 (regresión verificada). |
| Orquestación | [`templates/resources/midleware/Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) | Nueva `get_quizz_group_evaluation(type_q, data_token, date_from, date_to)`: agrega todas las encuestas contestadas del tipo por conteo agrupado, filtro opcional de fechas, envelope `{data,msg,error}`. |
| HTTP | [`templates/resources/rs_RRHH.py`](../templates/resources/rs_RRHH.py) | Nueva ruta `GET /quizzes/summary/<int:type_q>` (clase `QuizzesSummary`). |

## Qué ganó el motor (genérico, no clima-specific)

1. **`values`/`na_value` en `null` = respuesta excluida** (`score_items`): el ítem no aparece en `detail` ni puntúa — así se "anula" el Neutral.
2. **`agg:"avg"` sin valores → score `None`** (`_aggregate`); con `sum` conserva el `0` histórico. `classify(None, …)` nunca clasifica; los hijos `None` se ignoran al agregar.
3. **`total_agg: "avg_breakdown"`**: el total es el promedio de los scores del primer nivel del árbol (ignorando `None`) en vez de la suma de puntos por ítem.
4. **Adapter de `subquestions`** (`flatten_responses`): secciones sin rango `items` pero con `subquestions` se numeran con contador corrido 1-based en orden numérico de llave de sección (clima: sección `"0"` → ítems 1..45). Si una sección trae ambos, `items` manda; el contador avanza aunque la sección esté sin contestar.
5. **`evaluate_group(data_raws, rubric)`**: junta los puntos por ítem de N respondentes (`{item: [puntos, …]}`) y evalúa el mismo árbol sobre el conjunto → con `avg` eso es el **conteo agrupado** (% sobre todas las respuestas contables de la categoría, no promedio de los % individuales). Devuelve el shape uniforme + `respondents`; `detail` trae el promedio por ítem (en clima: % positivo por pregunta — útil para ubicar la pregunta problema).

`_tree_and_total` es el helper compartido entre `evaluate` y `evaluate_group`; `_eval_node` acepta puntos escalares o listas.

## Corte duro (sin migración)

El cuestionario viejo (12 secciones temáticas propias) es incompatible con el nuevo. Verificado contra la BD de dev: solo existían **3 tasks de clima, todas con `data_raw` vacío** (marzo 2025) — nada que migrar. Una task vieja *contestada* evaluaría con ítems desalineados; si apareciera alguna en prod, se reencuesta.

## Al modificar

- **Reubicar una pregunta de categoría / cambiar bandas / quitar la inversión de la 34**: editar `files/rubrics/3.json`, sin código ni redeploy.
- **Cambiar el cuestionario**: si cambia el **número o el orden** de subpreguntas, la rúbrica se desalinea — actualizar `tree[].items` y los `item_maps` a la vez. El mapeo es posicional (1-based sobre `subquestions`).
- **No** usar `0` como valor de exclusión en rúbricas de %: `0` puntúa (negativa), `null` excluye.
- El agregado filtra por el `timestamp` del task (fecha de creación/asignación), no por `metadata.date`.

---

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)**. Departamento `rrhh`.
**Base:** `/GUI/api/v1/rrhh` (captura en `/GUI/api/v1/misc`).
**Envelope:** `{ "data": …, "msg": …, "error": … }`.

### Captura (sin cambios de mecánica)

1. `GET /GUI/api/v1/misc/download/quizz/3` → plantilla (`data`). *(Antes de este cambio devolvía 400 por el JSON roto.)*
2. El front llena en la sección `"0"`: `"answer": [[0, idx], [1, idx], … [44, idx]]` — un par `[posición_subpregunta, índice_opción]` por cada una de las 45, **en orden**. Índice de opción: 0=Totalmente de acuerdo … 4=Totalmente en desacuerdo.
3. Guardar con el CRUD de tasks existente (`PUT /GUI/api/v1/misc/task/quizz`), conservando `metadata` intacta en el `body` (trae `type_quizz: 3`).

### `GET /GUI/api/v1/rrhh/quizz/<id_task>/evaluation` — resultado individual

Ahora responde para clima (ya no cae al "sin rúbrica"). Shape uniforme; las categorías son el primer nivel de `breakdown`:

```jsonc
// 200
{ "data": {
    "type": 3, "mode": "scored",
    "total": { "score": 85.42, "level": { "key": "bueno", "label": "Bueno" }, "actions": ["…"] },
    "breakdown": [
      { "id": "c1", "kind": "categoria", "label": "Liderazgo", "score": 84.5,
        "level": { "key": "adecuado", "label": "Adecuado" } },
      { "id": "c9", "kind": "categoria", "label": "Sentido de pertenencia - Cultura",
        "score": null }                                  // 100% neutral: sin nivel, fuera del total
    ],
    "detail": { "1": 100, "2": 0, "4": 100 }             // % por ítem; los neutrales NO aparecen
  }, "msg": null, "error": null }
```

### `GET /GUI/api/v1/rrhh/quizzes/summary/<type_q>` — tabla organizacional (nuevo)

Para clima: `type_q = 3`. Query opcional `date_from` / `date_to` (`YYYY-MM-DD`, inclusivos, sobre el timestamp del task). Es la tabla del reporte anual: `breakdown[].label|score|level` = filas, `total` = CLIMA ORGANIZACIONAL TOTAL.

```jsonc
// 200 — con encuestas contestadas
{ "data": {
    "type": 3, "mode": "scored", "respondents": 38,
    "total": { "score": 85.4, "level": { "key": "bueno", "label": "Bueno" }, "actions": ["…"] },
    "breakdown": [ { "id": "c1", "kind": "categoria", "label": "Liderazgo", "score": 84.5,
                     "level": { "key": "adecuado", "label": "Adecuado" } } /* …9 categorías… */ ],
    "detail": { "1": 92.11, "2": 71.05 }                 // % positivo POR PREGUNTA (drill-down)
  }, "msg": null, "error": null }

// 200 — sin encuestas contestadas en el rango (data NO es null: shape completo con scores null)
{ "data": { "type": 3, "respondents": 0, "total": { "score": null }, "breakdown": [ /* scores null */ ], "detail": {} },
  "msg": "Sin encuestas contestadas del tipo 3 en el rango solicitado", "error": null }

// 200 — tipo sin rúbrica (o cualitativo): data null, ramificar por data
{ "data": null, "msg": "No hay rubrica para el tipo de encuesta 0 (pendiente de migracion)", "error": null }

// 400 — fecha mal formada
{ "data": null, "msg": "Fecha invalida en date_from (formato YYYY-MM-DD): 31/12/2026", "error": null }
```

**Gotchas:**
- `score` puede ser `null` en cualquier nodo y en `total` (sin datos clasificables) → sin `level`. Pintar `—` y no sumarlo a nada.
- El agregado es **conteo agrupado** (todas las respuestas juntas), no promedio de los resultados individuales — no intentar reproducirlo sumando los `GET` individuales.
- `respondents` cuenta encuestas con al menos una respuesta; la vacía asignada no cuenta.
- La pregunta 34 está invertida: en `detail`, su 100 significa "en desacuerdo con trabajar bajo presión" (bueno).
- Bandas para colorear la tabla: `necesita_mejora` <80, `adecuado` 80–<85, `bueno` 85–90, `excelente` >90 (usar `level.key`, no recalcular).

## Pendientes

- **PDF individual de clima**: sigue imprimiendo el shape legacy vía el shim (`c_final`/`c_cat` en texto plano). Entra en el rediseño general de PDFs de encuestas (skill `pdf-design`).
- **PDF/export de la tabla organizacional** — hoy solo JSON; el front la pinta.
- Rúbrica de **salida (0)** cualitativa (pendiente previo, sin cambios).
