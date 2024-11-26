# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 15:31 $"

import json
from datetime import datetime

import pandas as pd

from static.constants import (
    format_timestamps,
    filepath_inventory_form,
    filepath_inventory_form_movements,
    format_date, file_codebar,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.product.p_and_s_controller import (
    get_movements_type_db,
    create_out_movement_db,
    create_in_movement_db,
    get_stock_db,
    update_movement_db,
    update_stock_db,
    get_all_products_db_tool_internal,
    create_product_db,
    update_product_db,
    get_all_categories_db,
    get_all_suppliers,
    create_product_db_admin,
    get_skus,
    insert_multiple_row_products_amc,
    update_stock_db_sku,
    insert_multiple_row_movements_amc,
    get_all_products_db,
    get_ins_db_detail,
    get_outs_db_detail,
    get_all_movements_db_detail,
    update_multiple_row_products_amc,
    update_stock_db_ids, get_product_barcode_data,
)
from templates.forms.BarCodeGenerator import create_one_code
from templates.forms.Storage import InventoryStorage
from templates.resources.methods.Aux_Inventory import generate_default_configuration_barcodes


def get_all_movements(type_m: str):
    if "salida" in type_m:
        type_m = "salida"
    elif "entrada" in type_m:
        type_m = "entrada"
    else:
        type_m = "%"
    flag, error, result = get_movements_type_db(type_m)
    out = []
    if not flag:
        return [], 400
    for item in result:
        id_m, id_product, type_m, quantity, movement_date, sm_id = item
        out.append(
            {
                "id": id_m,
                "id_product": id_product,
                "type_m": type_m,
                "quantity": quantity,
                "movement_date": movement_date,
                "sm_id": sm_id,
            }
        )
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
        flag, e, result = create_out_movement_db(
            data["info"]["id_product"],
            type_m,
            data["info"]["quantity"],
            data["info"]["movement_date"],
            data["info"]["sm_id"],
        )
    else:
        flag, e, result = create_in_movement_db(
            data["info"]["id_product"],
            type_m,
            data["info"]["quantity"],
            data["info"]["movement_date"],
            data["info"]["sm_id"],
        )
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
        return False, str(
            error
        ) + f" -No se encontro el producto {data['info']['id_product']}- " + str(
            actual_stock
        )
    quantity = data["info"]["quantity"]
    p_quantity = data["info"]["previous_q"]
    if data["info"]["sm_id"] == 0:
        data["info"]["sm_id"] = None
    flag, e, result = update_movement_db(
        data["id"],
        data["info"]["quantity"],
        data["info"]["movement_date"],
        data["info"]["sm_id"],
        type_m,
        data["info"]["id_product"],
    )
    if not flag:
        return False, e
    flag, error, result = update_stock_db(
        data["info"]["id_product"], actual_stock[0] - quantity + p_quantity
    )
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
    else:
        is_tool = "%"
        is_internal = "%"
    flag, error, result = get_all_products_db_tool_internal(is_tool, is_internal)
    if not flag:
        return [], 400
    out = []
    for item in result:
        # (id_product, sku, name, udm, stock, category_name, supplier_name, is_tool, is_internal, codes) = item
        codes_raw = json.loads(item[9])
        if isinstance(codes_raw, list):
            codes = codes_raw
        elif isinstance(codes_raw, dict):
            codes = [{"tag": k, "value": v} for k, v in codes_raw.items()]
        else:
            codes = []
        locations = json.loads(item[10])
        out.append(
            {
                "id": item[0],
                "name": item[1],
                "sku": item[2],
                "udm": item[3],
                "stock": item[4],
                "category_name": item[5],
                "supplier_name": item[6],
                "is_tool": item[7],
                "is_internal": item[8],
                "codes": codes,
                "locations": locations,
            }
        )
    return out, 200


def insert_product_db(data):
    if data["info"]["supplier_name"] is not None:
        flag, error, result = create_product_db(
            data["info"]["sku"],
            data["info"]["name"],
            data["info"]["udm"],
            data["info"]["stock"],
            data["info"]["category_name"],
            data["info"]["supplier_name"],
            data["info"]["is_tool"],
            data["info"]["is_internal"],
        )
    else:
        flag, error, result = create_product_db_admin(
            data["info"]["sku"],
            data["info"]["name"],
            data["info"]["udm"],
            data["info"]["stock"],
            data["info"]["category_name"],
        )
    if not flag:
        return False, error
    timestamp = datetime.now().strftime(format_timestamps)
    flag, e, result = create_in_movement_db(
        result, "entrada", data["info"]["stock"], timestamp, None
    )
    return True, result


def update_product_amc(data):
    flag, error, result = update_product_db(
        data["info"]["id"],
        data["info"]["sku"],
        data["info"]["name"],
        data["info"]["udm"],
        data["info"]["stock"],
        data["info"]["category_name"],
        data["info"]["supplier_name"],
        data["info"]["is_tool"],
        data["info"]["is_internal"],
    )
    if not flag:
        return False, error
    timestamp = datetime.now().strftime(format_timestamps)
    if data["info"]["quantity_move"] == 0:
        return True, result
    flag, e, result = create_in_movement_db(
        data["info"]["id"], "entrada", data["info"]["quantity_move"], timestamp, None
    )
    return True, result


def insert_and_update_multiple_products_amc(data):
    products_new = data["products_insert"]
    products_update = data["products_update"]
    data_out = []
    products_aux = [
        (
            None,
            item["sku"],
            item["name"],
            item["udm"],
            item["stock"],
            item["category_name"],
            item["supplier_name"],
            item["is_tool"],
            item["is_internal"],
            item["codes"],
            item["locations"],
        )
        for item in products_new
    ]
    flag, error, lastrowid = insert_multiple_row_products_amc(tuple(products_aux))
    if not flag:
        data_out.append(
            f"Insert multiple rows failed. Error: {str(error)}. Result: {lastrowid}"
        )
    else:
        data_out.append(f"Insert multiple rows success. Result: {lastrowid}")
        n_products = len(products_new)
        # (id_product, movement_type, quantity, movement_date, sm_id)
        movements = [
            (
                lastrowid - n_products + index + 1,
                "entrada",
                item["stock"],
                datetime.now().strftime(format_timestamps),
                None,
            )
            for index, item in enumerate(products_new)
        ]
        flag, error, result = insert_multiple_row_movements_amc(tuple(movements))
        if not flag:
            data_out.append(
                f"Insert multiple movements failed. Error: {str(error)}. Result: {result}"
            )
        else:
            data_out.append(f"Insert multiple movements success. Result: {result}")
    products_aux = [
        (
            item["id"],
            item["sku"],
            item["name"],
            item["udm"],
            item["stock"],
            item["category_name"],
            item["supplier_name"],
            item["is_tool"],
            item["is_internal"],
            item["codes"],
            item["locations"],
        )
        for item in products_update
    ]
    flag, error, result = update_multiple_row_products_amc(tuple(products_aux))
    if not flag:
        data_out.append(
            f"Update multiple rows failed. Error: {str(error)}. Result: {result}"
        )
    else:
        data_out.append(f"Update multiple rows success. Result: {result}")
        n_products = len(products_update)
        # (id_product, movement_type, quantity, movement_date, sm_id)
        movements = [
            (
                item["id"],
                "entrada" if item["quantity_move"] > 0 else "salida",
                abs(item["quantity_move"]),
                datetime.now().strftime(format_timestamps),
                None,
            )
            for item in products_update
        ]
        flag, error, result = insert_multiple_row_movements_amc(tuple(movements))
        if not flag:
            data_out.append(
                f"Insert multiple movements failed. Error: {str(error)}. Result: {result}"
            )
        else:
            data_out.append(f"Insert multiple movements success. Result: {result}")
    msg_notification = "--System Notification--\n" + "\n".join(data_out)
    create_notification_permission_notGUI(
        msg_notification, ["almacen"], "Notifaction de Inventario", 0, 0
    )
    return True, data_out


def insert_multiple_movements(data):
    movements = data["movements"]
    data_out = []
    date = datetime.now().strftime(format_timestamps)
    movements_aux = [
        (item["id_product"], item["type_m"], item["quantity"], date, item["sm_id"])
        for item in movements
    ]
    flag, error, result = insert_multiple_row_movements_amc(tuple(movements_aux))
    if not flag:
        data_out.append(
            f"Insert multiple movements failed. Error: {str(error)}. Result: {result}"
        )
    else:
        data_out.append(f"Insert multiple movements success. Result: {result}")
        stock_update = [
            (
                item["id_product"],
                item["quantity"] + item["old_stock"]
                if item["type_m"] == "entrada"
                else item["old_stock"] - item["quantity"],
            )
            for item in movements
        ]
        flag, error, result = update_stock_db_ids(
            stock_update[0, :], stock_update[1, :]
        )
        if not flag:
            data_out.append(
                f"Update stock failed. Error: {str(error)}. Result: {result}"
            )
        else:
            data_out.append(f"Update stock success. Result: {result}")
    msg_notification = "--System Notification--\n" + "\n".join(data_out)
    create_notification_permission_notGUI(
        msg_notification, ["almacen"], "Notifaction de Movimientos", 0, 0
    )
    return True, data_out


def get_categories_db():
    flag, error, result = get_all_categories_db()
    if not flag:
        return [], 400
    out = []
    for item in result:
        id_category, name = item
        out.append(
            {
                "id": id_category,
                "name": name,
            }
        )
    return 200, out


def get_suppliers_db():
    flag, error, result = get_all_suppliers()
    if not flag:
        return [], 400
    out = []
    for item in result:
        (
            id_supplier,
            name,
            seller_name,
            seller_email,
            phone,
            address,
            web_url,
            type_s,
        ) = item
        out.append(
            {
                "id": id_supplier,
                "name": name,
                "seller_name": seller_name,
                "seller_email": seller_email,
                "phone": phone,
                "address": address,
                "web_url": web_url,
                "type": type_s,
            }
        )
    return 200, out


def read_excel_file_regular(file: str, is_tool=False, is_internal=0):
    df = pd.read_excel(file, skiprows=[0, 1, 2, 3], sheet_name="PRODUCTOS")
    df = df.fillna("")
    items = df.values.tolist()
    flag, error, result_sku = get_skus()
    skus = [sku[0] for sku in result_sku]
    new_items = []
    update_items = []
    stocks_update = []
    new_input_quantity = []
    for item in items:
        if str(item[0]) not in skus:
            tool = 0 if not is_tool else 1
            new_items.append(
                (
                    None,
                    str(item[0]),
                    item[1],
                    item[2],
                    item[6],
                    None,
                    None,
                    tool,
                    is_internal,
                )
            )
        else:
            index = skus.index(str(item[0]))
            stock_old = result_sku[index][1]
            update_items.append(item[0])
            stocks_update.append(item[6] + stock_old)
            new_input_quantity.append(item[6])
    return new_items, update_items, stocks_update, new_input_quantity, result_sku, skus


def upload_product_db_from_file(file: str, is_internal=0, is_tool=False):
    (new_items, update_items, stocks_update, new_input_quantity, result_sku, skus) = (
        read_excel_file_regular(file, is_tool, is_internal)
    )
    data_result = {}
    flag, error, result = insert_multiple_row_products_amc(tuple(new_items))
    data_result["new"] = str(error) if not flag else new_items
    movements = []
    for item in new_items:
        movements.append((item[1], "entrada", item[4]))
    flag, error, result = insert_multiple_row_movements_amc(tuple(movements))
    if flag:
        msg = f"Se crearon nuevos items y movimientos de entrada al inventario.\nf{new_items}"
        create_notification_permission_notGUI(
            msg,
            ["Almacen"],
            "Nuevos items y movimientos de entrada.",
            0,
            0,
        )
    data_result["new_notification"] = flag
    flag, error, result = update_stock_db_sku(update_items, stocks_update)
    data_result["update"] = str(error) if not flag else update_items
    movements = []
    for item, quantity in zip(update_items, new_input_quantity):
        id_product = result_sku[skus.index(str(item))][2]
        movements.append((id_product, "entrada", quantity))
    flag, error, result = insert_multiple_row_movements_amc(tuple(movements))
    if flag:
        msg = f"Se actualizó stock de items al inventario.\nf{update_items}"
        create_notification_permission_notGUI(
            msg,
            ["Almacen"],
            "Actualizacion de items y movimientos de entrada",
            0,
            0,
        )
    data_result["update_notification"] = flag
    return 200, data_result


def create_file_inventory():
    flag, error, _products = get_all_products_db()
    try:
        products = [
            (item[0], item[2], item[3], item[5], " ", item[4], " ")
            for item in _products
        ]
    except Exception as e:
        print(e)
        return None, 400
    # sort by ID
    products.sort(key=lambda x: x[0])
    flag = InventoryStorage(
        dict_data={"filename_out": filepath_inventory_form, "products": products},
        type_form="Materials",
    )
    return (filepath_inventory_form, 200) if flag else (None, 400)


def create_file_movements_amc(data):
    type_m = data["type"]
    match type_m:
        case "entrada":
            flag, error, _movements = get_ins_db_detail()
        case "salida":
            flag, error, _movements = get_outs_db_detail()
        case _:
            flag, error, _movements = get_all_movements_db_detail()

    date_init = datetime.strptime(data["date_init"], format_date)
    date_end = datetime.strptime(data["date_end"], format_date)
    try:
        movements = []
        for item in _movements:
            date = item[5]
            if date < date_init or date > date_end:
                continue
            movements.append(
                (
                    item[2],
                    date.strftime(format_date),
                    item[7],
                    item[8],
                    item[9],
                    f"{item[3]}: {item[4]}",
                    item[6],
                    "",
                    f"{json.loads(item[10])['location_1']}: {json.loads(item[10])['location_2']}",
                )
            )
    except Exception as e:
        print(e)
        return None, 400
    # sort by ID
    movements.sort(key=lambda x: x[1])
    flag = InventoryStorage(
        dict_data={
            "filename_out": filepath_inventory_form_movements,
            "products": movements,
        },
        type_form="Movements",
    )
    return (filepath_inventory_form_movements, 200) if flag else (None, 400)


def create_pdf_barcode(data):
    id_product = data.get("id_product", 0)
    format_dict = data.get("format", {})
    if format_dict == {}:
        flag, error, result = get_product_barcode_data(id_product)
        codes = json.loads(result[2])
        codigo = codes[0].get("value", "None") if len(codes) > 0 else "None"
        kw, values = generate_default_configuration_barcodes(
            name=result[0], code=result[1], sku=codigo
        )
    else:
        kw, values = generate_default_configuration_barcodes(**format_dict)
    create_one_code(**kw)
    return kw.get("filepath", file_codebar), 200
