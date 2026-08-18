# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 24/jul./2026  at 12:00 $"

import json
from datetime import date, datetime
from decimal import Decimal

import pytz

from static.constants import (
    format_timestamps,
    log_file_admin_collecions,
    timezone_software,
)
from templates.controllers.purchases.purchase_management_controller import (
    SELECT_COLUMNS,
    delete_purchase_management,
    get_purchase_management_by_id,
    get_purchase_management_list,
    insert_purchase_management,
    set_active_purchase_management,
    update_purchase_management,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file

# --- Catalogos (codigo -> etiqueta). El GET /catalogs los expone al front. ----
PM_CLASSIFICATION = {
    0: "HERRAMIENTAS",
    1: "EPP",
    2: "INVERSION",
    3: "GASTOS",
    4: "REEMBOLSO",
    5: "CREDITO",
    6: "VIATICOS",
}
PM_STATUS = {
    0: "PENDIENTE",
    1: "PAGADO",
    2: "URGENTE",
    3: "POR_PAGAR",
    4: "PUEDE_ESPERAR",
}
PM_DEBT_TYPE = {
    0: "DEUDA",
    1: "GASTO",
    2: "INVERSION",
}

# Llaves que viven en extra_info (texto crudo cuando no hay FK / campos sueltos).
# payload_key -> llave canonica. Aqui coinciden 1:1.
PM_EXTRA_KEY_MAP = {
    "supplier_text": "supplier_text",
    "client_text": "client_text",
    "contract_text": "contract_text",
    "department_text": "department_text",
    "requester_text": "requester_text",
    "invoice_number": "invoice_number",
    "income_date": "income_date",
    "bank_deposit": "bank_deposit",
}

# Columnas base que un PUT puede sobreescribir (sin history/extra_info/timestamp).
_BASE_UPDATE_COLS = (
    "request_date",
    "description",
    "classification",
    "supplier_id",
    "client_id",
    "contract_id",
    "po_id",
    "amount_usd",
    "amount_mxn",
    "status",
    "payment_date",
    "approved",
    "approval_date",
    "comments",
    "debt_type",
    "profit_percentage",
    "cost_ternium_iva",
    "profit",
)

_PERMISSIONS = ["administracion", "purchases"]


# --- Helpers ------------------------------------------------------------------
def _now(timezone):
    return datetime.now(pytz.utc).astimezone(timezone)


def _json_safe(value):
    """Coerciona tipos del driver (date/datetime/Decimal) a algo serializable."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _load_json(value, default):
    """extra_info/history llegan como dict/list (ya parseado) o str (fetch)."""
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        parsed = json.loads(value)
        return parsed
    except (ValueError, TypeError):
        return default


def _extra_info_updates(payload: dict, raw_payload: dict | None, key_map: dict) -> dict:
    """Llaves de extra_info a escribir. Con raw_payload (PUT) solo las presentes
    en el JSON crudo; sin el (POST) todas las del modulo."""
    updates = {}
    for payload_key, canonical_key in key_map.items():
        if raw_payload is not None and payload_key not in raw_payload:
            continue
        updates[canonical_key] = payload.get(payload_key)
    return updates


def _row_to_dict(row) -> dict:
    """Tupla del SELECT -> dict aplanado y JSON-safe para el front."""
    data = {col: _json_safe(val) for col, val in zip(SELECT_COLUMNS, row)}
    data["history"] = _load_json(data.get("history"), [])
    extra = _load_json(data.get("extra_info"), {})
    extra = extra if isinstance(extra, dict) else {}
    data["extra_info"] = extra
    # Aplana las llaves de texto de extra_info al nivel superior (comodidad front).
    for canonical in PM_EXTRA_KEY_MAP.values():
        data[canonical] = extra.get(canonical)
    return data


def _validate_enums(payload: dict, raw_payload: dict | None = None):
    """Valida los tres enteros contra su catalogo. Devuelve lista de errores o None.
    Con raw_payload solo valida las llaves presentes en el JSON crudo."""
    errors = []
    checks = (
        ("classification", PM_CLASSIFICATION),
        ("status", PM_STATUS),
        ("debt_type", PM_DEBT_TYPE),
    )
    for key, catalog in checks:
        if raw_payload is not None and key not in raw_payload:
            continue
        value = payload.get(key)
        if value is None:
            continue
        if value not in catalog:
            errors.append(f"{key}={value} no es un valor valido {sorted(catalog.keys())}")
    return errors or None


def _to_int_or_none(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _resolve_id(data: dict):
    return data.get("id_pm") if data.get("id_pm") else data.get("id")


# --- CRUD ---------------------------------------------------------------------
def create_purchase_management_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    now = _now(timezone)
    timestamp = now.strftime(format_timestamps)
    user = data_token.get("emp_id")

    errors = _validate_enums(data)
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400

    approved = int(data.get("approved") or 0)
    approval_date = data.get("approval_date")
    if approved == 1 and not approval_date:
        approval_date = now.strftime("%Y-%m-%d")

    history = [{
        "user": user,
        "action": "Creación",
        "date": timestamp,
        "comment": "Creación de registro de gestión de compras.",
    }]
    extra_info = _extra_info_updates(data, None, PM_EXTRA_KEY_MAP)

    row = {
        "timestamp": timestamp,
        "created_by": user,
        "request_date": data.get("request_date"),
        "description": data.get("description"),
        "classification": data.get("classification"),
        "supplier_id": data.get("supplier_id"),
        "client_id": data.get("client_id"),
        "contract_id": data.get("contract_id"),
        "po_id": data.get("po_id"),
        "amount_usd": data.get("amount_usd"),
        "amount_mxn": data.get("amount_mxn"),
        "status": int(data.get("status") or 0),
        "payment_date": data.get("payment_date"),
        "approved": approved,
        "approval_date": approval_date,
        "comments": data.get("comments"),
        "debt_type": data.get("debt_type"),
        "profit_percentage": data.get("profit_percentage"),
        "cost_ternium_iva": data.get("cost_ternium_iva"),
        "profit": data.get("profit"),
        "is_active": 1,
        "history": history,
        "extra_info": extra_info,
    }
    flag, error, id_pm = insert_purchase_management(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo crear el registro de gestión de compras", "error": error}, 400
    msg = f"Registro de gestión de compras creado correctamente (ID {id_pm})"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Gestión de compras", user or 0, 0)
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_pm": id_pm}, "msg": msg, "error": None}, 201


def update_purchase_management_api(data, data_token, raw_payload):
    timezone = pytz.timezone(timezone_software)
    now = _now(timezone)
    timestamp = now.strftime(format_timestamps)
    user = data_token.get("emp_id")

    id_pm = _resolve_id(data)
    if not id_pm:
        return {"data": None, "msg": "Falta el id del registro", "error": "id_pm requerido"}, 400

    errors = _validate_enums(data, raw_payload)
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400

    flag, error, existing = get_purchase_management_by_id(id_pm, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el registro", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe el registro (ID {id_pm})", "error": "No encontrado"}, 404
    current = _row_to_dict(existing)

    # Merge parcial: se sobreescribe solo lo presente en el JSON crudo; el resto
    # conserva el valor actual (edicion tipo celda, no reemplazo total).
    merged = {}
    for col in _BASE_UPDATE_COLS:
        merged[col] = data.get(col) if col in raw_payload else current.get(col)

    approved = int(merged.get("approved") or 0)
    if approved == 1 and not merged.get("approval_date"):
        merged["approval_date"] = now.strftime("%Y-%m-%d")
    merged["approved"] = approved

    extra_info = dict(current.get("extra_info") or {})
    extra_info.update(_extra_info_updates(data, raw_payload, PM_EXTRA_KEY_MAP))
    merged["extra_info"] = extra_info

    history = current.get("history") or []
    history.append({
        "user": user,
        "action": "Actualización",
        "date": timestamp,
        "comment": "Actualización de registro de gestión de compras.",
    })
    merged["history"] = history

    flag, error, _ = update_purchase_management(id_pm, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el registro", "error": error}, 400
    msg = f"Registro de gestión de compras actualizado correctamente (ID {id_pm})"
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_pm": id_pm}, "msg": msg, "error": None}, 200


def cancel_purchase_management_api(data, data_token):
    """Cancelacion suave: is_active=0. Recuperable, oculta de los listados activos."""
    timezone = pytz.timezone(timezone_software)
    timestamp = _now(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id")

    id_pm = _resolve_id(data)
    if not id_pm:
        return {"data": None, "msg": "Falta el id del registro", "error": "id_pm requerido"}, 400

    flag, error, existing = get_purchase_management_by_id(id_pm, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el registro", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe el registro (ID {id_pm})", "error": "No encontrado"}, 404
    current = _row_to_dict(existing)
    if int(current.get("is_active") or 0) == 0:
        return {"data": {"id_pm": id_pm}, "msg": f"El registro ya estaba cancelado (ID {id_pm})", "error": None}, 200

    history = current.get("history") or []
    history.append({
        "user": user,
        "action": "Cancelación",
        "date": timestamp,
        "comment": data.get("comment") or "Cancelación del registro.",
    })
    flag, error, _ = set_active_purchase_management(id_pm, 0, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo cancelar el registro", "error": error}, 400
    msg = f"Registro de gestión de compras cancelado (ID {id_pm})"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Gestión de compras", user or 0, 0)
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_pm": id_pm}, "msg": msg, "error": None}, 200


def delete_purchase_management_api(data, data_token):
    """Borrado fisico. Irreversible; para ocultar sin perder usar cancel."""
    id_pm = _resolve_id(data)
    if not id_pm:
        return {"data": None, "msg": "Falta el id del registro", "error": "id_pm requerido"}, 400

    flag, error, rowcount = delete_purchase_management(id_pm, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo eliminar el registro", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe el registro (ID {id_pm})", "error": "No encontrado"}, 404
    msg = f"Registro de gestión de compras eliminado (ID {id_pm})"
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_pm": id_pm}, "msg": msg, "error": None}, 200


def fetch_purchase_management(params, data_token):
    status = _to_int_or_none(params.get("status"))
    classification = _to_int_or_none(params.get("classification"))
    client_id = _to_int_or_none(params.get("client_id"))
    date_from = params.get("date_from") or None
    date_to = params.get("date_to") or None

    # is_active: por defecto solo activos (1). all=1 -> todos (None).
    # is_active=0 -> solo cancelados.
    is_active_param = params.get("is_active")
    include_all = str(params.get("all") or "").strip().lower() in ("1", "true", "yes")
    if is_active_param is not None and str(is_active_param).strip() != "":
        is_active = _to_int_or_none(is_active_param)
    elif include_all:
        is_active = None
    else:
        is_active = 1

    flag, error, rows = get_purchase_management_list(
        status, classification, client_id, date_from, date_to, is_active, data_token
    )
    if not flag:
        return {"data": None, "msg": "Error al consultar gestión de compras", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_row_to_dict(r) for r in rows]
    return {"data": data_out, "msg": f"{len(data_out)} registros", "error": None}, 200


def get_purchase_management_detail_api(id_pm, data_token):
    flag, error, row = get_purchase_management_by_id(id_pm, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el registro", "error": error}, 400
    if not row:
        return {"data": None, "msg": f"No existe el registro (ID {id_pm})", "error": "No encontrado"}, 404
    return {"data": _row_to_dict(row), "msg": "ok", "error": None}, 200


def get_purchase_management_catalogs():
    def _fmt(catalog):
        return [{"code": code, "label": label} for code, label in catalog.items()]

    data = {
        "classification": _fmt(PM_CLASSIFICATION),
        "status": _fmt(PM_STATUS),
        "debt_type": _fmt(PM_DEBT_TYPE),
    }
    return {"data": data, "msg": "ok", "error": None}, 200
