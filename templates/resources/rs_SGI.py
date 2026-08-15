# -*- coding: utf-8 -*-
import os
import tempfile

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_models import expected_headers_per
from static.Models.api_sgi_models import (
    VehicleVoucherDownloadAttachmentForm,
    VoucherSafetyFormDelete,
    VoucherSafetyFormPost,
    VoucherSafetyFormPut,
    VoucherSafetyStatusFormPut,
    VoucherToolsFormDelete,
    VoucherToolsFormPost,
    VoucherToolsFormPut,
    VoucherToolsStatusFormPut,
    VoucherVehicleDeleteForm,
    VoucherVehiclePostForm,
    VoucherVehiclePutForm,
    expected_files_attachment,
    vehicle_voucher_delete_model,
    vehicle_voucher_download_att_model,
    voucher_safety_delete_model,
    voucher_safety_post_model,
    voucher_safety_put_model,
    voucher_safety_status_put_model,
    voucher_tools_delete_model,
    voucher_tools_post_model,
    voucher_tools_put_model,
    voucher_tools_status_put_model,
    voucher_vehicle_post_model,
    voucher_vehicle_put_model,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.MD_SGI import (
    create_voucher_safety_api,
    create_voucher_tools_api,
    create_voucher_vehicle_api,
    create_voucher_vehicle_attachment_api,
    delete_voucher_safety_api,
    delete_voucher_tools_api,
    delete_voucher_vehicle_api,
    download_voucher_vehicle_attachment_api,
    download_voucher_vehicle_pdf_api,
    get_vouchers_safety_api,
    get_vouchers_tools_api,
    get_vouchers_vehicle_api,
    update_status_safety,
    update_status_tools,
    update_voucher_safety_api,
    update_voucher_tools_api,
    update_voucher_vehicle_api,
)
from templates.resources.midleware.MD_SGI_Vouchers import (
    create_voucher_epp_attachment_api,
    create_voucher_tools_attachment_api,
)

__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:51 $"

ns = Namespace("GUI/api/v1/sgi", description="SGI")


@ns.route("/voucher/tools")
class VoucherToolsActions(Resource):
    @ns.expect(expected_headers_per, voucher_tools_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherToolsFormPost.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_voucher_tools_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, voucher_tools_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherToolsFormPut.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_voucher_tools_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, voucher_tools_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherToolsFormDelete.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_voucher_tools_api(data, data_token)
        return data_out, code


@ns.route("/voucher/toolsState")
class VoucherToolsState(Resource):
    @ns.expect(expected_headers_per, voucher_tools_status_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherToolsStatusFormPut.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_status_tools(data, data_token)
        return data_out, code


@ns.route("/voucher/safety")
class VoucerSafetyActions(Resource):
    @ns.expect(expected_headers_per, voucher_safety_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherSafetyFormPost.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_voucher_safety_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, voucher_safety_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherSafetyFormPut.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_voucher_safety_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, voucher_safety_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherSafetyFormDelete.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_voucher_safety_api(data, data_token)
        return data_out, code


@ns.route("/voucher/tools/<string:year>&<string:month>&<string:day>")
class FetchVoucherTools(Resource):
    @ns.expect(expected_headers_per)
    def get(self, year, month, day):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_vouchers_tools_api(
            {"date": f"{year}-{month}-{day}"}, data_token
        )
        return data_out, code


@ns.route("/voucher/safety/<string:year>&<string:month>&<string:day>")
class FetchVoucherSafety(Resource):
    @ns.expect(expected_headers_per)
    def get(self, year, month, day):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_vouchers_safety_api(
            {"date": f"{year}-{month}-{day}"}, data_token
        )
        return data_out, code


@ns.route("/voucher/safetyState")
class VoucherSafetyState(Resource):
    @ns.expect(expected_headers_per, voucher_safety_status_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherSafetyStatusFormPut.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_status_safety(data, data_token)
        return data_out, code


@ns.route("/voucher/vehicle/<string:year>&<string:month>&<string:day>")
class FetchVoucherVehicle(Resource):
    @ns.expect(expected_headers_per)
    def get(self, year, month, day):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_vouchers_vehicle_api(
            {"date": f"{year}-{month}-{day}"}, data_token
        )
        return data_out, code


@ns.route("/voucher/vehicle")
class VoucerVehicleActions(Resource):
    @ns.expect(expected_headers_per, voucher_vehicle_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherVehiclePostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_voucher_vehicle_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, voucher_vehicle_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherVehiclePutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_voucher_vehicle_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, vehicle_voucher_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherVehicleDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_voucher_vehicle_api(data, data_token)
        return data_out, code


@ns.route("/voucher/vehicle/attachment-<string:id_voucher>")
class UploadVehicleVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment)
    def post(self, id_voucher):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": None}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = create_voucher_vehicle_attachment_api(
                {
                    "filepath": filepath_download,
                    "filename": filename,
                    "id_voucher": id_voucher,
                },
                data_token,
            )
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400


@ns.route("/voucher/vehicle/attachment/download")
class DownloadVehicleVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, vehicle_voucher_download_att_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VehicleVoucherDownloadAttachmentForm.from_json(  # pyrefly: ignore
            ns.payload
        )
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        filename = data["filename"].split("/")[-1]
        temp_filepath = os.path.join(tempfile.mkdtemp(), filename)
        data["filepath"] = temp_filepath
        data_out, code = download_voucher_vehicle_attachment_api(data, data_token)
        if isinstance(data_out.get("path"), str):
            return send_file(data_out["path"], as_attachment=True)
        else:
            return {"data": None, "msg": "Error al descargar el archivo", "error": str(data_out)}, 400


@ns.route("/voucher/vehicle/download/pdf/<int:id_voucher>")
class DownloadVehicleChecklistPDF(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_voucher):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # 200 -> blob del PDF (FO-CDA-03 R3); 4xx/5xx -> envelope {data, msg, error}
        data_out, code = download_voucher_vehicle_pdf_api(id_voucher, data_token)
        if code == 200:
            return send_file(data_out, as_attachment=True)  # pyrefly: ignore
        return data_out, code


@ns.route("/voucher/epp/attachment-<string:id_voucher>")
class UploadEppVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment)
    def post(self, id_voucher):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": None}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = create_voucher_epp_attachment_api(
                {
                    "filepath": filepath_download,
                    "filename": filename,
                    "id_voucher": id_voucher,
                },
                data_token,
            )
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400

@ns.route("/voucher/tools/attachment-<string:id_voucher>")
class UploadToolsVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment)
    def post(self, id_voucher):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": None}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = create_voucher_tools_attachment_api(
                {
                    "filepath": filepath_download,
                    "filename": filename,
                    "id_voucher": id_voucher,
                },
                data_token,
            )
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400
