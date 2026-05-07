# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/ene./2024  at 15:31 $"

import json
from datetime import datetime
from tkinter import Misc, filedialog

import ttkbootstrap as ttk

from static.constants import (
    conversion_quizzes_path,
    format_timestamps,
)
from static.constants import filepath_recommendations
from templates.controllers.notifications.Notifications_controller import (
    insert_notification,
)




def calculate_results_quizzes(dict_quizz: dict, tipo_q: int):
    dict_results = {"c_final": 0, "c_dom": 0, "c_cat": 0, "detail": {}}
    dict_conversions = json.load(open(conversion_quizzes_path, encoding="utf-8"))
    match tipo_q:
        case 1:
            dict_values = dict_conversions["norm035"]["v1"]["conversion"]
            c_final = 0
            c_dom = 0
            c_cat = 0
            for question in dict_quizz.values():
                if question["items"] != "":
                    upper_limit = question["items"][1]
                    lower_limit = question["items"][0]
                    answers = question["answer"]
                    for q in range(lower_limit, upper_limit + 1):
                        for group in dict_values.values():
                            items = group["items"]
                            values = group["values"]
                            if q in items:
                                res = values[answers[q - lower_limit][1]]
                                # pyrefly: ignore [unsupported-operation]
                                dict_results["detail"][str(q)] = res
                                c_final += res
                                break
            dict_results["c_final"] = c_final
            dict_cat_doms = dict_conversions["norm035"]["v1"]["categorias"]
            dict_results["c_dom"] = {}
            dict_results["c_cat"] = {}

            for cat_dic in dict_cat_doms.values():
                cat_name = cat_dic["categoria"]
                dict_results["c_cat"][cat_name] = 0
                for dom_name, dom_dic in cat_dic["dominio"].items():
                    dict_results["c_dom"][dom_name] = 0
                    for dim_dic in dom_dic["dimensiones"]:
                        dim_name = dim_dic["dimension"]
                        items = dim_dic["item"]
                        # pyrefly: ignore [missing-attribute]
                        for q, val in dict_results["detail"].items():
                            if int(q) in items:
                                dict_results["c_dom"][dom_name] += val
                                dict_results["c_cat"][cat_name] += val
        case 2:
            dict_values = dict_conversions["norm035"]["v2"]["conversion"]
            c_final = 0
            for question in dict_quizz.values():
                if question["items"] != "":
                    upper_limit = question["items"][1]
                    lower_limit = question["items"][0]
                    answers = question["answer"]
                    for q in range(lower_limit, upper_limit + 1):
                        for group in dict_values.values():
                            items = group["items"]
                            values = group["values"]
                            if q in items:
                                res = values[answers[q - lower_limit][1]]
                                # pyrefly: ignore [unsupported-operation]
                                dict_results["detail"][str(q)] = res
                                c_final += res
                                break
            dict_results["c_final"] = c_final
            dict_cat_doms = dict_conversions["norm035"]["v2"]["categorias"]
            dict_results["c_dom"] = {}
            dict_results["c_cat"] = {}
            dict_results["c_dim"] = {}
            for cat_dic in dict_cat_doms.values():
                cat_name = cat_dic["categoria"]
                dict_results["c_cat"][cat_name] = 0
                for dom_name, dom_dic in cat_dic["dominio"].items():
                    dict_results["c_dom"][dom_name] = 0
                    for dim_dic in dom_dic["dimensiones"]:
                        dim_name = dim_dic["dimension"]
                        items = dim_dic["item"]
                        dict_results["c_dim"][dim_name] = 0
                        # pyrefly: ignore [missing-attribute]
                        for q, val in dict_results["detail"].items():
                            if int(q) in items:
                                # print("calculate: ", q, items)
                                dict_results["c_dom"][dom_name] += val
                                dict_results["c_cat"][cat_name] += val
                                dict_results["c_dim"][dim_name] += val
        case _:
            pass
    return dict_results


def recommendations_results_quizzes(dict_results: dict, tipo_q: int):
    # Asumiendo que tienes la ruta correcta en filepath_recommendations
    dict_conversions_recomen = json.load(
        open(filepath_recommendations, encoding="utf-8")
    )
    dict_recommendations = {
        "c_final_r": "",
        "c_dom_r": "",
        "c_cat_r": "",
    }

    # Asumiendo que dict_results contiene las claves 'c_final', 'c_dom', 'c_cat'
    # y que pueden tener valores como 'MUY ALTO', 'ALTO', 'MEDIO', 'BAJO', 'NULO'.

    # Acceder a las recomendaciones basadas en el resultado final, dominio, y categoría
    final_score = dict_results.get(
        "c_final", "NULO"
    )  # Usar NULO como valor por defecto si no se encuentra
    dom_score = dict_results.get("c_dom", "default_dom")  # Usar un valor por defecto
    cat_score = dict_results.get("c_cat", "default_cat")  # Usar un valor por defecto

    # Acceder a las recomendaciones finales
    dict_recommendations["c_final_r"] = dict_conversions_recomen["c_final_r"].get(
        final_score, ["No hay recomendaciones específicas."]
    )

    # Aquí necesitas modificar el código según cómo desees manejar las recomendaciones de dominio y categoría
    # dado que en tu JSON 'c_dom_r' es solo una cadena, puedes necesitar un enfoque diferente o más información
    # Si 'c_dom_r' debería ser una estructura similar a 'c_final_r', ajusta tu JSON y tu código en consecuencia

    # Acceder a las recomendaciones de categoría
    if cat_score in dict_conversions_recomen["c_cat_r"]:
        dict_recommendations["c_cat_r"] = dict_conversions_recomen["c_cat_r"][cat_score]
    else:
        dict_recommendations["c_cat_r"] = [
            "No hay recomendaciones específicas para esta categoría."
        ]

    return dict_recommendations


def Reverse(lst):
    new_lst = lst[::-1]
    return new_lst


def hex_to_item_tableview(hex_num: str, digits: int):
    hex_num = hex_num.replace("0x", "")
    hex_num = int(hex_num, 16)
    hex_num = hex(hex_num)
    hex_num = hex_num.replace("0x", "")
    hex_num = hex_num.zfill(digits)
    return hex_num


def list_hex_numbers(n: int):
    hex_numbers = []
    for i in range(1, n + 1):
        hex_numbers.append(hex(i))
    return hex_numbers


def select_path():
    """
    Función para seleccionar una carpeta de archivos
    :return:
    """
    path = filedialog.askdirectory()
    print(path)
    return path


def create_notification_permission(
    msg: str, data_token, permissions: list, title: str, sender_id: int, recierver_id=0
):
    """
    Función para crear una notificación de permiso
    :param recierver_id:
    :param sender_id:
    :param title:
    :param msg:
    :param permissions:
    :return:
    """
    permissions = [item.lower() for item in permissions]
    date = datetime.now()
    timestamp = date.strftime(format_timestamps)
    body = {
        "id": 0,
        "status": 0,
        "title": title,
        "msg": msg,
        "timestamp": timestamp,
        "sender_id": sender_id,
        "receiver_id": recierver_id,
        "app": permissions,
    }
    flag, error, result = insert_notification(body, data_token)
    return flag


def validate_digits_numbers(new_value) -> bool:
    """
    Validates that the new value is a number.
    This function is called when the user types in a new value in the
    spinbox.
    It checks if the new value is a number and returns True or
    False accordingly.
    :param new_value: New value to be validated
    :return: True if the new value is a number, False otherwise
    """
    return new_value.isdigit()


def create_spinboxes_time(
    master: Misc,
    father,
    row: int,
    column: int,
    pad_x: int = 5,
    pad_y: int = 5,
    style: str = "primary",
    title: str = "",
    mins_defaul=0,
    hours_default=8,
) -> tuple:
    """Creates a clock with two spinboxes for minutes and hours
    :param title:
    :param father:
    :param master: <Misc> father instance where the object is created
    :param row: <int> row to be placed
    :param column: <int> column to be placed
    :param pad_x: <int> pad in x for the group, not for individual object
    :param pad_y: <int> pad in y for the group, not for individual object
    :param style: <str> bootstrap style selected
    :param mins_defaul: <int> default value for minutes
    :param hours_default: <int> deafult value for hours
    :return: Frame tkinter frame containing the spinboxes
    """
    clock = ttk.Frame(master)
    clock.grid(row=row, column=column, padx=pad_x, pady=pad_y, sticky="w")
    # minutes spinboxes
    # noinspection PyArgumentList
    minutes_spinbox = ttk.Spinbox(
        clock, from_=0, to=59, bootstyle=style, width=2, justify="center"
    )
    minutes_spinbox.grid(row=0, column=1, padx=1, pady=1, sticky="w")
    # hours spinbox
    # noinspection PyArgumentList
    hours_spinbox = ttk.Spinbox(
        clock, from_=0, to=23, bootstyle=style, width=2, justify="center"
    )
    hours_spinbox.grid(row=0, column=0, padx=1, pady=1, sticky="w")
    # add valitation to spinbox
    vcmd_mins = (master.register(validate_digits_numbers), "%P")
    minutes_spinbox.configure(validate="key", validatecommand=vcmd_mins)
    vcmd_hours = (master.register(validate_digits_numbers), "%P")
    hours_spinbox.configure(validate="key", validatecommand=vcmd_hours)
    # set default values
    minutes_spinbox.set(mins_defaul)
    hours_spinbox.set(hours_default)
    # father.clocks.append({title: [minutes_spinbox, hours_spinbox]})
    return clock, {title: [minutes_spinbox, hours_spinbox]}
