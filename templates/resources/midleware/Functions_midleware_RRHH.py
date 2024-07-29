# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 28/jun./2024  at 16:28 $'

import json
from datetime import datetime

import pandas as pd

from static.extensions import files_fichaje_path, patterns_files_fichaje, cache_file_emp_fichaje, format_date_fichaje_file
from templates.Functions_Sharepoint import get_files_site, download_files_site
from templates.controllers.payroll.payroll_controller import get_payrolls, update_payroll
from templates.misc.Functions_AuxFiles import get_events_op_date, get_pairs_nomina_docs, get_data_xml_file_nomina
from templates.misc.Functions_Files import extract_fichajes_file, check_names_employees_in_cache, get_info_f_file_name, \
    get_info_t_file_name, get_info_bitacora, unify_data_employee
from templates.misc.Functions_Files_RH import check_fichajes_files_in_directory


class ClockFichajeHours:
    def __init__(self, time: str):
        self.time_in = time.split(":")
        self.hours = int(self.time_in[0])

    def get(self):
        return self.hours


class ClockFichajeMinutes:
    def __init__(self, time: str):
        self.time_in = time.split(":")
        self.minutes = int(self.time_in[1])

    def get(self):
        return self.minutes


class GraceMinutes:
    def __init__(self, grace: int):
        self.minutes = grace

    def get(self):
        return self.minutes


def get_files_fichaje():
    flag, files = check_fichajes_files_in_directory(files_fichaje_path, patterns_files_fichaje)
    if not flag:
        return False, files
    files_list = [v for k, v in files.items()]
    print(files_list)
    return True, files_list


def get_data_file(filename: str, type_f: str):
    if type_f.lower() == "fichaje":
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            dff = extract_fichajes_file(filename)
            coldata = []
            names_list = []
            if len(dff) != 0:
                coldata = []
                for i, col in enumerate(dff.columns.tolist()):
                    coldata.append(
                        {"text": col, "stretch": True}
                    )
                names_list = dff["name"].unique().tolist()
                names_and_ids = check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
                for name in names_and_ids.keys():
                    name_db = names_and_ids[name]["name_db"]
                    id_db = names_and_ids[name]["id"]
                    dff.loc[dff["name"] == name, "name"] = name_db
                    dff.loc[dff["name"] == name_db, "ID"] = id_db
                # enables scales
                names_list = dff["name"].unique().tolist()
            return True, {"columns": coldata, "df": dff, "names": names_list}
        return False, ["No aceptable extension detected"]
    else:
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            dft = extract_fichajes_file(filename)
            coldata = []
            for i, col in enumerate(dft.columns.tolist()):
                coldata.append(
                    {"text": col, "stretch": True}
                )
            names_list = dft["name"].unique().tolist()
            names_and_ids = check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
            for name in names_and_ids.keys():
                name_db = names_and_ids[name]["name_db"]
                id_db = names_and_ids[name]["id"]
                dft.loc[dft["name"] == name, "name"] = name_db
                dft.loc[dft["name"] == name, "ID"] = id_db
            return True, {"columns": coldata, "df": dft}
        return False, ["No aceptable extension detected"]


def get_bitacora_data(date_file):
    data_bitacora, columns = get_events_op_date(date_file, True)
    # create dataframe pandas
    data_f = {}
    for i, column in enumerate(columns):
        data_f[column] = []
        for row in data_bitacora:
            if column == "Nombre":
                data_f[column].append(row[i].upper())
            else:
                data_f[column].append(row[i])
    dfb = pd.DataFrame.from_dict(data_f)
    return True, {"df": dfb, "columns": columns}


def get_data_name_fichaje(name: str, dff, dft, dfb, clocks, window_time_in, window_time_out):
    df_name = dff[dff["name"] == name]
    id_emp = df_name["ID"].values[0]
    date_max = dff["Fecha"].max()  # most recent date
    # -----------file fichaje------------
    (worked_days_f, days_absence, count_l_f, count_e_f,
     days_late_dic_f, days_extra_dic_f, days_early_dic_f) = get_info_f_file_name(
        dff, name, clocks, window_time_in, window_time_out, True if dff is not None else False, date_max=date_max)
    date_example = pd.to_datetime(worked_days_f[0][0]) if len(worked_days_f) > 0 else datetime.now()
    # ------------file ternium-----------
    (worked_days_t, worked_intime_t, count_l_t, count_e_t,
     days_late_t, days_extra_t, days_worked_t, days_not_worked_t, days_early_t) = get_info_t_file_name(
        dft, name, clocks, window_time_in, window_time_out,
        True if dft is not None else False, month=date_example.month, date_max=date_max)
    # ------------info bitacora-----------
    (days_absence_bit, days_extra_bit, days_primes_bit, days_lates_bit,
     absences_bit, extras_bit, primes_bit, lates_bit, normals_bit, early_bit, pasive_bit,
     contract) = get_info_bitacora(
        dfb, name=name, id_emp=id_emp, flag=True, date_limit=date_max)
    (normal_data_emp, absence_data_emp, prime_data_emp,
     late_data_emp, extra_data_emp, early_data_emp, pasive_data_emp) = unify_data_employee(
        [worked_days_f, days_worked_t, normals_bit],
        [days_absence, None, absences_bit],
        [None, None, primes_bit],
        [days_late_dic_f, days_late_t, lates_bit],
        [days_extra_dic_f, days_extra_t, extras_bit],
        [days_early_dic_f, days_early_t, early_bit],
        [None, None, pasive_bit],
    )
    list_normal_data = [{"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]} for k, v in normal_data_emp.items()]
    list_absence_data = [{"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]} for k, v in absence_data_emp.items()]
    list_primer_data = [{"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]} for k, v in prime_data_emp.items()]
    list_late_data = [{"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]} for k, v in late_data_emp.items()]
    list_extra_data = [{"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]} for k, v in extra_data_emp.items()]
    list_early_data = [{"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]} for k, v in early_data_emp.items()]
    list_pasive_data = [{"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]} for k, v in pasive_data_emp.items()]
    return {"name": name, "ID": id_emp, "contract": contract,
            "normal_data": list_normal_data, "absence_data": list_absence_data,
            "prime_data": list_primer_data, "late_data": list_late_data, 
            "extra_data": list_extra_data, 
            "early_data": list_early_data, 
            "pasive_data": list_pasive_data}


def get_fichaje_data(data: dict):
    files = data.get("files")
    clock_h = ClockFichajeHours(data.get("time_in"))
    clock_m = ClockFichajeMinutes(data.get("time_in"))
    clock_h_out = ClockFichajeHours(data.get("time_out"))
    clock_m_out = ClockFichajeMinutes(data.get("time_out"))
    grace_in = GraceMinutes(data.get("grace_init"))
    grace_out = GraceMinutes(data.get("grace_end"))
    clocks = [{"entrada": [clock_m, clock_h]},
              {"salida":  [clock_m_out, clock_h_out]}]
    data_files = []
    name_list = []
    date_file = ""
    dff, dft = None, None
    for file in files:
        flag, data_file = get_data_file(file["path"],  file["report"])
        data_files.append(data_file) if flag else data_files.append([])
        name_list.extend(data_file["names"]) if "names" in data_file.keys() else None
        if file["report"].lower() == 'fichaje':
            date_file = file["date"]
            dff = data_file["df"]
        else:
            dft = data_file["df"]
    date_file = datetime.strptime(date_file, format_date_fichaje_file)
    flag,  data_bitacora = get_bitacora_data(date_file)
    data_out = []
    for name in name_list:
        data_emp = get_data_name_fichaje(name, dff, dft, data_bitacora["df"], clocks, grace_in, grace_out)
        data_out.append(data_emp)
    return 200, data_out


def upload_nomina_doc(data):
    pass
    return 200, None


def update_files_data_nominas(key: str, paths_pdf_xml: dict, data_xml: dict):
    flag, error, result = get_payrolls(data_xml["emp_id"])
    data_emp = {} if not flag or len(result) == 0 else json.loads(result[1])
    date = pd.to_datetime(data_xml["date"])
    year = str(date.year)
    month = str(date.month)
    if year in data_emp.keys():
        if month in data_emp[year].keys():
            data_emp[year][month][key] = paths_pdf_xml
        else:
            data_emp[year][month] = {key: paths_pdf_xml}
        return data_emp
    if month in data_emp.keys():
        data_emp[year][month][key] = paths_pdf_xml
    else:
        data_emp[year] = {month: {key: paths_pdf_xml}}
    return data_emp


def update_data_docs_nomina():
    settings = json.load(open("files/settings.json", "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    folder_nominas = settings["gui"]["RRHH"]["folder_nominas"]
    data, code = get_files_site(url_shrpt+folder_rrhh, folder_nominas)
    data_dict = get_pairs_nomina_docs(data)
    data_emps = {}
    results = []
    for k, v in data_dict.items():
        download_path, code = download_files_site(url_shrpt+folder_rrhh, v["xml"])
        if code == 200:
            data_file = get_data_xml_file_nomina(download_path)
            data_emps[data_file["emp_id"]] = update_files_data_nominas(k, v, data_file)
            flag, error, result = update_payroll(data_emps[data_file["emp_id"]], data_file["emp_id"])
            results.append((flag, error, result))
    return results


def download_nomina_doc(data):
    settings = json.load(open("files/settings.json", "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    download_path, code = download_files_site(url_shrpt+folder_rrhh, data["file_url"])
    return download_path, code


def get_files_list_nomina(emp_id):
    flag, error, result = get_payrolls(emp_id)
    files = []
    for item in result:
        emp_id = int(item[0])
        dict_data = json.loads(item[1])
        for year in dict_data.keys():
            for month in dict_data[year].keys():
                for file in dict_data[year][month].keys():
                    files.append({
                        "year": year,
                        "month": month,
                        "files": dict_data[year][month][file],
                        "name":  file,
                        "emp_id": emp_id
                    })
    return 200, files
