# -*- coding: utf-8 -*-

__author__ = "Edisson Naula"
__date__ = "$ 27/jul./2023  at 16:41 $"


import mysql.connector

from static.constants import secrets, HOST_DB_DEFAULT, USER_DB_DEFAULT, PASS_DB_DEFAULT


def execute_sql(
    sql: str, values: tuple | None = None, type_sql=1, data_token=None
) -> tuple[bool, str, list | int | tuple]:
    """
    Execute the sql with the values provides (OR not) AND returns a value
    depending on the type of query.
    In case of exception returns None
    :param type_sql: type of query to execute
    :param sql: sql query
    :param values: values for sql query
    :return: <flag , error, result> where result is:
        - tuple of items if type 1 |
        - item if type 2 |
        - rowcount if type 3 |
        - lastrowid if type 4 |
        - list of items if type 5 |
    """
    try:
        host_db = secrets[HOST_DB_DEFAULT]
        user_db = secrets[USER_DB_DEFAULT]
        pass_db = secrets[PASS_DB_DEFAULT]
        try:
            if data_token is not None:
                if data_token["is_tester"]:
                    host_db = secrets["HOST_DB_TEST"]
                    user_db = secrets["USER_DB_TEST"]
                    pass_db = secrets["PASS_DB_TEST"]
        except Exception:
            pass
        mydb = mysql.connector.connect(
            host=host_db,
            user=user_db,
            password=pass_db,
        )
        my_cursor = mydb.cursor(buffered=True)
    except Exception as e:
        print("error sql execute: ", e)
        return False, str(e), []
    out = []
    flag = True
    exception = "None"
    try:
        match type_sql:
            case 2:
                my_cursor.execute(sql, values)  # pyrefly: ignore
                out = my_cursor.fetchall()
            case 1:
                my_cursor.execute(sql, values)  # pyrefly: ignore
                out = my_cursor.fetchone()
            case 3:
                my_cursor.execute(sql, values)  # pyrefly: ignore
                mydb.commit()
                out = my_cursor.rowcount
            case 4:
                my_cursor.execute(sql, values)  # pyrefly: ignore
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
        exception = str(e)
    finally:
        # if not isinstance(out, list) or not isinstance(out, tuple):
        #     out = [out]
        out = out if out is not None else []
        my_cursor.close()
        mydb.close()
        return flag, exception, out  # pyrefly: ignore


def execute_sql_multiple(sql: str, values_list: list, type_sql=1, data_token=None):
    """
    Execute the sql with the values provides (OR not) AND returns a value
    depending on the type of query.
    In case of exception, returns None
    :param values_list: values for sql query
    :param type_sql: type of query to execute
    :param sql: sql query
    :return:
    """
    out = []
    flag = True
    error = None
    try:
        host_db = secrets[HOST_DB_DEFAULT]
        user_db = secrets[USER_DB_DEFAULT]
        pass_db = secrets[PASS_DB_DEFAULT]
        try:
            if data_token is not None:
                if data_token["is_tester"]:
                    host_db = secrets["HOST_DB_TEST"]
                    user_db = secrets["USER_DB_TEST"]
                    pass_db = secrets["PASS_DB_TEST"]
        except Exception:
            pass
        mydb = mysql.connector.connect(
            host=host_db,
            user=user_db,
            password=pass_db,
        )
        my_cursor = mydb.cursor(buffered=True)
    except Exception as e:
        print("Error at executing sql: ", str(e))
        return False, e, []
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
        except Exception as e:
            error = str(e)
            print(error)
            out.append([])
            flag = False
    out = out if out is not None else []
    my_cursor.close()
    mydb.close()
    return flag, error, out
