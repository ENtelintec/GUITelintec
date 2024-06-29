# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 28/jun./2024  at 16:23 $'

from flask_restx import fields
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


request_data_fichaje_files_model = api.model('FichFilesRequest', {
    "files": fields.List(fields.Nested(file_model)),
    "grace_init": fields.Integer(required=True, description='The time grace at the beggining of the day'),
    "grace_end": fields.Integer(required=True, description='The time grace at the end of the day'),
    })
