# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"

import json
from datetime import datetime

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
    history = {
        "id_voucher": v_tools_id,
        "type": 0,
        "timestamp": timestamp,
        "user": data_token.get("emp_id"),
        "comment": "Voucher creado",
    }
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
    history = {
        "id_voucher": lastrowid_safety,
        "type": 1,
        "timestamp": timestamp,
        "user": data_token.get("emp_id"),
        "comment": "Voucher creado",
    }
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


def get_vouchers_tools_api(data, data_token=None):
    flag, error, result = get_vouchers_tools_with_items_date(
        data["date"], data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting vouchers",
            "error": str(error),
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


def get_vouchers_safety_api(data, data_token=None):
    flag, error, result = get_vouchers_safety_with_items(
        data["date"], data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at getting vouchers",
            "error": str(error),
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
            "id_voucher": data["id_voucher_general"],
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": f"Voucher safety actualizado de estados: "
            f"{data['user_state']}-{data['epp_state']}-{data['storage_state']}",
        }
    )
    flag, error, rows_updated = update_state_safety_voucher(
        data["id_voucher_general"],
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
    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"]
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating history voucher",
            "error": str(error),
        }, 400
    return {"data": [rows_updated], "msg": "Voucher updated successfully"}, 200
