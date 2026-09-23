# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 11/sep./2026  at 12:00 $"

"""Control de saldos (Cobranza): cabecera (con o sin contrato) con formato FO-CXC
del catalogo de SGI (iso_formats), columnas dinamicas (custom_fields) y movimientos
de saldo inmutables. Ver Docs/control_saldos_cabecera.md y
Docs/control_saldos_sin_contrato.md.

Reglas:
  * Con contrato: un control ACTIVO por contrato (validado aqui; un cancelado no
    bloquea). Sin contrato (contract_id NULL): client_id + title obligatorios y
    sin unicidad. contract_id / client_id / format_id son inmutables.
  * Membresia remision -> control = activity_reports.balance_control_id (UNICA
    llave). Reglas de adopcion en _check_adoptable (POST y PUT /remissions):
    mismo cliente; control con contrato acepta remisiones de ese contrato o sin
    contrato (se les asigna); control sin contrato solo remisiones sin contrato;
    una remision en OTRO control activo se rechaza (uno cancelado no cuenta).
  * Cancelar NO libera remisiones: siguen apuntando al control cancelado y se
    re-adoptan sin paso previo.
  * Campos propios del formato viven en extra_info del control y se validan
    contra iso_formats.config.header_fields (llave declarada, tipo, opciones).
  * contracted_amount solo se fija en el POST (movimiento inicial); el PUT lo
    rechaza. Despues solo se mueve con POST /balanceControl/movement (tipo 1
    INYECCION > 0 o 2 AJUSTE != 0, saldo resultante nunca < 0), con bloqueo
    optimista sobre el monto leido (409 si otro movimiento gano la carrera).
  * custom_fields: [{key, label, value_type, comment}], orden = orden de columnas;
    key unica y sin chocar con columnas/campos del formato. Los VALORES por
    remision viven en activity_reports.extra_info.custom_fields (PUT /remissionBalance).
"""

import functools
import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytz

from static.constants import (
    format_timestamps,
    log_file_admin_collecions,
    timezone_software,
)
from templates.controllers.contracts.contracts_controller import get_contract
from templates.controllers.purchases.balance_control_controller import (
    CONTROL_COLUMNS,
    FORMAT_COLUMNS,
    MOVEMENT_COLUMNS,
    attach_remission_to_control,
    delete_balance_control,
    detach_remission_from_control,
    get_active_balance_control_by_contract,
    get_balance_control_by_id,
    get_balance_control_movements,
    get_balance_controls,
    get_customer_name,
    get_free_remissions_by_contract,
    get_iso_format_by_id,
    get_iso_formats,
    get_remissions_by_ids,
    get_remissions_summary_by_control,
    insert_balance_control,
    insert_balance_control_movement,
    remove_custom_field_keys_from_remissions,
    set_active_balance_control,
    update_balance_control_custom_fields,
    update_balance_control_header,
    update_balance_control_amount_optimistic,
    update_balance_control_history,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file

# --- Catalogos ------------------------------------------------------------------
VALUE_TYPES = ("text", "number", "date", "boolean")
CURRENCIES = ("MXN", "USD")
MOVEMENT_TYPES = {0: "INICIAL", 1: "INYECCION", 2: "AJUSTE"}
FORMAT_KIND = "balance_control"

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,49}$")
_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# Base editable de la cabecera (columnas reales). contract_id / client_id /
# format_id / contracted_amount NO estan: inmutables tras el POST (ver docstring).
_BASE_COLS = (
    "title",
    "month_period",
    "currency",
    "contract_number",
    "pedido_exiros",
    "start_date",
    "end_date",
    "plant",
    "coordinator",
    "contract_object",
)
_DATE_COLS = ("start_date", "end_date")
# Llaves que el POST acepta en metadata ademas de la base y los campos del formato.
_POST_ONLY_KEYS = ("contract_id", "client_id", "format_id", "contracted_amount")
_PUT_ID_KEYS = ("id_control", "id")
# Llaves reservadas: una columna dinamica no puede usar el nombre de una columna
# real del control ni de una llave aplanada de la remision.
_RESERVED_BASE_KEYS = set(CONTROL_COLUMNS) | {
    "id", "custom_fields", "remissions", "items", "history", "files",
    "balance_control_id", "balance_control_active",
}

_PERM_NOTIFY = ["administracion"]


# --- Helpers genericos -----------------------------------------------------------
class _ApiError(Exception):
    """Corta el flujo del midleware con un envelope {data, msg, error} + codigo listo."""

    def __init__(self, envelope: dict, code: int):
        super().__init__(envelope.get("msg"))
        self.response = (envelope, code)


def _api_guard(fn):
    """Convierte _ApiError en el (envelope, code) que devuelven todas las *_from_api."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except _ApiError as exc:
            return exc.response

    return wrapper


def _now():
    return datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software))


def _json_safe(value) -> Any:
    if isinstance(value, datetime):
        return value.strftime(format_timestamps)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _load_json(value, default) -> Any:
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


def _format_to_dict(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(FORMAT_COLUMNS, row)}
    config = _load_json(data.get("config"), None)
    data["config"] = config if isinstance(config, dict) else None
    data["history"] = _load_json(data.get("history"), [])
    data["label"] = f"{data.get('code')} {data.get('revision')}".strip()
    return data


def _movement_to_dict(row) -> dict:
    data = {col: _json_safe(val) for col, val in zip(MOVEMENT_COLUMNS, row)}
    data["extra_info"] = _load_json(data.get("extra_info"), {})
    mov_type = data.get("type")
    data["type_label"] = MOVEMENT_TYPES.get(int(mov_type), "") if mov_type is not None else ""
    return data


def _control_to_dict(row, header_keys=None) -> dict:
    """Fila del SELECT -> dict JSON-safe. Aplana los campos del formato
    (header_keys) desde extra_info al nivel superior, como el GET de remisiones."""
    data = {col: _json_safe(val) for col, val in zip(CONTROL_COLUMNS, row)}
    data["custom_fields"] = _load_json(data.get("custom_fields"), []) or []
    data["history"] = _load_json(data.get("history"), []) or []
    extra = _load_json(data.get("extra_info"), {})
    data["extra_info"] = extra if isinstance(extra, dict) else {}
    data["format_label"] = f"{data.get('format_code') or ''} {data.get('format_revision') or ''}".strip()
    for key in header_keys or []:
        data[key] = data["extra_info"].get(key)
    return data


def _header_fields(config: dict | None) -> list:
    if not isinstance(config, dict):
        return []
    fields = config.get("header_fields") or []
    return [f for f in fields if isinstance(f, dict) and f.get("key")]


def _reserved_keys(config: dict | None) -> set:
    """Llaves con las que una columna dinamica NO puede chocar (regla 7.3)."""
    reserved = set(_RESERVED_BASE_KEYS)
    if isinstance(config, dict):
        for col in config.get("columns") or []:
            if isinstance(col, dict):
                if col.get("key"):
                    reserved.add(str(col["key"]))
                if col.get("source_key"):
                    reserved.add(str(col["source_key"]))
        for field in _header_fields(config):
            reserved.add(str(field["key"]))
    return reserved


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    text = str(value).strip().lower()
    if text in ("1", "true", "si", "sí", "yes", "y", "s"):
        return True
    if text in ("0", "false", "no", "n"):
        return False
    return None


def coerce_value(value, value_type: str):
    """Coerciona un valor al tipo declarado. Devuelve (ok, valor, error).
    None / "" -> (True, None, None): significa 'vaciar'."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return True, None, None
    if value_type == "number":
        if isinstance(value, bool):
            return False, None, "se esperaba un número"
        try:
            return True, float(value), None
        except (ValueError, TypeError):
            return False, None, "se esperaba un número"
    if value_type == "date":
        if isinstance(value, datetime):
            return True, value.strftime("%Y-%m-%d"), None
        if isinstance(value, date):
            return True, value.isoformat(), None
        text = str(value).strip()[:10]
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return False, None, "se esperaba una fecha YYYY-MM-DD"
        return True, text, None
    if value_type == "boolean":
        parsed = _to_bool(value)
        if parsed is None:
            return False, None, "se esperaba true/false"
        return True, parsed, None
    # text
    return True, str(value).strip(), None


def validate_custom_fields(custom_fields, reserved: set):
    """Valida/normaliza la lista de columnas dinamicas. Devuelve (errores, lista)."""
    errors = []
    normalized = []
    seen = set()
    if custom_fields is None:
        custom_fields = []
    if not isinstance(custom_fields, list):
        return ["custom_fields debe ser una lista"], []
    for idx, field in enumerate(custom_fields):
        if not isinstance(field, dict):
            errors.append(f"custom_fields[{idx}] debe ser un objeto")
            continue
        key = str(field.get("key") or "").strip()
        label = str(field.get("label") or "").strip()
        value_type = str(field.get("value_type") or "").strip()
        comment = str(field.get("comment") or "").strip()
        if not key:
            errors.append(f"custom_fields[{idx}]: falta key")
            continue
        if not _KEY_RE.match(key):
            errors.append(f"custom_fields[{idx}]: key '{key}' inválida (snake_case, inicia con letra, máx. 50)")
            continue
        if key in seen:
            errors.append(f"custom_fields: key '{key}' repetida")
            continue
        if key in reserved:
            errors.append(f"custom_fields: key '{key}' choca con una columna del formato")
            continue
        if not label:
            errors.append(f"custom_fields[{idx}] ('{key}'): falta label")
            continue
        if value_type not in VALUE_TYPES:
            errors.append(f"custom_fields[{idx}] ('{key}'): value_type '{value_type}' fuera de {list(VALUE_TYPES)}")
            continue
        seen.add(key)
        normalized.append({"key": key, "label": label, "value_type": value_type, "comment": comment})
    return errors, normalized


def _coerce_header_extra(raw_metadata: dict, header_fields: list, current: dict | None = None):
    """Campos propios del formato presentes en el JSON crudo -> extra_info.
    Devuelve (errores, updates). Con current (PUT) solo toca lo enviado."""
    errors = []
    updates = {}
    for field in header_fields:
        key = field["key"]
        if key not in raw_metadata:
            continue
        ok, value, err = coerce_value(raw_metadata.get(key), str(field.get("value_type") or "text"))
        if not ok:
            errors.append(f"{key}: {err}")
            continue
        options = field.get("options")
        if value is not None and isinstance(options, list) and options and value not in options:
            errors.append(f"{key}: '{value}' fuera de las opciones {options}")
            continue
        updates[key] = value
    return errors, updates


def _validate_base(metadata: dict, raw_metadata: dict, is_put: bool):
    """Valida tipos/formatos de la base. Devuelve (errores, dict de columnas presentes)."""
    errors = []
    base = {}
    for col in _BASE_COLS:
        if is_put and col not in raw_metadata:
            continue
        value = metadata.get(col)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            base[col] = "MXN" if col == "currency" else None
            continue
        value = str(value).strip()
        if col == "currency":
            value = value.upper()
            if value not in CURRENCIES:
                errors.append(f"currency '{value}' fuera de {list(CURRENCIES)}")
                continue
        elif col == "month_period":
            if not _PERIOD_RE.match(value):
                errors.append(f"month_period '{value}' debe ser YYYY-MM")
                continue
        elif col in _DATE_COLS:
            ok, value, err = coerce_value(value, "date")
            if not ok:
                errors.append(f"{col}: {err}")
                continue
        base[col] = value
    if base.get("start_date") and base.get("end_date") and base["end_date"] < base["start_date"]:
        errors.append("end_date no puede ser anterior a start_date")
    return errors, base


def _unknown_keys(raw_metadata: dict, allowed: set) -> list:
    return sorted(k for k in raw_metadata.keys() if k not in allowed)


def _diff(old: dict, new: dict, fields) -> list:
    changes = []
    for field in fields:
        before = _json_safe(old.get(field))
        after = _json_safe(new.get(field))
        if isinstance(before, float) or isinstance(after, float):
            try:
                if before is not None and after is not None and float(before) == float(after):
                    continue
            except (TypeError, ValueError):
                pass
        if (before in (None, "")) and (after in (None, "")):
            continue
        if before != after:
            changes.append({"field": field, "before": before, "after": after})
    return changes


def _load_balance_format(format_id, data_token) -> dict:
    """Formato de control de saldos activo (dict). Lanza _ApiError si no aplica."""
    flag, error, row = get_iso_format_by_id(format_id, data_token)
    if not flag:
        raise _ApiError({"data": None, "msg": "Error al consultar el formato", "error": error}, 400)
    if row is None:
        raise _ApiError({"data": None, "msg": f"No existe el formato (ID {format_id})", "error": "Formato no encontrado"}, 404)
    fmt = _format_to_dict(row)
    if int(fmt.get("is_active") or 0) != 1:
        raise _ApiError({"data": None, "msg": f"El formato {fmt['label']} está retirado", "error": "Formato inactivo"}, 400)
    if not isinstance(fmt.get("config"), dict) or fmt["config"].get("kind") != FORMAT_KIND:
        raise _ApiError({"data": None, "msg": f"El formato {fmt['label']} no es de control de saldos", "error": "Formato sin config de control de saldos"}, 400)
    return fmt


def _load_control(id_control, data_token) -> tuple[dict, dict]:
    """(control, formato) por id. Lanza _ApiError si no existe."""
    flag, error, row = get_balance_control_by_id(id_control, data_token)
    if not flag:
        raise _ApiError({"data": None, "msg": "Error al consultar el control", "error": error}, 400)
    if row is None:
        raise _ApiError({"data": None, "msg": f"No existe el control (ID {id_control})", "error": "Control no encontrado"}, 404)
    flag, error, fmt_row = get_iso_format_by_id(row[CONTROL_COLUMNS.index("format_id")], data_token)
    fmt = _format_to_dict(fmt_row) if flag and fmt_row is not None else {"config": None, "label": ""}
    config = fmt.get("config")
    header_keys = [f["key"] for f in _header_fields(config if isinstance(config, dict) else None)]
    return _control_to_dict(row, header_keys), fmt


def _resolve_id(data: dict):
    for key in _PUT_ID_KEYS:
        if data.get(key):
            return int(data[key])
    return None


# --- Membresia: reglas de adopcion (un solo lugar para POST y PUT /remissions) -----
def _int_or_none(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _check_adoptable(control_contract_id, control_client_id, id_control, row):
    """Motivo (str) por el que la remision NO puede entrar al control, o None si
    puede. `row` = fila REMISSION_LINK_COLUMNS. `id_control` = None en el POST
    (el control aun no existe)."""
    _rid, r_contract, _history, r_client, r_control, r_active = row[:6]
    r_contract = _int_or_none(r_contract)
    r_client = _int_or_none(r_client)
    r_control = _int_or_none(r_control)
    if r_control is not None and r_control != id_control and int(r_active or 0) == 1:
        return f"pertenece al control activo {r_control}"
    if r_client != _int_or_none(control_client_id):
        return f"cliente distinto ({r_client} ≠ {control_client_id})"
    if control_contract_id:
        if r_contract not in (None, int(control_contract_id)):
            return f"pertenece a otro contrato ({r_contract})"
    elif r_contract is not None:
        return f"tiene contrato ({r_contract}); un control sin contrato solo acepta remisiones sin contrato"
    return None


def _attach_rows(id_control: int, control_contract_id, label: str, rows, timestamp, user, data_token):
    """Liga las remisiones al control (history en cada una). No fatal por
    remision: devuelve (ids ligados, errores)."""
    attached = []
    errors = []
    for row in rows:
        rid, r_contract, rem_history, _client, r_control = row[:5]
        if _int_or_none(r_control) == id_control:
            continue  # ya estaba en este control
        changes = [{"field": "balance_control_id", "before": r_control, "after": id_control}]
        if control_contract_id and r_contract is None:
            changes.append({"field": "contract_id", "before": None, "after": int(control_contract_id)})
        rem_history = _load_json(rem_history, []) or []
        rem_history.append({
            "timestamp": timestamp,
            "user": user,
            "action": "Adopción a control de saldos",
            "comment": f"Ligada al control de saldos {id_control} ({label}).",
            "changes": {"metadata": changes, "items": []},
        })
        flag, error, rowcount = attach_remission_to_control(
            rid, id_control, int(control_contract_id) if control_contract_id else None, rem_history, data_token
        )
        if flag and rowcount:
            attached.append(rid)
        else:
            errors.append(f"remisión {rid} no ligada: {error or 'otro control activo la tomó antes'}")
    return attached, errors


def resolve_balance_control_for_remission(contract_id, client_id, data_token):
    """Auto-enlace al CREAR una remision: id del control ACTIVO de su contrato, o
    None (sin contrato, contrato sin control activo, o cliente distinto al del
    control). Nunca falla: un error de consulta solo deja la remision sin ligar."""
    contract_id = _int_or_none(contract_id)
    if not contract_id or contract_id <= 0:
        return None
    flag, _error, row = get_active_balance_control_by_contract(contract_id, data_token)
    if not flag or row is None:
        return None
    control_client = _int_or_none(row[CONTROL_COLUMNS.index("client_id")])
    if control_client is not None and _int_or_none(client_id) != control_client:
        return None
    return int(row[0])


# --- Catalogos ------------------------------------------------------------------
def get_balance_control_catalogs_from_api(data_token):
    flag, error, rows = get_iso_formats(data_token, only_active=True)
    if not flag:
        return {"data": None, "msg": "Error al consultar los formatos", "error": error}, 400
    formats = [_format_to_dict(r) for r in rows]
    balance_formats = [f for f in formats if isinstance(f.get("config"), dict) and f["config"].get("kind") == FORMAT_KIND]
    return {
        "data": {
            "formats": balance_formats,
            "value_types": list(VALUE_TYPES),
            "currencies": list(CURRENCIES),
            "movement_types": [{"code": k, "label": v} for k, v in MOVEMENT_TYPES.items()],
        },
        "msg": None,
        "error": None,
    }, 200


# --- POST -----------------------------------------------------------------------
@_api_guard
def create_balance_control_from_api(data, raw_payload, data_token):
    now = _now()
    timestamp = now.strftime(format_timestamps)
    today = now.strftime("%Y-%m-%d")
    user = data_token.get("emp_id")
    user_name = data_token.get("name")
    metadata = data.get("metadata") or {}
    raw_metadata = (raw_payload or {}).get("metadata") or {}
    if not isinstance(raw_metadata, dict):
        return {"data": None, "msg": "Estructura de datos inválida", "error": "metadata debe ser un objeto"}, 400

    contract_id = int(metadata.get("contract_id") or 0)
    format_id = int(metadata.get("format_id") or 0)
    client_id_in = int(metadata.get("client_id") or 0)
    if format_id <= 0:
        return {"data": None, "msg": "Falta format_id", "error": "format_id es obligatorio"}, 400

    # Rama CON contrato: cliente y defaults salen del contrato; 1 activo por contrato.
    # Rama SIN contrato (contract_id 0/null/ausente): client_id + title obligatorios.
    contract_code = None
    contract_meta = {}
    contract_identifier = None
    if contract_id > 0:
        flag, error, contract = get_contract(data_token, contract_id)
        if not flag or not contract:
            return {"data": None, "msg": f"No existe el contrato (ID {contract_id})", "error": error or "Contrato no encontrado"}, 404
        contract_code = contract[5]
        contract_meta = _load_json(contract[1], {})
        contract_meta = contract_meta if isinstance(contract_meta, dict) else {}
        contract_identifier = str(contract_meta.get("identifier") or "").strip() or None
        client_id = int(contract[6])
        if client_id_in > 0 and client_id_in != client_id:
            return {
                "data": None,
                "msg": "client_id no coincide con el cliente del contrato",
                "error": [f"client_id {client_id_in} ≠ cliente del contrato {contract_code} ({client_id})"],
            }, 400
    else:
        contract_id = 0
        client_id = client_id_in
        missing = []
        if client_id <= 0:
            missing.append("client_id es obligatorio en un control sin contrato")
        if not str(metadata.get("title") or "").strip():
            missing.append("title es obligatorio en un control sin contrato")
        if missing:
            return {"data": None, "msg": "Faltan datos del control sin contrato", "error": missing}, 400
    flag, error, client_name = get_customer_name(client_id, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el cliente", "error": error}, 400
    if client_name is None:
        return {"data": None, "msg": f"No existe el cliente (ID {client_id})", "error": "Cliente no encontrado"}, 404

    # Formato de control de saldos
    fmt = _load_balance_format(format_id, data_token)
    header_fields = _header_fields(fmt["config"])
    header_keys = {f["key"] for f in header_fields}

    # Unicidad: un control ACTIVO por contrato (sin contrato no hay unicidad)
    if contract_id > 0:
        flag, error, existing = get_active_balance_control_by_contract(contract_id, data_token)
        if not flag:
            return {"data": None, "msg": "Error al consultar controles del contrato", "error": error}, 400
        if existing is not None:
            existing_id = existing[0]
            return {
                "data": {"id_control": existing_id},
                "msg": f"El contrato {contract_code} ya tiene un control de saldos activo (ID {existing_id})",
                "error": "Control duplicado",
            }, 409

    # Llaves desconocidas en metadata -> 400 (nada se descarta en silencio)
    allowed = set(_BASE_COLS) | set(_POST_ONLY_KEYS) | header_keys
    unknown = _unknown_keys(raw_metadata, allowed)
    if unknown:
        return {"data": None, "msg": "metadata trae llaves que el formato no declara", "error": [f"llave desconocida: {k}" for k in unknown]}, 400

    errors, base = _validate_base(metadata, raw_metadata, is_put=False)
    errors_extra, extra_info = _coerce_header_extra(raw_metadata, header_fields)
    errors.extend(errors_extra)

    amount = metadata.get("contracted_amount")
    try:
        amount = float(amount) if amount is not None else 0.0
    except (ValueError, TypeError):
        errors.append("contracted_amount debe ser numérico")
        amount = 0.0
    if amount < 0:
        errors.append("contracted_amount no puede ser negativo")

    errors_cf, custom_fields = validate_custom_fields(data.get("custom_fields") or [], _reserved_keys(fmt["config"]))
    errors.extend(errors_cf)
    if errors:
        return {"data": None, "msg": "Datos del control inválidos", "error": errors}, 400

    if contract_id > 0:
        if not base.get("title"):
            base["title"] = contract_identifier or contract_code
        if not base.get("contract_number"):
            base["contract_number"] = contract_code
        if not base.get("pedido_exiros") and contract_meta.get("exiros"):
            base["pedido_exiros"] = str(contract_meta["exiros"]).strip() or None
    label = f"contrato {contract_code}" if contract_id > 0 else f"sin contrato, {client_name}: {base.get('title')}"

    # Remisiones explicitas: TODAS deben ser adoptables o no se crea nada.
    remission_ids = list(dict.fromkeys(int(r) for r in (data.get("remissions") or []) if r is not None))
    rows_by_id = {}
    if remission_ids:
        flag, error, rows = get_remissions_by_ids(remission_ids, data_token)
        if not flag:
            return {"data": None, "msg": "Error al consultar las remisiones", "error": error}, 400
        found = {r[0]: r for r in rows}
        rem_errors = []
        for rid in remission_ids:
            if rid not in found:
                rem_errors.append(f"remisión {rid}: no existe")
                continue
            reason = _check_adoptable(contract_id, client_id, None, found[rid])
            if reason:
                rem_errors.append(f"remisión {rid}: {reason}")
        if rem_errors:
            return {"data": None, "msg": "Remisiones inválidas para este control", "error": rem_errors}, 400
        rows_by_id = {rid: found[rid] for rid in remission_ids}

    # Auto-adopcion (solo con contrato): las remisiones del contrato que esten
    # libres o en un control cancelado. Las no adoptables (p.ej. otro cliente) se
    # reportan en `error` sin bloquear el alta.
    partial_errors = []
    if contract_id > 0:
        flag, error, free_rows = get_free_remissions_by_contract(contract_id, data_token)
        if not flag:
            partial_errors.append(f"no se pudieron consultar las remisiones del contrato: {error}")
            free_rows = []
        for r in free_rows:
            if r[0] in rows_by_id:
                continue
            reason = _check_adoptable(contract_id, client_id, None, r)
            if reason:
                partial_errors.append(f"remisión {r[0]} del contrato no adoptada: {reason}")
            else:
                rows_by_id[r[0]] = r

    history = [{
        "user": user,
        "action": "Creación",
        "date": timestamp,
        "comment": f"Creación del control de saldos ({fmt['label']}): {label}.",
    }]
    row = {
        "contract_id": contract_id if contract_id > 0 else None,
        "format_id": format_id,
        "client_id": client_id,
        **base,
        "contracted_amount": amount,
        "custom_fields": custom_fields,
        "is_active": 1,
        "created_by": user,
        "timestamp": timestamp,
        "history": history,
        "extra_info": extra_info,
    }
    flag, error, new_id = insert_balance_control(row, data_token)
    if not flag or not isinstance(new_id, int):
        return {"data": None, "msg": "No se pudo crear el control de saldos", "error": error}, 400
    id_control: int = new_id

    # Movimiento inicial (0 -> contracted_amount). Si falla, reversa del control.
    flag, error, id_movement = insert_balance_control_movement({
        "id_control": id_control,
        "type": 0,
        "movement_date": today,
        "amount": amount,
        "previous_balance": 0,
        "resulting_balance": amount,
        "user_id": user,
        "user_name": user_name,
        "reason": "Monto contratado inicial",
        "document": base.get("pedido_exiros"),
        "timestamp": timestamp,
    }, data_token)
    if not flag:
        delete_balance_control(id_control, data_token)
        write_log_file(log_file_admin_collecions, f"Reversa del control {id_control}: fallo el movimiento inicial ({error})", data_token)
        return {"data": None, "msg": "No se pudo registrar el movimiento inicial; el control no se creó", "error": error}, 400

    # Membresia (no fatal por remision)
    adopted, attach_errors = _attach_rows(
        id_control, contract_id, label, list(rows_by_id.values()), timestamp, user, data_token
    )
    partial_errors.extend(attach_errors)

    msg = f"Control de saldos creado correctamente (ID {id_control}, {fmt['label']}, {label})"
    if adopted:
        msg += f"; remisiones adoptadas: {adopted}"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Control de saldos", user or 0, 0)
    write_log_file(log_file_admin_collecions, msg + (f" | parciales: {partial_errors}" if partial_errors else ""), data_token)
    return {
        "data": {"id_control": id_control, "id_movement": id_movement, "adopted_remissions": adopted},
        "msg": msg,
        "error": partial_errors or None,
    }, 201


# --- GET ------------------------------------------------------------------------
def _to_int_or_none(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def get_balance_controls_from_api(params: dict, data_token):
    contract_id = _to_int_or_none(params.get("contract_id"))
    format_id = _to_int_or_none(params.get("format_id"))
    if str(params.get("all") or "").lower() in ("1", "true", "yes"):
        is_active = None
    else:
        is_active = _to_int_or_none(params.get("is_active"))
        is_active = 1 if is_active is None else is_active
    client_id = _to_int_or_none(params.get("client_id"))
    has_contract = _to_int_or_none(params.get("has_contract"))
    if has_contract is not None:
        has_contract = 1 if has_contract else 0
    flag, error, rows = get_balance_controls(
        contract_id, format_id, is_active, data_token, client_id=client_id, has_contract=has_contract
    )
    if not flag:
        return {"data": None, "msg": "Error al consultar los controles de saldos", "error": error}, 400
    # header_keys por formato (un solo fetch del catalogo)
    flag_f, _e, fmt_rows = get_iso_formats(data_token, only_active=False)
    keys_by_format = {}
    if flag_f:
        for r in fmt_rows:
            f = _format_to_dict(r)
            keys_by_format[f["id"]] = [h["key"] for h in _header_fields(f.get("config"))]
    data_out = [_control_to_dict(r, keys_by_format.get(r[CONTROL_COLUMNS.index("format_id")], [])) for r in rows]
    return {"data": data_out, "msg": None, "error": None}, 200


@_api_guard
def get_balance_control_from_api(id_control: int, data_token):
    control, fmt = _load_control(id_control, data_token)
    flag, error, mov_rows = get_balance_control_movements(id_control, data_token)
    movements = [_movement_to_dict(r) for r in mov_rows] if flag else []
    flag_r, error_r, rem_rows = get_remissions_summary_by_control(id_control, data_token)
    remissions = [
        {"id": r[0], "folio": r[1], "date": _json_safe(r[2]), "status": r[3]} for r in rem_rows
    ] if flag_r else []
    control["format"] = {
        "id": fmt.get("id"),
        "code": fmt.get("code"),
        "revision": fmt.get("revision"),
        "name": fmt.get("name"),
        "label": fmt.get("label"),
        "config": fmt.get("config"),
    }
    control["movements"] = movements
    control["remissions"] = remissions
    control["remissions_count"] = len(remissions)
    errors = [e for e in (error if not flag else None, error_r if not flag_r else None) if e]
    return {"data": control, "msg": None, "error": errors or None}, 200


# --- PUT parcial de cabecera ------------------------------------------------------
@_api_guard
def update_balance_control_from_api(data, raw_payload, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    metadata = data.get("metadata") or {}
    raw_metadata = (raw_payload or {}).get("metadata") or {}
    if not isinstance(raw_metadata, dict):
        return {"data": None, "msg": "Estructura de datos inválida", "error": "metadata debe ser un objeto"}, 400
    id_control = _resolve_id(metadata)
    if not id_control:
        return {"data": None, "msg": "Falta el id del control", "error": "id_control requerido"}, 400

    control, fmt = _load_control(id_control, data_token)
    if int(control.get("is_active") or 0) != 1:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control})", "error": "Control inactivo"}, 400

    # Inmutables: monto (solo con movimientos), contrato, cliente y formato.
    locked = [k for k in _POST_ONLY_KEYS if k in raw_metadata]
    if locked:
        return {
            "data": None,
            "msg": "contracted_amount, contract_id, client_id y format_id no se editan por este PUT",
            "error": [
                f"{k} es inmutable"
                + (" (el monto solo cambia con movimientos de saldo)" if k == "contracted_amount" else "")
                for k in locked
            ],
        }, 400

    header_fields = _header_fields(fmt.get("config"))
    allowed = set(_BASE_COLS) | set(_PUT_ID_KEYS) | {f["key"] for f in header_fields}
    unknown = _unknown_keys(raw_metadata, allowed)
    if unknown:
        return {"data": None, "msg": "metadata trae llaves que el formato no declara", "error": [f"llave desconocida: {k}" for k in unknown]}, 400

    errors, base_updates = _validate_base(metadata, raw_metadata, is_put=True)
    if "title" in base_updates and not base_updates["title"]:
        errors.append("title no puede quedar vacío")
    errors_extra, extra_updates = _coerce_header_extra(raw_metadata, header_fields)
    errors.extend(errors_extra)
    if errors:
        return {"data": None, "msg": "Datos del control inválidos", "error": errors}, 400

    merged = {col: control.get(col) for col in _BASE_COLS}
    merged.update(base_updates)
    if merged.get("start_date") and merged.get("end_date") and str(merged["end_date"]) < str(merged["start_date"]):
        return {"data": None, "msg": "Datos del control inválidos", "error": ["end_date no puede ser anterior a start_date"]}, 400
    extra_info = dict(control.get("extra_info") or {})
    extra_info.update(extra_updates)

    old_meta = {**{c: control.get(c) for c in _BASE_COLS}, **{f["key"]: (control.get("extra_info") or {}).get(f["key"]) for f in header_fields}}
    new_meta = {**merged, **{f["key"]: extra_info.get(f["key"]) for f in header_fields}}
    changes = _diff(old_meta, new_meta, list(old_meta.keys()))

    history = control.get("history") or []
    history.append({
        "user": user,
        "action": "Actualización",
        "date": timestamp,
        "comment": "Actualización de la cabecera del control de saldos.",
        "changes": changes,
    })
    merged["history"] = history
    merged["extra_info"] = extra_info
    flag, error, _ = update_balance_control_header(id_control, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el control", "error": error}, 400
    msg = f"Control de saldos actualizado correctamente (ID {id_control})"
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_control": id_control, "changes": changes}, "msg": msg, "error": None}, 200


# --- PUT columnas dinamicas (lista completa) ---------------------------------------
@_api_guard
def update_balance_control_fields_from_api(data, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _resolve_id(data)
    if not id_control:
        return {"data": None, "msg": "Falta el id del control", "error": "id_control requerido"}, 400

    control, fmt = _load_control(id_control, data_token)
    if int(control.get("is_active") or 0) != 1:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control})", "error": "Control inactivo"}, 400

    errors, custom_fields = validate_custom_fields(data.get("custom_fields") or [], _reserved_keys(fmt.get("config")))
    if errors:
        return {"data": None, "msg": "Columnas dinámicas inválidas", "error": errors}, 400

    old_fields = control.get("custom_fields") or []
    old_keys = [f.get("key") for f in old_fields if isinstance(f, dict)]
    new_keys = [f["key"] for f in custom_fields]
    removed = [k for k in old_keys if k not in new_keys]
    added = [k for k in new_keys if k not in old_keys]

    history = control.get("history") or []
    history.append({
        "user": user,
        "action": "Actualización",
        "date": timestamp,
        "comment": "Actualización de columnas dinámicas del control de saldos.",
        "changes": {"custom_fields": {"added": added, "removed": removed, "order": new_keys}},
    })
    flag, error, _ = update_balance_control_custom_fields(id_control, custom_fields, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron actualizar las columnas dinámicas", "error": error}, 400

    # Sweep: los valores de las columnas quitadas se borran de las remisiones
    # ligadas al control (si no, resucitan al re-crear una columna con el mismo key).
    swept = 0
    sweep_error = None
    if removed:
        flag, error, swept = remove_custom_field_keys_from_remissions(id_control, removed, data_token)
        if not flag:
            sweep_error = f"no se pudieron limpiar los valores de {removed} en las remisiones: {error}"
            write_log_file(log_file_admin_collecions, f"Control {id_control}: {sweep_error}", data_token)
            swept = 0

    msg = f"Columnas dinámicas del control actualizadas (ID {id_control}: +{len(added)} / -{len(removed)})"
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {
        "data": {
            "id_control": id_control,
            "custom_fields": custom_fields,
            "added_keys": added,
            "removed_keys": removed,
            "remissions_swept": swept,
        },
        "msg": msg,
        "error": [sweep_error] if sweep_error else None,
    }, 200


# --- Cancelacion suave -----------------------------------------------------------
@_api_guard
def cancel_balance_control_from_api(data, data_token):
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _resolve_id(data)
    if not id_control:
        return {"data": None, "msg": "Falta el id del control", "error": "id_control requerido"}, 400
    control, _fmt = _load_control(id_control, data_token)
    if int(control.get("is_active") or 0) == 0:
        return {"data": {"id_control": id_control}, "msg": f"El control ya estaba cancelado (ID {id_control})", "error": None}, 200
    history = control.get("history") or []
    history.append({
        "user": user,
        "action": "Cancelación",
        "date": timestamp,
        "comment": data.get("comment") or "Cancelación del control de saldos.",
    })
    flag, error, _ = set_active_balance_control(id_control, 0, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo cancelar el control", "error": error}, 400
    msg = f"Control de saldos cancelado (ID {id_control})"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Control de saldos", user or 0, 0)
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_control": id_control}, "msg": msg, "error": None}, 200


# --- Movimientos de saldo: POST /balanceControl/movement ----------------------------
def _money(value) -> Decimal:
    """Decimal a 2 decimales (contracted_amount es DECIMAL(15,2))."""
    return Decimal(str(value)).quantize(Decimal("0.01"))


@_api_guard
def create_balance_movement_from_api(data, data_token):
    """Inyeccion (1) o ajuste (2) de saldo sobre un control ACTIVO. Nunca toca
    movimientos previos: UPDATE optimista del monto de la cabecera + INSERT del
    movimiento; si el INSERT falla se revierte el monto (best-effort)."""
    now = _now()
    timestamp = now.strftime(format_timestamps)
    user = data_token.get("emp_id")
    user_name = data_token.get("name")
    id_control = _resolve_id(data)
    if not id_control:
        return {"data": None, "msg": "Falta el id del control", "error": "id_control requerido"}, 400
    control, _fmt = _load_control(id_control, data_token)
    if int(control.get("is_active") or 0) == 0:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control}); no admite movimientos", "error": "Control cancelado"}, 400

    errors = []
    mov_type = data.get("type")
    try:
        mov_type = int(mov_type)
    except (ValueError, TypeError):
        mov_type = -1
    if mov_type not in (1, 2):
        errors.append("type debe ser 1 (INYECCION) o 2 (AJUSTE)")
    amount = Decimal("0")
    if data.get("amount") is None:
        errors.append("amount requerido")
    else:
        try:
            amount = _money(data.get("amount"))
        except (ValueError, TypeError, ArithmeticError):
            errors.append("amount debe ser numérico")
    if mov_type == 1 and amount <= 0:
        errors.append("una INYECCION debe tener amount > 0")
    if mov_type == 2 and amount == 0:
        errors.append("un AJUSTE debe tener amount distinto de 0 (negativo para restar)")
    ok, movement_date, err = coerce_value(data.get("movement_date"), "date")
    if not ok:
        errors.append(f"movement_date: {err}")
    movement_date = movement_date or now.strftime("%Y-%m-%d")
    previous = _money(control.get("contracted_amount") or 0)
    expected = data.get("expected_balance")
    if expected is not None and expected != "":
        try:
            if _money(expected) != previous:
                return {
                    "data": {"id_control": id_control, "current_balance": float(previous)},
                    "msg": f"El saldo del control cambió (actual {previous}); recarga y vuelve a intentar",
                    "error": "expected_balance no coincide con el saldo actual",
                }, 409
        except (ValueError, TypeError, ArithmeticError):
            errors.append("expected_balance debe ser numérico")
    resulting = previous + amount
    if resulting < 0 and not errors:
        errors.append(f"el saldo resultante no puede ser negativo (actual {previous}, movimiento {amount})")
    if errors:
        return {"data": None, "msg": "Movimiento inválido", "error": errors}, 400

    label = MOVEMENT_TYPES[mov_type]
    reason = (data.get("reason") or "").strip() or None
    document = (data.get("document") or "").strip() or None
    history = control.get("history") or []
    history.append({
        "user": user,
        "action": f"Movimiento de saldo ({label})",
        "date": timestamp,
        "comment": f"{previous} -> {resulting} (monto {amount})" + (f"; {reason}" if reason else ""),
    })
    # 1) Cabecera con bloqueo optimista (0 filas = carrera perdida o cancelado en medio)
    flag, error, rows = update_balance_control_amount_optimistic(
        id_control, str(resulting), str(previous), history, data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el saldo del control", "error": error}, 400
    if not rows:
        return {
            "data": {"id_control": id_control},
            "msg": f"El saldo del control cambió mientras se registraba el movimiento (ID {id_control}); recarga y vuelve a intentar",
            "error": "Conflicto de concurrencia sobre contracted_amount",
        }, 409
    # 2) Movimiento (inmutable). Si falla, se regresa el monto.
    flag, error, id_movement = insert_balance_control_movement({
        "id_control": id_control,
        "type": mov_type,
        "movement_date": movement_date,
        "amount": str(amount),
        "previous_balance": str(previous),
        "resulting_balance": str(resulting),
        "user_id": user,
        "user_name": user_name,
        "reason": reason,
        "document": document,
        "timestamp": timestamp,
        "extra_info": data.get("extra_info") if isinstance(data.get("extra_info"), dict) else {},
    }, data_token)
    if not flag:
        history.pop()
        flag_r, error_r, _ = update_balance_control_amount_optimistic(
            id_control, str(previous), str(resulting), history, data_token
        )
        detail = error if flag_r else f"{error}; y no se pudo revertir el monto ({error_r})"
        write_log_file(log_file_admin_collecions, f"Movimiento de saldo fallido en control {id_control}: {detail}", data_token)
        return {"data": None, "msg": "No se pudo registrar el movimiento; el saldo no cambió", "error": detail}, 400

    msg = f"{label} registrada en el control (ID {id_control}): saldo {previous} -> {resulting} (movimiento ID {id_movement})"
    create_notification_permission(msg, data_token, _PERM_NOTIFY, "Control de saldos", user or 0, 0)
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {
        "data": {
            "id_control": id_control,
            "id_movement": id_movement,
            "type": mov_type,
            "type_label": label,
            "movement_date": movement_date,
            "amount": float(amount),
            "previous_balance": float(previous),
            "resulting_balance": float(resulting),
            "contracted_amount": float(resulting),
        },
        "msg": msg,
        "error": None,
    }, 201


# --- Membresia: PUT /balanceControl/remissions (add / remove) ------------------------
@_api_guard
def update_balance_control_remissions_from_api(data, data_token):
    """Agrega/quita remisiones de un control ACTIVO. Valida TODO antes de
    escribir (una sola falla -> 400 y no se aplica nada). `add` usa las mismas
    reglas que remissions[] del POST; una remision en OTRO control activo se
    rechaza (mover = remove explicito alla primero). `remove` no toca contract_id."""
    timestamp = _now().strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_control = _resolve_id(data)
    if not id_control:
        return {"data": None, "msg": "Falta el id del control", "error": "id_control requerido"}, 400
    add_ids = list(dict.fromkeys(int(r) for r in (data.get("add") or []) if r is not None))
    remove_ids = list(dict.fromkeys(int(r) for r in (data.get("remove") or []) if r is not None))
    if not add_ids and not remove_ids:
        return {"data": None, "msg": "Nada que hacer", "error": ["add y remove vienen vacíos"]}, 400
    both = [rid for rid in add_ids if rid in remove_ids]
    if both:
        return {"data": None, "msg": "Remisiones inválidas para este control", "error": [f"remisión {rid}: viene en add y en remove" for rid in both]}, 400

    control, _fmt = _load_control(id_control, data_token)
    if int(control.get("is_active") or 0) != 1:
        return {"data": None, "msg": f"El control está cancelado (ID {id_control})", "error": "Control inactivo"}, 400
    control_contract = control.get("contract_id")
    control_client = control.get("client_id")
    label = control.get("title") or control.get("contract_code") or ""

    flag, error, rows = get_remissions_by_ids(add_ids + remove_ids, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar las remisiones", "error": error}, 400
    found = {r[0]: r for r in rows}
    errors = []
    for rid in add_ids:
        if rid not in found:
            errors.append(f"remisión {rid}: no existe")
            continue
        reason = _check_adoptable(control_contract, control_client, id_control, found[rid])
        if reason:
            errors.append(f"remisión {rid}: {reason}")
    for rid in remove_ids:
        if rid not in found:
            errors.append(f"remisión {rid}: no existe")
        elif _int_or_none(found[rid][4]) != id_control:
            errors.append(f"remisión {rid}: no está en este control")
    if errors:
        return {"data": None, "msg": "Remisiones inválidas para este control", "error": errors}, 400

    added, write_errors = _attach_rows(
        id_control, control_contract, label, [found[rid] for rid in add_ids], timestamp, user, data_token
    )
    removed = []
    for rid in remove_ids:
        rem_history = _load_json(found[rid][2], []) or []
        rem_history.append({
            "timestamp": timestamp,
            "user": user,
            "action": "Retiro de control de saldos",
            "comment": f"Retirada del control de saldos {id_control} ({label}).",
            "changes": {"metadata": [{"field": "balance_control_id", "before": id_control, "after": None}], "items": []},
        })
        flag, error, rowcount = detach_remission_from_control(rid, id_control, rem_history, data_token)
        if flag and rowcount:
            removed.append(rid)
        else:
            write_errors.append(f"remisión {rid} no retirada: {error or 'ya no estaba en este control'}")
    if not added and not removed and write_errors:
        return {"data": None, "msg": "No se pudo aplicar ningún cambio de remisiones", "error": write_errors}, 400

    if added or removed:
        history = control.get("history") or []
        history.append({
            "user": user,
            "action": "Actualización",
            "date": timestamp,
            "comment": "Actualización de las remisiones del control de saldos.",
            "changes": {"remissions": {"added": added, "removed": removed}},
        })
        flag, error, _ = update_balance_control_history(id_control, history, data_token)
        if not flag:
            write_errors.append(f"no se pudo registrar el history del control: {error}")

    flag_r, _error_r, rem_rows = get_remissions_summary_by_control(id_control, data_token)
    msg = f"Remisiones del control actualizadas (ID {id_control}: +{len(added)} / -{len(removed)})"
    write_log_file(log_file_admin_collecions, msg + (f" | parciales: {write_errors}" if write_errors else ""), data_token)
    return {
        "data": {
            "id_control": id_control,
            "added": added,
            "removed": removed,
            "remissions_count": len(rem_rows) if flag_r else None,
        },
        "msg": msg,
        "error": write_errors or None,
    }, 200


# --- Valores de columnas dinamicas por remision (usado por PUT /remissionBalance) ---
def validate_remission_custom_fields(balance_control_id, custom_values, data_token):
    """Valida el dict {key: value} de una remision contra las columnas del control
    al que esta ligada (activity_reports.balance_control_id), que debe estar
    ACTIVO. Devuelve (errores, dict coercionado) donde None = borrar."""
    if not isinstance(custom_values, dict):
        return ["custom_fields debe ser un objeto {key: value}"], {}
    if not balance_control_id:
        return ["la remisión no está en ningún control de saldos"], {}
    flag, error, row = get_balance_control_by_id(int(balance_control_id), data_token)
    if not flag:
        return [f"error al consultar el control de saldos: {error}"], {}
    if row is None:
        return [f"no existe el control de saldos {balance_control_id}"], {}
    control = _control_to_dict(row)
    if int(control.get("is_active") or 0) != 1:
        return [f"el control {control['id_control']} está cancelado"], {}
    declared = {f["key"]: f for f in control.get("custom_fields") or [] if isinstance(f, dict) and f.get("key")}
    errors = []
    coerced = {}
    for key, value in custom_values.items():
        field = declared.get(str(key))
        if field is None:
            errors.append(f"custom_fields.{key}: columna no declarada en el control {control['id_control']}")
            continue
        ok, parsed, err = coerce_value(value, str(field.get("value_type") or "text"))
        if not ok:
            errors.append(f"custom_fields.{key}: {err}")
            continue
        coerced[str(key)] = parsed
    return errors, coerced
