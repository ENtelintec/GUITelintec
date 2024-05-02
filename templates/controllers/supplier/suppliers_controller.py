# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:30 $'

from templates.database.connection import execute_sql


def get_supplier(limit=(0, 100)) -> list[list]:
    sql = ("SELECT supplier_id, name, location "
           "FROM sql_telintec.suppliers "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def insert_supplier(name: str, location: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT INTO sql_telintec.suppliers (name, location) "
           "VALUES (%s, %s)")
    val = (name, location)
    flag, e, out = execute_sql(sql, val, 4)
    print(out, "record inserted.")
    return flag, None, out


def update_supplier_DB(name: str, location: str, supplier_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("UPDATE sql_telintec.suppliers "
           "SET name = %s, location = %s "
           "WHERE supplier_id = %s")
    val = (name, location, supplier_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_supplier_DB(supplier_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("DELETE FROM sql_telintec.suppliers "
           "WHERE supplier_id = %s")
    val = (supplier_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_supplier_amc(name: str, id_s: int):
    columns = ("id_supplier", "name", "phone", "type", "address")
    sql = ("SELECT id_supplier, name, phone, type, address "
           "FROM suppliers_amc "
           "WHERE id_supplier = %s OR "
           "match(name) against (%s IN NATURAL LANGUAGE MODE ) "
           "LIMIT 10")
    val = (id_s, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns
