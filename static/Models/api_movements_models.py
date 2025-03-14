# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 15:33 $"

from flask_restx import fields

from static.constants import api
from wtforms.fields.form import FormField
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import StringField
from wtforms.form import Form
from wtforms import IntegerField
from wtforms.validators import InputRequired

movement_model = api.model(
    "MovementAMC",
    {
        "id_product": fields.Integer(
            required=True, description="The product id", example=1
        ),
        "type_m": fields.String(required=True, description="The movement type"),
        "quantity": fields.Float(required=True, description="The movement quantity"),
        "sm_id": fields.String(required=True, description="The movement id", example=1),
        "previous_q": fields.Float(required=True, description="The previous quantity"),
        "reference": fields.String(
            required=True, description="The movement reference", example="reference"
        ),
    },
)


movement_out_model = api.model(
    "MovementOutAMC",
    {
        "id": fields.Integer(required=True, description="The movement id", example=1),
        "id_product": fields.Integer(
            required=True, description="The product id", example=1
        ),
        "type_m": fields.String(required=True, description="The movement type"),
        "quantity": fields.Float(required=True, description="The movement quantity"),
        "movement_date": fields.String(
            required=True, description="The movement date", example="2024-04-03"
        ),
        "sm_id": fields.String(
            required=True, description="The movement id", example="sm-code"
        ),
        "reference": fields.String(
            required=True, description="The movement reference", example="reference"
        ),
    },
)


movements_output_model = api.model(
    "MovementsOutAMC",
    {
        "data": fields.List(fields.Nested(movement_out_model)),
        "msg": fields.String(required=False, description="The message"),
        "error": fields.String(required=False, description="The error"),
    },
)

movement_insert_model = api.model(
    "MovementInputAMC",
    {
        "info": fields.Nested(movement_model),
    },
)

movement_update_model = api.model(
    "MovementUpdateAMC",
    {
        "info": fields.Nested(movement_model),
        "id": fields.Integer(
            required=True, description="The movement id to modify", exameple=1
        ),
    },
)

movement_delete_model = api.model(
    "MovementDeleteAMC",
    {
        "id": fields.Integer(
            required=True, description="The movement id to delete", example=1
        )
    },
)


class MovementForm(Form):
    id_product = IntegerField(
        "id_product",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
    type_m = StringField("type_m", validators=[InputRequired()])
    quantity = FloatField("quantity", validators=[], default=0.0)
    sm_id = StringField(
        "sm_id",
        validators=[InputRequired()],
    )
    previous_q = FloatField("previous_q", validators=[], default=0.0)
    reference = StringField("reference", validators=[], default="update")


class MovementInsertForm(Form):
    info = FormField(MovementForm)


class MovementUpdateForm(Form):
    info = FormField(MovementForm)
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )


class MovementDeleteForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
