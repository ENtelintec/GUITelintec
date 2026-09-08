# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 11/feb/2025  at 21:36 $"

from flask_restx import fields
from werkzeug.datastructures import FileStorage
from wtforms import FieldList
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField
from wtforms.form import Form
from wtforms.validators import AnyOf, InputRequired, Optional

from static.constants import api
from static.Models.api_models import validate_json

# Multipart parser: payroll file uploaded straight to the S3 RH bucket under
# payroll/<year>/<month>/<emp_id>/<filename>. Replaces the old SharePoint scan model.
update_files_parser = api.parser()
update_files_parser.add_argument(
    "file",
    type=FileStorage,
    location="files",
    required=True,
    help="Archivo de nomina (pdf o xml)",
)
update_files_parser.add_argument(
    "year", type=str, location="form", required=True, help="Anio, ej. 2025"
)
update_files_parser.add_argument(
    "month", type=str, location="form", required=True, help="Mes 01-12"
)
update_files_parser.add_argument(
    "emp_id", type=str, location="form", required=True, help="Id del empleado"
)
update_files_parser.add_argument(
    "key",
    type=str,
    location="form",
    required=True,
    help="Identificador de la nomina (agrupa pdf y xml)",
)

create_mail_model = api.model(
    "CreateMailModel",
    {
        "to": fields.String(
            required=True, description="The email to send", example="example@gmail.com"
        ),
        "subject": fields.String(
            required=True, description="The subject of the email", example="Subject"
        ),
        "body": fields.String(
            required=True, description="The body of the email", example="Body"
        ),
        "emp_id": fields.Integer(
            required=True, description="The employee id", example=0
        ),
        "from_": fields.String(
            required=True, description="The email from", example="example@gmail.com"
        ),
        "xml": fields.String(
            required=True, description="The xml file", example="xml_url"
        ),
        "pdf": fields.String(
            required=True, description="The pdf file", example="pdf_url"
        ),
    },
)

update_data_payroll_model = api.model(
    "UpdateDataPayroll",
    {
        "id": fields.Integer(required=True, description="The id of the employee"),
        "data_dict": fields.String(
            required=True, description="The data of the employee", default="{}"
        ),
    },
)

request_file_model = api.model(
    "RequestFile",
    {
        "emp_id":  fields.Integer(required=True, description="The employee id"),
        "pdf": fields.String(required=True, description="The file pdf url"),
        "xml": fields.String(required=True, description="The file xml url"),
    },
)

# Multipart: XML de CFDI de nomina para sugerir empleado/periodo (no sube nada).
extract_xml_parser = api.parser()
extract_xml_parser.add_argument(
    "file",
    type=FileStorage,
    location="files",
    required=True,
    help="XML de CFDI de nomina",
)

# --- Gestion de archivos de nomina (2026-09-07, docs/nomina_gestion_archivos_y_notificacion.md)
delete_payroll_file_model = api.model(
    "DeletePayrollFile",
    {
        "emp_id": fields.Integer(required=True, description="Id del empleado", example=34),
        "year": fields.Integer(required=True, description="Anio del periodo", example=2026),
        "month": fields.Integer(required=True, description="Mes 1-12 (se normaliza a 2 digitos)", example=9),
        "key": fields.String(
            required=True,
            description="Identificador de la nomina (agrupa pdf+xml), el mismo del POST",
            example="2026-09-Q1",
        ),
        "kind": fields.String(
            required=False,
            description="pdf | xml | both (default both)",
            example="both",
        ),
    },
)

notify_payroll_model = api.model(
    "NotifyPayroll",
    {
        "emp_id": fields.Integer(required=True, description="Id del empleado", example=34),
        "year": fields.Integer(required=True, description="Anio del periodo", example=2026),
        "month": fields.Integer(required=True, description="Mes 1-12", example=9),
        "key": fields.String(required=True, description="Identificador de la nomina", example="2026-09-Q1"),
        "message": fields.String(
            required=False,
            description="Texto de la notificacion (default: 'Tu recibo de nomina <key> (<mes>/<anio>) ya esta disponible...')",
        ),
        "channels": fields.List(
            fields.String,
            required=False,
            description="Canales: ['app'] (default). 'email' se acepta y se reporta como pendiente (2a etapa)",
            example=["app"],
        ),
    },
)


class CreateMailForm(Form):
    to = StringField("to", validators=[InputRequired()])
    subject = StringField("subject", validators=[InputRequired()])
    body = StringField("body", validators=[InputRequired()])
    emp_id = StringField("emp_id", validators=[InputRequired()])
    from_ = StringField("from_", validators=[InputRequired()])
    xml = StringField("xml", validators=[InputRequired()])
    pdf = StringField("pdf", validators=[InputRequired()])


class UpdateDataPayrollForm(Form):
    id = StringField("id", validators=[InputRequired()])
    data_dict = StringField("data_dict", validators=[validate_json])


class RequestFileForm(Form):
    emp_id = IntegerField("emp_id", validators=[InputRequired()])
    pdf = StringField("pdf", validators=[InputRequired()])
    xml = StringField("xml", validators=[InputRequired()])


class DeletePayrollFileForm(Form):
    emp_id = IntegerField("emp_id", validators=[InputRequired()])
    year = IntegerField("year", validators=[InputRequired()])
    month = IntegerField("month", validators=[InputRequired()])
    key = StringField("key", validators=[InputRequired()])
    # null explicito de JSON llega como None (wtforms_json no aplica el default):
    # el midleware trata None como "both".
    kind = StringField(
        "kind", validators=[Optional(), AnyOf(["pdf", "xml", "both"])], default="both"
    )


class NotifyPayrollForm(Form):
    emp_id = IntegerField("emp_id", validators=[InputRequired()])
    year = IntegerField("year", validators=[InputRequired()])
    month = IntegerField("month", validators=[InputRequired()])
    key = StringField("key", validators=[InputRequired()])
    message = StringField("message", validators=[Optional()], default=None)
    # Ausente/null llega como [] (wtforms_json ignora el default de FieldList):
    # el midleware trata la lista vacia como ["app"].
    channels = FieldList(StringField(), validators=[])
