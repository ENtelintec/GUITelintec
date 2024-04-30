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

client_emp_sm_response_model = api.model('Employee', {
    'data': fields.List(fields.List(fields.String)),
    'comment': fields.String(description='comment'),
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

product_model_SM_selection = api.model('Product Data', {
    'id': fields.String(required=True, description='The product id'),
    'name': fields.String(required=True, description='The product name'),
    'udm': fields.String(required=True, description='The product unit of measure'),
    'stock':  fields.Integer(required=True, description='The product stock')
})

products_answer_model = api.model('AnswerProducts', {
    'data': fields.List(fields.Nested(product_model_SM_selection)),
    'page': fields.Integer(required=True, description='The page number send'),
    'pages': fields.Integer(required=True, description='The total number of'
                                                       ' pages with the selected limit')
})

products_request_model = api.model('ProductSearch', {
    'limit':  fields.Integer(required=True, description='The results limit', example=10),
    'page': fields.Integer(required=True, description='The output page default: 1', example=0)
})

sm_model = api.model('SM', {
    'id': fields.Integer(required=True, description='The id <ignored on add event>'),
    'sm_code': fields.String(required=True, description='The sm code'),
    'folio': fields.String(required=True, description='The folio'),
    'contract': fields.String(required=True, description='The contract'),
    'facility': fields.String(required=True, description='The facility'),
    'location': fields.String(required=True, description='The location'),
    'client_id': fields.Integer(required=True, description='The client id', example=1),
    'order_quotation': fields.String(required=True, description='The order or quotation'),
    'emp_id': fields.String(required=True, description='The employee id', example=1),
    'date': fields.String(required=True, description='The date'),
    'limit_date': fields.String(required=True, description='The limit date'),
    'status': fields.Integer(required=True, description='The status of the sm'),
    'history':  fields.String(required=True, description='The history'),
    'comment': fields.String(required=True, description='The comment')
})

table_sm_model = api.model('Table SM', {
    'data': fields.List(fields.Nested(sm_model)),
    'page': fields.Integer(required=True, description='The page number send'),
    'pages': fields.Integer(required=True, description='The total number of'
                                                       ' pages with the selected limit')
})

table_request_model = api.model('Table Request', {
    'limit':  fields.Integer(required=True, description='The results limit', example=10),
    'page': fields.Integer(required=True, description='The output page default: 1', example=0)
})

sm_product_request_model = api.model('SM Product Request', {
    'id': fields.Integer(required=True, description='The product id', example=1),
    'quantity': fields.Integer(required=True, description='The quantity'),
    'comment': fields.String(required=True, description='The comment')
})

sm_post_model = api.model('SM Post', {
    "info":  fields.Nested(sm_model),
    "items": fields.List(fields.Nested(sm_product_request_model))
})

sm_put_model = api.model('SM Put', {
    "info":  fields.Nested(sm_model),
    "items": fields.List(fields.Nested(sm_product_request_model)),
    "id": fields.Integer(required=True, description='The id')
})


delete_request_sm_model = api.model('Delete Request SM', {
    'id': fields.Integer(required=True, description='The id'),
    'sm_code': fields.String(required=True, description='The sm code')
})

fichaje_request_model = api.model('Fichaje Request', {
    'date': fields.String(required=True, description='The date', example="2024-03-01"),
})

fichaje_add_update_request_model = api.model('Fichaje Add Request', {
    'id': fields.Integer(required=True, description='The id <ignored when adding event>'),
    'date': fields.String(required=True, description='The date', example="2024-03-01"),
    'event':  fields.String(required=True, description='The event', example="falta"),
    'value':  fields.Float(required=True, description='The value', example=1.0),
    'comment':  fields.String(required=True, description='The comment', example="This is a comment"),
    'id_emp':  fields.Integer(required=True, description='The id of the editor employee ', example=1),
    'contract':  fields.String(required=True, description='The contract of the empployee', example="INFRA")
})

fichaje_delete_request_model = api.model('Fichaje Delete Request', {
    'id': fields.Integer(required=True, description='The id'),
    'date': fields.String(required=True, description='The date', example="2024-03-01"),
    'event':  fields.String(required=True, description='The event', example="falta"),
    'id_emp':  fields.Integer(required=True, description='The id of the editor employee ', example=1),
    'contract':  fields.String(required=True, description='The contract of the empployee', example="INFRA")
})

new_cliente_model = api.model('New Cliente', {
    'name': fields.String(required=True, description='The name'),
    'address': fields.String(required=True, description='The address'),
    'phone': fields.String(required=True, description='The phone'),
    'email': fields.String(required=True, description='The email'),
    'rfc': fields.String(required=True, description='The rfc')
})

new_product_model = api.model('New Product', {
    'name': fields.String(required=True, description='The name'),
    'udm': fields.String(required=True, description='The udm'),
    'supplier': fields.Float(required=True, description='The supplier'),
    'stock': fields.Integer(required=True, description='The stock'),
    'sku': fields.String(required=True, description='The sku'),
    'category':  fields.Integer(required=True, description='The category')
})
