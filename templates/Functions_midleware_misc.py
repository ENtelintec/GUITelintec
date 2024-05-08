# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 08/may./2024  at 10:34 $'

import json

from templates.controllers.notifications.Notifications_controller import get_notifications_by_user


def get_all_notification_db_user_status(id_emp, status):
    code = 200
    flag, error, result = get_notifications_by_user(id_emp, status)
    data_out = []
    for item in result:
        body = json.loads(item[2])
        body["id"] = item[1]
        data_out.append(body)
    return code if flag else 400, data_out if flag else error
