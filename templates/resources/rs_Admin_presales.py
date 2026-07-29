# -*- coding: utf-8 -*-
import os
import tempfile

from flask import request
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_contracts_models import (
    ContractDeleteForm,
    ContractInsertForm,
    ContractSettingsForm,
    ContractUpdateForm,
    QuotationDeleteForm,
    QuotationInsertForm,
    QuotationUpdateForm,
    contract_model_delete,
    contract_model_insert,
    contract_model_update,
    contract_settings_model,
    expected_files_contract,
    expected_files_contract_comparison,
    expected_files_quotation,
    quotation_model_insert,
    quotation_model_update,
)
from static.Models.api_fichajes_models import expected_files
from static.Models.api_models import expected_headers_per
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_midleware_admin import (
    compare_file_and_quotation,
    create_contract_from_api,
    create_quotation_from_api,
    delete_contract_from_api,
    delete_quotation_from_api,
    folio_from_department,
    get_contracts,
    get_contracts_abreviations,
    get_contractsWithItems,
    get_folio_from_contract_ternium,
    get_quotations,
    items_contract_from_file,
    items_quotation_from_file,
    modify_pattern_phrase_contract_pdf,
    products_contract_from_file,
    products_quotation_from_file,
    update_contract_from_api,
    update_quoation_from_api,
)
from templates.resources.midleware.MD_Admin_Collections import fetch_products_contracts

__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:03 $"

ns = Namespace("GUI/api/v1/admin/presales")


@ns.route("/quotation/<string:id_q>")
class Quotations(Resource):
    # @ns.marshal_with(answer_quotation_model)
    @ns.expect(expected_headers_per)
    def get(self, id_q):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_quotations(data_token, id_q)
        return data, code


@ns.route("/quotation")
class QuotationAction(Resource):
    @ns.expect(expected_headers_per, quotation_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = QuotationInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_quotation_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, quotation_model_update)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = QuotationUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_quoation_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = QuotationDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_quotation_from_api(data, data_token)
        return data_out, code


@ns.route("/quotation/products/upload")
class QuotationProductsUpload(Resource):
    @ns.expect(expected_headers_per, expected_files_quotation)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": "No file in request"}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = products_quotation_from_file(filepath_download)
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400


@ns.route("/contract/<string:id_c>")
class Contracts(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_c):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_contracts(id_c, data_token)
        return data, code


@ns.route("/contracts/products")
class ContractsWProducts(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_contractsWithItems(data_token)
        return data, code


@ns.route("/contract")
class ContractAction(Resource):
    @ns.expect(expected_headers_per, contract_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ContractInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_contract_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, contract_model_update)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ContractUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_contract_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, contract_model_delete)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ContractDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_contract_from_api(data, data_token)
        return data_out, code


@ns.route("/contract/review/products/upload")
class ContractProductsUpload(Resource):
    @ns.expect(expected_headers_per, expected_files_contract)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": "No file in request"}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = products_contract_from_file({"path": filepath_download})
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400


@ns.route("/contract/settings")
class ContractSettings(Resource):
    @ns.expect(expected_headers_per, contract_settings_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ContractSettingsForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        flag, error = modify_pattern_phrase_contract_pdf(data)
        if not flag:
            return {"data": None, "msg": "No se pudo actualizar la configuración", "error": error}, 400
        return {"data": None, "msg": "Configuración actualizada correctamente", "error": None}, 200


@ns.route("/compare")
class CompareContractQuotation(Resource):
    @ns.expect(expected_headers_per, expected_files_contract_comparison)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": "No file in request"}, 400
        file = request.files["file"]
        data: dict[str, int | str | None] = {}
        id_quotation = request.form.get("id_quotation")
        try:
            data["id_quotation"] = int(id_quotation) if id_quotation else None
        except ValueError:
            return {"data": None, "msg": "id_quotation no es un número válido", "error": None}, 400
        if data["id_quotation"] is None:
            return {"data": None, "msg": "id_quotation es requerido", "error": None}, 400
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data["path"] = filepath_download
            data_out, code = compare_file_and_quotation(data, data_token)
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400


@ns.route("/folio/ternium")
class FolioTernium(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["administracion", "almacen", "sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_folio_from_contract_ternium(data_token)
        return data_out, code


@ns.route("/folio/cotfc")
class FolioCotfc(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["administracion", "almacen", "sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = folio_from_department(data_token)
        return data_out, code


@ns.route("/quotation/items/file")
class ItemsQuotationFileUpload(Resource):
    @ns.expect(expected_headers_per, expected_files)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": "No file in request"}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = items_quotation_from_file({"path": filepath_download})
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400


@ns.route("/contract/items/file")
class ItemsContractFileUpload(Resource):
    @ns.expect(expected_headers_per, expected_files)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": "No file in request"}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = items_contract_from_file({"path": filepath_download}, data_token)
            return data_out, code
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400


@ns.route("/contracts/abreviations")
class ContractsAbreviations(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["administracion", "rrhh", "operaciones", "sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_contracts_abreviations(data_token)
        return data_out, code


@ns.route("/products/contracts")
class ProductsContracts(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["administracion", "remission", "operaciones", "sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = fetch_products_contracts(data_token)
        return data, code
