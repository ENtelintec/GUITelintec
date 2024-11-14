# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/nov/2024  at 16:15 $"

from static.Models.api_models import date_filter, datetime_filter
from static.extensions import api
from flask_restx import fields
from wtforms.fields.datetime import DateTimeField, DateField
from wtforms.validators import InputRequired
from wtforms import FormField, StringField, URLField, FloatField
from wtforms.fields.list import FieldList
from wtforms.form import Form

from templates.controllers.purchases.purchases_admin_controller import insert_new_purchase_db

purchase_metadata_model = api.model(
    "PurchaseMetadata",
    {
        "name": fields.String(required=True, description="The name"),
        "quantity": fields.Integer(required=True, description="The quantity"),
        "supplier": fields.String(required=True, description="The supplier"),
        "link": fields.String(required=True, description="The link"),
        "comments": fields.String(required=True, description="The comments"),
        "date_required": fields.String(required=True, description="The date required"),
    },
)

timestamp_model = api.model(
    "TimestampP",
    {
        "timestamp": fields.String(
            required=True, description="The quotation timestamp"
        ),
        "comment": fields.String(required=True, description="The quotation comment"),
    },
)

timestamps_purchase_model = api.model(
    "TimestampPurchase",
    {
        "complete": fields.Nested(timestamp_model, required=False),
        "update": fields.List(fields.Nested(timestamp_model), required=False),
    },
)

purchase_post_model = api.model(
    "PurchasePost",
    {
        "metadata": fields.Nested(purchase_metadata_model),
        "creation": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "timestamps": fields.Nested(timestamps_purchase_model),
    },
)


class MetadataPurchaseForm(Form):
    name = StringField("Name", [InputRequired()])
    quantity = FloatField("Quantity", [InputRequired()])
    supplier = StringField("Supplier", [InputRequired()])
    link = URLField("Link", [InputRequired()])
    comments = StringField("Comments", [InputRequired()])
    date_required = DateField("Date Required", [InputRequired()], filters=[date_filter])


class TimestampPurchaseForm(Form):
    timestamp = DateTimeField("Timestamp", [InputRequired()], filters=[datetime_filter])
    comment = StringField("Comment", [], default="")


class TimestampsPurchaseForm(Form):
    complete = FormField(TimestampPurchaseForm, "complete", default={})
    update = FieldList(
        FormField(TimestampPurchaseForm), "update", validators=[], default=[]
    )


class PurchasePostForm(Form):
    metadata = FormField(MetadataPurchaseForm, "metadata")
    creation = DateTimeField("Creation", [InputRequired()], filters=[datetime_filter])
