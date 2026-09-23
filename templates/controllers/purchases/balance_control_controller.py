# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 11/sep./2026  at 12:00 $"

"""Control de saldos (Cobranza): cabecera (con o sin contrato), catalogo de
formatos ISO y movimientos de saldo. DDL en scripts_db_handle/control_saldos.sql
+ scripts_db_handle/control_saldos_sin_contrato.sql.

Membresia remision -> control: activity_reports.balance_control_id (UNICA llave,
Docs/control_saldos_sin_contrato.md). activity_reports.contract_id solo dice bajo
que contrato marco se ejecuto el trabajo: NINGUNA query de este modulo debe
relacionar remisiones con un control por contract_id.
"""

import json

from templates.database.connection import execute_sql

_TABLE = "sql_telintec_mod_admin.balance_controls"
_TABLE_MOV = "sql_telintec_mod_admin.balance_control_movements"
_TABLE_FMT = "sql_telintec_mod_admin.iso_formats"
_TABLE_AR = "sql_telintec_mod_admin.activity_reports"
_TABLE_CONTRACTS = "sql_telintec_mod_admin.contracts"
_TABLE_CUSTOMERS = "sql_telintec.customers_amc"

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
    # control sin contrato (2026-09-14): identidad propia. Append-only.
    "client_id",
    "title",
    "client_name",
)
_SELECT_CONTROL = (
    "SELECT bc.id_control, bc.contract_id, bc.format_id, bc.month_period, bc.currency, "
    "bc.contract_number, bc.pedido_exiros, bc.contracted_amount, bc.start_date, bc.end_date, "
    "bc.plant, bc.coordinator, bc.contract_object, bc.custom_fields, bc.is_active, "
    "bc.created_by, bc.timestamp, bc.history, bc.extra_info, "
    "f.code, f.revision, f.name, c.code, c.abbreviation, "
    "JSON_UNQUOTE(JSON_EXTRACT(c.metadata, '$.identifier')), "
    f"(SELECT COUNT(*) FROM {_TABLE_AR} ar WHERE ar.balance_control_id = bc.id_control), "
    "bc.client_id, bc.title, cu.name "
    f"FROM {_TABLE} bc "
    f"LEFT JOIN {_TABLE_FMT} f ON f.id = bc.format_id "
    f"LEFT JOIN {_TABLE_CONTRACTS} c ON c.id = bc.contract_id "
    f"LEFT JOIN {_TABLE_CUSTOMERS} cu ON cu.id_customer = bc.client_id "
)

# Columnas de las remisiones vistas desde el control (append-only, el midleware
# indexa por posicion): control_active = is_active del control al que apunta
# (NULL si no apunta a ninguno).
REMISSION_LINK_COLUMNS = (
    "id",
    "contract_id",
    "history",
    "client_id",
    "balance_control_id",
    "control_active",
)
_SELECT_REMISSION_LINK = (
    "SELECT ar.id, ar.contract_id, ar.history, ar.client_id, ar.balance_control_id, bcl.is_active "
    f"FROM {_TABLE_AR} ar "
    f"LEFT JOIN {_TABLE} bcl ON bcl.id_control = ar.balance_control_id "
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
        "(contract_id, format_id, client_id, title, month_period, currency, contract_number, pedido_exiros, "
        "contracted_amount, start_date, end_date, plant, coordinator, contract_object, "
        "custom_fields, is_active, created_by, timestamp, history, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("contract_id"),  # None = control sin contrato
        data.get("format_id"),
        data.get("client_id"),
        data.get("title"),
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
    client_id: int | None = None,
    has_contract: int | None = None,
):
    """Listado con filtros estilo param-or-NULL. has_contract: 1 = solo con
    contrato, 0 = solo sin contrato. type_sql=2."""
    sql = (
        f"{_SELECT_CONTROL} "
        "WHERE (%s IS NULL OR bc.contract_id = %s) "
        "AND (%s IS NULL OR bc.format_id = %s) "
        "AND (%s IS NULL OR bc.is_active = %s) "
        "AND (%s IS NULL OR bc.client_id = %s) "
        "AND (%s IS NULL OR (%s = 1 AND bc.contract_id IS NOT NULL) OR (%s = 0 AND bc.contract_id IS NULL)) "
        "ORDER BY bc.id_control DESC"
    )
    val = (
        contract_id, contract_id,
        format_id, format_id,
        is_active, is_active,
        client_id, client_id,
        has_contract, has_contract, has_contract,
    )
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
    client_id, format_id ni contracted_amount (el monto solo se mueve con
    movimientos). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE} SET "
        "title = %s, month_period = %s, currency = %s, contract_number = %s, pedido_exiros = %s, "
        "start_date = %s, end_date = %s, plant = %s, coordinator = %s, contract_object = %s, "
        "history = %s, extra_info = %s "
        "WHERE id_control = %s"
    )
    val = (
        data.get("title"),
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


def update_balance_control_history(id_control: int, history: list, data_token):
    """Solo history (p.ej. cambios de membresia de remisiones). type_sql=3."""
    sql = f"UPDATE {_TABLE} SET history = %s WHERE id_control = %s"
    val = (json.dumps(history, ensure_ascii=False), id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def get_customer_name(client_id: int, data_token):
    """Nombre del cliente (customers_amc) o None si no existe. type_sql=1."""
    sql = f"SELECT name FROM {_TABLE_CUSTOMERS} WHERE id_customer = %s"
    flag, e, out = execute_sql(sql, (client_id,), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out[0]


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


def update_balance_control_amount_optimistic(
    id_control: int, new_amount, expected_amount, history: list, data_token
):
    """Mueve contracted_amount con bloqueo optimista: solo escribe si el monto
    en BD sigue siendo `expected_amount` (el leido antes de calcular) y el control
    esta activo. type_sql=3 -> rowcount (0 = otro movimiento gano la carrera o el
    control se cancelo entre la lectura y la escritura -> 409 en el midleware)."""
    sql = (
        f"UPDATE {_TABLE} SET contracted_amount = %s, history = %s "
        "WHERE id_control = %s AND contracted_amount = %s AND is_active = 1"
    )
    val = (new_amount, json.dumps(history, ensure_ascii=False), id_control, expected_amount)
    flag, e, out = execute_sql(sql, val, 3, data_token)
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


# --- Remisiones del control (membresia por balance_control_id) -------------------
def get_remissions_summary_by_control(id_control: int, data_token):
    """Resumen ligero de las remisiones ligadas al control: (id, folio, date, status). type_sql=2."""
    sql = f"SELECT id, folio, date, status FROM {_TABLE_AR} WHERE balance_control_id = %s ORDER BY id"
    flag, e, out = execute_sql(sql, (id_control,), 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def get_remissions_by_ids(ids: list, data_token):
    """Filas REMISSION_LINK_COLUMNS de las remisiones pedidas. type_sql=2."""
    if not ids:
        return True, None, []
    placeholders = ", ".join(["%s"] * len(ids))
    sql = f"{_SELECT_REMISSION_LINK} WHERE ar.id IN ({placeholders})"
    flag, e, out = execute_sql(sql, tuple(ids), 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def get_free_remissions_by_contract(contract_id: int, data_token):
    """Remisiones del contrato que NO estan en un control activo (sin control o
    apuntando a uno cancelado): las que auto-adopta el POST de un control con
    contrato. Filas REMISSION_LINK_COLUMNS. type_sql=2."""
    sql = (
        f"{_SELECT_REMISSION_LINK} "
        "WHERE ar.contract_id = %s "
        "AND (ar.balance_control_id IS NULL OR bcl.id_control IS NULL OR bcl.is_active = 0) "
        "ORDER BY ar.id"
    )
    flag, e, out = execute_sql(sql, (contract_id,), 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def attach_remission_to_control(
    id_report: int, id_control: int, contract_id: int | None, history: list, data_token
):
    """Liga la remision al control. Con contract_id (control con contrato) tambien
    se lo asigna a la remision que no lo tenia (COALESCE conserva el existente
    cuando se pasa None). Guard en el WHERE: solo si la remision esta libre, ya
    era de este control o apunta a un control NO activo — dos altas concurrentes
    no pueden dejarla en dos controles. type_sql=3 -> 0 filas = alguien la tomo antes."""
    sql = (
        f"UPDATE {_TABLE_AR} SET balance_control_id = %s, "
        "contract_id = COALESCE(%s, contract_id), history = %s "
        "WHERE id = %s AND (balance_control_id IS NULL OR balance_control_id = %s "
        f"OR balance_control_id NOT IN (SELECT id_control FROM {_TABLE} WHERE is_active = 1))"
    )
    val = (id_control, contract_id, json.dumps(history, ensure_ascii=False), id_report, id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def detach_remission_from_control(id_report: int, id_control: int, history: list, data_token):
    """Saca la remision del control (balance_control_id = NULL). NO toca
    contract_id. type_sql=3 -> 0 filas = ya no estaba en este control."""
    sql = (
        f"UPDATE {_TABLE_AR} SET balance_control_id = NULL, history = %s "
        "WHERE id = %s AND balance_control_id = %s"
    )
    val = (json.dumps(history, ensure_ascii=False), id_report, id_control)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def remove_custom_field_keys_from_remissions(id_control: int, keys: list, data_token):
    """Sweep: quita extra_info.custom_fields.<key> de todas las remisiones ligadas
    al control. Las llaves ya vienen validadas (^[a-z][a-z0-9_]*$), asi que el
    path JSON no necesita comillas. type_sql=3 -> filas cambiadas."""
    if not keys:
        return True, None, 0
    paths = [f"$.custom_fields.{key}" for key in keys]
    remove_args = ", ".join(["%s"] * len(paths))
    sql = (
        f"UPDATE {_TABLE_AR} SET extra_info = JSON_REMOVE(extra_info, {remove_args}) "
        "WHERE balance_control_id = %s AND extra_info IS NOT NULL "
        f"AND JSON_CONTAINS_PATH(extra_info, 'one', {remove_args})"
    )
    val = tuple(paths) + (id_control,) + tuple(paths)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out
