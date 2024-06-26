# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:19 $'

import json
from datetime import datetime

from templates.database.connection import execute_sql


def get_sm_entries():
    sql = (
        "SELECT sm_id, sm_code, folio, contract, facility, location, client_id, emp_id, "
        "pedido_cotizacion, date, limit_date, "
        "items, status, history, comment "
        "FROM materials_request ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def insert_sm_db(data):
    event = [{"event": "creation",
              "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "user": data['info']['emp_id']}]
    sql = ("INSERT INTO materials_request "
           "(sm_code, folio, contract, facility, location, "
           "client_id, emp_id, pedido_cotizacion, date, limit_date, items, status, history, comment)"
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    val = (data['info']['sm_code'], data['info']['folio'], data['info']['contract'], data['info']['facility'],
           data['info']['location'], data['info']['client_id'], data['info']['emp_id'],
           data['info']['order_quotation'], data['info']['date'], data['info']['limit_date'],
           json.dumps(data['items']), 0, json.dumps(event), data['info']['comment'])
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def delete_sm_db(id_m: int, sm_code: str):
    sql = ("DELETE FROM materials_request "
           "WHERE sm_id = %s AND sm_code = %s ")
    val = (id_m, sm_code)
    flag, error, result = execute_sql(sql, val, 3)
    if not flag:
        return False, error, None
    sql = ("SELECT sm_id, sm_code, folio, contract, facility, location, client_id, emp_id, date, limit_date, "
           "items, status, history, comment, pedido_cotizacion "
           "FROM materials_request "
           "WHERE sm_id = %s AND sm_code = %s")
    val = (id_m, sm_code)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return True, "Material request deleted", None
    else:
        return False, "Material request not deleted", None


def update_sm_db(data):
    sql = ("SELECT sm_id "
           "FROM materials_request ")
    flag, error, result = execute_sql(sql, None, 5)
    if not flag:
        return False, error, None
    ids_sm = [i[0] for i in result]
    if data['id_sm'] not in ids_sm:
        return True, "Material request not found", None
    sql = ("UPDATE materials_request "
           "SET sm_code = %s, folio = %s, contract = %s, facility = %s, location = %s, "
           "client_id = %s, emp_id = %s, date = %s, limit_date = %s, items = %s, status = 0, pedido_cotizacion = %s, "
           "history = %s, comment = %s "
           "WHERE sm_id = %s")
    val = (data['info']['sm_code'], data['info']['folio'], data['info']['contract'], data['info']['facility'],
           data['info']['location'], data['info']['client_id'], data['info']['emp_id'], data['info']['date'],
           data['info']['limit_date'], json.dumps(data['items']),
           data['info']['order_quotation'], json.dumps(data['info']['history']),
           data['info']['comment'],
           data['id_sm'])
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def cancel_sm_db(id_m: int, history: dict):
    sql = ("SELECT sm_id "
           "FROM materials_request ")
    flag, error, result = execute_sql(sql, None, 5)
    if not flag:
        return False, error, None
    ids_sm = [i[0] for i in result]
    if id_m not in ids_sm:
        return True, "Material request not found", None
    sql = ("UPDATE materials_request "
           "SET status = -1, history = %s  "
           "WHERE sm_id = %s ")
    val = (json.dumps(history), id_m)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def update_history_sm(sm_id, history: dict, items: list, is_complete=False):
    if is_complete:
        sql = ("UPDATE materials_request "
               "SET history = %s, status = 2 , items = %s "
               "WHERE sm_id = %s ")
        val = (json.dumps(history), json.dumps(items), sm_id)
        flag, error, result = execute_sql(sql, val, 4)
    else:
        sql = ("UPDATE materials_request "
               "SET history = %s, status = 1, items = %s "
               "WHERE sm_id = %s ")
        val = (json.dumps(history), json.dumps(items), sm_id)
        flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def finalize_status_sm(sm_id: int):
    sql = ("UPDATE materials_request SET status = 3 "
           "WHERE sm_id = %s ")
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_all_sm_plots(emp_id: int, is_supper=False):
    if is_supper:
        sql = ("SELECT sm_id, emp_id, date, limit_date, status "
               "FROM materials_request ")
        val = None
    else:
        sql = ("SELECT sm_id, emp_id, date, limit_date, status "
               "FROM materials_request "
               "WHERE emp_id = %s ")
        val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 5 if is_supper else 2)
    return flag, error, result


def update_only_status(status: int, sm_id: int):
    sql = ("UPDATE materials_request "
           "SET status = %s "
           "WHERE sm_id = %s ")
    val = (status, sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result
