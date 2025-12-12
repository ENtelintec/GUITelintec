# -*- coding: utf-8 -*-
from static.constants import format_date
from datetime import date
from datetime import datetime
from static.constants import format_timestamps
from templates.controllers.employees.us_controller import update_biocredentials_DB
from templates.controllers.employees.us_controller import fetch_employess_user_data

__author__ = "Edisson Naula"
__date__ = "$ 09/12/2025 at 11:04 $"


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
                "usernames": item[8],
                "biocredentials": item[9],
            }
        )
    return {"data": out, "error": "", "msg": "Usuarios obtenidos correctamente"}, 200


def update_biocredentials_from_api(data, data_token):
    flag, error, result = update_biocredentials_DB(
        data["biocredentials"], data["emp_id"]
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
