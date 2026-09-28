# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/sep./2026  at 16:30 $"

"""Control de Entregas (Administración): cabecera por cotización OCD y las
consultas derivadas (pedido / entregado / pendiente por partida). DDL en
scripts_db_handle/control_entregas_ocd.sql + control_entregas_ocd_membresia.sql.

Membresía remisión -> control: activity_reports.delivery_control_id (única
llave; docs/control_entregas.md). activity_reports.quotation_id apunta a
quotations_activities y NO sirve para esto. Las cantidades entregadas se
derivan de quotation_activity_items.item_c_id -> quotation_items(id) con la
remisión no cancelada (activity_reports.status <> 3); nunca se almacenan.
"""

import json

from templates.database.connection import execute_sql

_TABLE = "sql_telintec_mod_admin.delivery_controls"
_TABLE_AR = "sql_telintec_mod_admin.activity_reports"
_TABLE_Q = "sql_telintec_mod_admin.quotations"
_TABLE_QI = "sql_telintec_mod_admin.quotation_items"
_TABLE_QAI = "sql_telintec_mod_admin.quotation_activity_items"
_TABLE_CUSTOMERS = "sql_telintec.customers_amc"

# Remisión cancelada (activity_reports.status): no cuenta como entregado.
REMISSION_CANCELLED_STATUS = 3
CONTROL_CANCELLED_STATUS = 2

# Columnas devueltas por los SELECT; el midleware mapea por índice con estas
# mismas tuplas, así que el orden importa (append-only).
CONTROL_COLUMNS = (
    "id_control",
    "quotation_id",
    "client_id",
    "title",
    "client_po_number",
    "currency",
    "status",
    "custom_fields",
    "created_by",
    "timestamp",
    "history",
    "extra_info",
    # unidas
    "quotation_code",
    "quotation_document_type",
    "quotation_approved_date",
    "client_name",
    "remissions_count",
)
_SELECT_CONTROL = (
    "SELECT dc.id_control, dc.quotation_id, dc.client_id, dc.title, dc.client_po_number, "
    "dc.currency, dc.status, dc.custom_fields, dc.created_by, dc.timestamp, dc.history, dc.extra_info, "
    "q.metadata->>'$.quotation_code', q.metadata->>'$.document_type', q.metadata->>'$.approved_date', "
    "cu.name, "
    f"(SELECT COUNT(*) FROM {_TABLE_AR} ar WHERE ar.delivery_control_id = dc.id_control) "
    f"FROM {_TABLE} dc "
    f"LEFT JOIN {_TABLE_Q} q ON q.id = dc.quotation_id "
    f"LEFT JOIN {_TABLE_CUSTOMERS} cu ON cu.id_customer = dc.client_id "
)

# Partidas de la cotización (pedido). Append-only.
ORDER_ITEM_COLUMNS = (
    "id",
    "partida",
    "section_index",
    "udm",
    "quantity",
    "price_unit",
    "description",
    "n_part",
    "brand",
)

# Remisiones vistas desde el control (append-only).
REMISSION_LINK_COLUMNS = (
    "id",
    "client_id",
    "history",
    "delivery_control_id",
    "control_status",
    "status",
    "folio",
)
_SELECT_REMISSION_LINK = (
    "SELECT ar.id, ar.client_id, ar.history, ar.delivery_control_id, dcl.status, ar.status, ar.folio "
    f"FROM {_TABLE_AR} ar "
    f"LEFT JOIN {_TABLE} dcl ON dcl.id_control = ar.delivery_control_id "
)


def _rows(flag, e, out):
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def _placeholders(ids) -> str:
    return ", ".join(["%s"] * len(ids))


# --- Cabecera -------------------------------------------------------------------
def insert_delivery_control(data: dict, data_token):
    """Inserta la cabecera. type_sql=4 -> lastrowid."""
    sql = (
        f"INSERT INTO {_TABLE} "
        "(quotation_id, client_id, title, client_po_number, currency, status, custom_fields, "
        "created_by, timestamp, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data["quotation_id"],
        data["client_id"],
        data["title"],
        data.get("client_po_number"),
        data.get("currency") or "MXN",
        int(data.get("status") or 0),
        json.dumps(data.get("custom_fields") or [], ensure_ascii=False),
        data.get("created_by"),
        data.get("timestamp"),
        json.dumps(data.get("history") or [], ensure_ascii=False),
        json.dumps(data.get("extra_info") or {}, ensure_ascii=False),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def get_delivery_controls(
    quotation_id: int | None,
    client_id: int | None,
    status: int | None,
    active_only: int | None,
    data_token,
):
    """Listado param-or-NULL. active_only (no NULL) = status <> 2. type_sql=2."""
    sql = (
        f"{_SELECT_CONTROL} "
        "WHERE (%s IS NULL OR dc.quotation_id = %s) "
        "AND (%s IS NULL OR dc.client_id = %s) "
        "AND (%s IS NULL OR dc.status = %s) "
        f"AND (%s IS NULL OR dc.status <> {CONTROL_CANCELLED_STATUS}) "
        "ORDER BY dc.id_control DESC"
    )
    val = (quotation_id, quotation_id, client_id, client_id, status, status, active_only)
    return _rows(*execute_sql(sql, val, 2, data_token))


def get_delivery_control_by_id(id_control: int, data_token):
    """Una cabecera por id (cualquier status). type_sql=1 -> tupla o None."""
    sql = f"{_SELECT_CONTROL} WHERE dc.id_control = %s"
    flag, e, out = execute_sql(sql, (id_control,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def get_active_delivery_control_by_quotation(quotation_id: int, data_token):
    """Control NO cancelado de la cotización (a lo más uno). type_sql=1."""
    sql = f"{_SELECT_CONTROL} WHERE dc.quotation_id = %s AND dc.status <> {CONTROL_CANCELLED_STATUS} LIMIT 1"
    flag, e, out = execute_sql(sql, (quotation_id,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def get_active_controls_by_quotations(quotation_ids: list, data_token):
    """(id_control, quotation_id, client_id, status) de los controles NO cancelados
    de esas cotizaciones. type_sql=2."""
    if not quotation_ids:
        return True, None, []
    sql = (
        f"SELECT id_control, quotation_id, client_id, status FROM {_TABLE} "
        f"WHERE quotation_id IN ({_placeholders(quotation_ids)}) AND status <> {CONTROL_CANCELLED_STATUS}"
    )
    return _rows(*execute_sql(sql, tuple(quotation_ids), 2, data_token))


def update_delivery_control_header(id_control: int, data: dict, history: list, data_token):
    """UPDATE de la cabecera editable (title, client_po_number, currency, status). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE} SET title = %s, client_po_number = %s, currency = %s, status = %s, history = %s "
        "WHERE id_control = %s"
    )
    val = (
        data["title"],
        data.get("client_po_number"),
        data.get("currency") or "MXN",
        int(data.get("status") or 0),
        json.dumps(history, ensure_ascii=False),
        id_control,
    )
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def update_delivery_control_custom_fields(id_control: int, custom_fields: list, history: list, data_token):
    sql = f"UPDATE {_TABLE} SET custom_fields = %s, history = %s WHERE id_control = %s"
    val = (json.dumps(custom_fields, ensure_ascii=False), json.dumps(history, ensure_ascii=False), id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def set_delivery_control_status(id_control: int, status: int, history: list | None, data_token):
    """Cambia status (0 abierto / 1 completo / 2 cancelado). history None = no tocar. type_sql=3."""
    if history is None:
        sql = f"UPDATE {_TABLE} SET status = %s WHERE id_control = %s"
        val = (status, id_control)
    else:
        sql = f"UPDATE {_TABLE} SET status = %s, history = %s WHERE id_control = %s"
        val = (status, json.dumps(history, ensure_ascii=False), id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def update_delivery_control_history(id_control: int, history: list, data_token):
    sql = f"UPDATE {_TABLE} SET history = %s WHERE id_control = %s"
    val = (json.dumps(history, ensure_ascii=False), id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_delivery_control(id_control: int, data_token):
    """Borrado físico (solo testers / limpieza). Con la FK opcional, las
    remisiones ligadas quedan con delivery_control_id NULL. type_sql=3."""
    sql = f"DELETE FROM {_TABLE} WHERE id_control = %s"
    flag, e, out = execute_sql(sql, (id_control,), 3, data_token)
    return flag, e, out


# --- Derivados: pedido vs entregado ----------------------------------------------
def get_quotation_order_items(quotation_id: int, data_token):
    """Partidas de la cotización (ORDER_ITEM_COLUMNS). type_sql=2."""
    sql = (
        f"SELECT {', '.join(ORDER_ITEM_COLUMNS)} FROM {_TABLE_QI} "
        "WHERE quotation_id = %s ORDER BY section_index, partida, id"
    )
    return _rows(*execute_sql(sql, (quotation_id,), 2, data_token))


def get_quotation_items_by_ids(item_ids: list, data_token):
    """(id, quotation_id, quantity, partida, description) de partidas por id. type_sql=2."""
    if not item_ids:
        return True, None, []
    sql = (
        f"SELECT id, quotation_id, quantity, partida, description FROM {_TABLE_QI} "
        f"WHERE id IN ({_placeholders(item_ids)})"
    )
    return _rows(*execute_sql(sql, tuple(item_ids), 2, data_token))


def get_delivered_by_item(quotation_id: int, exclude_report_id: int | None, data_token):
    """Por partida (item_c_id): (item_c_id, delivered_qty, delivered_amount,
    remissions_count, last_date) sumando los items de remisión no cancelada que
    apuntan a las partidas de la cotización. exclude_report_id deja fuera una
    remisión (la que se está editando). type_sql=2."""
    sql = (
        "SELECT qai.item_c_id, COALESCE(SUM(qai.quantity), 0), COALESCE(SUM(qai.line_total), 0), "
        "COUNT(DISTINCT ar.id), MAX(ar.date) "
        f"FROM {_TABLE_QAI} qai "
        f"JOIN {_TABLE_AR} ar ON ar.id = qai.report_id "
        f"JOIN {_TABLE_QI} qi ON qi.id = qai.item_c_id "
        "WHERE qi.quotation_id = %s "
        f"AND COALESCE(ar.status, 0) <> {REMISSION_CANCELLED_STATUS} "
        "AND (%s IS NULL OR ar.id <> %s) "
        "GROUP BY qai.item_c_id"
    )
    val = (quotation_id, exclude_report_id, exclude_report_id)
    return _rows(*execute_sql(sql, val, 2, data_token))


def get_delivery_totals_by_quotations(quotation_ids: list, data_token):
    """Para el listado: por cotización (quotation_id, ordered_qty, ordered_amount,
    delivered_qty, delivered_amount, last_date). type_sql=2."""
    if not quotation_ids:
        return True, None, []
    ph = _placeholders(quotation_ids)
    sql = (
        "SELECT qi.quotation_id, "
        "COALESCE(SUM(qi.quantity), 0), COALESCE(SUM(qi.quantity * qi.price_unit), 0), "
        "COALESCE(SUM(d.delivered_qty), 0), COALESCE(SUM(d.delivered_amount), 0), MAX(d.last_date) "
        f"FROM {_TABLE_QI} qi "
        "LEFT JOIN ("
        "  SELECT qai.item_c_id, SUM(qai.quantity) AS delivered_qty, SUM(qai.line_total) AS delivered_amount, "
        "         MAX(ar.date) AS last_date "
        f"  FROM {_TABLE_QAI} qai JOIN {_TABLE_AR} ar ON ar.id = qai.report_id "
        f"  WHERE COALESCE(ar.status, 0) <> {REMISSION_CANCELLED_STATUS} AND qai.item_c_id IS NOT NULL "
        "  GROUP BY qai.item_c_id"
        ") d ON d.item_c_id = qi.id "
        f"WHERE qi.quotation_id IN ({ph}) "
        "GROUP BY qi.quotation_id"
    )
    return _rows(*execute_sql(sql, tuple(quotation_ids), 2, data_token))


def get_delivery_control_remissions(id_control: int, quotation_id: int, data_token):
    """Remisiones ligadas al control: (id, folio, date, status, amount, on_order_amount,
    extra_info). amount = Σ line_total de todos sus items; on_order_amount = solo
    los items que apuntan a partidas de la cotización. type_sql=2."""
    sql = (
        "SELECT ar.id, ar.folio, ar.date, ar.status, "
        f"(SELECT COALESCE(SUM(x.line_total), 0) FROM {_TABLE_QAI} x WHERE x.report_id = ar.id), "
        f"(SELECT COALESCE(SUM(y.line_total), 0) FROM {_TABLE_QAI} y JOIN {_TABLE_QI} qy ON qy.id = y.item_c_id "
        " WHERE y.report_id = ar.id AND qy.quotation_id = %s), "
        "ar.extra_info "
        f"FROM {_TABLE_AR} ar WHERE ar.delivery_control_id = %s ORDER BY ar.date, ar.id"
    )
    return _rows(*execute_sql(sql, (quotation_id, id_control), 2, data_token))


def get_delivery_control_off_order_items(id_control: int, quotation_id: int, data_token):
    """Items de las remisiones del control que NO apuntan a una partida de la
    cotización (item_c_id NULL o de otra cotización), remisión no cancelada:
    (qa_item_id, report_id, folio, description, udm, quantity, unit_price, line_total, item_c_id). type_sql=2."""
    sql = (
        "SELECT qai.qa_item_id, qai.report_id, ar.folio, qai.description, qai.udm, qai.quantity, "
        "qai.unit_price, qai.line_total, qai.item_c_id "
        f"FROM {_TABLE_QAI} qai "
        f"JOIN {_TABLE_AR} ar ON ar.id = qai.report_id "
        f"LEFT JOIN {_TABLE_QI} qi ON qi.id = qai.item_c_id "
        f"WHERE ar.delivery_control_id = %s AND COALESCE(ar.status, 0) <> {REMISSION_CANCELLED_STATUS} "
        "AND (qai.item_c_id IS NULL OR qi.quotation_id IS NULL OR qi.quotation_id <> %s) "
        "ORDER BY ar.id, qai.qa_item_id"
    )
    return _rows(*execute_sql(sql, (id_control, quotation_id), 2, data_token))


# --- Membresía ------------------------------------------------------------------
def get_remission_link_rows(ids: list, data_token):
    """REMISSION_LINK_COLUMNS de las remisiones pedidas. type_sql=2."""
    if not ids:
        return True, None, []
    sql = f"{_SELECT_REMISSION_LINK} WHERE ar.id IN ({_placeholders(ids)})"
    return _rows(*execute_sql(sql, tuple(ids), 2, data_token))


def get_free_remissions_for_quotation(quotation_id: int, client_id: int, data_token):
    """Remisiones del cliente, libres (sin control o en uno cancelado) y con al
    menos un item que apunte a una partida de la cotización. type_sql=2."""
    sql = (
        f"{_SELECT_REMISSION_LINK} "
        "WHERE ar.client_id = %s "
        f"AND (ar.delivery_control_id IS NULL OR dcl.status = {CONTROL_CANCELLED_STATUS}) "
        f"AND EXISTS (SELECT 1 FROM {_TABLE_QAI} qai JOIN {_TABLE_QI} qi ON qi.id = qai.item_c_id "
        "            WHERE qai.report_id = ar.id AND qi.quotation_id = %s)"
    )
    return _rows(*execute_sql(sql, (client_id, quotation_id), 2, data_token))


def attach_remission_to_delivery_control(id_report: int, id_control: int, history: list, data_token):
    """Liga la remisión al control. Guard: solo si está libre, ya era de este
    control o apunta a uno cancelado. type_sql=3 -> 0 filas = alguien la tomó antes."""
    sql = (
        f"UPDATE {_TABLE_AR} SET delivery_control_id = %s, history = %s "
        "WHERE id = %s AND (delivery_control_id IS NULL OR delivery_control_id = %s "
        f"OR delivery_control_id NOT IN (SELECT id_control FROM {_TABLE} WHERE status <> {CONTROL_CANCELLED_STATUS}))"
    )
    val = (id_control, json.dumps(history, ensure_ascii=False), id_report, id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def detach_remission_from_delivery_control(id_report: int, id_control: int, history: list, data_token):
    sql = (
        f"UPDATE {_TABLE_AR} SET delivery_control_id = NULL, history = %s "
        "WHERE id = %s AND delivery_control_id = %s"
    )
    val = (json.dumps(history, ensure_ascii=False), id_report, id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


# --- Valores de columnas dinámicas por remisión (extra_info.delivery_fields) --------
def get_remission_delivery_fields(id_report: int, data_token):
    """(delivery_control_id, extra_info) de una remisión. type_sql=1."""
    sql = f"SELECT delivery_control_id, extra_info, client_id, status FROM {_TABLE_AR} WHERE id = %s"
    flag, e, out = execute_sql(sql, (id_report,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def set_remission_delivery_fields(id_report: int, values: dict, data_token):
    """Escribe extra_info.delivery_fields completo (JSON_SET sobre el extra_info). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE_AR} SET extra_info = JSON_SET(COALESCE(extra_info, JSON_OBJECT()), "
        "'$.delivery_fields', CAST(%s AS JSON)) WHERE id = %s"
    )
    val = (json.dumps(values, ensure_ascii=False), id_report)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def remove_delivery_field_keys_from_remissions(id_control: int, keys: list, data_token):
    """Sweep: quita las llaves dadas de extra_info.delivery_fields en las
    remisiones del control. type_sql=3 -> filas afectadas."""
    if not keys:
        return True, None, 0
    paths = ", ".join(["%s"] * len(keys))
    sql = (
        f"UPDATE {_TABLE_AR} SET extra_info = JSON_REMOVE(extra_info, {paths}) "
        "WHERE delivery_control_id = %s AND JSON_EXTRACT(extra_info, '$.delivery_fields') IS NOT NULL"
    )
    val = tuple(f"$.delivery_fields.{k}" for k in keys) + (id_control,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out
