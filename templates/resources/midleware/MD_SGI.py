# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta

import boto3
import pytz
from botocore.exceptions import ClientError, NoCredentialsError

from static.constants import (
    format_date,
    format_timestamps,
    log_file_sgi_chv,
    secrets,
    timezone_software,
)
from templates.controllers.vouchers.vouchers_controller import (
    create_voucher_general,
    create_voucher_item,
    create_voucher_safety,
    create_voucher_tools,
    create_voucher_vehicle,
    delete_items_voucher,
    delete_voucher_item,
    delete_voucher_tools,
    delete_voucher_vehicle,
    get_vouchers_safety_with_items,
    get_vouchers_tools_with_items_date,
    get_vouchers_vehicle_with_items,
    update_history_voucher,
    update_state_safety_voucher,
    update_state_tools_voucher,
    update_voucher_general_from_delete,
    update_voucher_item,
    update_voucher_safety,
    update_voucher_tools,
    update_voucher_vehicle,
    update_voucher_vehicle_files,
    update_voucher_vehicle_status,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.misc.Functions_Files import write_log_file

__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"


def create_voucher_tools_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"], data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el voucher general", "error": error}, 400
    flag, error, v_tools_id = create_voucher_tools(
        lastrowid,
        data["position"],
        data["type_transaction"],
        data["superior"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo crear el voucher de herramientas",
            "error": error,
        }, 400
    history = [
        {
            "id_voucher": v_tools_id,
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher creado",
        }
    ]
    flag, error, rows_updated = update_history_voucher(history, lastrowid, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, p_id = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            data_token,
            item["observations"],
        )
        if not flag:
            errors.append({"id_inventory": item["id_inventory"], "error": error})
    if data["items"] and len(errors) == len(data["items"]):
        delete_items_voucher(lastrowid, data_token)
        delete_voucher_tools(lastrowid, data_token)
        update_voucher_general_from_delete(lastrowid, [], data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún item del voucher; operación revertida",
            "error": errors,
        }, 400
    msg_out = f"Voucher de herramientas creado correctamente (ID {lastrowid})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron crear."
    return {
        "data": {"id_voucher": lastrowid},
        "msg": msg_out,
        "error": errors if errors else None,
    }, 201


def update_voucher_tools_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher_general"],
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher tools actualizado",
        }
    )
    flag, error, rows_updated = update_voucher_tools(
        data["id_voucher_general"],
        data["position"],
        data["type_transaction"],
        data["superior"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
        data["user_state"],
        data["superior_state"],
        data["storage_state"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher de herramientas",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, result = delete_voucher_item(item["id_item"], data_token)
        elif item["id_item"] > 0:
            flag, error, result = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        else:
            flag, error, result = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        if not flag:
            errors.append({"id_item": item["id_item"], "error": error})
    id_ = data["id_voucher_general"]
    msg_out = f"Voucher de herramientas actualizado correctamente (ID {id_})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron procesar."
    return {"data": {"id_voucher": id_}, "msg": msg_out, "error": errors if errors else None}, 200


def delete_voucher_tools_api(data, data_token):
    flag, error, rows_updated = delete_items_voucher(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron eliminar los items del voucher",
            "error": error,
        }, 400
    flag, error, rows_updated = delete_voucher_tools(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo eliminar el voucher de herramientas",
            "error": error,
        }, 400
    history = data["history"]
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history.append(
        {
            "id_voucher": data["id"],
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher eliminado",
        }
    )
    flag, error, result = update_voucher_general_from_delete(data["id"], history, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher general",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id"]},
        "msg": f"Voucher de herramientas eliminado correctamente (ID {data['id']})",
        "error": None,
    }, 200


def create_voucher_safety_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"], data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el voucher general", "error": error}, 400
    flag, error, lastrowid_safety = create_voucher_safety(
        lastrowid,
        data["motive"],
        data["epp_emp"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo crear el voucher de seguridad",
            "error": error,
        }, 400
    history = [
        {
            "id_voucher": lastrowid_safety,
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher creado",
        }
    ]
    flag, error, rows_updated = update_history_voucher(history, lastrowid, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, lastrowid_item = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            data_token,
            item["observations"],
        )
        if not flag:
            errors.append({"id_item": lastrowid_item, "error": error})
    if data["items"] and len(errors) == len(data["items"]):
        delete_items_voucher(lastrowid, data_token)
        delete_voucher_tools(lastrowid, data_token)
        update_voucher_general_from_delete(lastrowid, [], data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún item del voucher; operación revertida",
            "error": errors,
        }, 400
    msg_out = f"Voucher de seguridad creado correctamente (ID {lastrowid})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron crear."
    return {
        "data": {"id_voucher": lastrowid},
        "msg": msg_out,
        "error": errors if errors else None,
    }, 201


def update_voucher_safety_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher_general"],
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher safety actualizado",
        }
    )
    flag, error, rows_changed = update_voucher_safety(
        data["id_voucher_general"],
        data["epp_emp"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
        data["epp_state"],
        data["storage_state"],
        data["motive"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher de seguridad",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, lastrowid = delete_voucher_item(item["id_item"], data_token)
        elif item["id_item"] > 0:
            flag, error, lastrowid = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        else:
            flag, error, lastrowid = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        if not flag:
            errors.append({"id_inventory": item["id_inventory"], "error": error})
    id_ = data["id_voucher_general"]
    msg_out = f"Voucher de seguridad actualizado correctamente (ID {id_})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron procesar."
    return {"data": {"id_voucher": id_}, "msg": msg_out, "error": errors if errors else None}, 200


def delete_voucher_safety_api(data, data_token):
    flag, error, rows_updated = delete_items_voucher(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron eliminar los items del voucher",
            "error": error,
        }, 400
    flag, error, rows_updated = delete_voucher_tools(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo eliminar el voucher de seguridad",
            "error": error,
        }, 400
    history = data["history"]
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history.append(
        {
            "id_voucher": data["id"],
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher eliminado",
        }
    )
    flag, error, result = update_voucher_general_from_delete(data["id"], history, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher general",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id"]},
        "msg": f"Voucher de seguridad eliminado correctamente (ID {data['id']})",
        "error": None,
    }, 200


def get_vouchers_tools_api(data, data_token):
    flag, error, result = get_vouchers_tools_with_items_date(
        data["date"], data_token, data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron obtener los vouchers de herramientas",
            "error": error,
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener vouchers: resultado inesperado",
            "error": str(result),
        }, 400
    data_out = []
    for item in result:
        data_out.append(
            {
                "id_voucher_general": item[0],
                "type": item[1],
                "date": item[2].strftime(format_timestamps)
                if not isinstance(item[2], str)
                else item[2],
                "contract": item[3],
                "position": item[4],
                "type_transaction": item[5],
                "user": item[6],
                "superior": item[7],
                "storage_emp": item[8],
                "designated_emp": item[9],
                "user_state": item[10],
                "superior_state": item[11],
                "storage_state": item[12],
                "extra_info": json.loads(item[13]),
                "items": json.loads(item[14]),
                "history": json.loads(item[15]),
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def get_vouchers_safety_api(data, data_token):
    flag, error, result = get_vouchers_safety_with_items(
        data["date"], data_token=data_token, user=data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron obtener los vouchers de seguridad",
            "error": error,
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener vouchers: resultado inesperado",
            "error": str(result),
        }, 400
    data_out = []
    for item in result:
        data_out.append(
            {
                "id_voucher_general": item[0],
                "type": item[1],
                "date": item[2].strftime(format_timestamps)
                if not isinstance(item[2], str)
                else item[2],
                "contract": item[3],
                "motive": item[4],
                "user": item[5],
                "epp_emp": item[6],
                "storage_emp": item[7],
                "designated_emp": item[8],
                "user_state": item[9],
                "epp_state": item[10],
                "storage_state": item[11],
                "extra_info": json.loads(item[12]),
                "items": json.loads(item[13]),
                "history": json.loads(item[14]),
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def update_status_tools(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher"],
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": f"Voucher tools actualizado de estados: "
            f"{data['user_state']}-{data['superior_state']}-{data['storage_state']}",
        }
    )
    flag, error, rows_updated = update_state_tools_voucher(
        data["id_voucher"],
        data["user_state"],
        data["superior_state"],
        data["storage_state"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el estado del voucher de herramientas",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(history, data["id_voucher"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id_voucher"]},
        "msg": f"Estado del voucher de herramientas actualizado correctamente (ID {data['id_voucher']})",
        "error": None,
    }, 200


def update_status_safety(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher"],
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": f"Voucher safety actualizado de estados: "
            f"{data['user_state']}-{data['epp_state']}-{data['storage_state']}",
        }
    )
    flag, error, rows_updated = update_state_safety_voucher(
        data["id_voucher"],
        data["user_state"],
        data["epp_state"],
        data["storage_state"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el estado del voucher de seguridad",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(history, data["id_voucher"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id_voucher"]},
        "msg": f"Estado del voucher de seguridad actualizado correctamente (ID {data['id_voucher']})",
        "error": None,
    }, 200


def get_vouchers_vehicle_api(data, data_token):
    flag, error, result = get_vouchers_vehicle_with_items(
        data["date"], data_token, data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron obtener los vouchers vehiculares",
            "error": error,
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener vouchers vehiculares: resultado inesperado",
            "error": str(result),
        }, 400
    data_out = []
    for item in result:
        extra_info = json.loads(item[20])
        accesories = json.loads(item[15]) if item[15] else []
        data_out.append(
            {
                "id_voucher_general": item[0],
                "type": item[1],
                "date": item[2].strftime(format_timestamps)
                if not isinstance(item[2], str)
                else item[2],
                "contract": item[3],
                "realizado_por": item[4],
                "received_by": item[5],
                "brand": item[6],
                "model": item[7],
                "color": item[8],
                "year": item[9],
                "placas": item[10],
                "kilometraje": item[11],
                "registration_card": item[12],
                "insurance": item[13],
                "referendo": item[14],
                "accessories": accesories
                if isinstance(accesories, list)
                else json.loads(accesories),
                "vehicle_type": item[16],
                "observations": item[17],
                "items": json.loads(item[18]),
                "history": json.loads(item[19]),
                "files": extra_info.get("files"),
                "status": item[21],
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def create_voucher_vehicle_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"], data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el voucher general", "error": error}, 400
    try:
        accessories = json.dumps(data["accessories"])
    except Exception as e:
        return {
            "data": None,
            "msg": "Error al procesar los datos de accesorios",
            "error": str(e),
        }, 400

    flag, error, lastrowid_vehicle = create_voucher_vehicle(
        lastrowid,
        data["brand"],
        data["model"],
        data_token,
        data.get("color"),
        data.get("year"),
        data["placas"],
        data.get("kilometraje", 0),
        int(data["registration_card"]),
        int(data["insurance"]),
        int(data["referendo"]),
        accessories,
        data["type"],
        data["received_by"],
        data.get("observations"),
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el voucher vehicular", "error": error}, 400

    history = [
        {
            "id_voucher": lastrowid_vehicle,
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher creado",
        }
    ]
    flag, error, rows_updated = update_history_voucher(history, lastrowid, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400

    errors = []
    for item in data["items"]:
        flag, error, lastrowid_item = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            data_token,
            item.get("observations"),
        )
        if not flag:
            errors.append({"id_item": lastrowid_item, "error": error})

    if data["items"] and len(errors) == len(data["items"]):
        delete_items_voucher(lastrowid, data_token)
        delete_voucher_vehicle(lastrowid, data_token)
        update_voucher_general_from_delete(lastrowid, json.dumps([]), data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún item del voucher vehicular; operación revertida",
            "error": errors,
        }, 400

    msg_out = f"Voucher vehicular creado correctamente (ID {lastrowid})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron crear."
    return {
        "data": {"id_voucher": lastrowid},
        "msg": msg_out,
        "error": errors if errors else None,
    }, 201


def update_voucher_vehicle_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher_general"],
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher vehicular actualizado",
        }
    )
    try:
        accessories = json.dumps(data["accessories"])
    except Exception as e:
        return {
            "data": None,
            "msg": "Error al procesar los datos de accesorios",
            "error": str(e),
        }, 400
    flag, error, rows_changed = update_voucher_vehicle(
        data["id_voucher_general"],
        data["brand"],
        data["model"],
        data_token,
        data.get("color"),
        data.get("year"),
        data["placas"],
        data.get("kilometraje", 0),
        int(data["registration_card"]),
        int(data["insurance"]),
        int(data["referendo"]),
        accessories,
        data["type"],
        data["received_by"],
        data.get("observations"),
        data.get("status"),
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher vehicular",
            "error": error,
        }, 400

    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400

    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, lastrowid = delete_voucher_item(item["id_item"], data_token)
        elif item["id_item"] > 0:
            flag, error, lastrowid = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        else:
            flag, error, lastrowid = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        if not flag:
            errors.append({"id_inventory": item["id_inventory"], "error": error})

    id_ = data["id_voucher_general"]
    msg_out = f"Voucher vehicular actualizado correctamente (ID {id_})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron procesar."
    return {"data": {"id_voucher": id_}, "msg": msg_out, "error": errors if errors else None}, 200


def delete_voucher_vehicle_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    time_older = datetime.now(pytz.utc).astimezone(time_zone) - timedelta(days=365)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, voucher_data = get_vouchers_vehicle_with_items(
        time_older, data_token, id_voucher=data["id"]
    )
    if not flag:
        return {"data": None, "msg": "No se pudo obtener el voucher vehicular", "error": error}, 400
    if not (isinstance(voucher_data, list) or isinstance(voucher_data, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener el voucher vehicular: resultado inesperado",
            "error": str(voucher_data),
        }, 400
    status = voucher_data[0][21]
    if status == 0:
        flag, error, result = delete_voucher_item(data["id"], data_token)
        if not flag:
            return {
                "data": None,
                "msg": "No se pudo eliminar el voucher vehicular",
                "error": error,
            }, 400
        flag, error, result = delete_voucher_vehicle(data["id"], data_token)
        if not flag:
            return {
                "data": None,
                "msg": "No se pudo eliminar el voucher vehicular",
                "error": error,
            }, 400
    else:
        flag, error, result = update_voucher_vehicle_status(3, data["id"], data_token)
        if not flag:
            return {
                "data": None,
                "msg": "No se pudo cancelar el voucher vehicular",
                "error": error,
            }, 400

    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    history = json.loads(voucher_data[0][19])
    history.append(
        {
            "id_voucher": data["id"],
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher vehicular eliminado"
            if status == 0
            else "Voucher vehicular cancelado",
        }
    )

    flag, error, rows_changed = update_voucher_general_from_delete(
        data["id"], json.dumps(history), data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher vehicular",
            "error": error,
        }, 400
    accion = "eliminado" if status == 0 else "cancelado"
    msg = (
        f"Voucher vehicular {accion} correctamente (ID {data['id']}) "
        f"por el empleado {data_token.get('name')}"
    )
    create_notification_permission_notGUI(
        msg,
        data_token,
        ["administracion", "operaciones", "sgi"],
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sgi_chv, msg, data_token)
    return {
        "data": {"id_voucher": data["id"]},
        "msg": f"Voucher vehicular {accion} correctamente (ID {data['id']})",
        "error": None,
    }, 200


def create_voucher_vehicle_attachment_api(data, data_token):
    """{"filepath": filepath_download, "filename": filename}, data_token"""
    filename = data["filename"]
    id_voucher_name = filename.split("-")[0]
    try:
        if int(id_voucher_name) != int(data["id_voucher"]) and int(data["id_voucher"]) <= 0:
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
    timestamp_year_ago = timestamp - timedelta(days=365)
    flag, error, result = get_vouchers_vehicle_with_items(
        timestamp_year_ago.strftime(format_date), data_token, data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo obtener el checklist vehicular",
            "error": error,
        }, 400
    if not isinstance(result, list):
        return {
            "data": None,
            "msg": "Error al obtener el checklist vehicular: resultado inesperado",
            "error": str(result),
        }, 400
    voucher_data = []
    for item in result:
        if int(item[0]) == int(data["id_voucher"]):
            voucher_data = item
            break
    if len(voucher_data) <= 0:
        return {
            "data": None,
            "msg": "Voucher vehicular no encontrado",
            "error": str(voucher_data),
        }, 400
    date_voucher = voucher_data[2]
    history = json.loads(voucher_data[19])
    filepath_down = data["filepath"]
    file_extension = filepath_down.split(".")[-1].lower()
    valid_extension = ["pdf", "jpg", "jpeg", "png", "zip", "webp"]
    if file_extension not in valid_extension:
        return {"data": None, "msg": "Formato de archivo no válido", "error": None}, 400
    path_aws = f"checklistV/{date_voucher.strftime('%Y/%m/%d/')}{data['filename']}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_CH_BUCKET")
    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=str(bucket_name), Key=path_aws)
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no encontradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        elif error_code == "AccessDenied":
            return {
                "data": None,
                "msg": f"Acceso denegado al bucket: {bucket_name}",
                "error": str(e),
            }, 400
        else:
            return {"data": None, "msg": f"Error AWS: {str(e)}", "error": str(e)}, 400
    msg = f"Archivo adjunto agregado: {filename} al voucher {data['id_voucher']} por el empleado {data_token.get('name')}"
    status = voucher_data[21]
    if "firma-aprobado" in filename.lower():
        status = 1
        msg += " y estado actualizado a (aprobado)"
    if "firma-recibido" in filename.lower():
        status = 2
        msg += " y estado actualizado a (recibido)"
    history.append(
        {
            "id_voucher": data["id_voucher"],
            "type": 2,
            "timestamp": timestamp.strftime(format_timestamps),
            "user": data_token.get("emp_id"),
            "comment": f"Archivo adjunto agregado: {path_aws}",
        }
    )
    extra_info = json.loads(voucher_data[20])
    files = extra_info.get("files", [])
    files.append({"filename": data["filename"], "path": path_aws})
    extra_info["files"] = files
    flag, error, rows_updated = update_voucher_vehicle_files(
        data["id_voucher"], history, extra_info, status, data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error al actualizar el historial del voucher (archivo ya subido)",
            "error": error,
        }, 400
    create_notification_permission_notGUI(
        msg,
        data_token,
        ["administracion", "operaciones", "sgi"],
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sgi_chv, msg, data_token)
    return {"data": path_aws, "msg": msg, "error": None}, 201


def download_voucher_vehicle_attachment_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    timestamp_year_ago = timestamp - timedelta(days=365)
    flag, error, result = get_vouchers_vehicle_with_items(
        timestamp_year_ago.strftime(format_date), data_token, data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo obtener el checklist vehicular",
            "error": error,
        }, 400
    if not isinstance(result, list):
        return {
            "data": None,
            "msg": "Error al obtener el checklist vehicular: resultado inesperado",
            "error": str(result),
        }, 400
    voucher_data = []
    for item in result:
        if item[0] == data["id_voucher"]:
            voucher_data = item
            break
    if len(voucher_data) <= 0:
        return {
            "data": None,
            "msg": f"Voucher vehicular no encontrado (ID {data['id_voucher']})",
            "error": str(voucher_data),
        }, 400
    extra_info = json.loads(voucher_data[20])
    files = extra_info.get("files", [])
    name_file = data["filename"]
    flag_found = False
    path_aws = ""
    for file in files:
        if file["filename"] == name_file:
            flag_found = True
            path_aws = file["path"]
            break
    if not flag_found:
        return {"data": None, "msg": "Archivo no encontrado en el voucher", "error": None}, 400
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_CH_BUCKET")
    try:
        s3_client.download_file(Bucket=str(bucket_name), Key=path_aws, Filename=data["filepath"])
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no encontradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        elif error_code == "AccessDenied":
            return {
                "data": None,
                "msg": f"Acceso denegado al bucket: {bucket_name}",
                "error": str(e),
            }, 400
        elif error_code == "NoSuchKey":
            return {
                "data": None,
                "msg": f"Archivo no encontrado en S3: {path_aws}",
                "error": str(e),
            }, 400
        else:
            return {
                "data": None,
                "msg": f"Error al descargar archivo: {str(e)}",
                "error": str(e),
            }, 400
    return {"path": data["filepath"]}, 200
