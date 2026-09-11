# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 11/sep./2026  at 12:00 $"

from flask_restx import fields
from wtforms import FloatField, FormField, StringField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import IntegerField
from wtforms.form import Form
from wtforms.validators import AnyOf, InputRequired

from static.constants import api

# =====================================================================
# Control de saldos (Cobranza) — cabecera por contrato
# Ruta base: /GUI/api/v1/admin/collections/balanceControl
# Doble capa: api.model (swagger) + WTForms (validación runtime).
# Los campos PROPIOS DEL FORMATO (requires_hes, site, quotation_number, ...)
# NO se declaran aquí: son dinámicos (iso_formats.config.header_fields) y el
# midleware los lee del JSON crudo de `metadata`, validándolos contra el
# formato. Una llave que el formato no declare responde 400 (nada se
# descarta en silencio). Ver Docs/control_saldos_cabecera.md.
# =====================================================================

VALUE_TYPES = ("text", "number", "date", "boolean")

balance_control_custom_field_model = api.model(
    "BalanceControlCustomField",
    {
        "key": fields.String(required=True, description="Llave snake_case, única en el control y sin chocar con columnas del formato", example="numero_estimacion"),
        "label": fields.String(required=True, description="Encabezado de la columna", example="Número de estimación"),
        "value_type": fields.String(required=True, description="text | number | date | boolean", example="number"),
        "comment": fields.String(required=False, description="Para qué sirve la columna", example="Estimación del contrato"),
    },
)

_bc_base_fields = {
    "month_period": fields.String(required=False, description="Periodo YYYY-MM (informativo)", example="2026-08"),
    "currency": fields.String(required=False, description="MXN | USD (default MXN)", example="MXN"),
    "contract_number": fields.String(required=False, description="Nº de contrato marco (default: contracts.code)", example="6700373484"),
    "pedido_exiros": fields.String(required=False, description="Pedido EXIROS", example="3716578048"),
    "start_date": fields.String(required=False, description="Inicio de vigencia YYYY-MM-DD", example="2026-03-09"),
    "end_date": fields.String(required=False, description="Fin de vigencia YYYY-MM-DD", example="2027-03-08"),
    "plant": fields.String(required=False, description="Planta", example="San Nico"),
    "coordinator": fields.String(required=False, description="Coordinador responsable", example="Nombre del coordinador"),
    "contract_object": fields.String(required=False, description="Objeto del contrato", example="Cableado estructurado y accesorios"),
}

balance_control_metadata_post_model = api.model(
    "BalanceControlMetadataPost",
    {
        "contract_id": fields.Integer(required=True, description="Contrato (sql_telintec_mod_admin.contracts.id)", example=9),
        "format_id": fields.Integer(required=True, description="Formato FO-CXC (iso_formats.id, ver /balanceControl/catalogs)", example=13),
        "contracted_amount": fields.Float(required=False, description="Monto contratado inicial (>= 0). Solo aquí; después se mueve con movimientos de saldo", example=1250000.0),
        **_bc_base_fields,
    },
)

balance_control_post_model = api.model(
    "BalanceControlPost",
    {
        "metadata": fields.Nested(balance_control_metadata_post_model, required=True, description="Cabecera. Los campos propios del formato van planos aquí mismo (p.ej. quotation_number, requires_hes)"),
        "remissions": fields.List(fields.Integer, required=False, description="Ids de remisiones a validar/adoptar (opcional)", example=[341, 342]),
        "custom_fields": fields.List(fields.Nested(balance_control_custom_field_model), required=False, description="Columnas dinámicas (orden = orden en la tabla)"),
    },
)

balance_control_metadata_put_model = api.model(
    "BalanceControlMetadataPut",
    {
        "id_control": fields.Integer(required=True, description="ID del control", example=1),
        **_bc_base_fields,
    },
)

balance_control_put_model = api.model(
    "BalanceControlPut",
    {
        "metadata": fields.Nested(balance_control_metadata_put_model, required=True, description="Update PARCIAL: solo se escribe lo presente; contracted_amount/contract_id/format_id → 400"),
    },
)

balance_control_fields_model = api.model(
    "BalanceControlFields",
    {
        "id_control": fields.Integer(required=True, description="ID del control", example=1),
        "custom_fields": fields.List(fields.Nested(balance_control_custom_field_model), required=True, description="Lista COMPLETA (reemplaza la anterior; las llaves quitadas se limpian de las remisiones)"),
    },
)

balance_control_cancel_model = api.model(
    "BalanceControlCancel",
    {
        "id_control": fields.Integer(required=True, description="ID del control a cancelar (suave)", example=1),
        "comment": fields.String(required=False, description="Motivo", example="Creado por error"),
    },
)


# --- WTForms ------------------------------------------------------------------
class BalanceControlCustomFieldForm(Form):
    key = StringField("key", [InputRequired()])
    label = StringField("label", [InputRequired()])
    value_type = StringField("value_type", [InputRequired(), AnyOf(VALUE_TYPES, message="value_type fuera de text|number|date|boolean")])
    comment = StringField("comment", [], default="")


class _BalanceControlBaseForm(Form):
    month_period = StringField("month_period", [], default="")
    currency = StringField("currency", [], default="MXN")
    contract_number = StringField("contract_number", [], default="")
    pedido_exiros = StringField("pedido_exiros", [], default="")
    start_date = StringField("start_date", [], default="")
    end_date = StringField("end_date", [], default="")
    plant = StringField("plant", [], default="")
    coordinator = StringField("coordinator", [], default="")
    contract_object = StringField("contract_object", [], default="")


class MetadataBalanceControlPostForm(_BalanceControlBaseForm):
    contract_id = IntegerField("contract_id", [InputRequired(message="contract_id requerido")])
    format_id = IntegerField("format_id", [InputRequired(message="format_id requerido")])
    # null de JSON llega como None (wtforms_json no aplica el default): el midleware lo trata como 0.
    contracted_amount = FloatField("contracted_amount", [], default=0.0)


class BalanceControlPostForm(Form):
    metadata = FormField(MetadataBalanceControlPostForm, "metadata")
    remissions = FieldList(IntegerField(validators=[]), "remissions", default=[])
    custom_fields = FieldList(FormField(BalanceControlCustomFieldForm), "custom_fields", default=[])


class MetadataBalanceControlPutForm(_BalanceControlBaseForm):
    id_control = IntegerField("id_control", [], default=None)
    id = IntegerField("id", [], default=None)


class BalanceControlPutForm(Form):
    metadata = FormField(MetadataBalanceControlPutForm, "metadata")


class BalanceControlFieldsForm(Form):
    id_control = IntegerField("id_control", [InputRequired(message="id_control requerido")])
    custom_fields = FieldList(FormField(BalanceControlCustomFieldForm), "custom_fields", default=[])


class BalanceControlCancelForm(Form):
    id_control = IntegerField("id_control", [InputRequired(message="id_control requerido")])
    comment = StringField("comment", [], default="")
