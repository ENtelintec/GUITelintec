# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/sep./2026  at 16:30 $"

from flask_restx import fields
from wtforms import FormField, StringField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import IntegerField
from wtforms.form import Form
from wtforms.validators import AnyOf, InputRequired

from static.constants import api
from static.Models.api_balance_control_models import (
    BalanceControlCustomFieldForm,
    balance_control_custom_field_model,
)

# =====================================================================
# Control de Entregas (Administración) — cabecera por cotización OCD
# (docs/control_entregas.md). Ruta base: /GUI/api/v1/admin/collections/deliveryControl
# Doble capa: api.model (swagger) + WTForms (validación runtime).
# custom_fields reusa el contrato de control de saldos ({key,label,value_type,comment}).
# =====================================================================

CURRENCIES = ("MXN", "USD")

delivery_control_post_model = api.model(
    "DeliveryControlPost",
    {
        "quotation_id": fields.Integer(required=True, description="Cotización con metadata.document_type = ocd (PUT /admin/presales/quotation/ocd)", example=51),
        "title": fields.String(required=False, description="Nombre visible (default: quotation_code de la cotización)", example="OCD fibra óptica Guerrero"),
        "client_po_number": fields.String(required=False, description="Pedido EXIROS / nº de OC del cliente (default: el de la cotización)", example="3716578048"),
        "currency": fields.String(required=False, description="MXN | USD (default: el de la cotización)", example="MXN"),
        "remissions": fields.List(fields.Integer, required=False, description="Ids de remisiones a ligar (mismo cliente, libres); además se auto-adoptan las libres con items de esta cotización", example=[71, 72]),
        "custom_fields": fields.List(fields.Nested(balance_control_custom_field_model), required=False, description="Columnas dinámicas (orden = orden en la tabla)"),
    },
)

delivery_control_put_model = api.model(
    "DeliveryControlPut",
    {
        "id_control": fields.Integer(required=True, description="ID del control", example=3),
        "title": fields.String(required=False, description="Nombre visible (no puede vaciarse)", example="OCD fibra óptica Guerrero"),
        "client_po_number": fields.String(required=False, description="Pedido EXIROS / nº de OC"),
        "currency": fields.String(required=False, description="MXN | USD"),
        "status": fields.Integer(required=False, description="0 abierto · 1 completo (2 solo por /cancel). El back lo recalcula al entrar/salir remisiones", example=1),
    },
)

delivery_control_fields_model = api.model(
    "DeliveryControlFields",
    {
        "id_control": fields.Integer(required=True, description="ID del control", example=3),
        "custom_fields": fields.List(fields.Nested(balance_control_custom_field_model), required=True, description="Lista COMPLETA (reemplaza; las llaves quitadas se limpian de las remisiones)"),
    },
)

delivery_control_values_model = api.model(
    "DeliveryControlValues",
    {
        "id_control": fields.Integer(required=True, description="ID del control (activo)", example=3),
        "id_remission": fields.Integer(required=True, description="Remisión ligada al control", example=71),
        "values": fields.Raw(required=True, description="{key: valor} de las columnas dinámicas del control; se coerciona por value_type; null/'' vacía", example={"guia_embarque": "GE-1123", "entrega_parcial": True}),
    },
)

delivery_control_remissions_model = api.model(
    "DeliveryControlRemissions",
    {
        "id_control": fields.Integer(required=True, description="ID del control (activo)", example=3),
        "add": fields.List(fields.Integer, required=False, description="Remisiones a ligar (mismo cliente; en otro control activo -> 400)", example=[73]),
        "remove": fields.List(fields.Integer, required=False, description="Remisiones a retirar (deben estar en este control)", example=[71]),
    },
)

delivery_control_cancel_model = api.model(
    "DeliveryControlCancel",
    {
        "id_control": fields.Integer(required=True, description="ID del control a cancelar (suave: status 2)", example=3),
        "comment": fields.String(required=False, description="Motivo", example="Creado por error"),
    },
)


# --- WTForms ------------------------------------------------------------------
class DeliveryControlPostForm(Form):
    quotation_id = IntegerField("quotation_id", [InputRequired(message="quotation_id requerido")])
    title = StringField("title", [], default="")
    client_po_number = StringField("client_po_number", [], default="")
    currency = StringField("currency", [AnyOf(("",) + CURRENCIES, message="currency debe ser MXN o USD")], default="")
    remissions = FieldList(IntegerField(validators=[]), "remissions", default=[])
    custom_fields = FieldList(FormField(BalanceControlCustomFieldForm), "custom_fields", default=[])


class DeliveryControlPutForm(Form):
    id_control = IntegerField("id_control", [InputRequired(message="id_control requerido")])
    # "" / None = no viene (update parcial). status None = no viene.
    title = StringField("title", [], default=None)
    client_po_number = StringField("client_po_number", [], default=None)
    currency = StringField("currency", [AnyOf(("", None) + CURRENCIES, message="currency debe ser MXN o USD")], default=None)
    status = IntegerField("status", [], default=None)


class DeliveryControlFieldsForm(Form):
    id_control = IntegerField("id_control", [InputRequired(message="id_control requerido")])
    custom_fields = FieldList(FormField(BalanceControlCustomFieldForm), "custom_fields", default=[])


class DeliveryControlValuesForm(Form):
    # `values` es un dict libre: se lee del JSON crudo en el midleware.
    id_control = IntegerField("id_control", [InputRequired(message="id_control requerido")])
    id_remission = IntegerField("id_remission", [InputRequired(message="id_remission requerido")])


class DeliveryControlRemissionsForm(Form):
    id_control = IntegerField("id_control", [InputRequired(message="id_control requerido")])
    add = FieldList(IntegerField(validators=[]), "add", default=[])
    remove = FieldList(IntegerField(validators=[]), "remove", default=[])


class DeliveryControlCancelForm(Form):
    id_control = IntegerField("id_control", [InputRequired(message="id_control requerido")])
    comment = StringField("comment", [], default="")
