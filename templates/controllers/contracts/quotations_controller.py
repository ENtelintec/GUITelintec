# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 14:34 $"

import json
from datetime import datetime

import pytz

from static.constants import format_timestamps, timezone_software
from templates.database.connection import execute_sql


def create_quotation(metadata: dict, data_token, status=0):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    metadata["status"] = status
    sql = (
        "INSERT INTO sql_telintec_mod_admin.quotations (metadata, creation) "
        "VALUES (%s, %s)"
    )
    val = (json.dumps(metadata), timestamp)
    flag, error, id_quotation = execute_sql(sql, val, 4, data_token)
    return flag, error, id_quotation


def create_items_quotation(items: list, data_token):
    result_list = []
    error_list = []
    flag_list = []
    for item in items:
        extra_info = item.get("extra_info")
        val = (
            item["quotation_id"],
            item["contract_id"],
            item["partida"],
            item.get("section_index", 0),
            item["udm"],
            item["brand"],
            item["type_p"],
            item["n_part"],
            item["quantity"],
            item["revision"],
            item["price_unit"],
            item["description"],
            item["description_small"],
            json.dumps(extra_info) if extra_info else None,
            item["id_inventory"],
        )
        sql = (
            "INSERT INTO sql_telintec_mod_admin.quotation_items "
            "(quotation_id, contract_id, partida, section_index, udm, brand, type_p, "
            "n_part, quantity, revision, price_unit, description, description_small, "
            "extra_info, id_inventory) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        flag, error, lastrowid = execute_sql(sql, val, 4, data_token)
        flag_list.append(flag)
        error_list.append(error)
        result_list.append(lastrowid)
    return flag_list, error_list, result_list


def get_quotation_metadata(id_quotation: int, data_token):
    """Solo cabecera: (metadata JSON str, timestamps JSON str) o [] si no existe. type_sql=1.

    Lectura ligera para los merges de metadata (OCD, PUT de cabecera): evita
    agregar los items como hace get_quotation.
    """
    sql = "SELECT metadata, timestamps FROM sql_telintec_mod_admin.quotations WHERE id = %s"
    flag, error, out = execute_sql(sql, (id_quotation,), 1, data_token)
    return flag, error, out


def find_ocd_by_client_po_number(client_po_number: str, exclude_id, data_token):
    """id de OTRA cotización OCD con el mismo client_po_number (comparado sin
    mayúsculas ni espacios al borde, como la collation general_ci de tender_number)
    o None. Candado en código porque la llave vive en metadata JSON
    (docs/ocd_reglas_po_vencimiento.md). type_sql=1."""
    sql = (
        "SELECT id FROM sql_telintec_mod_admin.quotations "
        "WHERE JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.document_type')) = 'ocd' "
        "AND UPPER(TRIM(JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.client_po_number')))) = UPPER(TRIM(%s)) "
        "AND id <> %s LIMIT 1"
    )
    flag, error, out = execute_sql(sql, (client_po_number, exclude_id or 0), 1, data_token)
    if not flag:
        return False, error, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out[0]


def get_quotation_codes_by_prefix(prefix: str, data_token):
    """Folios (metadata.quotation_code) que empiezan con prefix, comparados sin
    mayúsculas: receta max + 1 del folio sugerido (docs/folio_sugerido_cotizaciones.md),
    como get_folios_by_pattern de SM. type_sql=2 -> lista de strings."""
    sql = (
        "SELECT JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.quotation_code')) "
        "FROM sql_telintec_mod_admin.quotations "
        "WHERE UPPER(JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.quotation_code'))) LIKE UPPER(%s)"
    )
    flag, error, out = execute_sql(sql, (prefix + "%",), 2, data_token)
    if not flag or not isinstance(out, list):
        return False, error, []
    return True, None, [str(row[0]) for row in out if row and row[0]]


def find_quotation_by_code(quotation_code: str, exclude_id, data_token):
    """id de OTRA cotización (cualquier document_type) con el mismo quotation_code,
    comparado sin mayúsculas ni espacios al borde, o None. Candado del folio al
    marcar una OCD (docs/folio_sugerido_cotizaciones.md); preventa y CISCO no lo
    usan. type_sql=1."""
    sql = (
        "SELECT id FROM sql_telintec_mod_admin.quotations "
        "WHERE UPPER(TRIM(JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.quotation_code')))) = UPPER(TRIM(%s)) "
        "AND id <> %s LIMIT 1"
    )
    flag, error, out = execute_sql(sql, (quotation_code, exclude_id or 0), 1, data_token)
    if not flag:
        return False, error, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out[0]


def get_quotation_items_delivery_dates(id_quotation: int, data_token):
    """[(id, partida, delivery_date | None)] de las partidas de la cotización, para
    validar un due_date nuevo contra las fechas ya capturadas. type_sql=2."""
    sql = (
        "SELECT id, partida, NULLIF(extra_info->>'$.delivery_date', '') "
        "FROM sql_telintec_mod_admin.quotation_items WHERE quotation_id = %s ORDER BY partida"
    )
    flag, error, out = execute_sql(sql, (id_quotation,), 2, data_token)
    if not flag or not isinstance(out, list):
        return False, error, []
    return True, None, out


def update_quotation(id_quotation, metadata: dict, data_token, timestamps=None):
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
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def create_item_quotation(item: dict, data_token):
    extra_info = item.get("extra_info")
    sql = (
        "INSERT INTO sql_telintec_mod_admin.quotation_items "
        "(quotation_id, contract_id, partida, section_index, udm, brand, type_p, "
        "n_part, quantity, revision, price_unit, description, description_small, "
        "extra_info, id_inventory) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        item["quotation_id"],
        item["contract_id"],
        item["partida"],
        item.get("section_index", 0),
        item["udm"],
        item["brand"],
        item["type_p"],
        item["n_part"],
        item["quantity"],
        item["revision"],
        item["price_unit"],
        item["description"],
        item["description_small"],
        json.dumps(extra_info) if extra_info else None,
        item["id_inventory"],
    )
    flag, error, out = execute_sql(sql, val, 4, data_token)
    return flag, error, out


def update_item_quotation(id_item, quotation_id, item: dict, data_token):
    """Actualiza un item. El AND quotation_id evita reescribir el item de otra
    cotizacion si llega un qa_item_id ajeno; out es el rowcount (0 = no aplicado)."""
    extra_info = item.get("extra_info")
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_items "
        "SET partida = %s, section_index = %s, udm = %s, brand = %s, type_p = %s, "
        "n_part = %s, quantity = %s, revision = %s, price_unit = %s, description = %s, "
        "description_small = %s, extra_info = %s, id_inventory = %s "
        "WHERE id = %s AND quotation_id = %s"
    )
    val = (
        item["partida"],
        item.get("section_index", 0),
        item["udm"],
        item["brand"],
        item["type_p"],
        item["n_part"],
        item["quantity"],
        item["revision"],
        item["price_unit"],
        item["description"],
        item["description_small"],
        json.dumps(extra_info) if extra_info else None,
        item["id_inventory"],
        id_item,
        quotation_id,
    )
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def delete_item_quotation(id_item, quotation_id, data_token):
    sql = (
        "DELETE FROM sql_telintec_mod_admin.quotation_items "
        "WHERE id = %s AND quotation_id = %s"
    )
    val = (id_item, quotation_id)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def delete_quotation_items(id_quotation, data_token):
    sql = "DELETE FROM sql_telintec_mod_admin.quotation_items WHERE quotation_id = %s"
    val = (id_quotation,)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def delete_contract_from_item_quotation(contract_id, data_token):
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_items "
        "SET contract_id = NULL "
        "WHERE contract_id = %s"
    )
    val = (contract_id,)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def assign_contract_to_quotation_items(id_quotation, contract_id, data_token):
    """Pone contract_id a las partidas de la cotizacion que aun no tienen contrato
    (licitacion ganada -> contrato, docs/tenders_control.md). type_sql=3."""
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_items "
        "SET contract_id = %s "
        "WHERE quotation_id = %s AND contract_id IS NULL"
    )
    val = (contract_id, id_quotation)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def set_quotation_metadata_keys(id_quotation, keys: dict, data_token):
    """JSON_SET de llaves sueltas en metadata, sin reescribir el resto (sincronia
    licitacion -> cotizacion interna). Las llaves las pone el codigo, nunca el
    payload: van interpoladas en la ruta JSON. type_sql=3."""
    if not keys:
        return True, None, 0
    paths = ", ".join(f"'$.{key}', %s" for key in keys)
    sql = f"UPDATE sql_telintec_mod_admin.quotations SET metadata = JSON_SET(metadata, {paths}) WHERE id = %s"
    val = tuple(keys.values()) + (id_quotation,)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def delete_quotation(id_quotation, data_token):
    sql = "DELETE FROM sql_telintec_mod_admin.quotations WHERE id = %s"
    val = (id_quotation,)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out


def get_quotation(data_token, id_quotation: int | None = None):
    """Cotizacion(es) con sus items en la columna products (indice 2).

    El orden de las PRIMERAS 12 llaves del JSON_OBJECT es load-bearing:
    compare_file_quotation arma un DataFrame con estos registros y compara por
    posicion contra un vector de 12 elementos (indices 0..11), asi que no
    reordenes ni insertes llaves entre 'qa_item_id' y 'id_inventory'. Las 3
    llaves de seccion (section_index/section_title/section_type) van al FINAL
    (indices 12..14): el compare solo lee 0..11, asi que son inertes para el.
    Despues van delivery_date (OCD) y las llaves CISCO item / smart_account /
    service_months / delivery_time (docs/cotizaciones_cisco.md), null fuera de CISCO.
    """
    if id_quotation is not None:
        sql = (
            "SELECT "
            "q.id AS quotation_id, "
            "q.metadata, "
            "JSON_ARRAYAGG(JSON_OBJECT( "
            "  'qa_item_id', qi.id, "
            "  'partida', qi.partida, "
            "  'udm', qi.udm, "
            "  'brand', qi.brand, "
            "  'type_p', qi.type_p, "
            "  'n_part', qi.n_part, "
            "  'quantity', qi.quantity, "
            "  'revision', qi.revision, "
            "  'price_unit', ROUND(qi.price_unit, 2), "
            "  'description', qi.description, "
            "  'description_small', qi.description_small, "
            "  'id_inventory', qi.id_inventory, "
            "  'section_index', qi.section_index, "
            "  'section_title', COALESCE(qi.extra_info->>'$.section_title', 'General'), "
            "  'section_type', COALESCE(qi.extra_info->>'$.section_type', 'general'), "
            "  'delivery_date', NULLIF(qi.extra_info->>'$.delivery_date', ''), "
            "  'item', qi.extra_info->>'$.item', "
            "  'smart_account', qi.extra_info->'$.smart_account', "
            "  'service_months', qi.extra_info->'$.service_months', "
            "  'delivery_time', qi.extra_info->>'$.delivery_time' "
            ")) AS products, "
            "q.creation, "
            "q.timestamps "
            "FROM sql_telintec_mod_admin.quotations q "
            "LEFT JOIN sql_telintec_mod_admin.quotation_items qi ON qi.quotation_id = q.id "
            "WHERE q.id = %s "
            "GROUP BY q.id"
        )
        val = (id_quotation,)
    else:
        sql = (
            "SELECT "
            "q.id AS quotation_id, "
            "q.metadata, "
            "JSON_ARRAYAGG(JSON_OBJECT( "
            "  'qa_item_id', qi.id, "
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
            "  'id_inventory', qi.id_inventory, "
            "  'section_index', qi.section_index, "
            "  'section_title', COALESCE(qi.extra_info->>'$.section_title', 'General'), "
            "  'section_type', COALESCE(qi.extra_info->>'$.section_type', 'general'), "
            "  'delivery_date', NULLIF(qi.extra_info->>'$.delivery_date', ''), "
            "  'item', qi.extra_info->>'$.item', "
            "  'smart_account', qi.extra_info->'$.smart_account', "
            "  'service_months', qi.extra_info->'$.service_months', "
            "  'delivery_time', qi.extra_info->>'$.delivery_time' "
            ")) AS products, "
            "q.creation, "
            "q.timestamps "
            "FROM sql_telintec_mod_admin.quotations q "
            "LEFT JOIN sql_telintec_mod_admin.quotation_items qi ON qi.quotation_id = q.id "
            "GROUP BY q.id"
        )
        val = ()

    flag, error, result = execute_sql(sql, val, 2, data_token)
    if not flag:
        return False, error, []
    if not isinstance(result, list):
        return False, error, []
    if id_quotation and len(result) == 0:
        return False, "Quotation not found", []
    return True, None, result


def get_quotation_data_display(data_token, id_quotation=None):
    if id_quotation is None:
        sql = (
            "SELECT id, "
            "metadata->'$.company', "
            "metadata->'$.quotation_code', "
            "creation "
            "FROM sql_telintec_mod_admin.quotations"
        )
        flag, error, result = execute_sql(sql, None, 5, data_token)
        if not flag:
            return False, error, None
        return True, None, result
    sql = (
        "SELECT id, "
        "metadata->'$.company', "
        "metadata->'$.quotation_code', "
        "creation "
        "FROM sql_telintec_mod_admin.quotations "
        "WHERE id = %s"
    )
    val = (id_quotation,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    if not isinstance(result, tuple):
        return False, error, None
    if len(result) == 0:
        return False, "Quotation not found", None
    else:
        return True, None, result[0]


def get_items_quotation_from_cotract(contract_id, data_token):
    # section_index va al FINAL (indice 4): check_for_partidas_updates indexa por
    # posicion (item[1]=partida, item[2]=id_inventory), asi que agregarlo al final
    # no mueve esos indices.
    sql = (
        "SELECT id, partida, id_inventory, quotation_id, section_index "
        "FROM sql_telintec_mod_admin.quotation_items "
        "WHERE contract_id = %s"
    )
    val = (contract_id,)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    if not isinstance(result, list):
        return False, error, []
    if len(result) == 0:
        return False, "Quotation not found", []
    else:
        return True, None, result


def update_quotation_item_partida_from_sm(
    contract_id, section_index, partida, id_inventory, data_token
):
    # section_index en el WHERE evita pegar en varias filas cuando la POS. reinicia
    # por seccion (partida repetida en el mismo contrato).
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_items "
        "SET id_inventory = %s "
        "WHERE contract_id = %s AND section_index = %s AND partida = %s"
    )
    val = (id_inventory, contract_id, section_index, partida)
    flag, error, out = execute_sql(sql, val, 3, data_token)
    return flag, error, out
