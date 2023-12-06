# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 27/jul./2023  at 16:41 $'

import mysql.connector
from dotenv import dotenv_values

secrets = dotenv_values(".env")


def execute_sql(sql: str, values: tuple = None, type_sql=1):
    """
    Execute the sql with the values provides (or not) and returns a value
    depending on the type of query. In case of exception returns None
    :param type_sql: type of query to execute
    :param sql: sql query
    :param values: values for sql query
    :return:
    """
    mydb = mysql.connector.connect(
        host=secrets["HOST_DB"],
        user=secrets["USER_SQL"],
        password=secrets["PASS_SQL"],
        database="sql_telintec"
    )
    my_cursor = mydb.cursor()
    out = []
    flag = True
    exception = None
    try:
        match type_sql:
            case 2:
                my_cursor.execute(sql, values)
                out = my_cursor.fetchall()
            case 1:
                my_cursor.execute(sql, values)
                out = my_cursor.fetchone()
            case 3:
                my_cursor.execute(sql, values)
                mydb.commit()
                out = my_cursor.rowcount
            case 4:
                my_cursor.execute(sql, values)
                mydb.commit()
                out = my_cursor.lastrowid
            case 5:
                my_cursor.execute(sql)
                out = my_cursor.fetchall()
            case _:
                out = []
    except Exception as e:
        print(e)
        out = []
        flag = False
        exception = e
    finally:
        out = out if out is not None else []
        my_cursor.close()
        mydb.close()
        return flag, exception, out


def get_employees(limit=(0, 100)) -> list[list]:
    sql = "SELECT * FROM sql_telintec.employees LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_departments(limit=(0, 100)) -> list[list]:
    sql = "SELECT * FROM sql_telintec.departments LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_heads(limit=(0, 100)) -> list[list]:
    sql = "SELECT * FROM sql_telintec.heads LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_customers(limit=(0, 100)) -> list[list]:
    sql = "SELECT * FROM sql_telintec.customers LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_supplier(limit=(0, 100)) -> list[list]:
    sql = "SELECT * FROM sql_telintec.suppliers LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_p_and_s(limit=(0, 100)):
    sql = "SELECT * FROM sql_telintec.products_services LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_chats_w_limit(limit=(0, 100)):
    sql = "SELECT chat_id, platform, context FROM chats ORDER BY chat_id DESC LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = [] if my_result is None else my_result
    return out


def get_chats(limit=(0, 100)):
    sql = "SELECT * FROM chats ORDER BY chat_id DESC LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = [] if my_result is None else my_result
    return out


def get_orders(limit=(0, 100)):
    sql = "SELECT * FROM sql_telintec.orders LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_v_orders(limit=(0, 100)):
    sql = "SELECT * FROM sql_telintec.virtual_orders LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_tickets(limit=(0, 100)):
    sql = "SELECT * FROM sql_telintec.tickets LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_purchases(limit=(0, 100)):
    sql = "SELECT * FROM sql_telintec.purchases LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_users(limit=(0, 100)):
    sql = ("SELECT U_id, usernames, permissions,"
           " exp, timestamp_token FROM sql_telintec.users_system LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def insert_employee(name: str, lastname: str, dni: str, phone: str, email: str,
                    department: str, modality: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.employees (name, l_name, dni, phone_number, email, department_id, modality) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    val = (name, lastname, dni, phone, email, department, modality)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


def insert_customer(name: str, lastname: str, phone: str, city: str, email: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.customers (name, l_name, phone_number, city, email) "
           "VALUES (%s, %s, %s, %s, %s)")
    val = (name, lastname, phone, city, email)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted.")
    return flag, e, out


def insert_department(name: str, location: str) -> tuple[bool, Exception | None, int | None]:
    sql = "INSERT INTO sql_telintec.departments (name, location) VALUES (%s, %s)"
    val = (name, location)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, None, out


def insert_head(position_name: str, department: str,
                employee: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.heads (name, department, employee) "
           "VALUES (%s, %s, %s)")
    val = (position_name, department, employee)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


def insert_supplier(name: str, location: str) -> tuple[bool, Exception | None, int | None]:
    sql = "INSERT INTO sql_telintec.suppliers (name, location) VALUES (%s, %s)"
    val = (name, location)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, None, out


def insert_product_and_service(product_id: str, name: str, model: str, brand: str,
                               description: str, price_retail: str, quantity: str,
                               price_provider: str,
                               support: int, is_service: int) -> tuple[bool, Exception | None, str | None]:
    sql = ("INSERT INTO sql_telintec.products_services (product_id, name, model, marca, description, "
           "price_retail, available_quantity, price_provider, support_offered, is_service) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    val = (product_id, name, model, brand, description, price_retail, quantity,
           price_provider, str(support), str(is_service))
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in products_services.")
    return flag, None, product_id


def check_last_id(old: str = None) -> list:
    if old is None:
        sql = "SELECT MAX(chat_id) FROM chats"
        flag, e, out = execute_sql(sql, type_sql=5)
    else:
        sql = "SELECT chat_id FROM chats WHERE chat_id > %s"
        val = (old,)
        flag, e, out = execute_sql(sql, val, 2)
    return out
