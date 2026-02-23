from templates.controllers.activities.remisions_controller import (
    delete_quotation_activity,
    delete_quotation_activity_item,
    get_quotation_activity_by_id,
    insert_quotation_activity_item,
    update_quotation_activity,
    update_quotation_activity_item,
)
from templates.controllers.activities.remisions_controller import (
    insert_quotation_activity,
)
from templates.controllers.contracts.remision_controller import delete_remission_item
from templates.controllers.contracts.contracts_controller import (
    get_contract_and_items_from_number,
)
from templates.resources.midleware.MD_SM import get_iddentifiers_creation_contracts

import json
from datetime import datetime

import pytz

from static.constants import log_file_admin, timezone_software, format_timestamps
from templates.Functions_Utils import create_notification_permission
from templates.controllers.contracts.remision_controller import (
    create_remission,
    create_remission_item,
    delete_remission,
    update_remission,
    get_remission_items,
    update_remission_item,
    delete_remission_items_by_remission,
    fetch_remissions_with_items,
)
from templates.misc.Functions_Files import write_log_file

__author__ = "Edisson Naula"
__date__ = "$ 27/oct/2025  at 20:37 $"


def create_quotation_activity_from_api(data, data_token):
    # create quotation activity registry:
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    msg = ""
    user = data_token.get("emp_id")
    history_qa = [
        {
            timestamp: timestamp,
            "user": user,
            "action": "Creacion",
            "comment": "Creación de actividad de cotización.",
        }
    ]
    flag, error, id_quotation = insert_quotation_activity(
        date_activity=data["date_activity"],
        folio=data["folio"],
        client_id=data["client_id"],
        client_company_name=data["client_company_name"],
        client_contact_name=data["client_contact_name"],
        client_phone=data["client_phone"],
        client_email=data["client_email"],
        plant=data["plant"],
        area=data["area"],
        location=data["location"],
        general_description=data["general_description"],
        comments=data["comments"],
        history=history_qa,
        status=data["status"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "error al crear registro de cotizacion de actividad",
            "error": str(error),
        }, 400
    msg += f"Actividad de cotización creada correctamente con id: {id_quotation}"

    # create items for quotation
    flag_list = []
    errors = []
    results = []
    history_item = [
        {
            timestamp: timestamp,
            "user": user,
            "action": "Creacion",
            "comment": "Creación de ítem de actividad de cotización.",
        }
    ]
    for item in data["items"]:
        flag, error, id_item = insert_quotation_activity_item(
            quotation_id=id_quotation,  # pyrefly: ignore
            report_id=item.get("report_id", None),
            description=item["description"],
            udm=item["udm"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            history=history_item,
            item_c_id=item.get("item_contract_id", None),
        )
        flag_list.append(flag)
        errors.append(str(error))
        results.append(id_item)
    if flag_list.count(True) == len(flag_list):
        msg += "Items de actividad de cotización creada correctamente"
    elif flag_list.count(False) == len(flag_list):
        flag, error, result = delete_quotation_activity(id_quotation)  # pyrefly: ignore
        msg += "Error al crear ítems de actividad de cotización. Actividad eliminada."
        return {
            "data": results,
            "error": errors + [error],
            "msg": msg,
        }, 400
    else:
        msg += "Error al crear ciertos ítems de la actividad de cotización"
    create_notification_permission(msg, ["administracion"], "Remisión Creada", user, 0)
    write_log_file(log_file_admin, msg)
    return {"data": results, "msg": "Ok"}, 201


def update_quotation_activity_from_api(data, data_token):
    # retrieve quotation activity registry:
    flag, error, result_qa = get_quotation_activity_by_id(data["id"])
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de cotización de actividad",
            "error": str(error),
        }, 400
    # get history
    history = result_qa[14] if result_qa[14] else []  # pyrefly: ignore
    if len(history) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener historial de la cotización",
            "error": str(error),
        }, 400
    items = json.loads(result_qa[15]) if result_qa[15] else []  # pyrefly: ignore
    if len(items) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener ítems de la cotización",
            "error": str(error),
        }, 400
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    user = data_token.get("emp_id")
    items_to_update = data["items"]
    msg = ""
    flags = []
    errors = []
    results = []
    if len(items_to_update) <= 0:
        msg += "No hay ítems para actualizar"
    else:
        dict_items = {item[0]: item for item in items}
        for new_item in items_to_update:
            item_id = new_item.get("id", 0)
            if item_id <= 0:
                # create new item
                history_item = [
                    {
                        timestamp: timestamp,
                        "user": user,
                        "action": "Creacion",
                        "comment": "Creación de ítem de actividad de cotización.",
                    }
                ]
                flag, error, id_item = insert_quotation_activity_item(
                    quotation_id=data["id"],  # pyrefly: ignore
                    report_id=new_item.get("report_id", None),
                    description=new_item["description"],
                    udm=new_item["udm"],
                    quantity=new_item["quantity"],
                    unit_price=new_item["unit_price"],
                    history=history_item,
                    item_c_id=new_item.get("client_id", None),
                )
                result = id_item
            else:
                # update old item
                history_item = (
                    json.loads(dict_items[item_id][8]) if dict_items[item_id][8] else []
                )
                if len(history_item) <= 0:
                    flag, error, result = (
                        False,
                        f"Historial de ítem vacío para item: {item_id}",
                        None,
                    )
                else:
                    history_item.append(
                        {
                            timestamp: timestamp,
                            "user": user,
                            "action": "Actualización",
                            "comment": "Actualización de ítem de actividad de cotización.",
                        }
                    )
                    flag, error, result = update_quotation_activity_item(
                        qa_item_id=item_id,
                        quotation_id=data["id"],
                        report_id=new_item.get("report_id", None),
                        item_c_id=new_item.get("client_id", None),
                        description=new_item["description"],
                        udm=new_item["udm"],
                        quantity=new_item["quantity"],
                        unit_price=new_item["unit_price"],
                        history=history_item,
                    )
            flags.append(flag)
            errors.append(str(error))
            results.append(item_id)
    if flags.count(True) == len(flags):
        msg += "Items de actividad de cotización actualizados correctamente: " + str(
            results
        )
    elif flags.count(False) == len(flags):
        msg += "Error al actualizar ítems de actividad de cotización. Reversión de cambios."
        return {
            "data": results,
            "error": errors,
            "msg": msg,
        }, 400
    else:
        msg += "Error al actualizar ciertos ítems de la actividad de cotización"
    history.append(
        {
            timestamp: timestamp,
            "user": user,
            "action": "Actualización",
            "comment": "Actualización de actividad de cotización\n" + msg,
        }
    )
    flag, error, result = update_quotation_activity(
        qa_id=data["id"],
        date_activity=data["date_activity"],
        folio=data["folio"],
        client_id=data["client_id"],
        client_company_name=data["client_company_name"],
        client_contact_name=data["client_contact_name"],
        client_phone=data["client_phone"],
        client_email=data["client_email"],
        plant=data["plant"],
        area=data["area"],
        location=data["location"],
        general_description=data["general_description"],
        comments=data["comments"],
        history=history,
        status=data["status"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al actualizar registro de cotización de actividad, pero item/s actualizados",
            "error": str(error),
        }, 400
    create_notification_permission(
        msg, ["administracion"], "Cotización de actividad actualizada", user, 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok", "error": None}, 200


def get_quotations_from_api(id_quotation: int|None, data_token):
    flag, e, out = get_quotation_activity_by_id(id_quotation)
    if not flag:
        return {"data": None, "msg": str(e)}, 400
    data_out = []
    if not (isinstance(out, list) or isinstance(out, tuple)):
        return {"data": None, "msg": "No se encontraron actividades de cotización"}, 400
    if isinstance(out[0], tuple):
        out = [out]
    data_out.append(
        {
            "id": out[0][0],
            "date_activity": out[0][1],
            "folio": out[0][2],
            "client_id": out[0][3],
            "client_company_name": out[0][4],
            "client_contact_name": out[0][5],
            "client_phone": out[0][6],
            "client_email": out[0][7],
            "plant": out[0][8],
            "area": out[0][9],
            "location": out[0][10],
            "general_description": out[0][11],
            "comments": out[0][12],
            "status": out[0][13],
            "history": out[0][14],
            "items": out[0][15],
        }
    )
    return {"data": data_out, "msg": "Ok"}, 200


def delete_quotation_activity_from_api(data, data_token):
    id_quotation = data["id"]
    user = data_token.get("emp_id", 0)
    msg = ""

    # Retrieve quotation activity registry:
    flag, error, result_qa = get_quotation_activity_by_id(id_quotation)
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de cotización de actividad",
            "error": str(error),
        }, 400

    # Delete items:
    items = json.loads(result_qa[15]) if result_qa[15] else []  # pyrefly: ignore
    if len(items) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener ítems de la cotización",
            "error": str(error),
        }, 400
    flags = []
    errors = []
    results = []
    for item in items:
        flag, error, result = delete_quotation_activity_item(item[0])
        flags.append(flag)
        errors.append(str(error))
        results.append(result)
    if flags.count(True) == len(flags):
        msg += "Ítems de actividad de cotización eliminados correctamente"
    elif flags.count(False) == len(flags):
        return {
            "data": results,
            "error": errors,
            "msg": "Error al eliminar ítems de actividad de cotización",
        }, 400
    else:
        msg += "Error al eliminar ciertos ítems de la actividad de cotización"

    # Delete quotation activity:
    flag, error, result = delete_quotation_activity(id_quotation)
    if not flag:
        return {
            "data": None,
            "msg": "Error al eliminar registro de cotización de actividad",
            "error": str(error),
        }, 400
    msg += f"Actividad de cotización eliminada correctamente con id: {id_quotation}"
    create_notification_permission(
        msg, ["administracion"], "Cotización de actividad eliminada", user, 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 200


def create_remission_items_from_api(products: list, id_remission: int):
    flags, errors, results = [], [], []
    for item in products:
        try:
            flag, error, id_item = create_remission_item(
                remission_id=id_remission,
                description=item.get("description", ""),
                quantity=item.get("quantity", 0),
                udm=item.get("udm", ""),
                price_unit=item.get("price_unit", 0),
                quotation_item_id=item.get("quotation_item_id", None),
            )
            flags.append(flag)
            errors.append(str(error))
            results.append(id_item)
        except Exception as e:
            flags.append(False)
            errors.append(str(e))
            results.append(None)

    return flags, errors, results


def create_remission_from_api(data, data_token):
    # Extraer campos clave del metadata
    remission_code = data["metadata"].pop("remission_code", "error rcode")
    client_id = data["metadata"].pop("client_id", 50)
    emission = data["metadata"].pop("emission", "error edate")
    status = data["metadata"].pop("status", 0)
    user = data_token.get("emp_id", "desconocido")

    msg = ""
    contract_id = data.get("contract_id", None)
    if not contract_id:
        return {
            "data": "No se encontró contrato asociado para la remisión",
            "error": "Falta contract_id en metadata",
            "msg": "Error al crear remisión",
        }, 400

    # Crear la remisión
    flag, error, id_remission = create_remission(
        remission_code,
        contract_id,
        client_id,
        emission,
        data["metadata"],
        user,
        status,
    )

    if not flag:
        return {
            "data": "No fue posible crear la remisión",
            "error": error,
            "msg": "Error al crear remisión",
        }, 400

    # Crear ítems de la remisión
    flag_list, error_list, result_list = create_remission_items_from_api(
        data["products"],
        id_remission,  # pyrefly: ignore
    )

    if flag_list.count(True) == len(flag_list):
        msg += "\nItems de remisión creados correctamente"
    elif flag_list.count(False) == len(flag_list):
        flag, error_r, result_r = delete_remission(id_remission)  # pyrefly: ignore
        return {
            "data": result_list,
            "error": error_list + [error_r],
            "msg": "Error al crear ítems. Remisión eliminada.",
        }, 400
    else:
        msg += "\nError al crear ciertos ítems de la remisión"

    msg += f"\nRemisión creada con ID-{id_remission} por el empleado {user}"
    create_notification_permission(msg, ["administracion"], "Remisión Creada", user, 0)
    write_log_file(log_file_admin, msg)

    return {"data": result_list, "msg": "Ok"}, 201


def update_remission_items_from_api(
    items_to_update: list, id_remission: int, items_to_create: list
):
    flags, errors, results, flags_operation = [], [], [], []
    for item in items_to_update:
        # Ítem existente → actualizar
        flag, error, result = update_remission_item(
            id_item=item.get("id"),
            description=item.get("description"),
            quantity=item.get("quantity"),
            udm=item.get("udm"),
            price_unit=item.get("price_unit"),
            quotation_item_id=item.get("quotation_item_id"),
        )
        flags.append(flag)
        errors.append(str(error))
        results.append(result)
        flags_operation.append("update")
    for item in items_to_create:
        # Ítem nuevo → crear
        flag, error, result = create_remission_item(
            remission_id=id_remission,
            description=item.get("description", ""),
            quantity=item.get("quantity", 0),
            udm=item.get("udm", ""),
            price_unit=item.get("price_unit", 0),
            quotation_item_id=item.get("quotation_item_id", None),
        )
        flags.append(flag)
        errors.append(str(error))
        results.append(result)
        flags_operation.append("create")

    return flags, errors, results, flags_operation


def update_remission_from_api(data, data_token):
    msg = ""
    id_remission = data["id"]
    user = data_token.get("emp_id", 0)

    # Inicializar trazabilidad por ítem
    item_changes = {
        "created": [],
        "updated": [],
        "failed": [],
    }

    items_to_delete = data.get("items_to_delete", [])
    # Eliminar ítems marcados para eliminación
    for item in items_to_delete:
        item_id = item.get("id", None)
        if item_id:
            flag, error, result = delete_remission_item(item_id)
            if flag:
                item_changes["updated"].append(item_id)
            else:
                item_changes["failed"].append({"item": item, "error": str(error)})
    # Obtener ítems actuales de la remisión
    flag, error, result = get_remission_items(id_remission)
    if not flag:
        return {"data": None, "msg": str(error)}, 400

    dict_items = {item[0]: item for item in result}  # pyrefly: ignore
    items = data["items"]
    new_items = [
        item
        for item in items
        if item.get("id", -1) == -1 or item.get("id") not in dict_items
    ]
    items_to_update = [
        item
        for item in items
        if item.get("id", -1) != -1 and item.get("id") in dict_items
    ]
    # Actualizar y crear ítems según corresponda
    flag_list, error_list, result_list, flags_operation = (
        update_remission_items_from_api(new_items, id_remission, items_to_update)
    )
    for i, flag in enumerate(flag_list):
        if flag:
            if flags_operation[i] == "update":
                item_changes["updated"].append(items[i].get("id"))
            else:
                item_changes["created"].append(result_list[i])
        else:
            item_changes["failed"].append({"item": items[i], "error": error_list[i]})
    msg += (
        f"Ítems actualizados para la remisión ID-{id_remission} por el empleado {user}"
    )

    # Validación de ítems
    if flag_list.count(True) == len(flag_list):
        msg += f"\nTodos los ítems fueron procesados correctamente ({len(flag_list)} ítems)"
    elif flag_list.count(False) == len(flag_list):
        return {
            "data": result_list,
            "error": error_list,
            "msg": "Error al actualizar ítems.",
        }, 400
    else:
        msg += (
            f"\nError parcial: {len(item_changes['failed'])} ítems fallaron"
            + str(error_list)
            + "\n"
            + str(result_list)
        )

    # Extraer campos clave
    remission_code = data["metadata"].pop("remission_code", "error rcode")
    client_id = data["metadata"].pop("client_id", 50)
    emission = data["metadata"].pop("emission", "error edate")
    status = data["metadata"].pop("status", 0)
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    history = data.get("history", [])
    history.append(
        {
            "timestamp": timestamp,
            "user": user,
            "action": "update",
            "comment": f"Actualizar remisión. Ítems creados: {len(item_changes['created'])}, "
            f"actualizados: {len(item_changes['updated'])}, fallidos: {len(item_changes['failed'])}",
        }
    )

    # Actualizar remisión
    flag, error, result = update_remission(
        id_remission, data["metadata"], history=history, status=status
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400

    msg += f"\nRemisión actualizada con ID-{id_remission} por el empleado {user}"
    create_notification_permission(
        msg, ["administracion"], "Remisión Actualizada", user, 0
    )
    write_log_file(log_file_admin, msg)

    return {
        "data": result,
        "error": error_list,
        "msg": msg,
        "changes": item_changes,
    }, 200


def delete_remission_from_api(data, data_token):
    id_remission = data["id"]
    user = data_token.get("emp_id", 0)

    # Eliminar ítems vinculados a la remisión
    flag, error, result = delete_remission_items_by_remission(id_remission)
    if not flag:
        return {"data": None, "msg": f"Error al eliminar ítems: {error}"}, 400

    # Eliminar la remisión
    flag, error, result = delete_remission(id_remission)
    if not flag:
        return {"data": None, "msg": f"Error al eliminar remisión: {error}"}, 400

    msg = f"Remisión eliminada con ID-{id_remission} por el empleado {user}"
    create_notification_permission(
        msg, ["administracion"], "Remisión Eliminada", user, 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 200


def fetch_remissions_by_status_db(status: str, data_token: dict):
    flag, error, data = fetch_remissions_with_items(status)

    if not flag:
        return {"data": [], "msg": str(error)}, 400

    data_out = []
    for item in data:  # pyrefly: ignore
        metadata = json.loads(item[5]) if item[5] else {}
        contract_id = item[6]
        items = json.loads(item[7]) if item[7] else []

        data_out.append(
            {
                "id": item[0],
                "code": item[1],
                "client_id": item[2],
                "contract_id": contract_id,
                "emission": item[3].strftime(format_timestamps)
                if not isinstance(item[3], str)
                else item[3],
                "status": item[4],
                "user": metadata.get("user", ""),
                "planta": metadata.get("planta", ""),
                "area": metadata.get("area", ""),
                "location": metadata.get("location", ""),
                "email": metadata.get("email", ""),
                "phone": metadata.get("phone", ""),
                "observations": metadata.get("observations", ""),
                "printed": metadata.get("printed", False),
                "items": items,
            }
        )

    return {"data": data_out, "msg": "Ok"}, 200


def fetch_products_contracts(data_token):
    iddentifiers, dict_tabs, code = get_iddentifiers_creation_contracts(data_token)
    if not iddentifiers:
        return {"data": [], "msg": code}, 400
    data_out = []
    for iddentifier in iddentifiers:
        flag, error, result = get_contract_and_items_from_number(iddentifier)
        if not flag:
            continue
        items = []
        for item in result:  # pyrefly: ignore
            if item[2] is None:
                continue
            items.append(
                {
                    "id": item[2],
                    "partida": item[3],
                    "id_inventory": item[4],
                    "description": item[5],
                    "udm": item[6],
                }
            )
        if len(items) == 0:
            continue

        data_out.append(
            {
                "id": result[0][0],  # pyrefly: ignore
                "metadata": json.loads(result[0][1])  # pyrefly: ignore
                if result[0][1]  # pyrefly: ignore
                else {},  # pyrefly: ignore
                "items": items,
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200
