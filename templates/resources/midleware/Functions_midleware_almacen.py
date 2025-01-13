# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 15:31 $"

import json
from datetime import datetime

import pandas as pd
import pytz

from static.constants import (
    format_timestamps,
    filepath_inventory_form,
    filepath_inventory_form_movements,
    format_date,
    file_codebar,
    timezone_software,
    format_timestamps_tz,
    log_file_almacen,
    filepath_inventory_form_excel,
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
    update_stock_db_ids,
    get_product_barcode_data,
)
from templates.controllers.supplier.suppliers_controller import get_all_suppliers_amc
from templates.forms.BarCodeGenerator import (
    create_one_code,
    create_multiple_barcodes_products,
)
from templates.forms.Storage import InventoryStorage
from templates.misc.Functions_Files import write_log_file
from templates.resources.methods.Aux_Inventory import (
    generate_default_configuration_barcodes,
    create_excel_file,
)


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
        return ["error at retrieving data"], 400
    for item in result:
        id_m, id_product, type_m, quantity, movement_date, sm_id, reference = item
        reference = json.loads(reference) if reference is not None else None
        out.append(
            {
                "id": id_m,
                "id_product": id_product,
                "type_m": type_m,
                "quantity": quantity,
                "movement_date": movement_date,
                "sm_id": sm_id,
                "reference": reference,
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
                "sku": item[1],
                "name": item[2],
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
            sku=data["info"]["sku"],
            name=data["info"]["name"],
            udm=data["info"]["udm"],
            stock=data["info"]["stock"],
            id_category=data["info"]["category_name"],
            id_supplier=data["info"]["supplier_name"],
            is_tool=data["info"]["is_tool"],
            is_internal=data["info"]["is_internal"],
            codes=data["info"]["codes"],
            locations=data["info"]["locations"],
            brand=data["info"]["brand"],
        )
    else:
        flag, error, result = create_product_db_admin(
            sku=data["info"]["sku"],
            name=data["info"]["name"],
            udm=data["info"]["udm"],
            stock=data["info"]["stock"],
            id_category=data["info"]["category_name"],
            codes=data["info"]["codes"],
        )
    if not flag:
        return False, error
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, e, result = create_in_movement_db(
        result, "entrada", data["info"]["stock"], timestamp, None, "creation"
    )
    return True, result


def update_product_amc(data):
    flag, error, result = update_product_db(
        id_product=data["info"]["id"],
        sku=data["info"]["sku"],
        name=data["info"]["name"],
        udm=data["info"]["udm"],
        stock=data["info"]["stock"],
        id_category=data["info"]["category_name"],
        id_supplier=data["info"]["supplier_name"],
        is_tool=data["info"]["is_tool"],
        is_internal=data["info"]["is_internal"],
        codes=data["info"]["codes"],
        locations=data["info"]["locations"],
        brand=data["info"]["brand"],
    )
    if not flag:
        return False, error
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    if data["info"]["quantity_move"] == 0:
        return True, result
    movement_type = "entrada" if data["info"]["quantity_move"] > 0 else "salida"
    flag, e, result = create_in_movement_db(
        data["info"]["id"],
        movement_type,
        abs(data["info"]["quantity_move"]),
        timestamp,
        None,
        "update",
    )
    return True, result


def insert_multiple_products_from_api(data):
    products_new = data["products_insert"]
    data_out = {
        "inserted": [],
        "errors_insert": [],
        "errors_movements": [],
        "movements": [],
    }
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
            item["brand"],
        )
        for item in products_new
    ]
    flags, errors, lastrowids = insert_multiple_row_products_amc(tuple(products_aux))
    movements = []
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps_tz)
    for flag, error, lastrowid, item in zip(flags, errors, lastrowids, products_new):
        data_out["errors_insert"].append(
            f"Error at insert->{error}"
        ) if not flag else data_out["inserted"].append(lastrowid)
        # (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
        movements.append(
            (
                lastrowid,
                "entrada",
                item.get("stock", None),
                date,
                None,
                "creation",
            )
        ) if flag else None
    msg = f"Se insertaron {len(data_out['inserted'])} productos."
    msg += (
        f"\nHubo {len(data_out['errors_insert'])} errores al insertar productos."
        if len(data_out["errors_insert"]) > 0
        else ""
    )
    # create movements in
    flags, errors, results = insert_multiple_row_movements_amc(tuple(movements))
    for flag, error, result in zip(flags, errors, results):
        data_out["errors"].append(
            f"Error at insert movement->{error}"
        ) if not flag else data_out["movements"].append(result)
    msg += f"\nSe generaron {len(movements)} movimientos."
    msg += (
        f"\nHubo {len(data_out['errors_movements'])} errores al insertar movimientos."
        if len(data_out["errors_movements"]) > 0
        else ""
    )
    data_out["msg"] = msg
    return data_out


def update_multiple_products_from_api(data):
    products_update = data["products_update"]
    data_out = {
        "updated": [],
        "errors_update": [],
        "errors_movements": [],
        "movements": [],
    }
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
            item["brand"],
        )
        for item in products_update
    ]
    flags, errors, results = update_multiple_row_products_amc(tuple(products_aux))
    movements = []
    # date utc -6
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps_tz)
    for flag, error, result, item in zip(flags, errors, results, products_update):
        data_out["errors_update"].append(
            f"Error at update->{error}"
        ) if not flag else data_out["updated"].append(result)
        # (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
        movement_type = "entrada" if item["quantity_move"] > 0 else "salida"
        movements.append(
            (
                item["id"],
                movement_type,
                abs(item.get("quantity_move")),
                date,
                None,
                "update",
            )
        ) if flag else None
    msg = f"Se actualizaron {len(data_out['updated'])} productos."
    msg += (
        f"\nHubo {len(data_out['errors_update'])} errores al actualizar productos."
        if len(data_out["errors_update"]) > 0
        else ""
    )
    flags, errors, results = insert_multiple_row_movements_amc(tuple(movements))
    for flag, error, result in zip(flags, errors, results):
        data_out["errors_movements"].append(
            f"Error at insert movement->{error}"
        ) if not flag else data_out["movements"].append(result)
    msg += f"\nSe generaron {len(movements)} movimientos."
    msg += (
        f"\nHubo {len(data_out['errors_movements'])} errores al insertar movimientos."
        if len(data_out["errors_movements"]) > 0
        else ""
    )
    data_out["msg"] = msg
    return data_out


def insert_and_update_multiple_products_from_api(data, token_data=None):
    data_out_insert = insert_multiple_products_from_api(data)
    data_out_update = update_multiple_products_from_api(data)
    msg_notification = (
        "--System Notification--\n"
        + data_out_insert["msg"]
        + "\n"
        + data_out_update["msg"]
    )
    create_notification_permission_notGUI(
        msg_notification, ["almacen"], "Notifaction de Inventario", 0, 0
    )
    time_zone = pytz.timezone(timezone_software)
    timestamp = (
        datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps_tz)
    )
    data_out = {"insert": data_out_insert, "update": data_out_update}
    msg_notification += f"[Timestamp: {timestamp}]"
    msg_notification += f"[ID: {token_data.get('emp_id', 'No id')}]"
    write_log_file(log_file_almacen, msg_notification)
    return data_out


def insert_multiple_movements_from_api(data):
    movements = data["movements"]
    data_out = []
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps_tz)
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


def insert_new_product(new_items):
    data_out = {"inserted": [], "errors_insert": [], "movements": []}
    flags, errors, lastrowids = insert_multiple_row_products_amc(tuple(new_items))
    movements = []
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps_tz)
    for flag, error, lastrowid, item in zip(flags, errors, lastrowids, new_items):
        data_out["errors_insert"].append(
            f"Error at insert->{error}"
        ) if not flag else data_out["inserted"].append(lastrowid)
        # (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
        movements.append(
            (
                lastrowid,
                "entrada",
                item.get("stock", None),
                date,
                None,
                "creation",
            )
        ) if flag else None
    msg = f"Se insertaron {len(data_out['inserted'])} productos."
    msg += (
        f"\nHubo {len(data_out['errors_insert'])} errores al insertar productos."
        if len(data_out["errors_insert"]) > 0
        else ""
    )
    flags, errors, results = insert_multiple_row_movements_amc(tuple(movements))
    for flag, error, result in zip(flags, errors, results):
        data_out["errors"].append(
            f"Error at insert movement->{error}"
        ) if not flag else data_out["movements"].append(result)
    msg += f"\nSe generaron {len(movements)} movimientos."
    msg += (
        f"\nHubo {len(data_out['errors_movements'])} errores al insertar movimientos."
        if len(data_out["errors_movements"]) > 0
        else ""
    )
    data_out["msg"] = msg
    return data_out


def update_old_products(
    update_items, stocks_update, new_input_quantity, skus, result_sku
):
    data_out = {
        "updated": [],
        "errors_update": [],
        "movements": [],
        "errors_movements": [],
    }
    flags, errors, results = update_stock_db_sku(update_items, stocks_update)
    movements = []
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps_tz)
    for flag, error, result, item in zip(
        flags, errors, results, update_items, new_input_quantity
    ):
        data_out["errors_update"].append(
            f"Error at update->{error}"
        ) if not flag else data_out["updated"].append(result)
        # (id_product, movement_type, quantity, movement_date, sm_id, extra_info)
        movement_type = "entrada" if item["quantity_move"] > 0 else "salida"
        movements.append(
            (
                result_sku[skus.index(str(item))][2],
                movement_type,
                abs(item.get["quantity_move"]),
                date,
                None,
                "update",
            )
        ) if flag else None

    msg = f"Se actualizaron {len(data_out['updated'])} productos."
    msg += (
        f"\nHubo {len(data_out['errors_update'])} errores al actualizar productos."
        if len(data_out["errors_update"]) > 0
        else ""
    )
    flags, errors, results = insert_multiple_row_movements_amc(tuple(movements))
    for flag, error, result in zip(flags, errors, results):
        data_out["errors_movements"].append(
            f"Error at insert movement->{error}"
        ) if not flag else data_out["movements"].append(result)
    msg += f"\nSe generaron {len(movements)} movimientos."
    msg += (
        f"\nHubo {len(data_out['errors_movements'])} errores al insertar movimientos."
        if len(data_out["errors_movements"]) > 0
        else ""
    )
    data_out["msg"] = msg
    return data_out


def upload_product_db_from_file(
    file: str, is_internal=0, is_tool=False, token_data=None
):
    (new_items, update_items, stocks_update, new_input_quantity, result_sku, skus) = (
        read_excel_file_regular(file, is_tool, is_internal)
    )

    data_out_insert = insert_new_product(new_items)
    data_out_update = update_old_products(
        update_items, stocks_update, new_input_quantity, skus, result_sku
    )
    msg_notification = (
        "--System Notification--\n"
        + data_out_insert["msg"]
        + "\n"
        + data_out_update["msg"]
    )
    create_notification_permission_notGUI(
        msg_notification, ["almacen"], "Notification de Inventario", 0, 0
    )
    time_zone = pytz.timezone(timezone_software)
    timestamp = (
        datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps_tz)
    )
    data_out = {"insert": data_out_insert, "update": data_out_update}
    msg_notification += f"[Timestamp: {timestamp}]"
    msg_notification += f"[ID: {token_data.get('emp_id', 'No id')}]"
    write_log_file(log_file_almacen, msg_notification)
    return data_out


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
    flag, error, result = get_all_suppliers_amc()
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
            extra_info,
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
    df = pd.read_excel(file, skiprows=[0, 1, 2, 3, 4], sheet_name="PRODUCTOS")
    df = df.fillna("")
    items = df.values.tolist()
    flag, error, result_sku = get_skus()
    skus = [sku[0] for sku in result_sku]
    flag, error, suppliers = get_all_suppliers_amc()
    dict_suppliers = {supplier[1]: supplier[0] for supplier in suppliers}
    flag, error, categories = get_all_categories_db()
    dict_categories = {category[1]: category[0] for category in categories}
    new_items = []
    update_items = []
    stocks_update = []
    new_input_quantity = []
    for item in items:
        if str(item[0]) not in skus:
            tool = 0 if not is_tool else 1
            codes = [{"tag": "sku_fabricante", "value": str(item[0])}]
            new_items.append(
                (
                    None,
                    str(item[8]),
                    item[2],
                    item[3],
                    float(item[6]) if item[6] != "" else 0,
                    dict_categories.get(item[4], None),
                    dict_suppliers.get(item[1], None),
                    tool,
                    is_internal,
                    codes,
                    str(item[7]),
                    " ",
                )
            )
        else:
            index = skus.index(str(item[0]))
            stock_old = result_sku[index][1]
            update_items.append(item[0])
            stocks_update.append(item[6] + stock_old)
            new_input_quantity.append(item[6])
    return new_items, update_items, stocks_update, new_input_quantity, result_sku, skus


def retrieve_data_file_inventory(type_data="dict", data=None):
    flag, error, _products = get_all_products_db() if data is None else True, None, data
    if not flag:
        return error, 400
    try:
        # [id_product, sku, name, udm, stock, category_name, supplier_name,  is_tool, is_internal,  codes, locations,  brand, brands]
        # sort by ID
        _products.sort(key=lambda x: x[0])
        if type_data == "dict":
            products = {
                "id": [],
                "sku": [],
                "name": [],
                "udm": [],
                "stock": [],
                "category_name": [],
                "supplier_name": [],
                "is_tool": [],
                "is_internal": [],
                "codes": [],
                "locations": [],
                "brand": [],
            }
            for item in _products:
                products["id"].append(item[0])
                products["sku"].append(item[1])
                products["name"].append(item[2])
                products["udm"].append(item[3])
                products["stock"].append(item[4])
                products["category_name"].append(item[5])
                products["supplier_name"].append(item[6])
                products["is_tool"].append(item[7])
                products["is_internal"].append(item[8])
                products["codes"].append(item[9])
                products["locations"].append(item[10])
                products["brand"].append(item[11])
        elif "list":
            products = [
                (item[0], item[2], item[3], item[5], " ", item[4], " ")
                for item in _products
            ]
    except Exception as e:
        print(e)
        return None, 400
    return products, 200


def create_file_inventory_pdf():
    products, code = retrieve_data_file_inventory(type_data="list")
    if code != 200:
        return None, 400
    flag = InventoryStorage(
        dict_data={"filename_out": filepath_inventory_form, "products": products},
        type_form="Materials",
    )
    return (filepath_inventory_form, 200) if flag else (None, 400)


def create_file_inventory_excel():
    products, code = retrieve_data_file_inventory()
    if code != 200:
        return None, 400
    try:
        create_excel_file(products, filepath_inventory_form_excel)
    except Exception as e:
        print(e)
        return str(e), 400
    return filepath_inventory_form_excel, 200


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


def create_pdf_barcode_multiple(data):
    if len(data) <= 0:
        return "No data to print", 400
    general_format = data.get("format", {})
    name_list = []
    sku_list = []
    code_list = []
    for index, item in enumerate(data):
        name_list.append(item["format"].get("name", f"No Name {index}"))
        sku_list.append(item["format"].get("sku", f"No SKU {index}"))
        code_list.append(item["format"].get("code", f"No Code {index}"))
    if len(general_format) == 0:
        kw, values = generate_default_configuration_barcodes()
    else:
        kw, values = generate_default_configuration_barcodes(**general_format)
    create_multiple_barcodes_products(code_list, sku_list, name_list, **kw)
    return kw.get("filepath", file_codebar), 200
