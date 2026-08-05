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


def flatten_per_question(data_raw):
    """Adapta un `data_raw` donde cada pregunta es una entrada con `answer`
    escalar (indice de opcion) — layout de eva 360 y afines. La llave de la
    pregunta ES el numero de item. `{ "4": {"answer": 0}, ... }` -> `{4: 0}`.
    """
    flat = {}
    if not isinstance(data_raw, dict):
        return flat
    for key, question in data_raw.items():
        if not isinstance(question, dict):
            continue
        if not str(key).lstrip("-").isdigit():
            continue
        ans = question.get("answer")
        if ans is None or ans == "":
            continue
        idx = ans[1] if isinstance(ans, (list, tuple)) and len(ans) > 1 else ans
        flat[int(key)] = idx
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

    scoring = rubric.get("scoring", {})
    if scoring.get("response_layout") == "per_question":
        flat = flatten_per_question(data_raw)
    else:
        flat = flatten_responses(data_raw)
    points = score_items(flat, scoring.get("item_maps", []))
    levels = rubric.get("levels", {})
    breakdown = [_eval_node(n, points, levels) for n in rubric.get("tree", [])]

    total_score = sum(points.values())
    total: dict = {"score": total_score}
    scale = rubric.get("scale")
    if scale and scale.get("max"):
        total["scaled"] = round(total_score / scale["max"] * scale.get("to", 100), 1)
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


def evaluate_eva360(perspectives, assigned_roles=None, evaluated_emp=None, evaluation_id=None):
    """Agrega las N perspectivas de un proceso eva 360 en un resultado unico.

    `perspectives`: lista de `{"role": str, "evaluation": <dict de evaluate()> | None}`
    (una por evaluador asignado; `evaluation` None si aun no responde). El promedio
    va sobre las respondidas; se exponen `assigned` vs `answered`.

    Devuelve:
      { type:4, evaluation_id, evaluated_emp, assigned, answered,
        general:{score_100}, by_perspective:{role:{score_100, raw_total}},
        competencies:[{id, label, by_role:{role:val}, average, distribution:{"1..5":n}}] }
    """
    answered = [p for p in perspectives if p.get("evaluation")]
    by_perspective = {}
    comp_acc = {}
    for p in answered:
        role = p.get("role")
        ev = p["evaluation"]
        total = ev.get("total", {})
        by_perspective[role] = {
            "score_100": total.get("scaled"),
            "raw_total": total.get("score"),
        }
        for node in ev.get("breakdown", []):
            cid = node.get("id")
            acc = comp_acc.setdefault(
                cid, {"id": cid, "label": node.get("label"), "by_role": {}, "values": []}
            )
            acc["by_role"][role] = node.get("score")
            if node.get("score") is not None:
                acc["values"].append(node.get("score"))

    scaled = [v["score_100"] for v in by_perspective.values() if v["score_100"] is not None]
    general = round(sum(scaled) / len(scaled), 1) if scaled else None

    competencies = []
    for acc in comp_acc.values():
        vals = acc["values"]
        distribution = {str(k): 0 for k in range(1, 6)}
        for v in vals:
            iv = int(round(v))
            if 1 <= iv <= 5:
                distribution[str(iv)] += 1
        competencies.append({
            "id": acc["id"],
            "label": acc["label"],
            "by_role": acc["by_role"],
            "average": round(sum(vals) / len(vals), 2) if vals else None,
            "distribution": distribution,
        })

    assigned = len(assigned_roles) if assigned_roles is not None else len(perspectives)
    return {
        "type": 4,
        "evaluation_id": evaluation_id,
        "evaluated_emp": evaluated_emp,
        "assigned": assigned,
        "answered": len(answered),
        "general": {"score_100": general},
        "by_perspective": by_perspective,
        "competencies": competencies,
    }
