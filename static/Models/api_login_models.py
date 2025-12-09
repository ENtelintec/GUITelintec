# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/ago/2024  at 18:01 $"

from flask_restx import fields
from static.constants import api
from wtforms.fields.simple import StringField, PasswordField
from wtforms.form import Form
from wtforms.validators import InputRequired


token_model = api.model(
    "Token",
    {
        "username": fields.String(required=True, description="The username"),
        "password": fields.String(
            required=True, description="The password or pass_key"
        ),
    },
)

put_biocredentials_model = api.model(
    "Biocredentials",
    {
        "emp_id": fields.Integer(required=True, description="The employee ID"),
        "biocredentials": fields.Integer(
            required=True, description="The biocredentials status"
        ),
    },
)

class TokenModelForm(Form):
    username = StringField("username", validators=[InputRequired()])
    password = PasswordField("password", validators=[InputRequired()])


class BiocredentialsPutModelForm(Form):
    emp_id = StringField("emp_id", validators=[InputRequired()])
    biocredentials = StringField("biocredentials", validators=[InputRequired()])
