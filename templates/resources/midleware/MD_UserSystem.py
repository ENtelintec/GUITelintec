# -*- coding: utf-8 -*-
import json

import jwt
import pytz

from static.constants import format_date, format_timestamps, timezone_software, secrets, filepath_permission, \
    log_file_users
from datetime import date, datetime

from templates.Functions_Utils import create_notification_permission
from templates.controllers.employees.us_controller import (
    update_biocredentials_DB,
    create_user_system_with_token,
)
from templates.controllers.employees.us_controller import fetch_employess_user_data

__author__ = "Edisson Naula"
__date__ = "$ 09/12/2025 at 11:04 $"

from templates.misc.Functions_Files import write_log_file


def read_permissions_file(path: str = filepath_permission):
    """
    read permission json file
    :return:
    """
    with open(path, "r") as f:
        data = json.load(f)
    return data


def fetch_permissions_from_api():
    try:
        permissions = read_permissions_file()
    except Exception as e:
        return {"data": [], "error": str(e), "msg": "Error al obtener los permisos"}, 400
    return {"data": permissions, "error": "", "msg": "Permisos obtenidos correctamente"}, 200


def fectchUsersDBApi(data, data_token):
    flag, error, result = fetch_employess_user_data(data["status"])
    if not flag:
        return {data: [], "error": error, "msg": "Error al obtener los usuarios"}, 400
    if not isinstance(result, list):
        return {"error": "Error al obtener los usuarios"}, 400
    out = []
    for item in result:
        out.append(
            {
                "employee_id": item[0],
                "name": str(item[1]) + " " + str(item[2]),
                "birthday": item[3].strftime(format_date)
                if isinstance(item[3], date)
                else item[3],
                "contract": item[4],
                "status": item[5],
                "department_id": item[6],
                "department_name": item[7],
                "user": item[8],
                "biocredentials": item[9],
            }
        )
    return {"data": out, "error": "", "msg": "Usuarios obtenidos correctamente"}, 200


def update_biocredentials_from_api(data, data_token):
    flag, error, result = update_biocredentials_DB(
        data["biocredentials"], data["emp_id"], data["user"]
    )
    if not flag:
        return {
            "data": [result],
            "error": error,
            "msg": "Error al actualizar los datos",
        }, 400
    return {
        "data": [result],
        "error": "",
        "msg": "Datos actualizados correctamente",
    }, 200


def create_employee_user_from_api(data, data_token):
    dic_perm = {i: item for i, item in enumerate(data["permissions"])}
    data_user = {
        "permissions": dic_perm,
        "emp_id": data["emp_id"],
        "name": data["name"],
        "contrato": data["contract"],
        "user": data["user"],
        "dep_id": data["dep_id"],
    }
    token = jwt.encode(data_user, secrets.get("TOKEN_MASTER_KEY"), algorithm="HS256")
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    expires = 31536000
    flag, error, id_user = create_user_system_with_token(
        data["user"],
        data["hashpass"],
        dic_perm,
        token,
        expires,
        timestamp,
        data["emp_id"],
    )

    if not flag:
        return {
            "data": [id_user],
            "error": error,
            "msg": "Error al crear el usuario",
        }, 400
    msg = f"Usuario creado con ID-{id_user} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg,
        ["administracion", "operaciones"],
        "Encargado Creado",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_users, msg)
    return {
        "data": [id_user],
        "error": "",
        "msg": "Usuario creado correctamente",
    }, 201
