# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 11/feb/2025  at 21:36 $"

from flask_restx import fields
from wtforms.fields.simple import StringField
from wtforms.form import Form
from wtforms.validators import InputRequired

from static.constants import api, format_timestamps, format_date

update_files_model = api.model(
    "UpdateFilesModel",
    {
        "year":  fields.String(
            required=True, description="The year of the file", example="2025"
        ),
        "month": fields.String(
            required=True, description="The month of the file", example="Enero"
        ),
        "quincena": fields.String(
            required=False, description="The quincena patter", example="1Q"
        ),
    },
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
        "from": fields.String(
            required=True, description="The email from", example="example@gmail.com"
        ),
        "xml":  fields.String(
            required=True, description="The xml file", example="xml_url"
        ),
        "pdf":  fields.String(
            required=True, description="The pdf file", example="pdf_url"
        ),
    },
)


class UpdateFilesForm(Form):
    year = StringField("year", validators=[InputRequired()])
    month = StringField("month", validators=[InputRequired()])
    quincena = StringField("quincena", validators=[], default="")


class CreateMailForm(Form):
    to = StringField("to", validators=[InputRequired()])
    subject = StringField("subject", validators=[InputRequired()])
    body = StringField("body", validators=[InputRequired()])
    emp_id = StringField("emp_id", validators=[InputRequired()])
    from_ = StringField("from", validators=[InputRequired()])
    xml = StringField("xml", validators=[InputRequired()])
    pdf = StringField("pdf", validators=[InputRequired()])