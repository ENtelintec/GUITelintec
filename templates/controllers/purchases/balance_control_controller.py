# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 11/sep./2026  at 12:00 $"

"""Control de saldos (Cobranza): cabecera por contrato, catalogo de formatos ISO
y movimientos de saldo. DDL en scripts_db_handle/control_saldos.sql.

Membresia remision -> control: activity_reports.contract_id (no hay vinculo nuevo).
"""

import json

from templates.database.connection import execute_sql

_TABLE = "sql_telintec_mod_admin.balance_controls"
_TABLE_MOV = "sql_telintec_mod_admin.balance_control_movements"
_TABLE_FMT = "sql_telintec_mod_admin.iso_formats"
_TABLE_AR = "sql_telintec_mod_admin.activity_reports"
_TABLE_CONTRACTS = "sql_telintec_mod_admin.contracts"

# Columnas devueltas por los SELECT; el midleware mapea por indice con estas
# mismas tuplas, asi que el orden importa (append-only).
FORMAT_COLUMNS = (
    "id",
    "code",
    "revision",
    "name",
    "department",
    "emission_date",
    "config",
    "is_active",
    "history",
    "created_by",
    "timestamp",
)
_SELECT_FMT = f"SELECT {', '.join(FORMAT_COLUMNS)} FROM {_TABLE_FMT}"

CONTROL_COLUMNS = (
    "id_control",
    "contract_id",
    "format_id",
    "month_period",
    "currency",
    "contract_number",
    "pedido_exiros",
    "contracted_amount",
    "start_date",
    "end_date",
    "plant",
    "coordinator",
    "contract_object",
    "custom_fields",
    "is_active",
    "created_by",
    "timestamp",
    "history",
    "extra_info",
    # unidas (LEFT JOIN): formato y contrato
    "format_code",
    "format_revision",
    "format_name",
    "contract_code",
    "contract_abbreviation",
    "contract_identifier",
    "remissions_count",
)
_SELECT_CONTROL = (
    "SELECT bc.id_control, bc.contract_id, bc.format_id, bc.month_period, bc.currency, "
    "bc.contract_number, bc.pedido_exiros, bc.contracted_amount, bc.start_date, bc.end_date, "
    "bc.plant, bc.coordinator, bc.contract_object, bc.custom_fields, bc.is_active, "
    "bc.created_by, bc.timestamp, bc.history, bc.extra_info, "
    "f.code, f.revision, f.name, c.code, c.abbreviation, "
    "JSON_UNQUOTE(JSON_EXTRACT(c.metadata, '$.identifier')), "
    f"(SELECT COUNT(*) FROM {_TABLE_AR} ar WHERE ar.contract_id = bc.contract_id) "
    f"FROM {_TABLE} bc "
    f"LEFT JOIN {_TABLE_FMT} f ON f.id = bc.format_id "
    f"LEFT JOIN {_TABLE_CONTRACTS} c ON c.id = bc.contract_id "
)

MOVEMENT_COLUMNS = (
    "id_movement",
    "id_control",
    "type",
    "movement_date",
    "amount",
    "previous_balance",
    "resulting_balance",
    "user_id",
    "user_name",
    "reason",
    "document",
    "timestamp",
    "extra_info",
)
_SELECT_MOV = f"SELECT {', '.join(MOVEMENT_COLUMNS)} FROM {_TABLE_MOV}"


# --- Formatos ISO (catalogo de SGI) ---------------------------------------------
def get_iso_formats(data_token, only_active: bool = True):
    """Lista de formatos ISO. type_sql=2 (o 5 sin filtro)."""
    if only_active:
        sql = f"{_SELECT_FMT} WHERE is_active = %s ORDER BY id"
        flag, e, out = execute_sql(sql, (1,), 2, data_token)
    else:
        sql = f"{_SELECT_FMT} ORDER BY id"
        flag, e, out = execute_sql(sql, None, 5, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def get_iso_format_by_id(id_format: int, data_token):
    """Un formato por id. type_sql=1 -> tupla o [] si no existe."""
    sql = f"{_SELECT_FMT} WHERE id = %s"
    flag, e, out = execute_sql(sql, (id_format,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


# --- Cabecera del control -------------------------------------------------------
def insert_balance_control(data: dict, data_token):
    """Inserta la cabecera. type_sql=4 -> lastrowid."""
    sql = (
        f"INSERT INTO {_TABLE} "
        "(contract_id, format_id, month_period, currency, contract_number, pedido_exiros, "
        "contracted_amount, start_date, end_date, plant, coordinator, contract_object, "
        "custom_fields, is_active, created_by, timestamp, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("contract_id"),
        data.get("format_id"),
        data.get("month_period"),
        data.get("currency", "MXN"),
        data.get("contract_number"),
        data.get("pedido_exiros"),
        data.get("contracted_amount", 0),
        data.get("start_date"),
        data.get("end_date"),
        data.get("plant"),
        data.get("coordinator"),
        data.get("contract_object"),
        json.dumps(data.get("custom_fields", []), ensure_ascii=False),
        data.get("is_active", 1),
        data.get("created_by"),
        data.get("timestamp"),
        json.dumps(data.get("history", []), ensure_ascii=False),
        json.dumps(data.get("extra_info", {}), ensure_ascii=False),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def get_balance_controls(
    contract_id: int | None,
    format_id: int | None,
    is_active: int | None,
    data_token,
):
    """Listado con filtros estilo param-or-NULL. type_sql=2."""
    sql = (
        f"{_SELECT_CONTROL} "
        "WHERE (%s IS NULL OR bc.contract_id = %s) "
        "AND (%s IS NULL OR bc.format_id = %s) "
        "AND (%s IS NULL OR bc.is_active = %s) "
        "ORDER BY bc.id_control DESC"
    )
    val = (contract_id, contract_id, format_id, format_id, is_active, is_active)
    flag, e, out = execute_sql(sql, val, 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def get_balance_control_by_id(id_control: int, data_token):
    """Una cabecera por id (activa o no). type_sql=1."""
    sql = f"{_SELECT_CONTROL} WHERE bc.id_control = %s"
    flag, e, out = execute_sql(sql, (id_control,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def get_active_balance_control_by_contract(contract_id: int, data_token):
    """El control ACTIVO del contrato (a lo mas uno). type_sql=1."""
    sql = (
        f"{_SELECT_CONTROL} WHERE bc.contract_id = %s AND bc.is_active = 1 "
        "ORDER BY bc.id_control DESC LIMIT 1"
    )
    flag, e, out = execute_sql(sql, (contract_id,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def update_balance_control_header(id_control: int, data: dict, data_token):
    """Actualiza la base editable + history + extra_info. NO toca contract_id,
    format_id ni contracted_amount (el monto solo se mueve con movimientos). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE} SET "
        "month_period = %s, currency = %s, contract_number = %s, pedido_exiros = %s, "
        "start_date = %s, end_date = %s, plant = %s, coordinator = %s, contract_object = %s, "
        "history = %s, extra_info = %s "
        "WHERE id_control = %s"
    )
    val = (
        data.get("month_period"),
        data.get("currency", "MXN"),
        data.get("contract_number"),
        data.get("pedido_exiros"),
        data.get("start_date"),
        data.get("end_date"),
        data.get("plant"),
        data.get("coordinator"),
        data.get("contract_object"),
        json.dumps(data.get("history", []), ensure_ascii=False),
        json.dumps(data.get("extra_info", {}), ensure_ascii=False),
        id_control,
    )
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def update_balance_control_custom_fields(id_control: int, custom_fields: list, history: list, data_token):
    """Reemplaza la lista completa de columnas dinamicas. type_sql=3."""
    sql = f"UPDATE {_TABLE} SET custom_fields = %s, history = %s WHERE id_control = %s"
    val = (
        json.dumps(custom_fields, ensure_ascii=False),
        json.dumps(history, ensure_ascii=False),
        id_control,
    )
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def set_active_balance_control(id_control: int, is_active: int, history: list, data_token):
    """Cancelacion suave / reactivacion. type_sql=3."""
    sql = f"UPDATE {_TABLE} SET is_active = %s, history = %s WHERE id_control = %s"
    val = (is_active, json.dumps(history, ensure_ascii=False), id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_balance_control(id_control: int, data_token):
    """Borrado fisico. Solo para reversa del POST (movimientos en cascada). type_sql=3."""
    sql = f"DELETE FROM {_TABLE} WHERE id_control = %s"
    flag, e, out = execute_sql(sql, (id_control,), 3, data_token)
    return flag, e, out


# --- Movimientos de saldo (inmutables: solo INSERT / SELECT) --------------------
def insert_balance_control_movement(data: dict, data_token):
    """type_sql=4 -> lastrowid."""
    sql = (
        f"INSERT INTO {_TABLE_MOV} "
        "(id_control, type, movement_date, amount, previous_balance, resulting_balance, "
        "user_id, user_name, reason, document, timestamp, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("id_control"),
        data.get("type", 0),
        data.get("movement_date"),
        data.get("amount", 0),
        data.get("previous_balance", 0),
        data.get("resulting_balance", 0),
        data.get("user_id"),
        data.get("user_name"),
        data.get("reason"),
        data.get("document"),
        data.get("timestamp"),
        json.dumps(data.get("extra_info", {}), ensure_ascii=False),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def get_balance_control_movements(id_control: int, data_token):
    """Movimientos del control, del mas reciente al mas antiguo. type_sql=2."""
    sql = f"{_SELECT_MOV} WHERE id_control = %s ORDER BY id_movement DESC"
    flag, e, out = execute_sql(sql, (id_control,), 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


# --- Remisiones del contrato (lado control) -------------------------------------
def get_remissions_summary_by_contract(contract_id: int, data_token):
    """Resumen ligero de las remisiones del contrato: (id, folio, date, status). type_sql=2."""
    sql = f"SELECT id, folio, date, status FROM {_TABLE_AR} WHERE contract_id = %s ORDER BY id"
    flag, e, out = execute_sql(sql, (contract_id,), 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def get_remissions_by_ids(ids: list, data_token):
    """(id, contract_id, history) de las remisiones pedidas. type_sql=2."""
    if not ids:
        return True, None, []
    placeholders = ", ".join(["%s"] * len(ids))
    sql = f"SELECT id, contract_id, history FROM {_TABLE_AR} WHERE id IN ({placeholders})"
    flag, e, out = execute_sql(sql, tuple(ids), 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def adopt_remission_to_contract(id_report: int, contract_id: int, history: list, data_token):
    """Asigna contrato a una remision huerfana (solo si sigue sin contrato). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE_AR} SET contract_id = %s, history = %s "
        "WHERE id = %s AND contract_id IS NULL"
    )
    val = (contract_id, json.dumps(history, ensure_ascii=False), id_report)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def remove_custom_field_keys_from_remissions(contract_id: int, keys: list, data_token):
    """Sweep: quita extra_info.custom_fields.<key> de todas las remisiones del
    contrato. Las llaves ya vienen validadas (^[a-z][a-z0-9_]*$), asi que el
    path JSON no necesita comillas. type_sql=3 -> filas cambiadas."""
    if not keys:
        return True, None, 0
    paths = [f"$.custom_fields.{key}" for key in keys]
    remove_args = ", ".join(["%s"] * len(paths))
    sql = (
        f"UPDATE {_TABLE_AR} SET extra_info = JSON_REMOVE(extra_info, {remove_args}) "
        "WHERE contract_id = %s AND extra_info IS NOT NULL "
        f"AND JSON_CONTAINS_PATH(extra_info, 'one', {remove_args})"
    )
    val = tuple(paths) + (contract_id,) + tuple(paths)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out
