# -*- coding: utf-8 -*-
"""
Midleware del proceso Eva 360.

Un proceso eva 360 = 1 task de CONTROL (asignada a RH, guarda expected_roles y
status_eval) + N tasks de EVALUADOR (una por rol: self|superior|peer|subordinate),
todas sobre `tasks_gui` y ligadas por `metadata.evaluation_id` (UUID generado
aqui). Cada evaluador llena su task por el CRUD de encuestas existente
(`PUT /misc/task/quizz`); la agregacion del resultado vive en
`quizz_eval_engine.evaluate_eva360`.

Una perspectiva cuenta como respondida solo cuando TODAS las competencias de la
rubrica tienen respuesta (un parcial bajaria el score escalado a 100).
"""
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026 $"

import json
import uuid

from templates.controllers.misc.tasks_controller import (
    create_task,
    get_tasks_by_eva360_group,
    update_task,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.resources.midleware.quizz_eval_engine import (
    evaluate,
    evaluate_eva360,
    flatten_per_question,
    load_rubric,
)

EVA360_TYPE = 4
EVA360_ROLES = ("self", "superior", "peer", "subordinate")


def _rubric_items(rubric):
    items = set()
    for m in rubric.get("scoring", {}).get("item_maps", []):
        items.update(int(i) for i in m.get("items", []))
    return items


def _is_answered(data_raw, rubric_items):
    """True si todas las competencias de la rubrica tienen respuesta."""
    flat = flatten_per_question(data_raw)
    return rubric_items.issubset(set(flat.keys()))


def _parse_rows(result):
    """Filas de tasks_gui -> (control | None, raters[]). Cada entrada trae
    id, body, data_raw y metadata ya parseados."""
    control = None
    raters = []
    for row in result:
        body = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        data_raw = json.loads(row[2]) if isinstance(row[2], str) else row[2]
        meta = (body or {}).get("metadata") or {}
        entry = {"id_task": row[0], "body": body, "data_raw": data_raw, "meta": meta}
        if meta.get("eva360_kind") == "control":
            control = entry
        else:
            raters.append(entry)
    return control, raters


def _load_process(evaluation_id, data_token):
    """Carga y clasifica las tasks del proceso. Devuelve (envelope_error|None,
    code, control, raters)."""
    flag, error, result = get_tasks_by_eva360_group(evaluation_id, data_token)
    if not flag:
        return (
            {"data": None, "msg": "No se pudo obtener el proceso eva 360", "error": error},
            400, None, [],
        )
    rows = result if isinstance(result, list) else []
    if not rows:
        return (
            {"data": None, "msg": f"Proceso eva 360 {evaluation_id} no encontrado", "error": None},
            404, None, [],
        )
    control, raters = _parse_rows(rows)
    return None, 200, control, raters


def create_eva360_process(data, data_token):
    """Crea el proceso completo: task de control + una task por evaluador.
    El back genera el evaluation_id y arma el linking (el front no toca metadata).
    """
    evaluated_emp = data["evaluated_emp"]
    evaluated_name = data.get("evaluated_name") or ""
    date_limit = data.get("date_limit") or ""
    raters_in = data.get("raters") or []

    if not raters_in:
        return {"data": None, "msg": "Se requiere al menos un evaluador", "error": None}, 400
    seen_roles = set()
    raters = []
    for r in raters_in:
        role = (r.get("role") or "").strip().lower()
        if role not in EVA360_ROLES:
            return {
                "data": None,
                "msg": f"Rol invalido '{role}'. Validos: {', '.join(EVA360_ROLES)}",
                "error": None,
            }, 400
        if role in seen_roles:
            return {"data": None, "msg": f"Rol duplicado '{role}' (uno por rol)", "error": None}, 400
        seen_roles.add(role)
        emp_id = r.get("emp_id") or 0
        if role == "self":
            emp_id = evaluated_emp
        if not emp_id:
            return {
                "data": None,
                "msg": f"Falta emp_id para el rol '{role}'",
                "error": None,
            }, 400
        raters.append({"role": role, "emp_id": emp_id})

    evaluation_id = uuid.uuid4().hex
    emp_origin = data_token.get("emp_id", 0) if isinstance(data_token, dict) else 0

    meta_control = {
        "type_quizz": EVA360_TYPE,
        "eva360_kind": "control",
        "evaluation_id": evaluation_id,
        "evaluated_emp_id": evaluated_emp,
        "name_emp": evaluated_name,
        "expected_roles": [r["role"] for r in raters],
        "status_eval": "open",
    }
    flag, error, id_control = create_task(
        "eva360 control", emp_origin, emp_origin, date_limit, meta_control, {}, data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear la task de control", "error": error}, 400

    created = []
    errors = []
    for r in raters:
        meta_rater = {
            "type_quizz": EVA360_TYPE,
            "evaluation_id": evaluation_id,
            "evaluated_emp_id": evaluated_emp,
            "name_emp": evaluated_name,
            "eva360_role": r["role"],
        }
        flag, error, id_task = create_task(
            f"quizz eva360 {r['role']}",
            r["emp_id"],
            emp_origin,
            date_limit,
            meta_rater,
            {},
            data_token,
        )
        if flag:
            created.append({"role": r["role"], "emp_id": r["emp_id"], "id_task": id_task})
            msg = (
                f"Se te asigno una evaluacion 360 ({r['role']}) "
                f"de {evaluated_name or evaluated_emp} (task {id_task})"
            )
            create_notification_permission_notGUI(
                msg, data_token, ["RRHH"], "Nueva evaluacion 360 asignada",
                emp_origin, r["emp_id"],
            )
        else:
            errors.append(f"Rol {r['role']}: {error}")

    data_out = {
        "evaluation_id": evaluation_id,
        "id_control": id_control,
        "raters": created,
    }
    if errors:
        return {
            "data": data_out,
            "msg": "Proceso creado parcialmente; fallaron algunas tasks de evaluador",
            "error": errors,
        }, 400
    return {
        "data": data_out,
        "msg": f"Proceso eva 360 creado ({evaluation_id}) con {len(created)} evaluadores",
        "error": None,
    }, 201


def get_eva360_process(evaluation_id, data_token):
    """Detalle del proceso para RH: control + evaluadores con su avance."""
    err, code, control, raters = _load_process(evaluation_id, data_token)
    if err is not None:
        return err, code
    rubric = load_rubric(EVA360_TYPE)
    rubric_items = _rubric_items(rubric) if rubric else set()
    raters_out = []
    for r in raters:
        raters_out.append({
            "id_task": r["id_task"],
            "role": r["meta"].get("eva360_role"),
            "emp_destiny": r["body"].get("emp_destiny"),
            "answered": _is_answered(r["data_raw"], rubric_items) if rubric_items else False,
        })
    ctrl_meta = control["meta"] if control else {}
    data_out = {
        "evaluation_id": evaluation_id,
        "id_control": control["id_task"] if control else None,
        "evaluated_emp": ctrl_meta.get("evaluated_emp_id"),
        "evaluated_name": ctrl_meta.get("name_emp"),
        "expected_roles": ctrl_meta.get("expected_roles", []),
        "status_eval": ctrl_meta.get("status_eval", "open"),
        "raters": raters_out,
    }
    return {"data": data_out, "msg": None, "error": None}, 200


def get_eva360_result(evaluation_id, data_token):
    """Resultado agregado del proceso (evaluate_eva360): general, por
    perspectiva y por competencia. Promedia solo las respondidas."""
    err, code, control, raters = _load_process(evaluation_id, data_token)
    if err is not None:
        return err, code
    rubric = load_rubric(EVA360_TYPE)
    if rubric is None:
        return {
            "data": None,
            "msg": "No hay rubrica para eva 360 (files/rubrics/4.json)",
            "error": None,
        }, 400
    rubric_items = _rubric_items(rubric)
    perspectives = []
    for r in raters:
        role = r["meta"].get("eva360_role")
        if _is_answered(r["data_raw"], rubric_items):
            perspectives.append({"role": role, "evaluation": evaluate(r["data_raw"], rubric)})
        else:
            perspectives.append({"role": role, "evaluation": None})
    ctrl_meta = control["meta"] if control else {}
    result = evaluate_eva360(
        perspectives,
        assigned_roles=ctrl_meta.get("expected_roles") or [p["role"] for p in perspectives],
        evaluated_emp=ctrl_meta.get("evaluated_emp_id"),
        evaluation_id=evaluation_id,
    )
    result["status_eval"] = ctrl_meta.get("status_eval", "open")
    result["evaluated_name"] = ctrl_meta.get("name_emp")
    return {"data": result, "msg": None, "error": None}, 200


def complete_eva360_process(evaluation_id, data_token):
    """RH marca el proceso como completado (status_eval='complete' en la task
    de control). Idempotente."""
    err, code, control, _raters = _load_process(evaluation_id, data_token)
    if err is not None:
        return err, code
    if control is None:
        return {
            "data": None,
            "msg": f"El proceso {evaluation_id} no tiene task de control",
            "error": None,
        }, 400
    meta = control["meta"]
    meta["status_eval"] = "complete"
    # update_task con data_raw=None lo resetea a {}; la task de control no
    # guarda respuestas, asi que es seguro.
    flag, error, _ = update_task(
        control["id_task"], control["body"], data_token, metadata=meta
    )
    if not flag:
        return {"data": None, "msg": "No se pudo completar el proceso", "error": error}, 400
    return {
        "data": {"evaluation_id": evaluation_id, "status_eval": "complete"},
        "msg": f"Proceso eva 360 {evaluation_id} marcado como completado",
        "error": None,
    }, 200
