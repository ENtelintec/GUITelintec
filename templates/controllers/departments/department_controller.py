# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:25 $'

from templates.database.connection import execute_sql


def get_departments(data_token, limit=(0, 100)):
    sql = ("SELECT department_id, name, location "
           "FROM sql_telintec.departments "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    out = my_result if my_result is not None else []
    return out


def insert_department(name: str, location: str, data_token):
    sql = ("INSERT INTO sql_telintec.departments (name, location) "
           "VALUES (%s, %s)")
    val = (name, location)
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, None, out


def update_department_DB(name: str, location: str, department_id: int, data_token):
    sql = ("UPDATE sql_telintec.departments "
           "SET name = %s, location = %s "
           "WHERE department_id = %s")
    val = (name, location, department_id)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_department_DB(department_id: int, data_token):
    sql = ("DELETE FROM sql_telintec.departments "
           "WHERE department_id = %s")
    val = (department_id,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out
