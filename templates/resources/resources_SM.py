# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/abr./2024  at 10:26 $'

from flask_restx import Resource, Namespace
from static.Models.api_models import client_emp_sm_response_model, products_answer_model, products_request_model, \
    sm_post_model, delete_request_sm_model, sm_put_model, table_sm_model, table_request_model, new_cliente_model, \
    new_product_model
from templates.Functions_DB_midleware import get_products_sm, get_all_sm
from templates.Functions_Text import parse_data
from templates.controllers.customer.customers_controller import get_sm_clients
from templates.controllers.employees.employees_controller import get_sm_employees
from templates.controllers.index import DataHandler
from templates.controllers.material_request.sm_controller import insert_sm_db, delete_sm_db, update_sm_db

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


@ns.route('/all')
class AllSm(Resource):
    @ns.expect(table_request_model)
    @ns.marshal_with(table_sm_model)
    def post(self):
        code, data = parse_data(ns.payload, 5)
        if code == 400:
            return {"data": None, "page": 0, "pages": 0}, code
        data, code = get_all_sm(data['limit'], data['page'])
        return data, code


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
            return {"answer": "error at updating db"}, 400

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
            return {"answer": "error at updating db"}, 400

    @ns.expect(sm_put_model)
    def put(self):
        code, data = parse_data(ns.payload, 8)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        flag, error, result = update_sm_db(data)
        if flag:
            return {"answer": "ok", "msg": error}, 200
        else:
            return {"answer": "error at updating db"}, 400


@ns.route('/newclient')
class Client(Resource):
    @ns.expect(new_cliente_model)
    def post(self):
        code, data = parse_data(ns.payload, 12)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        _data = DataHandler()
        result = _data.create_customer(data['name'], data['email'], data['phone'], data['rfc'], data["address"])
        if isinstance(result, str):
            return {"answer": "Error", "msg": result}, 400
        else:
            return {"answer": "ok", "msg": result}, 201


@ns.route('/newproduct')
class Product(Resource):
    @ns.expect(new_product_model)
    def post(self):
        code, data = parse_data(ns.payload, 13)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        print(data)
        _data = DataHandler()
        result = _data.create_product(data['sku'], data['name'], data['udm'], data['stock'], data['category'], data['supplier'])
        if isinstance(result, str):
            return {"answer": "Error", "msg": result}, 400
        else:
            return {"answer": "ok", "msg": result}, 201
