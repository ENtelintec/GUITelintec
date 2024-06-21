# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:37 $'

import json

from templates.database.connection import execute_sql


def get_users(limit=(0, 100)):
    sql = ("SELECT "
           "U_id, "
           "usernames, "
           "permissions, "
           "exp, "
           "timestamp_token "
           "FROM sql_telintec.users_system "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def get_username_data(username: str):
    sql = ("select "
           "sql_telintec.users_system.exp, "
           "sql_telintec.users_system.timestamp_token, "
           "sql_telintec.employees.name, "
           "sql_telintec.employees.l_name, "
           "sql_telintec.employees.department_id, "
           "sql_telintec.departments.name, "
           "sql_telintec.employees.contrato, "
           "sql_telintec.employees.employee_id "
           "FROM sql_telintec.users_system "
           "INNER JOIN sql_telintec.employees ON users_system.emp_id = employee_id "
           "INNER JOIN sql_telintec.departments on sql_telintec.employees.department_id = sql_telintec.departments.department_id "
           "WHERE users_system.usernames = %s")
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
            "contract": result[6],
            "id": result[7]
        }
    return out


def get_user_data_by_ID(user_id: int):
    sql = ("SELECT "
           "sql_telintec.users_system.exp, "
           "sql_telintec.users_system.timestamp_token, "
           "sql_telintec.employees.name, "
           "sql_telintec.employees.l_name, "
           "sql_telintec.employees.department_id, "
           "sql_telintec.departments.name, "
           "sql_telintec.employees.contrato "
           "FROM sql_telintec.users_system "
           "INNER JOIN sql_telintec.employees ON sql_telintec.users_system.emp_id = employee_id "
           "INNER JOIN sql_telintec.departments on sql_telintec.employees.department_id = sql_telintec.departments.department_id "
           "WHERE sql_telintec.users_system.emp_id = %s ")
    val = (user_id,)
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


def verify_user_DB(user: str, password: str) -> bool:
    """
    Verifies if the user AND password are correct.
    :param password: <String>
    :param user: <String>
    :return: <Boolean>
    """
    sql = ("SELECT usernames "
           "FROM sql_telintec.users_system "
           "WHERE usernames = %s AND password = %s")
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
    sql = (
        "SELECT "
        "sql_telintec.users_system.permissions, "
        "sql_telintec.users_system.emp_id, "
        "sql_telintec.employees.name, "
        "sql_telintec.employees.l_name, "
        "sql_telintec.employees.contrato  "
        "FROM sql_telintec.users_system "
        "INNER JOIN sql_telintec.employees ON (sql_telintec.users_system.emp_id = sql_telintec.employees.employee_id) "
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
