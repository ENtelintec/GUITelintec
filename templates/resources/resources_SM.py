# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/abr./2024  at 10:26 $"

from flask import send_file
from flask_restx import Resource, Namespace
from static.Models.api_sm_models import (
    client_emp_sm_response_model,
    products_answer_model,
    products_request_model,
    sm_post_model,
    delete_request_sm_model,
    sm_put_model,
    table_sm_model,
    table_request_model,
    new_cliente_model,
    new_product_model,
    request_sm_plot_data_model,
    employees_answer_model,
    request_sm_dispatch_model,
    response_sm_dispatch_model,
    ProductRequestForm,
    TableRequestForm,
    SMPostForm,
    SMPutForm,
    SMDeleteForm,
)
from static.extensions import log_file_sm_path
from templates.Functions_AuxPlots import get_data_sm_per_range
from templates.misc.Functions_Files import write_log_file
from templates.Functions_Utils import create_notification_permission
from templates.resources.midleware.Functions_DB_midleware import (
    get_products_sm,
    get_all_sm,
    get_employees_almacen,
    dispatch_sm,
    cancel_sm,
    dowload_file_sm,
)
from templates.Functions_Text import parse_data
from templates.controllers.customer.customers_controller import get_sm_clients
from templates.controllers.employees.employees_controller import get_sm_employees
from templates.controllers.index import DataHandler
from templates.controllers.material_request.sm_controller import (
    insert_sm_db,
    delete_sm_db,
    update_sm_db,
)

ns = Namespace("GUI/api/v1/sm")


@ns.route("/employees")
class Employees(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    def get(self):
        flag, error, result = get_sm_employees()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route("/clients")
class Clients(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    def get(self):
        flag, error, result = get_sm_clients()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route("/products")
class Products(Resource):
    @ns.expect(products_request_model)
    @ns.marshal_with(products_answer_model)
    def post(self):
        print(ns.payload)
        validator = ProductRequestForm.from_json(ns.payload)
        if not validator.validate():
            print(validator.errors)
            return {"error": validator.errors}, 400
        data = validator.data
        data_out, code = get_products_sm(data["limit"], data["page"])
        return data_out, code


@ns.route("/all")
class AllSm(Resource):
    @ns.expect(table_request_model)
    @ns.marshal_with(table_sm_model)
    def post(self):
        validator = TableRequestForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        data_out, code = get_all_sm(data["limit"], data["page"], data["emp_id"])
        return data_out, code


@ns.route("/add")
class AddSM(Resource):
    @ns.expect(sm_post_model)
    def post(self):
        validator = SMPostForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 6)
        # if code == 400 or code == 204:
        #     return {"answer": "The data has a bad structure"}, code
        flag, error, result = insert_sm_db(data)
        if not flag:
            print(error)
            return {"answer": "error at updating db"}, 400
        msg = (
            f"Nueva SM creada #{data['info']['id']}, folio: {data['info']['folio']}, "
            f"fecha limite: {data['info']['critical_date']}, "
            f"empleado con id: {data['info']['emp_id']}, "
            f"comentario: {data['info']['comment']}"
        )
        create_notification_permission(
            msg,
            ["sm", "administracion", "almacen"],
            "Nueva SM Recibida",
            data["info"]["emp_id"],
            0,
        )
        write_log_file(log_file_sm_path, msg)
        return {"answer": "ok", "msg": result}, 201

    @ns.expect(delete_request_sm_model)
    def delete(self):
        validator = SMDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 7)
        # if code == 400:
        #     return {"answer": "The data has a bad structure"}, code
        flag, error, result = delete_sm_db(data["id"])
        if flag:
            msg = f"SM #{data['id']} eliminada, " f"empleado con id: {data['id_emp']}"
            create_notification_permission(
                msg,
                ["sm", "administracion", "almacen"],
                "SM Eliminada",
                sender_id=data["id_emp"],
            )
            write_log_file(log_file_sm_path, msg)
            return {"answer": "ok", "msg": error}, 200
        else:
            print(error)
            return {"answer": "error at updating db"}, 400

    @ns.expect(sm_put_model)
    def put(self):
        validator = SMPutForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 8)
        # if code == 400:
        #     return {"answer": "The data has a bad structure"}, code
        flag, error, result = update_sm_db(data)
        if flag:
            msg = (
                f"Nueva SM creada #{data['info']['id']}, folio: {data['info']['folio']}, "
                f"fecha limite: {data['info']['critical_date']}, "
                f"empleado con id: {data['info']['emp_id']}, "
                f"comentario: {data['info']['comment']}"
            )
            create_notification_permission(
                msg,
                ["sm", "administracion", "almacen"],
                "Nueva SM Recibida",
                data["info"]["emp_id"],
                0,
            )
            write_log_file(log_file_sm_path, msg)
            return {"answer": "ok", "msg": error}, 200
        else:
            return {"answer": "error at updating db"}, 400


@ns.route("/newclient")
class Client(Resource):
    @ns.expect(new_cliente_model)
    def post(self):
        code, data = parse_data(ns.payload, 12)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        _data = DataHandler()
        result = _data.create_customer(
            data["name"], data["email"], data["phone"], data["rfc"], data["address"]
        )
        if isinstance(result, str):
            return {"answer": "Error", "msg": result}, 400
        else:
            return {"answer": "ok", "msg": result}, 201


@ns.route("/newproduct")
class Product(Resource):
    @ns.expect(new_product_model)
    def post(self):
        code, data = parse_data(ns.payload, 13)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        print(data)
        _data = DataHandler()
        print(data)
        result = _data.create_product(
            data["sku"],
            data["name"],
            data["udm"],
            data["stock"],
            data["category"],
            data["supplier"],
        )
        print(result)
        if isinstance(result, str):
            return {"answer": "Error", "msg": result}, 400
        else:
            return {"answer": "ok", "msg": result}, 201


@ns.route("/plot/<string:typerange>")
class PlotSMData(Resource):
    @ns.marshal_with(request_sm_plot_data_model)
    def get(self, typerange):
        data_out = get_data_sm_per_range(typerange, "normal")
        return {"data": data_out, "type": "normal plot lines"}, 200


@ns.route("/almacen/employees")
class AlmacenEmployees(Resource):
    @ns.marshal_with(employees_answer_model)
    def get(self):
        data_out, code = get_employees_almacen()
        if code == 200:
            return {"data": data_out, "msg": "ok"}, code
        else:
            return {"data": [], "msg": "error"}, code


@ns.route("/manage/dispatch")
class ManageSMDispatch(Resource):
    @ns.marshal_with(response_sm_dispatch_model)
    @ns.expect(request_sm_dispatch_model)
    def post(self):
        code, data = parse_data(ns.payload, 15)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        code, data_out = dispatch_sm(data)
        if code == 200:
            return {"msg": "ok", "data": data_out}, code
        else:
            return {"msg": "error at dispaching", "data": data_out}, code

    @ns.expect(request_sm_dispatch_model)
    def delete(self):
        code, data = parse_data(ns.payload, 15)
        if code == 400:
            return {"answer": "The data has a bad structure"}, code
        code, data_out = cancel_sm(data)
        if code == 200:
            return {"msg": "SM cancel"}, code
        else:
            return {"msg": "error at canceling", "data": data_out}, code


@ns.route("/download/pdf/<int:sm_id>")
class DownloadPDFSM(Resource):
    def get(self, sm_id):
        data, code = dowload_file_sm(sm_id)
        print(data, code)
        if code == 200:
            return send_file(data, as_attachment=True)
        else:
            return {"msg": "error at downloading"}, code
