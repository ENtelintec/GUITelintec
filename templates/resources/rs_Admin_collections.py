# -*- coding: utf-8 -*-


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
    delete_report_activity_from_api,
)
from static.Models.api_purchases_models import ReportActivityUpdateForm
from static.Models.api_purchases_models import report_activity_update_model
from templates.resources.midleware.MD_Admin_Collections import (
    update_report_activity_from_api,
)
from static.Models.api_purchases_models import ReportActivityCreateForm
from static.Models.api_purchases_models import report_activity_create_model
from templates.resources.midleware.MD_Admin_Collections import (
    create_report_activity_from_api,
)
from templates.resources.midleware.MD_Admin_Collections import (
    get_report_activity_from_api,
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
            request, department="orders"
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
            request, department="orders"
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
            request, department="orders"
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
            request, department="orders"
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
        flag, error, result = token_verification_procedure(request, department="orders")
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
            request, department="orders"
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


@ns.route("/order/status")
class ChangeStateOrder(Resource):
    @ns.expect(expected_headers_per, purchase_order_update_status_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="orders"
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
            request, department="orders"
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
        data, code = dowload_file_purchase(po_id)
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
        data, code = download_file_purchase_item_approved()
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


@ns.route("/activity/report")
class ActivityReportAction(Resource):
    @ns.expect(expected_headers_per, report_activity_create_model)
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
        data_out, code = create_report_activity_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, report_activity_update_model)
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
        data_out, code = update_report_activity_from_api(data, data_token)
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
        data_out, code = delete_report_activity_from_api(data, data_token)
        return data_out, code


@ns.route("/activity/reports-<string:id_report>")
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
        except Exception as e:
            print(f"retrieviong all {e}")
            id_report = None
        data_out, code = get_report_activity_from_api(id_report, data_token)
        return data_out, code


# @ns.route("/remission")
# class RemissionAction(Resource):
#     @ns.expect(expected_headers_per, remission_model_insert)
#     def post(self):
#         flag, data_token, msg = token_verification_procedure(
#             request, department="administracion"
#         )
#         if not flag:
#             return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401

#         validator = RemissionInsertForm.from_json(ns.payload)  # pyrefly: ignore
#         if not validator.validate():
#             return {"data": validator.errors, "msg": "Error at structure"}, 400

#         data = validator.data
#         data_out, code = create_remission_from_api(data, data_token)
#         return data_out, code

#     @ns.expect(expected_headers_per, remission_model_update)
#     def put(self):
#         flag, data_token, msg = token_verification_procedure(
#             request, department="administracion"
#         )
#         if not flag:
#             return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401

#         validator = RemissionUpdateForm.from_json(ns.payload)  # pyrefly: ignore
#         if not validator.validate():
#             return {"data": validator.errors, "msg": "Error at structure"}, 400

#         data = validator.data
#         data_out, code = update_remission_from_api(data, data_token)
#         return data_out, code

#     @ns.expect(expected_headers_per, remission_model_delete)
#     def delete(self):
#         flag, data_token, msg = token_verification_procedure(
#             request, department="administracion"
#         )
#         if not flag:
#             return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401

#         validator = RemissionDeleteForm.from_json(ns.payload)  # pyrefly: ignore
#         if not validator.validate():
#             return {"data": validator.errors, "msg": "Error at structure"}, 400

#         data = validator.data
#         data_out, code = delete_remission_from_api(data, data_token)
#         return data_out, code


# @ns.route("/remissions/<string:status>")
# class FetchRemissions(Resource):
#     @ns.expect(expected_headers_per)
#     def get(self, status):
#         flag, data_token, msg = token_verification_procedure(
#             request, department="administracion"
#         )
#         if not flag:
#             return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
#         data, code = fetch_remissions_by_status_db(status, data_token)
#         return data, code
