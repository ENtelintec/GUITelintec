# -*- coding: utf-8 -*-
"""
Midleware del modulo CDA — Control de Estado de Vehiculos (FO-CDA-02 R3).

CRUD de las 6 tablas (vehicles + polizas/servicios/llantas/multas/compras) y
las vistas calculadas que replican las hojas del Excel. TODO campo derivado
(proximo mantenimiento, ¿requiere?, dias restantes, KPIs, refrendo AL DIA,
llanta vencida, pagos vencidos de poliza, TOTAL de compras, semana del año)
se computa aqui en los GET — nunca se almacena.

Reglas de mantenimiento (constantes abajo): aceite mineral cada 5,000 km,
sintetico cada 10,000 km; proxima fecha = ultima + 6 meses; requiere = km
actual >= proximo km O fecha proxima vencida.
"""
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026 $"

import calendar
import json
from datetime import date, datetime
from decimal import Decimal

import pytz

from static.constants import format_timestamps, log_file_cda, timezone_software
from templates.controllers.vehicles.vehicles_controller import (
    FINE_COLUMNS,
    POLICY_COLUMNS,
    PURCHASE_COLUMNS,
    SERVICE_COLUMNS,
    TIRE_COLUMNS,
    VEHICLE_COLUMNS,
    delete_fine,
    delete_policy,
    delete_service,
    delete_tire,
    delete_vehicle,
    delete_vehicle_purchase,
    get_fine_by_id,
    get_fines,
    get_policies,
    get_policy_by_id,
    get_service_by_id,
    get_services,
    get_tire_by_position,
    get_tires,
    get_vehicle_by_code,
    get_vehicle_by_id,
    get_vehicle_purchase_by_id,
    get_vehicle_purchases,
    get_vehicles_list,
    insert_fine,
    insert_policy,
    insert_service,
    insert_tire,
    insert_vehicle,
    insert_vehicle_purchase,
    set_active_vehicle,
    update_fine,
    update_policy,
    update_service,
    update_tire,
    update_vehicle,
    update_vehicle_km,
    update_vehicle_purchase,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file

# --- Catalogos (codigo -> etiqueta). GET /cda/catalogs los expone al front. ---
# Anotados como dict plano: las llaves llegan de datos (int | None) y pyrefly
# rechazaria .get(None) sobre dict[int, str].
VEHICLE_STATUS: dict = {0: "ACTIVO", 1: "DETENIDO", 2: "BAJA"}
OIL_TYPE: dict = {0: "MINERAL", 1: "SINTETICO"}
PAYMENT_FORM: dict = {0: "MENSUAL", 1: "TRIMESTRAL", 2: "ANUAL", 3: "CONTADO"}
SERVICE_TYPE: dict = {0: "MANTENIMIENTO", 1: "REPARACION", 2: "SERVICIO"}
TIRE_POSITION: dict = {
    0: "DELANTERA PILOTO",
    1: "DELANTERA COPILOTO",
    2: "TRASERA PILOTO",
    3: "TRASERA COPILOTO",
    4: "REPUESTO",
}
PURCHASE_STATUS: dict = {0: "PENDIENTE", 1: "COMPRADO", 2: "CANCELADO"}
ACCESSORY_KEYS = (
    "torreta_ambar",
    "luces",
    "sticker_acceso",
    "eslinga_matracas",
    "topes_bloqueo",
    "extintor",
    "gato",
    "llave_cruz",
    "triangulo",
    "limpiaparabrisas",
    "llanta_repuesto",
    "cables_corriente",
)

# --- Reglas de mantenimiento / pagos (constantes nombradas, no configurables) -
OIL_INTERVAL_KM: dict = {0: 5000, 1: 10000}  # mineral / sintetico
MAINTENANCE_INTERVAL_MONTHS = 6
PAYMENT_SLOTS: dict = {0: 12, 1: 4, 2: 1, 3: 1}  # mensual/trimestral/anual/contado
PAYMENT_PERIOD_MONTHS: dict = {0: 1, 1: 3, 2: 12, 3: 12}

_PERMISSIONS = ["administracion", "sgi"]

_VEHICLE_UPDATE_COLS = (
    "code", "model", "plate", "brand", "niv", "status", "oil_type",
    "current_km", "current_km_date", "rin_size", "tire_size",
    "refrendo_last_paid",
)
_POLICY_UPDATE_COLS = (
    "inciso", "insurer", "date_start", "date_end", "payment_form",
    "notification", "other_requirements",
)
_SERVICE_UPDATE_COLS = ("service_type", "date", "description", "km", "workshop", "cost")
_TIRE_UPDATE_COLS = (
    "dot", "manufacture_date", "brand", "expiry_date", "physical_state",
    "needs_change",
)
_FINE_UPDATE_COLS = ("year", "month", "amount", "description", "responsible")
_PURCHASE_UPDATE_COLS = (
    "checklist_sent", "checklist_sent_date", "problem", "quantity", "unit",
    "cost", "supplier", "observations", "status", "po_id",
)


# --- Helpers ------------------------------------------------------------------
def _now():
    return datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software))


def _today():
    return _now().date()


def _add_months(d: date, months: int) -> date:
    """Suma (o resta) meses calendario a una fecha, ajustando el dia al tope
    del mes destino (31/ene + 1 mes -> 28/feb)."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
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


def _to_date(value):
    """date/datetime/str(YYYY-MM-DD...) -> date | None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _to_int_or_none(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _row_to_dict(row, columns) -> dict:
    data = {col: _json_safe(val) for col, val in zip(columns, row)}
    if "history" in data:
        data["history"] = _load_json(data.get("history"), [])
    if "extra_info" in data:
        extra = _load_json(data.get("extra_info"), {})
        data["extra_info"] = extra if isinstance(extra, dict) else {}
    return data


def _vehicle_to_dict(row) -> dict:
    """Fila de vehicles -> dict enriquecido (labels + accesorios normalizados +
    refrendo derivado)."""
    data = _row_to_dict(row, VEHICLE_COLUMNS)
    data["status_label"] = VEHICLE_STATUS.get(data.get("status"))
    data["oil_type_label"] = OIL_TYPE.get(data.get("oil_type"))
    accessories = _load_json(data.get("accessories"), {})
    accessories = accessories if isinstance(accessories, dict) else {}
    data["accessories"] = {k: int(accessories.get(k) or 0) for k in ACCESSORY_KEYS}
    data["refrendo_status"] = _refrendo_status(data.get("refrendo_last_paid"), _today().year)
    data["refrendo_note"] = (data.get("extra_info") or {}).get("refrendo_note")
    return data


def _refrendo_status(refrendo_last_paid, year: int) -> str:
    paid = _to_date(refrendo_last_paid)
    if paid is None:
        return "SIN_REGISTRO"
    return "AL_DIA" if paid.year >= year else "VENCIDO"


def _validate_enums(payload: dict, checks, raw_payload=None):
    """checks: iterable de (key, catalogo). Con raw_payload solo valida las
    llaves presentes en el JSON crudo. Devuelve lista de errores o None."""
    errors = []
    for key, catalog in checks:
        if raw_payload is not None and key not in raw_payload:
            continue
        value = payload.get(key)
        if value is None:
            continue
        if value not in catalog:
            errors.append(f"{key}={value} no es un valor valido {sorted(catalog.keys())}")
    return errors or None


def _history_entry(user, action, comment):
    return {
        "user": user,
        "action": action,
        "date": _now().strftime(format_timestamps),
        "comment": comment,
    }


def _require_vehicle(vehicle_id, data_token) -> tuple:
    """Valida que el vehiculo exista. Devuelve (envelope_error | None, vehicle_dict);
    en error el dict va vacio (no usar)."""
    vid = _to_int_or_none(vehicle_id)
    if not vid:
        return {"data": None, "msg": "Falta vehicle_id", "error": "vehicle_id requerido"}, {}
    flag, error, row = get_vehicle_by_id(vid, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el vehículo", "error": error}, {}
    if not row:
        return {"data": None, "msg": f"No existe el vehículo (ID {vid})", "error": "No encontrado"}, {}
    return None, _vehicle_to_dict(row)


def _normalize_payments(payments, payment_form):
    """Lista de pagos -> slots normalizados [{n, date, amount, paid}] con el
    numero de slots derivado de la forma de pago."""
    slots = PAYMENT_SLOTS.get(payment_form, 1)
    by_n = {}
    for item in payments or []:
        if not isinstance(item, dict):
            continue
        n = _to_int_or_none(item.get("n"))
        if n is None or not (1 <= n <= slots):
            continue
        by_n[n] = {
            "n": n,
            "date": item.get("date") or None,
            "amount": item.get("amount"),
            "paid": 1 if item.get("paid") else 0,
        }
    return [
        by_n.get(n, {"n": n, "date": None, "amount": None, "paid": 0})
        for n in range(1, slots + 1)
    ]


def _policy_to_dict(row) -> dict:
    data = _row_to_dict(row, POLICY_COLUMNS)
    data["payment_form_label"] = PAYMENT_FORM.get(data.get("payment_form"))
    payments = _load_json(data.get("payments"), [])
    data["payments"] = _enrich_payments(
        payments if isinstance(payments, list) else [],
        data.get("payment_form"),
        data.get("date_start"),
    )
    return data


def _enrich_payments(payments, payment_form, date_start):
    """Agrega expected_date y overdue (calculados) a cada slot de pago."""
    start = _to_date(date_start)
    period = PAYMENT_PERIOD_MONTHS.get(payment_form, 12)
    today = _today()
    out = []
    normalized = _normalize_payments(payments, payment_form if payment_form is not None else 3)
    for idx, item in enumerate(normalized, start=1):
        expected = _add_months(start, period * (idx - 1)) if start else None
        item["expected_date"] = expected.isoformat() if expected else None
        item["overdue"] = bool(expected and not item.get("paid") and expected < today)
        out.append(item)
    return out


# =============================================================================
# Vehiculos (maestro)
# =============================================================================
def create_vehicle_api(data, data_token):
    user = data_token.get("emp_id")
    errors = _validate_enums(data, (("status", VEHICLE_STATUS), ("oil_type", OIL_TYPE)))
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400

    code = (data.get("code") or "").strip()
    if not code:
        return {"data": None, "msg": "Falta el código del vehículo", "error": "code requerido"}, 400
    flag, error, existing = get_vehicle_by_code(code, data_token)
    if not flag:
        return {"data": None, "msg": "Error al validar el código", "error": error}, 400
    if existing:
        return {"data": None, "msg": f"Ya existe un vehículo con el código {code}", "error": "code duplicado"}, 400

    accessories = data.get("accessories") or {}
    accessories = {k: int(accessories.get(k) or 0) for k in ACCESSORY_KEYS}
    extra_info = {}
    if data.get("refrendo_note") is not None:
        extra_info["refrendo_note"] = data.get("refrendo_note")

    row = {
        "code": code,
        "model": data.get("model"),
        "plate": data.get("plate"),
        "brand": data.get("brand"),
        "niv": data.get("niv"),
        "status": int(data.get("status") or 0),
        "oil_type": int(data.get("oil_type") or 0),
        "current_km": data.get("current_km"),
        "current_km_date": data.get("current_km_date"),
        "rin_size": data.get("rin_size"),
        "tire_size": data.get("tire_size"),
        "refrendo_last_paid": data.get("refrendo_last_paid"),
        "accessories": accessories,
        "extra_info": extra_info,
        "history": [_history_entry(user, "Creación", "Alta del vehículo.")],
        "is_active": 1,
    }
    flag, error, id_vehicle = insert_vehicle(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo crear el vehículo", "error": error}, 400
    msg = f"Vehículo {code} creado correctamente (ID {id_vehicle})"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Control de vehículos", user or 0, 0)
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_vehicle": id_vehicle}, "msg": msg, "error": None}, 201


def update_vehicle_api(data, data_token, raw_payload):
    user = data_token.get("emp_id")
    id_vehicle = _to_int_or_none(data.get("id_vehicle") or data.get("id"))
    if not id_vehicle:
        return {"data": None, "msg": "Falta el id del vehículo", "error": "id_vehicle requerido"}, 400

    errors = _validate_enums(
        data, (("status", VEHICLE_STATUS), ("oil_type", OIL_TYPE)), raw_payload
    )
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400

    flag, error, existing = get_vehicle_by_id(id_vehicle, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el vehículo", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe el vehículo (ID {id_vehicle})", "error": "No encontrado"}, 404
    current = _vehicle_to_dict(existing)

    # Cambio de codigo -> validar unicidad contra otro vehiculo.
    if "code" in raw_payload:
        new_code = (data.get("code") or "").strip()
        if not new_code:
            return {"data": None, "msg": "El código no puede quedar vacío", "error": "code requerido"}, 400
        if new_code != current.get("code"):
            flag, error, other = get_vehicle_by_code(new_code, data_token)
            if not flag:
                return {"data": None, "msg": "Error al validar el código", "error": error}, 400
            if other:
                return {"data": None, "msg": f"Ya existe un vehículo con el código {new_code}", "error": "code duplicado"}, 400

    merged: dict = {}
    for col in _VEHICLE_UPDATE_COLS:
        merged[col] = data.get(col) if col in raw_payload else current.get(col)
    merged["status"] = int(merged.get("status") or 0)
    merged["oil_type"] = int(merged.get("oil_type") or 0)

    accessories = dict(current.get("accessories") or {})
    if "accessories" in raw_payload:
        incoming = data.get("accessories") or {}
        for k in ACCESSORY_KEYS:
            if k in (raw_payload.get("accessories") or {}):
                accessories[k] = int(incoming.get(k) or 0)
    merged["accessories"] = {k: int(accessories.get(k) or 0) for k in ACCESSORY_KEYS}

    extra_info = dict(current.get("extra_info") or {})
    if "refrendo_note" in raw_payload:
        extra_info["refrendo_note"] = data.get("refrendo_note")
    merged["extra_info"] = extra_info

    history = current.get("history") or []
    history.append(_history_entry(user, "Actualización", "Actualización del vehículo."))
    merged["history"] = history

    flag, error, _ = update_vehicle(id_vehicle, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el vehículo", "error": error}, 400
    msg = f"Vehículo actualizado correctamente (ID {id_vehicle})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_vehicle": id_vehicle}, "msg": msg, "error": None}, 200


def cancel_vehicle_api(data, data_token):
    """Baja logica (is_active=0). Recuperable; conserva todo el historial."""
    user = data_token.get("emp_id")
    id_vehicle = _to_int_or_none(data.get("id_vehicle") or data.get("id"))
    if not id_vehicle:
        return {"data": None, "msg": "Falta el id del vehículo", "error": "id_vehicle requerido"}, 400

    flag, error, existing = get_vehicle_by_id(id_vehicle, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el vehículo", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe el vehículo (ID {id_vehicle})", "error": "No encontrado"}, 404
    current = _vehicle_to_dict(existing)
    if int(current.get("is_active") or 0) == 0:
        return {"data": {"id_vehicle": id_vehicle}, "msg": f"El vehículo ya estaba dado de baja (ID {id_vehicle})", "error": None}, 200

    history = current.get("history") or []
    history.append(_history_entry(user, "Baja", data.get("comment") or "Baja lógica del vehículo."))
    flag, error, _ = set_active_vehicle(id_vehicle, 0, history, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo dar de baja el vehículo", "error": error}, 400
    msg = f"Vehículo dado de baja (ID {id_vehicle})"
    create_notification_permission(msg, data_token, _PERMISSIONS, "Control de vehículos", user or 0, 0)
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_vehicle": id_vehicle}, "msg": msg, "error": None}, 200


def delete_vehicle_api(data, data_token):
    """Borrado fisico. Irreversible: las hijas caen en cascada."""
    id_vehicle = _to_int_or_none(data.get("id_vehicle") or data.get("id"))
    if not id_vehicle:
        return {"data": None, "msg": "Falta el id del vehículo", "error": "id_vehicle requerido"}, 400
    flag, error, rowcount = delete_vehicle(id_vehicle, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo eliminar el vehículo", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe el vehículo (ID {id_vehicle})", "error": "No encontrado"}, 404
    msg = f"Vehículo eliminado (ID {id_vehicle})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_vehicle": id_vehicle}, "msg": msg, "error": None}, 200


def _resolve_is_active(params):
    """is_active: default solo activos (1); all=1 -> todos; is_active=0 -> bajas."""
    is_active_param = params.get("is_active")
    include_all = str(params.get("all") or "").strip().lower() in ("1", "true", "yes")
    if is_active_param is not None and str(is_active_param).strip() != "":
        return _to_int_or_none(is_active_param)
    if include_all:
        return None
    return 1


def fetch_vehicles(params, data_token):
    status = _to_int_or_none(params.get("status"))
    is_active = _resolve_is_active(params)
    flag, error, rows = get_vehicles_list(status, is_active, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar vehículos", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    data_out = [_vehicle_to_dict(r) for r in rows]
    return {"data": data_out, "msg": f"{len(data_out)} vehículos", "error": None}, 200


def get_vehicle_detail_api(id_vehicle, data_token):
    """Vehiculo + su historial de polizas + llantas."""
    err, vehicle = _require_vehicle(id_vehicle, data_token)
    if err is not None:
        code = 404 if "No existe" in (err.get("msg") or "") else 400
        return err, code
    flag, error, p_rows = get_policies(vehicle["id"], None, data_token)
    policies = [_policy_to_dict(r) for r in p_rows] if flag and isinstance(p_rows, list) else []
    flag, error, t_rows = get_tires(vehicle["id"], data_token)
    tires = [_tire_to_dict(r) for r in t_rows] if flag and isinstance(t_rows, list) else []
    vehicle["policies"] = policies
    vehicle["tires"] = tires
    return {"data": vehicle, "msg": "ok", "error": None}, 200


# =============================================================================
# Polizas
# =============================================================================
def create_policy_api(data, data_token):
    errors = _validate_enums(data, (("payment_form", PAYMENT_FORM),))
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400
    err, vehicle = _require_vehicle(data.get("vehicle_id"), data_token)
    if err is not None:
        return err, 400

    payment_form = int(data.get("payment_form") or 0)
    row = {
        "vehicle_id": vehicle["id"],
        "inciso": data.get("inciso"),
        "insurer": data.get("insurer"),
        "date_start": data.get("date_start"),
        "date_end": data.get("date_end"),
        "payment_form": payment_form,
        "payments": _normalize_payments(data.get("payments"), payment_form),
        "notification": data.get("notification"),
        "other_requirements": data.get("other_requirements"),
        "extra_info": {},
        "is_active": 1,
    }
    flag, error, id_policy = insert_policy(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo crear la póliza", "error": error}, 400
    msg = f"Póliza creada correctamente (ID {id_policy}) para {vehicle['code']}"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_policy": id_policy}, "msg": msg, "error": None}, 201


def update_policy_api(data, data_token, raw_payload):
    id_policy = _to_int_or_none(data.get("id_policy") or data.get("id"))
    if not id_policy:
        return {"data": None, "msg": "Falta el id de la póliza", "error": "id_policy requerido"}, 400
    errors = _validate_enums(data, (("payment_form", PAYMENT_FORM),), raw_payload)
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400

    flag, error, existing = get_policy_by_id(id_policy, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar la póliza", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe la póliza (ID {id_policy})", "error": "No encontrado"}, 404
    current = _row_to_dict(existing, POLICY_COLUMNS)

    merged: dict = {}
    for col in _POLICY_UPDATE_COLS:
        merged[col] = data.get(col) if col in raw_payload else current.get(col)
    merged["payment_form"] = int(merged.get("payment_form") or 0)
    if "is_active" in raw_payload:
        merged["is_active"] = int(data.get("is_active") or 0)
    else:
        merged["is_active"] = int(current.get("is_active") or 1)

    if "payments" in raw_payload:
        merged["payments"] = _normalize_payments(data.get("payments"), merged["payment_form"])
    else:
        payments = _load_json(current.get("payments"), [])
        merged["payments"] = _normalize_payments(
            payments if isinstance(payments, list) else [], merged["payment_form"]
        )
    merged["extra_info"] = current.get("extra_info") or {}

    flag, error, _ = update_policy(id_policy, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar la póliza", "error": error}, 400
    msg = f"Póliza actualizada correctamente (ID {id_policy})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_policy": id_policy}, "msg": msg, "error": None}, 200


def delete_policy_api(data, data_token):
    id_policy = _to_int_or_none(data.get("id_policy") or data.get("id"))
    if not id_policy:
        return {"data": None, "msg": "Falta el id de la póliza", "error": "id_policy requerido"}, 400
    flag, error, rowcount = delete_policy(id_policy, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo eliminar la póliza", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe la póliza (ID {id_policy})", "error": "No encontrado"}, 404
    msg = f"Póliza eliminada (ID {id_policy})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_policy": id_policy}, "msg": msg, "error": None}, 200


# =============================================================================
# Servicios (mantenimientos + reparaciones + servicios)
# =============================================================================
def _auto_update_km(vehicle: dict, km, service_date, data_token):
    """Si el servicio trae un odometro mayor al actual, actualiza el vehiculo."""
    km = _to_int_or_none(km)
    if km is None:
        return
    current = _to_int_or_none(vehicle.get("current_km"))
    if current is None or km > current:
        update_vehicle_km(vehicle["id"], km, service_date or _today().isoformat(), data_token)


def create_service_api(data, data_token):
    errors = _validate_enums(data, (("service_type", SERVICE_TYPE),))
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400
    err, vehicle = _require_vehicle(data.get("vehicle_id"), data_token)
    if err is not None:
        return err, 400

    row = {
        "vehicle_id": vehicle["id"],
        "service_type": int(data.get("service_type") or 0),
        "date": data.get("date"),
        "description": data.get("description"),
        "km": data.get("km"),
        "workshop": data.get("workshop"),
        "cost": data.get("cost"),
        "extra_info": {},
    }
    flag, error, id_service = insert_service(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo registrar el servicio", "error": error}, 400
    _auto_update_km(vehicle, data.get("km"), data.get("date"), data_token)
    msg = f"Servicio registrado correctamente (ID {id_service}) para {vehicle['code']}"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_service": id_service}, "msg": msg, "error": None}, 201


def update_service_api(data, data_token, raw_payload):
    id_service = _to_int_or_none(data.get("id_service") or data.get("id"))
    if not id_service:
        return {"data": None, "msg": "Falta el id del servicio", "error": "id_service requerido"}, 400
    errors = _validate_enums(data, (("service_type", SERVICE_TYPE),), raw_payload)
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400

    flag, error, existing = get_service_by_id(id_service, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el servicio", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe el servicio (ID {id_service})", "error": "No encontrado"}, 404
    current = _row_to_dict(existing, SERVICE_COLUMNS)

    merged: dict = {}
    for col in _SERVICE_UPDATE_COLS:
        merged[col] = data.get(col) if col in raw_payload else current.get(col)
    merged["service_type"] = int(merged.get("service_type") or 0)
    merged["extra_info"] = current.get("extra_info") or {}

    flag, error, _ = update_service(id_service, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el servicio", "error": error}, 400
    err, vehicle = _require_vehicle(current.get("vehicle_id"), data_token)
    if err is None:
        _auto_update_km(vehicle, merged.get("km"), merged.get("date"), data_token)
    msg = f"Servicio actualizado correctamente (ID {id_service})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_service": id_service}, "msg": msg, "error": None}, 200


def delete_service_api(data, data_token):
    id_service = _to_int_or_none(data.get("id_service") or data.get("id"))
    if not id_service:
        return {"data": None, "msg": "Falta el id del servicio", "error": "id_service requerido"}, 400
    flag, error, rowcount = delete_service(id_service, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo eliminar el servicio", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe el servicio (ID {id_service})", "error": "No encontrado"}, 404
    msg = f"Servicio eliminado (ID {id_service})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_service": id_service}, "msg": msg, "error": None}, 200


# =============================================================================
# Llantas
# =============================================================================
def _tire_to_dict(row) -> dict:
    data = _row_to_dict(row, TIRE_COLUMNS)
    data["position_label"] = TIRE_POSITION.get(data.get("position"))
    expiry = _to_date(data.get("expiry_date"))
    data["expired"] = bool(expiry and expiry < _today())
    return data


def upsert_tire_api(data, data_token, raw_payload):
    """PUT idempotente por (vehicle_id, position): crea la fila si no existe,
    si existe actualiza en sitio y registra el cambio en history."""
    user = data_token.get("emp_id")
    position = _to_int_or_none(data.get("position"))
    if position is None or position not in TIRE_POSITION:
        return {
            "data": None,
            "msg": f"position inválida (válidas: {sorted(TIRE_POSITION.keys())})",
            "error": "position",
        }, 400
    err, vehicle = _require_vehicle(data.get("vehicle_id"), data_token)
    if err is not None:
        return err, 400

    flag, error, existing = get_tire_by_position(vehicle["id"], position, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar la llanta", "error": error}, 400

    if not existing:
        row = {
            "vehicle_id": vehicle["id"],
            "position": position,
            "dot": data.get("dot"),
            "manufacture_date": data.get("manufacture_date"),
            "brand": data.get("brand"),
            "expiry_date": data.get("expiry_date"),
            "physical_state": data.get("physical_state"),
            "needs_change": int(data.get("needs_change") or 0),
            "history": [_history_entry(user, "Creación", "Registro inicial de la llanta.")],
            "extra_info": {},
        }
        flag, error, id_tire = insert_tire(row, data_token)
        if not flag:
            return {"data": None, "msg": "No se pudo registrar la llanta", "error": error}, 400
        msg = f"Llanta registrada (ID {id_tire}) en {vehicle['code']} - {TIRE_POSITION[position]}"
        write_log_file(log_file_cda, msg, data_token)
        return {"data": {"id_tire": id_tire}, "msg": msg, "error": None}, 201

    current = _tire_to_dict(existing)
    merged: dict = {}
    changes: dict = {}
    for col in _TIRE_UPDATE_COLS:
        if col in raw_payload:
            merged[col] = data.get(col)
            if merged[col] != current.get(col):
                changes[col] = [current.get(col), merged[col]]
        else:
            merged[col] = current.get(col)
    merged["needs_change"] = int(merged.get("needs_change") or 0)
    merged["extra_info"] = current.get("extra_info") or {}

    history = current.get("history") or []
    entry = _history_entry(user, "Actualización", "Actualización de la llanta.")
    if changes:
        entry["changes"] = changes
    history.append(entry)
    merged["history"] = history

    flag, error, _ = update_tire(current["id"], merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar la llanta", "error": error}, 400
    msg = f"Llanta actualizada (ID {current['id']}) en {vehicle['code']} - {TIRE_POSITION[position]}"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_tire": current["id"]}, "msg": msg, "error": None}, 200


def delete_tire_api(data, data_token):
    """Por id_tire, o por (vehicle_id + position)."""
    id_tire = _to_int_or_none(data.get("id_tire") or data.get("id"))
    if not id_tire:
        vehicle_id = _to_int_or_none(data.get("vehicle_id"))
        position = _to_int_or_none(data.get("position"))
        if vehicle_id and position is not None:
            flag, error, existing = get_tire_by_position(vehicle_id, position, data_token)
            if not flag:
                return {"data": None, "msg": "Error al consultar la llanta", "error": error}, 400
            if existing:
                id_tire = _row_to_dict(existing, TIRE_COLUMNS).get("id")
    if not id_tire:
        return {"data": None, "msg": "Falta id_tire (o vehicle_id + position)", "error": "id_tire requerido"}, 400
    flag, error, rowcount = delete_tire(id_tire, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo eliminar la llanta", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe la llanta (ID {id_tire})", "error": "No encontrado"}, 404
    msg = f"Llanta eliminada (ID {id_tire})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_tire": id_tire}, "msg": msg, "error": None}, 200


# =============================================================================
# Multas
# =============================================================================
def create_fine_api(data, data_token):
    err, vehicle = _require_vehicle(data.get("vehicle_id"), data_token)
    if err is not None:
        return err, 400
    year = _to_int_or_none(data.get("year"))
    month = _to_int_or_none(data.get("month"))
    if not year or month is None or not (1 <= month <= 12):
        return {"data": None, "msg": "year/month inválidos (month 1..12)", "error": "year/month"}, 400

    row = {
        "vehicle_id": vehicle["id"],
        "year": year,
        "month": month,
        "amount": data.get("amount"),
        "description": data.get("description"),
        "responsible": data.get("responsible"),
        "extra_info": {},
    }
    flag, error, id_fine = insert_fine(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo registrar la multa", "error": error}, 400
    msg = f"Multa registrada (ID {id_fine}) para {vehicle['code']} ({year}-{month:02d})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_fine": id_fine}, "msg": msg, "error": None}, 201


def update_fine_api(data, data_token, raw_payload):
    id_fine = _to_int_or_none(data.get("id_fine") or data.get("id"))
    if not id_fine:
        return {"data": None, "msg": "Falta el id de la multa", "error": "id_fine requerido"}, 400
    flag, error, existing = get_fine_by_id(id_fine, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar la multa", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe la multa (ID {id_fine})", "error": "No encontrado"}, 404
    current = _row_to_dict(existing, FINE_COLUMNS)

    merged: dict = {}
    for col in _FINE_UPDATE_COLS:
        merged[col] = data.get(col) if col in raw_payload else current.get(col)
    month = _to_int_or_none(merged.get("month"))
    if month is None or not (1 <= month <= 12):
        return {"data": None, "msg": "month inválido (1..12)", "error": "month"}, 400
    merged["extra_info"] = current.get("extra_info") or {}

    flag, error, _ = update_fine(id_fine, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar la multa", "error": error}, 400
    msg = f"Multa actualizada (ID {id_fine})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_fine": id_fine}, "msg": msg, "error": None}, 200


def delete_fine_api(data, data_token):
    id_fine = _to_int_or_none(data.get("id_fine") or data.get("id"))
    if not id_fine:
        return {"data": None, "msg": "Falta el id de la multa", "error": "id_fine requerido"}, 400
    flag, error, rowcount = delete_fine(id_fine, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo eliminar la multa", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe la multa (ID {id_fine})", "error": "No encontrado"}, 404
    msg = f"Multa eliminada (ID {id_fine})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_fine": id_fine}, "msg": msg, "error": None}, 200


# =============================================================================
# Pendiente de compra
# =============================================================================
def _purchase_to_dict(row) -> dict:
    data = _row_to_dict(row, PURCHASE_COLUMNS)
    data["status_label"] = PURCHASE_STATUS.get(data.get("status"))
    qty = data.get("quantity")
    cost = data.get("cost")
    data["total"] = round(qty * cost, 2) if qty is not None and cost is not None else None
    created = _to_date(data.get("created_at"))
    if created:
        iso = created.isocalendar()
        data["week"] = iso[1]
        data["week_year"] = iso[0]
    else:
        data["week"] = None
        data["week_year"] = None
    return data


def create_vehicle_purchase_api(data, data_token):
    errors = _validate_enums(data, (("status", PURCHASE_STATUS),))
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400
    err, vehicle = _require_vehicle(data.get("vehicle_id"), data_token)
    if err is not None:
        return err, 400

    row = {
        "vehicle_id": vehicle["id"],
        "checklist_sent": int(data.get("checklist_sent") or 0),
        "checklist_sent_date": data.get("checklist_sent_date"),
        "problem": data.get("problem"),
        "quantity": data.get("quantity"),
        "unit": data.get("unit"),
        "cost": data.get("cost"),
        "supplier": data.get("supplier"),
        "observations": data.get("observations"),
        "status": int(data.get("status") or 0),
        "po_id": data.get("po_id"),
        "extra_info": {},
    }
    flag, error, id_purchase = insert_vehicle_purchase(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo registrar la compra", "error": error}, 400
    msg = f"Compra pendiente registrada (ID {id_purchase}) para {vehicle['code']}"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_purchase": id_purchase}, "msg": msg, "error": None}, 201


def update_vehicle_purchase_api(data, data_token, raw_payload):
    id_purchase = _to_int_or_none(data.get("id_purchase") or data.get("id"))
    if not id_purchase:
        return {"data": None, "msg": "Falta el id de la compra", "error": "id_purchase requerido"}, 400
    errors = _validate_enums(data, (("status", PURCHASE_STATUS),), raw_payload)
    if errors:
        return {"data": None, "msg": "Valor de catálogo inválido", "error": errors}, 400

    flag, error, existing = get_vehicle_purchase_by_id(id_purchase, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar la compra", "error": error}, 400
    if not existing:
        return {"data": None, "msg": f"No existe la compra (ID {id_purchase})", "error": "No encontrado"}, 404
    current = _row_to_dict(existing, PURCHASE_COLUMNS)

    merged: dict = {}
    for col in _PURCHASE_UPDATE_COLS:
        merged[col] = data.get(col) if col in raw_payload else current.get(col)
    merged["checklist_sent"] = int(merged.get("checklist_sent") or 0)
    merged["status"] = int(merged.get("status") or 0)
    merged["extra_info"] = current.get("extra_info") or {}

    flag, error, _ = update_vehicle_purchase(id_purchase, merged, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar la compra", "error": error}, 400
    msg = f"Compra actualizada (ID {id_purchase})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_purchase": id_purchase}, "msg": msg, "error": None}, 200


def delete_vehicle_purchase_api(data, data_token):
    id_purchase = _to_int_or_none(data.get("id_purchase") or data.get("id"))
    if not id_purchase:
        return {"data": None, "msg": "Falta el id de la compra", "error": "id_purchase requerido"}, 400
    flag, error, rowcount = delete_vehicle_purchase(id_purchase, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo eliminar la compra", "error": error}, 400
    if not rowcount:
        return {"data": None, "msg": f"No existe la compra (ID {id_purchase})", "error": "No encontrado"}, 404
    msg = f"Compra eliminada (ID {id_purchase})"
    write_log_file(log_file_cda, msg, data_token)
    return {"data": {"id_purchase": id_purchase}, "msg": msg, "error": None}, 200


# =============================================================================
# Vistas (las hojas del Excel)
# =============================================================================
def _fetch_vehicles_map(params, data_token):
    """Vehiculos activos (o segun params) como lista + mapa id->dict."""
    status = _to_int_or_none(params.get("status"))
    is_active = _resolve_is_active(params)
    flag, error, rows = get_vehicles_list(status, is_active, data_token)
    if not flag:
        return None, error
    rows = rows if isinstance(rows, list) else []
    vehicles = [_vehicle_to_dict(r) for r in rows]
    return vehicles, None


def fetch_policies_view(params, data_token):
    """Hoja CONTROL DE POLIZAS: cada vehiculo con su poliza vigente (la de
    date_end mas reciente activa) y sus pagos enriquecidos."""
    vehicles, error = _fetch_vehicles_map(params, data_token)
    if vehicles is None:
        return {"data": None, "msg": "Error al consultar vehículos", "error": error}, 400
    flag, error, p_rows = get_policies(None, 1, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar pólizas", "error": error}, 400
    p_rows = p_rows if isinstance(p_rows, list) else []
    # get_policies ordena por vehicle_id, date_end DESC -> la primera por
    # vehiculo es la vigente.
    latest = {}
    for r in p_rows:
        pol = _policy_to_dict(r)
        latest.setdefault(pol["vehicle_id"], pol)
    data_out = []
    for v in vehicles:
        data_out.append({
            "id_vehicle": v["id"],
            "code": v["code"],
            "model": v["model"],
            "plate": v["plate"],
            "brand": v["brand"],
            "niv": v["niv"],
            "policy": latest.get(v["id"]),
        })
    return {"data": data_out, "msg": f"{len(data_out)} vehículos", "error": None}, 200


def fetch_maintenance_view(params, data_token):
    """Hoja C.MANTENIMIENTOS: ultimo mantenimiento + proximo (calculado) +
    indicadores + KPIs."""
    vehicles, error = _fetch_vehicles_map(params, data_token)
    if vehicles is None:
        return {"data": None, "msg": "Error al consultar vehículos", "error": error}, 400
    flag, error, s_rows = get_services(None, 0, None, None, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar mantenimientos", "error": error}, 400
    s_rows = s_rows if isinstance(s_rows, list) else []
    # get_services ordena por date DESC -> el primero por vehiculo es el ultimo.
    last_by_vehicle = {}
    for r in s_rows:
        svc = _row_to_dict(r, SERVICE_COLUMNS)
        last_by_vehicle.setdefault(svc["vehicle_id"], svc)

    today = _today()
    data_out = []
    pending = 0
    done_6_months = 0
    for v in vehicles:
        last = last_by_vehicle.get(v["id"])
        interval_km = int(OIL_INTERVAL_KM.get(v.get("oil_type")) or OIL_INTERVAL_KM[0])
        entry: dict = {
            "id_vehicle": v["id"],
            "code": v["code"],
            "model": v["model"],
            "plate": v["plate"],
            "status": v["status"],
            "status_label": v["status_label"],
            "oil_type": v["oil_type"],
            "oil_type_label": v["oil_type_label"],
            "interval_km": interval_km,
            "current_km": v.get("current_km"),
            "current_km_date": v.get("current_km_date"),
            "last_maintenance": None,
            "next_maintenance": None,
            "requires_maintenance": None,
            "days_remaining": None,
            "maintained_last_6_months": False,
        }
        if last:
            last_date = _to_date(last.get("date"))
            last_km = _to_int_or_none(last.get("km"))
            entry["last_maintenance"] = {
                "id_service": last.get("id"),
                "date": last.get("date"),
                "description": last.get("description"),
                "km": last_km,
                "workshop": last.get("workshop"),
            }
            next_km = None
            if last_km is not None:
                next_km = last_km + interval_km
            next_date = _add_months(last_date, MAINTENANCE_INTERVAL_MONTHS) if last_date else None
            entry["next_maintenance"] = {
                "date": next_date.isoformat() if next_date else None,
                "km": next_km,
            }
            current_km = _to_int_or_none(v.get("current_km"))
            by_km = bool(next_km is not None and current_km is not None and current_km >= next_km)
            by_date = bool(next_date and today > next_date)
            entry["requires_maintenance"] = by_km or by_date
            entry["days_remaining"] = (next_date - today).days if next_date else None
            entry["maintained_last_6_months"] = bool(
                last_date and last_date >= _add_months(today, -MAINTENANCE_INTERVAL_MONTHS)
            )
        else:
            # Sin mantenimiento registrado: pendiente por definicion.
            entry["requires_maintenance"] = True
        if entry["requires_maintenance"]:
            pending += 1
        if entry["maintained_last_6_months"]:
            done_6_months += 1
        data_out.append(entry)

    total = len(data_out)
    kpis = {
        "vehicles_in_control": total,
        "pending_maintenance": pending,
        "pct_maintained_last_6_months": round(done_6_months / total * 100, 1) if total else 0.0,
    }
    return {"data": {"vehicles": data_out, "kpis": kpis}, "msg": f"{total} vehículos", "error": None}, 200


def fetch_services_view(params, data_token):
    """Hoja REP. Y SERV.: historial filtrable de servicios con info del vehiculo."""
    vehicle_id = _to_int_or_none(params.get("vehicle_id"))
    service_type = _to_int_or_none(params.get("service_type"))
    date_from = params.get("date_from") or None
    date_to = params.get("date_to") or None
    flag, error, rows = get_services(vehicle_id, service_type, date_from, date_to, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar servicios", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    vehicles, v_err = _fetch_vehicles_map({"all": "1"}, data_token)
    v_map = {v["id"]: v for v in (vehicles or [])}
    data_out = []
    total_cost = 0.0
    for r in rows:
        svc = _row_to_dict(r, SERVICE_COLUMNS)
        v = v_map.get(svc["vehicle_id"], {})
        svc["service_type_label"] = SERVICE_TYPE.get(svc.get("service_type"))
        svc["code"] = v.get("code")
        svc["model"] = v.get("model")
        svc["plate"] = v.get("plate")
        svc["vehicle_status_label"] = v.get("status_label")
        if svc.get("cost") is not None:
            total_cost += float(svc["cost"])
        data_out.append(svc)
    return {
        "data": {"services": data_out, "total_cost": round(total_cost, 2)},
        "msg": f"{len(data_out)} servicios",
        "error": None,
    }, 200


def fetch_tires_view(params, data_token):
    """Hoja STA.LLANTAS: por vehiculo, las 5 posiciones (existentes o vacias)."""
    vehicles, error = _fetch_vehicles_map(params, data_token)
    if vehicles is None:
        return {"data": None, "msg": "Error al consultar vehículos", "error": error}, 400
    flag, error, t_rows = get_tires(None, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar llantas", "error": error}, 400
    t_rows = t_rows if isinstance(t_rows, list) else []
    by_vehicle = {}
    for r in t_rows:
        tire = _tire_to_dict(r)
        by_vehicle.setdefault(tire["vehicle_id"], {})[tire["position"]] = tire
    data_out = []
    for v in vehicles:
        tires_map = by_vehicle.get(v["id"], {})
        positions = []
        for pos in sorted(TIRE_POSITION.keys()):
            tire = tires_map.get(pos)
            positions.append(tire if tire else {
                "id": None,
                "vehicle_id": v["id"],
                "position": pos,
                "position_label": TIRE_POSITION[pos],
                "needs_change": 0,
                "expired": False,
            })
        data_out.append({
            "id_vehicle": v["id"],
            "code": v["code"],
            "model": v["model"],
            "rin_size": v.get("rin_size"),
            "tire_size": v.get("tire_size"),
            "tires": positions,
        })
    return {"data": data_out, "msg": f"{len(data_out)} vehículos", "error": None}, 200


def fetch_refrendos_view(params, data_token):
    """Hoja REFRENDOS: estatus derivado del refrendo + multas del año por mes."""
    year = _to_int_or_none(params.get("year")) or _today().year
    vehicles, error = _fetch_vehicles_map(params, data_token)
    if vehicles is None:
        return {"data": None, "msg": "Error al consultar vehículos", "error": error}, 400
    flag, error, f_rows = get_fines(None, year, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar multas", "error": error}, 400
    f_rows = f_rows if isinstance(f_rows, list) else []
    fines_by_vehicle = {}
    for r in f_rows:
        fine = _row_to_dict(r, FINE_COLUMNS)
        fines_by_vehicle.setdefault(fine["vehicle_id"], []).append(fine)

    data_out = []
    grand_total = 0.0
    for v in vehicles:
        fines = fines_by_vehicle.get(v["id"], [])
        by_month: dict = {m: [] for m in range(1, 13)}
        total_amount = 0.0
        for fine in fines:
            month = _to_int_or_none(fine.get("month"))
            if month is not None and month in by_month:
                by_month[month].append(fine)
            if fine.get("amount") is not None:
                total_amount += float(fine["amount"])
        grand_total += total_amount
        data_out.append({
            "id_vehicle": v["id"],
            "code": v["code"],
            "model": v["model"],
            "plate": v["plate"],
            "refrendo_last_paid": v.get("refrendo_last_paid"),
            "refrendo_status": _refrendo_status(v.get("refrendo_last_paid"), year),
            "refrendo_note": v.get("refrendo_note"),
            "fines_by_month": {str(m): items for m, items in by_month.items()},
            "fines_total": round(total_amount, 2),
        })
    return {
        "data": {"year": year, "vehicles": data_out, "fines_grand_total": round(grand_total, 2)},
        "msg": f"{len(data_out)} vehículos",
        "error": None,
    }, 200


def fetch_vehicle_purchases_view(params, data_token):
    """Hoja PENDIENTE DE COMPRA: filas + total calculado + semana derivada."""
    vehicle_id = _to_int_or_none(params.get("vehicle_id"))
    status = _to_int_or_none(params.get("status"))
    date_from = params.get("date_from") or None
    date_to = params.get("date_to") or None
    flag, error, rows = get_vehicle_purchases(vehicle_id, status, date_from, date_to, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar compras", "error": error}, 400
    rows = rows if isinstance(rows, list) else []
    vehicles, _v_err = _fetch_vehicles_map({"all": "1"}, data_token)
    v_map = {v["id"]: v for v in (vehicles or [])}
    data_out = []
    total_pending = 0.0
    for r in rows:
        item = _purchase_to_dict(r)
        v = v_map.get(item["vehicle_id"], {})
        item["code"] = v.get("code")
        item["model"] = v.get("model")
        item["plate"] = v.get("plate")
        if item.get("status") == 0 and item.get("total") is not None:
            total_pending += item["total"]
        data_out.append(item)
    return {
        "data": {"purchases": data_out, "total_pending": round(total_pending, 2)},
        "msg": f"{len(data_out)} compras",
        "error": None,
    }, 200


def get_cda_catalogs():
    def _fmt(catalog):
        return [{"code": code, "label": label} for code, label in catalog.items()]

    data = {
        "vehicle_status": _fmt(VEHICLE_STATUS),
        "oil_type": _fmt(OIL_TYPE),
        "payment_form": _fmt(PAYMENT_FORM),
        "service_type": _fmt(SERVICE_TYPE),
        "tire_position": _fmt(TIRE_POSITION),
        "purchase_status": _fmt(PURCHASE_STATUS),
        "accessory_keys": list(ACCESSORY_KEYS),
        "rules": {
            "oil_interval_km": {OIL_TYPE[k]: v for k, v in OIL_INTERVAL_KM.items()},
            "maintenance_interval_months": MAINTENANCE_INTERVAL_MONTHS,
            "payment_slots": {PAYMENT_FORM[k]: v for k, v in PAYMENT_SLOTS.items()},
        },
    }
    return {"data": data, "msg": "ok", "error": None}, 200
