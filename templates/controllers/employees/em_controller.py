# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 20:07 $"

import json

from templates.database.connection import execute_sql


def insert_new_exam_med(
    name: str,
    blood: str,
    status: str,
    aptitud: list,
    renovaciones: list,
    apt_actual: int,
    emp_id: int,
) -> tuple[bool, Exception | None, int | None]:
    sql = (
        "INSERT INTO sql_telintec.examenes_med "
        "(name, blood, status, aptitud, renovacion, aptitude_actual, empleado_id) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        name.upper(),
        blood,
        status.upper(),
        json.dumps(aptitud),
        json.dumps(renovaciones),
        apt_actual,
        emp_id,
    )
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, e, out


def update_aptitud_renovacion(
    aptitud: list, renovaciones: list, apt_actual: int, exam_id
):
    sql = (
        "UPDATE sql_telintec.examenes_med "
        "SET aptitud = %s, renovacion = %s, aptitude_actual = %s "
        "WHERE examen_id = %s"
    )
    val = (json.dumps(aptitud), json.dumps(renovaciones), apt_actual, exam_id)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted.")
    return flag, e, out


def delete_exam_med(exm_id: int):
    sql = "DELETE FROM sql_telintec.examenes_med " "WHERE examen_id = %s"
    val = (exm_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_aptitud_renovacion(emp_id: int):
    sql = (
        "SELECT aptitud, renovacion "
        "FROM sql_telintec.examenes_med "
        "WHERE empleado_id = %s"
    )
    val = (emp_id,)
    flag, e, out = execute_sql(sql, val, 1)
    return flag, e, out


def update_aptitud(aptitud: list, apt_actual: int, emp_id: int = None, exam_id=None):
    sql = (
        (
            "UPDATE sql_telintec.examenes_med "
            "SET aptitud = %s, aptitude_actual = %s "
            "WHERE empleado_id = %s"
        )
        if exam_id is None
        else (
            "UPDATE sql_telintec.examenes_med "
            "SET aptitud = %s, aptitude_actual = %s "
            "WHERE examen_id = %s"
        )
    )
    val = (
        (json.dumps(aptitud), apt_actual, emp_id)
        if exam_id is None
        else (json.dumps(aptitud), apt_actual, exam_id)
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_aptitud(emp_id: int):
    sql = "SELECT aptitud " "FROM sql_telintec.examenes_med " "WHERE empleado_id = %s"
    val = (emp_id,)
    flag, e, out = execute_sql(sql, val, 1)
    return flag, e, out


# option 3
def update_renovacion(
    renovaciones: list, last_date: str, emp_id: int = None, exam_id=None
):
    sql = (
        (
            "UPDATE sql_telintec.examenes_med "
            "SET renovacion = %s "
            "WHERE empleado_id = %s"
        )
        if exam_id is None
        else (
            "UPDATE sql_telintec.examenes_med "
            "SET renovacion = %s "
            "WHERE examen_id = %s"
        )
    )
    val = (
        (json.dumps(renovaciones), emp_id)
        if exam_id is None
        else (json.dumps(renovaciones), exam_id)
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_renovacion(emp_id: int, exam_id=None):
    sql = (
        (
            "SELECT renovacion "
            "FROM sql_telintec.examenes_med "
            "WHERE empleado_id = %s"
        )
        if exam_id is None
        else (
            "SELECT renovacion "
            "FROM sql_telintec.examenes_med "
            "WHERE examen_id = %s"
        )
    )
    val = (emp_id,)
    flag, e, out = execute_sql(sql, val, 1)
    return flag, e, out


def get_all_examenes():
    sql = (
        "SELECT "
        "examen_id, "
        "examenes_med.name, "
        "blood, "
        "UPPER(employees.status), "
        "aptitud, "
        "renovacion, "
        "aptitude_actual, "
        "empleado_id "
        "FROM sql_telintec.examenes_med "
        "LEFT JOIN sql_telintec.employees on employees.employee_id = examenes_med.empleado_id "
        "ORDER BY name "
    )
    flag, e, out = execute_sql(sql, type_sql=5)
    return flag, e, out


def update_status_EM(status, emp_id):
    sql = "UPDATE sql_telintec.examenes_med SET status = %s WHERE empleado_id = %s"
    val = (status, emp_id)
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_date_aptitud(dates, aptituds, emp_id=None, exam_id=None):
    sql = (
        (
            "UPDATE sql_telintec.examenes_med "
            "SET renovacion = %s, aptitud = %s, aptitude_actual = %s "
            "WHERE empleado_id = %s"
        )
        if exam_id is None
        else (
            "UPDATE sql_telintec.examenes_med "
            "SET renovacion = %s, aptitud = %s, aptitude_actual = %s "
            "WHERE examen_id = %s"
        )
    )
    last_aptitud = aptituds[-1] if len(aptituds) > 0 else 0
    val = (
        (json.dumps(dates), json.dumps(aptituds), last_aptitud, emp_id)
        if exam_id is None
        else (json.dumps(dates), json.dumps(aptituds), last_aptitud, exam_id)
    )
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def get_employees_without_records():
    sql = (
        "SELECT name, l_name, status, birthday, date_admission, employee_id "
        "FROM sql_telintec.employees "
        "WHERE LOWER(status) = 'activo' "
        "AND employee_id NOT IN (SELECT empleado_id FROM sql_telintec.examenes_med) "
        "ORDER BY name, l_name"
    )
    flag, e, out = execute_sql(sql, type_sql=5)
    return flag, e, out
