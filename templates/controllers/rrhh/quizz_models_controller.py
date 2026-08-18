# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026  at 12:00 $"

import json

from templates.database.connection import execute_sql

# Primera tabla del esquema por departamento sql_telintec_mod_rrhh
# (DDL: scripts_db_handle/quizz_models.sql; seed: seed_quizz_models.py).
_TABLE = "sql_telintec_mod_rrhh.quizz_models"

# Columnas devueltas por el SELECT de detalle (incluye los JSON pesados).
# El midleware mapea por indice usando esta misma tupla: el orden importa.
SELECT_COLUMNS = (
    "type_q",
    "name",
    "template",
    "rubric",
    "status",
    "protected",
    "created_by",
    "timestamp",
    "updated_at",
    "history",
)

# Columnas del listado (sin template/rubric completos: un template pesa
# decenas de KB y la lista es para pickers/tablas).
LIST_COLUMNS = (
    "type_q",
    "name",
    "status",
    "protected",
    "created_by",
    "timestamp",
    "updated_at",
    "has_rubric",
    "n_entries",
)

# Columnas que un UPDATE parcial puede tocar (whitelist del SET dinamico).
_UPDATABLE_COLS = ("name", "template", "rubric", "status", "history")


def get_quizz_models_db(status, data_token):
    """Listado ligero con filtro opcional por status (param-or-NULL).
    type_sql=2 -> fetchall."""
    sql = (
        "SELECT type_q, name, status, protected, created_by, timestamp, "
        "updated_at, rubric IS NOT NULL, JSON_LENGTH(template) "
        f"FROM {_TABLE} "
        "WHERE (status = %s OR %s IS NULL) "
        "ORDER BY type_q"
    )
    val = (status, status)
    flag, e, result = execute_sql(sql, val, 2, data_token)
    return flag, e, result


def get_quizz_model_db(type_q, data_token):
    """Fila completa (template y rubrica incluidos). type_sql=1 -> fetchone."""
    sql = f"SELECT {', '.join(SELECT_COLUMNS)} FROM {_TABLE} WHERE type_q = %s"
    val = (type_q,)
    flag, e, result = execute_sql(sql, val, 1, data_token)
    return flag, e, result


def get_quizz_model_rubric_db(type_q, data_token):
    """Solo la rubrica (para el motor de evaluacion). type_sql=1 -> fetchone."""
    sql = f"SELECT rubric FROM {_TABLE} WHERE type_q = %s"
    val = (type_q,)
    flag, e, result = execute_sql(sql, val, 1, data_token)
    return flag, e, result


def get_quizz_model_template_db(type_q, data_token):
    """Nombre + template + status (para captura/creacion de tasks).
    type_sql=1 -> fetchone."""
    sql = f"SELECT name, template, status FROM {_TABLE} WHERE type_q = %s"
    val = (type_q,)
    flag, e, result = execute_sql(sql, val, 1, data_token)
    return flag, e, result


def insert_quizz_model(data: dict, data_token):
    """Inserta un modelo nuevo (type_q lo asigna el AUTO_INCREMENT, arranca
    en 5 tras el seed). type_sql=4 -> lastrowid = type_q asignado."""
    sql = (
        f"INSERT INTO {_TABLE} "
        "(name, template, rubric, status, protected, created_by, timestamp, history) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        data.get("name"),
        json.dumps(data.get("template"), ensure_ascii=False),
        json.dumps(data["rubric"], ensure_ascii=False)
        if data.get("rubric") is not None
        else None,
        data.get("status", 0),
        data.get("protected", 0),
        data.get("created_by"),
        data.get("timestamp"),
        json.dumps(data.get("history", []), ensure_ascii=False),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_quizz_model_fields(type_q, updates: dict, data_token):
    """UPDATE parcial: solo escribe las columnas presentes en `updates`
    (whitelist _UPDATABLE_COLS). Los dict/list se serializan a JSON; un None
    explicito escribe NULL. type_sql=3 -> rowcount (filas *cambiadas*)."""
    cols, vals = [], []
    for col in _UPDATABLE_COLS:
        if col not in updates:
            continue
        value = updates[col]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        cols.append(f"{col} = %s")
        vals.append(value)
    if not cols:
        return True, "None", 0
    sql = f"UPDATE {_TABLE} SET {', '.join(cols)} WHERE type_q = %s"
    vals.append(type_q)
    flag, e, out = execute_sql(sql, tuple(vals), 3, data_token)
    return flag, e, out


def delete_quizz_model(type_q, data_token):
    """Borrado fisico. Las reglas (protected/status/tasks) las valida el
    midleware ANTES de llamar aqui. type_sql=3 -> rowcount."""
    sql = f"DELETE FROM {_TABLE} WHERE type_q = %s"
    val = (type_q,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def count_tasks_by_type_quizz(type_q, data_token):
    """(total, contestadas) de quizz_tasks que referencian el tipo via
    body.metadata.type_quizz. Contestada = data_raw con al menos una llave
    (create_task inicializa data_raw = {}). type_sql=1 -> fetchone."""
    sql = (
        "SELECT COUNT(*), "
        "COALESCE(SUM(CASE WHEN data_raw IS NOT NULL "
        "AND JSON_LENGTH(data_raw) > 0 THEN 1 ELSE 0 END), 0) "
        "FROM sql_telintec_mod_rrhh.quizz_tasks "
        "WHERE CAST(body->>'$.metadata.type_quizz' AS SIGNED) = %s "
        "AND body->>'$.metadata.type_quizz' IS NOT NULL"
    )
    val = (type_q,)
    flag, e, result = execute_sql(sql, val, 1, data_token)
    return flag, e, result
