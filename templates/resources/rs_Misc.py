# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 10:00 $"

import json

from flask import send_file, request
from flask_restx import Namespace, Resource

from static.Models.api_models import (
    notification_insert_model,
    notification_request_model,
    request_av_response_model,
    response_av_model,
    response_files_av_model,
    NotificationInsertForm,
    RequestAVResponseForm,
    task_insert_model,
    TaskInsertForm,
    task_update_model,
    TaskUpdateForm,
    task_delete_model,
    TaskDeleteForm,
    expected_headers_per,
    NotificationUpdateForm,
)
from static.constants import filepath_settings, quizzes_RRHH
from templates.controllers.notifications.Notifications_controller import (
    insert_notification,
    update_status_notification,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_DB_midleware import (
    create_task_from_api,
    update_task_from_api,
    delete_task_from_api,
)
from templates.resources.midleware.Functions_midleware_misc import (
    get_all_notification_db_user_status,
    get_response_AV,
    get_files_openai,
    get_all_notification_db_permission,
    get_task_by_id_employee,
    get_all_dashboard_data,
)

ns = Namespace("GUI/api/v1/misc")


@ns.route("/notifications/employee/<int:id_emp>&<int:status>")
class Notifications(Resource):
    @ns.marshal_with(notification_request_model)
    @ns.expect(expected_headers_per)
    def get(self, id_emp, status):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        status = status if status in [0, 1] else "%"
        code, result = get_all_notification_db_user_status(id_emp, status)
        return {"data": result, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route("/notifications/all/<int:status>")
class NotificationsAll(Resource):
    @ns.marshal_with(notification_request_model)
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        status = status if status in [0, 1] else "%"
        code, result = get_all_notification_db_permission(status, data_token)
        return {"data": result, "msg": "Ok" if code == 200 else "Error"}, code


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
        validator = NotificationInsertForm.from_json(ns.payload) # pyrefly:ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = insert_notification(data["info"])
        if flag:
            return {"msg": "Ok", "data": str(result)}, 200
        else:
            return {"error": error, "data": str(result)}, 400

    @ns.expect(expected_headers_per, notification_insert_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = NotificationUpdateForm.from_json(ns.payload)    # pyrefly:ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        # data["id"] = data["info"]["id"]
        flag, error, result = update_status_notification(
            data["id"], data["info"]["status"]
        )
        if flag:
            return {"msg": "Ok", "data": str(result)}, 200
        else:
            return {"error": error, "data": str(result)}, 400


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
            return {"data": f"Error en el tipo de quizz: {str(e)}"}, 400


@ns.route("/AV/response")
class ResponseAV(Resource):
    @ns.marshal_with(response_av_model)
    @ns.expect(expected_headers_per, request_av_response_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["almacen", "operaciones", "rrhh", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = RequestAVResponseForm.from_json(ns.payload) # pyrefly:ignore
        if not validator.validate():
            return {"error": validator.errors}, 400
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
            return {"answer": f"Error at getting answer from openAI: {str(e)}"}, 400


@ns.route("/AV/files/<string:department>")
class FilesAV(Resource):
    @ns.marshal_with(response_files_av_model)
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
            return {"files": [], "error": str(e)}, 400


@ns.route("/task/quizz")
class Task(Resource):
    @ns.expect(expected_headers_per, task_insert_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TaskInsertForm.from_json(ns.payload)    # pyrefly:ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        response, code = create_task_from_api(data)
        return response, code

    @ns.expect(expected_headers_per, task_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["rrhh", "common"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TaskUpdateForm.from_json(ns.payload)    # pyrefly:ignore
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        reponse, code = update_task_from_api(data)
        return reponse, code

    @ns.expect(expected_headers_per, task_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TaskDeleteForm.from_json(ns.payload)    # pyrefly:ignore
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
        data, code = get_task_by_id_employee(emp_id)
        if code == 200:
            return {"data": data}, 200
        else:
            return {"data": data, "msg": "Error"}, code


@ns.route("/download/quizz/<int:type_q>")
class DownloadFileQuizz(Resource):
    @ns.expect(expected_headers_per)
    def get(self, type_q):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        try:
            quizz = quizzes_RRHH[str(type_q)]
            with open(quizz["path"], "r", encoding="utf-8") as file:
                json_data = json.load(file)
            return {"data": json_data, "msg": "ok"}, 200
        except Exception as e:
            return {"data": f"Error en el tipo de quizz: {str(e)}"}, 400


@ns.route("/dashboard")
class Dashboard(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="basic"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_all_dashboard_data(data_token)
        if code == 200:
            return {"data": data}, 200
        else:
            return {"data": data, "msg": "Error"}, code
