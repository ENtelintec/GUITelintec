# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/abr./2024  at 16:40 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def get_ins_db(data_token):
    sql = (
        "SELECT "
        "sql_telintec.product_movements_amc.id_movement, "
        "sql_telintec.product_movements_amc.id_product, "
        "sql_telintec.product_movements_amc.movement_type, "
        "sql_telintec.product_movements_amc.quantity, "
        "sql_telintec.product_movements_amc.movement_date, "
        "sql_telintec.product_movements_amc.sm_id, "
        "sql_telintec.products_amc.name as product_name "
        "FROM sql_telintec.product_movements_amc "
        "JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "WHERE sql_telintec.product_movements_amc.movement_type = 'entrada'"
    )
    flag, error, my_result = execute_sql(sql, None, 5, data_token)
    return flag, error, my_result


def get_ins_db_detail(data_token):
    sql = (
        "SELECT "
        "sql_telintec.product_movements_amc.id_movement, "
        "sql_telintec.product_movements_amc.id_product, "
        "sql_telintec.products_amc.sku, "
        "sql_telintec.product_movements_amc.movement_type, "
        "sql_telintec.product_movements_amc.quantity, "
        "sql_telintec.product_movements_amc.movement_date, "
        "sql_telintec.product_movements_amc.sm_id, "
        "sql_telintec.products_amc.name as product_name, "
        "sql_telintec.products_amc.udm, "
        "sql_telintec.suppliers_amc.name AS supplier_name,"
        "sql_telintec.products_amc.locations, "
        "sql_telintec.product_movements_amc.extra_info->'$.reference' "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "LEFT JOIN sql_telintec.suppliers_amc ON sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier "
        "WHERE sql_telintec.product_movements_amc.movement_type = 'entrada' ORDER BY movement_date DESC;"
    )
    flag, error, my_result = execute_sql(sql, None, 5, data_token)
    return flag, error, my_result


def create_in_movement_db(
    id_product, movement_type, quantity, movement_date, sm_id, data_token, reference=None
):
    extra_info = {"reference": reference.upper()} if reference else {"reference": ""}
    extra_info = json.dumps(extra_info) if extra_info else None
    insert_sql = (
        "INSERT INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    vals = (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
    flag, error, result = execute_sql(insert_sql, vals, 4, data_token)
    return flag, error, result


def update_movement_db(
    id_movement,
    quantity,
    movement_date,
    sm_id, data_token,
    type_m=None,
    id_product=None,
    reference=None,
):
    reference = reference if reference is not None else ""
    if type_m is not None and id_product is not None and reference is not None:
        update_sql = (
            "UPDATE sql_telintec.product_movements_amc "
            "SET quantity = %s, movement_date = %s, sm_id = %s , movement_type = %s, id_product = %s , "
            "extra_info = JSON_REPLACE(extra_info, '$.reference', %s) "
            "WHERE id_movement = %s "
        )
        vals = (
            quantity,
            movement_date,
            sm_id,
            type_m,
            id_product,
            reference.upper(),
            id_movement,
        )
    elif type_m is not None:
        update_sql = (
            "UPDATE sql_telintec.product_movements_amc "
            "SET quantity = %s, movement_date = %s, sm_id = %s , movement_type = %s "
            "WHERE id_movement = %s "
        )
        vals = (quantity, movement_date, sm_id, type_m, id_movement)
    elif id_product is not None:
        update_sql = (
            "UPDATE sql_telintec.product_movements_amc "
            "SET quantity = %s, movement_date = %s, sm_id = %s , id_product = %s "
            "WHERE id_movement = %s "
        )
        vals = (quantity, movement_date, sm_id, id_product, id_movement)
    elif reference is not None:
        update_sql = (
            "UPDATE sql_telintec.product_movements_amc "
            "SET quantity = %s, movement_date = %s, sm_id = %s , "
            "extra_info = JSON_REPLACE(extra_info, '$.reference', %s) "
            "WHERE id_movement = %s "
        )
        vals = (quantity, movement_date, sm_id, reference.upper(), id_movement)
    else:
        update_sql = (
            "UPDATE sql_telintec.product_movements_amc "
            "SET quantity = %s, movement_date = %s, sm_id = %s "
            "WHERE id_movement = %s "
        )
        vals = (quantity, movement_date, sm_id, id_movement)
    flag, error, result = execute_sql(update_sql, vals, 4, data_token)
    return flag, error, result


def delete_movement_db(id_movement, data_token):
    delete_sql = "DELETE FROM sql_telintec.product_movements_amc WHERE id_movement = %s"
    vals = (id_movement,)
    flag, error, result = execute_sql(delete_sql, vals, 4, data_token)
    return flag, error, result


def get_outs_db(data_token):
    sql = (
        "SELECT "
        "sql_telintec.product_movements_amc.id_movement, "
        "sql_telintec.product_movements_amc.id_product, "
        "sql_telintec.product_movements_amc.movement_type, "
        "sql_telintec.product_movements_amc.quantity, "
        "sql_telintec.product_movements_amc.movement_date, "
        "sql_telintec.product_movements_amc.sm_id, "
        "sql_telintec.products_amc.name as product_name "
        "FROM sql_telintec.product_movements_amc "
        "JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "WHERE sql_telintec.product_movements_amc.movement_type = 'salida'"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_outs_db_detail(data_token):
    sql = (
        "SELECT "
        "sql_telintec.product_movements_amc.id_movement, "
        "sql_telintec.product_movements_amc.id_product,"
        "sql_telintec.products_amc.sku, "
        "sql_telintec.product_movements_amc.movement_type, "
        "sql_telintec.product_movements_amc.quantity, "
        "sql_telintec.product_movements_amc.movement_date, "
        "sql_telintec.product_movements_amc.sm_id, "
        "sql_telintec.products_amc.name as product_name, "
        "sql_telintec.products_amc.udm, "
        "sql_telintec.suppliers_amc.name AS supplier_name,"
        "sql_telintec.products_amc.locations, "
        "sql_telintec.product_movements_amc.extra_info->'$.reference' "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "LEFT JOIN sql_telintec.suppliers_amc ON sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier "
        "WHERE sql_telintec.product_movements_amc.movement_type = 'salida' ORDER BY movement_date DESC;"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_all_movements_db_detail(data_token, type_m="all"):
    type_m = type_m if type_m in ["entrada", "salida"] else "%"
    sql = (
        "SELECT "
        "sql_telintec.product_movements_amc.id_movement, "
        "sql_telintec.product_movements_amc.id_product, "
        "sql_telintec.products_amc.sku, "
        "sql_telintec.product_movements_amc.movement_type, "
        "sql_telintec.product_movements_amc.quantity, "
        "sql_telintec.product_movements_amc.movement_date, "
        "sql_telintec.product_movements_amc.sm_id, "
        "sql_telintec.products_amc.name as product_name,"
        "sql_telintec.products_amc.udm, "
        "sql_telintec.suppliers_amc.name AS supplier_name, "
        "sql_telintec.products_amc.locations, "
        "sql_telintec.product_movements_amc.extra_info->'$.reference' "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "LEFT JOIN sql_telintec.suppliers_amc ON sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier "
        "WHERE sql_telintec.product_movements_amc.movement_type like %s ORDER BY movement_date DESC;"
    )
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    return flag, error, result


def get_movements_type_db(type_m: str, data_token):
    sql = (
        "SELECT "
        "id_movement, "
        "products_amc.id_product, "
        "movement_type, "
        "quantity, "
        "movement_date, "
        "sm_id, "
        "product_movements_amc.extra_info->'$.reference', "
        "sku, "
        "suppliers_amc.name, "
        "products_amc.codes "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON (sql_telintec.products_amc.id_product = sql_telintec.product_movements_amc.id_product)"
        "INNER JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
        "WHERE movement_type LIKE %s ORDER BY movement_date DESC"
    )
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    return flag, error, result


def get_movements_type_db_all(data_token, type_m="all"):
    type_m = type_m if type_m in ["entrada", "salida"] else "%"
    sql = (
        "SELECT "
        "id_movement, "
        "products_amc.id_product, "
        "movement_type, "
        "quantity, "
        "movement_date, "
        "sm_id, "
        "sql_telintec.product_movements_amc.extra_info->'$.reference', "
        "sku, "
        "suppliers_amc.name,"
        "products_amc.codes, "
        "products_amc.name as product_name "
        "FROM sql_telintec.product_movements_amc "
        "LEFT JOIN sql_telintec.products_amc ON (sql_telintec.products_amc.id_product = sql_telintec.product_movements_amc.id_product)"
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
        "WHERE movement_type LIKE %s "
        "ORDER BY movement_date DESC"
    )
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    return flag, error, result


def get_epp_movements_db(type_m, data_token):
    if type_m in ["salida", "entrada"]:
        type_m = type_m
    else:
        type_m = "%"
    sql = (
        "SELECT "
        "id_movement, "
        "products_amc.id_product, "
        "movement_type, "
        "quantity, "
        "movement_date, "
        "sm_id, "
        "sql_telintec.product_movements_amc.extra_info->'$.reference', "
        "sku, "
        "suppliers_amc.name, "
        "products_amc.codes "
        "FROM sql_telintec.product_movements_amc "
        "LEFT JOIN sql_telintec.products_amc ON (sql_telintec.products_amc.id_product = sql_telintec.product_movements_amc.id_product)"
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
        "WHERE movement_type LIKE %s AND sql_telintec.products_amc.extra_info->>'$.epp' = 1 "
        "ORDER BY movement_date DESC"
    )
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    return flag, error, result


def get_epp_movements_db_detail(type_m, data_token):
    type_m = type_m if type_m in ["entrada", "salida"] else "%"
    sql = (
        "SELECT "
        "sql_telintec.product_movements_amc.id_movement, "
        "sql_telintec.product_movements_amc.id_product, "
        "sql_telintec.products_amc.sku, "
        "sql_telintec.product_movements_amc.movement_type, "
        "sql_telintec.product_movements_amc.quantity, "
        "sql_telintec.product_movements_amc.movement_date, "
        "sql_telintec.product_movements_amc.sm_id, "
        "sql_telintec.products_amc.name as product_name,"
        "sql_telintec.products_amc.udm, "
        "sql_telintec.suppliers_amc.name AS supplier_name, "
        "sql_telintec.products_amc.locations, "
        "sql_telintec.product_movements_amc.extra_info->'$.reference' "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "LEFT JOIN sql_telintec.suppliers_amc ON sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier "
        "WHERE sql_telintec.product_movements_amc.movement_type like %s AND sql_telintec.products_amc.extra_info->>'$.epp' = 1 "
        "ORDER BY movement_date DESC;"
    )
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    return flag, error, result


def create_movement_db_amc(
    id_product,
    movement_type,
    quantity,
    movement_date,
    sm_id, data_token,
    reference=None,
    type_m=None,
):
    extra_info = {"reference": reference.upper()} if reference else {"reference": ""}
    extra_info = json.dumps(extra_info)
    sql = (
        "INSERT  INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    vals = (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
    flag, error, result = execute_sql(sql, vals, 4, data_token)
    return flag, error, result


def get_product_movement_amc(type_m: str, id_m: int, id_p: int, date: str, data_token):
    columns = ("id_movement", "id_product", "type", "quantity", "date")
    sql = (
        "SELECT id_movement, id_product, movement_type, quantity, movement_date "
        "FROM sql_telintec.product_movements_amc "
        "WHERE (id_movement = %s OR "
        "id_product = %s) AND movement_type LIKE %s "
    )
    if date is not None:
        sql = sql + " AND movement_date = %s"
    sql = sql + " LIMIT 10"
    val = (id_m, id_p, type_m, date)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result, columns


def get_movements_type(type_m: str, data_token, limit=10):
    sql = (
        "SELECT sql_telintec.product_movements_amc.id_product, "
        "cast(sum(sql_telintec.product_movements_amc.quantity) as float) as total_move, "
        "sql_telintec.products_amc.name, "
        "sql_telintec.products_amc.udm "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON (sql_telintec.products_amc.id_product = sql_telintec.product_movements_amc.id_product) "
        "WHERE movement_type LIKE %s "
        "GROUP BY id_product "
        "ORDER BY total_move "
        "LIMIT %s "
    )
    val = (type_m, limit, data_token)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


def insert_multiple_row_movements_amc(movements: tuple, data_token):
    if len(movements) == 0:
        return [], ["No movements to insert"], []
    flags = []
    errors = []
    results = []
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    for index, movement in enumerate(movements):
        if len(movement) < 4:
            sm_id = "None"
            extra_info = json.dumps({"reference": ""})
        else:
            sm_id = movement[4] if movement[4] != "None" else "None"
            extra_info = json.dumps({"reference": movement[5]})
        sql = (
            "INSERT  INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id, extra_info) "
            "VALUES (%s, %s, %s, %s, %s, %s);"
        )
        vals = (movement[0], movement[1], movement[2], date, sm_id, extra_info)
        flag, error, result = execute_sql(sql, vals, 4, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results
