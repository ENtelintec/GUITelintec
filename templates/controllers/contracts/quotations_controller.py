# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 14:34 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def create_quotation(metadata: dict, status=0):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    metadata["status"] = status
    sql = (
        "INSERT INTO sql_telintec_mod_admin.quotations (metadata, creation) "
        "VALUES (%s, %s)"
    )
    val = (json.dumps(metadata), timestamp)
    flag, error, id_quotation = execute_sql(sql, val, 4)
    return flag, error, id_quotation


def create_items_quotation(items: list):
    result_list = []
    error_list = []
    flag_list = []
    for item in items:
        val = (
            item["quotation_id"],
            item["contract_id"],
            item["partida"],
            item["udm"],
            item["brand"],
            item["type_p"],
            item["n_part"],
            item["quantity"],
            item["revision"],
            item["price_unit"],
            item["description"],
            item["description_small"],
            item["id_inventory"],
        )
        sql = (
            "INSERT INTO sql_telintec_mod_admin.quotation_items "
            "(quotation_id, contract_id, partida, udm, brand, type_p, n_part, "
            "quantity, revision, price_unit, description, description_small, "
            "id_inventory) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        flag, error, lastrowid = execute_sql(sql, val, 4)
        flag_list.append(flag)
        error_list.append(error)
        result_list.append(lastrowid)
    return flag_list, error_list, result_list


def update_quotation(id_quotation, metadata: dict, timestamps=None):
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
        "SET metadata = %s, timestamps = %s  "
        "WHERE id = %s"
    )
    val = (
        json.dumps(metadata),
        json.dumps(timestamps),
        id_quotation,
    )
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def create_item_quotation(item: dict):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.quotation_items "
        "(quotation_id, contract_id, partida, udm, brand, type_p, n_part, "
        "quantity, revision, price_unit, description, description_small, "
        "id_inventory) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        item["quotation_id"],
        item["contract_id"],
        item["partida"],
        item["udm"],
        item["brand"],
        item["type_p"],
        item["n_part"],
        item["quantity"],
        item["revision"],
        item["price_unit"],
        item["description"],
        item["description_small"],
        item["id_inventory"],
    )
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def update_item_quotation(id_item, item: dict):
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_items "
        "SET partida = %s, udm = %s, brand = %s, type_p = %s, n_part = %s, quantity = %s, "
        "revision = %s, price_unit = %s, description = %s, description_small = %s, "
        "id_inventory = %s "
        "WHERE id = %s"
    )
    val = (
        item["partida"],
        item["udm"],
        item["brand"],
        item["type_p"],
        item["n_part"],
        item["quantity"],
        item["revision"],
        item["price_unit"],
        item["description"],
        item["description_small"],
        item["id_inventory"],
        id_item,
    )
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_item_quotation(id_item):
    sql = "DELETE FROM sql_telintec_mod_admin.quotation_items " "WHERE id = %s"
    val = (id_item,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_quotation_items(id_quotation):
    sql = (
        "DELETE FROM sql_telintec_mod_admin.quotation_items " "WHERE quotation_id = %s"
    )
    val = (id_quotation,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_contract_from_item_quotation(contract_id):
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_items "
        "SET contract_id = NULL "
        "WHERE contract_id = %s"
    )
    val = (contract_id,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_quotation(id_quotation):
    sql = "DELETE FROM sql_telintec_mod_admin.quotations " "WHERE id = %s"
    val = (id_quotation,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def get_quotation(id_quotation=None):
    sql = (
        "SELECT "
        "q.id AS quotation_id, "
        "q.metadata, "
        "JSON_ARRAYAGG(JSON_OBJECT( "
        "  'id', qi.id, "
        "  'partida', qi.partida, "
        "  'udm', qi.udm, "
        "  'brand', qi.brand, "
        "  'type_p', qi.type_p, "
        "  'n_part', qi.n_part, "
        "  'quantity', qi.quantity, "
        "  'revision', qi.revision, "
        "  'price_unit', qi.price_unit, "
        "  'description', qi.description, "
        "  'description_small', qi.description_small, "
        "  'id_inventory', qi.id_inventory "
        ")) AS products, "
        "q.creation, "
        "q.timestamps,"
        "qi.contract_id "
        "FROM sql_telintec_mod_admin.quotations q "
        "LEFT JOIN sql_telintec_mod_admin.quotation_items qi ON qi.quotation_id = q.id "
        "WHERE q.id = %s OR %s IS NULL "
        "GROUP BY q.id"
    )
    val = (id_quotation, id_quotation)
    flag, error, result = execute_sql(sql, val, 5)
    if not flag:
        return False, error, []
    if id_quotation and len(result) == 0:
        return False, "Quotation not found", []
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


def get_items_quotation_from_cotract(contract_id):
    sql = (
        "SELECT id, partida, id_inventory, quotation_id "
        "FROM sql_telintec_mod_admin.quotation_items "
        "WHERE contract_id = %s"
    )
    val = (contract_id,)
    flag, error, result = execute_sql(sql, val, 2)
    if len(result) == 0:
        return False, "Quotation not found", []
    else:
        return True, None, result


def update_quotation_item_partida_from_sm(contract_id, partida, id_inventory):
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_items "
        "SET id_inventory = %s "
        "WHERE contract_id = %s AND partida = %s"
    )
    val = (id_inventory, contract_id, partida)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out
