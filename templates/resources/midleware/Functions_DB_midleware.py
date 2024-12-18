# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/abr./2024  at 11:38 $"

import json
import os
import tempfile
from datetime import datetime, timedelta

import pandas as pd

from static.constants import format_date
from templates.controllers.employees.employees_controller import (
    get_all_data_employees,
    get_all_data_employee,
)
from templates.controllers.employees.vacations_controller import (
    get_vacations_data,
    get_vacations_data_emp,
)
from templates.controllers.material_request.sm_controller import (
    get_sm_by_id,
    get_info_names_by_sm_id,
)
from templates.forms.Materials import MaterialsRequest


def check_date_difference(date_modify, delta):
    flag = True
    date_now = datetime.now()
    date_modify = (
        datetime.strptime(date_modify, format_date)
        if isinstance(date_modify, str)
        else date_modify
    )
    date_modify = (
        date_modify.date() if isinstance(date_modify, datetime) else date_modify
    )
    # week of the month
    week_modify = date_modify.isocalendar()[1]
    date_now = date_now.date()
    week_now = date_now.isocalendar()[1]
    date_modify = date_modify + timedelta(days=delta)
    if week_now - week_modify > 1:
        flag = False
    return flag


""" --------------------------------------API RRHH----------------------------------------------------------"""


def get_info_employees_with_status(status: str):
    flag, error, result = get_all_data_employees(status)
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
        ) = item
        data_out.append(
            {
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
                "legajo": legajo,
            }
        )

    return (data_out, 200) if flag else ([], 400)


def create_csv_file_employees(status: str):
    flag, error, result = get_all_data_employees(status)
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
            ) = item
            file.write(
                f"{id_emp},{name},{phone},{department},{modality},{email},{contract},{admission},{rfc},{curp},{nss},{emergency_contact},{position},{status},{departure},{examen},{birthday},{legajo}\n"
            )
    return filepath


def get_info_employee_id(id_emp: int):
    flag, error, result = get_all_data_employee(id_emp)
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
    ) = result
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
        "legajo": legajo,
    }
    return (data_out, 200) if flag else ({}, 400)


def get_vacations_employee(emp_id: int):
    flag, error, result = get_vacations_data_emp(emp_id)
    out = None
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
        "date_admission": result[3],
        "seniority": seniority,
    }
    return out, 200


def get_all_vacations():
    flag, error, result = get_vacations_data()
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
