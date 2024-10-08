# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 16/jul./2024  at 15:50 $"

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
