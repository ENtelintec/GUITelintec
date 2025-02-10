# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 10:34 $"

import json
import pickle

from static.constants import filepath_settings
from templates.Functions_openAI import get_response_assistant, get_files_list_openai
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


def get_all_notification_db_permission(permission, status):
    code = 200
    flag, error, result = get_notifications_by_permission(
        permission.split(".")[-1].lower(), status
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
            body = json.loads(item[1])
            data_raw = json.loads(item[2])
            data_out.append({"id": item[0], "data": body, "data_raw": data_raw})
        return data_out, 200
    else:
        return [str(error, result)], 400
