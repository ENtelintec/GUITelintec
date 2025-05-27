# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/dic/2024  at 12:10 $"

import json
import math
import os
import tempfile
from datetime import datetime

import pandas as pd
import pytz

from static.constants import (
    log_file_sm_path,
    format_timestamps,
    timezone_software,
    dict_depts_identifiers,
    tabs_sm,
    format_date,
)
from templates.Functions_Utils import create_notification_permission
from templates.controllers.contracts.contracts_controller import (
    get_contract_by_client,
    get_contracts_by_ids,
    get_items_contract_string,
)
from templates.controllers.customer.customers_controller import create_customer_db
from templates.controllers.departments.heads_controller import (
    check_if_gerente,
    check_if_head_not_auxiliar,
    check_if_leader,
    check_if_auxiliar_with_contract,
)
from templates.controllers.employees.employees_controller import get_emp_contract
from templates.controllers.index import DataHandler
from templates.controllers.material_request.sm_controller import (
    get_sm_entries,
    update_history_sm,
    get_sm_by_id,
    get_info_names_by_sm_id,
    update_history_extra_info_sm_by_id,
    update_history_items_sm,
)
from templates.controllers.product.p_and_s_controller import (
    get_sm_products,
    create_product_db_admin,
    create_product_db,
    get_products_stock_from_ids,
)
from templates.forms.StorageMovSM import FileSmPDF
from templates.misc.Functions_Files import write_log_file


def get_products_sm(contract: str):
    flag, error, contract = get_items_contract_string(contract)
    if len(contract) > 0:
        items_contract = json.loads(contract[3]) if contract[3] is not None else []
    else:
        items_contract = []
    ids_in_contract = {}
    for item in items_contract:
        if item["id"] is None:
            continue
        ids_in_contract[item["id"]] = item["partida"]
    flag, error, result = get_sm_products()
    if not flag:
        return {"data": {"contract": [], "normal": []}}, 400
    items_normal = []
    items_partida = []
    for item in result:
        if item[0] in ids_in_contract.keys():
            items_partida.append(
                {
                    "id": item[0],
                    "name": item[1],
                    "udm": item[2],
                    "stock": item[3],
                    "partida": ids_in_contract[item[0]],
                }
            )
        else:
            items_normal.append(
                {
                    "id": item[0],
                    "name": item[1],
                    "udm": item[2],
                    "stock": item[3],
                    "partida": "",
                }
            )
    data_out = {"data": {"contract": items_partida, "normal": items_normal}}
    return data_out, 200


def get_all_sm(limit, page=0, emp_id=-1):
    flag, error, result = get_sm_entries(emp_id)
    if limit == -1:
        limit = len(result) + 1
    limit = limit if limit > 0 else 10
    page = page if page >= 0 else 0
    if len(result) <= 0:
        return {"data": [], "page": 0, "pages": 0}, 200
    pages = math.floor(len(result) / limit)
    if page > pages:
        return None, 204
    items = []
    if pages == 0:
        limit_up = len(result)
        limit_down = 0
    else:
        limit_down = limit * page
        limit_up = limit * (page + 1)
        limit_up = limit_up if limit_up < len(result) else len(result)
    for i in range(limit_down, limit_up):
        products = json.loads(result[i][10])
        new_products = []
        if products is not None:
            for product in products:
                if product.get("id", 0) == -1:
                    new_products.append(product)
        extra_info = json.loads(result[i][14])
        # time_zone = pytz.timezone(timezone_software)
        # date_now = datetime.now(pytz.utc).astimezone(time_zone)
        #  kpi warehouse
        admin_not_date = extra_info.get("admin_notification_date", "")
        admin_not_date = (
            datetime.strptime(admin_not_date, format_date)
            if admin_not_date != ""
            and isinstance(admin_not_date, str)
            and admin_not_date is not None
            else None
        )
        date_creation = (
            datetime.strptime(result[i][8], format_timestamps)
            if result[i][8] != "" and isinstance(result[i][8], str)
            else result[i][8]
        )
        if admin_not_date is not None:
            kpi_warehouse = (
                "CUMPLE" if (admin_not_date - date_creation).days <= 2 else "NO CUMPLE"
            )
        else:
            kpi_warehouse = ""
        # operation kpi
        critical_date = (
            datetime.strptime(result[i][9], format_timestamps)
            if result[i][9] != "" and isinstance(result[i][9], str)
            else result[i][9]
        )
        op_not_date = extra_info.get("operations_notification_date", "")
        op_not_date = (
            datetime.strptime(op_not_date, format_date)
            if op_not_date != ""
            and isinstance(op_not_date, str)
            and op_not_date is not None
            else None
        )
        if op_not_date is not None:
            kpi_operations = (
                "CUMPLE" if (critical_date - critical_date).days >= 1 else "NO CUMPLE"
            )
        else:
            kpi_operations = ""
        dict_sm = {
            "id": result[i][0],
            "folio": result[i][1],
            "contract": result[i][2],
            "facility": result[i][3],
            "location": result[i][4],
            "client_id": result[i][5],
            "emp_id": result[i][6],
            "order_quotation": result[i][7],
            "date": result[i][8].strftime(format_timestamps)
            if isinstance(result[i][8], datetime)
            else result[i][8],
            "critical_date": result[i][9].strftime(format_timestamps)
            if isinstance(result[i][9], datetime)
            else result[i][9],
            "items": json.loads(result[i][10]),
            "items_new": new_products,
            "status": result[i][11],
            "history": json.loads(result[i][12]),
            "comment": result[i][13],
            "destination": extra_info.get("destination", "Not found"),
            "contract_contact": extra_info.get("contract_contact", "Not Found"),
            # Nuevos campos agregados
            "project": extra_info.get("project", ""),
            "urgent": extra_info.get("urgent", 0),
            "activity_description": extra_info.get("activity_description", ""),
            "requesting_user_status": extra_info.get("requesting_user_status", 0),
            "warehouse_reviewed": extra_info.get("warehouse_reviewed", 0),
            "warehouse_status": extra_info.get("warehouse_status", 1),
            "admin_notification_date": extra_info.get("admin_notification_date", ""),
            "kpi_warehouse": kpi_warehouse,
            "warehouse_comments": extra_info.get("warehouse_comments", ""),
            "admin_reviewed": extra_info.get("admin_reviewed", 0),
            "admin_status": extra_info.get("admin_status", 1),
            "warehouse_notification_date": extra_info.get(
                "warehouse_notification_date", ""
            ),
            # "purchasing_kpi": extra_info.get("purchasing_kpi", 0),
            "admin_comments": extra_info.get("admin_comments", ""),
            "general_request_status": extra_info.get("general_request_status", 1),
            "operations_notification_date": extra_info.get(
                "operations_notification_date", ""
            ),
            "operations_kpi": kpi_operations,
            "requesting_user_state": extra_info.get("requesting_user_state", ""),
        }

        # if isinstance(extra_info, dict):
        #     for k, v in extra_info.items():
        #         dict_sm[k] = v
        items.append(dict_sm)
    data_out = {"data": items, "page": page, "pages": pages + 1}
    return data_out, 200


def get_department_identifiers(department_id, result, flag_creation=False):
    match department_id:
        case 1:
            return [1]  # Dirección
        case 2:
            return (
                [2001]
                if "seguridad" in result[1].lower()
                else [2]
                if "director" in result[1].lower()
                else []
            )
        case 3:  # Administración
            return (
                [3001]
                if "almacen" in result[1].lower()
                else [3002]
                if "ti" in result[1].lower()
                else [3004]
                if "medición" in result[1].lower()
                else list(dict_depts_identifiers.keys())
                if not flag_creation
                else [3, 3001, 3002, 3003, 3004]
            )
        case 4:
            return [4]  # RH
        case _:
            return [department_id]  # Default


def get_iddentifiers_creation(data_token):
    permissions = data_token.get("permissions", {}).values()
    ids_identtifier = []
    contracts = []
    # if any("administrator" in item.lower().split(".")[-1] for item in permissions):
    if any(
        word in item.lower().split(".")[-1]
        for word in ["administrator"]
        for item in permissions
    ):
        ids_identtifier = list(dict_depts_identifiers.keys())
        flag, error, contracts = get_contract_by_client(40)
    else:
        for check_func in (check_if_gerente, check_if_head_not_auxiliar):
            flag, error, result = check_func(data_token.get("emp_id"))
            if flag and result:
                ids_identtifier = get_department_identifiers(
                    data_token.get("dep_id"), result, True
                )
                break
        for check_func in (check_if_leader,):
            flag, error, result = check_func(data_token.get("emp_id"))
            if flag and len(result) > 0:
                ids = []
                for item in result:
                    extra_info = json.loads(item[7])
                    ids += extra_info.get("contracts", [])
                    ids += extra_info.get("contracts_temp", [])
                ids = list(set(ids))
                flag, error, contracts = get_contracts_by_ids(ids)
                if not flag:
                    return {"data": None, "msg": str(error)}, 400
                break
    identifiers = [
        dict_depts_identifiers.get(dept_id)
        for dept_id in ids_identtifier
        if dict_depts_identifiers.get(dept_id)
    ]
    identifier_list = [
        item
        for sublist in identifiers
        for item in (sublist if isinstance(sublist, list) else [sublist])
    ]
    for result in contracts:
        metadata = json.loads(result[1])
        contract_number = metadata["contract_number"]
        idn_contract = contract_number[-4:]
        if str(idn_contract) not in identifier_list:
            identifier_list.append(f"{idn_contract}")
    if not identifier_list:
        return {"data": None, "msg": "Folios for user not found"}, 200
    return identifier_list, 200


def get_iddentifiers(data_token):
    permissions = data_token.get("permissions", {}).values()
    ids_identtifier = []
    contracts = []
    # if any("administrator" in item.lower().split(".")[-1] for item in permissions):
    if any(
        word in item.lower().split(".")[-1]
        for word in ["administrator", "almacen"]
        for item in permissions
    ):
        ids_identtifier = list(dict_depts_identifiers.keys())
        flag, error, contracts = get_contract_by_client(40)
    else:
        for check_func in (check_if_gerente, check_if_head_not_auxiliar):
            flag, error, result = check_func(data_token.get("emp_id"))
            if flag and result:
                ids_identtifier = get_department_identifiers(
                    data_token.get("dep_id"), result
                )
                break
        for check_func in (check_if_leader, check_if_auxiliar_with_contract):
            flag, error, result = check_func(data_token.get("emp_id"))
            if flag and len(result) > 0:
                ids = []
                for item in result:
                    extra_info = json.loads(item[7])
                    ids += extra_info.get("contracts", [])
                    ids += extra_info.get("contracts_temp", [])
                ids = list(set(ids))
                flag, error, contracts = get_contracts_by_ids(ids)
                if not flag:
                    return {"data": None, "msg": str(error)}, 400
                break
    identifiers = [
        dict_depts_identifiers.get(dept_id)
        for dept_id in ids_identtifier
        if dict_depts_identifiers.get(dept_id)
    ]
    identifier_list = [
        item
        for sublist in identifiers
        for item in (sublist if isinstance(sublist, list) else [sublist])
    ]
    for result in contracts:
        metadata = json.loads(result[1])
        contract_number = metadata["contract_number"]
        idn_contract = contract_number[-4:]
        if str(idn_contract) not in identifier_list:
            identifier_list.append(f"{idn_contract}")
    if not identifier_list:
        return {"data": None, "msg": "Folios for user not found"}, 200
    return identifier_list, 200


def fetch_all_sm_with_permissions(data_token):
    iddentifiers, code = get_iddentifiers_creation(data_token)
    if code != 200:
        return {"data": [], "msg": iddentifiers}, 400
    data_sm, code = get_all_sm(-1, 0, -1)
    if code != 200:
        return {"data": [], "msg": data_sm}, 400
    data_out = {}
    ident_list = [f"sm-{item.lower()}-" for item in iddentifiers]
    for key in ident_list:
        tab = tabs_sm.get(key)
        if tab is None:
            continue
        if tab not in data_out:
            data_out[tab] = []
    for sm in data_sm["data"]:
        for key in ident_list:
            tab = tabs_sm.get(key)
            if tab is None:
                continue
            if key in sm["folio"].lower():
                data_out[tab].append(sm)
                break
    return {"data": data_out}, 200


def get_all_sm_control_table(data_token):
    iddentifiers, code = get_iddentifiers(data_token)
    if code != 200:
        return {"data": [], "msg": iddentifiers}, 400
    data_sm, code = get_all_sm(-1, 0, -1)
    if code != 200:
        return {"data": [], "msg": data_sm}, 400
    data_out = {}
    ident_list = [f"sm-{item.lower()}-" for item in iddentifiers]
    for key in ident_list:
        tab = tabs_sm.get(key)
        if tab is None:
            continue
        if tab not in data_out:
            data_out[tab] = []
    for sm in data_sm["data"]:
        for key in ident_list:
            tab = tabs_sm.get(key)
            if tab is None:
                continue
            if key in sm["folio"].lower():
                data_out[tab].append(sm)
                break
    return {"data": data_out}, 200


def update_data_dicts(products: list, products_sm):
    for list_items in products:
        for item in list_items:
            for i, item_p in enumerate(products_sm):
                if item["id"] == item_p["id"]:
                    products_sm[i] = item
                    break
    return products_sm


def dispatch_products(
    avaliable: list[dict],
    to_request: list[dict],
    sm_id: int,
    new_products: list[dict],
    data=None,
) -> tuple[list[dict], list[dict], list[dict]]:
    _data = DataHandler()
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    # ------------------------------avaliable products------------------------------------------
    msg = ""
    for i, product in enumerate(avaliable):
        # create out movements
        if "remanent" not in product.keys():
            if product["stock"] >= product["quantity"]:
                _data.create_out_movement(
                    product["id"], "salida", product["quantity"], date, sm_id
                )
                product["comment"] += " ;(Despachado) "
                delivered_trans = product["quantity"]
            else:
                _data.create_out_movement(
                    product["id"], "salida", product["stock"], date, sm_id
                )
                delivered_trans = product["stock"]
                product["remanent"] = product["quantity"] - product["stock"]
                product["comment"] += " ;(Semidespachado) "
        elif "remanent" in product.keys() and product["remanent"] > 0:
            _data.create_out_movement(
                product["id"], "salida", product["remanent"], date, sm_id
            )
            delivered_trans = product["remanent"]
            product["comment"] += " ;(Despachado) "
        else:
            # cuando el remante es menor que cero
            product["comment"] += " ;(Despachado) "
            continue
        # update stock avaliable
        _data.update_stock(product["id"], product["stock"] - delivered_trans)
        product["stock"] -= delivered_trans
        avaliable[i] = product
        msg += f"Cantidad: {delivered_trans}-{product['name']}, movimiento de salida al despachar."
    emp_id = data["emp_id"] if data is not None else 0
    emp_id_creation = data["emp_id_creation"] if data is not None else 0
    if len(avaliable) > 0:
        create_notification_permission(
            msg,
            ["almacen"],
            "Movimientos almacen despachar sm",
            emp_id,
            emp_id_creation,
        )
    # ------------------------------products to request------------------------------------------
    msg = ""
    for i, product in enumerate(to_request):
        _ins = _data.create_in_movement(
            product["id"], "entrada", product["quantity"], date, sm_id
        )
        product["comment"] += " ;(Pedido) "
        to_request[i] = product
        msg += f"{product['quantity']} {product['name']} movimiento de entrada."
        product["stock"] += product["quantity"]
    if len(to_request) > 0:
        create_notification_permission(
            msg,
            ["almacen"],
            "Movimiento pedidos al despachar sm",
            emp_id,
            emp_id_creation,
        )
    # ------------------------------products to request for new-----------------------------------
    msg = ""
    for i, product in enumerate(new_products):
        try:
            int(product["id"])
            if int(product["id"]) == -1 or int(product["id"]) < 0:
                msg += f"{product['quantity']} {product['name']} debe primero ser ingresado al inventario"
                continue
        except Exception as e:
            print("Error in the format of the id: ", str(e))
            continue
        # _ins = _data.create_in_movement(
        #     product["id"], "entrada", product["quantity"], date, sm_id
        # )
        product["comment"] += " ;(Pedido) "
        new_products[i] = product
        msg += f"{product['quantity']} {product['name']} movimiento de entrada de producto nuevo."
    if len(new_products) > 0:
        create_notification_permission(
            msg,
            ["almacen"],
            "Movimiento de entrada (Productos Nuevos)",
            emp_id,
            emp_id_creation,
        )
    return avaliable, to_request, new_products


# def dispatch_sm(data):
#     if len(data["items"]) > 0:
#         flag, error, result = update_sm_products_by_id(data["id"], data["items"])
#         if not flag:
#             return 400, f"Not posible to update products in sm, error: {error}"
#     flag, error, result = get_sm_by_id(data["id"])
#     if not flag or len(result) <= 0:
#         return 400, ["sm not foud"]
#     history_sm = json.loads(result[12])
#     emp_id_creation = result[6]
#     time_zone = pytz.timezone(timezone_software)
#     date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
#     history_sm.append(
#         {
#             "user": data["emp_id"],
#             "event": "dispatch",
#             "date": date_now,
#             "comment": data["comment"],
#         }
#     )
#     products_sm = json.loads(result[10])
#     products_to_dispacth = []
#     products_to_request = []
#     new_products = []
#     for item in products_sm:
#         if "(Nuevo)" in item["comment"] and "(Pedido)" not in item["comment"]:
#             new_products.append(item)
#             continue
#         if (
#             item["stock"] >= 0
#             and "(Despachado)" not in item["comment"]
#             and "(Semidespachado)" in item["comment"]
#         ):
#             products_to_dispacth.append(item)
#         elif (
#             "(Pedido)" not in item["comment"] and "(Despachado)" not in item["comment"]
#         ):
#             products_to_request.append(item)
#     # update db with corresponding movements
#     data["emp_id_creation"] = emp_id_creation
#     (products_to_dispacth, products_to_request, new_products) = dispatch_products(
#         products_to_dispacth, products_to_request, data["id"], new_products, data
#     )
#     # update table with new stock
#     products_sm = update_data_dicts(
#         [products_to_dispacth, products_to_request, new_products], products_sm
#     )
#     is_complete = (
#         True if len(products_to_request) == 0 and len(new_products) == 0 else False
#     )
#     flag, error, result = update_history_sm(
#         data["id"], history_sm, products_sm, is_complete
#     )
#     if is_complete:
#         print("complete dispatch sm")
#     if flag:
#         msg = f"SM con ID-{data['id']} despachada"
#         write_log_file(log_file_sm_path, msg)
#         if not is_complete:
#             msg += (
#                 "\n Productos a despachar:  "
#                 + "\n".join(
#                     [
#                         f"{item['quantity']} {item['name']}"
#                         for item in products_to_dispacth
#                     ]
#                 )
#                 + "--"
#             )
#             msg += (
#                 "\n Productos a solicitar:  "
#                 + "\n".join(
#                     [
#                         f"{item['quantity']} {item['name']}"
#                         for item in products_to_request
#                     ]
#                 )
#                 + "--"
#             )
#             msg += (
#                 "\n Productos nuevos:  "
#                 + "\n".join(
#                     [
#                         f"{item['quantity']} {item['name']} {item['url']}"
#                         for item in new_products
#                     ]
#                 )
#                 + "--"
#             )
#         else:
#             msg += "\nTodos los productos han sido despachados"
#         create_notification_permission(
#             msg, ["sm"], "SM Despachada", data["emp_id"], emp_id_creation
#         )
#         return 200, {
#             "to_dispatch": products_to_dispacth,
#             "to_request": products_to_request,
#             "new_products": new_products,
#         }
#     else:
#         return 400, {"msg": str(error)}


def dispatch_sm(data, data_token):
    if len(data["items"]) <= 0:
        return 400, ["No item to update in sm"]
    flag, error, result = get_sm_by_id(data["id"])
    if not flag or len(result) <= 0:
        return 400, ["SM not foud"]
    id_user = result[6]
    products_sm = json.loads(result[10])
    history_sm = json.loads(result[12])
    ids_list = [item["id"] for item in products_sm if item.get("id") >= 0]
    updated_products = []
    flag, error, result = get_products_stock_from_ids(ids_list)
    if not flag:
        return 400, {"msg": f"Error at retrieving stock: {str(error)}"}
    flag_semidespachado = False
    stocks = {item[0]: item[1] for item in result}
    comment_history = ""
    for item in products_sm:
        if "dispatched" not in item.keys():
            item["dispatched"] = 0
        for item_n in data["items"]:
            if item["id"] == item_n["id"]:
                if item_n["quantity"] > stocks[item["id"]]:
                    return 400, {
                        "msg": f"Quantity to dispatch is greater than stock for product {item['id']}-{item['name']}"
                    }
                if "(Despachado)".lower() in item["comment"].lower():
                    return 400, {
                        "msg": f"Product {item['id']}-{item['name']} already dispatched"
                    }
                item["dispatched"] += item_n["quantity"]
                if item["dispatched"] > item["quantity"]:
                    return 400, {
                        "msg": f"Quantity to dispatch is greater than requested for product {item['id']}-{item['name']}"
                    }
                # insertar al inicio de los comentarios
                item["comment"] = f"{item_n['comment']}\n{item['comment']}"
                # agregar los comandos
                item["comment"] += (
                    " ;(Despachado) "
                    if item["dispatched"] >= item["quantity"]
                    else " ;(Semidespachado) "
                )
                comment_history += f"Dispatch: {item['quantity']}->{item['id']}\n"
                break
        updated_products.append(item)
        if "(Semidespachado)".lower() in item["comment"].lower():
            flag_semidespachado = True

    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    comment_history += (
        "SM Despachada" if not flag_semidespachado else "SM Semidespachada"
    )
    history_sm.append(
        {
            "user": data_token["emp_id"],
            "event": "dispatch",
            "date": date_now,
            "comment": comment_history,
        }
    )
    flag, error, result = update_history_items_sm(
        data["id"], updated_products, history_sm
    )
    if flag:
        msg = (
            f"SM con ID-{data['id']} despachada por el empleado {data_token['emp_id']}"
            if not flag_semidespachado
            else f"SM con ID-{data['id']} semidespachada por el empleado {data_token['emp_id']}"
        )
        write_log_file(log_file_sm_path, msg)
        create_notification_permission(
            msg, ["sm"], "SM Despachada", data_token["emp_id"], id_user
        )
        return 200, {"msg": "ok"}
    else:
        return 400, {"msg": f"Error at updating sm {str(error)}"}


def cancel_sm(data):
    flag, error, result = get_sm_by_id(data["id"])
    if not flag or len(result) <= 0:
        return 400, ["sm not foud"]
    history_sm = json.loads(result[0][13])
    emp_id_creation = result[0][7]
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history_sm.append(
        {
            "user": data["emp_id"],
            "event": "cancelation",
            "date": date_now,
            "comment": data["comment"],
        }
    )
    flag, error, result = update_history_sm(data["id"], history_sm, [], True)
    if flag:
        msg = f"SM con ID-{data['id']} cancelada"
        create_notification_permission(
            msg, ["sm"], "SM Cancelada", data["emp_id"], emp_id_creation
        )
        write_log_file(log_file_sm_path, msg)
        return 200, {"msg": "ok"}
    else:
        return 400, {"msg": str(error)}


def get_employees_almacen():
    flag, error, result = get_emp_contract("almacen")
    data_out = []
    for item in result:
        id_emp, name, lastname = item
        data_out.append({"id": id_emp, "name": name.upper() + " " + lastname.upper()})
    return data_out, 200


def dowload_file_sm(sm_id: int, type_file="pdf"):
    flag, error, result = get_sm_by_id(sm_id)
    if not flag or len(result) == 0:
        return None, 400
    folio = result[1]
    contract = result[2]
    facility = result[3]
    location = result[4]
    client_id = result[5]
    emp_id = result[6]
    order_quotation = result[7]
    date = pd.to_datetime(result[8])
    critical_date = pd.to_datetime(result[9])
    items = json.loads(result[10])
    status = result[11]
    history = json.loads(result[12])
    observations = result[13]
    extra_info = json.loads(result[14])
    download_path = (
        os.path.join(
            tempfile.mkdtemp(), os.path.basename(f"sm_{result[0]}_{date.date()}.pdf")
        )
        if type_file == "pdf"
        else os.path.join(
            tempfile.mkdtemp(), os.path.basename(f"sm_{result[0]}_{date.date()}.xlsx")
        )
    )
    products = []
    flag, error, result = get_info_names_by_sm_id(result[0])
    if flag and len(result) == 0:
        customer_name = result[0]
        emp_name = result[1] + " " + result[2]
    else:
        customer_name = "None"
        emp_name = "None"
    counter = 1
    for item in items:
        name = item["name"] if "name" in item.keys() else "None"
        quantity = item["quantity"] if "quantity" in item.keys() else "None"
        comment = item["comment"] if "comment" in item.keys() else "None"
        udm = item["udm"] if "udm" in item.keys() else "None"
        stock = item["dispached"] if "dispached" in item.keys() else "None"
        if "(despachado)" in comment.lower():
            status = "Despachado"
        elif "(pedido)" in comment.lower():
            status = "Pedido"
        elif "(nuevo)" in comment.lower():
            status = "Nuevo-Pedido"
        else:
            status = "pendiente"
        products.append((counter, name, quantity, udm, stock, status))

    if type_file == "pdf":
        flag = FileSmPDF(
            {
                "filename_out": download_path,
                "products": products,
                "metadata": {
                    "Fecha de Solicitud": date.strftime(format_date),
                    "Folio": folio,
                    "Contrato": contract,
                    "Usuario Solicitante": customer_name,
                    "Número de Pedido": order_quotation,
                    "Personal Telintec": emp_name,
                    "Planta": facility,
                    "Área Dirigida Telintec": location,
                    "Área / Ubicación": location,
                    "Fecha Crítica de Entrega": critical_date.strftime(format_date),
                },
                "observations": observations,
                "date_complete_delivery": "2023-06-01",
                "date_first_delivery": "2023-06-01",
            },
        )
        if not flag:
            print("error at generating pdf", download_path)
            return None, 400
    else:
        lista_de_items = products
        # Definir los nombres de las columnas
        columnas = ["No.", "Nombre", "Cantidad", "Unidad de Medida", "Stock", "Estatus"]
        # Convertir la lista en un DataFrame
        df = pd.DataFrame(lista_de_items, columns=columnas)
        # Guardar el DataFrame en un archivo Excel
        df.to_excel(download_path, index=False)
    return download_path, 200


def create_customer(name, email, phone, rfc, address):
    flag, error, result = create_customer_db(name, email, phone, rfc, address)
    if flag:
        return {"msg": "ok", "data": result}, 201
    else:
        return {"msg": str(error)}, 400


def create_product(
    sku,
    name,
    udm,
    stock,
    id_category,
    id_supplier,
    is_tool=0,
    is_internal=0,
    codes=None,
    locations=None,
):
    if id_supplier is not None:
        flag, error, result = create_product_db(
            sku,
            name,
            udm,
            stock,
            id_category,
            id_supplier,
            is_tool,
            is_internal,
            codes,
            locations,
        )
    else:
        flag, error, result = create_product_db_admin(
            sku, name, udm, stock, id_category, codes
        )
    return {"msg": "ok", "data": result}, 201 if flag else {"msg": str(error)}, 400


def update_sm_from_control_table(data, data_token):
    flag, error, result = get_sm_by_id(data["id"])
    if not flag or len(result) <= 0:
        return 400, ["sm not foud"]
    history_sm = json.loads(result[12])
    emp_id_creation = result[6]
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history_sm.append(
        {
            "user": data_token.get("emp_id"),
            "event": "update table info",
            "date": date_now,
            "comment": "Update from control table",
        }
    )
    extra_info = json.loads(result[14])
    comments = ""
    for k, value in data["info"].items():
        if k == "comments":
            comments = value
            continue
        extra_info[k] = value
    flag, error, result = update_history_extra_info_sm_by_id(
        data["id"], extra_info, history_sm, comments
    )
    if flag:
        msg = f"SM con ID-{data['id']} actualizada"
        create_notification_permission(
            msg, ["sm"], "SM Actualizada", data_token.get("emp_id"), emp_id_creation
        )
        write_log_file(log_file_sm_path, msg)
        return 200, {"msg": "ok"}
    else:
        return 400, {"msg": str(error)}
