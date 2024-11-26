# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 15:22 $"

import os

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_inventory_models import (
    products_output_model,
    product_insert_model,
    product_delete_model,
    categories_output_model,
    suppliers_output_model,
    expected_files_almacen,
    ProductDeleteForm,
    ProductPostForm,
    ProductPutForm,
    FileMovementsForm,
    file_movements_request_model,
    products_list_post_model,
    ProductsListPostForm, movements_list_post_model, MovementsListPostForm, file_barcode_request_model, FileBarcodeForm,
)
from static.Models.api_movements_models import (
    movements_output_model,
    movement_insert_model,
    movement_delete_model,
    MovementInsertForm,
    MovementDeleteForm,
)
from templates.resources.midleware.Functions_midleware_almacen import (
    get_all_movements,
    insert_movement,
    update_movement,
    get_all_products_DB,
    insert_product_db,
    update_product_amc,
    get_categories_db,
    get_suppliers_db,
    upload_product_db_from_file,
    create_file_inventory,
    create_file_movements_amc,
    insert_and_update_multiple_products_amc, insert_multiple_movements, create_pdf_barcode,
)
from templates.controllers.product.p_and_s_controller import (
    delete_movement_db,
    delete_product_db,
)

ns = Namespace("GUI/api/v1/almacen")


@ns.route("/movements/<string:type_m>")
class GetMovements(Resource):
    @ns.marshal_with(movements_output_model)
    def get(self, type_m):
        data, code = get_all_movements(type_m)
        data_out = {"data": data, "msg": "Ok" if code == 200 else "Error"}
        return data_out, code


@ns.route("/movement")
class MovementDB(Resource):
    @ns.expect(movement_insert_model)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = MovementInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, result = insert_movement(data)
        return {
            "data": str(result),
            "msg": "Ok" if flag else "Error",
        }, 201 if flag else 400

    @ns.expect(movement_insert_model)
    def put(self):
        # noinspection PyUnresolvedReferences
        validator = MovementInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, result = update_movement(data)
        return {
            "data": str(result),
            "msg": "Ok" if flag else "Error",
        }, 200 if flag else 400

    @ns.expect(movement_delete_model)
    def delete(self):
        # noinspection PyUnresolvedReferences
        validator = MovementDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, result = delete_movement_db(data["id"])
        return {
            "data": str(result),
            "msg": "Ok" if flag else error,
        }, 200 if flag else 400


@ns.route("/multiple/movements")
class MultipleMovementDB(Resource):
    @ns.expect(movements_list_post_model)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = MovementsListPostForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, result = insert_multiple_movements(data)
        return {
            "data": result,
            "msg": "Ok" if flag else "Error",
        }, 201 if flag else 400


@ns.route("/inventory/products/<string:type_p>")
class InventoryProducts(Resource):
    @ns.marshal_with(products_output_model)
    def get(self, type_p):
        data, code = get_all_products_DB(type_p)
        return {"data": data, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route("/inventory/product")
class InventoryProduct(Resource):
    @ns.expect(product_insert_model)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = ProductPostForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, data_out = insert_product_db(data)
        return {
            "data": data_out,
            "msg": "Ok" if flag else "Error",
        }, 201 if flag else 400

    @ns.expect(product_insert_model)
    def put(self):
        # noinspection PyUnresolvedReferences
        validator = ProductPutForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, data_out = update_product_amc(data)
        return {
            "data": str(data_out),
            "msg": "Ok" if flag else "Error",
        }, 200 if flag else 400

    @ns.expect(product_delete_model)
    def delete(self):
        # noinspection PyUnresolvedReferences
        validator = ProductDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, error, data_out = delete_product_db(data["id"])
        return {
            "data": str(data_out),
            "msg": "Ok" if flag else "Error",
        }, 200 if flag else 400


@ns.route("/inventory/multiple/products")
class InventoryMultipleProducts(Resource):
    @ns.expect(products_list_post_model)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = ProductsListPostForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        flag, data_out = insert_and_update_multiple_products_amc(data)
        if not flag:
            return {"data": data_out, "msg": "Error"}, 400
        return {"data": data_out, "msg": "Ok"}, 200


@ns.route("/inventory/categories/all")
class InventoryCategories(Resource):
    @ns.marshal_with(categories_output_model)
    def get(self):
        code, data = get_categories_db()
        return {"data": data, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route("/inventory/suppliers/all")
class InventorySuppliers(Resource):
    @ns.marshal_with(suppliers_output_model)
    def get(self):
        code, data = get_suppliers_db()
        return {"data": data, "msg": "Ok" if code == 200 else "Error"}, code


@ns.route("/inventory/file/upload/regular")
class UploadInventoryeFile(Resource):
    @ns.expect(expected_files_almacen)
    def post(self):
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            if not filename.lower().endswith(".xlsx"):
                return {"data": "No se detecto un archivo xlsx valido"}, 400
            new_name = "inventario.xlsx"
            file.save(os.path.join("files", new_name))
            code, data = upload_product_db_from_file(os.path.join("files", new_name))
            if code != 200:
                return {"data": data, "msg": "Error at file structure"}, 400
            return {"data": data, "msg": f"Ok with filaname: {new_name}"}, 200
        else:
            return {"msg": "No se subio el archivo"}, 400


@ns.route("/inventory/file/upload/tool")
class UploadInventoryeFileTool(Resource):
    @ns.expect(expected_files_almacen)
    def post(self):
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            if not filename.lower().endswith(".xlsx"):
                return {"data": "No se detecto un archivo xlsx valido"}, 400
            new_name = "inventario.xlsx"
            file.save(os.path.join("files", new_name))
            code, data = upload_product_db_from_file(
                os.path.join("files", new_name), is_tool=True
            )
            if code != 200:
                return {"data": data, "msg": "Error at file structure"}, 400
            return {"data": data, "msg": f"Ok with filaname: {new_name}"}, 200
        else:
            return {"msg": "No se subio el archivo"}, 400


@ns.route("/inventory/file/upload/internal")
class UploadInventoryeFileInternal(Resource):
    @ns.expect(expected_files_almacen)
    def post(self):
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 400
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            if not filename.lower().endswith(".xlsx"):
                return {"data": "No se detecto un archivo xlsx valido"}, 400
            new_name = "inventario.xlsx"
            file.save(os.path.join("files", new_name))
            code, data = upload_product_db_from_file(
                os.path.join("files", new_name), is_internal=1
            )
            if code != 200:
                return {"data": data, "msg": "Error at file structure"}, 400
            return {"data": data, "msg": f"Ok with filaname: {new_name}"}, 200
        else:
            return {"msg": "No se subio el archivo"}, 400


@ns.route("/inventory/file/download/products")
class DownloadInventoryFile(Resource):
    def get(self):
        filepath, code = create_file_inventory()
        if code != 200:
            return {"data": filepath, "msg": "Error at creating file"}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/inventory/file/download/movements")
class DownloadMovementsFile(Resource):
    @ns.expect(file_movements_request_model)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = FileMovementsForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        filepath, code = create_file_movements_amc(data)
        if code != 200:
            return {"data": filepath, "msg": "Error at creating file"}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/inventory/file/download/barcode")
class DownloadBarcodeFile(Resource):
    @ns.expect(file_barcode_request_model)
    def post(self):
        # noinspection PyUnresolvedReferences
        validator = FileBarcodeForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": validator.errors, "msg": "Error at structure"}, 400
        data = validator.data
        filepath, code = create_pdf_barcode(data)
        return send_file(filepath, as_attachment=True) if code == 200 else (
            {"data": filepath, "msg": "Error at creating file"}, 400
        )
