# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/sep./2026  at 10:00 $"

from flask_restx import fields
from wtforms import IntegerField, StringField
from wtforms.fields.numeric import FloatField
from wtforms.form import Form
from wtforms.validators import InputRequired, Optional

from static.constants import api

# =====================================================================
# Almacén multisede — lado SEDE (GUI/api/v1/sucursal, rs_Sucursal.py).
# Movimientos libres de la sede (F2). Doble capa: api.model (swagger) +
# WTForms (validación runtime). `id_warehouse` es opcional: si el usuario
# tiene un solo permiso Sucursal-<id>, se infiere. Ver docs/almacen_multisede_f2.md.
# =====================================================================

sucursal_movement_post_model = api.model(
    "SucursalMovementPost",
    {
        "id_warehouse": fields.Integer(required=False, description="Sede (opcional si el permiso es de una sola)", example=2),
        "id_product": fields.Integer(required=True, description="Producto del catálogo compartido", example=1),
        "movement_type": fields.String(required=True, description="entrada | salida", example="entrada"),
        "quantity": fields.Float(required=True, description="Cantidad > 0", example=10),
        "movement_date": fields.String(
            required=False, description="YYYY-MM-DD o YYYY-MM-DD HH:MM:SS (default: ahora)", example="2026-09-08"
        ),
        "reference": fields.String(required=False, description="Referencia libre (factura, vale...); se guarda en mayúsculas"),
        "comment": fields.String(required=False, description="Comentario libre"),
    },
)

sucursal_movement_put_model = api.model(
    "SucursalMovementPut",
    {
        "id_movement": fields.Integer(required=True, description="Movimiento de la sede a editar", example=6901),
        "movement_type": fields.String(required=False, description="entrada | salida"),
        "quantity": fields.Float(required=False, description="Cantidad > 0"),
        "movement_date": fields.String(required=False, description="YYYY-MM-DD o YYYY-MM-DD HH:MM:SS"),
        "reference": fields.String(required=False),
        "comment": fields.String(required=False),
    },
)

sucursal_movement_delete_model = api.model(
    "SucursalMovementDelete",
    {
        "id_movement": fields.Integer(required=True, description="Movimiento de la sede a borrar", example=6901),
    },
)


class SucursalMovementPostForm(Form):
    id_warehouse = IntegerField("id_warehouse", validators=[Optional()], default=None)
    id_product = IntegerField("id_product", validators=[InputRequired()])
    movement_type = StringField("movement_type", validators=[InputRequired()])
    quantity = FloatField("quantity", validators=[InputRequired()])
    movement_date = StringField("movement_date", validators=[Optional()], default=None)
    reference = StringField("reference", validators=[Optional()], default=None)
    comment = StringField("comment", validators=[Optional()], default=None)


class SucursalMovementPutForm(Form):
    id_movement = IntegerField("id_movement", validators=[InputRequired()])
    # parcial: el midleware aplica solo las llaves presentes en el payload crudo
    movement_type = StringField("movement_type", validators=[Optional()], default=None)
    quantity = FloatField("quantity", validators=[Optional()], default=None)
    movement_date = StringField("movement_date", validators=[Optional()], default=None)
    reference = StringField("reference", validators=[Optional()], default=None)
    comment = StringField("comment", validators=[Optional()], default=None)


class SucursalMovementDeleteForm(Form):
    id_movement = IntegerField("id_movement", validators=[InputRequired()])


# --- Recepción de traslados (F3, lado sede). `items` por ns.payload crudo.
transfer_receive_item_model = api.model(
    "TransferReceiveItem",
    {
        "id_product": fields.Integer(required=True, example=1),
        "quantity_received": fields.Float(required=True, description="Lo realmente recibido (>= 0; 0 = no llegó)", example=10),
        "comment": fields.String(required=False, description="Nota del item (dañado, faltante...)"),
    },
)

transfer_receive_model = api.model(
    "TransferReceive",
    {
        "id_transfer": fields.Integer(required=True, example=1),
        "items": fields.List(
            fields.Nested(transfer_receive_item_model),
            required=True,
            description="Exactamente los productos del traslado (todos, sin extras)",
        ),
        "comment": fields.String(required=False, description="Comentario general de la recepción"),
    },
)


class TransferReceiveForm(Form):
    id_transfer = IntegerField("id_transfer", validators=[InputRequired()])
    comment = StringField("comment", validators=[Optional()], default=None)
    # items: lista cruda validada en receive_transfer_api
