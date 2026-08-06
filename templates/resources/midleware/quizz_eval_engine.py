"""
Motor de evaluacion de encuestas (config-driven).

Reemplaza el scoring/interpretacion hardcodeado por tipo
(`calculate_results_quizzes` + `recommendations_results_quizzes`) por un solo
motor que aplica una **rubrica en datos**. El tipo de encuesta deja de vivir
en el codigo: es puro config. La rubrica vive en la BD (columna `rubric` de
`sql_telintec_mod_rrhh.quizz_models`, CRUD en /rrhh/quizz/models); los
`files/rubrics/<tipo>.json` del repo quedaron como fuente del seed.

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
    Un score None (sin datos clasificables) nunca clasifica.
    """
    if score is None or not bands:
        return None
    for entry in bands:
        key, low, high = entry[0], entry[1], entry[2]
        if (low is None or score >= low) and (high is None or score < high):
            return key
    return None


def flatten_responses(data_raw):
    """Adapta el `data_raw` actual (secciones con rango `items` + lista `answer`
    de pares [label, indice]) a un mapa plano {numero_item: indice_opcion}.

    Secciones sin rango `items` pero con lista `subquestions` (layout de clima
    laboral) se numeran con un contador corrido 1-based en el orden numerico de
    las llaves de seccion: la subpregunta k de la seccion es el item base+k. El
    contador avanza aunque la seccion este sin contestar, para que la
    numeracion sea estable. Si una seccion trae ambos, `items` manda.

    Puente hacia el shape viejo mientras la UI de captura se normaliza; cuando
    el front mande respuestas ya planas, este adapter se vuelve trivial.
    """
    flat = {}
    if not isinstance(data_raw, dict):
        return flat

    def _order(kv):
        try:
            return (0, int(kv[0]))
        except (TypeError, ValueError):
            return (1, 0)

    next_item = 1
    for _, section in sorted(data_raw.items(), key=_order):
        if not isinstance(section, dict):
            continue
        items = section.get("items")
        answers = section.get("answer")
        subquestions = section.get("subquestions")
        lo = hi = None
        if items and items != "":
            try:
                lo, hi = int(items[0]), int(items[1])
            except (TypeError, ValueError, IndexError):
                continue
        elif isinstance(subquestions, list) and subquestions:
            lo, hi = next_item, next_item + len(subquestions) - 1
            next_item = hi + 1
        if lo is None or hi is None or not isinstance(answers, list):
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
    """{item: indice_opcion} -> {item: puntos} usando los item_maps de la rubrica.

    Un valor `null` en `values` (o un `na_value: null`) EXCLUYE la respuesta del
    puntaje: el item no aparece en el resultado (p.ej. la opcion Neutral de
    clima laboral, que "se anula" y no cuenta para ningun lado).
    """
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
            val = values[idx]
        else:
            val = na
        if val is None:
            continue
        points[q] = val
    return points


def _aggregate(vals, agg):
    """Con `avg` y sin valores devuelve None (sin datos clasificables); con
    `sum` conserva el 0 historico (Norma 035 / eva 360)."""
    if not vals:
        return None if agg == "avg" else 0
    if agg == "avg":
        return round(sum(vals) / len(vals), 2)
    return sum(vals)


def _eval_node(node, points, levels):
    """`points` mapea item -> puntos (int) o item -> [puntos, ...] (agregado
    de varios respondentes, conteo agrupado)."""
    agg = node.get("agg", "sum")
    children = node.get("children")
    result_children = []
    if children:
        for ch in children:
            result_children.append(_eval_node(ch, points, levels))
        child_scores = [c["score"] for c in result_children if c.get("score") is not None]
        score = _aggregate(child_scores, agg)
    else:
        item_pts = []
        for it in node.get("items", []):
            val = points.get(int(it))
            if val is None:
                continue
            if isinstance(val, list):
                item_pts.extend(val)
            else:
                item_pts.append(val)
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


def _flatten_for(rubric, data_raw):
    """Aplica el adapter de respuestas que pide la rubrica."""
    if rubric.get("scoring", {}).get("response_layout") == "per_question":
        return flatten_per_question(data_raw)
    return flatten_responses(data_raw)


def _tree_and_total(points, rubric):
    """Evalua el arbol y el total sobre `points` ({item: puntos} o, en conteo
    agrupado, {item: [puntos, ...]}). Devuelve (breakdown, total).

    `total_agg: "avg_breakdown"` en la rubrica hace que el total sea el
    promedio de los scores del primer nivel del arbol (ignorando None) en vez
    de la suma de puntos por item — es el "promedio de categorias" de clima.
    Un total sin datos queda en score None y no clasifica.
    """
    levels = rubric.get("levels", {})
    breakdown = [_eval_node(n, points, levels) for n in rubric.get("tree", [])]

    if rubric.get("total_agg") == "avg_breakdown":
        top_scores = [n["score"] for n in breakdown if n.get("score") is not None]
        total_score = _aggregate(top_scores, "avg")
    else:
        total_score = 0
        for val in points.values():
            total_score += sum(val) if isinstance(val, list) else val
    total: dict = {"score": total_score}
    scale = rubric.get("scale")
    if total_score is not None and scale and scale.get("max"):
        total["scaled"] = round(total_score / scale["max"] * scale.get("to", 100), 1)
    key = classify(total_score, rubric.get("bands_total"))
    if key:
        lv = levels.get(key, {})
        total["level"] = {"key": key, "label": lv.get("label", key)}
        total["actions"] = lv.get("actions", [])
    return breakdown, total


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

    flat = _flatten_for(rubric, data_raw)
    points = score_items(flat, rubric.get("scoring", {}).get("item_maps", []))
    breakdown, total = _tree_and_total(points, rubric)

    return {
        "type": rubric.get("type"),
        "mode": mode,
        "total": total,
        "breakdown": breakdown,
        "detail": {str(q): p for q, p in sorted(points.items())},
    }


def evaluate_group(data_raws, rubric):
    """Agrega N encuestas del mismo tipo por CONTEO AGRUPADO: junta los puntos
    por item de todos los respondentes ({item: [puntos, ...]}) y evalua el
    mismo arbol sobre el conjunto — con `agg: "avg"` eso es el % sobre todas
    las respuestas contables de la categoria (no el promedio de los % de cada
    quien). Solo aplica a rubricas `scored`; devuelve None en cualitativas.

    Devuelve el contrato uniforme mas `respondents` (encuestas con al menos
    una respuesta); `detail` trae el promedio por item (en clima: % de
    percepcion positiva de cada pregunta).
    """
    if rubric.get("mode", "scored") == "qualitative":
        return None
    item_maps = rubric.get("scoring", {}).get("item_maps", [])
    pooled = {}
    respondents = 0
    for data_raw in data_raws:
        if isinstance(data_raw, str):
            import json
            try:
                data_raw = json.loads(data_raw)
            except (TypeError, ValueError):
                continue
        flat = _flatten_for(rubric, data_raw)
        if not flat:
            continue
        respondents += 1
        for q, val in score_items(flat, item_maps).items():
            pooled.setdefault(q, []).append(val)

    breakdown, total = _tree_and_total(pooled, rubric)
    return {
        "type": rubric.get("type"),
        "mode": "scored",
        "respondents": respondents,
        "total": total,
        "breakdown": breakdown,
        "detail": {
            str(q): round(sum(vals) / len(vals), 2) for q, vals in sorted(pooled.items())
        },
    }


def load_rubric(type_q, data_token=None):
    """Carga la rubrica del tipo desde la BD (quizz_models.rubric). Devuelve
    el dict o None si el tipo no existe o no tiene rubrica. Se ignora el
    status del modelo a proposito: el historial de un tipo archivado sigue
    siendo evaluable. `data_token` viaja para el switching a BD de test."""
    import json
    from templates.controllers.rrhh.quizz_models_controller import (
        get_quizz_model_rubric_db,
    )

    flag, _, row = get_quizz_model_rubric_db(int(type_q), data_token)
    if not flag or not row:
        return None
    rubric = row[0]  # pyrefly: ignore
    if rubric is None or rubric == "":
        return None
    if isinstance(rubric, str):
        try:
            rubric = json.loads(rubric)
        except (TypeError, ValueError):
            return None
    return rubric if isinstance(rubric, dict) else None


def evaluate_task(data_raw, type_q, data_token=None):
    """Conveniencia: carga la rubrica del tipo y evalua. None si no hay rubrica."""
    rubric = load_rubric(type_q, data_token)
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


# --- Validacion de rubricas (CRUD de modelos de encuesta) ---------------------
_VALID_MODES = ("scored", "qualitative")
_VALID_LAYOUTS = (None, "sections", "per_question")
_VALID_AGGS = (None, "sum", "avg")


def _validate_bands(bands, path, levels, errors):
    """Bandas [[key, low, high], ...]: forma + que la key exista en levels."""
    if not isinstance(bands, list):
        errors.append(f"{path}: debe ser una lista de bandas [key, low, high]")
        return
    for i, entry in enumerate(bands):
        if not isinstance(entry, (list, tuple)) or len(entry) < 3:
            errors.append(f"{path}[{i}]: banda invalida, se espera [key, low, high]")
            continue
        key, low, high = entry[0], entry[1], entry[2]
        if not isinstance(key, str) or not key:
            errors.append(f"{path}[{i}]: la key de la banda debe ser un string")
        elif levels and key not in levels:
            errors.append(f"{path}[{i}]: la key '{key}' no existe en levels")
        for name, limit in (("low", low), ("high", high)):
            if limit is not None and not isinstance(limit, (int, float)):
                errors.append(f"{path}[{i}]: {name} debe ser numero o null")


def _validate_tree_node(node, path, levels, errors):
    if not isinstance(node, dict):
        errors.append(f"{path}: nodo invalido, debe ser un objeto")
        return
    if node.get("agg") not in _VALID_AGGS:
        errors.append(f"{path}: agg '{node.get('agg')}' invalido (sum|avg)")
    children = node.get("children")
    items = node.get("items")
    if not children and not items:
        errors.append(f"{path}: el nodo necesita 'children' o 'items'")
    if items is not None:
        if not isinstance(items, list) or not items:
            errors.append(f"{path}: items debe ser lista no vacia de numeros de item")
        else:
            for it in items:
                if not str(it).lstrip("-").isdigit():
                    errors.append(f"{path}: item '{it}' no es un numero")
    if node.get("bands") is not None:
        _validate_bands(node["bands"], f"{path}.bands", levels, errors)
    if children is not None:
        if not isinstance(children, list):
            errors.append(f"{path}: children debe ser una lista")
        else:
            for i, ch in enumerate(children):
                _validate_tree_node(ch, f"{path}.children[{i}]", levels, errors)


def validate_rubric(rubric):
    """Validacion estructural de una rubrica ANTES de guardarla en el modelo.
    Devuelve lista de errores (vacia = valida). Es la contraparte del CRUD de
    /rrhh/quizz/models: una rubrica mal formada no debe llegar a la BD para
    tronar semanas despues al evaluar la primera encuesta contestada."""
    errors = []
    if not isinstance(rubric, dict):
        return ["la rubrica debe ser un objeto JSON"]
    mode = rubric.get("mode", "scored")
    if mode not in _VALID_MODES:
        errors.append(f"mode '{mode}' invalido ({'|'.join(_VALID_MODES)})")
        return errors
    if mode == "qualitative":
        return errors

    levels = rubric.get("levels", {})
    if not isinstance(levels, dict):
        errors.append("levels debe ser un objeto {key: {label, actions}}")
        levels = {}

    scoring = rubric.get("scoring")
    if not isinstance(scoring, dict):
        errors.append("scoring es obligatorio en modo scored")
        return errors
    if scoring.get("response_layout") not in _VALID_LAYOUTS:
        errors.append(
            f"scoring.response_layout '{scoring.get('response_layout')}' invalido "
            "(sections|per_question|ausente)"
        )
    item_maps = scoring.get("item_maps")
    if not isinstance(item_maps, list) or not item_maps:
        errors.append("scoring.item_maps debe ser una lista no vacia")
        item_maps = []
    for i, m in enumerate(item_maps):
        path = f"scoring.item_maps[{i}]"
        if not isinstance(m, dict):
            errors.append(f"{path}: debe ser un objeto")
            continue
        items = m.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"{path}.items: lista no vacia de numeros de item")
        else:
            for it in items:
                if not str(it).lstrip("-").isdigit():
                    errors.append(f"{path}.items: item '{it}' no es un numero")
        values = m.get("values")
        if not isinstance(values, list) or not values:
            errors.append(f"{path}.values: lista no vacia (puntos por indice de opcion)")
        else:
            non_null = 0
            for v in values:
                if v is None:
                    continue
                if not isinstance(v, (int, float)):
                    errors.append(f"{path}.values: '{v}' debe ser numero o null")
                else:
                    non_null += 1
            if non_null == 0:
                errors.append(f"{path}.values: todos los valores son null (nada puntua)")
        na = m.get("na_value", 0)
        if na is not None and not isinstance(na, (int, float)):
            errors.append(f"{path}.na_value: debe ser numero o null")

    if rubric.get("bands_total") is not None:
        _validate_bands(rubric["bands_total"], "bands_total", levels, errors)
    if rubric.get("total_agg") not in (None, "avg_breakdown"):
        errors.append(f"total_agg '{rubric.get('total_agg')}' invalido (avg_breakdown|ausente)")
    scale = rubric.get("scale")
    if scale is not None:
        if not isinstance(scale, dict) or not isinstance(scale.get("max"), (int, float)) or scale["max"] <= 0:
            errors.append("scale: debe ser objeto con max numerico > 0")

    tree = rubric.get("tree")
    if tree is not None:
        if not isinstance(tree, list):
            errors.append("tree debe ser una lista de nodos")
        else:
            for i, node in enumerate(tree):
                _validate_tree_node(node, f"tree[{i}]", levels, errors)
    return errors


def dry_run_rubric(rubric):
    """Corre `evaluate()` con respuestas sinteticas construidas desde los
    item_maps (cada item contesta la primera opcion con valor no-null) y
    verifica que produzca el shape uniforme. Atrapa rubricas estructuralmente
    validas pero rotas en ejecucion. Devuelve un string de error o None."""
    try:
        if rubric.get("mode", "scored") == "qualitative":
            result = evaluate({}, rubric)
            if "qualitative" not in result:
                return "la evaluacion de prueba no produjo salida cualitativa"
            return None

        item_maps = rubric.get("scoring", {}).get("item_maps", [])
        answer_by_item = {}
        for m in item_maps:
            values = m.get("values", [])
            idx = next((i for i, v in enumerate(values) if v is not None), 0)
            for it in m.get("items", []):
                answer_by_item[int(it)] = idx
        if not answer_by_item:
            return "item_maps sin items: no hay nada que evaluar"

        if rubric.get("scoring", {}).get("response_layout") == "per_question":
            synthetic = {str(it): {"answer": idx} for it, idx in answer_by_item.items()}
        else:
            lo, hi = min(answer_by_item), max(answer_by_item)
            answers = [["op", answer_by_item.get(q, 0)] for q in range(lo, hi + 1)]
            synthetic = {"0": {"items": [lo, hi], "answer": answers}}

        result = evaluate(synthetic, rubric)
        if not isinstance(result.get("total"), dict) or "breakdown" not in result:
            return "la evaluacion de prueba no produjo total/breakdown"
        if not result.get("detail"):
            return "la evaluacion de prueba no puntuo ningun item (revisar items/values)"
        return None
    except Exception as e:
        return f"la evaluacion de prueba fallo: {e}"
