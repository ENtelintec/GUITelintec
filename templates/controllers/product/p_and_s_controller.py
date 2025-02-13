# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/abr./2024  at 16:40 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.Functions_Utils import clean_name
from templates.database.connection import execute_sql


def get_ins_db():
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
    flag, error, my_result = execute_sql(sql, None, 5)
    return flag, error, my_result


def get_ins_db_detail():
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
    flag, error, my_result = execute_sql(sql, None, 5)
    return flag, error, my_result


def create_in_movement_db(
    id_product, movement_type, quantity, movement_date, sm_id, reference=None
):
    extra_info = {"reference": reference.upper()} if reference else {"reference": ""}
    extra_info = json.dumps(extra_info) if extra_info else None
    insert_sql = (
        "INSERT INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    vals = (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_movement_db(
    id_movement,
    quantity,
    movement_date,
    sm_id,
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
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_movement_db(id_movement):
    delete_sql = "DELETE FROM sql_telintec.product_movements_amc WHERE id_movement = %s"
    vals = (id_movement,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def get_outs_db():
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
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_outs_db_detail():
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
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_movements_db_detail():
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
        "WHERE sql_telintec.product_movements_amc.movement_type like '%' ORDER BY movement_date DESC;"
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_movements_type_db(type_m: str):
    sql = (
        "SELECT "
        "id_movement, "
        "products_amc.id_product, "
        "movement_type, "
        "quantity, "
        "movement_date, "
        "sm_id, "
        "products_amc.extra_info->'$.reference', "
        "sku, "
        "suppliers_amc.name "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON (sql_telintec.products_amc.id_product = sql_telintec.product_movements_amc.id_product)"
        "INNER JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
        "WHERE movement_type LIKE %s ORDER BY movement_date DESC"
    )
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def get_movements_type_db_all():
    sql = (
        "SELECT "
        "id_movement, "
        "products_amc.id_product, "
        "movement_type, "
        "quantity, "
        "movement_date, "
        "sm_id, "
        "products_amc.extra_info->'$.reference', "
        "sku, "
        "suppliers_amc.name "
        "FROM sql_telintec.product_movements_amc "
        "LEFT JOIN sql_telintec.products_amc ON (sql_telintec.products_amc.id_product = sql_telintec.product_movements_amc.id_product)"
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
        "ORDER BY movement_date DESC LIMIT 1000"
    )
    vals = ()
    flag, error, result = execute_sql(sql, vals, 5)
    return flag, error, result


def create_out_movement_db(
    id_product, movement_type, quantity, movement_date, sm_id, reference=None
):
    extra_info = {"reference": reference.upper()} if reference else {"reference": ""}
    extra_info = json.dumps(extra_info)
    sql = (
        "INSERT  INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    vals = (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def get_all_categories_db():
    sql = (
        "SELECT  id_category, name FROM sql_telintec.product_categories_amc "
        "ORDER By name;"
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def create_category_db(name: str):
    insert_sql = "INSERT INTO sql_telintec.product_categories_amc (name) VALUES (%s)"
    vals = (name,)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_category_db(id_category, name):
    update_sql = (
        "UPDATE sql_telintec.product_categories_amc "
        "SET name = %s "
        "WHERE id_category = %s"
    )
    vals = (name, id_category)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_category_db(id_category):
    delete_sql = (
        "DELETE FROM sql_telintec.product_categories_amc " "WHERE id_category = %s"
    )
    vals = (id_category,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def get_skus():
    sql = "SELECT sku, stock, id_product FROM sql_telintec.products_amc"
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def create_product_db(
    sku,
    name,
    udm,
    stock,
    id_category,
    id_supplier,
    is_tool,
    is_internal,
    codes=None,
    locations=None,
    brand=None,
):
    try:
        sku = str(sku).upper()
        name = str(name)
        udm = str(udm)
        stock = int(stock)
        id_category = int(id_category) if id_category else None
        id_supplier = int(id_supplier) if id_supplier else None
        codes = codes if codes is not None else [{"tag": "sku_fabricante", "value": ""}]
        locations = (
            locations if locations is not None else {"location_1": "", "location_2": ""}
        )
        extra_info = {"brand": brand} if brand is not None else {"brand": ""}
    except Exception as e:
        return False, str(e), None
    insert_sql = (
        "INSERT INTO sql_telintec.products_amc "
        "(sku, name, udm, stock, id_category, is_tool, is_internal, id_supplier, codes, locations, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    vals = (
        sku,
        name,
        udm,
        stock,
        id_category,
        is_tool,
        is_internal,
        id_supplier,
        json.dumps(codes),
        json.dumps(locations),
        json.dumps(extra_info),
    )
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_product_db(
    id_product,
    sku,
    name,
    udm,
    stock,
    id_category,
    id_supplier,
    is_tool,
    is_internal,
    codes=None,
    locations=None,
    brand=None,
):
    try:
        sku = str(sku).upper()
        name = str(name)
        udm = str(udm)
        stock = float(stock)
        id_category = int(id_category) if id_category else None
        id_supplier = int(id_supplier) if id_supplier else None
        codes = codes if codes is not None else [{"tag": "sku_fabricante", "value": ""}]
        locations = (
            locations if locations is not None else {"location_1": "", "location_2": ""}
        )
        brand = brand if brand is not None else ""
    except Exception as e:
        return False, str(e), None
    update_sql = (
        "UPDATE sql_telintec.products_amc "
        "SET sku = %s, name = %s, udm = %s, stock = %s, id_category = %s, id_supplier = %s, "
        "is_tool = %s, is_internal = %s, codes = %s, locations = %s, "
        "extra_info = JSON_REPLACE(extra_info, '$.brand', %s) "
        "WHERE id_product = %s;"
    )
    vals = (
        sku,
        name,
        udm,
        stock,
        id_category,
        id_supplier,
        is_tool,
        is_internal,
        json.dumps(codes),
        json.dumps(locations),
        brand,
        id_product,
    )
    flag, error, result = execute_sql(update_sql, vals, 3)
    return flag, error, result


def create_product_db_admin(sku, name, udm, stock, id_category, codes=None):
    try:
        sku = str(sku)
        name = str(name)
        udm = str(udm)
        stock = int(stock)
        id_category = int(id_category)
        codes = codes if codes is not None else [{"tag": "sku_fabricante", "value": ""}]
    except Exception as e:
        return False, str(e), None
    insert_sql = (
        "INSERT INTO sql_telintec.products_amc "
        "(sku, name, udm, stock, id_category, codes) "
        "VALUES (%s, %s, %s, %s, %s, %s) as new "
        "ON DUPLICATE KEY UPDATE "
        "sku = new.sku, "
        "name = new.name, "
        "udm = new.udm, "
        "stock = new.stock, "
        "id_category = new.id_category, "
        "codes = new.codes; "
    )
    vals = (sku, name, udm, stock, id_category, codes)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def get_last_sku():
    sql = "SELECT sku FROM sql_telintec.products_amc ORDER BY sku DESC"
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_products_db():
    sql = (
        "SELECT "
        "sql_telintec.products_amc.id_product,"
        "sql_telintec.products_amc.sku AS sku,"
        "sql_telintec.products_amc.name AS name,"
        "sql_telintec.products_amc.udm AS udm,"
        "sql_telintec.products_amc.stock AS stock,"
        "sql_telintec.product_categories_amc.name AS category_name,"
        "sql_telintec.suppliers_amc.name AS supplier_name, "
        "sql_telintec.products_amc.is_tool,"
        "sql_telintec.products_amc.is_internal, "
        "sql_telintec.products_amc.codes,"
        "sql_telintec.products_amc.locations, "
        "sql_telintec.products_amc.extra_info->'$.brand', "
        "sql_telintec.suppliers_amc.extra_info->'$.brands' "
        "FROM sql_telintec.products_amc "
        "LEFT JOIN sql_telintec.product_categories_amc ON (sql_telintec.products_amc.id_category = sql_telintec.product_categories_amc.id_category) "
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier) "
        "ORDER BY products_amc.name "
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_products_db_tool_internal(is_tool: int, is_internal: int):
    sql = (
        "SELECT "
        "sql_telintec.products_amc.id_product,"
        "sql_telintec.products_amc.sku AS sku,"
        "sql_telintec.products_amc.name AS name,"
        "sql_telintec.products_amc.udm AS udm,"
        "sql_telintec.products_amc.stock AS stock,"
        "sql_telintec.product_categories_amc.name AS category_name,"
        "sql_telintec.suppliers_amc.name AS supplier_name, "
        "sql_telintec.products_amc.is_tool, "
        "sql_telintec.products_amc.is_internal, "
        "sql_telintec.products_amc.codes, "
        "sql_telintec.products_amc.locations, "
        "sql_telintec.products_amc.extra_info "
        "FROM sql_telintec.products_amc "
        "LEFT JOIN sql_telintec.product_categories_amc ON (sql_telintec.products_amc.id_category = sql_telintec.product_categories_amc.id_category) "
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
        "WHERE products_amc.is_internal like %s AND products_amc.is_tool like %s "
    )
    vals = (is_internal, is_tool)
    flag, error, result = execute_sql(sql, vals, 2)

    return flag, error, result


def delete_product_db(id_product):
    delete_sql = "DELETE FROM sql_telintec.products_amc " "WHERE id_product = %s"
    vals = (id_product,)
    flag, error, result = execute_sql(delete_sql, vals, 3)
    return flag, error, result


def update_stock_db(id_product, stock, just_add=False):
    if not just_add:
        update_sql = (
            "UPDATE sql_telintec.products_amc "
            "SET stock = %s "
            "WHERE id_product = %s"
        )
    else:
        update_sql = (
            "UPDATE sql_telintec.products_amc "
            "SET stock = stock + %s "
            "WHERE id_product = %s"
        )
    vals = (stock, id_product)
    flag, error, result = execute_sql(update_sql, vals, 3)
    return flag, error, result


def get_stock_db(id_product):
    sql = "SELECT stock " "FROM sql_telintec.products_amc " "WHERE id_product = %s"
    vals = (id_product,)
    flag, error, result = execute_sql(sql, vals, 1)
    return flag, error, result


def get_p_and_s(limit=(0, 100)):
    sql = (
        "SELECT product_id, name, model, marca, description, price_retail, available_quantity, "
        "price_provider, support_offered, is_service, category, image "
        "FROM sql_telintec.products_services "
        "LIMIT %s, %s"
    )
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def insert_product_and_service(
    product_id: int,
    name: str,
    model: str,
    brand: str,
    description: str,
    price_retail: str,
    quantity: str,
    price_provider: str,
    support: int,
    is_service: int,
    categories: str,
    img_url: str,
) -> tuple[bool, Exception | None, list | None]:
    sql = (
        "INSERT INTO sql_telintec.products_services (product_id, name, model, marca, description, "
        "price_retail, available_quantity, price_provider, support_offered, is_service,"
        "category, image) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        product_id,
        name,
        model,
        brand,
        description,
        price_retail,
        quantity,
        price_provider,
        str(support),
        str(is_service),
        categories,
        img_url,
    )
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in products_services.")
    return flag, None, out


def update_product_and_service(
    product_id: int,
    name: str,
    model: str,
    brand: str,
    description: str,
    price_retail: str,
    quantity: str,
    price_provider: str,
    support: int,
    is_service: int,
    categories: str,
    img_url: str,
) -> tuple[bool, Exception | None, list | None]:
    sql = (
        "UPDATE sql_telintec.products_services "
        "SET "
        "name = %s, "
        "model = %s, "
        "marca = %s, "
        "description = %s, "
        "price_retail = %s, "
        "available_quantity = %s, "
        "price_provider = %s, "
        "support_offered = %s, "
        "is_service = %s, "
        "category = %s, "
        "image = %s "
        "WHERE product_id = %s"
    )
    val = (
        name,
        model,
        brand,
        description,
        price_retail,
        quantity,
        price_provider,
        str(support),
        str(is_service),
        categories,
        img_url,
        product_id,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_product_and_service(id_ps: int):
    sql = "DELETE FROM sql_telintec.products_services " "WHERE product_id = %s"
    val = (id_ps,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_product_categories():
    columns = ("id_category", "name")
    sql = (
        "SELECT "
        "sql_telintec.product_categories_amc.id_category, "
        "sql_telintec.product_categories_amc.name "
        "FROM sql_telintec.product_categories_amc "
        "LIMIT 20 "
    )
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result, columns


def get_products_almacen(id_p: int, name: str, category: str, limit: int = 10):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    sql = (
        "SELECT "
        "id_product, "
        "name, "
        "udm, "
        "stock, "
        "id_category "
        "FROM sql_telintec.products_amc "
        "WHERE id_product = %s OR (match(name) against (%s IN NATURAL LANGUAGE MODE ) AND id_category = %s ) "
        "LIMIT %s"
    )
    val = (id_p, name, category, limit)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_high_stock_products(category: str, quantity: int):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = (
        "SELECT id_category, name "
        "FROM sql_telintec.product_categories_amc "
        "WHERE name = %s"
    )
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = (
            "SELECT id_product, name, udm, stock, id_category "
            "FROM sql_telintec.products_amc "
            "WHERE id_category = %s "
            "ORDER BY stock DESC "
            "LIMIT %s"
        )
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_low_stock_products(category: str, quantity: int):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = (
        "SELECT id_category, name "
        "FROM sql_telintec.product_categories_amc "
        "WHERE name = %s"
    )
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = (
            "SELECT id_product, name, udm, stock, id_category "
            "FROM sql_telintec.products_amc "
            "WHERE id_category = %s "
            "ORDER BY stock "
            "LIMIT %s"
        )
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_no_stock_products(category: str, quantity: int = 10):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = (
        "SELECT id_category, name "
        "FROM sql_telintec.product_categories_amc "
        "WHERE name = %s"
    )
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = (
            "SELECT id_product, name, udm, stock, id_category "
            "FROM sql_telintec.products_amc "
            "WHERE id_category = %s "
            "AND stock=0 "
            "LIMIT %s"
        )
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_product_movement_amc(type_m: str, id_m: int, id_p: int, date: str):
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
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_supply_inv_amc(id_s: int, name: str):
    columns = ("id_supply", "name", "id_supplier", "date", "status")
    sql = (
        "SELECT id_supply, name, stock "
        "FROM sql_telintec.supply_inventory_amc "
        "WHERE (id_supply = %s OR "
        "match(name) against (%s IN NATURAL LANGUAGE MODE ) ) "
        "LIMIT 10"
    )
    val = (id_s, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_sm_products():
    sql = "SELECT id_product, name, udm, stock " "FROM sql_telintec.products_amc "
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_suppliers():
    sql = (
        "SELECT id_supplier, name, seller_name, seller_email, phone, address, web_url, type "
        "FROM sql_telintec.suppliers_amc "
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_movements_type(type_m: str, limit=10):
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

    val = (type_m, limit)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result


def get_product_barcode_data(id_product):
    sql = (
        "SELECT name, sku, codes "
        "FROM sql_telintec.products_amc "
        "WHERE id_product = %s"
    )
    val = (id_product,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result


def get_stock_db_products():
    sql = (
        "SELECT id_product,stock "
        "FROM sql_telintec.products_amc "
        "WHERE products_amc.id_product like '%' "
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def update_stock_db_sku(skus: list, stocks: list):
    if len(skus) != len(stocks) or len(skus) == 0:
        return [], "No products to update", []
    flags = []
    errors = []
    results = []
    for sku, stock in zip(skus, stocks):
        sql = "UPDATE sql_telintec.products_amc " "SET stock = %s " "WHERE sku = %s"
        vals = (stock, sku)
        flag, error, result = execute_sql(sql, vals, 3)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_stock_db_ids(ids: list, stocks: list):
    if len(ids) != len(stocks) or len(ids) == 0:
        return [], "No products to update", []
    flags = []
    errors = []
    results = []
    for _id, stock in zip(ids, stocks):
        sql = (
            "UPDATE sql_telintec.products_amc "
            "SET stock = %s "
            "WHERE id_product = %s"
        )
        vals = (stock, _id)
        flag, error, result = execute_sql(sql, vals, 3)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def insert_multiple_row_products_amc(products: tuple, dict_cat=None, dict_supp=None):
    codec = "ASCII"
    if len(products) == 0:
        return [], ["No products to insert"], []
    flags = []
    errors = []
    results = []
    for index, product in enumerate(products):
        if len(product) < 10:
            codes = json.dumps([])
            locations = json.dumps({"location_1": ""})
            extra_info = json.dumps({"brand": ""})
        else:
            codes = json.dumps([])
            location_1 = product[10]
            locations = json.dumps({"location_1": location_1})
            extra_info = json.dumps({"brand": product[11]})
        sku = clean_name(product[1].encode(codec, errors="ignore").decode(codec))[0]
        name = str(product[2]).replace("'", "").replace('"', "")
        category_id = (
            dict_cat.get(product[5], None) if dict_cat is not None else product[5]
        )
        supplier_id = (
            dict_supp.get(product[6], None) if dict_supp is not None else product[6]
        )
        sql = (
            "INSERT INTO sql_telintec.products_amc "
            "(sku, name, udm, stock, id_category, is_tool, is_internal, id_supplier, codes, locations, extra_info)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) as new "
            "ON DUPLICATE KEY UPDATE "
            "sku = new.sku, name = new.name, udm = new.udm, stock = new.stock, id_category = new.id_category, "
            "is_tool = new.is_tool, is_internal = new.is_internal, id_supplier = new.id_supplier, "
            "codes = new.codes, locations = new.locations, extra_info = new.extra_info "
        )
        vals = (
            sku.upper(),
            name,
            product[3],
            product[4],
            category_id,
            product[7],
            product[8],
            supplier_id,
            codes,
            locations,
            extra_info,
        )
        flag, error, result = execute_sql(sql, vals, 4)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_multiple_row_products_amc(products: tuple, dict_cat=None, dict_supp=None):
    if len(products) == 0:
        return [], ["No products to update"], []
    flags = []
    errors = []
    results = []
    for index, product in enumerate(products):
        if len(product) < 10:
            codes = json.dumps([])
            locations = json.dumps({"location_1": ""})
            brand = ""
        else:
            codes = product[9]
            location_1 = product[10]
            locations = json.dumps({"location_1": location_1})
            brand = product[11]
        category_id = (
            dict_cat.get(product[5], "None") if dict_cat is not None else product[5]
        )
        supplier_id = (
            dict_supp.get(product[6], "None") if dict_supp is not None else product[6]
        )
        sql = (
            "UPDATE sql_telintec.products_amc "
            "SET sku = %s, name = %s, udm = %s, stock = %s, id_category = %s, id_supplier = %s, is_tool = %s, is_internal = %s, "
            "codes = %s, locations = %s, extra_info = JSON_SET(extra_info, '$.brand', %s) "
            "WHERE id_product = %s"
        )
        vals = (
            product[1].upper(),
            product[2],
            product[3],
            product[4],
            category_id,
            supplier_id,
            product[7],
            product[8],
            codes,
            locations,
            brand,
            product[0],
        )
        flag, error, result = execute_sql(sql, vals, 3)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def insert_multiple_row_movements_amc(movements: tuple):
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
        flag, error, result = execute_sql(sql, vals, 4)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_multiple_products_suppliers(products: tuple):
    if len(products) == 0:
        return [], ["No products to update"], []
    flags = []
    errors = []
    results = []
    for product in products:
        sql = (
            "UPDATE sql_telintec.products_amc " "SET id_supplier = %s " "WHERE sku = %s"
        )
        vals = (product[1], product[0])
        flag, error, result = execute_sql(sql, vals, 3)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def insert_multiple_categories_amc(categories: tuple):
    if len(categories) == 0:
        return [], ["No categories to insert"], []
    flags = []
    errors = []
    results = []
    for category in categories:
        sql = (
            "INSERT INTO sql_telintec.product_categories_amc (name) "
            "VALUES (%s) "
            "ON DUPLICATE KEY UPDATE name = %s"
        )
        vals = (category, category)
        flag, error, result = execute_sql(sql, vals, 4)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_multiple_products_categories(products: tuple):
    if len(products) == 0:
        return [], ["No products to update"], []
    flags = []
    errors = []
    results = []
    for product in products:
        sql = (
            "UPDATE sql_telintec.products_amc " "SET id_category = %s " "WHERE sku = %s"
        )
        vals = (product[1], product[0])
        flag, error, result = execute_sql(sql, vals, 3)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def udpate_multiple_row_stock_ids(data):
    if len(data) == 0:
        return [], ["No products to update"], []
    flags = []
    errors = []
    results = []
    for item in data:
        sql = (
            "UPDATE sql_telintec.products_amc "
            "SET stock = %s "
            "WHERE id_product = %s"
        )
        vals = (item[1], item[0])
        flag, error, result = execute_sql(sql, vals, 3)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results
