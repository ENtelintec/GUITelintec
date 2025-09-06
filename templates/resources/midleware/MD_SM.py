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
    format_date,
    format_timestamps,
    log_file_sm_path,
    timezone_software,
)
from templates.controllers.contracts.contracts_controller import (
    get_contract_by_client,
    get_contracts_by_ids,
    get_items_contract_string,
)
from templates.controllers.customer.customers_controller import create_customer_db
from templates.controllers.departments.heads_controller import (
    check_if_auxiliar_with_contract,
    check_if_leader,
)
from templates.controllers.employees.employees_controller import get_emp_contract

# from templates.controllers.index import DataHandler
from templates.controllers.material_request.sm_controller import (
    get_info_names_by_sm_id,
    get_sm_by_id,
    get_sm_entries,
    insert_sm_db,
    update_history_extra_info_sm_by_id,
    update_history_sm,
    create_items_sm_db,
    update_items_sm,
    update_sm_db,
    update_history_status_sm,
    get_sm_folios_db,
    delete_sm_db,
    delete_item_from_sm_id,
)
from templates.controllers.product.p_and_s_controller import (
    create_movement_db_amc,
    create_product_db,
    create_product_db_admin,
    get_products_stock_from_ids,
    get_sm_products,
    update_stock_db,
    complete_reservation_db,
)
from templates.forms.StorageMovSM import FileSmPDF
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.Functions_midleware_admin import get_iddentifiers


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
                    "reserved": item[4],
                    "available_stock": item[5],
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
                    "reserved": item[4],
                    "available_stock": item[5],
                }
            )
    data_out = {"data": {"contract": items_partida, "normal": items_normal}}
    return data_out, 200


def calculate_items_delivered(items):
    total = 0
    dispatched_total = 0
    for item in items:
        quantity = item.get("quantity", 1.0)
        total += quantity if quantity else 1.0
        dispatched = item.get("dispatched", 0)
        dispatched_total += dispatched if dispatched else 0
    return round((dispatched_total / total) * 100, 2) if total else 0


def calculate_items_delivered_2(items):
    total = sum(item.get("quantity", 1.0) for item in items)
    dispatched_total = sum(item.get("dispatched", 0) for item in items)
    return round((dispatched_total / total) * 100, 2) if total else 0


def get_all_sm(limit, page=0, emp_id=-1, with_items=True):
    emp_id = None if emp_id == -1 else emp_id
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
        extra_info = json.loads(result[i][14])
        # time_zone = pytz.timezone(timezone_software)
        # date_now = datetime.now(pytz.utc).astimezone(time_zone)
        #  kpi warehouse
        admin_not_date = extra_info.get("admin_notification_date", "")
        admin_not_date = (
            pd.to_datetime(admin_not_date)
            if admin_not_date != ""
            and isinstance(admin_not_date, str)
            and admin_not_date is not None
            else None
        )
        date_creation = (
            pd.to_datetime(result[i][8])
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
            pd.to_datetime(result[i][9])
            if result[i][9] != "" and isinstance(result[i][9], str)
            else result[i][9]
        )
        op_not_date = extra_info.get("operations_notification_date", "")
        op_not_date = (
            pd.to_datetime(op_not_date)
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
        items_sm = json.loads(result[i][10]) if with_items else []
        percentage = calculate_items_delivered(json.loads(result[i][10]))

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
            "items": items_sm,
            "percentage": percentage,
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


def get_iddentifiers_creation_contracts(data_token):
    permissions = data_token.get("permissions", {}).values()
    contracts = []
    dict_tabs = {}
    if any(
        word in item.lower().split(".")[-1]
        for word in ["administrator"]
        for item in permissions
    ):
        flag, error, contracts = get_contract_by_client(40)
    else:
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
                    return {"data": None, "msg": str(error)}, dict_tabs, 400
                break
    identifier_list = []
    for result in contracts:
        contract_number = result[5]
        idn_contract = contract_number[-4:]
        metadata_contract = json.loads(result[1])
        if str(idn_contract) not in identifier_list:
            identifier_list.append(f"{idn_contract}")
            dict_tabs[f"sm-{idn_contract}-"] = metadata_contract.get(
                "abbreviation", f"{idn_contract}"
            )
    if not identifier_list:
        return {"data": None, "msg": "Folios for user not found"}, dict_tabs, 200
    return identifier_list, dict_tabs, 200


def get_iddentifiers_ternium(data_token):
    permissions = data_token.get("permissions", {}).values()
    contracts = []
    dict_tabs = {}
    if any(
        word in item.lower().split(".")[-1]
        for word in ["administrator", "almacen"]
        for item in permissions
    ):
        flag, error, contracts = get_contract_by_client(40)
    else:
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
                    return {"data": None, "msg": str(error)}, dict_tabs, 400
                break

    identifier_list = []
    for result in contracts:
        contract_number = result[5]
        metadata_contract = json.loads(result[1])
        idn_contract = contract_number[-4:]
        if str(idn_contract) not in identifier_list:
            identifier_list.append(f"{idn_contract}")
            dict_tabs[f"sm-{idn_contract}-"] = metadata_contract.get(
                "abbreviation", f"{idn_contract}"
            )
    if not identifier_list:
        return {"data": None, "msg": "Folios for user not found"}, dict_tabs, 200
    return identifier_list, dict_tabs, 200


def clasify_sm(iddentifiers, data_sm, data_token, tabs_sm):
    data_out = {}
    ident_list = [f"sm-{item.lower()}-" for item in iddentifiers]
    for key in ident_list:
        tab = tabs_sm.get(key)
        if tab is None:
            continue
        if tab not in data_out:
            data_out[tab] = []
    ident_set = set(ident_list)
    for sm in data_sm["data"]:
        folio = sm["folio"].lower()
        added = False
        for key in ident_set:
            if key in folio:
                tab = tabs_sm.get(key)
                if tab:
                    data_out[tab].append(sm)
                    added = True
                    break
        if not added and sm["emp_id"] == data_token.get("emp_id"):
            data_out.setdefault("Otros", []).append(sm)
    return data_out


def fetch_all_sm_with_permissions(data_token):
    iddentifiers, dict_tabs, code = get_iddentifiers_creation_contracts(data_token)
    abbs_list_departments, code = get_iddentifiers(data_token, ["administrator"])
    for abb in abbs_list_departments:
        dict_tabs[f"sm-{abb.lower()}-"] = abb
    if code != 200:
        abbs_list_departments = []
    data_sm, code = get_all_sm(-1, 0, -1)
    if code != 200:
        return {"data": [], "msg": data_sm}, 400
    data_out = clasify_sm(
        iddentifiers + abbs_list_departments, data_sm, data_token, dict_tabs
    )
    return {"data": data_out}, 200


def get_all_sm_control_table(data_token):
    iddentifiers_contracts, dict_tabs_contracts, code = get_iddentifiers_ternium(
        data_token
    )
    abbs_list_departments, code = get_iddentifiers(data_token, ["administrator"])
    for abb in abbs_list_departments:
        dict_tabs_contracts[f"sm-{abb.lower()}-"] = abb
    if code != 200:
        # print(abbs_list_departments)
        abbs_list_departments = []
    data_sm, code = get_all_sm(-1, 0, -1, with_items=False)
    if code != 200:
        return {"data": [], "msg": data_sm}, 400
    data_out = clasify_sm(
        iddentifiers_contracts + abbs_list_departments,
        data_sm,
        data_token,
        dict_tabs_contracts,
    )
    return {"data": data_out}, 200


def update_data_dicts(products: list, products_sm):
    for list_items in products:
        for item in list_items:
            for i, item_p in enumerate(products_sm):
                if item["id"] == item_p["id"]:
                    products_sm[i] = item
                    break
    return products_sm


# def dispatch_products_from_GUI(
#     available: list[dict],
#     to_request: list[dict],
#     sm_id: int,
#     new_products: list[dict],
#     data=None,
# ) -> tuple[list[dict], list[dict], list[dict]]:
#     # _data = DataHandler()
#     time_zone = pytz.timezone(timezone_software)
#     date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
#     # ------------------------------avaliable products------------------------------------------
#     msg = ""
#     for i, product in enumerate(available):
#         # create out movements
#         if "remanent" not in product.keys():
#             if product["stock"] >= product["quantity"]:
#                 create_movement_db_amc(
#                     product["id"], "salida", product["quantity"], date, sm_id
#                 )
#                 product["comment"] += " ;(Despachado) "
#                 delivered_trans = product["quantity"]
#             else:
#                 create_movement_db_amc(
#                     product["id"], "salida", product["stock"], date, sm_id
#                 )
#                 delivered_trans = product["stock"]
#                 product["remanent"] = product["quantity"] - product["stock"]
#                 product["comment"] += " ;(Semidespachado) "
#         elif "remanent" in product.keys() and product["remanent"] > 0:
#             create_movement_db_amc(
#                 product["id"], "salida", product["remanent"], date, sm_id
#             )
#             delivered_trans = product["remanent"]
#             product["comment"] += " ;(Despachado) "
#         else:
#             # cuando el remante es menor que cero
#             product["comment"] += " ;(Despachado) "
#             continue
#         # update stock avaliable
#         update_stock_db(product["id"], product["stock"] - delivered_trans)
#         product["stock"] -= delivered_trans
#         available[i] = product
#         msg += f"Cantidad: {delivered_trans}-{product['name']}, movimiento de salida al despachar."
#     emp_id = data["emp_id"] if data is not None else 0
#     emp_id_creation = data["emp_id_creation"] if data is not None else 0
#     if len(available) > 0:
#         create_notification_permission(
#             msg,
#             ["almacen"],
#             "Movimientos almacen despachar sm",
#             emp_id,
#             emp_id_creation,
#         )
#     # ------------------------------products to request------------------------------------------
#     msg = ""
#     for i, product in enumerate(to_request):
#         _ins = create_movement_db_amc(
#             product["id"], "entrada", product["quantity"], date, sm_id
#         )
#         product["comment"] += " ;(Pedido) "
#         to_request[i] = product
#         msg += f"{product['quantity']} {product['name']} movimiento de entrada."
#         product["stock"] += product["quantity"]
#     if len(to_request) > 0:
#         create_notification_permission(
#             msg,
#             ["almacen"],
#             "Movimiento pedidos al despachar sm",
#             emp_id,
#             emp_id_creation,
#         )
#     # ------------------------------products to request for new-----------------------------------
#     msg = ""
#     for i, product in enumerate(new_products):
#         try:
#             int(product["id"])
#             if int(product["id"]) == -1 or int(product["id"]) < 0:
#                 msg += f"{product['quantity']} {product['name']} debe primero ser ingresado al inventario"
#                 continue
#         except Exception as e:
#             print("Error in the format of the id: ", str(e))
#             continue
#         # _ins = _data.create_in_movement(
#         #     product["id"], "entrada", product["quantity"], date, sm_id
#         # )
#         product["comment"] += " ;(Pedido) "
#         new_products[i] = product
#         msg += f"{product['quantity']} {product['name']} movimiento de entrada de producto nuevo."
#     if len(new_products) > 0:
#         create_notification_permission(
#             msg,
#             ["almacen"],
#             "Movimiento de entrada (Productos Nuevos)",
#             emp_id,
#             emp_id_creation,
#         )
#     return available, to_request, new_products


def determine_status_sm(items: list):
    total_items = len(items)
    for item in items:
        if item["state"] == 4:
            total_items -= 1
    return 2 if total_items == 0 else 1


def dispatch_sm(data, data_token):
    if len(data["items"]) <= 0:
        return 400, ["No item to update in sm"]
    flag, error, result = get_sm_by_id(data["id"])
    if not flag or len(result) <= 0:
        return 400, ["SM not foud"]
    id_user = result[6]
    products_sm = json.loads(result[10])
    history_sm = json.loads(result[12])
    extra_info_sm = json.loads(result[14])
    folio = result[1]
    # products ids in the inventory
    ids_inventory_sm_list = [
        item["id_inventory"] for item in products_sm if item.get("state") > 0
    ]
    updated_products = []
    flag, error, result = get_products_stock_from_ids(ids_inventory_sm_list)
    if not flag:
        return 400, {"msg": f"Error at retrieving stock: {str(error)}"}
    flag_semidespachado = False
    stocks = {item[0]: item[1] for item in result}
    comment_history = ""
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    dict_products_sm = {
        item["id"]: {**item, "dispatched": item.get("dispatched", 0)}
        for item in products_sm
    }
    msg_items = []
    operations_done = False
    for item_n in data["items"]:
        item_to_update = dict_products_sm.get(item_n["id"])
        old_item = item_to_update.copy()
        # si el item no existe
        if item_to_update is None:
            msg_items.append(
                f"Producto {item_n['id']}-{item_n['name']} no encontrado en la sm"
            )
            updated_products.append(old_item)
            continue
        # si no hay cantidad para despachar
        if item_n["quantity"] > stocks.get(item_to_update["id_inventory"], 0):
            msg_items.append(
                f"La cantidad para despachar es mayor que el stock disponible para el producto "
                f"{item_to_update['id']}-{item_to_update['id_inventory']}-{item_to_update['name']}"
            )
            updated_products.append(old_item)
            continue
        # si ya esta despachado
        if (
            "(Despachado)".lower() in item_to_update["comment"].lower()
            or item_to_update["state"] == 4
        ):
            msg_items.append(
                f"Producto {item_to_update['id']}-{item_to_update['name']} ya fue despachado"
            )
            # updated_products.append(old_item)
            continue
        # calculo de cantidad total despachada
        item_to_update["dispatched"] += item_n["quantity"]
        # si la cantidad es mayor que la requerida
        if item_to_update["dispatched"] > item_to_update["quantity"]:
            msg_items.append(
                f"La cantidad a despachar es mayor que la cantidad requerida para el producto "
                f"{item_to_update['id']}-{item_to_update['id_inventory']}-{item_to_update['name']}"
            )
            updated_products.append(old_item)
            continue
        # --- Crear un movimiento de salida para el despachado
        flag, error, result = create_movement_db_amc(
            item_to_update["id_inventory"],
            "salida",
            item_n["quantity"],
            date_now,
            folio,
            "Despachado de SM",
        )
        if not flag:
            msg_items.append(
                f"x---Error al crear el movimiento para el item {item_to_update['id_inventory']}: {str(error)}"
            )
            updated_products.append(old_item)
            continue
        msg_items.append(
            f"----Movimiento creado para el item {item_to_update['id_inventory']}: {str(result)}"
        )
        # -- actualizar stock del producto
        flag, error, res_stock = update_stock_db(
            item_to_update["id_inventory"], -item_n["quantity"], True
        )
        msg_items.append(
            f"x---Error al actualizar el stock para el producto {item_to_update['id_inventory']}: {str(error)}"
        ) if not flag else msg_items.append(
            f"---Stock actualizado para el item {item_to_update['id_inventory']}: {str(res_stock)}"
        )
        # -- actualizar el estado de la reservación
        flag, error, res_res = complete_reservation_db(item_to_update["reservation_id"])
        msg_items.append(
            f"x---Error al tratar de completar la reservación {item_to_update['id']}: {str(error)}"
        ) if not flag else msg_items.append(
            f"---Reservación completada {item_to_update['id']}: {str(res_res)}"
        )
        # verificar si se despacho por completo
        item_to_update["state"] = (
            4 if item_to_update["dispatched"] == item_to_update["quantity"] else 3
        )
        # insertar al inicio de los comentarios
        item_to_update["comment"] = f"{item_n['comment']}\n{item_to_update['comment']}"
        # agregar los comandos
        item_to_update["comment"] += (
            " ;(Despachado) "
            if item_to_update["dispatched"] >= item_to_update["quantity"]
            else " ;(Semidespachado) "
        )
        comment_history += (
            f"Despachado: {item_to_update['quantity']}->{item_to_update['id']}\n"
        )
        # --- agregar el item para que se actualize en los datos de la sm
        updated_products.append(item_to_update)
        if (
            "(Semidespachado)".lower() in item_to_update["comment"].lower()
            or item_to_update["state"] == 3
        ):
            flag_semidespachado = True
        operations_done = True
    ids_to_update = [item["id"] for item in updated_products]
    for k, v in dict_products_sm.items():
        if k not in ids_to_update:
            updated_products.append(v)
    if not operations_done:
        return 400, {"msg": msg_items, "error": "No operations done"}
    comment_history += (
        "SM Despachada" if not flag_semidespachado else "SM Semidespachada"
    )
    history_sm.append(
        {
            "user": data_token["emp_id"],
            "event": "Accion de despachado",
            "date": date_now,
            "comment": comment_history + f" por el empleado {data_token['emp_id']}",
        }
    )
    errors, results_smi = update_items_sm(updated_products, data["id"])
    if len(errors) > 0:
        msg_items.append(f"Error al actualizar items: {errors}")
    if len(results_smi) > 0:
        msg_items.append(f"Items SM actualizados: {results_smi}")
    new_status = determine_status_sm(updated_products)
    # actualizar valores en tabla de control
    warehouse_reviewed = extra_info_sm.get("warehouse_reviewed", 0)
    warehouse_notification_date = extra_info_sm.get("warehouse_notification_date", "")
    operations_notification_date = extra_info_sm.get("operations_notification_date", "")
    admin_notification_date = extra_info_sm.get("admin_notification_date", "")
    extra_info = (
        {
            "admin_status": 2,
            "warehouse_status": 1,
            "general_request_status": 0,
            "warehouse_notification_date": date_now
            if warehouse_notification_date == ""
            else warehouse_notification_date,
            "operations_notification_date": date_now
            if operations_notification_date == ""
            else operations_notification_date,
            "admin_notification_date": date_now
            if admin_notification_date == ""
            else admin_notification_date,
        }
        if new_status == 2
        else {}
    )
    if warehouse_reviewed == 0:
        extra_info["warehouse_reviewed"] = 1
    for k, v in extra_info.items():
        extra_info_sm[k] = v
    flag, error, result_his = update_history_status_sm(
        data["id"], history_sm, new_status, extra_info_sm
    )
    msg_items.append(
        f"Historial actualizado: {str(result_his)}"
    ) if flag else msg_items.append(
        f"Error al actualizar el historial de la sm: {str(error)}"
    )
    msg = (
        f"SM con ID-{data['id']} despachada por el empleado {data_token['emp_id']}"
        if not flag_semidespachado
        else f"SM con ID-{data['id']} semidespachada por el empleado {data_token['emp_id']}"
    )
    if msg_items:
        msg += "\n" + "\n".join(msg_items)
    write_log_file(log_file_sm_path, msg)
    create_notification_permission(
        msg, ["sm"], "SM Despachada", data_token["emp_id"], id_user
    )
    return 200, {"msg": msg_items}


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
            "event": "Cancelación",
            "date": date_now,
            "comment": data["comment"] + f"por el empleado {data['emp_id']}",
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
    # client_id = result[5]
    # emp_id = result[6]
    order_quotation = result[7]
    date = pd.to_datetime(result[8])
    critical_date = pd.to_datetime(result[9])
    items = json.loads(result[10]) if isinstance(result[10], str) else result[10]
    # status = result[11]
    # history = json.loads(result[12])
    observations = result[13]
    # extra_info = json.loads(result[14])
    download_path = (
        os.path.join(
            tempfile.mkdtemp(), os.path.basename(f"sm_{result[0]}_{folio}.pdf")
        )
        if type_file == "pdf"
        else os.path.join(
            tempfile.mkdtemp(), os.path.basename(f"sm_{result[0]}_{folio}.xlsx")
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


def update_sm_from_control_table(data, data_token, sm_data=None):
    if sm_data is None:
        flag, error, result = get_sm_by_id(data["id"])
    else:
        flag, error, result = True, None, sm_data
    if not flag or len(result) <= 0:
        return 400, ["sm not foud"]
    history_sm = json.loads(result[12])
    emp_id_creation = result[6]
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    comment_history = f"Actualización de datos desde la tabla de control por el empleado {data_token.get('emp_id')}"

    extra_info = json.loads(result[14])
    comments = ""
    for k, value in data["info"].items():
        if k == "comments":
            comments = value
            continue
        extra_info[k] = value
        comment_history += f"-{k}-{value}-"
    history_sm.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Actualizar control de sm",
            "date": date_now,
            "comment": comment_history,
        }
    )
    flag, error, result = update_history_extra_info_sm_by_id(
        data["id"], extra_info, history_sm, comments
    )
    if flag:
        msg = f"SM con ID-{data['id']} actualizada"
        create_notification_permission(
            msg,
            ["sm", "almacen", "administracion"],
            "SM Actualizada",
            data_token.get("emp_id"),
            emp_id_creation,
        )
        write_log_file(log_file_sm_path, msg + "-->" + comment_history)
        return 200, {"msg": "ok"}
    else:
        return 400, {"msg": str(error)}


def check_item_sm_for_init_vals(items: list):
    all_avaliable = True
    for item in items:
        if item.get("id", 0) <= 0:
            all_avaliable = False
            break
        if item.get("stock", 0) < item["quantity"]:
            all_avaliable = False
            break
    if all_avaliable:
        extra_info = {
            "warehouse_status": 0,
            "admin_status": 2,
            "general_request_status": 0,
        }
    else:
        extra_info = {
            "warehouse_status": 1,
            "admin_status": 0,
            "general_request_status": 2,
        }
    return extra_info


def create_sm_from_api(data, data_token):
    if len(data["items"]) == 0:
        return {
            "answer": "error no sufficient items",
            "data": data["items"],
            "error": "No items detected",
        }, 400
    extra_info = check_item_sm_for_init_vals(data["items"])
    flag, error, result = insert_sm_db(data, extra_info)
    if not flag:
        print(error)
        return {"answer": "error at updating db"}, 400
    msg = (
        f"Nueva SM creada #{result}, folio: {data['info']['folio']}, "
        f"fecha limite: {data['info']['critical_date']}, "
        f"empleado con id: {data_token.get('emp_id')}, "
        f"comentario: {data['info']['comment']}"
    )
    errors_items, result_ids_items = create_items_sm_db(data["items"], result)
    if len(result_ids_items) > 0:
        msg += f"\nItems creados: {result_ids_items}"
    if len(errors_items) > 0:
        msg += f"\nErrores al crear items: {errors_items}"
    create_notification_permission(
        msg,
        ["sm", "administracion", "almacen"],
        "Nueva SM Recibida",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sm_path, msg)
    return {"answer": "ok", "data": msg, "error": error}, 201


def check_if_items_sm_correct_for_update(data):
    all_ok = True
    error = None
    items_out = []
    for item in data["items"]:
        items_out.append(item)
        if item.get("quantity", 0) < item["quantity"]:
            all_ok = False
            error = f"Item con id {item['id']} no tiene suficiente stock"
            break
        if item.get("id", 0) <= 0:
            if item.get("id_inventory", 0) <= 0:
                all_ok = False
                error = (
                    f"Item con id {item['id']} no tiene id de inventario para crearlo"
                )
                break
        if item.get("id_inventory", 0) <= 0:
            if item.get("id", 0) > 0:
                all_ok = False
                error = f"No se puede actualizar el item con id {item['id']} sin id de inventario"
                break
    return all_ok, items_out, error


def update_sm_from_api(data, data_token):
    flag, items_out, error = check_if_items_sm_correct_for_update(data)
    if not flag:
        return {
            "answer": "error at items",
            "data": items_out,
            "error": error,
        }, 400
    flag, error, result = update_sm_db(data)
    if flag:
        msg = (
            f"SM  actualizada  #{data['info']['id']}, folio: {data['info']['folio']}, "
            f"fecha limite: {data['info']['critical_date']}, "
            f"empleado con id: {data_token.get('emp_id')}, "
            f"comentario: {data['info']['comment']}"
        )
        errors, results = update_items_sm(data["items"], data["id"])
        if len(results) > 0:
            msg += f"\nItems actualizados: {results}"
        if len(errors) > 0:
            msg += f"\nErrores al actualizar items: {errors}"
        create_notification_permission(
            msg,
            ["sm", "administracion", "almacen"],
            "Nueva SM Recibida",
            data_token.get("emp_id"),
            0,
        )
        write_log_file(log_file_sm_path, msg)
        return {"answer": "ok", "data": msg, "error": error}, 200
    else:
        return {"answer": "error at updating db", "data": "", "error": error}, 400


def delete_sm_from_api(data, data_token):
    flag, error, result = delete_item_from_sm_id(data["id"])
    if not flag:
        return {"answer": "error at deleting items of sm in db"}, 400
    msg = f"Items eliminados <{result}> de la sm con id: {data['id']}\n"
    flag, error, result = delete_sm_db(data["id"])
    if flag:
        msg += (
            f"SM #{data['id']} eliminada, empleado con id: {data_token.get('emp_id')}"
        )
        create_notification_permission(
            msg,
            ["sm", "administracion", "almacen"],
            "SM Eliminada",
            sender_id=data.get("id_emp"),
        )
        write_log_file(log_file_sm_path, msg)
        return {"answer": "ok", "msg": error}, 200
    else:
        print(error)
        return {"answer": "error at updating db"}, 400


def update_items_sm_from_api(data, data_token):
    errors, results = update_items_sm(data["items"], data["id_sm"])
    msg = ""
    if len(results) > 0:
        msg = f"Items actualizados: {results}"
    if len(errors) > 0:
        msg += f"\nErrores al actualizar items: {errors}"
    create_notification_permission(
        msg,
        ["sm", "administracion", "almacen"],
        "Nueva SM Recibida",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sm_path, msg)
    return {"answer": "ok", "data": msg, "error": errors}, 200


def get_sm_folios_from_api(data_token):
    flag, error, result = get_sm_folios_db()
    if not flag:
        return {"answer": "error at getting sm folios"}, 400
    folios = []
    for item in result:
        folios.append(
            {
                "id": item[0],
                "folio": item[1],
            }
        )
    return {"answer": "ok", "data": folios}, 200
