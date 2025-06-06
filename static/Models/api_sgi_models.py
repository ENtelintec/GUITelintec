# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"

from wtforms.fields.form import FormField

from static.constants import api
from flask_restx import fields
from wtforms.validators import InputRequired
from wtforms import StringField, FloatField, IntegerField, FieldList
from wtforms.form import Form


# voucher_model = api.model(
#     "Voucher",
#     {
#         "type": fields.Integer(
#             required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
#         ),
#         "date": fields.String(required=True, description="Fecha del voucher"),
#         "user": fields.Integer(required=True, description="ID del usuario"),
#         "contract": fields.Integer(required=True, description="ID del contrato"),
#     },
# )

voucher_items_post_model = api.model(
    "VoucherItemsPost",
    {
        "id_voucher": fields.Integer(
            required=True, description="ID del voucher asociado"
        ),
        "quantity": fields.Integer(required=True, description="Cantidad del ítem"),
        "unit": fields.String(required=True, description="Unidad de medida"),
        "description": fields.String(required=True, description="Descripción del ítem"),
        "observations": fields.String(description="Observaciones adicionales"),
        "id_inventory": fields.Integer(
            required=True, description="ID del inventario asociado"
        ),
    },
)

voucher_items_put_model = api.model(
    "VoucherItemsPut",
    {
        "id_item": fields.Integer(required=True, description="ID del voucher asociado"),
        "quantity": fields.Integer(required=True, description="Cantidad del ítem"),
        "unit": fields.String(required=True, description="Unidad de medida"),
        "description": fields.String(required=True, description="Descripción del ítem"),
        "observations": fields.String(description="Observaciones adicionales"),
        "id_inventory": fields.Integer(
            required=True, description="ID del inventario asociado"
        ),
    },
)

voucher_tools_post_model = api.model(
    "VoucherToolsPost",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "id_voucher_general": fields.Integer(
            required=False, description="ID del voucher general for update"
        ),
        "position": fields.String(required=True, description="Puesto del solicitante"),
        "type_transaction": fields.Integer(
            default=0, description="Tipo de transacción"
        ),
        "superior": fields.Integer(required=True, description="ID del superior"),
        "storage_emp": fields.Integer(
            required=True, description="ID del encargado de almacenamiento"
        ),
        "user_state": fields.Integer(default=0, description="Estado del usuario"),
        "superior_state": fields.Integer(default=0, description="Estado del superior"),
        "items": fields.List(fields.Nested(voucher_items_post_model)),
    },
)


voucher_tools_put_model = api.model(
    "VoucherToolsPut",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "id_voucher_general": fields.Integer(
            required=False, description="ID del voucher general for update"
        ),
        "position": fields.String(required=True, description="Puesto del solicitante"),
        "type_transaction": fields.Integer(
            default=0, description="Tipo de transacción"
        ),
        "superior": fields.Integer(required=True, description="ID del superior"),
        "storage_emp": fields.Integer(
            required=True, description="ID del encargado de almacenamiento"
        ),
        "user_state": fields.Integer(default=0, description="Estado del usuario"),
        "superior_state": fields.Integer(default=0, description="Estado del superior"),
        "items": fields.List(fields.Nested(voucher_items_put_model)),
    },
)


voucher_safety_post_model = api.model(
    "VoucherSafetyPost",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "id_voucher_general": fields.Integer(
            required=False, description="ID del voucher general for update"
        ),
        "superior": fields.Integer(required=True, description="ID del superior"),
        "epp_emp": fields.Integer(
            required=True, description="ID del empleado que recibe el EPP"
        ),
        "epp_state": fields.Integer(default=0, description="Estado del EPP"),
        "superior_state": fields.Integer(default=0, description="Estado del superior"),
        "motive": fields.Integer(default=0, description="Motivo del voucher"),
        "items": fields.List(fields.Nested(voucher_items_post_model)),
    },
)


voucher_safety_put_model = api.model(
    "VoucherSafetyPut",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "id_voucher_general": fields.Integer(
            required=False, description="ID del voucher general for update"
        ),
        "superior": fields.Integer(required=True, description="ID del superior"),
        "epp_emp": fields.Integer(
            required=True, description="ID del empleado que recibe el EPP"
        ),
        "epp_state": fields.Integer(default=0, description="Estado del EPP"),
        "superior_state": fields.Integer(default=0, description="Estado del superior"),
        "motive": fields.Integer(default=0, description="Motivo del voucher"),
        "items": fields.List(fields.Nested(voucher_items_put_model)),
    },
)


class ItemsVoucherPostForm(Form):
    id_voucher = IntegerField("id", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit = StringField("unit", [InputRequired()])
    description = StringField("description", [InputRequired()])
    observations = StringField("observations", [])
    id_inventory = IntegerField("id_inventory", [InputRequired()])


class ItemsVoucherPutForm(Form):
    id_item = IntegerField("id_item", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit = StringField("unit", [InputRequired()])
    description = StringField("description", [InputRequired()])
    observations = StringField("observations", [])
    id_inventory = IntegerField("id_inventory", [InputRequired()])


class VoucherToolsFormPost(Form):
    type = StringField("type", [InputRequired()])
    user = IntegerField("user", [InputRequired()])
    contract = IntegerField("contract", [InputRequired()])
    position = StringField("position", [InputRequired()])
    type_transaction = IntegerField("type_transaction", [InputRequired()])
    superior = IntegerField("superior", [InputRequired()])
    storage_emp = IntegerField("storage_emp", [InputRequired()])
    user_state = IntegerField("user_state", [InputRequired()])
    superior_state = IntegerField("superior_state", [InputRequired()])
    items = FieldList(FormField(ItemsVoucherPostForm, "items"))


class VoucherToolsFormPut(Form):
    id_voucher_general = IntegerField("id_voucher_general", [InputRequired()])
    type = StringField("type", [InputRequired()])
    user = IntegerField("user", [InputRequired()])
    contract = IntegerField("contract", [InputRequired()])
    superior = IntegerField("superior", [InputRequired()])
    storage_emp = IntegerField("storage_emp", [InputRequired()])
    user_state = IntegerField("user_state", [InputRequired()])
    superior_state = IntegerField("superior_state", [InputRequired()])
    items = FieldList(FormField(ItemsVoucherPutForm, "items"))


class VoucherSafetyFormPost(Form):
    type = StringField("type", [InputRequired()])
    user = IntegerField("user", [InputRequired()])
    contract = IntegerField("contract", [InputRequired()])
    superior = IntegerField("superior", [InputRequired()])
    epp_emp = IntegerField("epp_emp", [InputRequired()])
    epp_state = IntegerField("epp_state", [InputRequired()])
    superior_state = IntegerField("superior_state", [InputRequired()])
    motive = IntegerField("motive", [InputRequired()])
    items = FieldList(FormField(ItemsVoucherPostForm, "items"))


class VoucherSafetyFormPut(Form):
    id_voucher_general = IntegerField("id_voucher_general", [InputRequired()])
    type = StringField("type", [InputRequired()])
    user = IntegerField("user", [InputRequired()])
    contract = IntegerField("contract", [InputRequired()])
    superior = IntegerField("superior", [InputRequired()])
    epp_emp = IntegerField("epp_emp", [InputRequired()])
    epp_state = IntegerField("epp_state", [InputRequired()])
    superior_state = IntegerField("superior_state", [InputRequired()])
    motive = IntegerField("motive", [InputRequired()])
    items = FieldList(FormField(ItemsVoucherPutForm, "items"))
