# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 19/oct./2026  at 12:00 $"

from flask_restx import fields
from wtforms import FloatField, FormField, StringField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import IntegerField
from wtforms.form import Form
from wtforms.validators import InputRequired

from static.Models.api_contracts_models import ProductsPutQuotationForm, products_quotation_put_model
from static.constants import api

# =====================================================================
# Control de licitaciones FO-PRE-04 (docs/tenders_control.md)
# Ruta base: /GUI/api/v1/admin/presales/tender*
# Doble capa: api.model (swagger) + WTForms (solo tipos). Las reglas
# (obligatorios, catálogos, fechas, OC/contrato solo con status 1) las valida
# el midleware sobre el JSON crudo: el PUT es parcial y necesita saber qué
# llaves vinieron, y 0 es un valor válido de status/scope (InputRequired lo
# trataría como vacío).
# =====================================================================

TENDER_STATUS_DOC = "0 en espera, 1 asignada, 2 no asignada, 3 cancelada"
TENDER_SCOPE_DOC = "0 suministro, 1 instalación, 2 mantenimiento, 3 suministro e instalación, 4 suministro, instalación y mantenimiento"

_tender_fields = {
    "tender_number": fields.String(description="Número de licitación (1-60, único global)", example="LIC-2026-001"),
    "client_id": fields.Integer(description="customers_amc.id_customer", example=4),
    "description": fields.String(example="Cableado de nave 3"),
    "scope": fields.Integer(description=TENDER_SCOPE_DOC, example=3),
    "buyer_user": fields.String(description="Usuario comprador (persona del cliente)", example="Ana Pérez"),
    "field_user": fields.String(description="Usuario de campo (persona del cliente)", example=None),
    "invitation_date": fields.String(description="YYYY-MM-DD", example="2026-10-01"),
    "closing_date": fields.String(description="YYYY-MM-DD, >= invitation_date", example="2026-10-15"),
    "amount_usd": fields.Float(description="Monto ofertado USD (>= 0 o null)", example=None),
    "amount_mxn": fields.Float(description="Monto ofertado MXN (>= 0 o null)", example=185000),
    "status": fields.Integer(description=TENDER_STATUS_DOC, example=0),
    "po_number": fields.String(description="Orden de compra; solo con status 1", example=None),
    "response_date": fields.String(description="YYYY-MM-DD o null", example=None),
    "submitted_date": fields.String(description="YYYY-MM-DD o null, >= invitation_date", example=None),
    "contract_id": fields.Integer(description="Contrato ligado; solo con status 1", example=None),
    "currency": fields.String(description="Moneda de las partidas (MXN | USD); vive en la cotización interna", example="MXN"),
}

tender_post_model = api.model(
    "TenderPost",
    {
        **_tender_fields,
        "tender_number": fields.String(required=True, description="Número de licitación (1-60, único global)", example="LIC-2026-001"),
        "client_id": fields.Integer(required=True, description="customers_amc.id_customer", example=4),
        "description": fields.String(required=True, example="Cableado de nave 3"),
        "scope": fields.Integer(required=True, description=TENDER_SCOPE_DOC, example=3),
        "invitation_date": fields.String(required=True, description="YYYY-MM-DD", example="2026-10-01"),
        "closing_date": fields.String(required=True, description="YYYY-MM-DD, >= invitation_date", example="2026-10-15"),
    },
)

tender_put_model = api.model(
    "TenderPut",
    {
        "id_tender": fields.Integer(required=True, example=1),
        **_tender_fields,
    },
)

tender_items_model = api.model(
    "TenderItems",
    {
        "id_tender": fields.Integer(required=True, example=1),
        "products": fields.List(
            fields.Nested(products_quotation_put_model),
            description="Mismo shape que products de PUT /quotation (qa_item_id 0/null = crear, is_erased 1 = borrar)",
        ),
    },
)


# --- WTForms ------------------------------------------------------------------
class _TenderFieldsForm(Form):
    # Todo opcional y sin default: el midleware decide con el JSON crudo.
    tender_number = StringField("tender_number", [])
    client_id = IntegerField("client_id", [], default=None)
    description = StringField("description", [])
    scope = IntegerField("scope", [], default=None)
    buyer_user = StringField("buyer_user", [])
    field_user = StringField("field_user", [])
    invitation_date = StringField("invitation_date", [])
    closing_date = StringField("closing_date", [])
    amount_usd = FloatField("amount_usd", [], default=None)
    amount_mxn = FloatField("amount_mxn", [], default=None)
    status = IntegerField("status", [], default=None)
    po_number = StringField("po_number", [])
    response_date = StringField("response_date", [])
    submitted_date = StringField("submitted_date", [])
    contract_id = IntegerField("contract_id", [], default=None)
    currency = StringField("currency", [])


class TenderPostForm(_TenderFieldsForm):
    pass


class TenderPutForm(_TenderFieldsForm):
    id_tender = IntegerField("id_tender", [InputRequired(message="id_tender requerido")])


class TenderItemsForm(Form):
    id_tender = IntegerField("id_tender", [InputRequired(message="id_tender requerido")])
    products = FieldList(FormField(ProductsPutQuotationForm, "products"))
