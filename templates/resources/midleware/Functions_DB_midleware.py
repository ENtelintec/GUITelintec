# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/abr./2024  at 11:38 $"

import csv
import io
import json

from static.constants import format_date
from templates.controllers.rrhh.quizz_models_controller import (
    get_quizz_model_template_db,
)
from templates.controllers.employees.em_controller import get_all_examenes
from templates.controllers.employees.employees_controller import (
    get_all_data_employee,
    get_all_data_employees,
    get_employees_directory,
)
from templates.controllers.employees.vacations_controller import (
    get_vacations_data,
    get_vacations_data_emp,
)
from templates.controllers.misc.tasks_controller import (
    create_task,
    delete_task,
    update_task,
)
from templates.Functions_Utils import create_notification_permission_notGUI


def get_info_employees_with_status(status: str, data_token=None):
    flag, error, result = get_all_data_employees(status, data_token)
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"error": "No se encontraron empleados"}, 400
    data_out = []
    for item in result:
        (
            id_emp,
            name,
            lastname,
            phone,
            department,
            modality,
            email,
            contract,
            admission,
            rfc,
            curp,
            nss,
            emergency_contact,
            position,
            status,
            departure,
            examen,
            birthday,
            legajo,
            extra_info,
            dep_id,
            username,
        ) = item
        extra_info = json.loads(extra_info)
        data_out.append(
            {
                "id": id_emp,
                "name": name.upper(),
                "lastname": lastname.upper(),
                "phone": phone,
                "dep": department,
                "modality": modality,
                "email": email,
                "contract": contract,
                "admission": admission
                if admission is None or isinstance(admission, str)
                else admission.strftime(format_date),
                "rfc": rfc,
                "curp": curp,
                "nss": nss,
                "emergency": emergency_contact,
                "position": position,
                "status": status,
                "departure": departure,
                "exam_id": examen,
                "birthday": birthday
                if birthday is None or isinstance(birthday, str)
                else birthday.strftime(format_date),
                "legajo": legajo,
                "id_leader": extra_info.get("id_leader", 0),
                "dep_id": dep_id,
                "username": username,
            }
        )

    return (data_out, 200) if flag else ([], 400)


def get_employees_directory_with_status(status: str, data_token):
    flag, error, result = get_employees_directory(status, data_token)
    if not flag or not isinstance(result, (list, tuple)):
        return {
            "data": [],
            "msg": "No se pudieron obtener los empleados",
            "error": error,
        }, 400
    data_out = []
    for item in result:
        (
            id_emp,
            name,
            lastname,
            phone,
            department,
            modality,
            email,
            contract,
            position,
            status_emp,
            extra_info,
            dep_id,
            username,
        ) = item
        extra_info = json.loads(extra_info) if extra_info else {}
        data_out.append(
            {
                "id": id_emp,
                "name": name.strip().upper() if name else name,
                "lastname": lastname.strip().upper() if lastname else lastname,
                "phone": phone,
                "email": email,
                "dep": department,
                "dep_id": dep_id,
                "contract": contract,
                "position": position,
                "status": status_emp,
                "id_leader": extra_info.get("id_leader", 0),
                "modality": modality,
                "username": username,
            }
        )
    if len(data_out) == 0:
        return {"data": [], "msg": "No se encontraron empleados", "error": None}, 200
    return {"data": data_out, "msg": None, "error": None}, 200


def _csv_buffer(header: list, rows: list) -> io.BytesIO:
    # CSV en memoria: sin archivo compartido entre requests ni rutas relativas.
    # csv.writer entrecomilla los valores con coma, comilla o salto de linea;
    # NULL sale vacio (antes se imprimia "None").
    text = io.StringIO()
    writer = csv.writer(text, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(["" if value is None else value for value in row])
    return io.BytesIO(text.getvalue().encode("utf-8"))


def create_csv_file_employees(status: str, data_token=None):
    flag, error, result = get_all_data_employees(status, data_token)
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": None, "msg": "No se encontraron empleados", "error": error}, 400
    result = result if flag else []
    header = [
        "id", "name", "phone", "department", "modality", "email", "contract", "admission",
        "rfc", "curp", "nss", "emergency", "position", "status", "departure", "exam_id",
        "birthday", "legajo", "l_name",
    ]
    rows = []
    for item in result:
        (
            id_emp,
            name,
            lastname,
            phone,
            department,
            modality,
            email,
            contract,
            admission,
            rfc,
            curp,
            nss,
            emergency_contact,
            position,
            status,
            departure,
            examen,
            birthday,
            legajo,
            extra_info,
            department_id,
            usernames,
        ) = item
        # `l_name` al final: las 18 columnas de antes no cambian de posicion.
        rows.append(
            [
                id_emp, name, phone, department, modality, email, contract, admission, rfc,
                curp, nss, emergency_contact, position, status, departure, examen, birthday,
                legajo, lastname,
            ]
        )
    return _csv_buffer(header, rows)


def create_csv_file_medical(data_token):
    flag, error, result = get_all_examenes(data_token)
    if not flag or not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": None, "msg": "Error al obtener los datos del empleado", "error": error}, 400
    header = ["id_exam", "nombre", "sangre", "estatus", "aptitudes", "fechas", "apt_actual", "emp_id"]
    rows = []
    for item in result:
        id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id, _extra = item
        rows.append([id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id])
    return _csv_buffer(header, rows)


def create_csv_file_vacations(data_token):
    flag, error, result = get_vacations_data(data_token)
    if not flag or not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": None, "msg": "Error al obtener los datos del empleado", "error": error}, 400
    header = ["emp_id", "Nombre", "Apellido", "fecha_inicio", "body"]
    rows = []
    for item in result:
        emp_id, name, l_name, date_admission, seniority, _renovacion = item
        rows.append([emp_id, name, l_name, date_admission, seniority])
    return _csv_buffer(header, rows)


def get_info_employee_id(id_emp: int, data_token):
    flag, error, result = get_all_data_employee(id_emp, data_token)
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"error": "No se encontro el empleado"}, 400
    (
        id_emp,
        name,
        lastname,
        phone,
        department,
        modality,
        email,
        contract,
        admission,
        rfc,
        curp,
        nss,
        emergency_contact,
        position,
        status,
        departure,
        examen,
        birthday,
        legajo,
        dep_id,
    ) = result
    data_out = {
        "id": id_emp,
        "name": name.upper() + " " + lastname.upper(),
        "phone": phone,
        "dep": department,
        "modality": modality,
        "email": email,
        "contract": contract,
        "admission": admission
        if admission is None or isinstance(admission, str)
        else admission.strftime(format_date),
        "rfc": rfc,
        "curp": curp,
        "nss": nss,
        "emergency": emergency_contact,
        "position": position,
        "status": status,
        "departure": departure,
        "exam_id": examen,
        "birthday": birthday
        if birthday is None or isinstance(birthday, str)
        else birthday.strftime(format_date),
        "legajo": legajo,
        "dep_id": dep_id,
    }
    return (data_out, 200) if flag else ({}, 400)


_PRIMA_DEFAULT = {"status": "No", "fecha_pago": ""}  # defaults de PrimaVacForm


def _seniority_list(raw) -> list:
    # Tolerante a periodos sin `prima`/`dates` (el alta por API no guardaba
    # `prima` hasta 2026-10-09; un registro asi tumbaba los GET con KeyError).
    seniority_raw = json.loads(raw) if raw else {}
    return [
        {
            "year": int(k),
            "status": v.get("status", ""),
            "comentarios": v.get("comentarios", ""),
            "prima": v.get("prima") or dict(_PRIMA_DEFAULT),
            "dates": v.get("dates", []),
        }
        for k, v in seniority_raw.items()
    ]


def get_vacations_employee(emp_id: int, data_token):
    flag, error, result = get_vacations_data_emp(emp_id, data_token)
    out = None
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"error": "No se encontraron vacaciones para el empleado"}, 400
    if not flag or len(result) == 0:
        return out, 400
    seniority = _seniority_list(result[4])
    out = {
        "emp_id": result[0],
        "name": result[1].upper() + " " + result[2].upper(),
        "date_admission": result[3]
        if result[3] is None or isinstance(result[3], str)
        else result[3].strftime(format_date),
        "seniority": seniority,
    }
    return out, 200


def get_all_vacations(data_token):
    flag, error, result = get_vacations_data(data_token)
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"error": "No se encontraron vacaciones"}, 400
    out = []
    if not flag or len(result) == 0:
        return [], 400
    for item in result:
        seniority = _seniority_list(item[4])
        out.append(
            {
                "emp_id": item[0],
                "name": item[1].upper() + " " + item[2].upper(),
                "date_admission": item[3]
                if isinstance(item[3], str) or item[3] is None
                else item[3].strftime(format_date),
                "seniority": seniority,
            }
        )

    return out, 200


def create_task_from_api(data, data_token):
    # Template y status desde la BD (quizz_models). Solo un modelo ACTIVO (1)
    # recibe encuestas: borrador no esta listo y archivada ya no se aplica.
    type_quizz = data["metadata"].get("type_quizz")
    flag, error, row = get_quizz_model_template_db(type_quizz, data_token)
    if not flag:
        return {"data": None, "msg": "Error al consultar el modelo de encuesta", "error": error}, 400
    if not row:
        return {
            "data": None,
            "msg": f"No existe el modelo de encuesta {type_quizz}",
            "error": None,
        }, 400
    status_model = row[2]  # pyrefly: ignore
    if int(status_model or 0) != 1:
        return {
            "data": None,
            "msg": (
                f"El modelo de encuesta {type_quizz} no está activo: "
                "no se pueden crear encuestas de este tipo"
            ),
            "error": None,
        }, 400
    dict_quizz = row[1]  # pyrefly: ignore
    if isinstance(dict_quizz, str):
        dict_quizz = json.loads(dict_quizz)
    flag, error, result = create_task(
        data["title"],
        data["emp_destiny"],
        data["emp_origin"],
        data["date_limit"],
        data["metadata"],
        dict_quizz,
        data_token,
    )
    if flag:
        msg = f"Se creo una tarea ({result}) {data['title']} para {data['metadata']['name_emp']}"
        create_notification_permission_notGUI(
            msg, data_token,
            ["RRHH"],
            "Nuevo tarea quizz creada",
            data["emp_origin"],
            data["emp_destiny"],
        )
        return {"data": {"id_task": result}, "msg": f"Tarea creada correctamente (ID {result})", "error": None}, 201
    else:
        print(error)
        return {"data": None, "msg": "No se pudo crear la tarea", "error": error}, 400


def update_task_from_api(data, data_token):
    data_raw = (
        json.loads(data["data_raw"])
        if isinstance(data["data_raw"], str)
        else data["data_raw"]
    )
    flag, error, result = update_task(
        data["id"], data["body"], data_raw=data_raw, data_token=data_token
    )
    if flag:
        msg = f"Se actualizo la tarea {data['body']['title']} para {data['body']['metadata']['name_emp']}"
        create_notification_permission_notGUI(
            msg, data_token,
            ["RRHH"],
            "Tarea quizz actualizada",
            data["body"]["emp_origin"],
            data["body"]["emp_destiny"],
        )
        return {"data": {"id_task": data["id"]}, "msg": f"Tarea actualizada correctamente (ID {data['id']})", "error": None}, 200
    else:
        return {"data": None, "msg": "No se pudo actualizar la tarea", "error": error}, 400


def delete_task_from_api(data, data_token):
    flag, error, result = delete_task(data["id"], data_token)
    if flag:
        msg = f"Se elimino la tarea {data['id']}"
        create_notification_permission_notGUI(
            msg, data_token,
            ["RRHH"],
            "Tarea quizz eliminada",
            data_token.get("emp_id"),
            0,
        )
        return {"data": {"id_task": data["id"]}, "msg": f"Tarea eliminada correctamente (ID {data['id']})", "error": None}, 200
    else:
        return {"data": None, "msg": "No se pudo eliminar la tarea", "error": error}, 400
