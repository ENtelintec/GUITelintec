# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 12/jul./2024  at 15:16 $"

import json
from datetime import datetime

from static.constants import format_date
from templates.controllers.fichajes.fichajes_controller import get_all_fichajes_op
from templates.misc.Functions_AuxFiles import split_commment, unify_comment_dict


def transform_bitacora_data_to_dict(data, columns):
    result = []
    for item in data:
        row = {}
        for i, column in enumerate(columns):
            row[column] = item[i]
        result.append(row)
    return result


def get_extras_last_month(extras_dict: dict, date=None):
    date_today = datetime.now().date() if date is None else date
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
