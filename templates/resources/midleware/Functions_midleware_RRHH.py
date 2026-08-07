# -*- coding: utf-8 -*-
from datetime import timedelta

__author__ = "Edisson Naula"
__date__ = "$ 28/jun./2024  at 16:28 $"

import json
import os
import tempfile
import uuid
import zipfile
from datetime import datetime

import boto3
import pandas as pd
import pytz
from botocore.exceptions import ClientError, NoCredentialsError

from static.constants import (
    cache_file_emp_fichaje,
    cache_file_resume_fichaje_path,
    conversion_quizzes_path,
    file_temp_zip,
    filepath_daemons,
    filepath_fichaje_temp,
    filepath_recommendations,
    filepath_settings,
    format_date,
    format_date_fichaje_file,
    format_timestamps,
    index_file_nominas,
    log_file_rh,
    patterns_files_fichaje,
    quizz_out_path,
    secrets,
    timezone_software,
)
from templates.controllers.employees.em_controller import (
    get_all_examenes,
    get_employees_without_records,
    insert_new_exam_med,
    update_aptitud_renovacion,
)
from templates.controllers.employees.employees_controller import (
    new_employee,
    terminate_employee_db,
    update_employee,
)
from templates.controllers.employees.vacations_controller import (
    insert_vacation,
    update_registry_vac,
)
from templates.controllers.misc.tasks_controller import (
    get_all_tasks_by_status,
    get_task_by_id_emp,
    update_task,
)
from templates.controllers.payroll.payroll_controller import (
    get_payrolls,
    update_payroll,
    update_payroll_employees,
)
from templates.Functions_Sharepoint import (
    create_mail_draft_with_attachment,
    download_files_site,
    get_files_site,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_AuxFiles import (
    get_data_xml_file_nomina,
    get_events_op_date,
    get_pairs_nomina_docs,
)
from templates.misc.Functions_Files import (
    check_names_employees_in_cache,
    extract_fichajes_file,
    get_fichajes_resume_cache,
    get_info_bitacora,
    get_info_f_file_name,
    get_info_t_file_name,
    unify_data_employee,
    write_log_file,
)
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


def create_new_employee_db(data, data_token):
    flag, error, result = new_employee(
        data["info"]["name"],
        data["info"]["lastname"],
        data["info"]["curp"],
        data["info"]["phone"],
        data["info"]["modality"],
        data["info"]["dep"],
        data["info"]["contract"],
        data["info"]["admission"],
        data["info"]["rfc"],
        data["info"]["nss"],
        data["info"]["position"],
        data["info"]["status"],
        data["info"]["departure"],
        data["info"]["birthday"],
        data["info"]["legajo"],
        data["info"]["email"],
        data["info"]["emergency"],
        data_token,
        data["info"]["id_leader"],
    )
    if flag:
        return {"data": {"id_employee": result}, "msg": f"Empleado creado correctamente (ID {result})", "error": None}, 201
    else:
        return {"data": None, "msg": "No se pudo crear el empleado", "error": error}, 400


def update_employee_db(data, data_token):
    flag, error, result = update_employee(
        data["id"],
        data["info"]["name"],
        data["info"]["lastname"],
        data["info"]["curp"],
        data["info"]["phone"],
        data["info"]["modality"],
        data["info"]["dep"],
        data["info"]["contract"],
        data["info"]["admission"],
        data["info"]["rfc"],
        data["info"]["nss"],
        data["info"]["position"],
        data["info"]["status"],
        data["info"]["departure"],
        data["info"]["birthday"],
        data["info"]["legajo"],
        data["info"]["email"],
        data["info"]["emergency"],
        data_token,
        data["info"]["id_leader"],
    )
    if flag:
        return {"data": {"id_employee": result}, "msg": f"Empleado actualizado correctamente (ID {result})", "error": None}, 200
    else:
        return {"data": None, "msg": "No se pudo actualizar el empleado", "error": error}, 400


def terminate_employee_from_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    date = timestamp.strftime(format_timestamps)
    departure = {"date": date, "reason": data["reason"]}
    flag, error, result = terminate_employee_db(data["id"], json.dumps(departure), data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo dar de baja al empleado",
            "error": error,
        }, 400
    msg = (
        f"Empleado con id: {data['id']} dado de baja por {data['reason']}. "
        f"Realizado por el empleado con id: {data_token['emp_id']} "
    )
    write_log_file(log_file_rh, msg, data_token)
    create_notification_permission(
        msg, data_token, ["rrhh"], "Empleado dato de baja", data_token.get("emp_id"), 0
    )
    return {"data": {"id_employee": data["id"]}, "msg": f"Empleado dado de baja correctamente (ID {data['id']})", "error": None}, 200


def get_files_fichaje(data_token):
    flag, files = check_fichajes_files_in_directory(patterns_files_fichaje)
    if not flag:
        return False, files
    files_list = [v for k, v in files.items()]
    return True, files_list


def fetch_fichajes_all_employees(data_token):
    fichajes_resume, flag = get_fichajes_resume_cache(
        cache_file_resume_fichaje_path, is_hard_update=True
    )
    if not flag:
        return {"data": [], "msg": "No se pudieron obtener los fichajes", "error": None}, 400
    out_aux = []
    for item in fichajes_resume:
        out_aux.append(
            {
                "id": item[0],
                "name": item[1],
                "contract": item[2],
                "absences": item[3],
                "late": item[4],
                "total_late": item[5],
                "extra": item[6],
                "total_h_extra": item[7],
                "primes": item[8],
                "absences_details": item[9],
                "late_details": item[10],
                "extra_details": item[11],
                "primes_details": item[12],
                "normals_details": item[13],
                "earlies_details": item[14],
                "pasiva_details": item[15],
            }
        )
    return {"data": out_aux, "msg": None, "error": None}, 200


def fetch_fichaje_employee(id_emp):
    fichajes_resume, flag = get_fichajes_resume_cache(
        cache_file_resume_fichaje_path, is_hard_update=True
    )
    if not flag:
        return {"data": None, "msg": "No se pudieron obtener los fichajes", "error": None}, 400
    for item in fichajes_resume:
        if str(item[0]) == id_emp:
            return {
                "data": {
                    "id": item[0],
                    "name": item[1],
                    "contract": item[2],
                    "absences": item[3],
                    "late": item[4],
                    "total_late": item[5],
                    "extra": item[6],
                    "total_h_extra": item[7],
                    "primes": item[8],
                    "absences_details": item[9],
                    "late_details": item[10],
                    "extra_details": item[11],
                    "primes_details": item[12],
                    "normals_details": item[13],
                    "earlies_details": item[14],
                    "pasiva_details": item[15],
                },
                "msg": None,
                "error": None,
            }, 200
    return {"data": None, "msg": "No se encontró el fichaje del empleado", "error": None}, 400


def get_data_file(filename: str, type_f: str):
    if type_f.lower() == "fichaje":
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            dff = extract_fichajes_file(filename)
            coldata = []
            names_list = []
            if dff is None:
                return False, ["No aceptable extension detected"]
            if len(dff) != 0:
                coldata = []
                for i, col in enumerate(dff.columns.tolist()):
                    coldata.append({"text": col, "stretch": True})
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
            if dft is None:
                return False, ["No aceptable extension detected"]
            coldata = []
            for i, col in enumerate(dft.columns.tolist()):
                coldata.append({"text": col, "stretch": True})
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


def get_data_name_fichaje(name: str, dff, dfb, clocks, window_time_in, window_time_out, dft=None):
    df_name = dff[dff["name"] == name]
    id_emp = df_name["ID"].values[0]
    date_max = dff["Fecha"].max()  # most recent date
    # -----------file fichaje------------
    (
        worked_days_f,
        days_absence,
        count_l_f,
        count_e_f,
        days_late_dic_f,
        days_extra_dic_f,
        days_early_dic_f,
    ) = get_info_f_file_name(
        dff,
        name,
        clocks,
        window_time_in,
        window_time_out,
        True if dff is not None else False,
        date_max=date_max,
    )
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone)
    date_example = pd.to_datetime(worked_days_f[0][0]) if len(worked_days_f) > 0 else date
    # ------------file ternium-----------
    (
        worked_days_t,
        worked_intime_t,
        count_l_t,
        count_e_t,
        days_late_t,
        days_extra_t,
        days_worked_t,
        days_not_worked_t,
        days_early_t,
    ) = get_info_t_file_name(
        dft,
        name,
        clocks,
        window_time_in,
        window_time_out,
        True if dft is not None else False,
        month=date_example.month,
        date_max=date_max,
    )
    # ------------info bitacora-----------
    (
        days_absence_bit,
        days_extra_bit,
        days_primes_bit,
        days_lates_bit,
        absences_bit,
        extras_bit,
        primes_bit,
        lates_bit,
        normals_bit,
        early_bit,
        pasive_bit,
        contract,
    ) = get_info_bitacora(dfb, name=name, id_emp=id_emp, flag=True, date_limit=date_max)
    (
        normal_data_emp,
        absence_data_emp,
        prime_data_emp,
        late_data_emp,
        extra_data_emp,
        early_data_emp,
        pasive_data_emp,
    ) = unify_data_employee(
        [worked_days_f, days_worked_t, normals_bit],
        [days_absence, None, absences_bit],
        [None, None, primes_bit],
        [days_late_dic_f, days_late_t, lates_bit],
        [days_extra_dic_f, days_extra_t, extras_bit],
        [days_early_dic_f, days_early_t, early_bit],
        [None, None, pasive_bit],
    )
    def _fmt_ts(k):
        if isinstance(k, str):
            return k
        if isinstance(k, datetime):
            return k.strftime(format_timestamps)
        return str(k)

    list_normal_data = [
        {"timestamp": _fmt_ts(k), "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in normal_data_emp.items()
    ]
    list_absence_data = [
        {"timestamp": _fmt_ts(k), "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in absence_data_emp.items()
    ]
    list_primer_data = [
        {"timestamp": _fmt_ts(k), "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in prime_data_emp.items()
    ]
    list_late_data = [
        {"timestamp": _fmt_ts(k), "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in late_data_emp.items()
    ]
    list_extra_data = [
        {"timestamp": _fmt_ts(k), "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in extra_data_emp.items()
    ]
    list_early_data = [
        {"timestamp": _fmt_ts(k), "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in early_data_emp.items()
    ]
    list_pasive_data = [
        {"timestamp": _fmt_ts(k), "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in pasive_data_emp.items()
    ]
    return {
        "name": name,
        "ID": id_emp,
        "contract": contract,
        "normal_data": list_normal_data,
        "absence_data": list_absence_data,
        "prime_data": list_primer_data,
        "late_data": list_late_data,
        "extra_data": list_extra_data,
        "early_data": list_early_data,
        "pasive_data": list_pasive_data,
    }


def get_fichaje_data(data: dict):
    files = data.get("files", [])
    clock_h = ClockFichajeHours(data.get("time_in", ""))
    clock_m = ClockFichajeMinutes(data.get("time_in", ""))
    clock_h_out = ClockFichajeHours(data.get("time_out", ""))
    clock_m_out = ClockFichajeMinutes(data.get("time_out", ""))
    grace_in = GraceMinutes(data.get("grace_init", ""))
    grace_out = GraceMinutes(data.get("grace_end", ""))
    clocks = [{"entrada": [clock_m, clock_h]}, {"salida": [clock_m_out, clock_h_out]}]
    data_files = []
    name_list = []
    date_file = ""
    dff = None
    for file in files:
        path, code = download_fichaje_file(
            {
                "file_url": file["path"],
                "temp": filepath_fichaje_temp,
            }
        )
        if code != 200:
            return {"data": None, "msg": "No se pudo descargar el archivo de fichaje", "error": str(path)}, 400
        flag, data_file = get_data_file(filepath_fichaje_temp, file["report"])
        if not flag:
            return {"data": None, "msg": "Error al leer el archivo de fichaje", "error": str(data_file)}, 400
        if not (isinstance(data_file, list) or isinstance(data_file, tuple)):
            return {"data": None, "msg": "Error al procesar el archivo de fichaje", "error": None}, 400
        data_files.append(data_file) if flag else data_files.append([])
        name_list.extend(data_file["names"]) if "names" in data_file.keys() else None
        if file["report"].lower() == "fichaje":
            date_file = file["date"]
            dff = data_file["df"]
    date_file = datetime.strptime(date_file, format_date_fichaje_file)
    flag, data_bitacora = get_bitacora_data(date_file)
    data_out = []
    for name in name_list:
        data_emp = get_data_name_fichaje(
            name, dff, data_bitacora["df"], clocks, grace_in, grace_out, dft=None
        )
        data_out.append(data_emp)
    return {"data": data_out, "msg": None, "error": None}, 200


def upload_nomina_doc(data):
    pass
    return 200, None


def update_files_data_nominas(key: str, paths_pdf_xml: dict, data_xml: dict, data_token):
    flag, error, result = get_payrolls(data_xml["emp_id"], data_token)
    data_emp = {} if not flag or len(result) == 0 else json.loads(result[1])
    try:
        date = pd.to_datetime(data_xml["date"])
    except Exception as e:
        print("Error, date not found in file xml. DB not updated", e)
        return data_emp, False
    year = str(date.year)
    month = str(date.month)
    if year in data_emp.keys():
        if month in data_emp[year].keys():
            data_emp[year][month][key] = paths_pdf_xml
        else:
            data_emp[year][month] = {key: paths_pdf_xml}
        return data_emp, True
    if month in data_emp.keys():
        data_emp[year][month][key] = paths_pdf_xml
    else:
        data_emp[year] = {month: {key: paths_pdf_xml}}
    return data_emp, True


def update_data_docs_nomina(data_token, patterns=None, use_index=False):
    print("Updating data docs nomina ", patterns)
    settings = json.load(open(filepath_settings, "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    folder_nominas = settings["gui"]["RRHH"]["folder_nominas"]
    patterns = patterns if patterns is not None else []
    folder_patterns = [folder_nominas] + patterns
    flag_quincena = False if len(patterns) <= 2 else True
    if len(patterns) == 3:
        flag_quincena = True if patterns[2] is not None else False
    if not use_index:
        code, data = get_files_site(url_shrpt + folder_rrhh, folder_patterns)
        data_dict = get_pairs_nomina_docs(data)
        data_dict_old = json.load(open(index_file_nominas, "r"))
        data_dict_old.update(data_dict)
        json.dump(data_dict_old, open(index_file_nominas, "w"))
    else:
        data_dict = json.load(open(index_file_nominas, "r"))
    data_emps = {}
    results = []
    for k, v in data_dict.items():
        if "xml" not in v.keys() or "pdf" not in v.keys():
            results.append((False, "No se encontraron los archivos necesarios", None))
            continue
        if folder_patterns[1].lower() in v["xml"].lower():
            if flag_quincena:
                if folder_patterns[2].lower() in v["xml"].lower():
                    download_path, code = download_files_site(url_shrpt + folder_rrhh, v["xml"])
                else:
                    print(f"Not pass the filter {folder_patterns}", v["xml"])
                    continue
            else:
                download_path, code = download_files_site(url_shrpt + folder_rrhh, v["xml"])
        else:
            print(f"Not pass the filter {folder_patterns}", v["xml"])
            continue
        if code != 200:
            results.append((False, f"Error al descargar el archivo XML: {download_path}", None))
            continue
        data_file = get_data_xml_file_nomina(download_path)
        if data_file["emp_id"] is None:
            print(f"No se encontro el empleado con datos {data_file['emp_name']}")
            results.append((False, f"No se encontro el empleado: {data_file['emp_name']}", None))
            continue
        data_emps[data_file["emp_id"]], flag = update_files_data_nominas(
            k, v, data_file, data_token
        )
        if flag:
            flag, error, result = update_payroll(
                data_emps[data_file["emp_id"]], data_file["emp_id"], data_token
            )
            results.append((flag, error, result))
        else:
            results.append((False, "Error al generar dict de empleado", None))
    return results


def download_nomina_docs(data, data_token):
    """Descarga el pdf y xml de nomina desde el bucket S3 de RH (data['pdf'] y
    data['xml'] son keys S3, ej. payroll/<year>/<month>/<emp_id>/<filename>) y
    los empaqueta en un zip. Migrado desde SharePoint."""
    bucket_name = secrets.get("S3_RH_BUCKET")
    s3_client = boto3.client("s3")
    tmp_dir = tempfile.mkdtemp()
    downloaded = []
    for key in [data.get("pdf"), data.get("xml")]:
        if not key:
            continue
        local_path = os.path.join(tmp_dir, os.path.basename(key))
        try:
            s3_client.download_file(Bucket=str(bucket_name), Key=key, Filename=local_path)
            downloaded.append(local_path)
        except (NoCredentialsError, ClientError, FileNotFoundError) as e:
            print(f"Error al descargar nomina desde S3 (key {key}): {e}")
            continue
    if len(downloaded) == 0:
        return {"data": None, "msg": "No se pudieron descargar los archivos de nómina", "error": "Ningún archivo descargado desde S3"}, 400
    with zipfile.ZipFile(file_temp_zip, "w") as zipf:
        for path in downloaded:
            zipf.write(path, arcname=os.path.basename(path))
    if not os.path.exists(file_temp_zip):
        return {"data": None, "msg": "Error al generar el archivo ZIP de nómina", "error": "El archivo ZIP no fue creado"}, 400
    return file_temp_zip, 200


def get_files_list_nomina_RH(emp_id, data_token):
    flag, error, result = get_payrolls(emp_id, data_token)
    dicts_data = []
    for item in result:
        emp_id = int(item[0])
        name = f"{item[2].upper()} {item[3].upper()}"
        dict_data = json.loads(item[1])
        dicts_data.append({"id": emp_id, "name": name, "data": dict_data})
    return 200, dicts_data


def get_files_list_nomina(emp_id, data_token):
    flag, error, result = get_payrolls(emp_id, data_token)
    if not flag:
        return {"data": None, "msg": "Error al obtener nóminas", "error": error}, 400
    files = []
    dicts_data = []
    for item in result:
        emp_id = int(item[0])
        name = f"{item[2].upper()} {item[3].upper()}"
        dict_data = json.loads(item[1])
        for year in dict_data.keys():
            for month in dict_data[year].keys():
                for file in dict_data[year][month].keys():
                    files.append(
                        {
                            "year": year,
                            "month": month,
                            "files": dict_data[year][month][file],
                            "name": file,
                            "emp_id": emp_id,
                        }
                    )
        dicts_data.append({"id": emp_id, "name": name, "data": dict_data})
    return {"data": files, "msg": None, "error": None}, 200


def insert_medical_db(data, data_token):
    allergies = data["info"]["allergies"]
    observations = data["info"]["observations"]
    extra_info = {"allergies": allergies, "observations": observations}
    flag, error, result = insert_new_exam_med(
        data["info"]["name"],
        data["info"]["blood"],
        data["info"]["status"],
        data["info"]["aptitudes"],
        data["info"]["dates"],
        data["info"]["apt_actual"],
        data["info"]["emp_id"],
        extra_info,
        data_token,
    )
    if flag:
        return {"data": {"id_exam": result}, "msg": f"Registro médico creado correctamente (ID {result})", "error": None}, 201
    else:
        return {"data": None, "msg": "No se pudo crear el registro médico", "error": error}, 400


def update_medical_db(data, data_token):
    apt_actual = data["info"]["aptitudes"][-1] if len(data["info"]["aptitudes"]) > 0 else 0
    allergies = data["info"]["allergies"]
    observations = data["info"]["observations"]
    extra_info = {"allergies": allergies, "observations": observations}
    flag, error, result = update_aptitud_renovacion(
        data["info"]["aptitudes"],
        data["info"]["dates"],
        apt_actual,
        exam_id=data["id"],
        extra_info=extra_info,
        data_token=data_token,
    )
    if flag:
        return {"data": {"id_exam": result}, "msg": f"Registro médico actualizado correctamente (ID {result})", "error": None}, 200
    else:
        return {"data": None, "msg": "No se pudo actualizar el registro médico", "error": error}, 400


def insert_new_vacation(data, data_token):
    seniority_dict = {}
    for item in data["seniority"]:
        seniority_dict[str(item["year"])] = {
            "status": item["status"],
            "comentarios": item["comentarios"],
            "dates": item.get("dates", []),
        }
    if not len(seniority_dict) > 0:
        return False, "No hay informacion que insertar", None
    flag, error, result = insert_vacation(data["emp_id"], seniority_dict, data_token=data_token)
    return flag, error, result


def update_vacation(data, data_token):
    seniority_dict = {}
    for item in data["seniority"]:
        seniority_dict[str(item["year"])] = {
            "status": item["status"],
            "comentarios": item["comentarios"],
            "prima": item["prima"],
            "dates": item["dates"],
        }
    if not len(seniority_dict) > 0:
        return False, "No hay informacion que actualizar o corrupcion de info.", None
    flag, error, result = update_registry_vac(data["emp_id"], seniority_dict, data_token)
    return flag, error, result


def get_all_quizzes(data_token):
    flag, error, tasks = get_all_tasks_by_status(status=-1, title="quizz", data_token=data_token)
    if not flag:
        return False, error, []
    data_out = []
    for item in tasks:
        data_out.append(
            {
                "id": item[0],
                "body": json.loads(item[1]),
                "data_raw": json.loads(item[2]),
                "timestamp": item[3].strftime(format_timestamps)
                if isinstance(item[3], datetime)
                else item[3],
            }
        )
    return True, "", data_out


def get_task_by_id_employee(id_emp: int, data_token):
    flag, error, result = get_task_by_id_emp(id_emp, data_token)
    if not flag:
        return {"data": None, "msg": "Error al obtener las tareas", "error": error}, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": None, "msg": "Formato de datos inválido", "error": f"no tasks {result}"}, 400
    data_out = []
    for item in result:
        data_out.append(
            {
                "id": item[0],
                "body": json.loads(item[1]),
                "data_raw": json.loads(item[2]),
                "timestamp": item[3].strftime(format_timestamps)
                if isinstance(item[3], datetime)
                else item[3],
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def get_quizz_evaluation(id_task, data_token):
    """Evalua una encuesta por su id (task) con el motor config-driven y
    devuelve el resultado uniforme. Determinista desde `data_raw` + rubrica
    (siempre fresco); no persiste ni genera PDF. Devuelve (envelope, code).
    """
    from templates.resources.midleware.quizz_eval_engine import evaluate_task

    flag, error, result = get_all_tasks_by_status(
        status=-1, data_token=data_token, id_task=id_task, title=None
    )
    if not flag:
        return {"data": None, "msg": "No se pudo obtener la encuesta", "error": error}, 400
    rows = result if isinstance(result, list) else []
    if not rows:
        return {"data": None, "msg": f"Encuesta {id_task} no encontrada", "error": None}, 404
    row = rows[0]
    body = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    data_raw = json.loads(row[2]) if isinstance(row[2], str) else row[2]
    tipo_q = (body or {}).get("metadata", {}).get("type_quizz")
    if tipo_q is None:
        return {
            "data": None,
            "msg": f"La tarea {id_task} no es una encuesta (sin type_quizz)",
            "error": None,
        }, 400
    evaluation = evaluate_task(data_raw, tipo_q, data_token)
    if evaluation is None:
        return {
            "data": None,
            "msg": f"No hay rubrica para el tipo de encuesta {tipo_q} (pendiente de migracion)",
            "error": None,
        }, 200
    return {"data": evaluation, "msg": None, "error": None}, 200


def get_quizz_group_evaluation(type_q, data_token, date_from=None, date_to=None):
    """Resultado organizacional de una encuesta: agrega TODAS las encuestas
    contestadas del tipo por conteo agrupado (motor `evaluate_group`), con
    filtro opcional por fecha del task (`YYYY-MM-DD`, ambos limites
    inclusivos). En clima (3) esto es la tabla de % por categoria + total.
    Determinista y on-read (no persiste). Devuelve (envelope, code).
    """
    from templates.resources.midleware.quizz_eval_engine import (
        evaluate_group,
        load_rubric,
    )

    rubric = load_rubric(type_q, data_token)
    if rubric is None:
        return {
            "data": None,
            "msg": f"No hay rubrica para el tipo de encuesta {type_q} (pendiente de migracion)",
            "error": None,
        }, 200
    if rubric.get("mode") == "qualitative":
        return {
            "data": None,
            "msg": f"La encuesta tipo {type_q} es cualitativa: no tiene agregado numerico",
            "error": None,
        }, 200

    limits = {}
    for name, raw in (("date_from", date_from), ("date_to", date_to)):
        if raw in (None, ""):
            limits[name] = None
            continue
        try:
            limits[name] = datetime.strptime(raw, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return {
                "data": None,
                "msg": f"Fecha invalida en {name} (formato YYYY-MM-DD): {raw}",
                "error": None,
            }, 400
    dt_from, dt_to = limits["date_from"], limits["date_to"]

    flag, error, tasks = get_all_tasks_by_status(status=-1, title="quizz", data_token=data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron obtener las encuestas", "error": error}, 400

    data_raws = []
    for row in tasks if isinstance(tasks, list) else []:
        try:
            body = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            tipo_row = int((body or {}).get("metadata", {}).get("type_quizz"))
        except (TypeError, ValueError):
            continue
        if tipo_row != int(type_q):
            continue
        if dt_from or dt_to:
            ts = row[3]
            if isinstance(ts, str):
                try:
                    ts = datetime.strptime(ts, format_timestamps)
                except ValueError:
                    continue
            if not isinstance(ts, datetime):
                continue
            if (dt_from and ts.date() < dt_from) or (dt_to and ts.date() > dt_to):
                continue
        data_raws.append(row[2])

    evaluation = evaluate_group(data_raws, rubric)
    msg = None
    if evaluation is not None and evaluation.get("respondents") == 0:
        msg = f"Sin encuestas contestadas del tipo {type_q} en el rango solicitado"
    return {"data": evaluation, "msg": msg, "error": None}, 200


# DEPRECADO: `recommendations_results_quizzes` y `calculate_results_quizzes`
# fueron reemplazadas por el motor config-driven en
# `templates/resources/midleware/quizz_eval_engine.py`. Ya no se llaman desde
# ningun lado (grep confirma). Removibles en un follow-up de limpieza.
def recommendations_results_quizzes(dict_results: dict, tipo_q: int):
    # Asumiendo que tienes la ruta correcta en filepath_recommendations
    dict_conversions_recomen = json.load(open(filepath_recommendations, encoding="utf-8"))
    dict_recommendations = {
        "c_final_r": "",
        "c_dom_r": "",
        "c_cat_r": "",
    }

    # Asumiendo que dict_results contiene las claves 'c_final', 'c_dom', 'c_cat'
    # y que pueden tener valores como 'MUY ALTO', 'ALTO', 'MEDIO', 'BAJO', 'NULO'.

    # Acceder a las recomendaciones basadas en el resultado final, dominio, y categoría
    final_score = dict_results.get(
        "c_final", "NULO"
    )  # Usar NULO como valor por defecto si no se encuentra
    dom_score = dict_results.get("c_dom", "default_dom")  # Usar un valor por defecto
    cat_score = dict_results.get("c_cat", "default_cat")  # Usar un valor por defecto

    # Acceder a las recomendaciones finales
    dict_recommendations["c_final_r"] = dict_conversions_recomen["c_final_r"].get(
        final_score, ["No hay recomendaciones específicas."]
    )
    print(dict_results)
    # Aquí necesitas modificar el código según cómo desees manejar las recomendaciones de dominio y categoría
    # dado que en tu JSON 'c_dom_r' es solo una cadena, puedes necesitar un enfoque diferente o más información
    # Si 'c_dom_r' debería ser una estructura similar a 'c_final_r', ajusta tu JSON y tu código en consecuencia
    print(cat_score)
    # check max score cat
    max_cat_score = ""
    maxv = 0
    for k, v in cat_score.items():
        if maxv < v:
            maxv = v
            max_cat_score = k
    # Acceder a las recomendaciones de categoría
    if max_cat_score in dict_conversions_recomen["c_cat_r"]:
        dict_recommendations["c_cat_r"] = dict_conversions_recomen["c_cat_r"][max_cat_score]
    else:
        dict_recommendations["c_cat_r"] = [
            "No hay recomendaciones específicas para esta categoría."
        ]

    return dict_recommendations


def calculate_results_quizzes(dict_quizz: dict, tipo_q: int):
    dict_results = {"c_final": 0, "c_dom": 0, "c_cat": 0, "detail": {}}
    dict_conversions = json.load(open(conversion_quizzes_path, encoding="utf-8"))
    match tipo_q:
        case 1:
            dict_values = dict_conversions["norm035"]["v1"]["conversion"]
            c_final = 0
            for question in dict_quizz.values():
                if question["items"] != "":
                    upper_limit = question["items"][1]
                    lower_limit = question["items"][0]
                    answers = question["answer"]
                    for q in range(lower_limit, upper_limit + 1):
                        for group in dict_values.values():
                            items = group["items"]
                            values = group["values"]
                            if q in items:
                                res = values[answers[q - lower_limit][1]]
                                dict_results["detail"][str(q)] = res
                                c_final += res
                                break
            dict_results["c_final"] = c_final
            dict_cat_doms = dict_conversions["norm035"]["v1"]["categorias"]
            dict_results["c_dom"] = {}
            dict_results["c_cat"] = {}

            for cat_dic in dict_cat_doms.values():
                cat_name = cat_dic["categoria"]
                dict_results["c_cat"][cat_name] = 0
                for dom_name, dom_dic in cat_dic["dominio"].items():
                    dict_results["c_dom"][dom_name] = 0
                    for dim_dic in dom_dic["dimensiones"]:
                        dim_name = dim_dic["dimension"]
                        items = dim_dic["item"]
                        for q, val in dict_results["detail"].items():
                            if int(q) in items:
                                dict_results["c_dom"][dom_name] += val
                                dict_results["c_cat"][cat_name] += val
        case 2:
            dict_values = dict_conversions["norm035"]["v2"]["conversion"]
            c_final = 0
            for question in dict_quizz.values():
                if question["items"] != "":
                    upper_limit = question["items"][1]
                    lower_limit = question["items"][0]
                    answers = question["answer"]
                    for q in range(lower_limit, upper_limit + 1):
                        for group in dict_values.values():
                            items = group["items"]
                            values = group["values"]
                            if q in items:
                                res = values[answers[q - lower_limit][1]]
                                dict_results["detail"][str(q)] = res
                                c_final += res
                                break
            dict_results["c_final"] = c_final
            dict_cat_doms = dict_conversions["norm035"]["v2"]["categorias"]
            dict_results["c_dom"] = {}
            dict_results["c_cat"] = {}
            dict_results["c_dim"] = {}
            for cat_dic in dict_cat_doms.values():
                cat_name = cat_dic["categoria"]
                dict_results["c_cat"][cat_name] = 0
                for dom_name, dom_dic in cat_dic["dominio"].items():
                    dict_results["c_dom"][dom_name] = 0
                    for dim_dic in dom_dic["dimensiones"]:
                        dim_name = dim_dic["dimension"]
                        items = dim_dic["item"]
                        dict_results["c_dim"][dim_name] = 0
                        for q, val in dict_results["detail"].items():
                            if int(q) in items:
                                # print("calculate: ", q, items)
                                dict_results["c_dom"][dom_name] += val
                                dict_results["c_cat"][cat_name] += val
                                dict_results["c_dim"][dim_name] += val
        case _:
            pass
    return dict_results


def _legacy_shape_from_evaluation(evaluation):
    """Deriva el shape viejo (results/recommendations) desde el resultado
    uniforme del motor, para que el generador de PDF actual siga leyendo
    `results`/`recommendations` sin tocar el layout de reportlab. Shim de
    transicion: se elimina cuando el PDF se redisene para leer `evaluation`.
    """
    total = evaluation.get("total", {})
    c_dom, c_cat = {}, {}
    cat_actions = []
    for cat in evaluation.get("breakdown", []):
        c_cat[cat.get("label")] = cat.get("score")
        if cat.get("actions") and not cat_actions:
            cat_actions = cat["actions"]
        for dom in cat.get("children", []):
            c_dom[dom.get("label")] = dom.get("score")
    results = {"c_final": total.get("score"), "c_dom": c_dom, "c_cat": c_cat}
    recommendations = {
        "c_final_r": total.get("actions", []),
        "c_dom_r": "",
        "c_cat_r": cat_actions,
    }
    return results, recommendations


def generate_pdf_from_json(data, data_token):
    from static.FramesClasses import dict_typer_quizz_generator
    from templates.resources.midleware.quizz_eval_engine import evaluate_task

    json_dict = data["body"]
    tipo_op = json_dict["metadata"]["type_quizz"]
    # Sin generador dedicado (modelos nuevos creados por API) se usa el PDF
    # generico de resumen mas abajo — necesita la evaluacion, no el generador.
    generator = dict_typer_quizz_generator.get(tipo_op)

    data_raw = (
        json.loads(data["data_raw"]) if isinstance(data["data_raw"], str) else data["data_raw"]
    )

    # Evaluacion via el motor config-driven (fuente de verdad, shape uniforme).
    evaluation = evaluate_task(data_raw, tipo_op, data_token)
    if evaluation is not None and evaluation.get("mode") == "scored":
        data_raw["evaluation"] = evaluation
        results, recommendations = _legacy_shape_from_evaluation(evaluation)
        data_raw["results"] = results
        data_raw["recommendations"] = recommendations
        # Persistir solo con un id valido (evita pisar la fila 0 por el default del form).
        if data.get("id"):
            flag, error, _ = update_task(
                data["id"], data["body"], data_raw=data_raw, data_token=data_token
            )
            if not flag:
                write_log_file(
                    log_file_rh, f"No se pudo actualizar el task de quizz: {error}", data_token
                )
    else:
        # Tipo aun sin rubrica (o cualitativo): expone la evaluacion si existe y
        # deja defaults seguros para no romper el generador de PDF.
        if evaluation is not None:
            data_raw["evaluation"] = evaluation
        data_raw.setdefault("results", {"c_final": 0, "c_dom": {}, "c_cat": {}})
        data_raw.setdefault("recommendations", {"c_final_r": [], "c_dom_r": "", "c_cat_r": []})

    # Archivo temporal unico por request (evita el clobber del temp compartido).
    file_out = os.path.join(quizz_out_path, f"quiz_report_{uuid.uuid4().hex}.pdf")

    if generator is None:
        # Fallback: PDF generico de resumen (renderiza el shape uniforme del
        # motor; sirve para cualquier modelo creado via /rrhh/quizz/models).
        if evaluation is None:
            return 400, (
                f"No hay generador de PDF ni rubrica para el tipo de encuesta {tipo_op}"
            )
        try:
            from templates.controllers.rrhh.quizz_models_controller import (
                get_quizz_model_template_db,
            )
            from templates.forms.QuizzGenericReport import create_generic_quizz_report

            flag_model, _, model_row = get_quizz_model_template_db(tipo_op, data_token)
            model_name = (
                model_row[0]  # pyrefly: ignore
                if flag_model and model_row
                else f"Tipo {tipo_op}"
            )
            metadata = json_dict.get("metadata", {})
            create_generic_quizz_report(
                {
                    "path_file": file_out,
                    "title": model_name,
                    "folio": f"Encuesta {data.get('id') or 's/n'} / tipo {tipo_op}",
                    "metadata": {
                        "Empleado": metadata.get("name_emp"),
                        "Puesto": metadata.get("position"),
                        "Fecha": metadata.get("date"),
                        "Entrevistador": metadata.get("interviewer"),
                        "Modelo": f"{model_name} (tipo {tipo_op})",
                    },
                    "evaluation": evaluation,
                }
            )
            return 201, file_out
        except Exception as e:
            write_log_file(
                log_file_rh, f"Error al generar el pdf generico de quizz: {e}", data_token
            )
            return 400, "Error al generar el pdf"

    try:
        generator(
            data_raw,
            None,
            file_out,
            json_dict["metadata"]["name_emp"],
            json_dict["metadata"]["position"],
            "terminal",
            json_dict["metadata"]["admision"],
            json_dict["metadata"]["departure"],
            json_dict["metadata"]["date"],
            json_dict["metadata"]["interviewer"],
        )
        return 201, file_out
    except Exception as e:
        write_log_file(log_file_rh, f"Error al generar el pdf de quizz: {e}", data_token)
        return 400, "Error al generar el pdf"


def get_files_fichaje_shrpt():
    settings = json.load(open(filepath_settings, "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    folder_fichaje = settings["gui"]["RRHH"]["folder_checador"]
    code, files_fichaje = get_files_site(url_shrpt + folder_rrhh, folder_url=folder_fichaje)
    return code, files_fichaje


def download_fichaje_file(data):
    settings = json.load(open(filepath_settings, "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    download_path, code = download_files_site(
        url_shrpt + folder_rrhh, data["file_url"], data["temp"]
    )
    return download_path, code


def create_payroll_file_attachment_api(data, data_token):
    """Sube un archivo de nomina (pdf o xml) al bucket S3 de RH bajo
    payroll/<year>/<month>/<emp_id>/<filename> y registra la ruta en el
    indice files_data del empleado (files_data[year][month][key][pdf|xml])."""
    filename = data["filename"]
    filepath_down = data["filepath"]
    key = data["key"]
    # year/month normalizados: month a dos digitos 01-12
    try:
        emp_id = int(data["emp_id"])
        year = str(int(data["year"]))
        month = f"{int(data['month']):02d}"
    except (ValueError, TypeError) as e:
        return {"data": None, "msg": "year, month o emp_id invalidos", "error": str(e)}, 400
    # reconocer el tipo de archivo: solo pdf o xml
    file_extension = filename.split(".")[-1].lower()
    valid_extension = ["pdf", "xml"]
    if file_extension not in valid_extension:
        return {"data": None, "msg": "Formato de archivo no válido (solo pdf o xml)", "error": None}, 400
    # subir a S3: payroll/<year>/<month>/<emp_id>/<filename>
    path_aws = f"payroll/{year}/{month}/{emp_id}/{filename}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_RH_BUCKET")
    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=str(bucket_name), Key=path_aws)
    except FileNotFoundError:
        return {"data": None, "msg": "Local file not found"}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "AWS credentials not found"}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket does not exist: {bucket_name}"}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Access denied to bucket: {bucket_name}"}, 400
        else:
            return {"data": None, "msg": f"AWS error: {str(e)}"}, 400
    # registrar la ruta en el indice del empleado, agrupando pdf y xml por 'key'
    flag, error, result = get_payrolls(emp_id, data_token)
    has_record = (
        flag and isinstance(result, (list, tuple)) and len(result) > 0 and result[0] is not None
    )
    files_data = json.loads(result[0][1]) if has_record else {}  # pyrefly: ignore
    files_data.setdefault(year, {}).setdefault(month, {}).setdefault(key, {})
    files_data[year][month][key][file_extension] = path_aws
    flag, error, rows = update_payroll(files_data, emp_id, data_token)
    if not flag:
        return {
            "data": path_aws,
            "msg": "Archivo subido a S3 pero error al actualizar el indice",
            "error": error,
        }, 400
    msg = (
        f"Archivo de nomina {filename} ({file_extension}) subido para el empleado "
        f"{emp_id} en {year}/{month} (key {key})"
    )
    write_log_file(log_file_rh, msg, data_token)
    return {"data": path_aws, "msg": msg, "error": None}, 201


def create_mail_payroll(data):
    flags_daemons = json.load(open(filepath_daemons, "r"))
    if flags_daemons["update_files_nomina"]:
        msg = "Accion no permitida mientras se actualizan los datos."
        return 400, msg
    destinatarios = data["to"].split(";")
    asunto = data["subject"]
    cuerpo = data["body"]
    _from = data["from_"]
    settings = json.load(open(filepath_settings, "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    download_path_xml, code = download_files_site(url_shrpt + folder_rrhh, data["xml"])
    download_path_pdf, code = download_files_site(url_shrpt + folder_rrhh, data["pdf"])
    temp_files = [download_path_xml, download_path_pdf]
    response, code = create_mail_draft_with_attachment(
        data["emp_id"],
        _from,
        asunto,
        cuerpo,
        temp_files,
        to_recipients=destinatarios,
    )
    return code, response


def update_payroll_list_employees(data_token):
    flags_daemons = json.load(open(filepath_daemons, "r"))
    if flags_daemons["update_files_nomina"]:
        msg = "Accion no permitida mientras se actualizan los datos."
        return 400, msg
    flag, error, result = update_payroll_employees(data_token)
    msg = "Se han agregado correctamente:\n"
    counter = 0
    for item in result:
        if item[0]:
            counter += 1
    msg += f"{counter} empleados"
    msg += "\nLos siguientes no se han agregado:\n"
    for item in result:
        if not item[0] and "Duplicate entry" not in str(item[1]):
            msg += f"{item[2]}\n"
    return 200 if flag else 400, msg


def update_data_employee(data, data_token):
    data_dict = json.loads(data["data_dict"])
    flag, error, result = update_payroll(data_dict, data["id"], data_token)
    if flag:
        return 200, {"data": result, "msg": "Datos de nómina actualizados correctamente", "error": None}
    return 400, {"data": None, "msg": "No se pudieron actualizar los datos de nómina", "error": error}


def fetch_employees_without_records(data_token):
    # name, l_name, status, birthday, date_admission, employee_id
    flag, error, result = get_employees_without_records(data_token)
    if not flag:
        return 400, {"data": None, "msg": "No se pudieron obtener los empleados sin registros", "error": error}
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return 400, {"data": [], "msg": "No hay empleados sin registros", "error": None}
    out = []
    for item in result:
        birthday = (
            item[3]
            if isinstance(item[3], str) or item[3] is None or item[4] == "None"
            else item[3].strftime(format_date)
        )
        admission = (
            item[4]
            if isinstance(item[4], str) or item[4] is None or item[4] == "None"
            else item[4].strftime(format_date)
        )
        out.append(
            {
                "name": item[0].upper() + " " + item[1].upper(),
                "status": item[2],
                "birthday": birthday,
                "date_admission": admission,
                "emp_id": item[5],
            }
        )
    return 200, {"data": out, "msg": None, "error": None}


def fetch_medicals(data_token) -> tuple[dict, int]:
    flag, e, result = get_all_examenes(data_token)
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": [], "msg": "No hay registros médicos", "error": None}, 400
    if not flag:
        return {"data": [], "msg": "No se pudieron obtener los registros médicos", "error": None}, 400

    data_out = []
    messages = []

    # Definir límites por tipo de aptitud
    limits = {
        "APTO 1": timedelta(days=365),  # revisión anual
        "APTO 2": timedelta(days=180),  # revisión cada 6 meses
        "APTO 3": timedelta(days=90),  # revisión cada 3 meses
        "APTO 4": None,  # NO APTO
    }

    warning_threshold = timedelta(days=30)

    for row in result:
        (
            id_exam,
            nombre,
            sangre,
            status,
            aptitud,
            fechas,
            apt_actual,
            emp_id,
            extra_info,
        ) = row

        extra_info = json.loads(extra_info)
        aptitudes = json.loads(aptitud)
        dates = json.loads(fechas)

        # Última fecha registrada
        last_date = None
        if dates:
            last_date = datetime.strptime(max(dates), format_timestamps)

        exam_data = {
            "exist": True,
            "id_exam": id_exam,
            "name": nombre,
            "blood": sangre,
            "status": status if status is not None else "INACTIVO",
            "aptitudes": aptitudes,
            "dates": dates,
            "apt_last": apt_actual,
            "emp_id": emp_id,
            "allergies": extra_info.get("allergies", ""),
            "observations": extra_info.get("observations", ""),
        }
        data_out.append(exam_data)

        # Validación de fechas según aptitud
        if apt_actual in limits and limits[apt_actual] is not None and last_date:
            delta = datetime.now() - last_date
            limite = limits[apt_actual]
            if limite is None:
                continue

            if delta > limite:
                # Mensaje crítico
                messages.append(
                    f"[CRÍTICO] El empleado {nombre} requiere revisión: "
                    f"Aptitud {apt_actual}, última fecha {last_date.strftime(format_timestamps)}, "
                    f"supera el límite de {limite.days} días."
                )
            elif limite - delta <= warning_threshold:
                # Mensaje de aviso
                remaining = limite - delta
                messages.append(
                    f"[AVISO] El empleado {nombre} está próximo a revisión: "
                    f"Aptitud {apt_actual}, última fecha {last_date.strftime(format_timestamps)}, "
                    f"faltan {remaining.days} días para el límite de {limite.days} días."
                )

        elif apt_actual == "APTO 4":
            messages.append(
                f"[CRÍTICO] El empleado {nombre} (ID {id_exam}) está marcado como NO APTO."
            )

    return {"data": data_out, "msg": None, "error": messages if messages else None}, 200


def fetch_medical_employee(id_emp, data_token):
    flag, e, result = get_all_examenes(data_token)
    if not flag or not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": None, "msg": "No se pudo obtener el registro médico", "error": None}, 400
    for row in result:
        id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id, _extra = row
        if str(emp_id) == id_emp:
            return {
                "data": {
                    "exist": True,
                    "id_exam": id_exam,
                    "name": nombre,
                    "blood": sangre,
                    "status": status,
                    "aptitudes": aptitud,
                    "dates": fechas,
                    "apt_last": apt_actual,
                    "emp_id": emp_id,
                },
                "msg": None,
                "error": None,
            }, 200
    return {"data": {"exist": False}, "msg": None, "error": None}, 200
