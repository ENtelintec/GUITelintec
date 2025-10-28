# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 27/oct/2025  at 20:37 $"

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
            errors.append(error)
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
        data["products"], id_remission
    )

    if flag_list.count(True) == len(flag_list):
        msg += "\nItems de remisión creados correctamente"
    elif flag_list.count(False) == len(flag_list):
        flag, error_r = delete_remission(id_remission)
        return {
            "data": {result_list},
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
    products: list, id_remission: int, dict_items: dict
):
    flags, errors, results = [], [], []

    for item in products:
        try:
            item_id = item.get("id")
            if item_id and item_id in dict_items:
                # Ítem existente → actualizar
                flag, error, result = update_remission_item(
                    id_item=item_id,
                    description=item.get("description"),
                    quantity=item.get("quantity"),
                    udm=item.get("udm"),
                    price_unit=item.get("price_unit"),
                    quotation_item_id=item.get("quotation_item_id"),
                )
            else:
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
            errors.append(error)
            results.append(result)
        except Exception as e:
            flags.append(False)
            errors.append(str(e))
            results.append(None)

    return flags, errors, results


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

    # Si no hay ítems previos vinculados y se envían nuevos productos
    if data.get("quotation_item_id", 0) == 0 and len(data.get("products", [])) > 0:
        flag_list, error_list, result_list = create_remission_items_from_api(
            data["products"], id_remission
        )
        for i, flag in enumerate(flag_list):
            if flag:
                item_changes["created"].append(result_list[i])
            else:
                item_changes["failed"].append(
                    {"item": data["products"][i], "error": error_list[i]}
                )
        msg += f"Se crearon {len(item_changes['created'])} ítems para la remisión ID-{id_remission} por el empleado {user}"
    else:
        # Obtener ítems previos
        flag, error, result = get_remission_items(id_remission)
        if not flag:
            return {"data": None, "msg": str(error)}, 400

        dict_items = {item["id"]: item for item in result}
        products = data["products"]

        flag_list, error_list, result_list = update_remission_items_from_api(
            products, id_remission, dict_items
        )
        for i, flag in enumerate(flag_list):
            if flag:
                if products[i].get("id") in dict_items:
                    item_changes["updated"].append(products[i].get("id"))
                else:
                    item_changes["created"].append(result_list[i])
            else:
                item_changes["failed"].append(
                    {"item": products[i], "error": error_list[i]}
                )
        msg += f"Ítems actualizados para la remisión ID-{id_remission} por el empleado {user}"

    # Validación de ítems
    if flag_list.count(True) == len(flag_list):
        msg += f"\nTodos los ítems fueron procesados correctamente ({len(flag_list)} ítems)"
    elif flag_list.count(False) == len(flag_list):
        flag, error_r = delete_remission(id_remission)
        return {
            "data": {result_list},
            "error": error_list + [error_r],
            "msg": "Error al actualizar ítems. Remisión eliminada.",
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
    for item in data:
        metadata = json.loads(item[5]) if item[5] else {}
        items = json.loads(item[6]) if item[6] else []

        data_out.append(
            {
                "id": item[0],
                "code": item[1],
                "client_id": item[2],
                "emission": item[3],
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
