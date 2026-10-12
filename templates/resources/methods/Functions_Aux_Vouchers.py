# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 12/oct./2026  at 12:00 $"

"""Anexos de los 3 tipos de vale (checklist vehicular, EPP, herramientas) con una
sola receta (docs/checklist_vehicular_anexos_sin_carrera.md, P-103):

  * el vale se carga por id, sin ventana de fecha;
  * el archivo debe llamarse "<id del vale>-<archivo>";
  * el objeto sube a S3 una vez (llave determinista) y la lista
    `extra_info.files` + el history se escriben en UNA sentencia condicional:
    si otra subida cambio la lista entre la lectura y la escritura, se re-lee y
    se recalcula; tras FILES_WRITE_ATTEMPTS intentos responde 409.

Los midleware (MD_SGI, MD_SGI_Vouchers) solo eligen el `kind`.
"""

import json
import random
import time
from datetime import datetime
from typing import Any

import boto3
import pytz
from botocore.exceptions import ClientError, NoCredentialsError

from static.constants import (
    format_timestamps,
    log_file_sgi_chv,
    log_file_sgi_vouchers,
    secrets,
    timezone_software,
)
from templates.controllers.vouchers.vouchers_controller import (
    VEHICLE_VOUCHER_CANCELLED_STATUS,
    get_voucher_head,
    update_voucher_files,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.misc.Functions_Files import write_log_file

# Por tipo de vale: tabla (la resuelve el controller por `kind`), prefijo S3,
# `type` de la entrada del history, firmas -> status y status "cancelado" (solo
# el vehicular lo tiene; una firma no lo reactiva).
VOUCHER_FILE_KINDS: dict[str, dict[str, Any]] = {
    "vehicle": {
        "label": "vehicular",
        "s3_prefix": "checklistV",
        "history_type": 2,
        "signatures": (("firma-aprobado", 1, "aprobado"), ("firma-recibido", 2, "recibido")),
        "cancelled_status": VEHICLE_VOUCHER_CANCELLED_STATUS,
        "log_file": log_file_sgi_chv,
    },
    "epp": {
        "label": "EPP",
        "s3_prefix": "eppVoucher",
        "history_type": 1,
        "signatures": (
            ("firma-aprobado", 1, "aprobado"),
            ("firma-despachado", 2, "despachado"),
            ("firma-recibido", 3, "recibido"),
        ),
        "cancelled_status": None,
        "log_file": log_file_sgi_vouchers,
    },
    "tools": {
        "label": "de herramientas",
        "s3_prefix": "toolsVoucher",
        "history_type": 0,
        "signatures": (
            ("firma-aprobado", 1, "aprobado"),
            ("firma-despachado", 2, "despachado"),
            ("firma-recibido", 3, "recibido"),
        ),
        "cancelled_status": None,
        "log_file": log_file_sgi_vouchers,
    },
}
VALID_ATTACHMENT_EXTENSIONS = ("pdf", "jpg", "jpeg", "png", "zip", "webp")
# Intentos de la escritura condicional de `files` antes de responder 409.
FILES_WRITE_ATTEMPTS = 8


def files_retry_pause(attempt: int):
    # Espera aleatoria creciente: sin ella, N subidas simultaneas reintentan al
    # mismo tiempo y vuelven a chocar (peor caso ~1.4 s en total).
    time.sleep(random.uniform(0, 0.05 * attempt))


def _json_object(value) -> dict:
    """extra_info de BD -> dict (tolera NULL, texto y el doble-codificado de filas viejas)."""
    result = value
    for _ in range(2):
        if not isinstance(result, str):
            break
        try:
            result = json.loads(result)
        except (ValueError, TypeError):
            return {}
    return result if isinstance(result, dict) else {}


def load_voucher(kind: str, id_voucher, data_token):
    """
    Carga la cabecera de un vale por id, **sin ventana de fecha**. Devuelve
    ``(payload_error, code, head)``: si ``payload_error`` no es ``None`` el
    llamador responde ``(payload_error, code)`` tal cual. ``head`` =
    ``{"id", "date", "extra_info", "status", "files"}``.
    """
    label = VOUCHER_FILE_KINDS[kind]["label"]
    try:
        id_voucher = int(id_voucher)
    except (TypeError, ValueError) as e:
        return {"data": None, "msg": "ID de voucher inválido", "error": str(e)}, 400, None
    if id_voucher <= 0:
        return {"data": None, "msg": "ID de voucher inválido", "error": None}, 400, None
    flag, error, row = get_voucher_head(kind, id_voucher, data_token)
    if not flag:
        return {"data": None, "msg": f"No se pudo obtener el voucher {label}", "error": error}, 400, None
    if not isinstance(row, (tuple, list)) or len(row) == 0 or row[0] is None:
        return {"data": None, "msg": f"Voucher {label} no encontrado (ID {id_voucher})", "error": None}, 404, None
    extra_info = _json_object(row[2])
    files = extra_info.get("files")
    head: dict[str, Any] = {
        "id": int(row[0]),  # pyrefly: ignore
        "date": row[1],
        "extra_info": extra_info,
        "status": row[3],
        "files": files if isinstance(files, list) else [],
    }
    return None, 200, head


def _upload_to_s3(filepath, key):
    """Sube el archivo; devuelve (payload_error, code) o (None, 201)."""
    bucket_name = secrets.get("S3_CH_BUCKET")
    try:
        boto3.client("s3").upload_file(Filename=filepath, Bucket=str(bucket_name), Key=key)
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no encontradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        if error_code == "AccessDenied":
            return {"data": None, "msg": f"Acceso denegado al bucket: {bucket_name}", "error": str(e)}, 400
        return {"data": None, "msg": f"Error AWS: {str(e)}", "error": str(e)}, 400
    return None, 201


def attach_voucher_file(kind: str, data: dict, data_token):
    """
    Alta de un anexo: ``data = {"id_voucher", "filename", "filepath"}``.
    Respuesta 201 ``{"data": <llave S3>, "msg", "error": None}`` (mismo shape
    de siempre); 400 validaciones; 404 vale inexistente; 409 contención.
    """
    cfg = VOUCHER_FILE_KINDS[kind]
    filename = data["filename"]
    payload_error, code, head = load_voucher(kind, data.get("id_voucher"), data_token)
    if payload_error is not None:
        return payload_error, code
    id_voucher = head["id"]  # pyrefly: ignore
    # Los anexos se nombran "<id del vale>-<archivo>" (asi los sube el front y
    # asi estan en BD). Antes la condicion llevaba `and` y nunca rechazaba.
    try:
        id_in_name = int(filename.split("-")[0])
    except ValueError as e:
        return {
            "data": None,
            "msg": "Error al procesar el nombre del archivo (debe empezar con el id del voucher: <id>-<archivo>)",
            "error": str(e),
        }, 400
    if id_in_name != id_voucher:
        return {
            "data": None,
            "msg": f"El nombre del archivo no corresponde al voucher (empieza con {id_in_name}, el voucher es {id_voucher})",
            "error": None,
        }, 400
    filepath = data["filepath"]
    if filepath.split(".")[-1].lower() not in VALID_ATTACHMENT_EXTENSIONS:
        return {"data": None, "msg": "Formato de archivo no válido", "error": None}, 400
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    date_voucher = head["date"]  # pyrefly: ignore
    path_aws = f"{cfg['s3_prefix']}/{date_voucher.strftime('%Y/%m/%d/')}{filename}"
    payload_error, code = _upload_to_s3(filepath, path_aws)
    if payload_error is not None:
        return payload_error, code
    # status solo se escribe si la firma lo cambia (la ultima firma del nombre
    # manda, como siempre); un vale cancelado no se reactiva (CASE en SQL).
    status_signature, status_label = None, ""
    for marker, status_value, label in cfg["signatures"]:
        if marker in filename.lower():
            status_signature, status_label = status_value, label
    new_entry = {"filename": filename, "path": path_aws, "timestamp": timestamp}
    msg = ""
    for attempt in range(FILES_WRITE_ATTEMPTS):
        if attempt > 0:
            files_retry_pause(attempt)
            payload_error, code, head = load_voucher(kind, id_voucher, data_token)
            if payload_error is not None:
                return payload_error, code
        files = head["files"]  # pyrefly: ignore
        msg = f"Archivo adjunto agregado: {filename} al voucher {id_voucher} por el empleado {data_token.get('name')}"
        status = status_signature
        if status is not None:
            if cfg["cancelled_status"] is not None and head["status"] == cfg["cancelled_status"]:  # pyrefly: ignore
                status = None
                msg += " (voucher cancelado: el estado no cambia)"
            else:
                msg += f" y estado actualizado a ({status_label})"
        # Re-subir el mismo archivo reemplaza su entrada en vez de duplicarla
        # (misma llave S3: el objeto ya se sobreescribio).
        replaced = any(file.get("path") == path_aws for file in files)
        new_files = [file for file in files if file.get("path") != path_aws]
        if replaced:
            msg += " (reemplaza el archivo previo con el mismo nombre)"
        new_files.append(new_entry)
        history_entry = {
            "id_voucher": id_voucher,
            "type": cfg["history_type"],
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": f"Archivo adjunto agregado: {path_aws}",
        }
        flag, error, rows_updated = update_voucher_files(
            kind,
            id_voucher,
            history_entry,
            new_files,
            data_token,
            status=status,
            expected_files=files,
            cancelled_status=cfg["cancelled_status"],
        )
        if not flag:
            return {
                "data": None,
                "msg": "Error al actualizar el historial del voucher (archivo ya subido)",
                "error": error,
            }, 400
        if rows_updated:
            break
    else:
        return {
            "data": None,
            "msg": (
                "La lista de anexos cambió mientras se guardaba (subidas simultáneas). "
                "El archivo ya está en S3: vuelve a subirlo con el mismo nombre"
            ),
            "error": "conflicto de escritura en files",
        }, 409
    create_notification_permission_notGUI(
        msg, data_token, ["administracion", "operaciones", "sgi"], data_token.get("emp_id"), 0
    )
    write_log_file(cfg["log_file"], msg, data_token)
    return {"data": path_aws, "msg": msg, "error": None}, 201
