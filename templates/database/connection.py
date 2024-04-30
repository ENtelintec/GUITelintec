import mysql.connector
from static.extensions import secrets


def connectionDB():
    try:
        connection = mysql.connector.connect(
            host=secrets["HOST_DB"],
            user=secrets["USER_SQL"],
            password=secrets["PASS_SQL"],
            database="sql_telintec",
        )
        if connection.is_connected():
            return connection

    except mysql.connector.Error as error:
        print(f"No se pudo conectar: {error}")