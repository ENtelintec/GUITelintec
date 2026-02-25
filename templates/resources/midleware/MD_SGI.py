# -*- coding: utf-8 -*-
from static.constants import log_file_sgi_chv
from templates.misc.Functions_Files import write_log_file
from templates.Functions_Utils import create_notification_permission_notGUI
from static.constants import format_date
from botocore.exceptions import ClientError, NoCredentialsError
from static.constants import secrets

__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"

import json
from datetime import datetime, timedelta

import boto3
import pytz

from static.constants import timezone_software, format_timestamps
from templates.controllers.vouchers.vouchers_controller import (
    create_voucher_general,
    create_voucher_tools,
    create_voucher_safety,
    update_voucher_tools,
    update_voucher_safety,
    create_voucher_item,
    update_voucher_item,
    get_vouchers_tools_with_items_date,
    get_vouchers_safety_with_items,
    update_history_voucher,
    update_state_tools_voucher,
    update_state_safety_voucher,
    delete_voucher_item,
    get_vouchers_vehicle_with_items,
    create_voucher_vehicle,
    update_voucher_vehicle,
    delete_items_voucher,
    delete_voucher_tools,
    update_voucher_general_from_delete,
    delete_voucher_vehicle,
    update_voucher_vehicle_files,
)


def create_voucher_tools_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"]
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating general voucher",
            "error": str(error),
        }, 400
    flag, error, v_tools_id = create_voucher_tools(
        lastrowid,
        data["position"],
        data["type_transaction"],
        data["superior"],
        data["storage_emp"],
        data["designated_emp"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating tools voucher",
            "error": str(error),
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
    flag, error, rows_updated = update_history_voucher(history, lastrowid)
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, p_id = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            item["observations"],
        )
        if not flag:
            errors.append(
                {
                    "id_inventory": item["id_inventory"],
                    "error": str(error),
                }
            )
    if len(errors) > 0:
        return {
            "data": [lastrowid],
            "msg": "Voucher created but error at creating tools voucher",
            "errors": errors,
        }, 400
    return {"data": [lastrowid], "msg": "ok", "error": None}, 201


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
        data["user_state"],
        data["superior_state"],
        data["storage_state"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating tools voucher",
            "error": str(error),
        }, 400
    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"]
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400
    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, result = delete_voucher_item(item["id_item"])
        elif item["id_item"] > 0:
            flag, error, result = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                item["observations"],
            )
        else:
            flag, error, result = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                item["observations"],
            )
        if not flag:
            errors.append(
                {
                    "id_item": item["id_item"],
                    "error": str(error),
                }
            )
    if len(errors) > 0:
        return {
            "data": None,
            "msg": "Voucher created but error at updating tools",
            "errors": errors,
        }, 400
    return {"data": rows_updated, "msg": "Voucher updated successfully"}, 200


def delete_voucher_tools_api(data, data_token):
    flag, error, rows_updated = delete_items_voucher(data["id"])
    if not flag:
        return {
            "data": None,
            "msg": "Error when eliminating items related to voucher",
            "error": str(error),
        }, 400
    flag, error, rows_updated = delete_voucher_tools(data["id"])
    if not flag:
        return {
            "data": None,
            "msg": "Error at deleting voucher",
            "error": str(error),
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
    flag, error, result = update_voucher_general_from_delete(data["id"], history)
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating voucher",
            "error": str(error),
        }, 400
    return {"data": rows_updated, "msg": "Voucher updated successfully"}, 200


def create_voucher_safety_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"]
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating general voucher",
            "error": str(error),
        }, 400
    flag, error, lastrowid_safety = create_voucher_safety(
        lastrowid,
        data["motive"],
        data["epp_emp"],
        data["storage_emp"],
        data["designated_emp"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating safety voucher",
            "error": str(error),
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
    flag, error, rows_updated = update_history_voucher(history, lastrowid)
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, lastrowid_item = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            item["observations"],
        )
        if not flag:
            errors.append(
                {
                    "id_item": lastrowid_item,
                    "error": str(error),
                }
            )
    if len(errors) > 0:
        return {
            "data": [lastrowid],
            "msg": "Voucher created but error at creating safety items",
            "errors": errors,
        }, 400
    return {"data": [lastrowid], "msg": "Voucher created successfully"}, 201


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
        data["epp_state"],
        data["storage_state"],
        data["motive"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating safety voucher",
            "error": str(error),
        }, 400
    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"]
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400
    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, lastrowid = delete_voucher_item(item["id_item"])
        elif item["id_item"] > 0:
            flag, error, lastrowid = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                item["observations"],
            )
        else:
            flag, error, lastrowid = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                item["observations"],
            )
        if not flag:
            errors.append(
                {
                    "id_inventory": item["id_inventory"],
                    "error": str(error),
                }
            )
    if len(errors) > 0:
        return {
            "data": None,
            "msg": "Voucher created but error at creating safety items",
            "errors": errors,
        }, 400
    return {"data": [rows_changed], "msg": "Voucher updated successfully"}, 200


def delete_voucher_safety_api(data, data_token):
    flag, error, rows_updated = delete_items_voucher(data["id"])
    if not flag:
        return {
            "data": None,
            "msg": "Error when eliminating items related to voucher",
            "error": str(error),
        }, 400
    flag, error, rows_updated = delete_voucher_tools(data["id"])
    if not flag:
        return {
            "data": None,
            "msg": "Error at deleting voucher",
            "error": str(error),
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
    flag, error, result = update_voucher_general_from_delete(data["id"], history)
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating voucher",
            "error": str(error),
        }, 400
    return {"data": rows_updated, "msg": "Voucher updated successfully"}, 200


def get_vouchers_tools_api(data, data_token):
    flag, error, result = get_vouchers_tools_with_items_date(
        data["date"], data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting vouchers",
            "error": str(error),
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error at getting vouchers: result is not a list or tuple",
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
    return {"data": data_out, "msg": "Vouchers retrieved successfully"}, 200


def get_vouchers_safety_api(data, data_token):
    flag, error, result = get_vouchers_safety_with_items(
        data["date"], data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting vouchers",
            "error": str(error),
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error at getting vouchers: result is not a list or tuple",
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
    return {"data": data_out, "msg": "Vouchers retrieved successfully"}, 200


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
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating tools voucher",
            "error": str(error),
        }, 400
    flag, error, rows_updated = update_history_voucher(history, data["id_voucher"])
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400
    return {"data": [rows_updated], "msg": "Voucher updated successfully"}, 200


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
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating safety voucher",
            "error": str(error),
        }, 400
    flag, error, rows_updated = update_history_voucher(history, data["id_voucher"])
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400
    return {"data": [rows_updated], "msg": "Voucher updated successfully"}, 200


def get_vouchers_vehicle_api(data, data_token):
    flag, error, result = get_vouchers_vehicle_with_items(
        data["date"], data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting vehicle vouchers",
            "error": str(error),
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error at getting vehicle vouchers: result is not a list or tuple",
            "error": str(result),
        }, 400
    data_out = []
    for item in result:
        extra_info = json.loads(item[20])
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
                "accessories": json.loads(item[15]),
                "vehicle_type": item[16],
                "observations": item[17],
                "items": json.loads(item[18]),
                "history": json.loads(item[19]),
                "files": extra_info.get("files"),
            }
        )
    return {"data": data_out, "msg": "Vehicle vouchers retrieved successfully"}, 200


def create_voucher_vehicle_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    # 1. Crear voucher general
    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"]
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating general voucher",
            "error": str(error),
        }, 400
    try:
        accessories = json.dumps(data["accessories"])
    except Exception as e:
        return {
            "data": None,
            "msg": "Error at processing accessories data",
            "error": str(e),
        }, 400

    # 2. Crear voucher vehicular
    flag, error, lastrowid_vehicle = create_voucher_vehicle(
        lastrowid,
        data["brand"],
        data["model"],
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
        return {
            "data": None,
            "msg": "Error at creating vehicle voucher",
            "error": str(error),
        }, 400

    # 3. Actualizar historial
    history = [
        {
            "id_voucher": lastrowid_vehicle,
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher creado",
        }
    ]
    flag, error, rows_updated = update_history_voucher(history, lastrowid)
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400

    # 4. Crear ítems relacionados
    errors = []
    for item in data["items"]:
        flag, error, lastrowid_item = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            item.get("observations"),
        )
        if not flag:
            errors.append(
                {
                    "id_item": lastrowid_item,
                    "error": str(error),
                }
            )

    if len(errors) > 0:
        return {
            "data": [lastrowid],
            "msg": "Voucher created but error at creating vehicle items",
            "errors": errors,
        }, 400

    return {"data": [lastrowid], "msg": "Vehicle voucher created successfully"}, 201


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
            "msg": "Error at processing accessories data",
            "error": str(e),
        }, 400
    flag, error, rows_changed = update_voucher_vehicle(
        data["id_voucher_general"],
        data["brand"],
        data["model"],
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
        return {
            "data": None,
            "msg": "Error at updating vehicle voucher",
            "error": str(error),
        }, 400

    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"]
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400

    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, lastrowid = delete_voucher_item(item["id_item"])
        elif item["id_item"] > 0:
            flag, error, lastrowid = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                item["observations"],
            )
        else:
            flag, error, lastrowid = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                item["observations"],
            )
        if not flag:
            errors.append(
                {
                    "id_inventory": item["id_inventory"],
                    "error": str(error),
                }
            )

    if len(errors) > 0:
        return {
            "data": None,
            "msg": "Voucher updated but error at processing vehicle items",
            "errors": errors,
        }, 400

    return {"data": [rows_changed], "msg": "Vehicle voucher updated successfully"}, 200


def delete_voucher_vehicle_api(data, data_token):
    flag, error, result = delete_voucher_item(data["id"])
    if not flag:
        return {
            "data": None,
            "msg": "Error at deleting vehicle voucher",
            "error": str(error),
        }, 400
    flag, error, result = delete_voucher_vehicle(data["id"])
    if not flag:
        return {
            "data": None,
            "msg": "Error at deleting vehicle voucher",
            "error": str(error),
        }, 400
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    history = data["history"]
    history.append(
        {
            "id_voucher": data["id"],
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher vehicular eliminado",
        }
    )

    flag, error, rows_changed = update_voucher_general_from_delete(
        data["id"], json.dumps(history)
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at deleting vehicle voucher",
            "error": str(error),
        }, 400

    return {"data": [rows_changed], "msg": "Vehicle voucher deleted successfully"}, 200


def create_voucher_vehicle_attachment_api(data, data_token):
    """{"filepath": filepath_download, "filename": filename}, data_token"""
    filename = data["filename"]
    id_voucher_name = filename.split("-")[0]
    try:
        if (
            int(id_voucher_name) != int(data["id_voucher"])
            and int(data["id_voucher"]) <= 0
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
    timestamp_year_ago = timestamp - timedelta(days=365)
    flag, error, result = get_vouchers_vehicle_with_items(
        timestamp_year_ago.strftime(format_date), data_token.get("emp_id")
    )
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
    voucher_data = []
    for item in result:
        if int(item[0]) == int(data["id_voucher"]):
            voucher_data = item
            break
    if len(voucher_data) <= 0:
        return {
            "data": None,
            "msg": "Error at getting checklist vehicular by id: voucher not found",
            "error": str(voucher_data),
        }, 400
    history = json.loads(voucher_data[19])
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
    path_aws = f"checklistV/{timestamp.strftime('%Y/%m/%d/')}{data['filename']}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_CH_BUCKET")

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
    files.append(
        {
            "filename": data["filename"],
            "path": path_aws,
        }
    )
    extra_info["files"] = files
    flag, error, rows_updated = update_voucher_vehicle_files(
        data["id_voucher"], history, extra_info
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher but file uploaded",
            "error": str(error),
        }, 400
    msg = "File uploaded successfully but error at updating history voucher"
    create_notification_permission_notGUI(
        msg, ["administracion", "operaciones", "sgi"], data_token.get("emp_id"), 0
    )
    write_log_file(log_file_sgi_chv, msg)
    return {"data": path_aws, "msg": msg}, 201


def download_voucher_vehicle_attachment_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    timestamp_year_ago = timestamp - timedelta(days=365)
    flag, error, result = get_vouchers_vehicle_with_items(
        timestamp_year_ago.strftime(format_date), data_token.get("emp_id")
    )
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
    voucher_data = []
    for item in result:
        if item[0] == data["id_voucher"]:
            voucher_data = item
            break
    if len(voucher_data) <= 0:
        return {
            "data": None,
            "msg": f"Error at getting checklist vehicular by id: {data['id_voucher']} not in db",
            "error": str(voucher_data),
        }, 400
    extra_info = json.loads(voucher_data[20])
    files = extra_info.get("files", [])
    path_aws = data["filename"]
    flag_found = False
    for file in files:
        if file["path"] == path_aws:
            flag_found = True
            break
    if not flag_found:
        return {"data": None, "msg": "File not found in voucher"}, 400
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_CH_BUCKET")
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
