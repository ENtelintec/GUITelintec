# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 24/may./2024  at 16:26 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def create_task(task_title, emp_destiny, emp_origin, task_date, metadata, dict_quizz):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    body = {
        "title": task_title,
        "emp_destiny": emp_destiny,
        "emp_origin": emp_origin,
        "date_limit": task_date,
        "metadata": metadata,
        "status": 0,
        "changes": [{"action": "creation", "timestamp": timestamp}],
    }
    data_raw = {}
    sql = (
        "INSERT INTO sql_telintec.tasks_gui (body, timestamp, data_raw) "
        "VALUES (%s, %s, %s)"
    )
    val = (json.dumps(body), timestamp, json.dumps(data_raw))
    flag, error, id_task = execute_sql(sql, val, 4)
    return flag, error, id_task


def update_task(id_task, body: dict, status=None, metadata=None, data_raw=None):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    body["status"] = status if status is not None else body["status"]
    body["metadata"] = metadata if metadata is not None else body["metadata"]
    changes = (
        body["changes"] if isinstance(body["changes"], list) else [body["changes"]]
    )
    changes.append({"action": "update", "timestamp": timestamp})
    data_raw = data_raw if data_raw is not None else {}
    sql = (
        "UPDATE sql_telintec.tasks_gui "
        "SET body = %s, "
        "timestamp = %s, "
        "data_raw = %s "
        "WHERE id = %s"
    )
    val = (json.dumps(body), timestamp, json.dumps(data_raw), id_task)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_task(id_task):
    sql = "DELETE FROM sql_telintec.tasks_gui " "WHERE id = %s"
    val = (id_task,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def get_all_tasks_by_status(
    status, id_task=None, id_destiny=None, id_origin=None, title="quizz"
):
    if status is None or status == -1 or id_task is not None:
        status = "%"
    sql = (
        "SELECT id, body, data_raw, timestamp "
        "FROM sql_telintec.tasks_gui "
        "WHERE body->'$.status' LIKE %s "
    )
    vals = (status,)
    if id_task is not None:
        sql += "AND id = %s "
        vals += (id_task,)
    else:
        if title is not None:
            sql += "AND LCASE(body->'$.title') REGEXP %s "
            vals += (title.lower(),)
        if id_destiny is not None:
            sql += "AND body->'$.emp_destiny' = %s "
            vals += (id_destiny,)
        if id_origin is not None:
            sql += "AND body->'$.emp_origin' = %s "
            vals += (id_origin,)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def get_task_by_id_emp(id_emp):
    sql = (
        "SELECT id, body, data_raw, timestamp "
        "FROM sql_telintec.tasks_gui "
        "WHERE body->'$.emp_destiny' = %s "
    )
    vals = (id_emp,)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result
