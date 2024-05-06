# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/abr./2024  at 16:40 $'

from templates.database.connection import execute_sql


def get_ins_db():
    sql = ("SELECT product_movements_amc.id_movement, "
           "product_movements_amc.id_product, "
           "product_movements_amc.movement_type, "
           "product_movements_amc.quantity, "
           "product_movements_amc.movement_date, "
           "product_movements_amc.sm_id, "
           "products_amc.name as product_name "
           "FROM product_movements_amc "
           "JOIN products_amc ON product_movements_amc.id_product = products_amc.id_product "
           "WHERE product_movements_amc.movement_type = 'entrada'")
    flag, error, my_result = execute_sql(sql, None, 5)
    return flag, error, my_result


def create_in_movement_db(id_product, movement_type, quantity, movement_date, sm_id):
    insert_sql = (
        "INSERT INTO product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    vals = (id_product, movement_type, quantity, movement_date, sm_id)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_movement_db(id_movement, quantity, movement_date, sm_id, type_m=None, id_product=None):
    update_sql = ("UPDATE product_movements_amc "
                  "SET quantity = %s, movement_date = %s, sm_id = %s , id_product = %s, movement_type = %s "
                  "WHERE id_movement = %s ")
    vals = (quantity, movement_date, sm_id, type_m, id_product, id_movement)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_movement_db(id_movement):
    delete_sql = "DELETE FROM product_movements_amc WHERE id_movement = %s"
    vals = (id_movement,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def get_outs_db():
    sql = ("SELECT "
           "product_movements_amc.id_movement, "
           "product_movements_amc.id_product, "
           "product_movements_amc.movement_type, "
           "product_movements_amc.quantity, "
           "product_movements_amc.movement_date, "
           "product_movements_amc.sm_id, "
           "products_amc.name as product_name "
           "FROM product_movements_amc "
           "JOIN products_amc ON product_movements_amc.id_product = products_amc.id_product "
           "WHERE product_movements_amc.movement_type = 'salida'")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_movements_type_db(type_m: str):
    sql = ("SELECT "
           "id_movement, "
           "id_product, "
           "movement_type, "
           "quantity, "
           "movement_date, "
           "sm_id "
           "FROM product_movements_amc "
           "WHERE movement_type LIKE %s ")
    vals = (type_m,)
    flag, error, result = execute_sql(sql, vals, 2)
    return flag, error, result


def create_out_movement_db(id_product, movement_type, quantity, movement_date, sm_id):
    sql = ("INSERT  INTO product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id) "
           "VALUES (%s, %s, %s, %s, %s)")
    vals = (id_product, movement_type, quantity, movement_date, sm_id)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def get_all_categories_db():
    sql = ("SELECT  id_category, name "
           "FROM product_categories_amc")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def create_category_db(name: str):
    insert_sql = "INSERT INTO product_categories_amc (name) VALUES (%s)"
    vals = (name,)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def update_category_db(id_category, name):
    update_sql = "UPDATE product_categories_amc SET name = %s WHERE id_category = %s"
    vals = (name, id_category)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_category_db(id_category):
    delete_sql = "DELETE FROM product_categories_amc WHERE id_category = %s"
    vals = (id_category,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def create_product_db(sku, name, udm, stock, id_category, id_supplier, is_tool, is_internal):
    sku = str(sku)
    name = str(name)
    udm = str(udm)
    stock = int(stock)
    id_category = int(id_category)
    id_supplier = int(id_supplier)
    insert_sql = ("INSERT INTO products_amc "
                  "(sku, name, udm, stock, id_category) "
                  "VALUES (%s, %s, %s, %s, %s)")
    vals = (sku, name, udm, stock, id_category)
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def get_all_products_db():
    sql = ("SELECT "
           "sql_telintec.products_amc.id_product,"
           "sql_telintec.products_amc.sku AS sku,"
           "sql_telintec.products_amc.name AS name,"
           "sql_telintec.products_amc.udm AS udm,"
           "sql_telintec.products_amc.stock AS stock,"
           "sql_telintec.product_categories_amc.name AS category_name,"
           "sql_telintec.suppliers_amc.name AS supplier_name "
           "FROM sql_telintec.products_amc "
           "LEFT JOIN sql_telintec.supplier_product_amc ON (sql_telintec.products_amc.id_product = sql_telintec.supplier_product_amc.id_product) "
           "LEFT JOIN sql_telintec.product_categories_amc ON (sql_telintec.products_amc.id_category = sql_telintec.product_categories_amc.id_category) "
           "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.supplier_product_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_products_db_tool_internal(is_tool: int, is_internal: int):
    sql = ("SELECT "
           "sql_telintec.products_amc.id_product,"
           "sql_telintec.products_amc.sku AS sku,"
           "sql_telintec.products_amc.name AS name,"
           "sql_telintec.products_amc.udm AS udm,"
           "sql_telintec.products_amc.stock AS stock,"
           "sql_telintec.product_categories_amc.name AS category_name,"
           "sql_telintec.suppliers_amc.name AS supplier_name, "
           "sql_telintec.products_amc.is_tool AS is_tool, "
           "sql_telintec.products_amc.is_internal AS is_internal "
           "FROM sql_telintec.products_amc "
           "LEFT JOIN sql_telintec.supplier_product_amc ON (sql_telintec.products_amc.id_product = sql_telintec.supplier_product_amc.id_product) "
           "LEFT JOIN sql_telintec.product_categories_amc ON (sql_telintec.products_amc.id_category = sql_telintec.product_categories_amc.id_category) "
           "LEFT JOIN sql_telintec.suppliers_amc ON (sql_telintec.supplier_product_amc.id_supplier = sql_telintec.suppliers_amc.id_supplier)"
           "WHERE products_amc.is_internal like %s AND products_amc.is_tool like %s ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def update_product_db(id_product, sku, name, udm, stock, id_category, id_supplier, is_tool=0, is_internal=0):
    update_sql = ("UPDATE products_amc "
                  "SET sku = %s, name = %s, udm = %s, stock = %s, id_category = %s, id_supplier = %s , is_tool = %s, is_internal = %s "
                  "WHERE id_product = %s")
    vals = (sku, name, udm, stock, id_category, id_supplier, is_tool, is_internal, id_product)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_product_db(id_product):
    delete_sql = ("DELETE FROM products_amc "
                  "WHERE id_product = %s")
    vals = (id_product,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def update_stock_db(id_product, stock):
    update_sql = ("UPDATE products_amc "
                  "SET stock = %s "
                  "WHERE id_product = %s")
    vals = (stock, id_product)
    flag, error, result = execute_sql(update_sql, vals, 3)
    return flag, error, result


def get_stock_db(id_product):
    sql = ("SELECT stock "
           "FROM products_amc "
           "WHERE id_product = %s")
    vals = (id_product,)
    flag, error, result = execute_sql(sql, vals, 1)
    return flag, error, result


def get_p_and_s(limit=(0, 100)):
    sql = ("SELECT product_id, name, model, marca, description, price_retail, available_quantity, "
           "price_provider, support_offered, is_service, category, image "
           "FROM sql_telintec.products_services "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def insert_product_and_service(product_id: int, name: str, model: str, brand: str,
                               description: str, price_retail: str, quantity: str,
                               price_provider: str,
                               support: int, is_service: int, categories: str,
                               img_url: str) -> tuple[bool, Exception | None, list | None]:
    sql = ("INSERT INTO sql_telintec.products_services (product_id, name, model, marca, description, "
           "price_retail, available_quantity, price_provider, support_offered, is_service,"
           "category, image) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    val = (product_id, name, model, brand, description, price_retail, quantity,
           price_provider, str(support), str(is_service), categories, img_url)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in products_services.")
    return flag, None, out


def update_product_and_service(product_id: int, name: str, model: str, brand: str,
                               description: str, price_retail: str, quantity: str,
                               price_provider: str,
                               support: int, is_service: int, categories: str,
                               img_url: str) -> tuple[bool, Exception | None, list | None]:
    sql = ("UPDATE sql_telintec.products_services "
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
           "WHERE product_id = %s")
    val = (name, model, brand, description, price_retail, quantity, price_provider,
           str(support), str(is_service), categories, img_url, product_id)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_product_and_service(id_ps: int):
    sql = ("DELETE FROM sql_telintec.products_services "
           "WHERE product_id = %s")
    val = (id_ps,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_product_categories():
    columns = ("id_category", "name")
    sql = ("SELECT "
           "product_categories_amc.id_category, "
           "product_categories_amc.name "
           "FROM product_categories_amc "
           "LIMIT 20 ")
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result, columns


def get_products_almacen(id_p: int, name: str, category: str, limit: int = 10):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    sql = ("SELECT "
           "id_product, "
           "name, "
           "udm, "
           "stock, "
           "id_category "
           "FROM products_amc "
           "WHERE id_product = %s OR (match(name) against (%s IN NATURAL LANGUAGE MODE ) AND id_category = %s ) "
           "LIMIT %s")
    val = (id_p, name, category, limit)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_high_stock_products(category: str, quantity: int):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = ("SELECT id_category, name "
           "FROM product_categories_amc "
           "WHERE name = %s")
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = ("SELECT id_product, name, udm, stock, id_category "
               "FROM products_amc "
               "WHERE id_category = %s "
               "ORDER BY stock DESC "
               "LIMIT %s")
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_low_stock_products(category: str, quantity: int):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = ("SELECT id_category, name "
           "FROM product_categories_amc "
           "WHERE name = %s")
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = ("SELECT id_product, name, udm, stock, id_category "
               "FROM products_amc "
               "WHERE id_category = %s "
               "ORDER BY stock "
               "LIMIT %s")
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_no_stock_products(category: str, quantity: int = 10):
    columns = ("id_product", "name", "udm", "stock", "id_category")
    # get category
    sql = ("SELECT id_category, name "
           "FROM product_categories_amc "
           "WHERE name = %s")
    val = (category.lower(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) > 0:
        category_id = result[0]
        sql = ("SELECT id_product, name, udm, stock, id_category "
               "FROM products_amc "
               "WHERE id_category = %s "
               "AND stock=0 "
               "LIMIT %s")
        val = (category_id, quantity)
        flag, error, result = execute_sql(sql, val, 2)
        return flag, error, result, columns
    else:
        return False, "No category in the DB", [], columns


def get_product_movement_amc(type_m: str, id_m: int, id_p: int, date: str):
    columns = ("id_movement", "id_product", "type", "quantity", "date")
    sql = ("SELECT id_movement, id_product, movement_type, quantity, movement_date "
           "FROM product_movements_amc "
           "WHERE (id_movement = %s OR "
           "id_product = %s) AND movement_type LIKE %s ")
    if date is not None:
        sql = sql + " AND movement_date = %s"
    sql = sql + " LIMIT 10"
    val = (id_m, id_p, type_m, date)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_supply_inv_amc(id_s: int, name: str):
    columns = ("id_supply", "name", "id_supplier", "date", "status")
    sql = ("SELECT id_supply, name, stock "
           "FROM supply_inventory_amc "
           "WHERE (id_supply = %s OR "
           "match(name) against (%s IN NATURAL LANGUAGE MODE ) ) "
           "LIMIT 10")
    val = (id_s, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_sm_products():
    sql = ("SELECT id_product, name, udm, stock "
           "FROM products_amc ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_suppliers():
    sql = ("SELECT id_supplier, name, seller_name, seller_email, phone, address, web_url, type "
           "FROM suppliers_amc ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result
