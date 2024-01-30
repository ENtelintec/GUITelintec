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
    mydb = mysql.connector.connect(
        host=secrets["HOST_DB_AWS"],
        user=secrets["USER_SQL_AWS"],
        password=secrets["PASS_SQL_AWS"],
        database="sql_telintec"
    )
    my_cursor = mydb.cursor(buffered=True)
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
    mydb = mysql.connector.connect(
        host=secrets["HOST_DB_AWS"],
        user=secrets["USER_SQL_AWS"],
        password=secrets["PASS_SQL_AWS"],
        database="sql_telintec"
    )
    out = []
    flag = True
    error = None
    my_cursor = mydb.cursor(buffered=True)
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


def new_employee(name, lastname, curp, phone, email, department, contract, entry_date, rfc, nss, emergency, modality):
    sql = ("INSERT INTO employees (name, l_name, curp, phone_number, email, department_id,"
           " contrato, date_admission, rfc, nss, emergency_contact, modality) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    values = (name, lastname, curp, phone, email, department,
              contract, entry_date, rfc, nss, emergency, modality)
    flag, e, out = execute_sql(sql, values, 4)
    return flag, e, out


def update_employee(employee_id, name, lastname, curp, phone, email, department, contract, entry_date, rfc, nss, emergency, modality):
    sql = ("UPDATE employees SET name = %s, l_name = %s, curp = %s, phone_number = %s, email = %s, department_id = %s,"
           "contrato = %s, date_admission = %s, rfc = %s, nss = %s, emergency_contact = %s, modality = %s "
           "WHERE employee_id = %s")
    values = (name, lastname, curp, phone, email, department,
              contract, entry_date, rfc, nss, emergency, modality, employee_id)
    flag, e, out = execute_sql(sql, values, 3)
    return flag, e, out


def get_employee_id_name(name: str) -> tuple[None, None] | tuple[int, str]:
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
        return None, None
    else:
        return out[0], f"{out[1].title()} {out[2].title()}"


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
    if e is not None or len(out) == 0:
        return None
    else:
        return out[0]


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


def insert_employee(name: str, lastname: str, dni: str, phone: str, email: str,
                    department: str, modality: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.employees (name, l_name, phone_number, email, department_id, modality) "
           "VALUES (%s, %s, %s, %s, %s, %s)")
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
           " employees.l_name, employees.department_id, departments.name "
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
            "department_name": result[5]
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


# --------------------------------Examenes medicos GUI--------------------------
def insert_new_exam_med(name: str, blood: str, status: str, aptitud: list,
                        renovaciones: list, apt_actual: int, last_date: str,
                        emp_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.examenes_med "
           "(name, blood, status, aptitud, renovacion, aptitude_actual, fecha_ultima_renovacion, empleado_id) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
    val = (name.upper(), blood, status.upper(), json.dumps(aptitud),
           json.dumps(renovaciones), apt_actual,
           datetime.strptime(last_date, "%d/%m/%Y"), emp_id)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


# option 1
def update_aptitud_renovacion(aptitud: list, renovaciones: list, apt_actual: int, last_date: str, emp_id: int):
    sql = ("UPDATE sql_telintec.examenes_med "
           "SET aptitud = %s, renovacion = %s, aptitude_actual = %s, fecha_ultima_renovacion = %s "
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
           "SET renovacion = %s, fecha_ultima_renovacion = %s "
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

# ---------------------------Login API-----------------------
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
    sql = "SELECT permissions FROM users_system " \
          "WHERE usernames = %s AND password = %s"
    val = (user, password)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        permissions = json.loads(result[0])
    else:
        print("User not found")
        permissions = None
    return permissions
