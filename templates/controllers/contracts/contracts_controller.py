# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 14:34 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def create_contract(
    id_quotation,
    metadata: dict,
    contract_number: str,
    client_id: int,
    emission: str,
    status=0,
):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    metadata["status"] = status
    sql = (
        "INSERT INTO sql_telintec_mod_admin.contracts (metadata, creation, quotation_id, code, client_id, emission) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    val = (
        json.dumps(metadata),
        timestamp,
        id_quotation,
        contract_number,
        client_id,
        emission,
    )
    flag, error, id_contract = execute_sql(sql, val, 4)
    return flag, error, id_contract


def update_contract(
    id_contract,
    metadata: dict,
    contract_number: str,
    client_id: int,
    emission: str,
    timestamps=None,
    quotation_id=None,
):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    if timestamps is None:
        timestamps = {
            "complete": {"timestamp": "", "comment": ""},
            "update": [{"timestamp": timestamp, "comment": "creation"}],
        }
    else:
        timestamps["update"].append({"timestamp": timestamp, "comment": "update"})
    sql = (
        "UPDATE sql_telintec_mod_admin.contracts "
        "SET metadata = %s, timestamps = %s, quotation_id = %s, code = %s, client_id =  %s, emission = %s "
        "WHERE id = %s"
    )
    val = (
        json.dumps(metadata),
        json.dumps(timestamps),
        quotation_id,
        contract_number,
        client_id,
        emission,
        id_contract,
    )
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def delete_contract(id_contract):
    sql = "DELETE FROM sql_telintec_mod_admin.contracts WHERE id = %s"
    val = (id_contract,)
    flag, error, out = execute_sql(sql, val, 3)
    return flag, error, out


def get_contract(id_contract=None):
    if id_contract is None:
        sql = (
            "SELECT id, metadata, creation, quotation_id, timestamps, code, client_id, emission "
            "FROM sql_telintec_mod_admin.contracts"
        )
        flag, error, result = execute_sql(sql, None, 2)
        print(flag, error, result)
        if not flag:
            return False, error, []
        if not (isinstance(result, tuple) or isinstance(result, list)):
            return False, error, []
        return True, None, result
    sql = (
        "SELECT id, metadata, creation, quotation_id, timestamps, code, client_id, emission "
        "FROM sql_telintec_mod_admin.contracts "
        "WHERE id = %s"
    )
    val = (id_contract,)
    flag, error, result = execute_sql(sql, val, 1)
    if not isinstance(result, tuple) or not isinstance(result, list):
        return False, error, []
    if len(result) == 0:
        return False, "Contract not found", []
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
    if not isinstance(result, tuple):
        return False, error, None
    if len(result) == 0:
        return False, "Contract not found", None
    else:
        return True, None, result


def get_contract_by_client(client_id: int):
    sql = (
        "SELECT id, metadata, creation, quotation_id, timestamps, code "
        "FROM sql_telintec_mod_admin.contracts "
        "WHERE client_id = %s"
    )
    val = (client_id,)
    flag, error, result = execute_sql(sql, val, 2)
    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def get_contracts_by_ids(ids_list: list):
    if len(ids_list) == 0:
        return True, "Contract not found", []
    regexp_clauses = " OR ".join(["id = %s"] * len(ids_list))
    sql = (
        f"SELECT id, metadata, creation, quotation_id, timestamps, code "
        f"FROM sql_telintec_mod_admin.contracts "
        f"WHERE {regexp_clauses}"
    )
    val = tuple(ids_list)
    flag, error, result = execute_sql(sql, val, 2)
    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def get_contracts_abreviations_db():
    sql = (
        "SELECT "
        "JSON_UNQUOTE(metadata->'$.abbreviation'), "
        "id, "
        "metadata, "
        "abbreviation, "
        "1 "
        "FROM sql_telintec_mod_admin.contracts "
        "UNION SELECT "
        "abbreviation, "
        "department_id, "
        "JSON_OBJECT( 'name', name, 'location', location ),   "
        "'',"
        "0 "
        "FROM sql_telintec.departments "
        "UNION SELECT "
        "abbreviation, "
        "id, "
        "JSON_OBJECT( 'name', name, 'department', id_department),"
        "'', "
        "0 "
        "FROM sql_telintec.areas "
    )
    flag, error, result = execute_sql(sql, None, 5)
    if not isinstance(result, list):
        return False, "Not data found or error", []
    if len(result) == 0:
        return False, "Contract not found", []
    else:
        return True, None, result


def get_items_contract_string(key: str) -> tuple[bool, str, int | list]:
    sql = (
        "SELECT "
        "c.id AS contract_id, "
        "q.id AS quotation_id, "
        "qi.id AS item_id, "
        "qi.partida, "
        "qi.id_inventory "
        "FROM sql_telintec_mod_admin.contracts c "
        "LEFT JOIN sql_telintec_mod_admin.quotations q ON q.id = c.quotation_id "
        "LEFT JOIN sql_telintec_mod_admin.quotation_items qi ON qi.contract_id = c.id "
        "WHERE RIGHT(JSON_UNQUOTE(JSON_EXTRACT(c.metadata, '$.contract_number')), 4) = %s "
        "OR JSON_EXTRACT(c.metadata, '$.abbreviation') = %s"
    )
    val = (key, key)
    flag, error, result = execute_sql(sql, val, 2)
    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def get_contract_and_items_from_number(lastdigits: str):
    """
    Fetch contract and its items using the last digits of the contract number.
    """
    sql = (
        "SELECT "
        "c.id AS contract_id, "
        "c.metadata AS contract_metadata, "
        "qi.id AS item_id, "
        "qi.partida, "
        "qi.id_inventory, "
        "qi.description, "
        "qi.udm "
        "FROM sql_telintec_mod_admin.contracts c "
        "LEFT JOIN sql_telintec_mod_admin.quotations q ON q.id = c.quotation_id "
        "LEFT JOIN sql_telintec_mod_admin.quotation_items qi ON qi.contract_id = c.id "
        "WHERE RIGHT(JSON_UNQUOTE(JSON_EXTRACT(c.metadata, '$.contract_number')), 4) = %s"
    )
    val = (lastdigits,)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result
