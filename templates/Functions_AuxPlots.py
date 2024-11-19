# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 09/may./2024  at 16:49 $"

from static.constants import status_dic
from templates.controllers.material_request.sm_controller import get_all_sm_plots
from templates.controllers.product.p_and_s_controller import get_movements_type

line_style = ["-", "--", "-.", ":", "-*"]


def generate_normal_data_from_dict(data_dict: dict, type_range: str):
    data_dict_p = {}
    title = ""
    ylabel = ""
    legend = []
    match type_range:
        case "day":
            for year in data_dict.keys():
                keys_final = str(year)
                for month in data_dict[year].keys():
                    keys_final += f"-{month}"
                    values = [0, 0, 0, 0, 0]
                    for day in data_dict[year][month].keys():
                        keys_final += f"-{day}"
                        for item in data_dict[year][month][day]:
                            id_sm, id_emp, date_init, date_limit, status = item
                            values[status] += 1
                        data_dict_p[keys_final] = values
            title = "SMs por día"
            ylabel = "# de SMs"
            legend = tuple(status_dic.values())
        case "month":
            for year in data_dict.keys():
                keys_final = str(year)
                for month in data_dict[year].keys():
                    keys_final += f"-{month}"
                    values = [0, 0, 0, 0, 0]
                    for day in data_dict[year][month].keys():
                        for item in data_dict[year][month][day]:
                            id_sm, id_emp, date_init, date_limit, status = item
                            values[status] += 1
                    data_dict_p[keys_final] = values
                    title = "SMs por mes"
                    ylabel = "# de SMs"
                    legend = tuple(status_dic.values())
        case _:
            for year in data_dict.keys():
                keys_final = str(year)
                values = [0, 0, 0, 0, 0]
                for month in data_dict[year].keys():
                    for day in data_dict[year][month].keys():
                        for item in data_dict[year][month][day]:
                            id_sm, id_emp, date_init, date_limit, status = item
                            values[status] += 1
                data_dict_p[keys_final] = values
            title = "SMs por año"
            ylabel = "# de SMs"
            legend = tuple(status_dic.values())
    data_chart = {
        "data": data_dict_p,
        "title": title,
        "ylabel": ylabel,
        "legend": legend,
    }
    return data_chart


def generate_bar_data_from_dict(data_dict: dict, type_range: str, type_chart: str):
    data_dict_p = {}
    title = ""
    ylabel = ""
    legend = []
    match type_range:
        case "day":
            for year in data_dict.keys():
                for month in data_dict[year].keys():
                    values = [0, 0, 0, 0, 0]
                    for day in data_dict[year][month].keys():
                        keys_final = str(year)
                        keys_final += f"-{month}"
                        keys_final += f"-{day}"
                        for item in data_dict[year][month][day]:
                            id_sm, id_emp, date_init, date_limit, status = item
                            values[status] += 1
                        data_dict_p[keys_final] = values
            title = "SMs por día"
            ylabel = "# de SMs"
            legend = tuple(status_dic.values())
        case "month":
            for year in data_dict.keys():
                for month in data_dict[year].keys():
                    keys_final = str(year)
                    keys_final += f"-{month}"
                    values = [0, 0, 0, 0, 0]
                    for day in data_dict[year][month].keys():
                        for item in data_dict[year][month][day]:
                            id_sm, id_emp, date_init, date_limit, status = item
                            values[status] += 1
                    data_dict_p[keys_final] = values
                    title = "SMs por mes"
                    ylabel = "# de SMs"
                    legend = tuple(status_dic.values())
        case _:
            for year in data_dict.keys():
                keys_final = str(year)
                values = [0, 0, 0, 0, 0]
                for month in data_dict[year].keys():
                    for day in data_dict[year][month].keys():
                        for item in data_dict[year][month][day]:
                            id_sm, id_emp, date_init, date_limit, status = item
                            values[status] += 1
                data_dict_p[keys_final] = values
            title = "SMs por año"
            ylabel = "# de SMs"
            legend = tuple(status_dic.values())

    match type_chart:
        case "bar":
            data_chart = {
                "data": data_dict_p,
                "title": title,
                "ylabel": ylabel,
                "legend": legend,
            }
        case _:
            data_chart = {
                "val_x": list(data_dict_p.keys()),
                "val_y": list(data_dict_p.values()),
                "title": title,
                "ylabel": ylabel,
                "legend": legend,
                "line_style": line_style,
            }
    return data_chart


def get_data_sm_per_range(type_r: str, type_chart: str):
    flag, error, results = get_all_sm_plots(16, False)
    dict_results = {}
    for item in results:
        id_sm, id_emp, date_init, date_limit, status = item
        month = date_init.month
        day = date_init.day
        year = date_init.year
        if year not in dict_results:
            dict_results[year] = {
                month: {day: [[id_sm, id_emp, date_init, date_limit, status]]}
            }
            continue
        if month not in dict_results[year]:
            dict_results[year][month] = {
                day: [[id_sm, id_emp, date_init, date_limit, status]]
            }
            continue
        if day not in dict_results[year][month]:
            dict_results[year][month][day] = [
                [id_sm, id_emp, date_init, date_limit, status]
            ]
            continue
        else:
            dict_results[year][month][day].append(
                [id_sm, id_emp, date_init, date_limit, status]
            )
    return generate_bar_data_from_dict(dict_results, type_r, type_chart)


def get_data_movements_type(type_m: str, n_elements: int):
    flag, error, results = get_movements_type(type_m, n_elements)
    if not flag:
        return None
    data_dict_p = {}
    for item in results:
        id_prod, quantity, name, udm = item
        if str(id_prod) not in data_dict_p:
            data_dict_p[str(id_prod)] = quantity
    title = f"Movimientos de {type_m}"
    ylabel = "Cantidad"
    legend = None
    data_chart = {
        "data": data_dict_p,
        "title": title,
        "ylabel": ylabel,
        "legend": legend,
        "xlabel": "ID Productos",
    }
    return data_chart
