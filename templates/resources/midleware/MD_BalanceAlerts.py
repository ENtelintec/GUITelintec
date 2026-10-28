# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct./2026  at 18:00 $"

"""Barrido diario de avisos de sistema (junta con Administracion 2026-10-22,
docs/avisos_saldos_entregas_traslados.md):

- Control de saldos activo: vigencia a 60 / 30 / 15 dias de end_date (vencido
  incluido) y saldo disponible al 25 / 10 / 0 % del contratado.
- Control de entregas abierto (OCD): due_date a 60 / 30 / 15 dias.
- Traslados RECIBIDO CON DIFERENCIAS con 1 dia o mas sin resolver (cada dia,
  sin marcas).

Lo dispara la primera llamada del dia a GET /balanceControl (receta de medicos y
CDA: NotificationsSearch type_n="balance" + flags en files/flags_daemons.json).
Una vez por umbral y por control: la marca en extra_info.notified guarda la
referencia que la hizo valida (end_date, contracted_amount o due_date). Si la
referencia cambia (VIGENCIA, INYECCION/AJUSTE, due_date nuevo) el umbral vuelve
a avisar; no hace falta limpiar marcas desde los endpoints de movimiento.

El aviso de saldos y entregas sale ademas por correo SES a gerentes y jefes de
Administracion (P-095, docs/avisos_saldos_correo.md); solo en prod y sin token
tester, para no mandarles datos de dev/test.
"""

from datetime import date, datetime

import pytz

from static.constants import environment, log_file_admin_collecions, timezone_software
from templates.controllers.employees.employees_controller import get_active_employees_by_puesto
from templates.controllers.product.warehouses_controller import TRANSFER_COLUMNS, get_transfers_db
from templates.controllers.purchases.balance_control_controller import (
    get_balance_controls,
    get_last_amount_movement_ids,
    set_balance_control_notified,
)
from templates.controllers.purchases.delivery_control_controller import (
    get_delivery_controls,
    set_delivery_control_notified,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.misc.Functions_Files import write_log_file
from templates.misc.Functions_Mail import is_ses_configured, send_email_ses
from templates.resources.methods.Functions_Aux_RH import split_emails
from templates.resources.midleware import MD_BalanceControl, MD_DeliveryControl

# Umbrales fijos (decision 2026-10-22). El de 60 dias coincide con VALIDITY_EXPIRING_DAYS.
DAY_THRESHOLDS = (60, 30, 15)
PCT_THRESHOLDS = (25, 10, 0)
TRANSFER_UNRESOLVED_STATUS = 2  # RECIBIDO CON DIFERENCIAS (MD_Multisede.WH_TRANSFER_STATUS)
TRANSFER_MIN_DAYS = 1
# Saldos y entregas también le llegan a adminCobranza (P-155, docs/permisos_administracion.md);
# el lector cruza estas etiquetas con el nombre del permiso en minúsculas.
PERM_BALANCE = ["administracion", "admincobranza"]
PERM_TRANSFERS = ["almacen", "administracion"]
TITLE = "Notificaciones de sistema"
# Correo del aviso de saldos y entregas (P-095, decision 2026-10-22): gerentes y
# jefes de Administracion (departments.id 3, puesto GERENTE... / JEFE...), solo a
# sus correos institucionales. Los traslados no van por correo.
EMAIL_DEPARTMENT_ID = 3
EMAIL_PUESTO_PREFIXES = ("GERENTE", "JEFE")
EMAIL_DOMAIN = "@telintec.com.mx"
EMAIL_SUBJECT = "Avisos de control de saldos y entregas"


def _today() -> date:
    return datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software)).date()


def _money(value) -> str:
    return f"{float(value or 0):,.2f}"


def _pending_thresholds(value, thresholds, notified: dict, prefix: str, ref: str) -> list:
    """Umbrales cruzados (value <= umbral) que no tienen marca vigente: una marca
    vale solo si guardo la misma referencia (end_date / contratado / due_date)."""
    out = []
    for threshold in thresholds:
        if value <= threshold:
            mark = notified.get(f"{prefix}_{threshold}")
            if not (isinstance(mark, dict) and str(mark.get("ref")) == ref):
                out.append(threshold)
    return out


def _days_line(kind: str, label: str, date_text: str, days: int) -> str:
    if days < 0:
        return f"[{kind}] {label}: venció el {date_text} (hace {-days} días)"
    if days == 0:
        return f"[{kind}] {label}: vence hoy ({date_text})"
    return f"[{kind}] {label}: vence el {date_text} (faltan {days} días)"


def _balance_label(c: dict) -> str:
    name = c.get("contract_identifier") or c.get("title") or c.get("client_name") or ""
    number = c.get("contract_number") or c.get("contract_code") or ""
    inner = ", ".join(x for x in (str(name), str(number)) if x)
    return f"Control de saldos {c.get('id_control')} ({inner})" if inner else f"Control de saldos {c.get('id_control')}"


def _delivery_label(c: dict) -> str:
    inner = ", ".join(x for x in (str(c.get("title") or c.get("quotation_code") or ""), str(c.get("client_name") or "")) if x)
    return f"Control de entregas {c.get('id_control')} ({inner})" if inner else f"Control de entregas {c.get('id_control')}"


def build_balance_alerts(data_token) -> tuple[list, list, str | None]:
    """(lineas, [(id_control, notified_nuevo)], error) de los controles de saldos ACTIVOS."""
    flag, error, rows = get_balance_controls(None, None, 1, data_token)
    if not flag:
        return [], [], error
    # Referencia de los umbrales de porcentaje: contratado + ultimo movimiento de
    # dinero, para que una INYECCION/AJUSTE re-arme el aviso aunque el monto coincida.
    flag_m, _e, last_amount_mov = get_last_amount_movement_ids(data_token)
    if not flag_m:
        last_amount_mov = {}
    today = _today().isoformat()
    lines: list = []
    updates: list = []
    for row in rows:
        c = MD_BalanceControl._control_to_dict(row)
        extra = c.get("extra_info") or {}
        notified = dict(extra.get("notified") or {}) if isinstance(extra.get("notified"), dict) else {}
        new_marks: dict = {}
        label = _balance_label(c)
        days = c.get("days_to_end")
        end_date = str(c.get("end_date") or "")[:10]
        if days is not None and end_date:
            due = _pending_thresholds(int(days), DAY_THRESHOLDS, notified, "days", end_date)
            if due:
                lines.append(_days_line("Saldos", label, end_date, int(days)))
                for threshold in due:
                    new_marks[f"days_{threshold}"] = {"at": today, "ref": end_date}
        contracted = float(c.get("contracted_amount") or 0)
        if contracted > 0:
            available = float(c.get("available_amount") or 0)
            pct = available / contracted * 100
            ref = f"{contracted:.2f}#{last_amount_mov.get(int(c['id_control']), 0)}"
            due = _pending_thresholds(pct, PCT_THRESHOLDS, notified, "pct", ref)
            if due:
                lines.append(
                    f"[Saldos] {label}: saldo disponible {_money(available)} de {_money(contracted)} "
                    f"{c.get('currency') or 'MXN'} ({pct:.0f} %)" + (" — saldo agotado" if pct <= 0 else "")
                )
                for threshold in due:
                    new_marks[f"pct_{threshold}"] = {"at": today, "ref": ref}
        if new_marks:
            notified.update(new_marks)
            updates.append((int(c["id_control"]), notified))
    return lines, updates, None


def build_delivery_alerts(data_token) -> tuple[list, list, str | None]:
    """(lineas, [(id_control, notified_nuevo)], error) de los controles de entregas ABIERTOS (status 0)."""
    flag, error, rows = get_delivery_controls(None, None, 0, None, data_token)
    if not flag:
        return [], [], error
    today = _today().isoformat()
    lines: list = []
    updates: list = []
    for row in rows:
        c = MD_DeliveryControl._control_to_dict(row)
        days = c.get("days_to_due")
        due_date = str(c.get("due_date") or "")[:10]
        if days is None or not due_date:
            continue
        extra = c.get("extra_info") or {}
        notified = dict(extra.get("notified") or {}) if isinstance(extra.get("notified"), dict) else {}
        due = _pending_thresholds(int(days), DAY_THRESHOLDS, notified, "days", due_date)
        if not due:
            continue
        lines.append(_days_line("Entregas", _delivery_label(c), due_date, int(days)))
        for threshold in due:
            notified[f"days_{threshold}"] = {"at": today, "ref": due_date}
        updates.append((int(c["id_control"]), notified))
    return lines, updates, None


def transfer_alert_lines(rows, today: date | None = None) -> list:
    """Una linea por traslado RECIBIDO CON DIFERENCIAS con TRANSFER_MIN_DAYS o mas
    desde la recepcion (received_at; created_at si no hay). Sin marcas: se repite
    cada dia hasta que se resuelva (PUT /almacen/transfer/<id>/resolve)."""
    today = today or _today()
    lines = []
    for row in rows or []:
        t = dict(zip(TRANSFER_COLUMNS, row))
        when = t.get("received_at") or t.get("created_at")
        if when is None:
            continue
        if isinstance(when, datetime):
            when_date = when.date()
        elif isinstance(when, date):
            when_date = when
        else:
            try:
                when_date = datetime.strptime(str(when)[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
        days = (today - when_date).days
        if days < TRANSFER_MIN_DAYS:
            continue
        lines.append(
            f"[Traslados] Traslado {t.get('folio')} ({t.get('origin_name')} → {t.get('dest_name')}) "
            f"recibido con diferencias el {when_date.isoformat()}: {days} día(s) sin resolver"
        )
    return lines


def build_transfer_alerts(data_token) -> tuple[list, str | None]:
    flag, error, rows = get_transfers_db({"status": TRANSFER_UNRESOLVED_STATUS, "limit": 2000}, data_token)
    if not flag or not isinstance(rows, list):
        return [], error
    return transfer_alert_lines(rows), None


def balance_alert_recipients(data_token) -> tuple[list, str | None]:
    """Correos institucionales (sin duplicados) de los gerentes y jefes de Administracion activos."""
    flag, error, rows = get_active_employees_by_puesto(EMAIL_DEPARTMENT_ID, EMAIL_PUESTO_PREFIXES, data_token)
    if not flag or not isinstance(rows, list):
        return [], error or "no se pudieron leer los destinatarios"
    out: list = []
    for row in rows:
        for email in split_emails(row[4]):
            if email.lower().endswith(EMAIL_DOMAIN) and email.lower() not in {e.lower() for e in out}:
                out.append(email)
    return out, None


def email_balance_alert(msg: str, data_token, send=None) -> dict:
    """Manda el aviso de saldos y entregas por SES. status: sent | failed |
    pending (SES sin configurar) | skipped (fuera de prod o token tester: los
    destinatarios son personas reales). `send` (o el send_email_ses del modulo,
    que se resuelve al llamar) se sustituye en pruebas."""
    send = send or send_email_ses
    if environment != "prod" or (data_token or {}).get("is_tester"):
        return {"status": "skipped", "to": [], "error": None}
    if not is_ses_configured():
        return {"status": "pending", "to": [], "error": None}
    recipients, error = balance_alert_recipients(data_token)
    if error or not recipients:
        reason = error or "sin destinatarios (gerentes y jefes de Administración con correo institucional)"
        return {"status": "failed", "to": [], "error": reason}
    body = msg + "\n\nCorreo automático del sistema Telintec; las mismas líneas están en Notificaciones de sistema."
    ok, error, _message_id = send(recipients, f"{EMAIL_SUBJECT} — {_today().isoformat()}", body)
    return {"status": "sent" if ok else "failed", "to": recipients, "error": None if ok else error}


def run_balance_sweep(data_token, notify=create_notification_permission_notGUI, send_email=None) -> dict:
    """Corre el barrido completo: arma las lineas, inserta las notificaciones de
    sistema, manda el correo de saldos y entregas y, SOLO si al menos un canal
    (notificacion o correo) salio, escribe las marcas (si no, el umbral vuelve a
    intentarse al dia siguiente). `notify` y `send_email` se sustituyen en pruebas."""
    send_email = send_email or email_balance_alert
    errors: list = []
    marks_written = 0
    mail: dict = {"status": None, "to": [], "error": None}
    b_lines, b_updates, error = build_balance_alerts(data_token)
    if error:
        errors.append(f"saldos: {error}")
    d_lines, d_updates, error = build_delivery_alerts(data_token)
    if error:
        errors.append(f"entregas: {error}")
    t_lines, error = build_transfer_alerts(data_token)
    if error:
        errors.append(f"traslados: {error}")

    if b_lines or d_lines:
        msg = "Notificaciones de sistema — Control de saldos y entregas\n" + "\n".join(b_lines + d_lines)
        saved = notify(msg, data_token, PERM_BALANCE, TITLE, 0, 0)
        mail = send_email(msg, data_token)
        if mail.get("error"):
            errors.append(f"correo de saldos y entregas: {mail['error']}")
        if saved or mail.get("status") == "sent":
            for id_control, notified in b_updates:
                flag, err, _ = set_balance_control_notified(id_control, notified, data_token)
                marks_written += 1 if flag else 0
                if not flag:
                    errors.append(f"marca saldos {id_control}: {err}")
            for id_control, notified in d_updates:
                flag, err, _ = set_delivery_control_notified(id_control, notified, data_token)
                marks_written += 1 if flag else 0
                if not flag:
                    errors.append(f"marca entregas {id_control}: {err}")
        else:
            errors.append(
                "no se pudo guardar la notificación ni enviar el correo de saldos y entregas; las marcas no se escribieron"
            )
    if t_lines:
        msg = "Notificaciones de sistema — Traslados con diferencias sin resolver\n" + "\n".join(t_lines)
        if not notify(msg, data_token, PERM_TRANSFERS, TITLE, 0, 0):
            errors.append("no se pudo guardar la notificación de traslados")
    write_log_file(
        log_file_admin_collecions,
        f"Barrido de avisos: {len(b_lines)} de saldos, {len(d_lines)} de entregas, {len(t_lines)} de traslados, "
        f"{marks_written} marcas, correo {mail.get('status')} a {mail.get('to')}"
        + (f"; errores: {errors}" if errors else ""),
        data_token,
    )
    return {
        "balance_lines": b_lines,
        "delivery_lines": d_lines,
        "transfer_lines": t_lines,
        "marks_written": marks_written,
        "email": mail,
        "errors": errors,
    }
