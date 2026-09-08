# -*- coding: utf-8 -*-
"""
Multisede de almacén — orquestación del lado PRINCIPAL (rutas en rs_Almacen.py):
catálogo de sedes (F1), inventario consolidado (F1), traslados (F3). El lado
sede vive en MD_Sucursal.py (F2). Plan: docs/almacen_multisede_plan.md.

Reglas:
  * Exactamente una sede con is_main=1 (nace del seed); la API no crea ni
    desactiva principales.
  * Baja de sede = suave (is_active=0); no hay DELETE físico.
  * `extra_info` se MERGEA por llaves presentes (no se pisa entera).
"""
__author__ = "Edisson Naula"
__date__ = "$ 07/sep./2026  at 12:00 $"

import json
from datetime import date, datetime

import pytz

from static.constants import format_timestamps, log_file_almacen, timezone_software
from templates.controllers.product.warehouses_controller import (
    CONSOLIDATED_COLUMNS,
    WAREHOUSE_COLUMNS,
    get_consolidated_stock_db,
    get_warehouse_db,
    get_warehouses_db,
    insert_warehouse_db,
    update_warehouse_fields_db,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file

# --- Catálogos (código -> etiqueta). Los expone GET /almacen/warehouses/catalogs.
WH_TRANSFER_STATUS = {
    0: "EN TRÁNSITO",
    1: "RECIBIDO",
    2: "RECIBIDO CON DIFERENCIAS",
    3: "CANCELADO",
}

_PERMISSIONS = ["almacen"]


# --- Helpers -----------------------------------------------------------------
def _now_ts():
    timezone = pytz.timezone(timezone_software)
    return datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)


def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _load_json(value, default):
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


def _row_to_warehouse(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(WAREHOUSE_COLUMNS, row)}
    data["is_main"] = int(data.get("is_main") or 0)
    data["is_active"] = int(data.get("is_active") or 0)
    data["extra_info"] = _load_json(data.get("extra_info"), {})
    data["history"] = _load_json(data.get("history"), [])
    return data


def _append_history(history, user, action, comment):
    history = history if isinstance(history, list) else []
    history.append(
        {"timestamp": _now_ts(), "user": user, "action": action, "comment": comment}
    )
    return history


def _load_warehouse(id_warehouse, data_token):
    """-> (dict | None, envelope de error | None, code)."""
    flag, error, row = get_warehouse_db(id_warehouse, data_token)
    if not flag:
        return None, {"data": None, "msg": "Error al consultar la sede", "error": error}, 400
    if not row:
        return None, {"data": None, "msg": f"No existe la sede {id_warehouse}", "error": "No encontrado"}, 404
    return _row_to_warehouse(row), None, 200


def verify_warehouse_permission(data_token, id_warehouse) -> bool:
    """Un usuario de sede opera SOLO su sede: su permiso es
    `App.Department.Sucursal-<id>`. Match exacto del sufijo numérico (el
    match substring de verify_department_permission solo abre la puerta al
    namespace `sucursal`; aquí se valida el id). 'administrator' pasa siempre
    (mismo criterio que el resto del API)."""
    try:
        wanted = int(id_warehouse)
    except (TypeError, ValueError):
        return False
    permissions = (data_token or {}).get("permissions", {}) or {}
    for item in permissions.values():
        name = str(item).lower()
        if "administrator" in name:
            return True
        suffix = name.rsplit("sucursal-", 1)
        if len(suffix) == 2 and suffix[1].isdigit() and int(suffix[1]) == wanted:
            return True
    return False


# --- Catálogo de sedes -------------------------------------------------------
def fetch_warehouses_api(params, data_token):
    """GET /almacen/warehouses. Default: solo activas; ?all=1 -> todas."""
    include_all = str(params.get("all") or "").strip().lower() in ("1", "true", "yes")
    only_active = None if include_all else 1
    flag, error, rows = get_warehouses_db(only_active, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar las sedes", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_row_to_warehouse(r) for r in rows]
    return {"data": data_out, "msg": f"{len(data_out)} sedes", "error": None}, 200


def get_warehouse_api(id_warehouse, data_token):
    """GET /almacen/warehouse/<id>."""
    current, err, code = _load_warehouse(id_warehouse, data_token)
    if current is None:
        return err, code
    return {"data": current, "msg": None, "error": None}, 200


def create_warehouse_api(data, raw_payload, data_token):
    """POST /almacen/warehouse: alta de sede SECUNDARIA (is_main=0 siempre).
    `extra_info` (dict libre: address, manager, phone...) del payload crudo."""
    user = data_token.get("emp_id")
    name = (data.get("name") or "").strip()
    if not name:
        return {"data": None, "msg": "El nombre de la sede es obligatorio", "error": None}, 400
    extra_info = raw_payload.get("extra_info")
    if extra_info is not None and not isinstance(extra_info, dict):
        return {"data": None, "msg": "extra_info debe ser un objeto JSON", "error": None}, 400
    if raw_payload.get("is_main"):
        return {
            "data": None,
            "msg": "No se puede crear otra sede principal: el principal es único (seed)",
            "error": None,
        }, 400
    row = {
        "name": name,
        "extra_info": extra_info or {},
        "history": _append_history([], user, "Creación", f"Alta de la sede '{name}'."),
    }
    flag, error, id_warehouse = insert_warehouse_db(row, data_token)
    if not flag:
        msg = "No se pudo crear la sede"
        if "Duplicate entry" in error:
            msg = f"Ya existe una sede con el nombre '{name}'"
        return {"data": None, "msg": msg, "error": error}, 400
    msg = f"Sede {id_warehouse} ({name}) creada"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Sedes de almacén", user or 0, 0)
    write_log_file(log_file_almacen, msg, data_token)
    return {"data": {"id_warehouse": id_warehouse, "name": name}, "msg": msg, "error": None}, 201


def update_warehouse_api(data, raw_payload, data_token):
    """PUT /almacen/warehouse: parcial (solo llaves presentes en el JSON
    crudo): name, is_active (0 = baja suave, 1 = reactivar), extra_info
    (merge por llave; null en una llave la quita). El principal no se
    desactiva ni se renombra a vacío."""
    user = data_token.get("emp_id")
    id_warehouse = data.get("id_warehouse")
    current, err, code = _load_warehouse(id_warehouse, data_token)
    if current is None:
        return err, code

    updates = {}
    changed = []
    if "name" in raw_payload:
        name = (data.get("name") or "").strip()
        if not name:
            return {"data": None, "msg": "El nombre no puede quedar vacío", "error": None}, 400
        if name != current.get("name"):
            updates["name"] = name
            changed.append(f"name '{current.get('name')}' -> '{name}'")
    if "is_active" in raw_payload:
        is_active = raw_payload.get("is_active")
        if is_active not in (0, 1, True, False):
            return {"data": None, "msg": "is_active debe ser 0 o 1", "error": None}, 400
        is_active = int(bool(is_active))
        if is_active == 0 and current.get("is_main") == 1:
            return {
                "data": None,
                "msg": "La sede principal no se puede dar de baja",
                "error": None,
            }, 400
        if is_active != current.get("is_active"):
            updates["is_active"] = is_active
            changed.append("baja" if is_active == 0 else "reactivación")
    if "extra_info" in raw_payload:
        patch = raw_payload.get("extra_info")
        if patch is not None and not isinstance(patch, dict):
            return {"data": None, "msg": "extra_info debe ser un objeto JSON", "error": None}, 400
        merged = dict(current.get("extra_info") or {})
        for key, value in (patch or {}).items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = value
        if patch and "placeholder" not in patch:
            merged["placeholder"] = False  # capturar datos reales limpia el placeholder del seed
        if merged != current.get("extra_info"):
            updates["extra_info"] = merged
            changed.append(f"extra_info ({', '.join((patch or {}).keys())})")
    if "is_main" in raw_payload:
        return {"data": None, "msg": "is_main no se edita por API", "error": None}, 400

    if not updates:
        return {
            "data": {"id_warehouse": int(id_warehouse)},
            "msg": "Sin cambios",
            "error": None,
        }, 200
    updates["history"] = _append_history(
        current.get("history"), user, "Actualización", f"Actualización de: {'; '.join(changed)}."
    )
    flag, error, _ = update_warehouse_fields_db(id_warehouse, updates, data_token)
    if not flag:
        msg = "No se pudo actualizar la sede"
        if "Duplicate entry" in error:
            msg = f"Ya existe una sede con el nombre '{updates.get('name')}'"
        return {"data": None, "msg": msg, "error": error}, 400
    msg = f"Sede {id_warehouse} ({updates.get('name', current.get('name'))}) actualizada: {'; '.join(changed)}"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Sedes de almacén", user or 0, 0)
    write_log_file(log_file_almacen, msg, data_token)
    return {"data": {"id_warehouse": int(id_warehouse)}, "msg": msg, "error": None}, 200


def get_multisede_catalogs_api():
    """GET /almacen/warehouses/catalogs."""
    data = {
        "transfer_status": [{"code": c, "label": l} for c, l in WH_TRANSFER_STATUS.items()],
        "rules": [
            "products_amc.stock es el stock de la sede principal; las sedes secundarias llevan el suyo en warehouse_stock_amc.",
            "El catalogo de productos es compartido: una sede no crea productos.",
            "Kardex unico: id_warehouse NULL = principal; las pantallas actuales de almacen solo muestran el principal.",
            "Traslado = dos pasos: el principal registra el envio (descuenta su stock) y la sede confirma lo recibido (una sola vez).",
            "Las diferencias de un traslado no se ajustan solas: el principal las resuelve a mano.",
            "Baja de sede = suave (is_active 0); la principal no se da de baja.",
            "Permiso de sede: App.Department.Sucursal-<id_warehouse>.",
        ],
    }
    return {"data": data, "msg": "ok", "error": None}, 200


# --- Inventario consolidado --------------------------------------------------
def get_consolidated_inventory_api(params, data_token):
    """GET /almacen/inventory/consolidated?search=&only_multisede=1. Por
    producto: stock del principal, por sede secundaria, en tránsito y total."""
    search = (params.get("search") or "").strip() or None
    only_multisede = (
        1 if str(params.get("only_multisede") or "").strip().lower() in ("1", "true", "yes") else None
    )
    flag, error, rows = get_consolidated_stock_db(search, only_multisede, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el inventario consolidado", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = []
    for row in rows:
        item = dict(zip(CONSOLIDATED_COLUMNS, row))
        by_warehouse = _load_json(item.get("by_warehouse"), []) or []
        stock_main = float(item.get("stock_main") or 0)
        for entry in by_warehouse:
            entry["stock"] = float(entry.get("stock") or 0)
        in_transit = float(item.get("in_transit") or 0)
        stock_sedes = sum(e["stock"] for e in by_warehouse)
        data_out.append(
            {
                "id_product": item["id_product"],
                "sku": item["sku"],
                "name": item["name"],
                "udm": item["udm"],
                "stock_main": stock_main,
                "by_warehouse": by_warehouse,
                "stock_sedes": stock_sedes,
                "in_transit": in_transit,
                "stock_total": stock_main + stock_sedes + in_transit,
            }
        )
    return {"data": data_out, "msg": f"{len(data_out)} productos", "error": None}, 200
