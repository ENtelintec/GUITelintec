# -*- coding: utf-8 -*-
"""
Namespace SUCURSAL — lado sede del almacén multisede: inventario de la sede,
stock del principal en solo lectura y movimientos libres (entrada / salida)
con stock por sede (F2, docs/almacen_multisede_f2.md); traslados hacia la
sede y confirmación de recepción (F3, docs/almacen_multisede_f3.md).
Plan: docs/almacen_multisede_plan.md.

Permisos: `sucursal` (App.Department.Sucursal-<id>; el midleware valida el
id de sede contra el permiso). Las lecturas admiten además `almacen` /
`administracion` (supervisión desde el principal) con id_warehouse explícito.
"""
__author__ = "Edisson Naula"
__date__ = "$ 08/sep./2026  at 10:00 $"

from flask import request
from flask_restx import Namespace, Resource

from static.Models.api_models import expected_headers_per
from static.Models.api_sucursal_models import (
    SucursalMovementDeleteForm,
    SucursalMovementPostForm,
    SucursalMovementPutForm,
    TransferReceiveForm,
    sucursal_movement_delete_model,
    sucursal_movement_post_model,
    sucursal_movement_put_model,
    transfer_receive_model,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.MD_Sucursal import (
    create_sede_movement_api,
    delete_sede_movement_api,
    fetch_sede_transfers_api,
    get_main_inventory_api,
    get_sede_inventory_api,
    get_sede_movements_api,
    get_sede_transfer_api,
    receive_transfer_api,
    update_sede_movement_api,
)

ns = Namespace("GUI/api/v1/sucursal")

_READERS = ["sucursal", "almacen", "administracion"]
_WRITERS = "sucursal"


def _unauthorized(msg):
    return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401


def _invalid_structure(errors):
    return {"data": None, "msg": "Estructura de datos invalida", "error": errors}, 400


@ns.route("/inventory")
class SedeInventory(Resource):
    @ns.doc(
        params={
            "id_warehouse": "Sede (opcional si el permiso es de una sola sede)",
            "search": "Filtra por sku o nombre (LIKE)",
            "only_with_stock": "1 -> solo productos con stock > 0 en la sede",
        }
    )
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=_READERS)
        if not flag:
            return _unauthorized(msg)
        params = {
            "id_warehouse": request.args.get("id_warehouse"),
            "search": request.args.get("search"),
            "only_with_stock": request.args.get("only_with_stock"),
        }
        data_out, code = get_sede_inventory_api(params, data_token)
        return data_out, code


@ns.route("/inventory/main")
class MainInventoryReadOnly(Resource):
    @ns.doc(params={"search": "Filtra por sku o nombre", "only_with_stock": "1 -> solo con stock > 0"})
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=_READERS)
        if not flag:
            return _unauthorized(msg)
        params = {
            "search": request.args.get("search"),
            "only_with_stock": request.args.get("only_with_stock"),
        }
        data_out, code = get_main_inventory_api(params, data_token)
        return data_out, code


@ns.route("/movements/<string:type_m>")
class SedeMovements(Resource):
    @ns.doc(
        params={
            "type_m": "entrada | salida | all",
            "id_warehouse": "Sede (opcional si el permiso es de una sola sede)",
            "date_from": "YYYY-MM-DD inclusivo",
            "date_to": "YYYY-MM-DD inclusivo",
            "limit": "Tope de filas (default 500, máx 5000)",
        }
    )
    @ns.expect(expected_headers_per)
    def get(self, type_m):
        flag, data_token, msg = token_verification_procedure(request, department=_READERS)
        if not flag:
            return _unauthorized(msg)
        params = {
            "id_warehouse": request.args.get("id_warehouse"),
            "date_from": request.args.get("date_from"),
            "date_to": request.args.get("date_to"),
            "limit": request.args.get("limit"),
        }
        data_out, code = get_sede_movements_api(type_m, params, data_token)
        return data_out, code


@ns.route("/movement")
class SedeMovement(Resource):
    @ns.expect(expected_headers_per, sucursal_movement_post_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department=_WRITERS)
        if not flag:
            return _unauthorized(msg)
        # noinspection PyUnresolvedReferences
        validator = SucursalMovementPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data_out, code = create_sede_movement_api(validator.data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, sucursal_movement_put_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department=_WRITERS)
        if not flag:
            return _unauthorized(msg)
        # noinspection PyUnresolvedReferences
        validator = SucursalMovementPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data_out, code = update_sede_movement_api(validator.data, ns.payload, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, sucursal_movement_delete_model)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department=_WRITERS)
        if not flag:
            return _unauthorized(msg)
        # noinspection PyUnresolvedReferences
        validator = SucursalMovementDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data_out, code = delete_sede_movement_api(validator.data, data_token)
        return data_out, code


# --- Traslados hacia la sede (F3) ---------------------------------------------
@ns.route("/transfers")
class SedeTransfers(Resource):
    @ns.doc(
        params={
            "id_warehouse": "Sede (opcional si el permiso es de una sola sede)",
            "status": "0 en tránsito · 1 recibido · 2 con diferencias · 3 cancelado",
            "date_from": "YYYY-MM-DD inclusivo (creación)",
            "date_to": "YYYY-MM-DD inclusivo (creación)",
            "limit": "Tope de filas (default 200, máx 2000)",
        }
    )
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department=_READERS)
        if not flag:
            return _unauthorized(msg)
        params = {k: request.args.get(k) for k in ("id_warehouse", "status", "date_from", "date_to", "limit")}
        data_out, code = fetch_sede_transfers_api(params, data_token)
        return data_out, code


@ns.route("/transfer/<int:id_transfer>")
class SedeTransferDetail(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_transfer):
        flag, data_token, msg = token_verification_procedure(request, department=_READERS)
        if not flag:
            return _unauthorized(msg)
        data_out, code = get_sede_transfer_api(id_transfer, data_token)
        return data_out, code


@ns.route("/transfer/receive")
class SedeTransferReceive(Resource):
    @ns.expect(expected_headers_per, transfer_receive_model)
    def put(self):
        """Confirma la recepción (una sola vez) capturando lo realmente recibido por item."""
        flag, data_token, msg = token_verification_procedure(request, department=_WRITERS)
        if not flag:
            return _unauthorized(msg)
        # noinspection PyUnresolvedReferences
        validator = TransferReceiveForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return _invalid_structure(validator.errors)
        data_out, code = receive_transfer_api(validator.data, ns.payload, data_token)
        return data_out, code
