# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:17 $"


from static.extensions import api, format_date
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


def date_filter(datetime_obj):
    return (
        datetime_obj.strftime(format_date)
        if not isinstance(datetime_obj, str)
        else datetime_obj
    )


class MovementsChartsForm(Form):
    type_m = StringField("type_m", validators=[InputRequired()])
    n_products = IntegerField("n_products", validators=[InputRequired()])


class FichajeEmpForm(Form):
    emp_id = IntegerField("emp_id", validators=[InputRequired()])
    date = StringField("date", validators=[InputRequired()], filters=[date_filter])
