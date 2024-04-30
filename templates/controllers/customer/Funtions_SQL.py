# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/abr./2024  at 17:53 $'

from templates.Functions_SQL import execute_sql


def get_all_customers_db():
    sql = ("SELECT id_customer, name, email, phone, rfc, address "
           "FROM customers_amc")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def create_customer_db(name, email, phone, rfc, address):
    insert_sql = ("INSERT INTO customers_amc (name, email, phone, rfc, address) "
                  "VALUES (%s, %s, %s, %s, %s)")
    vals = (name, email, phone, rfc, address)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_customer_db(id_customer, name, email, phone, rfc, address):
    update_sql = ("UPDATE customers_amc "
                  "SET name = %s, email = %s, phone = %s, rfc = %s, address = %s "
                  "WHERE id_customer = %s")
    vals = (name, email, phone, rfc, address, id_customer)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_customer_db(id_customer):
    delete_sql = ("DELETE FROM customers_amc "
                  "WHERE id_customer = %s")
    vals = (id_customer,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result
