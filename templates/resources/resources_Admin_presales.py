# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 20/jun./2024  at 15:03 $'

from flask_restx import Namespace, Resource

from static.Models.api_contracts_models import answer_quotation_model, quotation_model_insert, \
    quotation_model_update, quotation_model_delete, answer_contract_model, contract_model_insert, contract_model_update, \
    contract_model_delete
from templates.Functions_midleware_admin import get_quotations, get_contracts
from templates.controllers.contracts.contracts_controller import create_contract, update_contract
from templates.controllers.contracts.quotations_controller import create_quotation, update_quotation, delete_quotation
from templates.resources.Functions_Aux_Admin import parse_data

ns = Namespace('GUI/api/v1/admin/presales')


@ns.route('/quotation/<string:id_q>')
class Quotations(Resource):
    @ns.marshal_with(answer_quotation_model)
    def get(self, id_q):
        data, code = get_quotations(id_q)
        return data, code


@ns.route('/quotation')
class Quotation(Resource):
    @ns.expect(quotation_model_insert)
    def post(self):
        code, data = parse_data(ns.payload, 1)
        if code != 200:
            return {"data": data, "msg": "Error at structure"}, 400
        flag, error, result = create_quotation(data["metadata"], data["products"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200
    
    @ns.expect(quotation_model_update)
    def put(self):
        code, data = parse_data(ns.payload, 1)
        if code != 200:
            return {"data": data, "msg": "Error at structure"}, 400
        flag, error, result = update_quotation(data["id"], data["metadata"], data["products"], data["timestamps"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200
    
    @ns.marshal_with(quotation_model_delete)
    def delete(self):
        code, data = parse_data(ns.payload, 1)
        if code != 200:
            return {"data": data, "msg": "Error at structure"}, 400
        flag, error, result = delete_quotation(data["id"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200


@ns.route('/contract/<string:id_c>')
class Contract(Resource):
    @ns.marshal_with(answer_contract_model)
    def get(self, id_c):
        data, code = get_contracts(id_c)
        return data, code
    

@ns.route('/contract')
class Contracts(Resource):
    @ns.expect(contract_model_insert)
    def post(self):
        code, data = parse_data(ns.payload, 2)
        if code != 200:
            return {"data": data, "msg": "Error at structure"}, 400
        flag, error, result = create_contract(data["quotation_id"], data["metadata"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200
    
    @ns.expect(contract_model_update)
    def put(self):
        code, data = parse_data(ns.payload, 2)
        if code != 200:
            return {"data": data, "msg": "Error at structure"}, 400
        flag, error, result = update_contract(data["id"], data["metadata"], data["timestamps"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200
    
    @ns.marshal_with(contract_model_delete)
    def delete(self):
        code, data = parse_data(ns.payload, 2)
        if code != 200:
            return {"data": data, "msg": "Error at structure"}, 400
        flag, error, result = delete_quotation(data["id"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200
