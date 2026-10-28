# -*- coding: utf-8 -*-
import os
import tempfile

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_models import expected_headers_per
from static.Models.api_sgi_models import (
    IsoFormatDeleteForm,
    IsoFormatPostForm,
    IsoFormatPutForm,
    IsoFormatStatusForm,
    VoucherAttachmentDeleteForm,
    VoucherDownloadAttachmentForm,
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
    iso_format_delete_model,
    iso_format_post_model,
    iso_format_put_model,
    iso_format_status_model,
    vehicle_voucher_delete_model,
    voucher_attachment_delete_model,
    voucher_download_att_model,
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
from templates.resources.midleware.MD_IsoFormats import (
    create_iso_format_from_api,
    delete_iso_format_from_api,
    get_iso_format_from_api,
    get_iso_formats_catalogs_from_api,
    get_iso_formats_from_api,
    set_iso_format_status_from_api,
    update_iso_format_from_api,
)
from templates.resources.midleware.MD_SGI import (
    VEHICLE_CHECKLIST_PERMS,
    create_voucher_safety_api,
    create_voucher_tools_api,
    create_voucher_vehicle_api,
    create_voucher_vehicle_attachment_api,
    delete_voucher_safety_api,
    delete_voucher_tools_api,
    delete_voucher_vehicle_api,
    delete_voucher_vehicle_attachment_api,
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
    delete_voucher_epp_attachment_api,
    delete_voucher_tools_attachment_api,
    download_voucher_epp_attachment_api,
    download_voucher_tools_attachment_api,
)

__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:51 $"

ns = Namespace("GUI/api/v1/sgi", description="SGI")


# Vales y checklist (docs/permisos_plan.md D6, P-198; docs/permisos_sgi.md): match exacto.
# Cada tipo de vale tiene su permiso (voucherTool, voucherSafe); listar y cambiar el estado
# también lo usan almacén y quien aprueba (y EPP en los vales de EPP). Administrator pasa siempre.
_VOUCHER_BASE = ["App.Department.SGI", "App.Department.Voucher"]
_TOOLS = _VOUCHER_BASE + ["App.Department.voucherTool"]
_TOOLS_STATE = _TOOLS + ["App.Department.voucherApprove", "App.Department.ALMACEN"]
_SAFETY = _VOUCHER_BASE + ["App.Department.voucherSafe"]
_SAFETY_STATE = _SAFETY + [
    "App.Department.voucherApprove",
    "App.Department.Epp",
    "App.Department.eppApprove",
    "App.Department.ALMACEN",
]
_VEHICLE = VEHICLE_CHECKLIST_PERMS
_VEHICLE_DELETE = _VOUCHER_BASE + ["App.Department.checkvApprove"]


@ns.route("/voucher/tools")
class VoucherToolsActions(Resource):
    @ns.expect(expected_headers_per, voucher_tools_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, permissions=_TOOLS
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
            request, permissions=_TOOLS
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
            request, permissions=_TOOLS
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
            request, permissions=_TOOLS_STATE
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
            request, permissions=_SAFETY
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
            request, permissions=_SAFETY
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
            request, permissions=_SAFETY
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
            request, permissions=_TOOLS_STATE
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
            request, permissions=_SAFETY_STATE
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
            request, permissions=_SAFETY_STATE
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
            request, permissions=_VEHICLE
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
            request, permissions=_VEHICLE
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
            request, permissions=_VEHICLE
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
            request, permissions=_VEHICLE_DELETE
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherVehicleDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_voucher_vehicle_api(data, data_token)
        return data_out, code


def _voucher_attachment_upload(id_voucher, create_api, permissions):
    """POST multipart (un archivo por request, campo `file`) de los 3 tipos de vale."""
    flag, data_token, msg = token_verification_procedure(request, permissions=permissions)
    if not flag:
        return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
    if "file" not in request.files:
        return {"data": None, "msg": "No se detectó un archivo", "error": None}, 400
    file = request.files["file"]
    if not (file and file.filename):
        return {"data": None, "msg": "No se subió el archivo", "error": None}, 400
    filename = secure_filename(file.filename)
    filepath_download = os.path.join(tempfile.mkdtemp(), filename)
    file.save(filepath_download)
    data_out, code = create_api(
        {"filepath": filepath_download, "filename": filename, "id_voucher": id_voucher},
        data_token,
    )
    return data_out, code


def _voucher_attachment_delete(id_voucher, delete_api, permissions):
    """DELETE {filename, reason?} de un anexo de los 3 tipos de vale
    (docs/vales_anexos_descarga_borrado.md): 200 envelope con `files` restantes,
    400 firma, 404 vale/archivo, 409 contención (repetir)."""
    flag, data_token, msg = token_verification_procedure(request, permissions=permissions)
    if not flag:
        return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
    validator = VoucherAttachmentDeleteForm.from_json(ns.payload)  # pyrefly: ignore
    if not validator.validate():
        return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
    data = validator.data
    data["id_voucher"] = id_voucher
    return delete_api(data, data_token)


def _voucher_attachment_download(download_api, permissions):
    """POST {id_voucher, filename} -> blob en 200; envelope JSON en 4xx (el front
    decide por el status)."""
    flag, data_token, msg = token_verification_procedure(request, permissions=permissions)
    if not flag:
        return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
    validator = VoucherDownloadAttachmentForm.from_json(ns.payload)  # pyrefly: ignore
    if not validator.validate():
        return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
    data = validator.data
    filename = data["filename"].split("/")[-1]
    data["filepath"] = os.path.join(tempfile.mkdtemp(), filename)
    data_out, code = download_api(data, data_token)
    if code == 200 and isinstance(data_out.get("path"), str):
        return send_file(data_out["path"], as_attachment=True)
    return data_out, code


@ns.route("/voucher/vehicle/attachment-<string:id_voucher>")
class UploadVehicleVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment)
    def post(self, id_voucher):
        return _voucher_attachment_upload(id_voucher, create_voucher_vehicle_attachment_api, _VEHICLE)

    @ns.expect(expected_headers_per, voucher_attachment_delete_model)
    def delete(self, id_voucher):
        return _voucher_attachment_delete(id_voucher, delete_voucher_vehicle_attachment_api, _VEHICLE)


@ns.route("/voucher/vehicle/attachment/download")
class DownloadVehicleVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, voucher_download_att_model)
    def post(self):
        return _voucher_attachment_download(download_voucher_vehicle_attachment_api, _VEHICLE)


@ns.route("/voucher/vehicle/download/pdf/<int:id_voucher>")
class DownloadVehicleChecklistPDF(Resource):
    @ns.doc(params={"full": "1 -> documento combinado (checklist + anexos PDF + evidencia fotográfica)"})
    @ns.expect(expected_headers_per)
    def get(self, id_voucher):
        flag, data_token, msg = token_verification_procedure(
            request, permissions=_VEHICLE
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # 200 -> blob del PDF (FO-CDA-03 R3); 4xx/5xx -> envelope {data, msg, error}.
        # ?full=1 -> checklist + anexos PDF + evidencia fotografica
        # (docs/checklist_vehicular_full_pdf.md); sin el, solo el checklist.
        full = request.args.get("full", default="0").strip().lower() in ("1", "true", "yes")
        data_out, code = download_voucher_vehicle_pdf_api(id_voucher, data_token, full=full)
        if code == 200:
            return send_file(data_out, as_attachment=True)  # pyrefly: ignore
        return data_out, code


@ns.route("/voucher/epp/attachment-<string:id_voucher>")
class UploadEppVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment)
    def post(self, id_voucher):
        return _voucher_attachment_upload(id_voucher, create_voucher_epp_attachment_api, _SAFETY)

    @ns.expect(expected_headers_per, voucher_attachment_delete_model)
    def delete(self, id_voucher):
        return _voucher_attachment_delete(id_voucher, delete_voucher_epp_attachment_api, _SAFETY)


@ns.route("/voucher/epp/attachment/download")
class DownloadEppVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, voucher_download_att_model)
    def post(self):
        return _voucher_attachment_download(download_voucher_epp_attachment_api, _SAFETY)


@ns.route("/voucher/tools/attachment-<string:id_voucher>")
class UploadToolsVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment)
    def post(self, id_voucher):
        return _voucher_attachment_upload(id_voucher, create_voucher_tools_attachment_api, _TOOLS)

    @ns.expect(expected_headers_per, voucher_attachment_delete_model)
    def delete(self, id_voucher):
        return _voucher_attachment_delete(id_voucher, delete_voucher_tools_attachment_api, _TOOLS)


@ns.route("/voucher/tools/attachment/download")
class DownloadToolsVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, voucher_download_att_model)
    def post(self):
        return _voucher_attachment_download(download_voucher_tools_attachment_api, _TOOLS)



# =====================================================================
# Formatos ISO (catálogo de SGI) — ver Docs/iso_formats_crud.md
# Lecturas: sgi + administracion (el catálogo lo consumen saldos y los PDFs);
# escrituras: solo sgi (dueño del catálogo).
# =====================================================================
_FMT_READ = ["App.Department.SGI", "App.Department.Administracion"]
_FMT_WRITE = ["App.Department.SGI"]


@ns.route("/formats")
class IsoFormatsList(Resource):
    @ns.doc(params={
        "all": "1 -> vigentes y retirados (default solo vigentes)",
        "department": "Filtra por área dueña (rrhh, almacen, presales, sgi, administracion, cda, sm, compras)",
        "kind": "Filtra por config.kind (p.ej. balance_control)",
    })
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, permissions=_FMT_READ)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        params = {
            "all": request.args.get("all"),
            "department": request.args.get("department"),
            "kind": request.args.get("kind"),
        }
        data_out, code = get_iso_formats_from_api(params, data_token)
        return data_out, code


@ns.route("/formats/catalogs")
class IsoFormatsCatalogs(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, permissions=_FMT_READ)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_iso_formats_catalogs_from_api(data_token)
        return data_out, code


@ns.route("/format")
class IsoFormatOps(Resource):
    @ns.expect(expected_headers_per, iso_format_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, permissions=_FMT_WRITE)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = IsoFormatPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = create_iso_format_from_api(ns.payload, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, iso_format_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, permissions=_FMT_WRITE)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = IsoFormatPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = update_iso_format_from_api(ns.payload, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, iso_format_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, permissions=_FMT_WRITE)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = IsoFormatDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = delete_iso_format_from_api(validator.data, data_token)
        return data_out, code


@ns.route("/format/status")
class IsoFormatStatus(Resource):
    @ns.expect(expected_headers_per, iso_format_status_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, permissions=_FMT_WRITE)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = IsoFormatStatusForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = set_iso_format_status_from_api(validator.data, data_token)
        return data_out, code


@ns.route("/format/<int:id_format>")
class IsoFormatDetail(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_format):
        flag, data_token, msg = token_verification_procedure(request, permissions=_FMT_READ)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_iso_format_from_api(id_format, data_token)
        return data_out, code
