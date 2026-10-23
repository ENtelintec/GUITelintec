# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct./2026  at 19:00 $"

"""Check-in con foto (sql_telintec_mod_rrhh.checkins). DDL en
scripts_db_handle/checkins.sql; diseño en docs/checkin_foto.md."""

import json

from templates.database.connection import execute_sql

_TABLE = "sql_telintec_mod_rrhh.checkins"
_TABLE_EMP = "sql_telintec.employees"

# Columnas de los SELECT; el midleware mapea por indice (append-only).
CHECKIN_COLUMNS = (
    "id",
    "emp_id",
    "emp_name",
    "emp_lastname",
    "type",
    "timestamp",
    "lat",
    "lon",
    "accuracy",
    "photo_key",
    "manual",
    "status",
    "created_by",
    "device_info",
    "created_at",
)
# history / extra_info solo en el detalle: un ORDER BY sobre JSON mete el body al
# sort buffer (regla del repo, docs/contracts_products_sort_memory_fix.md).
DETAIL_COLUMNS = CHECKIN_COLUMNS + ("history", "extra_info")
_SELECT = (
    "SELECT c.id, c.emp_id, e.name, e.l_name, c.type, c.timestamp, c.lat, c.lon, c.accuracy, "
    "c.photo_key, c.is_manual, c.status, c.created_by, c.device_info, c.created_at "
    f"FROM {_TABLE} c LEFT JOIN {_TABLE_EMP} e ON e.employee_id = c.emp_id "
)
_SELECT_DETAIL = (
    "SELECT c.id, c.emp_id, e.name, e.l_name, c.type, c.timestamp, c.lat, c.lon, c.accuracy, "
    "c.photo_key, c.is_manual, c.status, c.created_by, c.device_info, c.created_at, c.history, c.extra_info "
    f"FROM {_TABLE} c LEFT JOIN {_TABLE_EMP} e ON e.employee_id = c.emp_id "
)


def insert_checkin(data: dict, data_token):
    """Un evento. type_sql=4 -> id."""
    sql = (
        f"INSERT INTO {_TABLE} (emp_id, type, timestamp, lat, lon, accuracy, photo_key, is_manual, status, "
        "created_by, device_info, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, %s, %s)"
    )
    val = (
        data["emp_id"],
        data["type"],
        data["timestamp"],
        data.get("lat"),
        data.get("lon"),
        data.get("accuracy"),
        data.get("photo_key"),
        1 if data.get("manual") else 0,
        data.get("created_by"),
        data.get("device_info"),
        json.dumps(data.get("history") or [], ensure_ascii=False),
        json.dumps(data.get("extra_info") or {}, ensure_ascii=False),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def get_checkin_by_id(id_checkin: int, data_token):
    """Detalle (DETAIL_COLUMNS) o None. type_sql=1."""
    flag, e, out = execute_sql(_SELECT_DETAIL + "WHERE c.id = %s", (id_checkin,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def get_checkins(emp_id, date_from: str, date_to: str, status, limit: int, data_token):
    """Eventos en el rango (DATE(timestamp) entre date_from y date_to inclusive),
    param-or-NULL en emp_id y status. Mas recientes primero. type_sql=2."""
    sql = (
        _SELECT
        + "WHERE (%s IS NULL OR c.emp_id = %s) "
        "AND DATE(c.timestamp) >= %s AND DATE(c.timestamp) <= %s "
        "AND (%s IS NULL OR c.status = %s) "
        "ORDER BY c.timestamp DESC, c.id DESC LIMIT %s"
    )
    val = (emp_id, emp_id, date_from, date_to, status, status, int(limit))
    flag, e, out = execute_sql(sql, val, 2, data_token)
    if not flag or not isinstance(out, list):
        return False, e, []
    return True, None, out


def cancel_checkin(id_checkin: int, history_entry: dict, data_token):
    """status 0 -> 1 + entrada al history (JSON_ARRAY_APPEND). type_sql=3 -> filas
    (0 = no existe o ya estaba anulado)."""
    sql = (
        f"UPDATE {_TABLE} SET status = 1, "
        "history = JSON_ARRAY_APPEND(COALESCE(history, JSON_ARRAY()), '$', CAST(%s AS JSON)) "
        "WHERE id = %s AND status = 0"
    )
    flag, e, out = execute_sql(sql, (json.dumps(history_entry, ensure_ascii=False), id_checkin), 3, data_token)
    return flag, e, out


def delete_checkin(id_checkin: int, data_token):
    """Solo para limpieza de pruebas; el API no borra eventos. type_sql=3."""
    flag, e, out = execute_sql(f"DELETE FROM {_TABLE} WHERE id = %s", (id_checkin,), 3, data_token)
    return flag, e, out
