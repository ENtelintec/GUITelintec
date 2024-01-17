# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 16/ene./2024  at 18:49 $'

from flask_restx import Resource, Namespace

from static.api_models import token_model
from templates.FunctionsSQL import verify_user_DB, get_permissions_user_password
from templates.FunctionsText import parse_data

ns = Namespace('GUI/api/v1/auth')


@ns.route('/loginUP')
class LoginUP(Resource):
    @ns.expect(token_model)
    def post(self):
        code, data = parse_data(ns.payload, 1)
        out = {
            "verified": False,
            "user": data['username'],
            "permissions": "invalid credentials"
        }
        if code == 200:
            pass_key = data['password']
            is_real_user = verify_user_DB(data['username'], pass_key)
            permissions = get_permissions_user_password(data['username'], pass_key)
            if is_real_user:
                out = {
                    "verified": True,
                    "user": data['username'],
                    "permissions": permissions
                }
            else:
                code = 400
        return out, code
