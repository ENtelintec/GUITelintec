# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:17 $"

from flask_restx import fields
from wtforms import IntegerField, StringField
from wtforms.form import Form
from wtforms.validators import InputRequired, NumberRange

from static.constants import api
from static.Models.api_models import date_filter

movements_charts_model = api.model(
    "MovementsCharts",
    {
        "type_m": fields.String(
            required=True, description="The type_m", example="Entrada"
        ),
        "n_products": fields.Integer(
            required=True, description="The number if products to retrieve", example=10
        ),
    },
)


fichaje_emp_model = api.model(
    "FichajeEmp",
    {
        "emp_id": fields.Integer(required=True, description="The emp_id", example=1),
        "date": fields.String(
            required=True,
            description="Date from where the events are counted",
            example="2023-01-01",
        ),
    },
)


class MovementsChartsForm(Form):
    type_m = StringField("type_m", validators=[InputRequired()])
    n_products = IntegerField("n_products", validators=[InputRequired()])


class FichajeEmpForm(Form):
    emp_id = IntegerField(
        "emp_id",
        validators=[
            InputRequired(message="id required or value 0 not acepted"),
            NumberRange(min=-1),
        ],
    )
    date = StringField("date", validators=[InputRequired()], filters=[date_filter])
