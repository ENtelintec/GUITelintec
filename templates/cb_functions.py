# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:37 $'

import json
import time
from typing import List, Union

import jwt
import mysql.connector

from static.extensions import secrets


def execute_sql(sql: str, values: tuple = None, type_sql=1):
    """
    Execute the sql with the values provides (or not) and returns a value
    depending on the type of query. In case of exception returns None
    :param type_sql: type of query to execute
    :param sql: sql query
    :param values: values for sql query
    :return:
    """
    mydb = mysql.connector.connect(
        host=secrets["HOST_DB"],
        user=secrets["USER_SQL"],
        password=secrets["PASS_SQL"],
        database="sql_telintec"
    )
    my_cursor = mydb.cursor()
    out = []
    e = None
    try:
        match type_sql:
            case 2:
                my_cursor.execute(sql, values)
                out = my_cursor.fetchall()
            case 1:
                my_cursor.execute(sql, values)
                out = my_cursor.fetchone()
            case 3:
                my_cursor.execute(sql, values)
                mydb.commit()
                out = my_cursor.rowcount
            case 4:
                my_cursor.execute(sql, values)
                mydb.commit()
                out = my_cursor.lastrowid
            case 5:
                my_cursor.execute(sql)
                out = my_cursor.fetchall()
            case _:
                out = []
    except Exception as e:
        print(e)
        out = []
        return out, e
    finally:
        out = out if out is not None else []
        my_cursor.close()
        mydb.close()
        return out, e


def verify_user_DB(user: str, password: str) -> bool:
    """
    Verifies if the user and password are correct.
    :param password: <string>
    :param user: <string>
    :return: <boolean>
    """
    sql = "SELECT usernames FROM users_system " \
          "WHERE usernames = %s AND password = %s"
    val = (user, password)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    flag = True if len(result) > 0 else False
    return flag


def generate_token(user: str, user_key: str, password: str) -> List[Union[None, int]]:
    """
    Generates a token for the user.
    :param user_key: <string>
    :param password: <string>
    :param user: <string>
    :return: <string>
    """
    sql = "SELECT permissions FROM users_system WHERE usernames = %s AND password = %s"
    val = (user, password)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    if result is not None:
        permissions = json.loads(result[0])
        data = {"name": user_key,
                "pass": password,
                "permissions": permissions}
        return [jwt.encode(data, secrets.get("TOKEN_MASTER_KEY"), algorithm="HS256"), 201]
    else:
        return [None, 404]


def update_DB_token(user: str, token: str, expires_in: int) -> int:
    """
    Updates the token for the user.
    :param expires_in: int
    :param user: <string>
    :param token: <string>
    :return: None
    """
    sql = "SELECT usernames FROM users_system " \
          "WHERE usernames = %s"
    val = (user,)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    code = 200
    if result is not None:
        sql = "UPDATE users_system " \
              "SET token = %s, exp = %s , timestamp_token = %s " \
              "WHERE usernames = %s"
        timestamp_token = time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime())
        val = (token, expires_in, timestamp_token, user)
        # my_cursor.execute(sql, val)
        # mydb.commit()
        execute_sql(sql, val, 3)
    else:
        print("User not found")
        code = 204

    return code


def get_token_info(user: str) -> List[Union[str, int, str, int]]:
    """
    Gets the token information for the user.
    :param user: <string>
    :return: <list> [<token>, <expires_in>, <timestamp_token>, <code>
        <token>: <string>
        <expires_in>: <int>
        <timestamp_token>: <string>
        <code>: <int>
    """
    sql = "SELECT token, exp, timestamp_token FROM users_system " \
          "WHERE usernames = %s AND token IS NOT NULL"
    val = (user,)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    code = 200
    if len(result) > 0:
        token = result[0]
        expires_in = result[1]
        timestamp_token = result[2]
    else:
        print("User not found")
        token = None
        expires_in = None
        timestamp_token = None
        code = 204

    return [token, expires_in, timestamp_token, code]


def verify_token(token: str, user: str) -> bool:
    """
    Verifies if the token is valid.
    :param user: <string>
    :param token: <string>
    :return: <boolean>
    """
    sql = "SELECT token FROM users_system " \
          "WHERE usernames = %s"
    val = (user,)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchall()
    result, e = execute_sql(sql, val, 2)
    flag = False
    if result is not None:
        for i in result:
            if i[0] == token:
                flag = True
    return flag


def unpack_token(token: str) -> dict:
    """
    Unpacks the token.
    :param token: <string>
    :return: <dict>
    """
    return jwt.decode(token, secrets.get("TOKEN_MASTER_KEY"), algorithms="HS256")


def parse_data(data: dict, mode: int):
    """
    Parses the data.
    :param data: <dict>
    :param mode: <int>
    :return: <dict>
    """
    code = 200
    try:
        match mode:
            case 1:
                out = {
                    "username": data['username'],
                    "password": data['password']
                }
            case 2:
                out = {
                    "username": data['username']
                }
            case 3:
                out = {
                    "token": data['token']
                }
            case _:
                print("Invalid mode")
                code = 204
                out = {
                    "error": "Invalid mode"
                }
    except Exception as e:
        print(e)
        code = 404
        out = {
            "error": "Invalid sintaxis" + str(e)
        }

    return code, out


def delete_token_DB(user: str):
    """
    Deletes the token for the user.
    :param user: <string>
    :return: None
    """
    sql = "UPDATE users_system " \
          "SET token = NULL, exp = NULL, timestamp_token = NULL " \
          "WHERE usernames = %s"
    val = (user,)
    result, e = execute_sql(sql, val, 3)
    flag = True if e is None else False
    return flag, e


def verify_user_DB_token(user: str, token: str):
    """
    Verifies if the user and token are correct.
    :param user: <string>
    :param token: <string>
    :return: <boolean>
    """
    sql = "SELECT usernames FROM users_system " \
          "WHERE usernames = %s AND token = %s"
    val = (user, token)
    result, e = execute_sql(sql, val)
    flag = True if len(result) > 0 else False
    return flag


def get_permissions(token: str):
    """
    Gets the permissions for the user.
    :param token: <string>
    :return: <list> [<permissions>, <code>
        <permissions>: <list>
        <code>: <int>
    """
    sql = "SELECT usernames, permissions FROM users_system " \
          "WHERE token = %s"
    val = (token,)
    result, e = execute_sql(sql, val, 2)
    if len(result) > 0:
        username = result[0][0]
        permissions = json.loads(result[0][1])
    else:
        print("User not found")
        permissions = None
        username = None
    return permissions, username
