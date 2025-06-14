# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 19:25 $"

import json


from templates.database.connection import execute_sql


def get_heads_db(id_department: int = None):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
    )
    sql += "WHERE heads.department = %s" if id_department is not None else ""
    val = (id_department,) if id_department is not None else None
    flag, e, my_result = (
        execute_sql(sql, val, 2)
        if id_department is not None
        else execute_sql(sql, val, 5)
    )
    return flag, e, my_result


def get_heads_list_db(dep_list: list):
    placeholders = ", ".join(["%s"] * len(dep_list))
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        f"WHERE heads.department IN ({placeholders})"
    )
    val = tuple(dep_list)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def check_if_gerente(id_employee: int):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        "WHERE heads.employee = %s AND (LOWER(heads.name) like '%gerente%' OR LOWER(heads.name) like '%jefe%')"
    )
    val = (id_employee,)
    flag, e, my_result = execute_sql(sql, val, 1)
    return flag, e, my_result


def check_if_leader(id_employee: int):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        "WHERE ("
        "heads.employee = %s OR "
        "JSON_CONTAINS(sql_telintec.heads.extra_info->'$.other_leaders', CAST( %s AS JSON))"
        ") AND LOWER(heads.name) like '%lider%'"
    )
    val = (id_employee, id_employee)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def check_if_auxiliar_with_contract(id_employee: int):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        "WHERE heads.employee = %s AND LOWER(heads.name) like '%auxiliar%' "
    )
    val = (id_employee,)
    flag, e, my_result = execute_sql(sql, val, 2)
    return flag, e, my_result


def check_if_head_not_auxiliar(id_employee: int):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        "WHERE heads.employee = %s AND LOWER(heads.name) not like '%auxiliar%'  AND LOWER(heads.name) not like '%lider%' "
    )
    val = (id_employee,)
    flag, e, my_result = execute_sql(sql, val, 1)
    return flag, e, my_result


def insert_head_DB(
    position_name: str, department: int, employee: int, extra_info: dict
):
    sql = (
        "INSERT INTO sql_telintec.heads (name, department, employee, extra_info) "
        "VALUES (%s, %s, %s, %s)"
    )
    val = (position_name, department, employee, json.dumps(extra_info))
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_head_DB(position_id: int, department: int, employee: int, extra_info: dict):
    sql = (
        "UPDATE sql_telintec.heads "
        "SET department = %s, employee = %s, extra_info = %s "
        "WHERE position_id = %s"
    )
    val = (department, employee, json.dumps(extra_info), position_id)
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def delete_head_DB(head_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = "DELETE FROM sql_telintec.heads " "WHERE position_id = %s"
    val = (head_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out
