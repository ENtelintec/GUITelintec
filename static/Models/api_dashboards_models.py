# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:17 $"


from static.extensions import api
from flask_restx import fields
from wtforms.validators import InputRequired
from wtforms import IntegerField, StringField
from wtforms.form import Form


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


class MovementsChartsForm(Form):
    type_m = StringField("type_m", validators=[InputRequired()])
    n_products = IntegerField("n_products", validators=[InputRequired()])
