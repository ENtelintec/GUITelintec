# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 22/ene./2024  at 16:09 $'

from datetime import datetime

from PIL import Image, ImageTk

from static.extensions import cache_file_resume_fichaje
from templates.Functions_Files import get_fichajes_resume_cache, update_fichajes_resume_cache
from templates.Functions_SQL import get_fichaje_DB, update_fichaje_DB, insert_new_fichaje_DB

import json

carpeta_principal = "img"


def get_image_side_menu(wname, image_path=carpeta_principal):
    """
    Get the image for the side menu.
    :param wname: The name of the window.
    :type wname: String.
    :param image_path: The path of the image.
    :type image_path: String.
    :return: The image.
    :rtype: CTkImage.
    """
    images = {
        "DB": "bd_img_col_!.png",
        "Notificaciones": "not_img_col_re.png",
        "Chats": "chat_light.png",
        "Settings": "settings.png",
        "Fichajes": "fichaje.png",
        "Cuenta": "user_robot.png",
        "Examenes": "exam_medical.png",
        "Emp. Detalles": "emp_details_dark.png",
        "Home": "warehouse_white.png",
        "Clients (A)": "employees_ligth.png",
        "Inventario": "products_ligth.png",
        "Entradas": "incoming.png",
        "Salidas": "out_p.png",
        "Devoluciones": "return_p.png",
        "Ordenes (A)": "order_p.png",
        "Proveedores (A)": "providers_p.png",
        "Configuraciones (A)": "settings.png",
        "messenger": "messenger.png",
        "whasapp": "whasapp.png",
        "telegram": "telegram.png",
        "webchat": "webchat.png",
        "logo": "telintec-500.png",
        "Empleados": "customers_ligth.png",
        "Clientes": "employees_ligth.png",
        "Departamentos": "departments_ligth.png",
        "Encargados": "heads_ligth.png",
        "Proveedores": "suppliers_ligth.png",
        "Productos": "products_ligth.png",
        "Ordenes": "orders_img.png",
        "Compras": "purchases_img.png",
        "Tickets": "ticket_img.png",
        "Chat": "chats_img.png",
        "O. Virtuales": "v_orders_img.png",
        "Usuarios": "add_user_light.png"
    }
    if wname in images.keys():
        if wname == "logo":
            image = Image.open(image_path + "/" + images[wname])
            resize_img = image.resize((100, 80))
            out_img = ImageTk.PhotoImage(resize_img)
            return out_img
            # return CTkImage(light_image=Image.open(os.path.join(image_path, images[wname])),
            #                 size=(80, 60))
        image = Image.open(image_path + "/" + images[wname])
        resize_img = image.resize((30, 30))
        out_img = ImageTk.PhotoImage(resize_img)
        return out_img
        # return CTkImage(light_image=Image.open(os.path.join(image_path, images[wname])),
        #                 size=(30, 30))
    else:
        image = Image.open(image_path + "/" + images["DB"])
        resize_img = image.resize((30, 30))
        out_img = ImageTk.PhotoImage(resize_img)
        return out_img
        # return CTkImage(light_image=Image.open(os.path.join(image_path, images["DB"])),
        #                 size=(30, 30))


def get_data_employees(status="ACTIVO"):
    columns = ("ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Dias Extra", "Total", "Primas",
               "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas")
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje)
    if flag:
        return fichajes_resume, columns
    else:
        print("error at getting data resume")
        return None, None


def get_data_employees_ids(ids: list):
    columns = ("ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Dias Extra", "Total", "Primas",
               "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas")
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje)
    if flag:
        for row in fichajes_resume:
            if row[0] not in ids:
                fichajes_resume.remove(row)
        return fichajes_resume, columns
    else:
        print("error at getting data resume")
        return None, None


def update_bitacora(emp_id: int, event, data):
    """
    Update the bitacora.
    :param emp_id: The id of the employee.
    :param event: The event.
    :param data: The data.
    :return: None.
    """
    event_dic = {}
    contract = data[3]
    flag, error, result = get_fichaje_DB(emp_id)
    if flag:
        contract_db = result[2]
        if contract_db == contract:
            match event:
                case "falta":
                    event_dic = json.loads(result[3])
                case "atraso":
                    event_dic = json.loads(result[4])
                case "extra":
                    event_dic = json.loads(result[5])
                case "prima":
                    event_dic = json.loads(result[6])
        else:
            print("error at updating bitacora, not the same contract for the employee")
    else:
        print("error at getting data from db or not data found for the employee")
    date = datetime.strptime(data[0], "%d/%m/%Y")
    if date.year not in event_dic.keys():
        event_dic[date.year] = {}
        event_dic[date.year][date.month] = {}
        event_dic[date.year][date.month][date.day] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date
        }
    elif date.month not in event_dic[date.year].keys():
        event_dic[date.year][date.month] = {}
        event_dic[date.year][date.month][date.day] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date
        }
    elif date.day not in event_dic[date.year][date.month].keys():
        event_dic[date.year][date.month][date.day] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date
        }
    if flag:
        match event:
            case "falta":
                flag, error, result = update_fichaje_DB(emp_id, contract, event_dic, result[4], result[5], result[6])
            case "atraso":
                flag, error, result = update_fichaje_DB(emp_id, contract, result[3], event_dic, result[5], result[6])
            case "extra":
                flag, error, result = update_fichaje_DB(emp_id, contract, result[3], result[4], event_dic, result[6])
            case "prima":
                flag, error, result = update_fichaje_DB(emp_id, contract, result[3], result[4], result[5], event_dic)
    else:
        match event:
            case "falta":
                flag, error, result = insert_new_fichaje_DB(emp_id, contract, event_dic, {}, {}, {})
            case "atraso":
                flag, error, result = insert_new_fichaje_DB(emp_id, contract, {}, event_dic, {}, {})
            case "extra":
                flag, error, result = insert_new_fichaje_DB(emp_id, contract, {}, {}, event_dic, {})
            case "prima":
                flag, error, result = insert_new_fichaje_DB(emp_id, contract, {}, {}, {}, event_dic)
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje)
    if flag:
        for i, row in enumerate(fichajes_resume):
            if int(row[0]) == emp_id:
                match event:
                    case "falta":
                        fichajes_resume[i][8] = event_dic
                    case "atraso":
                        fichajes_resume[i][9] = event_dic
                    case "extra":
                        fichajes_resume[i][10] = event_dic
                    case "prima":
                        fichajes_resume[i][11] = event_dic
    else:
        update_fichajes_resume_cache(cache_file_resume_fichaje, [], True)
    return flag, error, result


def get_data_from_dict_by_date(data: dict, date: datetime, stamp: str):
    """
    Get the data from the dict by the date.
    :param stamp:
    :param data: The data.
    :param date: The date.
    :return: The data.
    """
    data_out = []
    if date.year in data.keys():
        if date.month in data[date.year].keys():
            for day in data[date.year][date.month].values():
                data_out.append([stamp, day["timestamp"], day["value"], day["comment"]])
            return data_out
    return None


def unify_data_list(info_list: list, data: list[list]):
    """
    Unify the data list.
    :param info_list: The info list.
    :param data: The data.
    :return: The data.
    """
    out_list = []
    # concatenate info list with every row of data list
    for data_event in data:
        if data_event is None:
            continue
        for row in data_event:
            out_list.append(info_list + row)
    return out_list


def get_events_date(date):
    """
    Get the events of the date.
    :param date: The date.
    :return: The events.
    """
    data_events = []
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje)
    for row in fichajes_resume:
        (id_emp, name, contract, faltas, tardanzas, extras, extras_value, primas,
         absences_dic, lates_dic, extras_dic, primes_dic) = row
        data_absences = get_data_from_dict_by_date(absences_dic, date, "falta")
        data_lates = get_data_from_dict_by_date(lates_dic, date, "atraso")
        data_extras = get_data_from_dict_by_date(extras_dic, date, "extra")
        data_primes = get_data_from_dict_by_date(primes_dic, date, "prima")
        data_events_emp = unify_data_list([id_emp, name, contract],
                                          [data_absences, data_lates, data_extras, data_primes])
        for item in data_events_emp:
            if item is not None:
                data_events.append(item)

    columns = ("ID", "Nombre", "Contrato", "Evento", "Timestamp", "Valor", "Comentario")
    return data_events, columns
