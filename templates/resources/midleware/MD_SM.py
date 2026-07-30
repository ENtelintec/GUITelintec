import json
import math
import os
import tempfile
from datetime import datetime

import boto3
import pandas as pd
import pytz
from botocore.exceptions import ClientError, NoCredentialsError

from static.constants import (
    format_date,
    format_timestamps,
    log_file_sm_path,
    secrets,
    timezone_software,
)
from templates.controllers.contracts.contracts_controller import (
    get_contract_by_client,
    get_contracts_by_ids,
    get_items_contract_string,
)
from templates.controllers.contracts.quotations_controller import (
    get_items_quotation_from_cotract,
    update_quotation_item_partida_from_sm,
)
from templates.controllers.customer.customers_controller import create_customer_db
from templates.controllers.employees.employees_controller import get_emp_contract
from templates.controllers.heads.heads_controller import (
    check_if_auxiliar_with_contract,
    check_if_leader,
)
from templates.controllers.material_request.sm_controller import (
    create_items_sm_db,
    delete_item_from_sm_id,
    delete_sm_db,
    get_folios_by_pattern,
    get_info_names_by_sm_id,
    get_sm_by_id,
    get_sm_entries,
    get_sm_folios_db,
    get_sm_from_item,
    get_sm_items_state,
    insert_sm_db,
    insert_urgent_sm_db,
    update_extra_info_sm_item_db,
    update_history_extra_info_sm_by_id,
    update_history_sm_from_cancel,
    update_history_status_sm,
    update_inventory_state_sm_item_db,
    update_items_sm,
    update_sm_db,
    update_state_sm_item_db,
)
from templates.controllers.product.movements_controller import create_movement_db_amc
from templates.controllers.product.products_controller import (
    create_product_db,
    create_product_db_admin,
    get_products_stock_from_ids,
    get_products_w_reservations,
    update_stock_db,
)
from templates.controllers.product.reservations_controller import (
    complete_reservation_db,
)
from templates.forms.StorageMovSM import FileSmPDF
from templates.Functions_Utils import (
    create_notification_permission,
    create_notification_permission_notGUI,
)
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.Functions_midleware_admin import get_iddentifiers

__author__ = "Edisson Naula"
__date__ = "$ 18/dic/2024  at 12:10 $"


def get_products_sm(contract: str, data_token) -> tuple[dict, int]:
    if contract != "all":
        flag, error, items_contract = get_items_contract_string(contract, data_token)
    else:
        items_contract = []
    # id_inventory -> lista de (partida, section_index). Un mismo producto puede
    # estar en varias secciones/partidas del contrato; se guardan todas (antes se
    # sobrescribia y ganaba la ultima) para emitir una fila por par.
    ids_in_contract: dict = {}
    if isinstance(items_contract, int):
        return {
            "data": {"contract": [], "normal": []},
            "msg": "Items del contrato no válidos",
            "error": "Not valid items",
        }, 400
    for item in items_contract:
        if item[4] is None:
            continue
        ids_in_contract.setdefault(item[4], []).append((item[3], item[5]))
    flag, error, result_p = get_products_w_reservations(data_token)
    if not flag:
        return {
            "data": {"contract": [], "normal": []},
            "msg": "No se pudieron obtener los productos",
            "error": error,
        }, 400
    items_normal = []
    items_partida = []
    if isinstance(result_p, int):
        return {
            "data": {"contract": [], "normal": []},
            "msg": "Productos con reservación no válidos",
            "error": "Not valid items with reservation",
        }, 400
    for product in result_p:
        sku = product[6]
        codes = json.loads(product[7]) if product[7] else []
        sku_fabricante = ""
        for code in codes:
            if code.get("tag") == "sku_fabricante":
                sku_fabricante = code.get("value")
                break
        if product[0] in ids_in_contract.keys():
            # Una fila por (partida, section_index): el mismo producto puede servir a
            # varias partidas/secciones del contrato y el front las elige por separado.
            for partida, section_index in ids_in_contract[product[0]]:
                items_partida.append(
                    {
                        "id": product[0],
                        "name": product[1],
                        "udm": product[2],
                        "stock": product[3],
                        "partida": partida,
                        "section_index": section_index,
                        "reserved": product[4],
                        "available_stock": product[5],
                        "sku": sku,
                        "sku_fabricante": sku_fabricante,
                    }
                )
        else:
            items_normal.append(
                {
                    "id": product[0],
                    "name": product[1],
                    "udm": product[2],
                    "stock": product[3],
                    "partida": "",
                    "reserved": product[4],
                    "available_stock": product[5],
                    "sku": sku,
                    "sku_fabricante": sku_fabricante,
                }
            )
    data_out = {
        "data": {"contract": items_partida, "normal": items_normal},
        "msg": None,
        "error": None,
    }
    return data_out, 200


def calculate_items_delivered(items):
    total = 0
    dispatched_total = 0
    if isinstance(items, int):
        return 0
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


def extract_extra_info_sm_item(items: list[dict]):
    new_items = []
    need_aprove = False
    for item in items:
        # extract is_tool from extra info and erase is_tool from extra info
        extra_info: dict = item.get("extra_info", {})
        if extra_info is None:
            extra_info = {}
        item["is_tool"] = extra_info.get("is_tool", 0)
        if item["is_tool"] == 1:
            need_aprove = True
        # extra_info.pop("is_tool", None)
        approve_required = extra_info.get("approve_required", 0)
        if approve_required is None:
            approve_required = 1 if item["is_tool"] == 1 else 0
        extra_info["approve_required"] = approve_required
        item["extra_info"] = extra_info
        item["url"] = extra_info.get("url", "")
        item["approve_required"] = approve_required
        new_items.append(item)
    return new_items, need_aprove


def get_all_sm(limit, data_token, page=0, emp_id=-1, with_items=True):
    emp_id = None if emp_id == -1 else emp_id
    flag, error, result = get_sm_entries(data_token, emp_id)
    if limit == -1:
        limit = len(result) + 1
    limit = limit if limit > 0 else 10
    page = page if page >= 0 else 0
    if len(result) <= 0:
        return {"data": [], "page": 0, "pages": 0, "msg": None, "error": None}, 200
    pages = math.floor(len(result) / limit)
    if page > pages:
        return None, 204
    sm_list = []
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
            kpi_warehouse = "CUMPLE" if (admin_not_date - date_creation).days <= 2 else "NO CUMPLE"
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
            if op_not_date != "" and isinstance(op_not_date, str) and op_not_date is not None
            else None
        )
        if op_not_date is not None:
            kpi_operations = "CUMPLE" if (critical_date - critical_date).days >= 1 else "NO CUMPLE"
        else:
            kpi_operations = ""
        # process items from the sm
        items_sm = json.loads(result[i][10]) if with_items else []
        # extract state and approved required for sm item
        items_sm, approve_required = extract_extra_info_sm_item(items_sm)
        approve_required = 1 if approve_required else 0
        percentage = calculate_items_delivered(json.loads(result[i][10]))
        # process comments if not a json text create a list of the comments
        try:
            comment = json.loads(result[i][13])
        except Exception:
            comment = [result[i][13]]
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
            "comment": comment,
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
            "warehouse_notification_date": extra_info.get("warehouse_notification_date", ""),
            # "purchasing_kpi": extra_info.get("purchasing_kpi", 0),
            "admin_comments": extra_info.get("admin_comments", ""),
            "general_request_status": extra_info.get("general_request_status", 1),
            "operations_notification_date": extra_info.get("operations_notification_date", ""),
            "operations_kpi": kpi_operations,
            "requesting_user_state": extra_info.get("requesting_user_state", ""),
            "date_closing": extra_info.get("date_closing", ""),
            "approve_required": approve_required,
            "files": extra_info.get("files", [])
        }

        # if isinstance(extra_info, dict):
        #     for k, v in extra_info.items():
        #         dict_sm[k] = v
        sm_list.append(dict_sm)
    data_out = {"data": sm_list, "page": page, "pages": pages + 1, "msg": None, "error": None}
    return data_out, 200


def get_iddentifiers_creation_contracts(data_token):
    permissions = data_token.get("permissions", {}).values()
    contracts = []
    dict_tabs = {}
    if any(
        word in item.lower().split(".")[-1] for word in ["administrator"] for item in permissions
    ):
        flag, error, contracts = get_contract_by_client(40, data_token)
    else:
        for check_func in (check_if_leader,):
            flag, error, result = check_func(data_token.get("emp_id"), data_token)
            if flag and len(result) > 0:
                ids = []
                for item in result:
                    extra_info = json.loads(item[7])
                    ids += extra_info.get("contracts", [])
                    ids += extra_info.get("contracts_temp", [])
                ids = list(set(ids))
                flag, error, contracts = get_contracts_by_ids(ids, data_token)
                if not flag:
                    return {"data": None, "msg": error}, dict_tabs, 400
                break
    identifier_list = []
    for result in contracts:
        contract_number = result[5]
        idn_contract = contract_number[-4:]
        metadata_contract = json.loads(result[1])
        if str(idn_contract) not in identifier_list:
            identifier_list.append(f"{idn_contract}")
            dict_tabs[f"sm-{idn_contract}-"] = metadata_contract.get(
                "abbreviation_sm",
                metadata_contract.get("identifier", f"{idn_contract}"),
            )
    if not identifier_list:
        return {"data": None, "msg": "Folios for user not found"}, dict_tabs, 200
    return identifier_list, dict_tabs, 200


def get_iddentifiers_ternium(data_token):
    permissions = data_token.get("permissions", {}).values()
    contracts = []
    dict_tabs = {}
    last_part_perm = [item.lower().split(".")[-1] for item in permissions]
    if any(perm in word for perm in last_part_perm for word in ["administrator", "almacen"]):
        flag, error, contracts = get_contract_by_client(40, data_token)
    else:
        for check_func in (check_if_leader, check_if_auxiliar_with_contract):
            flag, error, result = check_func(data_token.get("emp_id"), data_token)
            if flag and len(result) > 0:
                ids = []
                for item in result:
                    extra_info = json.loads(item[7])
                    ids += extra_info.get("contracts", [])
                    ids += extra_info.get("contracts_temp", [])
                ids = list(set(ids))
                flag, error, contracts = get_contracts_by_ids(ids, data_token)
                if not flag:
                    return {"data": None, "msg": error}, dict_tabs, 400
                break

    identifier_list = []
    for result_contract in contracts:
        contract_number = result_contract[5]
        metadata_contract = json.loads(result_contract[1])
        idn_contract = contract_number[-4:]
        if str(idn_contract) not in identifier_list:
            identifier_list.append(f"{idn_contract}")
            dict_tabs[f"sm-{idn_contract}-"] = metadata_contract.get(
                "abbreviation_sm",
                metadata_contract.get("identifier", f"{idn_contract}"),
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
    if code != 200 or isinstance(iddentifiers, dict):
        iddentifiers = []
    abbs_list_departments, code = get_iddentifiers(
        data_token, ["administrator"], from_where="create_folio"
    )
    for abb in abbs_list_departments:
        dict_tabs[f"sm-{abb.lower()}-"] = abb
    if code != 200 or isinstance(abbs_list_departments, dict):
        abbs_list_departments = []
    data_sm, code = get_all_sm(-1, data_token, 0, -1)
    if code != 200:
        return {"data": {}, "msg": "No se pudieron obtener las SM", "error": str(data_sm)}, 400
    data_out = clasify_sm(iddentifiers + abbs_list_departments, data_sm, data_token, dict_tabs)
    return {"data": data_out, "msg": None, "error": None}, 200


def get_all_sm_control_table(data_token):
    iddentifiers_contracts, dict_tabs_contracts, code = get_iddentifiers_ternium(data_token)
    if code != 200 or isinstance(iddentifiers_contracts, dict):
        iddentifiers_contracts = []
    abbs_list_departments, code = get_iddentifiers(data_token, ["administrator"])
    if code != 200 or isinstance(abbs_list_departments, dict):
        abbs_list_departments = []
    for abb in abbs_list_departments:
        dict_tabs_contracts[f"sm-{abb.lower()}-"] = abb
    data_sm, code = get_all_sm(-1, data_token, 0, -1, with_items=False)
    if code != 200:
        return {"data": {}, "msg": "No se pudieron obtener las SM", "error": str(data_sm)}, 400
    data_out = clasify_sm(
        iddentifiers_contracts + abbs_list_departments,
        data_sm,
        data_token,
        dict_tabs_contracts,
    )
    return {"data": data_out, "msg": None, "error": None}, 200


def update_data_dicts(products: list, products_sm):
    for list_items in products:
        for item in list_items:
            for i, item_p in enumerate(products_sm):
                if item["id"] == item_p["id"]:
                    products_sm[i] = item
                    break
    return products_sm


def determine_status_sm(items: list):
    total_items = len(items)
    for item in items:
        if item["state"] == 4:
            total_items -= 1
    return 2 if total_items == 0 else 1


def eliminate_signaling_comment(comment: str):
    comment_out = (
        comment.replace("(Despachado)", "")
        .replace("(Semidespachado)", "")
        .replace("(Pedido)", "")
        .replace("(Cancelado)", "")
        .replace("(Nuevo)", "")
        .replace(";;", ";")
        # .strip("; ")
    )
    return comment_out


def dispatch_sm(data, data_token):
    if len(data["items"]) <= 0:
        return 400, {
            "msg": "No hay items para despachar en la SM",
            "error": "No item to update in sm",
        }
    flag, error, result = get_sm_by_id(data["id"], data_token)
    if not flag or len(result) <= 0:
        return 400, {"msg": "SM no encontrada", "error": "SM not found"}
    id_user = result[6]
    products_sm = json.loads(result[10])
    history_sm = json.loads(result[12])
    comment_general = json.loads(result[13])
    extra_info_sm = json.loads(result[14])
    folio = result[1]
    # products ids in the inventory
    ids_inventory_sm_list = [
        item["id_inventory"]
        for item in products_sm
        if item.get("state") > 0 and item.get("id_inventory") is not None
    ]
    updated_products = []
    flag, error, result = get_products_stock_from_ids(ids_inventory_sm_list, data_token)
    if not flag:
        return 400, {"msg": "No se pudo obtener el stock de los productos", "error": error}
    flag_semidespachado = False
    stocks = {item[0]: item[1] for item in result}
    comment_history = ""
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    dict_products_sm = {
        item["id"]: {**item, "dispatched": item.get("dispatched", 0)} for item in products_sm
    }
    msg_items = []
    operations_done = flag_semidespachado
    comments_items_updated = []
    for item_n in data["items"]:
        item_to_update = dict_products_sm.get(item_n["id"], {})
        old_item = item_to_update.copy()
        # si el item no existe
        if item_to_update is None:
            msg_items.append(f"Producto {item_n['id']}-{item_n['name']} no encontrado en la sm")
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
            data_token,
            "Despachado de SM",
        )
        if not flag:
            msg_items.append(
                f"x---Error al crear el movimiento para el item {item_to_update['id_inventory']}: {error}"
            )
            updated_products.append(old_item)
            continue
        msg_items.append(
            f"----Movimiento creado para el item {item_to_update['id_inventory']}: {str(result)}"
        )
        # -- actualizar stock del producto
        flag, error, res_stock = update_stock_db(
            item_to_update["id_inventory"], -item_n["quantity"], data_token, True
        )
        msg_items.append(
            f"x---Error al actualizar el stock para el producto {item_to_update['id_inventory']}: {error}"
        ) if not flag else msg_items.append(
            f"---Stock actualizado para el item {item_to_update['id_inventory']}: {str(res_stock)}"
        )
        # -- actualizar el estado de la reservación
        flag, error, res_res = complete_reservation_db(item_to_update["reservation_id"], data_token)
        msg_items.append(
            f"x---Error al tratar de completar la reservación {item_to_update['id']}: {error}"
        ) if not flag else msg_items.append(
            f"---Reservación completada {item_to_update['id']}: {str(res_res)}"
        )
        # verificar si se despacho por completo
        item_to_update["state"] = (
            4 if item_to_update["dispatched"] == item_to_update["quantity"] else 3
        )

        # insertar al inicio de los comentarios
        item_to_update["comment"] = f"{item_n['comment']}\n{item_to_update['comment']}"
        new_comment_item = item_n["comment"]
        if new_comment_item.strip() != "" and new_comment_item not in comments_items_updated:
            comments_items_updated.append(eliminate_signaling_comment(new_comment_item))
        # agregar los comandos
        item_to_update["comment"] += (
            " ;(Despachado) "
            if item_to_update["dispatched"] >= item_to_update["quantity"]
            else " ;(Semidespachado) "
        )
        comment_history += f"Despachado: {item_to_update['quantity']}->{item_to_update['id']}\n"
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
        return 400, {"msg": "No se realizaron operaciones de despacho", "error": msg_items}
    comment_history += "SM Despachada" if not flag_semidespachado else "SM Semidespachada"
    # agregar el comentario a los comentarios generales de las sm
    if len(comments_items_updated) > 0:
        comment_general.append(
            {
                "user": data_token["emp_id"],
                "date": date_now,
                "comment": "\n".join(comments_items_updated),
            }
        )
    history_sm.append(
        {
            "user": data_token["emp_id"],
            "event": "Accion de despachado",
            "date": date_now,
            "comment": comment_history + f" por el empleado {data_token['emp_id']}",
        }
    )
    errors, results_smi = update_items_sm(updated_products, data["id"], data_token)
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
        data["id"], history_sm, new_status, extra_info_sm, comment_general, data_token
    )
    msg_items.append(f"Historial actualizado: {str(result_his)}") if flag else msg_items.append(
        f"Error al actualizar el historial de la sm: {error}"
    )
    msg = (
        f"SM con ID-{data['id']} despachada por el empleado {data_token['emp_id']}"
        if not flag_semidespachado
        else f"SM con ID-{data['id']} semidespachada por el empleado {data_token['emp_id']}"
    )
    if msg_items:
        msg += "\n" + "\n".join(msg_items)
    write_log_file(log_file_sm_path, msg, data_token)
    create_notification_permission(
        msg, data_token, ["sm"], "SM Despachada", data_token["emp_id"], id_user
    )
    return 200, {"msg": msg_items}


def cancel_sm(data, data_token):
    flag, error, result = get_sm_by_id(data["id"], data_token)
    if not flag or len(result) <= 0:
        return {"data": None, "msg": "SM no encontrada", "error": "SM not found"}, 400
    history_sm = json.loads(result[12])
    comments_general = json.loads(result[13])
    emp_id_creation = result[6]
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history_sm.append(
        {
            "user": data_token["emp_id"],
            "event": "Cancelación",
            "date": date_now,
            "comment": data["comment"] + f"por el empleado {data_token['emp_id']}",
        }
    )
    comments_general.append(
        {
            "user": data_token["emp_id"],
            "date": date_now,
            "comment": data["comment"],
        }
    )
    flag, error, result = update_history_sm_from_cancel(
        data["id"], history_sm, comments_general, data_token, True
    )
    if flag:
        msg = f"SM con ID-{data['id']} cancelada"
        create_notification_permission(
            msg,
            data_token,
            ["sm"],
            "SM Cancelada",
            data_token["emp_id"],
            emp_id_creation,
        )
        write_log_file(log_file_sm_path, msg, data_token)
        return {
            "data": {"id_sm": data["id"]},
            "msg": f"SM cancelada correctamente (ID {data['id']})",
            "error": None,
        }, 200
    else:
        return {"data": None, "msg": "No se pudo cancelar la SM", "error": error}, 400


def get_employees_almacen(data_token):
    flag, error, result = get_emp_contract("almacen", data_token)
    data_out = []
    for item in result:
        id_emp, name, lastname = item
        data_out.append({"id": id_emp, "name": name.upper() + " " + lastname.upper()})
    return data_out, 200


def _downscale_signature_image(local_path, max_width=600):
    """Reduce la resolución de una firma grande para no engordar el PDF (la
    imagen se muestra chica pero reportlab la incrusta a su resolución de
    origen). Devuelve la misma ruta (reescrita in-place o intacta). No fatal:
    ante cualquier error devuelve la imagen original."""
    try:
        from PIL import Image

        with Image.open(local_path) as img:
            if img.width <= max_width:
                return local_path
            ratio = max_width / float(img.width)
            new_size = (max_width, max(1, int(img.height * ratio)))
            img.resize(new_size, Image.Resampling.LANCZOS).save(local_path)
        return local_path
    except Exception as e:
        print("erro downscale sm signature", str(e))
        return local_path


def _build_sm_delivery_files(files_sm, data_token):
    """
    Arma las filas de la tabla de entregas/firmas del PDF de la SM a partir de
    los attachments (``extra_info["files"]``): pre-llena No./fecha/título y
    descarga de S3 la firma de quien recibe para incrustarla. No fatal por
    archivo: si el attachment no es una imagen dibujable (pdf/zip) o falla la
    descarga, la fila queda con ``image_path=None`` (celda en blanco para firmar
    a mano). Siempre devuelve al menos una fila.
    """
    drawable = {"jpg", "jpeg", "png", "webp"}
    bucket_name = secrets.get("S3_ADMIN_BUCKET")
    tmp_dir = tempfile.mkdtemp()
    s3_client = None
    delivery_files = []
    for idx, f in enumerate(files_sm[:20], start=1):
        if not isinstance(f, dict):
            continue
        timestamp = f.get("timestamp") or ""
        date_str = timestamp.split(" ")[0] if timestamp else ""
        title = f.get("title") or f"Entrega {idx}"
        path_aws = f.get("path")
        filename = f.get("filename") or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        image_path = None
        if path_aws and ext in drawable:
            try:
                if s3_client is None:
                    s3_client = boto3.client("s3")
                local_path = os.path.join(tmp_dir, f"sign_{idx}_{os.path.basename(path_aws)}")
                s3_client.download_file(Bucket=str(bucket_name), Key=path_aws, Filename=local_path)
                image_path = _downscale_signature_image(local_path)
            except Exception as e:
                write_log_file(
                    log_file_sm_path,
                    f"No se pudo cargar la firma '{filename}' para el PDF de la SM: {str(e)}",
                    data_token,
                )
                image_path = None
        delivery_files.append(
            {"no": idx, "date": date_str, "title": title, "image_path": image_path}
        )
    if not delivery_files:
        delivery_files = [{"no": 1, "date": "", "title": "", "image_path": None}]
    return delivery_files


def dowload_file_sm(sm_id: int, data_token, type_file="pdf"):
    flag, error, result = get_sm_by_id(sm_id, data_token)
    if not flag or len(result) == 0 or result[0] is None:
        return {
            "data": None,
            "msg": f"SM con id {sm_id} no encontrada",
            "error": error or "SM no encontrada",
        }, 404
    folio = result[1]
    contract = result[2]
    facility = result[3]
    location = result[4]
    # client_id = result[5]
    # emp_id = result[6]
    order_quotation = result[7]
    date = pd.to_datetime(result[8], errors="coerce") if result[8] else None
    critical_date = pd.to_datetime(result[9], errors="coerce") if result[9] else None
    items = json.loads(result[10]) if isinstance(result[10], str) else result[10]
    # status = result[11]
    # history = json.loads(result[12])
    # comment/observations (result[13]) no se imprime en el documento
    try:
        extra_info = json.loads(result[14]) if result[14] else {}
    except Exception as e:
        print("erro download extra_info", str(e))
        extra_info = {}
    files_sm = extra_info.get("files", []) if isinstance(extra_info, dict) else []
    # una fila de entrega por attachment; descarga la firma de quien recibe de
    # S3 para incrustarla y pre-llena fecha/título (no fatal por archivo)
    delivery_files = _build_sm_delivery_files(files_sm, data_token) if type_file == "pdf" else []
    basename = f"sm_{folio}"
    download_path = (
        os.path.join(tempfile.mkdtemp(), os.path.basename(basename + ".pdf"))
        if type_file == "pdf"
        else os.path.join(tempfile.mkdtemp(), os.path.basename(basename + ".xlsx"))
    )
    products = []
    flag, error, result = get_info_names_by_sm_id(result[0], data_token)
    if flag and len(result) > 0:
        customer_name = result[0]
        emp_name = result[1] + " " + result[2]
    else:
        customer_name = "None"
        emp_name = "None"
    if items is None:
        items = []
    # Una SM sin items produce [{'id': None, ...}] por el LEFT JOIN + JSON_ARRAYAGG.
    items = [item for item in items if isinstance(item, dict) and item.get("id") is not None]
    for counter, item in enumerate(items, start=1):
        name = item.get("name") or "None"
        quantity = item.get("quantity") or 0
        comment = item.get("comment") or ""
        udm = item.get("udm") or "None"
        dispatched = item.get("dispatched") or 0
        if "(despachado)" in comment.lower():
            status = "Despachado"
        # "(Semidespachado)" no contiene "(despachado)" como substring (la "i" de
        # "semi" se interpone), así que sin esta rama un despacho parcial caía
        # hasta el else e imprimía "pendiente". Va después de "(Despachado)"
        # porque el comment acumula marcadores: si el item terminó completo,
        # ambos están presentes y gana el completo.
        elif "(semidespachado)" in comment.lower():
            status = "Semidespachado"
        elif "(pedido)" in comment.lower():
            status = "Pedido"
        elif "(nuevo)" in comment.lower():
            status = "Nuevo-Pedido"
        else:
            status = "pendiente"
        products.append((counter, name, quantity, udm, dispatched, status))

    if type_file == "pdf":
        flag = FileSmPDF(
            {
                "filename_out": download_path,
                "products": products,
                "metadata": {
                    "Fecha de Solicitud": date.strftime(format_date)
                    if isinstance(date, datetime) and not pd.isnull(date)
                    else "",
                    "Folio": folio,
                    "Contrato": contract,
                    "Usuario Solicitante": customer_name,
                    "Número de Pedido": order_quotation,
                    "Personal Telintec": emp_name,
                    "Planta": facility,
                    "Área Dirigida Telintec": location,
                    "Área / Ubicación": location,
                    "Fecha Crítica de Entrega": critical_date.strftime(format_date)
                    if isinstance(critical_date, datetime) and not pd.isnull(critical_date)
                    else "",
                },
                "delivery_files": delivery_files,
            },
        )
        if not flag:
            print("error at generating pdf", download_path)
            return {
                "data": None,
                "msg": f"No se pudo generar el PDF de la SM con id {sm_id}",
                "error": "Error al generar el PDF",
            }, 400
    else:
        lista_de_items = products
        # Definir los nombres de las columnas
        columnas = ["No.", "Nombre", "Cantidad", "Unidad de Medida", "C. Suministrado", "Estatus"]
        # Convertir la lista en un DataFrame
        df = pd.DataFrame(lista_de_items, columns=columnas)
        # Guardar el DataFrame en un archivo Excel
        df.to_excel(download_path, index=False)
    return download_path, 200


def create_customer(name, email, phone, rfc, address, data_token):
    flag, error, result = create_customer_db(name, email, phone, rfc, address, data_token)
    if flag:
        return {
            "data": {"id_customer": result},
            "msg": f"Cliente creado correctamente (ID {result})",
            "error": None,
        }, 201
    else:
        return {"data": None, "msg": "No se pudo crear el cliente", "error": error}, 400


def create_product(
    sku,
    name,
    udm,
    stock,
    id_category,
    id_supplier,
    data_token,
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
            data_token,
            codes,
            locations,
        )
    else:
        flag, error, result = create_product_db_admin(
            sku, name, udm, stock, id_category, data_token, codes
        )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el producto", "error": error}, 400
    return {
        "data": {"id_product": result},
        "msg": f"Producto creado correctamente (ID {result})",
        "error": None,
    }, 201


def update_sm_from_control_table(data, data_token, sm_data=None) -> tuple[int, dict]:
    if sm_data is None:
        flag, error, result = get_sm_by_id(data["id"], data_token)
    else:
        flag, error, result = True, None, sm_data
    if not flag or len(result) <= 0:
        return 400, {"data": None, "msg": "SM no encontrada", "error": "sm not found"}
    history_sm_json = result[12]
    history_sm_json = history_sm_json if history_sm_json else "[]"
    history_sm = json.loads(history_sm_json)
    emp_id_creation = result[6]
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    extra_info = json.loads(result[14]) if result[14] else {}

    comment_history = (
        f"Actualización de datos desde la tabla de control por el empleado {data_token.get('name')}"
    )
    comments = []
    for k, value in data["info"].items():
        if k == "comment":
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
        data["id"], extra_info, history_sm, comments, data_token
    )
    if flag:
        msg = f"SM con ID-{data['id']} actualizada"
        create_notification_permission(
            msg,
            data_token,
            ["sm", "almacen", "administracion"],
            "SM Actualizada",
            data_token.get("emp_id"),
            emp_id_creation,
        )
        write_log_file(log_file_sm_path, msg + "-->" + comment_history)
        return 200, {
            "data": {"id_sm": data["id"]},
            "msg": f"SM actualizada correctamente (ID {data['id']})",
            "error": None,
        }
    else:
        return 400, {"data": None, "msg": "No se pudo actualizar la SM", "error": error}


def check_item_sm_for_init_vals(items: list):
    all_avaliable = True
    items_out = []
    for item in items:
        items_out.append(item)
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


def check_for_partidas_updates(products: list, contract_id: int, data_token):
    flags, errors, results = ([], [], [])
    if contract_id is None or contract_id == 0:
        return flags, errors, results
    flag, error, old_items = get_items_quotation_from_cotract(contract_id, data_token)
    old_items = old_items if old_items is not None else []

    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    # La POS. reinicia por seccion, asi que la llave es (section_index, partida),
    # no partida sola. item[1]=partida, item[2]=id_inventory, item[4]=section_index.
    # Se normaliza a int para que el path PUT (partida como string) matchee las
    # llaves int de la BD y no dispare UPDATEs redundantes.
    dict_partidas = {}
    for row in old_items:
        partida_db = _safe_int(row[1])
        if partida_db is None:
            continue
        dict_partidas[(_safe_int(row[4]) or 0, partida_db)] = row[2]

    for item in products:
        partida = _safe_int(item.get("partida"))
        if partida is None or partida == 0:
            continue
        section_index = _safe_int(item.get("section_index", 0)) or 0
        key = (section_index, partida)
        id_inventory_old = dict_partidas.get(key, None)
        id_inventory_new = item.get("id", None)
        if id_inventory_new is None:
            continue
        if id_inventory_old != id_inventory_new:
            flag, error, result = update_quotation_item_partida_from_sm(
                contract_id, section_index, partida, id_inventory_new, data_token
            )
            if not flag:
                return [False], [error], [result]
            dict_partidas[key] = id_inventory_new
            flags.append(flag)
            errors.append(error)
            results.append(result)
    return flags, errors, results


def create_sm_from_api(data, data_token):
    if len(data["items"]) == 0:
        return {
            "data": None,
            "msg": "No hay items suficientes para crear la SM",
            "error": "No items detected",
        }, 400

    folio_new_sm = data["info"]["folio"]
    try:
        folio_parts = folio_new_sm.split("-")
        folio_pattern = "-".join(folio_parts[:2])
        flag, error, folios_old = get_folios_by_pattern(folio_pattern, data_token)
        for folio in folios_old:
            old_number = int(folio[0].split("-")[-1])
            new_number = int(folio_parts[2])
            if old_number < new_number <= old_number + 3:
                break
            elif new_number > old_number + 3:
                return {
                    "data": None,
                    "msg": "Folio consecutivo no permitido",
                    "error": "Folio consecutivo no permitido",
                }, 400
    except Exception as e:
        print("error parse folio: ", str(e))
        return {
            "data": None,
            "msg": "No se pudo extraer el folio para crear la SM",
            "error": str(e),
        }, 400
    # start creating sm
    extra_info = check_item_sm_for_init_vals(data["items"])
    flag, error, sm_result = insert_sm_db(data, data_token, extra_info)
    if not flag:
        print("error insert sm: ", error)
        return {"data": None, "msg": "No se pudo crear la SM", "error": error}, 400
    if sm_result is None:
        return {"data": None, "msg": "No se pudo crear la SM", "error": "sm_result is None"}, 400
    msg = (
        f"Nueva SM creada #{sm_result}, folio: {data['info']['folio']}, "
        f"fecha limite: {data['info']['critical_date']}, "
        f"empleado con id: {data_token.get('name')}, "
        f"comentario: {data['info']['comment']}"
    )
    errors_items, result_ids_items = create_items_sm_db(data["items"], sm_result, data_token)
    if len(result_ids_items) > 0:
        msg += f"\nItems creados: {result_ids_items}"
    if len(errors_items) > 0:
        msg += f"\nErrores al crear items: {errors_items}"
    flags, errors, result_partidas = check_for_partidas_updates(
        data["items"], data["info"]["contract_id"], data_token
    )
    if len(result_partidas) > 0:
        msg += f"\nPartidas actualizadas: {result_partidas}"
    if len(errors) > 0:
        msg += f"\nErrores al actualizar partidas: {errors}"
    create_notification_permission(
        msg,
        data_token,
        ["sm", "administracion", "almacen"],
        "Nueva SM Recibida",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sm_path, msg, data_token)
    # detalle largo -> log/notificacion; respuesta lleva data estructurado y error conciso
    error_list = [
        f"Item '{it.get('name')}' (inv {it.get('id_inventory')}) no se creó" for it in errors_items
    ] + [f"Partida: {e}" for e in errors]
    msg_out = f"SM creada correctamente (ID {sm_result})"
    if error_list:
        msg_out += f". {len(error_list)} elemento(s) no se pudieron crear."
    return {
        "data": {"id_sm": sm_result},
        "msg": msg_out,
        "error": error_list if error_list else None,
        "id_sm": sm_result,
    }, 201


def create_urgent_sm_from_api(data, data_token):
    if len(data["items"]) == 0:
        return {
            "data": None,
            "msg": "No hay items suficientes para crear la SM",
            "error": "No items detected",
        }, 400
    folio_new_sm = data["info"]["folio"]
    try:
        folio_parts = folio_new_sm.split("-")
        folio_pattern = "-".join(folio_parts[:2])
        flag, error, folios_old = get_folios_by_pattern(folio_pattern, data_token)
        for folio in folios_old:
            old_number = int(folio[0].split("-")[-1])
            new_number = int(folio_parts[2])
            if old_number < new_number <= old_number + 3:
                break
            elif new_number > old_number + 3:
                return {
                    "data": None,
                    "msg": "Folio consecutivo no permitido",
                    "error": "Folio consecutivo no permitido",
                }, 400
    except Exception as e:
        print("error at parsing folios: ", str(e))
        return {
            "data": None,
            "msg": "No se pudo extraer el folio para crear la SM",
            "error": str(e),
        }, 400
    extra_info = check_item_sm_for_init_vals(data["items"])
    flag, error, result = insert_urgent_sm_db(data, data_token, extra_info)
    if not flag:
        print("error inser urgent sm: ", error)
        return {"data": None, "msg": "No se pudo crear la SM", "error": error}, 400
    if result is None:
        return {"data": None, "msg": "No se pudo crear la SM", "error": "result is None"}, 400
    msg = (
        f"Nueva SM creada #{result}, folio: {data['info']['folio']}, "
        f"fecha limite: {data['info']['critical_date']}, "
        f"empleado con id: {data_token.get('name')}. "
    )
    errors_items, result_ids_items = create_items_sm_db(data["items"], result, data_token)
    if len(result_ids_items) > 0:
        msg += f"\nItems creados: {result_ids_items}"
    if len(errors_items) > 0:
        msg += f"\nErrores al crear items: {errors_items}"
    flags, errors, result_partidas = check_for_partidas_updates(
        data["items"], data["info"]["contract_id"], data_token
    )
    if len(result_partidas) > 0:
        msg += f"\nPartidas actualizadas: {result_partidas}"
    if len(errors) > 0:
        msg += f"\nErrores al actualizar partidas: {errors}"
    create_notification_permission(
        msg,
        data_token,
        ["sm", "administracion", "almacen"],
        "Nueva SM Recibida",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sm_path, msg, data_token)
    # detalle largo -> log/notificacion; respuesta lleva data estructurado y error conciso
    error_list = [
        f"Item '{it.get('name')}' (inv {it.get('id_inventory')}) no se creó" for it in errors_items
    ] + [f"Partida: {e}" for e in errors]
    msg_out = f"SM urgente creada correctamente (ID {result})"
    if error_list:
        msg_out += f". {len(error_list)} elemento(s) no se pudieron crear."
    return {
        "data": {"id_sm": result},
        "msg": msg_out,
        "error": error_list if error_list else None,
        "id_sm": result,
    }, 201


def check_if_items_sm_correct_for_update(items_in):
    all_ok = True
    error = None
    items_out = []
    for item in items_in:
        items_out.append(item)
        if item.get("quantity", 0) < 0:
            all_ok = False
            error = f"Item con id {item['id']} no tiene cantidad adecuada"
        if item.get("id_inventory", 0) <= 0:
            if item.get("id", 0) > 0:
                all_ok = False
                error = f"No se puede actualizar el item con id {item['id']} sin id de inventario"

    return all_ok, items_out, error


def update_sm_from_api(data, data_token):
    # check date maximun 24 hours
    date = data["info"].get("date", "2024-06-29")
    date_sm = pd.to_datetime(date)
    date_now = pd.to_datetime(datetime.now().strftime(format_date))
    if (date_sm - date_now).days > 1:
        return {
            "data": None,
            "msg": "El tiempo permitido para modificación no debe ser mayor a 24 horas",
            "error": "El tiempo permitido para modificacion no deber ser mayor a 24 horas",
        }, 400
    # check parse items
    flag, items_out, error = check_if_items_sm_correct_for_update(data.get("items", []))
    if not flag:
        return {
            "data": None,
            "msg": "Error en los items de la SM",
            "error": error,
        }, 400
    # update metada sm
    flag, error, result = update_sm_db(data, data_token)
    if flag:
        msg = (
            f"SM  actualizada  #{data['info']['id']}, folio: {data['info']['folio']}, "
            f"fecha limite: {data['info']['critical_date']}, "
            f"empleado con id: {data_token.get('emp_id')}, "
            f"comentario: {data['info']['comment']}"
        )
        # update items sm
        errors, results = update_items_sm(items_out, data["id"], data_token)
        flags, errors_p, result_partidas = check_for_partidas_updates(
            data["items"], data["info"]["contract_id"], data_token
        )
        if len(result_partidas) > 0:
            msg += f"\nPartidas actualizadas: {result_partidas}"
        if len(errors_p) > 0:
            msg += f"\nErrores al actualizar partidas: {errors_p}"
        if len(results) > 0:
            msg += f"\nItems actualizados: {results}"
        if len(errors) > 0:
            msg += f"\nErrores al actualizar items: {errors}"
        create_notification_permission(
            msg,
            data_token,
            ["sm", "administracion", "almacen"],
            "Nueva SM Recibida",
            data_token.get("emp_id"),
            0,
        )
        write_log_file(log_file_sm_path, msg, data_token)
        # detalle largo -> log/notificacion; respuesta lleva data estructurado y error conciso
        error_list = [f"Item {e.get('id')}: {e.get('error')}" for e in errors] + [
            f"Partida: {e}" for e in errors_p
        ]
        msg_out = f"SM actualizada correctamente (ID {data['id']})"
        if error_list:
            msg_out += f". {len(error_list)} elemento(s) no se pudieron actualizar."
        return {
            "data": {"id_sm": data["id"]},
            "msg": msg_out,
            "error": error_list if error_list else None,
            "id_sm": data["id"],
        }, 200
    else:
        return {"data": None, "msg": "No se pudo actualizar la SM", "error": error}, 400


def delete_sm_from_api(data, data_token):
    flag, error, result = delete_item_from_sm_id(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron eliminar los items de la SM",
            "error": error,
        }, 400
    msg = f"Items eliminados <{result}> de la sm con id: {data['id']}\n"
    flag, error, result = delete_sm_db(data["id"], data_token)
    if flag:
        msg += f"SM #{data['id']} eliminada, empleado con id: {data_token.get('emp_id')}"
        create_notification_permission(
            msg,
            data_token,
            ["sm", "administracion", "almacen"],
            "SM Eliminada",
            sender_id=data.get("id_emp"),
        )
        write_log_file(log_file_sm_path, msg, data_token)
        return {
            "data": {"id_sm": data["id"]},
            "msg": f"SM eliminada correctamente (ID {data['id']})",
            "error": None,
            "id_sm": data["id"],
        }, 200
    else:
        print("error create notification", error)
        return {"data": None, "msg": "No se pudo eliminar la SM", "error": error}, 400


def get_sm_folios_from_api(data_token):
    flag, error, result = get_sm_folios_db(data_token)
    if not flag:
        return {"data": [], "msg": "No se pudieron obtener los folios de SM", "error": error}, 400
    folios = []
    for item in result:
        folios.append(
            {
                "id": item[0],
                "folio": item[1],
            }
        )
    return {"msg": None, "data": folios, "error": None}, 200


def get_sm_items_from_api(data, data_token):
    # id_sm, mr.folio , name
    flag, error, result = get_sm_items_state(data.get("state", 0), data_token)
    if not flag:
        return {"data": [], "msg": "No se pudieron obtener los items de SM", "error": error}, 400
    items = []
    for item in result:
        items.append(
            {
                "id": item[0],
                "id_sm": item[1],
                "folio": item[2],
                "name": item[3],
            }
        )
    return {"msg": None, "data": items, "error": None}, 200


def update_sm_item_state_and_inventory(data, data_token):
    flag, error, result = update_inventory_state_sm_item_db(
        data.get("state", 0), data.get("id_inventory"), data.get("id_item"), data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el estado del item",
            "error": error,
        }, 400
    msg = f"Item con id {data.get('id_item')} actualizado a estado {data.get('state')} con id de inventario {data.get('id_inventory')}"
    create_notification_permission(
        msg,
        data_token,
        ["administracion", "almacen"],
        "SM Actualizada",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sm_path, msg, data_token)
    return {
        "msg": f"Item actualizado correctamente (ID {data.get('id_item')})",
        "data": result,
        "error": None,
    }, 200


def update_sm_item_state(data, data_token):
    flag, error, sm_data = get_sm_from_item(data.get("id_item"), data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo obtener la SM", "error": error}, 400
    state = data.get("state")
    if state <= 0:
        return {"data": None, "msg": "Estado inválido para el item", "error": "invalid state"}, 400
    if not (isinstance(sm_data, list) or isinstance(sm_data, tuple)):
        return {"data": None, "msg": "Datos de SM inválidos", "error": "invalid sm data"}, 400
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history_sm = json.loads(sm_data[12])
    msg = f"Item con id {data.get('id_item')} actualizado a estado {data.get('state')} de la sm {sm_data[0]}."
    history_sm.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Actualizar estado de sm",
            "date": date_now,
            "comment": msg,
        }
    )
    flag, error, result = update_state_sm_item_db(
        state, data.get("id_item"), history_sm, sm_data[0], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el estado del item",
            "error": error,
        }, 400
    create_notification_permission(
        msg,
        data_token,
        ["administracion", "almacen"],
        "SM Actualizada",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sm_path, msg, data_token)
    return {
        "msg": f"Item actualizado correctamente (ID {data.get('id_item')})",
        "data": result,
        "error": None,
    }, 200


def update_sm_item_approve(data, data_token):
    flag, error, sm_data = get_sm_from_item(data.get("id_item"), data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo obtener la SM", "error": error}, 400
    approve_required = data.get("approve_required", 0)
    if approve_required not in [0, 1]:
        return {
            "data": None,
            "msg": "Valor de aprobación inválido",
            "error": "invalid approve_required",
        }, 400
    if not (isinstance(sm_data, list) or isinstance(sm_data, tuple)):
        return {"data": None, "msg": "Datos de SM inválidos", "error": "invalid sm data"}, 400
    extra_info_item = {}

    items_sm = json.loads(sm_data[10])
    for item in items_sm:
        if item["id"] == data.get("id_item"):
            extra_info_item = item.get("extra_info", {})
            break
    extra_info_item["approve_required"] = approve_required
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history_sm = json.loads(sm_data[12])
    msg = f"Item con id {data.get('id_item')} actualizado a aprobacion {approve_required} de la sm {sm_data[0]}."
    history_sm.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Actualizar aprobacion de sm",
            "date": date_now,
            "comment": msg,
        }
    )
    flag, error, result = update_extra_info_sm_item_db(
        extra_info_item, data.get("id_item"), history_sm, sm_data[0], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar la aprobación del item",
            "error": error,
        }, 400
    create_notification_permission(
        msg,
        data_token,
        ["administracion", "almacen"],
        "SM Actualizada",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sm_path, msg, data_token)
    return {
        "msg": f"Item actualizado correctamente (ID {data.get('id_item')})",
        "data": result,
        "error": None,
    }, 200


def update_items_sm_from_api(data, data_token):
    """
    Actualiza items de una SM, genera notificación y registra historial.

    Espera:
      data: {
        "id_sm": <int|str>,
        "items": <list>
      }
      data_token: {
        "emp_id": <int|str>
      }
    """
    flag, result, sm_data = get_sm_by_id(data["id_sm"], data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo obtener la SM", "error": result}, 400

    timezone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)

    # Cargar historial de forma segura
    try:
        history_raw = sm_data[12]
        history_sm = json.loads(history_raw)
        if not isinstance(history_sm, list):
            history_sm = []
        extra_info = json.loads(sm_data[14])
        comments_sm = json.loads(sm_data[13])
    except Exception as e:
        return {"data": None, "msg": "No se pudo procesar la SM", "error": str(e)}, 400

    # Actualizar items
    errors, results = update_items_sm(data["items"], data["id_sm"], data_token)

    # Construcción de mensajes
    emp_id = data_token.get("emp_id")
    msg_parts = []

    if results:
        msg_parts.append(f"{len(results)} item(s) actualizado(s) por empleado {emp_id}.")
    if errors:
        msg_parts.append(f"{len(errors)} error(es) durante la actualización.")

    msg = (
        " ".join(msg_parts)
        if msg_parts
        else f"Sin cambios en los items. Operación registrada por empleado {emp_id}."
    )

    # Determinar código HTTP
    code = 200 if not errors else 400

    # Notificación (mensaje compacto con empleado)
    create_notification_permission(
        msg,
        data_token,
        ["sm", "administracion", "almacen"],
        "Nueva SM Recibida",
        emp_id,
        0,
    )

    # Escribir log
    write_log_file(log_file_sm_path, msg, data_token)

    # Comentario para historial (breve y profesional)
    comment_history = (
        f"Empleado {emp_id} actualizó {len(results)} item(s)"
        + (f" y hubo {len(errors)} error(es)." if errors else ".")
        if (results or errors)
        else f"Empleado {emp_id} registró la operación sin cambios."
    )

    # Registrar en historial con tu formato
    history_sm.append(
        {
            "user": emp_id,
            "event": "Actualizar aprobacion de sm",
            "date": date_now,
            "comment": comment_history,
        }
    )
    flag, error, result = update_history_extra_info_sm_by_id(
        data["id_sm"], extra_info, history_sm, comments_sm, data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial de la SM",
            "error": error,
        }, 400

    msg_out = (
        "Items actualizados correctamente"
        if code == 200
        else "Algunos items no se pudieron actualizar"
    )
    # detalle largo -> log/notificacion; respuesta lleva data estructurado y error conciso
    error_list = [f"Item {e.get('id')}: {e.get('error')}" for e in errors]
    return {
        "data": {"id_sm": data["id_sm"]},
        "msg": msg_out,
        "error": error_list if error_list else None,
        "id_sm": data["id_sm"],
    }, code


def update_items_bulk_sm_from_api(data, data_token):
    results = []
    errors = []
    for entry in data.get("updates", []):
        data_out, code = update_items_sm_from_api(entry, data_token)
        if code == 200:
            results.append({"id_sm": entry["id_sm"], "result": data_out})
        else:
            errors.append({"id_sm": entry["id_sm"], "error": data_out})
    if errors and not results:
        return {"msg": "No se pudo actualizar ningún item", "data": results, "error": errors}, 400
    if errors:
        return {
            "msg": "Algunos items no se pudieron actualizar",
            "data": results,
            "error": errors,
        }, 207
    return {"msg": "Todos los items actualizados", "data": results, "error": None}, 200


def create_sm_attachment_api(data, data_token):
    filename = data["filename"]
    if "firma" not in filename.lower():
        return {"data": None, "msg": "Nombre de archivo incorrecto", "error": "filename"}, 400
    id_report_name = filename.split("-")[0]
    try:
        if int(id_report_name) != int(data["id_sm"]) and int(data["id_sm"]) <= 0:
            return (
                {
                    "data": None,
                    "msg": "El nombre del archivo no corresponde al sm",
                    "error": "id mismatch",
                },
                400,
            )
    except Exception as e:
        return (
            {
                "data": None,
                "msg": "Error al procesar el nombre del archivo",
                "error": str(e),
            },
            400,
        )
    time_zone = pytz.timezone(timezone_software)
    # timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    flag, error, result = get_sm_by_id(data["id_sm"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo obtener la SM",
            "error": error,
        }, 400
    # get_sm_by_id devuelve una sola fila (tupla); antes se iteraba como lista
    # de SMs y el endpoint fallaba siempre con "resultado no es una lista"
    if len(result) == 0 or result[0] is None or int(result[0]) != int(data["id_sm"]):
        return {
            "data": None,
            "msg": f"No se pudo obtener la SM: SM con id {data['id_sm']} no encontrada",
            "error": "SM no encontrada",
        }, 400
    sm_data = result
    date_sm = sm_data[8]
    history = json.loads(sm_data[12])
    # reconocer el tipo de archivo [pdf, image, zip]
    filepath_down = data["filepath"]
    file_extension = filepath_down.split(".")[-1].lower()
    valid_extension = ["pdf", "jpg", "jpeg", "png", "zip", "webp"]
    if file_extension not in valid_extension:
        return (
            {"data": None, "msg": "Formato de archivo no valido", "error": file_extension},
            400,
        )
    # create name sm/year/month/day/filename
    path_aws = f"smData/{date_sm.strftime('%Y/%m/%d/')}{data['filename']}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_ADMIN_BUCKET")
    msg = f"Archivo adjunto agregado: {filename} al sm {data['id_sm']} por el empleado {data_token.get('name')}"
    status = sm_data[11]
    if "firma-recibido" in filename.lower():  # if is sign file change status to 1
        status = 5
        msg += " y estado actualizado a (firmado)"
    else:
        return {"data": None, "msg": "Nombre de archivo incorrecto", "error": "filename"}, 400

    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=str(bucket_name), Key=path_aws)
    except FileNotFoundError:
        return {
            "data": None,
            "msg": "Archivo local no encontrado",
            "error": "Local file not found",
        }, 400
    except NoCredentialsError:
        return {
            "data": None,
            "msg": "No se encontraron credenciales de AWS",
            "error": "AWS credentials not found",
        }, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {
                "data": None,
                "msg": "El bucket no existe",
                "error": f"Bucket does not exist: {bucket_name}",
            }, 400
        elif error_code == "AccessDenied":
            return {
                "data": None,
                "msg": "Acceso denegado al bucket",
                "error": f"Access denied to bucket: {bucket_name}",
            }, 400
        else:
            return {"data": None, "msg": "Error de AWS", "error": str(e)}, 400

    history.append(
        {
            "timestamp": timestamp.strftime(format_timestamps),
            "user": data_token.get("emp_id"),
            "action": "Adjuntar archivo",
            "comment": msg,
        }
    )
    extra_info = json.loads(sm_data[14]) if sm_data[14] else {}
    comments = json.loads(sm_data[13]) if sm_data[13] else []
    files = extra_info.get("files", [])
    # timestamp y title alimentan la tabla de entregas/firmas del PDF de la SM:
    # title lleva el número de entrega ("Entrega N") y timestamp la fecha
    files.append(
        {
            "filename": data["filename"],
            "path": path_aws,
            "timestamp": timestamp.strftime(format_timestamps),
            "title": data.get("title") or f"Entrega {len(files) + 1}",
        }
    )
    extra_info["files"] = files
    flag, error, rows_updated = update_history_status_sm(
        data["id_sm"], history, status, extra_info, comments, data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "El archivo se subió pero no se pudo actualizar el historial de la SM",
            "error": error,
        }, 400
    user_created_sm = sm_data[6]
    create_notification_permission_notGUI(
        msg,
        data_token,
        ["administracion", "sm"],
        data_token.get("emp_id"),
        user_created_sm,
    )
    write_log_file(log_file_sm_path, msg, data_token)
    return {"data": path_aws, "msg": msg, "error": None}, 201
