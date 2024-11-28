# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/abr./2024  at 16:40 $"

import json
from datetime import datetime

from static.constants import format_timestamps
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
        "sql_telintec.products_amc.locations "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "LEFT JOIN sql_telintec.suppliers_amc ON sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier "
        "WHERE sql_telintec.product_movements_amc.movement_type = 'entrada';"
    )
    flag, error, my_result = execute_sql(sql, None, 5)
    return flag, error, my_result


def create_in_movement_db(id_product, movement_type, quantity, movement_date, sm_id):
    insert_sql = (
        "INSERT INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    vals = (id_product, movement_type, quantity, movement_date, sm_id)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_movement_db(
    id_movement, quantity, movement_date, sm_id, type_m=None, id_product=None
):
    if type_m is not None and id_product is not None:
        update_sql = (
            "UPDATE sql_telintec.product_movements_amc "
            "SET quantity = %s, movement_date = %s, sm_id = %s , movement_type = %s, id_product = %s "
            "WHERE id_movement = %s "
        )
        vals = (quantity, movement_date, sm_id, type_m, id_product, id_movement)
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
        "sql_telintec.products_amc.locations "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "LEFT JOIN sql_telintec.suppliers_amc ON sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier "
        "WHERE sql_telintec.product_movements_amc.movement_type = 'salida';"
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
        "sql_telintec.products_amc.locations "
        "FROM sql_telintec.product_movements_amc "
        "INNER JOIN sql_telintec.products_amc ON sql_telintec.product_movements_amc.id_product = sql_telintec.products_amc.id_product "
        "LEFT JOIN sql_telintec.suppliers_amc ON sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier;"
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_movements_type_db(type_m: str):
    sql = (
        "SELECT "
        "id_movement, "
        "id_product, "
        "movement_type, "
        "quantity, "
        "movement_date, "
        "sm_id "
        "FROM sql_telintec.product_movements_amc "
        "WHERE movement_type LIKE %s "
    )
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def create_out_movement_db(id_product, movement_type, quantity, movement_date, sm_id):
    sql = (
        "INSERT  INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    vals = (id_product, movement_type, quantity, movement_date, sm_id)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def get_all_categories_db():
    sql = "SELECT  id_category, name FROM sql_telintec.product_categories_amc"
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
):
    try:
        sku = str(sku)
        name = str(name)
        udm = str(udm)
        stock = int(stock)
        id_category = int(id_category) if id_category else None
        id_supplier = int(id_supplier) if id_supplier else None
        codes = codes if codes is not None else []
        locations = (
            {"location_1": "", "location_2": ""} if locations is None else locations
        )
    except Exception as e:
        return False, str(e), None
    insert_sql = (
        "INSERT INTO sql_telintec.products_amc "
        "(sku, name, udm, stock, id_category, is_tool, is_internal, id_supplier, codes, locations) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
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
):
    try:
        sku = str(sku)
        name = str(name)
        udm = str(udm)
        stock = int(stock)
        id_category = int(id_category)
        codes = "[]" if codes is None else codes
        locations = (
            "{'location_1': " ",  'location_2': " "}"
            if locations is None
            else locations
        )
    except Exception as e:
        return False, str(e), None
    update_sql = (
        "UPDATE sql_telintec.products_amc "
        "SET sku = %s, name = %s, udm = %s, stock = %s, id_category = %s, id_supplier = %s, "
        "is_tool = %s, is_internal = %s, codes = %s, locations = %s "
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
        codes = "[]" if codes is None else codes
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
        "sql_telintec.products_amc.locations "
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
        "sql_telintec.products_amc.locations "
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
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def update_stock_db(id_product, stock):
    update_sql = (
        "UPDATE sql_telintec.products_amc " "SET stock = %s " "WHERE id_product = %s"
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
        return False, "No products to update", None
    sql = "UPDATE sql_telintec.products_amc SET stock = CASE "
    for sku, stock in zip(skus, stocks):
        sql += f"WHEN sku = '{sku}' THEN {stock} "
    sql += (
        "ELSE stock "
        "END "
        "WHERE sku IN (" + ", ".join([f"'{sku}'" for sku in skus]) + ");"
    )

    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result


def update_stock_db_ids(ids: list, stocks: list):
    if len(ids) != len(stocks) or len(ids) == 0:
        return False, "No products to update", None
    sql = "UPDATE sql_telintec.products_amc SET stock = CASE "
    try:
        for _id, stock in zip(ids, stocks):
            sql += f"WHEN id_product = '{_id}' THEN {stock} "
        sql += (
            "ELSE stock "
            "END "
            "WHERE id_product IN (" + ", ".join([f"'{_id}'" for _id in ids]) + ");"
        )
    except Exception as e:
        # noinspection PyUnboundLocalVariable
        msg_error = (
            f"Error in update_stock_db_ids: {str(e)} at id: {_id}, stock: {stock}"
        )
        return False, msg_error, None
    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result


def insert_multiple_row_products_amc(products: tuple, dict_cat=None, dict_supp=None):
    codec = "ASCII"
    if len(products) == 0:
        return False, "No products to insert", None
    sql = "INSERT INTO sql_telintec.products_amc (sku, name, udm, stock, id_category, id_supplier, is_tool, is_internal, codes, locations) VALUES "
    try:
        for index, product in enumerate(products):
            if len(product) < 10:
                codes = json.dumps([])
                locations = json.dumps({"location_1": "", "location_2": ""})
            else:
                codes = json.dumps([])
                location_1 = product[10]
                location_2 = product[11]
                locations = json.dumps(
                    {"location_1": location_1, "location_2": location_2}
                )
            sku = clean_name(product[1].encode(codec, errors="ignore").decode(codec))[0]
            name = str(product[2]).replace("'", "").replace('"', "")

            if index > 0:
                sql += ", "
            if dict_cat is not None:
                category_id = dict_cat[product[5]] if product[5] != "None" else "None"
            else:
                category_id = product[5]
            if dict_supp is not None:
                supplier_id = dict_supp[product[6]] if product[6] != "None" else "None"
            else:
                supplier_id = product[6]
            sql += f"('{str(sku.upper())}', '{str(name)}', '{product[3]}', {product[4]}, {category_id}, {supplier_id}, {product[7]}, {product[8]}, ('{codes}'), ('{locations}'))"
    except Exception as e:
        # noinspection PyUnboundLocalVariable
        msg_error = f"Error in insert_multiple_row_products_amc: {str(e)} at index: {index}, product: {product}"
        return False, msg_error, None
    sql += (
        "as new ON DUPLICATE KEY UPDATE "
        "name = new.name, "
        "udm = new.udm, stock = new.stock, "
        "id_category = new.id_category, id_supplier = new.id_supplier, "
        "is_tool = new.is_tool, is_internal = new.is_internal, "
        "codes = new.codes, locations = new.locations;"
    )

    sql = sql.replace("None", "NULL")
    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result


def update_multiple_row_products_amc(products: tuple, dict_cat=None, dict_supp=None):
    if len(products) == 0:
        return False, "No products to update", None
    try:
        sql = "INSERT INTO sql_telintec.products_amc (id_product, sku, name, udm, stock, id_category, id_supplier, is_tool, is_internal, codes, locations) VALUES "
        for index, product in enumerate(products):
            if len(product) < 10:
                codes = json.dumps([])
                locations = json.dumps({"location_1": "", "location_2": ""})
            else:
                codes = product[9]
                location_1 = product[10]
                location_2 = product[11]
                locations = json.dumps(
                    {"location_1": location_1, "location_2": location_2}
                )
            if index > 0:
                sql += ", "
            if dict_cat is not None:
                category_id = dict_cat[product[5]] if product[5] != "None" else "None"
            else:
                category_id = product[5]
            if dict_supp is not None:
                supplier_id = dict_supp[product[6]] if product[6] != "None" else "None"
            else:
                supplier_id = product[6]
            sql += f"({product[0]}, '{product[1]}', '{product[2]}', '{product[3]}', {product[4]}, {category_id}, {supplier_id}, {product[7]}, {product[8]}, ('{codes}'), ('{locations}')) "
    except Exception as e:
        # noinspection PyUnboundLocalVariable
        msg_error = f"Error in update_multiple_row_products_amc: {str(e)} at index: {index}, product: {product}"
        return False, msg_error, None
    sql += (
        "AS new ON DUPLICATE KEY UPDATE "
        "sku = new.sku, "
        "name = new.name, "
        "udm = new.udm, "
        "stock = new.stock, "
        "id_category = new.id_category, "
        "id_supplier = new.id_supplier, "
        "is_tool = new.is_tool, "
        "is_internal = new.is_internal, "
        "codes = new.codes, "
        "locations = new.locations; "
    )
    sql = sql.replace("None", "NULL")
    flag, error, result = execute_sql(sql, None, 3)
    return flag, error, result


def insert_multiple_row_movements_amc(movements: tuple):
    if len(movements) == 0:
        return False, "No movements to insert", None
    try:
        sql = "INSERT INTO sql_telintec.product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id) VALUES "
        for index, movement in enumerate(movements):
            if index > 0:
                sql += ", "
            if len(movement) < 4:
                date = datetime.now().strftime(format_timestamps)
                sm_id = "None"
            else:
                date = movement[3]
                sm_id = movement[4] if movement[4] != "None" else "None"
            sql += f"({movement[0]}, '{movement[1]}', {movement[2]}, '{date}', {sm_id})"
    except Exception as e:
        # noinspection PyUnboundLocalVariable
        msg_error = f"Error in insert_multiple_row_movements_amc: {str(e)} at index: {index}, movement: {movement}"
        return False, msg_error, None
    sql += (
        "AS new ON DUPLICATE KEY UPDATE "
        "id_product = new.id_product, "
        "movement_type = new.movement_type, "
        "quantity = new.quantity, "
        "movement_date = new.movement_date,"
        "sm_id = new.sm_id; "
    )
    sql = sql.replace("None", "NULL")
    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result


def update_multiple_products_suppliers(products: tuple):
    if len(products) == 0:
        return False, "No products to update", None
    sql = "UPDATE sql_telintec.products_amc SET id_supplier = CASE "
    for product in products:
        sql += f"WHEN sku = '{product[0]}' THEN {product[1]} "
    sql += (
        "ELSE sku "
        "END "
        "WHERE sku IN (" + ", ".join([f"'{product[0]}'" for product in products]) + ");"
    )
    sql = sql.replace("None", "NULL")
    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result


def insert_multiple_categories_amc(categories: tuple):
    if len(categories) == 0:
        return False, "No categories to insert", None
    sql = "INSERT INTO sql_telintec.product_categories_amc (name) VALUES "
    for index, category in enumerate(categories):
        if index > 0:
            sql += ", "
        sql += f"('{category}')"
    sql = sql.replace("None", "NULL")
    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result


def update_multiple_products_categories(products: tuple):
    if len(products) == 0:
        return False, "No products to update", None
    sql = "UPDATE sql_telintec.products_amc SET id_category = CASE "
    for product in products:
        sql += f"WHEN sku = '{product[0]}' THEN {product[1]} "
    sql += (
        "ELSE sku "
        "END "
        "WHERE sku IN (" + ", ".join([f"'{product[0]}'" for product in products]) + ");"
    )
    sql = sql.replace("None", "NULL")
    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result


def udpate_multiple_row_stock_ids(data):
    if len(data) == 0:
        return False, "No products to update", None
    sql = "UPDATE sql_telintec.products_amc SET stock = CASE "
    for product in data:
        sql += f"WHEN id_product = '{product[0]}' THEN {product[1]} "
    sql += (
        "ELSE id_product "
        "END "
        "WHERE id_product IN ("
        + ", ".join([f"'{product[0]}'" for product in data])
        + ");"
    )
    sql = sql.replace("None", "NULL")
    flag, error, result = execute_sql(sql, None, 4)
    return flag, error, result
