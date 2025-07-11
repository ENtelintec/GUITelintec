# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 14:34 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def create_quotation(metadata: dict, products: dict, status=0):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    metadata["status"] = status
    sql = (
        "INSERT INTO sql_telintec_mod_admin.quotations (metadata, products, creation) "
        "VALUES (%s, %s, %s)"
    )
    val = (json.dumps(metadata), json.dumps(products), timestamp)
    flag, error, id_quotation = execute_sql(sql, val, 4)
    return flag, error, id_quotation


def update_quotation(id_quotation, metadata: dict, products: list, timestamps=None):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    if timestamps is None:
        timestamps = {
            "complete": {"timestamp": "", "comment": ""},
            "update": [timestamp],
        }
    else:
        timestamps["update"].append(timestamp)
    sql = (
        "UPDATE sql_telintec_mod_admin.quotations "
        "SET metadata = %s, products = %s, timestamps = %s  "
        "WHERE id = %s"
    )
    val = (
        json.dumps(metadata),
        json.dumps(products),
        json.dumps(timestamps),
        id_quotation,
    )
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def update_quotation_from_contract(id_quotation, products: list):
    sql = (
        "UPDATE sql_telintec_mod_admin.quotations "
        "SET products = %s "
        "WHERE id = %s"
    )
    val = (json.dumps(products), id_quotation)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_quotation(id_quotation):
    sql = "DELETE FROM sql_telintec_mod_admin.quotations " "WHERE id = %s"
    val = (id_quotation,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def get_quotation(id_quotation=None):
    if id_quotation is None:
        sql = (
            "SELECT id, metadata, products, creation, timestamps, metadata->'$.company', metadata->'$.emission' "
            "FROM sql_telintec_mod_admin.quotations"
        )
        flag, error, result = execute_sql(sql, None, 5)
        if not flag:
            return False, error, None
        return True, None, result
    sql = (
        "SELECT id, metadata, products, creation, timestamps "
        "FROM sql_telintec_mod_admin.quotations "
        "WHERE id = %s"
    )
    val = (id_quotation,)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return False, "Quotation not found", None
    else:
        return True, None, result


def get_quotation_data_display(id_quotation=None):
    if id_quotation is None:
        sql = (
            "SELECT id, "
            "metadata->'$.company', "
            "metadata->'$.quotation_code', "
            "metadata->'$.codigo', "
            "creation "
            "FROM sql_telintec_mod_admin.quotations"
        )
        flag, error, result = execute_sql(sql, None, 5)
        if not flag:
            return False, error, None
        return True, None, result
    sql = (
        "SELECT id, "
        "metadata->'$.company', "
        "metadata->'$.quotation_code', "
        "metadata->'$.codigo', "
        "creation "
        "FROM sql_telintec_mod_admin.quotations "
        "WHERE id = %s"
    )
    val = (id_quotation,)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return False, "Quotation not found", None
    else:
        return True, None, result[0]
