# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/jun./2024  at 16:23 $"

from werkzeug.datastructures import FileStorage
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import EmailField, StringField
from wtforms.form import Form
from wtforms.validators import InputRequired

from static.constants import api
from static.Models.api_models import date_filter

expected_files = api.parser()
expected_files.add_argument("file", type=FileStorage, location="files", required=True)


class EmployeeInputForm(Form):
    name = StringField("name", validators=[InputRequired()])
    lastname = StringField("lastname", validators=[InputRequired()])
    phone = StringField("phone", validators=[InputRequired()])
    dep = IntegerField("dep", validators=[InputRequired()])
    modality = StringField("modality", validators=[InputRequired()])
    email = EmailField("email", validators=[InputRequired()])
    contract = StringField("contract", validators=[InputRequired()])
    admission = DateField(
        "admission", validators=[InputRequired()], filters=[date_filter]
    )
    rfc = StringField("rfc", validators=[InputRequired()])
    curp = StringField("curp", validators=[InputRequired()])
    nss = StringField("nss", validators=[InputRequired()])
    emergency = StringField("emergency", validators=[InputRequired()])
    position = StringField("position", validators=[InputRequired()])
    status = StringField("status", validators=[InputRequired()])
    departure = StringField("departure", validators=[InputRequired()])
    birthday = DateField(
        "birthday", validators=[InputRequired()], filters=[date_filter]
    )
    legajo = StringField("legajo", validators=[InputRequired()])
