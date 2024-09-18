# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 10:00 $"

from flask import send_file
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
)
from static.extensions import filepath_settings
from templates.Functions_GUI_Utils import create_notification_permission
from templates.controllers.misc.tasks_controller import (
    create_task,
    update_task,
    delete_task,
)
from templates.resources.midleware.Functions_midleware_misc import (
    get_all_notification_db_user_status,
    get_response_AV,
    get_files_openai,
    get_all_notification_db_permission,
    get_task_by_id_employee,
)
from templates.controllers.notifications.Notifications_controller import (
    insert_notification,
    update_status_notification,
)

ns = Namespace("GUI/api/v1/misc")


@ns.route("/notifications/employee/<int:id_emp>&<int:status>")
class Notifications(Resource):
    @ns.marshal_with(notification_request_model)
    def get(self, id_emp, status):
        status = status if status in [0, 1] else "%"
        code, result = get_all_notification_db_user_status(id_emp, status)
        return {"data": result, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route("/notifications/permission/<string:permission>&<int:status>")
class NotificationsPermission(Resource):
    @ns.marshal_with(notification_request_model)
    def get(self, permission, status):
        status = status if status in [0, 1] else "%"
        code, result = get_all_notification_db_permission(permission, status)
        return {"data": result, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route("/notification")
class Notification(Resource):
    @ns.expect(notification_insert_model)
    def post(self):
        validator = NotificationInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = insert_notification(data["info"])
        if flag:
            return {"msg": "Ok", "data": str(result)}, 200
        else:
            return {"error": error, "data": str(result)}, 400

    @ns.expect(notification_insert_model)
    def put(self):
        validator = NotificationInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data["id"] = data["info"]["id"]
        flag, error, result = update_status_notification(
            data["id"], data["info"]["status"]
        )
        if flag:
            return {"msg": "Ok", "data": str(result)}, 200
        else:
            return {"error": error, "data": str(result)}, 400


@ns.route("/download/gui/settings")
class DownloadFileVacations(Resource):
    def get(self):
        try:
            return send_file(filepath_settings, as_attachment=True)
        except Exception as e:
            return {"data": f"Error en el tipo de quizz: {str(e)}"}, 400


@ns.route("/AV/response")
class ResponseAV(Resource):
    @ns.marshal_with(response_av_model)
    @ns.expect(request_av_response_model)
    def post(self):
        validator = RequestAVResponseForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
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
    def get(self, department):
        try:
            files = get_files_openai(department)
            if len(files) == 0:
                files = []
            return {"files": files}, 200
        except Exception as e:
            return {"files": [], "error": str(e)}, 400


@ns.route("/task/quizz")
class Task(Resource):
    @ns.expect(task_insert_model)
    def post(self):
        validator = TaskInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = create_task(
            data["title"],
            data["emp_destiny"],
            data["emp_origin"],
            data["date_limit"],
            data["metadata"],
        )
        if flag:
            msg = f"Se creo una tarea ({result}) {data['title']} para {data['metadata']['name_emp']}"
            create_notification_permission(
                msg,
                ["RRHH"],
                "Nuevo tarea quizz creada",
                data["emp_origin"],
                data["emp_destiny"],
            )
            return {"msg": f"Ok-->{msg}"}, 201
        else:
            print(error)
            return {"msg": "Ok", "data": str(error)}, 400

    @ns.expect(task_update_model)
    def put(self):
        print(ns.payload)
        validator = TaskUpdateForm.from_json(ns.payload)

        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        print(data["body"].keys())
        flag, error, result = update_task(data["id"], data["body"])
        if flag:
            msg = f"Se actualizo la tarea {data['body']['title']} para {data['body']['metadata']['name_emp']}"
            create_notification_permission(
                msg,
                ["RRHH"],
                "Tarea quizz actualizada",
                data["body"]["emp_origin"],
                data["body"]["emp_destiny"],
            )
            return {"msg": f"Ok-->{msg}"}, 200
        else:
            return {"msg": "Fail", "data": str(error)}, 400

    @ns.expect(task_delete_model)
    def delete(self):
        validator = TaskDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = delete_task(data["id"])
        if flag:
            msg = f"Se elimino la tarea ({result}) {data['body']['title']} para {data['body']['metadata']['name_emp']}"
            create_notification_permission(
                msg,
                ["RRHH"],
                "Tarea quizz eliminada",
                data["body"]["emp_origin"],
                data["body"]["emp_destiny"],
            )
            return {"msg": f"Ok-->{msg}"}, 200
        else:
            return {"msg": "Fail", "data": str(error)}, 400


@ns.route("/task/<int:emp_id>")
class TaskGui(Resource):
    def get(self, emp_id):
        data, code = get_task_by_id_employee(emp_id)
        if code == 200:
            return {"data": data}, 200
        else:
            return {"data": data, "msg": "Error"}, code
