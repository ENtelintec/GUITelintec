# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 17/sep./2026  at 12:00 $"

"""CRUD del catalogo de formatos ISO (SGI) sobre sql_telintec_mod_admin.iso_formats.
Ver Docs/iso_formats_crud.md.

Reglas:
  * (code, revision) unico (UNIQUE de la tabla) -> 409.
  * La revision se sube EN LA MISMA FILA (PUT con revision nueva + emission_date);
    la anterior queda en history. Nunca una fila nueva por revision: los ids 1..8
    estan atados por codigo a los PDFs (iso_form).
  * config: NULL para formatos solo-PDF; con kind "balance_control" se valida la
    estructura {columns[], header_fields[]} que consume MD_BalanceControl. Quitar
    el config a un formato que ya usan controles de saldos -> 400.
  * Baja suave (is_active=0): el formato deja de ofrecerse para controles nuevos
    y los PDFs/controles existentes siguen imprimiendolo. Reactivable.
  * DELETE fisico solo sin controles que lo referencien (FK RESTRICT) y si el id
    no esta atado a un PDF en codigo (ISO_FORM_IDS_IN_CODE).
"""

import functools
import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, log_file_sgi_formats, timezone_software
from templates.controllers.sgi.iso_formats_controller import (
    count_balance_controls_by_format,
    delete_iso_format,
    get_iso_format_by_code_rev,
    get_iso_format_by_id,
    get_iso_formats_filtered,
    insert_iso_format,
    set_iso_format_active,
    update_iso_format,
)
from templates.forms.PDFGenerator import ISO_FORM_IDS_IN_CODE, invalidate_iso_formats_cache
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.MD_BalanceControl import (
    FORMAT_KIND,
    VALUE_TYPES,
    _format_to_dict,
    _KEY_RE,
    coerce_value,
)

DEPARTMENTS = ("rrhh", "almacen", "presales", "sgi", "administracion", "cda", "sm", "compras")
KINDS = (FORMAT_KIND,)  # kinds con config estructurada; cualquier otro dict se guarda tal cual
_EDITABLE = ("code", "revision", "name", "department", "emission_date", "config")
_ID_KEYS = ("id", "id_format")
_PERM_NOTIFY = ["sgi"]


class _ApiError(Exception):
    def __init__(self, envelope: dict, code: int):
        super().__init__(envelope.get("msg"))
        self.response = (envelope, code)


def _api_guard(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except _ApiError as exc:
            return exc.response
    return wrapper


def _now():
    return datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software))


def _resolve_id(data: dict):
    for key in _ID_KEYS:
        value = data.get(key)
        if value not in (None, "", 0):
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
    return None


def _load_format(id_format, data_token) -> dict:
    flag, error, row = get_iso_format_by_id(id_format, data_token)
    if not flag:
        raise _ApiError({"data": None, "msg": "Error al consultar el formato", "error": error}, 400)
    if row is None:
        raise _ApiError({"data": None, "msg": f"No existe el formato (ID {id_format})", "error": "Formato no encontrado"}, 404)
    return _format_to_dict(row)


def _usage(id_format, data_token) -> dict:
    _flag, _e, (total, active) = count_balance_controls_by_format(id_format, data_token)
    return {"balance_controls": total, "balance_controls_active": active, "bound_to_pdf": id_format in ISO_FORM_IDS_IN_CODE}


# --- Validacion --------------------------------------------------------------------
def _validate_field_list(items, name: str, errors: list, allow_options: bool):
    """Valida columns[] / header_fields[]; devuelve las llaves encontradas."""
    keys = []
    if not isinstance(items, list):
        errors.append(f"config.{name} debe ser una lista")
        return keys
    for i, item in enumerate(items):
        where = f"config.{name}[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{where} debe ser un objeto")
            continue
        key = str(item.get("key") or "").strip()
        if not _KEY_RE.match(key):
            errors.append(f"{where}.key inválida ('{key}'): minúsculas, dígitos y _ (máx. 50, empieza con letra)")
        elif key in keys:
            errors.append(f"{where}.key repetida: '{key}'")
        keys.append(key)
        if not str(item.get("label") or "").strip():
            errors.append(f"{where}.label requerido")
        if item.get("value_type") not in VALUE_TYPES:
            errors.append(f"{where}.value_type debe ser uno de {list(VALUE_TYPES)}")
        for flag_key in ("is_sum", "required"):
            if flag_key in item and not isinstance(item[flag_key], bool):
                errors.append(f"{where}.{flag_key} debe ser true/false")
        if "source_key" in item and item["source_key"] is not None and not isinstance(item["source_key"], str):
            errors.append(f"{where}.source_key debe ser texto")
        if "options" in item and item["options"] is not None:
            if not allow_options:
                errors.append(f"{where}.options solo aplica en header_fields")
            elif not isinstance(item["options"], list) or not all(isinstance(o, str) for o in item["options"]):
                errors.append(f"{where}.options debe ser una lista de textos")
    return keys


def validate_format_config(config) -> list:
    """Errores de estructura del config. None -> formato solo-PDF (valido)."""
    errors: list = []
    if config is None:
        return errors
    if not isinstance(config, dict):
        return ["config debe ser un objeto JSON o null"]
    kind = config.get("kind")
    if kind is not None and not isinstance(kind, str):
        errors.append("config.kind debe ser texto")
    if kind == FORMAT_KIND:
        col_keys = _validate_field_list(config.get("columns", []), "columns", errors, allow_options=False)
        hdr_keys = _validate_field_list(config.get("header_fields", []), "header_fields", errors, allow_options=True)
        dup = sorted(set(col_keys) & set(hdr_keys))
        if dup:
            errors.append(f"llaves repetidas entre columns y header_fields: {dup}")
    return errors


def _validate_base(raw: dict, current: dict | None, errors: list) -> dict:
    """Mezcla el parcial (solo llaves presentes en raw) con la fila actual y valida."""
    out = dict(current or {})
    for key in _EDITABLE:
        if key in raw:
            out[key] = raw[key]
    code = str(out.get("code") or "").strip().upper()
    if not code:
        errors.append("code requerido")
    elif len(code) > 30:
        errors.append("code: máximo 30 caracteres")
    out["code"] = code
    revision = str(out.get("revision") or "R0").strip().upper()
    if len(revision) > 10:
        errors.append("revision: máximo 10 caracteres")
    out["revision"] = revision
    name = str(out.get("name") or "").strip()
    if not name:
        errors.append("name requerido")
    out["name"] = name
    department = out.get("department")
    department = str(department).strip().lower() if department not in (None, "") else None
    if department is not None and department not in DEPARTMENTS:
        errors.append(f"department debe ser uno de {list(DEPARTMENTS)} (o null)")
    out["department"] = department
    ok, emission_date, err = coerce_value(out.get("emission_date"), "date")
    if not ok:
        errors.append(f"emission_date: {err}")
    out["emission_date"] = emission_date
    out["config"] = out.get("config")
    errors.extend(validate_format_config(out["config"]))
    return out


def _check_unique(code: str, revision: str, exclude_id, data_token):
    flag, error, row = get_iso_format_by_code_rev(code, revision, data_token)
    if not flag:
        raise _ApiError({"data": None, "msg": "Error al validar la unicidad del formato", "error": error}, 400)
    if row is not None and int(row[0]) != exclude_id:
        raise _ApiError({
            "data": {"id": int(row[0])},
            "msg": f"Ya existe el formato {code} {revision} (ID {int(row[0])})",
            "error": "code + revision duplicados",
        }, 409)


# --- Lecturas ----------------------------------------------------------------------
def get_iso_formats_catalogs_from_api(_data_token):
    return {
        "data": {
            "departments": list(DEPARTMENTS),
            "value_types": list(VALUE_TYPES),
            "kinds": list(KINDS),
            "ids_bound_to_pdf": sorted(ISO_FORM_IDS_IN_CODE),
            "config_schema": {
                "kind": "balance_control",
                "columns": [{"key": "str", "label": "str", "value_type": "text|number|date|boolean", "source_key": "str?", "is_sum": "bool?"}],
                "header_fields": [{"key": "str", "label": "str", "value_type": "text|number|date|boolean", "required": "bool?", "options": ["str"]}],
            },
        },
        "msg": None,
        "error": None,
    }, 200


def get_iso_formats_from_api(params: dict, data_token):
    only_active = str(params.get("all", "")).strip().lower() not in ("1", "true", "yes")
    department = (params.get("department") or "").strip().lower() or None
    kind = (params.get("kind") or "").strip() or None
    flag, error, rows = get_iso_formats_filtered(data_token, only_active, department, kind)
    if not flag:
        return {"data": [], "msg": "Error al consultar los formatos", "error": error}, 400
    return {"data": [_format_to_dict(r) for r in rows], "msg": None, "error": None}, 200


@_api_guard
def get_iso_format_from_api(id_format: int, data_token):
    fmt = _load_format(id_format, data_token)
    fmt["usage"] = _usage(id_format, data_token)
    return {"data": fmt, "msg": None, "error": None}, 200


# --- Escrituras --------------------------------------------------------------------
@_api_guard
def create_iso_format_from_api(raw: dict, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    errors: list = []
    base = _validate_base(raw or {}, None, errors)
    if errors:
        return {"data": None, "msg": "Formato inválido", "error": errors}, 400
    _check_unique(base["code"], base["revision"], None, data_token)
    base["created_by"] = user
    base["timestamp"] = timestamp
    base["history"] = [{"user": user, "action": "Alta", "date": timestamp, "comment": f"{base['code']} {base['revision']}"}]
    flag, error, new_id = insert_iso_format(base, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo crear el formato", "error": error}, 400
    invalidate_iso_formats_cache()
    msg = f"Formato ISO creado (ID {new_id}, {base['code']} {base['revision']})"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Formatos ISO", user or 0, 0)
    write_log_file(log_file_sgi_formats, msg, data_token)
    return {"data": {"id": new_id, "label": f"{base['code']} {base['revision']}"}, "msg": msg, "error": None}, 201


@_api_guard
def update_iso_format_from_api(raw: dict, data_token):
    """PUT parcial: solo escribe las llaves presentes en el JSON crudo."""
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    raw = raw or {}
    id_format = _resolve_id(raw)
    if not id_format:
        return {"data": None, "msg": "Falta el id del formato", "error": "id requerido"}, 400
    current = _load_format(id_format, data_token)
    present = [k for k in _EDITABLE if k in raw]
    if not present:
        return {"data": None, "msg": "Nada que actualizar", "error": f"manda al menos una de {list(_EDITABLE)}"}, 400
    errors: list = []
    merged = _validate_base(raw, current, errors)
    usage = _usage(id_format, data_token)
    if "config" in raw and raw["config"] is None and current.get("config") is not None and usage["balance_controls"] > 0:
        errors.append(f"no se puede quitar el config: {usage['balance_controls']} control(es) de saldos usan este formato")
    if errors:
        return {"data": None, "msg": "Formato inválido", "error": errors}, 400
    if merged["code"] != current.get("code") or merged["revision"] != current.get("revision"):
        _check_unique(merged["code"], merged["revision"], id_format, data_token)

    changes = []
    for key in present:
        before, after = current.get(key), merged.get(key)
        if before != after:
            changes.append({"field": key, "before": before, "after": after})
    if not changes:
        return {"data": {"id": id_format}, "msg": f"Sin cambios en el formato (ID {id_format})", "error": None}, 200
    history = list(current.get("history") or [])
    is_new_rev = any(c["field"] == "revision" for c in changes)
    history.append({
        "user": user,
        "action": "Nueva revisión" if is_new_rev else "Edición",
        "date": timestamp,
        "comment": "; ".join(f"{c['field']}: {c['before']!r} -> {c['after']!r}" for c in changes if c["field"] != "config")
                   + ("; config actualizado" if any(c["field"] == "config" for c in changes) else ""),
    })
    merged["history"] = history
    flag, error, _ = update_iso_format(id_format, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el formato", "error": error}, 400
    invalidate_iso_formats_cache()
    warnings = []
    if any(c["field"] == "config" for c in changes) and usage["balance_controls"] > 0:
        warnings.append(
            f"{usage['balance_controls']} control(es) de saldos usan este formato: los valores ya capturados en llaves "
            "que se quitaron o cambiaron de tipo no se migran (quedan en extra_info)"
        )
    label = f"{merged['code']} {merged['revision']}"
    msg = f"Formato ISO actualizado (ID {id_format}, {label}): {', '.join(c['field'] for c in changes)}"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Formatos ISO", user or 0, 0)
    write_log_file(log_file_sgi_formats, msg, data_token)
    return {"data": {"id": id_format, "label": label, "changes": changes, "warnings": warnings}, "msg": msg, "error": None}, 200


@_api_guard
def set_iso_format_status_from_api(data: dict, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_format = _resolve_id(data)
    if not id_format:
        return {"data": None, "msg": "Falta el id del formato", "error": "id requerido"}, 400
    is_active = 1 if data.get("is_active") in (1, True, "1", "true") else 0
    current = _load_format(id_format, data_token)
    if int(current.get("is_active") or 0) == is_active:
        state = "vigente" if is_active else "retirado"
        return {"data": {"id": id_format, "is_active": is_active}, "msg": f"El formato ya estaba {state} (ID {id_format})", "error": None}, 200
    history = list(current.get("history") or [])
    history.append({
        "user": user,
        "action": "Reactivación" if is_active else "Baja",
        "date": timestamp,
        "comment": data.get("comment") or "",
    })
    flag, error, _ = set_iso_format_active(id_format, is_active, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo cambiar el estado del formato", "error": error}, 400
    invalidate_iso_formats_cache()
    usage = _usage(id_format, data_token)
    label = f"{current.get('code')} {current.get('revision')}"
    msg = (f"Formato ISO {'reactivado' if is_active else 'retirado'} (ID {id_format}, {label})"
           + (f"; {usage['balance_controls_active']} control(es) activo(s) lo siguen usando" if not is_active and usage["balance_controls_active"] else ""))
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Formatos ISO", user or 0, 0)
    write_log_file(log_file_sgi_formats, msg, data_token)
    return {"data": {"id": id_format, "is_active": is_active, "usage": usage}, "msg": msg, "error": None}, 200


@_api_guard
def delete_iso_format_from_api(data: dict, data_token):
    user = data_token.get("emp_id")
    id_format = _resolve_id(data)
    if not id_format:
        return {"data": None, "msg": "Falta el id del formato", "error": "id requerido"}, 400
    current = _load_format(id_format, data_token)
    usage = _usage(id_format, data_token)
    label = f"{current.get('code')} {current.get('revision')}"
    if usage["bound_to_pdf"]:
        return {
            "data": {"id": id_format, "usage": usage},
            "msg": f"El formato {label} (ID {id_format}) está atado a un PDF del sistema; solo se puede retirar (baja suave)",
            "error": "Formato referenciado por código (iso_form)",
        }, 400
    if usage["balance_controls"] > 0:
        return {
            "data": {"id": id_format, "usage": usage},
            "msg": f"El formato {label} (ID {id_format}) lo usan {usage['balance_controls']} control(es) de saldos; retíralo en vez de borrarlo",
            "error": "Formato referenciado por balance_controls",
        }, 400
    flag, error, rows = delete_iso_format(id_format, data_token)
    if not flag or not rows:
        return {"data": None, "msg": "No se pudo borrar el formato", "error": error or "0 filas"}, 400
    invalidate_iso_formats_cache()
    msg = f"Formato ISO borrado (ID {id_format}, {label})"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Formatos ISO", user or 0, 0)
    write_log_file(log_file_sgi_formats, msg, data_token)
    return {"data": {"id": id_format}, "msg": msg, "error": None}, 200
