# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/abr./2024  at 11:38 $'

import math
from datetime import datetime, timedelta

from templates.Functions_SQL import get_sm_products, get_sm_entries

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


def check_date_difference(date_modify, delta):
    flag = True
    date_now = datetime.now()
    date_modify = datetime.strptime(date_modify, "%Y-%m-%d")
    date_modify = date_modify.date()
    # week of the month
    week_modify = date_modify.isocalendar()[1]
    date_now = date_now.date()
    week_now = date_now.isocalendar()[1]
    date_modify = date_modify + timedelta(days=delta)
    if week_now-week_modify > 1:
        flag = False
    return flag


def get_all_sm(limit, page=0):
    flag, error, result = get_sm_entries()
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
            'sm_code': result[i][1],
            'folio':  result[i][2],
            'contract': result[i][3],
            'facility': result[i][4],
            'location': result[i][5],
            'client_id': result[i][6],
            'emp_id': result[i][7],
            'date': result[i][8],
            'limit_date': result[i][9],
            'items': result[i][10],
            'status': result[i][11]
        })
    data_out = {
        'data': items,
        'page': page,
        'pages': pages + 1
    }
    return data_out, 200