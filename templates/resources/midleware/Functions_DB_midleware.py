# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/abr./2024  at 11:38 $'

import json
import math
import os
import tempfile
from datetime import datetime, timedelta

import pandas as pd

from static.extensions import format_timestamps, log_file_sm_path
from templates.controllers.employees.employees_controller import get_all_data_employees, get_all_data_employee, \
    get_emp_contract
from templates.controllers.employees.vacations_controller import get_vacations_data, get_vacations_data_emp
from templates.controllers.index import DataHandler
from templates.controllers.material_request.sm_controller import get_sm_entries, get_sm_by_id, update_history_sm, \
    get_info_names_by_sm_id, update_sm_products_by_id
from templates.controllers.product.p_and_s_controller import get_sm_products
from templates.forms.Materials import MaterialsRequest
from templates.misc.Functions_Files import write_log_file
from templates.Functions_Utils import create_notification_permission

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
        return {"data": [], "page": 0, "pages": 0}, 200
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
        products = json.loads(result[i][10])
        new_products = []
        for product in products:
            if ("(Nuevo)" in product["comment"] and "(Pedido)" not in product["comment"]) or product["url"]!="":
                new_products.append(product)
        extra_info = json.loads(result[i][14])
        items.append({
            'id': result[i][0],
            'folio': result[i][1],
            'contract': result[i][2],
            'facility': result[i][3],
            'location': result[i][4],
            'client_id': result[i][5],
            'emp_id': result[i][6],
            'order_quotation': result[i][7],
            'date': result[i][8],
            'critical_date': result[i][9],
            'items': json.loads(result[i][10]),
            'items_new': new_products,
            'status': result[i][11],
            'history': json.loads(result[i][12]),
            'comment': result[i][13],
            'destination':  extra_info["destination"] if "destination" in extra_info.keys() else "",
            'contract_contact':  extra_info["contract_contact"] if "contract_contact" in extra_info.keys() else ""
        })
    data_out = {
        'data': items,
        'page': page,
        'pages': pages + 1
    }
    return data_out, 200


def update_data_dicts(products: list, products_sm):    
    for list_items in products:
        for item in list_items:
            for i, item_p in enumerate(products_sm):
                if item["id"] == item_p["id"]:
                    products_sm[i] = item
                    break
    return products_sm


def dispatch_sm(data):
    if len(data["items"]) > 0:
        flag, error, result = update_sm_products_by_id(data["items"], data["id"])
        if not flag:
            return 400, f"Not posible to update products in sm, error: {error}"
    flag, error, result = get_sm_by_id(data['id'])
    if not flag or len(result) <= 0:
        return 400, ["sm not foud"]
    history_sm = json.loads(result[0][13])
    emp_id_creation = result[0][7]
    history_sm.append(
        {"user": data["emp_id"], "event": "dispatch", "date": datetime.now().strftime(format_timestamps),
         "comment": data["comment"]})
    products_sm = json.loads(result[0][11])
    products_to_dispacth = []
    products_to_request = []
    new_products = []
    for item in products_sm:
        if "(Nuevo)" in item["comment"] and "(Pedido)" not in item["comment"]:
            new_products.append(item)
            continue
        if ((item["stock"] >= item["quantity"] or
            "(Pedido)" in item["comment"]) and 
                "(Despachado)" not in item["comment"]):
            products_to_dispacth.append(item)
        elif "(Pedido)" not in item["comment"] and "(Despachado)" not in item["comment"]:
            products_to_request.append(item)
    # update db with corresponding movements
    (products_to_dispacth, products_to_request, new_products) = dispatch_products(
        products_to_dispacth, products_to_request, data['id'], new_products)
    # update table with new stock
    products_sm = update_data_dicts([products_to_dispacth, products_to_request, new_products], products_sm)
    is_complete = True if len(products_to_request) == 0 and len(new_products) == 0 else False
    flag, error, result = update_history_sm(data['id'], history_sm, products_sm, is_complete)
    if flag:
        msg = f"SM con ID-{data['id']} despachada"
        write_log_file(log_file_sm_path, msg)
        msg += "\n Productos a despachar:  " + "\n".join([f"{item['quantity']} {item['name']}" for item in products_to_dispacth])
        msg += "\n Productos a solicitar:  " + "\n".join([f"{item['quantity']} {item['name']}" for item in products_to_request])
        msg += "\n Productos nuevos:  " + "\n".join([f"{item['quantity']} {item['name']} {item['url']}" for item in new_products])
        create_notification_permission(msg, ["sm"], "SM Despachada", data["emp_id"], emp_id_creation)
        return 200, {"to_dispatch": products_to_dispacth, "to_request": products_to_request,
                     "new_products": new_products}
    else:
        return 400, {"msg": str(error)}


def cancel_sm(data):
    flag, error, result = get_sm_by_id(data['id'])
    if not flag or len(result) <= 0:
        return 400, ["sm not foud"]
    history_sm = json.loads(result[0][13])
    emp_id_creation = result[0][7]
    history_sm.append(
        {"user": data["emp_id"], "event": "cancelation", "date": datetime.now().strftime(format_timestamps),
         "comment": data["comment"]})
    flag, error, result = update_history_sm(data['id'], history_sm, [], True)
    if flag:
        msg = f"SM con ID-{data['id']} cancelada"
        create_notification_permission(msg, ["sm"], "SM Cancelada", data["emp_id"], emp_id_creation)
        write_log_file(log_file_sm_path, msg)
        return 200, {"msg": "ok"}
    else:
        return 400, {"msg": str(error)}


def get_employees_almacen():
    flag, error, result = get_emp_contract("almacen")
    print(flag, error, result)
    data_out = []
    for item in result:
        id_emp, name, lastname = item
        data_out.append({
            "id": id_emp,
            "name": name.upper() + " " + lastname.upper()
        })
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
    # ------------------------------products to request for new-----------------------------------
    for i, product in enumerate(new_products):
        if product["id"] == -1:
            continue
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
        file.write(
            "id,name,phone,department,modality,email,contract,admission,rfc,curp,nss,emergency,position,status,departure,exam_id,birthday,legajo\n")
        for item in result:
            (id_emp, name, lastname, phone, department, modality, email, contract, admission, rfc, curp, nss,
             emergency_contact, position, status, departure, examen, birthday, legajo) = item
            file.write(
                f"{id_emp},{name},{phone},{department},{modality},{email},{contract},{admission},{rfc},{curp},{nss},{emergency_contact},{position},{status},{departure},{examen},{birthday},{legajo}\n")
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


def dowload_file_sm(sm_id: int):
    flag, error, result = get_sm_by_id(sm_id)
    if not flag or len(result) == 0:
        return None, 400    
    folio = result[1]
    contract = result[2]
    facility = result[3]
    location = result[4]
    client_id = result[5]
    emp_id = result[6]
    order_quotation = result[7]
    date = pd.to_datetime(result[8])
    critical_date = pd.to_datetime(result[9])
    items = json.loads(result[10])
    status = result[11]
    history = json.loads(result[12])
    observations = result[13]
    extra_info = json.loads(result[14])
    download_path = os.path.join(tempfile.mkdtemp(), os.path.basename(f"sm_{result[0]}_{date.date()}.pdf"))
    products = []
    flag, error, result = get_info_names_by_sm_id(result[0])
    if flag and len(result) == 0:
        customer_name = result[0]
        emp_name = result[1] + " " + result[2]
    else:
        customer_name = "None"
        emp_name = "None"
    counter = 1
    for item in items:
        name = item['name'] if "name" in item.keys() else "None"
        quantity = item['quantity'] if "quantity" in item.keys() else "None"
        comment = item['comment'] if "comment" in item.keys() else "None"
        udm = item['udm'] if "udm" in item.keys() else "None"
        stock = item['dispached'] if "dispached" in item.keys() else "None"
        if "(despachado)" in comment.lower():
            status = "Despachado"
        elif "(pedido)" in comment.lower():
            status = "Pedido"
        elif "(nuevo)" in comment.lower():
            status = "Nuevo-Pedido"
        else:
            status = "pendiente"
        products.append((counter, name, quantity, udm, stock, status))        
    flag = MaterialsRequest({
        "filename_out": download_path,
        "products": products,
        "info": {
            "fecha de solictud": date.date(),
            "contrato": contract,
            "numero de pedido": order_quotation,
            "planta": facility,
            "Area/ubicacion": location,
            "folio": folio,
            "usuario solicitante": customer_name,
            "personal telintec": emp_name,
            "area dirigida telintec": extra_info["destination"],
            "fecha critica de entrega": critical_date.date(),
            "history": history,
        },
        "observations": observations,
        "date_complete_delivery": "2023-06-01",
        "date_first_delivery": "2023-06-01",
    },
        type_form="MaterialsRequest")
    if not flag:
        print("error at generating pdf", download_path)
        return None, 400
    return download_path, 200
