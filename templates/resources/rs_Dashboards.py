# -*- coding: utf-8 -*-

from datetime import datetime

import pytz
from flask import request
from flask_restx import Namespace, Resource

from static.constants import (
    format_date,
    timezone_software,
)
from static.Models.api_dashboards_models import (
    FichajeEmpForm,
    MovementsChartsForm,
    fichaje_emp_model,
    movements_charts_model,
)
from static.Models.api_models import expected_headers_per
from templates.daemons.NotificationsSearch import NotificationsSearch
from templates.Functions_Utils import read_flag_daemons, update_flag_daemons
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_midleware_dashboard import (
    get_data_chart_fichaje_emp,
    get_data_chart_movements,
    get_data_chart_sm,
)

__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:15 $"

ns = Namespace("GUI/api/v1/dashboard")


@ns.route("/inventory/movements")
class MovementenInventoryChart(Resource):
    @ns.expect(expected_headers_per, movements_charts_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="almacen"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = MovementsChartsForm.from_json(ns.payload) # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = get_data_chart_movements(data, data_token)
        return data_out, code


@ns.route("/inventory/sm/<string:range_g>/<string:type_chart>")
class SMChart(Resource):
    @ns.expect(expected_headers_per)
    def get(self, range_g, type_chart):
        flag, data_token, msg = token_verification_procedure(
            request, department="almacen"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data = {"range": range_g, "type_chart": type_chart}
        data_out, code = get_data_chart_sm(data, data_token)
        return data_out, code


@ns.route("/fichaje/emp")
class FichajeEmpChart(Resource):
    @ns.expect(expected_headers_per, fichaje_emp_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = FichajeEmpForm.from_json(ns.payload) # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = get_data_chart_fichaje_emp(data)
        return data_out, code


@ns.route("/notifications/medicals")
class NotificationsMedicals(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flags_daemons = read_flag_daemons()
        if not flags_daemons.get("flag_medical", False):
            return {"data": None, "msg": "Se está ya realizando la búsqueda de notificaciones", "error": None}, 200
        time_zone = pytz.timezone(timezone_software)
        timestamp = datetime.now(pytz.utc).astimezone(time_zone)
        last_date = flags_daemons.get("last_date_medicals", None)
        if last_date:
            last_date = datetime.strptime(last_date, format_date)
            last_date = time_zone.localize(last_date)
        if last_date is None or last_date.date() < timestamp.date():
            sercher = NotificationsSearch(data_token)
            sercher.start()
            update_flag_daemons(
                last_date_medicals=timestamp.strftime(format_date), flag_medical=False
            )
            return {"data": None, "msg": "Buscando notificaciones médicas", "error": None}, 201
        else:
            return {"data": None, "msg": "No hay notificaciones médicas o ya se realizó la búsqueda hoy", "error": None}, 200
