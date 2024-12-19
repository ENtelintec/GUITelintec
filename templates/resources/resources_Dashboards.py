# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:15 $"

from flask import request
from flask_restx import Namespace, Resource

from static.Models.api_dashboards_models import (
    movements_charts_model,
    MovementsChartsForm,
    fichaje_emp_model,
    FichajeEmpForm,
)
from static.Models.api_models import expected_headers_per
from templates.resources.methods.Functions_Aux_Login import verify_token, token_verification_procedure
from templates.resources.midleware.Functions_midleware_dashboard import (
    get_data_chart_movements,
    get_data_chart_sm,
    get_data_chart_fichaje_emp,
)

ns = Namespace("GUI/api/v1/dashboard")


@ns.route("/inventory/movements")
class MovementenInventoryChart(Resource):
    @ns.expect(expected_headers_per, movements_charts_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = MovementsChartsForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_chart, code = get_data_chart_movements(data)
        if code == 200:
            return data_chart, 200
        else:
            return {"message": f"Error al obtener los datos {data_chart}"}, 400


@ns.route("/inventory/sm/<string:range_g>/<string:type_chart>")
class SMChart(Resource):
    @ns.expect(expected_headers_per)
    def get(self, range_g, type_chart):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        data = {"range": range_g, "type_chart": type_chart}
        data_chart, code = get_data_chart_sm(data)
        if code == 200:
            return data_chart, 200
        else:
            return {"message": f"Error al obtener los datos {data_chart}"}, 400


@ns.route("/fichaje/emp")
class FichajeEmpChart(Resource):
    @ns.expect(expected_headers_per, fichaje_emp_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeEmpForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_chart, code = get_data_chart_fichaje_emp(data)
        if code == 200:
            return data_chart, 200
        else:
            return {"message": f"Error al obtener los datos {data_chart}"}, 400
