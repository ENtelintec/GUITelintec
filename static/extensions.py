# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:32 $'

from dotenv import dotenv_values
from flask_restx import Api


secrets = dotenv_values(".env")
api = Api(doc='/GUI/doc')
