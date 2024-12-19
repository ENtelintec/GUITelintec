# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 16:17 $"

import json
from datetime import datetime

from static.constants import format_timestamps
from templates.database.connection import execute_sql


def get_notifications_by_user(user_id: int, status="%"):
    sql = (
        "SELECT timestamp, id, body "
        "FROM sql_telintec.notifications_gui "
        "WHERE body->'$.receiver_id' = %s and body->'$.status' like %s "
    )
    vals = (user_id, status)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def get_notifications_by_permission(permissions_key: str, status="%"):
    sql = (
        "SELECT timestamp, id, body "
        "FROM sql_telintec.notifications_gui "
        "WHERE body->'$.app' REGEXP %s and body->'$.status' like %s "
    )
    vals = (permissions_key, status)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def get_notification_by_permission(user_id: int, permissions=None):
    sql = (
        "SELECT timestamp, id, body "
        "FROM sql_telintec.notifications_gui "
        "WHERE body->'$.receiver_id' = %s "
    )
    vals = (user_id,)
    if permissions is not None:
        for item in permissions:
            sql += f"OR body->'$.app' REGEXP '{item.lower()}' "
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def insert_notification(body: dict):
    timestamp = datetime.now().strftime(format_timestamps)
    sql = (
        "INSERT INTO sql_telintec.notifications_gui (body, timestamp) "
        "VALUES (%s, %s)"
    )
    vals = (json.dumps(body), timestamp)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_notification_body(id_not: int, body: dict):
    timestamp = datetime.now().strftime(format_timestamps)
    sql = (
        "UPDATE sql_telintec.notifications_gui "
        "SET body = %s, timestamp = %s "
        "WHERE id = %s"
    )
    vals = (json.dumps(body), timestamp, id_not)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_status_notification(id_not: int, status: int):
    timestamp = datetime.now().strftime(format_timestamps)
    sql = (
        "UPDATE sql_telintec.notifications_gui "
        "SET body = JSON_REPLACE(body, '$.status', %s), timestamp = %s "
        "WHERE id = %s"
    )
    vals = (status, timestamp, id_not)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result
