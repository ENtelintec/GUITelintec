# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:06 $"

from flask import request
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
)

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


@ns.route("/application/order")
class OperationsApplicationPOs(Resource):
    @ns.expect(expected_headers_per, pos_application_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="orders"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = POsApplicationPostForm.from_json(ns.payload)
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
        validator = POsApplicationPutForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_po_application_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="orders"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = cancel_po_application_api(data, data_token)
        return data_out, code


@ns.route("/order")
class OperationsPOs(Resource):
    @ns.expect(expected_headers_per, purchase_order_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="orders"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderPostForm.from_json(ns.payload)
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
        validator = PurchaseOrderPutForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_purchase_order_api(data, error)
        return data_out, code

    @ns.expect(expected_headers_per)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="orders"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = PurchaseOrderDeleteForm.from_json(ns.payload)
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
        validator = PurchaseOrderUpdateStatusForm.from_json(ns.payload)
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
        validator = PurchaseOrderUpdateStatusForm.from_json(ns.payload)
        data = validator.data
        data_out, code = change_state_po_application_api(data, data_token)
        return data_out, code
