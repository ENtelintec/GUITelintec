# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/mar/2025  at 16:27 $"

import json

from templates.database.connection import execute_sql


def get_all_bitacora_rh_db():
    sql = (
        "SELECT "
        "sql_telintec.bitacora_rh.id_event, "
        "sql_telintec.bitacora_rh.emp_id, "
        "sql_telintec.bitacora_rh.event, "
        "sql_telintec.bitacora_rh.timestamp, "
        "sql_telintec.bitacora_rh.extra_info, "
        "sql_telintec.employees.name, "
        "sql_telintec.employees.l_name, "
        "sql_telintec.employees.contrato "
        "FROM sql_telintec.bitacora_rh "
        "LEFT JOIN sql_telintec.employees ON bitacora_rh.emp_id = employees.employee_id "
        "ORDER BY name, l_name DESC "
    )
    flag, error, my_result = execute_sql(sql, None, 5)
    return flag, error, my_result


def insert_bitacora_rh_db(emp_id, event, timestamp, comment, value):
    extra_info = {"comment":  comment, "value": value}
    sql = (
        "INSERT INTO sql_telintec.bitacora_rh (emp_id, event, timestamp, extra_info) "
        "VALUES (%s, %s, %s, %s)"
    )
    vals = (emp_id, event, timestamp, json.dumps(extra_info))
    flag, error, my_result = execute_sql(sql, vals, 4)
    return flag, error, my_result


def update_bitacora_rh_db(id_event, emp_id, event, timestamp, comment, value):
    sql = (
        "UPDATE sql_telintec.bitacora_rh "
        "SET emp_id = %s, event = %s, timestamp = %s, "
        "extra_info = JSON_REPLACE(extra_info, '$.comment', %s), extra_info = JSON_REPLACE(extra_info, '$.value', %s)"
        "WHERE id_event = %s"
    )
    vals = (emp_id, event, timestamp, comment, value, id_event)
    flag, error, my_result = execute_sql(sql, vals, 3)
    return flag, error, my_result


def delete_bitacora_rh_db(id_event):
    sql = "DELETE FROM sql_telintec.bitacora_rh WHERE id_event = %s"
    vals = (id_event,)
    flag, error, my_result = execute_sql(sql, vals, 3)
    return flag, error, my_result

