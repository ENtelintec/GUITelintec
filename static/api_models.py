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


employees_info_model = api.model('EmployeeInfo', {
    "columns": fields.List(fields.String(required=True, description="The columns")),
    "data": fields.List(fields.List(fields.String))
    })

resume_model = api.model('Resume', {
    "id": fields.Integer(required=True, description="The id"),
    "name": fields.String(required=True, description="The name"),
    "contract": fields.String(required=True, description="The contract"),
    "absences": fields.Integer(required=True, description="The absences"),
    "late": fields.Integer(required=True, description="The late"),
    "extra": fields.Integer(required=True, description="The extra"),
    "total_h_extra": fields.Integer(required=True, description="The total"),
    "primes": fields.Integer(required=True, description="The primes"),
    "absences_details": fields.String(required=True, description="The absences details"),
    "late_details": fields.String(required=True, description="The late details"),
    "extra_details": fields.String(required=True, description="The extra details"),
    "primes_details": fields.String(required=True, description="The primes details")
    })
examenes_medicos_model = api.model('ExamenesMedicos', {
    "exist":  fields.Boolean(required=True, description="The exist"),
    "id_exam": fields.Integer(required=True, description="The id"),
    "name": fields.String(required=True, description="The name"),
    "blood": fields.String(required=True, description="The date"),
    "status": fields.String(required=True, description="The status"),
    "aptitudes": fields.String(required=True, description="The aptitud"),
    "dates": fields.String(required=True, description="The date"),
    "emp_id": fields.Integer(required=True, description="The id")
    })

employes_examenes_model = api.model('EmployesExamenes', {
    "data": fields.List(fields.Nested(examenes_medicos_model))
    })

employees_resume_model = api.model('EmployeesResume', {
    "data": fields.List(fields.Nested(resume_model)),
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