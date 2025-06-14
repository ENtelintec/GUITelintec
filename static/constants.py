# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/nov./2023  at 17:32 $"

import json

from dotenv import dotenv_values
from flask_restx import Api
from pathlib import Path

environment = "prod"
secrets = dotenv_values(".env") if environment != "prod" else dotenv_values("../.env")
domain_path = "domain.pem" if environment != "prod" else "../domain.pem"
api = Api()
paths_dpb_folders = json.load(open("files/paths_general.json"))
local_father_path_dpb = "C:/Users/Edisson/Telintec Dropbox/SOFTWARE TELINTEC"
IMG_PATH_COLLAPSING = Path("./img")
ventanasApp_path = "static/ventanasAppGUI.json"
cache_file_EM_path = "files/EM_cache.pkl"
cache_file_Fichajes_path = "files/Fichajes_cache.pkl"
cache_file_Tickets_path = "files/Tickets_cache.pkl"
cache_file_Chats_path = "files/Chats_cache.pkl"
cache_file_nominas = "files/nominas_cache.json"
index_file_nominas = "files/nominas_index.json"
cache_file_Notificaciones_path = "files/Notificaciones_cache.pkl"
cache_file_resume_fichaje_path = "files/fichajes_resume_cache.pkl"
cache_file_emp_fichaje = "files/emp_name_ids_fichajes_cache.pkl"
files_fichaje_path = "files/files_fichaje/"
file_temp_zip = "files/docs.zip"
cache_oct_file_temp_path = "files/OCT_cache.csv"
cache_oct_fichaje_path = "files/contracts_cache.pkl"
filepath_settings = "files/settings.json"
filepath_daemons = "files/flags_daemons.json"
filepath_recomendations = "files/recomendations.json"
file_size_pages = "files/size_pages.json"
quizzes_dir_path = "static/quizzes_dir.json"
quizzes_temp_pdf = "files/quizz_out/temp_quiz.pdf"
files_user = "files/users.json"
file_codebar = "files/codebar.pdf"
quizzes_RRHH = {
    "0": {"name": "Encuesta de Salida", "path": "files/quizz_salida.json", "type": 0},
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
    "3": {
        "name": "Encuesta de clima laboral",
        "path": "files/quizz_clima_laboral.json",
        "type": 3,
    },
    "4": {
        "name": "Encuesta eva 360",
        "path": "files/quizz_eva_360.json",
        "type": 4,
    },
}
conversion_quizzes_path = "files/conversions_quizzes.json"
filepath_recommendations = "files/recommendations.json"
quizz_out_path = "files/quizz_out/"
log_file_bitacora_path = "files/logs/bitacora"
log_file_sm_path = "files/logs/sm"
log_file_db = "files/logs/db"
log_file_admin = "files/logs/admin"
log_file_almacen = "files/logs/almacen"
path_contract_files = "files/contracts"
filepath_bitacora_download = "files/quizz_out/temp_bitacora.csv"
filepath_inventory_form = "files/inventory_temp.pdf"
filepath_inventory_form_excel = "files/inventory_temp.xlsx"
filepath_inventory_form_movements_pdf = "files/movements_temp.pdf"
filepath_inventory_form_movements_excel = "files/movements_temp.xlsx"
filepath_sm_pdf = "files/sm_temp.pdf"
filepath_fichaje_temp = "files/files_fichaje/fichaje_temp.xlsx"
filepath_ternium_temp = "files/files_fichaje/ternium_temp.xls"
patterns_files_fichaje = ["Fichaje", "Ternium"]
department_tools_openAI = {
    "director": "files/tools_AV_default.json",
    "rrhh": "files/tools_AV_rrhh.json",
    "administrator": "files/tools_AV_default.json",
    "almacen": "files/tools_AV_almacen.json",
    "default": "files/tools_AV_default.json",
}
tools_AV_avaliable = {
    "default": [{"type": "code_interpreter"}, {"type": "retrieval"}],
    "rrhh": [
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {
            "type": "function",
            "name": "getTotalFichajeEmployee",
            "args": ["id", "name", "date"],
        },
        {
            "type": "function",
            "name": "getActiveEmployees",
            "args": ["status", "quantity", "date"],
        },
        {"type": "function", "name": "getEmployeeInfo", "args": ["id"]},
    ],
    "almacen": [
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {"type": "function", "name": "getProductCategories", "args": ["name"]},
        {
            "type": "function",
            "name": "getProductsAlmacen",
            "args": ["name", "id", "category"],
        },
        {
            "type": "function",
            "name": "getHighStockProducts",
            "args": ["category", "quantity"],
        },
        {
            "type": "function",
            "name": "getLowStockProducts",
            "args": ["category", "quantity"],
        },
        {"type": "function", "name": "getCostumer", "args": ["name", "id"]},
        {"type": "function", "name": "getSupplier", "args": ["name", "id"]},
        {
            "type": "function",
            "name": "getOrder",
            "args": ["id", "customer", "status", "id_customer", "date"],
        },
        {
            "type": "function",
            "name": "getProductMovement",
            "args": ["type", "id", "id_p", "date"],
        },
        {"type": "function", "name": "getSupplyInventory", "args": ["name", "id"]},
        {"type": "function", "name": "getNoStockProducts", "args": ["category"]},
    ],
}
windows_names_db_frame = [
    "Empleados",
    "Clientes",
    "Departamentos",
    "Encargados",
    "Proveedores",
    "Productos",
    "Ordenes",
    "Tickets",
    "Chats",
    "O. Virtuales",
]
delta_bitacora_edit = 14
status_dic = {
    0: "Pendiente",
    1: "En Proceso",
    2: "Completado",
    3: "Finalizado",
    -1: "Cancelado",
}
format_timestamps = "%Y-%m-%d %H:%M:%S"
format_timestamps_tz = "%Y-%m-%d %H:%M:%S"
timezone_software = "America/Mexico_City"
format_date = "%Y-%m-%d"
format_date_fichaje_file = "%d-%m-%Y"
dict_deps = {
    "Direccion": 1,
    "Operaciones": 2,
    "Administracion": 3,
    "RRHH": 4,
    "REPSE": 5,
    "IA": 6,
    "Otros": 7,
}
# almacen en administracion
# los auxiliares no generan
# control de activos (mariscal TI)
# coordinador de almacen (ALM, CDA-VEH)
# sgi pertenece a direccion el puesto se llama coordinador de sgi (Jennfier)
# sgi enrique DIRE pero las hace Jenny
# rh crean sm todos
dict_depts_identifiers = {
    1: ["DIRE", "SGI"],
    2: "OP",
    3: "ADMON",
    4: "RH",
    3001: ["ALM", "PA-CDA-VEH"],
    3002: "PA-CDA-TI",
    3003: "PA-CDA-EQO",
    3004: "PA-CDA-MED",
    2001: "SST",
}
tabs_sm = {
    "sm-dire-": "Direccion",
    "sm-sgi-": "SGI",
    "sm-op-": "Operaciones",
    "sm-admon-": "Administracion",
    "sm-rh-": "RH",
    "sm-alm-": "Almacen",
    "sm-pa-cda-veh-": "CDA Vehiculos",
    "sm-pa-cda-ti-": "CDA TI",
    "sm-pa-cda-eqo-": "Inmuebles",
    "sm-pa-cda-med-": "CDA Eq. Medición",
    "sm-sst-": "Seguridad",
    "sm-5000-": "INFRA",
    "sm-8272-": "GRUAS",
    "sm-3650-": "PESQUERIA",
    "sm-9971-": "AUTO",
    "sm-0701-": "RFID",
    "sm-3122-": "CCTV",
    "sm-3487-": "PUEBLA",
}
format_timestamps_filename = "%Y-%m-%d"
HOST_DB_DEFAULT = "HOST_DB" if environment != "prod" else "HOST_DB_AWS"
USER_DB_DEFAULT = "USER_SQL" if environment != "prod" else "USER_SQL_AWS"
PASS_DB_DEFAULT = "PASS_SQL" if environment != "prod" else "PASS_SQL_AWS"
