# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 17/sep./2026  at 12:00 $"

"""Correo saliente por AWS SES (boto3). Ver Docs/nomina_correo_ses.md.

Configuracion en .env (secrets): SES_SENDER (obligatorio, identidad verificada
en SES; sin el, is_ses_configured() es False y los canales de correo se
reportan como pendientes), SES_REGION (opcional; default = region de boto),
SES_REPLY_TO (opcional). Las credenciales son las mismas que usa S3.
"""

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from static.constants import secrets

MAX_ATTACHMENTS_BYTES = 9 * 1024 * 1024  # SES rechaza mensajes > 10 MB (raw, ya codificado)


def is_ses_configured() -> bool:
    return bool((secrets.get("SES_SENDER") or "").strip())


def _ses_client():
    region = (secrets.get("SES_REGION") or "").strip()
    return boto3.client("ses", region_name=region) if region else boto3.client("ses")


def send_email_ses(to: list, subject: str, body_text: str, attachments=None, body_html: str | None = None):
    """Envia un correo (texto + html opcional + adjuntos) por SES send_raw_email.
    attachments: [(filename, bytes)]. Devuelve (ok, error, message_id)."""
    if not is_ses_configured():
        return False, "SES no configurado: falta SES_SENDER en .env", None
    recipients = [str(t).strip() for t in (to or []) if str(t).strip()]
    if not recipients:
        return False, "Sin destinatarios", None
    sender = str(secrets.get("SES_SENDER")).strip()
    attachments = attachments or []
    total = sum(len(content) for _name, content in attachments)
    if total > MAX_ATTACHMENTS_BYTES:
        return False, f"Adjuntos demasiado grandes para SES ({total} bytes > {MAX_ATTACHMENTS_BYTES})", None

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    reply_to = (secrets.get("SES_REPLY_TO") or "").strip()
    if reply_to:
        msg["Reply-To"] = reply_to
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body_text or "", "plain", "utf-8"))
    if body_html:
        alt.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(alt)
    for filename, content in attachments:
        part = MIMEApplication(content)
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)
    try:
        resp = _ses_client().send_raw_email(
            Source=sender, Destinations=recipients, RawMessage={"Data": msg.as_bytes()}
        )
    except NoCredentialsError:
        return False, "Credenciales AWS no configuradas", None
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        detail = e.response.get("Error", {}).get("Message", str(e))
        if code == "MessageRejected":
            return False, f"SES rechazó el mensaje: {detail} (¿remitente/destinatario verificados? ¿sandbox?)", None
        return False, f"Error SES ({code}): {detail}", None
    except BotoCoreError as e:
        return False, f"Error SES: {e}", None
    return True, None, resp.get("MessageId")
