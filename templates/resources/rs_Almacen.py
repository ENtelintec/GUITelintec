# -*- coding: utf-8 -*-

import os

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_inventory_models import (
    FileBarcodeForm,
    FileBarcodeMultipleForm,
    FileMovementsForm,
    MovementsListPostForm,
    ProductDeleteForm,
    ProductPostForm,
    ProductPutForm,
    ProductsListPostForm,
    ReservationDeleteForm,
    ReservationPostForm,
    ReservationPutForm,
    expected_files_almacen,
    file_barcode_multiple_request_model,
    file_barcode_request_model,
    file_movements_request_model,
    movements_list_post_model,
    product_delete_model,
    product_insert_model,
    product_model_update,
    products_list_post_model,
    reservation_delete_model,
    reservation_post_model,
    reservation_put_model,
)
from static.Models.api_models import expected_headers_per
from static.Models.api_movements_models import (
    MovementDeleteForm,
    MovementInsertForm,
    MovementUpdateForm,
    movement_delete_model,
    movement_insert_model,
    movement_update_model,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_midleware_almacen import (
    create_file_inventory_excel,
    create_file_inventory_pdf,
    create_file_movements_amc,
    create_pdf_barcode,
    create_pdf_barcode_multiple,
    create_reservation_from_api,
    delete_movement_amc,
    delete_product_from_api,
    delete_reservation_from_api,
    get_all_movements,
    get_all_products_DB,
    get_categories_db,
    get_epp_db,
    get_epp_movements,
    get_new_code_products,
    get_reservations_db,
    get_suppliers_db,
    insert_and_update_multiple_products_from_api,
    insert_movement,
    insert_multiple_movements_from_api,
    insert_product_db,
    update_movement,
    update_product_amc,
    update_reservation_from_api,
    upload_product_db_from_file,
)

__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 15:22 $"

ns = Namespace("GUI/api/v1/almacen")

# Envelope de respuesta unificado: {data, msg, error}. Ver
# docs/almacen_response_envelope.md y docs/sm_response_envelope.md.
def _invalid_structure(errors):
    return {"data": None, "msg": "Estructura de datos invalida", "error": errors}, 400


@ns.route("/movements/<string:type_m>")
class GetMovements(Resource):
    @ns.expect(expected_headers_per)
    def get(self, type_m):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {
                "data": [],
                "error": msg if msg != "" else "No autorizado. Token invalido",
            }, 401
        data_out, code = get_all_movements(type_m, data_token)
        return data_out, code


@ns.route("/movement")
class MovementDB(Resource):
    @ns.expect(expected_headers_per, movement_insert_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department=["almacen", "epp"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = MovementInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = insert_movement(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, movement_update_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department=["almacen", "epp"])
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = MovementUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = update_movement(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, movement_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = MovementDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = delete_movement_amc(data, data_token)
        return data_out, code


@ns.route("/multiple/movements")
class MultipleMovementDB(Resource):
    @ns.expect(expected_headers_per, movements_list_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = MovementsListPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = insert_multiple_movements_from_api(data, data_token)
        return data_out, code


@ns.route("/inventory/products/<string:type_p>")
class FetchProducts(Resource):
    @ns.expect(expected_headers_per)
    def get(self, type_p):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_all_products_DB(type_p, data_token)
        return data_out, code


@ns.route("/inventory/product")
class ProductActions(Resource):
    @ns.expect(expected_headers_per, product_insert_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ProductPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = insert_product_db(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, product_model_update)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ProductPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = update_product_amc(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, product_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ProductDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = delete_product_from_api(data, data_token)
        return data_out, code


@ns.route("/inventory/multiple/products")
class InventoryMultipleProducts(Resource):
    @ns.expect(expected_headers_per, products_list_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = ProductsListPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = insert_and_update_multiple_products_from_api(data, data_token)
        return data_out, code


@ns.route("/inventory/categories/all")
class InventoryCategories(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_categories_db(data_token)
        return data_out, code


@ns.route("/inventory/suppliers/allSuppliers")
class InventorySuppliers(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_suppliers_db(data_token)
        return data_out, code


@ns.route("/codes/generate")
class GenerateCode(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_new_code_products(data_token)
        return data_out, code


def _save_and_upload_inventory_file(data_token, **upload_kwargs):
    """Shared handler for the 3 inventory file-upload endpoints. Validates the
    incoming xlsx, persists it, and passes it to the midleware (which returns the
    {data, msg, error} envelope)."""
    if "file" not in request.files:
        return {"data": None, "msg": "No se detecto un archivo", "error": "No se detecto un archivo"}, 400
    file = request.files["file"]
    if not (file and file.filename):
        return {"data": None, "msg": "No se subio el archivo", "error": "No se subio el archivo"}, 400
    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".xlsx"):
        return {"data": None, "msg": "No se detecto un archivo xlsx valido", "error": "Formato de archivo invalido"}, 400
    new_name = "inventario.xlsx"
    file.save(os.path.join("files", new_name))
    try:
        data_out, code = upload_product_db_from_file(os.path.join("files", new_name), token_data=data_token, **upload_kwargs)
        return data_out, code
    except Exception as e:
        print(e)
        return {"data": None, "msg": "Error en la estructura del archivo", "error": str(e)}, 400


@ns.route("/file/upload/regular")
class UploadInventoryeFile(Resource):
    @ns.expect(expected_headers_per, expected_files_almacen)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        return _save_and_upload_inventory_file(data_token)


@ns.route("/file/upload/tool")
class UploadInventoryeFileTool(Resource):
    @ns.expect(expected_headers_per, expected_files_almacen)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        return _save_and_upload_inventory_file(data_token, is_tool=True)


@ns.route("/file/upload/internal")
class UploadInventoryeFileInternal(Resource):
    @ns.expect(expected_headers_per, expected_files_almacen)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        return _save_and_upload_inventory_file(data_token, is_internal=1)


@ns.route("/file/download/products/pdf")
class DownloadInventoryFilePDF(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        filepath, code = create_file_inventory_pdf(data_token)
        if code != 200 or filepath is None:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/file/download/products/excel")
class DownloadInventoryFileExcel(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        filepath, code = create_file_inventory_excel(data_token)
        if code != 200 or filepath is None:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/file/download/movements/pdf")
class DownloadMovementsFilePDF(Resource):
    @ns.expect(expected_headers_per, file_movements_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = FileMovementsForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        filepath, code = create_file_movements_amc(data, data_token)
        if code != 200 or filepath is None:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/file/download/movements/excel")
class DownloadMovementsFileExcel(Resource):
    @ns.expect(expected_headers_per, file_movements_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = FileMovementsForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        filepath, code = create_file_movements_amc(data, data_token, type_file="excel")
        if code != 200 or filepath is None:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/file/download/barcode")
class DownloadBarcodeFile(Resource):
    @ns.expect(expected_headers_per, file_barcode_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = FileBarcodeForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        filepath, code = create_pdf_barcode(data, data_token)
        if code != 200:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(str(filepath), as_attachment=True)


@ns.route("/file/download/barcode/multiple")
class DownloadMultipleBarcodeFile(Resource):
    @ns.expect(expected_headers_per, file_barcode_multiple_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="almacen")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = FileBarcodeMultipleForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        filepath, code = create_pdf_barcode_multiple(data)
        if code != 200:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/inventory/epp")
class InventoryEpp(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="epp")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_epp_db(data_token)
        return data_out, code


@ns.route("/movements/epp/<string:type_m>")
class GetMovementsEpp(Resource):
    @ns.expect(expected_headers_per)
    def get(self, type_m):
        flag, data_token, msg = token_verification_procedure(request, department="epp")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_epp_movements(type_m, data_token)
        return data_out, code


@ns.route("/file/download/eppmovements/pdf")
class DownloadEppMovementsFilePDF(Resource):
    @ns.expect(expected_headers_per, file_movements_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="epp")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = FileMovementsForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        filepath, code = create_file_movements_amc(data, data_token, epp=1)
        if code != 200 or filepath is None:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/file/download/eppmovements/excel")
class DownloadEppMovementsFileExcel(Resource):
    @ns.expect(expected_headers_per, file_movements_request_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="epp")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = FileMovementsForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        filepath, code = create_file_movements_amc(data, data_token, type_file="excel", epp=1)
        if code != 200 or filepath is None:
            return {"data": None, "msg": "No se pudo generar el archivo", "error": filepath}, 400
        return send_file(filepath, as_attachment=True)


@ns.route("/reservation")
class ReservationActions(Resource):
    @ns.expect(expected_headers_per, reservation_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReservationPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = create_reservation_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, reservation_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReservationPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = update_reservation_from_api(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, reservation_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        validator = ReservationDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data = validator.data
        data_out, code = delete_reservation_from_api(data, data_token)
        return data_out, code


@ns.route("/reservations")
class GetReservations(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(
            request, department=["administracion", "almacen"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_reservations_db(data_token)
        return data_out, code
