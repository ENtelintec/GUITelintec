# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/may./2024  at 11:21 $'

from flask_restx import fields
from static.extensions import api

employee_model = api.model('Employee', {
    "id": fields.Integer(required=True, description="The employee id"),
    "name": fields.String(required=True, description="The employee name"),
    "phone": fields.String(required=True, description="The employee phone number"),
    "dep": fields.String(required=True, description="The employee department"),
    "modality": fields.String(required=True, description="The employee modality"),
    "email": fields.String(required=True, description="The employee email"),
    "contract": fields.String(required=True, description="The employee contract"),
    "admission": fields.String(required=True, description="The employee admission date", example="2024-03-01"),
    "rfc": fields.String(required=True, description="The employee rfc"),
    "curp": fields.String(required=True, description="The employee curp"),
    "nss": fields.String(required=True, description="The employee nss"),
    "emergency": fields.String(required=True, description="The employee emergency contact", example='{"name": null, "phone_number": "81 0000 0000"}'),
    "position": fields.String(required=True, description="The employee puesto"),
    "status": fields.String(required=True, description="The employee status"),
    "departure": fields.String(required=True, description="The employee departure", example='{"date": "2024-03-01", "reason": ""}'),
    "exam_id": fields.Integer(required=True, description="The medical examen id"),
    "birthday": fields.String(required=True, description="The employee birthday", example="2024-03-01"),
    "legajo":  fields.String(required=True, description="The employee legajo")
    })

employee_model_input = api.model('Employee', {
    "name": fields.String(required=True, description="The employee name"),
    "lastname":  fields.String(required=True, description="The employee lastname"),
    "phone": fields.String(required=True, description="The employee phone number"),
    "dep": fields.Integer(required=True, description="The employee department id"),
    "modality": fields.String(required=True, description="The employee modality"),
    "email": fields.String(required=True, description="The employee email"),
    "contract": fields.String(required=True, description="The employee contract"),
    "admission": fields.String(required=True, description="The employee admission date", example="2024-03-01"),
    "rfc": fields.String(required=True, description="The employee rfc"),
    "curp": fields.String(required=True, description="The employee curp"),
    "nss": fields.String(required=True, description="The employee nss"),
    "emergency": fields.String(required=True, description="The employee emergency contact", example='{"name": null, "phone_number": "81 0000 0000"}'),
    "position": fields.String(required=True, description="The employee puesto"),
    "status": fields.String(required=True, description="The employee status"),
    "departure": fields.String(required=True, description="The employee departure", example='{"date": "2024-03-01", "reason": ""}'),
    "birthday": fields.String(required=True, description="The employee birthday", example="2024-03-01"),
    "legajo":  fields.String(required=True, description="The employee legajo")
    })

employee_model_update = api.model('Employee update', {
    "id":  fields.Integer(required=True, description="The employee id"),
    "info": fields.Nested(employee_model_input)
})

employee_model_delete = api.model('Employee delete', {
    "id":  fields.Integer(required=True, description="The employee id")
})

employee_model_insert = api.model('Employee delete all', {
    "info":  fields.Nested(employee_model_input)
})

employees_info_model = api.model('EmployeeInfo', {
    "data": fields.List(fields.Nested(employee_model))
    })
