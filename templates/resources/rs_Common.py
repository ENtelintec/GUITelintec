# -*- coding: utf-8 -*-

from flask import request, send_file
from flask_restx import Namespace, Resource

from static.Models.api_models import (
    expected_headers_per,
)
from static.Models.api_payroll_models import RequestFileForm, request_file_model
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_midleware_misc import (
    get_all_vacations_data_date,
)
from templates.resources.midleware.Functions_midleware_RRHH import (
    download_nomina_docs,
    get_files_list_nomina,
)

__author__ = "Edisson Naula"
__date__ = "$ 20/sept/2024  at 17:06 $"

ns = Namespace("GUI/api/v1/common")


@ns.route("/payroll/employee/<int:emp_id>")
class ListFilesPayroll(Resource):
    @ns.expect(expected_headers_per)
    def get(self, emp_id):
        flag, data_token, msg = token_verification_procedure(
            request, department="rrhh", emp_id=emp_id
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_files_list_nomina(emp_id, data_token)
        return data_out, code


@ns.route("/payroll/employee/file")
class DownloadFilesPayroll(Resource):
    @ns.expect(request_file_model, expected_headers_per)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = RequestFileForm.from_json(ns.payload) # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        flag, data_token, msg = token_verification_procedure(
            request, emp_id=data["emp_id"], department="rrhh"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = download_nomina_docs(data, data_token)
        if code != 200:
            return data_out, code
        return send_file(data_out, as_attachment=True) # pyrefly: ignore


@ns.route("/vacations/events")
class VacationsEvents(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["common", "basic"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401

        data_out, code = get_all_vacations_data_date(data_token)
        return data_out, code
