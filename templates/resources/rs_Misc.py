# -*- coding: utf-8 -*-

from flask import request, send_file
from flask_restx import Namespace, Resource

from static.constants import filepath_settings
from static.Models.api_models import (
    NotificationInsertForm,
    NotificationUpdateForm,
    RequestAVResponseForm,
    TaskDeleteForm,
    TaskInsertForm,
    TaskUpdateForm,
    expected_headers_per,
    notification_insert_model,
    request_av_response_model,
    task_delete_model,
    task_insert_model,
    task_update_model,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_DB_midleware import (
    create_task_from_api,
    delete_task_from_api,
    update_task_from_api,
)
from templates.resources.midleware.MD_QuizzModels import get_quizz_template_api
from templates.resources.midleware.Functions_midleware_misc import (
    create_notification_from_api,
    get_all_dashboard_data,
    get_all_notification_db_permission,
    get_all_notification_db_user_status,
    get_files_openai,
    get_response_AV,
    get_task_by_id_employee,
    update_notification_status_from_api,
)

__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 10:00 $"

ns = Namespace("GUI/api/v1/misc")


@ns.route("/notifications/employee/<int:id_emp>&<int:status>")
class Notifications(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp, status):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        status = status if status in [0, 1] else "%"
        data_out, code = get_all_notification_db_user_status(id_emp, status, data_token)
        return data_out, code


@ns.route("/notifications/all/<int:status>")
class NotificationsAll(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        status = status if status in [0, 1] else "%"
        data_out, code = get_all_notification_db_permission(status, data_token)
        return data_out, code


@ns.route("/notification")
class Notification(Resource):
    @ns.expect(expected_headers_per, notification_insert_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = NotificationInsertForm.from_json(ns.payload)  # pyrefly:ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_notification_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, notification_insert_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = NotificationUpdateForm.from_json(ns.payload)  # pyrefly:ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_notification_status_from_api(data, data_token)
        return data_out, code


@ns.route("/download/gui/settings")
class DownloadFileVacations(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        try:
            return send_file(filepath_settings, as_attachment=True)
        except Exception as e:
            return {"data": None, "msg": "Error al descargar el archivo de configuración", "error": str(e)}, 400


@ns.route("/AV/response")
class ResponseAV(Resource):
    @ns.expect(expected_headers_per, request_av_response_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["almacen", "operaciones", "rrhh", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = RequestAVResponseForm.from_json(ns.payload)  # pyrefly:ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        try:
            files, res, id_chat = get_response_AV(
                data["department"],
                data["msg"],
                data["files"],
                data["filename"],
                data["id"],
            )
            return {"answer": res, "files": files, "id": id_chat}, 200
        except Exception as e:
            return {"data": None, "msg": "Error al obtener respuesta del asistente virtual", "error": str(e)}, 400


@ns.route("/AV/files/<string:department>")
class FilesAV(Resource):
    @ns.expect(expected_headers_per)
    def get(self, department):
        flag, data_token, msg = token_verification_procedure(
            request, department=["almacen", "operaciones", "rrhh", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        try:
            files = get_files_openai(department)
            if len(files) == 0:
                files = []
            return {"files": files}, 200
        except Exception as e:
            return {"data": None, "msg": "Error al obtener archivos del asistente virtual", "error": str(e)}, 400


@ns.route("/task/quizz")
class Task(Resource):
    @ns.expect(expected_headers_per, task_insert_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TaskInsertForm.from_json(ns.payload)  # pyrefly:ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        response, code = create_task_from_api(data, data_token)
        return response, code

    @ns.expect(expected_headers_per, task_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["rrhh", "common"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TaskUpdateForm.from_json(ns.payload)  # pyrefly:ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        reponse, code = update_task_from_api(data, data_token)
        return reponse, code

    @ns.expect(expected_headers_per, task_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TaskDeleteForm.from_json(ns.payload)  # pyrefly:ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        response, code = delete_task_from_api(data, data_token)
        return response, code


@ns.route("/task/<int:emp_id>")
class TaskGui(Resource):
    @ns.expect(expected_headers_per)
    def get(self, emp_id):
        flag, data_token, msg = token_verification_procedure(request, emp_id=emp_id)
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_task_by_id_employee(emp_id, data_token)
        return data_out, code


@ns.route("/download/quizz/<int:type_q>")
class DownloadFileQuizz(Resource):
    @ns.expect(expected_headers_per)
    def get(self, type_q):
        """Template del cuestionario desde la BD (quizz_models); misma ruta y
        shape de siempre, el front de captura no se entera del cambio."""
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_quizz_template_api(type_q, data_token)
        return data_out, code


@ns.route("/dashboard")
class Dashboard(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["Basic", "Common"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_all_dashboard_data(data_token)
        return data_out, code
