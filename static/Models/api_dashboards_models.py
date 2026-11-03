# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:17 $"

from flask_restx import fields
from wtforms import IntegerField, StringField
from wtforms.form import Form
from wtforms.validators import InputRequired, Optional

from static.constants import api

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


# --- Dashboard RH (docs/dashboard_rrhh.md) ----------------------------------
rrhh_series_model = api.model(
    "RRHHSeries",
    {
        "metric": fields.String(
            required=True,
            description="KPI a graficar: altas_bajas | headcount",
            example="altas_bajas",
        ),
        "date_from": fields.String(required=True, description="Inicio inclusivo YYYY-MM-DD", example="2026-01-01"),
        "date_to": fields.String(required=True, description="Fin inclusivo YYYY-MM-DD", example="2026-09-30"),
        "group_by": fields.String(
            required=False,
            description="month (default) | department",
            example="month",
        ),
    },
)


class RRHHSeriesForm(Form):
    metric = StringField("metric", validators=[InputRequired()])
    date_from = StringField("date_from", validators=[InputRequired()])
    date_to = StringField("date_to", validators=[InputRequired()])
    # Ausente/null → el midleware asume "month" (wtforms_json no aplica el default a un null).
    group_by = StringField("group_by", validators=[Optional()], default="month")
