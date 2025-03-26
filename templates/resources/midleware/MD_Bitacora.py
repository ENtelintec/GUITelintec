# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 12/jul./2024  at 15:16 $"

import csv
import json
from datetime import datetime, timedelta

import pytz

from static.constants import (
    format_date,
    log_file_bitacora_path,
    delta_bitacora_edit,
    filepath_bitacora_download,
    format_timestamps,
    timezone_software,
)
from templates.Functions_Utils import create_notification_permission
from templates.controllers.fichajes.bitacora_rh_controller import (
    get_all_bitacora_rh_db,
    insert_bitacora_rh_db,
    update_bitacora_rh_db,
    delete_bitacora_rh_db,
    get_bitacora_rh_db_by_date,
)
from templates.controllers.fichajes.fichajes_controller import get_all_fichajes_op
from templates.misc.Functions_AuxFiles import (
    split_commment,
    unify_comment_dict,
    get_events_op_date,
    update_bitacora,
    update_bitacora_value,
    erase_value_bitacora,
)
from templates.misc.Functions_Files import write_log_file


def check_date_difference(date_modify, delta):
    flag = True
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone)
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


def transform_bitacora_data_to_dict(data, columns):
    result = []
    for item in data:
        row = {}
        for i, column in enumerate(columns):
            row[column] = item[i]
        result.append(row)
    return result


def handle_comment_extra(type_extra: int, comment: str, hour_in, hour_out):
    comment_dict = split_commment(comment)
    places = comment_dict["place"].split("<**>")
    if len(places) > 1:
        places[type_extra] = " "
    comment_dict["place"] = "<**>".join(places)
    comment_dict["times"] = "<**>".join([hour_in, hour_out])
    comment_dict["aproved"] = 0
    comment_out = unify_comment_dict(comment_dict)
    return comment_out


def get_events_from_extraordinary_sources(hour_in: str, hour_out: str, data: dict):
    events = []
    data_events = []
    normal_hour_in = datetime.strptime(hour_in.split("-->")[0], "%H:%M")
    normal_hour_out = datetime.strptime(hour_out.split("-->")[0], "%H:%M")
    tmp_hour_in = datetime.strptime(hour_in.split("-->")[2], "%H:%M")
    tmp_hour_out = datetime.strptime(hour_out.split("-->")[2], "%H:%M")
    # timestamp limit hours in and out
    tmp_limit_hour_in = datetime.strptime(hour_in.split("-->")[1], "%H:%M")
    tmp_limit_hour_out = datetime.strptime(hour_out.split("-->")[1], "%H:%M")
    if (
        normal_hour_in <= tmp_hour_in <= tmp_limit_hour_in
        and normal_hour_out <= tmp_hour_out <= tmp_limit_hour_out
    ):
        # print(
        #     f"event: normal, date: {data['date']}, value: {1.0}, comment: {data['comment']}"
        # )
        events.append("normal")
        data_events.append([data["date"], 1.0, data["comment"], data["contract"]])
    else:
        if tmp_hour_in > tmp_limit_hour_in:
            hours_late = tmp_hour_in - tmp_limit_hour_in
            hours_late = hours_late.total_seconds() / 3600.0
            # print(f"event: late, date: {data['date']}, value: {int(hours_late)} hours {int(hours_late % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("atraso")
            data_events.append(
                [data["date"], hours_late, data["comment"], data["contract"]]
            )
        elif tmp_hour_in < normal_hour_in:
            hours_early = normal_hour_in - tmp_hour_in
            hours_early = hours_early.total_seconds() / 3600.0
            # print(f"event: extra, date: {data['date']}, value: {int(-hours_early)} hours {int(-hours_early % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("extra")
            data_events.append(
                [
                    data["date"],
                    hours_early,
                    handle_comment_extra(
                        1,
                        data["comment"],
                        hour_in.split("-->")[2],
                        hour_out.split("-->")[2],
                    ),
                    data["contract"],
                ]
            )
        if tmp_hour_out > tmp_limit_hour_out:
            hours_extra = tmp_hour_out - tmp_limit_hour_out
            hours_extra = hours_extra.total_seconds() / 3600.0
            # print(f"event: extra, date: {data['date']}, value: {int(hours_extra)} hours {int(hours_extra % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("extra")
            data_events.append(
                [
                    data["date"],
                    hours_extra,
                    handle_comment_extra(
                        0,
                        data["comment"],
                        hour_in.split("-->")[2],
                        hour_out.split("-->")[2],
                    ),
                    data["contract"],
                ]
            )
        # early leaving
        elif tmp_hour_out < normal_hour_out:
            early_hours = normal_hour_out - tmp_hour_out
            early_hours = early_hours.total_seconds() / 3600.0
            # print(f"event: early, date: {data['date']}, value: {int(-early_hours)} hours {int(-early_hours % 1 * 60)} minutes, comment: {data['comment']}")
            events.append("early")
            data_events.append(
                [data["date"], early_hours, data["comment"], data["contract"]]
            )
    events_final = []
    data_events_final = []
    for event, data_event in zip(events, data_events):
        if event in events_final:
            index = events_final.index(event)
            data_events_final[index][1] += data_event[1]
        else:
            events_final.append(event)
            data_events_final.append(data_event)
    return events_final, data_events_final


def get_extras_last_month(extras_dict: dict, date=None):
    time_zone = pytz.timezone(timezone_software)
    date_today = (
        datetime.now(pytz.utc).astimezone(time_zone).date() if date is None else date
    )
    year = date_today.year
    month = date_today.month - 1
    day = date_today.day
    events = []
    if str(year) in extras_dict.keys():
        if (
            str(month) in extras_dict[str(year)].keys()
            or str(month + 1) in extras_dict[str(year)].keys()
        ):
            try:
                for day_key in extras_dict[str(year)][str(month)].keys():
                    if int(day_key) >= day:
                        events.append(extras_dict[str(year)][str(month)][str(day_key)])
            except KeyError:
                # print("error ", month)
                pass
            try:
                for day_key in extras_dict[str(year)][str(month + 1)].keys():
                    if int(day_key) <= day:
                        events.append(
                            extras_dict[str(year)][str(month + 1)][str(day_key)]
                        )
            except KeyError:
                # print("error ", month + 1)
                pass
    return events


def get_events_extra(data):
    flag, error, result = get_all_fichajes_op()
    date = (
        datetime.strptime(data["date"], format_date)
        if isinstance(data["date"], str)
        else data["date"]
    )
    print("flag", flag, "error", error)
    events_out = []
    for row in result:
        extras_dict = json.loads(row[8])
        events = get_extras_last_month(extras_dict, date)
        for event in events:
            comment = event["comment"]
            comment_dict = split_commment(comment)
            event["comment_dict"] = comment_dict
            event["name"] = row[0] + " " + row[1]
            event["emp_id"] = row[3]
            event["contract"] = row[4]
            events_out.append(event)
    return events_out, 200


def add_aproved_to_comment(comment_str):
    comment_dict = split_commment(comment_str)
    if comment_dict["aproved"] is not None:
        comment_dict["comment"] += "\naproved-->" + str(1)
    comment = unify_comment_dict(comment_dict)
    return comment


def get_events_bitacora(data):
    date = data["date"]
    date = datetime.strptime(date, format_date) if isinstance(date, str) else date
    events, columns = get_events_op_date(date, True, emp_id=data["emp_id"])
    data_events = []
    for item in events:
        data_events.append(
            {
                "id": item[0],
                "name": item[1].upper(),
                "contrato": item[2],
                "evento": item[3],
                "lugar": item[4],
                "act": item[5],
                "incidencia": item[6],
                "valor": item[7],
                "timestamp": item[8],
                "commentario": item[9],
                "approved": int(item[10]),
                "comment_raw": item[11],
            }
        )
    return {"data": events, "dataEvents": data_events, "columns": columns}, 200


def create_event_bitacora_from_api(data):
    out = check_date_difference(data["date"], delta_bitacora_edit)
    flag = False
    error = None
    events_added = []
    if not out:
        return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
    if data["event"].lower() == "extraordinary":
        event, data_events = get_events_from_extraordinary_sources(
            data["hour_in"], data["hour_out"], data
        )
        for index, item in enumerate(data_events):
            flag, error, result = update_bitacora(data["id_emp"], event[index], item)
            if flag:
                events_added.append(f"{event[index]}_{item[1]}, result: {result}")
    else:
        flag, error, result = update_bitacora(
            data["id_emp"],
            data["event"],
            (data["date"], data["value"], data["comment"], data["contract"]),
        )
        if flag:
            events_added.append(f"{data['event']}_{data['value']}, result: {result}")
    if flag:
        msg = (
            f"Record inserted-->Por: {data['id_leader']}, para empleado: {data['id_emp']}, Fecha: {data['date']}, "
            f"Evento: {data['event']}, Valor: {data['value']}, Comentario: {data['comment']}"
        )
        create_notification_permission(
            msg,
            ["bitacora", "operaciones"],
            "Nuevo evento bitacora",
            data["id_leader"],
            data["id_emp"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"answer": "The event has been added", "data": events_added}, 201
    elif error is not None:
        print(error)
        return {"answer": "There has been an error at adding the bitacora"}, 404
    else:
        return {"answer": "Fail to add registry"}, 404


def update_event_bitacora_from_api(data):
    out = check_date_difference(data["date"], delta_bitacora_edit)
    if not out:
        return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
    flag, error, result = update_bitacora_value(
        data["id_emp"],
        data["event"],
        (data["date"], data["value"], data["comment"], data["contract"]),
    )
    if flag:
        msg = (
            f"Record updated-->Por: {data['id_leader']}, para empleado: {data['id_emp']}, Fecha: {data['date']}, "
            f"Evento: {data['event']}, Valor: {data['value']}, Comentario: {data['comment']}"
        )
        create_notification_permission(
            msg,
            ["bitacora", "operaciones"],
            "Evento bitacora actualizado",
            data["id_leader"],
            data["id_emp"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"answer": "The event has been updated"}, 200
    elif error is not None:
        print(error)
        return {"answer": "There has been an error at updating the bitacora"}, 404
    else:
        return {"answer": "Fail to update registry"}, 404


def delete_event_bitacora_from_api(data):
    out = check_date_difference(data["date"], delta_bitacora_edit)
    if not out:
        return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
    flag, error, result = erase_value_bitacora(
        data["id_emp"], data["event"], (data["date"], data["contract"])
    )
    if flag:
        msg = (
            f"Record deleted-->Por: {data['id_leader']}, para empleado: {data['id_emp']}, Fecha: {data['date']}, "
            f"Evento: {data['event']}"
        )
        create_notification_permission(
            msg,
            ["bitacora", "operaciones"],
            "Evento bitacora eliminado",
            data["id_leader"],
            data["id_emp"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"answer": "The event has been deleted"}, 200
    elif error is not None:
        print(error)
        return {"answer": "There has been an error at deleting the bitacora"}, 404
    else:
        return {"answer": "Fail to delete registry"}, 404


def get_file_report_bitacora(data):
    date = data["date"]
    date = datetime.strptime(date, format_date) if isinstance(date, str) else date
    events, columns = get_events_op_date(date, False, emp_id=data["id_emp"])
    event_filtered = []
    match data["span"]:
        case "day":
            for item in events:
                if datetime.strptime(item[7], format_timestamps).day == date.day:
                    event_filtered.append(item)
        case "week":
            for item in events:
                if (
                    datetime.strptime(item[7], format_timestamps).isocalendar()[1]
                    == date.isocalendar()[1]
                ):
                    event_filtered.append(item)
        case "month":
            for item in events:
                if datetime.strptime(item[7], format_timestamps).month == date.month:
                    event_filtered.append(item)
    # save csv
    with open(filepath_bitacora_download, "w") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for item in event_filtered:
            writer.writerow(item)
    return filepath_bitacora_download, 200


def create_multiple_event_bitacora_from_api(data):
    events_recieved = data["events"]
    events_added = []
    msg = f"---Agregando nuevos eventos por el lider {data['id_leader']}---"
    for event in events_recieved:
        if event["event"].lower() == "extraordinary":
            event_e, data_events = get_events_from_extraordinary_sources(
                event["hour_in"], event["hour_out"], event
            )
            for index, item in enumerate(data_events):
                flag, error, result = update_bitacora(
                    event["id_emp"], event_e[index], item
                )
                if flag:
                    events_added.append(
                        f"id_emp: {event['id_emp']}, {event_e[index]}_{item[1]}, flag: {flag}, error: {str(error)}, result: {result}"
                    )
                    msg += f"\nid_emp: {event['id_emp']}, {event_e[index]}_{item[1]}, flag: {flag}, error: {str(error)}, result: {result}"
        else:
            flag, error, result = update_bitacora(
                event["id_emp"],
                event["event"],
                (
                    event["date"],
                    event["value"],
                    event["comment"],
                    event["contract"],
                ),
            )
            events_added.append(
                f"id_emp: {event['id_emp']}, {event['event']}_{event['value']}, flag: {flag}, error: {str(error)}, result: {result}"
            )
            msg += f"\nid_emp: {event['id_emp']}, {event['event']}_{event['value']}, flag: {flag}, error: {str(error)}, result: {result}"
    create_notification_permission(
        msg,
        ["bitacora", "operaciones"],
        "Nuevo evento bitacora",
        data["id_leader"],
        data["id_leader"],
    )
    write_log_file(log_file_bitacora_path, msg)
    return {"answer": "The events were proccessed.", "data": events_added}, 200


def aprove_event_bitacora_from_api(data):
    flag, error, result = update_bitacora(
        data["id_emp"],
        "extra",
        [data["date"], data["value"], data["comment"], data["contract"]],
    )
    data["comment"] = add_aproved_to_comment(data["comment"])
    if flag:
        msg = f"Evento extra aprovado: {data['id_emp']}, {data['date']}, {data['value']}, {data['comment']}"
        create_notification_permission(
            msg,
            ["bitacora", "operaciones"],
            "Evento extra aprovado bitacora",
            data["id_leader"],
            data["id_emp"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"answer": "The event has been updated"}, 200
    elif error is not None:
        print(error)
        return {"answer": "There has been an error at aproving the bitacora"}, 404
    else:
        return {"answer": "Fail to update registry"}, 404


def fetch_all_bitacora_rh():
    flag, error, result = get_all_bitacora_rh_db()
    dict_emps = {}
    # id_event, emp_id, event, timestamp, extra_info, name, l_name, contrato
    for item in result:
        extra_info = json.loads(item[4])
        if item[1] in dict_emps.keys():
            events = dict_emps[item[1]]["events"]
            events.append(
                {
                    "timestamp": item[3].strftime(format_timestamps),
                    "type": item[2],
                    "comment": extra_info.get("comment", ""),
                    "value": extra_info.get("value", 1.0),
                    "id": item[0],
                }
            )
            dict_emps[item[1]]["events"] = events
        else:
            dict_emps[item[1]] = {
                "emp_id": item[1],
                "name": item[5],
                "lastname": item[6],
                "contract": item[7],
                "events": [
                    {
                        "timestamp": item[3].strftime(format_timestamps),
                        "type": item[2],
                        "comment": extra_info.get("comment", ""),
                        "value": extra_info.get("value", 1.0),
                        "id": item[0],
                    }
                ],
            }
    out_data = list(dict_emps.values())
    print(out_data)
    if flag:
        return {"data": out_data, "msg": "ok"}, 200
    else:
        return {"data": [], "msg": str(error)}, 400


def create_event_bitacora_rh_from_api(data, data_token):
    flag, error, result = insert_bitacora_rh_db(
        data["emp_id"],
        data["type"],
        data["timestamp"],
        data["comment"],
        data["value"],
    )
    if flag:
        msg = f"Evento de bitacora registrado por RH: {data['emp_id']}, {data['timestamp']}, {data['type']}, {data['value']}"
        create_notification_permission(
            msg,
            ["RH"],
            "Evento de bitacora registrado",
            data_token.get("emp_id", 0),
            data["emp_id"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"msg": "The event has been updated"}, 200
    elif error is not None:
        print(error)
        return {"msg": "There has been an error at aproving the bitacora"}, 400
    else:
        return {"msg": "Fail to update registry"}, 400


def update_event_bitacora_rh_from_api(data, data_token):
    flag, error, result = update_bitacora_rh_db(
        data["id"],
        data["emp_id"],
        data["type"],
        data["timestamp"],
        data["comment"],
        data["value"],
    )
    if flag:
        msg = f"Evento de bitacora actualizado por RH: {data['emp_id']}, {data['timestamp']}, {data['type']}, {data['value']}"
        create_notification_permission(
            msg,
            ["RH"],
            "Evento de bitacora actualizado",
            data_token.get("emp_id", 0),
            data["emp_id"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"msg": "The event has been updated"}, 200
    elif error is not None:
        print(error)
        return {"msg": "There has been an error at aproving the bitacora"}, 400
    else:
        return {"msg": "Fail to update registry"}, 400


def delete_event_bitacora_rh_from_api(data, data_token):
    flag, error, result = delete_bitacora_rh_db(
        data["id"],
    )
    if flag:
        msg = f"Evento de bitacora eliminado por RH: {data['id']}"
        create_notification_permission(
            msg,
            ["RH"],
            "Evento de bitacora eliminado",
            data_token.get("emp_id", 0),
            data["emp_id"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"msg": "The event has been deleted"}, 200
    elif error is not None:
        print(error)
        return {"msg": "There has been an error at aproving the bitacora"}, 400
    else:
        return {"msg": "Fail to update registry"}, 400


def fetch_bitacora_rh_from_api_by_date(data):

    flag, error, result = get_bitacora_rh_db_by_date(data["date"])
    dict_emps = {}
    # id_event, emp_id, event, timestamp, extra_info, name, l_name, contrato
    for item in result:
        extra_info = json.loads(item[4])
        if item[1] in dict_emps.keys():
            events = dict_emps[item[1]]["events"]
            events.append(
                {
                    "timestamp": item[3].strftime(format_timestamps),
                    "type": item[2],
                    "comment": extra_info.get("comment", ""),
                    "value": extra_info.get("value", 1.0),
                    "id": item[0],
                }
            )
            dict_emps[item[1]]["events"] = events
        else:
            dict_emps[item[1]] = {
                "emp_id": item[1],
                "name": item[5],
                "lastname": item[6],
                "contract": item[7],
                "events": [
                    {
                        "timestamp": item[3].strftime(format_timestamps),
                        "type": item[2],
                        "comment": extra_info.get("comment", ""),
                        "value": extra_info.get("value", 1.0),
                        "id": item[0],
                    }
                ],
            }
    out_data = list(dict_emps.values())
    print(out_data)
    if flag:
        return {"data": out_data, "msg": "ok"}, 200
    else:
        return {"data": [], "msg": str(error)}, 400
