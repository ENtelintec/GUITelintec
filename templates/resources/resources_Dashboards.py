# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:15 $"

from flask_restx import Namespace, Resource

from static.Models.api_dashboards_models import (
    movements_charts_model,
    MovementsChartsForm,
    fichaje_emp_model,
    FichajeEmpForm,
)
from templates.resources.midleware.Functions_midleware_dashboard import (
    get_data_chart_movements,
    get_data_chart_sm,
    get_data_chart_fichaje_emp,
)

ns = Namespace("GUI/api/v1/dashboard")


@ns.route("/inventory/movements")
class MovementenInventoryChart(Resource):
    @ns.expect(movements_charts_model)
    def post(self):
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
    def get(self, range_g, type_chart):
        data = {"range": range_g, "type_chart": type_chart}
        data_chart, code = get_data_chart_sm(data)
        if code == 200:
            return data_chart, 200
        else:
            return {"message": f"Error al obtener los datos {data_chart}"}, 400


@ns.route("/fichaje/emp")
class FichajeEmpChart(Resource):
    @ns.expect(fichaje_emp_model)
    def post(self):
        validator = FichajeEmpForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_chart, code = get_data_chart_fichaje_emp(data)
        if code == 200:
            return data_chart, 200
        else:
            return {"message": f"Error al obtener los datos {data_chart}"}, 400
