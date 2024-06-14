# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/abr./2024  at 9:53 $'

from datetime import datetime

from flask_restx import Resource, Namespace

from static.Models.api_models import fichaje_request_model, fichaje_add_update_request_model, \
    fichaje_delete_request_model
from static.Models.api_sm_models import client_emp_sm_response_model
from static.extensions import delta_bitacora_edit
from templates.Functions_AuxFiles import get_events_op_date, update_bitacora, update_bitacora_value, \
    erase_value_bitacora
from templates.Functions_DB_midleware import check_date_difference
from templates.Functions_Text import parse_data
from templates.controllers.employees.employees_controller import get_employees_op_names

ns = Namespace('GUI/api/v1/bitacora')


@ns.route('/employees')
class Employees(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    def get(self):
        flag, error, result = get_employees_op_names()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route('/fichaje/table')
class Fichaje(Resource):
    @ns.expect(fichaje_request_model)
    def post(self):
        code, data = parse_data(ns.payload, 9)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        date = data["date"]
        date = datetime.strptime(date, '%Y-%m-%d')
        events, columns = get_events_op_date(date, False)
        return {"data": events, "columns": columns}, 200


@ns.route('/fichaje/event')
class FichajeAPI(Resource):
    @ns.expect(fichaje_add_update_request_model)
    def post(self):
        code, data = parse_data(ns.payload, 10)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        out = check_date_difference(data["date"], delta_bitacora_edit)
        if not out:
            return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
        flag, error, result = update_bitacora(
            data["id_emp"], data["event"], (data["date"], data["value"], data["comment"], data["contract"]))
        if flag:
            return {"answer": "The event has been added"}, 201
        elif error is not None:
            print(error)
            return {"answer": "There has been an error at adding the bitacora"}, 404
        else:
            return {"answer": "Fail to add registry"}, 404

    @ns.expect(fichaje_add_update_request_model)
    def put(self):
        code, data = parse_data(ns.payload, 10)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        out = check_date_difference(data["date"], delta_bitacora_edit)
        if not out:
            return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
        flag, error, result = update_bitacora_value(
            data["id_emp"], data["event"], (data["date"], data["value"], data["comment"], data["contract"]))
        if flag:
            return {"answer": "The event has been updated"}, 200
        elif error is not None:
            print(error)
            return {"answer": "There has been an error at updating the bitacora"}, 404
        else:
            return {"answer": "Fail to update registry"}, 404

    @ns.expect(fichaje_delete_request_model)
    def delete(self):
        code, data = parse_data(ns.payload, 11)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        out = check_date_difference(data["date"], delta_bitacora_edit)
        if not out:
            return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
        flag, error, result = erase_value_bitacora(data["id_emp"], data["event"], (data["date"], data["contract"]))
        if flag:
            return {"answer": "The event has been deleted"}, 200
        elif error is not None:
            print(error)
            return {"answer": "There has been an error at deleting the bitacora"}, 404
        else:
            return {"answer": "Fail to delete registry"}, 404
