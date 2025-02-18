# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/jul./2024  at 15:34 $"

import json

from templates.database.connection import execute_sql


def get_payrolls(employee_id):
    if employee_id <= 0:
        sql = ("SELECT id, files_data, sql_telintec.employees.name, sql_telintec.employees.l_name "
               "FROM sql_telintec.payroll "
               "LEFT JOIN sql_telintec.employees ON employees.employee_id = payroll.id "
               "ORDER BY sql_telintec.employees.name ")
        flag, error, result = execute_sql(sql, None, 5)
        return flag, error, result
    else:
        sql = "SELECT id, files_data " "FROM sql_telintec.payroll " "WHERE id = %s"
        vals = (employee_id,)
        flag, error, result = execute_sql(sql, vals, 1)
        return flag, error, [result]


def create_payroll(data, emp_id):
    sql = "INSERT INTO " "sql_telintec.payroll (id, files_data) " "VALUES (%s, %s)"
    vals = (emp_id, data)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_payroll(data: dict, emp_id):
    sql = "UPDATE sql_telintec.payroll " "SET files_data = %s " "WHERE id = %s"
    vals = (json.dumps(data), emp_id)
    flag, error, result = execute_sql(sql, vals, 3)
    return flag, error, result


def delete_payroll(emp_id):
    sql = "DELETE FROM sql_telintec.payroll " "WHERE id = %s"
    vals = (emp_id,)
    flag, error, result = execute_sql(sql, vals, 3)
    return flag, error, result


def get_payrolls_with_info(employee_id):
    if employee_id <= 0:
        sql = (
            "SELECT "
            "id, UPPER(name), UPPER(l_name), files_data "
            "FROM sql_telintec.payroll "
            "INNER JOIN sql_telintec.employees ON employees.employee_id = payroll.id"
        )
        flag, error, result = execute_sql(sql, None, 5)
    else:
        sql = (
            "SELECT id, UPPER(name), UPPER(l_name), files_data "
            "FROM sql_telintec.payroll "
            "INNER JOIN sql_telintec.employees ON employees.employee_id = payroll.id "
            "WHERE id = %s"
        )
        vals = (employee_id,)
        flag, error, result = execute_sql(sql, vals, 1)
    return flag, error, result


def update_payroll_employees():
    sql = "SELECT employee_id from sql_telintec.employees"
    flag, error, result = execute_sql(sql, None, 5)
    if not flag:
        return flag, error, []
    data_out = []
    for employee in result:
        emp_id = employee[0]
        sql = "INSERT INTO sql_telintec.payroll (id) VALUES (%s)"
        vals = (emp_id,)
        flag, error, result = execute_sql(sql, vals, 4)
        data_out.append([flag, error, emp_id])
    return True, None, data_out
