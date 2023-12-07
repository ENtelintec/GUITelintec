# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:32 $'

import json

from dotenv import dotenv_values
from flask_restx import Api
from pathlib import Path

paths_dpb_folders = json.load(open('files/paths_general.json'))
local_father_path_dpb = 'C:/Users/Edisson/Telintec Dropbox/SOFTWARE TELINTEC'
secrets = dotenv_values(".env")
api = Api(doc='/GUI/doc')
url_api = "http://127.0.0.1:5000/AuthAPI/api/v1/auth/loginUP"
IMG_PATH_COLLAPSING = Path('./img')
ventanasApp = {
    'App.Deparment.Director':  ["DB", "Notificaciones", "Chats", "Settings", "Tickets"],
    'App.Deparment.RRHH':  ["Notificaciones", "Settings"],
    'App.Deparment.Administrator':  ["DB", "Notificaciones", "Chats", "Settings", "Tickets"],
    'App.Deparment.Default':  ["Notificaciones"]
}