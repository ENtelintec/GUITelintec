# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/abr./2024  at 11:38 $'

import math
from datetime import datetime, timedelta

from templates.Functions_SQL import get_sm_products, get_sm_entries
from templates.controllers.index import DataHandler

"""---------------------------API SM-----------------------------------------"""


def get_products_sm(limit, page=0):
    flag, error, result = get_sm_products()
    if limit == -1:
        limit = len(result) + 1
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
    if week_now - week_modify > 1:
        flag = False
    return flag


def get_all_sm(limit, page=0):
    flag, error, result = get_sm_entries()
    if limit == -1:
        limit = len(result) + 1
    limit = limit if limit > 0 else 10
    page = page if page >= 0 else 0
    if len(result) <= 0:
        return [None, 204]
    pages = math.floor(len(result) / limit)
    if page > pages:
        print("page > pages")
        return [None, 204]
    items = []
    if pages == 0:
        limit_up = len(result)
        limit_down = 0
    else:
        limit_down = limit * page
        limit_up = limit * (page + 1)
        limit_up = limit_up if limit_up < len(result) else len(result)
    for i in range(limit_down, limit_up):
        items.append({
            'id': result[i][0],
            'sm_code': result[i][1],
            'folio': result[i][2],
            'contract': result[i][3],
            'facility': result[i][4],
            'location': result[i][5],
            'client_id': result[i][6],
            'emp_id': result[i][7],
            'order_quotation': result[i][8],
            'date': result[i][9],
            'limit_date': result[i][10],
            'items': result[i][11],
            'status': result[i][12],
            'history': result[i][13],
            'comment': result[i][14],
        })
    data_out = {
        'data': items,
        'page': page,
        'pages': pages + 1
    }
    return data_out, 200


def dispatch_products(
        avaliable: list[dict], to_request: list[dict], sm_id: int, new_products: list[dict]
) -> tuple[list[dict], list[dict], list[dict]]:
    _data = DataHandler()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # ------------------------------avaliable products------------------------------------------
    for i, product in enumerate(avaliable):
        _outs = _data.create_out_movement(
            product['id'],
            "salida",
            product['quantity'],
            date,
            sm_id
        )
        _data.update_stock(product['id'], product["stock"] - product['quantity'])
        print(f"producto {product['id']} en salida {product['quantity']}")
        print(f"producto {product['id']} actualizado stock {product['stock'] - product['quantity']}")
        product['comment'] += " ;(Despachado) "
        avaliable[i] = product
    # ------------------------------products to request------------------------------------------
    for i, product in enumerate(to_request):
        _ins = _data.create_in_movement(
            product['id'], "entrada", product['quantity'], date, sm_id)
        print(f"producto {product['id']} pedido {product['quantity']}")
        product['comment'] += " ;(Pedido) "
        to_request[i] = product
    # ------------------------------products to request for admin-----------------------------------
    for i, product in enumerate(new_products):
        _ins = _data.create_in_movement(
            product['id'], "entrada", product['quantity'], date, sm_id)
        print(f"producto {product['id']} nuevo {product['quantity']}")
        product['comment'] += " ;(Pedido) "
        new_products[i] = product
    return avaliable, to_request, new_products
