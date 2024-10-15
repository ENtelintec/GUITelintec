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
from templates.resources.methods.Functions_Aux_Login import verify_token
from templates.resources.midleware.Functions_midleware_RRHH import (
    get_files_list_nomina,
    download_nomina_doc,
)

ns = Namespace("GUI/api/v1/common")


@ns.route("/payroll/employee/<int:emp_id>")
class ListFilesPayroll(Resource):
    @ns.expect(expected_headers_per)
    def get(self, emp_id):
        try:
            flag, data_token = verify_token(
                request.headers["Authorization"], emp_id=emp_id
            )
            if not flag:
                return {"data": None, "msg": "Token invalido"}, 401
        except KeyError:
            return {"data": None, "msg": "No Authorization"}, 401
        code, data_out = get_files_list_nomina(emp_id)
        if code != 200:
            return {"data": None, "msg": "No files"}, code
        return {"data": data_out, "msg": "ok"}, code


@ns.route("/payroll/employee/file")
class DownloadFilesPayroll(Resource):
    @ns.expect(request_file_model, expected_headers_per)
    def post(self):
        validator = RequestFileForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        try:
            flag, data_token = verify_token(
                request.headers["Authorization"], emp_id=data["emp_id"]
            )
            if not flag:
                return {"data": None, "msg": "Token invalido"}, 401
        except KeyError:
            return {"data": None, "msg": "No Authorization"}, 401
        print(data)
        filepath, code = download_nomina_doc(data)
        if code != 200:
            return {"data": None, "msg": "No files"}, code
        return send_file(filepath, as_attachment=True)
