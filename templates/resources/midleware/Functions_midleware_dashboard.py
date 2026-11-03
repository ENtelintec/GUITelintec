# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:33 $"

import numpy as np

from templates.Functions_AuxPlots import get_data_movements_type, get_data_sm_per_range


def get_data_chart_movements(data, data_token):
    type_m = data["type_m"]
    types = []
    if type_m == "all":
        types = ["Entrada", "Salida"]
    elif type_m == "Entrada":
        types = ["Entrada"]
    elif type_m == "Salida":
        types = ["Salida"]
    else:
        return {
            "data": None,
            "msg": "Tipo de movimiento inválido",
            "error": "type_m debe ser 'all', 'Entrada' o 'Salida'",
        }, 400
    data_out_full = {}
    for t in types:
        data_chart = get_data_movements_type(data["type_m"], data["n_products"], data_token)
        data_dict = data_chart.get("data")
        values = [v for k, v in data_dict.items()]
        x_tags = [k for k, v in data_dict.items()]
        data_chart["data"] = {"values": values, "x_tags": x_tags}
        data_out_full[t] = data_chart
    return {"data": data_out_full, "msg": None, "error": None}, 200


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


def get_data_chart_sm(data, data_token):
    if not validate_range(data["range"]):
        return {
            "data": None,
            "msg": "Rango inválido",
            "error": "range debe ser 'day', 'month' o 'year'",
        }, 400
    if not validate_type_chart(data["type_chart"]):
        return {
            "data": None,
            "msg": "Tipo de gráfica no soportado",
            "error": f"type_chart '{data['type_chart']}' no está soportado aún",
        }, 400
    data_chart = get_data_sm_per_range(data["range"], data["type_chart"], data_token)
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
    return {"data": data_chart, "msg": None, "error": None}, 200
