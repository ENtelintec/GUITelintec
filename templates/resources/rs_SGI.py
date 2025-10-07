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
    voucher_tools_put_model,
    voucher_tools_status_put_model,
    VoucherToolsStatusFormPut,
    voucher_safety_status_put_model,
    VoucherSafetyStatusFormPut,
    voucher_safety_put_model,
    voucher_vehicle_post_model,
    voucher_vehicle_put_model,
    VoucherVehiclePostForm,
    VoucherVehiclePutForm,
)
from templates.resources.midleware.MD_SGI import (
    create_voucher_tools_api,
    create_voucher_safety_api,
    update_voucher_tools_api,
    update_voucher_safety_api,
    get_vouchers_tools_api,
    get_vouchers_safety_api,
    update_status_tools,
    update_status_safety,
    get_vouchers_vehicle_api,
    create_voucher_vehicle_api,
    update_voucher_vehicle_api,
)

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
        validator = VoucherToolsFormPost.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
        validator = VoucherToolsFormPut.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_voucher_tools_api(data, data_token)
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
        validator = VoucherToolsStatusFormPut.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
        validator = VoucherSafetyFormPost.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
        validator = VoucherSafetyFormPut.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_voucher_safety_api(data, data_token)
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
        validator = VoucherSafetyStatusFormPut.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
        validator = VoucherVehiclePostForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
        validator = VoucherVehiclePutForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data_out, code = update_voucher_vehicle_api(data, data_token)
        return data_out, code
