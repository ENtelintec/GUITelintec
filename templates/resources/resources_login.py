# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 16/ene./2024  at 18:49 $"

from flask_restx import Resource, Namespace

from static.Models.api_models import token_model, TokenModelForm
from templates.controllers.employees.us_controller import (
    verify_user_DB,
    get_permissions_user_password,
)

ns = Namespace("GUI/api/v1/auth")


@ns.route("/loginUP")
class LoginUP(Resource):
    @ns.expect(token_model)
    def post(self):
        validator = TokenModelForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 1)
        out = {
            "verified": False,
            "user": data["username"],
            "permissions": "invalid credentials",
        }
        pass_key = data["password"]
        is_real_user = verify_user_DB(data["username"], pass_key)
        out_dict = get_permissions_user_password(data["username"], pass_key)
        print(out_dict)
        permissions = (
            out_dict["permissions"] if out_dict["permissions"] is not None else {}
        )
        permissions_list = []
        for v in permissions.values():
            permissions_list.append({"role": v})
        if not is_real_user:
            return out, 400
        out = {
            "verified": True,
            "user": data["username"],
            "permissions": permissions_list,
            "name": out_dict["name"],
            "contract": out_dict["contract"],
            "emp_id": out_dict["emp_id"],
        }
        return out, 200
