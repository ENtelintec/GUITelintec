# -*- coding: utf-8 -*-
"""
Namespace CDA — Control De Activos. Primer modulo: Control de Estado de
Vehiculos (FO-CDA-02 R3). Otros activos se agregaran bajo este mismo namespace.
"""
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026 $"

from flask import request
from flask_restx import Namespace, Resource

from static.Models.api_cda_models import (
    CdaFineDeleteForm,
    CdaFinePostForm,
    CdaFinePutForm,
    CdaPolicyDeleteForm,
    CdaPolicyPostForm,
    CdaPolicyPutForm,
    CdaPurchaseDeleteForm,
    CdaPurchasePostForm,
    CdaPurchasePutForm,
    CdaServiceDeleteForm,
    CdaServicePostForm,
    CdaServicePutForm,
    CdaTireDeleteForm,
    CdaTirePutForm,
    CdaVehicleCancelForm,
    CdaVehicleDeleteForm,
    CdaVehiclePostForm,
    CdaVehiclePutForm,
    cda_fine_delete_model,
    cda_fine_post_model,
    cda_fine_put_model,
    cda_policy_delete_model,
    cda_policy_post_model,
    cda_policy_put_model,
    cda_purchase_delete_model,
    cda_purchase_post_model,
    cda_purchase_put_model,
    cda_service_delete_model,
    cda_service_post_model,
    cda_service_put_model,
    cda_tire_delete_model,
    cda_tire_put_model,
    cda_vehicle_cancel_model,
    cda_vehicle_delete_model,
    cda_vehicle_post_model,
    cda_vehicle_put_model,
)
from static.Models.api_models import expected_headers_per
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.MD_CDA import (
    cancel_vehicle_api,
    create_fine_api,
    create_policy_api,
    create_service_api,
    create_vehicle_api,
    create_vehicle_purchase_api,
    delete_fine_api,
    delete_policy_api,
    delete_service_api,
    delete_tire_api,
    delete_vehicle_api,
    delete_vehicle_purchase_api,
    fetch_maintenance_view,
    fetch_policies_view,
    fetch_services_view,
    fetch_tires_view,
    fetch_refrendos_view,
    fetch_vehicle_purchases_view,
    fetch_vehicles,
    get_cda_catalogs,
    get_vehicle_detail_api,
    update_fine_api,
    update_policy_api,
    update_service_api,
    update_vehicle_api,
    update_vehicle_purchase_api,
    upsert_tire_api,
)

ns = Namespace("GUI/api/v1/cda")

_DEPARTMENTS = ["administracion", "sgi"]


def _auth():
    flag, data_token, msg = token_verification_procedure(request, department=_DEPARTMENTS)
    if not flag:
        return None, ({"error": msg if msg != "" else "No autorizado. Token invalido"}, 401)
    return data_token, None


@ns.route("/catalogs")
class CdaCatalogs(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        data_out, code = get_cda_catalogs()
        return data_out, code


@ns.route("/vehicles")
class CdaVehicles(Resource):
    @ns.doc(
        params={
            "status": "Filtra por estatus (0=ACTIVO, 1=DETENIDO, 2=BAJA)",
            "is_active": "1=activos (default), 0=dados de baja",
            "all": "1 -> incluye activos y bajas (ignora is_active)",
        }
    )
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        params = {
            "status": request.args.get("status"),
            "is_active": request.args.get("is_active"),
            "all": request.args.get("all"),
        }
        data_out, code = fetch_vehicles(params, data_token)
        return data_out, code


@ns.route("/vehicle/<int:id_vehicle>")
class CdaVehicleDetail(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_vehicle):
        data_token, err = _auth()
        if err:
            return err
        data_out, code = get_vehicle_detail_api(id_vehicle, data_token)
        return data_out, code


@ns.route("/vehicle")
class CdaVehicleOps(Resource):
    @ns.expect(expected_headers_per, cda_vehicle_post_model)
    def post(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaVehiclePostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = create_vehicle_api(validator.data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, cda_vehicle_put_model)
    def put(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaVehiclePutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        # raw_payload -> el midleware solo sobreescribe lo enviado (update parcial).
        data_out, code = update_vehicle_api(validator.data, data_token, ns.payload or {})
        return data_out, code

    @ns.expect(expected_headers_per, cda_vehicle_delete_model)
    def delete(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaVehicleDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = delete_vehicle_api(validator.data, data_token)
        return data_out, code


@ns.route("/vehicle/cancel")
class CdaVehicleCancel(Resource):
    @ns.expect(expected_headers_per, cda_vehicle_cancel_model)
    def put(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaVehicleCancelForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = cancel_vehicle_api(validator.data, data_token)
        return data_out, code


@ns.route("/policy")
class CdaPolicyOps(Resource):
    @ns.expect(expected_headers_per, cda_policy_post_model)
    def post(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaPolicyPostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = create_policy_api(validator.data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, cda_policy_put_model)
    def put(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaPolicyPutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = update_policy_api(validator.data, data_token, ns.payload or {})
        return data_out, code

    @ns.expect(expected_headers_per, cda_policy_delete_model)
    def delete(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaPolicyDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = delete_policy_api(validator.data, data_token)
        return data_out, code


@ns.route("/service")
class CdaServiceOps(Resource):
    @ns.expect(expected_headers_per, cda_service_post_model)
    def post(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaServicePostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = create_service_api(validator.data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, cda_service_put_model)
    def put(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaServicePutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = update_service_api(validator.data, data_token, ns.payload or {})
        return data_out, code

    @ns.expect(expected_headers_per, cda_service_delete_model)
    def delete(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaServiceDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = delete_service_api(validator.data, data_token)
        return data_out, code


@ns.route("/tire")
class CdaTireOps(Resource):
    @ns.expect(expected_headers_per, cda_tire_put_model)
    def put(self):
        """Upsert por (vehicle_id, position): crea si no existe, actualiza si existe."""
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaTirePutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = upsert_tire_api(validator.data, data_token, ns.payload or {})
        return data_out, code

    @ns.expect(expected_headers_per, cda_tire_delete_model)
    def delete(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaTireDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = delete_tire_api(validator.data, data_token)
        return data_out, code


@ns.route("/fine")
class CdaFineOps(Resource):
    @ns.expect(expected_headers_per, cda_fine_post_model)
    def post(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaFinePostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = create_fine_api(validator.data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, cda_fine_put_model)
    def put(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaFinePutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = update_fine_api(validator.data, data_token, ns.payload or {})
        return data_out, code

    @ns.expect(expected_headers_per, cda_fine_delete_model)
    def delete(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaFineDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = delete_fine_api(validator.data, data_token)
        return data_out, code


@ns.route("/purchase")
class CdaPurchaseOps(Resource):
    @ns.expect(expected_headers_per, cda_purchase_post_model)
    def post(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaPurchasePostForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = create_vehicle_purchase_api(validator.data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, cda_purchase_put_model)
    def put(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaPurchasePutForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = update_vehicle_purchase_api(validator.data, data_token, ns.payload or {})
        return data_out, code

    @ns.expect(expected_headers_per, cda_purchase_delete_model)
    def delete(self):
        data_token, err = _auth()
        if err:
            return err
        # noinspection PyUnresolvedReferences
        validator = CdaPurchaseDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
        data_out, code = delete_vehicle_purchase_api(validator.data, data_token)
        return data_out, code


# --- Vistas (las hojas del Excel) --------------------------------------------
@ns.route("/view/policies")
class CdaViewPolicies(Resource):
    @ns.doc(params={"status": "Filtra vehículos por estatus", "all": "1 -> incluye bajas"})
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        params = {
            "status": request.args.get("status"),
            "is_active": request.args.get("is_active"),
            "all": request.args.get("all"),
        }
        data_out, code = fetch_policies_view(params, data_token)
        return data_out, code


@ns.route("/view/maintenance")
class CdaViewMaintenance(Resource):
    @ns.doc(params={"status": "Filtra vehículos por estatus", "all": "1 -> incluye bajas"})
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        params = {
            "status": request.args.get("status"),
            "is_active": request.args.get("is_active"),
            "all": request.args.get("all"),
        }
        data_out, code = fetch_maintenance_view(params, data_token)
        return data_out, code


@ns.route("/view/services")
class CdaViewServices(Resource):
    @ns.doc(
        params={
            "vehicle_id": "Filtra por vehículo",
            "service_type": "0=MANTENIMIENTO, 1=REPARACION, 2=SERVICIO",
            "date_from": "date >= YYYY-MM-DD",
            "date_to": "date <= YYYY-MM-DD",
        }
    )
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        params = {
            "vehicle_id": request.args.get("vehicle_id"),
            "service_type": request.args.get("service_type"),
            "date_from": request.args.get("date_from"),
            "date_to": request.args.get("date_to"),
        }
        data_out, code = fetch_services_view(params, data_token)
        return data_out, code


@ns.route("/view/tires")
class CdaViewTires(Resource):
    @ns.doc(params={"status": "Filtra vehículos por estatus", "all": "1 -> incluye bajas"})
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        params = {
            "status": request.args.get("status"),
            "is_active": request.args.get("is_active"),
            "all": request.args.get("all"),
        }
        data_out, code = fetch_tires_view(params, data_token)
        return data_out, code


@ns.route("/view/refrendos")
class CdaViewRefrendos(Resource):
    @ns.doc(params={"year": "Año (default: el actual)", "all": "1 -> incluye bajas"})
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        params = {
            "year": request.args.get("year"),
            "status": request.args.get("status"),
            "is_active": request.args.get("is_active"),
            "all": request.args.get("all"),
        }
        data_out, code = fetch_refrendos_view(params, data_token)
        return data_out, code


@ns.route("/view/purchases")
class CdaViewPurchases(Resource):
    @ns.doc(
        params={
            "vehicle_id": "Filtra por vehículo",
            "status": "0=PENDIENTE, 1=COMPRADO, 2=CANCELADO",
            "date_from": "created_at >= YYYY-MM-DD",
            "date_to": "created_at <= YYYY-MM-DD",
        }
    )
    @ns.expect(expected_headers_per)
    def get(self):
        data_token, err = _auth()
        if err:
            return err
        params = {
            "vehicle_id": request.args.get("vehicle_id"),
            "status": request.args.get("status"),
            "date_from": request.args.get("date_from"),
            "date_to": request.args.get("date_to"),
        }
        data_out, code = fetch_vehicle_purchases_view(params, data_token)
        return data_out, code
