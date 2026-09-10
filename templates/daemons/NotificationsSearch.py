# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 13/mar/2025  at 13:15 $"

import threading

from templates.Functions_Utils import (
    create_notification_permission_notGUI,
    update_flag_daemons,
)
from templates.resources.midleware.Functions_midleware_RRHH import fetch_medicals


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
            case "payroll":
                print("searching for payroll notifications")
            case _:
                print("Error in type_n")
