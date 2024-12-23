# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/sept/2024  at 17:06 $"

from flask import request, send_file
from flask_restx import Namespace, Resource

from static.Models.api_models import (
    expected_headers_per,
    request_file_model,
    RequestFileForm,
)
from templates.resources.methods.Functions_Aux_Login import verify_token, token_verification_procedure
from templates.resources.midleware.Functions_midleware_RRHH import (
    get_files_list_nomina,
    download_nomina_doc,
)

ns = Namespace("GUI/api/v1/common")


@ns.route("/payroll/employee/<int:emp_id>")
class ListFilesPayroll(Resource):
    @ns.expect(expected_headers_per)
    def get(self, emp_id):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh", emp_id=emp_id)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        code, data_out = get_files_list_nomina(emp_id)
        if code != 200:
            return {"data": None, "msg": "No files"}, code
        return {"data": data_out, "msg": "ok"}, code


@ns.route("/payroll/employee/file")
class DownloadFilesPayroll(Resource):
    @ns.expect(request_file_model, expected_headers_per)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = RequestFileForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        flag, data_token, msg = token_verification_procedure(request, emp_id=data["emp_id"], department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        filepath, code = download_nomina_doc(data)
        if code != 200:
            return {"data": None, "msg": "No files"}, code
        return send_file(filepath, as_attachment=True)
