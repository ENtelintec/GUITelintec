# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/abr./2024  at 9:53 $"

from flask import send_file, request
from flask_restx import Resource, Namespace

from static.Models.api_fichaje_models import (
    fichaje_request_model,
    fichaje_add_update_request_model,
    fichaje_delete_request_model,
    bitacora_dowmload_report_model,
    FichajeRequestFormr,
    FichajeAddUpdateRequestForm,
    FichajeDeleteRequestForm,
    BitacoraDownloadReportForm,
    FichajeRequestMultipleEvents_model,
    FichajeRequestMultipleEvents,
    FichajeRequestExtras_model,
    FichajeRequestExtras,
    FichajeAproveExtras_model,
    FichajeAproveExtras,
)
from static.Models.api_models import expected_headers_per
from static.Models.api_sm_models import client_emp_sm_response_model
from templates.controllers.employees.employees_controller import (
    get_employees_op_names,
    get_contracts_operaciones,
)
from templates.resources.methods.Functions_Aux_Login import verify_token, token_verification_procedure
from templates.resources.midleware.MD_Bitacora import (
    get_events_extra,
    get_events_bitacora,
    create_event_bitacora_from_api,
    update_event_bitacora_from_api,
    delete_event_bitacora_from_api, get_file_report_bitacora, create_multiple_event_bitacora_from_api, aprove_event_bitacora_from_api,
)

ns = Namespace("GUI/api/v1/bitacora")


@ns.route("/employees")
class Employees(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        flag, error, result = get_employees_op_names()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route("/fichaje/table")
class FichajeTable(Resource):
    @ns.expect(expected_headers_per, fichaje_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeRequestFormr.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        response, code = get_events_bitacora(data)
        return response, code


@ns.route("/fichaje/event")
class FichajeEvent(Resource):
    @ns.expect(expected_headers_per, fichaje_add_update_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeAddUpdateRequestForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        response, code = create_event_bitacora_from_api(data)
        return response, code

    @ns.expect(expected_headers_per, fichaje_add_update_request_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeAddUpdateRequestForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        response, code = update_event_bitacora_from_api(data)
        return response, code

    @ns.expect(expected_headers_per, fichaje_delete_request_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeDeleteRequestForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        response, code = delete_event_bitacora_from_api(data)
        return response, code


@ns.route("/dowload/report")
class BitacoraDownloadReport(Resource):
    @ns.expect(expected_headers_per, bitacora_dowmload_report_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = BitacoraDownloadReportForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        filepath, code = get_file_report_bitacora(data)
        # data_out = transform_bitacora_data_to_dict(event_filtered, columns)
        try:
            return send_file(filepath, as_attachment=True)
        except Exception as e:
            return {"data": f"Error en el tipo de quizz: {str(e)}"}, 400


@ns.route("/contract_list")
class BitacoraEmployeesList(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        flag, error, result = get_contracts_operaciones()
        # filtering unique contracts
        contracts = list(set([item[0] for item in result]))
        contracts.sort()
        if flag:
            return {"data": contracts, "comment": error}, 200
        else:
            return {"data": [contracts], "comment": error}, 400


@ns.route("/fichaje/multiple")
class FichajeMultipleEvent(Resource):
    @ns.expect(expected_headers_per, FichajeRequestMultipleEvents_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeRequestMultipleEvents.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        response, code = create_multiple_event_bitacora_from_api(data)
        return response, code


@ns.route("/fichajes/extra")
class FichajesGetExtra(Resource):
    @ns.expect(expected_headers_per, FichajeRequestExtras_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeRequestExtras.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        data, code = get_events_extra(data)
        return {"data": data}, code


@ns.route("/fichajes/extra/aprove")
class FichajesAproveExtra(Resource):
    @ns.expect(expected_headers_per, FichajeAproveExtras_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="bitacoras")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 400
        # noinspection PyUnresolvedReferences
        validator = FichajeAproveExtras.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        response, code = aprove_event_bitacora_from_api(data)
        return response, code
