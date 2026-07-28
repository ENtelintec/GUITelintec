"""
Motor de evaluacion de encuestas (config-driven).

Reemplaza el scoring/interpretacion hardcodeado por tipo
(`calculate_results_quizzes` + `recommendations_results_quizzes`) por un solo
motor que aplica una **rubrica en datos** (`files/rubrics/<tipo>.json`). El tipo
de encuesta deja de vivir en el codigo: es puro config.

Pipeline:  parse respuestas -> puntaje por item (item_maps) ->
           agregacion en arbol (sum/avg) -> clasificacion por bandas ->
           interpretacion por nivel (levels).

La salida es un contrato UNIFORME (mismo shape para todos los tipos) que el
front renderiza con un solo componente recursivo. Ver
`Docs/plan_rh_mes.md` para el diseno.

__author__ = "Edisson Naula"
__date__ = "2026-07-27"
"""

__author__ = "Edisson Naula"
__date__ = "2026-07-27"


def classify(score, bands):
    """Clasifica un puntaje contra un set de bandas [[key, low, high], ...].

    Una banda aplica si (low is None or score >= low) and (high is None or
    score < high). Devuelve la key del nivel o None si ninguna aplica.
    """
    if not bands:
        return None
    for entry in bands:
        key, low, high = entry[0], entry[1], entry[2]
        if (low is None or score >= low) and (high is None or score < high):
            return key
    return None


def flatten_responses(data_raw):
    """Adapta el `data_raw` actual (secciones con rango `items` + lista `answer`
    de pares [label, indice]) a un mapa plano {numero_item: indice_opcion}.

    Puente hacia el shape viejo mientras la UI de captura se normaliza; cuando
    el front mande respuestas ya planas, este adapter se vuelve trivial.
    """
    flat = {}
    if not isinstance(data_raw, dict):
        return flat
    for section in data_raw.values():
        if not isinstance(section, dict):
            continue
        items = section.get("items")
        answers = section.get("answer")
        if not items or items == "" or not isinstance(answers, list):
            continue
        try:
            lo, hi = int(items[0]), int(items[1])
        except (TypeError, ValueError, IndexError):
            continue
        for q in range(lo, hi + 1):
            pos = q - lo
            if pos >= len(answers):
                continue
            a = answers[pos]
            idx = a[1] if isinstance(a, (list, tuple)) and len(a) > 1 else a
            flat[q] = idx
    return flat


def score_items(flat, item_maps):
    """{item: indice_opcion} -> {item: puntos} usando los item_maps de la rubrica."""
    lookup = {}
    for m in item_maps:
        values = m.get("values", [])
        na = m.get("na_value", 0)
        for it in m.get("items", []):
            lookup[int(it)] = (values, na)
    points = {}
    for q, idx in flat.items():
        try:
            q = int(q)
        except (TypeError, ValueError):
            continue
        if q not in lookup:
            continue
        values, na = lookup[q]
        if isinstance(idx, bool):
            idx = int(idx)
        if isinstance(idx, int) and 0 <= idx < len(values):
            points[q] = values[idx]
        else:
            points[q] = na
    return points


def _aggregate(vals, agg):
    if not vals:
        return 0
    if agg == "avg":
        return round(sum(vals) / len(vals), 2)
    return sum(vals)


def _eval_node(node, points, levels):
    agg = node.get("agg", "sum")
    children = node.get("children")
    result_children = []
    if children:
        for ch in children:
            result_children.append(_eval_node(ch, points, levels))
        score = _aggregate([c["score"] for c in result_children], agg)
    else:
        item_pts = [points[int(it)] for it in node.get("items", []) if int(it) in points]
        score = _aggregate(item_pts, agg)
    out = {
        "id": node.get("id"),
        "kind": node.get("kind"),
        "label": node.get("label"),
        "score": score,
    }
    key = classify(score, node.get("bands"))
    if key:
        out["level"] = {"key": key, "label": levels.get(key, {}).get("label", key)}
    if node.get("actions"):
        out["actions"] = node["actions"]
    if result_children:
        out["children"] = result_children
    return out


def _evaluate_qualitative(data_raw, rubric):
    collected = []
    if isinstance(data_raw, dict):
        for section in data_raw.values():
            if not isinstance(section, dict):
                continue
            collected.append({
                "question": section.get("question"),
                "answer": section.get("answer"),
            })
    return {
        "type": rubric.get("type"),
        "mode": "qualitative",
        "qualitative": collected,
    }


def evaluate(data_raw, rubric):
    """Evalua un `data_raw` (encuesta llenada) contra una rubrica.

    Devuelve el contrato uniforme:
      { type, mode, total:{score, level, actions}, breakdown:[nodo...],
        detail:{item: puntos} }
    o, en modo cualitativo: { type, mode, qualitative:[{question, answer}] }.
    """
    if isinstance(data_raw, str):
        import json
        data_raw = json.loads(data_raw)
    mode = rubric.get("mode", "scored")
    if mode == "qualitative":
        return _evaluate_qualitative(data_raw, rubric)

    flat = flatten_responses(data_raw)
    points = score_items(flat, rubric.get("scoring", {}).get("item_maps", []))
    levels = rubric.get("levels", {})
    breakdown = [_eval_node(n, points, levels) for n in rubric.get("tree", [])]

    total_score = sum(points.values())
    total: dict = {"score": total_score}
    key = classify(total_score, rubric.get("bands_total"))
    if key:
        lv = levels.get(key, {})
        total["level"] = {"key": key, "label": lv.get("label", key)}
        total["actions"] = lv.get("actions", [])

    return {
        "type": rubric.get("type"),
        "mode": mode,
        "total": total,
        "breakdown": breakdown,
        "detail": {str(q): p for q, p in sorted(points.items())},
    }


def load_rubric(type_q):
    """Carga `files/rubrics/<tipo>.json`. Devuelve el dict o None si no existe."""
    import json
    import os
    from static.constants import rubrics_dir_path

    path = os.path.join(rubrics_dir_path, f"{int(type_q)}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_task(data_raw, type_q):
    """Conveniencia: carga la rubrica del tipo y evalua. None si no hay rubrica."""
    rubric = load_rubric(type_q)
    if rubric is None:
        return None
    return evaluate(data_raw, rubric)
