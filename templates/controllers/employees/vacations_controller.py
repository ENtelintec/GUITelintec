# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 20:16 $"

import json

from templates.database.connection import execute_sql


def insert_vacation(emp_id: int, seniority: dict):
    sql = "INSERT INTO sql_telintec.vacations " "(emp_id, seniority) " "VALUES (%s, %s)"
    val = (emp_id, json.dumps(seniority))
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def update_registry_vac(emp_id: int, seniority: dict):
    sql = "UPDATE sql_telintec.vacations " "SET seniority = %s " "WHERE emp_id = %s"
    val = (json.dumps(seniority), emp_id)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def delete_vacation(emp_id: int):
    sql = "DELETE FROM sql_telintec.vacations " "WHERE emp_id = %s"
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def get_vacations_data():
    sql = (
        "SELECT emp_id, name, l_name, date_admission, seniority  "
        "FROM sql_telintec.vacations "
        "INNER JOIN sql_telintec.employees ON sql_telintec.vacations.emp_id = sql_telintec.employees.employee_id "
        "ORDER BY name, l_name"
    )
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result


def get_vacations_data_emp(emp_id: int):
    sql = (
        "SELECT emp_id, name, l_name, date_admission, seniority  "
        "FROM sql_telintec.vacations "
        "INNER JOIN sql_telintec.employees ON sql_telintec.vacations.emp_id = sql_telintec.employees.employee_id "
        "WHERE emp_id = %s"
    )
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result
