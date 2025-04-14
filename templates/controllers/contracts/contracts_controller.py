# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 14:34 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def create_contract(id_quotation, metadata: dict, status=0):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    metadata["status"] = status
    sql = (
        "INSERT INTO sql_telintec_mod_admin.contracts (metadata, creation, quotation_id) "
        "VALUES (%s, %s, %s)"
    )
    val = (json.dumps(metadata), timestamp, id_quotation)
    flag, error, id_contract = execute_sql(sql, val, 4)
    return flag, error, id_contract


def update_contract(id_contract, metadata: dict, timestamps=None, quotation_id=None):
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
        "UPDATE sql_telintec_mod_admin.contracts "
        "SET metadata = %s, timestamps = %s, quotation_id = %s  "
        "WHERE id = %s"
    )
    val = (json.dumps(metadata), json.dumps(timestamps), quotation_id, id_contract)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_contract(id_contract):
    sql = "DELETE FROM sql_telintec_mod_admin.contracts " "WHERE id = %s"
    val = (id_contract,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def get_contract(id_contract=None):
    if id_contract is None:
        sql = (
            "SELECT id, metadata, creation, quotation_id, timestamps "
            "FROM sql_telintec_mod_admin.contracts"
        )
        flag, error, result = execute_sql(sql, None, 2)
        if not flag:
            return False, error, None
        return True, None, result
    sql = (
        "SELECT id, metadata, creation, quotation_id, timestamps "
        "FROM sql_telintec_mod_admin.contracts "
        "WHERE id = %s"
    )
    val = (id_contract,)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return False, "Contract not found", None
    else:
        return True, None, result


def get_contract_from_abb(contract_abb: str):
    sql = (
        "SELECT id, metadata, creation, quotation_id, timestamps "
        "FROM sql_telintec_mod_admin.contracts "
        "WHERE metadata->'$.abbreviation' = %s"
    )
    val = (contract_abb.upper(),)
    flag, error, result = execute_sql(sql, val, 1)
    if len(result) == 0:
        return False, "Contract not found", None
    else:
        return True, None, result


def get_contracts_abreviations_db():
    sql = (
        "SELECT metadata->'$.abbreviation', id, metadata "
        "FROM sql_telintec_mod_admin.contracts "
    )
    flag, error, result = execute_sql(sql, None, 2)
    if len(result) == 0:
        return False, "Contract not found", None
    else:
        return True, None, result
