# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/abr./2024  at 10:26 $"

from flask import send_file, request
from flask_restx import Resource, Namespace

from static.Models.api_models import expected_headers_per
from static.Models.api_sm_models import (
    client_emp_sm_response_model,
    sm_post_model,
    delete_request_sm_model,
    sm_put_model,
    table_sm_model,
    new_cliente_model,
    new_product_model,
    request_sm_plot_data_model,
    employees_answer_model,
    request_sm_dispatch_model,
    SMPostForm,
    SMPutForm,
    SMDeleteForm,
    NewClienteForm,
    RequestSMDispatchForm,
    NewProductForm,
    control_table_sm_put_model,
    SMInfoControlTablePutForm,
    item_sm_put_model,
    ItemSmPutForm,
)
from static.constants import log_file_sm_path
from templates.Functions_AuxPlots import get_data_sm_per_range
from templates.Functions_Utils import create_notification_permission
from templates.controllers.customer.customers_controller import get_sm_clients
from templates.controllers.employees.employees_controller import get_sm_employees
from templates.controllers.index import DataHandler
from templates.controllers.material_request.sm_controller import (
    delete_sm_db,
)
from templates.misc.Functions_Files import write_log_file
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.MD_SM import (
    get_products_sm,
    get_all_sm,
    dispatch_sm,
    get_employees_almacen,
    cancel_sm,
    dowload_file_sm,
    create_customer,
    create_product,
    update_sm_from_control_table,
    get_all_sm_control_table,
    fetch_all_sm_with_permissions,
    create_sm_from_api,
    update_sm_from_api,
    update_items_sm_from_api,
    get_sm_folios_from_api,
)

ns = Namespace("GUI/api/v1/sm")


@ns.route("/employees")
class Employees(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, error, result = get_sm_employees()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route("/clients")
class Clients(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, error, result = get_sm_clients()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route("/products/<string:contract>")
class Products(Resource):
    @ns.expect(expected_headers_per)
    def get(self, contract):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_products_sm(contract)
        return data_out, code


@ns.route("/all")
class AllSm(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sm", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_all_sm(-1, 0, -1)
        return data_out, code


@ns.route("/permission")
class AllSmPerPermission(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sm", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = fetch_all_sm_with_permissions(data_token)
        return data_out, code


@ns.route("/employee")
class AllSmEmployee(Resource):
    @ns.expect(expected_headers_per)
    @ns.marshal_with(table_sm_model)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_all_sm(-1, 0, data_token.get("emp_id"))
        return data_out, code


@ns.route("/add")
class AddUpdateSM(Resource):
    @ns.expect(expected_headers_per, sm_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMPostForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        data_out, code = create_sm_from_api(data, data_token)
        return data, code

    @ns.expect(expected_headers_per, delete_request_sm_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        flag, error, result = delete_sm_db(data["id"])
        if flag:
            msg = f"SM #{data['id']} eliminada, empleado con id: {data_token.get('emp_id')}"
            create_notification_permission(
                msg,
                ["sm", "administracion", "almacen"],
                "SM Eliminada",
                sender_id=data.get("id_emp"),
            )
            write_log_file(log_file_sm_path, msg)
            return {"answer": "ok", "msg": error}, 200
        else:
            print(error)
            return {"answer": "error at updating db"}, 400

    @ns.expect(expected_headers_per, sm_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMPutForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        data_out, code = update_sm_from_api(data, data_token)
        return data, code


@ns.route("/newclient")
class Client(Resource):
    @ns.expect(expected_headers_per, new_cliente_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = NewClienteForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        _data = DataHandler()
        result, code = create_customer(
            data["name"], data["email"], data["phone"], data["rfc"], data["address"]
        )
        return result, code


@ns.route("/newproduct")
class Product(Resource):
    @ns.expect(expected_headers_per, new_product_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = NewProductForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        response, code = create_product(
            data["sku"],
            data["name"],
            data["udm"],
            data["stock"],
            data["category"],
            data["supplier"],
        )
        return response, code


@ns.route("/plot/<string:typerange>")
class PlotSMData(Resource):
    @ns.marshal_with(request_sm_plot_data_model)
    @ns.expect(expected_headers_per)
    def get(self, typerange):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out = get_data_sm_per_range(typerange, "normal")
        return {"data": data_out, "type": "normal plot lines"}, 200


@ns.route("/almacen/employees")
class AlmacenEmployees(Resource):
    @ns.marshal_with(employees_answer_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_employees_almacen()
        if code == 200:
            return {"data": data_out, "msg": "ok"}, code
        else:
            return {"data": [], "msg": "error"}, code


@ns.route("/manage/dispatch")
class DispatchSM(Resource):
    @ns.expect(expected_headers_per, request_sm_dispatch_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = RequestSMDispatchForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        code, data_out = dispatch_sm(data, data_token)
        if code == 200:
            return {"msg": "ok", "data": data_out}, code
        else:
            return {"msg": "error at dispaching", "data": data_out}, code

    @ns.expect(expected_headers_per, request_sm_dispatch_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = RequestSMDispatchForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        code, data_out = cancel_sm(data)
        if code == 200:
            return {"msg": "SM cancel"}, code
        else:
            return {"msg": "error at canceling", "data": data_out}, code


@ns.route("/download/pdf/<int:sm_id>")
class DownloadPDFSM(Resource):
    @ns.expect(expected_headers_per)
    def get(self, sm_id):
        flag, data_token, msg = token_verification_procedure(request, department=["sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = dowload_file_sm(sm_id)
        if code == 200:
            return send_file(data, as_attachment=True)
        else:
            return {"msg": "error at downloading"}, code


@ns.route("/download/excel/<int:sm_id>")
class DownloadExcelSM(Resource):
    @ns.expect(expected_headers_per)
    def get(self, sm_id):
        flag, data_token, msg = token_verification_procedure(request, department=["sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = dowload_file_sm(sm_id, type_file="excel")
        if code == 200:
            return send_file(data, as_attachment=True)
        else:
            return {"msg": "error at downloading"}, code


@ns.route("/control/table")
class ControlTableSM(Resource):
    @ns.expect(expected_headers_per, control_table_sm_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = SMInfoControlTablePutForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        code, data_out = update_sm_from_control_table(data, data_token)
        return data_out, code


@ns.route("/control/table/all")
class AllControlTableSm(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_all_sm_control_table(data_token)
        return data_out, code


@ns.route("/item")
class SmItemsActions(Resource):
    @ns.expect(expected_headers_per, item_sm_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sm", "administracion", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ItemSmPutForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        data_out, code = update_items_sm_from_api(data, data_token)
        return data_out, code


@ns.route("/folioSmAll")
class FetchSMFolios(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sm", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_sm_folios_from_api(data_token)
        return data_out, code
