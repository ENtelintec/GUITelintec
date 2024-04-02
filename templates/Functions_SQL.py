# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 27/jul./2023  at 16:41 $'

import json
from datetime import datetime

import mysql.connector

from static.extensions import secrets


def execute_sql(sql: str, values: tuple = None, type_sql=1):
    """
    Execute the sql with the values provides (or not) and returns a value
    depending on the type of query. In case of exception returns None
    :param type_sql: type of query to execute
    :param sql: sql query
    :param values: values for sql query
    :return:
    """
    try:
        mydb = mysql.connector.connect(
            host=secrets["HOST_DB_AWS"],
            user=secrets["USER_SQL_AWS"],
            password=secrets["PASS_SQL_AWS"],
            database="sql_telintec"
        )
        my_cursor = mydb.cursor(buffered=True)
    except Exception as e:
        print(e)
        return False, e, []
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


def execute_sql_multiple(sql: str, values_list: list = None, type_sql=1):
    """
    Execute the sql with the values provides (or not) and returns a value
    depending on the type of query. In case of exception returns None
    :param values_list: values for sql query
    :param type_sql: type of query to execute
    :param sql: sql query
    :return:
    """
    try:
        mydb = mysql.connector.connect(
            host=secrets["HOST_DB_AWS"],
            user=secrets["USER_SQL_AWS"],
            password=secrets["PASS_SQL_AWS"],
            database="sql_telintec"
        )
        my_cursor = mydb.cursor(buffered=True)
    except Exception as e:
        print(e)
        return False, e, []
    out = []
    flag = True
    error = None
    # my_cursor = mydb.cursor(buffered=True)
    for i in range(len(values_list[0])):
        values = []
        for j in range(len(values_list)):
            values.append(values_list[j][i])
        values = tuple(values)
        try:
            match type_sql:
                case 2:
                    my_cursor.execute(sql, values)
                    out.append(my_cursor.fetchall())
                case 1:
                    my_cursor.execute(sql, values)
                    out.append(my_cursor.fetchone())
                case 3:
                    my_cursor.execute(sql, values)
                    mydb.commit()
                    out.append(my_cursor.rowcount)
                case 4:
                    my_cursor.execute(sql, values)
                    mydb.commit()
                    out.append(my_cursor.lastrowid)
                case 5:
                    my_cursor.execute(sql)
                    out.append(my_cursor.fetchall())
                case _:
                    out.append([])
        except Exception as error:
            print(error)
            out.append([])
            flag = False
    out = out if out is not None else []
    my_cursor.close()
    mydb.close()
    return flag, error, out


def get_employees(limit=(0, 100)) -> list[list]:
    sql = "SELECT * FROM sql_telintec.employees LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def new_employee(name, lastname, curp, phone, email, department, contract, entry_date, rfc, nss, emergency, modality,
                 puesto, estatus, departure):
    sql = ("INSERT INTO employees (name, l_name, curp, phone_number, email, department_id,"
           " contrato, date_admission, rfc, nss, emergency_contact, modality, puesto, status, departure) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    values = (name.lower(), lastname.lower(), curp, phone, email, department,
              contract, entry_date, rfc, nss, emergency, modality, puesto, estatus,
              json.dumps(departure))
    flag, e, out = execute_sql(sql, values, 4)
    return flag, e, out


def update_employee(employee_id, name, lastname, curp, phone, email, department, contract, entry_date, rfc, nss,
                    emergency, modality, puesto, estatus, departure):
    sql = ("UPDATE employees SET name = %s, l_name = %s, curp = %s, phone_number = %s, email = %s, department_id = %s,"
           "contrato = %s, date_admission = %s, rfc = %s, nss = %s, emergency_contact = %s, modality = %s , "
           "puesto = %s, status = %s, departure = %s "
           "WHERE employee_id = %s")
    values = (name.lower(), lastname.lower(), curp, phone, email, department,
              contract, entry_date, rfc, nss, emergency, modality, puesto,
              estatus, json.dumps(departure), employee_id)
    flag, e, out = execute_sql(sql, values, 3)
    return flag, e, out


def get_employee_id_name(name: str) -> tuple[None, str] | tuple[int, str]:
    """
        Get the id of the employee
        :param name: name of the employee
        :return: id of the employee
        """
    sql = ("SELECT employee_id, name, l_name FROM employees WHERE "
           "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) and "
           "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )")
    # lowercase names
    name = name.lower()
    values = (name, name)
    flag, e, out = execute_sql(sql, values, 1)
    if e is not None or len(out) == 0:
        return None, str(e)
    else:
        return out[0], f"{out[1].title()} {out[2].title()}"


def delete_employee(employee_id: int):
    try:
        employee_id = int(employee_id)
    except ValueError:
        return False, None, None
    sql = "DELETE FROM employees WHERE employee_id = %s"
    values = (employee_id,)
    flag, e, out = execute_sql(sql, values, 3)
    return flag, e, out


def get_id_employee(name: str) -> None | int:
    """
    Get the id of the employee
    :param name: name of the employee
    :return: id of the employee
    """
    sql = ("SELECT employee_id FROM employees WHERE "
           "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) and "
           "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )")
    # lowercase names
    name = name.lower()
    values = (name, name)
    flag, e, out = execute_sql(sql, values, 1)
    # print(name, flag, e, out)
    if e is not None or len(out) == 0:
        return None
    else:
        return out[0]


def get_name_employee(id_employee: int) -> None | str:
    """
    Get the name of the employee
    :param id_employee: id of the employee
    :return: name of the employee
    """
    sql = "SELECT name, l_name FROM employees WHERE employee_id = %s"
    values = (id_employee,)
    flag, e, out = execute_sql(sql, values, 1)
    if e is not None or len(out) == 0:
        return None
    else:
        return f"{out[0].upper()} {out[1].upper()}"


def get_id_name_employee(department: int, is_all=False):
    """
    :param department:
    :param is_all:
    :return:
    """
    sql = ("SELECT employee_id, name, l_name, puesto, date_admission, departure FROM employees "
           "WHERE department_id = %s")
    if is_all:
        sql = "SELECT employee_id, name, l_name, puesto, date_admission, departure FROM employees"
        flag, e, out = execute_sql(sql, None, 5)
    else:
        values = (department,)
        flag, e, out = execute_sql(sql, values, 5)
    return flag, e, out


def get_employees_op_names():
    sql = ("SELECT employee_id, name, l_name, contrato FROM employees "
           "WHERE  department_id = 2")
    flag, e, out = execute_sql(sql, None, 5)
    if e is not None:
        return False, e, None
    else:
        return flag, e, out


def get_ids_employees(names: list):
    """
    Get the id of the employee
    :param names: list name of the employee
    :return: id of the employee
    """
    sql = ("SELECT employee_id FROM employees WHERE "
           "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) and "
           "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )")
    # lowercase names
    for i, name in enumerate(names):
        names[i] = name.lower()
    values = [names, names]
    flag, e, out = execute_sql_multiple(sql, values, 1)
    if e is not None:
        return None
    else:
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


def insert_customer(
        name: str, lastname: str, phone: str, city: str,
        email: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.customers (name, l_name, phone_number, city, email) "
           "VALUES (%s, %s, %s, %s, %s)")
    val = (name, lastname, phone, city, email)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_customer_DB(
        name: str, lastname: str, phone: str, city: str,
        email: str, customer_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("UPDATE sql_telintec.customers SET name = %s, l_name = %s, phone_number = %s, "
           "city = %s, email = %s WHERE customer_id = %s")
    val = (name, lastname, phone, city, email, customer_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_customer_DB(customer_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = "DELETE FROM sql_telintec.customers WHERE customer_id = %s"
    val = (customer_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_department(name: str, location: str) -> tuple[bool, Exception | None, int | None]:
    sql = "INSERT INTO sql_telintec.departments (name, location) VALUES (%s, %s)"
    val = (name, location)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, None, out


def update_department_DB(name: str, location: str, department_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("UPDATE sql_telintec.departments SET name = %s, location = %s "
           "WHERE department_id = %s")
    val = (name, location, department_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_department_DB(department_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = "DELETE FROM sql_telintec.departments WHERE department_id = %s"
    val = (department_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_head(position_name: str, department: str,
                employee: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.heads (name, department, employee) "
           "VALUES (%s, %s, %s)")
    val = (position_name, department, employee)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


def update_head_DB(position_name: str, department: str,
                   employee: str, head_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("UPDATE sql_telintec.heads SET name = %s, department = %s, employee = %s "
           "WHERE position_id = %s")
    val = (position_name, department, employee, head_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_head_DB(head_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = "DELETE FROM sql_telintec.heads WHERE position_id = %s"
    val = (head_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_supplier(name: str, location: str) -> tuple[bool, Exception | None, int | None]:
    sql = "INSERT INTO sql_telintec.suppliers (name, location) VALUES (%s, %s)"
    val = (name, location)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, None, out


def update_supplier_DB(name: str, location: str, supplier_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("UPDATE sql_telintec.suppliers SET name = %s, location = %s "
           "WHERE supplier_id = %s")
    val = (name, location, supplier_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_supplier_DB(supplier_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = "DELETE FROM sql_telintec.suppliers WHERE supplier_id = %s"
    val = (supplier_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


# --------------------------------Products and Services--------------------------------
def insert_product_and_service(product_id: int, name: str, model: str, brand: str,
                               description: str, price_retail: str, quantity: str,
                               price_provider: str,
                               support: int, is_service: int, categories: str,
                               img_url: str) -> tuple[bool, Exception | None, list | None]:
    sql = ("INSERT INTO sql_telintec.products_services (product_id, name, model, marca, description, "
           "price_retail, available_quantity, price_provider, support_offered, is_service,"
           "category, image) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    val = (product_id, name, model, brand, description, price_retail, quantity,
           price_provider, str(support), str(is_service), categories, img_url)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in products_services.")
    return flag, None, out


def update_product_and_service(product_id: int, name: str, model: str, brand: str,
                               description: str, price_retail: str, quantity: str,
                               price_provider: str,
                               support: int, is_service: int, categories: str,
                               img_url: str) -> tuple[bool, Exception | None, list | None]:
    sql = ("UPDATE sql_telintec.products_services SET name = %s, model = %s, marca = %s, "
           "description = %s, price_retail = %s, available_quantity = %s, price_provider = %s, "
           "support_offered = %s, is_service = %s, category = %s, image = %s "
           "WHERE product_id = %s")
    val = (name, model, brand, description, price_retail, quantity, price_provider,
           str(support), str(is_service), categories, img_url, product_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_product_and_service(id_ps: int):
    sql = "DELETE FROM sql_telintec.products_services WHERE product_id = %s"
    val = (id_ps,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_order(id_order: int, id_product: int, quantity: int, date_order, id_customer: int, id_employee: int):
    sql = ("INSERT INTO sql_telintec.orders (order_id, product_id, quantity, date_order, "
           "customer_id, employee_id) VALUES (%s, %s, %s, %s, %s, %s)")
    val = (id_order, id_product, quantity, date_order, id_customer, id_employee)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in orders.")
    return flag, None, out


def update_order_db(id_order: int, id_product: int, quantity: int, date_order, id_customer: int, id_employee: int):
    sql = ("UPDATE sql_telintec.orders SET product_id = %s, quantity = %s, date_order = %s, "
           "customer_id = %s, employee_id = %s WHERE order_id = %s")
    val = (id_product, quantity, date_order, id_customer, id_employee, id_order)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_order_db(id_order: int):
    sql = "DELETE FROM sql_telintec.orders WHERE order_id = %s"
    val = (id_order,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_vorder_db(id_vorder: int, products: str, date_order,
                     id_customer: int, id_employee: int, chat_id: int):
    sql = ("INSERT INTO sql_telintec.virtual_orders (vo_id, products, date_order, "
           "customer_id, employee_id, chat_id) VALUES (%s, %s, %s, %s, %s, %s)")
    val = (id_vorder, products, date_order, id_customer, id_employee)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in vorders.")
    return flag, None, out


def update_vorder_db(id_vorder: int, products: str, date_order,
                     id_customer: int, id_employee: int, chat_id: int):
    sql = ("UPDATE sql_telintec.virtual_orders SET products = %s, date_order = %s, "
           "customer_id = %s, employee_id = %s, chat_id = %s WHERE vo_id = %s")
    val = (products, date_order, id_customer, id_employee, chat_id, id_vorder)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_vorder_db(id_vorder: int):
    sql = "DELETE FROM sql_telintec.virtual_orders WHERE vo_id = %s"
    val = (id_vorder,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_ticket_db(id_t: int, content: str, is_retrieved: int, is_answered: int, timestamp: str):
    sql = ("INSERT INTO sql_telintec.tickets (ticket_id, content_ticket, is_retrieved, is_answered, "
           "timestamp_create) VALUES (%s, %s, %s, %s, %s)")
    val = (id_t, content, is_retrieved, is_answered, timestamp)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in tickets.")
    return flag, None, out


def update_ticket_db(id_t: int, content: str, is_retrieved: int, is_answered: int, timestamp: str):
    sql = ("UPDATE sql_telintec.tickets SET content_ticket = %s, is_retrieved = %s, is_answered = %s, "
           "timestamp_create = %s WHERE ticket_id = %s")
    val = (content, is_retrieved, is_answered, timestamp, id_t)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_ticket_db(id_t: int):
    sql = "DELETE FROM sql_telintec.tickets WHERE ticket_id = %s"
    val = (id_t,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def check_last_id(old: str = None) -> list:
    if old is None:
        sql = "SELECT MAX(chat_id) FROM chats"
        flag, e, out = execute_sql(sql, type_sql=5)
    else:
        sql = "SELECT chat_id FROM chats WHERE chat_id > %s"
        val = (old,)
        flag, e, out = execute_sql(sql, val, 2)
    return out


# --------------------------------Observer GUI--------------------------------
def get_isAlive(chat_id: int, sender_id):
    sql = "SELECT is_alive FROM chats WHERE chat_id = %s AND sender_id = %s"
    val = (chat_id, sender_id)
    flag, error, result = execute_sql(sql, val, 1)
    return result


def update_isAlive(chat_id: int, sender_id, is_alive):
    sql = "UPDATE chats SET is_alive = %s WHERE chat_id = %s AND sender_id = %s"
    val = (is_alive, chat_id, sender_id)
    flag, error, result = execute_sql(sql, val, 3)
    return result


def get_only_context(chat_id: str):
    sql = "SELECT context FROM chats WHERE chat_id = %s"
    val = (chat_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return result


def set_finish_chat(chat_id: str):
    sql = "UPDATE chats SET is_alive = 0, is_review = 1 WHERE chat_id = %s"
    val = (chat_id,)
    flag, error, result = execute_sql(sql, val, 3)
    return result


def get_username_data(username: str):
    sql = ("select users_system.exp, users_system.timestamp_token, employees.name,"
           " employees.l_name, employees.department_id, departments.name, employees.contrato "
           "from users_system "
           "INNER JOIN employees ON (users_system.emp_id = employee_id and usernames=%s) "
           "INNER JOIN departments on employees.department_id = departments.department_id")
    val = (username,)
    flag, error, result = execute_sql(sql, val)
    out = None
    if len(result) > 0:
        out = {
            "exp": result[0],
            "timestamp": result[1],
            "name": result[2],
            "lastname": result[3],
            "department_id": result[4],
            "department_name": result[5],
            "contract": result[6]
        }
    return out


def get_all_data_employees(status: str):
    if "all" in status.lower():
        status = "%"
    elif "inactivo" in status.lower():
        status = "INACTIVO"
    else:
        status = "ACTIVO"
    sql = ("SELECT sql_telintec.employees.*, departments.name, examen_id FROM sql_telintec.employees "
           "left join departments on sql_telintec.employees.department_id = departments.department_id "
           "left join examenes_med on "
           "(sql_telintec.employees.employee_id = examenes_med.empleado_id and examenes_med.status like %s )")
    val = (status,)
    flag, error, result = execute_sql(sql, val, type_sql=2)
    return flag, error, result


def get_all_fichajes():
    sql = ("SELECT employees.name, employees.l_name,fichajes.* "
           "FROM sql_telintec.fichajes "
           "INNER JOIN employees ON (fichajes.emp_id = employees.employee_id)")
    flag, error, result = execute_sql(sql, type_sql=2)
    return flag, error, result


def update_fichaje_DB(emp_id: int, contract: str, absences: dict, lates: dict, extras: dict,
                      primes: dict, normal: dict):
    sql = ("UPDATE sql_telintec.fichajes "
           "SET contract = %s, absences = %s, lates = %s, extras = %s, primes = %s, normal = %s "
           "WHERE emp_id = %s")
    val = (contract, json.dumps(absences), json.dumps(lates), json.dumps(extras),
           json.dumps(primes), json.dumps(normal), emp_id)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def insert_new_fichaje_DB(emp_id: int, contract: str, absences: dict, lates: dict, extras: dict,
                          primes: dict, normals: dict):
    sql = ("INSERT INTO sql_telintec.fichajes "
           "(emp_id, contract, absences, lates, extras, primes, normal) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    val = (emp_id, contract, json.dumps(absences), json.dumps(lates),
           json.dumps(extras), json.dumps(primes), json.dumps(normals))
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_fichaje_DB(emp_id: int):
    sql = ("SELECT * FROM sql_telintec.fichajes "
           "WHERE emp_id = %s")
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


# --------------------------------Examenes medicos GUI--------------------------
def insert_new_exam_med(name: str, blood: str, status: str, aptitud: list,
                        renovaciones: list, apt_actual: int, last_date: str,
                        emp_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.examenes_med "
           "(name, blood, status, aptitud, renovacion, aptitude_actual, empleado_id) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    val = (name.upper(), blood, status.upper(), json.dumps(aptitud),
           json.dumps(renovaciones), apt_actual,
           datetime.strptime(last_date, "%d/%m/%Y"), emp_id)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


# option 1
def update_aptitud_renovacion(aptitud: list, renovaciones: list, apt_actual: int, last_date: str, emp_id: int):
    sql = ("UPDATE sql_telintec.examenes_med "
           "SET aptitud = %s, renovacion = %s, aptitude_actual = %s "
           "WHERE empleado_id = %s")
    val = (json.dumps(aptitud), json.dumps(renovaciones), apt_actual, last_date, emp_id)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


# option 1
def get_aptitud_renovacion(emp_id: int):
    sql = ("SELECT aptitud, renovacion "
           "FROM sql_telintec.examenes_med "
           "WHERE empleado_id = %s")
    val = (emp_id,)
    flag, e, out = execute_sql(sql, val, 1)
    return flag, e, out


# option 2
def update_aptitud(aptitud: list, apt_actual: int, emp_id: int):
    sql = ("UPDATE sql_telintec.examenes_med "
           "SET aptitud = %s, aptitude_actual = %s "
           "WHERE empleado_id = %s")
    val = (json.dumps(aptitud), apt_actual, emp_id)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


def get_aptitud(emp_id: int):
    sql = ("SELECT aptitud "
           "FROM sql_telintec.examenes_med "
           "WHERE empleado_id = %s")
    val = (emp_id,)
    flag, e, out = execute_sql(sql, val, 1)
    return flag, e, out


# option 3
def update_renovacion(renovaciones: list, last_date: str, emp_id: int):
    sql = ("UPDATE sql_telintec.examenes_med "
           "SET renovacion = %s "
           "WHERE empleado_id = %s")
    val = (json.dumps(renovaciones), last_date, emp_id)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


def get_renovacion(emp_id: int):
    sql = ("SELECT renovacion "
           "FROM sql_telintec.examenes_med "
           "WHERE empleado_id = %s")
    val = (emp_id,)
    flag, e, out = execute_sql(sql, val, 1)
    return flag, e, out


def get_all_examenes():
    sql = "SELECT * FROM sql_telintec.examenes_med"
    flag, e, out = execute_sql(sql, type_sql=5)
    return flag, e, out


def update_status_EM(status, emp_id):
    sql = "UPDATE sql_telintec.examenes_med SET status = %s WHERE empleado_id = %s"
    val = (status, emp_id)
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


'''---------------------------Login API-----------------------'''


def verify_user_DB(user: str, password: str) -> bool:
    """
    Verifies if the user and password are correct.
    :param password: <String>
    :param user: <String>
    :return: <Boolean>
    """
    sql = "SELECT usernames FROM users_system " \
          "WHERE usernames = %s AND password = %s"
    val = (user, password)
    flag, error, result = execute_sql(sql, val)
    return True if len(result) > 0 else False


def get_permissions_user_password(user: str, password: str):
    """
    Gets the permissions for the user.
    :param user: <string>
    :param password: <string>
    :return: <list> [<permissions>, <code>
        <permissions>: <list>
        <code>: <int>
    """
    sql = ("SELECT permissions, emp_id, name, l_name, contrato  FROM users_system "
           "INNER JOIN employees ON (users_system.emp_id = employees.employee_id) "
           "WHERE usernames = %s AND password = %s ")
    val = (user, password)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        permissions = json.loads(result[0])
        emp_id = result[1]
        name = result[2]
        l_name = result[3]
        contrato = result[4]
    else:
        print("User not found")
        permissions = None
        emp_id = None
        name = None
        l_name = None
        contrato = None
    out = {"permissions": permissions,
           "emp_id": emp_id,
           "name": name + " " + l_name,
           "contract": contrato}
    return out


'''---------------------------Vacations table-----------------------'''


def insert_vacation(emp_id: int, seniority: dict):
    sql = "INSERT INTO vacations (emp_id, seniority) VALUES (%s, %s)"
    val = (emp_id, json.dumps(seniority))
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_vacations_data():
    sql = ("SELECT emp_id, name, l_name, date_admission, seniority  "
           "FROM vacations "
           "inner join employees on vacations.emp_id = employees.employee_id")
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result


def update_registry_vac(emp_id: int, seniority: dict):
    sql = "UPDATE vacations SET seniority = %s WHERE emp_id = %s"
    val = (json.dumps(seniority), emp_id)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_all_employees_active():
    sql = ("SELECT employee_id, name, l_name, date_admission "
           "FROM employees WHERE status = 'activo'")
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result


'''-------------------------AV almacén tables-----------------------'''


def get_product_categories():
    columns = ("id_category", "name")
    sql = "SELECT product_categories_amc.id_category, product_categories_amc.name FROM product_categories_amc limit 20 "
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result, columns


def get_products_almacen(id_p: int, name: str, category: str, limit: int = 10):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    sql = ("SELECT id_product, name, udm, stock, id_category FROM products_amc WHERE id_product = %s or "
           "(match(name) against (%s IN NATURAL LANGUAGE MODE ) and id_category = %s ) "
           "limit %s")
    val = (id_p, name, category, limit)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_high_stock_products(category: str, quantity: int):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = "SELECT * FROM product_categories_amc WHERE name = %s"
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = ("SELECT id_product, name, udm, stock, id_category "
               "FROM products_amc WHERE id_category = %s "
               "ORDER BY stock DESC limit %s")
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_low_stock_products(category: str, quantity: int):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = "SELECT * FROM product_categories_amc WHERE name = %s"
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = ("SELECT id_product, name, udm, stock, id_category "
               "FROM products_amc WHERE id_category = %s "
               "ORDER BY stock limit %s")
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_no_stock_products(category: str, quantity: int = 10):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = "SELECT * FROM product_categories_amc WHERE name = %s"
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = ("SELECT id_product, name, udm, stock, id_category "
               "FROM products_amc WHERE id_category = %s "
               "and stock=0 limit %s")
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_costumers_amc(name: str, id_c: int):
    columns = ("id_customer", "name", "phone", "email", "address")
    sql = ("SELECT id_customer, name, phone, email, address "
           "FROM customers_amc WHERE id_customer = %s or "
           "match(name) against (%s IN NATURAL LANGUAGE MODE ) "
           "limit 10")
    val = (id_c, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_supplier_amc(name: str, id_s: int):
    columns = ("id_supplier", "name", "phone", "type", "address")
    sql = ("SELECT id_supplier, name, phone, type, address "
           "FROM suppliers_amc WHERE id_supplier = %s or "
           "match(name) against (%s IN NATURAL LANGUAGE MODE ) "
           "limit 10")
    val = (id_s, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_orders_amc(id_o: int, id_c: int, status: str, name_c: str):
    columns = ("id_order", "id_customer", "status", "sm_code", "date", "id_customer")
    if id_c is None:
        # get id customer from name_c
        sql = "SELECT id_customer FROM customers_amc WHERE match(name) against (%s IN NATURAL LANGUAGE MODE ) "
        val = (name_c,)
        flag, error, result = execute_sql(sql, val, 1)
        if len(result) > 0:
            id_c = result[0]
        else:
            id_c = "%"
    sql = ("SELECT id_order, id_customer, status, sm_code, order_date, id_customer "
           "FROM orders_amc WHERE (id_order = %s or "
           "id_customer = %s) and status like %s "
           "limit 10")
    val = (id_o, id_c, status)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_product_movement_amc(type_m: str, id_m: int, id_p: int):
    columns = ("id_movement", "id_product", "type", "quantity", "date")
    sql = ("SELECT id_movement, id_product, movement_type, quantity, movement_date "
           "FROM product_movements_amc WHERE (id_movement = %s or "
           "id_product = %s) and movement_type like %s "
           "limit 10")
    val = (id_m, id_p, type_m)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_supply_inv_amc(id_s: int, name: str):
    columns = ("id_supply", "name", "id_supplier", "date", "status")
    sql = ("SELECT id_supply, name, stock "
           "FROM supply_inventory_amc WHERE (id_supply = %s or "
           "match(name) against (%s IN NATURAL LANGUAGE MODE ) ) "
           "limit 10")
    val = (id_s, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_fichaje_emp_AV(name: str, id_e: int):
    columns = ("id_employee", "absences", "lates", "lates_value[h]", "extras", "extras_value[h]", "primes")
    if id_e is None:
        id_e, name_db = get_employee_id_name(name)
        if id_e is not None:
            sql = ("SELECT emp_id, absences, lates, extras, primes "
                   "FROM fichajes WHERE emp_id = %s")
            val = (id_e,)
            flag, error, result = execute_sql(sql, val, 1)
            return flag, error, result, columns
        else:
            return False, "No employee in the DB", [], columns
    else:
        sql = ("SELECT emp_id, absences, lates, extras, primes "
               "FROM fichajes WHERE emp_id = %s")
        val = (id_e,)
        flag, error, result = execute_sql(sql, val, 1)
        return flag, error, result, columns


def get_employees_w_status(status: str, quantity: int, order: str):
    columns = ("employee_id", "name", "l_name", "date_admission", "status")
    sql = ("SELECT employee_id, name, l_name, date_admission, status "
           "FROM employees "
           "WHERE status like %s "
           "ORDER BY %s "
           "limit %s")
    val = (status, order, quantity)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_employee_info(id_e: int):
    columns = ("employee_id", "name", "l_name", "date_admission", "status", "department", "phone", "email", "contrato")
    sql = ("SELECT employee_id, name, l_name, date_admission, status, department_id, phone_number, email, contrato "
           "FROM employees "
           "WHERE employee_id = %s")
    val = (id_e,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result, columns


'''-----------------------------------SM API-------------------------------------'''


def get_sm_employees():
    sql = ("SELECT employee_id, name, l_name "
           "FROM employees where status = 'activo' "
           "and (department_id=2 or department_id=3)")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_sm_clients():
    sql = ("SELECT id_customer, name "
           "FROM customers_amc  ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_sm_products():
    sql = ("SELECT id_product, name, udm, stock "
           "FROM products_amc ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_sm_entries():
    sql = ("SELECT sm_id, sm_code, folio, contract, facility, location, client_id, emp_id, date, limit_date, items, status "
           "FROM materials_request ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def insert_sm_db(data):
    sql = ("INSERT INTO materials_request (sm_code, folio, contract, facility, location, "
           "client_id, emp_id, date, limit_date, items, status)"
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    val = (data['info']['sm_code'], data['info']['folio'], data['info']['contract'], data['info']['facility'], data['info']['location'],
           data['info']['client_id'], data['info']['emp_id'], data['info']['date'], data['info']['limit_date'],
           json.dumps(data['items']), data['info']['status'])
    flag, error, result = execute_sql(sql, val, 4)
    print(error, result)
    return flag, error, result


def delete_sm_db(id_m: int, sm_code: str):
    sql = "DELETE FROM materials_request WHERE sm_id = %s and sm_code = %s "
    val = (id_m, sm_code)
    flag, error, result = execute_sql(sql, val, 3)
    if not flag:
        return False, error, None
    sql = "SELECT * FROM materials_request WHERE sm_id = %s and sm_code = %s"
    val = (id_m, sm_code)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return True, "Material request deleted", None
    else:
        return False, "Material request not deleted", None


def update_sm_db(data):
    sql = "SELECT sm_id FROM materials_request "
    flag, error, result = execute_sql(sql, None, 5)
    if not flag:
        return False, error, None
    ids_sm = result
    if data['id_sm'] not in ids_sm:
        return True, "Material request not found", None
    sql = ("UPDATE materials_request SET sm_code = %s, folio = %s, contract = %s, facility = %s, location = %s, "
           "client_id = %s, emp_id = %s, date = %s, limit_date = %s, items = %s, status = %s "
           "WHERE sm_id = %s")
    val = (data['info']['sm_code'], data['info']['folio'], data['info']['contract'], data['info']['facility'], data['info']['location'],
           data['info']['client_id'], data['info']['emp_id'], data['info']['date'], data['info']['limit_date'],
           json.dumps(data['items']), data['info']['status'], data['id_sm'])
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result
