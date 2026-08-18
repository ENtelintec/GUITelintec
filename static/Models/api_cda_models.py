# -*- coding: utf-8 -*-
"""
Modelos del modulo CDA — Control de Estado de Vehiculos (FO-CDA-02 R3).
Ruta base: /GUI/api/v1/cda
Doble capa: api.model (swagger/docs) + WTForms Form (validacion runtime).
Al agregar un campo, actualizar AMBOS. Casi todo es opcional; los enums se
validan contra catalogo en el midleware (MD_CDA), no aqui.
"""
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026 $"

from flask_restx import fields
from wtforms import FloatField, FormField, StringField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import IntegerField
from wtforms.form import Form

from static.constants import api

# =============================================================================
# api.model (swagger)
# =============================================================================
_accessories_fields = {
    key: fields.Integer(required=False, description=f"{key} (0/1)", example=1)
    for key in (
        "torreta_ambar", "luces", "sticker_acceso", "eslinga_matracas",
        "topes_bloqueo", "extintor", "gato", "llave_cruz", "triangulo",
        "limpiaparabrisas", "llanta_repuesto", "cables_corriente",
    )
}
accessories_model = api.model("CdaAccessories", dict(_accessories_fields))

_vehicle_common_fields = {
    "code": fields.String(required=True, description="Código de flotilla (único)", example="TEL-001"),
    "model": fields.String(required=False, description="Modelo/apodo", example="HIACE"),
    "plate": fields.String(required=False, description="Placa", example="SCH128A"),
    "brand": fields.String(required=False, description="Marca", example="TOYOTA"),
    "niv": fields.String(required=False, description="NIV/VIN", example="JTFSX23P2K6202970"),
    "status": fields.Integer(required=False, description="0=ACTIVO, 1=DETENIDO, 2=BAJA", example=0),
    "oil_type": fields.Integer(required=False, description="0=MINERAL(5k km), 1=SINTETICO(10k km)", example=0),
    "current_km": fields.Integer(required=False, description="Kilometraje actual", example=45000),
    "current_km_date": fields.String(required=False, description="Fecha del km actual (YYYY-MM-DD)"),
    "rin_size": fields.String(required=False, description="Medida de rin", example="R16"),
    "tire_size": fields.String(required=False, description="Medida de llanta", example="205/65R16"),
    "refrendo_last_paid": fields.String(required=False, description="Último refrendo pagado (YYYY-MM-DD); AL_DIA se deriva"),
    "refrendo_note": fields.String(required=False, description="Nota de refrendo (extra_info)"),
    "accessories": fields.Nested(accessories_model, required=False, description="Checklist de accesorios (0/1)"),
}

cda_vehicle_post_model = api.model("CdaVehiclePost", dict(_vehicle_common_fields))
cda_vehicle_put_model = api.model(
    "CdaVehiclePut",
    {"id_vehicle": fields.Integer(required=True, description="ID del vehículo", example=1), **_vehicle_common_fields},
)
cda_vehicle_delete_model = api.model(
    "CdaVehicleDelete",
    {"id_vehicle": fields.Integer(required=True, description="ID del vehículo", example=1)},
)
cda_vehicle_cancel_model = api.model(
    "CdaVehicleCancel",
    {
        "id_vehicle": fields.Integer(required=True, description="ID del vehículo", example=1),
        "comment": fields.String(required=False, description="Motivo de la baja"),
    },
)

payment_slot_model = api.model(
    "CdaPaymentSlot",
    {
        "n": fields.Integer(required=True, description="Número de pago (1..slots)", example=1),
        "date": fields.String(required=False, description="Fecha en que se pagó (YYYY-MM-DD)"),
        "amount": fields.Float(required=False, description="Monto del pago"),
        "paid": fields.Integer(required=False, description="0/1", example=1),
    },
)

_policy_common_fields = {
    "inciso": fields.String(required=False, description="Nº inciso (folio de la aseguradora)", example="745A5305YV"),
    "insurer": fields.String(required=False, description="Aseguradora", example="BBVA SEGUROS"),
    "date_start": fields.String(required=False, description="Inicio de vigencia (YYYY-MM-DD)"),
    "date_end": fields.String(required=False, description="Fin de vigencia (YYYY-MM-DD)"),
    "payment_form": fields.Integer(required=False, description="0=MENSUAL(12), 1=TRIMESTRAL(4), 2=ANUAL(1), 3=CONTADO(1)", example=0),
    "payments": fields.List(fields.Nested(payment_slot_model), required=False, description="Slots de pago (se normalizan por forma de pago)"),
    "notification": fields.String(required=False, description="Notificación (texto libre)"),
    "other_requirements": fields.String(required=False, description="Otros requisitos"),
}
cda_policy_post_model = api.model(
    "CdaPolicyPost",
    {"vehicle_id": fields.Integer(required=True, description="ID del vehículo", example=1), **_policy_common_fields},
)
cda_policy_put_model = api.model(
    "CdaPolicyPut",
    {
        "id_policy": fields.Integer(required=True, description="ID de la póliza", example=1),
        "is_active": fields.Integer(required=False, description="1=vigente, 0=cancelada"),
        **_policy_common_fields,
    },
)
cda_policy_delete_model = api.model(
    "CdaPolicyDelete",
    {"id_policy": fields.Integer(required=True, description="ID de la póliza", example=1)},
)

_service_common_fields = {
    "service_type": fields.Integer(required=False, description="0=MANTENIMIENTO, 1=REPARACION, 2=SERVICIO", example=0),
    "date": fields.String(required=False, description="Fecha (YYYY-MM-DD)"),
    "description": fields.String(required=False, description="Descripción del mantenimiento/reparación"),
    "km": fields.Integer(required=False, description="Kilometraje al momento (auto-actualiza el del vehículo si es mayor)", example=45000),
    "workshop": fields.String(required=False, description="Taller"),
    "cost": fields.Float(required=False, description="Costo"),
}
cda_service_post_model = api.model(
    "CdaServicePost",
    {"vehicle_id": fields.Integer(required=True, description="ID del vehículo", example=1), **_service_common_fields},
)
cda_service_put_model = api.model(
    "CdaServicePut",
    {"id_service": fields.Integer(required=True, description="ID del servicio", example=1), **_service_common_fields},
)
cda_service_delete_model = api.model(
    "CdaServiceDelete",
    {"id_service": fields.Integer(required=True, description="ID del servicio", example=1)},
)

cda_tire_put_model = api.model(
    "CdaTirePut",
    {
        "vehicle_id": fields.Integer(required=True, description="ID del vehículo", example=1),
        "position": fields.Integer(required=True, description="0=DEL.PILOTO, 1=DEL.COPILOTO, 2=TRAS.PILOTO, 3=TRAS.COPILOTO, 4=REPUESTO", example=0),
        "dot": fields.String(required=False, description="Código/fecha DOT"),
        "manufacture_date": fields.String(required=False, description="Fecha de fabricación (YYYY-MM-DD)"),
        "brand": fields.String(required=False, description="Marca de la llanta"),
        "expiry_date": fields.String(required=False, description="Fecha de vencimiento (YYYY-MM-DD); 'expired' se deriva"),
        "physical_state": fields.String(required=False, description="Estado físico actual (texto libre)"),
        "needs_change": fields.Integer(required=False, description="¿Requiere cambio? 0/1", example=0),
    },
)
cda_tire_delete_model = api.model(
    "CdaTireDelete",
    {
        "id_tire": fields.Integer(required=False, description="ID de la llanta (o vehicle_id + position)"),
        "vehicle_id": fields.Integer(required=False, description="ID del vehículo"),
        "position": fields.Integer(required=False, description="Posición 0..4"),
    },
)

_fine_common_fields = {
    "year": fields.Integer(required=True, description="Año", example=2026),
    "month": fields.Integer(required=True, description="Mes 1..12", example=3),
    "amount": fields.Float(required=False, description="Monto de la multa"),
    "description": fields.String(required=False, description="Motivo/descripción"),
    "responsible": fields.String(required=False, description="Responsable"),
}
cda_fine_post_model = api.model(
    "CdaFinePost",
    {"vehicle_id": fields.Integer(required=True, description="ID del vehículo", example=1), **_fine_common_fields},
)
cda_fine_put_model = api.model(
    "CdaFinePut",
    {"id_fine": fields.Integer(required=True, description="ID de la multa", example=1), **_fine_common_fields},
)
cda_fine_delete_model = api.model(
    "CdaFineDelete",
    {"id_fine": fields.Integer(required=True, description="ID de la multa", example=1)},
)

_purchase_common_fields = {
    "checklist_sent": fields.Integer(required=False, description="¿Checklist enviado? 0/1", example=0),
    "checklist_sent_date": fields.String(required=False, description="Fecha de envío del checklist (YYYY-MM-DD)"),
    "problem": fields.String(required=False, description="Problema o falla"),
    "quantity": fields.Float(required=False, description="Cantidad"),
    "unit": fields.String(required=False, description="Unidad", example="PZA"),
    "cost": fields.Float(required=False, description="Costo unitario (TOTAL = quantity*cost, calculado)"),
    "supplier": fields.String(required=False, description="Proveedor o taller"),
    "observations": fields.String(required=False, description="Observaciones"),
    "status": fields.Integer(required=False, description="0=PENDIENTE, 1=COMPRADO, 2=CANCELADO", example=0),
    "po_id": fields.Integer(required=False, description="Enlace flojo a purchase_orders (sin lógica)"),
}
cda_purchase_post_model = api.model(
    "CdaPurchasePost",
    {"vehicle_id": fields.Integer(required=True, description="ID del vehículo", example=1), **_purchase_common_fields},
)
cda_purchase_put_model = api.model(
    "CdaPurchasePut",
    {"id_purchase": fields.Integer(required=True, description="ID de la compra", example=1), **_purchase_common_fields},
)
cda_purchase_delete_model = api.model(
    "CdaPurchaseDelete",
    {"id_purchase": fields.Integer(required=True, description="ID de la compra", example=1)},
)


# =============================================================================
# WTForms (validacion real)
# =============================================================================
class CdaAccessoriesForm(Form):
    torreta_ambar = IntegerField("torreta_ambar", [], default=None)
    luces = IntegerField("luces", [], default=None)
    sticker_acceso = IntegerField("sticker_acceso", [], default=None)
    eslinga_matracas = IntegerField("eslinga_matracas", [], default=None)
    topes_bloqueo = IntegerField("topes_bloqueo", [], default=None)
    extintor = IntegerField("extintor", [], default=None)
    gato = IntegerField("gato", [], default=None)
    llave_cruz = IntegerField("llave_cruz", [], default=None)
    triangulo = IntegerField("triangulo", [], default=None)
    limpiaparabrisas = IntegerField("limpiaparabrisas", [], default=None)
    llanta_repuesto = IntegerField("llanta_repuesto", [], default=None)
    cables_corriente = IntegerField("cables_corriente", [], default=None)


class _CdaVehicleBaseForm(Form):
    code = StringField("code", [], default=None)
    model = StringField("model", [], default=None)
    plate = StringField("plate", [], default=None)
    brand = StringField("brand", [], default=None)
    niv = StringField("niv", [], default=None)
    status = IntegerField("status", [], default=None)
    oil_type = IntegerField("oil_type", [], default=None)
    current_km = IntegerField("current_km", [], default=None)
    current_km_date = StringField("current_km_date", [], default=None)
    rin_size = StringField("rin_size", [], default=None)
    tire_size = StringField("tire_size", [], default=None)
    refrendo_last_paid = StringField("refrendo_last_paid", [], default=None)
    refrendo_note = StringField("refrendo_note", [], default=None)
    accessories = FormField(CdaAccessoriesForm)


class CdaVehiclePostForm(_CdaVehicleBaseForm):
    pass


class CdaVehiclePutForm(_CdaVehicleBaseForm):
    id_vehicle = IntegerField("id_vehicle", [], default=None)
    id = IntegerField("id", [], default=None)


class CdaVehicleDeleteForm(Form):
    id_vehicle = IntegerField("id_vehicle", [], default=None)
    id = IntegerField("id", [], default=None)


class CdaVehicleCancelForm(Form):
    id_vehicle = IntegerField("id_vehicle", [], default=None)
    id = IntegerField("id", [], default=None)
    comment = StringField("comment", [], default=None)


class CdaPaymentSlotForm(Form):
    n = IntegerField("n", [], default=None)
    date = StringField("date", [], default=None)
    amount = FloatField("amount", [], default=None)
    paid = IntegerField("paid", [], default=None)


class _CdaPolicyBaseForm(Form):
    inciso = StringField("inciso", [], default=None)
    insurer = StringField("insurer", [], default=None)
    date_start = StringField("date_start", [], default=None)
    date_end = StringField("date_end", [], default=None)
    payment_form = IntegerField("payment_form", [], default=None)
    payments = FieldList(FormField(CdaPaymentSlotForm), validators=[], default=[])
    notification = StringField("notification", [], default=None)
    other_requirements = StringField("other_requirements", [], default=None)


class CdaPolicyPostForm(_CdaPolicyBaseForm):
    vehicle_id = IntegerField("vehicle_id", [], default=None)


class CdaPolicyPutForm(_CdaPolicyBaseForm):
    id_policy = IntegerField("id_policy", [], default=None)
    id = IntegerField("id", [], default=None)
    is_active = IntegerField("is_active", [], default=None)


class CdaPolicyDeleteForm(Form):
    id_policy = IntegerField("id_policy", [], default=None)
    id = IntegerField("id", [], default=None)


class _CdaServiceBaseForm(Form):
    service_type = IntegerField("service_type", [], default=None)
    date = StringField("date", [], default=None)
    description = StringField("description", [], default=None)
    km = IntegerField("km", [], default=None)
    workshop = StringField("workshop", [], default=None)
    cost = FloatField("cost", [], default=None)


class CdaServicePostForm(_CdaServiceBaseForm):
    vehicle_id = IntegerField("vehicle_id", [], default=None)


class CdaServicePutForm(_CdaServiceBaseForm):
    id_service = IntegerField("id_service", [], default=None)
    id = IntegerField("id", [], default=None)


class CdaServiceDeleteForm(Form):
    id_service = IntegerField("id_service", [], default=None)
    id = IntegerField("id", [], default=None)


class CdaTirePutForm(Form):
    vehicle_id = IntegerField("vehicle_id", [], default=None)
    position = IntegerField("position", [], default=None)
    dot = StringField("dot", [], default=None)
    manufacture_date = StringField("manufacture_date", [], default=None)
    brand = StringField("brand", [], default=None)
    expiry_date = StringField("expiry_date", [], default=None)
    physical_state = StringField("physical_state", [], default=None)
    needs_change = IntegerField("needs_change", [], default=None)


class CdaTireDeleteForm(Form):
    id_tire = IntegerField("id_tire", [], default=None)
    id = IntegerField("id", [], default=None)
    vehicle_id = IntegerField("vehicle_id", [], default=None)
    position = IntegerField("position", [], default=None)


class _CdaFineBaseForm(Form):
    year = IntegerField("year", [], default=None)
    month = IntegerField("month", [], default=None)
    amount = FloatField("amount", [], default=None)
    description = StringField("description", [], default=None)
    responsible = StringField("responsible", [], default=None)


class CdaFinePostForm(_CdaFineBaseForm):
    vehicle_id = IntegerField("vehicle_id", [], default=None)


class CdaFinePutForm(_CdaFineBaseForm):
    id_fine = IntegerField("id_fine", [], default=None)
    id = IntegerField("id", [], default=None)


class CdaFineDeleteForm(Form):
    id_fine = IntegerField("id_fine", [], default=None)
    id = IntegerField("id", [], default=None)


class _CdaPurchaseBaseForm(Form):
    checklist_sent = IntegerField("checklist_sent", [], default=None)
    checklist_sent_date = StringField("checklist_sent_date", [], default=None)
    problem = StringField("problem", [], default=None)
    quantity = FloatField("quantity", [], default=None)
    unit = StringField("unit", [], default=None)
    cost = FloatField("cost", [], default=None)
    supplier = StringField("supplier", [], default=None)
    observations = StringField("observations", [], default=None)
    status = IntegerField("status", [], default=None)
    po_id = IntegerField("po_id", [], default=None)


class CdaPurchasePostForm(_CdaPurchaseBaseForm):
    vehicle_id = IntegerField("vehicle_id", [], default=None)


class CdaPurchasePutForm(_CdaPurchaseBaseForm):
    id_purchase = IntegerField("id_purchase", [], default=None)
    id = IntegerField("id", [], default=None)


class CdaPurchaseDeleteForm(Form):
    id_purchase = IntegerField("id_purchase", [], default=None)
    id = IntegerField("id", [], default=None)
