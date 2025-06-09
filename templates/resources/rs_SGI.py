# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:51 $"


from flask import request
from flask_restx import Namespace, Resource

from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from static.Models.api_models import expected_headers_per
from static.Models.api_sgi_models import (
    VoucherToolsFormPost,
    VoucherSafetyFormPost,
    voucher_tools_post_model,
    voucher_safety_post_model,
    VoucherToolsFormPut,
    VoucherSafetyFormPut,
)
from templates.resources.midleware.MD_SGI import (
    create_voucher_tools_api,
    create_voucher_safety_api,
    update_voucher_tools_api,
    update_voucher_safety_api,
)

ns = Namespace("GUI/api/v1/sgi", description="SGI")


@ns.route("/voucher/tools")
class VoucherTools(Resource):
    @ns.expect(expected_headers_per, voucher_tools_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherToolsFormPost.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = create_voucher_tools_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, voucher_tools_post_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherToolsFormPut.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_voucher_tools_api(data, data_token)
        return data_out, code


@ns.route("/voucher/safety")
class VoucerSafety(Resource):
    @ns.expect(expected_headers_per, voucher_safety_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherSafetyFormPost.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = create_voucher_safety_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, voucher_safety_post_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sgi", "voucher"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = VoucherSafetyFormPut.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_voucher_safety_api(data, data_token)
        return data_out, code
