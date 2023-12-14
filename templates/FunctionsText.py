# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/nov./2023  at 16:55 $'

import unicodedata
import templates.FunctionsSQL as fsql


def clean_accents(txt: str):
    return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def compare_employee_name(name_1, name_2):
    name_or = name_1.copy()
    for i, name in enumerate(name_1):
        name_1[i] = clean_accents(name)
    name_2 = clean_accents(name_2)
    ids_1 = fsql.get_ids_employees(name_1)
    id_2 = fsql.get_id_employee(name_2)
    for i, id_1 in enumerate(ids_1):
        if id_1 is not None:
            if id_1[0] == id_2[0]:
                return name_or[i], True
    return None, False
