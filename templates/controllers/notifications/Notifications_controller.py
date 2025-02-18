# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 16:17 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def get_notifications_by_user(user_id: int, status="%"):
    sql = (
        "SELECT timestamp, id, body "
        "FROM sql_telintec.notifications_gui "
        "WHERE body->'$.receiver_id' = %s and body->'$.status' like %s ORDER BY body->'$.status' , timestamp DESC "
    )
    vals = (user_id, status)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def get_notifications_by_permission(permissions_keys: list, sender_id="%", status="%"):
    regexp_clauses = " OR ".join(
        [f"body->'$.app' REGEXP '{key}'" for key in permissions_keys]
    )
    sql = (
        f"SELECT timestamp, id, body "
        f"FROM sql_telintec.notifications_gui "
        f"WHERE ({regexp_clauses}) and body->'$.status' like %s OR body->'$.sender_id' like %s "
        f"ORDER BY body->'$.status', timestamp DESC"
    )
    vals = (status, sender_id)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def insert_notification(body: dict):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    sql = (
        "INSERT INTO sql_telintec.notifications_gui (body, timestamp) "
        "VALUES (%s, %s)"
    )
    vals = (json.dumps(body), timestamp)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_notification_body(id_not: int, body: dict):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    sql = (
        "UPDATE sql_telintec.notifications_gui "
        "SET body = %s, timestamp = %s "
        "WHERE id = %s"
    )
    vals = (json.dumps(body), timestamp, id_not)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_status_notification(id_not: int, status: int):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    sql = (
        "UPDATE sql_telintec.notifications_gui "
        "SET body = JSON_REPLACE(body, '$.status', %s), timestamp = %s "
        "WHERE id = %s"
    )
    vals = (status, timestamp, id_not)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result
