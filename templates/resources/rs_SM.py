# -*- coding: utf-8 -*-

import os
import tempfile

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_models import expected_headers_per
from static.Models.api_sm_models import (
    expected_files_attachment_sm,
    ItemApproveSMForm,
    ItemsBulkSmPutForm,
    ItemSMInventoryPutForm,
    ItemSmPutForm,
    ItemStateSMForm,
    NewClienteForm,
    NewProductForm,
    RequestSMDispatchForm,
    SMDeleteForm,
    SMInfoControlTablePutForm,
    SMPostForm,
    SMPutForm,
    SMUrgentPostForm,
    control_table_sm_put_model,
    delete_request_sm_model,
    item_approve_model,
    item_sm_inventory_put_model,
    item_sm_put_model,
    item_state_model,
    items_bulk_put_model,
    new_cliente_model,
    new_product_model,
    request_sm_dispatch_model,
    sm_post_model,
    sm_put_model,
    sm_urgent_post_model,
)
from templates.controllers.customer.customers_controller import get_sm_clients
from templates.controllers.employees.employees_controller import get_sm_employees
from templates.Functions_AuxPlots import get_data_sm_per_range
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.MD_SM import (
    cancel_sm,
    create_customer,
    create_product,
    create_sm_attachment_api,
    create_sm_from_api,
    create_urgent_sm_from_api,
    delete_sm_from_api,
    dispatch_sm,
    dowload_file_sm,
    fetch_all_sm_with_permissions,
    get_all_sm,
    get_all_sm_control_table,
    get_employees_almacen,
    get_products_sm,
    get_sm_folios_from_api,
    get_sm_items_from_api,
    update_items_bulk_sm_from_api,
    update_items_sm_from_api,
    update_sm_from_api,
    update_sm_from_control_table,
    update_sm_item_approve,
    update_sm_item_state,
    update_sm_item_state_and_inventory,
)

__author__ = "Edisson Naula"
__date__ = "$ 01/abr./2024  at 10:26 $"

ns = Namespace("GUI/api/v1/sm")


@ns.route("/employees")
class Employees(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, error, result = get_sm_employees()
        if flag:
            return {"data": result, "msg": None, "error": None}, 200
        else:
            return {
                "data": [],
                "msg": "No se pudieron obtener los empleados",
                "error": error,
            }, 400


@ns.route("/clients")
class Clients(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, error, result = get_sm_clients(data_token)
        if flag:
            return {"data": result, "msg": None, "error": None}, 200
        else:
            return {
                "data": [],
                "msg": "No se pudieron obtener los clientes",
                "error": error,
            }, 400


@ns.route("/products/<string:contract>")
class Products(Resource):
    @ns.expect(expected_headers_per)
    def get(self, contract):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_products_sm(contract, data_token)
        return data_out, code


@ns.route("/all")
class FetchAllSm(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["sm", "almacen"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_all_sm(-1, data_token, 0, -1)
        return data_out, code


@ns.route("/permission")
class AllSmPerPermission(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["sm", "almacen"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = fetch_all_sm_with_permissions(data_token)
        return data_out, code


@ns.route("/employee")
class AllSmEmployee(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_all_sm(-1, data_token, 0, data_token.get("emp_id"))
        return data_out, code


@ns.route("/add")
class ActionsSM(Resource):
    @ns.expect(expected_headers_per, sm_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = create_sm_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, delete_request_sm_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = delete_sm_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, sm_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = update_sm_from_api(data, data_token)
        return data_out, code


@ns.route("/add/urgent")
class ActionsUrgentSM(Resource):
    @ns.expect(expected_headers_per, sm_urgent_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMUrgentPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = create_urgent_sm_from_api(data, data_token)
        return data_out, code


@ns.route("/cancel")
class CancelSM(Resource):
    @ns.expect(expected_headers_per, delete_request_sm_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SMDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = cancel_sm(data, data_token)
        return data_out, code


@ns.route("/newclient")
class Client(Resource):
    @ns.expect(expected_headers_per, new_cliente_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = NewClienteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        result, code = create_customer(
            data["name"], data["email"], data["phone"], data["rfc"], data["address"], data_token
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
        validator = NewProductForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        response, code = create_product(
            data["sku"],
            data["name"],
            data["udm"],
            data["stock"],
            data["category"],
            data["supplier"],
            data_token,
        )
        return response, code


@ns.route("/plot/<string:typerange>")
class PlotSMData(Resource):
    @ns.expect(expected_headers_per)
    def get(self, typerange):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out = get_data_sm_per_range(typerange, "normal", data_token)
        return {"data": data_out, "type": "normal plot lines", "error": None}, 200


@ns.route("/almacen/employees")
class AlmacenEmployees(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_employees_almacen(data_token)
        if code == 200:
            return {"data": data_out, "msg": "Empleados de almacén obtenidos", "error": None}, code
        else:
            return {
                "data": [],
                "msg": "No se pudieron obtener los empleados de almacén",
                "error": "error",
            }, code


@ns.route("/manage/dispatch")
class DispatchSM(Resource):
    @ns.expect(expected_headers_per, request_sm_dispatch_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department=["almacen"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = RequestSMDispatchForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        code, data_out = dispatch_sm(data, data_token)
        if code == 200:
            return {"msg": "SM despachada correctamente", "data": data_out, "error": None}, code
        else:
            return {
                "data": None,
                "msg": data_out.get("msg", "No se pudo despachar la SM")
                if isinstance(data_out, dict)
                else "No se pudo despachar la SM",
                "error": data_out.get("error", data_out)
                if isinstance(data_out, dict)
                else data_out,
            }, code


@ns.route("/download/pdf/<int:sm_id>")
class DownloadPDFSM(Resource):
    @ns.expect(expected_headers_per)
    def get(self, sm_id):
        flag, data_token, msg = token_verification_procedure(request, department=["sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = dowload_file_sm(sm_id, data_token)
        if code == 200:
            # con code 200 data siempre es la ruta (str) del archivo generado
            return send_file(
                data,  # pyrefly: ignore
                as_attachment=True,
                download_name=data.replace("\\", "/").split("/")[-1],  # pyrefly: ignore
            )
        else:
            return data, code


@ns.route("/download/excel/<int:sm_id>")
class DownloadExcelSM(Resource):
    @ns.expect(expected_headers_per)
    def get(self, sm_id):
        flag, data_token, msg = token_verification_procedure(request, department=["sm"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = dowload_file_sm(sm_id, data_token, type_file="excel")
        if code == 200:
            # con code 200 data siempre es la ruta (str) del archivo generado
            return send_file(
                data,  # pyrefly: ignore
                as_attachment=True,
                download_name=data.replace("\\", "/").split("/")[-1],  # pyrefly: ignore
            )
        else:
            return data, code


@ns.route("/control/table")
class ControlTableSM(Resource):
    @ns.expect(expected_headers_per, control_table_sm_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = SMInfoControlTablePutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
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
        validator = ItemSmPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = update_items_sm_from_api(data, data_token)
        return data_out, code


@ns.route("/folioSmAll")
class FetchSMFolios(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=["sm", "almacen"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_sm_folios_from_api(data_token)
        return data_out, code


@ns.route("/items/state-<int:state>")
class FetchSMItemsByState(Resource):
    @ns.expect(expected_headers_per)
    def get(self, state):
        flag, data_token, msg = token_verification_procedure(request, department=["sm", "almacen"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_sm_items_from_api({"state": state}, data_token)
        return data_out, code


@ns.route("/item/inventory")
class UpdateItemInventoryID(Resource):
    @ns.expect(expected_headers_per, item_sm_inventory_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="sm")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ItemSMInventoryPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data["state"] = 1
        data_out, code = update_sm_item_state_and_inventory(data, data_token)
        return data_out, code


@ns.route("/item/stateUpdate")
class UpdateItemSMState(Resource):
    @ns.expect(expected_headers_per, item_state_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department=["sm", "almacen"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ItemStateSMForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = update_sm_item_state(data, data_token)
        return data_out, code


@ns.route("/items/bulk")
class SmItemsBulkActions(Resource):
    @ns.expect(expected_headers_per, items_bulk_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["sm", "administracion", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ItemsBulkSmPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = update_items_bulk_sm_from_api(data, data_token)
        return data_out, code


@ns.route("/item/approveRequired")
class UpdateItemSMApprove(Resource):
    @ns.expect(expected_headers_per, item_approve_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department=["sm", "almacen"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ItemApproveSMForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = update_sm_item_approve(data, data_token)
        return data_out, code


@ns.route("/attachment-<string:id_sm>")
class UploadSMAttachment(Resource):
    @ns.expect(expected_headers_per, expected_files_attachment_sm)
    def post(self, id_sm):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "operaciones"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": "no file"}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data_out, code = create_sm_attachment_api(
                {
                    "filepath": filepath_download,
                    "filename": filename,
                    "id_sm": id_sm,
                    "title": request.form.get("title", ""),
                },
                data_token,
            )
            if code != 201:
                return {
                    "data": None,
                    "msg": data_out.get("msg", "Error en la estructura del archivo")
                    if isinstance(data_out, dict)
                    else "Error en la estructura del archivo",
                    "error": data_out.get("error", data_out)
                    if isinstance(data_out, dict)
                    else data_out,
                }, 400
            return {
                "data": data_out.get("data") if isinstance(data_out, dict) else data_out,
                "msg": data_out.get("msg", f"Archivo adjuntado: {filename}")
                if isinstance(data_out, dict)
                else f"Archivo adjuntado: {filename}",
                "error": None,
            }, 201
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": "no file"}, 400
