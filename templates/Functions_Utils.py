# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 16/jul./2024  at 15:50 $"

import json
import re
from datetime import datetime

import jwt
import pytz

from static.constants import (
    format_timestamps,
    secrets,
    file_size_pages,
    timezone_software,
    filepath_daemons,
)
from templates.controllers.notifications.Notifications_controller import (
    insert_notification,
)

import os


def create_notification_permission(
    msg: str, permissions: list, title: str, sender_id: int, recierver_id=0, extra_emps=None
):
    """
    Función para crear una notificación de permiso
    :param extra_emps:
    :param recierver_id:
    :param sender_id:
    :param title:
    :param msg:
    :param permissions:
    :return:
    """
    extra_emps = extra_emps if extra_emps else []
    permissions = [item.lower() for item in permissions]
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    body = {
        "id": 0,
        "status": 0,
        "title": title,
        "msg": msg,
        "timestamp": timestamp,
        "sender_id": sender_id,
        "receiver_id": recierver_id,
        "app": permissions,
        "extra_emps": extra_emps
    }
    flag, error, result = insert_notification(body)
    return flag


def unpack_token(token: str) -> dict:
    """
    Unpacks the token.
    :param token: <string>
    :return: <dict>
    """
    return jwt.decode(token, secrets.get("TOKEN_MASTER_KEY"), algorithms="HS256")


def create_notification_permission_notGUI(
    msg: str, permissions: list, title: str, sender_id: int, recierver_id=0
):
    """
    Función para crear una notificación de permiso
    :param recierver_id:
    :param sender_id:
    :param title:
    :param msg:
    :param permissions:
    :return:
    """
    sender_id = sender_id if sender_id else 0
    permissions = [item.lower() for item in permissions]
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    body = {
        "id": 0,
        "status": 0,
        "title": title,
        "msg": msg,
        "timestamp": timestamp,
        "sender_id": sender_id,
        "receiver_id": recierver_id,
        "app": permissions,
    }
    flag, error, result = insert_notification(body)
    return flag


def normalize_command(s: str):
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
    )
    for a, b in replacements:
        s = s.replace(a, b).replace(a.upper(), b.upper())
    s = s.lower()
    return s


def clean_command(command: str) -> str:
    """

    :param command: command for sql bot
    :return: cleaned command without special characters
    """
    message = normalize_command(command)
    message = message.replace("'''", "")
    numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    ignore = [
        "a",
        "ante",
        "bajo",
        "con",
        "contra",
        "de",
        "desde",
        "durante",
        "en",
        "entre",
        "hacia",
        "hasta",
        "mediante",
        "para",
        "por",
        "según",
        "sin",
        "sobre",
        "tras",
        "y",
        "e",
        "ni",
        "que",
        "o",
        "u",
        "pero",
        "aunque",
        "sino",
    ]
    for item in ignore:
        message = message.replace(f" {item} ", " ")
    for number in numbers:
        match = re.search(f"{number}", message)
        if match is not None:
            index = match.regs[0][0]
            message = message[:index] + "" + message[index + 1 :]
    message = message.replace("''", "'%'")
    message = message.replace("/", "")
    message = message.replace("  ", " ")
    message = message.replace("=", " like ")
    msg_list = message.split(",")
    message = " AND ".join(msg_list)
    matches = re.findall(r"'(.*?)'", message)
    if matches.__len__() != 0:
        for item in matches:
            message = message.replace(item, item.replace(" ", " OR "))
    return message


def clean_name(name: str):
    """

    :param name: name to be cleaned and make an iterable
    :return: cleaned message list without special characters
    """
    message = normalize_command(name)
    ignore = [
        "a",
        "ante",
        "bajo",
        "con",
        "contra",
        "de",
        "desde",
        "durante",
        "en",
        "entre",
        "hacia",
        "hasta",
        "mediante",
        "para",
        "por",
        "según",
        "sin",
        "sobre",
        "tras",
        "y",
        "e",
        "ni",
        "que",
        "o",
        "u",
        "pero",
        "aunque",
        "sino",
    ]
    for item in ignore:
        message = message.replace(f" {item} ", " ")
    message = message.replace("''", "'%'")
    message = message.replace("'generic'", "'%'")
    message = message.replace("  ", " ")
    msg_list = message.split(" ")
    return msg_list


def get_page_size_dict():
    """
    Función para obtener el tamaño de la página
    :return: <dict>
    """
    dict_pagesize = json.load(open(file_size_pages, "r"))
    return dict_pagesize


def add_pagesize(page_size: str, values: list):
    """
    Función para agregar el tamaño de la página
    :param page_size: <str>
    :param values: <list>
    :return: <dict>
    """
    dict_pagesize = get_page_size_dict()
    dict_pagesize[page_size.upper()] = values
    with open(file_size_pages, "w") as file:
        # noinspection PyTypeChecker
        json.dump(dict_pagesize, file, indent=4, sort_keys=True)
    return dict_pagesize


def delete_pagesize(page_size: str):
    """
    Función para eliminar el tamaño de la página
    :param page_size: <str>
    :return: <dict>
    """
    dict_pagesize = get_page_size_dict()
    dict_pagesize.pop(page_size.upper())
    with open(file_size_pages, "w") as file:
        # noinspection PyTypeChecker
        json.dump(dict_pagesize, file, indent=4, sort_keys=True)
    return dict_pagesize


def get_page_size(page_size: str):
    """
    Función para obtener el tamaño de la página
    :param page_size: <str>
    :return: <dict>
    """
    dict_pagesize = get_page_size_dict()
    return dict_pagesize[page_size.upper()]


def update_flag_daemons(**kwargs):
    """
    Función para actualizar el archivo de daemons
    :param kwargs:
    :return:
    """
    # check if file exists
    if not os.path.exists(filepath_daemons):
        with open(filepath_daemons, "w") as file:
            # noinspection PyTypeChecker
            json.dump({}, file, indent=4)
    flags_daemons = json.load(open(filepath_daemons, "r"))
    for key, value in kwargs.items():
        flags_daemons[key] = value
    with open(filepath_daemons, "w") as file:
        # noinspection PyTypeChecker
        json.dump(flags_daemons, file, indent=4)


def read_flag_daemons():
    """
    Función para leer el archivo de daemons
    :return:
    """
    flags_daemons = json.load(open(filepath_daemons, "r"))
    return flags_daemons
