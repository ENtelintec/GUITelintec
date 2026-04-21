# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 19:25 $"

import json


from templates.database.connection import execute_sql


def get_heads_db(data_token, id_department: int | None = None):
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
        execute_sql(sql, val, 2, data_token)
        if id_department is not None
        else execute_sql(sql, val, 5, data_token)
    )
    if not isinstance(my_result, list):
        return flag, "no data found or error", []
    return flag, e, my_result


def get_heads_list_db(dep_list: list, data_token):
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
    print(sql, val)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    if not isinstance(my_result, list):
        return flag, e, []
    return flag, e, my_result


def check_if_gerente(id_employee: int, data_token):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info, "
        "areas.abbreviation, "
        "JSON_UNQUOTE(heads.extra_info->'$.area'), "
        "departments.abbreviation "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        "LEFT JOIN sql_telintec.areas ON JSON_UNQUOTE(heads.extra_info->'$.area') = areas.id "
        "WHERE heads.employee = %s AND (LOWER(heads.name) like '%gerente%' OR LOWER(heads.name) like '%jefe%')"
    )
    val = (id_employee,)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    if not isinstance(my_result, list):
        return flag, e, []
    return flag, e, my_result


def check_if_leader(id_employee: int, data_token):
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
        "LEFT JOIN sql_telintec.areas ON JSON_UNQUOTE(heads.extra_info->'$.area') = areas.id "
        "WHERE ("
        "heads.employee = %s OR "
        "JSON_CONTAINS(sql_telintec.heads.extra_info->'$.other_leaders', CAST( %s AS JSON))"
        ") AND LOWER(heads.name) like '%lider%'"
    )
    val = (id_employee, id_employee)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    if not isinstance(my_result, list):
        return flag, e, []
    return flag, e, my_result


def check_if_auxiliar_with_contract(id_employee: int, data_token):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info, "
        "areas.abbreviation, "
        "JSON_UNQUOTE(heads.extra_info->'$.area'), "
        "departments.abbreviation "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        "LEFT JOIN sql_telintec.areas ON JSON_UNQUOTE(heads.extra_info->'$.area') = areas.id "
        "WHERE heads.employee = %s AND LOWER(heads.name) like '%auxiliar%' "
    )
    val = (id_employee,)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    if not isinstance(my_result, list):
        return flag, e, []
    return flag, e, my_result


def check_if_head_not_auxiliar(id_employee: int, data_token):
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info,"
        "areas.abbreviation, "
        "JSON_UNQUOTE(heads.extra_info->'$.area'), "
        "departments.abbreviation "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "LEFT JOIN sql_telintec.departments ON heads.department = departments.department_id "
        "LEFT JOIN sql_telintec.areas ON JSON_UNQUOTE(heads.extra_info->'$.area') = areas.id "
        "WHERE (heads.employee = %s "
        "AND LOWER(heads.name) not like '%auxiliar%'  "
        "AND LOWER(heads.name) not like '%lider%') "
        "OR "
        "(JSON_CONTAINS(sql_telintec.heads.extra_info->'$.other_leaders', CAST( %s AS JSON)) "
        "AND LOWER(heads.name) not like '%auxiliar%'  "
        "AND LOWER(heads.name) not like '%lider%') "
    )
    val = (id_employee, id_employee)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    return flag, e, my_result


def check_if_auxiliar(id_employee: int, data_token):
    """
    Join all departments when is auxiliar
    """
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info,"
        "areas.abbreviation, "
        "JSON_UNQUOTE(heads.extra_info->'$.area'), "
        "departments.abbreviation "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "JOIN sql_telintec.departments ON departments.department_id not like '' "
        "LEFT JOIN sql_telintec.areas ON JSON_UNQUOTE(heads.extra_info->'$.area') = areas.id "
        "WHERE (heads.employee = %s "
        "AND LOWER(heads.name) like '%auxiliar%')  "
    )
    val = (id_employee,)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    return flag, e, my_result


def check_if_gerente_admin(id_employee: int, data_token):
    """
    Join all departments when is jefe admin
    """
    sql = (
        "SELECT "
        "heads.position_id, "
        "heads.name, "
        "heads.employee, "
        "heads.department, "
        "departments.name, "
        "UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, "
        "employees.email, "
        "heads.extra_info,"
        "areas.abbreviation, "
        "JSON_UNQUOTE(heads.extra_info->'$.area'), "
        "departments.abbreviation "
        "FROM sql_telintec.heads "
        "LEFT JOIN sql_telintec.employees ON heads.employee = employees.employee_id "
        "JOIN sql_telintec.departments ON departments.department_id not like '' "
        "LEFT JOIN sql_telintec.areas ON JSON_UNQUOTE(heads.extra_info->'$.area') = areas.id "
        "WHERE heads.employee = %s AND (LOWER(heads.name) like '%gerente%' OR LOWER(heads.name) like '%jefe%')"
    )
    val = (id_employee,)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    print("check admin", my_result)
    return flag, e, my_result


def insert_head_DB(
    position_name: str, department: int, employee: int, extra_info: dict, data_token
):
    sql = (
        "INSERT INTO sql_telintec.heads (name, department, employee, extra_info) "
        "VALUES (%s, %s, %s, %s)"
    )
    val = (position_name, department, employee, json.dumps(extra_info))
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_head_DB(
    position_id: int, department: int, employee: int, extra_info: dict, data_token
):
    sql = (
        "UPDATE sql_telintec.heads "
        "SET department = %s, employee = %s, extra_info = %s "
        "WHERE position_id = %s"
    )
    val = (department, employee, json.dumps(extra_info), position_id)
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def delete_head_DB(head_id: int, data_token) -> tuple[bool, str | None, int | None]:
    sql = "DELETE FROM sql_telintec.heads WHERE position_id = %s"
    val = (head_id,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    if not isinstance(out, int):
        return False, e, 0
    return flag, e, out
