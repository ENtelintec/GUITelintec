# -*- coding: utf-8 -*-

import os
import tempfile

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_models import (
    expected_headers_per,
)
from static.Models.api_payroll_models import RequestFileForm, request_file_model
from static.Models.api_checkin_models import expected_files_checkin
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.MD_Checkin import (
    create_checkin_api,
    download_checkin_photo_api,
    get_checkin_catalogs_api,
    get_my_checkins_api,
)
from templates.resources.midleware.Functions_DB_midleware import (
    get_employees_directory_with_status,
)
from templates.resources.midleware.Functions_midleware_admin import get_contracts_catalog
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
        return send_file(data_out, mimetype="application/zip", as_attachment=True, download_name="docs.zip") # pyrefly: ignore


@ns.route("/vacations/events")
class VacationsEvents(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["common", "basic"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401

        data_out, code = get_all_vacations_data_date(data_token)
        return data_out, code


@ns.route("/employees/<string:status>")
class EmployeesDirectory(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(request, department="common")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_employees_directory_with_status(status, data_token)
        return data_out, code


@ns.route("/contracts")
class ContractsCatalog(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="common")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_contracts_catalog(data_token)
        return data_out, code


# --- Check-in con foto (docs/checkin_foto.md): el empleado sobre si mismo -----------------
_CK_EMP = ["common", "basic"]


@ns.route("/checkin")
class CheckinSelf(Resource):
    @ns.expect(expected_headers_per, expected_files_checkin)
    def post(self):
        """Registra ENTRADA (0) o SALIDA (1) del empleado del token con foto obligatoria; la hora la pone el servidor."""
        flag, data_token, msg = token_verification_procedure(request, department=_CK_EMP)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        file = request.files.get("file")
        filepath, filename = None, ""
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath)
        data = {
            "type": request.form.get("type"),
            "lat": request.form.get("lat"),
            "lon": request.form.get("lon"),
            "accuracy": request.form.get("accuracy"),
            "device_info": request.form.get("device_info") or request.headers.get("User-Agent", ""),
            "filename": filename,
            "filepath": filepath,
        }
        data_out, code = create_checkin_api(data, data_token)
        return data_out, code


@ns.route("/checkin/me")
class CheckinMine(Resource):
    @ns.doc(params={"date_from": "YYYY-MM-DD (default: 30 dias atras)", "date_to": "YYYY-MM-DD (default hoy)", "all": "1 -> incluye anulados"})
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=_CK_EMP)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        params = {"date_from": request.args.get("date_from"), "date_to": request.args.get("date_to"), "all": request.args.get("all")}
        data_out, code = get_my_checkins_api(params, data_token)
        return data_out, code


@ns.route("/checkin/catalogs")
class CheckinCatalogs(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=_CK_EMP)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_checkin_catalogs_api()
        return data_out, code


@ns.route("/checkin/<int:id_checkin>/photo")
class CheckinPhotoSelf(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_checkin):
        """Foto de un registro PROPIO (blob en 200; envelope en 4xx)."""
        flag, data_token, msg = token_verification_procedure(request, department=_CK_EMP)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        envelope, local_path, code = download_checkin_photo_api(id_checkin, data_token, only_own=True)
        if envelope is not None or not local_path:
            return envelope, code
        return send_file(local_path, as_attachment=True, download_name=os.path.basename(local_path))
