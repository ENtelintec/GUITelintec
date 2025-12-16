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
        "user": fields.String(required=True, description="The user name"),
    },
)


permission_model = api.model(
    "PermissionModel",
    {
        "permission": fields.String(required=True, description="The permission"),
        "description": fields.String(required=True, description="The description"),
    },
)

post_user_model = api.model(
    "PostUser", {
        "permissions": fields.List(fields.Nested(permission_model), required=True, description="The permissions"),
        "emp_id": fields.Integer(required=True, description="The employee ID"),
        "name": fields.String(required=True, description="The name"),
        "contract": fields.String(required=True, description="The contract"),
        "user": fields.String(required=True, description="The user name"),
        "dep_id": fields.Integer(required=True, description="The department ID"),
        "hashpass": fields.String(required=True, description="The hashed password")
    }
)


class TokenModelForm(Form):
    username = StringField("username", validators=[InputRequired()])
    password = PasswordField("password", validators=[InputRequired()])


class BiocredentialsPutModelForm(Form):
    emp_id = StringField("emp_id", validators=[InputRequired()])
    biocredentials = StringField("biocredentials", validators=[InputRequired()])
    user = StringField("user", validators=[InputRequired()])


class PostUserModelForm(Form):
    permissions = StringField("permissions", validators=[InputRequired()])
    emp_id = StringField("emp_id", validators=[InputRequired()])
    name = StringField("name", validators=[InputRequired()])
    contract = StringField("contract", validators=[InputRequired()])
    user = StringField("user", validators=[InputRequired()])
    dep_id = StringField("dep_id", validators=[InputRequired()])
    hashpass = StringField("hashpass", validators=[InputRequired()])
