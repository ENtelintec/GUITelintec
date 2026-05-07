# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/abr./2024  at 16:40 $"

import json

from templates.database.connection import execute_sql
from templates.Functions_Utils import clean_name


def get_all_categories_db(data_token):
    sql = (
        "SELECT  id_category, name FROM sql_telintec.product_categories_amc "
        "ORDER By name;"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def create_category_db(name: str, data_token):
    insert_sql = "INSERT INTO sql_telintec.product_categories_amc (name) VALUES (%s)"
    vals = (name,)
    flag, error, result = execute_sql(insert_sql, vals, 4, data_token)
    return flag, error, result


def update_category_db(id_category, name, data_token):
    update_sql = (
        "UPDATE sql_telintec.product_categories_amc "
        "SET name = %s "
        "WHERE id_category = %s"
    )
    vals = (name, id_category)
    flag, error, result = execute_sql(update_sql, vals, 4, data_token)
    return flag, error, result


def delete_category_db(id_category, data_token):
    delete_sql = (
        "DELETE FROM sql_telintec.product_categories_amc WHERE id_category = %s"
    )
    vals = (id_category,)
    flag, error, result = execute_sql(delete_sql, vals, 4, data_token)
    return flag, error, result


def get_skus(data_token):
    sql = "SELECT sku, stock, id_product FROM sql_telintec.products_amc"
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def create_product_db(
    sku,
    name,
    udm,
    stock,
    id_category,
    id_supplier,
    is_tool,
    is_internal, data_token,
    codes=None,
    locations=None,
    brand=None,
    epp: int = 0,
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
        extra_info["epp"] = epp  # pyrefly: ignore
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
    flag, error, result = execute_sql(insert_sql, vals, 4, data_token)
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
    is_internal, data_token,
    codes=None,
    locations=None,
    brand=None,
    epp=0,
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
        "extra_info = JSON_SET(extra_info, '$.brand', %s), "
        "extra_info = JSON_SET(extra_info, '$.epp', %s) "
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
        epp,
        id_product,
    )
    flag, error, result = execute_sql(update_sql, vals, 3, data_token)
    return flag, error, result


def create_product_db_admin(sku, name, udm, stock, id_category, data_token, codes=None):
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
    flag, error, result = execute_sql(insert_sql, vals, 4, data_token)
    return flag, error, result


def get_last_sku(data_token):
    sql = "SELECT sku FROM sql_telintec.products_amc ORDER BY sku DESC"
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_all_products_db_old(data_token):
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
        "sql_telintec.suppliers_amc.extra_info->'$.brands', "
        "sql_telintec.products_amc.name_short "
        "FROM sql_telintec.products_amc "
        "LEFT JOIN sql_telintec.product_categories_amc ON (sql_telintec.products_amc.id_category = sql_telintec.product_categories_amc.id_category) "
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier) "
        "ORDER BY products_amc.name "
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_all_products_db_tool_internal(is_tool: int | str, is_internal: int | str, data_token):
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
        "sql_telintec.products_amc.extra_info, "
        "IFNULL(r.reserved_qty, 0) AS reserved_qty, "
        "stock - IFNULL(r.reserved_qty, 0) AS available_stock, "
        "name_short "
        "FROM sql_telintec.products_amc "
        "LEFT JOIN sql_telintec.product_categories_amc ON (sql_telintec.products_amc.id_category = sql_telintec.product_categories_amc.id_category) "
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier) "
        "LEFT JOIN ( "
        "   SELECT id_product, "
        "       SUM(quantity) AS reserved_qty "
        "   FROM sql_telintec.product_reservations"
        "   WHERE status = 0 "
        "   GROUP BY id_product) r ON sql_telintec.products_amc.id_product = r.id_product "
        "WHERE products_amc.is_internal like %s AND products_amc.is_tool like %s "
    )
    vals = (is_internal, is_tool)
    flag, error, result = execute_sql(sql, vals, 2, data_token)
    return flag, error, result


def delete_product_db(id_product, data_token):
    delete_sql = "DELETE FROM sql_telintec.products_amc WHERE id_product = %s"
    vals = (id_product,)
    flag, error, result = execute_sql(delete_sql, vals, 3, data_token)
    return flag, error, result


def update_stock_db(id_product, stock, data_token, just_add=False):
    if not just_add:
        update_sql = (
            "UPDATE sql_telintec.products_amc SET stock = %s WHERE id_product = %s"
        )
    else:
        update_sql = (
            "UPDATE sql_telintec.products_amc "
            "SET stock = stock + %s "
            "WHERE id_product = %s"
        )
    vals = (stock, id_product)
    flag, error, result = execute_sql(update_sql, vals, 3, data_token)
    return flag, error, result


def get_stock_db(id_product, data_token):
    sql = "SELECT stock, name FROM sql_telintec.products_amc WHERE id_product = %s"
    vals = (id_product,)
    flag, error, result = execute_sql(sql, vals, 1, data_token)
    return flag, error, result


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
    img_url: str, data_token,
) -> tuple[bool, str | None, int]:
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
    flag, e, out = execute_sql(sql, val, 3, data_token)
    if not isinstance(out, int):
        return flag, e, 0
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
    img_url: str, data_token,
) -> tuple[bool, str | None, int]:
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
    flag, e, out = execute_sql(sql, val, 3, data_token)
    if not isinstance(out, int):
        return flag, e, 0
    return flag, e, out


def delete_product_and_service(id_ps: int, data_token):
    sql = "DELETE FROM sql_telintec.products_services WHERE product_id = %s"
    val = (id_ps,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def get_product_categories(data_token):
    columns = ("id_category", "name")
    sql = (
        "SELECT "
        "sql_telintec.product_categories_amc.id_category, "
        "sql_telintec.product_categories_amc.name "
        "FROM sql_telintec.product_categories_amc "
        "LIMIT 20 "
    )
    flag, error, result = execute_sql(sql, type_sql=5, data_token=data_token)
    return flag, error, result, columns


def get_products_almacen(id_p: int, name: str, category: str, data_token, limit: int = 10):
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
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result, columns


def get_high_stock_products(category: str, quantity: int, data_token):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    sql = (
        "SELECT id_category, name "
        "FROM sql_telintec.product_categories_amc "
        "WHERE name = %s"
    )
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    if not isinstance(result, tuple):
        return False, "No category in the DB", [], columns
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
        flag, error, result = execute_sql(sql, val, 2, data_token)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_low_stock_products(category: str, quantity: int, data_token):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    sql = (
        "SELECT id_category, name "
        "FROM sql_telintec.product_categories_amc "
        "WHERE name = %s"
    )
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    if not isinstance(result, tuple):
        return False, "No category in the DB", [], columns
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
        flag, error, result = execute_sql(sql, val, 2, data_token)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_no_stock_products(category: str, data_token, quantity: int = 10):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    sql = (
        "SELECT id_category, name "
        "FROM sql_telintec.product_categories_amc "
        "WHERE name = %s"
    )
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    if not isinstance(result, tuple):
        return False, "No category in the DB", [], columns
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
        flag, error, result = execute_sql(sql, val, 2, data_token)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_supply_inv_amc(id_s: int, name: str, data_token):
    columns = ("id_supply", "name", "id_supplier", "date", "status")
    sql = (
        "SELECT id_supply, name, stock "
        "FROM sql_telintec.supply_inventory_amc "
        "WHERE (id_supply = %s OR "
        "match(name) against (%s IN NATURAL LANGUAGE MODE ) ) "
        "LIMIT 10"
    )
    val = (id_s, name)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result, columns


def get_products_w_reservations(data_token):
    sql = """
          SELECT
            p.id_product,
            p.name,
            p.udm,
            p.stock,
            IFNULL(r.reserved_qty, 0) AS reserved_qty,
            p.stock - IFNULL(r.reserved_qty, 0) AS available_stock,
            p.sku,
            p.codes
                FROM sql_telintec.products_amc p
                LEFT JOIN (
                    SELECT
                        id_product,
                        SUM(quantity) AS reserved_qty
                    FROM sql_telintec.product_reservations
                    WHERE status = 0 -- Solo reservas pendientes
                    GROUP BY id_product
                ) r ON p.id_product = r.id_product
           ;
          """
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_all_suppliers(data_token):
    sql = (
        "SELECT id_supplier, name, seller_name, seller_email, phone, address, web_url, type "
        "FROM sql_telintec.suppliers_amc "
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_product_barcode_data(id_product, data_token):
    sql = "SELECT name, sku, codes FROM sql_telintec.products_amc WHERE id_product = %s"
    val = (id_product,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def get_stock_db_products(data_token) -> tuple[bool, str, list]:
    sql = (
        "SELECT id_product,stock "
        "FROM sql_telintec.products_amc "
        "WHERE products_amc.id_product like '%' "
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    if not isinstance(result, list):
        return False, "No products in the DB", []
    return flag, error, result


def update_stock_db_sku(skus: list, stocks: list, data_token):
    if len(skus) != len(stocks) or len(skus) == 0:
        return [], "No products to update", []
    flags = []
    errors = []
    results = []
    for sku, stock in zip(skus, stocks):
        sql = "UPDATE sql_telintec.products_amc SET stock = %s WHERE sku = %s"
        vals = (stock, sku)
        flag, error, result = execute_sql(sql, vals, 3, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_stock_db_ids(ids: list, stocks: list, data_token):
    if len(ids) != len(stocks) or len(ids) == 0:
        return [], "No products to update", []
    flags = []
    errors = []
    results = []
    for _id, stock in zip(ids, stocks):
        sql = (
            "UPDATE sql_telintec.products_amc "
            "SET stock = stock + %s "
            "WHERE id_product = %s"
        )
        vals = (stock, _id)
        flag, error, result = execute_sql(sql, vals, 3, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def insert_multiple_row_products_amc(
    products: tuple, data_token, dict_cat=None, dict_supp=None
):
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
            extra_info = json.dumps({"brand": "", "epp": 0})
        else:
            codes = json.dumps([])
            location_1 = product[10]
            locations = json.dumps({"location_1": location_1})
            extra_info = json.dumps({"brand": product[11], "epp": product[12]})
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
        flag, error, result = execute_sql(sql, vals, 4, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_multiple_row_products_amc(
    products: tuple, data_token, dict_cat=None, dict_supp=None
):
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
            epp = 0
        else:
            codes = product[9]
            location_1 = product[10]
            locations = json.dumps({"location_1": location_1})
            brand = product[11]
            epp = product[12]
        category_id = (
            dict_cat.get(product[5], "None") if dict_cat is not None else product[5]
        )
        supplier_id = (
            dict_supp.get(product[6], "None") if dict_supp is not None else product[6]
        )
        sql = (
            "UPDATE sql_telintec.products_amc "
            "SET sku = %s, name = %s, udm = %s, stock = %s, id_category = %s, id_supplier = %s, is_tool = %s, is_internal = %s, "
            "codes = %s, locations = %s, extra_info = JSON_SET(extra_info, '$.brand', %s), extra_info = JSON_SET(extra_info, '$.epp', %s)  "
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
            epp,
            product[0],
        )
        flag, error, result = execute_sql(sql, vals, 3, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_multiple_products_suppliers(products: tuple, data_token):
    if len(products) == 0:
        return [], ["No products to update"], []
    flags = []
    errors = []
    results = []
    for product in products:
        sql = "UPDATE sql_telintec.products_amc SET id_supplier = %s WHERE sku = %s"
        vals = (product[1], product[0])
        flag, error, result = execute_sql(sql, vals, 3, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def insert_multiple_categories_amc(categories: tuple, data_token):
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
        flag, error, result = execute_sql(sql, vals, 4, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def update_multiple_products_categories(products: tuple, data_token):
    if len(products) == 0:
        return [], ["No products to update"], []
    flags = []
    errors = []
    results = []
    for product in products:
        sql = """
            UPDATE sql_telintec.products_amc
            SET id_category = %s WHERE sku = %s
            """
        vals = (product[1], product[0])
        flag, error, result = execute_sql(sql, vals, 3, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def udpate_multiple_row_stock_ids(data, data_token):
    if len(data) == 0:
        return [], ["No products to update"], []
    flags = []
    errors = []
    results = []
    for item in data:
        sql = "UPDATE sql_telintec.products_amc SET stock = %s WHERE id_product = %s"
        vals = (item[1], item[0])
        flag, error, result = execute_sql(sql, vals, 3, data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    return flags, errors, results


def get_all_epp_inventory(data_token):
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
        "sql_telintec.products_amc.extra_info, "
        "sql_telintec.products_amc.name_short "
        "FROM sql_telintec.products_amc "
        "LEFT JOIN sql_telintec.product_categories_amc ON (sql_telintec.products_amc.id_category = sql_telintec.product_categories_amc.id_category) "
        "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.products_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
        "WHERE sql_telintec.products_amc.extra_info->>'$.epp' = 1 "
        "ORDER BY name "
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_product_by_sku_manufacture(sku: str, data_token) -> tuple[bool, str, list]:
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
        "WHERE JSON_SEARCH(codes, 'one', %s, NULL, '$[*].value') IS NOT NULL "
        "ORDER BY name "
    )
    val = (sku,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    if not isinstance(result, list):
        return flag, error, []
    return flag, error, result


def get_products_stock_from_ids(ids: list, data_token):
    if len(ids) == 0:
        return [], ["No products to retrieve"], []
    sql = (
        "SELECT "
        "sql_telintec.products_amc.id_product, "
        "sql_telintec.products_amc.stock "
        "FROM sql_telintec.products_amc "
        f"WHERE sql_telintec.products_amc.id_product IN ({','.join(map(str, ids))})"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    if not isinstance(result, list):
        return flag, "Not data found or error", []
    return flag, error, result
