# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/nov./2023  at 17:32 $"


import os
from pathlib import Path

from dotenv import dotenv_values
from flask_restx import Api

_root_path = Path(__file__).resolve().parent.parent
_env_dir = _root_path if (_root_path / ".env").is_file() else _root_path.parent
_env_file = _env_dir / ".env"
if not _env_file.is_file():
    raise RuntimeError(f"No se encontro .env en {_root_path} ni en {_root_path.parent}")
secrets = dotenv_values(_env_file)
environment = os.environ.get("API_ENVIRONMENT") or secrets.get("API_ENVIRONMENT") or ""
if environment not in ("dev", "prod"):
    raise RuntimeError(
        f"API_ENVIRONMENT debe ser 'dev' o 'prod' (vale {environment!r}, leido de {_env_file})"
    )
# Interruptor del corte a tokens de 24 h (docs/tokens_solo_24h.md): sin la llave todo sigue como
# hasta hoy; TOKEN_LEGACY_ENABLED=0 solo acepta ES256 con exp e iat, hasta 24 h, y gui_system deja
# de ser firmante. Se borra junto con el código HS256 cuando el corte esté estable (P-224).
TOKEN_LEGACY_ENABLED = (os.environ.get("TOKEN_LEGACY_ENABLED") or secrets.get("TOKEN_LEGACY_ENABLED") or "1") != "0"
TOKEN_MAX_LIFETIME_SECONDS = 24 * 60 * 60
# Tokens ES256: una llave pública por kid (firmante), junto al .env (docs/token_es256_por_kid.md).
# "dev" firma los testers y solo se acepta en dev.
TOKEN_PUBLIC_KIDS = (
    ("lambda",)
    + (("gui_system",) if TOKEN_LEGACY_ENABLED else ())
    + (("dev",) if environment == "dev" else ())
)
token_public_key_paths = {kid: str(_env_dir / f"token_public_{kid}.pem") for kid in TOKEN_PUBLIC_KIDS}
TOKEN_LEEWAY_SECONDS = 30  # desfase de reloj tolerado en exp/iat entre el firmante y el API
api = Api()
local_father_path_dpb = "C:/Users/Edisson/Telintec Dropbox/SOFTWARE TELINTEC"
IMG_PATH_COLLAPSING = Path("./img")
ventanasApp_path = "static/ventanasAppGUI.json"
cache_file_EM_path = "files/EM_cache.pkl"
cache_file_Tickets_path = "files/Tickets_cache.pkl"
cache_file_Chats_path = "files/Chats_cache.pkl"
cache_file_nominas = "files/nominas_cache.json"
cache_file_Notificaciones_path = "files/Notificaciones_cache.pkl"
cache_file_resume_fichaje_path = "files/fichajes_resume_cache.pkl"
file_temp_zip = "files/docs.zip"
filepath_settings = "files/settings.json"
filepath_daemons = "files/flags_daemons.json"
filepath_recomendations = "files/recomendations.json"
file_size_pages = "files/size_pages.json"
# Los templates y rubricas de encuestas viven en la BD
# (sql_telintec_mod_rrhh.quizz_models, CRUD en /rrhh/quizz/models). Los
# files/quizz_*.json y files/rubrics/*.json del repo son la fuente del seed
# (scripts_db_handle/seed_quizz_models.py), no se leen en runtime.
quizzes_temp_pdf = "files/quizz_out/temp_quiz.pdf"
files_user = "files/users.json"
file_codebar = "files/codebar.pdf"
conversion_quizzes_path = "files/conversions_quizzes.json"
filepath_recommendations = "files/recommendations.json"
quizz_out_path = "files/quizz_out/"
log_file_bitacora_path = "files/logs/bitacora"
log_file_sm_path = "files/logs/sm"
log_file_sgi_chv = "files/logs/sgi_chv"
log_file_sgi_vouchers = "files/logs/sgi_vouchers"
log_file_db = "files/logs/db"
log_file_admin = "files/logs/admin"
log_file_admin_collecions = "files/logs/admin_collections"
log_file_almacen = "files/logs/almacen"
log_file_po = "files/logs/po"
log_file_rh = "files/logs/rh"
log_file_users = "files/logs/users"
log_file_cda = "files/logs/cda"
log_file_sucursal = "files/logs/sucursal"
log_file_sgi_formats = "files/logs/sgi_formats"
filepath_bitacora_download = "files/quizz_out/temp_bitacora.csv"
filepath_inventory_form = "files/inventory_temp.pdf"
filepath_inventory_form_excel = "files/inventory_temp.xlsx"
filepath_inventory_form_movements_pdf = "files/movements_temp.pdf"
filepath_inventory_form_movements_excel = "files/movements_temp.xlsx"
filepath_sm_pdf = "files/sm_temp.pdf"
filepath_po_pdf = "files/po_temp.pdf"
filepath_remission_pdf = "files/remission_temp.pdf"
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
# dict_depts_identifiers = {
#     1: ["DIRE", "SGI"],
#     2: "OP",
#     3: "ADMON",
#     4: "RH",
#     3001: ["ALM", "CDA-VEH"],
#     3002: "CDA-TI",
#     3003: "CDA-EQO",
#     3004: "CDA-MED",
#     2001: "SST",
# }
# tabs_sm = {
#     "sm-dire-": "Direccion",
#     "sm-sgi-": "SGI",
#     "sm-op-": "Operaciones",
#     "sm-admon-": "Administracion",
#     "sm-rrhh-": "RH",
#     "sm-alm-": "Almacen",
#     "sm-pa-cda-veh-": "CDA Vehiculos",
#     "sm-pa-cda-ti-": "CDA TI",
#     "sm-pa-cda-eqo-": "Inmuebles",
#     "sm-pa-cda-med-": "CDA Eq. Medición",
#     "sm-sst-": "Seguridad",
#     "sm-5000-": "INFRA",
#     "sm-8272-": "GRUAS",
#     "sm-3650-": "PESQUERIA",
#     "sm-9971-": "AUTO",
#     "sm-0701-": "RFID",
#     "sm-3122-": "CCTV",
#     "sm-3487-": "PUEBLA",
#     "sm-8514-": "REDES-MTTO",
# }
format_timestamps_filename = "%Y-%m-%d"
HOST_DB_DEFAULT = "HOST_DB" if environment != "prod" else "HOST_DB_AWS"
USER_DB_DEFAULT = "USER_SQL" if environment != "prod" else "USER_SQL_AWS"
PASS_DB_DEFAULT = "PASS_SQL" if environment != "prod" else "PASS_SQL_AWS"
