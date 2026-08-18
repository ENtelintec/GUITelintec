# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 24/jul./2026  at 12:00 $"

from flask_restx import fields
from wtforms import FloatField, StringField
from wtforms.fields.numeric import IntegerField
from wtforms.form import Form

from static.constants import api

# =====================================================================
# Gestión de Compras (FO-COM-01 R3)
# Ruta base: /GUI/api/v1/admin/collections/purchaseManagement
# Doble capa: api.model (swagger/docs) + WTForms Form (validación runtime).
# Al agregar un campo, actualizar AMBOS. Casi todo es opcional: el
# seguimiento es flojo (ver Docs/gestion_de_compras.md).
# =====================================================================

# --- Campos compartidos (api.model) ------------------------------------------
_pm_common_fields = {
    "request_date": fields.String(required=False, description="FECHA DE SOLICITUD (YYYY-MM-DD)", example="2026-07-20"),
    "description": fields.String(required=False, description="DESCRIPCION", example="Compra de taladro"),
    "classification": fields.Integer(required=False, description="CLASIFICACIÓN 0..6", example=0),
    "supplier_id": fields.Integer(required=False, description="FK suppliers_amc (nullable)", example=12),
    "client_id": fields.Integer(required=False, description="FK customers_amc (nullable)", example=3),
    "contract_id": fields.Integer(required=False, description="FK contracts (nullable)", example=8),
    "po_id": fields.Integer(required=False, description="FK purchase_orders (nullable)", example=44),
    "amount_usd": fields.Float(required=False, description="MONTO USD", example=120.5),
    "amount_mxn": fields.Float(required=False, description="MONTO MXN", example=2100.0),
    "status": fields.Integer(required=False, description="ESTATUS 0..4 (default 0=PENDIENTE)", example=0),
    "payment_date": fields.String(required=False, description="FECHA DE PAGO (YYYY-MM-DD)", example="2026-07-25"),
    "approved": fields.Integer(required=False, description="APROBACIÓN DE GERENCIA (0/1)", example=0),
    "approval_date": fields.String(required=False, description="FECHA DE APROBACIÓN (YYYY-MM-DD)", example="2026-07-24"),
    "comments": fields.String(required=False, description="COMENTARIOS", example="Urgente para obra"),
    "debt_type": fields.Integer(required=False, description="DEUDA/GASTO/INVERSION 0..2", example=1),
    "profit_percentage": fields.Float(required=False, description="PORCENTAJE DE GANANCIA (tal cual)", example=15.0),
    "cost_ternium_iva": fields.Float(required=False, description="COSTO A TERNIUM CON IVA", example=2436.0),
    "profit": fields.Float(required=False, description="GANANCIA", example=336.0),
    # extra_info (texto crudo cuando no hay FK / campos sueltos del formato)
    "supplier_text": fields.String(required=False, description="PROVEEDOR (texto, si no hay FK)", example="Ferretería X"),
    "client_text": fields.String(required=False, description="CLIENTE (texto, si no hay FK)", example="Ternium"),
    "contract_text": fields.String(required=False, description="CONTRATO (texto, si no hay FK)"),
    "department_text": fields.String(required=False, description="DEPARTAMENTO (texto)", example="Operaciones"),
    "requester_text": fields.String(required=False, description="SOLICITANTE (texto)", example="Juan Pérez"),
    "invoice_number": fields.String(required=False, description="NRO DE FACTURA (texto)", example="A-1234"),
    "income_date": fields.String(required=False, description="FECHA DE INGRESO (texto)"),
    "bank_deposit": fields.String(required=False, description="DEPOSITO BANCO BASE (texto)"),
}

purchase_management_post_model = api.model("PurchaseManagementPost", dict(_pm_common_fields))

purchase_management_put_model = api.model(
    "PurchaseManagementPut",
    {"id_pm": fields.Integer(required=True, description="ID del registro", example=1), **_pm_common_fields},
)

purchase_management_delete_model = api.model(
    "PurchaseManagementDelete",
    {"id_pm": fields.Integer(required=True, description="ID del registro a eliminar", example=1)},
)

purchase_management_cancel_model = api.model(
    "PurchaseManagementCancel",
    {
        "id_pm": fields.Integer(required=True, description="ID del registro a cancelar", example=1),
        "comment": fields.String(required=False, description="Motivo de la cancelación"),
    },
)


# --- WTForms (validación real) ------------------------------------------------
class _PurchaseManagementBaseForm(Form):
    request_date = StringField("request_date", [], default=None)
    description = StringField("description", [], default=None)
    classification = IntegerField("classification", [], default=None)
    supplier_id = IntegerField("supplier_id", [], default=None)
    client_id = IntegerField("client_id", [], default=None)
    contract_id = IntegerField("contract_id", [], default=None)
    po_id = IntegerField("po_id", [], default=None)
    amount_usd = FloatField("amount_usd", [], default=None)
    amount_mxn = FloatField("amount_mxn", [], default=None)
    status = IntegerField("status", [], default=0)
    payment_date = StringField("payment_date", [], default=None)
    approved = IntegerField("approved", [], default=0)
    approval_date = StringField("approval_date", [], default=None)
    comments = StringField("comments", [], default=None)
    debt_type = IntegerField("debt_type", [], default=None)
    profit_percentage = FloatField("profit_percentage", [], default=None)
    cost_ternium_iva = FloatField("cost_ternium_iva", [], default=None)
    profit = FloatField("profit", [], default=None)
    # extra_info
    supplier_text = StringField("supplier_text", [], default=None)
    client_text = StringField("client_text", [], default=None)
    contract_text = StringField("contract_text", [], default=None)
    department_text = StringField("department_text", [], default=None)
    requester_text = StringField("requester_text", [], default=None)
    invoice_number = StringField("invoice_number", [], default=None)
    income_date = StringField("income_date", [], default=None)
    bank_deposit = StringField("bank_deposit", [], default=None)


class PurchaseManagementPostForm(_PurchaseManagementBaseForm):
    pass


class PurchaseManagementPutForm(_PurchaseManagementBaseForm):
    id_pm = IntegerField("id_pm", [], default=None)
    id = IntegerField("id", [], default=None)


class PurchaseManagementDeleteForm(Form):
    id_pm = IntegerField("id_pm", [], default=None)
    id = IntegerField("id", [], default=None)


class PurchaseManagementCancelForm(Form):
    id_pm = IntegerField("id_pm", [], default=None)
    id = IntegerField("id", [], default=None)
    comment = StringField("comment", [], default=None)
