# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:29 $'

import hashlib
from datetime import datetime

from flask import request

import templates.FunctionsFiles as cbf

from flask_restx import Resource, Namespace
from static.api_models import token_model, token_info_model, token_permissions_model, expected_headers_per, \
    permissions_answer, expected_headers_bot

ns = Namespace('GUI/api/v1')

