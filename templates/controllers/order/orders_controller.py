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
    chat_id: int,
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
    print(out, "record inserted in vorders.")
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
    sql = "DELETE FROM sql_telintec.virtual_orders " "WHERE vo_id = %s"
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
        ")) AS items, "
        "po.time_delivery "
        "FROM sql_telintec_mod_admin.purchase_orders AS po "
        "LEFT JOIN sql_telintec_mod_admin.purchase_order_items AS poi ON po.id_order = poi.order_id "
        "WHERE (po.status = %s or %s IS NULL ) AND (po.created_by = %s OR %s IS NULL) GROUP BY po.id_order"
    )
    val = (status, status, created_by, created_by)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def get_pos_application_with_items(created_by: int | None):
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
        " 'duration_services', poi.duration_services "
        ")) AS items "
        "FROM sql_telintec_mod_admin.pos_applications AS po "
        "LEFT JOIN sql_telintec_mod_admin.purchase_order_items AS poi ON po.id_order = poi.order_id "
        "WHERE po.created_by = %s OR %s IS NULL GROUP BY po.id_order"
    )
    val = (created_by, created_by)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def insert_purchase_order(
    timestamp: str,
    status: int,
    created_by: int,
    approved_by: int | None,
    supplier_id: int,
    total_amount: float | None,
    folio: str,
    reference: str,
    history: list,
    extra_info: dict,
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.purchase_orders "
        "(timestamp, status, created_by, approved_by, "
        "supplier_id, total_amount, folio, reference, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        timestamp,
        status,
        created_by,
        approved_by,
        supplier_id,
        total_amount,
        folio,
        reference,
        json.dumps(history),
        json.dumps(extra_info),
    )
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_purchase_order(
    id_order: int,
    timestamp: str,
    status: int,
    created_by: int,
    approved_by: int,
    supplier_id: int,
    total_amount: float,
    folio: str,
    reference: str,
    history: list,
    extra_info: dict,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_orders "
        "SET timestamp = %s, status = %s, created_by = %s, "
        "approved_by = %s, supplier_id = %s, total_amount = %s, "
        "folio = %s, reference = %s, history = %s, extra_info = %s "
        "WHERE id_order = %s"
    )
    val = (
        timestamp,
        status,
        created_by,
        approved_by,
        supplier_id,
        total_amount,
        folio,
        reference,
        json.dumps(history),
        json.dumps(extra_info),
        id_order,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_purchase_order_status(
    id_order: int, history: list, status: int, id_approved: int
):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_orders "
        "SET status = %s, history = %s, approved_by= %s "
        "WHERE id_order = %s"
    )
    val = (status, json.dumps(history), id_approved, id_order)
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


def delete_purchase_order(id_order: int):
    sql = "DELETE FROM sql_telintec_mod_admin.purchase_orders " "WHERE id_order = %s"
    val = (id_order,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_items_purchase_orders(id_order: int):
    sql = (
        "SELECT id_item, order_id, quantity, unit_price, description, extra_info "
        "FROM sql_telintec_mod_admin.purchase_order_items "
        "WHERE order_id = %s"
    )
    val = (id_order,)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def insert_purchase_order_item(
    order_id: int,
    quantity: int,
    unit_price: float,
    description: str,
    extra_info: dict,
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.purchase_order_items "
        "(order_id, quantity, unit_price, description, extra_info) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    val = (
        order_id,
        quantity,
        unit_price,
        description,
        json.dumps(extra_info),
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_purchase_order_items(items: list):
    if len(items) == 0:
        return False, "No items", None
    flags = []
    errors = []
    outs = []
    for item in items:
        flag, e, out = insert_purchase_order_item(
            item["order_id"],
            item["quantity"],
            item["unit_price"],
            item["description"],
            item["extra_info"],
        )
        flags.append(flag)
        errors.append(e)
        outs.append(out)
    return all(flags), errors, outs


def update_purchase_order_item(
    id_item: int,
    order_id: int,
    quantity: int,
    unit_price: float,
    description: str,
    extra_info: dict,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.purchase_order_items "
        "SET quantity = %s, unit_price = %s, description = %s, extra_info = %s "
        "WHERE id_item = %s AND order_id = %s"
    )
    val = (
        quantity,
        unit_price,
        description,
        json.dumps(extra_info),
        id_item,
        order_id,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_purchase_order_items(items: list):
    if len(items) == 0:
        return False, "No items", None
    flags = []
    errors = []
    outs = []
    for item in items:
        flag, e, out = update_purchase_order_item(
            item["id_item"],
            item["order_id"],
            item["quantity"],
            item["unit_price"],
            item["description"],
            item["extra_info"],
        )
        flags.append(flag)
        errors.append(e)
        outs.append(out)
    return all(flags), errors, outs


def delete_purchase_order_item(id_item: int, order_id: int):
    sql = (
        "DELETE FROM sql_telintec_mod_admin.purchase_order_items "
        "WHERE id_item = %s AND order_id = %s"
    )
    val = (id_item, order_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out
