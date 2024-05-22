# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 18:20 $'

import json

from templates.database.connection import execute_sql
from templates.controllers.employees.employees_controller import get_employee_id_name


def update_fichaje_DB(emp_id: int, contract: str, absences: dict, lates: dict, extras: dict,
                      primes: dict, normal: dict):
    sql = ("UPDATE sql_telintec.fichajes "
           "SET contract = %s, absences = %s, lates = %s, extras = %s, primes = %s, normal = %s "
           "WHERE emp_id = %s")
    val = (contract, json.dumps(absences), json.dumps(lates), json.dumps(extras),
           json.dumps(primes), json.dumps(normal), emp_id)
    flag, error, result = execute_sql(sql, val, 3)
    return flag, error, result


def insert_new_fichaje_DB(emp_id: int, contract: str, absences: dict, lates: dict, extras: dict,
                          primes: dict, normals: dict):
    sql = ("INSERT INTO sql_telintec.fichajes "
           "(emp_id, contract, absences, lates, extras, primes, normal) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    val = (emp_id, contract, json.dumps(absences), json.dumps(lates),
           json.dumps(extras), json.dumps(primes), json.dumps(normals))
    flag, error, result = execute_sql(sql, val, 4)
    return flag, error, result


def get_fichaje_DB(emp_id: int):
    sql = ("SELECT ficha_id, emp_id, contract, absences, lates, extras, primes, normal "
           "FROM sql_telintec.fichajes "
           "WHERE emp_id = %s")
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def get_all_fichajes():
    # (name, lastname, id_fich, id_emp, contract, absences, lates, extras, primes, normal)
    sql = ("SELECT employees.name, employees.l_name, "
           "fichajes.ficha_id, fichajes.emp_id, fichajes.contract, "
           "fichajes.absences, fichajes.lates, fichajes.extras, fichajes.primes, fichajes.normal "
           "FROM sql_telintec.fichajes "
           "INNER JOIN employees ON (fichajes.emp_id = employees.employee_id)")
    flag, error, result = execute_sql(sql, type_sql=2)
    return flag, error, result


def get_fichaje_emp_AV(name: str, id_e: int):
    columns = ("id_employee", "absences", "lates", "lates_value[h]", "extras", "extras_value[h]", "primes")
    sql = ("SELECT emp_id, absences, lates, extras, primes "
           "FROM fichajes WHERE emp_id = %s")
    if id_e is None:
        id_e, name_db = get_employee_id_name(name)
        if id_e is None:
            return False, "No employee in the DB", [], columns
    val = (id_e,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result, columns
