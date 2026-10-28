# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct./2026  at 19:00 $"

"""Check-in con foto tipo Wellhub (junta con Administración 2026-10-22, F8 de
docs/planes/plan_junta_2026_10_22.md; contrato en docs/checkin_foto.md).

Respaldo para cuando el biométrico no esté, simple a propósito:
- el empleado registra entrada/salida con foto obligatoria, hora del SERVIDOR y
  ubicación opcional; el back NO exige alternancia (acepta lo que llegue);
- RH ve todo, anula eventos (baja suave con motivo) y registra manuales sin foto;
- el resumen por empleado y día (primera entrada, última salida, horas) se
  calcula en lectura; nada se persiste agregado;
- fotos en S3_RH_BUCKET bajo checkins/<entorno>/<emp_id>/<fecha>/<epoch_ms>-<type>.<ext>
  (P-177; las de antes, sin <entorno>, siguen en photo_key).
`fichajes` (Excel del biométrico) se ignora.
"""

import io
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from decimal import Decimal

import boto3
import pytz
import xlsxwriter
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from PIL import Image, ImageOps

from static.constants import format_date, format_timestamps, log_file_rh, secrets, timezone_software
from templates.controllers.employees.checkins_controller import (
    CHECKIN_COLUMNS,
    DETAIL_COLUMNS,
    cancel_checkin,
    get_checkin_by_id,
    get_checkins,
    insert_checkin,
)
from templates.controllers.employees.employees_controller import test_id_employee
from templates.forms.CheckinsPDF import FileCheckinsPDF
from templates.misc.Functions_Files import write_log_file
from templates.resources.methods.Functions_Aux_S3 import s3_env_key

CHECKIN_TYPES = {0: "ENTRADA", 1: "SALIDA"}
CHECKIN_STATUSES = {0: "VALIDO", 1: "ANULADO"}
PHOTO_EXTENSIONS = ("jpg", "jpeg", "png", "webp")
DEFAULT_RANGE_DAYS = 30
MAX_RANGE_DAYS = 366
LIST_LIMIT = 5000
EXPORT_PDF_LIMIT = 200  # cada foto se baja de S3: el PDF pide acotar el rango antes
PHOTO_THUMB_PX = 400  # lado mayor de la foto reducida que va al PDF
PHOTO_WORKERS = 8
XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _now() -> datetime:
    return datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software))


def _json_safe(value):
    if isinstance(value, datetime):
        return value.strftime(format_timestamps)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _int_or_none(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _float_or_none(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _row_to_dict(row, detail: bool = False) -> dict:
    cols = DETAIL_COLUMNS if detail else CHECKIN_COLUMNS
    data = {col: _json_safe(val) for col, val in zip(cols, row)}
    data["type"] = _int_or_none(data.get("type"))
    data["type_label"] = CHECKIN_TYPES.get(data["type"] if data["type"] is not None else -1, "")
    data["status"] = _int_or_none(data.get("status")) or 0
    data["status_label"] = CHECKIN_STATUSES.get(data["status"], "")
    data["manual"] = bool(data.get("manual"))
    data["has_photo"] = bool(data.get("photo_key"))
    data["emp_name"] = " ".join(x for x in (str(data.get("emp_name") or "").strip(), str(data.get("emp_lastname") or "").strip()) if x).upper()
    data.pop("emp_lastname", None)
    if detail:
        import json

        for key in ("history", "extra_info"):
            raw = data.get(key)
            if isinstance(raw, str):
                try:
                    data[key] = json.loads(raw)
                except ValueError:
                    data[key] = None
    return data


def _history_entry(user, action: str, comment: str) -> dict:
    return {"timestamp": _now().strftime(format_timestamps), "user": user, "action": action, "comment": comment}


def _parse_range(params: dict) -> tuple[str, str, str | None]:
    """(date_from, date_to, error). Default: últimos DEFAULT_RANGE_DAYS días hasta hoy.
    Con error las fechas vienen vacías."""
    today = _now().date()
    raw_to = str(params.get("date_to") or "").strip()
    raw_from = str(params.get("date_from") or "").strip()
    try:
        date_to = datetime.strptime(raw_to, format_date).date() if raw_to else today
        date_from = datetime.strptime(raw_from, format_date).date() if raw_from else date_to - timedelta(days=DEFAULT_RANGE_DAYS)
    except ValueError:
        return "", "", "date_from / date_to deben ser fechas YYYY-MM-DD"
    if date_from > date_to:
        return "", "", "date_from no puede ser posterior a date_to"
    if (date_to - date_from).days > MAX_RANGE_DAYS:
        return "", "", f"el rango no puede superar {MAX_RANGE_DAYS} días"
    return date_from.isoformat(), date_to.isoformat(), None


def _status_filter(params: dict):
    """Sin `all`: solo válidos (status 0). all=1 -> todos."""
    return None if str(params.get("all") or "").lower() in ("1", "true", "yes") else 0


def _employee_status(emp_id, data_token) -> tuple[str | None, bool]:
    """(status del empleado, existe)."""
    flag, _e, row = test_id_employee(int(emp_id), data_token)
    if not flag or not isinstance(row, (list, tuple)) or len(row) == 0:
        return None, False
    return (str(row[1]).strip().lower() if row[1] is not None else None), True


def _photo_key(emp_id: int, when: datetime, type_code: int, ext: str, data_token) -> str:
    rest = f"{emp_id}/{when.strftime('%Y-%m-%d')}/{int(time.time() * 1000)}-{type_code}.{ext}"
    return s3_env_key("checkins", rest, data_token)


# --- Empleado ------------------------------------------------------------------------------
def create_checkin_api(data: dict, data_token):
    """POST /common/checkin (multipart). El evento es siempre del emp_id del token;
    la hora la pone el servidor. Foto obligatoria; lat/lon/accuracy opcionales."""
    emp_id = _int_or_none(data_token.get("emp_id"))
    if not emp_id:
        return {"data": None, "msg": "El token no trae empleado (emp_id)", "error": "sin emp_id"}, 400
    type_code = _int_or_none(data.get("type"))
    if type_code is None or type_code not in CHECKIN_TYPES:
        return {"data": None, "msg": "type inválido", "error": ["type debe ser 0 (ENTRADA) o 1 (SALIDA)"]}, 400
    type_code = int(type_code)
    filename = str(data.get("filename") or "")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if not data.get("filepath") or ext not in PHOTO_EXTENSIONS:
        return {
            "data": None,
            "msg": "La foto es obligatoria",
            "error": [f"file: se requiere una imagen {', '.join(PHOTO_EXTENSIONS)} (recibido: '{filename or 'nada'}')"],
        }, 400
    lat, lon, accuracy = _float_or_none(data.get("lat")), _float_or_none(data.get("lon")), _float_or_none(data.get("accuracy"))
    errors = []
    if lat is not None and not -90 <= lat <= 90:
        errors.append("lat fuera de rango (-90..90)")
    if lon is not None and not -180 <= lon <= 180:
        errors.append("lon fuera de rango (-180..180)")
    if (lat is None) != (lon is None):
        errors.append("lat y lon van juntas")
    if errors:
        return {"data": None, "msg": "Ubicación inválida", "error": errors}, 400
    status, exists = _employee_status(emp_id, data_token)
    if not exists:
        return {"data": None, "msg": f"El empleado {emp_id} del token no existe", "error": "empleado no encontrado"}, 404
    now = _now()
    key = _photo_key(emp_id, now, type_code, ext, data_token)
    bucket = str(secrets.get("S3_RH_BUCKET"))
    try:
        boto3.client("s3").upload_file(Filename=data["filepath"], Bucket=bucket, Key=key)
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no configuradas", "error": None}, 400
    except (ClientError, BotoCoreError) as e:
        return {"data": None, "msg": "Error al subir la foto a S3", "error": str(e)}, 400
    device_info = str(data.get("device_info") or "").strip()[:255] or None
    row = {
        "emp_id": emp_id,
        "type": type_code,
        "timestamp": now.strftime(format_timestamps),
        "lat": lat,
        "lon": lon,
        "accuracy": accuracy,
        "photo_key": key,
        "manual": False,
        "created_by": emp_id,
        "device_info": device_info,
        "history": [_history_entry(emp_id, "Registro", f"{CHECKIN_TYPES[type_code]} con foto desde la app")],
    }
    flag, error, id_checkin = insert_checkin(row, data_token)
    if not flag:
        return {"data": None, "msg": "La foto se subió pero no se pudo guardar el registro", "error": error}, 400
    msg = f"{CHECKIN_TYPES[type_code]} registrada para el empleado {emp_id} a las {row['timestamp']} (ID {id_checkin})"
    write_log_file(log_file_rh, msg, data_token)
    return {
        "data": {
            "id": id_checkin,
            "emp_id": emp_id,
            "type": type_code,
            "type_label": CHECKIN_TYPES[type_code],
            "timestamp": row["timestamp"],
            "lat": lat,
            "lon": lon,
            "accuracy": accuracy,
            "photo_key": key,
            "employee_status": status,
        },
        "msg": msg,
        "error": None,
    }, 201


def get_my_checkins_api(params: dict, data_token):
    """GET /common/checkin/me?date_from&date_to&all=1: eventos propios."""
    emp_id = _int_or_none(data_token.get("emp_id"))
    if not emp_id:
        return {"data": None, "msg": "El token no trae empleado (emp_id)", "error": "sin emp_id"}, 400
    date_from, date_to, err = _parse_range(params)
    if err:
        return {"data": None, "msg": "Rango inválido", "error": [err]}, 400
    flag, error, rows = get_checkins(emp_id, date_from, date_to, _status_filter(params), LIST_LIMIT, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron consultar los registros", "error": error}, 400
    events = [_row_to_dict(r) for r in rows]
    return {
        "data": {"emp_id": emp_id, "date_from": date_from, "date_to": date_to, "events": events, "summary": build_daily_summary(events)},
        "msg": None,
        "error": None,
    }, 200


# --- RH ---------------------------------------------------------------------------------------
def _hhmm(when: datetime | None) -> str | None:
    return when.strftime("%H:%M") if when else None


def _hours(seconds: float) -> float:
    return round(seconds / 3600, 2)


def _pair_segments(day_events: list) -> list:
    """Tramos (entrada, salida) de un día ya ordenado: cada ENTRADA abre un tramo y
    la SALIDA siguiente lo cierra. Una ENTRADA con otro tramo abierto deja ese sin
    salida; una SALIDA sin tramo abierto queda sin entrada (None en el hueco)."""
    segments = []
    open_in = None
    for when, _id, type_code in day_events:
        if type_code == 0:
            if open_in is not None:
                segments.append((open_in, None))
            open_in = when
        elif open_in is None:
            segments.append((None, when))
        else:
            segments.append((open_in, when))
            open_in = None
    if open_in is not None:
        segments.append((open_in, None))
    return segments


def build_daily_summary(events: list) -> list:
    """Por empleado y día (solo eventos válidos), con los tramos entrada -> salida
    del día (`segments`, ver _pair_segments). `hours` = suma de los tramos
    cerrados (descuenta comida y salidas intermedias); `span_hours` = de la
    primera ENTRADA a la última SALIDA posterior (el `hours` de antes del
    2026-10-28); `incomplete` = algún tramo sin entrada o sin salida. Calculado en
    lectura; sin retardos ni tolerancias."""
    buckets: dict = {}
    for ev in events:
        if ev.get("status") != 0 or ev.get("type") not in CHECKIN_TYPES:
            continue
        try:
            when = datetime.strptime(str(ev["timestamp"]), format_timestamps)
        except (TypeError, ValueError):
            continue
        key = (int(ev["emp_id"]), when.date().isoformat())
        bucket = buckets.setdefault(key, {"emp_name": ev.get("emp_name") or "", "events": []})
        bucket["events"].append((when, _int_or_none(ev.get("id")) or 0, ev["type"]))
    out = []
    for (emp_id, day), b in sorted(buckets.items(), key=lambda kv: (kv[0][1], kv[0][0]), reverse=True):
        day_events = sorted(b["events"])
        segments = _pair_segments(day_events)
        closed = [(a, z) for a, z in segments if a and z]
        ins = [w for w, _id, t in day_events if t == 0]
        first_in = ins[0] if ins else None
        later_outs = [w for w, _id, t in day_events if t == 1 and (first_in is None or w >= first_in)]
        last_out = later_outs[-1] if later_outs else None
        out.append({
            "emp_id": emp_id,
            "emp_name": b["emp_name"],
            "date": day,
            "first_in": _hhmm(first_in),
            "last_out": _hhmm(last_out),
            "hours": _hours(sum((z - a).total_seconds() for a, z in closed)) if closed else None,
            "span_hours": _hours((last_out - first_in).total_seconds()) if first_in and last_out else None,
            "segments": [
                {"in": _hhmm(a), "out": _hhmm(z), "hours": _hours((z - a).total_seconds()) if a and z else None}
                for a, z in segments
            ],
            "events_count": len(day_events),
            "incomplete": len(closed) < len(segments),
        })
    return out


def _rh_filters(params: dict):
    """Filtros de RH (emp_id opcional + rango). (emp_id, date_from, date_to, envelope de error | None)."""
    emp_id = _int_or_none(params.get("emp_id"))
    if params.get("emp_id") not in (None, "") and emp_id is None:
        return None, "", "", {"data": None, "msg": "emp_id inválido", "error": ["emp_id debe ser entero"]}
    date_from, date_to, err = _parse_range(params)
    if err:
        return None, "", "", {"data": None, "msg": "Rango inválido", "error": [err]}
    return emp_id, date_from, date_to, None


def get_checkins_api(params: dict, data_token):
    """GET /rrhh/checkins?emp_id&date_from&date_to&all=1 -> eventos + resumen por día."""
    emp_id, date_from, date_to, invalid = _rh_filters(params)
    if invalid is not None:
        return invalid, 400
    flag, error, rows = get_checkins(emp_id, date_from, date_to, _status_filter(params), LIST_LIMIT, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron consultar los registros", "error": error}, 400
    events = [_row_to_dict(r) for r in rows]
    return {
        "data": {
            "date_from": date_from,
            "date_to": date_to,
            "events": events,
            "summary": build_daily_summary(events),
            "meta": {"returned": len(events), "limit": LIST_LIMIT, "truncated": len(events) >= LIST_LIMIT},
        },
        "msg": None,
        "error": None,
    }, 200


def create_manual_checkin_api(data: dict, data_token):
    """POST /rrhh/checkin: RH registra un evento por el empleado (olvidó fichar),
    sin foto, con la hora capturada (no futura) y motivo obligatorio."""
    emp_id = int(data["emp_id"])
    type_code = _int_or_none(data.get("type"))
    if type_code is None or type_code not in CHECKIN_TYPES:
        return {"data": None, "msg": "type inválido", "error": ["type debe ser 0 (ENTRADA) o 1 (SALIDA)"]}, 400
    type_code = int(type_code)
    raw_ts = str(data.get("timestamp") or "").strip()
    try:
        when = datetime.strptime(raw_ts, format_timestamps)
    except ValueError:
        try:
            when = datetime.strptime(raw_ts, "%Y-%m-%d %H:%M")
        except ValueError:
            return {"data": None, "msg": "timestamp inválido", "error": ["timestamp debe ser YYYY-MM-DD HH:MM:SS"]}, 400
    now = _now().replace(tzinfo=None)
    if when > now:
        return {"data": None, "msg": "timestamp inválido", "error": [f"timestamp {raw_ts} es futuro (hora del servidor {now.strftime(format_timestamps)})"]}, 400
    reason = str(data.get("reason") or "").strip()
    if not reason:
        return {"data": None, "msg": "Falta el motivo", "error": ["reason es obligatorio en un registro manual"]}, 400
    _status, exists = _employee_status(emp_id, data_token)
    if not exists:
        return {"data": None, "msg": f"No existe el empleado {emp_id}", "error": "empleado no encontrado"}, 404
    user = data_token.get("emp_id")
    row = {
        "emp_id": emp_id,
        "type": type_code,
        "timestamp": when.strftime(format_timestamps),
        "manual": True,
        "created_by": user,
        "history": [_history_entry(user, "Registro manual", f"{CHECKIN_TYPES[type_code]} registrada por RH. Motivo: {reason}")],
    }
    flag, error, id_checkin = insert_checkin(row, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo guardar el registro manual", "error": error}, 400
    msg = f"{CHECKIN_TYPES[type_code]} manual registrada por RH ({user}) para el empleado {emp_id} a las {row['timestamp']} (ID {id_checkin}): {reason}"
    write_log_file(log_file_rh, msg, data_token)
    return {
        "data": {"id": id_checkin, "emp_id": emp_id, "type": type_code, "type_label": CHECKIN_TYPES[type_code],
                 "timestamp": row["timestamp"], "manual": True, "photo_key": None},
        "msg": msg,
        "error": None,
    }, 201


def cancel_checkin_api(data: dict, data_token):
    """PUT /rrhh/checkin/cancel: baja suave (status 1) con motivo; no se borra."""
    id_checkin = int(data["id"])
    reason = str(data.get("reason") or "").strip()
    if not reason:
        return {"data": None, "msg": "Falta el motivo", "error": ["reason es obligatorio para anular"]}, 400
    flag, error, row = get_checkin_by_id(id_checkin, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo consultar el registro", "error": error}, 400
    if row is None:
        return {"data": None, "msg": f"No existe el registro {id_checkin}", "error": "registro no encontrado"}, 404
    current = _row_to_dict(row, detail=True)
    if current["status"] == 1:
        return {"data": {"id": id_checkin, "status": 1}, "msg": f"El registro {id_checkin} ya estaba anulado", "error": "ya anulado"}, 400
    user = data_token.get("emp_id")
    flag, error, rows = cancel_checkin(id_checkin, _history_entry(user, "Anulación", f"Anulado por RH. Motivo: {reason}"), data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo anular el registro", "error": error}, 400
    if not rows:
        return {"data": {"id": id_checkin, "status": 1}, "msg": f"El registro {id_checkin} ya estaba anulado", "error": "ya anulado"}, 400
    msg = f"Registro de check-in {id_checkin} ({current['type_label']} del empleado {current['emp_id']} a las {current['timestamp']}) anulado por RH ({user}): {reason}"
    write_log_file(log_file_rh, msg, data_token)
    return {"data": {"id": id_checkin, "emp_id": current["emp_id"], "status": 1, "status_label": CHECKIN_STATUSES[1]}, "msg": msg, "error": None}, 200


def download_checkin_photo_api(id_checkin: int, data_token, only_own: bool = False):
    """Devuelve (envelope|None, local_path|None, code). Baja la foto a un temp.
    only_own: el empleado solo ve las suyas (GET /common/checkin/<id>/photo)."""
    flag, error, row = get_checkin_by_id(id_checkin, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo consultar el registro", "error": error}, None, 400
    if row is None:
        return {"data": None, "msg": f"No existe el registro {id_checkin}", "error": "registro no encontrado"}, None, 404
    current = _row_to_dict(row, detail=True)
    if only_own and _int_or_none(data_token.get("emp_id")) != _int_or_none(current.get("emp_id")):
        return {"data": None, "msg": "El registro no es del empleado del token", "error": "sin permiso"}, None, 403
    if not current.get("photo_key"):
        return {"data": None, "msg": f"El registro {id_checkin} no tiene foto (registro manual)", "error": "sin foto"}, None, 404
    local = os.path.join(tempfile.mkdtemp(), os.path.basename(current["photo_key"]))
    try:
        boto3.client("s3").download_file(Bucket=str(secrets.get("S3_RH_BUCKET")), Key=current["photo_key"], Filename=local)
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no configuradas", "error": None}, None, 400
    except (ClientError, BotoCoreError) as e:
        return {"data": None, "msg": "No se pudo descargar la foto de S3", "error": str(e)}, None, 400
    return None, local, 200


def get_checkin_catalogs_api():
    return {
        "data": {
            "types": [{"code": k, "label": v} for k, v in CHECKIN_TYPES.items()],
            "statuses": [{"code": k, "label": v} for k, v in CHECKIN_STATUSES.items()],
            "photo_extensions": list(PHOTO_EXTENSIONS),
            "default_range_days": DEFAULT_RANGE_DAYS,
        },
        "msg": None,
        "error": None,
    }, 200


# --- Exportar (RH): Excel solo datos y PDF con foto -----------------------------------------
def _events_for_export(params: dict, data_token, limit: int):
    """Mismos filtros que GET /rrhh/checkins. (envelope de error | None, eventos por
    empleado y en orden cronológico, filtros, code). Más de `limit` -> 400; sin
    eventos -> 404 (no se entrega un archivo vacío)."""
    emp_id, date_from, date_to, invalid = _rh_filters(params)
    if invalid is not None:
        return invalid, [], {}, 400
    status = _status_filter(params)
    flag, error, rows = get_checkins(emp_id, date_from, date_to, status, limit + 1, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron consultar los registros", "error": error}, [], {}, 400
    if len(rows) > limit:
        return {
            "data": None,
            "msg": f"Demasiados registros para exportar (más de {limit})",
            "error": [f"el archivo admite hasta {limit} registros: acota el rango de fechas o elige un empleado"],
        }, [], {}, 400
    if not rows:
        return {"data": None, "msg": "No hay registros en el rango", "error": "sin registros"}, [], {}, 404
    events = sorted((_row_to_dict(r) for r in rows), key=lambda e: (e["emp_name"], e["emp_id"], e["timestamp"], e["id"]))
    filters = {"emp_id": emp_id, "date_from": date_from, "date_to": date_to, "all": status is None}
    return None, events, filters, 200


def _export_summary(events: list) -> list:
    """Resumen por día en el orden de los archivos (empleado, fecha ascendente)."""
    return sorted(build_daily_summary(events), key=lambda s: (s["emp_name"], s["emp_id"], s["date"]))


def _export_filename(filters: dict, ext: str) -> str:
    emp = f"emp{filters['emp_id']}_" if filters.get("emp_id") else ""
    return f"checkins_{emp}{filters['date_from']}_{filters['date_to']}.{ext}"


def _segments_text(segments: list) -> str:
    """`08:00–13:00, 14:00–sin salida`."""
    return ", ".join(f"{s['in'] or 'sin entrada'}–{s['out'] or 'sin salida'}" for s in segments)


def _maps_url(ev: dict) -> str | None:
    return f"https://www.google.com/maps?q={ev['lat']},{ev['lon']}" if ev.get("lat") is not None and ev.get("lon") is not None else None


def export_checkins_excel_api(params: dict, data_token):
    """GET /rrhh/checkins/download/excel: hojas Registros y Resumen (solo datos,
    sin fotos). (envelope | None, (buffer, nombre) | None, code)."""
    envelope, events, filters, code = _events_for_export(params, data_token, LIST_LIMIT)
    if envelope is not None:
        return envelope, None, code
    buffer = io.BytesIO()
    book = xlsxwriter.Workbook(buffer, {"in_memory": True})
    header = book.add_format({"bold": True, "bg_color": "#BDD7EE", "border": 1})
    sheet = book.add_worksheet("Registros")
    columns = ["ID", "Empleado ID", "Empleado", "Fecha", "Hora", "Tipo", "Estado", "Origen", "Latitud", "Longitud",
               "Precisión (m)", "Mapa", "Foto", "Dispositivo", "Registrado"]
    widths = [8, 12, 32, 12, 10, 10, 10, 11, 12, 12, 13, 11, 6, 40, 20]
    for col, (name, width) in enumerate(zip(columns, widths)):
        sheet.write(0, col, name, header)
        sheet.set_column(col, col, width)
    for row, ev in enumerate(events, start=1):
        stamp = str(ev["timestamp"])
        values = [ev["id"], ev["emp_id"], ev["emp_name"], stamp[:10], stamp[11:19], ev["type_label"], ev["status_label"],
                  "Manual RH" if ev["manual"] else "App", ev.get("lat"), ev.get("lon"), ev.get("accuracy"), None,
                  "Sí" if ev["has_photo"] else "No", ev.get("device_info"), ev.get("created_at")]
        sheet.write_row(row, 0, values)
        url = _maps_url(ev)
        if url:
            sheet.write_url(row, 11, url, string="Ver mapa")
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, len(events), len(columns) - 1)

    summary = _export_summary(events)
    sheet = book.add_worksheet("Resumen")
    columns = ["Empleado ID", "Empleado", "Fecha", "Primera entrada", "Última salida", "Tramos", "Horas trabajadas",
               "Permanencia (h)", "Registros", "Incompleto"]
    widths = [12, 32, 12, 15, 14, 40, 16, 15, 10, 11]
    for col, (name, width) in enumerate(zip(columns, widths)):
        sheet.write(0, col, name, header)
        sheet.set_column(col, col, width)
    for row, s in enumerate(summary, start=1):
        sheet.write_row(row, 0, [s["emp_id"], s["emp_name"], s["date"], s["first_in"], s["last_out"], _segments_text(s["segments"]),
                                 s["hours"], s["span_hours"], s["events_count"], "Sí" if s["incomplete"] else "No"])
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, max(len(summary), 1), len(columns) - 1)
    book.close()
    buffer.seek(0)
    return None, (buffer, _export_filename(filters, "xlsx")), 200


def _photo_thumbnail(raw: bytes) -> bytes:
    """JPEG reducido (lado mayor PHOTO_THUMB_PX), con la rotación EXIF aplicada."""
    with Image.open(io.BytesIO(raw)) as img:
        small = (ImageOps.exif_transpose(img) or img).convert("RGB")
    small.thumbnail((PHOTO_THUMB_PX, PHOTO_THUMB_PX))
    out = io.BytesIO()
    small.save(out, format="JPEG", quality=75)
    return out.getvalue()


def _load_thumbnails(events: list) -> dict:
    """{id: jpeg reducido} de los eventos con foto, en paralelo. Una foto que no
    baja de S3 o no abre se queda fuera (el PDF pone "Foto no disponible")."""
    with_photo = [ev for ev in events if ev.get("photo_key")]
    if not with_photo:
        return {}
    s3_client = boto3.client("s3")
    bucket = str(secrets.get("S3_RH_BUCKET"))

    def fetch(ev):
        try:
            raw = s3_client.get_object(Bucket=bucket, Key=ev["photo_key"])["Body"].read()
            return ev["id"], _photo_thumbnail(raw)
        except (ClientError, BotoCoreError, OSError, ValueError, Image.DecompressionBombError):
            return ev["id"], None

    with ThreadPoolExecutor(max_workers=PHOTO_WORKERS) as pool:
        return {id_checkin: thumb for id_checkin, thumb in pool.map(fetch, with_photo) if thumb}


def export_checkins_pdf_api(params: dict, data_token):
    """GET /rrhh/checkins/download/pdf: resumen por día + cada registro con su foto
    (hasta EXPORT_PDF_LIMIT). (envelope | None, (buffer, nombre) | None, code)."""
    envelope, events, filters, code = _events_for_export(params, data_token, EXPORT_PDF_LIMIT)
    if envelope is not None:
        return envelope, None, code
    photos = _load_thumbnails(events)
    summary = _export_summary(events)
    employee = "Todos"
    if filters["emp_id"]:
        employee = f"{events[0]['emp_name'] or 'Empleado'} (ID {filters['emp_id']})"
    with_photo = sum(1 for ev in events if ev.get("photo_key"))
    buffer = io.BytesIO()
    FileCheckinsPDF({
        "filename_out": buffer,
        "period": f"{filters['date_from']} a {filters['date_to']}",
        "employee": employee,
        "include_cancelled": filters["all"],
        "generated_at": _now().strftime("%Y-%m-%d %H:%M"),
        "photos_text": f"{len(photos)} de {with_photo}" + (f" ({with_photo - len(photos)} no disponibles)" if len(photos) < with_photo else ""),
        "summary": [dict(s, segments_text=_segments_text(s["segments"])) for s in summary],
        "events": [dict(ev, maps_url=_maps_url(ev)) for ev in events],
        "photos": photos,
    })
    buffer.seek(0)
    return None, (buffer, _export_filename(filters, "pdf")), 200
