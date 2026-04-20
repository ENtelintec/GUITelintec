from templates.controllers.activities.remisions_controller import (
    update_report_activity_files,
)
import boto3
import json
import pytz
from datetime import datetime
from static.constants import secrets
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError
from static.constants import log_file_admin_collecions
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.activities.remisions_controller import update_activity_report
from templates.controllers.activities.remisions_controller import (
    get_remission_by_id,
)
from templates.controllers.activities.remisions_controller import delete_remission_db
from templates.controllers.activities.remisions_controller import (
    update_items_quotation_w_remission,
)
from templates.controllers.activities.remisions_controller import insert_remission
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
from templates.controllers.contracts.contracts_controller import (
    get_contract_and_items_from_number,
)
from templates.resources.midleware.MD_SM import get_iddentifiers_creation_contracts

from static.constants import timezone_software, format_timestamps
from templates.Functions_Utils import create_notification_permission
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
        status=data["status"], data_token=data_token,
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
            data_token=data_token,
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
    create_notification_permission(msg, data_token, ["administracion"], "Remisión Creada", user, 0)
    write_log_file(log_file_admin_collecions, msg)
    return {"data": results, "msg": "Ok"}, 201


def update_quotation_activity_from_api(data, data_token):
    # retrieve quotation activity registry:
    flag, error, result_qa = get_quotation_activity_by_id(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de cotización de actividad",
            "error": str(error),
        }, 400
    # get history
    history = json.loads(result_qa[14]) if result_qa[14] else []  # pyrefly: ignore
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
        dict_items = {int(item["qa_item_id"]): item for item in items}
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
                    data_token=data_token,
                )
                result = id_item
            else:
                if new_item.get("is_erased", 0) != 0:
                    flag, error, result = delete_quotation_activity_item(item_id, data_token)
                else:
                    # update old item
                    history_item = (
                        dict_items[item_id]["history"]
                        if dict_items[item_id]["history"]
                        else []
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
                            data_token=data_token,
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
    print(history)
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
        data_token=data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al actualizar registro de cotización de actividad, pero item/s actualizados",
            "error": str(error),
        }, 400
    create_notification_permission(
        msg, data_token, ["administracion"], "Cotización de actividad actualizada", user, 0
    )
    write_log_file(log_file_admin_collecions, msg)
    return {"data": result, "msg": "Ok", "error": None}, 200


def get_quotations_from_api(id_quotation: int | None, data_token):
    if id_quotation is not None and id_quotation <= 0:
        id_quotation = None
    flag, e, out = get_quotation_activity_by_id(id_quotation, data_token)
    if not flag:
        return {"data": None, "msg": str(e)}, 400
    if not (isinstance(out, list) or isinstance(out, tuple)):
        return {
            "data": None,
            "msg": "No se encontraron actividades de cotización validas",
        }, 400
    # if len(out)<=0:
    #     return {"data": out, "msg": "No se encontraron actividades de cotización"}, 200
    if isinstance(out, tuple):
        out = [out]
    data_out = []
    for item in out:
        data_out.append(
            {
                "id": item[0],
                "date_activity": item[1].strftime(format_timestamps)
                if not isinstance(item[1], str)
                else item[1],
                "folio": item[2],
                "client_id": item[3],
                "client_company_name": item[4],
                "client_contact_name": item[5],
                "client_phone": item[6],
                "client_email": item[7],
                "plant": item[8],
                "area": item[9],
                "location": item[10],
                "general_description": item[11],
                "comments": item[12],
                "status": item[13],
                "history": json.loads(item[14]) if item[14] else [],
                "items": json.loads(item[15]) if item[15] else [],
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def delete_quotation_activity_from_api(data, data_token):
    id_quotation = data["id"]
    user = data_token.get("emp_id", 0)
    msg = ""

    # Retrieve quotation activity registry:
    flag, error, result_qa = get_quotation_activity_by_id(id_quotation, data_token)
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
        flag, error, result = delete_quotation_activity_item(item["qa_item_id"], data_token)
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
    flag, error, result = delete_quotation_activity(id_quotation, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al eliminar registro de cotización de actividad",
            "error": str(error),
        }, 400
    msg += f"Actividad de cotización eliminada correctamente con id: {id_quotation}"
    create_notification_permission(
        msg, data_token, ["administracion"], "Cotización de actividad eliminada", user, 0
    )
    write_log_file(log_file_admin_collecions, msg)
    return {"data": result, "msg": "Ok"}, 200


def create_extra_info_remision(data: dict):
    extra_info = {}
    extra_info["pedido"] = data["metadata"].get("pedido", "")
    extra_info["pedido_exiros"] = data["metadata"].get("pedido_exiros", "")
    extra_info["activity"] = data["metadata"].get("activity", "")
    extra_info["remision"] = data["metadata"].get("remision", "")
    extra_info["remito"] = data["metadata"].get("remito", "")
    extra_info["date_report"] = data["metadata"].get("date_report", "")
    extra_info["date_sign"] = data["metadata"].get("date_sign", "")
    extra_info["date_delivery"] = data["metadata"].get("date_delivery", "")
    return 


def create_remission_control_table_from_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id", "desconocido")
    history_report = [
        {
            timestamp: timestamp,
            "user": user,
            "action": "Creación",
            "comment": "Creación de remision de actividad.",
        }
    ]
    quotation_id = data["metadata"].get("quotation_id", None)
    extra_info = create_extra_info_remision(data)
    flag, error, id_remission = insert_remission(
        date=data["metadata"]["date"],
        folio=data["metadata"]["folio"],
        client_id=data["metadata"]["client_id"],
        plant=data["metadata"].get("plant"),
        area=data["metadata"].get("area"),
        location=data["metadata"].get("location"),
        general_description=data["metadata"].get("general_description"),
        comments=data["metadata"].get("comments"),
        quotation_id=quotation_id if quotation_id or quotation_id > 0 else None,
        history=history_report,
        contract_id=data["metadata"].get("contract_id", None),
        pedido=data["metadata"].get("pedido", ""),
        pedido_exiros=data["metadata"].get("pedido_exiros", ""),
        extra_info=extra_info,
        data_token=data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al crear reporte de actividad",
            "error": str(error),
        }, 400
    msg = "Item en tabla de control creado correctamente con id: " + str(id_remission) + f" por el usuario {data_token['name']}."
    create_notification_permission(
        msg, data_token, ["administracion"], "Item de tabla de control creado", user, 0
    )
    write_log_file(log_file_admin_collecions, msg)
    return {"data": id_remission, "msg": "Ok"}, 201


def create_remission_from_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id", "desconocido")
    history_report = [
        {
            timestamp: timestamp,
            "user": user,
            "action": "Creación",
            "comment": "Creación de remision de actividad.",
        }
    ]
    quotation_id = data["metadata"].get("quotation_id", None)
    extra_info = create_extra_info_remision(data)
    flag, error, id_remission = insert_remission(
        date=data["metadata"]["date"],
        folio=data["metadata"]["folio"],
        client_id=data["metadata"]["client_id"],
        plant=data["metadata"].get("plant"),
        area=data["metadata"].get("area"),
        location=data["metadata"].get("location"),
        general_description=data["metadata"].get("general_description"),
        comments=data["metadata"].get("comments"),
        quotation_id=quotation_id if quotation_id or quotation_id > 0 else None,
        history=history_report,
        contract_id=data["metadata"].get("contract_id", None),
        pedido=data["metadata"].get("pedido", ""),
        pedido_exiros=data["metadata"].get("pedido_exiros", ""),
        extra_info=extra_info,
        data_token=data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al crear reporte de actividad",
            "error": str(error),
        }, 400
    if not isinstance(id_remission, int):
        return {
            "data": None,
            "msg": "Error al crear reporte de actividad, id_report no es un entero",
            "error": str(id_remission),
        }, 400
    flag_list = []
    errors = []
    results = []
    if data["metadata"]["quotation_id"] is not None:
        flag, error, result = update_items_quotation_w_remission(
            id_remission, data["metadata"]["quotation_id"], data_token
        )
        flag_list.append(flag)
        errors.append(str(error))
        results.append(result)
    else:
        # create items quoatation from report
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
                quotation_id=None,
                report_id=id_remission,
                description=item["description"],
                udm=item["udm"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                history=history_item,
                item_c_id=item.get("item_contract_id", None),
                data_token=data_token,
            )
            flag_list.append(flag)
            errors.append(str(error))
            results.append(id_item)
    if flag_list.count(True) == len(flag_list):
        msg = "Reporte de actividad creado correctamente con id: " + str(id_remission)
        if quotation_id is not None:
            msg += " y items de cotización actualizados correctamente"
        else:
            msg += " y items de cotización creados correctamente"
    elif flag_list.count(False) == len(flag_list):
        flag, error, result = delete_remission_db(id_remission, data_token)
        msg = "Error al crear items de cotización. Reporte eliminado."
        return {
            "data": results,
            "error": errors + [error],
            "msg": msg,
        }, 400
    else:
        msg = "Reporte de actividad creado con id: " + str(id_remission)
        if quotation_id is not None:
            msg += ", pero error al actualizar ciertos items de cotización"
        else:
            msg += ", pero error al crear ciertos items de cotización"
    create_notification_permission(
        msg, data_token, ["administracion"], "Remision de actividad creado", user, 0
    )
    write_log_file(log_file_admin_collecions, msg)
    return {"data": results, "msg": "Ok"}, 201


def get_remission_from_api(id_report: int | None, data_token):
    if id_report is not None and id_report <= 0:
        id_report = None
    flag, error, result = get_remission_by_id(id_report, data_token)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "No se encontraron reportes de actividad validos",
        }, 400
    if isinstance(result, tuple):
        result = [result]
    data_out = []
    for item in result:
        extra_info = json.loads(item[19])
        data_out.append(
            {
                "id": item[0],
                "date": item[1].strftime(format_timestamps)
                if not isinstance(item[1], str)
                else item[1],
                "folio": item[2],
                "client_id": item[3],
                "client_company_name": item[4],
                "client_contact_name": item[5],
                "client_phone": item[6],
                "client_email": item[7],
                "plant": item[8],
                "area": item[9],
                "location": item[10],
                "general_description": item[11],
                "comments": item[12],
                "quotation_id": item[13],
                "status": item[14],
                "history": json.loads(item[15]) if item[15] else [],
                "items": json.loads(item[16]) if item[16] else [],
                "files": json.loads(item[17]) if item[17] else [],
                "contract_id": item[18],
                "pedido": extra_info.get("pedido", ""),
                "pedido_exiros": extra_info.get("pedido_exiros", ""),
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def update_remission_from_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id", "desconocido")
    msg = ""

    # Retrieve report activity registry:
    flag, error, result_ra = get_remission_by_id(data["id"], data_token)
    if not(isinstance(result_ra, list) or isinstance(result_ra, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": "valor devuelto por la db no esperado",
        }, 400
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": str(error),
        }, 400

    history = result_ra[15]  
    history = json.loads(history) if history else []
    history.append(
        {
            timestamp: timestamp,
            "user": user,
            "action": "Actualización",
            "comment": "Actualización de remision de actividad.",
        }
    )
    quotation_id = data.get("quotation_id", None)
    # Update report activity:
    flag, error, result = update_activity_report(
        report_id=data["metadata"]["id"],
        date=data["metadata"]["date"],
        folio=data["metadata"]["folio"],
        client_id=data["metadata"]["client_id"],
        # client_company_name=data["metadata"]["client_company_name"],
        # client_contact_name=data["metadata"]["client_contact_name"],
        # client_phone=data["metadata"]["client_phone"],
        # client_email=data["metadata"]["client_email"],
        plant=data["metadata"]["plant"],
        area=data["metadata"]["area"],
        location=data["metadata"]["location"],
        general_description=data["metadata"]["description"],
        comments=data["metadata"]["comments"],
        quotation_id=quotation_id if quotation_id or quotation_id > 0 else None,
        history=history,
        status=data["metadata"]["status"],
        contract_id=data["metadata"].get("contract_id", None),
        pedido=data["metadata"].get("pedido", ""),
        pedido_exiros=data["metadata"].get("pedido_exiros", ""),
        data_token=data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al actualizar registro de remision  de actividad",
            "error": str(error),
        }, 400
    msg = "Remision de actividad actualizado correctamente con id: " + str(
        data["metadata"]["id"]
    )
    items_report = json.loads(result_ra[16]) if result_ra[16] else []
    dict_items = {int(item["qa_item_id"]): item for item in items_report}
    # Update items:
    flag_list = []
    errors = []
    results = []
    for item in data["items"]:
        if item["id"] is not None and item["id"] > 0:
            if item["is_erased"] == 1:
                flag, error, result = delete_quotation_activity_item(item["id"], data_token)
            else:
                history_item = dict_items[item["id"]]["history"]
                history_item.append(
                    {
                        timestamp: timestamp,
                        "user": user,
                        "action": "Actualización",
                        "comment": "Actualización de ítem de reporte de actividad.",
                    }
                )
                flag, error, result = update_quotation_activity_item(
                    item["id"],
                    quotation_id,
                    data["metadata"]["id"],
                    item.get("item_contract_id", None),
                    item["description"],
                    item["udm"],
                    item["quantity"],
                    item["unit_price"],
                    history_item, data_token,
                )
        else:
            history_item = [
                {
                    timestamp: timestamp,
                    "user": user,
                    "action": "Creación",
                    "comment": "Creación de ítem de reporte de actividad.",
                }
            ]
            flag, error, result = insert_quotation_activity_item(
                quotation_id=None,
                report_id=data["metadata"]["id"],
                description=item["description"],
                udm=item["udm"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                history=history_item,
                item_c_id=item.get("item_contract_id", None),
                data_token=data_token,
            )
        flag_list.append(flag)
        errors.append(str(error))
        results.append(result)
    if flag_list.count(True) == len(flag_list):
        msg += " y items de de remision actualizados correctamente"
    elif flag_list.count(False) == len(flag_list):
        msg += " pero error al actualizar ciertos items de remision"
    else:
        msg += " pero error al actualizar ciertos items de remision"
    create_notification_permission(
        msg, data_token, ["administracion"], "Remision de actividad actualizado", user, 0
    )
    write_log_file(log_file_admin_collecions, msg)
    return {"data": result, "msg": "Ok", "error": None}, 200


def delete_remission_from_api(data, data_token):
    id_remission = data["id"]
    user = data_token.get("emp_id", 0)
    msg = ""

    # Retrieve report activity registry:
    flag, error, result_ra = get_remission_by_id(id_remission, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": str(error),
        }, 400

    # Delete items:
    items = json.loads(result_ra[16]) if result_ra[16] else []  # pyrefly: ignore
    if len(items) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener ítems del reporte",
            "error": str(error),
        }, 400
    flags = []
    errors = []
    results = []
    for item in items:
        flag, error, result = delete_quotation_activity_item(item["qa_item_id"], data_token)
        flags.append(flag)
        errors.append(str(error))
        results.append(result)
    if flags.count(True) == len(flags):
        msg += "Ítems de reporte de actividad eliminados correctamente"
    elif flags.count(False) == len(flags):
        return {
            "data": results,
            "error": errors,
            "msg": "Error al eliminar ítems de reporte de actividad",
        }, 400
    else:
        msg += "Error al eliminar ciertos ítems del reporte de actividad"

    # Delete report activity:
    flag, error, result = delete_remission_db(id_remission, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al eliminar registro de reporte de actividad",
            "error": str(error),
        }, 400
    msg += f"Reporte de actividad eliminado correctamente con id: {id_remission}"
    create_notification_permission(
        msg, data_token, ["administracion"], "Reporte de actividad eliminado", user, 0
    )
    write_log_file(log_file_admin_collecions, msg)
    return {"data": result, "msg": "Ok"}, 200


def create_activity_report_attachment_api(data, data_token):
    filename = data["filename"]
    id_report_name = filename.split("-")[0]
    try:
        if (
            int(id_report_name) != int(data["id_report"])
            and int(data["id_report"]) <= 0
        ):
            return (
                {
                    "data": None,
                    "msg": "El nombre del archivo no corresponde al voucher",
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
    flag, error, result = get_remission_by_id(data["id_report"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting report by id",
            "error": str(error),
        }, 400
    if not isinstance(result, list):
        return {
            "data": None,
            "msg": "Error at getting report activity by id: result is not a list",
            "error": str(result),
        }, 400
    report_data = []
    for item in result:
        if int(item[0]) == int(data["id_report"]):
            report_data = item
            break
    if len(report_data) <= 0:
        return {
            "data": None,
            "msg": "Error at getting report activity by id: voucher not found",
            "error": str(report_data),
        }, 400
    date_report = report_data[1]
    history = json.loads(report_data[15])
    # reconocer el tipo de archivo [pdf, image, zip]
    filepath_down = data["filepath"]
    file_extension = filepath_down.split(".")[-1].lower()
    valid_extension = ["pdf", "jpg", "jpeg", "png", "zip", "webp"]
    if file_extension not in valid_extension:
        return (
            {"data": None, "msg": "Formato de archivo no valido"},
            400,
        )
    # create name vouchers_vehicles/year/month/day/filename
    path_aws = f"reportActivity/{date_report.strftime('%Y/%m/%d/')}{data['filename']}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_ADMIN_BUCKET")

    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=bucket_name, Key=path_aws)
    except FileNotFoundError:
        return {"data": None, "msg": "Local file not found"}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "AWS credentials not found"}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket does not exist: {bucket_name}"}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Access denied to bucket: {bucket_name}"}, 400
        else:
            return {"data": None, "msg": f"AWS error: {str(e)}"}, 400
    msg = f"Archivo adjunto agregado: {filename} al voucher {data['id_report']} por el empleado {data_token.get('name')}"
    status = report_data[14]
    if "firma-realizado" in filename.lower():  # if is sign file change status to 1
        status = 1
        msg += " y estado actualizado a (firmado)"
    if "firma-recibido" in filename.lower():  # if is sign file change status to 1
        status = 2
        msg += " y estado actualizado a (aprobado)"
    history.append(
        {
            "timestamp": timestamp.strftime(format_timestamps),
            "user": data_token.get("emp_id"),
            "action": "Adjuntar archivo",
            "comment": msg,
        }
    )
    files = json.loads(report_data[17])
    files.append(
        {
            "filename": data["filename"],
            "path": path_aws,
        }
    )
    flag, error, rows_updated = update_report_activity_files(
        data["id_report"], history, status, files, data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history report but file uploaded",
            "error": str(error),
        }, 400
    create_notification_permission_notGUI(
        msg, data_token, ["administracion", "operaciones", "sgi"], data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin_collecions, msg)
    return {"data": path_aws, "msg": msg}, 201


def download_report_activity_attachment_api(data, data_token):
    flag, error, result = get_remission_by_id(data["id_report"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting checklist vehicular by id",
            "error": str(error),
        }, 400
    if not isinstance(result, list):
        return {
            "data": None,
            "msg": "Error at getting checklist vehicular by id: result is not a list",
            "error": str(result),
        }, 400
    report_data = []
    for item in result:
        if item[0] == data["id_voucher"]:
            report_data = item
            break
    if len(report_data) <= 0:
        return {
            "data": None,
            "msg": f"Error at getting report activity by id: {data['id_voucher']} not in db",
            "error": str(report_data),
        }, 400
    files = json.loads(report_data[17]) if report_data[17] else []
    name_file = data["filename"]
    flag_found = False
    path_aws = ""
    for file in files:
        if file["filename"] == name_file:
            flag_found = True
            path_aws = file["path"]
            break
    if not flag_found:
        return {"data": None, "msg": "File not found in voucher"}, 400
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_ADMIN_BUCKET")
    try:
        s3_client.download_file(
            Bucket=bucket_name, Key=path_aws, Filename=data["filepath"]
        )
    except FileNotFoundError:
        return {"data": None, "msg": "Local file not found"}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "AWS credentials not found"}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket does not exist: {bucket_name}"}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Access denied to bucket: {bucket_name}"}, 400
        elif error_code == "NoSuchKey":
            return {"data": None, "msg": f"File not found: {path_aws}"}, 400
        else:
            return {"data": None, "msg": f"Error downloading file: {str(e)}"}, 400
    return {"path": data["filepath"]}, 200


def fetch_products_contracts(data_token):
    iddentifiers, dict_tabs, code = get_iddentifiers_creation_contracts(data_token)
    if not iddentifiers:
        return {"data": [], "msg": code}, 400
    data_out = []
    for iddentifier in iddentifiers:
        flag, error, result = get_contract_and_items_from_number(iddentifier, data_token)
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
