# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 12/jul./2024  at 15:16 $'


def transform_bitacora_data_to_dict(data, columns):
    result = []
    for item in data:
        row = {}
        for i, column in enumerate(columns):
            row[column] = item[i]
        result.append(row)
    return result
