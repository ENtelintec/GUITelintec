# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 19:43 $'

from templates.database.connection import execute_sql


def get_chats(limit=(0, 100)):
    sql = ("SELECT "
           "chat_id, "
           "context, "
           "timestamp_start, "
           "timestamp_end, "
           "receiver_id, "
           "sender_id, "
           "platform, "
           "is_alive, "
           "is_review "
           "FROM chats "
           "ORDER BY chat_id DESC "
           "LIMIT %s, %s")
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = [] if my_result is None else my_result
    return out


def check_last_id(old: str = None) -> list:
    if old is None:
        sql = ("SELECT MAX(chat_id) "
               "FROM chats")
        flag, e, out = execute_sql(sql, type_sql=5)
    else:
        sql = ("SELECT chat_id "
               "FROM chats "
               "WHERE chat_id > %s")
        val = (old,)
        flag, e, out = execute_sql(sql, val, 2)
    return out


def get_isAlive(chat_id: int, sender_id):
    sql = ("SELECT is_alive "
           "FROM chats "
           "WHERE chat_id = %s AND sender_id = %s")
    val = (chat_id, sender_id)
    flag, error, result = execute_sql(sql, val, 1)
    return result


def update_isAlive(chat_id: int, sender_id, is_alive):
    sql = ("UPDATE chats "
           "SET is_alive = %s "
           "WHERE chat_id = %s AND sender_id = %s")
    val = (is_alive, chat_id, sender_id)
    flag, error, result = execute_sql(sql, val, 3)
    return result


def get_only_context(chat_id: str):
    sql = "SELECT context FROM chats WHERE chat_id = %s"
    val = (chat_id,)
    flag, error, result = execute_sql(sql, val, 1)
    return result


def set_finish_chat(chat_id: str):
    sql = "UPDATE chats SET is_alive = 0, is_review = 1 WHERE chat_id = %s"
    val = (chat_id,)
    flag, error, result = execute_sql(sql, val, 3)
    return result


def get_chats_w_limit(limit=(0, 100)):
    sql = "SELECT chat_id, platform, context FROM chats ORDER BY chat_id DESC LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = [] if my_result is None else my_result
    return out
