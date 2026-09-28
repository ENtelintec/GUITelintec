# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/sep./2026  at 16:30 $"

"""Control de Entregas (Administración): cabecera por cotización OCD, partidas
pedido / entregado / pendiente derivadas de las remisiones, membresía explícita
remisión -> control y validación de sobre-entrega. Ver docs/control_entregas.md.

Reglas:
  * UN control NO cancelado por cotización (409). La cotización debe ser OCD
    (quotations.metadata.document_type = "ocd", docs/quotation_ocd.md) -> 400.
  * Membresía remisión -> control = activity_reports.delivery_control_id (única
    llave). activity_reports.quotation_id apunta a quotations_activities y no
    sirve. Auto-enlace al crear la remisión: metadata.delivery_control_id
    explícito, o el control activo de la cotización a la que apuntan sus items
    (item_contract_id -> quotation_items.id). PUT /deliveryControl/remissions
    {add, remove} para el resto (mismo cliente; en otro control activo -> 400).
  * Entregado por partida = Σ quotation_activity_items.quantity con
    item_c_id = partida y remisión con status <> 3 (cancelada). Nunca se guarda.
  * Sobre-entrega: POST/PUT /remission cuyos items dejen entregado > pedido en
    una partida cuya cotización tenga control activo -> 400 listando partidas.
    Items sin item_c_id (o de otra cotización) se permiten y salen en el bloque
    "fuera de la orden" del detalle.
  * status: 0 abierto / 1 completo / 2 cancelado. refresh_delivery_control_status
    pone 1 cuando todas las partidas quedan en pendiente <= 0 (y regresa a 0 si
    deja de cumplirse); el PUT permite fijar 0/1 a mano; 2 solo por /cancel.
  * custom_fields: mismo contrato que control de saldos; los VALORES por
    remisión viven en activity_reports.extra_info.delivery_fields
    (PUT /deliveryControl/values), coercionados por value_type.
"""

from decimal import Decimal

from static.constants import (
    format_timestamps,
    log_file_admin_collecions,
)
from templates.controllers.contracts.quotations_controller import get_quotation_metadata
from templates.controllers.purchases.delivery_control_controller import (
    CONTROL_CANCELLED_STATUS,
    CONTROL_COLUMNS,
    ORDER_ITEM_COLUMNS,
    REMISSION_LINK_COLUMNS,
    attach_remission_to_delivery_control,
    detach_remission_from_delivery_control,
    get_active_controls_by_quotations,
    get_active_delivery_control_by_quotation,
    get_delivered_by_item,
    get_delivery_control_by_id,
    get_delivery_control_off_order_items,
    get_delivery_control_remissions,
    get_delivery_controls,
    get_delivery_totals_by_quotations,
    get_free_remissions_for_quotation,
    get_quotation_items_by_ids,
    get_quotation_order_items,
    get_remission_delivery_fields,
    get_remission_link_rows,
    insert_delivery_control,
    remove_delivery_field_keys_from_remissions,
    set_delivery_control_status,
    set_remission_delivery_fields,
    update_delivery_control_custom_fields,
    update_delivery_control_header,
    update_delivery_control_history,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.MD_BalanceControl import (
    VALUE_TYPES,
    _api_guard,
    _ApiError,
    _json_safe,
    _load_json,
    _now,
    coerce_value,
    validate_custom_fields,
)

# --- Catálogos ------------------------------------------------------------------
CURRENCIES = ("MXN", "USD")
CONTROL_STATUSES = {0: "ABIERTO", 1: "COMPLETO", 2: "CANCELADO"}
REMISSION_CANCELLED = 3
_EPS = 1e-6

# Llaves con las que una columna dinámica no puede chocar (columnas del control
# + llaves del detalle por partida / remisión).
_RESERVED_KEYS = set(CONTROL_COLUMNS) | set(ORDER_ITEM_COLUMNS) | {
    "id", "items", "off_order_items", "remissions", "totals", "delivery_fields",
    "ordered_qty", "delivered_qty", "pending_qty", "ordered_amount", "delivered_amount",
    "pending_amount", "delivery_control_id", "delivery_control_active", "folio", "date",
    "amount", "on_order_amount",
}
_PERM_NOTIFY = ["administracion"]


# --- Helpers ---------------------------------------------------------------------
def _f(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _r2(value) -> float:
    return round(_f(value), 2)


def _int_or_none(value):
    try:
        return int(value) if value is not None and value != "" else None
    except (ValueError, TypeError):
        return None


def _control_to_dict(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(CONTROL_COLUMNS, row)}
    data["custom_fields"] = _load_json(data.get("custom_fields"), []) or []
    data["history"] = _load_json(data.get("history"), []) or []
    extra = _load_json(data.get("extra_info"), {})
    data["extra_info"] = extra if isinstance(extra, dict) else {}
    status = _int_or_none(data.get("status"))
    data["status"] = status if status is not None else 0
    data["status_label"] = CONTROL_STATUSES.get(data["status"], "")
    data["is_active"] = data["status"] != CONTROL_CANCELLED_STATUS
    data["quotation_document_type"] = data.get("quotation_document_type") or "quotation"
    return data


def _load_control(id_control, data_token) -> dict:
    flag, error, row = get_delivery_control_by_id(id_control, data_token)
    if not flag:
        raise _ApiError({"data": None, "msg": "Error al consultar el control de entregas", "error": error}, 400)
    if row is None:
        raise _ApiError({"data": None, "msg": f"No existe el control de entregas (ID {id_control})", "error": "Control no encontrado"}, 404)
    return _control_to_dict(row)


def _history_entry(user, action, timestamp, comment, changes=None) -> dict:
    entry = {"user": user, "action": action, "date": timestamp, "comment": comment}
    if changes is not None:
        entry["changes"] = changes
    return entry


def _remission_history(row_history, user, action, timestamp, comment, changes) -> list:
    history = _load_json(row_history, []) or []
    history.append({"timestamp": timestamp, "user": user, "action": action, "comment": comment, "changes": changes})
    return history


def _order_items_dicts(quotation_id: int, data_token) -> list:
    flag, error, rows = get_quotation_order_items(quotation_id, data_token)
    if not flag:
        raise _ApiError({"data": None, "msg": "Error al consultar las partidas de la cotización", "error": error}, 400)
    return [{col: _json_safe(val) for col, val in zip(ORDER_ITEM_COLUMNS, r)} for r in rows]


def _delivered_map(quotation_id: int, exclude_report_id, data_token) -> dict:
    flag, error, rows = get_delivered_by_item(quotation_id, exclude_report_id, data_token)
    if not flag:
        raise _ApiError({"data": None, "msg": "Error al consultar lo entregado", "error": error}, 400)
    return {
        int(r[0]): {"qty": _f(r[1]), "amount": _f(r[2]), "remissions_count": int(r[3] or 0), "last_date": _json_safe(r[4])}
        for r in rows if r[0] is not None
    }


def _compute_items(quotation_id: int, data_token) -> tuple[list, dict]:
    """Partidas con pedido / entregado / pendiente y los totales del control."""
    items = _order_items_dicts(quotation_id, data_token)
    delivered = _delivered_map(quotation_id, None, data_token)
    totals = {"ordered_qty": 0.0, "ordered_amount": 0.0, "delivered_qty": 0.0, "delivered_amount": 0.0}
    out = []
    for it in items:
        d = delivered.get(int(it["id"]), {})
        ordered_qty = _f(it.get("quantity"))
        unit_price = _f(it.get("price_unit"))
        delivered_qty = _f(d.get("qty"))
        ordered_amount = ordered_qty * unit_price
        delivered_amount = _f(d.get("amount"))
        row = dict(it)
        row.update({
            "ordered_qty": _r2(ordered_qty),
            "delivered_qty": _r2(delivered_qty),
            "pending_qty": _r2(ordered_qty - delivered_qty),
            "unit_price": _r2(unit_price),
            "ordered_amount": _r2(ordered_amount),
            "delivered_amount": _r2(delivered_amount),
            "pending_amount": _r2(ordered_amount - delivered_amount),
            "remissions_count": int(d.get("remissions_count") or 0),
            "last_delivery_date": d.get("last_date"),
            "complete": (ordered_qty - delivered_qty) <= _EPS,
        })
        out.append(row)
        totals["ordered_qty"] += ordered_qty
        totals["ordered_amount"] += ordered_amount
        totals["delivered_qty"] += delivered_qty
        totals["delivered_amount"] += delivered_amount
    totals = {k: _r2(v) for k, v in totals.items()}
    totals["pending_qty"] = _r2(totals["ordered_qty"] - totals["delivered_qty"])
    totals["pending_amount"] = _r2(totals["ordered_amount"] - totals["delivered_amount"])
    totals["items_count"] = len(out)
    totals["items_complete"] = sum(1 for r in out if r["complete"])
    base = totals["ordered_amount"] if totals["ordered_amount"] > 0 else totals["ordered_qty"]
    done = totals["delivered_amount"] if totals["ordered_amount"] > 0 else totals["delivered_qty"]
    totals["progress_pct"] = _r2(min(100.0, done / base * 100)) if base > 0 else 0.0
    totals["complete"] = len(out) > 0 and totals["items_complete"] == len(out)
    return out, totals


def _link_row(r) -> dict:
    return {col: val for col, val in zip(REMISSION_LINK_COLUMNS, r)}


def _check_attachable(control: dict, row: dict) -> str | None:
    """Regla de adopción: mismo cliente y no estar en OTRO control activo."""
    if _int_or_none(row.get("client_id")) != _int_or_none(control.get("client_id")):
        return f"remisión {row['id']}: cliente distinto ({row.get('client_id')} ≠ {control.get('client_id')})"
    other = _int_or_none(row.get("delivery_control_id"))
    other_status = _int_or_none(row.get("control_status"))
    if other and other != control["id_control"] and other_status != CONTROL_CANCELLED_STATUS:
        return f"remisión {row['id']}: pertenece al control de entregas activo {other}"
    return None


def _attach_rows(control: dict, rows: list, timestamp, user, data_token) -> tuple[list, list]:
    """Escribe la membresía de las filas ya validadas. Devuelve (ids ligados, errores)."""
    attached, errors = [], []
    for row in rows:
        if _int_or_none(row.get("delivery_control_id")) == control["id_control"]:
            continue
        history = _remission_history(
            row.get("history"), user, "Adopción a control de entregas", timestamp,
            f"Ligada al control de entregas {control['id_control']}.",
            {"metadata": [{"field": "delivery_control_id", "before": row.get("delivery_control_id"), "after": control["id_control"]}], "items": []},
        )
        flag, error, rows_affected = attach_remission_to_delivery_control(row["id"], control["id_control"], history, data_token)
        if not flag:
            errors.append(f"remisión {row['id']}: {error}")
        elif not rows_affected:
            errors.append(f"remisión {row['id']}: otro usuario la ligó a un control antes")
        else:
            attached.append(int(row["id"]))
    return attached, errors


def refresh_delivery_control_status(id_control, data_token) -> int | None:
    """Recalcula el status abierto/completo tras un movimiento de remisiones.
    Nunca toca un control cancelado ni falla hacia afuera (a log)."""
    id_control = _int_or_none(id_control)
    if not id_control:
        return None
    try:
        control = _load_control(id_control, data_token)
        if control["status"] == CONTROL_CANCELLED_STATUS:
            return control["status"]
        _items, totals = _compute_items(control["quotation_id"], data_token)
        new_status = 1 if totals["complete"] else 0
        if new_status != control["status"]:
            set_delivery_control_status(id_control, new_status, None, data_token)
        return new_status
    except _ApiError as exc:
        write_log_file(log_file_admin_collecions, f"Control de entregas {id_control}: no se pudo recalcular el status ({exc.response[0].get('error')})", data_token)
        return None


# --- Integración con remisiones (la usa MD_Admin_Collections) ---------------------
def _requested_by_item(payload_items: list, existing_items: list | None) -> tuple[dict, list]:
    """Cantidad solicitada por partida (item_c_id) según el payload de la remisión
    + los items existentes que el payload no menciona (PUT: no se tocan).
    Devuelve (dict item_c_id -> qty, errores de forma)."""
    requested: dict[int, float] = {}
    existing_by_id = {int(it["qa_item_id"]): it for it in (existing_items or []) if it.get("qa_item_id")}
    mentioned = set()
    for it in payload_items or []:
        qa_item_id = _int_or_none(it.get("qa_item_id")) or 0
        if qa_item_id > 0:
            mentioned.add(qa_item_id)
        if it.get("is_erased") == 1:
            continue
        item_c_id = _int_or_none(it.get("item_contract_id")) or 0
        if item_c_id <= 0 and qa_item_id > 0:
            # el PUT conserva item_c_id cuando el payload no lo manda
            item_c_id = _int_or_none((existing_by_id.get(qa_item_id) or {}).get("item_c_id")) or 0
        if item_c_id <= 0:
            continue
        requested[item_c_id] = requested.get(item_c_id, 0.0) + _f(it.get("quantity"))
    for qa_item_id, it in existing_by_id.items():
        if qa_item_id in mentioned:
            continue
        item_c_id = _int_or_none(it.get("item_c_id")) or 0
        if item_c_id > 0:
            requested[item_c_id] = requested.get(item_c_id, 0.0) + _f(it.get("quantity"))
    return requested, []


def check_over_delivery(payload_items: list, existing_items: list | None, exclude_report_id, data_token) -> tuple[list, dict]:
    """Valida los items de una remisión contra las partidas de su OCD.

    Devuelve (errores, controles) donde controles = {quotation_id: (id_control,
    client_id)} de las cotizaciones CON control activo a las que apuntan los
    items. Sin control activo no hay regla (los flujos de contrato no cambian).
    Un error de consulta se reporta como error de validación (400)."""
    requested, errors = _requested_by_item(payload_items, existing_items)
    if not requested:
        return errors, {}
    flag, error, rows = get_quotation_items_by_ids(list(requested.keys()), data_token)
    if not flag:
        return [f"no se pudieron consultar las partidas: {error}"], {}
    items_info: dict[int, dict] = {
        int(r[0]): {"quotation_id": _int_or_none(r[1]), "quantity": _f(r[2]), "partida": r[3], "description": r[4]}
        for r in rows
    }
    quotation_ids = sorted({int(v["quotation_id"]) for v in items_info.values() if v["quotation_id"]})
    flag, error, ctrl_rows = get_active_controls_by_quotations(quotation_ids, data_token)
    if not flag:
        return [f"no se pudieron consultar los controles de entregas: {error}"], {}
    controls = {int(r[1]): (int(r[0]), _int_or_none(r[2])) for r in ctrl_rows}
    if not controls:
        return errors, {}
    delivered_cache: dict = {}
    for item_c_id, qty in requested.items():
        info = items_info.get(item_c_id)
        if not info or info["quotation_id"] not in controls:
            continue
        qid = info["quotation_id"]
        if qid not in delivered_cache:
            delivered_cache[qid] = _delivered_map_safe(qid, exclude_report_id, data_token)
        delivered = _f((delivered_cache[qid].get(item_c_id) or {}).get("qty"))
        ordered = _f(info["quantity"])
        if delivered + qty > ordered + _EPS:
            errors.append(
                f"partida {info['partida']} ({str(info['description'] or '')[:40]}): pedido {_r2(ordered)}, "
                f"entregado {_r2(delivered)}, esta remisión {_r2(qty)} (excede por {_r2(delivered + qty - ordered)})"
            )
    return errors, controls


def _delivered_map_safe(quotation_id, exclude_report_id, data_token) -> dict:
    try:
        return _delivered_map(quotation_id, exclude_report_id, data_token)
    except _ApiError:
        return {}


def resolve_delivery_control_for_remission(explicit_id, client_id, controls_by_quotation: dict, data_token) -> tuple[int | None, str | None]:
    """Control al que nace ligada una remisión: el explícito (validado: existe,
    activo, mismo cliente) o, si no viene, el único control activo al que apuntan
    sus items. Devuelve (id_control o None, error o None)."""
    explicit_id = _int_or_none(explicit_id)
    client_id = _int_or_none(client_id)
    if explicit_id and explicit_id > 0:
        flag, error, row = get_delivery_control_by_id(explicit_id, data_token)
        if not flag:
            return None, f"no se pudo consultar el control de entregas {explicit_id}: {error}"
        if row is None:
            return None, f"no existe el control de entregas {explicit_id}"
        control = _control_to_dict(row)
        if control["status"] == CONTROL_CANCELLED_STATUS:
            return None, f"el control de entregas {explicit_id} está cancelado"
        if client_id is not None and _int_or_none(control.get("client_id")) != client_id:
            return None, f"el control de entregas {explicit_id} es de otro cliente ({control.get('client_id')} ≠ {client_id})"
        return explicit_id, None
    candidates = {ctrl_id for ctrl_id, ctrl_client in controls_by_quotation.values() if client_id is None or ctrl_client == client_id}
    if len(candidates) == 1:
        return candidates.pop(), None
    if len(candidates) > 1:
        return None, f"los items apuntan a partidas de más de un control de entregas activo ({sorted(candidates)}); manda metadata.delivery_control_id"
    return None, None


def delivery_control_lock_error(delivery_control_id, control_status, old_client_id, new_client_id):
    """Una remisión en un control de entregas ACTIVO no cambia de cliente por los
    PUT de remisión (retirarla es acción explícita). Devuelve envelope 400 o None."""
    ctrl = _int_or_none(delivery_control_id)
    if not ctrl or _int_or_none(control_status) == CONTROL_CANCELLED_STATUS:
        return None
    new_client = _int_or_none(new_client_id)
    if new_client is None or new_client == _int_or_none(old_client_id):
        return None
    return {
        "data": {"delivery_control_id": ctrl},
        "msg": f"La remisión está en el control de entregas {ctrl}",
        "error": f"la remisión está en el control de entregas {ctrl}; quítala con PUT /deliveryControl/remissions antes de cambiar client_id ({old_client_id} → {new_client})",
    }


# --- Catálogos ------------------------------------------------------------------
def get_delivery_control_catalogs_from_api(data_token):
    return {
        "data": {
            "statuses": [{"code": k, "label": v} for k, v in CONTROL_STATUSES.items()],
            "value_types": list(VALUE_TYPES),
            "currencies": list(CURRENCIES),
        },
        "msg": None,
        "error": None,
    }, 200


# --- POST -----------------------------------------------------------------------
@_api_guard
def create_delivery_control_from_api(data, data_token):
    now = _now()
    timestamp = now.strftime(format_timestamps)
    user = data_token.get("emp_id")
    quotation_id = _int_or_none(data.get("quotation_id"))
    if not quotation_id or quotation_id <= 0:
        return {"data": None, "msg": "Falta la cotización", "error": ["quotation_id requerido"]}, 400

    flag, error, row = get_quotation_metadata(quotation_id, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo leer la cotización", "error": error}, 400
    if not row:
        return {"data": None, "msg": f"No se encontró la cotización (ID {quotation_id})", "error": "Quotation not found"}, 404
    metadata = _load_json(row[0], {}) or {}  # pyrefly: ignore
    if (metadata.get("document_type") or "quotation") != "ocd":
        return {
            "data": None,
            "msg": f"La cotización {quotation_id} no es una OCD; conviértela primero con PUT /admin/presales/quotation/ocd",
            "error": ["document_type debe ser ocd"],
        }, 400
    client_id = _int_or_none(metadata.get("client_id"))
    if not client_id:
        return {"data": None, "msg": f"La cotización {quotation_id} no tiene client_id", "error": ["client_id de la cotización requerido"]}, 400

    flag, error, existing = get_active_delivery_control_by_quotation(quotation_id, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar controles de entregas", "error": error}, 400
    if existing is not None:
        return {
            "data": {"id_control": int(existing[0])},
            "msg": f"La cotización {quotation_id} ya tiene un control de entregas activo (ID {int(existing[0])})",
            "error": "Control activo existente",
        }, 409

    errors, custom_fields = validate_custom_fields(data.get("custom_fields") or [], _RESERVED_KEYS)
    if errors:
        return {"data": None, "msg": "Columnas dinámicas inválidas", "error": errors}, 400

    title = (data.get("title") or "").strip() or (metadata.get("quotation_code") or "").strip() or f"Cotización {quotation_id}"
    client_po_number = (data.get("client_po_number") or "").strip() or (metadata.get("client_po_number") or "").strip() or None
    currency = (data.get("currency") or "").strip() or (metadata.get("currency") or "MXN")
    if currency not in CURRENCIES:
        return {"data": None, "msg": "Moneda inválida", "error": ["currency debe ser MXN o USD"]}, 400

    # Remisiones explícitas: validar TODO antes de escribir.
    control_stub = {"id_control": None, "client_id": client_id}
    explicit_ids = sorted({int(r) for r in (data.get("remissions") or []) if r})
    explicit_rows = []
    if explicit_ids:
        flag, error, rows = get_remission_link_rows(explicit_ids, data_token)
        if not flag:
            return {"data": None, "msg": "Error al consultar remisiones", "error": error}, 400
        found = {int(r[0]): _link_row(r) for r in rows}
        errors = [f"remisión {rid}: no existe" for rid in explicit_ids if rid not in found]
        for rid, link in found.items():
            err = _check_attachable(control_stub, link)
            if err:
                errors.append(err)
        if errors:
            return {"data": None, "msg": "Remisiones no válidas para el control", "error": errors}, 400
        explicit_rows = list(found.values())

    history = [_history_entry(user, "Creación", timestamp, f"Creación del control de entregas para la cotización {quotation_id}.")]
    flag, error, id_control = insert_delivery_control({
        "quotation_id": quotation_id, "client_id": client_id, "title": title,
        "client_po_number": client_po_number, "currency": currency, "status": 0,
        "custom_fields": custom_fields, "created_by": user, "timestamp": timestamp,
        "history": history, "extra_info": {},
    }, data_token)
    if not flag or not isinstance(id_control, int):
        return {"data": None, "msg": "No se pudo crear el control de entregas", "error": error}, 400
    control = {"id_control": id_control, "client_id": client_id, "quotation_id": quotation_id}

    # Auto-adopción: remisiones libres del cliente con items de esta cotización.
    partial_errors = []
    auto_rows = []
    flag, error, rows = get_free_remissions_for_quotation(quotation_id, client_id, data_token)
    if flag:
        seen = {r["id"] for r in explicit_rows}
        auto_rows = [_link_row(r) for r in rows if int(r[0]) not in seen]
    else:
        partial_errors.append(f"no se pudieron buscar remisiones para auto-adoptar: {error}")
    attached, attach_errors = _attach_rows(control, explicit_rows + auto_rows, timestamp, user, data_token)
    partial_errors.extend(attach_errors)
    if attached:
        history.append(_history_entry(user, "Adopción de remisiones", timestamp, "Remisiones ligadas al crear el control.", {"remissions": {"added": attached, "removed": []}}))
        update_delivery_control_history(id_control, history, data_token)
    status = refresh_delivery_control_status(id_control, data_token)

    msg = f"Control de entregas creado (ID {id_control}) para la cotización {quotation_id}; {len(attached)} remisión(es) ligada(s)"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Control de entregas", user or 0, 0)
    write_log_file(log_file_admin_collecions, msg + (f" | parciales: {partial_errors}" if partial_errors else ""), data_token)
    return {
        "data": {"id_control": id_control, "adopted_remissions": attached, "status": status},
        "msg": msg,
        "error": partial_errors or None,
    }, 201


# --- GET listado / detalle -----------------------------------------------------------
def get_delivery_controls_from_api(params: dict, data_token):
    quotation_id = _int_or_none(params.get("quotation_id"))
    client_id = _int_or_none(params.get("client_id"))
    status = _int_or_none(params.get("status"))
    active_only = None if (status is not None or str(params.get("all") or "").lower() in ("1", "true", "yes")) else 1
    flag, error, rows = get_delivery_controls(quotation_id, client_id, status, active_only, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar los controles de entregas", "error": error}, 400
    controls = [_control_to_dict(r) for r in rows]
    qids = sorted({c["quotation_id"] for c in controls if c.get("quotation_id")})
    flag, error, totals_rows = get_delivery_totals_by_quotations(qids, data_token)
    totals = {}
    if flag:
        for r in totals_rows:
            ordered_qty, ordered_amount = _f(r[1]), _f(r[2])
            delivered_qty, delivered_amount = _f(r[3]), _f(r[4])
            base = ordered_amount if ordered_amount > 0 else ordered_qty
            done = delivered_amount if ordered_amount > 0 else delivered_qty
            totals[int(r[0])] = {
                "ordered_qty": _r2(ordered_qty), "ordered_amount": _r2(ordered_amount),
                "delivered_qty": _r2(delivered_qty), "delivered_amount": _r2(delivered_amount),
                "pending_qty": _r2(ordered_qty - delivered_qty), "pending_amount": _r2(ordered_amount - delivered_amount),
                "progress_pct": _r2(min(100.0, done / base * 100)) if base > 0 else 0.0,
                "last_delivery_date": _json_safe(r[5]),
            }
    for c in controls:
        c["totals"] = totals.get(c["quotation_id"]) or {
            "ordered_qty": 0.0, "ordered_amount": 0.0, "delivered_qty": 0.0, "delivered_amount": 0.0,
            "pending_qty": 0.0, "pending_amount": 0.0, "progress_pct": 0.0, "last_delivery_date": None,
        }
    return {"data": controls, "msg": None, "error": error if not flag else None}, 200


@_api_guard
def get_delivery_control_from_api(id_control: int, data_token):
    control = _load_control(id_control, data_token)
    items, totals = _compute_items(control["quotation_id"], data_token)
    control["items"] = items
    control["totals"] = totals
    errors = []
    flag, error, rows = get_delivery_control_remissions(id_control, control["quotation_id"], data_token)
    remissions = []
    if flag:
        for r in rows:
            extra = _load_json(r[6], {}) or {}
            remissions.append({
                "id": r[0], "folio": r[1], "date": _json_safe(r[2]), "status": r[3],
                "cancelled": _int_or_none(r[3]) == REMISSION_CANCELLED,
                "amount": _r2(r[4]), "on_order_amount": _r2(r[5]),
                "delivery_fields": extra.get("delivery_fields") if isinstance(extra.get("delivery_fields"), dict) else {},
            })
    else:
        errors.append(error)
    control["remissions"] = remissions
    control["remissions_count"] = len(remissions)
    flag, error, rows = get_delivery_control_off_order_items(id_control, control["quotation_id"], data_token)
    if flag:
        control["off_order_items"] = [
            {"qa_item_id": r[0], "report_id": r[1], "folio": r[2], "description": r[3], "udm": r[4],
             "quantity": _r2(r[5]), "unit_price": _r2(r[6]), "line_total": _r2(r[7]), "item_c_id": r[8]}
            for r in rows
        ]
    else:
        control["off_order_items"] = []
        errors.append(error)
    control["off_order_amount"] = _r2(sum(_f(x["line_total"]) for x in control["off_order_items"]))
    return {"data": control, "msg": None, "error": errors or None}, 200


# --- PUT cabecera -------------------------------------------------------------------
@_api_guard
def update_delivery_control_from_api(data, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _int_or_none(data.get("id_control"))
    control = _load_control(id_control, data_token)
    id_control = int(control["id_control"])
    if control["status"] == CONTROL_CANCELLED_STATUS:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control})", "error": "Control cancelado"}, 400
    new = {"title": control["title"], "client_po_number": control.get("client_po_number"), "currency": control["currency"], "status": control["status"]}
    errors = []
    if data.get("title") is not None:
        title = str(data["title"]).strip()
        if not title:
            errors.append("title no puede vaciarse")
        new["title"] = title
    if data.get("client_po_number") is not None:
        new["client_po_number"] = str(data["client_po_number"]).strip() or None
    if data.get("currency"):
        new["currency"] = str(data["currency"]).strip()
    if data.get("status") is not None:
        status = _int_or_none(data["status"])
        if status not in (0, 1):
            errors.append("status debe ser 0 (abierto) o 1 (completo); cancelar es PUT /deliveryControl/cancel")
        new["status"] = status
    if errors:
        return {"data": None, "msg": "Datos del control inválidos", "error": errors}, 400
    changed_fields = [k for k in ("title", "client_po_number", "currency", "status") if (control.get(k) or None) != (new[k] or None)]
    changes = [{"field": k, "before": control.get(k), "after": new[k]} for k in changed_fields]
    if not changes:
        return {"data": {"id_control": id_control, "changes": []}, "msg": "Sin cambios", "error": None}, 200
    history = control["history"]
    history.append(_history_entry(user, "Actualización", timestamp, "Actualización de la cabecera del control de entregas.", changes))
    flag, error, _ = update_delivery_control_header(id_control, new, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el control", "error": error}, 400
    final_status = int(new["status"] or 0)
    msg = f"Control de entregas actualizado (ID {id_control}): {', '.join(changed_fields)}"
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_control": id_control, "changes": changes, "status": final_status, "status_label": CONTROL_STATUSES.get(final_status, "")}, "msg": msg, "error": None}, 200


# --- PUT /fields ------------------------------------------------------------------------
@_api_guard
def update_delivery_control_fields_from_api(data, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _int_or_none(data.get("id_control"))
    control = _load_control(id_control, data_token)
    id_control = int(control["id_control"])
    if control["status"] == CONTROL_CANCELLED_STATUS:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control})", "error": "Control cancelado"}, 400
    errors, custom_fields = validate_custom_fields(data.get("custom_fields") or [], _RESERVED_KEYS)
    if errors:
        return {"data": None, "msg": "Columnas dinámicas inválidas", "error": errors}, 400
    old_keys = [f.get("key") for f in control["custom_fields"] if isinstance(f, dict)]
    new_keys = [f["key"] for f in custom_fields]
    removed = [k for k in old_keys if k not in new_keys]
    added = [k for k in new_keys if k not in old_keys]
    history = control["history"]
    history.append(_history_entry(user, "Actualización", timestamp, "Actualización de columnas dinámicas del control de entregas.", {"custom_fields": {"added": added, "removed": removed, "order": new_keys}}))
    flag, error, _ = update_delivery_control_custom_fields(id_control, custom_fields, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron actualizar las columnas dinámicas", "error": error}, 400
    swept = 0
    sweep_error = None
    if removed:
        flag, error, swept = remove_delivery_field_keys_from_remissions(id_control, removed, data_token)
        if not flag:
            sweep_error = f"no se pudieron limpiar los valores de {removed} en las remisiones: {error}"
            write_log_file(log_file_admin_collecions, f"Control de entregas {id_control}: {sweep_error}", data_token)
            swept = 0
    msg = f"Columnas dinámicas del control de entregas actualizadas (ID {id_control}: +{len(added)} / -{len(removed)})"
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {
        "data": {"id_control": id_control, "custom_fields": custom_fields, "added": added, "removed": removed, "remissions_swept": swept},
        "msg": msg,
        "error": sweep_error,
    }, 200


# --- PUT /values: valores de columnas dinámicas por remisión --------------------------
@_api_guard
def update_delivery_control_values_from_api(data, raw_payload, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _int_or_none(data.get("id_control"))
    id_remission = _int_or_none(data.get("id_remission")) or 0
    if id_remission <= 0:
        return {"data": None, "msg": "Falta la remisión", "error": ["id_remission requerido"]}, 400
    values = (raw_payload or {}).get("values")
    if not isinstance(values, dict):
        return {"data": None, "msg": "Estructura de datos inválida", "error": "values debe ser un objeto {key: valor}"}, 400
    control = _load_control(id_control, data_token)
    id_control = int(control["id_control"])
    if control["status"] == CONTROL_CANCELLED_STATUS:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control})", "error": "Control cancelado"}, 400
    flag, error, row = get_remission_delivery_fields(id_remission, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar la remisión", "error": error}, 400
    if row is None:
        return {"data": None, "msg": f"No existe la remisión (ID {id_remission})", "error": "Remisión no encontrada"}, 404
    if _int_or_none(row[0]) != id_control:  # pyrefly: ignore
        return {"data": None, "msg": f"La remisión {id_remission} no está en el control de entregas {id_control}", "error": "Remisión fuera del control"}, 400
    declared = {f["key"]: f for f in control["custom_fields"] if isinstance(f, dict) and f.get("key")}
    extra = _load_json(row[1], {}) or {}  # pyrefly: ignore
    current = extra.get("delivery_fields") if isinstance(extra.get("delivery_fields"), dict) else {}
    errors = []
    for key, value in values.items():
        field = declared.get(key)
        if field is None:
            errors.append(f"'{key}' no es una columna del control")
            continue
        ok, coerced, err = coerce_value(value, field["value_type"])
        if not ok:
            errors.append(f"'{key}': {err}")
            continue
        if coerced is None:
            current.pop(key, None)
        else:
            current[key] = coerced
    if errors:
        return {"data": None, "msg": "Valores inválidos", "error": errors}, 400
    flag, error, _ = set_remission_delivery_fields(id_remission, current, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron guardar los valores", "error": error}, 400
    write_log_file(log_file_admin_collecions, f"Control de entregas {id_control}: valores de la remisión {id_remission} actualizados ({sorted(values.keys())}) por {user} el {timestamp}", data_token)
    return {"data": {"id_control": id_control, "id_remission": id_remission, "delivery_fields": current}, "msg": f"Valores guardados en la remisión {id_remission}", "error": None}, 200


# --- PUT /remissions: membresía explícita ----------------------------------------------
@_api_guard
def update_delivery_control_remissions_from_api(data, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _int_or_none(data.get("id_control"))
    add_ids = sorted({int(r) for r in (data.get("add") or []) if r})
    remove_ids = sorted({int(r) for r in (data.get("remove") or []) if r})
    if not add_ids and not remove_ids:
        return {"data": None, "msg": "Nada que hacer", "error": ["add y remove vacíos"]}, 400
    if set(add_ids) & set(remove_ids):
        return {"data": None, "msg": "Listas en conflicto", "error": [f"remisión {r}: está en add y en remove" for r in sorted(set(add_ids) & set(remove_ids))]}, 400
    control = _load_control(id_control, data_token)
    id_control = int(control["id_control"])
    if control["status"] == CONTROL_CANCELLED_STATUS:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control})", "error": "Control cancelado"}, 400
    flag, error, rows = get_remission_link_rows(add_ids + remove_ids, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar remisiones", "error": error}, 400
    found = {int(r[0]): _link_row(r) for r in rows}
    errors = [f"remisión {rid}: no existe" for rid in add_ids + remove_ids if rid not in found]
    for rid in add_ids:
        if rid in found:
            err = _check_attachable(control, found[rid])
            if err:
                errors.append(err)
    for rid in remove_ids:
        if rid in found and _int_or_none(found[rid].get("delivery_control_id")) != id_control:
            errors.append(f"remisión {rid}: no está en el control de entregas {id_control}")
    if errors:
        return {"data": None, "msg": "Remisiones no válidas", "error": errors}, 400

    added, write_errors = _attach_rows(control, [found[r] for r in add_ids], timestamp, user, data_token)
    removed = []
    for rid in remove_ids:
        history = _remission_history(
            found[rid].get("history"), user, "Retiro de control de entregas", timestamp,
            f"Retirada del control de entregas {id_control}.",
            {"metadata": [{"field": "delivery_control_id", "before": id_control, "after": None}], "items": []},
        )
        flag, error, rows_affected = detach_remission_from_delivery_control(rid, id_control, history, data_token)
        if not flag:
            write_errors.append(f"remisión {rid}: {error}")
        elif not rows_affected:
            write_errors.append(f"remisión {rid}: ya no estaba en el control")
        else:
            removed.append(rid)
    if added or removed:
        history = control["history"]
        history.append(_history_entry(user, "Remisiones", timestamp, "Cambio de remisiones del control de entregas.", {"remissions": {"added": added, "removed": removed}}))
        update_delivery_control_history(id_control, history, data_token)
    status = refresh_delivery_control_status(id_control, data_token)
    flag, _e, row = get_delivery_control_by_id(id_control, data_token)
    count = int(row[CONTROL_COLUMNS.index("remissions_count")] or 0) if flag and row is not None else None
    msg = f"Control de entregas {id_control}: +{len(added)} / -{len(removed)} remisiones"
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_control": id_control, "added": added, "removed": removed, "remissions_count": count, "status": status}, "msg": msg, "error": write_errors or None}, 200


# --- PUT /cancel ---------------------------------------------------------------------------
@_api_guard
def cancel_delivery_control_from_api(data, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _int_or_none(data.get("id_control"))
    control = _load_control(id_control, data_token)
    id_control = int(control["id_control"])
    if control["status"] == CONTROL_CANCELLED_STATUS:
        return {"data": {"id_control": id_control}, "msg": f"El control ya estaba cancelado (ID {id_control})", "error": None}, 200
    history = control["history"]
    history.append(_history_entry(user, "Cancelación", timestamp, data.get("comment") or "Cancelación del control de entregas."))
    flag, error, _ = set_delivery_control_status(id_control, CONTROL_CANCELLED_STATUS, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo cancelar el control", "error": error}, 400
    msg = f"Control de entregas cancelado (ID {id_control})"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Control de entregas", user or 0, 0)
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_control": id_control}, "msg": msg, "error": None}, 200


# --- Reglas sobre la cotización (las usa Functions_midleware_admin) ---------------------
def quotation_change_order_errors(quotation_id: int, products: list, existing_products: dict, data_token) -> tuple[list, int | None]:
    """Con control de entregas activo: quitar una partida entregada o bajar su
    cantidad por debajo de lo entregado -> errores. Devuelve (errores, id_control)."""
    flag, error, row = get_active_delivery_control_by_quotation(quotation_id, data_token)
    if not flag:
        return [f"no se pudo consultar el control de entregas: {error}"], None
    if row is None:
        return [], None
    id_control = int(row[0])
    delivered = _delivered_map_safe(quotation_id, None, data_token)
    errors = []
    for p in products or []:
        item_id = _int_or_none(p.get("qa_item_id")) or 0
        if item_id <= 0 or item_id not in existing_products:
            continue
        got = _f((delivered.get(item_id) or {}).get("qty"))
        if got <= _EPS:
            continue
        partida = (existing_products.get(item_id) or {}).get("partida", item_id)
        if p.get("is_erased") == 1:
            errors.append(f"partida {partida}: no se puede quitar, ya tiene {_r2(got)} entregado (control de entregas {id_control})")
        elif _f(p.get("quantity")) + _EPS < got:
            errors.append(f"partida {partida}: cantidad {_r2(_f(p.get('quantity')))} menor a lo entregado {_r2(got)} (control de entregas {id_control})")
    return errors, id_control


def quotation_has_active_delivery_control(quotation_id: int, data_token) -> int | None:
    flag, _error, row = get_active_delivery_control_by_quotation(quotation_id, data_token)
    return int(row[0]) if flag and row is not None else None
