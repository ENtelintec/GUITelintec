# -*- coding: utf-8 -*-
import os
import tempfile

from flask import request
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_clients_suppliers_models import (
    ClientDeleteForm,
    ClientInsertForm,
    ClientUpdateForm,
    SupplierDeleteForm,
    SupplierEInfoUpdateForm,
    SupplierInsertForm,
    SupplierUpdateForm,
    client_model,
    supplier_delete_model,
    supplier_model,
    update_extra_info_model,
)
from static.Models.api_employee_models import (
    HeadDeleteForm,
    HeadInputForm,
    HeadUpdateForm,
    head_delete_model,
    head_insert_model,
    head_update_model,
)
from static.Models.api_fichajes_models import expected_files
from static.Models.api_models import expected_headers_per
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_midleware_admin import (
    delete_customer,
    delete_head_from_api,
    delete_supplier,
    fetch_heads,
    fetch_heads_main,
    get_all_clients_data,
    get_all_suppliers_data,
    get_items_supplier_name,
    insert_customer,
    insert_head_from_api,
    insert_supplier,
    items_supplier_from_file,
    update_customer,
    update_extra_info_supplier,
    update_head_from_api,
    update_supplier,
)

__author__ = "Edisson Naula"
__date__ = "$ 27/ene/2025  at 16:13 $"

ns = Namespace("GUI/api/v1/admin/db")


@ns.route("/clients/allClients")
class ClientsAll(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "sm"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_all_clients_data(data_token)
        return data, code


@ns.route("/client")
class ClientDB(Resource):
    @ns.expect(expected_headers_per, client_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )

        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ClientInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data, code = insert_customer(data, data_token)
        return data, code

    @ns.expect(expected_headers_per, client_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ClientUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data, code = update_customer(data, data_token)
        return data, code

    @ns.expect(expected_headers_per, client_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ClientDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data, code = delete_customer(data, data_token)
        return data, code


@ns.route("/suppliers/allSuppliers")
class SuppliersAll(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_all_suppliers_data(data_token)
        return data, code


@ns.route("/suppliers/items-<string:id_s>")
class FetchSuppliersItems(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_s):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_items_supplier_name(id_s, data_token)
        return data, code


@ns.route("/supplier")
class SupplierActions(Resource):
    @ns.expect(expected_headers_per, supplier_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SupplierInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data, code = insert_supplier(data, data_token)
        return data, code

    @ns.expect(expected_headers_per, supplier_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SupplierUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data, code = update_supplier(data, data_token)
        return data, code

    @ns.expect(expected_headers_per, supplier_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SupplierDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data, code = delete_supplier(data, data_token)
        return data, code


@ns.route("/extraInfoSupplier")
class UpdateEISupplier(Resource):
    @ns.expect(expected_headers_per, update_extra_info_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SupplierEInfoUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data, code = update_extra_info_supplier(data, data_token)
        return data, code


@ns.route("/heads")
class HeadsDepartmentAuto(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request,
            department=[
                "administracion",
                "operaciones",
                "rrhh",
                "iaotros",
                "respe",
            ],
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = fetch_heads_main(data_token)
        return data, code


@ns.route("/heads/<string:id_d>")
class HeadsDepartment(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_d):
        flag, data_token, msg = token_verification_procedure(
            request,
            department=[
                "administracion",
                "operaciones",
                "almacen",
                "sm",
                "bitacora",
                "rrhh",
            ],
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = fetch_heads(int(id_d), data_token)
        return data, code


@ns.route("/head")
class HeadDB(Resource):
    @ns.expect(expected_headers_per, head_insert_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "operaciones", "rrhh"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = HeadInputForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = insert_head_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, head_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "operaciones", "rrhh"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = HeadUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = update_head_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, head_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "operaciones", "rrhh"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = HeadDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data = validator.data
        data_out, code = delete_head_from_api(data, data_token)
        return data_out, code


@ns.route("/suppliers/items/file")
class ItemsSupplierFileUpload(Resource):
    @ns.expect(expected_headers_per, expected_files)
    def post(self):
        """
        Read excel file and parse items for supplier. Required column in excel:
        - ITEM
        - UDM
        - PRECIO UNITARIO
        - MARCA
        - NRO. PARTE
        - DESCRIPCIÓN LARGA
        - DESCRIPCIÓN CORTA
        """
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath_download = os.path.join(tempfile.mkdtemp(), filename)
            file.save(filepath_download)
            data = {"path": filepath_download}
            data_out, code = items_supplier_from_file(data)
            return data_out, code
        else:
            return {"msg": "No se subio el archivo"}, 400
