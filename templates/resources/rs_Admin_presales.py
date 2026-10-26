# -*- coding: utf-8 -*-
import os
import tempfile

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_contracts_models import (
    ContractDeleteForm,
    ContractInsertForm,
    ContractSettingsForm,
    ContractUpdateForm,
    QuotationDeleteForm,
    QuotationInsertForm,
    QuotationOcdForm,
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
    quotation_ocd_model,
)
from static.Models.api_fichajes_models import expected_files
from static.Models.api_models import expected_headers_per
from static.Models.api_quotation_cisco_models import (
    QuotationCiscoInsertForm,
    QuotationCiscoUpdateForm,
    quotation_cisco_model_insert,
    quotation_cisco_model_update,
)
from static.Models.api_quotation_costs_models import (
    QuotationCostAnalysisForm,
    quotation_cost_analysis_model,
)
from static.Models.api_tenders_models import (
    TenderItemsForm,
    TenderPostForm,
    TenderPutForm,
    tender_items_model,
    tender_post_model,
    tender_put_model,
)
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
    suggest_quotation_folio,
    update_contract_from_api,
    update_quoation_from_api,
    update_quotation_ocd_from_api,
)
from templates.resources.midleware.MD_Admin_Collections import fetch_products_contracts
from templates.resources.midleware.MD_QuotationCisco import (
    create_quotation_cisco_api,
    download_quotation_cisco_pdf,
    get_quotations_cisco_api,
    update_quotation_cisco_api,
)
from templates.resources.midleware.MD_QuotationCosts import (
    suggest_cost_analysis_api,
    update_quotation_cost_analysis_from_api,
)
from templates.resources.midleware.MD_Tenders import (
    create_tender_from_api,
    get_tender_from_api,
    get_tenders_from_api,
    update_tender_from_api,
    update_tender_items_from_api,
)

__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:03 $"

ns = Namespace("GUI/api/v1/admin/presales")


@ns.route("/quotation/<string:id_q>")
class Quotations(Resource):
    # @ns.marshal_with(answer_quotation_model)
    @ns.expect(expected_headers_per)
    @ns.doc(params={
        "document_type": "Solo en listado (id -1): quotation | ocd",
        "with_costs": "1 -> agrega cost_analysis por producto y cost_totals (Preventa; nunca va al PDF del cliente)",
        "status": "Solo en listado (id -1): metadata.status, uno o lista (0 o 0,3). 0 preventa, 1/2 catálogo de contrato, 3 licitación",
        "format": "Listado: sin él no salen las CISCO (salvo con document_type=ocd); cisco -> solo CISCO; all -> todas",
    })
    def get(self, id_q):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        with_costs = (request.args.get("with_costs") or "").strip().lower() in ("1", "true", "yes")
        data, code = get_quotations(
            data_token,
            id_q,
            document_type=request.args.get("document_type"),
            with_costs=with_costs,
            status=request.args.get("status"),
            fmt=request.args.get("format"),
        )
        return data, code


@ns.route("/tenders")
class Tenders(Resource):
    @ns.expect(expected_headers_per)
    @ns.doc(params={
        "status": "Uno o lista (1 o 0,1): 0 en espera, 1 asignada, 2 no asignada, 3 cancelada",
        "client_id": "customers_amc.id_customer",
        "date_from": "YYYY-MM-DD sobre closing_date",
        "date_to": "YYYY-MM-DD sobre closing_date",
        "has_contract": "1 con contrato, 0 sin contrato; ausente = no filtra",
    })
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_tenders_from_api(request.args, data_token)
        return data_out, code


@ns.route("/tender/<int:id_tender>")
class TenderById(Resource):
    @ns.expect(expected_headers_per)
    @ns.doc(params={"with_costs": "1 -> cost_analysis por partida (cost_totals viaja siempre)"})
    def get(self, id_tender):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        with_costs = (request.args.get("with_costs") or "").strip().lower() in ("1", "true", "yes")
        data_out, code = get_tender_from_api(id_tender, with_costs, data_token)
        return data_out, code


@ns.route("/tender")
class TenderActions(Resource):
    @ns.expect(expected_headers_per, tender_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TenderPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        # JSON crudo: el midleware necesita null vs ausente y 0 como valor válido.
        data_out, code = create_tender_from_api(ns.payload or {}, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, tender_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TenderPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        # PUT parcial: solo las llaves presentes en el JSON crudo.
        data_out, code = update_tender_from_api(ns.payload or {}, data_token)
        return data_out, code


@ns.route("/tender/items")
class TenderItems(Resource):
    @ns.expect(expected_headers_per, tender_items_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = TenderItemsForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = update_tender_items_from_api(validator.data, data_token)
        return data_out, code


@ns.route("/quotation/costAnalysis")
class QuotationCostAnalysis(Resource):
    @ns.expect(expected_headers_per, quotation_cost_analysis_model)
    def put(self):
        """Análisis de costos por partida (upsert + comparativa de proveedores; apply_prices escribe price_unit)."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = QuotationCostAnalysisForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        # raw_payload -> items[] (cost puede ser null) lo valida el midleware.
        data_out, code = update_quotation_cost_analysis_from_api(data, ns.payload or {}, data_token)
        return data_out, code


@ns.route("/quotation/costAnalysis/suggest")
class QuotationCostAnalysisSuggest(Resource):
    @ns.doc(params={
        "n_part": "Número de parte exacto (genéricos como GENERICO/S/N no se buscan: generic=true)",
        "description": "Texto a buscar en la descripción (mín. 3 caracteres); con n_part genérico es la única llave",
        "exclude_quotation_id": "Cotización que se está analizando (no se sugiere a sí misma)",
        "limit": "Máximo por fuente, default 5, tope 20",
    })
    @ns.expect(expected_headers_per)
    def get(self):
        """Sugerencias para el análisis de costos: análisis previos (con comparativa) e items cotizados antes."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = suggest_cost_analysis_api(request.args, data_token)
        return data_out, code


@ns.route("/quotation/cisco/<string:id_q>")
class QuotationsCisco(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_q):
        """Cotizaciones CISCO (FO-PRE-02): -1 lista todas las de metadata.format = cisco, <id> una; 404 si no existe o no es CISCO."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_quotations_cisco_api(id_q, data_token)
        return data_out, code


@ns.route("/quotation/cisco")
class QuotationCiscoAction(Resource):
    @ns.expect(expected_headers_per, quotation_cisco_model_insert)
    def post(self):
        """Crea una cotización CISCO (mismas tablas, metadata.format = cisco, partidas con item/smart_account/service_months)."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = QuotationCiscoInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = create_quotation_cisco_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, quotation_cisco_model_update)
    def put(self):
        """Actualiza una cotización CISCO: cabecera + upsert de partidas por qa_item_id (is_erased 1 borra)."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = QuotationCiscoUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_quotation_cisco_api(data, data_token)
        return data_out, code


@ns.route("/quotation/cisco/download/pdf/<int:id_q>")
class DownloadPDFQuotationCisco(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_q):
        """PDF FO-PRE-02 R2 de una cotización CISCO (blob en 200; envelope JSON en 404 si no existe o no es CISCO)."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = download_quotation_cisco_pdf(id_q, data_token)
        if code == 200:
            return send_file(data, as_attachment=True)  # pyrefly: ignore
        return data, code


@ns.route("/quotation/folio")
class QuotationFolio(Resource):
    @ns.expect(expected_headers_per)
    @ns.doc(params={
        "document_type": "quotation (default) | ocd",
        "format": "cisco -> prefijo COT-CISCO (solo con document_type quotation)",
    })
    def get(self):
        """Folio sugerido (patrón provisional + max + 1 del año) para pre-llenar una cotización u OCD; el usuario puede editarlo."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = suggest_quotation_folio(request.args, data_token)
        return data_out, code


@ns.route("/quotation/ocd")
class QuotationOcd(Resource):
    @ns.expect(expected_headers_per, quotation_ocd_model)
    def put(self):
        """Marca una cotización como OCD (orden de compra directa) o ajusta sus datos OCD; no toca items."""
        flag, data_token, msg = token_verification_procedure(request, department="administracion")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = QuotationOcdForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_quotation_ocd_from_api(data, data_token)
        return data_out, code


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
