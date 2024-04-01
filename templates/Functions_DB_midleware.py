# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/abr./2024  at 11:38 $'

import math

from templates.Functions_SQL import get_sm_products

"""---------------------------API SM-----------------------------------------"""


def get_products_sm(limit, page=0):
    flag, error, result = get_sm_products()
    if limit == -1:
        limit = len(result)+1
    limit = limit if limit > 0 else 10
    page = page if page >= 0 else 0
    if len(result) <= 0:
        return [None, 204]
    pages = math.floor(result.__len__() / limit)
    if page > pages:
        print("page > pages")
        return [None, 204]
    items = []
    if pages == 0:
        limit_up = result.__len__()
        limit_down = 0
    else:
        limit_down = limit * page
        limit_up = limit * (page + 1)
        limit_up = limit_up if limit_up < result.__len__() else result.__len__()
    for i in range(limit_down, limit_up):
        items.append({
            'id': result[i][0],
            'name': result[i][1],
            'udm': result[i][2],
            'stock': result[i][3]
        })
    data_out = {
        'data': items,
        'page': page,
        'pages': pages + 1
    }
    return data_out, 200
