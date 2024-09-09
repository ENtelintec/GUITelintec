# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:03 $"

from flask_restx import Namespace, Resource

from static.Models.api_contracts_models import (
    answer_quotation_model,
    quotation_model_insert,
    quotation_model_update,
    quotation_model_delete,
    answer_contract_model,
    contract_model_insert,
    contract_model_update,
    contract_model_delete,
    QuotationInsertForm,
    QuotationDeleteForm,
    ContractUpdateForm,
    ContractDeleteForm,
    QuotationUpdateForm,
    ContractInsertForm,
)
from templates.resources.midleware.Functions_midleware_admin import (
    get_quotations,
    get_contracts,
    get_folio_from_contract_ternium,
    folio_from_department,
)
from templates.controllers.contracts.contracts_controller import (
    create_contract,
    update_contract,
)
from templates.controllers.contracts.quotations_controller import (
    create_quotation,
    update_quotation,
    delete_quotation,
)

ns = Namespace("GUI/api/v1/admin/presales")


@ns.route("/quotation/<string:id_q>")
class Quotations(Resource):
    @ns.marshal_with(answer_quotation_model)
    def get(self, id_q):
        data, code = get_quotations(id_q)
        return data, code


@ns.route("/quotation")
class Quotation(Resource):
    @ns.expect(quotation_model_insert)
    def post(self):
        validator = QuotationInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, result = create_quotation(data["metadata"], data["products"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200

    @ns.expect(quotation_model_update)
    def put(self):
        validator = QuotationUpdateForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, result = update_quotation(
            data["id"], data["metadata"], data["products"], data["timestamps"]
        )
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200

    @ns.marshal_with(quotation_model_delete)
    def delete(self):
        validator = QuotationDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, result = delete_quotation(data["id"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200


@ns.route("/contract/<string:id_c>")
class Contracts(Resource):
    @ns.marshal_with(answer_contract_model)
    def get(self, id_c):
        data, code = get_contracts(id_c)
        return data, code


@ns.route("/contract")
class Contract(Resource):
    @ns.expect(contract_model_insert)
    def post(self):
        validator = ContractInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, result = create_contract(data["quotation_id"], data["metadata"])
        if not flag:
            return {"data": None, "msg": str(error)}, 400
        return {"data": result, "msg": "Ok"}, 200

    @ns.expect(contract_model_update)
    def put(self):
        validator = ContractUpdateForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, result = update_contract(
            data["id"], data["metadata"], data["timestamps"]
        )
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200

    @ns.expect(contract_model_delete)
    def delete(self):
        validator = ContractDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, result = delete_quotation(data["id"])
        if not flag:
            return {"data": None, "msg": error}, 400
        return {"data": result, "msg": "Ok"}, 200


@ns.route("/folio/ternium/<string:contract>")
class FolioTernium(Resource):
    def get(self, contract):
        data_out, code = get_folio_from_contract_ternium(contract)
        return data_out, code


@ns.route("/folio/cotfc/<string:key>")
class FolioCotfc(Resource):
    def get(self, key):
        data_out, code = folio_from_department(key)
        return data_out, code
