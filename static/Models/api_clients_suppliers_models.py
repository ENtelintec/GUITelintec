# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 27/ene/2025  at 16:17 $"

from wtforms.form import Form
from wtforms.validators import InputRequired

from static.constants import api
from flask_restx import fields
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, EmailField

from wtforms import FieldList, FormField

# "id_customer, " # "name, " # "email, " # "phone, " # "rfc, " # "address "
client_model = api.model(
    "ClientAMC",
    {
        "id": fields.Integer(required=True, description="The client id"),
        "name": fields.String(required=True, description="The client name"),
        "email": fields.String(required=True, description="The client email"),
        "phone": fields.String(required=True, description="The client phone"),
        "rfc": fields.String(required=True, description="The client rfc"),
        "address": fields.String(required=True, description="The client address"),
    },
)

client_delete_model = api.model(
    "ClientDelete",
    {
        "id": fields.Integer(required=True, description="The client id"),
    },
)

extra_info_supplier_model = api.model(
    "EISupplier",
    {
        "brands": fields.List(fields.String(), required=True, default=[]),
    },
)

supplier_model = api.model(
    "SupplierAMC",
    {
        "id": fields.Integer(required=True, description="The supplier id"),
        "name": fields.String(required=True, description="The supplier name"),
        "seller_email": fields.String(
            required=True, description="The supplier seller email"
        ),
        "seller_name": fields.String(
            required=True, description="The supplier seller name"
        ),
        "phone": fields.String(required=True, description="The supplier phone"),
        "address": fields.String(required=True, description="The supplier address"),
        "web": fields.String(required=True, description="The supplier web url"),
        "type": fields.String(required=True, description="The supplier type"),
        "extra_info": fields.Nested(extra_info_supplier_model),
    },
)
suppliers_output_model = api.model(
    "SuppliersOutAMC",
    {
        "data": fields.List(fields.Nested(supplier_model)),
        "msg": fields.String(required=False, description="The message"),
        "error": fields.String(required=False, description="The error"),
    },
)
supplier_delete_model = api.model(
    "SupplierDelete",
    {
        "id": fields.Integer(required=True, description="The supplier id"),
    },
)


class ClientInsertForm(Form):
    name = StringField("name", validators=[InputRequired(message="Name is required")])
    email = EmailField("email", validators=[], default="None")
    phone = StringField(
        "phone", validators=[InputRequired(message="Phone is required")]
    )
    rfc = StringField("rfc", validators=[], default="None")
    address = StringField(
        "address", validators=[InputRequired(message="Address is required")]
    )


class ClientUpdateForm(Form):
    id = IntegerField("id", validators=[InputRequired(message="Id is required")])
    name = StringField("name", validators=[InputRequired(message="Name is required")])
    email = EmailField("email", validators=[], default="None")
    phone = StringField(
        "phone", validators=[InputRequired(message="Phone is required")]
    )
    rfc = StringField("rfc", validators=[], default="None")
    address = StringField(
        "address", validators=[InputRequired(message="Address is required")]
    )


class ClientDeleteForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )


class ExtraInfoSupplierForm(Form):
    brands = FieldList(StringField(validators=[], default=""), "brands")


class SupplierInsertForm(Form):
    name = StringField("name", validators=[InputRequired(message="Name is required")])
    seller_name = StringField("seller_name", validators=[], default="None")
    email = EmailField("email", validators=[InputRequired(message="Email is required")])
    phone = StringField(
        "phone", validators=[InputRequired(message="Phone is required")]
    )
    address = StringField(
        "address", validators=[InputRequired(message="Address is required")]
    )
    web_url = StringField(
        "web_url", validators=[InputRequired(message="Web url is required")]
    )
    type = StringField("type", validators=[InputRequired(message="Type is required")])
    extra_info = FormField(ExtraInfoSupplierForm, "extra_info")


class SupplierUpdateForm(Form):
    id = IntegerField("id", validators=[InputRequired(message="Id is required")])
    name = StringField("name", validators=[InputRequired(message="Name is required")])
    seller_name = StringField("seller_name", validators=[], default="None")
    email = EmailField("email", validators=[InputRequired(message="Email is required")])
    phone = StringField(
        "phone", validators=[InputRequired(message="Phone is required")]
    )
    address = StringField(
        "address", validators=[InputRequired(message="Address is required")]
    )
    web = StringField(
        "web", validators=[InputRequired(message="Web url is required")]
    )
    type = StringField("type", validators=[InputRequired(message="Type is required")])
    extra_info = FormField(ExtraInfoSupplierForm, "extra_info")


class SupplierDeleteForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
