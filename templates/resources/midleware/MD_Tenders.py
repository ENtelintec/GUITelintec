# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 19/oct./2026  at 12:00 $"

"""Control de licitaciones FO-PRE-04 (docs/tenders_control.md).

Reglas:
  * Una licitacion = fila en tenders + cotizacion interna (metadata.status = 3)
    con las partidas en quotation_items. El POST crea ambas (cotizacion primero;
    si la licitacion falla se borra la cotizacion: execute_sql no da transacciones).
  * tender_number unico global (UNIQUE en BD + pre-chequeo para el 409).
  * status 0..3 y scope 0..4 numericos. po_number y contract_id solo con status 1.
    Las reglas se validan sobre los valores RESULTANTES (guardado + payload).
  * El PUT es parcial: solo las llaves presentes en el JSON crudo. Sincroniza en
    la cotizacion interna las llaves espejo (_QUOTATION_SYNC) con JSON_SET.
  * Partidas: solo por PUT /tender/items (mismo upsert que PUT /quotation).
  * El contrato se liga a mano por PUT (contrato historico) o solo, al crearlo
    con POST /contract sobre la cotizacion interna (Functions_midleware_admin).
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import NoReturn

from static.constants import format_date, format_timestamps, log_file_admin
from templates.controllers.contracts.contracts_controller import get_contract, get_contract_id_by_quotation
from templates.controllers.contracts.quotations_controller import (
    create_quotation,
    delete_quotation,
    get_quotation,
    set_quotation_metadata_keys,
)
from templates.controllers.contracts.tenders_controller import (
    QUOTATION_STATUS_TENDER,
    TENDER_COLUMNS,
    TENDER_STATUS_ASSIGNED,
    append_tender_history,
    get_tender_by_id,
    get_tender_id_by_contract,
    get_tender_id_by_number,
    get_tenders,
    insert_tender,
    is_duplicate_error,
    update_tender,
)
from templates.controllers.purchases.balance_control_controller import get_customer_name
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.Functions_midleware_admin import (
    _OCD_DEFAULTS,
    _dict_products_from_quotation,
    _msg_items_counts,
    get_quotations,
    items_delivery_date_errors,
    update_items_quotation_from_api,
)
from templates.resources.midleware.MD_BalanceControl import (
    _api_guard,
    _ApiError,
    _json_safe,
    _load_json,
    _now,
)

# --- Catálogos (numéricos; las etiquetas las pone el front) ------------------------
TENDER_STATUSES = {0: "En espera de respuesta", 1: "Asignada", 2: "No asignada", 3: "Cancelada"}
TENDER_SCOPES = {
    0: "Suministro",
    1: "Instalación",
    2: "Mantenimiento",
    3: "Suministro e instalación",
    4: "Suministro, instalación y mantenimiento",
}
CURRENCIES = ("MXN", "USD")

_REQUIRED_POST = ("tender_number", "client_id", "description", "scope", "invitation_date", "closing_date")
_TEXT_LIMITS = {"tender_number": 60, "buyer_user": 255, "field_user": 255, "po_number": 60}
_DATE_KEYS = ("invitation_date", "closing_date", "response_date", "submitted_date")
_AMOUNT_KEYS = ("amount_usd", "amount_mxn")
_INT_KEYS = ("client_id", "scope", "status", "contract_id")
# Columnas de tenders que el payload puede tocar (currency vive en la cotización).
_FIELD_KEYS = (
    "tender_number", "client_id", "description", "scope", "buyer_user", "field_user",
    "invitation_date", "closing_date", "amount_usd", "amount_mxn", "status", "po_number",
    "response_date", "submitted_date", "contract_id",
)
# Llave de la licitación -> llave espejo en quotations.metadata.
_QUOTATION_SYNC = {
    "tender_number": "quotation_code",
    "client_id": "client_id",
    "buyer_user": "user",
    "invitation_date": "emission",
    "closing_date": "limit_date",
    "currency": "currency",
}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LIST_HIDDEN = ("history", "extra_info")


# --- Helpers ---------------------------------------------------------------------
def _bad(msg: str, errors: list, code: int = 400, data=None) -> NoReturn:
    raise _ApiError({"data": data, "msg": msg, "error": errors}, code)


def _require_int(value, key: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise _ApiError({"data": None, "msg": "Datos inválidos", "error": [f"{key} requerido"]}, 400)


def _tender_to_dict(row, with_history: bool = False) -> dict:
    data = {col: _json_safe(val) for col, val in zip(TENDER_COLUMNS, row)}
    for key in _AMOUNT_KEYS:
        data[key] = float(data[key]) if data.get(key) is not None else None
    data["currency"] = data.get("currency") or "MXN"
    data["items_count"] = int(data.get("items_count") or 0)
    data["items_total"] = round(float(data.get("items_total") or 0), 2)
    # Licitación ganada convertida a OCD (PUT /quotation/ocd sobre su cotización interna).
    data["document_type"] = data.get("document_type") or "quotation"
    data["client_po_number"] = data.get("client_po_number") or ""
    if with_history:
        data["history"] = _load_json(data.get("history"), []) or []
    else:
        data.pop("history", None)
    data.pop("extra_info", None)
    return data


def _load_tender(id_tender, data_token) -> dict:
    flag, error, row = get_tender_by_id(id_tender, data_token)
    if not flag:
        _bad("No se pudo leer la licitación", [error])
    if row is None:
        raise _ApiError({"data": None, "msg": f"No se encontró la licitación (ID {id_tender})", "error": None}, 404)
    return _tender_to_dict(row, with_history=True)


def _parse_date(key: str, value, errors: list):
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    try:
        if not _DATE_RE.match(text):
            raise ValueError
        datetime.strptime(text, format_date)
    except ValueError:
        errors.append(f"{key}: se esperaba una fecha YYYY-MM-DD")
        return None
    return text


def _normalize(raw: dict, keys, errors: list) -> dict:
    """Valores del payload ya tipados para las llaves presentes. "" y null = None."""
    out = {}
    for key in keys:
        if key not in raw:
            continue
        value = raw.get(key)
        if key in _DATE_KEYS:
            out[key] = _parse_date(key, value, errors)
        elif key in _AMOUNT_KEYS:
            if value is None or str(value).strip() == "":
                out[key] = None
                continue
            try:
                amount = Decimal(str(value))
            except InvalidOperation:
                errors.append(f"{key}: se esperaba un número")
                continue
            if amount < 0:
                errors.append(f"{key} no puede ser negativo")
            out[key] = amount.quantize(Decimal("0.01"))
        elif key in _INT_KEYS:
            if value is None or str(value).strip() == "":
                out[key] = None
                continue
            try:
                if isinstance(value, bool) or (isinstance(value, float) and not value.is_integer()):
                    raise ValueError
                out[key] = int(value)
            except (TypeError, ValueError):
                errors.append(f"{key}: se esperaba un entero")
        elif key == "currency":
            text = str(value or "").strip().upper()
            if text and text not in CURRENCIES:
                errors.append("currency debe ser MXN o USD")
            out[key] = text or None
        else:
            text = str(value).strip() if value is not None else ""
            limit = _TEXT_LIMITS.get(key)
            if limit and len(text) > limit:
                errors.append(f"{key}: máximo {limit} caracteres")
            out[key] = text or None
    return out


def _rule_errors(t: dict) -> list:
    """Reglas sobre los valores resultantes de la licitación."""
    errors = []
    for key in _REQUIRED_POST:
        if t.get(key) is None:
            errors.append(f"{key} es obligatorio")
    if t.get("scope") is not None and t["scope"] not in TENDER_SCOPES:
        errors.append("scope fuera de catálogo (0-4)")
    if t.get("status") not in TENDER_STATUSES:
        errors.append("status fuera de catálogo (0-3)")
    inv = t.get("invitation_date")
    if inv and t.get("closing_date") and t["closing_date"] < inv:
        errors.append("closing_date antes de invitation_date")
    if inv and t.get("submitted_date") and t["submitted_date"] < inv:
        errors.append("submitted_date antes de invitation_date")
    if t.get("status") != TENDER_STATUS_ASSIGNED:
        if t.get("po_number"):
            errors.append("po_number solo con status 1 (asignada): manda po_number: null")
        if t.get("contract_id"):
            errors.append("contract_id solo con status 1 (asignada): manda contract_id: null")
    return errors


def _client_name(client_id, data_token) -> str:
    flag, error, name = get_customer_name(client_id, data_token)
    if not flag:
        _bad("No se pudo validar el cliente", [error])
    if name is None:
        raise _ApiError(
            {"data": None, "msg": "Datos inválidos", "error": [f"client_id {client_id} no existe en el catálogo de clientes"]},
            400,
        )
    return str(name)


def _check_number_free(tender_number: str, own_id, data_token):
    flag, error, found = get_tender_id_by_number(tender_number, data_token)
    if not flag:
        _bad("No se pudo validar el número de licitación", [error])
    if found is not None and found != own_id:
        raise _ApiError(
            {"data": {"id_tender": found}, "msg": f"La licitación {tender_number} ya existe", "error": None}, 409
        )


def _check_contract(contract_id: int, client_id, own_id, data_token):
    """Liga manual: el contrato existe, es del mismo cliente y no está en otra licitación."""
    flag, error, contract = get_contract(data_token, contract_id)
    if not flag or not contract:
        _bad("Datos inválidos", [f"contract_id {contract_id} no existe"])
    if int(contract[6]) != int(client_id):  # get_contract: índice 6 = client_id
        _bad("Datos inválidos", [f"el contrato {contract_id} es de otro cliente"])
    flag, error, other = get_tender_id_by_contract(contract_id, data_token)
    if not flag:
        _bad("No se pudo validar el contrato", [error])
    if other is not None and other != own_id:
        raise _ApiError(
            {"data": {"id_tender": other}, "msg": f"El contrato {contract_id} ya está ligado a la licitación {other}", "error": None},
            409,
        )


def _history_entry(user, timestamp, action, comment, changes=None) -> dict:
    entry = {"user": user, "action": action, "date": timestamp, "comment": comment}
    if changes is not None:
        entry["changes"] = changes
    return entry


# --- GET -------------------------------------------------------------------------
def _int_list(text, key: str) -> list:
    if text is None or str(text).strip() == "":
        return []
    try:
        return [int(x) for x in str(text).split(",") if x.strip() != ""]
    except ValueError:
        _bad("Filtros inválidos", [f"{key}: se esperaba un entero o una lista separada por comas"])
    return []


@_api_guard
def get_tenders_from_api(args: dict, data_token):
    errors: list = []
    filters: dict = {
        "statuses": _int_list(args.get("status"), "status"),
        "date_from": _parse_date("date_from", args.get("date_from"), errors),
        "date_to": _parse_date("date_to", args.get("date_to"), errors),
    }
    client_id = _int_list(args.get("client_id"), "client_id")
    filters["client_id"] = client_id[0] if client_id else None
    has_contract = _int_list(args.get("has_contract"), "has_contract")
    filters["has_contract"] = (1 if has_contract[0] else 0) if has_contract else None
    if errors:
        _bad("Filtros inválidos", errors)
    flag, error, rows = get_tenders(filters, data_token)
    if not flag:
        _bad("No se pudieron consultar las licitaciones", [error])
    data = [_tender_to_dict(r) for r in rows]
    data.sort(key=lambda t: (t.get("invitation_date") or "", t["id_tender"]), reverse=True)
    return {"data": data, "msg": None, "error": None}, 200


@_api_guard
def get_tender_from_api(id_tender: int, with_costs: bool, data_token):
    tender = _load_tender(id_tender, data_token)
    # Partidas y totales del análisis con el mismo armado que GET /quotation/<id>?with_costs=1.
    out, code = get_quotations(data_token, tender["quotation_id"], with_costs=True)
    found = out.get("data") if isinstance(out, dict) else None
    quotation = found[0] if code == 200 and isinstance(found, list) and found else None
    if not isinstance(quotation, dict):
        error = out.get("error") if isinstance(out, dict) else None
        return {"data": None, "msg": "No se pudieron leer las partidas de la licitación", "error": [error]}, 400
    # Una cotización sin partidas trae [{"qa_item_id": null, ...}] por el LEFT JOIN.
    products = [p for p in quotation.get("products") or [] if isinstance(p, dict) and p.get("qa_item_id")]
    if not with_costs:
        for p in products:
            p.pop("cost_analysis", None)
    tender["products"] = products
    tender["cost_totals"] = quotation.get("cost_totals")
    tender["exchange_rate"] = quotation.get("exchange_rate")
    return {"data": tender, "msg": None, "error": None}, 200


# --- POST ------------------------------------------------------------------------
@_api_guard
def create_tender_from_api(raw: dict, data_token):
    now = _now()
    timestamp = now.strftime(format_timestamps)
    user = data_token.get("emp_id")
    errors: list = []
    values = _normalize(raw, _FIELD_KEYS + ("currency",), errors)
    if values.get("status") is None:
        values["status"] = 0
    errors += _rule_errors(values)
    if errors:
        _bad("Datos inválidos", errors)
    client_name = _client_name(values["client_id"], data_token)
    _check_number_free(values["tender_number"], None, data_token)
    if values.get("contract_id"):
        _check_contract(values["contract_id"], values["client_id"], None, data_token)

    # 1) Cotización interna con las llaves espejo; el resto de la metadata de
    # cotización va vacío (la licitación no tiene teléfono, correo, planta...).
    metadata = {
        "emission": values["invitation_date"],
        "limit_date": values["closing_date"],
        "quotation_code": values["tender_number"],
        "company": client_name,
        "user": values.get("buyer_user") or "",
        "phone": "",
        "email": "",
        "planta": "",
        "area": "",
        "location": "",
        "client_id": values["client_id"],
        "emp_id": user,
        **_OCD_DEFAULTS,
        "currency": values.get("currency") or _OCD_DEFAULTS["currency"],
    }
    flag, error, id_quotation = create_quotation(metadata, data_token, status=QUOTATION_STATUS_TENDER)
    if not flag or not isinstance(id_quotation, int) or id_quotation <= 0:
        raise _ApiError({"data": None, "msg": "No se pudo crear la cotización de la licitación", "error": [error]}, 400)

    # 2) La licitación. Si falla, se borra la cotización recién creada.
    row_values = {k: values.get(k) for k in _FIELD_KEYS}
    history = [_history_entry(user, timestamp, "Creación", f"Licitación creada con la cotización {id_quotation}.")]
    flag, error, id_tender = insert_tender(row_values, id_quotation, user, timestamp, history, data_token)
    if not flag or not isinstance(id_tender, int) or id_tender <= 0:
        delete_quotation(id_quotation, data_token)
        if is_duplicate_error(error):
            _check_number_free(values["tender_number"], None, data_token)  # 409 con el id ganador
            _bad("La licitación choca con otra (número o contrato)", [error], code=409)
        _bad("No se pudo crear la licitación; cotización revertida", [error])

    msg = f"Licitación {values['tender_number']} creada (ID {id_tender}, cotización {id_quotation}) por {data_token.get('name')}"
    create_notification_permission(msg, data_token, ["administracion"], "Licitación Creada", user, 0)
    write_log_file(log_file_admin, msg, data_token)
    return {
        "data": {"id_tender": id_tender, "id_quotation": id_quotation},
        "msg": f"Licitación {values['tender_number']} creada",
        "error": None,
    }, 201


# --- PUT -------------------------------------------------------------------------
def _changes(current: dict, incoming: dict) -> dict:
    """Solo lo que de verdad cambia (fechas/montos comparados ya normalizados)."""
    out = {}
    for key, value in incoming.items():
        before = current.get(key)
        if key in _AMOUNT_KEYS:
            before = Decimal(str(before)).quantize(Decimal("0.01")) if before is not None else None
        if before != value:
            out[key] = value
    return out


@_api_guard
def update_tender_from_api(raw: dict, data_token):
    now = _now()
    timestamp = now.strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_tender = _require_int(raw.get("id_tender"), "id_tender")
    current = _load_tender(id_tender, data_token)
    errors: list = []
    incoming = _normalize(raw, _FIELD_KEYS + ("currency",), errors)
    if errors:
        _bad("Datos inválidos", errors)
    currency = incoming.pop("currency", None)
    changes = _changes(current, incoming)
    if currency is not None and currency != current.get("currency"):
        changes["currency"] = currency

    resulting = {**current, **changes}
    errors = _rule_errors(resulting)
    if "client_id" in changes and current.get("contract_id") and resulting.get("contract_id"):
        errors.append("el cliente no se cambia con contrato ligado: desliga el contrato primero")
    if errors:
        _bad("Datos inválidos", errors)
    if not changes:
        return {"data": current, "msg": "Sin cambios", "error": None}, 200

    client_name = None
    if "client_id" in changes:
        client_name = _client_name(changes["client_id"], data_token)
    if "tender_number" in changes:
        _check_number_free(changes["tender_number"], id_tender, data_token)
    if changes.get("contract_id"):
        _check_contract(changes["contract_id"], resulting["client_id"], id_tender, data_token)

    columns = {k: v for k, v in changes.items() if k != "currency"}
    diff = [
        {"field": k, "before": _json_safe(current.get(k)), "after": _json_safe(v)}
        for k, v in changes.items()
    ]
    entry = _history_entry(user, timestamp, "Actualización", "Actualización de la licitación.", diff)
    flag, error, _ = update_tender(id_tender, columns, entry, timestamp, data_token)
    if not flag:
        if is_duplicate_error(error):
            _bad("La licitación choca con otra (número o contrato)", [error], code=409)
        _bad("No se pudo actualizar la licitación", [error])

    # Sincronía con la cotización interna (solo las llaves espejo que cambiaron).
    sync = {_QUOTATION_SYNC[k]: v for k, v in changes.items() if k in _QUOTATION_SYNC}
    if "user" in sync and sync["user"] is None:
        sync["user"] = ""
    if client_name is not None:
        sync["company"] = client_name
    sync_error = None
    if sync:
        flag, sync_error, _ = set_quotation_metadata_keys(current["quotation_id"], sync, data_token)
        if flag:
            sync_error = None
    msg = f"Licitación {resulting['tender_number']} (ID {id_tender}) actualizada por {data_token.get('name')}: {', '.join(changes)}"
    write_log_file(log_file_admin, msg + (f" · sync cotización falló: {sync_error}" if sync_error else ""), data_token)
    updated = _load_tender(id_tender, data_token)
    updated.pop("history", None)
    return {
        "data": updated,
        "msg": f"Licitación {resulting['tender_number']} actualizada",
        "error": [f"No se pudo sincronizar la cotización {current['quotation_id']}: {sync_error}"] if sync_error else None,
    }, 200


# --- PUT /tender/items -----------------------------------------------------------
@_api_guard
def update_tender_items_from_api(data: dict, data_token):
    """Upsert de partidas sobre la cotización interna, mismo contrato que PUT /quotation."""
    timestamp = _now().strftime(format_timestamps)
    id_tender = data["id_tender"]
    tender = _load_tender(id_tender, data_token)
    id_quotation = tender["quotation_id"]
    flag, error, result = get_quotation(data_token=data_token, id_quotation=id_quotation)
    if not flag or len(result) == 0:
        _bad("No se pudieron leer las partidas de la licitación", [error])
    dict_products = _dict_products_from_quotation(result[0])
    # Con contrato ya creado sobre esta cotización, las partidas nuevas nacen con su contract_id.
    _, _, contract_id = get_contract_id_by_quotation(id_quotation, data_token)
    products = data.get("products") or []
    # delivery_date por partida: formato y nunca después del due_date de la OCD
    # (docs/ocd_reglas_po_vencimiento.md).
    quotation_meta = _load_json(result[0][1], {}) or {}
    date_errors = items_delivery_date_errors(products, quotation_meta.get("due_date"))
    if date_errors:
        _bad("Fechas de entrega de partidas inválidas", date_errors)
    flag_list, error_list, _result_list, counts, items_out = update_items_quotation_from_api(
        products, id_quotation, contract_id, dict_products, data_token
    )
    if flag_list and flag_list.count(False) == len(flag_list):
        _bad("No se pudo actualizar ninguna partida de la licitación", error_list)
    error_items = [e for f, e in zip(flag_list, error_list) if not f] or None
    resumen = _msg_items_counts(counts)
    entry = _history_entry(data_token.get("emp_id"), timestamp, "Partidas", f"Partidas: {resumen}.")
    append_tender_history(id_tender, entry, timestamp, data_token)
    write_log_file(
        log_file_admin,
        f"Partidas de la licitación {tender['tender_number']} (ID {id_tender}) por {data_token.get('name')}: {resumen}",
        data_token,
    )
    msg = f"Partidas de la licitación actualizadas: {resumen}"
    if error_items:
        msg += f". {len(error_items)} partidas no se pudieron guardar."
    return {
        "data": {"id_tender": id_tender, "id_quotation": id_quotation, "items": items_out},
        "msg": msg,
        "error": error_items,
    }, 200
