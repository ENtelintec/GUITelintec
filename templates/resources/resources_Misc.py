# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 08/may./2024  at 10:00 $'

from flask_restx import Namespace, Resource

from static.Models.api_models import notification_insert_model, notification_request_model
from templates.Functions_Text import parse_data
from templates.Functions_midleware_misc import get_all_notification_db_user_status
from templates.controllers.notifications.Notifications_controller import insert_notification, update_status_notification

ns = Namespace('GUI/api/v1/misc')


@ns.route('/notifications/<int:id_emp>&<int:status>')
class Notifications(Resource):
    @ns.marshal_with(notification_request_model)
    def get(self, id_emp, status):
        status = status if status in [0, 1] else "%"
        code, result = get_all_notification_db_user_status(id_emp, status)
        print(result)
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
        