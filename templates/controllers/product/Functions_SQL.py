# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/abr./2024  at 16:40 $'

from templates.Functions_SQL import execute_sql


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


def update_in_movement_db(id_movement, quantity, movement_date, sm_id):
    update_sql = ("UPDATE product_movements_amc "
                  "SET quantity = %s, movement_date = %s, sm_id = %s "
                  "WHERE id_movement = %s ")
    vals = (quantity, movement_date, sm_id, id_movement)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result


def delete_in_movement_db(id_movement):
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


def create_out_movement_db(id_product, movement_type, quantity, movement_date, sm_id):
    sql = ("INSERT  INTO product_movements_amc (id_product, movement_type, quantity, movement_date, sm_id) "
           "VALUES (%s, %s, %s, %s, %s)")
    vals = (id_product, movement_type, quantity, movement_date, sm_id)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def update_out_movement_db(id_movement, quantity, movement_date):
    sql = ("UPDATE product_movements_amc "
           "SET quantity = %s, movement_date = %s "
           "WHERE id_movement = %s ")
    vals = (quantity, movement_date, id_movement)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def delete_out_movement_db(id_movement):
    sql = "DELETE FROM product_movements_amc WHERE id_movement = %s"
    vals = (id_movement,)
    flag, error, result = execute_sql(sql, vals, 4)
    return flag, error, result


def get_all_categories_db():
    sql = "SELECT  id_category, name FROM product_categories_amc"
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


def create_product_db(sku, name, udm, stock, id_category, id_supplier):
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


def update_product_db(id_product, sku, name, udm, stock, id_category, id_supplier):
    update_sql = ("UPDATE products_amc "
                  "SET sku = %s, name = %s, udm = %s, stock = %s, id_category = %s "
                  "WHERE id_product = %s")
    vals = (sku, name, udm, stock, id_category, id_product)
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
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result
