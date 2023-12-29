# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/nov./2023  at 16:55 $'

import unicodedata
import templates.FunctionsSQL as fsql


def clean_accents(txt: str):
    return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def compare_employee_name(names_1, id_2):
    for id_1, name in names_1:
        if id_1 is not None:
            if id_1 == id_2:
                return name, id_1, True
    return None, None, False
