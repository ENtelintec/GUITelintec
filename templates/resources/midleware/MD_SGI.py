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
        data["user_state"],
        data["superior_state"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating tools voucher",
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
    flag, error, rows_updated = update_voucher_tools(
        data["id_voucher_general"],
        data["position"],
        data["type_transaction"],
        data["superior"],
        data["storage_emp"],
        data["user_state"],
        data["superior_state"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating tools voucher",
            "error": str(error),
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, result = update_voucher_item(
            item["id_item"],
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
    print("lastrowid", lastrowid)
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating general voucher",
            "error": str(error),
        }, 400
    flag, error, lastrowid_safety = create_voucher_safety(
        lastrowid,
        data["superior"],
        data["epp_emp"],
        data["epp_state"],
        data["superior_state"],
        data["motive"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating safety voucher",
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
    flag, error, rows_changed = update_voucher_safety(
        data["id_voucher_general"],
        data["superior"],
        data["epp_emp"],
        data["epp_state"],
        data["superior_state"],
        data["motive"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "Error at updating safety voucher",
            "error": str(error),
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, lastrowid = update_voucher_item(
            item["id_item"],
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
    flag, error, result = get_vouchers_tools_with_items_date(data["date"])
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
                "user": item[3],
                "contract": item[4],
                "position": item[5],
                "type_transaction": item[6],
                "superior": item[7],
                "storage_emp": item[8],
                "user_state": item[9],
                "superior_state": item[10],
                "extra_info": json.loads(item[11]),
                "items": json.loads(item[12]),
            }
        )
    return {"data": data_out, "msg": "Vouchers retrieved successfully"}, 200


def get_vouchers_safety_api(data, data_token=None):
    flag, error, result = get_vouchers_safety_with_items(data["date"])
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
                "user": item[3],
                "contract": item[4],
                "superior": item[5],
                "epp_emp": item[6],
                "epp_state": item[7],
                "superior_state": item[8],
                "motive": item[9],
                "extra_info": json.loads(item[10]),
                "items": json.loads(item[11]),
            }
        )
    return {"data": data_out, "msg": "Vouchers retrieved successfully"}, 200
