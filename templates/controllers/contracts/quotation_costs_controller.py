# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/sep./2026  at 19:30 $"

"""Análisis de costos por item cotizado (Preventa, FO-PRE-01 / FO-PRE-02):
quotation_item_costs (1:1 con quotation_items) + quotation_item_supplier_quotes
(N por item). DDL en scripts_db_handle/control_entregas_ocd.sql. Ver
docs/quotation_cost_analysis.md. Los calculados (unit_cost_mxn, unit_price_profit)
los escribe el midleware; aquí solo SQL.
"""

import json

from templates.database.connection import execute_sql

_TABLE_COST = "sql_telintec_mod_admin.quotation_item_costs"
_TABLE_SQ = "sql_telintec_mod_admin.quotation_item_supplier_quotes"
_TABLE_QI = "sql_telintec_mod_admin.quotation_items"
_TABLE_SUPPLIERS = "sql_telintec.suppliers_amc"

# Append-only: el midleware mapea por índice.
COST_COLUMNS = (
    "id_cost",
    "quotation_item_id",
    "quotation_id",
    "currency",
    "unit_cost",
    "exchange_rate",
    "unit_cost_mxn",
    "profit_pct",
    "unit_price_profit",
    "delivery_time",
    "service_months",
    "smart_account",
    "created_by",
    "timestamp",
    "history",
    "extra_info",
)
_SELECT_COST = f"SELECT {', '.join(COST_COLUMNS)} FROM {_TABLE_COST}"

SUPPLIER_QUOTE_COLUMNS = (
    "id_quote",
    "quotation_item_id",
    "position",
    "supplier_id",
    "supplier_name",
    "unit_price",
    "currency",
    "delivery_time",
    "comments",
    "is_selected",
    # unida
    "catalog_name",
)
_SELECT_SQ = (
    "SELECT sq.id_quote, sq.quotation_item_id, sq.position, sq.supplier_id, sq.supplier_name, "
    "sq.unit_price, sq.currency, sq.delivery_time, sq.comments, sq.is_selected, s.name "
    f"FROM {_TABLE_SQ} sq LEFT JOIN {_TABLE_SUPPLIERS} s ON s.id_supplier = sq.supplier_id "
)


def _rows(flag, e, out):
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def get_costs_by_quotation(quotation_id: int, data_token):
    """Análisis de todos los items de la cotización (COST_COLUMNS). type_sql=2."""
    sql = f"{_SELECT_COST} WHERE quotation_id = %s ORDER BY quotation_item_id"
    return _rows(*execute_sql(sql, (quotation_id,), 2, data_token))


def get_supplier_quotes_by_quotation(quotation_id: int, data_token):
    """Comparativa de proveedores de todos los items de la cotización (SUPPLIER_QUOTE_COLUMNS). type_sql=2."""
    sql = (
        f"{_SELECT_SQ} JOIN {_TABLE_QI} qi ON qi.id = sq.quotation_item_id "
        "WHERE qi.quotation_id = %s ORDER BY sq.quotation_item_id, sq.position"
    )
    return _rows(*execute_sql(sql, (quotation_id,), 2, data_token))


def insert_cost(data: dict, data_token):
    """INSERT del análisis de un item. type_sql=4 -> id_cost."""
    sql = (
        f"INSERT INTO {_TABLE_COST} "
        "(quotation_item_id, quotation_id, currency, unit_cost, exchange_rate, unit_cost_mxn, profit_pct, "
        "unit_price_profit, delivery_time, service_months, smart_account, created_by, timestamp, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data["quotation_item_id"], data["quotation_id"], data.get("currency") or "MXN",
        data.get("unit_cost"), data.get("exchange_rate"), data.get("unit_cost_mxn"), data.get("profit_pct"),
        data.get("unit_price_profit"), data.get("delivery_time"), data.get("service_months"), data.get("smart_account"),
        data.get("created_by"), data.get("timestamp"),
        json.dumps(data.get("history") or [], ensure_ascii=False),
        json.dumps(data.get("extra_info") or {}, ensure_ascii=False),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_cost(id_cost: int, data: dict, data_token):
    """UPDATE del análisis existente (misma fila; el history se pasa completo). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE_COST} SET currency = %s, unit_cost = %s, exchange_rate = %s, unit_cost_mxn = %s, "
        "profit_pct = %s, unit_price_profit = %s, delivery_time = %s, service_months = %s, smart_account = %s, "
        "history = %s, extra_info = %s WHERE id_cost = %s"
    )
    val = (
        data.get("currency") or "MXN", data.get("unit_cost"), data.get("exchange_rate"), data.get("unit_cost_mxn"),
        data.get("profit_pct"), data.get("unit_price_profit"), data.get("delivery_time"), data.get("service_months"),
        data.get("smart_account"),
        json.dumps(data.get("history") or [], ensure_ascii=False),
        json.dumps(data.get("extra_info") or {}, ensure_ascii=False),
        id_cost,
    )
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_cost_by_item(quotation_item_id: int, data_token):
    """Borra el análisis de un item (la comparativa se borra aparte). type_sql=3."""
    sql = f"DELETE FROM {_TABLE_COST} WHERE quotation_item_id = %s"
    flag, e, out = execute_sql(sql, (quotation_item_id,), 3, data_token)
    return flag, e, out


def delete_supplier_quotes_by_item(quotation_item_id: int, data_token):
    sql = f"DELETE FROM {_TABLE_SQ} WHERE quotation_item_id = %s"
    flag, e, out = execute_sql(sql, (quotation_item_id,), 3, data_token)
    return flag, e, out


def insert_supplier_quote(data: dict, data_token):
    sql = (
        f"INSERT INTO {_TABLE_SQ} "
        "(quotation_item_id, position, supplier_id, supplier_name, unit_price, currency, delivery_time, comments, is_selected) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data["quotation_item_id"], data["position"], data.get("supplier_id"), data.get("supplier_name"),
        data.get("unit_price"), data.get("currency") or "MXN", data.get("delivery_time"), data.get("comments"),
        1 if data.get("is_selected") else 0,
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_quotation_item_price(id_item: int, quotation_id: int, price_unit, data_token):
    """Escribe price_unit de la partida (apply_prices). type_sql=3."""
    sql = f"UPDATE {_TABLE_QI} SET price_unit = %s WHERE id = %s AND quotation_id = %s"
    flag, e, out = execute_sql(sql, (price_unit, id_item, quotation_id), 3, data_token)
    return flag, e, out


def get_supplier_names(ids: list, data_token):
    """{id_supplier: name} de los ids dados (para validar y snapshotear). type_sql=2."""
    if not ids:
        return True, None, {}
    ph = ", ".join(["%s"] * len(ids))
    sql = f"SELECT id_supplier, name FROM {_TABLE_SUPPLIERS} WHERE id_supplier IN ({ph})"
    flag, e, out = _rows(*execute_sql(sql, tuple(ids), 2, data_token))
    if not flag:
        return False, e, {}
    return True, None, {int(r[0]): r[1] for r in out}
