# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 16:17 $'

import json
from datetime import datetime

from static.extensions import format_timestamps
from templates.database.connection import execute_sql


def get_notifications_by_user(user_id: int):
    sql = ("SELECT timestamp, id, body "
           "FROM notifications_gui "
           "WHERE body->'$.receiver_id' = %s")
    vals = (user_id, )
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def get_notification_by_id(id_not: int):
    sql = ("SELECT timestamp, id, body "
           "FROM notifications_gui "
           "WHERE id = %s")
    vals = (id_not,)
    flag, error, result = execute_sql(sql, vals, 1)
    return flag, error, result


def insert_notification(body: dict):
    timestamp = datetime.now().strftime(format_timestamps)
    sql = ("INSERT INTO notifications_gui (body, timestamp) "
           "VALUES (%s, %s)")
    vals = (json.dumps(body), timestamp)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_notification_body(id_not: int, body: dict):
    timestamp = datetime.now().strftime(format_timestamps)
    sql = ("UPDATE notifications_gui "
           "SET body = %s, timestamp = %s "
           "WHERE id = %s")
    vals = (json.dumps(body), timestamp, id_not)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result
