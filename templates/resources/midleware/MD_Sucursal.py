# -*- coding: utf-8 -*-
"""
Multisede de almacén — orquestación del lado SEDE (namespace GUI/api/v1/sucursal,
rutas en rs_Sucursal.py). Fase 2 del plan docs/almacen_multisede_plan.md:
inventario de la sede, stock del principal en solo lectura y movimientos
libres (entrada/salida) con stock por sede en warehouse_stock_amc. Fase 3:
traslados hacia la sede (listar, detalle, confirmar recepción).

Reglas:
  * La sede que opera sale del permiso `App.Department.Sucursal-<id>`: si el
    usuario tiene exactamente uno, `id_warehouse` es opcional; un id ajeno
    -> 403. Lecturas: también `almacen`/`administracion` (supervisión) con
    `id_warehouse` explícito.
  * Kardex único: los movimientos de sede llevan id_warehouse = sede; el
    principal (NULL) nunca se toca desde aquí.
  * Stock por sede nunca negativo: se valida ANTES de escribir (POST salida,
    PUT por diferencia, DELETE por reversa). Sin transacciones entre llamadas:
    orden defensivo movimiento -> stock, con reversa best-effort si el stock
    falla.
  * Los movimientos nacidos de un traslado (extra_info.id_transfer, F3) NO
    se editan ni se borran desde el CRUD de la sede.
"""
__author__ = "Edisson Naula"
__date__ = "$ 08/sep./2026  at 10:00 $"

from datetime import date, datetime

import pytz

from static.constants import format_timestamps, log_file_sucursal, timezone_software
from templates.controllers.product.products_controller import get_stock_db
from templates.controllers.product.warehouses_controller import (
    SEDE_INVENTORY_COLUMNS,
    SEDE_MOVEMENT_COLUMNS,
    add_warehouse_stock_db,
    delete_warehouse_movement_db,
    get_main_inventory_db,
    get_transfers_db,
    get_warehouse_db,
    get_warehouse_inventory_db,
    get_warehouse_movement_db,
    get_warehouse_movements_db,
    get_warehouse_stock_db,
    insert_warehouse_movement_db,
    update_transfer_fields_db,
    update_warehouse_movement_db,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.MD_Multisede import (
    WH_TRANSFER_STATUS,
    _append_history,
    _enrich_transfer_items,
    _load_json,
    _load_transfer,
    _parse_transfer_filters,
    _row_to_transfer,
    _row_to_warehouse,
    verify_warehouse_permission,
)

_MOVEMENT_TYPES = ("entrada", "salida")
_MOVEMENTS_DEFAULT_LIMIT = 500
_MOVEMENTS_MAX_LIMIT = 5000


# --- Helpers -----------------------------------------------------------------
def _now_ts():
    timezone = pytz.timezone(timezone_software)
    return datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)


def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.strftime(format_timestamps) if isinstance(value, datetime) else value.isoformat()
    return value


def _sede_ids_from_token(data_token):
    """Ids de sede presentes en los permisos `Sucursal-<n>` del token."""
    ids = []
    for item in ((data_token or {}).get("permissions", {}) or {}).values():
        name = str(item).lower()
        parts = name.rsplit("sucursal-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            ids.append(int(parts[1]))
    return ids


def _is_main_reader(data_token):
    """Permisos del lado principal que pueden LEER cualquier sede."""
    for item in ((data_token or {}).get("permissions", {}) or {}).values():
        name = str(item).lower()
        if "almacen" in name or "administracion" in name or "administrator" in name:
            return True
    return False


def _resolve_warehouse(data_token, requested, read_only=False):
    """Decide sobre qué sede opera el request y valida el permiso.
    -> (sede dict, None, 200) o (None, envelope, code).
    - `requested` (id_warehouse del query/body) ausente: se usa la única
      sede del permiso del usuario; con varias o ninguna -> 400/403.
    - id ajeno -> 403 (salvo lectores del principal en read_only).
    - la sede debe existir (404), no ser la principal (400: opera por
      /almacen) y, para escrituras, estar activa (400)."""
    sede_ids = _sede_ids_from_token(data_token)
    if requested in (None, ""):
        if len(sede_ids) == 1:
            id_warehouse = sede_ids[0]
        elif len(sede_ids) > 1:
            return None, {
                "data": None,
                "msg": f"Tienes varias sedes ({sorted(sede_ids)}): manda id_warehouse",
                "error": None,
            }, 400
        elif read_only and _is_main_reader(data_token):
            return None, {"data": None, "msg": "id_warehouse es obligatorio", "error": None}, 400
        else:
            return None, {"data": None, "msg": "Sin permiso de sede (Sucursal-<id>)", "error": None}, 403
    else:
        try:
            id_warehouse = int(requested)
        except (TypeError, ValueError):
            return None, {"data": None, "msg": f"id_warehouse inválido: {requested}", "error": None}, 400
    allowed = verify_warehouse_permission(data_token, id_warehouse) or (
        read_only and _is_main_reader(data_token)
    )
    if not allowed:
        return None, {
            "data": None,
            "msg": f"Sin permiso para operar la sede {id_warehouse}",
            "error": None,
        }, 403
    flag, error, row = get_warehouse_db(id_warehouse, data_token)
    if not flag:
        return None, {"data": None, "msg": "Error al consultar la sede", "error": error}, 400
    if not row:
        return None, {"data": None, "msg": f"No existe la sede {id_warehouse}", "error": "No encontrado"}, 404
    sede = _row_to_warehouse(row)
    if sede.get("is_main") == 1:
        return None, {
            "data": None,
            "msg": "La sede principal opera por /almacen, no por /sucursal",
            "error": None,
        }, 400
    if not read_only and sede.get("is_active") != 1:
        return None, {
            "data": None,
            "msg": f"La sede {id_warehouse} ({sede.get('name')}) está dada de baja",
            "error": None,
        }, 400
    return sede, None, 200


def _row_to_inventory(row) -> dict:
    data = dict(zip(SEDE_INVENTORY_COLUMNS, row))
    data["stock"] = float(data.get("stock") or 0)
    data["stock_main"] = float(data.get("stock_main") or 0)
    data["is_tool"] = int(data.get("is_tool") or 0)
    data["is_internal"] = int(data.get("is_internal") or 0)
    return data


def _row_to_movement(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(SEDE_MOVEMENT_COLUMNS, row)}
    extra_raw = _load_json(data.get("extra_info"), {})
    extra: dict = extra_raw if isinstance(extra_raw, dict) else {}
    data["quantity"] = float(data.get("quantity") or 0)
    data["reference"] = extra.get("reference") or ""
    data["comment"] = extra.get("comment") or ""
    data["user"] = extra.get("user")
    data["id_transfer"] = extra.get("id_transfer")
    data["editable"] = extra.get("id_transfer") is None
    data["extra_info"] = extra
    return data


def _effect(movement_type, quantity):
    """Efecto de un movimiento sobre el stock de la sede: +q entrada, -q salida."""
    return float(quantity) if movement_type == "entrada" else -float(quantity)


def _sede_stock(id_warehouse, id_product, data_token):
    """-> (stock float, error|None). Sin fila = 0."""
    flag, error, row = get_warehouse_stock_db(id_warehouse, id_product, data_token)
    if not flag:
        return None, error
    return float(row[0]) if row else 0.0, None  # pyrefly: ignore


def _parse_movement_date(value):
    """'YYYY-MM-DD HH:MM:SS' o 'YYYY-MM-DD' -> timestamp normalizado; ausente = ahora."""
    if value in (None, ""):
        return _now_ts(), None
    text = str(value).strip()
    for fmt in (format_timestamps, "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).strftime(format_timestamps), None
        except ValueError:
            continue
    return None, f"movement_date inválida: {value} (usar YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)"


def _load_sede_movement(id_movement, data_token):
    """-> (movimiento dict, None, 200) o (None, envelope, code). El
    movimiento debe ser de sede (id_warehouse no NULL)."""
    flag, error, row = get_warehouse_movement_db(id_movement, data_token)
    if not flag:
        return None, {"data": None, "msg": "Error al consultar el movimiento", "error": error}, 400
    if not row:
        return None, {"data": None, "msg": f"No existe el movimiento {id_movement}", "error": "No encontrado"}, 404
    movement = _row_to_movement(row)
    if movement.get("id_warehouse") is None:
        return None, {
            "data": None,
            "msg": f"El movimiento {id_movement} es de la sede principal: se edita por /almacen",
            "error": None,
        }, 400
    return movement, None, 200


# --- Inventario ---------------------------------------------------------------
def get_sede_inventory_api(params, data_token):
    """GET /sucursal/inventory?id_warehouse=&search=&only_with_stock=1."""
    sede, err, code = _resolve_warehouse(data_token, params.get("id_warehouse"), read_only=True)
    if sede is None:
        return err, code
    search = (params.get("search") or "").strip() or None
    only_with_stock = (
        1 if str(params.get("only_with_stock") or "").strip().lower() in ("1", "true", "yes") else None
    )
    flag, error, rows = get_warehouse_inventory_db(sede["id_warehouse"], search, only_with_stock, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el inventario de la sede", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_row_to_inventory(r) for r in rows]
    return {
        "data": {"warehouse": {"id_warehouse": sede["id_warehouse"], "name": sede["name"]}, "products": data_out},
        "msg": f"{len(data_out)} productos",
        "error": None,
    }, 200


def get_main_inventory_api(params, data_token):
    """GET /sucursal/inventory/main?search=&only_with_stock=1 (solo lectura)."""
    search = (params.get("search") or "").strip() or None
    only_with_stock = (
        1 if str(params.get("only_with_stock") or "").strip().lower() in ("1", "true", "yes") else None
    )
    flag, error, rows = get_main_inventory_db(search, only_with_stock, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el inventario del principal", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_row_to_inventory(r) for r in rows]
    return {"data": data_out, "msg": f"{len(data_out)} productos", "error": None}, 200


# --- Kardex de la sede ---------------------------------------------------------
def get_sede_movements_api(type_m, params, data_token):
    """GET /sucursal/movements/<type_m>?id_warehouse=&date_from=&date_to=&limit=."""
    sede, err, code = _resolve_warehouse(data_token, params.get("id_warehouse"), read_only=True)
    if sede is None:
        return err, code
    type_like = type_m if type_m in _MOVEMENT_TYPES else "%"
    date_from = (params.get("date_from") or "").strip() or None
    date_to = (params.get("date_to") or "").strip() or None
    try:
        limit = int(params.get("limit") or _MOVEMENTS_DEFAULT_LIMIT)
    except (TypeError, ValueError):
        return {"data": None, "msg": f"limit inválido: {params.get('limit')}", "error": None}, 400
    limit = max(1, min(limit, _MOVEMENTS_MAX_LIMIT))
    flag, error, rows = get_warehouse_movements_db(
        sede["id_warehouse"], type_like, date_from, date_to, limit, data_token
    )
    if not flag:
        return {"data": None, "msg": "Error al consultar los movimientos de la sede", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_row_to_movement(r) for r in rows]
    return {
        "data": {"warehouse": {"id_warehouse": sede["id_warehouse"], "name": sede["name"]}, "movements": data_out},
        "msg": f"{len(data_out)} movimientos",
        "error": None,
    }, 200


def create_sede_movement_api(data, data_token):
    """POST /sucursal/movement: entrada o salida libre de la sede. Salida
    valida stock suficiente. Escribe movimiento (id_warehouse = sede) y
    luego suma/resta en warehouse_stock_amc; si el stock falla, borra el
    movimiento best-effort y responde 400."""
    sede, err, code = _resolve_warehouse(data_token, data.get("id_warehouse"))
    if sede is None:
        return err, code
    id_warehouse = sede["id_warehouse"]
    movement_type = str(data.get("movement_type") or "").strip().lower()
    if movement_type not in _MOVEMENT_TYPES:
        return {"data": None, "msg": "movement_type debe ser entrada o salida", "error": None}, 400
    try:
        quantity = float(data.get("quantity"))
    except (TypeError, ValueError):
        return {"data": None, "msg": "quantity inválida", "error": None}, 400
    if quantity <= 0:
        return {"data": None, "msg": "quantity debe ser mayor que 0", "error": None}, 400
    id_product = data.get("id_product")
    flag, error, product = get_stock_db(id_product, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el producto", "error": error}, 400
    if not product:
        return {"data": None, "msg": f"No existe el producto {id_product}", "error": "No encontrado"}, 404
    product_name = product[1]  # pyrefly: ignore
    movement_date, err_date = _parse_movement_date(data.get("movement_date"))
    if err_date:
        return {"data": None, "msg": err_date, "error": None}, 400

    stock_before, error = _sede_stock(id_warehouse, id_product, data_token)
    if stock_before is None:
        return {"data": None, "msg": "Error al consultar el stock de la sede", "error": error}, 400
    delta = _effect(movement_type, quantity)
    if stock_before + delta < 0:
        return {
            "data": None,
            "msg": (
                f"Stock insuficiente en la sede {id_warehouse} para {product_name}: "
                f"hay {stock_before:g}, se quieren sacar {quantity:g}"
            ),
            "error": None,
        }, 400

    extra_info = {
        "reference": str(data.get("reference") or "").strip().upper(),
        "comment": str(data.get("comment") or "").strip(),
        "user": data_token.get("emp_id"),
    }
    flag, error, id_movement = insert_warehouse_movement_db(
        id_warehouse, id_product, movement_type, quantity, movement_date, extra_info, data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el movimiento", "error": error}, 400
    flag, error, _ = add_warehouse_stock_db(id_warehouse, id_product, delta, data_token)
    if not flag:
        delete_warehouse_movement_db(id_movement, id_warehouse, data_token)  # reversa best-effort
        return {
            "data": None,
            "msg": "No se pudo actualizar el stock de la sede; el movimiento se revirtió",
            "error": error,
        }, 400
    stock_after = stock_before + delta
    msg = (
        f"Sede {id_warehouse} ({sede['name']}): {movement_type} de {quantity:g} de "
        f"{product_name} (producto {id_product}), stock {stock_before:g} -> {stock_after:g}"
        f"{' ref ' + extra_info['reference'] if extra_info['reference'] else ''}"
        f" [emp {data_token.get('emp_id')}]"
    )
    write_log_file(log_file_sucursal, msg, data_token)
    return {
        "data": {
            "id_movement": id_movement,
            "id_warehouse": id_warehouse,
            "id_product": id_product,
            "movement_type": movement_type,
            "quantity": quantity,
            "movement_date": movement_date,
            "stock_before": stock_before,
            "stock_after": stock_after,
        },
        "msg": msg,
        "error": None,
    }, 201


def update_sede_movement_api(data, raw_payload, data_token):
    """PUT /sucursal/movement: parcial (quantity, movement_type,
    movement_date, reference, comment). La sede sale del propio movimiento;
    el stock se compensa por diferencia (efecto nuevo - efecto viejo) con
    validación de no-negativo. Movimientos de traslado -> 400."""
    id_movement = data.get("id_movement")
    movement, err, code = _load_sede_movement(id_movement, data_token)
    if movement is None:
        return err, code
    sede, err, code = _resolve_warehouse(data_token, movement["id_warehouse"])
    if sede is None:
        return err, code
    id_warehouse = sede["id_warehouse"]
    if not movement["editable"]:
        return {
            "data": None,
            "msg": (
                f"El movimiento {id_movement} nació del traslado {movement['id_transfer']}: "
                "no se edita desde la sede (las diferencias se resuelven en el traslado)"
            ),
            "error": None,
        }, 400

    updates: dict = {}
    changed: list = []
    new_type = movement["movement_type"]
    new_qty = movement["quantity"]
    if "movement_type" in raw_payload:
        new_type = str(data.get("movement_type") or "").strip().lower()
        if new_type not in _MOVEMENT_TYPES:
            return {"data": None, "msg": "movement_type debe ser entrada o salida", "error": None}, 400
        if new_type != movement["movement_type"]:
            updates["movement_type"] = new_type
            changed.append(f"tipo {movement['movement_type']} -> {new_type}")
    if "quantity" in raw_payload:
        try:
            new_qty = float(data.get("quantity"))
        except (TypeError, ValueError):
            return {"data": None, "msg": "quantity inválida", "error": None}, 400
        if new_qty <= 0:
            return {"data": None, "msg": "quantity debe ser mayor que 0", "error": None}, 400
        if new_qty != movement["quantity"]:
            updates["quantity"] = new_qty
            changed.append(f"cantidad {movement['quantity']:g} -> {new_qty:g}")
    if "movement_date" in raw_payload:
        movement_date, err_date = _parse_movement_date(data.get("movement_date"))
        if err_date:
            return {"data": None, "msg": err_date, "error": None}, 400
        if movement_date != movement["movement_date"]:
            updates["movement_date"] = movement_date
            changed.append("fecha")
    extra = dict(movement.get("extra_info") or {})
    if "reference" in raw_payload:
        reference = str(data.get("reference") or "").strip().upper()
        if reference != extra.get("reference", ""):
            extra["reference"] = reference
            changed.append("referencia")
    if "comment" in raw_payload:
        comment = str(data.get("comment") or "").strip()
        if comment != extra.get("comment", ""):
            extra["comment"] = comment
            changed.append("comentario")
    if extra != (movement.get("extra_info") or {}):
        extra["updated_by"] = data_token.get("emp_id")
        updates["extra_info"] = extra
    if not updates:
        return {"data": {"id_movement": int(id_movement)}, "msg": "Sin cambios", "error": None}, 200

    delta = _effect(new_type, new_qty) - _effect(movement["movement_type"], movement["quantity"])
    stock_before, error = _sede_stock(id_warehouse, movement["id_product"], data_token)
    if stock_before is None:
        return {"data": None, "msg": "Error al consultar el stock de la sede", "error": error}, 400
    if stock_before + delta < 0:
        return {
            "data": None,
            "msg": (
                f"El cambio dejaría el stock de la sede en negativo ({stock_before:g} {delta:+g}): "
                "ajusta la cantidad o registra primero una entrada"
            ),
            "error": None,
        }, 400
    flag, error, _ = update_warehouse_movement_db(id_movement, id_warehouse, updates, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el movimiento", "error": error}, 400
    error_out = None
    if delta != 0:
        flag, error, _ = add_warehouse_stock_db(id_warehouse, movement["id_product"], delta, data_token)
        if not flag:
            error_out = f"Movimiento actualizado pero el stock de la sede no se ajustó ({delta:+g}): {error}"
    stock_after = stock_before + (delta if error_out is None else 0)
    msg = (
        f"Sede {id_warehouse}: movimiento {id_movement} actualizado ({'; '.join(changed)}), "
        f"stock del producto {movement['id_product']} {stock_before:g} -> {stock_after:g} [emp {data_token.get('emp_id')}]"
    )
    write_log_file(log_file_sucursal, msg + (f" | {error_out}" if error_out else ""), data_token)
    return {
        "data": {
            "id_movement": int(id_movement),
            "id_warehouse": id_warehouse,
            "stock_before": stock_before,
            "stock_after": stock_after,
            "stock_delta": delta,
        },
        "msg": msg,
        "error": error_out,
    }, 200


def delete_sede_movement_api(data, data_token):
    """DELETE /sucursal/movement: borra un movimiento libre de la sede y
    REVIERTE su efecto en el stock (validando no-negativo: borrar una entrada
    ya consumida -> 400). Movimientos de traslado -> 400."""
    id_movement = data.get("id_movement")
    movement, err, code = _load_sede_movement(id_movement, data_token)
    if movement is None:
        return err, code
    sede, err, code = _resolve_warehouse(data_token, movement["id_warehouse"])
    if sede is None:
        return err, code
    id_warehouse = sede["id_warehouse"]
    if not movement["editable"]:
        return {
            "data": None,
            "msg": (
                f"El movimiento {id_movement} nació del traslado {movement['id_transfer']}: "
                "no se borra desde la sede"
            ),
            "error": None,
        }, 400
    delta = -_effect(movement["movement_type"], movement["quantity"])
    stock_before, error = _sede_stock(id_warehouse, movement["id_product"], data_token)
    if stock_before is None:
        return {"data": None, "msg": "Error al consultar el stock de la sede", "error": error}, 400
    if stock_before + delta < 0:
        return {
            "data": None,
            "msg": (
                f"No se puede borrar la entrada de {movement['quantity']:g}: el stock de la sede "
                f"quedaría en negativo ({stock_before:g} {delta:+g}); parte ya se consumió"
            ),
            "error": None,
        }, 400
    flag, error, rowcount = delete_warehouse_movement_db(id_movement, id_warehouse, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo borrar el movimiento", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe el movimiento {id_movement} en la sede", "error": "No encontrado"}, 404
    error_out = None
    flag, error, _ = add_warehouse_stock_db(id_warehouse, movement["id_product"], delta, data_token)
    if not flag:
        error_out = f"Movimiento borrado pero el stock de la sede no se revirtió ({delta:+g}): {error}"
    stock_after = stock_before + (delta if error_out is None else 0)
    msg = (
        f"Sede {id_warehouse}: movimiento {id_movement} ({movement['movement_type']} de "
        f"{movement['quantity']:g} del producto {movement['id_product']}) borrado, "
        f"stock {stock_before:g} -> {stock_after:g} [emp {data_token.get('emp_id')}]"
    )
    write_log_file(log_file_sucursal, msg + (f" | {error_out}" if error_out else ""), data_token)
    return {
        "data": {
            "id_movement": int(id_movement),
            "id_warehouse": id_warehouse,
            "stock_before": stock_before,
            "stock_after": stock_after,
        },
        "msg": msg,
        "error": error_out,
    }, 200


# =============================================================================
# Traslados: lado SEDE (F3) — listar los que vienen hacia su sede, detalle y
# confirmar recepción (UNA sola vez, capturando lo realmente recibido).
# =============================================================================
def fetch_sede_transfers_api(params, data_token):
    """GET /sucursal/transfers?status=&date_from=&date_to=&limit=[&id_warehouse=]:
    traslados cuyo destino es la sede (en tránsito + históricos)."""
    sede, err, code = _resolve_warehouse(data_token, params.get("id_warehouse"), read_only=True)
    if sede is None:
        return err, code
    filters, err_msg = _parse_transfer_filters(params)
    if filters is None:
        return {"data": None, "msg": err_msg, "error": None}, 400
    filters["id_warehouse_dest"] = sede["id_warehouse"]
    flag, error, rows = get_transfers_db(filters, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar los traslados de la sede", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_enrich_transfer_items(_row_to_transfer(r), data_token) for r in rows]
    pending = sum(1 for t in data_out if t["status"] == 0)
    return {
        "data": {"warehouse": {"id_warehouse": sede["id_warehouse"], "name": sede["name"]}, "transfers": data_out},
        "msg": f"{len(data_out)} traslados ({pending} en tránsito)",
        "error": None,
    }, 200


def get_sede_transfer_api(id_transfer, data_token):
    """GET /sucursal/transfer/<id>: detalle; la sede sale del destino del
    traslado (solo lectura: también supervisores del principal)."""
    transfer, err, code = _load_transfer(id_transfer, data_token)
    if transfer is None:
        return err, code
    sede, err, code = _resolve_warehouse(data_token, transfer["id_warehouse_dest"], read_only=True)
    if sede is None:
        return err, code
    return {"data": _enrich_transfer_items(transfer, data_token), "msg": None, "error": None}, 200


def _parse_received_items(raw_items, expected_ids):
    """Valida los items recibidos: [{id_product, quantity_received, comment?}]
    -> ({id_product: {quantity_received, comment}}, error|None). Debe venir
    exactamente el conjunto de productos del traslado (sin extras ni faltantes)
    y cantidades >= 0 (0 = no llegó nada de ese item)."""
    if not isinstance(raw_items, list) or not raw_items:
        return None, "items debe ser una lista con lo recibido por producto"
    received = {}
    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            return None, f"items[{idx}] debe ser un objeto {{id_product, quantity_received, comment?}}"
        pid_raw, qty_raw = raw.get("id_product"), raw.get("quantity_received")
        if pid_raw is None or qty_raw is None:
            return None, f"items[{idx}]: id_product y quantity_received son obligatorios"
        try:
            pid = int(pid_raw)
            qty = float(qty_raw)
        except (TypeError, ValueError):
            return None, f"items[{idx}]: id_product y quantity_received deben ser numéricos"
        if qty < 0:
            return None, f"items[{idx}] (producto {pid}): quantity_received no puede ser negativa"
        if pid in received:
            return None, f"El producto {pid} viene repetido en items"
        received[pid] = {"quantity_received": qty, "comment": str(raw.get("comment") or "").strip()}
    missing = sorted(set(expected_ids) - set(received))
    extra = sorted(set(received) - set(expected_ids))
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"faltan los productos {missing} (manda quantity_received 0 si no llegaron)")
        if extra:
            parts.append(f"los productos {extra} no son parte del traslado")
        return None, "; ".join(parts)
    return received, None


def receive_transfer_api(data, raw_payload, data_token):
    """PUT /sucursal/transfer/receive {id_transfer, items:[{id_product,
    quantity_received, comment?}], comment?}: confirma la recepción UNA sola
    vez. Por item con cantidad > 0: ENTRADA en el kardex de la sede
    (id_warehouse = destino, extra_info {reference: folio, id_transfer}) +
    suma en warehouse_stock_amc. Cierra en 1 (exacto) o 2 (con diferencias);
    la diferencia NO se ajusta en ningún lado (la resuelve el principal
    viendo el traslado). Reversa best-effort si falla a la mitad."""
    user = data_token.get("emp_id")
    transfer, err, code = _load_transfer(data.get("id_transfer"), data_token)
    if transfer is None:
        return err, code
    sede, err, code = _resolve_warehouse(data_token, transfer["id_warehouse_dest"])
    if sede is None:
        return err, code
    if transfer["status"] != 0:
        return {
            "data": None,
            "msg": (
                f"El traslado {transfer['folio']} ya está en {transfer['status_label']}: "
                "la recepción se confirma una sola vez"
            ),
            "error": None,
        }, 400
    expected_ids = [int(i.get("id_product")) for i in transfer["items"]]
    received, err_msg = _parse_received_items(raw_payload.get("items"), expected_ids)
    if received is None:
        return {"data": None, "msg": err_msg, "error": None}, 400

    now = _now_ts()
    id_warehouse = sede["id_warehouse"]
    done = []  # (id_movement, id_product, qty, stock_sumado)
    failure = None
    new_items = []
    differences = []
    for item in transfer["items"]:
        pid = int(item["id_product"])
        sent = float(item.get("quantity_sent") or 0)
        got = received[pid]["quantity_received"]
        new_item = dict(item)
        new_item["quantity_received"] = got
        new_item["receive_comment"] = received[pid]["comment"]
        new_items.append(new_item)
        if got != sent:
            differences.append({"id_product": pid, "quantity_sent": sent, "quantity_received": got, "difference": got - sent})
        if got <= 0:
            continue
        extra_info = {
            "reference": transfer["folio"],
            "id_transfer": transfer["id_transfer"],
            "comment": received[pid]["comment"],
            "user": user,
        }
        flag, error, id_movement = insert_warehouse_movement_db(
            id_warehouse, pid, "entrada", got, now, extra_info, data_token
        )
        if not flag:
            failure = f"entrada del producto {pid}: {error}"
            break
        flag, error, _ = add_warehouse_stock_db(id_warehouse, pid, got, data_token)
        if not flag:
            done.append((id_movement, pid, got, False))
            failure = f"stock de la sede para el producto {pid}: {error}"
            break
        done.append((id_movement, pid, got, True))
    if failure:
        for id_movement, pid, qty, added in done:
            delete_warehouse_movement_db(id_movement, id_warehouse, data_token)
            if added:
                add_warehouse_stock_db(id_warehouse, pid, -qty, data_token)
        msg = f"La recepción del traslado {transfer['folio']} falló y se revirtió ({failure}); sigue en tránsito"
        write_log_file(log_file_sucursal, msg, data_token)
        return {"data": None, "msg": msg, "error": failure}, 400

    new_status = 2 if differences else 1
    comment = str(data.get("comment") or "").strip()
    diff_text = (
        "; ".join(
            f"producto {d['id_product']}: enviado {d['quantity_sent']:g}, recibido {d['quantity_received']:g}"
            for d in differences
        )
        if differences
        else "sin diferencias"
    )
    history = _append_history(
        transfer.get("history"), user, "Recepción",
        f"Recepción confirmada en {sede['name']} ({WH_TRANSFER_STATUS[new_status]}): {diff_text}"
        + (f". {comment}" if comment else "") + ".",
    )
    flag, error, _ = update_transfer_fields_db(
        transfer["id_transfer"],
        {"status": new_status, "items": new_items, "history": history, "received_by": user, "received_at": now},
        data_token,
    )
    if not flag:
        # Las entradas ya están en la sede: no se revierten (el material sí llegó);
        # el traslado queda en tránsito para reintentar el cierre.
        for id_movement, pid, qty, added in done:
            delete_warehouse_movement_db(id_movement, id_warehouse, data_token)
            if added:
                add_warehouse_stock_db(id_warehouse, pid, -qty, data_token)
        msg = f"No se pudo cerrar el traslado {transfer['folio']}; entradas revertidas, sigue en tránsito"
        write_log_file(log_file_sucursal, msg + f" | {error}", data_token)
        return {"data": None, "msg": msg, "error": error}, 400

    msg = (
        f"Traslado {transfer['folio']} recibido en {sede['name']} ({WH_TRANSFER_STATUS[new_status]}): "
        f"{len(done)} entrada(s), {diff_text} [emp {user}]"
    )
    create_notification_permission(
        f"Traslado {transfer['folio']} recibido en {sede['name']}: {WH_TRANSFER_STATUS[new_status]} ({diff_text}).",
        data_token, ["almacen"], "Traslados", user or 0, 0,
    )
    write_log_file(log_file_sucursal, msg, data_token)
    return {
        "data": {
            "id_transfer": transfer["id_transfer"],
            "folio": transfer["folio"],
            "status": new_status,
            "status_label": WH_TRANSFER_STATUS[new_status],
            "id_warehouse": id_warehouse,
            "received_at": now,
            "movements": [mv[0] for mv in done],
            "differences": differences,
        },
        "msg": msg,
        "error": None,
    }, 200
