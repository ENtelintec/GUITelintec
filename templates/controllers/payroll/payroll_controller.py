# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 22/jul./2024  at 15:34 $'

import json

from templates.database.connection import execute_sql


def get_payrolls(employee_id):
    if employee_id <= 0:
        sql = ("SELECT id, files_data "
               "FROM sql_telintec.payroll")
        flag, error, result = execute_sql(sql, None, 5)
    else:
        sql = ("SELECT id, files_data "
               "FROM sql_telintec.payroll "
               "WHERE id = %s")
        vals = (employee_id,)
        flag, error, result = execute_sql(sql, vals, 1)
    return flag, error, result


def create_payroll(data, emp_id):
    sql = ("INSERT INTO "
           "sql_telintec.payroll (id, files_data) "
           "VALUES (%s, %s)")
    vals = (emp_id, data)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_payroll(data: dict, emp_id):
    sql = ("UPDATE sql_telintec.payroll "
           "SET files_data = %s "
           "WHERE id = %s")
    vals = (json.dumps(data), emp_id)
    print(vals)
    flag, error, result = execute_sql(sql, vals, 3)
    return flag, error, result


def delete_payroll(emp_id):
    sql = ("DELETE FROM sql_telintec.payroll "
           "WHERE id = %s")
    vals = (emp_id,)
    flag, error, result = execute_sql(sql, vals, 3)
    return flag, error, result