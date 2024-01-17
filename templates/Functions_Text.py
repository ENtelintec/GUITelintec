# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/nov./2023  at 16:55 $'

import unicodedata
import templates.Functions_SQL as fsql


def clean_accents(txt: str):
    return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def compare_employee_name(names_1, id_2):
    for id_1, name in names_1:
        if id_1 is not None:
            if id_1 == id_2:
                return name, id_1, True
    return None, None, False


def parse_data(data: dict, mode: int):
    """
    Parses the data.
    :param data: <dict>
    :param mode: <int>
    :return: <dict>
    """
    code = 200
    try:
        match mode:
            case 1:
                out = {
                    "username": data['username'],
                    "password": data['password']
                }
            case 2:
                out = {
                    "username": data['username']
                }
            case 3:
                out = {
                    "token": data['token']
                }
            case 4:
                out = {
                    "username": data['username'],
                    "password": data['password'],
                    "permissions": data['permissions']
                }
            case _:
                print("Invalid mode")
                code = 204
                out = {
                    "error": "Invalid mode"
                }
    except Exception as e:
        print(e)
        code = 400
        out = {
            "error": "Invalid sintaxis" + str(e)
        }

    return code, out
