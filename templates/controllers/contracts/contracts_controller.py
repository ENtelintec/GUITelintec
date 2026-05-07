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
    data_token,
    status=0,
    abbreviation=None,
):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    metadata["status"] = status
    sql = "INSERT INTO sql_telintec_mod_admin.contracts (metadata, creation, quotation_id, code, client_id, emission, abbreviation) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (
        json.dumps(metadata),
        timestamp,
        id_quotation,
        contract_number,
        client_id,
        emission,
        abbreviation,
    )
    flag, error, id_contract = execute_sql(sql, val, 4, data_token)
    return flag, error, id_contract


def update_contract(
    id_contract,
    metadata: dict,
    contract_number: str,
    client_id: int,
    emission: str,
    data_token,
    timestamps=None,
    quotation_id=None,
    abbreviation=None,
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
    sql = "UPDATE sql_telintec_mod_admin.contracts SET metadata = %s, timestamps = %s, quotation_id = %s, code = %s, client_id =  %s, emission = %s , abbreviation = %s WHERE id = %s"
    val = (
        json.dumps(metadata),
        json.dumps(timestamps),
        quotation_id,
        contract_number,
        client_id,
        emission,
        abbreviation,
        id_contract,
    )
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def delete_contract(id_contract, data_token):
    sql = "DELETE FROM sql_telintec_mod_admin.contracts WHERE id = %s"
    val = (id_contract,)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def get_contract(data_token, id_contract=None):
    if id_contract is None:
        sql = "SELECT id, metadata, creation, quotation_id, timestamps, code, client_id, emission, abbreviation FROM sql_telintec_mod_admin.contracts"
        flag, error, result = execute_sql(sql, None, 2, data_token)
        if not flag:
            return False, error, []
        if not (isinstance(result, tuple) or isinstance(result, list)):
            return False, error, []
        return True, None, result
    sql = "SELECT id, metadata, creation, quotation_id, timestamps, code, client_id, emission, abbreviation FROM sql_telintec_mod_admin.contracts WHERE id = %s"
    val = (id_contract,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    if not isinstance(result, tuple) or not isinstance(result, list):
        return False, error, []
    if len(result) == 0:
        return False, "Contract not found", []
    else:
        return True, None, result


def get_contract_from_abb(contract_abb: str, data_token):
    sql = "SELECT id, metadata, creation, quotation_id, timestamps FROM sql_telintec_mod_admin.contracts WHERE metadata->'$.abbreviation_sm' = %s"
    val = (contract_abb.upper(),)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    if not isinstance(result, tuple):
        return False, error, None
    if len(result) == 0:
        return False, "Contract not found", None
    else:
        return True, None, result


def get_contract_by_client(client_id: int, data_token):
    sql = "SELECT id, metadata, creation, quotation_id, timestamps, code FROM sql_telintec_mod_admin.contracts WHERE client_id = %s"
    val = (client_id,)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def get_contracts_by_ids(ids_list: list, data_token):
    if len(ids_list) == 0:
        return True, "Contract not found", []
    regexp_clauses = " OR ".join(["id = %s"] * len(ids_list))
    sql = f"SELECT id, metadata, creation, quotation_id, timestamps, code FROM sql_telintec_mod_admin.contracts WHERE {regexp_clauses}"
    val = tuple(ids_list)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def get_contracts_abreviations_db(data_token):
    sql = (
        "SELECT "
        "JSON_UNQUOTE(metadata->'$.abbreviation_sm'), "
        "id, "
        "metadata, "
        "abbreviation, "
        "1 "
        "FROM sql_telintec_mod_admin.contracts "
        "UNION SELECT "
        "   abbreviation, "
        "   department_id, "
        "   JSON_OBJECT( 'name', name, 'location', location ),   "
        "   '', 0 "
        "   FROM sql_telintec.departments "
        "UNION SELECT "
        "   abbreviation, "
        "   id, "
        "   JSON_OBJECT( 'name', name, 'department', id_department),"
        "   '', 0 "
        "   FROM sql_telintec.areas "
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    if not isinstance(result, list):
        return False, "Not data found or error", []
    if len(result) == 0:
        return False, "Contract not found", []
    else:
        return True, None, result


def get_items_contract_string(key: str, data_token) -> tuple[bool, str, int | list]:
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
        "OR JSON_EXTRACT(c.metadata, '$.abbreviation_sm') = %s"
    )
    val = (key, key)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def get_contract_and_items_from_number(lastdigits: str, data_token):
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
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


def get_contracts_with_items(data_token):
    sql = (
        "SELECT "
        "c.id, "
        "c.metadata, "
        "c.creation, "
        "c.quotation_id, "
        "c.timestamps, "
        "c.code, "
        "c.client_id, "
        "c.emission, "
        "c.abbreviation, "
        "JSON_ARRAYAGG(JSON_OBJECT("
        "   'item_id', qi.id, "
        "   'partida', qi.partida, "
        "   'id_inventory', qi.id_inventory, "
        "   'description', qi.description, "
        "   'udm', qi.udm, "
        "   'quantity', qi.quantity, "
        "   'unit_price', qi.price_unit "
        ")) AS items "
        "FROM sql_telintec_mod_admin.contracts c "
        "LEFT JOIN sql_telintec_mod_admin.quotation_items qi ON qi.quotation_id = c.quotation_id "
        "GROUP BY c.id "
        "ORDER BY c.creation DESC"
    )
    flag, error, result = execute_sql(sql, None, 2, data_token)
    if not flag:
        return False, error, []
    if not (isinstance(result, tuple) or isinstance(result, list)):
        return False, error, []
    return True, None, result
