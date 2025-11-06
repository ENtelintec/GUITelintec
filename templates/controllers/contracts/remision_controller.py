# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 27/oct/2025  at 20:29 $"

import json
from datetime import datetime

import pytz

from static.constants import timezone_software, format_timestamps
from templates.database.connection import execute_sql


def create_remission(
    code: str,
    contract_id: int,
    client_id: int,
    emission: str,
    metadata: dict,
    user: str,
    status: int = 0,
):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    history = [
        {
            "timestamp": timestamp,
            "user": user,
            "action": "creation",
            "comment": "Remisión creada",
        }
    ]

    sql = (
        "INSERT INTO sql_telintec_mod_admin.remissions "
        "(code, contract_id, client_id, emission, metadata, history, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        code,
        contract_id,
        client_id,
        emission,
        json.dumps(metadata),
        json.dumps(history),
        status,
    )
    flag, error, id_remission = execute_sql(sql, val, 4)
    return flag, str(error), id_remission


def update_remission(
    id_remission: int,
    metadata_update: dict,
    history: list,
    status: int = None,
):
    if status is not None:
        sql = (
            "UPDATE sql_telintec_mod_admin.remissions "
            "SET metadata = %s, history = %s, status = %s WHERE id = %s"
        )
        val = (
            json.dumps(metadata_update),
            json.dumps(history),
            status,
            id_remission,
        )
    else:
        sql = (
            "UPDATE sql_telintec_mod_admin.remissions "
            "SET metadata = %s, history = %s WHERE id = %s"
        )
        val = (
            json.dumps(metadata_update),
            json.dumps(history),
            id_remission,
        )

    flag, error, result = execute_sql(sql, val, 3)
    return flag, str(error), result


def delete_remission(id_remission: int):
    sql = "DELETE FROM sql_telintec_mod_admin.remissions WHERE id = %s"
    flag, error, result = execute_sql(sql, (id_remission,), 3)
    return flag, str(error), result


def create_remission_item(
    remission_id: int,
    description: str,
    quantity: float,
    udm: str,
    price_unit: float,
    quotation_item_id: int = None,
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.remission_items "
        "(remission_id, quotation_item_id, description, quantity, udm, price_unit) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    val = (
        remission_id,
        quotation_item_id,
        description,
        quantity,
        udm,
        price_unit,
    )
    flag, error, id_item = execute_sql(sql, val, 4)
    return flag, str(error), id_item


def update_remission_item(
    id_item: int,
    description: str = None,
    quantity: float = None,
    udm: str = None,
    price_unit: float = None,
    quotation_item_id: int = None,
):
    # Construir dinámicamente los campos a actualizar
    fields = []
    values = []

    if description is not None:
        fields.append("description = %s")
        values.append(description)
    if quantity is not None:
        fields.append("quantity = %s")
        values.append(quantity)
    if udm is not None:
        fields.append("udm = %s")
        values.append(udm)
    if price_unit is not None:
        fields.append("price_unit = %s")
        values.append(price_unit)
    if quotation_item_id is not None:
        fields.append("quotation_item_id = %s")
        values.append(quotation_item_id)

    if not fields:
        return False, "No hay campos para actualizar", None

    sql = (
        f"UPDATE sql_telintec_mod_admin.remission_items SET {', '.join(fields)} "
        "WHERE id = %s"
    )
    values.append(id_item)

    flag, error, _ = execute_sql(sql, tuple(values), 3)
    return flag, str(error), id_item


def delete_remission_item(id_item: int):
    sql = "DELETE FROM sql_telintec_mod_admin.remission_items WHERE id = %s"
    flag, error, _ = execute_sql(sql, (id_item,), 3)
    return flag, str(error)


def get_remission_items(id_remission: int):
    sql = (
        "SELECT id, remission_id, quotation_item_id, description, quantity, udm, price_unit "
        "FROM sql_telintec_mod_admin.remission_items WHERE remission_id = %s"
    )
    flag, error, result = execute_sql(sql, (id_remission,), 2)
    return flag, str(error), result


def delete_remission_items_by_remission(id_remission: int):
    sql = "DELETE FROM sql_telintec_mod_admin.remission_items WHERE remission_id = %s"
    flag, error, _ = execute_sql(sql, (id_remission,), 3)
    return flag, str(error), id_remission


def fetch_remissions_with_items(status: str):
    """
    Obtiene remisiones con sus ítems anidados en formato JSON.
    :param status: Estado de la remisión (entero o 'all')
    :return: Lista de remisiones con ítems o mensaje de error
    """
    if status == "all":
        sql = (
            "SELECT "
            "r.id, r.code, r.client_id, r.emission, r.status, r.metadata, r.contract_id, "
            "JSON_ARRAYAGG(JSON_OBJECT("
            "'id', ri.id, "
            "'quotation_item_id', ri.quotation_item_id, "
            "'description', ri.description, "
            "'quantity', ri.quantity, "
            "'udm', ri.udm, "
            "'price_unit', ri.price_unit, "
            "'importe', ri.importe"
            ")) AS items "
            "FROM sql_telintec_mod_admin.remissions AS r "
            "LEFT JOIN sql_telintec_mod_admin.remission_items AS ri ON r.id = ri.remission_id "
            "GROUP BY r.id"
        )
        val = ()
    else:
        sql = (
            "SELECT "
            "r.id, r.code, r.client_id, r.emission, r.status, r.metadata, r.contract_id,  "
            "JSON_ARRAYAGG(JSON_OBJECT("
            "'id', ri.id, "
            "'quotation_item_id', ri.quotation_item_id, "
            "'description', ri.description, "
            "'quantity', ri.quantity, "
            "'udm', ri.udm, "
            "'price_unit', ri.price_unit, "
            "'importe', ri.importe"
            ")) AS items "
            "FROM sql_telintec_mod_admin.remissions AS r "
            "LEFT JOIN sql_telintec_mod_admin.remission_items AS ri ON r.id = ri.remission_id "
            "WHERE r.status = %s "
            "GROUP BY r.id"
        )
        val = (int(status),)

    flag, error, result = execute_sql(sql, val, 2)
    return flag, str(error), result
