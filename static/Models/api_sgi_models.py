# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"

from wtforms.fields.datetime import DateTimeField
from wtforms.fields.form import FormField

from static.Models.api_models import datetime_filter
from static.constants import api
from flask_restx import fields
from wtforms.validators import InputRequired
from wtforms import StringField, FloatField, IntegerField, FieldList, validators
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
        "is_erased": fields.Integer(
            required=True, description="Indicador de eliminación", example=0
        ),
    },
)

voucher_history_model = api.model(
    "VoucherHistory",
    {
        "id_voucher": fields.Integer(
            required=False, description="ID de la subtabla de voucher"
        ),
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "timestamp": fields.String(required=True, description="Fecha del voucher"),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "comment": fields.String(required=True, description="Comentario del historial"),
    },
)

voucher_tools_post_model = api.model(
    "VoucherToolsPost",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "position": fields.String(required=True, description="Puesto del solicitante"),
        "type_transaction": fields.Integer(
            default=0, description="Tipo de transacción"
        ),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "superior": fields.Integer(required=True, description="ID del superior"),
        "storage_emp": fields.Integer(
            required=True, description="ID del encargado de almacenamiento"
        ),
        "designated_emp": fields.Integer(
            required=True, description="ID del empleado designado"
        ),
        "items": fields.List(fields.Nested(voucher_items_post_model)),
    },
)


voucher_tools_put_model = api.model(
    "VoucherToolsPut",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "id_voucher_general": fields.Integer(
            required=False, description="ID del voucher general for update"
        ),
        "position": fields.String(required=True, description="Puesto del solicitante"),
        "type_transaction": fields.Integer(
            default=0, description="Tipo de transacción"
        ),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "superior": fields.Integer(required=True, description="ID del superior"),
        "storage_emp": fields.Integer(
            required=True, description="ID del encargado de almacenamiento"
        ),
        "designated_emp": fields.Integer(
            required=True, description="ID del empleado designado"
        ),
        "user_state": fields.Integer(default=0, description="Estado del usuario"),
        "superior_state": fields.Integer(default=0, description="Estado del superior"),
        "storage_state": fields.Integer(
            default=0, description="Estado del encargado de almacenamiento"
        ),
        "items": fields.List(fields.Nested(voucher_items_put_model)),
        "history": fields.List(fields.Nested(voucher_history_model)),
    },
)


voucher_tools_status_put_model = api.model(
    "VoucherToolsStatusPut",
    {
        "id_voucher": fields.Integer(required=True, description="ID del voucher"),
        "user_state": fields.Integer(default=0, description="Estado del usuario"),
        "superior_state": fields.Integer(default=0, description="Estado del superior"),
        "storage_state": fields.Integer(
            default=0, description="Estado del encargado de almacenamiento"
        ),
        "history": fields.List(fields.Nested(voucher_history_model)),
    },
)


voucher_safety_post_model = api.model(
    "VoucherSafetyPost",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "motive": fields.Integer(default=0, description="Motivo del voucher"),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "epp_emp": fields.Integer(
            required=True, description="ID del empleado que recibe el EPP"
        ),
        "storage_emp": fields.Integer(
            required=True, description="ID del encargado de almacenamiento"
        ),
        "designated_emp": fields.Integer(
            required=True, description="ID del empleado designado"
        ),
        "items": fields.List(fields.Nested(voucher_items_post_model)),
    },
)


voucher_safety_put_model = api.model(
    "VoucherSafetyPut",
    {
        "type": fields.Integer(
            required=True, description="Tipo de voucher (0: Tools, 1: Safety)"
        ),
        "contract": fields.Integer(required=True, description="ID del contrato"),
        "id_voucher_general": fields.Integer(
            required=False, description="ID del voucher general for update"
        ),
        "motive": fields.Integer(default=0, description="Motivo del voucher"),
        "user": fields.Integer(required=True, description="ID del usuario"),
        "epp_emp": fields.Integer(
            required=True, description="ID del empleado que recibe el EPP"
        ),
        "storage_emp": fields.Integer(
            required=True, description="ID del encargado de almacenamiento"
        ),
        "designated_emp": fields.Integer(
            required=True, description="ID del empleado designado"
        ),
        "user_state": fields.Integer(default=0, description="Estado del usuario"),
        "epp_state": fields.Integer(default=0, description="Estado del EPP"),
        "storage_state": fields.Integer(
            default=0, description="Estado del encargado de almacenamiento"
        ),
        "items": fields.List(fields.Nested(voucher_items_put_model)),
    },
)


voucher_safety_status_put_model = api.model(
    "VoucherSafetyStatusPut",
    {
        "id_voucher": fields.Integer(required=True, description="ID del voucher"),
        "user_state": fields.Integer(default=0, description="Estado del usuario"),
        "epp_state": fields.Integer(default=0, description="Estado del EPP"),
        "storage_state": fields.Integer(
            default=0, description="Estado del encargado de almacenamiento"
        ),
        "history": fields.List(fields.Nested(voucher_history_model)),
    },
)


class ItemsVoucherPostForm(Form):
    id_voucher = IntegerField("id", [])
    quantity = FloatField("quantity", [InputRequired()])
    unit = StringField("unit", [InputRequired()])
    description = StringField("description", [InputRequired()])
    observations = StringField("observations", [])
    id_inventory = IntegerField("id_inventory", [InputRequired()])


class ItemsVoucherPutForm(Form):
    id_item = IntegerField(
        "id_item", [validators.number_range(min=-1, message="Invalid type")]
    )
    quantity = FloatField("quantity", [InputRequired()])
    unit = StringField("unit", [InputRequired()])
    description = StringField("description", [InputRequired()])
    observations = StringField("observations", [])
    id_inventory = IntegerField("id_inventory", [InputRequired()])
    is_erased = IntegerField("is_erased", [], default=0)


class VoucherHistoryForm(Form):
    id_voucher = IntegerField(
        "id_voucher", [validators.number_range(min=-1, message="Invalid id")]
    )
    type = IntegerField(
        "type", [validators.number_range(min=-1, message="Invalid type")]
    )
    timestamp = DateTimeField("timestamp", [InputRequired()], filters=[datetime_filter])
    user = IntegerField("user", [validators.number_range(min=-1, message="Invalid id")])
    comment = StringField("comment", [InputRequired()])


class VoucherToolsFormPost(Form):
    type = IntegerField(
        "type", [validators.number_range(min=-1, message="Invalid type")]
    )
    contract = IntegerField("contract", [InputRequired()])
    position = StringField("position", [InputRequired()])
    type_transaction = IntegerField("type_transaction", [InputRequired()])
    user = IntegerField("user", [InputRequired()])
    superior = IntegerField("superior", [InputRequired()])
    storage_emp = IntegerField("storage_emp", [InputRequired()])
    designated_emp = IntegerField("designated_emp", [InputRequired()])
    items = FieldList(FormField(ItemsVoucherPostForm, "items"))


class VoucherToolsFormPut(Form):
    id_voucher_general = IntegerField("id_voucher_general", [InputRequired()])
    type = IntegerField(
        "type", [validators.number_range(min=-1, message="Invalid type")]
    )
    contract = IntegerField("contract", [InputRequired()])
    user = IntegerField("user", [InputRequired()])
    superior = IntegerField("superior", [InputRequired()])
    storage_emp = IntegerField("storage_emp", [InputRequired()])
    designated_emp = IntegerField("designated_emp", [InputRequired()])
    user_state = IntegerField("user_state", [InputRequired()])
    superior_state = IntegerField("superior_state", [InputRequired()])
    storage_state = IntegerField("storage_state", [InputRequired()])
    items = FieldList(FormField(ItemsVoucherPutForm, "items"))
    history = FieldList(FormField(VoucherHistoryForm, "history"))
    position = StringField("position", validators=[], default="")
    type_transaction = IntegerField(
        "type_transaction",
        validators=[validators.number_range(min=-1, message="Invalid type")],
    )


class VoucherSafetyFormPost(Form):
    type = IntegerField(
        "type", [validators.number_range(min=-1, message="Invalid type")]
    )
    contract = IntegerField("contract", [InputRequired()])
    motive = IntegerField("motive", [InputRequired()])
    user = IntegerField("user", [InputRequired()])
    epp_emp = IntegerField("epp_emp", [InputRequired()])
    storage_emp = IntegerField("storage_emp", [InputRequired()])
    designated_emp = IntegerField("designated_emp", [InputRequired()])
    items = FieldList(FormField(ItemsVoucherPostForm, "items"))


class VoucherSafetyFormPut(Form):
    id_voucher_general = IntegerField("id_voucher_general", [InputRequired()])
    type = IntegerField(
        "type", [validators.number_range(min=-1, message="Invalid type")]
    )
    contract = IntegerField("contract", [InputRequired()])
    motive = IntegerField(
        "motive", [validators.number_range(min=-1, message="Invalid motive")]
    )
    user = IntegerField("user", [InputRequired()])
    epp_emp = IntegerField("epp_emp", [InputRequired()])
    storage_emp = IntegerField("storage_emp", [InputRequired()])
    designated_emp = IntegerField("designated_emp", [InputRequired()])
    user_state = IntegerField(
        "user_state",
        [validators.number_range(min=-1, message="Invalid state")],
        default=0,
    )
    epp_state = IntegerField(
        "epp_state",
        [validators.number_range(min=-1, message="Invalid state")],
        default=0,
    )
    storage_state = IntegerField(
        "storage_state",
        [validators.number_range(min=-1, message="Invalid state")],
        default=0,
    )
    items = FieldList(FormField(ItemsVoucherPutForm, "items"))
    history = FieldList(FormField(VoucherHistoryForm, "history"))


class VoucherToolsStatusFormPut(Form):
    id_voucher = IntegerField("id_voucher", [InputRequired()])
    user_state = IntegerField(
        "user_state", [validators.number_range(min=-1, message="Invalid id")]
    )
    superior_state = IntegerField(
        "superior_state", [validators.number_range(min=-1, message="Invalid id")]
    )
    storage_state = IntegerField(
        "storage_state", [validators.number_range(min=-1, message="Invalid id")]
    )
    history = FieldList(FormField(VoucherHistoryForm, "history"))


class VoucherSafetyStatusFormPut(Form):
    id_voucher = IntegerField("id_voucher", [InputRequired()])
    user_state = IntegerField(
        "user_state", [validators.number_range(min=-1, message="Invalid id")]
    )
    epp_state = IntegerField(
        "epp_state", [validators.number_range(min=-1, message="Invalid id")]
    )
    storage_state = IntegerField(
        "storage_state", [validators.number_range(min=-1, message="Invalid id")]
    )
    history = FieldList(FormField(VoucherHistoryForm, "history"))
