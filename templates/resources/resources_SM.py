# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/abr./2024  at 10:26 $'

from flask_restx import Resource, Namespace
from static.api_models import client_emp_sm_response_model, products_answer_model, products_request_model, \
    sm_post_model, delete_request_sm_model, sm_put_model
from templates.Functions_DB_midleware import get_products_sm
from templates.Functions_SQL import get_sm_employees, get_sm_clients, insert_sm_db, delete_sm_db, update_sm_db
from templates.Functions_Text import parse_data

ns = Namespace('GUI/api/v1/sm')


@ns.route('/employees')
class Employees(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    def get(self):
        flag, error, result = get_sm_employees()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route('/clients')
class Clients(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    def get(self):
        flag, error, result = get_sm_clients()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route('/products')
class Products(Resource):
    @ns.expect(products_request_model)
    @ns.marshal_with(products_answer_model)
    def post(self):
        code, data = parse_data(ns.payload, 5)
        if code == 400:
            return {"data": None, "page": 0, "pages": 0}, code
        data_out, code = get_products_sm(data['limit'], data['page'])
        return data_out, code


@ns.route('/add')
class AddSM(Resource):
    @ns.expect(sm_post_model)
    def post(self):
        code, data = parse_data(ns.payload, 6)
        if code == 400 or code == 204:
            return {"answer": "The data has a bad structure"}, code
        flag, error, result = insert_sm_db(data)
        if flag:
            return {"answer": "ok", "msg": result}, 201
        else:
            print(error)
            return {"answer": f"error at updating db"}, 400

    @ns.expect(delete_request_sm_model)
    def delete(self):
        code, data = parse_data(ns.payload, 7)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        flag, error, result = delete_sm_db(data["id"], data["sm_code"])
        if flag:
            return {"answer": "ok", "msg": error}, 200
        else:
            print(error)
            return {"answer": f"error at updating db"}, 400

    @ns.expect(sm_put_model)
    def put(self):
        code, data = parse_data(ns.payload, 8)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        flag, error, result = update_sm_db(data)
        if flag:
            return {"answer": "ok", "msg": error}, 200
        else:
            return {"answer": f"error at updating db"}, 400
