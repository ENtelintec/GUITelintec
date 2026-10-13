# -*- coding: utf-8 -*-

__author__ = "Edisson Naula"
__date__ = "$ 27/jul./2023  at 16:41 $"


import os
import re
import threading
from datetime import datetime

import mysql.connector
import pytz
from mysql.connector import pooling
from mysql.connector.errors import PoolError

from static.constants import (
    HOST_DB_DEFAULT,
    PASS_DB_DEFAULT,
    USER_DB_DEFAULT,
    format_date,
    log_file_db,
    secrets,
    timezone_software,
)

# ---------------------------------------------------------------------------
# Pool de conexiones (docs/db_connection_pool.md)
#
# Un pool por destino (BD normal / BD de test del token `is_tester`) y por
# proceso: con un WSGI de varios workers cada proceso crea el suyo de forma
# perezosa en la primera consulta (nunca al importar: un pool heredado por
# fork compartiría sockets entre procesos). Si el pool se agota se abre una
# conexión directa como antes del pool (modo degradado, se anota en el log
# de `db`), de modo que bajo carga el comportamiento nunca es peor que el
# histórico. `pool_reset_session=True` hace rollback y limpia la sesión al
# devolver la conexión, así una transacción implícita de un SELECT no deja
# un snapshot viejo al siguiente request.
# ---------------------------------------------------------------------------
POOL_SIZE = 4

_pools: dict[str, pooling.MySQLConnectionPool] = {}
_pools_lock = threading.Lock()
_pools_pid: int | None = None


def _credentials(data_token) -> tuple[str | None, str | None, str | None]:
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
    return host_db, user_db, pass_db


def _log_db(text: str):
    """Log mínimo propio (Functions_Files importa controllers -> ciclo)."""
    try:
        date = datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software)).strftime(format_date)
        with open(f"{log_file_db}_log_{date}.txt", "a") as f:
            f.write(f"-->{text}\n")
    except Exception:
        pass


def _get_pool(host_db, user_db, pass_db) -> pooling.MySQLConnectionPool | None:
    """Pool del destino (host+usuario) de este proceso; lo crea la primera
    vez. None si no se pudo crear (el caller abre conexión directa)."""
    global _pools_pid
    key = f"{user_db}@{host_db}"
    with _pools_lock:
        pid = os.getpid()
        if _pools_pid != pid:
            _pools.clear()
            _pools_pid = pid
        pool = _pools.get(key)
        if pool is None:
            name = re.sub(pooling.CNX_POOL_NAMEREGEX, "_", f"gui_{pid}_{key}")[: pooling.CNX_POOL_MAXNAMESIZE]
            try:
                pool = pooling.MySQLConnectionPool(
                    pool_name=name,
                    pool_size=POOL_SIZE,
                    pool_reset_session=True,
                    host=host_db,
                    user=user_db,
                    password=pass_db,
                )
            except Exception as e:
                _log_db(f"pool: no se pudo crear el pool {key}: {e}")
                return None
            _pools[key] = pool
        return pool


def _connect(data_token):
    """Conexión lista para usar. Del pool cuando hay; directa si el pool no
    existe o está agotado. `close()` sobre una conexión del pool la devuelve
    (no la cierra), sobre una directa la cierra: el caller no distingue."""
    host_db, user_db, pass_db = _credentials(data_token)
    pool = _get_pool(host_db, user_db, pass_db)
    if pool is not None:
        try:
            return pool.get_connection()
        except PoolError as e:
            _log_db(f"pool: agotado ({user_db}@{host_db}), conexión directa: {e}")
    return mysql.connector.connect(host=host_db, user=user_db, password=pass_db)


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
        mydb = _connect(data_token)
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
            print("Error at executing sql: ", str(e), sql)
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
        mydb = _connect(data_token)
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
