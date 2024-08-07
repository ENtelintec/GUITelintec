# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 08/may./2024  at 10:00 $'

from flask import send_file
from flask_restx import Namespace, Resource

from static.Models.api_models import notification_insert_model, notification_request_model, request_av_response_model, \
    response_av_model, response_files_av_model
from static.extensions import filepath_settings
from templates.Functions_Text import parse_data
from templates.resources.midleware.Functions_midleware_misc import get_all_notification_db_user_status, get_response_AV, \
    get_files_openai, get_all_notification_db_permission
from templates.controllers.notifications.Notifications_controller import insert_notification, update_status_notification

ns = Namespace('GUI/api/v1/misc')


@ns.route('/notifications/employee/<int:id_emp>&<int:status>')
class Notifications(Resource):
    @ns.marshal_with(notification_request_model)
    def get(self, id_emp, status):
        status = status if status in [0, 1] else "%"
        code, result = get_all_notification_db_user_status(id_emp, status)
        return {"data": result, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route('/notifications/permission/<string:permission>&<int:status>')
class NotificationsPermission(Resource):
    @ns.marshal_with(notification_request_model)
    def get(self, permission, status):
        status = status if status in [0, 1] else "%"
        code, result = get_all_notification_db_permission(permission, status)
        return {"data": result, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route('/notification')
class Notification(Resource):
    @ns.expect(notification_insert_model)
    def post(self):
        code, data = parse_data(ns.payload, 19)
        if code != 200:
            return {"error": data}, code
        flag, error, result = insert_notification(data["info"])
        if flag:
            return {"msg": "Ok", "data": str(result)}, 200
        else:
            return {"error": error, "data": str(result)}, 400
    
    @ns.expect(notification_insert_model)
    def put(self):
        code, data = parse_data(ns.payload, 19)
        if code != 200:
            return {"error": data}, code
        flag, error, result = update_status_notification(data["id"], data["info"]["status"])
        if flag:
            return {"msg": "Ok", "data": str(result)}, 200
        else:
            return {"error": error, "data": str(result)}, 400

    @ns.route('/download/gui/settings')
    class DownloadFileVacations(Resource):
        def get(self):
            try:
                return send_file(filepath_settings, as_attachment=True)
            except Exception as e:
                return {"data": f"Error en el tipo de quizz: {str(e)}"}, 400


@ns.route('/AV/response')
class ResponseAV(Resource):
    @ns.marshal_with(response_av_model)
    @ns.expect(request_av_response_model)
    def post(self):
        code, data = parse_data(ns.payload, 20)
        if code != 200:
            return {"msg": f"Error in the data structure: {str(data)}"}, code
        try:
            files, res, id_chat = get_response_AV(data["department"], data["msg"], data["files"], data["filename"], data["id"])
            return {"answer": res, "files": files, "id": id_chat}, 200
        except Exception as e:
            return {"answer": f"Error at getting answer from openAI: {str(e)}"}, 400


@ns.route('/AV/files/<string:department>')
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