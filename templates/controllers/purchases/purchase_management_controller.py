# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 24/jul./2026  at 12:00 $"

import json

from templates.database.connection import execute_sql

# Orden canonico de columnas de la tabla (sin el PK autoincrement en INSERT).
# Se usa tanto para INSERT como para leer las filas del SELECT.
_TABLE = "sql_telintec_mod_admin.purchase_management"

# Columnas devueltas por los SELECT (incluye el PK). El midleware mapea por
# indice usando esta misma tupla, asi que el orden importa.
SELECT_COLUMNS = (
    "id_pm",
    "timestamp",
    "created_by",
    "request_date",
    "description",
    "classification",
    "supplier_id",
    "client_id",
    "contract_id",
    "po_id",
    "amount_usd",
    "amount_mxn",
    "status",
    "payment_date",
    "approved",
    "approval_date",
    "comments",
    "debt_type",
    "profit_percentage",
    "cost_ternium_iva",
    "profit",
    "is_active",
    "history",
    "extra_info",
)

_SELECT_SQL = f"SELECT {', '.join(SELECT_COLUMNS)} FROM {_TABLE}"


def insert_purchase_management(data: dict, data_token):
    """Inserta un registro de Gestion de Compras. type_sql=4 -> lastrowid."""
    sql = (
        f"INSERT INTO {_TABLE} "
        "(timestamp, created_by, request_date, description, classification, "
        "supplier_id, client_id, contract_id, po_id, amount_usd, amount_mxn, "
        "status, payment_date, approved, approval_date, comments, debt_type, "
        "profit_percentage, cost_ternium_iva, profit, is_active, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
        "%s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("timestamp"),
        data.get("created_by"),
        data.get("request_date"),
        data.get("description"),
        data.get("classification"),
        data.get("supplier_id"),
        data.get("client_id"),
        data.get("contract_id"),
        data.get("po_id"),
        data.get("amount_usd"),
        data.get("amount_mxn"),
        data.get("status", 0),
        data.get("payment_date"),
        data.get("approved", 0),
        data.get("approval_date"),
        data.get("comments"),
        data.get("debt_type"),
        data.get("profit_percentage"),
        data.get("cost_ternium_iva"),
        data.get("profit"),
        data.get("is_active", 1),
        json.dumps(data.get("history", [])),
        json.dumps(data.get("extra_info", {})),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_purchase_management(id_pm: int, data: dict, data_token):
    """Actualiza todas las columnas base de un registro. type_sql=3 -> rowcount."""
    sql = (
        f"UPDATE {_TABLE} SET "
        "request_date = %s, description = %s, classification = %s, "
        "supplier_id = %s, client_id = %s, contract_id = %s, po_id = %s, "
        "amount_usd = %s, amount_mxn = %s, status = %s, payment_date = %s, "
        "approved = %s, approval_date = %s, comments = %s, debt_type = %s, "
        "profit_percentage = %s, cost_ternium_iva = %s, profit = %s, "
        "history = %s, extra_info = %s "
        "WHERE id_pm = %s"
    )
    val = (
        data.get("request_date"),
        data.get("description"),
        data.get("classification"),
        data.get("supplier_id"),
        data.get("client_id"),
        data.get("contract_id"),
        data.get("po_id"),
        data.get("amount_usd"),
        data.get("amount_mxn"),
        data.get("status", 0),
        data.get("payment_date"),
        data.get("approved", 0),
        data.get("approval_date"),
        data.get("comments"),
        data.get("debt_type"),
        data.get("profit_percentage"),
        data.get("cost_ternium_iva"),
        data.get("profit"),
        json.dumps(data.get("history", [])),
        json.dumps(data.get("extra_info", {})),
        id_pm,
    )
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def set_active_purchase_management(id_pm: int, is_active: int, history: list, data_token):
    """Cancelacion suave / reactivacion: solo toca is_active + history. type_sql=3."""
    sql = (
        f"UPDATE {_TABLE} SET is_active = %s, history = %s WHERE id_pm = %s"
    )
    val = (is_active, json.dumps(history), id_pm)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_purchase_management(id_pm: int, data_token):
    """Borrado fisico. type_sql=3 -> rowcount."""
    sql = f"DELETE FROM {_TABLE} WHERE id_pm = %s"
    val = (id_pm,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def get_purchase_management_list(
    status: int | None,
    classification: int | None,
    client_id: int | None,
    date_from: str | None,
    date_to: str | None,
    is_active: int | None,
    data_token,
):
    """Lista con filtros opcionales (param-or-NULL). type_sql=2 -> fetchall."""
    sql = (
        f"{_SELECT_SQL} "
        "WHERE (status = %s OR %s IS NULL) "
        "AND (classification = %s OR %s IS NULL) "
        "AND (client_id = %s OR %s IS NULL) "
        "AND (request_date >= %s OR %s IS NULL) "
        "AND (request_date <= %s OR %s IS NULL) "
        "AND (is_active = %s OR %s IS NULL) "
        "ORDER BY request_date DESC, id_pm DESC"
    )
    val = (
        status, status,
        classification, classification,
        client_id, client_id,
        date_from, date_from,
        date_to, date_to,
        is_active, is_active,
    )
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    return flag, e, my_result


def get_purchase_management_by_id(id_pm: int, data_token):
    """Un solo registro por id. type_sql=1 -> fetchone (tupla o []) ."""
    sql = f"{_SELECT_SQL} WHERE id_pm = %s"
    val = (id_pm,)
    flag, e, my_result = execute_sql(sql, val, 1, data_token)
    return flag, e, my_result
