# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 16/jul./2024  at 15:50 $"

import re
from datetime import datetime

import jwt

from static.extensions import format_timestamps, secrets
from templates.controllers.notifications.Notifications_controller import (
    insert_notification,
)


def create_notification_permission(
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
    permissions = [item.lower() for item in permissions]
    date = datetime.now()
    timestamp = date.strftime(format_timestamps)
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
    permissions = [item.lower() for item in permissions]
    date = datetime.now()
    timestamp = date.strftime(format_timestamps)
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
