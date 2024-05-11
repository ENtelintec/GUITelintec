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


def create_supplier_amc(name_provider, seller_provider, email_provider, phone_provider, address_provider, web_provider, type_provider):
    name_provider = str(name_provider)
    seller_provider = str(seller_provider)
    email_provider = str(email_provider)
    phone_provider = str(phone_provider)
    address_provider = str(address_provider)
    web_provider = str(web_provider)
    type_provider = str(type_provider)
    insert_sql = ("INSERT INTO suppliers_amc "
                  "(name, seller_name, seller_email, phone, address, web_url, type) "
                  "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    vals = (name_provider, seller_provider, email_provider, phone_provider, address_provider, web_provider, type_provider)
    flag, error, result = execute_sql(insert_sql, vals, 3)
    return flag, error, result


def update_supplier_amc(id_provider, name_provider, seller_provider, email_provider, phone_provider, address_provider, web_provider, type_provider):
    update_sql = ("UPDATE suppliers_amc "
                  "SET name = %s, seller_name = %s, seller_email = %s, phone = %s, address = %s, web_url = %s, type = %s "
                  "WHERE id_supplier = %s")
    vals = (name_provider, seller_provider, email_provider, phone_provider, address_provider, web_provider, type_provider, id_provider)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result    


def delete_supplier_amc(id_supplier):
    delete_sql = ("DELETE FROM suppliers_amc "
                  "WHERE id_supplier = %s")
    vals = (id_supplier,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result
