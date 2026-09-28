# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/sep./2026  at 19:30 $"

from flask_restx import fields
from wtforms import BooleanField, FloatField
from wtforms.fields.numeric import IntegerField
from wtforms.form import Form
from wtforms.validators import InputRequired

from static.constants import api

# =====================================================================
# Análisis de costos por item cotizado (docs/quotation_cost_analysis.md)
# Ruta: PUT /GUI/api/v1/admin/presales/quotation/costAnalysis
# El form valida la cabecera; `items[]` (con `cost` que puede ser null) se
# lee del JSON crudo y lo valida el midleware campo por campo.
# =====================================================================

quotation_cost_model = api.model(
    "QuotationItemCost",
    {
        "currency": fields.String(required=False, description="Moneda del costo: MXN (default) | USD", example="USD"),
        "unit_cost": fields.Float(required=True, description="Precio unitario sin ganancia, en `currency`", example=0.55),
        "exchange_rate": fields.Float(required=False, description="Tipo de cambio de este item (default: el de la cabecera; obligatorio si currency = USD)", example=18.25),
        "profit_pct": fields.Float(required=False, description="Porcentaje de ganancia (30 = 30 %); default 0", example=30),
        "delivery_time": fields.String(required=False, description="Tiempo de entrega para el cliente", example="2 semanas"),
        "service_months": fields.Integer(required=False, description="CISCO: duración del servicio (meses)", example=12),
        "smart_account": fields.Boolean(required=False, description="CISCO: smart account obligatorio", example=True),
    },
)

quotation_supplier_quote_model = api.model(
    "QuotationItemSupplierQuote",
    {
        "position": fields.Integer(required=False, description="1 = Proveedor 1, 2 = Proveedor 2… (default: orden en la lista)", example=1),
        "supplier_id": fields.Integer(required=False, description="suppliers_amc.id_supplier (opcional)", example=12),
        "supplier_name": fields.String(required=False, description="Nombre libre si no está en catálogo", example="Distribuidor X"),
        "unit_price": fields.Float(required=False, example=0.55),
        "currency": fields.String(required=False, description="MXN | USD", example="USD"),
        "delivery_time": fields.String(required=False, example="10 días"),
        "comments": fields.String(required=False, example="Precio válido 15 días"),
        "is_selected": fields.Boolean(required=False, description="El proveedor elegido (a lo más uno por item)", example=True),
    },
)

quotation_cost_item_model = api.model(
    "QuotationCostAnalysisItem",
    {
        "id": fields.Integer(required=True, description="quotation_items.id (qa_item_id en GET /quotation)", example=900),
        "cost": fields.Nested(quotation_cost_model, required=False, allow_null=True, description="null = borrar el análisis y la comparativa del item"),
        "suppliers": fields.List(fields.Nested(quotation_supplier_quote_model), required=False, description="Lista COMPLETA (reemplaza la comparativa del item)"),
    },
)

quotation_cost_analysis_model = api.model(
    "QuotationCostAnalysis",
    {
        "id_quotation": fields.Integer(required=True, example=51),
        "exchange_rate": fields.Float(required=False, description="Tipo de cambio USD→MXN de la cabecera (se guarda en metadata.exchange_rate); cada item puede traer el suyo", example=18.25),
        "apply_prices": fields.Boolean(required=False, description="true -> escribe unit_price_profit en quotation_items.price_unit de los items enviados", example=False),
        "items": fields.List(fields.Nested(quotation_cost_item_model), required=True),
    },
)


class QuotationCostAnalysisForm(Form):
    id_quotation = IntegerField("id_quotation", [InputRequired(message="id_quotation requerido")])
    exchange_rate = FloatField("exchange_rate", [], default=None)
    apply_prices = BooleanField("apply_prices", [], default=False)
