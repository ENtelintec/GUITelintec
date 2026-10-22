# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 13/mar/2025  at 13:15 $"

import threading
from datetime import datetime

import pytz

from static.constants import format_date, timezone_software
from templates.Functions_Utils import (
    create_notification_permission_notGUI,
    read_flag_daemons,
    update_flag_daemons,
)
from templates.resources.midleware.Functions_midleware_RRHH import fetch_medicals
from templates.resources.midleware.MD_BalanceAlerts import run_balance_sweep
from templates.resources.midleware.MD_CDA import build_cda_alerts, build_cda_notification_lines


def build_medical_notifications(items: list) -> list[str]:
    """Una línea por empleado ACTIVO cuyo examen médico está vencido, por
    vencer (0..30 días) o marcado NO APTO, a partir de los campos que ya
    calcula `fetch_medicals` con la regla compartida de Functions_Aux_RH
    (antes se comparaba `year - year > 15`, así que jamás avisaba)."""
    out = []
    for item in items:
        if str(item.get("status") or "").upper() != "ACTIVO":
            continue
        alert = item.get("alert")
        name = item.get("name")
        if alert == "vencido":
            out.append(
                f"El empleado {name} debe realizar sus exámenes médicos: vencieron el "
                f"{item.get('due_date')} (hace {-int(item.get('days_left') or 0)} días)."
            )
        elif alert == "por_vencer":
            out.append(
                f"El empleado {name} debe programar sus exámenes médicos: vencen el "
                f"{item.get('due_date')} (faltan {int(item.get('days_left') or 0)} días)."
            )
        elif alert == "no_apto":
            out.append(f"El empleado {name} está marcado como NO APTO en su examen médico.")
    return out


def MedicalNotifications(data_token):
    out, code = fetch_medicals(data_token)
    if code != 200:
        return False
    medical_to_notify = build_medical_notifications(out.get("data") or [])
    if not medical_to_notify:
        return True
    msg = "Notificaciones de sistema\n" + "\n".join(medical_to_notify)
    return create_notification_permission_notGUI(
        msg, data_token, ["rrhh"], "Notificaciones de sistema", 0, 0
    )


def CDANotifications(data_token):
    """Barrido diario de CDA: una notificacion de sistema a sgi/administracion con
    una linea por alerta (polizas, pagos, mantenimiento, refrendo, llantas)."""
    alerts, _errors = build_cda_alerts(data_token)
    lines = build_cda_notification_lines(alerts)
    if not lines:
        return True
    msg = "Notificaciones de sistema — Control de vehículos\n" + "\n".join(lines)
    return create_notification_permission_notGUI(
        msg, data_token, ["sgi", "administracion"], "Notificaciones de sistema", 0, 0
    )


def start_daily_sweep(type_n: str, data_token, starter=None) -> str:
    """Lanza el barrido `type_n` si hoy no ha corrido: bandera `flag_<type_n>`
    (False mientras corre) y fecha `last_date_<type_n>` en files/flags_daemons.json,
    misma receta que médicos y CDA. Devuelve "started" | "running" | "done_today".
    `starter` (pruebas) sustituye al hilo real."""
    flags = read_flag_daemons()
    if not flags.get(f"flag_{type_n}", True):
        return "running"
    tz = pytz.timezone(timezone_software)
    now = datetime.now(pytz.utc).astimezone(tz)
    last_date = None
    last = flags.get(f"last_date_{type_n}")
    if last:
        try:
            last_date = datetime.strptime(str(last), format_date).date()
        except ValueError:
            last_date = None
    if last_date is not None and last_date >= now.date():
        return "done_today"
    update_flag_daemons(**{f"last_date_{type_n}": now.strftime(format_date), f"flag_{type_n}": False})
    if starter is not None:
        starter()
    else:
        NotificationsSearch(data_token, type_n=type_n).start()
    return "started"


class NotificationsSearch(threading.Thread):
    def __init__(self, data_token, type_n="medical"):
        super().__init__()
        self.type_n = type_n
        self.data_token = data_token

    def run(self):
        match self.type_n:
            case "medical":
                try:
                    MedicalNotifications(self.data_token)
                finally:
                    # Si la búsqueda truena, la bandera debe volver a True o el
                    # endpoint respondería "ya se está realizando" para siempre.
                    update_flag_daemons(flag_medical=True)
            case "cda":
                try:
                    CDANotifications(self.data_token)
                finally:
                    update_flag_daemons(flag_cda=True)
            case "balance":
                # Saldos / entregas / traslados (docs/avisos_saldos_entregas_traslados.md).
                try:
                    run_balance_sweep(self.data_token)
                finally:
                    update_flag_daemons(flag_balance=True)
            case "payroll":
                print("searching for payroll notifications")
            case _:
                print("Error in type_n")
