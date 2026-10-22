# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct./2026  at 19:00 $"

"""Check-in con foto (docs/checkin_foto.md): parser multipart del empleado,
forms de RH (manual y anulación) y api.model para swagger."""

from flask_restx import fields
from werkzeug.datastructures import FileStorage
from wtforms import IntegerField, StringField
from wtforms.form import Form
from wtforms.validators import InputRequired

from static.constants import api

# POST /common/checkin — multipart, una foto por request (regla del repo).
expected_files_checkin = api.parser()
expected_files_checkin.add_argument("file", type=FileStorage, location="files", required=True, help="Foto (jpg/jpeg/png/webp), obligatoria")
expected_files_checkin.add_argument("type", type=int, location="form", required=True, help="0 entrada · 1 salida")
expected_files_checkin.add_argument("lat", type=float, location="form", required=False, help="Latitud (opcional)")
expected_files_checkin.add_argument("lon", type=float, location="form", required=False, help="Longitud (opcional)")
expected_files_checkin.add_argument("accuracy", type=float, location="form", required=False, help="Precisión en metros (opcional)")
expected_files_checkin.add_argument("device_info", type=str, location="form", required=False, help="Dispositivo / user-agent (opcional, ≤ 255)")

checkin_manual_model = api.model(
    "CheckinManual",
    {
        "emp_id": fields.Integer(required=True, description="Empleado al que RH le registra el evento", example=36),
        "type": fields.Integer(required=True, description="0 entrada · 1 salida", example=0),
        "timestamp": fields.String(required=True, description="Hora del evento, YYYY-MM-DD HH:MM:SS (no futura)", example="2026-10-22 08:05:00"),
        "reason": fields.String(required=True, description="Motivo (olvidó fichar, sin señal, etc.); queda en history", example="Olvidó registrar la entrada"),
    },
)

checkin_cancel_model = api.model(
    "CheckinCancel",
    {
        "id": fields.Integer(required=True, description="Evento a anular (status 1, no se borra)", example=120),
        "reason": fields.String(required=True, description="Motivo; queda en history", example="Registro duplicado"),
    },
)


class CheckinManualForm(Form):
    emp_id = IntegerField("emp_id", [InputRequired(message="emp_id requerido")])
    type = IntegerField("type", [], default=None)
    timestamp = StringField("timestamp", [InputRequired(message="timestamp requerido")])
    reason = StringField("reason", [InputRequired(message="reason requerido")])


class CheckinCancelForm(Form):
    id = IntegerField("id", [InputRequired(message="id requerido")])
    reason = StringField("reason", [InputRequired(message="reason requerido")])
