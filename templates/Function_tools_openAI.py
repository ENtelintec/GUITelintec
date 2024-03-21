# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 20/mar./2024  at 15:24 $'

from templates.Functions_SQL import get_product_categories, get_products_almacen, get_high_stock_products, \
    get_low_stock_products, get_no_stock_products, get_costumers_amc, get_supplier_amc, get_orders_amc


def getProductCategories(**kwargs):
    for k, v in kwargs.items():
        match k:
            case _:
                pass
    flag, error, result, columns = get_product_categories()
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return []


def getProductsAlmacen(**kwargs):
    id_p = None
    name = None
    category = None
    for k, v in kwargs.items():
        match k:
            case "id":
                id_p = v
            case "name":
                name = v
            case "category":
                category = v
            case _:
                pass
    # fill with "" if an argument is None
    id_p = id_p if id_p is not None else "%"
    name = name if name is not None else "%"
    category = category if category is not None else "%"
    flag, error, result, columns = get_products_almacen(id_p, name, category)
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return [], columns


def getHighStockProducts(**kwargs):
    category = None
    quantity = None
    for k, v in kwargs.items():
        match k:
            case "category":
                category = v
            case "quantity":
                quantity = v
            case _:
                pass
    category = category if category is not None else "%"
    quantity = quantity if quantity is not None else 0
    flag, error, result, columns = get_high_stock_products(category=category, quantity=quantity)
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return []


def getLowStockProducts(**kwargs):
    category = None
    quantity = None
    for k, v in kwargs.items():
        match k:
            case "category":
                category = v
            case "quantity":
                quantity = v
            case _:
                pass
    category = category if category is not None else "%"
    quantity = quantity if quantity is not None else 0
    flag, error, result, columns = get_low_stock_products(category=category, quantity=quantity)
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return []


def getNoStockProducts(**kwargs):
    category = None
    for k, v in kwargs.items():
        match k:
            case "category":
                category = v
            case _:
                pass
    category = category if category is not None else "%"
    flag, error, result, columns = get_no_stock_products(category=category)
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return []


def getCostumer(**kwargs):
    name = None
    id_c = None
    for k, v in kwargs.items():
        match k:
            case "name":
                name = v
            case "id":
                id_c = v
            case _:
                pass
    name = name if name is not None else "%"
    id_c = id_c if id_c is not None else "%"
    flag, error, result, columns = get_costumers_amc(name, id_c)
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return []


def getSupplier(**kwargs):
    name = None
    id_s = None
    for k, v in kwargs.items():
        match k:
            case "name":
                name = v
            case "id":
                id_s = v
            case _:
                pass
    name = name if name is not None else "%"
    id_s = id_s if id_s is not None else "%"
    flag, error, result, columns = get_supplier_amc(name, id_s)
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return []


def getOrder(**kwargs):
    id_o = None
    name_c = None
    status = None
    id_c = None
    for k, v in kwargs.items():
        match k:
            case "id":
                id_o = v
            case "customer":
                name_c = v
            case "status":
                status = v
            case "id_custumer":
                id_c = v
            case _:
                pass
    pass
    id_o = id_o if id_o is not None else "%"
    id_c = id_c if id_c is not None and name_c is not None else None
    name_c = name_c if name_c is not None else "%"
    status = status if status is not None else "%"
    flag, error, result, columns = get_orders_amc(id_o, name_c, status, id_c)
    if flag:
        result.insert(0, columns)
        return result
    else:
        print(error)
        return []


def getProductMovement(**kwargs):
    return []


def getSupplyInventory(**kwargs):
    return []
