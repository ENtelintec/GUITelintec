# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/abr./2024  at 16:40 $"

import json

from templates.database.connection import execute_sql


def insert_reservation_db(id_product, quantity, sm_id, history, data_token):
    sql = (
        "INSERT INTO sql_telintec.product_reservations "
        "(id_product, quantity, sm_id, status, created_at, history) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    history_dict_list = json.loads(history)
    vals = (
        id_product,
        quantity,
        sm_id,
        0,
        history_dict_list[-1].get("timestamp"),
        history,
    )
    flag, error, lastrowid = execute_sql(sql, vals, 4, data_token)
    return flag, error, lastrowid


def update_reservation_db(
    id_reservation, status, quantity, history, data_token, add_quantity=False
):
    if not add_quantity:
        sql = (
            "UPDATE sql_telintec.product_reservations "
            "SET "
            "status = %s, "
            "quantity = %s, "
            "history = %s "
            "WHERE reservation_id = %s"
        )
    else:
        sql = (
            "UPDATE sql_telintec.product_reservations "
            "SET "
            "status = %s, "
            "quantity = quantity + %s, "
            "history = %s "
            "WHERE reservation_id = %s"
        )
    vals = (status, quantity, history, id_reservation)
    flag, error, lastrowid = execute_sql(sql, vals, 3, data_token)
    return flag, error, lastrowid


def update_reservation_with_smID_db(
    id_reservation, status, quantity, history, sm_id, data_token, add_quantity=False
):
    if not add_quantity:
        sql = (
            "UPDATE sql_telintec.product_reservations "
            "SET "
            "status = %s, "
            "quantity = %s, "
            "history = %s, "
            "sm_id = %s "
            "WHERE reservation_id = %s"
        )
    else:
        sql = (
            "UPDATE sql_telintec.product_reservations "
            "SET "
            "status = %s, "
            "quantity = quantity + %s, "
            "history = %s, "
            "sm_id =%s "
            "WHERE reservation_id = %s"
        )
    vals = (status, quantity, history, sm_id, id_reservation)
    flag, error, lastrowid = execute_sql(sql, vals, 3, data_token)
    return flag, error, lastrowid


def delete_reservation_db(id_reservation, data_token):
    sql = "DELETE FROM sql_telintec.product_reservations WHERE reservation_id = %s"
    vals = (id_reservation,)
    flag, error, lastrowid = execute_sql(sql, vals, 4, data_token)
    return flag, error, lastrowid


def complete_reservation_db(id_reservation, data_token):
    sql = (
        "UPDATE sql_telintec.product_reservations "
        "SET status = 1 "
        "WHERE reservation_id = %s"
    )
    vals = (id_reservation,)
    flag, error, lastrowid = execute_sql(sql, vals, 4, data_token)
    return flag, error, lastrowid


def get_all_reservations(data_token):
    sql = (
        "SELECT "
        "sql_telintec.product_reservations.reservation_id, "
        "sql_telintec.product_reservations.id_product, "
        "sql_telintec.product_reservations.sm_id, "
        "sql_telintec.product_reservations.quantity, "
        "sql_telintec.product_reservations.status, "
        "sql_telintec.product_reservations.history, "
        "sql_telintec.materials_request.folio, "
        "sql_telintec.products_amc.name, "
        "sql_telintec.products_amc.sku "
        "FROM sql_telintec.product_reservations "
        "LEFT JOIN sql_telintec.products_amc ON (sql_telintec.product_reservations.id_product = sql_telintec.products_amc.id_product) "
        "LEFT JOIN sql_telintec.materials_request ON (sql_telintec.product_reservations.sm_id = sql_telintec.materials_request.sm_id) "
        "ORDER BY reservation_id DESC "
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result
