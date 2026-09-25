# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 16:17 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def _status_key(row) -> tuple:
    """status del body (entero 0/1 en las 3 BDs); otro tipo o sin status va al final."""
    status = json.loads(row[2]).get("status")
    if isinstance(status, int) and not isinstance(status, bool):
        return 0, status
    return 1, 0


def _sort_notifications(rows: list) -> list:
    """Mismo orden que el antiguo ORDER BY body->'$.status', timestamp DESC, con
    desempate fijo por id DESC (en SQL el empate no estaba definido; MySQL daba
    casi siempre el id mas nuevo primero). Dos pasadas estables: primero
    timestamp/id DESC, luego status ASC."""
    rows = sorted(rows, key=lambda row: (row[0], row[1]), reverse=True)
    return sorted(rows, key=_status_key)


# Sin ORDER BY en estas consultas: el WHERE y el orden salen de body, asi que
# cualquier sort sobre notifications_gui mete el body completo al sort buffer
# (256 KB) y una sola notificacion enorme truena con 1038 "Out of sort memory".
# Se ordena en Python con _sort_notifications.
def get_notifications_by_user(user_id: int, data_token, status="%"):
    sql = (
        "SELECT timestamp, id, body "
        "FROM sql_telintec.notifications_gui "
        "WHERE body->'$.receiver_id' = %s and body->'$.status' like %s"
    )
    vals = (user_id, status)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    if flag and isinstance(result, list):
        result = _sort_notifications(result)
    return flag, error, result


def get_notifications_by_permission(permissions_keys: list, data_token, sender_id="%", status="%"):
    regexp_clauses = " OR ".join(
        [f"body->'$.app' REGEXP '{key}'" for key in permissions_keys]
    )
    sql = (
        f"SELECT timestamp, id, body "
        f"FROM sql_telintec.notifications_gui "
        f"WHERE ({regexp_clauses}) and body->'$.status' like %s OR body->'$.sender_id' like %s"
    )
    vals = (status, sender_id)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    if flag and isinstance(result, list):
        result = _sort_notifications(result)
    return flag, error, result


def insert_notification(body: dict, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    sql = (
        "INSERT INTO sql_telintec.notifications_gui (body, timestamp) "
        "VALUES (%s, %s)"
    )
    vals = (json.dumps(body), timestamp)
    flag, error, result = execute_sql(sql, vals, 4, data_token)
    return flag, error, result


def update_notification_body(id_not: int, body: dict, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    sql = (
        "UPDATE sql_telintec.notifications_gui "
        "SET body = %s, timestamp = %s "
        "WHERE id = %s"
    )
    vals = (json.dumps(body), timestamp, id_not)
    flag, error, result = execute_sql(sql, vals, 4, data_token)
    return flag, error, result


def update_status_notification(id_not: int, status: int, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    sql = (
        "UPDATE sql_telintec.notifications_gui "
        "SET body = JSON_REPLACE(body, '$.status', %s), timestamp = %s "
        "WHERE id = %s"
    )
    vals = (status, timestamp, id_not)
    flag, error, result = execute_sql(sql, vals, 4, data_token)
    return flag, error, result
