# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"

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
    if not flag:
        return {
            "data": None,
            "msg": "Error at creating general voucher",
            "error": str(error),
        }, 400
    flag, error, lastrowid = create_voucher_safety(
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
        flag, error, lastrowid = create_voucher_item(
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
                    "id_item": item["id_item"],
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
