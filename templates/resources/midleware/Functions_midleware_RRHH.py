# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/jun./2024  at 16:28 $"

import json
import zipfile
from datetime import datetime

import pandas as pd
import pytz

from static.constants import (
    patterns_files_fichaje,
    cache_file_emp_fichaje,
    format_date_fichaje_file,
    index_file_nominas,
    timezone_software,
    quizzes_temp_pdf,
    filepath_daemons,
    filepath_settings,
    file_temp_zip,
    format_timestamps,
    conversion_quizzes_path,
    filepath_recommendations,
    format_date,
    filepath_fichaje_temp,
    cache_file_resume_fichaje_path,
)
from templates.Functions_Sharepoint import (
    get_files_site,
    download_files_site,
    create_mail_draft_with_attachment,
)
from templates.controllers.employees.em_controller import (
    get_employees_without_records,
    get_all_examenes,
    insert_new_exam_med,
    update_aptitud_renovacion,
)
from templates.controllers.employees.employees_controller import (
    new_employee,
    update_employee,
)
from templates.controllers.employees.vacations_controller import (
    insert_vacation,
    update_registry_vac,
)
from templates.controllers.misc.tasks_controller import (
    get_all_tasks_by_status,
    update_task,
)
from templates.controllers.payroll.payroll_controller import (
    get_payrolls,
    update_payroll,
    update_payroll_employees,
)
from templates.misc.Functions_AuxFiles import (
    get_events_op_date,
    get_pairs_nomina_docs,
    get_data_xml_file_nomina,
)
from templates.misc.Functions_Files import (
    extract_fichajes_file,
    check_names_employees_in_cache,
    get_info_f_file_name,
    get_info_t_file_name,
    get_info_bitacora,
    unify_data_employee,
    get_fichajes_resume_cache,
)
from templates.misc.Functions_Files_RH import check_fichajes_files_in_directory

import os


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


def create_new_employee_db(data):
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
        data["info"]["id_leader"],
    )
    if flag:
        return {"data": str(result)}, 201
    else:
        return {"error": str(error)}, 400


def update_employee_db(data):
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
        data["info"]["id_leader"],
    )
    if flag:
        return {"data": str(result)}, 200
    else:
        return {"error": str(error)}, 400


def get_files_fichaje():
    flag, files = check_fichajes_files_in_directory(patterns_files_fichaje)
    if not flag:
        return False, files
    files_list = [v for k, v in files.items()]
    return True, files_list


def fetch_fichajes_all_employees():
    fichajes_resume, flag = get_fichajes_resume_cache(
        cache_file_resume_fichaje_path, is_hard_update=True
    )
    if not flag:
        return {"msg": "Error al obtener fichajes", "data": []}, 400
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
    out = {"data": out_aux, "msg": "Ok"}
    return out, 200


def fetch_fichaje_employee(id_emp):
    fichajes_resume, flag = get_fichajes_resume_cache(
        cache_file_resume_fichaje_path, is_hard_update=True
    )
    if not flag:
        return {"msg": "Error al obtener fichajes", "data": None}, 400
    out = {}
    code = 400
    for item in fichajes_resume:
        if str(item[0]) == id_emp:
            out = {
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
            code = 200
            break
    return out, code


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
                names_and_ids = check_names_employees_in_cache(
                    names_list, cache_file_emp_fichaje
                )
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
                coldata.append({"text": col, "stretch": True})
            names_list = dft["name"].unique().tolist()
            names_and_ids = check_names_employees_in_cache(
                names_list, cache_file_emp_fichaje
            )
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


def get_data_name_fichaje(
    name: str, dff, dfb, clocks, window_time_in, window_time_out, dft=None
):
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
    date_example = (
        pd.to_datetime(worked_days_f[0][0]) if len(worked_days_f) > 0 else date
    )
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
    list_normal_data = [
        {"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in normal_data_emp.items()
    ]
    list_absence_data = [
        {"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in absence_data_emp.items()
    ]
    list_primer_data = [
        {"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in prime_data_emp.items()
    ]
    list_late_data = [
        {"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in late_data_emp.items()
    ]
    list_extra_data = [
        {"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in extra_data_emp.items()
    ]
    list_early_data = [
        {"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
        for k, v in early_data_emp.items()
    ]
    list_pasive_data = [
        {"timestamp": k, "value": v[0], "comment": v[1], "timestamps_extra": v[2]}
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
    files = data.get("files")
    clock_h = ClockFichajeHours(data.get("time_in"))
    clock_m = ClockFichajeMinutes(data.get("time_in"))
    clock_h_out = ClockFichajeHours(data.get("time_out"))
    clock_m_out = ClockFichajeMinutes(data.get("time_out"))
    grace_in = GraceMinutes(data.get("grace_init"))
    grace_out = GraceMinutes(data.get("grace_end"))
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
            return code, path
        flag, data_file = get_data_file(filepath_fichaje_temp, file["report"])
        if not flag:
            return 400, data_file
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
    return 200, data_out


def upload_nomina_doc(data):
    pass
    return 200, None


def update_files_data_nominas(key: str, paths_pdf_xml: dict, data_xml: dict):
    flag, error, result = get_payrolls(data_xml["emp_id"])
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


def update_data_docs_nomina(patterns=None, use_index=False):
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
                    download_path, code = download_files_site(
                        url_shrpt + folder_rrhh, v["xml"]
                    )
                else:
                    print(f"Not pass the filter {folder_patterns}", v["xml"])
                    continue
            else:
                download_path, code = download_files_site(
                    url_shrpt + folder_rrhh, v["xml"]
                )
        else:
            print(f"Not pass the filter {folder_patterns}", v["xml"])
            continue
        if code != 200:
            results.append(
                (False, f"Error al descargar el archivo XML: {download_path}", None)
            )
            continue
        data_file = get_data_xml_file_nomina(download_path)
        if data_file["emp_id"] is None:
            print(f"No se encontro el empleado con datos {data_file['emp_name']}")
            results.append(
                (False, f"No se encontro el empleado: {data_file['emp_name']}", None)
            )
            continue
        data_emps[data_file["emp_id"]], flag = update_files_data_nominas(
            k, v, data_file
        )
        if flag:
            flag, error, result = update_payroll(
                data_emps[data_file["emp_id"]], data_file["emp_id"]
            )
            results.append((flag, error, result))
        else:
            results.append((False, "Error al generar dict de empleado", None))
    return results


def download_nomina_docs(data):
    settings = json.load(open(filepath_settings, "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    download_path_pdf, code1 = download_files_site(url_shrpt + folder_rrhh, data["pdf"])
    download_path_xml, code2 = download_files_site(url_shrpt + folder_rrhh, data["xml"])
    with zipfile.ZipFile(file_temp_zip, "w") as zipf:
        if code1 == 200:
            name_file = os.path.basename(download_path_pdf)
            zipf.write(download_path_pdf, arcname=name_file)
        if code2 == 200:
            name_file = os.path.basename(download_path_xml)
            zipf.write(download_path_xml, arcname=name_file)
    code = 200 if os.path.exists(file_temp_zip) else 400
    return file_temp_zip, code


def get_files_list_nomina_RH(emp_id):
    flag, error, result = get_payrolls(emp_id)
    dicts_data = []
    for item in result:
        emp_id = int(item[0])
        name = f"{item[2].upper()} {item[3].upper()}"
        dict_data = json.loads(item[1])
        dicts_data.append({"id": emp_id, "name": name, "data": dict_data})
    return 200, dicts_data


def get_files_list_nomina(emp_id):
    flag, error, result = get_payrolls(emp_id)
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
    return 200, files


def insert_medical_db(data):
    flag, error, result = insert_new_exam_med(
        data["info"]["name"],
        data["info"]["blood"],
        data["info"]["status"],
        data["info"]["aptitudes"],
        data["info"]["dates"],
        data["info"]["apt_actual"],
        data["info"]["emp_id"],
    )
    if flag:
        return {"data": str(result)}, 201
    else:
        return {"error": str(error)}, 400


def update_medical_db(data):
    apt_actual = (
        data["info"]["aptitudes"][-1] if len(data["info"]["aptitudes"]) > 0 else 0
    )
    flag, error, result = update_aptitud_renovacion(
        data["info"]["aptitudes"],
        data["info"]["dates"],
        apt_actual,
        exam_id=data["id"],
    )
    if flag:
        return {"data": str(result)}, 200
    else:
        return {"error": str(error)}, 400


def insert_new_vacation(data):
    seniority_dict = {}
    for item in data["seniority"]:
        seniority_dict[str(item["year"])] = {
            "status": item["status"],
            "comentarios": item["comentarios"],
            "dates": item.get("dates", []),
        }
    if not len(seniority_dict) > 0:
        return False, "No hay informacion que insertar", None
    flag, error, result = insert_vacation(data["emp_id"], seniority_dict)
    return flag, error, result


def update_vacation(data):
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
    flag, error, result = update_registry_vac(data["emp_id"], seniority_dict)
    return flag, error, result


def get_all_quizzes():
    flag, error, tasks = get_all_tasks_by_status(status=-1, title="quizz")
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


def recommendations_results_quizzes(dict_results: dict, tipo_q: int):
    # Asumiendo que tienes la ruta correcta en filepath_recommendations
    dict_conversions_recomen = json.load(
        open(filepath_recommendations, encoding="utf-8")
    )
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

    # Aquí necesitas modificar el código según cómo desees manejar las recomendaciones de dominio y categoría
    # dado que en tu JSON 'c_dom_r' es solo una cadena, puedes necesitar un enfoque diferente o más información
    # Si 'c_dom_r' debería ser una estructura similar a 'c_final_r', ajusta tu JSON y tu código en consecuencia

    # Acceder a las recomendaciones de categoría
    if cat_score in dict_conversions_recomen["c_cat_r"]:
        dict_recommendations["c_cat_r"] = dict_conversions_recomen["c_cat_r"][cat_score]
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


def generate_pdf_from_json(data):
    from static.FramesClasses import dict_typer_quizz_generator

    json_dict = data["body"]
    file_out = quizzes_temp_pdf
    tipo_op = json_dict["metadata"]["type_quizz"]
    is_update = True

    generator = dict_typer_quizz_generator[tipo_op]
    data_raw = (
        json.loads(data["data_raw"])
        if isinstance(data["data_raw"], str)
        else data["data_raw"]
    )
    if "results" not in data_raw.keys():
        dict_results = calculate_results_quizzes(data_raw, tipo_op)
        data_raw["results"] = dict_results
        is_update = False
    if "recommendations" not in data_raw.keys():
        dict_recomendations = recommendations_results_quizzes(
            data_raw["results"], tipo_op
        )
        data_raw["recommendations"] = dict_recomendations
        is_update = False
    if not is_update:
        flag, error, result = update_task(data["id"], data["body"], data_raw=data_raw)
        if not flag:
            print("Error al actualizar el task", error, result)
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
        print("Error al generar el pdf", e)
        return 400, "Error al generar el pdf"


def get_files_fichaje_shrpt():
    settings = json.load(open(filepath_settings, "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    folder_fichaje = settings["gui"]["RRHH"]["folder_checador"]
    code, files_fichaje = get_files_site(
        url_shrpt + folder_rrhh, folder_url=folder_fichaje
    )
    return code, files_fichaje


def download_fichaje_file(data):
    settings = json.load(open(filepath_settings, "r"))
    url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
    folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
    download_path, code = download_files_site(
        url_shrpt + folder_rrhh, data["file_url"], data["temp"]
    )
    return download_path, code


def update_files_payroll(data):
    quincena = data["quincena"]
    quincena = quincena if quincena != "" else None
    patterns = [data["year"], data["month"], quincena]
    from templates.daemons.Files_handling import UpdaterSharepointNomina

    thread_update = UpdaterSharepointNomina(patterns)
    thread_update.start()
    flags_daemons = json.load(open(filepath_daemons, "r"))
    flags_daemons["update_files_nomina"] = True
    with open(filepath_daemons, "w") as f:
        json.dump(flags_daemons, f)
    # json.dump(flags_daemons, open(filepath_daemons, "w"))
    return (
        200,
        f"Proceso de actualizacion iniciado y puede llegar a tardar minutos. Patrones tomados en cuenta {patterns}",
    )


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


def update_payroll_list_employees():
    flags_daemons = json.load(open(filepath_daemons, "r"))
    if flags_daemons["update_files_nomina"]:
        msg = "Accion no permitida mientras se actualizan los datos."
        return 400, msg
    flag, error, result = update_payroll_employees()
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


def update_data_employee(data):
    data_dict = json.loads(data["data_dict"])
    flag, error, result = update_payroll(data_dict, data["id"])
    return (
        (200, {"data": result, "msg": "ok"})
        if flag
        else (400, {"data": None, "msg": str(error)})
    )


def fetch_employees_without_records():
    # name, l_name, status, birthday, date_admission, employee_id
    flag, error, result = get_employees_without_records()
    if not flag:
        return 400, {"data": None, "msg": str(error)}
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
    return 200, {"data": out, "msg": "ok"}


def fetch_medicals():
    flag, e, result = get_all_examenes()
    out = {"data": None}
    if not flag:
        out = {"data": []}
        code = 400
        return out, code
    data_out = []
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
        data_out.append(
            {
                "exist": True,
                "id_exam": id_exam,
                "name": nombre,
                "blood": sangre,
                "status": status if status is not None else "INACTIVO",
                "aptitudes": json.loads(aptitud),
                "dates": json.loads(fechas),
                "apt_last": apt_actual,
                "emp_id": emp_id,
                "alergies": extra_info.get("alergies", ""),
                "observations": extra_info.get("observations", ""),
            }
        )
    out["data"] = data_out
    return out, 200


def fetch_medical_employee(id_emp):
    flag, e, result = get_all_examenes()
    out = {"exist": False, "data": None}
    if not flag:
        return out, 400
    for row in result:
        id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = row
        if str(emp_id) == id_emp:
            out = {
                "exist": True,
                "id_exam": id_exam,
                "name": nombre,
                "blood": sangre,
                "status": status,
                "aptitudes": aptitud,
                "dates": fechas,
                "apt_last": apt_actual,
                "emp_id": emp_id,
            }
            break
    return out, 200
