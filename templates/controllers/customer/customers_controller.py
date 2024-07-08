# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/abr./2024  at 17:53 $'

from templates.database.connection import execute_sql


def get_all_customers_db():
    sql = ("SELECT "
           "id_customer, "
           "name, "
           "email, "
           "phone, "
           "rfc, "
           "address "
           "FROM sql_telintec.customers_amc")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def create_customer_db(name, email, phone, rfc, address):
    insert_sql = ("INSERT INTO sql_telintec.customers_amc (name, email, phone, rfc, address) "
                  "VALUES (%s, %s, %s, %s, %s)")
    vals = (name, email, phone, rfc, address)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_customer_db(id_customer, name, email, phone, rfc, address):
    update_sql = ("UPDATE sql_telintec.customers_amc "
                  "SET name = %s, email = %s, phone = %s, rfc = %s, address = %s "
                  "WHERE id_customer = %s")
    vals = (name, email, phone, rfc, address, id_customer)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_customer_db(id_customer):
    delete_sql = ("DELETE FROM sql_telintec.customers_amc "
                  "WHERE id_customer = %s")
    vals = (id_customer,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def get_customers(limit=(0, 100)) -> list[list]:
    sql = ("SELECT customer_id, name, l_name, phone_number, city, email "
           "FROM sql_telintec.customers "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def insert_customer(name: str, lastname: str, phone: str, city: str,
                    email: str) -> tuple[bool, Exception | None, int | None]:
    sql = ("INSERT "
           "INTO sql_telintec.customers (name, l_name, phone_number, city, email) "
           "VALUES (%s, %s, %s, %s, %s)")
    val = (name, lastname, phone, city, email)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def update_customer_DB(
        name: str, lastname: str, phone: str, city: str,
        email: str, customer_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("UPDATE sql_telintec.customers "
           "SET name = %s, "
           "l_name = %s, "
           "phone_number = %s, "
           "city = %s, "
           "email = %s "
           "WHERE customer_id = %s")
    val = (name, lastname, phone, city, email, customer_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_customer_DB(customer_id: int) -> tuple[bool, Exception | None, int | None]:
    sql = ("DELETE FROM sql_telintec.customers "
           "WHERE customer_id = %s")
    val = (customer_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_costumers_amc(name: str, id_c: int):
    columns = ("id_customer", "name", "phone", "email", "address")
    sql = ("SELECT id_customer, name, phone, email, address "
           "FROM sql_telintec.customers_amc "
           "WHERE id_customer = %s OR match(name) against (%s IN NATURAL LANGUAGE MODE ) "
           "LIMIT 10")
    val = (id_c, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_sm_clients():
    sql = ("SELECT id_customer, name "
           "FROM sql_telintec.customers_amc  ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result
