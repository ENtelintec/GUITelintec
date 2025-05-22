# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 20:19 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.controllers.product.p_and_s_controller import get_stock_db_products
from templates.database.connection import execute_sql


def update_sm_items_stock(tuple_sm):
    flag, error, result = get_stock_db_products()
    tuple_out = []
    product_ids = [product[0] for product in result]
    if flag:
        for sm_data in tuple_sm:
            items_db = json.loads(sm_data[10])
            items_out = []
            for item in items_db:
                if item.get("id", 0) in product_ids:
                    index = product_ids.index(item["id"])
                    item["stock"] = result[index][1]
                items_out.append(item)
            sm_data = list(sm_data)
            sm_data[10] = json.dumps(items_out)
            tuple_out.append(sm_data)
    return tuple_out


def get_sm_entries(emp_id=-1):
    try:
        emp_id = int(emp_id)
    except ValueError:
        return False, "Invalid employee ID", []
    if emp_id <= -1:
        sql = (
            "SELECT "
            "sm_id, folio, contract, facility, location, client_id, emp_id, "
            "pedido_cotizacion, date, limit_date, "
            "items, status, history, comment, extra_info "
            "FROM sql_telintec.materials_request where emp_id like '%'"
        )
        flag, error, result = execute_sql(sql, None, 5)
    else:
        sql = "SELECT contrato from sql_telintec.employees where employee_id = %s "
        val = (emp_id,)
        flag, error, result = execute_sql(sql, val, 1)
        if flag and len(result) > 0:
            sql = (
                "SELECT sm_id, folio, contract, facility, location, client_id, emp_id, "
                "pedido_cotizacion, date, limit_date, "
                "items, status, history, comment, extra_info "
                "FROM sql_telintec.materials_request "
                "WHERE contract = %s or emp_id = %s "
            )
            val = (
                result[0],
                emp_id,
            )
            flag, error, result = execute_sql(sql, val, 2)
        else:
            return False, "Invalid employee ID", []
    result = update_sm_items_stock(result)
    return flag, error, result


def insert_sm_db(data):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    event = [
        {
            "event": "creation",
            "date": timestamp,
            "user": data["info"]["emp_id"],
        }
    ]
    extra_info = {
        "destination": data["info"].get("destination"),
        "contract_contact": data["info"].get("contract_contact"),
        # Nuevos campos con valores predeterminados
        "project": data["info"].get("project", ""),
        "urgent": data["info"].get("urgent", 0),
        "activity_description": data["info"].get("activity_description", ""),
        "request_date": timestamp,
        "requesting_user_status": data["info"].get("requesting_user_status", 0),
        "warehouse_reviewed": data["info"].get("warehouse_reviewed", 0),
        "warehouse_status": data["info"].get("warehouse_status", 1),
        "admin_notification_date": data["info"].get("admin_notification_date", ""),
        "kpi_warehouse": data["info"].get("kpi_warehouse", 0),
        "warehouse_comments": data["info"].get("warehouse_comments", ""),
        "admin_reviewed": data["info"].get("admin_reviewed", 0),
        "admin_status": data["info"].get("admin_status", 1),
        "warehouse_notification_date": data["info"].get(
            "warehouse_notification_date", ""
        ),
        "purchasing_kpi": data["info"].get("purchasing_kpi", 0),
        "admin_comments": data["info"].get("admin_comments", ""),
        "general_request_status": data["info"].get("general_request_status", 1),
        "operations_notification_date": data["info"].get(
            "operations_notification_date", ""
        ),
        "operations_kpi": data["info"].get("operations_kpi", 0),
        "requesting_user_state": data["info"].get("requesting_user_state", ""),
    }
    sql = (
        "INSERT INTO sql_telintec.materials_request "
        "(folio, contract, facility, location, "
        "client_id, emp_id, pedido_cotizacion, date, limit_date, items, status, history, comment, extra_info)"
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data["info"]["folio"],
        data["info"]["contract"],
        data["info"]["facility"],
        data["info"]["location"],
        data["info"]["client_id"],
        data["info"]["emp_id"],
        data["info"]["order_quotation"],
        data["info"]["date"],
        data["info"]["critical_date"],
        json.dumps(data["items"]),
        0,
        json.dumps(event),
        data["info"]["comment"],
        json.dumps(extra_info),
    )
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def delete_sm_db(id_m: int):
    sql = "DELETE FROM sql_telintec.materials_request " "WHERE sm_id = %s"
    val = (id_m,)
    flag, error, result = execute_sql(sql, val, 3)
    if not flag:
        return False, error, None
    sql = (
        "SELECT sm_id, folio, contract, facility, location, client_id, emp_id, date, limit_date, "
        "items, status, history, comment, pedido_cotizacion "
        "FROM sql_telintec.materials_request "
        "WHERE sm_id = %s "
    )
    val = (id_m,)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return True, "Material request deleted", None
    else:
        return False, "Material request not deleted", None


def update_sm_db(data):
    data["id"] = data["info"]["id"]
    sql = (
        "SELECT sm_id, extra_info FROM sql_telintec.materials_request "
        "WHERE sm_id = %s "
    )
    vals = (data["id"],)
    flag, error, result = execute_sql(sql, vals, 1)
    if not flag:
        return False, f"Error at retriving sm from db: {error}", None
    if len(result) == 0:
        return False, "Material request not found", None
    extra_info = json.loads(result[1])
    extra_info["destination"] = data["info"]["destination"]
    extra_info["contract_contact"] = data["info"]["contract_contact"]
    history = data["info"]["history"]
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    event = {
        "event": "update",
        "date": timestamp,
        "user": data["info"]["emp_id"],
    }
    history.append(event)
    sql = (
        "UPDATE sql_telintec.materials_request "
        "SET folio = %s, contract = %s, facility = %s, location = %s, "
        "client_id = %s, emp_id = %s, date = %s, limit_date = %s, items = %s, status = 0, pedido_cotizacion = %s, "
        "history = %s, comment = %s, extra_info = %s "
        "WHERE sm_id = %s"
    )
    val = (
        data["info"]["folio"],
        data["info"]["contract"],
        data["info"]["facility"],
        data["info"]["location"],
        data["info"]["client_id"],
        data["info"]["emp_id"],
        data["info"]["date"],
        data["info"]["critical_date"],
        json.dumps(data["items"]),
        data["info"]["order_quotation"],
        json.dumps(history),
        data["info"]["comment"],
        json.dumps(extra_info),
        data["id"],
    )
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def cancel_sm_db(id_m: int, history: dict):
    sql = "SELECT sm_id " "FROM sql_telintec.materials_request "
    flag, error, result = execute_sql(sql, None, 5)
    if not flag:
        return False, error, None
    ids_sm = [i[0] for i in result]
    if id_m not in ids_sm:
        return True, "Material request not found", None
    sql = (
        "UPDATE sql_telintec.materials_request "
        "SET status = -1, history = %s  "
        "WHERE sm_id = %s "
    )
    val = (json.dumps(history), id_m)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def update_history_sm(sm_id, history: dict, items: list, is_complete=False):
    if is_complete:
        sql = (
            "UPDATE sql_telintec.materials_request "
            "SET history = %s, status = 2 , items = %s "
            "WHERE sm_id = %s "
        )
        val = (json.dumps(history), json.dumps(items), sm_id)
        flag, error, result = execute_sql(sql, val, 4)
    else:
        sql = (
            "UPDATE sql_telintec.materials_request "
            "SET history = %s, status = 1, items = %s "
            "WHERE sm_id = %s "
        )
        val = (json.dumps(history), json.dumps(items), sm_id)
        flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def update_products_sm(sm_id, items: list):
    sql = "UPDATE sql_telintec.materials_request " "SET items = %s " "WHERE sm_id = %s "
    val = (json.dumps(items), sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def finalize_status_sm(sm_id: int):
    sql = "UPDATE sql_telintec.materials_request " "SET status = 3 " "WHERE sm_id = %s "
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_all_sm_plots(emp_id: int, is_supper=False):
    if is_supper:
        sql = (
            "SELECT sm_id, emp_id, date, limit_date, status "
            "FROM sql_telintec.materials_request "
        )
        val = None
    else:
        sql = (
            "SELECT sm_id, emp_id, date, limit_date, status "
            "FROM sql_telintec.materials_request "
            "WHERE emp_id = %s "
        )
        val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 5 if is_supper else 2)
    return flag, error, result


def update_only_status(status: int, sm_id: int):
    sql = (
        "UPDATE "
        "sql_telintec.materials_request "
        "SET status = %s "
        "WHERE sm_id = %s "
    )
    val = (status, sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_sm_by_id(sm_id: int):
    sql = (
        "SELECT "
        "sm_id, folio, contract, facility, location, "
        "client_id, emp_id, pedido_cotizacion, date, "
        "limit_date, items, status, history, "
        "comment, extra_info "
        "FROM sql_telintec.materials_request "
        "WHERE sm_id = %s"
    )
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def get_info_names_by_sm_id(sm_id: int):
    sql = (
        "SELECT "
        "sql_telintec.customers_amc.name, "
        "sql_telintec.employees.name, "
        "sql_telintec.employees.l_name "
        "FROM sql_telintec.materials_request "
        "INNER JOIN sql_telintec.customers_amc ON sql_telintec.materials_request.client_id = sql_telintec.customers_amc.id_customer "
        "INNER JOIN sql_telintec.employees ON sql_telintec.materials_request.emp_id = sql_telintec.employees.employee_id "
        "WHERE sm_id = %s"
    )
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def update_sm_products_by_id(sm_id: int, items: list):
    sql = (
        "UPDATE "
        "sql_telintec.materials_request "
        "SET items = %s "
        "WHERE sm_id = %s "
    )
    val = (json.dumps(items), sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_folios_by_pattern(pattern: str):
    sql = "SELECT folio FROM sql_telintec.materials_request WHERE folio LIKE %s"
    val = (f"{pattern}%",)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result


def update_history_extra_info_sm_by_id(
    sm_id: int, extra_info: dict, history: dict, comments: str
):
    sql = (
        "UPDATE sql_telintec.materials_request "
        "SET extra_info = %s, history = %s, comment = %s "
        "WHERE sm_id = %s "
    )
    val = (json.dumps(extra_info), json.dumps(history), comments, sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_pending_sm_db():
    sql = (
        "SELECT "
        "sm_id, folio, contract, facility, location, "
        "client_id, emp_id, pedido_cotizacion, date, "
        "limit_date, items, status, history, "
        "comment, extra_info "
        "FROM sql_telintec.materials_request "
        "WHERE status = 0 "
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result
