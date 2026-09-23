# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 17/sep./2026  at 12:00 $"

"""Catalogo de formatos ISO (SGI): sql_telintec_mod_admin.iso_formats. Escrituras
del CRUD de SGI (Docs/iso_formats_crud.md). Las lecturas por id/lista viven en
purchases/balance_control_controller.py (FORMAT_COLUMNS, get_iso_formats,
get_iso_format_by_id) y se reutilizan tal cual: mismo SELECT, mismo orden de
columnas (append-only).

La revision se sube EN LA MISMA FILA (UPDATE de revision + emission_date con la
anterior en history): los ids 1..8 estan atados por codigo a los PDFs (iso_form)
y una fila nueva por revision los dejaria imprimiendo la revision vieja.
"""

import json

from templates.controllers.purchases.balance_control_controller import (  # noqa: F401 (re-export)
    FORMAT_COLUMNS,
    get_iso_format_by_id,
    get_iso_formats,
)
from templates.database.connection import execute_sql

_TABLE = "sql_telintec_mod_admin.iso_formats"
_TABLE_BC = "sql_telintec_mod_admin.balance_controls"
_SELECT = f"SELECT {', '.join(FORMAT_COLUMNS)} FROM {_TABLE}"


def get_iso_formats_filtered(data_token, only_active: bool = True, department: str | None = None, kind: str | None = None):
    """Listado con filtros param-or-NULL. kind filtra por config.kind
    (NULL = formatos solo-PDF). type_sql=2."""
    sql = (
        f"{_SELECT} WHERE (%s IS NULL OR is_active = %s) "
        "AND (%s IS NULL OR department = %s) "
        "AND (%s IS NULL OR JSON_UNQUOTE(JSON_EXTRACT(config, '$.kind')) = %s) "
        "ORDER BY id"
    )
    active = 1 if only_active else None
    val = (active, active, department, department, kind, kind)
    flag, e, out = execute_sql(sql, val, 2, data_token)
    if not flag:
        return False, e, []
    if not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out


def get_iso_format_by_code_rev(code: str, revision: str, data_token):
    """Fila por (code, revision) — la UNIQUE de la tabla. type_sql=1."""
    sql = f"{_SELECT} WHERE code = %s AND revision = %s"
    flag, e, out = execute_sql(sql, (code, revision), 1, data_token)
    if not flag:
        return False, e, None
    if not isinstance(out, (list, tuple)) or len(out) == 0:
        return True, None, None
    return True, None, out


def insert_iso_format(data: dict, data_token):
    """type_sql=4 -> lastrowid."""
    sql = (
        f"INSERT INTO {_TABLE} "
        "(code, revision, name, department, emission_date, config, is_active, history, created_by, timestamp) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    config = data.get("config")
    val = (
        data.get("code"),
        data.get("revision", "R0"),
        data.get("name"),
        data.get("department"),
        data.get("emission_date"),
        json.dumps(config, ensure_ascii=False) if config is not None else None,
        data.get("is_active", 1),
        json.dumps(data.get("history", []), ensure_ascii=False),
        data.get("created_by"),
        data.get("timestamp"),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_iso_format(id_format: int, data: dict, data_token):
    """Escribe TODAS las columnas editables (el midleware ya mezclo el parcial
    con la fila actual). type_sql=3."""
    sql = (
        f"UPDATE {_TABLE} SET code = %s, revision = %s, name = %s, department = %s, "
        "emission_date = %s, config = %s, history = %s WHERE id = %s"
    )
    config = data.get("config")
    val = (
        data.get("code"),
        data.get("revision"),
        data.get("name"),
        data.get("department"),
        data.get("emission_date"),
        json.dumps(config, ensure_ascii=False) if config is not None else None,
        json.dumps(data.get("history", []), ensure_ascii=False),
        id_format,
    )
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def set_iso_format_active(id_format: int, is_active: int, history: list, data_token):
    """Baja suave / reactivacion. type_sql=3."""
    sql = f"UPDATE {_TABLE} SET is_active = %s, history = %s WHERE id = %s"
    val = (is_active, json.dumps(history, ensure_ascii=False), id_format)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_iso_format(id_format: int, data_token):
    """Borrado fisico (la FK de balance_controls es RESTRICT; el midleware
    verifica antes con count_balance_controls_by_format). type_sql=3."""
    sql = f"DELETE FROM {_TABLE} WHERE id = %s"
    flag, e, out = execute_sql(sql, (id_format,), 3, data_token)
    return flag, e, out


def count_balance_controls_by_format(id_format: int, data_token):
    """(total, activos) de controles de saldos que usan el formato. type_sql=1."""
    sql = f"SELECT COUNT(*), COALESCE(SUM(is_active = 1), 0) FROM {_TABLE_BC} WHERE format_id = %s"
    flag, e, out = execute_sql(sql, (id_format,), 1, data_token)
    if not flag or not isinstance(out, (list, tuple)) or len(out) == 0:
        return False, e, (0, 0)
    return True, None, (int(out[0] or 0), int(out[1] or 0))


def get_iso_format_headers(data_token=None):
    """(id, code, revision, emission_date) de TODOS los formatos (activos o no):
    lo consume PDFGenerator para imprimir 'Codigo: FO-XXX-NN Rn' e 'I. Vigencia'.
    type_sql=5 (sin params)."""
    sql = f"SELECT id, code, revision, emission_date FROM {_TABLE} ORDER BY id"
    flag, e, out = execute_sql(sql, None, 5, data_token)
    if not flag or not isinstance(out, (list, tuple)):
        return False, e, []
    return True, None, out
