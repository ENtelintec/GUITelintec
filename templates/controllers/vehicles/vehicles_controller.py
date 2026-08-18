# -*- coding: utf-8 -*-
"""
Controller del modulo CDA — Control de Estado de Vehiculos (FO-CDA-02 R3).
SQL crudo sobre sql_telintec_mod_admin (DDL en scripts_db_handle/control_vehiculos.sql).
Los campos calculados (proximo mantenimiento, refrendo al dia, llanta vencida,
totales) NO viven aqui: los computa el midleware MD_CDA.
"""
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026 $"

import json

from templates.database.connection import execute_sql

_T_VEHICLES = "sql_telintec_mod_admin.vehicles"
_T_POLICIES = "sql_telintec_mod_admin.vehicle_policies"
_T_SERVICES = "sql_telintec_mod_admin.vehicle_services"
_T_TIRES = "sql_telintec_mod_admin.vehicle_tires"
_T_FINES = "sql_telintec_mod_admin.vehicle_fines"
_T_PURCHASES = "sql_telintec_mod_admin.vehicle_purchases"

# Columnas devueltas por los SELECT (incluyen el PK). El midleware mapea por
# indice con estas mismas tuplas, asi que el orden importa.
VEHICLE_COLUMNS = (
    "id", "code", "model", "plate", "brand", "niv", "status", "oil_type",
    "current_km", "current_km_date", "rin_size", "tire_size",
    "refrendo_last_paid", "accessories", "extra_info", "history", "is_active",
    "created_at", "updated_at",
)
POLICY_COLUMNS = (
    "id", "vehicle_id", "inciso", "insurer", "date_start", "date_end",
    "payment_form", "payments", "notification", "other_requirements",
    "extra_info", "is_active", "created_at", "updated_at",
)
SERVICE_COLUMNS = (
    "id", "vehicle_id", "service_type", "date", "description", "km",
    "workshop", "cost", "extra_info", "created_at", "updated_at",
)
TIRE_COLUMNS = (
    "id", "vehicle_id", "position", "dot", "manufacture_date", "brand",
    "expiry_date", "physical_state", "needs_change", "history", "extra_info",
    "created_at", "updated_at",
)
FINE_COLUMNS = (
    "id", "vehicle_id", "year", "month", "amount", "description",
    "responsible", "extra_info", "created_at", "updated_at",
)
PURCHASE_COLUMNS = (
    "id", "vehicle_id", "checklist_sent", "checklist_sent_date", "problem",
    "quantity", "unit", "cost", "supplier", "observations", "status", "po_id",
    "extra_info", "created_at", "updated_at",
)

def _sel(columns, table):
    """SELECT con todos los identificadores backtickeados (cubre reservadas
    como `date`/`year`/`month`); las tuplas de columnas quedan limpias para
    que el midleware las use como llaves."""
    cols = ", ".join(f"`{c}`" for c in columns)
    return f"SELECT {cols} FROM {table}"


_SEL_VEHICLES = _sel(VEHICLE_COLUMNS, _T_VEHICLES)
_SEL_POLICIES = _sel(POLICY_COLUMNS, _T_POLICIES)
_SEL_SERVICES = _sel(SERVICE_COLUMNS, _T_SERVICES)
_SEL_TIRES = _sel(TIRE_COLUMNS, _T_TIRES)
_SEL_FINES = _sel(FINE_COLUMNS, _T_FINES)
_SEL_PURCHASES = _sel(PURCHASE_COLUMNS, _T_PURCHASES)


# --- Vehiculos (maestro) ------------------------------------------------------
def insert_vehicle(data: dict, data_token):
    sql = (
        f"INSERT INTO {_T_VEHICLES} "
        "(code, model, plate, brand, niv, status, oil_type, current_km, "
        "current_km_date, rin_size, tire_size, refrendo_last_paid, accessories, "
        "extra_info, history, is_active) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("code"),
        data.get("model"),
        data.get("plate"),
        data.get("brand"),
        data.get("niv"),
        data.get("status", 0),
        data.get("oil_type", 0),
        data.get("current_km"),
        data.get("current_km_date"),
        data.get("rin_size"),
        data.get("tire_size"),
        data.get("refrendo_last_paid"),
        json.dumps(data.get("accessories", {})),
        json.dumps(data.get("extra_info", {})),
        json.dumps(data.get("history", [])),
        data.get("is_active", 1),
    )
    return execute_sql(sql, val, 4, data_token)


def update_vehicle(id_vehicle: int, data: dict, data_token):
    sql = (
        f"UPDATE {_T_VEHICLES} SET "
        "code = %s, model = %s, plate = %s, brand = %s, niv = %s, status = %s, "
        "oil_type = %s, current_km = %s, current_km_date = %s, rin_size = %s, "
        "tire_size = %s, refrendo_last_paid = %s, accessories = %s, "
        "extra_info = %s, history = %s "
        "WHERE id = %s"
    )
    val = (
        data.get("code"),
        data.get("model"),
        data.get("plate"),
        data.get("brand"),
        data.get("niv"),
        data.get("status", 0),
        data.get("oil_type", 0),
        data.get("current_km"),
        data.get("current_km_date"),
        data.get("rin_size"),
        data.get("tire_size"),
        data.get("refrendo_last_paid"),
        json.dumps(data.get("accessories", {})),
        json.dumps(data.get("extra_info", {})),
        json.dumps(data.get("history", [])),
        id_vehicle,
    )
    return execute_sql(sql, val, 3, data_token)


def update_vehicle_km(id_vehicle: int, km: int, km_date, data_token):
    """Auto-update del odometro desde un servicio con km mayor."""
    sql = f"UPDATE {_T_VEHICLES} SET current_km = %s, current_km_date = %s WHERE id = %s"
    return execute_sql(sql, (km, km_date, id_vehicle), 3, data_token)


def set_active_vehicle(id_vehicle: int, is_active: int, history: list, data_token):
    sql = f"UPDATE {_T_VEHICLES} SET is_active = %s, history = %s WHERE id = %s"
    return execute_sql(sql, (is_active, json.dumps(history), id_vehicle), 3, data_token)


def delete_vehicle(id_vehicle: int, data_token):
    """Borrado fisico; las hijas caen por ON DELETE CASCADE."""
    sql = f"DELETE FROM {_T_VEHICLES} WHERE id = %s"
    return execute_sql(sql, (id_vehicle,), 3, data_token)


def get_vehicles_list(status, is_active, data_token):
    sql = (
        f"{_SEL_VEHICLES} "
        "WHERE (status = %s OR %s IS NULL) "
        "AND (is_active = %s OR %s IS NULL) "
        "ORDER BY code"
    )
    return execute_sql(sql, (status, status, is_active, is_active), 2, data_token)


def get_vehicle_by_id(id_vehicle: int, data_token):
    sql = f"{_SEL_VEHICLES} WHERE id = %s"
    return execute_sql(sql, (id_vehicle,), 1, data_token)


def get_vehicle_by_code(code: str, data_token):
    sql = f"{_SEL_VEHICLES} WHERE code = %s"
    return execute_sql(sql, (code,), 1, data_token)


# --- Polizas ------------------------------------------------------------------
def insert_policy(data: dict, data_token):
    sql = (
        f"INSERT INTO {_T_POLICIES} "
        "(vehicle_id, inciso, insurer, date_start, date_end, payment_form, "
        "payments, notification, other_requirements, extra_info, is_active) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("vehicle_id"),
        data.get("inciso"),
        data.get("insurer"),
        data.get("date_start"),
        data.get("date_end"),
        data.get("payment_form", 0),
        json.dumps(data.get("payments", [])),
        data.get("notification"),
        data.get("other_requirements"),
        json.dumps(data.get("extra_info", {})),
        data.get("is_active", 1),
    )
    return execute_sql(sql, val, 4, data_token)


def update_policy(id_policy: int, data: dict, data_token):
    sql = (
        f"UPDATE {_T_POLICIES} SET "
        "inciso = %s, insurer = %s, date_start = %s, date_end = %s, "
        "payment_form = %s, payments = %s, notification = %s, "
        "other_requirements = %s, extra_info = %s, is_active = %s "
        "WHERE id = %s"
    )
    val = (
        data.get("inciso"),
        data.get("insurer"),
        data.get("date_start"),
        data.get("date_end"),
        data.get("payment_form", 0),
        json.dumps(data.get("payments", [])),
        data.get("notification"),
        data.get("other_requirements"),
        json.dumps(data.get("extra_info", {})),
        data.get("is_active", 1),
        id_policy,
    )
    return execute_sql(sql, val, 3, data_token)


def delete_policy(id_policy: int, data_token):
    sql = f"DELETE FROM {_T_POLICIES} WHERE id = %s"
    return execute_sql(sql, (id_policy,), 3, data_token)


def get_policy_by_id(id_policy: int, data_token):
    sql = f"{_SEL_POLICIES} WHERE id = %s"
    return execute_sql(sql, (id_policy,), 1, data_token)


def get_policies(vehicle_id, is_active, data_token):
    sql = (
        f"{_SEL_POLICIES} "
        "WHERE (vehicle_id = %s OR %s IS NULL) "
        "AND (is_active = %s OR %s IS NULL) "
        "ORDER BY vehicle_id, date_end DESC, id DESC"
    )
    return execute_sql(sql, (vehicle_id, vehicle_id, is_active, is_active), 2, data_token)


# --- Servicios (mantenimientos + reparaciones) --------------------------------
def insert_service(data: dict, data_token):
    sql = (
        f"INSERT INTO {_T_SERVICES} "
        "(vehicle_id, service_type, `date`, description, km, workshop, cost, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("vehicle_id"),
        data.get("service_type", 0),
        data.get("date"),
        data.get("description"),
        data.get("km"),
        data.get("workshop"),
        data.get("cost"),
        json.dumps(data.get("extra_info", {})),
    )
    return execute_sql(sql, val, 4, data_token)


def update_service(id_service: int, data: dict, data_token):
    sql = (
        f"UPDATE {_T_SERVICES} SET "
        "service_type = %s, `date` = %s, description = %s, km = %s, "
        "workshop = %s, cost = %s, extra_info = %s "
        "WHERE id = %s"
    )
    val = (
        data.get("service_type", 0),
        data.get("date"),
        data.get("description"),
        data.get("km"),
        data.get("workshop"),
        data.get("cost"),
        json.dumps(data.get("extra_info", {})),
        id_service,
    )
    return execute_sql(sql, val, 3, data_token)


def delete_service(id_service: int, data_token):
    sql = f"DELETE FROM {_T_SERVICES} WHERE id = %s"
    return execute_sql(sql, (id_service,), 3, data_token)


def get_service_by_id(id_service: int, data_token):
    sql = f"{_SEL_SERVICES} WHERE id = %s"
    return execute_sql(sql, (id_service,), 1, data_token)


def get_services(vehicle_id, service_type, date_from, date_to, data_token):
    sql = (
        f"{_SEL_SERVICES} "
        "WHERE (vehicle_id = %s OR %s IS NULL) "
        "AND (service_type = %s OR %s IS NULL) "
        "AND (`date` >= %s OR %s IS NULL) "
        "AND (`date` <= %s OR %s IS NULL) "
        "ORDER BY `date` DESC, id DESC"
    )
    val = (
        vehicle_id, vehicle_id,
        service_type, service_type,
        date_from, date_from,
        date_to, date_to,
    )
    return execute_sql(sql, val, 2, data_token)


# --- Llantas ------------------------------------------------------------------
def insert_tire(data: dict, data_token):
    sql = (
        f"INSERT INTO {_T_TIRES} "
        "(vehicle_id, position, dot, manufacture_date, brand, expiry_date, "
        "physical_state, needs_change, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("vehicle_id"),
        data.get("position"),
        data.get("dot"),
        data.get("manufacture_date"),
        data.get("brand"),
        data.get("expiry_date"),
        data.get("physical_state"),
        data.get("needs_change", 0),
        json.dumps(data.get("history", [])),
        json.dumps(data.get("extra_info", {})),
    )
    return execute_sql(sql, val, 4, data_token)


def update_tire(id_tire: int, data: dict, data_token):
    sql = (
        f"UPDATE {_T_TIRES} SET "
        "dot = %s, manufacture_date = %s, brand = %s, expiry_date = %s, "
        "physical_state = %s, needs_change = %s, history = %s, extra_info = %s "
        "WHERE id = %s"
    )
    val = (
        data.get("dot"),
        data.get("manufacture_date"),
        data.get("brand"),
        data.get("expiry_date"),
        data.get("physical_state"),
        data.get("needs_change", 0),
        json.dumps(data.get("history", [])),
        json.dumps(data.get("extra_info", {})),
        id_tire,
    )
    return execute_sql(sql, val, 3, data_token)


def delete_tire(id_tire: int, data_token):
    sql = f"DELETE FROM {_T_TIRES} WHERE id = %s"
    return execute_sql(sql, (id_tire,), 3, data_token)


def get_tire_by_position(vehicle_id: int, position: int, data_token):
    sql = f"{_SEL_TIRES} WHERE vehicle_id = %s AND position = %s"
    return execute_sql(sql, (vehicle_id, position), 1, data_token)


def get_tires(vehicle_id, data_token):
    sql = (
        f"{_SEL_TIRES} "
        "WHERE (vehicle_id = %s OR %s IS NULL) "
        "ORDER BY vehicle_id, position"
    )
    return execute_sql(sql, (vehicle_id, vehicle_id), 2, data_token)


# --- Multas -------------------------------------------------------------------
def insert_fine(data: dict, data_token):
    sql = (
        f"INSERT INTO {_T_FINES} "
        "(vehicle_id, `year`, `month`, amount, description, responsible, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("vehicle_id"),
        data.get("year"),
        data.get("month"),
        data.get("amount"),
        data.get("description"),
        data.get("responsible"),
        json.dumps(data.get("extra_info", {})),
    )
    return execute_sql(sql, val, 4, data_token)


def update_fine(id_fine: int, data: dict, data_token):
    sql = (
        f"UPDATE {_T_FINES} SET "
        "`year` = %s, `month` = %s, amount = %s, description = %s, "
        "responsible = %s, extra_info = %s "
        "WHERE id = %s"
    )
    val = (
        data.get("year"),
        data.get("month"),
        data.get("amount"),
        data.get("description"),
        data.get("responsible"),
        json.dumps(data.get("extra_info", {})),
        id_fine,
    )
    return execute_sql(sql, val, 3, data_token)


def delete_fine(id_fine: int, data_token):
    sql = f"DELETE FROM {_T_FINES} WHERE id = %s"
    return execute_sql(sql, (id_fine,), 3, data_token)


def get_fine_by_id(id_fine: int, data_token):
    sql = f"{_SEL_FINES} WHERE id = %s"
    return execute_sql(sql, (id_fine,), 1, data_token)


def get_fines(vehicle_id, year, data_token):
    sql = (
        f"{_SEL_FINES} "
        "WHERE (vehicle_id = %s OR %s IS NULL) "
        "AND (`year` = %s OR %s IS NULL) "
        "ORDER BY `year` DESC, `month`, id"
    )
    return execute_sql(sql, (vehicle_id, vehicle_id, year, year), 2, data_token)


# --- Pendiente de compra ------------------------------------------------------
def insert_vehicle_purchase(data: dict, data_token):
    sql = (
        f"INSERT INTO {_T_PURCHASES} "
        "(vehicle_id, checklist_sent, checklist_sent_date, problem, quantity, "
        "unit, cost, supplier, observations, status, po_id, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("vehicle_id"),
        data.get("checklist_sent", 0),
        data.get("checklist_sent_date"),
        data.get("problem"),
        data.get("quantity"),
        data.get("unit"),
        data.get("cost"),
        data.get("supplier"),
        data.get("observations"),
        data.get("status", 0),
        data.get("po_id"),
        json.dumps(data.get("extra_info", {})),
    )
    return execute_sql(sql, val, 4, data_token)


def update_vehicle_purchase(id_purchase: int, data: dict, data_token):
    sql = (
        f"UPDATE {_T_PURCHASES} SET "
        "checklist_sent = %s, checklist_sent_date = %s, problem = %s, "
        "quantity = %s, unit = %s, cost = %s, supplier = %s, observations = %s, "
        "status = %s, po_id = %s, extra_info = %s "
        "WHERE id = %s"
    )
    val = (
        data.get("checklist_sent", 0),
        data.get("checklist_sent_date"),
        data.get("problem"),
        data.get("quantity"),
        data.get("unit"),
        data.get("cost"),
        data.get("supplier"),
        data.get("observations"),
        data.get("status", 0),
        data.get("po_id"),
        json.dumps(data.get("extra_info", {})),
        id_purchase,
    )
    return execute_sql(sql, val, 3, data_token)


def delete_vehicle_purchase(id_purchase: int, data_token):
    sql = f"DELETE FROM {_T_PURCHASES} WHERE id = %s"
    return execute_sql(sql, (id_purchase,), 3, data_token)


def get_vehicle_purchase_by_id(id_purchase: int, data_token):
    sql = f"{_SEL_PURCHASES} WHERE id = %s"
    return execute_sql(sql, (id_purchase,), 1, data_token)


def get_vehicle_purchases(vehicle_id, status, date_from, date_to, data_token):
    sql = (
        f"{_SEL_PURCHASES} "
        "WHERE (vehicle_id = %s OR %s IS NULL) "
        "AND (status = %s OR %s IS NULL) "
        "AND (DATE(created_at) >= %s OR %s IS NULL) "
        "AND (DATE(created_at) <= %s OR %s IS NULL) "
        "ORDER BY created_at DESC, id DESC"
    )
    val = (
        vehicle_id, vehicle_id,
        status, status,
        date_from, date_from,
        date_to, date_to,
    )
    return execute_sql(sql, val, 2, data_token)
