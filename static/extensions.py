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
api = Api()
# url_api = "http://127.0.0.1:5000/AuthAPI/api/v1/auth/loginUP"
url_api = "https://ec2-3-144-117-149.us-east-2.compute.amazonaws.com/AuthAPI/api/v1/auth/loginUP"
IMG_PATH_COLLAPSING = Path('./img')
ventanasApp = {
    'App.Deparment.Director': ["DB", "Notificaciones", "Chats", "Settings", "Tickets", "Cuenta"],
    'App.Deparment.RRHH': ["Fichajes", "Examenes", "Emp. Detalles", "Empleados", "Cuenta"],
    'App.Deparment.Administrator': ["DB", "Notificaciones", "Chats", "Fichajes", "Tickets", "Settings", "Cuenta"],
    'App.Deparment.ALMACEN': ["Home", "Clients (A)", "Inventario", "Entradas", "Salidas",  "Devoluciones", "Ordenes (A)",
                              "Proveedores (A)", "Configuraciones (A)", "Cuenta"],
    'App.Deparment.Default': ["Notificaciones", "Cuenta"]
}
cache_file_EM_path = "files/EM_cache.pkl"
cache_file_Fichajes_path = "files/Fichajes_cache.pkl"
cache_file_Tickets_path = "files/Tickets_cache.pkl"
cache_file_Chats_path = "files/Chats_cache.pkl"
cache_file_Notificaciones_path = "files/Notificaciones_cache.pkl"
