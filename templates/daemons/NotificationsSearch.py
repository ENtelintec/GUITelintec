# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 13/mar/2025  at 13:15 $"

import threading
from datetime import datetime

import pandas as pd
import pytz

from static.constants import timezone_software
from templates.Functions_Utils import (
    create_notification_permission_notGUI,
    update_flag_daemons,
)
from templates.resources.midleware.Functions_midleware_RRHH import fetch_medicals


def MedicalNotifications():
    time_zone = pytz.timezone(timezone_software)
    timestamp_today = datetime.now(pytz.utc).astimezone(time_zone)
    out, code = fetch_medicals()
    data = out.get("data", [])
    medical_to_notify = []
    for item in data:
        if item.get("status") != "ACTIVO":
            continue
        # get the last date
        last_date = item.get("dates")[-1]
        # check is a year minus 15 days have passed
        last_date = pd.to_datetime(last_date)
        if timestamp_today.year - last_date.year > 15:
            medical_to_notify.append(
                f"El empleado {item.get('name')} debe realizar sus examenes medicos"
            )
    if len(medical_to_notify) > 0:
        msg = "Notificaciones de sistema\n" + "\n".join(medical_to_notify)
        create_notification_permission_notGUI(
            msg, ["rrhh"], "Notificaciones de sistema", 0, 0
        )


class NotificationsSearch(threading.Thread):
    def __init__(self, type_n="medical"):
        super().__init__()
        self.type_n = type_n

    def run(self):
        match self.type_n:
            case "medical":
                MedicalNotifications()
                update_flag_daemons(flag_medical=True)
            case "payroll":
                print("searching for payroll notifications")
            case _:
                print("Error in type_n")
