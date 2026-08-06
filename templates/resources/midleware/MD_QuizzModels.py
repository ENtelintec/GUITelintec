# -*- coding: utf-8 -*-
"""
CRUD de modelos de encuesta (template + rubrica) sobre
sql_telintec_mod_rrhh.quizz_models. Un "modelo" es el par cuestionario
(template que el front renderiza) + rubrica (config del motor
quizz_eval_engine). Ver Docs/quizz_models_crud.md.

Ciclo de vida (status): 0 BORRADOR (todo editable, no contestable) ->
1 ACTIVA (contestable; template BLOQUEADO: las respuestas guardadas en
tasks_gui son indices contra el template vivo — no hay snapshot — y editarlo
las corrompe en silencio) -> 2 ARCHIVADA (oculta, historial sigue evaluable,
reactivable). La rubrica y el nombre siguen editables en 1/2: re-evaluar el
historial con una rubrica corregida es deseable (la evaluacion es on-read).
"""

__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026  at 12:00 $"

import json
from datetime import date, datetime

import pytz

from static.constants import format_timestamps, log_file_rh, timezone_software
from templates.controllers.rrhh.quizz_models_controller import (
    LIST_COLUMNS,
    SELECT_COLUMNS,
    count_tasks_by_type_quizz,
    delete_quizz_model,
    get_quizz_model_db,
    get_quizz_model_template_db,
    get_quizz_models_db,
    insert_quizz_model,
    update_quizz_model_fields,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.quizz_eval_engine import (
    dry_run_rubric,
    validate_rubric,
)

# --- Catalogos (codigo -> etiqueta). El GET /catalogs los expone al front. ----
QM_STATUS = {0: "BORRADOR", 1: "ACTIVA", 2: "ARCHIVADA"}

# Transiciones validas del ciclo de vida y su etiqueta para el history.
QM_TRANSITIONS = {
    (0, 1): "Publicación",
    (1, 2): "Archivado",
    (2, 1): "Reactivación",
}

# Widgets que el front sabe renderizar (campo `type` de cada entrada del
# template). Inventariados de los 5 cuestionarios historicos.
QM_WIDGET_TYPES = {
    1: "Selección múltiple (varias opciones, checkbox)",
    2: "Opción única (radio)",
    3: "Matriz de subpreguntas (escala de opciones compartida por cada subquestion)",
    5: "Texto abierto",
}

# Como mapea el data_raw contestado hacia los items de la rubrica
# (scoring.response_layout; ausente = sections).
QM_RESPONSE_LAYOUTS = {
    "sections": "Secciones con rango items [desde,hasta] o subquestions con "
    "contador corrido 1-based (Norma 035 / clima laboral)",
    "per_question": "La llave de la entrada ES el numero de item y answer es "
    "el indice de opcion (eva 360)",
}

_PERMISSIONS = ["rrhh"]


# --- Helpers ------------------------------------------------------------------
def _now_ts():
    timezone = pytz.timezone(timezone_software)
    return datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)


def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _load_json(value, default):
    """template/rubric/history llegan como dict/list (ya parseado) o str."""
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


def _parse_json_field(value, field):
    """Acepta el campo como dict o como string JSON. -> (obj, error|None)."""
    if isinstance(value, dict):
        return value, None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError) as e:
            return None, f"{field}: JSON invalido ({e})"
        if isinstance(parsed, dict):
            return parsed, None
    return None, f"{field}: debe ser un objeto JSON"


def _status_label(value):
    try:
        return QM_STATUS.get(int(value), str(value))
    except (TypeError, ValueError):
        return str(value)


def _row_to_detail(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(SELECT_COLUMNS, row)}
    data["template"] = _load_json(data.get("template"), {})
    data["rubric"] = _load_json(data.get("rubric"), None)
    data["history"] = _load_json(data.get("history"), [])
    data["status_label"] = _status_label(data.get("status"))
    return data


def _row_to_list_item(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(LIST_COLUMNS, row)}
    data["has_rubric"] = bool(data.get("has_rubric"))
    data["status_label"] = _status_label(data.get("status"))
    return data


def _append_history(history, user, action, comment):
    history = history if isinstance(history, list) else []
    history.append(
        {"user": user, "action": action, "date": _now_ts(), "comment": comment}
    )
    return history


def _validate_template(template):
    """Validacion estructural dura del cuestionario: lo que el front renderiza.
    Devuelve lista de errores (vacia = valido)."""
    if not isinstance(template, dict) or not template:
        return ['template debe ser un objeto JSON no vacio {"<n>": {...}}']
    errors = []
    for key, entry in template.items():
        path = f"template['{key}']"
        if not str(key).lstrip("-").isdigit():
            errors.append(f"{path}: la llave debe ser numerica")
        if not isinstance(entry, dict):
            errors.append(f"{path}: debe ser un objeto")
            continue
        question = entry.get("question")
        if not isinstance(question, str) or not question.strip():
            errors.append(f"{path}.question: obligatorio (string no vacio)")
        wtype = entry.get("type")
        if isinstance(wtype, bool) or not isinstance(wtype, int):
            errors.append(f"{path}.type: obligatorio (entero, ver /catalogs)")
        elif wtype not in QM_WIDGET_TYPES:
            errors.append(
                f"{path}.type: {wtype} no esta en el catalogo {sorted(QM_WIDGET_TYPES)}"
            )
        for list_key in ("options", "subquestions"):
            if list_key in entry and not isinstance(entry[list_key], list):
                errors.append(f"{path}.{list_key}: debe ser lista")
        items = entry.get("items")
        if items not in (None, ""):
            valid = (
                isinstance(items, list)
                and len(items) == 2
                and all(str(x).lstrip("-").isdigit() for x in items)
            )
            if not valid:
                errors.append(f"{path}.items: debe ser [desde, hasta] (numeros)")
    return errors


def _template_item_estimate(template, layout):
    """Estimado de cuantos items puntuables tiene el template, para el
    warning de consistencia (heuristica, no bloquea)."""
    if layout == "per_question":
        keys = [int(k) for k in template if str(k).lstrip("-").isdigit()]
        return max(keys) if keys else 0
    max_hi = 0
    counter = 0
    for entry in template.values():
        if not isinstance(entry, dict):
            continue
        items = entry.get("items")
        if (
            isinstance(items, list)
            and len(items) == 2
            and str(items[1]).lstrip("-").isdigit()
        ):
            max_hi = max(max_hi, int(items[1]))
        else:
            subq = entry.get("subquestions")
            if isinstance(subq, list):
                counter += len(subq)
    return max(max_hi, counter)


def _cross_warnings(template, rubric):
    """Consistencia template<->rubrica: SOLO advertencias (el mapeo
    pregunta->item es implicito y distinto por layout; un falso positivo
    bloqueando un guardado legitimo seria peor que avisar)."""
    warnings = []
    if not isinstance(template, dict) or not isinstance(rubric, dict):
        return warnings
    if rubric.get("mode", "scored") == "qualitative":
        return warnings
    scoring = rubric.get("scoring", {})
    layout = scoring.get("response_layout") or "sections"
    rubric_items = set()
    for m in scoring.get("item_maps", []):
        for it in m.get("items", []):
            try:
                rubric_items.add(int(it))
            except (TypeError, ValueError):
                continue
    if not rubric_items:
        return warnings

    estimate = _template_item_estimate(template, layout)
    max_item = max(rubric_items)
    if estimate and max_item > estimate:
        warnings.append(
            f"la rubrica referencia el item {max_item} pero el template aparenta "
            f"tener {estimate} preguntas puntuables"
        )
    if layout == "per_question":
        keys = {int(k) for k in template if str(k).lstrip("-").isdigit()}
        missing = sorted(rubric_items - keys)
        if missing:
            warnings.append(
                f"items de la rubrica sin llave en el template (per_question): {missing[:10]}"
            )
        matrices = any(
            isinstance(e, dict) and len(e.get("subquestions") or []) > 1
            for e in template.values()
        )
        if matrices:
            warnings.append(
                "response_layout=per_question pero el template tiene matrices con "
                "varias subpreguntas: verificar el layout"
            )
    return warnings


def _check_rubric(rubric):
    """Validacion estructural + dry-run. Devuelve lista de errores o None."""
    errors = validate_rubric(rubric)
    if errors:
        return errors
    dry_error = dry_run_rubric(rubric)
    if dry_error:
        return [dry_error]
    return None


# --- CRUD ---------------------------------------------------------------------
def fetch_quizz_models(params, data_token):
    """Listado ligero. Default: solo ACTIVAS (el picker). ?all=1 -> todas;
    ?status=N -> ese status."""
    status_param = params.get("status")
    include_all = str(params.get("all") or "").strip().lower() in ("1", "true", "yes")
    if status_param is not None and str(status_param).strip() != "":
        try:
            status = int(status_param)
        except (TypeError, ValueError):
            return {"data": None, "msg": f"status invalido: {status_param}", "error": None}, 400
    elif include_all:
        status = None
    else:
        status = 1

    flag, error, rows = get_quizz_models_db(status, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar los modelos de encuesta", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_row_to_list_item(r) for r in rows]
    return {"data": data_out, "msg": f"{len(data_out)} modelos", "error": None}, 200


def get_quizz_model_detail_api(type_q, data_token):
    """Detalle completo (template + rubrica + history + conteo de tasks)."""
    flag, error, row = get_quizz_model_db(type_q, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el modelo", "error": error}, 400
    if not row:
        return {"data": None, "msg": f"No existe el modelo de encuesta {type_q}", "error": "No encontrado"}, 404
    data = _row_to_detail(row)

    tasks_total, tasks_answered = 0, 0
    flag, _, counts = count_tasks_by_type_quizz(type_q, data_token)
    if flag and counts:
        tasks_total = int(counts[0] or 0)  # pyrefly: ignore
        tasks_answered = int(counts[1] or 0)  # pyrefly: ignore
    data["tasks_total"] = tasks_total
    data["tasks_answered"] = tasks_answered
    data["has_answered_tasks"] = tasks_answered > 0
    return {"data": data, "msg": None, "error": None}, 200


def create_quizz_model_api(data, raw_payload, data_token):
    """Crea un modelo nuevo en BORRADOR. `name` viene del form validado;
    `template` (obligatorio) y `rubric` (opcional) se toman del payload crudo
    como dicts. La rubrica puede agregarse despues con PUT."""
    user = data_token.get("emp_id")
    name = (data.get("name") or "").strip()
    if not name:
        return {"data": None, "msg": "El nombre del modelo es obligatorio", "error": None}, 400

    template, err = _parse_json_field(raw_payload.get("template"), "template")
    if err:
        return {"data": None, "msg": "Template inválido", "error": [err]}, 400
    errors = _validate_template(template)
    if errors:
        return {"data": None, "msg": "Template inválido", "error": errors}, 400

    rubric = None
    if raw_payload.get("rubric") is not None:
        rubric, err = _parse_json_field(raw_payload.get("rubric"), "rubric")
        if err:
            return {"data": None, "msg": "Rúbrica inválida", "error": [err]}, 400
        errors = _check_rubric(rubric)
        if errors:
            return {"data": None, "msg": "Rúbrica inválida", "error": errors}, 400

    warnings = _cross_warnings(template, rubric) if rubric else []

    history = _append_history([], user, "Creación", f"Creación del modelo '{name}' (borrador).")
    row = {
        "name": name,
        "template": template,
        "rubric": rubric,
        "status": 0,
        "protected": 0,
        "created_by": user,
        "timestamp": _now_ts(),
        "history": history,
    }
    flag, error, type_q = insert_quizz_model(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo crear el modelo de encuesta", "error": error}, 400

    # El type definitivo lo asigna el AUTO_INCREMENT: se sella en la rubrica
    # para que evaluate() reporte el tipo correcto.
    if rubric is not None:
        rubric["type"] = type_q
        update_quizz_model_fields(type_q, {"rubric": rubric}, data_token)

    msg = f"Modelo de encuesta creado en borrador (tipo {type_q}: {name})"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Modelos de encuesta", user or 0, 0)
    write_log_file(log_file_rh, msg, data_token)
    return {
        "data": {"type_q": type_q, "status": 0, "warnings": warnings},
        "msg": msg,
        "error": None,
    }, 201


def update_quizz_model_api(type_q, data, raw_payload, data_token):
    """PUT parcial: solo escribe las llaves presentes en el JSON crudo
    (name/template/rubric). Candados por status: template solo en BORRADOR;
    rubrica editable siempre pero solo se puede QUITAR (null) en borrador.
    El status NO se toca aqui (PUT /status)."""
    user = data_token.get("emp_id")
    if "status" in raw_payload:
        return {
            "data": None,
            "msg": "El status se cambia con PUT /rrhh/quizz/models/<id>/status",
            "error": None,
        }, 400

    flag, error, row = get_quizz_model_db(type_q, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el modelo", "error": error}, 400
    if not row:
        return {"data": None, "msg": f"No existe el modelo de encuesta {type_q}", "error": "No encontrado"}, 404
    current = _row_to_detail(row)
    status = int(current.get("status") or 0)

    updates = {}
    changed = []

    if "name" in raw_payload:
        name = (data.get("name") or "").strip()
        if not name:
            return {"data": None, "msg": "El nombre no puede quedar vacío", "error": None}, 400
        updates["name"] = name
        changed.append("name")

    if "template" in raw_payload:
        if status != 0:
            return {
                "data": None,
                "msg": (
                    f"El template está bloqueado: el modelo {type_q} está en "
                    f"{QM_STATUS.get(status)} y sus respuestas guardadas mapean contra "
                    "este template. Para cambiar preguntas crear un modelo nuevo."
                ),
                "error": None,
            }, 400
        template, err = _parse_json_field(raw_payload.get("template"), "template")
        if err:
            return {"data": None, "msg": "Template inválido", "error": [err]}, 400
        errors = _validate_template(template)
        if errors:
            return {"data": None, "msg": "Template inválido", "error": errors}, 400
        updates["template"] = template
        changed.append("template")

    if "rubric" in raw_payload:
        if raw_payload.get("rubric") is None:
            if status != 0:
                return {
                    "data": None,
                    "msg": (
                        "No se puede quitar la rúbrica de un modelo publicado: su "
                        "historial dejaría de ser evaluable. Solo se permite en borrador."
                    ),
                    "error": None,
                }, 400
            updates["rubric"] = None
            changed.append("rubric (removida)")
        else:
            rubric, err = _parse_json_field(raw_payload.get("rubric"), "rubric")
            if err or rubric is None:
                return {"data": None, "msg": "Rúbrica inválida", "error": [err]}, 400
            errors = _check_rubric(rubric)
            if errors:
                return {"data": None, "msg": "Rúbrica inválida", "error": errors}, 400
            rubric["type"] = int(type_q)
            updates["rubric"] = rubric
            changed.append("rubric")

    if not updates:
        return {
            "data": None,
            "msg": "Nada que actualizar: mandar name, template y/o rubric",
            "error": None,
        }, 400

    effective_template = updates.get("template", current.get("template"))
    effective_rubric = updates.get("rubric", current.get("rubric"))
    warnings = (
        _cross_warnings(effective_template, effective_rubric) if effective_rubric else []
    )

    updates["history"] = _append_history(
        current.get("history"), user, "Actualización",
        f"Actualización de: {', '.join(changed)}.",
    )
    flag, error, _ = update_quizz_model_fields(type_q, updates, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el modelo", "error": error}, 400
    msg = f"Modelo de encuesta {type_q} actualizado ({', '.join(changed)})"
    write_log_file(log_file_rh, msg, data_token)
    return {
        "data": {"type_q": int(type_q), "warnings": warnings},
        "msg": msg,
        "error": None,
    }, 200


def update_quizz_model_status_api(type_q, data, data_token):
    """Transiciones del ciclo de vida: 0->1 (publicar; re-valida template),
    1->2 (archivar), 2->1 (reactivar). Idempotente si ya esta en el status."""
    user = data_token.get("emp_id")
    new_status = data.get("status")
    if new_status not in QM_STATUS:
        return {
            "data": None,
            "msg": f"status invalido: {new_status} (0=borrador 1=activa 2=archivada)",
            "error": None,
        }, 400

    flag, error, row = get_quizz_model_db(type_q, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el modelo", "error": error}, 400
    if not row:
        return {"data": None, "msg": f"No existe el modelo de encuesta {type_q}", "error": "No encontrado"}, 404
    current = _row_to_detail(row)
    status = int(current.get("status") or 0)

    if status == new_status:
        return {
            "data": {"type_q": int(type_q), "status": status},
            "msg": f"El modelo {type_q} ya estaba en {QM_STATUS[status]}",
            "error": None,
        }, 200

    action = QM_TRANSITIONS.get((status, new_status))
    if action is None:
        valid = ", ".join(
            f"{a}->{b}" for (a, b) in QM_TRANSITIONS if a == status
        ) or "ninguna"
        return {
            "data": None,
            "msg": (
                f"Transición inválida {QM_STATUS[status]}->{QM_STATUS[new_status]}. "
                f"Desde {QM_STATUS[status]} solo: {valid}"
            ),
            "error": None,
        }, 400

    if new_status == 1 and status == 0:
        errors = _validate_template(current.get("template"))
        if errors:
            return {
                "data": None,
                "msg": "No se puede publicar: el template no es válido",
                "error": errors,
            }, 400

    history = _append_history(
        current.get("history"), user, action,
        f"{action} del modelo (status {status}->{new_status}).",
    )
    flag, error, _ = update_quizz_model_fields(
        type_q, {"status": new_status, "history": history}, data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo cambiar el status", "error": error}, 400
    msg = f"{action} del modelo de encuesta {type_q} ({current.get('name')})"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Modelos de encuesta", user or 0, 0)
    write_log_file(log_file_rh, msg, data_token)
    return {"data": {"type_q": int(type_q), "status": new_status}, "msg": msg, "error": None}, 200


def delete_quizz_model_api(type_q, data_token):
    """Borrado FISICO. Reglas: protected jamas; con tasks que referencien el
    tipo tampoco (arruinaria la evaluacion on-read de su historial) ->
    archivar en su lugar. Pensado para limpiar modelos creados por error."""
    flag, error, row = get_quizz_model_db(type_q, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el modelo", "error": error}, 400
    if not row:
        return {"data": None, "msg": f"No existe el modelo de encuesta {type_q}", "error": "No encontrado"}, 404
    current = _row_to_detail(row)

    if int(current.get("protected") or 0) == 1:
        return {
            "data": None,
            "msg": (
                f"El modelo {type_q} ({current.get('name')}) está protegido "
                "(instrumento legal): no se puede borrar, solo archivar."
            ),
            "error": None,
        }, 400

    flag, error, counts = count_tasks_by_type_quizz(type_q, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo verificar las tasks del tipo", "error": error}, 400
    total = int(counts[0] or 0) if counts else 0  # pyrefly: ignore
    if total > 0:
        return {
            "data": None,
            "msg": (
                f"El modelo {type_q} tiene {total} encuesta(s) asignadas/contestadas: "
                "no se puede borrar sin perder su historial. Archivar en su lugar "
                "(PUT /status con 2)."
            ),
            "error": None,
        }, 400

    flag, error, rowcount = delete_quizz_model(type_q, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo borrar el modelo", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe el modelo de encuesta {type_q}", "error": "No encontrado"}, 404
    msg = f"Modelo de encuesta {type_q} ({current.get('name')}) borrado"
    write_log_file(log_file_rh, msg, data_token)
    return {"data": {"type_q": int(type_q)}, "msg": msg, "error": None}, 200


def get_quizz_models_catalogs_api():
    def _fmt(catalog):
        return [{"code": code, "label": label} for code, label in catalog.items()]

    data = {
        "status": _fmt(QM_STATUS),
        "widget_types": _fmt(QM_WIDGET_TYPES),
        "response_layouts": [
            {"code": code, "label": label} for code, label in QM_RESPONSE_LAYOUTS.items()
        ],
        "transitions": [
            {"from": a, "to": b, "label": label} for (a, b), label in QM_TRANSITIONS.items()
        ],
        "rules": [
            "BORRADOR (0): todo editable; no aparece para contestar; borrable.",
            "ACTIVA (1): contestable; template bloqueado (crear modelo nuevo para "
            "cambiar preguntas); rubrica y nombre editables.",
            "ARCHIVADA (2): oculta; su historial sigue evaluable; reactivable.",
            "protected=1 (Norma 035): jamas borrable, ni con force.",
            "Borrado fisico solo sin tasks del tipo y sin protected.",
        ],
    }
    return {"data": data, "msg": "ok", "error": None}, 200


def get_quizz_template_api(type_q, data_token):
    """Template para la captura (compat de GET /misc/download/quizz/<type_q>:
    mismo shape de respuesta que cuando leia el archivo). Sirve cualquier
    status: la disponibilidad para contestar la controla create_task."""
    flag, error, row = get_quizz_model_template_db(type_q, data_token)
    if not flag:
        return {"data": None, "msg": "Error al obtener el cuestionario", "error": error}, 400
    if not row:
        return {
            "data": None,
            "msg": f"No existe el cuestionario tipo {type_q}",
            "error": None,
        }, 400
    template = _load_json(row[1], {})  # pyrefly: ignore
    return {"data": template, "msg": None, "error": None}, 200
