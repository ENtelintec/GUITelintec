# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:33 $"

from templates.Functions_AuxPlots import get_data_movements_type


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
