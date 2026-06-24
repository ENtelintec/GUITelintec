import json
from datetime import datetime, timedelta

import boto3
import pytz
from botocore.client import ClientError
from botocore.exceptions import NoCredentialsError

from static.constants import (
    format_date,
    format_timestamps,
    log_file_sgi_vouchers,
    secrets,
    timezone_software,
)
from templates.controllers.vouchers.vouchers_controller import (
    get_vouchers_safety_with_items,
    update_voucher_epp_files,
    update_voucher_tools_files,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.misc.Functions_Files import write_log_file

__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"


def create_voucher_epp_attachment_api(data, data_token):
    """{"filepath": filepath_download, "filename": filename}, data_token"""
    filename = data["filename"]
    id_voucher_name = filename.split("-")[0]
    try:
        if int(id_voucher_name) != int(data["id_voucher"]) and int(data["id_voucher"]) <= 0:
            return {"data": None, "msg": "El nombre del archivo no corresponde al voucher", "error": None}, 400
    except Exception as e:
        return {"data": None, "msg": "Error al procesar el nombre del archivo", "error": str(e)}, 400
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    timestamp_year_ago = timestamp - timedelta(days=365)
    flag, error, result = get_vouchers_safety_with_items(
        timestamp_year_ago.strftime(format_date), data_token, data_token.get("emp_id")
    )
    if not flag:
        return {"data": None, "msg": "No se pudo obtener el voucher EPP", "error": str(error)}, 400
    if not isinstance(result, list):
        return {"data": None, "msg": "Error al obtener el voucher EPP: resultado inesperado", "error": str(result)}, 400
    voucher_data = []
    for item in result:
        if int(item[0]) == int(data["id_voucher"]):
            voucher_data = item
            break
    if len(voucher_data) <= 0:
        return {"data": None, "msg": "Voucher EPP no encontrado", "error": str(voucher_data)}, 400
    date_voucher = voucher_data[2]
    history = json.loads(voucher_data[14])
    filepath_down = data["filepath"]
    file_extension = filepath_down.split(".")[-1].lower()
    valid_extension = ["pdf", "jpg", "jpeg", "png", "zip", "webp"]
    if file_extension not in valid_extension:
        return {"data": None, "msg": "Formato de archivo no válido", "error": None}, 400
    path_aws = f"eppVoucher/{date_voucher.strftime('%Y/%m/%d/')}{data['filename']}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_CH_BUCKET")
    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=str(bucket_name), Key=path_aws)
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no encontradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Acceso denegado al bucket: {bucket_name}", "error": str(e)}, 400
        else:
            return {"data": None, "msg": f"Error AWS: {str(e)}", "error": str(e)}, 400
    msg = f"Archivo adjunto agregado: {filename} al voucher {data['id_voucher']} por el empleado {data_token.get('name')}"
    status = voucher_data[15]
    if "firma-aprobado" in filename.lower():
        status = 1
        msg += " y estado actualizado a (aprobado)"
    if "firma-despachado" in filename.lower():
        status = 2
        msg += " y estado actualizado a (despachado)"
    if "firma-recibido" in filename.lower():
        status = 3
        msg += " y estado actualizado a (recibido)"
    history.append(
        {
            "id_voucher": data["id_voucher"],
            "type": 1,
            "timestamp": timestamp.strftime(format_timestamps),
            "user": data_token.get("emp_id"),
            "comment": f"Archivo adjunto agregado: {path_aws}",
        }
    )
    extra_info = json.loads(voucher_data[12])
    files = extra_info.get("files", [])
    files.append({"filename": data["filename"], "path": path_aws})
    extra_info["files"] = files
    flag, error, rows_updated = update_voucher_epp_files(
        data["id_voucher"], history, extra_info, status, data_token
    )
    if not flag:
        return {"data": None, "msg": "Error al actualizar el historial del voucher (archivo ya subido)", "error": str(error)}, 400
    create_notification_permission_notGUI(
        msg, data_token, ["administracion", "operaciones", "sgi"], data_token.get("emp_id"), 0
    )
    write_log_file(log_file_sgi_vouchers, msg, data_token)
    return {"data": path_aws, "msg": msg, "error": None}, 201


def create_voucher_tools_attachment_api(data, data_token):
    """{"filepath": filepath_download, "filename": filename}, data_token"""
    filename = data["filename"]
    id_voucher_name = filename.split("-")[0]
    try:
        if int(id_voucher_name) != int(data["id_voucher"]) and int(data["id_voucher"]) <= 0:
            return {"data": None, "msg": "El nombre del archivo no corresponde al voucher", "error": None}, 400
    except Exception as e:
        return {"data": None, "msg": "Error al procesar el nombre del archivo", "error": str(e)}, 400
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    timestamp_year_ago = timestamp - timedelta(days=365)
    flag, error, result = get_vouchers_safety_with_items(
        timestamp_year_ago.strftime(format_date), data_token, data_token.get("emp_id")
    )
    if not flag:
        return {"data": None, "msg": "No se pudo obtener el voucher de herramientas", "error": str(error)}, 400
    if not isinstance(result, list):
        return {"data": None, "msg": "Error al obtener el voucher de herramientas: resultado inesperado", "error": str(result)}, 400
    voucher_data = []
    for item in result:
        if int(item[0]) == int(data["id_voucher"]):
            voucher_data = item
            break
    if len(voucher_data) <= 0:
        return {"data": None, "msg": "Voucher de herramientas no encontrado", "error": str(voucher_data)}, 400
    date_voucher = voucher_data[2]
    history = json.loads(voucher_data[15])
    filepath_down = data["filepath"]
    file_extension = filepath_down.split(".")[-1].lower()
    valid_extension = ["pdf", "jpg", "jpeg", "png", "zip", "webp"]
    if file_extension not in valid_extension:
        return {"data": None, "msg": "Formato de archivo no válido", "error": None}, 400
    path_aws = f"toolsVoucher/{date_voucher.strftime('%Y/%m/%d/')}{data['filename']}"
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_CH_BUCKET")
    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=str(bucket_name), Key=path_aws)
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no encontradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Acceso denegado al bucket: {bucket_name}", "error": str(e)}, 400
        else:
            return {"data": None, "msg": f"Error AWS: {str(e)}", "error": str(e)}, 400
    msg = f"Archivo adjunto agregado: {filename} al voucher {data['id_voucher']} por el empleado {data_token.get('name')}"
    status = voucher_data[16]
    if "firma-aprobado" in filename.lower():
        status = 1
        msg += " y estado actualizado a (aprobado)"
    if "firma-despachado" in filename.lower():
        status = 2
        msg += " y estado actualizado a (despachado)"
    if "firma-recibido" in filename.lower():
        status = 3
        msg += " y estado actualizado a (recibido)"
    history.append(
        {
            "id_voucher": data["id_voucher"],
            "type": 0,
            "timestamp": timestamp.strftime(format_timestamps),
            "user": data_token.get("emp_id"),
            "comment": f"Archivo adjunto agregado: {path_aws}",
        }
    )
    extra_info = json.loads(voucher_data[13])
    files = extra_info.get("files", [])
    files.append({"filename": data["filename"], "path": path_aws})
    extra_info["files"] = files
    flag, error, rows_updated = update_voucher_tools_files(
        data["id_voucher"], history, extra_info, status, data_token
    )
    if not flag:
        return {"data": None, "msg": "Error al actualizar el historial del voucher (archivo ya subido)", "error": str(error)}, 400
    create_notification_permission_notGUI(
        msg, data_token, ["administracion", "operaciones", "sgi"], data_token.get("emp_id"), 0
    )
    write_log_file(log_file_sgi_vouchers, msg, data_token)
    return {"data": path_aws, "msg": msg, "error": None}, 201
