# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 22/ene./2024  at 16:09 $'

import json
import os
from datetime import datetime

from static.extensions import cache_file_resume_fichaje_path, status_dic, quizz_out_path, format_date, format_timestamps
from templates.misc.Functions_Files import get_fichajes_resume_cache, update_fichajes_resume_cache
from templates.controllers.employees.employees_controller import get_name_employee
from templates.controllers.fichajes.fichajes_controller import get_fichaje_DB, update_fichaje_DB, insert_new_fichaje_DB
from templates.controllers.material_request.sm_controller import get_sm_entries
from templates.controllers.product.p_and_s_controller import get_sm_products


def get_data_employees(status="ACTIVO"):
    columns = (
        "ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Total tardanzas", "Dias Extra", "Total extra", "Primas",
        "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas", "Detalles Normal")
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje_path)
    if flag:
        return fichajes_resume, columns
    else:
        print("error at getting data resume")
        return None, None


def get_data_employees_ids(ids: list):
    columns = ("ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Dias Extra", "Total", "Primas",
               "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas")
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje_path)
    if flag:
        for row in fichajes_resume:
            if row[0] not in ids:
                fichajes_resume.remove(row)
        return fichajes_resume, columns
    else:
        print("error at getting data resume")
        return None, None


def update_event_dict(event_dic, data):
    date = datetime.strptime(data[0], format_date)
    if str(date.year) not in event_dic.keys():
        event_dic[str(date.year)] = {}
        event_dic[str(date.year)][str(date.month)] = {}
        event_dic[str(date.year)][str(date.month)][str(date.day)] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date.strftime(format_timestamps)
        }
    elif str(date.month) not in event_dic[str(date.year)].keys():
        event_dic[str(date.year)][str(date.month)] = {}
        event_dic[str(date.year)][str(date.month)][str(date.day)] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date.strftime(format_timestamps)
        }
    elif str(date.day) not in event_dic[str(date.year)][str(date.month)].keys():
        event_dic[str(date.year)][str(date.month)][str(date.day)] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date.strftime(format_timestamps)
        }
    else:
        event_dic[str(date.year)][str(date.month)][str(date.day)] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date.strftime(format_timestamps)
        }
    return event_dic


def update_bitacora(emp_id: int, event, data):
    """
    Update the bitacora.
    :param emp_id: The id of the employee.
    :param event: The event.
    :param data: The data.
    :return: None.
    """
    events_indexes_db = {"falta": 3, "atraso": 4, "extra": 5, "prima": 6, "normal": 7}
    events_cache_indexes = {"falta": 9, "atraso": 10, "extra": 11, "prima": 12, "normal": 13}
    emp_id = int(emp_id)
    event_dic = {}
    new_registry = False
    contract_sel = data[3]
    # -----------------------retrieve fichaje from db--------------------------
    flag, error, result = get_fichaje_DB(emp_id)
    # --------------------------check event -----------------------------------
    if flag and len(result) > 0:
        event_dic = json.loads(result[events_indexes_db[event]])
    else:
        print("error at getting data from db or not data found for the employee")
        new_registry = True
    # ------------------update dictionary event-----------------------------
    event_dic = update_event_dict(event_dic, data)
    print("getting cache to update event")
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje_path)
    if not flag:
        return False, "error at getting cache file to update", result
    # ----------------- if new registry on db---------------------------------
    if new_registry:
        print("new registry in fichajes db")
        name = get_name_employee(emp_id)
        fichajes_resume.append([emp_id, name.title(), contract_sel, 0, 0, 0, 0, 0, 0, {}, {}, {}, {}, {}])
    # -----------------------------updates cache data and db--------------------------------
    flag = False
    for i, row in enumerate(fichajes_resume):
        # data in cache
        new_row = list(row)
        if row[0] == emp_id:
            new_row[events_cache_indexes[event]] = event_dic
            fichajes_resume[i] = new_row
            flag, error, result = update_fichaje_DB(
                emp_id, new_row[2],
                new_row[9], new_row[10], new_row[11], new_row[12], new_row[13])
            if flag:
                print("value updated in DB")
                flag, error = update_fichajes_resume_cache(cache_file_resume_fichaje_path, fichajes_resume, just_file=True)
                return flag, error, result
            else:
                print("error at updating the value in DB")
                return False, "error at updating the value in DB", None
    new_row = [emp_id, contract_sel, 0, 0, 0, 0, 0, 0, {}, {}, {}, {}, {}]
    new_row[events_cache_indexes[event]] = event_dic
    fichajes_resume.append(new_row)
    flag, error, result = insert_new_fichaje_DB(new_row[0], new_row[1], new_row[9], new_row[10],
                                                new_row[11], new_row[12], new_row[13])
    if flag:
        print("value inserted in DB")
        flag, error = update_fichajes_resume_cache(cache_file_resume_fichaje_path, fichajes_resume, just_file=True)
        return flag, error, result
    return flag, error, result


def update_bitacora_value(emp_id: int, event, data, id_event=None):
    """
    Update the bitacora for just values.
    :param id_event: 
    :param emp_id: The id of the employee.
    :param event: The event.
    :param data: The data.
    :return: None.
    """
    events_indexes_db = {"falta": 3, "atraso": 4, "extra": 5, "prima": 6, "normal": 7}
    events_cache_indexes = {"falta": 9, "atraso": 10, "extra": 11, "prima": 12, "normal": 13}
    event_dic = {}
    contract_sel = data[3]
    flag, error, result = get_fichaje_DB(emp_id)
    if flag and len(result) > 0:
        event_dic = json.loads(result[events_indexes_db[event]])
    else:
        print("error at getting data from db or not data found for the employee")
    date = datetime.strptime(data[0], format_date)
    try:
        event_dic[str(date.year)][str(date.month)][str(date.day)] = {
            "value": data[1],
            "comment": data[2],
            "timestamp": date.strftime(format_timestamps)
        }
    except KeyError:
        print(f"error at updating the value for {date}")
        return False, f"error at updating the value for {date}", None
    
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje_path)
    if not flag:
        print("error at getting data from cache")
        return False, "error at getting data from cache", None
    # -----------------------update fichaje cache and db-----------------------------
    for i, row in enumerate(fichajes_resume):
        new_row = list(row)
        if row[0] == emp_id:
            new_row[events_cache_indexes[event]] = event_dic
            fichajes_resume[i] = new_row
            flag, error, result = update_fichaje_DB(
                emp_id, new_row[2],
                new_row[9], new_row[10], new_row[11], new_row[12], new_row[13])
            if flag:
                print("value updated in DB")
                flag, error = update_fichajes_resume_cache(cache_file_resume_fichaje_path, fichajes_resume, just_file=True)
                return flag, error, result
            else:
                print("error at updating the value in DB")
                return False, "error at updating the value in DB", None
    return False, "error at updating the value in DB", None


def erase_value_bitacora(emp_id: int, event, data):
    """
    Erase the value of the bitacora.
    :param emp_id: The id of the employee.
    :param event: The event.
    :param data: The data.
    :return: None.
    """
    events_indexes_db = {"falta": 3, "atraso": 4, "extra": 5, "prima": 6, "normal": 7}
    events_cache_indexes = {"falta": 9, "atraso": 10, "extra": 11, "prima": 12, "normal": 13}
    event_dic = {}
    contract_sel = data[1]
    flag, error, result = get_fichaje_DB(emp_id)
    if flag and len(result) > 0:
        event_dic = json.loads(result[events_indexes_db[event]])
    else:
        print("error at getting data from db or not data found for the employee")
    date = datetime.strptime(data[0], format_date)
    if str(date.year) in event_dic.keys():
        if str(date.month) in event_dic[str(date.year)].keys():
            if str(date.day) in event_dic[str(date.year)][str(date.month)].keys():
                del event_dic[str(date.year)][str(date.month)][str(date.day)]
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje_path)
    if not flag:
        print("error at getting data from cache")
        return False, "error at getting data from cache", None
    # -------------- updatin cache file and db------------------------------------
    for i, row in enumerate(fichajes_resume):
        new_row = list(row)
        if row[0] == emp_id:
            new_row[events_cache_indexes[event]] = event_dic
            fichajes_resume[i] = new_row
            flag, error, result = update_fichaje_DB(
                emp_id, new_row[2],
                new_row[9], new_row[10], new_row[11], new_row[12], new_row[13])
            if flag:
                print("value updated in DB")        
                flag, error = update_fichajes_resume_cache(cache_file_resume_fichaje_path, fichajes_resume, just_file=True)
                return flag, error, result
            else:
                print("error at updating the value in DB")
                return False, "error at updating the value in DB", None
    return False, "error at deleting the value in DB", None


def get_data_from_dict_by_date(data: dict, date: datetime, stamp: str):
    """
    Get the data from the dict by the date.
    :param stamp:
    :param data: The data.
    :param date: The date.
    :return: The data.
    """
    data_out = []
    if str(date.year) in data.keys():
        if str(date.month) in data[str(date.year)].keys():
            for day in data[str(date.year)][str(date.month)].values():
                place, activity, incidence, comment = get_place_incidence_from_comment(day["comment"])
                data_out.append([stamp, place, activity, incidence, day["timestamp"], day["value"], comment])
            return data_out
    return None


def unify_data_list_events(info_list: list, data: list[list]):
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


def get_place_incidence_from_comment(comment: str):
    """
    Get the place and activity from the comment.
    :param comment: The comment.
    :return: The place and activity.
    """
    rows = comment.split("\n")
    place = ""
    activity = ""
    incidence = ""
    comment_out = ""
    for i, row in enumerate(rows):
        if i >= 1:
            if "actividad" in row:
                activity = row.split("-->")[1]
            elif "lugar" in row:
                place = row.split("-->")[1]
            elif "incidencia" in row:
                incidence = row.split("-->")[1]
            elif "-->" not in row:
                comment_out = row
        elif "-->" not in row:
            comment_out = row
    return place, activity, incidence, comment_out


def get_events_op_date(date: datetime, hard_update, only_op=True):
    """
    Get the events of the date.
    :param only_op:
    :param hard_update: Update from db
    :param date: The date.
    :return: The events.
    """
    data_events = []
    fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje_path, is_hard_update=hard_update)
    for row in fichajes_resume:
        (id_emp, name, contract, faltas, tardanzas, tardanzas_value, extras, extras_value, primas,
         absences_dic, lates_dic, extras_dic, primes_dic, normal_dic) = row
        data_absences = get_data_from_dict_by_date(absences_dic, date, "falta")
        data_lates = get_data_from_dict_by_date(lates_dic, date, "atraso")
        data_extras = get_data_from_dict_by_date(extras_dic, date, "extra")
        data_primes = get_data_from_dict_by_date(primes_dic, date, "prima")
        data_normal = get_data_from_dict_by_date(normal_dic, date, "normal")
        data_events_emp = unify_data_list_events([id_emp, name, contract],
                                                 [data_absences, data_lates, data_extras, data_primes, data_normal])
        for item in data_events_emp:
            if item is not None:
                if item[2] != "None" or not only_op:
                    data_events.append(item)
    columns = ("ID", "Nombre", "Contrato", "Evento", "Lugar", "Actividad", "Incidencia", "Timestamp", "Valor", "Comentario")
    return data_events, columns


def split_commment(txt: str, type_fun=0) -> dict:
    """
    Split the comment.
    :paramtxt: The comment.
    :return: The comment.
    Example ---> <"comentary \nincidencia-->acuerdo\nactividad-->actividad\nlugar-->lugar">
    """
    match type_fun:
        case 0:
            comment_dict = {
                "comment": "",
                "incidence": "",
                "activity": "",
                "place": "",
                "contract": None
            }
            rows = txt.split("\n")
            for i, row in enumerate(rows):
                if i == 0:
                    comment_dict["comment"] = rows[0]
                elif i >= 1:
                    if "actividad" in row:
                        comment_dict["activity"] = row.split("-->")[1]
                    elif "lugar" in row:
                        comment_dict["place"] = row.split("-->")[1]
                    elif "incidencia" in row:
                        comment_dict["incidence"] = row.split("-->")[1]
                    elif "contrato" in row:
                        comment_dict["contract"] = row.split("-->")[1]
                    else:
                        comment_dict["comment"] += "\t" + row
        case 1:
            comment_dict = {
                "comment": "",
                "pedido_cotizacion": "",
                "activity": "",
                "place": "",
                "contract": None
            }
            rows = txt.split("\n")
            for i, row in enumerate(rows):
                if i == 0:
                    comment_dict["comment"] = rows[0]
                elif i >= 1:
                    if "actividad" in row:
                        comment_dict["activity"] = row.split("-->")[1]
                    elif "lugar" in row:
                        comment_dict["place"] = row.split("-->")[1]
                    elif "incidencia" in row:
                        comment_dict["incidence"] = row.split("-->")[1]
                    elif "contrato" in row:
                        comment_dict["contract"] = row.split("-->")[1]
                    else:
                        comment_dict["comment"] += "\t" + row
        case _:
            comment_dict = {"comment": txt}
    return comment_dict


def unify_comment_dict(comment_dict: dict):
    """
    Unify the comment dict.
    :param comment_dict: The comment dict.
    :return: The comment dict.
    """
    comment = comment_dict["comment"]
    if comment_dict["incidence"] != "":
        comment += "\nincidencia-->" + comment_dict["incidence"]
    if comment_dict["activity"] != "":
        comment += "\nactividad-->" + comment_dict["activity"]
    if comment_dict["place"] != "":
        comment += "\nlugar-->" + comment_dict["place"]
    if comment_dict["contract"] is not None:
        comment += "\ncontrato-->" + str(comment_dict["contract"])
    return comment


def save_json_file_quizz(dict_quizz: dict, file_name: str):
    """
    Save the json file.
    :param dict_quizz: The dict.
    :param file_name: The file name.
    """
    # encode utf-8
    with open(file_name, "w") as file:
        json.dump(dict_quizz, file, indent=4, ensure_ascii=True)


def read_setting_file(file_path: str) -> dict:
    """
    Read the setting file.
    :param file_path: The file path.
    :return: The setting.
    """
    setting = json.load(open(file_path, encoding="utf-8"))
    return setting


def get_all_sm_entries(filter_status=False, is_supper=False, emp_id=None):
    flag, error, result = get_sm_entries()
    if flag:
        columns = (
            "ID", "Codigo", "Folio", "Contrato", "Planta", "Ubicación", "Cliente", "Empleado", "Orden/Cotización",
            "Fecha", "Fecha Limite", "Items", "Estado", "Historial", "Comentario")
        if filter_status:
            result = [row for row in result if row[12] == 0]
        if not is_supper:
            result = [row for row in result if row[7] == emp_id]
        for index, row in enumerate(result):
            id_sm, code, folio, contract, plant, location, client, employee, order, date, date_limit, items, status, history, comment = row
            new_row = (id_sm, code, folio, contract, plant, location, client, employee, order, date, date_limit, items,
                       status_dic[status], history, comment)
            result[index] = new_row
        return result, columns
    else:
        return None, None


def get_all_sm_products():
    flag, error, result = get_sm_products()
    if flag:
        columns = ("ID", "udm", "Stock", "Nombre")
        # change second column to last position column
        for i, row in enumerate(result):
            id_emp, name, udm, stock = row
            new_row = (id_emp, udm, stock, name)
            result[i] = new_row
        return result, columns
    else:
        return None, None


def load_quizzes_names(path_directory: str):
    # look for pdf filees in the directory
    quizzes_names_pdf = []
    quizzes_names_json = []
    path = path_directory
    try:
        for file in os.listdir(path_directory):
            if file.endswith(".pdf"):
                quizzes_names_pdf.append(file)
            elif file.endswith(".json"):
                quizzes_names_json.append(file)
    except Exception as e:
        print(e)
        print(path_directory)
        print(quizz_out_path)
        print("Error al cargar los quizzes, verifique la direccion del directorio en settings")
        print("intentando con directorio por defecto")
        for file in os.listdir(quizz_out_path):
            if file.endswith(".pdf"):
                quizzes_names_pdf.append(file)
            elif file.endswith(".json"):
                quizzes_names_json.append(file)
        path = quizz_out_path
    return quizzes_names_pdf,  quizzes_names_json, path


def get_data_files_quizzes(path_quizzes: str):
    """
    Get the data files.
    :param path_quizzes: The path quizzes.
    :return: The data files.
    """
    data_files = {}
    names_files_pdf, names_files_json, path = load_quizzes_names(path_quizzes)
    for json_name in names_files_json:
        file = json.load(open(path + json_name, "r"))
        name_emp = file["metadata"]["name_emp"]
        name_emp = name_emp.replace(" ", "")
        for name_pdf in names_files_pdf:
            if name_emp in name_pdf:
                break
    return names_files_pdf
