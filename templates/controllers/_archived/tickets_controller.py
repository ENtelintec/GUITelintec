# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:34 $'

from templates.database.connection import execute_sql


def get_tickets(limit=(0, 100)):
    sql = ("SELECT ticket_id, content_ticket, is_retrieved, is_answered, timestamp_create "
           "FROM sql_telintec.tickets "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def insert_ticket_db(id_t: int, content: str, is_retrieved: int, is_answered: int, timestamp: str):
    sql = ("INSERT INTO sql_telintec.tickets "
           "(ticket_id, "
           "content_ticket, "
           "is_retrieved, "
           "is_answered, "
           "timestamp_create) "
           "VALUES (%s, %s, %s, %s, %s)")
    val = (id_t, content, is_retrieved, is_answered, timestamp)
    flag, e, out = execute_sql(sql, val, 3)
    print(out, "record inserted in tickets.")
    return flag, None, out


def update_ticket_db(id_t: int, content: str, is_retrieved: int, is_answered: int, timestamp: str):
    sql = ("UPDATE sql_telintec.tickets "
           "SET "
           "content_ticket = %s, "
           "is_retrieved = %s, "
           "is_answered = %s, "
           "timestamp_create = %s "
           "WHERE ticket_id = %s")
    val = (content, is_retrieved, is_answered, timestamp, id_t)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_ticket_db(id_t: int):
    sql = "DELETE FROM sql_telintec.tickets WHERE ticket_id = %s"
    val = (id_t,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out

