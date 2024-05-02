# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:33 $'

from templates.database.connection import execute_sql


def get_orders(limit=(0, 100)):
    sql = ("SELECT order_id, product_id, quantity, date_order, customer_id, employee_id "
           "FROM orders "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_v_orders(limit=(0, 100)):
    sql = ("SELECT vo_id, products, date_order, customer_id, employee_id, chat_id "
           "FROM virtual_orders "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def update_order_db(id_order: int, id_product: int, quantity: int, date_order, id_customer: int, id_employee: int):
    sql = ("UPDATE sql_telintec.orders "
           "SET "
           "product_id = %s, "
           "quantity = %s, "
           "date_order = %s, "
           "customer_id = %s, "
           "employee_id = %s "
           "WHERE order_id = %s")
    val = (id_product, quantity, date_order, id_customer, id_employee, id_order)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_order_db(id_order: int):
    sql = ("DELETE FROM sql_telintec.orders "
           "WHERE order_id = %s")
    val = (id_order,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_vorder_db(id_vorder: int, products: str, date_order,
                     id_customer: int, id_employee: int, chat_id: int):
    sql = ("INSERT "
           "INTO sql_telintec.virtual_orders "
           "(vo_id, "
           "products, "
           "date_order, "
           "customer_id, "
           "employee_id, "
           "chat_id) "
           "VALUES (%s, %s, %s, %s, %s, %s)")
    val = (id_vorder, products, date_order, id_customer, id_employee)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in vorders.")
    return flag, None, out


def update_vorder_db(id_vorder: int, products: str, date_order,
                     id_customer: int, id_employee: int, chat_id: int):
    sql = ("UPDATE sql_telintec.virtual_orders "
           "SET "
           "products = %s, "
           "date_order = %s, "
           "customer_id = %s, "
           "employee_id = %s, "
           "chat_id = %s "
           "WHERE vo_id = %s")
    val = (products, date_order, id_customer, id_employee, chat_id, id_vorder)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_vorder_db(id_vorder: int):
    sql = ("DELETE FROM sql_telintec.virtual_orders "
           "WHERE vo_id = %s")
    val = (id_vorder,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_order(id_order: int, id_product: int, quantity: int, date_order, id_customer: int, id_employee: int):
    sql = ("INSERT INTO sql_telintec.orders "
           "(order_id, "
           "product_id, "
           "quantity, "
           "date_order, "
           "customer_id, "
           "employee_id) "
           "VALUES (%s, %s, %s, %s, %s, %s)")
    val = (id_order, id_product, quantity, date_order, id_customer, id_employee)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in orders.")
    return flag, None, out


def get_orders_amc(id_o: int, id_c: int, status: str, name_c: str, date: str):
    columns = ("id_order", "id_customer", "status", "sm_code", "date", "id_customer")
    if id_c is None:
        # get id customer FROM name_c
        sql = ("SELECT id_customer "
               "FROM customers_amc "
               "WHERE match(name) against (%s IN NATURAL LANGUAGE MODE ) ")
        val = (name_c,)
        flag, error, result = execute_sql(sql, val, 1)
        if len(result) > 0:
            id_c = result[0]
        else:
            id_c = "%"
    sql = ("SELECT id_order, id_customer, status, sm_code, order_date, id_customer "
           "FROM orders_amc "
           "WHERE (id_order = %s OR "
           "id_customer = %s) AND status LIKE %s ")
    if date is not None:
        sql = sql + " AND order_date = %s"
    sql = sql + " LIMIT 10"
    val = (id_o, id_c, status, date)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns
