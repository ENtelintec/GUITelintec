# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/jul./2024  at 15:34 $"

import json

from templates.database.connection import execute_sql


def get_payrolls(employee_id, data_token):
    if employee_id <= 0:
        sql = (
            "SELECT id, files_data, sql_telintec.employees.name, sql_telintec.employees.l_name "
            "FROM sql_telintec_mod_rrhh.payroll "
            "LEFT JOIN sql_telintec.employees ON employees.employee_id = payroll.id "
            "WHERE sql_telintec.employees.status = 'activo' "
            "ORDER BY sql_telintec.employees.name, sql_telintec.employees.l_name "
        )
        flag, error, result = execute_sql(sql, None, 5, data_token)
        return flag, error, result
    else:
        sql = (
            "SELECT id, files_data, sql_telintec.employees.name, sql_telintec.employees.l_name "
            "FROM sql_telintec_mod_rrhh.payroll "
            "LEFT JOIN sql_telintec.employees ON employees.employee_id = payroll.id "
            "WHERE id = %s"
        )
        vals = (employee_id,)
        flag, error, result = execute_sql(sql, vals, 1, data_token)
        return flag, error, [result]


def create_payroll(data, emp_id, data_token):
    sql = "INSERT INTO sql_telintec_mod_rrhh.payroll (id, files_data) VALUES (%s, %s)"
    vals = (emp_id, data)
    flag, error, result = execute_sql(sql, vals, 4, data_token)
    return flag, error, result


def update_payroll(data: dict, emp_id, data_token):
    sql = "UPDATE sql_telintec_mod_rrhh.payroll SET files_data = %s WHERE id = %s"
    vals = (json.dumps(data), emp_id)
    flag, error, result = execute_sql(sql, vals, 3, data_token)
    return flag, error, result


def delete_payroll(emp_id, data_token):
    sql = "DELETE FROM sql_telintec_mod_rrhh.payroll WHERE id = %s"
    vals = (emp_id,)
    flag, error, result = execute_sql(sql, vals, 3, data_token)
    return flag, error, result


def get_payrolls_with_info(employee_id, data_token):
    if employee_id <= 0:
        sql = (
            "SELECT "
            "id, UPPER(name), UPPER(l_name), files_data "
            "FROM sql_telintec_mod_rrhh.payroll "
            "INNER JOIN sql_telintec.employees ON employees.employee_id = payroll.id"
        )
        flag, error, result = execute_sql(sql, None, 5, data_token)
    else:
        sql = (
            "SELECT id, UPPER(name), UPPER(l_name), files_data "
            "FROM sql_telintec_mod_rrhh.payroll "
            "INNER JOIN sql_telintec.employees ON employees.employee_id = payroll.id "
            "WHERE id = %s"
        )
        vals = (employee_id,)
        flag, error, result = execute_sql(sql, vals, 1, data_token)
    return flag, error, result


def update_payroll_employees(data_token):
    """Fila de nómina para los empleados que no la tienen (la pantalla de Nómina
    lo llama en cada carga). Antes era un INSERT por empleado: 1 + N consultas,
    casi todas "Duplicate entry", y en prod el worker llegó al timeout de
    gunicorn (2026-10-28). Ahora: SELECT de los que faltan y, si falta alguno,
    un solo INSERT de varias filas; las dos con el mismo data_token (antes el
    SELECT iba sin token). -> (flag, error, ids agregados)."""
    sql = (
        "SELECT e.employee_id FROM sql_telintec.employees e "
        "LEFT JOIN sql_telintec_mod_rrhh.payroll p ON p.id = e.employee_id "
        "WHERE p.id IS NULL"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    if not flag:
        return False, error, []
    missing = [row[0] for row in result] if isinstance(result, (list, tuple)) else []
    if not missing:
        return True, None, []
    # ON DUPLICATE KEY: si otra carga los dio de alta entre el SELECT y el INSERT, no falla.
    placeholders = ", ".join(["(%s)"] * len(missing))
    sql = f"INSERT INTO sql_telintec_mod_rrhh.payroll (id) VALUES {placeholders} ON DUPLICATE KEY UPDATE id = id"
    flag, error, _rows = execute_sql(sql, tuple(missing), 3, data_token)
    if not flag:
        return False, error, []
    return True, None, missing
