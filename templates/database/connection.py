# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 27/jul./2023  at 16:41 $"


import mysql.connector

from static.constants import secrets, HOST_DB_DEFAULT, USER_DB_DEFAULT, PASS_DB_DEFAULT


def execute_sql(sql: str, values: tuple = None, type_sql=1):
    """
    Execute the sql with the values provides (OR not) AND returns a value
    depending on the type of query.
    In case of exception returns None
    :param type_sql: type of query to execute
    :param sql: sql query
    :param values: values for sql query
    :return: <flag , error, result> where result is:
        | list of items if type 1 |
        | item if type 2 |
        | rowcount if type 3 |
        | lastrowid if type 4 |
        | list of items if type 5 |
    """
    try:
        mydb = mysql.connector.connect(
            host=secrets[HOST_DB_DEFAULT],
            user=secrets[USER_DB_DEFAULT],
            password=secrets[PASS_DB_DEFAULT],
        )
        my_cursor = mydb.cursor(buffered=True)
    except Exception as e:
        print(e)
        return False, e, []
    out = []
    flag = True
    exception = None
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
        if "Duplicate entry" not in str(e):
            print("Error at executing sql: ", str(e), str(sql))
        out = []
        flag = False
        exception = e
    finally:
        out = out if out is not None else []
        my_cursor.close()
        mydb.close()
        return flag, exception, out


def execute_sql_multiple(sql: str, values_list: list = None, type_sql=1):
    """
    Execute the sql with the values provides (OR not) AND returns a value
    depending on the type of query.
    In case of exception, returns None
    :param values_list: values for sql query
    :param type_sql: type of query to execute
    :param sql: sql query
    :return:
    """
    try:
        mydb = mysql.connector.connect(
            host=secrets[HOST_DB_DEFAULT],
            user=secrets[USER_DB_DEFAULT],
            password=secrets[PASS_DB_DEFAULT],
            database="sql_telintec",
        )
        my_cursor = mydb.cursor(buffered=True)
    except Exception as e:
        print("Error at executing sql: ", str(e))
        return False, e, []
    out = []
    flag = True
    error = None
    # my_cursor = mydb.cursor(buffered=True)
    for i in range(len(values_list[0])):
        values = []
        for j in range(len(values_list)):
            values.append(values_list[j][i])
        values = tuple(values)
        try:
            match type_sql:
                case 2:
                    my_cursor.execute(sql, values)
                    out.append(my_cursor.fetchall())
                case 1:
                    my_cursor.execute(sql, values)
                    out.append(my_cursor.fetchone())
                case 3:
                    my_cursor.execute(sql, values)
                    mydb.commit()
                    out.append(my_cursor.rowcount)
                case 4:
                    my_cursor.execute(sql, values)
                    mydb.commit()
                    out.append(my_cursor.lastrowid)
                case 5:
                    my_cursor.execute(sql)
                    out.append(my_cursor.fetchall())
                case _:
                    out.append([])
        except Exception as error:
            print(error)
            out.append([])
            flag = False
    out = out if out is not None else []
    my_cursor.close()
    mydb.close()
    return flag, error, out
