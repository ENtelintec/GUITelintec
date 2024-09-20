# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:33 $"

import json

import numpy as np

from templates.Functions_AuxPlots import get_data_movements_type, get_data_sm_per_range
from templates.controllers.fichajes.fichajes_controller import get_fichaje_DB
from templates.misc.Functions_Files import get_cumulative_data_fichajes_dict


def get_data_chart_movements(data):
    type_m = data["type_m"]
    types = []
    if type_m == "all":
        types = ["Entrada", "Salida"]
    elif type_m == "Entrada":
        types = ["Entrada"]
    elif type_m == "Salida":
        types = ["Salida"]
    else:
        return ["Error type invalid"], 400
    data_out_full = {}
    for t in types:
        data_chart = get_data_movements_type(data["type_m"], data["n_products"])
        data_dict = data_chart.get("data")
        values = [v for k, v in data_dict.items()]
        x_tags = [k for k, v in data_dict.items()]
        data_chart["data"] = {"values": values, "x_tags": x_tags}
        data_out_full[t] = data_chart
    return data_out_full, 200


def validate_range(range_g: str):
    ranges = ["day", "month", "year"]
    if range_g in ranges:
        return True
    else:
        return False


def validate_type_chart(type_chart: str):
    types = ["normal"]
    if type_chart in types:
        return True
    else:
        return False


def get_data_chart_sm(data):
    if not validate_range(data["range"]):
        return {"message": "Error range invalid"}, 400
    if not validate_type_chart(data["type_chart"]):
        return {"message": "Error type chart invalid or not supported yet"}, 400
    data_chart = get_data_sm_per_range(data["range"], data["type_chart"])
    data_out = []
    val_y = np.array(data_chart["val_y"])
    for index, item in enumerate(data_chart["legend"]):
        data_out.append(
            {
                "values": val_y[:, index].tolist(),
                "x_tags": data_chart["val_x"],
                "legend": item,
                "lines_style": data_chart["line_style"][index],
            }
        )
    data_chart["data"] = data_out
    del data_chart["val_x"]
    del data_chart["val_y"]
    del data_chart["legend"]
    del data_chart["line_style"]
    return data_chart, 200


def get_data_chart_fichaje_emp(data):
    flag, error, result = get_fichaje_DB(data["emp_id"])
    if not flag:
        return {"message": str(error)}, 400
    if len(result) <= 0:
        return {"message": "No data found"}, 400
    (
        ficha_id,
        emp_id,
        contract,
        absences_dict,
        lates_dict,
        extras_dict,
        primes_dict,
        normal_dict,
        pasive_dict,
    ) = result
    faltas, faltas_value = get_cumulative_data_fichajes_dict(
        json.loads(absences_dict), date=data["date"]
    )
    atrasos, atrasos_value = get_cumulative_data_fichajes_dict(
        json.loads(lates_dict), date=data["date"]
    )
    extras, extras_value = get_cumulative_data_fichajes_dict(
        json.loads(extras_dict), date=data["date"]
    )
    primas, primas_value = get_cumulative_data_fichajes_dict(
        json.loads(primes_dict), date=data["date"]
    )
    normal, normal_value = get_cumulative_data_fichajes_dict(
        json.loads(normal_dict), date=data["date"]
    )
    pasiva, pasiva_value = get_cumulative_data_fichajes_dict(
        json.loads(pasive_dict), date=data["date"]
    )
    data_out = {
        "lates_event": {
            "value": atrasos,
            "tag": "Atrasos",
            "legend": "Evento",
        },
        "lates_value": {
            "value": atrasos_value,
            "tag": "Atrasos",
            "legend": "Hora",
        },
        "extras_event": {
            "value": extras,
            "tag": "Extras",
            "legend": "Horas",
        },
        "extras_value": {
            "value": extras_value,
            "tag": "Extras",
            "legend": "Hora",
        },
        "absences": {
            "value": faltas_value,
            "tag": "Faltas",
            "legend": "Evento",
        },
        "primes": {
            "value": primas,
            "tag": "Primas",
            "legend": "Evento",
        },
        "normal": {
            "value": normal,
            "tag": "Normal",
            "legend": "Evento",
        },
        "pasive": {
            "value": pasiva,
            "tag": "Pasive",
            "legend": "Evento",
        },
    }
    return data_out, 200
