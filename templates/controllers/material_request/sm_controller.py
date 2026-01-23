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


def get_sm_entries(emp_id=None):
    base_sql = (
        "SELECT "
        "mr.sm_id, "
        "mr.folio, "
        "mr.contract, "
        "mr.facility, "
        "mr.location, "
        "mr.client_id, "
        "mr.emp_id, "
        "mr.pedido_cotizacion, "
        "mr.date, "
        "mr.limit_date, "
        "JSON_ARRAYAGG(JSON_OBJECT("
        " 'id', smi.id_item, "
        " 'id_inventory', smi.id_inventory, "
        " 'name', smi.name, "
        " 'udm', smi.udm, "
        " 'comment', smi.comment, "
        " 'partida', smi.partida, "
        " 'quantity', smi.quantity, "
        " 'dispatched', smi.dispatched, "
        " 'movements', smi.movements, "
        " 'state', smi.state, "
        " 'extra_info', smi.extra_info, "
        " 'reserved', IFNULL(rsv.reserved, 0), "
        " 'reservation_id', rsv.reservation_id,"
        " 'deliveries', smi.deliveries,"
        " 'state_quantity', smi.state_quantity, "
        " 'state_delivery', smi.state_delivery , "
        " 'reserved_all', rAll.reserved_qty, "
        " 'available_stock', IFNULL(inv.stock, 0) - IFNULL(rAll.reserved_qty, 0), "
        " 'stock', IFNULL(inv.stock, 0) )"
        ") AS items, "
        "mr.status, "
        "mr.history, "
        "mr.comment, "
        "mr.extra_info "
        "FROM sql_telintec.materials_request AS mr "
        "LEFT JOIN sql_telintec.sm_items AS smi ON mr.sm_id = smi.id_sm "
        "LEFT JOIN sql_telintec.products_amc AS inv ON inv.id_product = smi.id_inventory "
        "LEFT JOIN ( "
        "   SELECT id_product, sm_id, quantity AS reserved, reservation_id "
        "   FROM sql_telintec.product_reservations "
        "   WHERE status = 0 "
        ") rsv ON (rsv.sm_id = smi.id_sm) AND (rsv.id_product = smi.id_inventory)  "
        "LEFT JOIN ( "
        "   SELECT id_product, "
        "       SUM(quantity) AS reserved_qty "
        "   FROM sql_telintec.product_reservations"
        "   WHERE status = 0 "
        "   GROUP BY id_product) rAll ON smi.id_inventory = rAll.id_product "
        "WHERE (mr.emp_id = %s OR %s IS NULL) "
        "GROUP BY mr.sm_id"
    )
    val = (emp_id, emp_id)
    flag, error, result = execute_sql(base_sql, val, 2)
    # result = update_sm_items_stock(result)
    if not isinstance(result, list):
        return False, "No SM entries found or error in query", []
    return flag, error, result


def get_sm_by_id(sm_id: int):
    sql = (
        "SELECT "
        "mr.sm_id, "
        "mr.folio, "
        "mr.contract, "
        "mr.facility, "
        "mr.location, "
        "mr.client_id, "
        "mr.emp_id, "
        "mr.pedido_cotizacion, "
        "mr.date, "
        "mr.limit_date, "
        "JSON_ARRAYAGG(JSON_OBJECT("
        " 'id', smi.id_item, "
        " 'id_inventory', smi.id_inventory, "
        " 'name', smi.name, "
        " 'udm', smi.udm, "
        " 'comment', smi.comment, "
        " 'partida', smi.partida, "
        " 'quantity', smi.quantity, "
        " 'dispatched', smi.dispatched, "
        " 'movements', smi.movements, "
        " 'state', smi.state, "
        " 'extra_info', smi.extra_info, "
        " 'reserved', IFNULL(rsv.reserved, 0), "
        " 'reservation_id', rsv.reservation_id,"
        " 'deliveries', smi.deliveries,"
        " 'state_quantity', smi.state_quantity, "
        " 'state_delivery', smi.state_delivery , "
        " 'reserved_all', rAll.reserved_qty, "
        " 'available_stock', IFNULL(inv.stock, 0) - IFNULL(rAll.reserved_qty, 0), "
        " 'stock', IFNULL(inv.stock, 0) )"
        ") AS items, "
        "mr.status, "
        "mr.history, "
        "mr.comment, "
        "mr.extra_info "
        "FROM sql_telintec.materials_request AS mr "
        "LEFT JOIN sql_telintec.sm_items AS smi ON mr.sm_id = smi.id_sm "
        "LEFT JOIN sql_telintec.products_amc AS inv ON inv.id_product = smi.id_inventory "
        "LEFT JOIN ( "
        "   SELECT id_product, sm_id, quantity AS reserved, reservation_id "
        "   FROM sql_telintec.product_reservations "
        "   WHERE status = 0 "
        ") rsv ON (rsv.sm_id = smi.id_sm) AND (rsv.id_product = smi.id_inventory)  "
        "LEFT JOIN ( "
        "   SELECT id_product, "
        "       SUM(quantity) AS reserved_qty "
        "   FROM sql_telintec.product_reservations"
        "   WHERE status = 0 "
        "   GROUP BY id_product) rAll ON smi.id_inventory = rAll.id_product "
        "WHERE mr.sm_id = %s"
    )
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 1)
    if not isinstance(result, tuple):
        return False, "No SM entries found or error in query", []
    return flag, error, result


def get_sm_by_folio(folio: str):
    sql = (
        "SELECT "
        "mr.sm_id, "
        "mr.folio, "
        "mr.contract, "
        "mr.facility, "
        "mr.location, "
        "mr.client_id, "
        "mr.emp_id, "
        "mr.pedido_cotizacion, "
        "mr.date, "
        "mr.limit_date, "
        "JSON_ARRAYAGG(JSON_OBJECT("
        " 'id', smi.id_item, "
        " 'id_inventory', smi.id_inventory, "
        " 'name', smi.name, "
        " 'udm', smi.udm, "
        " 'comment', smi.comment, "
        " 'partida', smi.partida, "
        " 'quantity', smi.quantity, "
        " 'dispatched', smi.dispatched, "
        " 'movements', smi.movements, "
        " 'state', smi.state, "
        " 'extra_info', smi.extra_info, "
        " 'reserved', IFNULL(rsv.reserved, 0), "
        " 'reservation_id', rsv.reservation_id,"
        " 'deliveries', smi.deliveries,"
        " 'state_quantity', smi.state_quantity, "
        " 'state_delivery', smi.state_delivery , "
        " 'reserved_all', rAll.reserved_qty, "
        " 'available_stock', IFNULL(inv.stock, 0) - IFNULL(rAll.reserved_qty, 0), "
        " 'stock', IFNULL(inv.stock, 0) )"
        ") AS items, "
        "mr.status, "
        "mr.history, "
        "mr.comment, "
        "mr.extra_info "
        "FROM sql_telintec.materials_request AS mr "
        "LEFT JOIN sql_telintec.sm_items AS smi ON mr.sm_id = smi.id_sm "
        "LEFT JOIN sql_telintec.products_amc AS inv ON inv.id_product = smi.id_inventory "
        "LEFT JOIN ( "
        "   SELECT id_product, sm_id, quantity AS reserved, reservation_id "
        "   FROM sql_telintec.product_reservations "
        "   WHERE status = 0 "
        ") rsv ON (rsv.sm_id = smi.id_sm) AND (rsv.id_product = smi.id_inventory)  "
        "LEFT JOIN ( "
        "   SELECT id_product, "
        "       SUM(quantity) AS reserved_qty "
        "   FROM sql_telintec.product_reservations"
        "   WHERE status = 0 "
        "   GROUP BY id_product) rAll ON smi.id_inventory = rAll.id_product "
        "WHERE mr.folio = %s"
    )
    val = (folio,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def create_items_sm_db(items: list, sm_id: int):
    errors = []
    results = []
    for item in items:
        sql = (
            "INSERT INTO sql_telintec.sm_items "
            "(id_sm, id_inventory, name, udm, comment, partida, quantity, dispatched, movements, state, extra_info) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        state = 0 if item.get("id", -1) == 1 else 1
        id_inventory = item.get("id") if item.get("id", -1) != 1 else None
        val = (
            sm_id,
            id_inventory,
            item.get("name"),
            item.get("udm", "PZA"),
            item.get("comment", ""),
            item.get("partida"),
            item.get("quantity", 1),
            item.get("dispatched", 0),
            json.dumps(item.get("movements", [])),
            state,
            json.dumps(item.get("extra_info", {})),
        )
        flag, error, id_item = execute_sql(sql, val, 4)
        if flag:
            results.append({"data": id_item, "action": "new"})
        else:
            errors.append(item)

    return errors, results


def update_items_sm(items: list, sm_id: int):
    errors = []
    results = []
    action = "update"
    ids_list = []
    for item in items:
        is_erased = item.get("is_erased", 0)
        if is_erased == 0:
            id_inventory = item.get("id_inventory", 0)
            if id_inventory in ids_list:
                continue
            if item.get("id", 0) != 0 :
                ids_list.append(id_inventory)
                sql = (
                    "UPDATE sql_telintec.sm_items "
                    "SET id_inventory = %s, name = %s, udm = %s, comment = %s, "
                    "partida = %s, quantity = %s, dispatched = %s, movements = %s, state = %s, "
                    "extra_info = %s, "
                    "deliveries = %s, state_delivery = %s, state_quantity = %s "
                    "WHERE id_item = %s"
                )
                val = (
                    id_inventory if id_inventory != 0 else None,
                    item.get("name"),
                    item.get("udm", "PZA"),
                    item.get("comment", ""),
                    item.get("partida"),
                    item.get("quantity"),
                    item.get("dispatched", 0),
                    json.dumps(item.get("movements", [])),
                    item.get("state", 1),
                    json.dumps(item.get("extra_info", {})),
                    json.dumps(item.get("deliveries", [])),
                    item.get("state_delivery", ""),
                    item.get("state_quantity", 0),
                    item.get("id"),
                )
                flag, error, result = execute_sql(sql, val, 4)
            else:
                action = "new"
                sql = (
                    "INSERT INTO sql_telintec.sm_items "
                    "(id_sm, id_inventory, name, udm, comment, partida, quantity, "
                    "dispatched, movements, state, extra_info, deliveries, state_delivery, state_quantity) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                )
                id_new = item.get("id", -1)
                id_new = None if id_new == -1 else id_new
                id_inventory = id_new if (id_inventory <= 0) else id_inventory
                val = (
                    sm_id,
                    id_inventory,
                    item.get("name"),
                    item.get("udm", "PZA"),
                    item.get("comment", ""),
                    item.get("partida"),
                    item.get("quantity"),
                    item.get("dispatched", 0),
                    json.dumps(item.get("movements", [])),
                    item.get("state", 0),
                    json.dumps(item.get("extra_info", {})),
                    json.dumps(item.get("deliveries", [])),
                    item.get("state_delivery", ""),
                    item.get("state_quantity", 0),
                )
                flag, error, result = execute_sql(sql, val, 4)
        else:
            action = "delete"
            sql = "DELETE FROM sql_telintec.sm_items WHERE id_item = %s"
            val = (item.get("id"),)
            flag, error, result = execute_sql(sql, val, 4)
        if flag:
            results.append({"data": result, "action": action, "id": item.get("id")})
        else:
            errors.append(item)

    return errors, results


def insert_sm_db(data, init_extra_info: dict|None=None):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    event = [
        {
            "event": "Creación",
            "date": timestamp,
            "user": data["info"]["emp_id"],
        }
    ]
    comment = data["info"].get("comment", [""])
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
        "date_closing": data["info"].get("date_closing", ""),
    }
    if init_extra_info is not None:
        for k, v in init_extra_info.items():
            extra_info[k] = v
    sql = (
        "INSERT INTO sql_telintec.materials_request "
        "(folio, contract, facility, location, "
        "client_id, emp_id, pedido_cotizacion, date, limit_date, status, history, comment, extra_info)"
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
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
        0,
        json.dumps(event),
        json.dumps(comment),
        json.dumps(extra_info),
    )
    flag, error, result = execute_sql(sql, val, 4)
    if not isinstance(result, int):
        return False, "Error at inserting sm", None
    return flag, error, result


def insert_urgent_sm_db(data: dict, extra_info: dict):
    init_extra_info = {
        "urgent": 1,
        "facility": data["info"].get("facility", ""),
        "location": data["info"].get("location", ""),
        "project": data["info"].get("project", ""),
        "contract_contact": data["info"].get("contract_contact", ""),
        "activity_description": data["info"].get("activity_description", ""),
        
    }
    comment = data["info"].get("comment", [""])
    if extra_info is not None:
        for k, v in extra_info.items():
            init_extra_info[k] = v
    event = [
        {
            "event": "Creación Urgente",
            "date": data["info"].get("date", ""),
            "user": data["info"]["emp_id"],
        }
    ]
    sql = (
        "INSERT INTO sql_telintec.materials_request "
        "(folio, contract, client_id, emp_id, date, limit_date, status, history, extra_info, pedido_cotizacion, comment)"
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data["info"]["folio"],
        data["info"]["contract"],
        data["info"]["client_id"],
        data["info"]["emp_id"],
        data["info"]["date"],
        data["info"]["critical_date"],
        0,
        json.dumps(event),
        json.dumps(init_extra_info),
        data["info"]["order_quotation"],
        json.dumps(comment),
    )
    flag, error, result = execute_sql(sql, val, 4)
    if not isinstance(result, int):
        return False, "Error at inserting sm", None
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
    if not isinstance(result, list):
        return False, "Error at retriving sm from db", None
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
    print(f"sm retived: {data['id']}")
    flag, error, result = execute_sql(sql, vals, 1)
    if not flag:
        return False, f"Error at retriving sm from db: {error}", None
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return False, "Error at retriving sm from db not list", None
    if len(result) == 0:
        return False, "Material request not found", None
    extra_info = json.loads(result[1])
    extra_info["destination"] = data["info"]["destination"]
    extra_info["contract_contact"] = data["info"]["contract_contact"]
    extra_info["activity_description"] = data["info"]["activity_description"]
    extra_info["project"] = data["info"]["project"]
    history = data["info"]["history"]
    comment = data["info"]["comment"]
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
        "client_id = %s, emp_id = %s, date = %s, limit_date = %s, status = 0, pedido_cotizacion = %s, "
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
        data["info"]["order_quotation"],
        json.dumps(history),
        json.dumps(comment),
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
    if not isinstance(result, list):
        return False, "Error at retriving sm from db", None
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


def update_history_sm(sm_id, history: list, items: list, is_complete=False):
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


def update_history_status_sm(sm_id, history: list, status, extra_info):
    sql = (
        "UPDATE sql_telintec.materials_request "
        "SET history = %s, status =  %s "
        "WHERE sm_id = %s "
    )
    val = (json.dumps(history), status, sm_id)
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
    if not isinstance(result, tuple):
        return False, "Error at retriving sm from db", []
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
    sql = "SELECT folio FROM sql_telintec.materials_request WHERE folio LIKE %s ORDER BY folio DESC"
    val = (f"{pattern}%",)
    flag, error, result = execute_sql(sql, val, 2)
    if not isinstance(result, list):
        return False, "Error at retriving sm from db", []
    return flag, error, result


def update_history_extra_info_sm_by_id(
    sm_id: int, extra_info: dict, history: dict, comments: list
):
    sql = (
        "UPDATE sql_telintec.materials_request "
        "SET extra_info = %s, history = %s, comment = %s "
        "WHERE sm_id = %s "
    )
    val = (json.dumps(extra_info), json.dumps(history), json.dumps(comments), sm_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_pending_sm_db():
    sql = (
        "SELECT "
        "mr.sm_id, "
        "mr.folio, "
        "mr.contract, "
        "mr.facility, "
        "mr.location, "
        "mr.client_id, "
        "mr.emp_id, "
        "mr.pedido_cotizacion, "
        "mr.date, "
        "mr.limit_date, "
        "JSON_ARRAYAGG(JSON_OBJECT("
        " 'id', smi.id_item, "
        " 'id_inventory', smi.id_inventory, "
        " 'name', smi.name, "
        " 'udm', smi.udm, "
        " 'comment', smi.comment, "
        " 'partida', smi.partida, "
        " 'quantity', smi.quantity, "
        " 'dispatched', smi.dispatched, "
        " 'movements', smi.movements, "
        " 'state', smi.state, "
        " 'extra_info', smi.extra_info, "
        " 'reserved', IFNULL(rsv.reserved, 0), "
        " 'reservation_id', rsv.reservation_id, "
        " 'deliveries', smi.deliveries, "
        " 'state_quantity', smi.state_quantity, "
        " 'state_delivery', smi.state_delivery, "
        " 'reserved_all', rAll.reserved_qty, "
        " 'available_stock', IFNULL(inv.stock, 0) - IFNULL(rAll.reserved_qty, 0), "
        " 'stock', IFNULL(inv.stock, 0) "
        ") ) AS items, "
        "mr.status, "
        "mr.history, "
        "mr.comment, "
        "mr.extra_info "
        "FROM sql_telintec.materials_request AS mr "
        "LEFT JOIN sql_telintec.sm_items AS smi ON mr.sm_id = smi.id_sm "
        "LEFT JOIN sql_telintec.products_amc AS inv ON inv.id_product = smi.id_inventory "
        "LEFT JOIN ( "
        "   SELECT id_product, sm_id, quantity AS reserved, reservation_id "
        "   FROM sql_telintec.product_reservations "
        "   WHERE status = 0 "
        ") rsv ON (rsv.sm_id = smi.id_sm) AND (rsv.id_product = smi.id_inventory) "
        "LEFT JOIN ( "
        "   SELECT id_product, SUM(quantity) AS reserved_qty "
        "   FROM sql_telintec.product_reservations "
        "   WHERE status = 0 "
        "   GROUP BY id_product "
        ") rAll ON smi.id_inventory = rAll.id_product "
        "WHERE mr.status = 0 "
        "GROUP BY mr.sm_id"
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result



def update_history_items_sm(sm_id: int, items: list, history: list):
    sql = (
        "UPDATE sql_telintec.materials_request " "SET history = %s " "WHERE sm_id = %s "
    )
    val = (json.dumps(items), json.dumps(history), sm_id)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def get_sm_folios_db():
    sql = (
        "SELECT "
        "sm_id, folio "
        "FROM sql_telintec.materials_request "
        "WHERE status < 2 "
    )
    flag, error, result = execute_sql(sql, None, 5)
    if not isinstance(result, list):
        return False, "Error at retriving sm from db", []
    return flag, error, result


def delete_item_from_sm_id(sm_id: int):
    sql = """DELETE FROM sql_telintec.sm_items WHERE id_sm = %s """
    val = (sm_id,)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def get_sm_items_state(state: str):
    sql = """
          SELECT id_item, id_sm, mr.folio , name
          FROM sql_telintec.sm_items
          LEFT JOIN sql_telintec.materials_request mr on mr.sm_id = sm_items.id_sm
          WHERE state = %s 
          """
    val = (state,)
    flag, error, result = execute_sql(sql, val, 2)
    if not isinstance(result, list):
        return False, "Error at retriving sm from db", []
    return flag, error, result


def update_inventory_state_sm_item_db(state, id_inventory, id_item):
    sql = """
          UPDATE sql_telintec.sm_items
          SET state = %s,
              id_inventory = %s
          WHERE id_sm = %s
          """
    val = (state, id_inventory, id_item)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result
