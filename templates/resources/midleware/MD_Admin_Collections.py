import json
from datetime import datetime

import boto3
import pytz
from botocore.exceptions import ClientError, NoCredentialsError

from static.constants import (
    format_timestamps,
    log_file_admin_collecions,
    secrets,
    timezone_software,
)
from templates.controllers.contracts.contracts_controller import (
    get_contract_and_items_from_number,
)
from templates.controllers.presales.remisions_controller import (
    delete_quotation_activity,
    delete_quotation_activity_item,
    delete_remission_db,
    get_quotation_activity_by_id,
    get_quotation_activity_items,
    get_remission_by_id,
    insert_quotation_activity,
    insert_quotation_activity_item,
    insert_remission,
    update_activity_report,
    update_quotation_activity,
    update_quotation_activity_item,
    update_report_activity_files,
)
from templates.Functions_Utils import (
    create_notification_permission,
    create_notification_permission_notGUI,
)
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.MD_SM import get_iddentifiers_creation_contracts

__author__ = "Edisson Naula"
__date__ = "$ 27/oct/2025  at 20:37 $"


def _coerce_extra_info(value) -> dict:
    """extra_info del item puede venir como dict (anidado en JSON_OBJECT) o como str (fetchall)."""
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def _flatten_items_unit_price_quotation(items: list) -> list:
    """Expone unit_price_quotation (sugerido de la cotizacion) plano en cada item del GET."""
    for it in items:
        extra_info_item = _coerce_extra_info(it.get("extra_info"))
        it["unit_price_quotation"] = extra_info_item.get("unit_price_quotation", 0)
    return items


# --- Historial resumido de cambios de la remision ---------------------------------
# Subconjunto curado de campos a vigilar; el front mapea cada field a su etiqueta.
_HISTORY_META_FIELDS = [
    "date", "folio", "client_id", "plant", "area", "location",
    "general_description", "comments", "status",
    "pedido", "pedido_exiros", "remision", "remito",
    "date_report", "date_sign", "date_delivery",
]
_HISTORY_ITEM_FIELDS = ["description", "udm", "quantity", "unit_price", "unit_price_quotation"]
_HISTORY_NUMERIC_FIELDS = {"quantity", "unit_price", "unit_price_quotation", "client_id", "status"}


def _normalize_history_value(field, value):
    """Normaliza un valor para comparar/almacenar en el diff (numericos a float, fechas a str)."""
    if value is None or value == "":
        return None
    if hasattr(value, "strftime"):  # date / datetime
        return value.strftime(format_timestamps)
    if field in _HISTORY_NUMERIC_FIELDS:
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value).strip()
    return str(value).strip()


def _diff_history_fields(old: dict, new: dict, fields: list) -> list:
    """Devuelve [{field, before, after}] para los campos curados que cambiaron."""
    changes = []
    for field in fields:
        before = _normalize_history_value(field, old.get(field))
        after = _normalize_history_value(field, new.get(field))
        if before != after:
            changes.append({"field": field, "before": before, "after": after})
    return changes


def _remission_meta_from_row(result_ra, extra_info: dict) -> dict:
    """Arma el dict de metadata curada a partir de la fila de activity_reports."""
    return {
        "date": result_ra[1],
        "folio": result_ra[2],
        "client_id": result_ra[3],
        "plant": result_ra[8],
        "area": result_ra[9],
        "location": result_ra[10],
        "general_description": result_ra[11],
        "comments": result_ra[12],
        "status": result_ra[14],
        "pedido": extra_info.get("pedido", ""),
        "pedido_exiros": extra_info.get("pedido_exiros", ""),
        "remision": extra_info.get("remision", ""),
        "remito": extra_info.get("remito", ""),
        "date_report": extra_info.get("date_report", ""),
        "date_sign": extra_info.get("date_sign", ""),
        "date_delivery": extra_info.get("date_delivery", ""),
    }


def _remission_meta_from_payload(metadata: dict, new_extra_info: dict, area=None, status=None) -> dict:
    """Arma el dict de metadata curada con los valores que se van a escribir.

    `area`/`status` permiten forzar el valor conservado (p. ej. tabla de control)
    para que no marquen un cambio espurio.
    """
    return {
        "date": metadata.get("date"),
        "folio": metadata.get("folio"),
        "client_id": metadata.get("client_id"),
        "plant": metadata.get("plant"),
        "area": area if area is not None else metadata.get("area"),
        "location": metadata.get("location"),
        "general_description": metadata.get("general_description"),
        "comments": metadata.get("comments"),
        "status": status if status is not None else metadata.get("status"),
        "pedido": new_extra_info.get("pedido", ""),
        "pedido_exiros": new_extra_info.get("pedido_exiros", ""),
        "remision": new_extra_info.get("remision", ""),
        "remito": new_extra_info.get("remito", ""),
        "date_report": new_extra_info.get("date_report", ""),
        "date_sign": new_extra_info.get("date_sign", ""),
        "date_delivery": new_extra_info.get("date_delivery", ""),
    }


def _diff_remission_items(old_items_map: dict, payload_items: list) -> list:
    """Resume altas/bajas/cambios de items: [{qa_item_id, description, action, fields:[...]}]."""
    items_changes = []
    for item in payload_items:
        item_id = item.get("id")
        if item_id is not None and item_id > 0:
            old_item = old_items_map.get(item_id, {})
            if item.get("is_erased") == 1:
                items_changes.append({
                    "qa_item_id": item_id,
                    "description": old_item.get("description", item.get("description", "")),
                    "action": "removed",
                    "fields": [],
                })
                continue
            old_suggested = _coerce_extra_info(old_item.get("extra_info")).get(
                "unit_price_quotation", 0
            )
            old_cmp = {
                "description": old_item.get("description"),
                "udm": old_item.get("udm"),
                "quantity": old_item.get("quantity"),
                "unit_price": old_item.get("unit_price"),
                "unit_price_quotation": old_suggested,
            }
            new_cmp = {
                "description": item.get("description"),
                "udm": item.get("udm"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price"),
                # el sugerido se preserva (la remision no lo envia): no debe marcar cambio
                "unit_price_quotation": old_suggested,
            }
            field_changes = _diff_history_fields(old_cmp, new_cmp, _HISTORY_ITEM_FIELDS)
            if field_changes:
                items_changes.append({
                    "qa_item_id": item_id,
                    "description": item.get("description", old_item.get("description", "")),
                    "action": "updated",
                    "fields": field_changes,
                })
        else:
            items_changes.append({
                "qa_item_id": None,
                "description": item.get("description", ""),
                "action": "added",
                "fields": [
                    {"field": f, "before": None, "after": _normalize_history_value(f, item.get(f))}
                    for f in _HISTORY_ITEM_FIELDS
                    if f != "unit_price_quotation"
                ],
            })
    return items_changes


def create_quotation_activity_from_api(data, data_token):
    # create quotation activity registry:
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    msg = ""
    user = data_token.get("emp_id")
    history_qa = [
        {
            "timestamp": timestamp,
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
        data_token=data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "error al crear registro de cotizacion de actividad",
            "error": error,
        }, 400
    msg += f"Actividad de cotización creada correctamente con id: {id_quotation}"

    # create items for quotation
    flag_list = []
    errors = []
    results = []
    history_item = [
        {
            "timestamp": timestamp,
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
            extra_info={"unit_price_quotation": item["unit_price"]},
            data_token=data_token,
        )
        flag_list.append(flag)
        errors.append(error)
        results.append(id_item)
    error_items = None
    if flag_list.count(True) == len(flag_list):
        pass
    elif flag_list.count(False) == len(flag_list):
        flag, error, result = delete_quotation_activity(id_quotation)  # pyrefly: ignore
        return {
            "data": None,
            "msg": "No se pudo crear ningún ítem; actividad de cotización eliminada",
            "error": errors + ([error] if not flag else []),
        }, 400
    else:
        error_items = [e for f, e in zip(flag_list, errors) if not f]
    msg_out = f"Actividad de cotización creada correctamente (ID {id_quotation})"
    if error_items:
        msg_out += f". {len(error_items)} ítems no se pudieron crear."
    create_notification_permission(msg_out, data_token, ["administracion"], "Actividad de cotización creada", user, 0)
    write_log_file(log_file_admin_collecions, msg_out, data_token)
    return {"data": {"id_quotation": id_quotation}, "msg": msg_out, "error": error_items}, 201


def update_quotation_activity_from_api(data, data_token):
    # retrieve quotation activity registry:
    flag, error, result_qa = get_quotation_activity_by_id(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de cotización de actividad",
            "error": error,
        }, 400
    # get history
    history = json.loads(result_qa[14]) if result_qa[14] else []  # pyrefly: ignore
    if len(history) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener historial de la cotización",
            "error": error,
        }, 400
    items = json.loads(result_qa[15]) if result_qa[15] else []  # pyrefly: ignore
    if len(items) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener ítems de la cotización",
            "error": error,
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
                        "timestamp": timestamp,
                        "user": user,
                        "action": "Creacion",
                        "comment": "Creación de ítem de actividad de cotización.",
                    }
                ]
                flag, error, _id_item = insert_quotation_activity_item(
                    quotation_id=data["id"],  # pyrefly: ignore
                    report_id=new_item.get("report_id", None),
                    description=new_item["description"],
                    udm=new_item["udm"],
                    quantity=new_item["quantity"],
                    unit_price=new_item["unit_price"],
                    history=history_item,
                    item_c_id=new_item.get("client_id", None),
                    extra_info={"unit_price_quotation": new_item["unit_price"]},
                    data_token=data_token,
                )
            else:
                if new_item.get("is_erased", 0) != 0:
                    flag, error, result = delete_quotation_activity_item(item_id, data_token)
                else:
                    # update old item
                    history_item = (
                        dict_items[item_id]["history"] if dict_items[item_id]["history"] else []
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
                                "timestamp": timestamp,
                                "user": user,
                                "action": "Actualización",
                                "comment": "Actualización de ítem de actividad de cotización.",
                            }
                        )
                        # El sugerido de la cotizacion siempre se actualiza en extra_info.
                        existing_item = dict_items[item_id]
                        extra_info_item = _coerce_extra_info(existing_item.get("extra_info"))
                        extra_info_item["unit_price_quotation"] = new_item["unit_price"]
                        # Si el item ya tiene remision (report_id), se protege el unit_price real;
                        # si no, unit_price = sugerido.
                        if existing_item.get("report_id"):
                            unit_price_to_write = existing_item.get("unit_price", new_item["unit_price"])
                        else:
                            unit_price_to_write = new_item["unit_price"]
                        flag, error, result = update_quotation_activity_item(
                            qa_item_id=item_id,
                            quotation_id=data["id"],
                            report_id=new_item.get("report_id", None),
                            item_c_id=new_item.get("client_id", None),
                            description=new_item["description"],
                            udm=new_item["udm"],
                            quantity=new_item["quantity"],
                            unit_price=unit_price_to_write,
                            history=history_item,
                            extra_info=extra_info_item,
                            data_token=data_token,
                        )
            flags.append(flag)
            errors.append(error)
            results.append(item_id)
    error_items = None
    if flags.count(True) == len(flags):
        pass
    elif flags.count(False) == len(flags):
        return {
            "data": None,
            "msg": "No se pudo actualizar ningún ítem de la actividad de cotización",
            "error": errors,
        }, 400
    else:
        error_items = [e for f, e in zip(flags, errors) if not f]
    history.append(
        {
            "timestamp": timestamp,
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
            "error": error,
        }, 400
    msg_out = f"Actividad de cotización actualizada correctamente (ID {data['id']})"
    if error_items:
        msg_out += f". {len(error_items)} ítems no se pudieron actualizar."
    create_notification_permission(
        msg_out, data_token, ["administracion"], "Cotización de actividad actualizada", user, 0
    )
    write_log_file(log_file_admin_collecions, msg_out, data_token)
    return {"data": {"id_quotation": data["id"]}, "msg": msg_out, "error": error_items}, 200


def get_quotations_from_api(id_quotation: int | None, data_token):
    if id_quotation is not None and id_quotation <= 0:
        id_quotation = None
    flag, e, out = get_quotation_activity_by_id(id_quotation, data_token)
    if not flag:
        return {"data": None, "msg": "Error al obtener actividades de cotización", "error": e}, 400
    if not (isinstance(out, list) or isinstance(out, tuple)):
        return {
            "data": [],
            "msg": "No se encontraron actividades de cotización válidas",
            "error": None,
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
                "items": _flatten_items_unit_price_quotation(
                    json.loads(item[15]) if item[15] else []
                ),
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


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
            "error": error,
        }, 400

    # Delete items:
    items = json.loads(result_qa[15]) if result_qa[15] else []  # pyrefly: ignore
    if len(items) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener ítems de la cotización",
            "error": error,
        }, 400
    flags = []
    errors = []
    results = []
    for item in items:
        flag, error, result = delete_quotation_activity_item(item["qa_item_id"], data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    if flags.count(True) == len(flags):
        pass
    elif flags.count(False) == len(flags):
        return {
            "data": None,
            "error": errors,
            "msg": "Error al eliminar ítems de actividad de cotización",
        }, 400
    # partial: continue — main entity still gets deleted

    # Delete quotation activity:
    flag, error, result = delete_quotation_activity(id_quotation, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al eliminar registro de cotización de actividad",
            "error": error,
        }, 400
    msg = f"Actividad de cotización eliminada correctamente (ID {id_quotation})"
    create_notification_permission(
        msg, data_token, ["administracion"], "Cotización de actividad eliminada", user, 0
    )
    write_log_file(log_file_admin_collecions, msg, data_token)
    return {"data": {"id_quotation": id_quotation}, "msg": msg, "error": None}, 200


def create_extra_info_remision(data: dict):
    extra_info = {}
    extra_info["pedido"] = data["metadata"].get("pedido", "")
    extra_info["pedido_exiros"] = data["metadata"].get("pedido_exiros", "")
    extra_info["activity"] = data["metadata"].get("activity")
    extra_info["remision"] = data["metadata"].get("remision", "")
    extra_info["remito"] = data["metadata"].get("remito", "")
    extra_info["date_report"] = data["metadata"].get("date_report", "")
    extra_info["date_sign"] = data["metadata"].get("date_sign", "")
    extra_info["date_delivery"] = data["metadata"].get("date_delivery", "")
    extra_info["user"] = data["metadata"].get("user", "")
    extra_info["project"] = (data["metadata"].get("project", ""),)
    extra_info["project_description"] = data["metadata"].get("project_description")
    extra_info["user_id"] = data["metadata"].get("user_id")

    return extra_info


def create_remission_control_table_from_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id", "desconocido")
    history_report = [
        {
            "timestamp": timestamp,
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
            "error": error,
        }, 400
    msg = (
        "Item en tabla de control creado correctamente con id: "
        + str(id_remission)
        + f" por el usuario {data_token['name']}."
    )
    create_notification_permission(
        msg, data_token, ["administracion"], "Item de tabla de control creado", user, 0
    )
    msg_out = f"Ítem de tabla de control creado correctamente (ID {id_remission})"
    write_log_file(log_file_admin_collecions, msg_out, data_token)
    return {"data": {"id_remission": id_remission}, "msg": msg_out, "error": None}, 201


def create_remission_from_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id", "desconocido")
    history_report = [
        {
            "timestamp": timestamp,
            "user": user,
            "action": "Creación",
            "comment": "Creación de remision de actividad.",
        }
    ]
    quotation_id = data["metadata"].get("quotation_id", 0)
    quotation_id = quotation_id if quotation_id and quotation_id > 0 else None
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
        quotation_id=quotation_id,
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
            "error": error,
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
    dict_quotation_items = {}
    if quotation_id is not None:
        flag, error, result = get_quotation_activity_items(quotation_id, data_token)
        if not flag:
            return {
                "data": None,
                "msg": "Error al obtener items de la cotización",
                "error": error,
            }, 400
        if not (isinstance(result, list) or isinstance(result, tuple)):
            return {
                "data": None,
                "msg": "Error al obtener items de la cotización, tipo de dato no esperado",
                "error": str(result),
            }, 400
        quotation_items = result
        dict_quotation_items = {
            int(item[0]): {
                "qa_item_id": item[0],
                "description": item[1],
                "udm": item[2],
                "quantity": item[3],
                "unit_price": item[4],
                "line_total": item[5],
                "history": item[6],
                "item_c_id": item[7],
                "report_id": item[8],
                "quotation_id": item[9],
                "extra_info": item[10],
            }
            for item in quotation_items
        }

    for remision_item in data["items"]:
        qa_item_id = remision_item["id"]
        if qa_item_id in dict_quotation_items.keys():
            history_item = dict_quotation_items[qa_item_id].get("history", [])
            history_item.append(
                {
                    "timestamp": timestamp,
                    "user": user,
                    "action": "Update from Remision",
                    "comment": "Se actualizo el item desde remision",
                }
            )
            # Preserva el sugerido (unit_price_quotation) que ya viene de la cotizacion;
            # unit_price pasa a ser el precio real de la remision.
            extra_info_item = _coerce_extra_info(
                dict_quotation_items[qa_item_id].get("extra_info")
            )
            flag, error, result = update_quotation_activity_item(
                qa_item_id,
                quotation_id,
                id_remission,
                dict_quotation_items[qa_item_id]["item_c_id"],
                remision_item["description"],
                remision_item["udm"],
                remision_item["quantity"],
                remision_item["unit_price"],
                history_item,
                data_token,
                extra_info=extra_info_item,
            )
            flag_list.append(flag)
            errors.append(error)
            results.append(result)
        else:
            history_item = [
                {
                    "timestamp": timestamp,
                    "user": user,
                    "action": "Creacion",
                    "comment": "Creación de ítem de actividad de cotización.",
                }
            ]
            flag, error, id_item = insert_quotation_activity_item(
                quotation_id=None,
                report_id=id_remission,
                description=remision_item["description"],
                udm=remision_item["udm"],
                quantity=remision_item["quantity"],
                unit_price=remision_item["unit_price"],
                history=history_item,
                item_c_id=remision_item.get("item_contract_id", None),
                extra_info={"unit_price_quotation": 0},
                data_token=data_token,
            )
            flag_list.append(flag)
            errors.append(error)
            results.append(id_item)

    error_items = None
    if flag_list.count(True) == len(flag_list):
        pass
    elif flag_list.count(False) == len(flag_list):
        flag, error, result = delete_remission_db(id_remission, data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún ítem; remisión eliminada",
            "error": errors + ([error] if not flag else []),
        }, 400
    else:
        error_items = [e for f, e in zip(flag_list, errors) if not f]
    msg_out = f"Remisión creada correctamente (ID {id_remission})"
    if error_items:
        msg_out += f". {len(error_items)} ítems no se pudieron crear."
    create_notification_permission(
        msg_out, data_token, ["administracion"], "Remisión de actividad creada", user, 0
    )
    write_log_file(log_file_admin_collecions, msg_out, data_token)
    return {"data": {"id_remission": id_remission}, "msg": msg_out, "error": error_items}, 201


def get_remission_from_api(id_report: int | None, data_token):
    if id_report is not None and id_report <= 0:
        id_report = None
    flag, error, result = get_remission_by_id(id_report, data_token)
    if not flag:
        return {"data": None, "msg": "Error al obtener remisiones", "error": error}, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": [],
            "msg": "No se encontraron remisiones válidas",
            "error": None,
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
                "items": _flatten_items_unit_price_quotation(
                    json.loads(item[16]) if item[16] else []
                ),
                "files": json.loads(item[17]) if item[17] else [],
                "contract_id": item[18],
                "pedido": extra_info.get("pedido", ""),
                "pedido_exiros": extra_info.get("pedido_exiros", ""),
                "activity": extra_info.get("activity"),
                "remision": extra_info.get("remision", ""),
                "remito": extra_info.get("remito", ""),
                "date_report": extra_info.get("date_report", ""),
                "date_sign": extra_info.get("date_sign", ""),
                "date_delivery": extra_info.get("date_delivery", ""),
                "project": extra_info.get("project", ""),
                "project_description": extra_info.get("project_description", ""),
                "user": extra_info.get("user", ""),
                "user_id": extra_info.get("user_id", ""),
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def update_remission_from_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id", "desconocido")

    # Retrieve report activity registry:
    flag, error, result_ra = get_remission_by_id(data["metadata"]["id"], data_token)
    if not (isinstance(result_ra, list) or isinstance(result_ra, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": "valor devuelto por la db no esperado",
        }, 400
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": error,
        }, 400

    history = result_ra[15]
    history = json.loads(history) if history else []
    quotation_id = data["metadata"].get("quotation_id", None)
    # Update report activity:
    extra_info = create_extra_info_remision(data)

    # Historial resumido de cambios (metadata + items) contra el estado previo.
    old_extra_info = _coerce_extra_info(result_ra[19])
    old_items_map = {
        int(it["qa_item_id"]): it
        for it in (json.loads(result_ra[16]) if result_ra[16] else [])
    }
    meta_changes = _diff_history_fields(
        _remission_meta_from_row(result_ra, old_extra_info),
        _remission_meta_from_payload(data["metadata"], extra_info),
        _HISTORY_META_FIELDS,
    )
    items_changes = _diff_remission_items(old_items_map, data["items"])
    history.append(
        {
            "timestamp": timestamp,
            "user": user,
            "action": "Actualización",
            "comment": "Actualización de remision de actividad.",
            "changes": {"metadata": meta_changes, "items": items_changes},
        }
    )

    flag, error, result = update_activity_report(
        report_id=data["metadata"]["id"],
        date=data["metadata"]["date"],
        folio=data["metadata"]["folio"],
        client_id=data["metadata"]["client_id"],
        plant=data["metadata"]["plant"],
        area=data["metadata"]["area"],
        location=data["metadata"]["location"],
        general_description=data["metadata"]["general_description"],
        comments=data["metadata"]["comments"],
        quotation_id=quotation_id if quotation_id or quotation_id > 0 else None,
        history=history,
        status=data["metadata"]["status"],
        contract_id=data["metadata"].get("contract_id", None),
        pedido=data["metadata"].get("pedido", ""),
        pedido_exiros=data["metadata"].get("pedido_exiros", ""),
        data_token=data_token,
        extra_info=extra_info,
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al actualizar registro de remision  de actividad",
            "error": error,
        }, 400
    dict_items = old_items_map
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
                        "timestamp": timestamp,
                        "user": user,
                        "action": "Actualización",
                        "comment": "Actualización de ítem de reporte de actividad.",
                    }
                )
                # Conserva el sugerido (unit_price_quotation); unit_price = real de la remision.
                extra_info_item = _coerce_extra_info(dict_items[item["id"]].get("extra_info"))
                flag, error, result = update_quotation_activity_item(
                    item["id"],
                    quotation_id,
                    data["metadata"]["id"],
                    item.get("item_contract_id", None),
                    item["description"],
                    item["udm"],
                    item["quantity"],
                    item["unit_price"],
                    history_item,
                    data_token,
                    extra_info=extra_info_item,
                )
        else:
            history_item = [
                {
                    "timestamp": timestamp,
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
                extra_info={"unit_price_quotation": 0},
                data_token=data_token,
            )
        flag_list.append(flag)
        errors.append(error)
        results.append(result)
    error_items = None
    if flag_list.count(True) == len(flag_list):
        pass
    elif flag_list.count(False) == len(flag_list):
        error_items = [e for f, e in zip(flag_list, errors) if not f]
    else:
        error_items = [e for f, e in zip(flag_list, errors) if not f]
    id_remission = data["metadata"]["id"]
    msg_out = f"Remisión actualizada correctamente (ID {id_remission})"
    if error_items:
        msg_out += f". {len(error_items)} ítems no se pudieron actualizar."
    create_notification_permission(
        msg_out, data_token, ["administracion"], "Remisión de actividad actualizada", user, 0
    )
    write_log_file(log_file_admin_collecions, msg_out, data_token)
    return {"data": {"id_remission": id_remission}, "msg": msg_out, "error": error_items}, 200


def update_remission_control_table_from_api(data, data_token):
    timezone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(timezone).strftime(format_timestamps)
    user = data_token.get("emp_id", "desconocido")

    flag, error, result_ra = get_remission_by_id(data["metadata"]["id"], data_token)
    if not (isinstance(result_ra, list) or isinstance(result_ra, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": "valor devuelto por la db no esperado",
        }, 400
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": error,
        }, 400

    area = result_ra[9]
    status = result_ra[14]

    history = result_ra[15]
    history = json.loads(history) if history else []

    old_extra_info = _coerce_extra_info(result_ra[19])
    existing_extra_info = dict(old_extra_info)
    existing_extra_info.update(create_extra_info_remision(data))

    # Historial resumido de cambios (solo metadata; la tabla de control no maneja items).
    # area/status se conservan del registro previo, por eso no deben marcar cambio.
    meta_changes = _diff_history_fields(
        _remission_meta_from_row(result_ra, old_extra_info),
        _remission_meta_from_payload(
            data["metadata"], existing_extra_info, area=area, status=status
        ),
        _HISTORY_META_FIELDS,
    )
    history.append(
        {
            "timestamp": timestamp,
            "user": user,
            "action": "Actualización",
            "comment": "Actualización de tabla de control de remision.",
            "changes": {"metadata": meta_changes, "items": []},
        }
    )

    quotation_id = data["metadata"].get("quotation_id", None)
    quotation_id = quotation_id if quotation_id and quotation_id > 0 else None

    flag, error, result = update_activity_report(
        report_id=data["metadata"]["id"],
        date=data["metadata"]["date"],
        folio=data["metadata"]["folio"],
        client_id=data["metadata"]["client_id"],
        plant=data["metadata"]["plant"],
        area=area,
        location=data["metadata"]["location"],
        general_description=data["metadata"]["general_description"],
        comments=data["metadata"]["comments"],
        quotation_id=quotation_id,
        history=history,
        status=status,
        contract_id=data["metadata"].get("contract_id", None),
        pedido=existing_extra_info.get("pedido", ""),
        pedido_exiros=existing_extra_info.get("pedido_exiros", ""),
        data_token=data_token,
        extra_info=existing_extra_info,
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al actualizar tabla de control de remision de actividad",
            "error": error,
        }, 400
    msg_out = f"Tabla de control de remisión actualizada correctamente (ID {data['metadata']['id']})"
    create_notification_permission(
        msg_out, data_token, ["administracion"], "Tabla de control actualizada", user, 0
    )
    write_log_file(log_file_admin_collecions, msg_out, data_token)
    return {"data": {"id_remission": data["metadata"]["id"]}, "msg": msg_out, "error": None}, 200


def delete_remission_from_api(data, data_token):
    id_remission = data["id"]
    user = data_token.get("emp_id", 0)

    # Retrieve report activity registry:
    flag, error, result_ra = get_remission_by_id(id_remission, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener registro de reporte de actividad",
            "error": error,
        }, 400

    # Delete items:
    items = json.loads(result_ra[16]) if result_ra[16] else []  # pyrefly: ignore
    if len(items) <= 0:
        return {
            "data": None,
            "msg": "Error al obtener ítems del reporte",
            "error": error,
        }, 400
    flags = []
    errors = []
    results = []
    for item in items:
        flag, error, result = delete_quotation_activity_item(item["qa_item_id"], data_token)
        flags.append(flag)
        errors.append(error)
        results.append(result)
    if flags.count(True) == len(flags):
        pass
    elif flags.count(False) == len(flags):
        return {
            "data": None,
            "error": errors,
            "msg": "Error al eliminar ítems de reporte de actividad",
        }, 400
    # partial: continue — main entity still gets deleted

    # Delete report activity:
    flag, error, result = delete_remission_db(id_remission, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al eliminar registro de reporte de actividad",
            "error": error,
        }, 400
    msg_out = f"Reporte de actividad eliminado correctamente (ID {id_remission})"
    create_notification_permission(
        msg_out, data_token, ["administracion"], "Reporte de actividad eliminado", user, 0
    )
    write_log_file(log_file_admin_collecions, msg_out, data_token)
    return {"data": {"id_remission": id_remission}, "msg": msg_out, "error": None}, 200


def create_activity_report_attachment_api(data, data_token):
    filename = data["filename"]
    id_report_name = filename.split("-")[0]
    try:
        if int(id_report_name) != int(data["id_report"]) and int(data["id_report"]) <= 0:
            return {
                "data": None,
                "msg": "El nombre del archivo no corresponde al voucher",
                "error": None,
            }, 400
    except Exception as e:
        return {
            "data": None,
            "msg": "Error al procesar el nombre del archivo",
            "error": str(e),
        }, 400
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    flag, error, result = get_remission_by_id(data["id_report"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener el reporte por ID",
            "error": error,
        }, 400
    if not isinstance(result, list):
        return {
            "data": None,
            "msg": "Error al obtener el reporte de actividad",
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
            "msg": f"Reporte no encontrado (ID {data['id_report']})",
            "error": None,
        }, 400
    date_report = report_data[1]
    history = json.loads(report_data[15])
    filepath_down = data["filepath"]
    file_extension = filepath_down.split(".")[-1].lower()
    valid_extension = ["pdf", "jpg", "jpeg", "png", "zip", "webp"]
    if file_extension not in valid_extension:
        return {
            "data": None,
            "msg": "Formato de archivo no válido",
            "error": None,
        }, 400
    path_aws = f"reportActivity/{date_report.strftime('%Y/%m/%d/')}{data['filename']}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_ADMIN_BUCKET")

    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=str(bucket_name), Key=path_aws)
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no configuradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Acceso denegado al bucket: {bucket_name}", "error": str(e)}, 400
        else:
            return {"data": None, "msg": "Error al subir archivo a S3", "error": str(e)}, 400
    log_msg = f"Archivo adjunto agregado: {filename} al voucher {data['id_report']} por el empleado {data_token.get('name')}"
    status = report_data[14]
    if "firma-realizado" in filename.lower():
        status = 1
        log_msg += " y estado actualizado a (firmado)"
    if "firma-recibido" in filename.lower():
        status = 2
        log_msg += " y estado actualizado a (aprobado)"
    history.append(
        {
            "timestamp": timestamp.strftime(format_timestamps),
            "user": data_token.get("emp_id"),
            "action": "Adjuntar archivo",
            "comment": log_msg,
        }
    )
    files = json.loads(report_data[17])
    files.append({"filename": data["filename"], "path": path_aws})
    flag, error, rows_updated = update_report_activity_files(
        data["id_report"], history, status, files, data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al actualizar el historial del reporte (archivo subido)",
            "error": error,
        }, 400
    create_notification_permission_notGUI(
        log_msg, data_token, ["administracion", "operaciones", "sgi"], data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin_collecions, log_msg, data_token)
    return {
        "data": {"path": path_aws},
        "msg": f"Archivo adjuntado correctamente al reporte (ID {data['id_voucher']})",
        "error": None,
    }, 201


def download_report_activity_attachment_api(data, data_token):
    flag, error, result = get_remission_by_id(data["id_report"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting checklist vehicular by id",
            "error": error,
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
            "msg": f"Reporte no encontrado (ID {data['id_voucher']})",
            "error": None,
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
        return {"data": None, "msg": "Archivo no encontrado en el reporte", "error": None}, 400
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_ADMIN_BUCKET")
    try:
        s3_client.download_file(Bucket=str(bucket_name), Key=path_aws, Filename=data["filepath"])
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no configuradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Acceso denegado al bucket: {bucket_name}", "error": str(e)}, 400
        elif error_code == "NoSuchKey":
            return {"data": None, "msg": f"Archivo no encontrado en S3: {path_aws}", "error": str(e)}, 400
        else:
            return {"data": None, "msg": "Error al descargar archivo de S3", "error": str(e)}, 400
    return {"data": {"path": data["filepath"]}, "msg": None, "error": None}, 200


def fetch_products_contracts(data_token):
    iddentifiers, dict_tabs, code = get_iddentifiers_creation_contracts(data_token)
    if not iddentifiers:
        return {
            "data": [],
            "msg": "No se pudieron obtener los contratos con productos",
            "error": code,
        }, 400
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
    return {"data": data_out, "msg": None, "error": None}, 200
