# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 19/oct./2026  at 12:00 $"

"""Control de licitaciones FO-PRE-04 (docs/tenders_control.md). DDL en
scripts_db_handle/licitaciones.sql.

Una licitacion = fila en tenders + cotizacion interna (quotations.metadata.status
= 3) con las partidas en quotation_items (tenders.quotation_id, 1:1). El contrato
que nace de una licitacion ganada apunta a esa misma cotizacion.
"""

from templates.controllers.presales.remisions_controller import HISTORY_APPEND_SQL, json_param
from templates.database.connection import execute_sql

_TABLE = "sql_telintec_mod_admin.tenders"
_TABLE_Q = "sql_telintec_mod_admin.quotations"
_TABLE_QI = "sql_telintec_mod_admin.quotation_items"
_TABLE_CONTRACTS = "sql_telintec_mod_admin.contracts"
_TABLE_CUSTOMERS = "sql_telintec.customers_amc"

# quotations.metadata.status de la cotizacion interna de una licitacion.
QUOTATION_STATUS_TENDER = 3
# tenders.status: la unica que admite po_number y contract_id.
TENDER_STATUS_ASSIGNED = 1

# Columnas devueltas por los SELECT; el midleware mapea por indice con esta
# misma tupla, asi que el orden importa (append-only).
TENDER_COLUMNS = (
    "id_tender",
    "tender_number",
    "client_id",
    "description",
    "scope",
    "buyer_user",
    "field_user",
    "invitation_date",
    "closing_date",
    "amount_usd",
    "amount_mxn",
    "status",
    "po_number",
    "response_date",
    "submitted_date",
    "quotation_id",
    "contract_id",
    "created_by",
    "created_at",
    "updated_at",
    "history",
    "extra_info",
    # unidas (LEFT JOIN / subconsultas)
    "client_name",
    "contract_code",
    "contract_identifier",
    "currency",
    "items_count",
    "items_total",
)
_TABLE_COLUMNS = TENDER_COLUMNS[:22]
# Columnas que el POST/PUT pueden escribir (whitelist: van interpoladas en el SQL).
WRITABLE_COLUMNS = (
    "tender_number",
    "client_id",
    "description",
    "scope",
    "buyer_user",
    "field_user",
    "invitation_date",
    "closing_date",
    "amount_usd",
    "amount_mxn",
    "status",
    "po_number",
    "response_date",
    "submitted_date",
    "contract_id",
)
# Sin ORDER BY: el orden lo pone el midleware en Python (regla del sort buffer:
# el SELECT lleva JSON, docs/contracts_products_sort_memory_fix.md).
_SELECT = (
    f"SELECT {', '.join('t.' + c for c in _TABLE_COLUMNS)}, "
    "cu.name, c.code, NULLIF(JSON_UNQUOTE(JSON_EXTRACT(c.metadata, '$.identifier')), 'null'), "
    "NULLIF(JSON_UNQUOTE(JSON_EXTRACT(q.metadata, '$.currency')), 'null'), "
    f"(SELECT COUNT(*) FROM {_TABLE_QI} qi WHERE qi.quotation_id = t.quotation_id), "
    f"(SELECT COALESCE(SUM(COALESCE(qi.quantity, 0) * COALESCE(qi.price_unit, 0)), 0) "
    f" FROM {_TABLE_QI} qi WHERE qi.quotation_id = t.quotation_id) "
    f"FROM {_TABLE} t "
    f"LEFT JOIN {_TABLE_CUSTOMERS} cu ON cu.id_customer = t.client_id "
    f"LEFT JOIN {_TABLE_CONTRACTS} c ON c.id = t.contract_id "
    f"LEFT JOIN {_TABLE_Q} q ON q.id = t.quotation_id "
)


def is_duplicate_error(error) -> bool:
    """execute_sql devuelve el error como texto: 1062 = choque con un UNIQUE."""
    return "1062" in str(error or "") or "Duplicate entry" in str(error or "")


def get_tenders(filters: dict, data_token):
    """Listado con filtros opcionales. type_sql=2.

    filters: statuses (list[int]), client_id, date_from / date_to (sobre
    closing_date) y has_contract (1 / 0); None = no filtra.
    """
    where = []
    val: list = []
    statuses = filters.get("statuses")
    if statuses:
        where.append(f"t.status IN ({', '.join(['%s'] * len(statuses))})")
        val.extend(statuses)
    if filters.get("client_id") is not None:
        where.append("t.client_id = %s")
        val.append(filters["client_id"])
    if filters.get("date_from"):
        where.append("t.closing_date >= %s")
        val.append(filters["date_from"])
    if filters.get("date_to"):
        where.append("t.closing_date <= %s")
        val.append(filters["date_to"])
    if filters.get("has_contract") is not None:
        where.append("t.contract_id IS NOT NULL" if filters["has_contract"] else "t.contract_id IS NULL")
    sql = _SELECT + (f"WHERE {' AND '.join(where)}" if where else "")
    flag, error, out = execute_sql(sql, tuple(val), 2, data_token)
    if not flag or not isinstance(out, list):
        return False, error, []
    return True, None, out


def get_tender_by_id(id_tender: int, data_token):
    """Una licitacion. type_sql=1 -> tupla, o None si no existe."""
    flag, error, out = execute_sql(_SELECT + "WHERE t.id_tender = %s", (id_tender,), 1, data_token)
    if not flag:
        return False, error, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def get_tender_by_quotation(id_quotation: int, data_token):
    """La licitacion dueña de una cotizacion interna, o None. type_sql=1."""
    flag, error, out = execute_sql(_SELECT + "WHERE t.quotation_id = %s", (id_quotation,), 1, data_token)
    if not flag:
        return False, error, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def get_tender_id_by_number(tender_number: str, data_token):
    """id_tender con ese numero (la collation general_ci ignora mayusculas), o None."""
    sql = f"SELECT id_tender FROM {_TABLE} WHERE tender_number = %s"
    flag, error, out = execute_sql(sql, (tender_number,), 1, data_token)
    if not flag:
        return False, error, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out[0]


def get_tender_id_by_contract(contract_id: int, data_token):
    """id_tender ligada a ese contrato, o None."""
    sql = f"SELECT id_tender FROM {_TABLE} WHERE contract_id = %s"
    flag, error, out = execute_sql(sql, (contract_id,), 1, data_token)
    if not flag:
        return False, error, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out[0]


def insert_tender(values: dict, quotation_id: int, created_by, timestamp: str, history: list, data_token):
    """Inserta la licitacion. type_sql=4 -> lastrowid."""
    cols = [c for c in WRITABLE_COLUMNS if c in values]
    sql = (
        f"INSERT INTO {_TABLE} ({', '.join(cols)}, quotation_id, created_by, created_at, history) "
        f"VALUES ({', '.join(['%s'] * (len(cols) + 4))})"
    )
    val = tuple(values[c] for c in cols) + (quotation_id, created_by, timestamp, json_param(history))
    return execute_sql(sql, val, 4, data_token)


def update_tender(id_tender: int, changes: dict, history_entry: dict, timestamp: str, data_token):
    """Escribe solo las columnas que cambian + updated_at + entrada de history. type_sql=3."""
    cols = [c for c in WRITABLE_COLUMNS if c in changes]
    sets = [f"{c} = %s" for c in cols] + ["updated_at = %s", HISTORY_APPEND_SQL]
    sql = f"UPDATE {_TABLE} SET {', '.join(sets)} WHERE id_tender = %s"
    val = tuple(changes[c] for c in cols) + (timestamp, json_param(history_entry), id_tender)
    return execute_sql(sql, val, 3, data_token)


def link_tender_contract(id_tender: int, contract_id: int, history_entry: dict, timestamp: str, data_token):
    """Liga el contrato solo si la licitacion sigue asignada y sin contrato
    (UPDATE condicional: rowcount 0 = otro request gano la carrera). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE} SET contract_id = %s, updated_at = %s, {HISTORY_APPEND_SQL} "
        "WHERE id_tender = %s AND contract_id IS NULL AND status = %s"
    )
    val = (contract_id, timestamp, json_param(history_entry), id_tender, TENDER_STATUS_ASSIGNED)
    return execute_sql(sql, val, 3, data_token)


def append_tender_history(id_tender: int, history_entry: dict, timestamp: str, data_token):
    """Solo history + updated_at (p. ej. tras editar partidas). type_sql=3."""
    sql = f"UPDATE {_TABLE} SET updated_at = %s, {HISTORY_APPEND_SQL} WHERE id_tender = %s"
    return execute_sql(sql, (timestamp, json_param(history_entry), id_tender), 3, data_token)
