# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:36 $'

from templates.database.connection import execute_sql


def get_purchases(limit=(0, 100)):
    sql = ("SELECT purchase_id, product_id, quantity, date_purchase, supplier_id "
           "FROM sql_telintec.purchases "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out
