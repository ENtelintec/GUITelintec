# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 10:34 $"

import json
import pickle
from datetime import datetime


from static.extensions import filepath_settings
from templates.Functions_openAI import get_response_assistant, get_files_list_openai
from templates.controllers.misc.tasks_controller import get_task_by_id_emp
from templates.controllers.notifications.Notifications_controller import (
    get_notifications_by_user,
    get_notifications_by_permission,
)
from templates.misc.Functions_AuxFiles import split_commment, unify_comment_dict


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


def handle_comment_extra(type_extra: int, comment: str):
    comment_dict = split_commment(comment)
    places = comment_dict["place"].split("<**>")
    print(f"places: {places}")
    if len(places) > 1:
        places[type_extra] = " "
    comment_dict["place"] = "<**>".join(places)
    comment_out = unify_comment_dict(comment_dict)
    return comment_out


def get_events_from_extraordinary_sources(hour_in: str, hour_out: str, data: dict):
    # data["event"], (data["date"], data["value"], data["comment"], data["contract"])
    events = []
    data_events = []

    normal_hour_in = datetime.strptime(hour_in.split("-->")[0], "%H:%M")
    normal_hour_out = datetime.strptime(hour_out.split("-->")[0], "%H:%M")
    timestamp_hour_in = datetime.strptime(hour_in.split("-->")[1], "%H:%M")
    timestamp_hour_out = datetime.strptime(hour_out.split("-->")[1], "%H:%M")
    # timestamp limit hours in and out
    timestamp_limit_hour_in = datetime.strptime(hour_in.split("-->")[2], "%H:%M")
    timestamp_limit_hour_out = datetime.strptime(hour_out.split("-->")[2], "%H:%M")
    if (
        normal_hour_in >= timestamp_hour_in >= timestamp_limit_hour_in
        and normal_hour_out >= timestamp_hour_out >= timestamp_limit_hour_out
    ):
        print(
            f"event: normal, date: {data['date']}, value: {1.0}, comment: {data['comment']}"
        )
        events.append("normal")
        data_events.append((data["date"], 1.0, data["comment"], data["contract"]))
    else:
        if timestamp_hour_in < timestamp_limit_hour_in:
            hours_late = timestamp_limit_hour_in - timestamp_hour_in
            hours_late = hours_late.total_seconds() / 3600.0
            # print(f"event: late, date: {data['date']}, value: {int(hours_late)} hours {int(hours_late % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("atraso")
            data_events.append(
                (data["date"], hours_late, data["comment"], data["contract"])
            )
        elif timestamp_hour_in > normal_hour_in > timestamp_limit_hour_in:
            hours_early = timestamp_hour_in - normal_hour_in
            hours_early = hours_early.total_seconds() / 3600.0
            # print(f"event: extra, date: {data['date']}, value: {int(-hours_early)} hours {int(-hours_early % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("extra")
            data_events.append(
                (
                    data["date"],
                    hours_early,
                    handle_comment_extra(1, data["comment"]),
                    data["contract"],
                )
            )
        if timestamp_hour_out < timestamp_limit_hour_out:
            hours_extra = timestamp_limit_hour_out - timestamp_hour_out
            hours_extra = hours_extra.total_seconds() / 3600.0
            # print(f"event: extra, date: {data['date']}, value: {int(hours_extra)} hours {int(hours_extra % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("extra")
            data_events.append(
                (
                    data["date"],
                    hours_extra,
                    handle_comment_extra(0, data["comment"]),
                    data["contract"],
                )
            )
        # early leaving
        if timestamp_hour_out > normal_hour_out:
            early_hours = timestamp_hour_out - normal_hour_out
            early_hours = early_hours.total_seconds() / 3600.0
            # print(f"event: early, date: {data['date']}, value: {int(-early_hours)} hours {int(-early_hours % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("early")
            data_events.append(
                (data["date"], early_hours, data["comment"], data["contract"])
            )
    return events, data_events


def get_task_by_id_employee(id_emp: int):
    flag, error, result = get_task_by_id_emp(id_emp)
    if flag:
        data_out = []
        for item in result:
            body = json.loads(item[1])
            data_out.append({"id": item[0], "data": body})
        return data_out, 200
    else:
        return [str(error, result)], 400
