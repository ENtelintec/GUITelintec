# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:32 $'

from flask_restx import fields
from static.extensions import api

permission_model = api.model('Permission', {
    'name': fields.String(required=True, description='The name'),
    'description': fields.String(required=True, description='The description')
    })

token_model = api.model('Token', {
    'username': fields.String(required=True, description='The username'),
    'password': fields.String(required=True, description='The password or pass_key')
    })

token_info_model = api.model('TokenInfo', {
    "access_token": fields.String(required=True, description="The access token"),
    "expires_in": fields.Integer(required=True, description="The number of seconds until the token expires"),
    "timestamp": fields.String(required=True, description="The time the token was created"),
    "remaining_time": fields.String(required=True, description="The number of seconds until the token expires")
})

token_permissions_model = api.model('TokenPermissions', {
    "token": fields.String(required=True, description="The access token")
})

permissions_answer = api.model('PermissionsAnswer', {
    "permissions": fields.String(required=True, description="The permissions"),
    "username": fields.String(required=True, description="The username"),
    "error": fields.String(required=False, description="The error")
})
expected_headers_per = api.parser()
expected_headers_per.add_argument('Authorization', location='headers', required=True)

expected_headers_bot = api.parser()
expected_headers_bot.add_argument('Authorization', location='headers', required=True)