# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 18/sept/2024  at 17:15 $"

import hashlib
from datetime import datetime

import pytz
from flask import request
from flask_restx import Namespace, Resource

from static.Models.api_dashboards_models import (
    movements_charts_model,
    MovementsChartsForm,
    fichaje_emp_model,
    FichajeEmpForm,
)
from static.Models.api_models import expected_headers_per
from static.constants import (
    timezone_software,
    format_date,
    secrets,
)
from templates.Functions_Utils import read_flag_daemons, update_flag_daemons
from templates.daemons.NotificationsSearch import NotificationsSearch
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
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
        flag, data_token, msg = token_verification_procedure(
            request, department="almacen"
        )
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
        flag, data_token, msg = token_verification_procedure(
            request, department="almacen"
        )
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


@ns.route("/notifications/medicals")
class NotificationsMedicals(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        token = request.headers.get("Authorization", None)
        if token is None:
            return {"error": "No se encontro token"}, 401
        token_d = secrets["KEY_WEBAPP"]
        # haslib md5 token_d
        if token != hashlib.md5(token_d.encode()).hexdigest():
            return {"error": "Token invalido"}, 401

        flags_daemons = read_flag_daemons()
        if not flags_daemons.get("flag_medical", False):
            return {"msg": "Se esta ya realizando la busqueda de notificaciones"}, 200
        time_zone = pytz.timezone(timezone_software)
        timestamp = datetime.now(pytz.utc).astimezone(time_zone)
        last_date = flags_daemons.get("last_date_medicals", None)
        if last_date:
            last_date = datetime.strptime(last_date, format_date)
            last_date = time_zone.localize(last_date)
        if last_date is None or last_date.date() < timestamp.date():
            sercher = NotificationsSearch()
            sercher.start()
            update_flag_daemons(
                last_date_medicals=timestamp.strftime(format_date), flag_medical=False
            )
            return {"msg": "Buscando notificaciones medicas"}, 201
        else:
            return {
                "msg": "No hay notificaciones medicas o ya se realizo la busqueda hoy"
            }, 200
