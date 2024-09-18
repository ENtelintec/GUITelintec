# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:15 $"

from flask_restx import Namespace, Resource

from static.Models.api_dashboards_models import (
    movements_charts_model,
    MovementsChartsForm,
)
from templates.resources.midleware.Functions_midleware_dashboard import (
    get_data_chart_movements,
)

ns = Namespace("GUI/api/v1/dashboard")


@ns.route("/inventory/movements")
class Notification(Resource):
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
