# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:19 $'

import json
from datetime import datetime

from static.extensions import format_timestamps
from templates.database.connection import execute_sql


def get_sm_entries(emp_id=-1):
    try:
        emp_id = int(emp_id)
    except ValueError:
        return False, "Invalid employee ID", []
    if emp_id <= -1:
        sql = (
            "SELECT sm_id, folio, contract, facility, location, client_id, emp_id, "
            "pedido_cotizacion, date, limit_date, "
            "items, status, history, comment "
            "FROM sql_telintec.materials_request ")
        flag, error, result = execute_sql(sql, None, 5)
    else:
        sql = "SELECT contrato from sql_telintec.employees where employee_id = %s "
        val = (emp_id,)
        flag, error, result = execute_sql(sql, val, 1)
        if flag and len(result) > 0:
            sql = (
                "SELECT sm_id, folio, contract, facility, location, client_id, emp_id, "
                "pedido_cotizacion, date, limit_date, "
                "items, status, history, comment "
                "FROM sql_telintec.materials_request "
                "WHERE contract = %s")
            val = (result[0],)
            flag, error, result = execute_sql(sql, val, 2)
        else:
            return False, "Invalid employee ID", []
    return flag, error, result


def insert_sm_db(data):
    event = [{"event": "creation",
              "date": datetime.now().strftime(format_timestamps), "user": data['info']['emp_id']}]
    extra_info = {"destination": data['info']['destination']}
    sql = ("INSERT INTO sql_telintec.materials_request "
           "(folio, contract, facility, location, "
           "client_id, emp_id, pedido_cotizacion, date, limit_date, items, status, history, comment, extra_info)"
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    val = (data['info']['folio'], data['info']['contract'], data['info']['facility'],
           data['info']['location'], data['info']['client_id'], data['info']['emp_id'],
           data['info']['order_quotation'], data['info']['date'], data['info']['critical_date'],
           json.dumps(data['items']), 0, json.dumps(event), data['info']['comment'], json.dumps(extra_info))
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def delete_sm_db(id_m: int):
    sql = ("DELETE FROM sql_telintec.materials_request "
           "WHERE sm_id = %s")
    val = (id_m,)
    flag, error, result = execute_sql(sql, val, 3)
    if not flag:
        return False, error, None
    sql = ("SELECT sm_id, folio, contract, facility, location, client_id, emp_id, date, limit_date, "
           "items, status, history, comment, pedido_cotizacion "
           "FROM sql_telintec.materials_request "
           "WHERE sm_id = %s ")
    val = (id_m,)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return True, "Material request deleted", None
    else:
        return False, "Material request not deleted", None


def update_sm_db(data):
    sql = ("SELECT sm_id "
           "FROM sql_telintec.materials_request ")
    flag, error, result = execute_sql(sql, None, 5)
    if not flag:
        return False, error, None
    ids_sm = [i[0] for i in result]
    if data['id_sm'] not in ids_sm:
        return True, "Material request not found", None
    extra_info = {"destination": data['info']['destination']}
    sql = ("UPDATE sql_telintec.materials_request "
           "SET folio = %s, contract = %s, facility = %s, location = %s, "
           "client_id = %s, emp_id = %s, date = %s, limit_date = %s, items = %s, status = 0, pedido_cotizacion = %s, "
           "history = %s, comment = %s, extra_info = %s "
           "WHERE sm_id = %s")
    val = (data['info']['folio'], data['info']['contract'], data['info']['facility'],
           data['info']['location'], data['info']['client_id'], data['info']['emp_id'], data['info']['date'],
           data['info']['critical_date'], json.dumps(data['items']),
           data['info']['order_quotation'], json.dumps(data['info']['history']),
           data['info']['comment'], json.dumps(extra_info),
           data['id_sm'])
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def cancel_sm_db(id_m: int, history: dict):
    sql = ("SELECT sm_id "
           "FROM sql_telintec.materials_request ")
    flag, error, result = execute_sql(sql, None, 5)
    if not flag:
        return False, error, None
    ids_sm = [i[0] for i in result]
    if id_m not in ids_sm:
        return True, "Material request not found", None
    sql = ("UPDATE sql_telintec.materials_request "
           "SET status = -1, history = %s  "
           "WHERE sm_id = %s ")
    val = (json.dumps(history), id_m)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def update_history_sm(sm_id, history: dict, items: list, is_complete=False):
    if is_complete:
        sql = ("UPDATE sql_telintec.materials_request "
               "SET history = %s, status = 2 , items = %s "
               "WHERE sm_id = %s ")
        val = (json.dumps(history), json.dumps(items), sm_id)
        flag, error, result = execute_sql(sql, val, 4)
    else:
        sql = ("UPDATE sql_telintec.materials_request "
               "SET history = %s, status = 1, items = %s "
               "WHERE sm_id = %s ")
        val = (json.dumps(history), json.dumps(items), sm_id)
        flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def finalize_status_sm(sm_id: int):
    sql = ("UPDATE sql_telintec.materials_request "
           "SET status = 3 "
           "WHERE sm_id = %s ")
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_all_sm_plots(emp_id: int, is_supper=False):
    if is_supper:
        sql = ("SELECT sm_id, emp_id, date, limit_date, status "
               "FROM sql_telintec.materials_request ")
        val = None
    else:
        sql = ("SELECT sm_id, emp_id, date, limit_date, status "
               "FROM sql_telintec.materials_request "
               "WHERE emp_id = %s ")
        val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 5 if is_supper else 2)
    return flag, error, result


def update_only_status(status: int, sm_id: int):
    sql = ("UPDATE sql_telintec.materials_request "
           "SET status = %s "
           "WHERE sm_id = %s ")
    val = (status, sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_sm_by_id(sm_id: int):
    sql = ("SELECT "
           "sm_id, folio, contract, facility, location, client_id, emp_id, pedido_cotizacion, date, "
           "limit_date, items, status, history, comment, extra_info "
           "FROM sql_telintec.materials_request "
           "WHERE sm_id = %s")
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def get_info_names_by_sm_id(sm_id: int):
    sql = ("SELECT "
           "sql_telintec.customers_amc.name, "
           "sql_telintec.employees.name, "
           "sql_telintec.employees.l_name "
           "FROM sql_telintec.materials_request "
           "INNER JOIN sql_telintec.customers_amc ON sql_telintec.materials_request.client_id = sql_telintec.customers_amc.id_customer "
           "INNER JOIN sql_telintec.employees ON sql_telintec.materials_request.emp_id = sql_telintec.employees.employee_id "
           "WHERE sm_id = %s")
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def update_sm_products_by_id(sm_id: int, items: list):
    sql = ("UPDATE sql_telintec.materials_request "
           "SET items = %s "
           "WHERE sm_id = %s ")
    val = (json.dumps(items), sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result
