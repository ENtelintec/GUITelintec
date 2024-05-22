# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:25 $'

from templates.database.connection import execute_sql


def get_heads(limit=(0, 100)) -> list[list]:
    sql = ("SELECT "
           "heads.name, "
           "heads.employee, "
           "heads.department, "
           "departments.name, "
           "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
           "employees.email "
           "FROM sql_telintec.heads "
           "INNER JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
           "INNER JOIN sql_telintec.departments ON heads.department = departments.department_id "
           "LIMIT %s ")
    val = (limit[1],)
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


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
    sql = ("UPDATE sql_telintec.heads "
           "SET name = %s, department = %s, employee = %s "
           "WHERE position_id = %s")
    val = (position_name, department, employee, head_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_head_DB(head_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("DELETE FROM sql_telintec.heads "
           "WHERE position_id = %s")
    val = (head_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out