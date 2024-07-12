# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/abr./2024  at 11:38 $'

import json
import math
from datetime import datetime, timedelta

from templates.controllers.employees.employees_controller import get_all_data_employees, get_all_data_employee
from templates.controllers.employees.vacations_controller import get_vacations_data, get_vacations_data_emp
from templates.controllers.index import DataHandler
from templates.controllers.material_request.sm_controller import get_sm_entries
from templates.controllers.product.p_and_s_controller import get_sm_products

"""---------------------------API material_request-----------------------------------------"""


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


def get_all_sm(limit, page=0, emp_id=-1):
    flag, error, result = get_sm_entries(emp_id)
    if limit == -1:
        limit = len(result) + 1
    limit = limit if limit > 0 else 10
    page = page if page >= 0 else 0
    if len(result) <= 0:
        return {"data":[], "page":0, "pages":0}, 200
    pages = math.floor(len(result) / limit)
    if page > pages:
        print("page > pages")
        return None, 204
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
            'items': json.loads(result[i][11]),
            'status': result[i][12],
            'history': json.loads(result[i][13]),
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
        product['comment'] += " ;(Despachado) "
        avaliable[i] = product
    # ------------------------------products to request------------------------------------------
    for i, product in enumerate(to_request):
        _ins = _data.create_in_movement(
            product['id'], "entrada", product['quantity'], date, sm_id)
        product['comment'] += " ;(Pedido) "
        to_request[i] = product
    # ------------------------------products to request for admin-----------------------------------
    for i, product in enumerate(new_products):
        _ins = _data.create_in_movement(
            product['id'], "entrada", product['quantity'], date, sm_id)
        product['comment'] += " ;(Pedido) "
        new_products[i] = product
    return avaliable, to_request, new_products


""" --------------------------------------API RRHH----------------------------------------------------------"""


def get_info_employees_with_status(status: str):
    flag, error, result = get_all_data_employees(status)
    data_out = []
    for item in result:
        (id_emp, name, lastname, phone, department, modality, email, contract, admission, rfc, curp, nss,
         emergency_contact, position, status, departure, examen, birthday, legajo) = item
        data_out.append({
            "id": id_emp,
            "name": name.upper() + " " + lastname.upper(),
            "phone": phone,
            "dep": department,
            "modality": modality,
            "email": email,
            "contract": contract,
            "admission": admission,
            "rfc": rfc,
            "curp": curp,
            "nss": nss,
            "emergency": emergency_contact,
            "position": position,
            "status": status,
            "departure": departure,
            "exam_id": examen,
            "birthday": birthday,
            "legajo": legajo
        })

    return (data_out, 200) if flag else ([], 400)


def create_csv_file_employees(status: str):
    flag, error, result = get_all_data_employees(status)
    result = result if flag else []
    # create file
    filepath = "files/emp.csv"
    with (open(filepath, "w")) as file:
        file.write("id,name,phone,department,modality,email,contract,admission,rfc,curp,nss,emergency,position,status,departure,exam_id,birthday,legajo\n")
        for item in result:
            (id_emp, name, lastname, phone, department, modality, email, contract, admission, rfc, curp, nss,
             emergency_contact, position, status, departure, examen, birthday, legajo) = item
            file.write(f"{id_emp},{name},{phone},{department},{modality},{email},{contract},{admission},{rfc},{curp},{nss},{emergency_contact},{position},{status},{departure},{examen},{birthday},{legajo}\n")
    return filepath


def get_info_employee_id(id_emp: int):
    flag, error, result = get_all_data_employee(id_emp)
    (id_emp, name, lastname, phone, department, modality, email, contract, admission, rfc, curp, nss,
     emergency_contact, position, status, departure, examen, birthday, legajo) = result
    data_out = {
        "id": id_emp,
        "name": name.upper() + " " + lastname.upper(),
        "phone": phone,
        "dep": department,
        "modality": modality,
        "email": email,
        "contract": contract,
        "admission": admission,
        "rfc": rfc,
        "curp": curp,
        "nss": nss,
        "emergency": emergency_contact,
        "position": position,
        "status": status,
        "departure": departure,
        "exam_id": examen,
        "birthday": birthday,
        "legajo": legajo
    }
    return (data_out, 200) if flag else ({}, 400)


def get_all_vacations():
    flag, error, result = get_vacations_data()
    out = []
    if not flag or len(result) == 0:
        return [], 400
    for item in result:
        (emp_id, name, l_name, date_admission, seniority) = item

        out.append({
            "emp_id": emp_id,
            "name": name.upper() + " " + l_name.upper(),
            "date_admission": date_admission,
            "seniority": json.loads(seniority)
        })

    return out, 200


def get_vacations_employee(emp_id: int):
    flag, error, result = get_vacations_data_emp(emp_id)
    out = None
    if not flag or len(result) == 0:
        return out, 400
    (emp_id, name, l_name, date_admission, seniority) = result
    out = {
        "emp_id": emp_id,
        "name": name.upper() + " " + l_name.upper(),
        "date_admission": date_admission,
        "seniority": json.loads(seniority)
    }
    return out, 200
