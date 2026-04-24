# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/abr./2024  at 11:38 $"

import json

from static.constants import format_date, quizzes_dir_path
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.employees.employees_controller import (
    get_all_data_employees,
    get_all_data_employee,
)
from templates.controllers.employees.vacations_controller import (
    get_vacations_data,
    get_vacations_data_emp,
)
from templates.controllers.misc.tasks_controller import (
    create_task,
    update_task,
    delete_task,
)


def get_info_employees_with_status(status: str):
    flag, error, result = get_all_data_employees(status)
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


def create_csv_file_employees(status: str):
    flag, error, result = get_all_data_employees(status)
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"error": "No se encontraron empleados"}, 400
    result = result if flag else []
    # create file
    filepath = "files/emp.csv"
    with open(filepath, "w") as file:
        file.write(
            "id,name,phone,department,modality,email,contract,admission,rfc,curp,nss,emergency,position,status,departure,exam_id,birthday,legajo\n"
        )
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
            ) = item
            file.write(
                f"{id_emp},{name},{phone},{department},{modality},{email},{contract},{admission},{rfc},{curp},{nss},{emergency_contact},{position},{status},{departure},{examen},{birthday},{legajo}\n"
            )
    return filepath


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
        "admission": admission.strftime(format_date),
        "rfc": rfc,
        "curp": curp,
        "nss": nss,
        "emergency": emergency_contact,
        "position": position,
        "status": status,
        "departure": departure,
        "exam_id": examen,
        "birthday": birthday.strftime(format_date),
        "legajo": legajo,
        "dep_id": dep_id,
    }
    return (data_out, 200) if flag else ({}, 400)


def get_vacations_employee(emp_id: int, data_token):
    flag, error, result = get_vacations_data_emp(emp_id, data_token)
    out = None
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"error": "No se encontraron vacaciones para el empleado"}, 400
    if not flag or len(result) == 0:
        return out, 400
    seniority_raw = json.loads(result[4])
    seniority = [
        {
            "year": int(k),
            "status": v["status"],
            "comentarios": v["comentarios"],
            "prima": v["prima"],
        }
        for k, v in seniority_raw.items()
    ]
    out = {
        "emp_id": result[0],
        "name": result[1].upper() + " " + result[2].upper(),
        "date_admission": result[3].strftime(format_date),
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
        seniority_raw = json.loads(item[4])
        seniority = [
            {
                "year": int(k),
                "status": v["status"],
                "comentarios": v["comentarios"],
                "prima": v["prima"],
                "dates": v.get("dates", []),
            }
            for k, v in seniority_raw.items()
        ]
        out.append(
            {
                "emp_id": item[0],
                "name": item[1].upper() + " " + item[2].upper(),
                "date_admission": item[3],
                "seniority": seniority,
            }
        )

    return out, 200


def create_task_from_api(data, data_token):
    quizzes_dir = json.load(open(quizzes_dir_path, encoding="utf-8"))
    dict_quizz = json.load(
        open(
            quizzes_dir[str(data["metadata"]["type_quizz"])]["path"],
            encoding="utf-8",
        )
    )
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
        return {"msg": f"Ok-->{msg}"}, 201
    else:
        print(error)
        return {"msg": "Ok", "data": str(error)}, 400


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
        return {"msg": f"Ok-->{msg}"}, 200
    else:
        return {"msg": "Fail", "data": str(error)}, 400


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
        return {"msg": f"Ok-->{msg}"}, 200
    else:
        return {"msg": "Fail", "data": str(error)}, 400
