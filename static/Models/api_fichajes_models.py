# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 28/jun./2024  at 16:23 $'

from flask_restx import fields
from werkzeug.datastructures import FileStorage

from static.extensions import api


file_model = api.model('FileFichaje', {
    'name': fields.String(required=True, description='The name'),
    'path': fields.String(required=True, description='The path'),
    'extension': fields.String(required=True, description='The extension'),
    'size': fields.String(required=True, description='The size'),
    'report': fields.String(required=True, description='The type of report'),
    'date': fields.String(required=True, description='The date in the name of the file'),
    'pairs': fields.String(required=True, description='The pairs'),
    })


answer_files_fichajes_model = api.model('FichFiles', {
    "data": fields.List(fields.Nested(file_model)),
    "msg": fields.String()
    })

# {"name": name, "ID": id_emp, "worked_days": worked_days_f, "absence_days": days_absence,
#             "late_days": days_late, "extra_days": days_extra, "contract": contract,
#             "normal_data": normal_data_emp, "absence_data": absence_data_emp,
#             "prime_data": prime_data_emp, "late_data": late_data_emp, "extra_data": extra_data_emp}

data_dict_emp_fichaje_model = api.model('DataDictEMPFichajes', {
    "timestamp":  fields.String(required=True, description='The timestamp of the event'),
    "value": fields.Float(required=True, description='The value of the event'),
    "timestamps_extra": fields.List(fields.String, required=True, description='Extra timestamps for this event'),
    "comment":  fields.String(required=True, description='The comment of the event')
    })

data_emp_fichajes_model = api.model('DataEmpFichajes', {
    "name": fields.String(required=True, description='The name of the employee'),
    "ID": fields.String(required=True, description='The ID of the employee'),
    "contract": fields.String(required=True, description='The contract of the employee'),
    "normal_data": fields.List(fields.Nested(data_dict_emp_fichaje_model)),
    "absence_data": fields.List(fields.Nested(data_dict_emp_fichaje_model)),
    "prime_data": fields.List(fields.Nested(data_dict_emp_fichaje_model)),
    "late_data": fields.List(fields.Nested(data_dict_emp_fichaje_model)),
    "extra_data": fields.List(fields.Nested(data_dict_emp_fichaje_model)),
    "early_data":  fields.List(fields.Nested(data_dict_emp_fichaje_model))
    })

request_data_fichaje_files_model = api.model('FichFilesRequest', {
    "files": fields.List(fields.Nested(file_model)),
    "grace_init": fields.Integer(required=True, description='The time grace at the beggining of the day'),
    "grace_end": fields.Integer(required=True, description='The time grace at the end of the day'),
    "time_in": fields.String(required=True, description='The time in of the day', example="08:00"),
    "time_out": fields.String(required=True, description='The time out of the day', example="18:00")
    })

answer_fichajes_model = api.model('AnsFichFiles', {
    "data": fields.Nested(data_emp_fichajes_model),
    "msg": fields.String()
    })

expected_files = api.parser()
expected_files.add_argument('file', type=FileStorage, location='files', required=True)

