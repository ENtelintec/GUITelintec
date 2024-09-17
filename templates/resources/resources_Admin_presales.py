# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:03 $"

import os
import tempfile

from flask import request
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

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
    expected_files_quotation,
    expected_files_contract,
    contract_settings_model,
    ContractSettingsForm,
    expected_files_contract_comparison,
)
from templates.resources.midleware.Functions_midleware_admin import (
    get_quotations,
    get_contracts,
    get_folio_from_contract_ternium,
    folio_from_department,
    products_quotation_from_file,
    products_contract_from_file,
    modify_pattern_phrase_contract_pdf,
    compare_file_and_quotation,
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


@ns.route("/quotation/products/upload")
class QuotationProductsUpload(Resource):
    @ns.expect(expected_files_quotation)
    def post(self):
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data, code = products_quotation_from_file(filepath_download)
            if code != 200:
                return {"data": data, "msg": "Error at file structure"}, 400
            return {"data": data, "msg": f"Ok with filaname: {filename}"}, 200
        else:
            return {"msg": "No se subio el archivo"}, 400


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


@ns.route("/contract/review/products/upload")
class ContractProductsUpload(Resource):
    @ns.expect(expected_files_contract)
    def post(self):
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data = {"path": filepath_download}
            data, code = products_contract_from_file(data)
            code = 200
            if code != 200:
                return {"data": data, "msg": "Error at file structure"}, 400
            return {"data": data, "msg": f"Ok with filaname: {filename}"}, 200
        else:
            return {"msg": "No se subio el archivo"}, 400


@ns.route("/contract/settings")
class ContractSettings(Resource):
    @ns.expect(contract_settings_model)
    def post(self):
        validator = ContractSettingsForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error = modify_pattern_phrase_contract_pdf(data)
        if not flag:
            return {"data": None, "msg": str(error)}, 400
        return {"msg": "Ok"}, 200


@ns.route("/compare")
class CompareContractQuotation(Resource):
    @ns.expect(expected_files_contract_comparison)
    def post(self):
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        #  get argument id_quotation
        data = {}
        id_quotation = request.form.get("id_quotation")
        try:
            data["id_quotation"] = int(id_quotation) if id_quotation else None
        except ValueError:
            return {"data": None, "msg": "Error at structure of id_quotation"}, 400
        if data["id_quotation"] is None:
            return {
                "data": None,
                "msg": "Error at structure of id_quotation None value",
            }, 400
        if file:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data["path"] = filepath_download
            data, code = compare_file_and_quotation(data)
            if code != 200:
                return {"data": data, "msg": "Error at file structure"}, 400
            return {"data": data, "msg": f"Ok with filaname: {filename}"}, 200
        else:
            return {"msg": "No se subio el archivo"}, 400


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
