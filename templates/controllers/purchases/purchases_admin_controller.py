# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/nov/2024  at 14:50 $"

import json

from templates.database.connection import execute_sql


def get_purchases_admin_db(limit=(0, 100)):
    sql = (
        "SELECT id, metadata, creation, timestamps "
        "FROM sql_telintec_mod_admin.purchases "
        "ORDER BY creation "
        "LIMIT %s, %s "
    )
    val = (limit[0], limit[1])
    flag, error, my_result = execute_sql(sql, val, 2)
    return flag, error, my_result


def insert_new_purchase_db(metadata: dict, creation: str):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.purchases "
        "(metadata, creation) "
        "VALUES (%s, %s) "
    )
    val = (json.dumps(metadata), creation)
    flag, error, lastrowid = execute_sql(sql, val, 4)
    return flag, error, lastrowid
