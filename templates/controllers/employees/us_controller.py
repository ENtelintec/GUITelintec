# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 19:37 $"

import json

from templates.database.connection import execute_sql


def fetch_employess_user_data(status="activo"):
    if status == "all":
        status = "%"
    sql = (
        "SELECT "
        "sql_telintec.employees.employee_id, "
        "sql_telintec.employees.name, "
        "l_name, "
        "birthday, "
        "contrato, "
        "status, "
        "sql_telintec.employees.department_id, "
        "sql_telintec.departments.name, "
        "sql_telintec.users_system.usernames, "
        "sql_telintec.users_system.biocredentials "
        "from sql_telintec.employees "
        "LEFT JOIN sql_telintec.departments on sql_telintec.departments.department_id=sql_telintec.employees.department_id "
        "LEFT JOIN sql_telintec.users_system on sql_telintec.users_system.emp_id=sql_telintec.employees.employee_id "
        "where status like %s"
    )
    val = (status,)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result


def update_biocredentials_DB(biocredentials, emp_id, user):
    sql = (
        "UPDATE sql_telintec.users_system "
        "SET biocredentials = %s "
        "WHERE emp_id = %s and usernames = %s "
    )
    val = (biocredentials, emp_id, user)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def create_user_system_with_token(
    user, hash_pass, dic_perm, token, exp, timestamp_token, emp_id
):
    sql = (
        "INSERT INTO sql_telintec.users_system (usernames, password, permissions, emp_id, token, exp, timestamp_token) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    val = (user, hash_pass, json.dumps(dic_perm), emp_id, token, exp, timestamp_token)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result
