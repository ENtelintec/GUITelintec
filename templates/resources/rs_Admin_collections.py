# -*- coding: utf-8 -*-


from templates.resources.midleware.MD_Purchases import get_items_with_fast_order
from static.Models.api_purchases_models import ReportActivityCreateControlTableForm
from static.Models.api_purchases_models import basic_control_table_report_model
from templates.resources.midleware.MD_Purchases import fetch_po_item_sm_item_id
from templates.resources.midleware.MD_Admin_Collections import (
    download_report_activity_attachment_api,
)
from static.Models.api_purchases_models import ReportActivityDownloadAttForm
from static.Models.api_purchases_models import report_activity_download_att_model
from templates.resources.midleware.MD_Admin_Collections import (
    create_activity_report_attachment_api,
)
import os
import tempfile
from werkzeug.utils import secure_filename
from static.Models.api_sgi_models import expected_files_attachment
from templates.resources.midleware.MD_Admin_Collections import get_quotations_from_api
from templates.resources.midleware.MD_Admin_Collections import (
    delete_quotation_activity_from_api,
)
from templates.resources.midleware.MD_Admin_Collections import (
    update_quotation_activity_from_api,
)
from templates.resources.midleware.MD_Admin_Collections import (
    create_quotation_activity_from_api,
)
from static.Models.api_purchases_models import ReportActivityDeleteForm
from static.Models.api_purchases_models import report_activity_delete_model
from templates.resources.midleware.MD_Admin_Collections import (
    delete_remission_from_api,
)
from static.Models.api_purchases_models import ReportActivityUpdateForm
from static.Models.api_purchases_models import remission_activity_update_model
from templates.resources.midleware.MD_Admin_Collections import (
    update_remission_from_api,
)
from static.Models.api_purchases_models import ReportActivityCreateForm
from static.Models.api_purchases_models import remission_activity_create_model
from templates.resources.midleware.MD_Admin_Collections import (
    create_remission_from_api,
)
from templates.resources.midleware.MD_Admin_Collections import (
    get_remission_from_api,
)
from static.Models.api_purchases_models import (
    QuotationActivityCreateForm,
    QuotationActivityDeleteForm,
    QuotationActivityUpdateForm,
    QuotationActivityStatusUpdateForm,
    quotation_activity_create_model,
    quotation_activity_update_model,
    quotation_activity_delete_model,
    quoatation_activity_status_update_model,
)
from static.Models.api_purchases_models import po_app_delete_model
from flask import request, send_file
from flask_restx import Namespace, Resource

from static.Models.api_models import expected_headers_per
from static.Models.api_purchases_models import (
    pos_application_post_model,
    POsApplicationPostForm,
    pos_application_put_model,
    POsApplicationPutForm,
    PurchaseOrderDeleteForm,
    purchase_order_update_status_model,
    PurchaseOrderUpdateStatusForm,
    purchase_order_post_model,
    PurchaseOrderPostForm,
    purchase_order_put_model,
    PurchaseOrderPutForm,
    purchase_order_delete_model,
    POAppDeleteForm,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure

from templates.resources.midleware.MD_Purchases import (
    fetch_purchase_orders,
    create_purchaser_order_api,
    update_purchase_order_api,
    cancel_purchase_order_api,
    change_state_order_api,
    create_po_application_api,
    update_po_application_api,
    cancel_po_application_api,
    change_state_po_application_api,
    fetch_pos_applications,
    dowload_file_purchase,
    fetch_pos_applications_to_approve,
    generate_folios_po,
    download_file_purchase_item_approved,
)

__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:06 $"

ns = Namespace("GUI/api/v1/admin/collections")


@ns.route("/orders/<string:status>")
class FetchPOs(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = fetch_purchase_orders(status, data_token)
        return data, code


@ns.route("/application/orders/<string:status>")
class FetchPOsApplications(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = fetch_pos_applications(status, data_token)
        return data, code


@ns.route("/application/orderstoApprove")
class FetchPOsApplicationsToApprove(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = fetch_pos_applications_to_approve(data_token)
        return data, code


@ns.route("/application/order")
class APOsOperations(Resource):
    @ns.expect(expected_headers_per, pos_application_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = POsApplicationPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = create_po_application_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, pos_application_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = POsApplicationPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_po_application_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, po_app_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = POAppDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = cancel_po_application_api(data, data_token)
        return data_out, code


@ns.route("/order")
class POsOperations(Resource):
    @ns.expect(expected_headers_per, purchase_order_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = create_purchaser_order_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, purchase_order_put_model)
    def put(self):
        flag, error, result = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {
                "error": error if error != "" else "No autorizado. Token invalido"
            }, 401

        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_purchase_order_api(data, error)
        return data_out, code

    @ns.expect(expected_headers_per, purchase_order_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = cancel_purchase_order_api(data, data_token)
        return data_out, code


@ns.route("/POItemsFoDelivery")
class FetchPoItemForFastDelivery(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        # get_all_item_purchase_order_with_id_item_sm
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = fetch_po_item_sm_item_id(data_token)
        return data, code


@ns.route("/order/status")
class ChangeStateOrder(Resource):
    @ns.expect(expected_headers_per, purchase_order_update_status_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderUpdateStatusForm.from_json(  # pyrefly: ignore
            ns.payload
        )
        data = validator.data
        data_out, code = change_state_order_api(data, data_token)
        return data_out, code


@ns.route("/application/order/status")
class ChangeStatePOApplication(Resource):
    @ns.expect(expected_headers_per, purchase_order_update_status_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderUpdateStatusForm.from_json(  # pyrefly: ignore
            ns.payload
        )
        data = validator.data
        data_out, code = change_state_po_application_api(data, data_token)
        return data_out, code


@ns.route("/purchase/download/pdf/<int:po_id>")
class DownloadPDFPurchase(Resource):
    @ns.expect(expected_headers_per)
    def get(self, po_id):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administration"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = dowload_file_purchase(po_id, data_token)
        if code == 200:
            return send_file(data, as_attachment=True)  # pyrefly: ignore
        else:
            return {"msg": "error at downloading"}, code


@ns.route("/purchase/download/pdfItemsPurchaseStorage")
class DownloadPDFPurchaseItemsStorage(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["almacen", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = download_file_purchase_item_approved(data_token)
        if code == 200:
            return send_file(data["data"], as_attachment=True)  # pyrefly: ignore
        else:
            return {"msg": "error at downloading"}, code


@ns.route("/purchase/folio/<string:folio>")
class FolioPO(Resource):
    @ns.expect(expected_headers_per)
    def get(self, folio):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = generate_folios_po(folio, data_token)
        return data_out, code


@ns.route("/activity/quotation")
class ActivityQuotatioAction(Resource):
    @ns.expect(expected_headers_per, quotation_activity_create_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = QuotationActivityCreateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = create_quotation_activity_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, quotation_activity_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = QuotationActivityUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_quotation_activity_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, quotation_activity_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = QuotationActivityDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = delete_quotation_activity_from_api(data, data_token)
        return data_out, code


@ns.route("/activity/quotations-<string:id_quotation>")
class FetchActivitieQuotationById(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_quotation):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        try:
            id_quotation = int(id_quotation)
        except Exception as e:
            print(f"retrieviong all {e}")
            id_quotation = None
        data_out, code = get_quotations_from_api(id_quotation, data_token)
        return data_out, code


@ns.route("/activity/ChangeStatus")
class ChangeStatusActivity(Resource):
    @ns.expect(expected_headers_per, quoatation_activity_status_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = QuotationActivityStatusUpdateForm.from_json(  # pyrefly: ignore
            ns.payload
        )
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_quotation_activity_from_api(data, data_token)
        return data_out, code


@ns.route("/remission")
class ActivityRemissionAction(Resource):
    @ns.expect(expected_headers_per, remission_activity_create_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReportActivityCreateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = create_remission_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, remission_activity_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReportActivityUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_remission_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, report_activity_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReportActivityDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = delete_remission_from_api(data, data_token)
        return data_out, code


@ns.route("/remissionControlTable")
class ActivityRemissionTableAction(Resource):
    @ns.expect(expected_headers_per, basic_control_table_report_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReportActivityCreateControlTableForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = create_remission_from_api(data, data_token)
        return data_out, code


@ns.route("/remission-<string:id_report>")
class FetchActivitieReportById(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_report):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        try:
            id_report = int(id_report)
            if id_report <= 0:
                id_report = None
        except Exception as e:
            print(f"retrieviong all {e}")
            id_report = None
        data_out, code = get_remission_from_api(id_report, data_token)
        return data_out, code


@ns.route("/remission/attachment-<string:id_report>")
class UploadActivityReportAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment)
    def post(self, id_report):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "operaciones"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = create_activity_report_attachment_api(
                {
                    "filepath": filepath_download,
                    "filename": filename,
                    "id_voucher": id_report,
                },
                data_token,
            )
            if code != 201:
                return {"data": data_out, "msg": "Error at file structure"}, 400
            return {"data": data_out, "msg": f"Ok with filaname: {filename}"}, 201
        else:
            return {"msg": "No se subio el archivo"}, 400


@ns.route("/voucher/vehicle/attachment/download")
class DownloadVehicleVoucherAttachment(Resource):
    @ns.expect(expected_headers_per, report_activity_download_att_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReportActivityDownloadAttForm.from_json(  # pyrefly: ignore
            ns.payload
        )
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        filename = data["filename"].split("/")[-1]
        temp_filepath = os.path.join(tempfile.mkdtemp(), filename)
        data["filepath"] = temp_filepath
        data_out, code = download_report_activity_attachment_api(data, data_token)
        if isinstance(data_out.get("path"), str):
            return send_file(data_out["path"], as_attachment=True)
        else:
            print(data)
            return {"data": data_out, "msg": "Error at file structure"}, 400


@ns.route("/APOItemsFastOrder")
class FetchAPoItemForFastDelivery(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        # get_all_item_purchase_order_with_id_item_sm
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_items_with_fast_order(data_token)
        return data, code