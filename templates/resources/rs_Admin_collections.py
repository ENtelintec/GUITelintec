# -*- coding: utf-8 -*-


import os
import tempfile

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_models import expected_headers_per
from static.Models.api_purchases_models import (
    POAppDeleteForm,
    POsApplicationPostForm,
    POsApplicationPutForm,
    PurchaseOrderDeleteForm,
    PurchaseOrderPostForm,
    PurchaseOrderPutForm,
    PurchaseOrderUpdateStatusForm,
    QuotationActivityCreateForm,
    QuotationActivityDeleteForm,
    QuotationActivityStatusUpdateForm,
    QuotationActivityUpdateForm,
    RemissionBalanceUpdateForm,
    ReportActivityCreateControlTableForm,
    ReportActivityCreateForm,
    ReportActivityDeleteForm,
    ReportActivityDownloadAttForm,
    ReportActivityUpdateControlTableForm,
    ReportActivityUpdateForm,
    expected_files_attachment_remission,
    po_app_delete_model,
    pos_application_post_model,
    pos_application_put_model,
    purchase_order_delete_model,
    purchase_order_post_model,
    purchase_order_put_model,
    purchase_order_update_status_model,
    quoatation_activity_status_update_model,
    quotation_activity_create_model,
    quotation_activity_delete_model,
    quotation_activity_update_model,
    remission_activity_create_control_table_model,
    remission_activity_create_model,
    remission_activity_update_control_table_model,
    remission_activity_update_model,
    remission_balance_update_model,
    report_activity_delete_model,
    report_activity_download_att_model,
)
from static.Models.api_purchase_management_models import (
    PurchaseManagementCancelForm,
    PurchaseManagementDeleteForm,
    PurchaseManagementPostForm,
    PurchaseManagementPutForm,
    purchase_management_cancel_model,
    purchase_management_delete_model,
    purchase_management_post_model,
    purchase_management_put_model,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.MD_Admin_Collections import (
    create_activity_report_attachment_api,
    create_quotation_activity_from_api,
    create_remission_control_table_from_api,
    create_remission_from_api,
    delete_quotation_activity_from_api,
    delete_remission_from_api,
    download_file_remission,
    download_report_activity_attachment_api,
    get_quotations_from_api,
    get_remission_from_api,
    update_quotation_activity_from_api,
    update_remission_balance_from_api,
    update_remission_control_table_from_api,
    update_remission_from_api,
)
from templates.resources.midleware.MD_Purchases import (
    cancel_po_application_api,
    cancel_purchase_order_api,
    change_state_order_api,
    change_state_po_application_api,
    create_po_application_api,
    create_purchaser_order_api,
    dowload_file_purchase,
    download_file_purchase_item_approved,
    fetch_po_item_sm_item_id,
    fetch_pos_applications,
    fetch_pos_applications_to_approve,
    fetch_purchase_orders,
    generate_folios_po,
    get_items_with_fast_order,
    match_po_movements_and_sms,
    update_po_application_api,
    update_purchase_order_api,
)
from templates.resources.midleware.MD_PurchaseManagement import (
    cancel_purchase_management_api,
    create_purchase_management_api,
    delete_purchase_management_api,
    fetch_purchase_management,
    get_purchase_management_catalogs,
    get_purchase_management_detail_api,
    update_purchase_management_api,
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_purchaser_order_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, purchase_order_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["orders", "administracion"]
        )
        if not flag:
            return {
                "error": msg if msg != "" else "No autorizado. Token invalido"
            }, 401

        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_purchase_order_api(data, data_token)
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
        return data, code


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
        return data, code


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


@ns.route("/purchase/movements/match")
class PurchaseMovementsMatch(Resource):
    @ns.expect(expected_headers_per)
    @ns.doc(
        params={
            "status": "Filtra por status de la OC (entero); canceladas (4) siempre se excluyen",
            "date_from": "Fecha inicial YYYY-MM-DD sobre el timestamp de la OC",
            "date_to": "Fecha final YYYY-MM-DD sobre el timestamp de la OC",
            "folio": "Limita el match a la OC cuyo folio o folio_supplier coincida",
        }
    )
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        params = {
            "status": request.args.get("status"),
            "date_from": request.args.get("date_from"),
            "date_to": request.args.get("date_to"),
            "folio": request.args.get("folio"),
        }
        data_out, code = match_po_movements_and_sms(params, data_token)
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        raw_metadata = ns.payload.get("metadata") or {}
        data_out, code = update_remission_from_api(data, data_token, raw_metadata)
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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_remission_from_api(data, data_token)
        return data_out, code


@ns.route("/remissionControlTable")
class ActivityRemissionTableAction(Resource):
    @ns.expect(expected_headers_per, remission_activity_create_control_table_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReportActivityCreateControlTableForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_remission_control_table_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, remission_activity_update_control_table_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReportActivityUpdateControlTableForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        raw_metadata = ns.payload.get("metadata") or {}
        data_out, code = update_remission_control_table_from_api(data, data_token, raw_metadata)
        return data_out, code


@ns.route("/remissionBalance")
class ActivityRemissionBalanceAction(Resource):
    @ns.expect(expected_headers_per, remission_balance_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = RemissionBalanceUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        raw_metadata = ns.payload.get("metadata") or {}
        data_out, code = update_remission_balance_from_api(data, data_token, raw_metadata)
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


@ns.route("/remission/download/pdf/<int:id_report>")
class DownloadPDFRemission(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_report):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        iva_rate = request.args.get("iva_rate", default=0.16, type=float)
        # ?full=1 -> documento combinado (Remision + anexos + fotos); por defecto
        # solo la pagina de la remision (comportamiento historico). Ver
        # Docs/remission_combined_pdf.md.
        full = request.args.get("full", default="0").strip().lower() in ("1", "true", "yes")
        data, code = download_file_remission(id_report, iva_rate, data_token, full=full)
        if code == 200:
            return send_file(data, as_attachment=True)  # pyrefly: ignore
        return data, code


@ns.route("/remission/attachment-<string:id_report>")
class UploadActivityReportAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment_remission)
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
                    "id_report": id_report,
                    "category": request.form.get("category", ""),
                    "folio": request.form.get("folio", ""),
                    "title": request.form.get("title", ""),
                },
                data_token,
            )
            return data_out, code
        else:
            return {"msg": "No se subio el archivo"}, 400


# =====================================================================
# Gestión de Compras (FO-COM-01 R3) — ver Docs/gestion_de_compras.md
# =====================================================================
@ns.route("/purchaseManagement")
class PurchaseManagementOps(Resource):
    @ns.doc(
        params={
            "status": "Filtra por estatus (entero 0..4)",
            "classification": "Filtra por clasificación (entero 0..6)",
            "client_id": "Filtra por cliente (id_customer)",
            "date_from": "request_date >= YYYY-MM-DD",
            "date_to": "request_date <= YYYY-MM-DD",
            "is_active": "1=activos (default), 0=cancelados",
            "all": "1 -> incluye activos y cancelados (ignora is_active)",
        }
    )
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        params = {
            "status": request.args.get("status"),
            "classification": request.args.get("classification"),
            "client_id": request.args.get("client_id"),
            "date_from": request.args.get("date_from"),
            "date_to": request.args.get("date_to"),
            "is_active": request.args.get("is_active"),
            "all": request.args.get("all"),
        }
        data_out, code = fetch_purchase_management(params, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, purchase_management_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseManagementPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_purchase_management_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, purchase_management_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseManagementPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        # raw_payload -> el midleware solo sobreescribe lo enviado (update parcial).
        raw_payload = ns.payload or {}
        data_out, code = update_purchase_management_api(data, data_token, raw_payload)
        return data_out, code

    @ns.expect(expected_headers_per, purchase_management_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseManagementDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_purchase_management_api(data, data_token)
        return data_out, code


@ns.route("/purchaseManagement/cancel")
class PurchaseManagementCancel(Resource):
    @ns.expect(expected_headers_per, purchase_management_cancel_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseManagementCancelForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = cancel_purchase_management_api(data, data_token)
        return data_out, code


@ns.route("/purchaseManagement/catalogs")
class PurchaseManagementCatalogs(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_purchase_management_catalogs()
        return data_out, code


@ns.route("/purchaseManagement/<int:id_pm>")
class PurchaseManagementDetail(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_pm):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "purchases"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_purchase_management_detail_api(id_pm, data_token)
        return data_out, code


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
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        filename = data["filename"].split("/")[-1]
        temp_filepath = os.path.join(tempfile.mkdtemp(), filename)
        data["filepath"] = temp_filepath
        data_out, code = download_report_activity_attachment_api(data, data_token)
        path = data_out.get("data", {})
        path = path.get("path") if isinstance(path, dict) else None
        if isinstance(path, str):
            return send_file(path, as_attachment=True)
        return data_out, code


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