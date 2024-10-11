# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 15:33 $"

from flask_restx import fields
from static.extensions import api, format_date
from wtforms.fields.form import FormField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import StringField
from wtforms.form import Form
from wtforms import IntegerField
from wtforms.validators import InputRequired, NumberRange

movement_model = api.model(
    "MovementAMC",
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
        "sm_id": fields.Integer(
            required=True, description="The movement id", example=1
        ),
        "previous_q": fields.Float(required=True, description="The previous quantity"),
    },
)

movements_output_model = api.model(
    "MovementsOutAMC",
    {
        "data": fields.List(fields.Nested(movement_model)),
        "msg": fields.String(required=True, description="The message"),
    },
)

movement_insert_model = api.model(
    "MovementInputAMC",
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


def date_filter(date):
    # Example filter function to format the date
    return date.strftime(format_date) if not isinstance(date, str) else date


class MovementForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
    id_product = IntegerField(
        "id_product",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
    type_m = StringField("type_m", validators=[InputRequired()])
    quantity = FloatField("quantity", validators=[], default=0.0)
    movement_date = DateField(
        "movement_date", validators=[InputRequired()], filters=[date_filter]
    )
    sm_id = IntegerField(
        "sm_id",
        validators=[NumberRange(min=0, message="Invalid sm id")],
    )
    previous_q = FloatField("previous_q", validators=[], default=0.0)


class MovementInsertForm(Form):
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
