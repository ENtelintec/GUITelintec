# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct./2026  at 21:00 $"

"""Cotizaciones CISCO (FO-PRE-02): formas y modelos de /quotation/cisco/*.
Ver docs/cotizaciones_cisco.md. La cabecera hereda la de preventa y agrega
concept (obligatorio) y currency (obligatoria); las partidas llevan item texto,
n_parte, smart_account, service_months y delivery_time en vez de partida/udm.
"""

from flask_restx import fields
from wtforms import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import FloatField, IntegerField
from wtforms.fields.simple import BooleanField, StringField
from wtforms.form import Form
from wtforms.validators import AnyOf, InputRequired

from static.constants import api
from static.Models.api_contracts_models import (
    QUOTATION_CURRENCIES,
    MetadataQuotationForm,
    metadata_quotation_model,
)

QUOTATION_FORMAT_CISCO = "cisco"

metadata_quotation_cisco_model = api.inherit(
    "MetadataQuotationCisco",
    metadata_quotation_model,
    {
        "concept": fields.String(required=True, description="Concepto de la cotización (FO-PRE-02)", example="Switches de acceso"),
        "currency": fields.String(required=True, description="MXN | USD", example="USD"),
        "delivery_time": fields.String(
            required=False, description="Tiempo de entrega general (comentario 2 del formato, texto)", example="4 a 6 semanas"
        ),
        "format": fields.String(required=False, description="Lo pone el back: siempre cisco", example="cisco"),
    },
)

products_quotation_cisco_model = api.model(
    "ProductsQuotationCisco",
    {
        "qa_item_id": fields.Integer(required=False, description="id del item; null/0 en el POST o para crear en el PUT", example=900),
        "item": fields.String(
            required=True, description="ITEM del formato: entero o con un nivel decimal (1, 1.1, 2); único en la cotización", example="1.1"
        ),
        "n_parte": fields.String(required=True, description="Número de parte", example="C9300-48P-E"),
        "smart_account": fields.Boolean(required=False, description="Smart account obligatorio", example=False),
        "description": fields.String(required=True, description="Descripción", example="Catalyst 9300 48 puertos PoE+"),
        "service_months": fields.Integer(required=False, description="Duración del servicio en meses (> 0) o null", example=36),
        "delivery_time": fields.String(required=False, description="Tiempo de entrega de la partida (texto)", example="6 semanas"),
        "quantity": fields.Integer(required=True, description="Cantidad (> 0)", example=2),
        "price_unit": fields.Float(required=True, description="Precio unitario sin IVA (>= 0)", example=5120.0),
        "udm": fields.String(required=False, description="Unidad; CISCO no la usa (se guarda PZA si viene vacía)", example=""),
        "delivery_date": fields.String(
            required=False, description="Fecha de entrega de la partida (YYYY-MM-DD, opcional; <= due_date si ya es OCD)", example="2026-12-01"
        ),
        "is_erased": fields.Integer(required=False, description="Solo PUT: 1 borra la partida", example=0),
    },
)

quotation_cisco_model_insert = api.model(
    "QuotationCiscoInsert",
    {
        "metadata": fields.Nested(metadata_quotation_cisco_model, required=True),
        "products": fields.List(fields.Nested(products_quotation_cisco_model), required=True),
    },
)

quotation_cisco_model_update = api.model(
    "QuotationCiscoUpdate",
    {
        "id": fields.Integer(required=True, description="id de la cotización CISCO", example=31),
        "metadata": fields.Nested(metadata_quotation_cisco_model, required=True),
        "products": fields.List(
            fields.Nested(products_quotation_cisco_model),
            required=True,
            description="Upsert por qa_item_id: con id actualiza, sin id crea, is_erased 1 borra",
        ),
    },
)


class MetadataQuotationCiscoForm(MetadataQuotationForm):
    concept = StringField("concept", validators=[InputRequired()])
    currency = StringField("currency", [AnyOf(QUOTATION_CURRENCIES, message="currency debe ser MXN o USD")])


class ProductsQuotationCiscoForm(Form):
    qa_item_id = IntegerField("qa_item_id", validators=[], default=0)
    item = StringField("item", validators=[InputRequired()])
    n_parte = StringField("n_parte", validators=[InputRequired()])
    smart_account = BooleanField("smart_account", validators=[], default=False)
    description = StringField("description", validators=[InputRequired()])
    service_months = IntegerField("service_months", validators=[], default=None)
    delivery_time = StringField("delivery_time", validators=[], default="")
    # quantity sin InputRequired: 0 lo rechaza el midleware en la lista de validaciones.
    quantity = IntegerField("quantity", validators=[], default=0)
    price_unit = FloatField("price_unit", validators=[], default=0.0)
    udm = StringField("udm", validators=[], default="")
    delivery_date = StringField("delivery_date", validators=[], default="")
    is_erased = IntegerField("is_erased", validators=[], default=0)


class QuotationCiscoInsertForm(Form):
    metadata = FormField(MetadataQuotationCiscoForm, "metadata")
    products = FieldList(FormField(ProductsQuotationCiscoForm, "products"))


class QuotationCiscoUpdateForm(Form):
    id = IntegerField("id", validators=[InputRequired(message="Invalid id or 0 not acepted")])
    metadata = FormField(MetadataQuotationCiscoForm, "metadata")
    products = FieldList(FormField(ProductsQuotationCiscoForm, "products"))
