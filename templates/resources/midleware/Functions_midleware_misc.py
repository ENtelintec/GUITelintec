# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 10:34 $"

import json
import pickle
from datetime import datetime

import pytz

from static.constants import (
    filepath_settings,
    format_timestamps,
    timezone_software,
    format_date,
)
from templates.Functions_openAI import get_response_assistant, get_files_list_openai
from templates.controllers.employees.vacations_controller import get_vacations_data
from templates.controllers.material_request.sm_controller import get_pending_sm_db
from templates.controllers.misc.tasks_controller import get_task_by_id_emp
from templates.controllers.notifications.Notifications_controller import (
    get_notifications_by_user,
    get_notifications_by_permission,
)


def get_all_notification_db_user_status(id_emp, status):
    code = 200
    flag, error, result = get_notifications_by_user(id_emp, status)
    data_out = []
    for item in result:
        body = json.loads(item[2])
        body["id"] = item[1]
        data_out.append(body)
    return code if flag else 400, data_out if flag else error


def get_all_notification_db_permission(status, data_token):
    code = 200
    permissions = data_token.get("permissions", {})
    terms_list = [item.split(".")[-1].lower() for item in permissions.values()]
    flag, error, result = get_notifications_by_permission(
        terms_list, data_token.get("emp_id", "%"), status
    )
    data_out = []
    for item in result:
        body = json.loads(item[2])
        body["id"] = item[1]
        data_out.append(body)
    return code if flag else 400, data_out if flag else error


def get_files_openai(department: str) -> list:
    try:
        with open(f"files/files_{department}_openAI_cache.pkl", "rb") as f:
            files_open_ai = pickle.load(f)
        files_open_ai_online, error = get_files_list_openai()
        if len(files_open_ai) > 0:
            for file in files_open_ai:
                if file["department"] != department:
                    files_open_ai.remove(file)
    except Exception as e:
        files_open_ai = []
        files_open_ai_online = []
        print(e)
    for i, file in enumerate(files_open_ai):
        for file_online in files_open_ai_online:
            if file["name"] == file_online.filename:
                if file_online.status == "processed":
                    files_open_ai[i]["status"] = "uploaded"
                else:
                    files_open_ai[i]["status"] = "pending"
                print(file["name"])
                break
    return files_open_ai


def get_response_AV(
    department: str, msg: str, files_av: list, filename: str, id_chat=None
):
    id_chat = id_chat if id_chat is not None else 0
    settings = json.load(open(filepath_settings))
    instructions = (
        f"Act as an Virtual Assistant, you work aiding in a telecomunications enterprise called Telintec.\n "
        f"You help in the {department} and you answer are concise and precise.\n"
        f"Ask for clarification if a user request is ambiguous\n."
        f"You answer in {settings['language']}."
    )
    files_av, res = get_response_assistant(
        msg, filename, files_av, instructions, department
    )
    print("Responge assistant gpt api: ", res)
    return files_av, res, id_chat


def get_task_by_id_employee(id_emp: int):
    flag, error, result = get_task_by_id_emp(id_emp)
    if flag:
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
        return data_out, 200
    else:
        return [str(error, result)], 400


def get_all_vacations_data_date():
    flag, error, result = get_vacations_data()
    if not flag:
        return error, 400
    time_zone = pytz.timezone(timezone_software)
    date_today = datetime.now(pytz.utc).astimezone(time_zone)
    date_today.replace(day=1)
    out = []
    for item in result:
        seniority_raw = json.loads(item[4])
        for k, v in seniority_raw.items():
            dates_vacation = v.get("dates", [])
            # filter by date base on the current month and go on
            dates_vacation = [
                date
                for date in dates_vacation
                if datetime.strptime(date, format_date).replace(tzinfo=time_zone)
                >= date_today
            ]
            if len(dates_vacation) == 0:
                continue
            out.append(
                {
                    "emp_id": item[0],
                    "name": item[1].upper() + " " + item[2].upper(),
                    "dates": dates_vacation,
                }
            )
    return out, 200


def get_all_dashboard_data(data_token):
    permissions = data_token.get("permissions", {})
    terms_list = [item.split(".")[-1].lower() for item in permissions.values()]
    #  get all notifications
    flag, error, result = get_notifications_by_permission(
        terms_list, data_token.get("emp_id", "%")
    )
    data_out = {}
    if not flag:
        return error, 400
    out_not = []
    for item in result:
        body = json.loads(item[2])
        body["id"] = item[1]
        out_not.append(body)
    data_out["notifications"] = out_not
    # get sm pending if almacen in term list
    out_sm = []
    if "almacen" in terms_list:
        flag, error, result = get_pending_sm_db()
        if not flag:
            return error, 400
        for item in result:
            out_sm.append(
                {
                    "id": item[0],
                    "folio": item[1],
                    "contract": item[2],
                    "facility": item[3],
                    "location": item[4],
                    "client_id": item[5],
                    "emp_id": item[6],
                    "order_quotation": item[7],
                    "date": item[8].strftime(format_timestamps)
                    if isinstance(item[8], datetime)
                    else item[8],
                    "critical_date": item[9].strftime(format_timestamps)
                    if isinstance(item[9], datetime)
                    else item[9],
                    "items": json.loads(item[10]),
                    "status": item[11],
                    "history": json.loads(item[12]),
                    "comment": item[13],
                    "extra_info": json.loads(item[14]),
                }
            )
        data_out["sm"] = out_sm
    return data_out, 200
