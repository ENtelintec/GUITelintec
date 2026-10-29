# -*- coding: utf-8 -*-
"""
Multisede de almacén — orquestación del lado PRINCIPAL (rutas en rs_Almacen.py):
catálogo de sedes (F1), inventario consolidado (F1), traslados (F3: crear,
cancelar, listar, detalle; resolver diferencias: docs/almacen_multisede_resolve.md).
El lado sede vive en MD_Sucursal.py (F2 movimientos, F3 recepción).
Plan: docs/almacen_multisede_plan.md.

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
from templates.controllers.product.movements_controller import delete_movement_db
from templates.controllers.product.products_controller import update_stock_db
from templates.controllers.product.warehouses_controller import (
    CONSOLIDATED_COLUMNS,
    TRANSFER_COLUMNS,
    WAREHOUSE_COLUMNS,
    delete_transfer_db,
    get_consolidated_stock_db,
    get_main_warehouse_db,
    get_next_transfer_folio_db,
    get_product_stock_and_reserved_db,
    get_products_brief_db,
    get_transfer_db,
    get_transfers_db,
    get_warehouse_db,
    get_warehouses_db,
    insert_transfer_db,
    insert_warehouse_db,
    insert_warehouse_movement_db,
    update_transfer_fields_db,
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
    4: "DIFERENCIA RESUELTA",  # el principal ya resolvió cada faltante (reingreso | merma)
}
# Status en los que la sede ya confirmó: items.quantity_received tiene valor.
_RECEIVED_STATUSES = (1, 2, 4)
# Acciones para resolver un faltante (PUT /almacen/transfer/<id>/resolve).
RESOLVE_ACTIONS = ("reingreso", "merma")
TRANSFERS_DEFAULT_LIMIT = 200
TRANSFERS_MAX_LIMIT = 2000

_PERMISSIONS = ["almacen"]


# --- Helpers -----------------------------------------------------------------
def _now_ts():
    timezone = pytz.timezone(timezone_software)
    return datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)


def _json_safe(value):
    """datetime -> format_timestamps (con espacio, nunca la 'T' de isoformat);
    date -> YYYY-MM-DD. Lo comparten sedes, traslados y movimientos de sede."""
    if isinstance(value, datetime):
        return value.strftime(format_timestamps)
    if isinstance(value, date):
        return value.isoformat()
    return value


def _clean_udm(value):
    """products_amc.udm trae espacios al final ('PIEZA '): se entrega sin ellos."""
    return value.strip() if isinstance(value, str) else value


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
    """GET /almacen/inventory/consolidated?search=&only_multisede=1&all=1. Por
    producto: stock del principal, por sede secundaria, en tránsito y total.
    Sin `search` ni `all=1` aplica only_multisede (P-203, 2026-10-28): el
    catálogo completo con sus dos subconsultas por producto solo a pedido."""
    truthy = ("1", "true", "yes")
    search = (params.get("search") or "").strip() or None
    explicit = str(params.get("only_multisede") or "").strip().lower() in truthy
    full = str(params.get("all") or "").strip().lower() in truthy
    only_multisede = 1 if explicit or (search is None and not full) else None
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
    scope = " (solo con stock en sedes o en tránsito)" if only_multisede else ""
    return {"data": data_out, "msg": f"{len(data_out)} productos{scope}", "error": None}, 200


# =============================================================================
# Traslados principal -> sede (F3). docs/almacen_multisede_f3.md
#
# Crear: valida stock DISPONIBLE del principal (stock - reservado) por item ->
# inserta el traslado (status 0) -> una SALIDA por item en el kardex del
# principal (id_warehouse NULL, extra_info {reference: folio, id_transfer})
# -> descuenta products_amc.stock. Sin transacciones: si algo falla a la
# mitad se revierte best-effort (movimientos borrados, stock reintegrado,
# traslado borrado) y se responde 400.
# Cancelar: solo en tránsito -> ENTRADA de reversa por item + reintegro, status 3.
# Recibir: lo hace la sede (MD_Sucursal.receive_transfer_api).
# =============================================================================
def _row_to_transfer(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(TRANSFER_COLUMNS, row)}
    items_raw = _load_json(data.get("items"), [])
    data["items"] = items_raw if isinstance(items_raw, list) else []
    data["history"] = _load_json(data.get("history"), [])
    data["status"] = int(data.get("status") or 0)
    data["status_label"] = WH_TRANSFER_STATUS.get(data["status"], str(data["status"]))
    return data


def _enrich_transfer_items(transfer: dict, data_token) -> dict:
    """Agrega sku/name/udm a cada item (desde products_amc) y calcula
    `difference` = recibido - enviado (None hasta recibir) y los totales."""
    items = transfer.get("items") or []
    flag, _, rows = get_products_brief_db([i.get("id_product") for i in items], data_token)
    brief = {}
    if flag and isinstance(rows, list):
        for row in rows:
            brief[int(row[0])] = {"sku": row[1], "name": row[2], "udm": _clean_udm(row[3])}
    total_sent = total_received = 0.0
    with_diff = resolved = 0
    enriched = []
    for item in items:
        pid = item.get("id_product")
        info = brief.get(int(pid), {}) if pid is not None else {}
        sent = float(item.get("quantity_sent") or 0)
        received = item.get("quantity_received")
        received_f = float(received) if received is not None else None
        difference = (received_f - sent) if received_f is not None else None
        if difference:
            with_diff += 1
        resolution = item.get("resolution") if isinstance(item.get("resolution"), dict) else None
        if resolution is not None:
            resolved += 1
        total_sent += sent
        total_received += received_f or 0
        enriched.append(
            {
                "id_product": pid,
                "sku": info.get("sku"),
                "name": info.get("name"),
                "udm": info.get("udm"),
                "quantity_sent": sent,
                "quantity_received": received_f,
                "difference": difference,
                "comment": item.get("comment") or "",
                "receive_comment": item.get("receive_comment") or "",
                # {action, quantity, comment, movement_id, user, timestamp} al resolver; None si no aplica
                "resolution": resolution,
            }
        )
    transfer["items"] = enriched
    transfer["totals"] = {
        "items": len(enriched),
        "quantity_sent": total_sent,
        "quantity_received": total_received if transfer.get("status") in _RECEIVED_STATUSES else None,
        "items_with_difference": with_diff,
        "items_resolved": resolved,
    }
    return transfer


def _load_transfer(id_transfer, data_token):
    """-> (dict | None, envelope | None, code)."""
    flag, error, row = get_transfer_db(id_transfer, data_token)
    if not flag:
        return None, {"data": None, "msg": "Error al consultar el traslado", "error": error}, 400
    if not row:
        return None, {"data": None, "msg": f"No existe el traslado {id_transfer}", "error": "No encontrado"}, 404
    return _row_to_transfer(row), None, 200


def _parse_transfer_items(raw_items):
    """Valida la lista de items del POST: [{id_product, quantity, comment?}].
    -> (items normalizados, error | None). Sin productos repetidos."""
    if not isinstance(raw_items, list) or not raw_items:
        return None, "items debe ser una lista con al menos un producto"
    items, seen = [], set()
    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            return None, f"items[{idx}] debe ser un objeto {{id_product, quantity, comment?}}"
        pid_raw, qty_raw = raw.get("id_product"), raw.get("quantity")
        if pid_raw is None or qty_raw is None:
            return None, f"items[{idx}]: id_product y quantity son obligatorios"
        try:
            pid = int(pid_raw)
            qty = float(qty_raw)
        except (TypeError, ValueError):
            return None, f"items[{idx}]: id_product y quantity deben ser numéricos"
        if qty <= 0:
            return None, f"items[{idx}] (producto {pid}): quantity debe ser mayor que 0"
        if pid in seen:
            return None, f"El producto {pid} viene repetido: junta la cantidad en un solo item"
        seen.add(pid)
        items.append({"id_product": pid, "quantity": qty, "comment": str(raw.get("comment") or "").strip()})
    return items, None


def _next_folio(data_token):
    flag, error, row = get_next_transfer_folio_db(data_token)
    if not flag:
        return None, error
    last = int(row[0]) if row and row[0] is not None else 0  # pyrefly: ignore
    return f"TRS-{last + 1:04d}", None


def create_transfer_api(data, raw_payload, data_token):
    """POST /almacen/transfer. Body {id_warehouse_dest, items:[{id_product,
    quantity, comment?}], comment?}. v1: el origen es siempre la sede
    principal. 201 con folio, ids de movimientos y stock resultante."""
    user = data_token.get("emp_id")
    items, err = _parse_transfer_items(raw_payload.get("items"))
    if items is None:
        return {"data": None, "msg": err, "error": None}, 400
    flag, error, main_row = get_main_warehouse_db(data_token)
    if not flag or not main_row:
        return {"data": None, "msg": "No hay sede principal configurada (seed)", "error": error}, 400
    origin = _row_to_warehouse(main_row)
    requested_origin = raw_payload.get("id_warehouse_origin")
    if requested_origin not in (None, "") and int(requested_origin) != origin["id_warehouse"]:
        return {
            "data": None,
            "msg": "v1: los traslados solo salen de la sede principal",
            "error": None,
        }, 400
    dest, err_env, code = _load_warehouse(data.get("id_warehouse_dest"), data_token)
    if dest is None:
        return err_env, code
    if dest["id_warehouse"] == origin["id_warehouse"] or dest.get("is_main") == 1:
        return {"data": None, "msg": "El destino debe ser una sede secundaria", "error": None}, 400
    if dest.get("is_active") != 1:
        return {"data": None, "msg": f"La sede {dest['id_warehouse']} ({dest['name']}) está dada de baja", "error": None}, 400

    # Validación de stock disponible del principal (stock - reservado) por item.
    products = {}
    shortages = []
    for item in items:
        flag, error, row = get_product_stock_and_reserved_db(item["id_product"], data_token)
        if not flag:
            return {"data": None, "msg": "Error al consultar el stock del principal", "error": error}, 400
        if not row:
            return {"data": None, "msg": f"No existe el producto {item['id_product']}", "error": "No encontrado"}, 404
        name, stock, reserved = row[0], float(row[1] or 0), float(row[2] or 0)  # pyrefly: ignore
        available = stock - reserved
        products[item["id_product"]] = {"name": name, "stock": stock, "reserved": reserved, "available": available}
        if item["quantity"] > available:
            shortages.append(
                f"{name} (producto {item['id_product']}): disponible {available:g} "
                f"(stock {stock:g} - reservado {reserved:g}), se piden {item['quantity']:g}"
            )
    if shortages:
        return {
            "data": None,
            "msg": "Stock insuficiente en el principal: " + "; ".join(shortages),
            "error": shortages,
        }, 400

    folio, error = _next_folio(data_token)
    if folio is None:
        return {"data": None, "msg": "No se pudo generar el folio del traslado", "error": error}, 400
    comment = str(data.get("comment") or "").strip()
    now = _now_ts()
    transfer_items = [
        {"id_product": i["id_product"], "quantity_sent": i["quantity"], "quantity_received": None, "comment": i["comment"]}
        for i in items
    ]
    history = [
        {
            "timestamp": now,
            "user": user,
            "action": "Envío",
            "comment": f"Traslado {folio} creado hacia {dest['name']}: {len(items)} item(s).",
        }
    ]
    flag, error, id_transfer = insert_transfer_db(
        {
            "folio": folio,
            "id_warehouse_origin": origin["id_warehouse"],
            "id_warehouse_dest": dest["id_warehouse"],
            "items": transfer_items,
            "comment": comment,
            "history": history,
            "created_by": user,
        },
        data_token,
    )
    if not flag:
        msg = "No se pudo crear el traslado"
        if "Duplicate entry" in error:
            msg = f"El folio {folio} ya existe (concurrencia): reintenta"
        return {"data": None, "msg": msg, "error": error}, 400

    # Salidas del principal + descuento de stock, con reversa best-effort.
    done = []  # [(id_movement, id_product, quantity, stock_descontado)]
    failure = None
    for item in items:
        extra_info = {
            "reference": folio,
            "id_transfer": id_transfer,
            "comment": item["comment"],
            "user": user,
        }
        flag, error, id_movement = insert_warehouse_movement_db(
            None, item["id_product"], "salida", item["quantity"], now, extra_info, data_token
        )
        if not flag:
            failure = f"salida del producto {item['id_product']}: {error}"
            break
        flag, error, _ = update_stock_db(item["id_product"], -item["quantity"], data_token, just_add=True)
        if not flag:
            done.append((id_movement, item["id_product"], item["quantity"], False))
            failure = f"descuento de stock del producto {item['id_product']}: {error}"
            break
        done.append((id_movement, item["id_product"], item["quantity"], True))
    if failure:
        for id_movement, pid, qty, discounted in done:
            delete_movement_db(id_movement, data_token)
            if discounted:
                update_stock_db(pid, qty, data_token, just_add=True)
        delete_transfer_db(id_transfer, data_token)
        msg = f"El traslado {folio} no se pudo completar y se revirtió ({failure})"
        write_log_file(log_file_almacen, msg, data_token)
        return {"data": None, "msg": msg, "error": failure}, 400

    msg = (
        f"Traslado {folio} (id {id_transfer}) enviado a {dest['name']}: "
        + ", ".join(f"{products[i['id_product']]['name']} x{i['quantity']:g}" for i in items)
        + f" [emp {user}]"
    )
    create_notification_permission(
        f"Traslado {folio} en camino desde {origin['name']}: {len(items)} item(s). Confirma la recepción en tu sede.",
        data_token, [f"sucursal-{dest['id_warehouse']}"], "Traslados", user or 0, 0,
    )
    write_log_file(log_file_almacen, msg, data_token)
    return {
        "data": {
            "id_transfer": id_transfer,
            "folio": folio,
            "status": 0,
            "status_label": WH_TRANSFER_STATUS[0],
            "id_warehouse_dest": dest["id_warehouse"],
            "items": [
                {
                    "id_product": i["id_product"],
                    "name": products[i["id_product"]]["name"],
                    "quantity_sent": i["quantity"],
                    "id_movement": mv[0],
                    "stock_main_after": products[i["id_product"]]["stock"] - i["quantity"],
                }
                for i, mv in zip(items, done)
            ],
        },
        "msg": msg,
        "error": None,
    }, 201


def cancel_transfer_api(data, data_token):
    """PUT /almacen/transfer/cancel {id_transfer, reason?}: solo en tránsito.
    Reversa automática al principal (una ENTRADA por item + reintegro de
    stock; el material nunca llegó a la sede) y status 3."""
    user = data_token.get("emp_id")
    transfer, err, code = _load_transfer(data.get("id_transfer"), data_token)
    if transfer is None:
        return err, code
    if transfer["status"] != 0:
        return {
            "data": None,
            "msg": (
                f"El traslado {transfer['folio']} está en {transfer['status_label']}: "
                "solo se cancela en tránsito"
            ),
            "error": None,
        }, 400
    reason = str(data.get("reason") or "").strip()
    now = _now_ts()
    done = []
    failure = None
    for item in transfer["items"]:
        qty = float(item.get("quantity_sent") or 0)
        extra_info = {
            "reference": transfer["folio"],
            "id_transfer": transfer["id_transfer"],
            "comment": f"Reversa por cancelación del traslado{': ' + reason if reason else ''}",
            "user": user,
        }
        flag, error, id_movement = insert_warehouse_movement_db(
            None, item["id_product"], "entrada", qty, now, extra_info, data_token
        )
        if not flag:
            failure = f"reversa del producto {item['id_product']}: {error}"
            break
        flag, error, _ = update_stock_db(item["id_product"], qty, data_token, just_add=True)
        if not flag:
            done.append((id_movement, item["id_product"], qty, False))
            failure = f"reintegro de stock del producto {item['id_product']}: {error}"
            break
        done.append((id_movement, item["id_product"], qty, True))
    if failure:
        for id_movement, pid, qty, added in done:
            delete_movement_db(id_movement, data_token)
            if added:
                update_stock_db(pid, -qty, data_token, just_add=True)
        msg = f"La cancelación del traslado {transfer['folio']} falló y se revirtió ({failure}); sigue en tránsito"
        write_log_file(log_file_almacen, msg, data_token)
        return {"data": None, "msg": msg, "error": failure}, 400
    history = _append_history(
        transfer.get("history"), user, "Cancelación",
        f"Traslado cancelado en tránsito; material reintegrado al principal{': ' + reason if reason else ''}.",
    )
    flag, error, _ = update_transfer_fields_db(
        transfer["id_transfer"], {"status": 3, "history": history}, data_token
    )
    error_out = None
    if not flag:
        error_out = f"Reversa aplicada pero el traslado no cambió a CANCELADO: {error}"
    msg = f"Traslado {transfer['folio']} cancelado; {len(done)} item(s) reintegrados al principal [emp {user}]"
    create_notification_permission(
        f"El traslado {transfer['folio']} fue cancelado por el principal{': ' + reason if reason else ''}.",
        data_token, [f"sucursal-{transfer['id_warehouse_dest']}"], "Traslados", user or 0, 0,
    )
    write_log_file(log_file_almacen, msg + (f" | {error_out}" if error_out else ""), data_token)
    return {
        "data": {
            "id_transfer": transfer["id_transfer"],
            "folio": transfer["folio"],
            "status": 3 if error_out is None else 0,
            "status_label": WH_TRANSFER_STATUS[3 if error_out is None else 0],
            "reversed_movements": [mv[0] for mv in done],
        },
        "msg": msg,
        "error": error_out,
    }, 200


def _parse_transfer_filters(params):
    """Query params del listado -> filtros del controller o (None, msg)."""
    filters: dict = {}
    status = params.get("status")
    if status not in (None, ""):
        try:
            filters["status"] = int(status)
        except (TypeError, ValueError):
            return None, f"status inválido: {status}"
        if filters["status"] not in WH_TRANSFER_STATUS:
            return None, f"status inválido: {status} (0..{max(WH_TRANSFER_STATUS)})"
    for key in ("id_warehouse_dest", "id_warehouse_origin"):
        value = params.get(key)
        if value not in (None, ""):
            try:
                filters[key] = int(value)
            except (TypeError, ValueError):
                return None, f"{key} inválido: {value}"
    for key in ("date_from", "date_to"):
        value = (params.get(key) or "").strip()
        if value:
            filters[key] = value
    limit = params.get("limit")
    filters["limit"] = TRANSFERS_DEFAULT_LIMIT
    if limit not in (None, ""):
        try:
            filters["limit"] = max(1, min(int(limit), TRANSFERS_MAX_LIMIT))
        except (TypeError, ValueError):
            return None, f"limit inválido: {limit}"
    return filters, None


def query_transfers(filters: dict, data_token):
    """Listado con aviso de recorte (mismo patrón que el kardex,
    docs/almacen_kardex_ventana.md): se pide `limit + 1` a la BD y si vuelve
    la fila de más, `meta.truncated`. -> (transfers enriquecidos, meta, None)
    o (None, None, error)."""
    limit = int(filters.get("limit") or TRANSFERS_DEFAULT_LIMIT)
    flag, error, rows = get_transfers_db({**filters, "limit": limit + 1}, data_token)
    if not flag:
        return None, None, error
    rows = rows if isinstance(rows, list) else []
    truncated = len(rows) > limit
    rows = rows[:limit]
    data_out = [_enrich_transfer_items(_row_to_transfer(r), data_token) for r in rows]
    meta = {"limit": limit, "returned": len(data_out), "truncated": truncated}
    return data_out, meta, None


def fetch_transfers_api(params, data_token):
    """GET /almacen/transfers?status=&id_warehouse_dest=&date_from=&date_to=&limit=.
    `meta: {limit, returned, truncated}` avisa si el tope recortó."""
    filters, err = _parse_transfer_filters(params)
    if filters is None:
        return {"data": None, "msg": err, "error": None}, 400
    data_out, meta, error = query_transfers(filters, data_token)
    if data_out is None or meta is None:
        return {"data": None, "msg": "Error al consultar los traslados", "error": error}, 400
    return {
        "data": data_out,
        "meta": meta,
        "msg": f"{len(data_out)} traslados" + (" (recortado al tope)" if meta["truncated"] else ""),
        "error": None,
    }, 200


def get_transfer_api(id_transfer, data_token):
    """GET /almacen/transfer/<id>: detalle enviado vs recibido."""
    transfer, err, code = _load_transfer(id_transfer, data_token)
    if transfer is None:
        return err, code
    return {"data": _enrich_transfer_items(transfer, data_token), "msg": None, "error": None}, 200


# --- Resolver diferencias (P-047, docs/almacen_multisede_resolve.md) ----------
def _parse_resolve_items(raw_items, pending: dict):
    """Valida items del resolve: [{id_product, action, comment?}]. Debe venir
    exactamente el conjunto de productos con faltante (`pending`: id ->
    cantidad faltante), sin extras ni repetidos, con action en RESOLVE_ACTIONS.
    -> ({id_product: {action, comment}}, None) | (None, msg)."""
    if not isinstance(raw_items, list) or not raw_items:
        return None, "items debe ser una lista con la acción por producto faltante"
    parsed = {}
    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            return None, f"items[{idx}] debe ser un objeto {{id_product, action, comment?}}"
        pid_raw = raw.get("id_product")
        action = str(raw.get("action") or "").strip().lower()
        if pid_raw is None or not action:
            return None, f"items[{idx}]: id_product y action son obligatorios"
        try:
            pid = int(pid_raw)
        except (TypeError, ValueError):
            return None, f"items[{idx}]: id_product debe ser numérico"
        if action not in RESOLVE_ACTIONS:
            return None, f"items[{idx}] (producto {pid}): action inválida '{action}' ({' | '.join(RESOLVE_ACTIONS)})"
        if pid in parsed:
            return None, f"El producto {pid} viene repetido en items"
        parsed[pid] = {"action": action, "comment": str(raw.get("comment") or "").strip()}
    missing = sorted(set(pending) - set(parsed))
    extra = sorted(set(parsed) - set(pending))
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"faltan los productos con diferencia {missing}")
        if extra:
            parts.append(f"los productos {extra} no tienen diferencia en este traslado")
        return None, "; ".join(parts)
    return parsed, None


def resolve_transfer_api(id_transfer, data, raw_payload, data_token):
    """PUT /almacen/transfer/<id>/resolve {items:[{id_product, action, comment?}],
    comment?}: cierra un RECIBIDO CON DIFERENCIAS (status 2) decidiendo por
    cada faltante (quantity_sent - quantity_received > 0):
      * reingreso: ENTRADA en el kardex del principal (id_warehouse NULL,
        extra_info {reference: folio, id_transfer, resolution}) por la
        diferencia + products_amc.stock += diferencia (misma pareja de
        llamadas que la reversa de cancel_transfer_api).
      * merma: sin movimiento (el stock ya salió al enviar); solo registro.
    Guarda `resolution` por renglón en items, history y status 4. Reversa
    best-effort si una entrada falla a la mitad. 200 con el traslado completo
    (mismo shape que GET /almacen/transfer/<id>)."""
    user = data_token.get("emp_id")
    transfer, err, code = _load_transfer(id_transfer, data_token)
    if transfer is None:
        return err, code
    if transfer["status"] != 2:
        return {
            "data": None,
            "msg": (
                f"El traslado {transfer['folio']} está en {transfer['status_label']}: "
                f"solo se resuelve en {WH_TRANSFER_STATUS[2]}"
            ),
            "error": None,
        }, 400
    pending = {}
    for item in transfer["items"]:
        if item.get("resolution"):
            continue  # defensivo: status 2 no debería traer renglones resueltos
        sent = float(item.get("quantity_sent") or 0)
        received = float(item.get("quantity_received") or 0)
        if sent - received > 0:
            pending[int(item["id_product"])] = sent - received
    if not pending:
        return {
            "data": None,
            "msg": f"El traslado {transfer['folio']} no tiene faltantes por resolver",
            "error": None,
        }, 400
    actions, err_msg = _parse_resolve_items(raw_payload.get("items"), pending)
    if actions is None:
        return {"data": None, "msg": err_msg, "error": None}, 400

    now = _now_ts()
    comment = str(data.get("comment") or "").strip()
    done = []  # (id_movement, id_product, qty, stock_sumado)
    failure = None
    new_items = []
    summary = []
    for item in transfer["items"]:
        pid = int(item["id_product"])
        new_item = dict(item)
        new_items.append(new_item)
        if pid not in pending:
            continue
        qty = pending[pid]
        action = actions[pid]["action"]
        item_comment = actions[pid]["comment"]
        resolution = {
            "action": action,
            "quantity": qty,
            "comment": item_comment,
            "movement_id": None,
            "user": user,
            "timestamp": now,
        }
        if action == "reingreso":
            extra_info = {
                "reference": transfer["folio"],
                "id_transfer": transfer["id_transfer"],
                "resolution": "reingreso",
                "comment": f"Reingreso por diferencia del traslado {transfer['folio']}"
                + (f": {item_comment}" if item_comment else ""),
                "user": user,
            }
            flag, error, id_movement = insert_warehouse_movement_db(
                None, pid, "entrada", qty, now, extra_info, data_token
            )
            if not flag:
                failure = f"reingreso del producto {pid}: {error}"
                break
            flag, error, _ = update_stock_db(pid, qty, data_token, just_add=True)
            if not flag:
                done.append((id_movement, pid, qty, False))
                failure = f"reintegro de stock del producto {pid}: {error}"
                break
            done.append((id_movement, pid, qty, True))
            resolution["movement_id"] = id_movement
        new_item["resolution"] = resolution
        summary.append(f"producto {pid}: {action} x{qty:g}")
    if failure:
        for id_movement, pid, qty, added in done:
            delete_movement_db(id_movement, data_token)
            if added:
                update_stock_db(pid, -qty, data_token, just_add=True)
        msg = f"La resolución del traslado {transfer['folio']} falló y se revirtió ({failure}); sigue con diferencias"
        write_log_file(log_file_almacen, msg, data_token)
        return {"data": None, "msg": msg, "error": failure}, 400

    history = _append_history(
        transfer.get("history"), user, "Resolución de diferencias",
        f"Faltantes resueltos ({'; '.join(summary)})" + (f". {comment}" if comment else "") + ".",
    )
    flag, error, _ = update_transfer_fields_db(
        transfer["id_transfer"], {"status": 4, "items": new_items, "history": history}, data_token
    )
    if not flag:
        # Los reingresos ya están en el principal: se revierten para que el
        # traslado quede consistente (sigue en status 2, reintentable).
        for id_movement, pid, qty, added in done:
            delete_movement_db(id_movement, data_token)
            if added:
                update_stock_db(pid, -qty, data_token, just_add=True)
        msg = f"No se pudo cerrar el traslado {transfer['folio']}; reingresos revertidos, sigue con diferencias"
        write_log_file(log_file_almacen, msg + f" | {error}", data_token)
        return {"data": None, "msg": msg, "error": error}, 400

    msg = (
        f"Traslado {transfer['folio']} ({WH_TRANSFER_STATUS[4]}): {'; '.join(summary)}; "
        f"{len(done)} reingreso(s) al principal [emp {user}]"
    )
    create_notification_permission(
        f"Diferencias del traslado {transfer['folio']} resueltas por el principal: {'; '.join(summary)}.",
        data_token, [f"sucursal-{transfer['id_warehouse_dest']}"], "Traslados", user or 0, 0,
    )
    write_log_file(log_file_almacen, msg, data_token)
    transfer, err, code = _load_transfer(transfer["id_transfer"], data_token)
    if transfer is None:
        return err, code
    return {"data": _enrich_transfer_items(transfer, data_token), "msg": msg, "error": None}, 200
