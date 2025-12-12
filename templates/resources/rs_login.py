# -*- coding: utf-8 -*-
from static.Models.api_login_models import put_biocredentials_model
from static.Models.api_models import expected_headers_per
from static.Models.api_login_models import BiocredentialsPutModelForm
from templates.resources.midleware.MD_UserSystem import update_biocredentials_from_api
from templates.resources.midleware.MD_UserSystem import fectchUsersDBApi
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from flask_restx import Namespace, Resource
from flask import request

__author__ = "Edisson Naula"
__date__ = "$ 16/ene./2024  at 18:49 $"


ns = Namespace("GUI/api/v1/UserSystem")


@ns.route("/usernames-<string:status>")
class LoginUP(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(
            request, department=["credentials", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        status = status if status in ["activo", "inactivo"] else "%"
        data_out, code = fectchUsersDBApi({"status": status}, data_token)
        return data_out, code


@ns.route("/update-biocredentials")
class BiocredentialUpdate(Resource):
    @ns.expect(expected_headers_per, put_biocredentials_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["credentials", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = BiocredentialsPutModelForm.from_json(ns.payload)    # pyrefly: ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_out, code = update_biocredentials_from_api(data, data_token)
        return data_out, code



