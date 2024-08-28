# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 18:20 $"

import json

from templates.database.connection import execute_sql
from templates.controllers.employees.employees_controller import get_employee_id_name


def update_fichaje_DB(
    emp_id: int,
    contract: str,
    absences: dict,
    lates: dict,
    extras: dict,
    primes: dict,
    normal: dict,
    early=None,
    pasiva=None,
):
    early = early if early is not None else {}
    pasiva = pasiva if pasiva is not None else {}
    sql = (
        "UPDATE sql_telintec.fichajes "
        "SET absences = %s, lates = %s, extras = %s, primes = %s, normal = %s, early = %s, pasiva = %s "
        "WHERE emp_id = %s"
    )
    val = (
        json.dumps(absences),
        json.dumps(lates),
        json.dumps(extras),
        json.dumps(primes),
        json.dumps(normal),
        json.dumps(early),
        json.dumps(pasiva),
        emp_id,
    )
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def create_new_emp_fichaje(emp_id: int, contract: str):
    sql = "INSERT INTO sql_telintec.fichajes (emp_id, contract) VALUES (%s, %s)"
    val = (emp_id, contract)
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def insert_new_fichaje_DB(
    emp_id: int,
    contract: str,
    absences: dict,
    lates: dict,
    extras: dict,
    primes: dict,
    normals: dict,
    early=None,
    pasiva=None,
):
    early = early if early is not None else {}
    pasiva = pasiva if pasiva is not None else {}
    sql = (
        "INSERT INTO sql_telintec.fichajes "
        "(emp_id, contract, absences, lates, extras, primes, normal, early, pasiva) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        emp_id,
        contract,
        json.dumps(absences),
        json.dumps(lates),
        json.dumps(extras),
        json.dumps(primes),
        json.dumps(normals),
        json.dumps(early),
        json.dumps(pasiva),
    )
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_fichaje_DB(emp_id: int):
    sql = (
        "SELECT "
        "ficha_id, emp_id, contract, "
        "absences, lates, extras, primes, normal, early, pasiva "
        "FROM sql_telintec.fichajes "
        "WHERE emp_id = %s"
    )
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def get_all_fichajes():
    sql = (
        "SELECT "
        "sql_telintec.employees.name, "
        "sql_telintec.employees.l_name, "
        "sql_telintec.fichajes.ficha_id, "
        "sql_telintec.fichajes.emp_id, "
        "sql_telintec.fichajes.contract, "
        "sql_telintec.fichajes.absences, "
        "sql_telintec.fichajes.lates, "
        "sql_telintec.fichajes.extras, "
        "sql_telintec.fichajes.primes, "
        "sql_telintec.fichajes.normal, "
        "sql_telintec.fichajes.early,"
        "sql_telintec.fichajes.pasiva "
        "FROM sql_telintec.fichajes "
        "INNER JOIN sql_telintec.employees ON (sql_telintec.fichajes.emp_id = sql_telintec.employees.employee_id)"
    )
    flag, error, result = execute_sql(sql, type_sql=2)
    return flag, error, result


def get_fichaje_emp_AV(name: str, id_e: int):
    columns = (
        "id_employee",
        "absences",
        "lates",
        "lates_value[h]",
        "extras",
        "extras_value[h]",
        "primes",
    )
    sql = (
        "SELECT emp_id, absences, lates, extras, primes "
        "FROM sql_telintec.fichajes "
        "WHERE emp_id = %s"
    )
    if id_e is None:
        id_e, name_db = get_employee_id_name(name)
        if id_e is None:
            return False, "No employee in the DB", [], columns
    val = (id_e,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result, columns
