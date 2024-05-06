# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 03/may./2024  at 15:31 $'

from templates.controllers.product.p_and_s_controller import get_movements_type_db, create_out_movement_db, \
    create_in_movement_db, get_stock_db, update_movement_db, update_stock_db, get_all_products_db_tool_internal, \
    create_product_db, update_product_db, get_all_categories_db, get_all_suppliers


def get_all_movements(type_m: str):
    if "salida" in type_m:
        type_m = "salida"
    elif "entrada" in type_m:
        type_m = "entrada"
    else:
        type_m = "%"
    print(type_m)
    flag, error, result = get_movements_type_db(type_m)
    out = []
    if not flag:
        return [], 400
    for item in result:
        id_m, id_product, type_m, quantity, movement_date, sm_id = item
        out.append({"id": id_m,
                    "id_product": id_product,
                    "type_m": type_m,
                    "quantity": quantity,
                    "movement_date": movement_date,
                    "sm_id": sm_id
                    })
    return out, 200


def insert_movement(data):
    type_m = data["info"]["type_m"]
    if "salida" in type_m:
        type_m = "salida"
    elif "entrada" in type_m:
        type_m = "entrada"
    else:
        return False, "Invalid type"
    if type_m == "salida":
        flag, e, result = create_out_movement_db(data["info"]["id_product"], type_m, data["info"]["quantity"],
                                                 data["info"]["movement_date"], data["info"]["sm_id"])
    else:
        flag, e, result = create_in_movement_db(data["info"]["id_product"], type_m, data["info"]["quantity"],
                                                data["info"]["movement_date"], data["info"]["sm_id"])
    if not flag:
        return False, e
    return True, result


def update_movement(data):
    type_m = data["info"]["type_m"]
    if "salida" in type_m:
        type_m = "salida"
    elif "entrada" in type_m:
        type_m = "entrada"
    else:
        return False, "Invalid type"
    flag, error, actual_stock = get_stock_db(data["info"]["id_product"])
    if not flag or isinstance(actual_stock, list):
        return False, error + " " + actual_stock
    print(actual_stock)
    quantity = data["info"]["quantity"]
    p_quantity = data["info"]["previous_q"]
    flag, e, result = update_movement_db(data["id"], data["info"]["quantity"], data["info"]["movement_date"],
                                         data["info"]["sm_id"], type_m, data["info"]["id_product"])
    if not flag:
        return False, e
    flag, error, result = update_stock_db(data["info"]["id_product"], actual_stock[0] - quantity + p_quantity)
    if not flag:
        return False, e
    return True, result


def get_all_products_DB(type_p):
    is_tool = 0
    is_internal = 0
    if "tool" in type_p:
        is_tool = 1
    elif "internal" in type_p:
        is_internal = 1
    flag, error, result = get_all_products_db_tool_internal(is_tool, is_internal)
    if not flag:
        return [], 400
    out = []
    for item in result:
        id_product, sku, name, udm, stock, category_name, supplier_name, is_tool, is_internal = item
        out.append({"id": id_product,
                    "name": name,
                    "sku": sku,
                    "udm": udm,
                    "stock": stock,
                    "category_name": category_name,
                    "supplier_name": supplier_name,
                    "is_tool": is_tool,
                    "is_internal": is_internal
                    })
    return out, 200


def insert_product_db(data):
    flag, error, result = create_product_db(data["info"]["sku"], data["info"]["name"], data["info"]["udm"],
                                            data["info"]["stock"], data["info"]["category_name"],
                                            data["info"]["supplier_name"], data["info"]["is_tool"],
                                            data["info"]["is_internal"])
    if not flag:
        return False, error
    return True, result


def update_product_amc(data):
    flag, error, result = update_product_db(data["id"], data["info"]["sku"], data["info"]["name"], data["info"]["udm"],
                                            data["info"]["stock"], data["info"]["category_name"],
                                            data["info"]["supplier_name"], data["info"]["is_tool"],
                                            data["info"]["is_internal"])
    if not flag:
        return False, error
    return True, result


def get_categories_db():
    flag, error, result = get_all_categories_db()
    if not flag:
        return [], 400
    out = []
    for item in result:
        id_category, name = item
        out.append({
            "id": id_category,
            "name": name,
        })
    return 200, out


def get_suppliers_db():
    flag, error, result = get_all_suppliers()
    if not flag:
        return [], 400
    out = []
    for item in result:
        id_supplier, name, seller_name, seller_email, phone, address, web_url, type_s = item
        out.append({
            "id": id_supplier,
            "name": name,
            "seller_name": seller_name,
            "seller_email": seller_email,
            "phone": phone,
            "address": address,
            "web_url": web_url,
            "type": type_s
        })
    return 200, out
