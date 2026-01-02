# -*- coding: utf-8 -*-
from templates.resources.midleware.Functions_midleware_admin import items_supplier_from_file
import tempfile
import os
from werkzeug.utils import secure_filename
from static.Models.api_fichajes_models import expected_files
from templates.resources.midleware.Functions_midleware_admin import get_items_supplier_name

from flask import request
from flask_restx import Namespace, Resource

from static.Models.api_clients_suppliers_models import (
    client_model,
    ClientDeleteForm,
    ClientInsertForm,
    ClientUpdateForm,
    supplier_delete_model,
    supplier_model,
    SupplierDeleteForm,
    SupplierUpdateForm,
    SupplierInsertForm,
)
from static.Models.api_employee_models import (
    head_insert_model,
    HeadInputForm,
    head_update_model,
    HeadUpdateForm,
    head_delete_model,
    HeadDeleteForm,
)
from static.Models.api_models import expected_headers_per
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_midleware_admin import (
    get_all_clients_data,
    insert_customer,
    delete_customer,
    update_customer,
    get_all_suppliers_data,
    update_supplier,
    insert_supplier,
    delete_supplier,
    fetch_heads,
    insert_head_from_api,
    update_head_from_api,
    delete_head_from_api,
    fetch_heads_main,
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
        data, code = get_all_clients_data()
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
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data, code = insert_customer(data)
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
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data, code = update_customer(data)
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
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data, code = delete_customer(data)
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
        data, code = get_all_suppliers_data()
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
        data, code = get_items_supplier_name(id_s)
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
        validator = SupplierInsertForm.from_json(ns.payload)    # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data, code = insert_supplier(data)
        return data, code

    @ns.expect(expected_headers_per, supplier_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SupplierUpdateForm.from_json(ns.payload)    # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data, code = update_supplier(data)
        return data, code

    @ns.expect(expected_headers_per, supplier_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department="administracion"
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = SupplierDeleteForm.from_json(ns.payload)    # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        data, code = delete_supplier(data)
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
                "ia" "otros",
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
        data, code = fetch_heads(int(id_d))
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
        validator = HeadInputForm.from_json(ns.payload)     # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
        validator = HeadUpdateForm.from_json(ns.payload)    # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
        validator = HeadDeleteForm.from_json(ns.payload)    # pyrefly: ignore
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
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
