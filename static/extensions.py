# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:32 $'

import json

from dotenv import dotenv_values
from flask_restx import Api
from pathlib import Path
import ttkbootstrap as ttk

paths_dpb_folders = json.load(open("files/paths_general.json"))
local_father_path_dpb = "C:/Users/Edisson/Telintec Dropbox/SOFTWARE TELINTEC"
secrets = dotenv_values(".env")
api = Api()
# url_api = "http://127.0.0.1:5000/AuthAPI/api/v1/auth/loginUP"
url_api = "https://ec2-3-144-117-149.us-east-2.compute.amazonaws.com/AuthAPI/api/v1/auth/loginUP"
IMG_PATH_COLLAPSING = Path("./img")
ventanasApp = {
    "App.Deparment.Director": [
        "DB",
        "Notificaciones",
        "Chats",
        "Settings",
        "Tickets",
        "Cuenta",
    ],
    "App.Deparment.RRHH": [
        "Fichajes",
        "Examenes",
        "Emp. Detalles",
        "Vacaciones",
        "Empleados",
        "Encuestas",
        "Cuenta",
    ],
    "App.Deparment.Administrator": [
        "DB",
        "Notificaciones",
        "Chats",
        "Fichajes",
        "Tickets",
        "Settings",
        "Cuenta",
    ],
    "App.Deparment.ALMACEN": [
        "Home",
        "Entradas",
        "Salidas",
        "Inventario",
        "Suministros Diarios",
        "Inventario Int.",
        "Clients (A)",
        "Proveedores (A)",
        "Configuraciones (A)",
        "Cuenta",
    ],
    "App.Deparment.Default": ["Cuenta"],
}
cache_file_EM_path = "files/EM_cache.pkl"
cache_file_Fichajes_path = "files/Fichajes_cache.pkl"
cache_file_Tickets_path = "files/Tickets_cache.pkl"
cache_file_Chats_path = "files/Chats_cache.pkl"
cache_file_Notificaciones_path = "files/Notificaciones_cache.pkl"
cache_file_resume_fichaje = 'files/fichajes_resume_cache.pkl'
cache_file_emp_fichaje = 'files/emp_name_ids_fichajes_cache.pkl'
cache_oct_file_temp_path = "files/OCT_cache.csv"
cache_oct_fichaje_path = 'files/contracts_cache.pkl'
filepath_settings = "files/settings.json"
quizzes_RRHH = {
    "0": {"name": "Encuesta de Salida",
          "path": "files/quizz_salida.json",
          "type": 0},
    "1": {
        "name": "Encuesta de Norma_035_50",
        "path": "files/quizz_norma035_50_v1.json",
        "type": 1,
    },
    "2": {
        "name": "Encuesta de Norma_035_+50",
        "path": "files/quizz_norma035_+50_v2.json",
        "type": 2,
    },
}
conversion_quizzes_path = "files/conversions_quizzes.json"
quizz_out_path = "files/"
