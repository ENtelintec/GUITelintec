# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 19:33 $"

from templates.database.connection import execute_sql

import json


def get_v_orders(limit=(0, 100)):
    sql = (
        "SELECT vo_id, products, date_order, customer_id, employee_id, chat_id "
        "FROM sql_telintec.virtual_orders "
        "LIMIT %s, %s"
    )
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def insert_vorder_db(
    id_vorder: int,
    products: str,
    date_order,
    id_customer: int,
    id_employee: int,
):
    sql = (
        "INSERT "
        "INTO sql_telintec.virtual_orders "
        "(vo_id, "
        "products, "
        "date_order, "
        "customer_id, "
        "employee_id, "
        "chat_id) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    val = (id_vorder, products, date_order, id_customer, id_employee)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, None, out


def update_vorder_db(
    id_vorder: int,
    products: str,
    date_order,
    id_customer: int,
    id_employee: int,
    chat_id: int,
):
    sql = (
        "UPDATE sql_telintec.virtual_orders "
        "SET "
        "products = %s, "
        "date_order = %s, "
        "customer_id = %s, "
        "employee_id = %s, "
        "chat_id = %s "
        "WHERE vo_id = %s"
    )
    val = (products, date_order, id_customer, id_employee, chat_id, id_vorder)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_vorder_db(id_vorder: int):
    sql = "DELETE FROM sql_telintec.virtual_orders WHERE vo_id = %s"
    val = (id_vorder,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_purchase_orders_with_items(status: int | None, created_by: int | None):
    sql = (
        "SELECT "
        "po.id_order, "
        "po.timestamp, "
        "po.status, "
        "po.created_by, "
        "po.supplier_id, "
        "po.folio, "
        "po.history, "
        "po.extra_info, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        " 'id', poi.id_item, "
        " 'purchase_id', poi.purchase_id, "
        " 'description', poi.description,"
        " 'quantity', poi.quantity,"
        " 'unit_price', poi.unit_price, "
        " 'extra_info', poi.extra_info, "
        " 'duration_services', poi.duration_services "
        ",'tool', poi.tool "
        ",'currency', poi.currency "
        ")) AS items, "
        "po.time_delivery "
        "FROM sql_telintec_mod_admin.purchase_orders AS po "
        "LEFT JOIN sql_telintec_mod_admin.purchase_order_items AS poi ON po.id_order = poi.purchase_id "
        "WHERE (po.status = %s or %s IS NULL ) AND (po.status != 4) AND (po.created_by = %s OR %s IS NULL) GROUP BY po.id_order"
    )
    val = (status, status, created_by, created_by)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def get_purchase_order_with_items_by_id(order_id: int):
    sql = (
        "SELECT "
        "po.timestamp, "
        "po.status, "
        "emps.name, "
        "emps.l_name, "
        "sa.name, "
        "po.folio, "
        "po.history, "
        "po.extra_info, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        " 'id', poi.id_item, "
        " 'purchase_id', poi.purchase_id, "
        " 'description', poi.description,"
        " 'quantity', poi.quantity,"
        " 'unit_price', poi.unit_price, "
        " 'extra_info', poi.extra_info, "
        " 'duration_services', poi.duration_services, "
        " 'tool', poi.tool "
        ",'currency', poi.currency "
        ")) AS items, "
        "po.time_delivery "
        "FROM sql_telintec_mod_admin.purchase_orders AS po "
        "LEFT JOIN sql_telintec_mod_admin.purchase_order_items AS poi ON po.id_order = poi.purchase_id "
        "LEFT JOIN sql_telintec.employees emps on emps.employee_id = po.created_by "
        "LEFT JOIN sql_telintec.suppliers_amc sa on po.supplier_id = sa.id_supplier "
        "WHERE po.id_order = %s GROUP BY po.id_order"
    )
    val = (order_id,)
    flag, e, my_result = execute_sql(sql, val, 1)
    return flag, e, my_result


def get_pos_application_with_items(status: int | None, created_by: int | None):
    sql = (
        "SELECT "
        "po.id_order, "
        "po.timestamp, "
        "po.status, "
        "po.created_by, "
        "po.reference, "
        "po.history, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        " 'id', poi.id_item, "
        " 'purchase_id', poi.purchase_id, "
        " 'description', poi.description,"
        " 'quantity', poi.quantity,"
        " 'unit_price', poi.unit_price, "
        " 'extra_info', poi.extra_info, "
        " 'duration_services', poi.duration_services, "
        " 'tool', poi.tool "
        ",'currency', poi.currency "
        ")) AS items, "
        "po.extra_info "
        "FROM sql_telintec_mod_admin.pos_applications AS po "
        "LEFT JOIN sql_telintec_mod_admin.purchase_order_items AS poi ON po.id_order = poi.order_id "
        "WHERE (po.status = %s or %s IS NULL ) AND (po.status != 4) AND (po.created_by = %s OR %s IS NULL) GROUP BY po.id_order"
    )
    val = (status, status, created_by, created_by)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def get_pos_application_with_items_to_approve():
    sql = (
        "SELECT "
        "po.id_order, "
        "po.timestamp, "
        "po.status, "
        "po.created_by, "
        "po.reference, "
        "po.history, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        " 'id', poi.id_item, "
        " 'purchase_id', poi.purchase_id, "
        " 'description', poi.description,"
        " 'quantity', poi.quantity,"
        " 'unit_price', poi.unit_price, "
        " 'extra_info', poi.extra_info, "
        " 'duration_services', poi.duration_services, "
        " 'tool', poi.tool "
        " ,'currency', poi.currency "
        ")) AS items, "
        "po.extra_info "
        "FROM sql_telintec_mod_admin.pos_applications AS po "
        "LEFT JOIN sql_telintec_mod_admin.purchase_order_items AS poi ON po.id_order = poi.order_id "
        "WHERE po.approved = 0 group by po.id_order "
    )
    flag, e, my_result = execute_sql(sql, None, 5)
    return flag, e, my_result


def insert_purchase_order(
    timestamp: str,
    status: int,
    created_by: int,
    supplier_id: int,
    folio: str,
    history: list,
    time_delivery: str,
    extra_info: dict,
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.purchase_orders "
        "(timestamp, status, created_by, "
        "supplier_id, folio, history, time_delivery, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        timestamp,
        status,
        created_by,
        supplier_id,
        folio,
        json.dumps(history),
        time_delivery,
        json.dumps(extra_info),
    )
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_purchase_order(
    id_order: int,
    timestamp: str,
    status: int,
    created_by: int,
    supplier_id: int,
    folio: str,
    history: list,
    extra_info: dict,
    time_delivery: str,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_orders "
        "SET timestamp = %s, status = %s, created_by = %s, "
        "supplier_id = %s, folio = %s, history = %s, extra_info = %s , time_delivery = %s "
        "WHERE id_order = %s"
    )
    val = (
        timestamp,
        status,
        created_by,
        supplier_id,
        folio,
        json.dumps(history),
        json.dumps(extra_info),
        time_delivery,
        id_order,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_purchase_order_status(id_order: int, history: list, status: int):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_orders "
        "SET status = %s, history = %s "
        "WHERE id_order = %s"
    )
    val = (status, json.dumps(history), id_order)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def cancel_purchase_order(history: list, id_order: int):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_orders "
        "SET status = 4, history = %s "
        "WHERE id_order = %s"
    )
    val = (json.dumps(history), id_order)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_po_application(
    timestamp: str,
    status: int,
    created_by: int,
    reference: str,
    history: list,
    approved=1,
    extra_info: dict|None = None,
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.pos_applications "
        "(timestamp, status, created_by, "
        "reference, history, approved, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    if extra_info is None:
        extra_info = {"sm_id": 0}
    val = (
        timestamp,
        status,
        created_by,
        reference,
        json.dumps(history),
        approved,
        json.dumps(extra_info),
    )
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_po_application(
    id_order: int,
    timestamp: str,
    status: int,
    created_by: int,
    reference: str,
    history: list,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.pos_applications "
        "SET timestamp = %s, status = %s, created_by = %s, "
        "reference = %s, history = %s "
        "WHERE id_order = %s "
    )
    val = (
        timestamp,
        status,
        created_by,
        reference,
        json.dumps(history),
        id_order,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_po_application_status(
    id_order: int, history: list, status: int, approved: int
):
    sql = (
        "UPDATE sql_telintec_mod_admin.pos_applications "
        "SET status = %s, history = %s , approved = %s "
        "WHERE id_order = %s"
    )
    val = (status, json.dumps(history), approved, id_order)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def cancel_po_application(history: list, id_order: int, status):
    sql = (
        "UPDATE sql_telintec_mod_admin.pos_applications "
        "SET status = %s, history = %s "
        "WHERE id_order = %s"
    )
    val = (status, json.dumps(history), id_order)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_purchase_order_item(
    order_id: int,
    quantity: int,
    unit_price: float,
    description: str,
    duration_services: str,
    extra_info: dict,
    tool=0,
    currency="MXN",
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.purchase_order_items "
        "(purchase_id, quantity, unit_price, description, duration_services, extra_info, tool, currency) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        order_id,
        quantity,
        unit_price,
        description,
        duration_services,
        json.dumps(extra_info),
        tool,
        currency,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_po_application_item(
    id_item: int,
    quantity: int,
    unit_price: float,
    duration_services: int,
    description: str,
    extra_info: dict,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_order_items "
        "SET quantity = %s, unit_price = %s, description = %s, duration_services = %s, extra_info = %s "
        "WHERE id_item = %s"
    )
    val = (
        quantity,
        unit_price,
        description,
        duration_services,
        json.dumps(extra_info),
        id_item,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_po_item(
    id_item: int,
    purchase_id: int,
    quantity: int,
    unit_price: float,
    description: str,
    duration_services: int,
    extra_info: dict,
    currency="MXN",
):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_order_items "
        "SET purchase_id = %s, quantity = %s, unit_price = %s, description = %s, "
        " duration_services = %s, extra_info = %s, currency = %s "
        " WHERE id_item = %s"
    )
    val = (
        purchase_id,
        quantity,
        unit_price,
        description,
        duration_services,
        json.dumps(extra_info),
        currency,
        id_item,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_folios_po_from_pattern(patterns: list):
    regexp_clauses = " OR ".join(["folio LIKE %s"] * len(patterns))
    like_patterns = [f"%{p}%" for p in patterns]
    sql = (
        "SELECT id_order, folio "
        "FROM sql_telintec_mod_admin.purchase_orders "
        f"WHERE {regexp_clauses}"
    )
    val = like_patterns
    flag, e, out = execute_sql(sql, val, 2)
    return flag, e, out
