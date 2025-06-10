# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/nov/2024  at 16:15 $"


from wtforms.fields.numeric import IntegerField

from static.Models.api_models import date_filter, datetime_filter
from static.constants import api
from flask_restx import fields
from wtforms.fields.datetime import DateTimeField, DateField
from wtforms.validators import InputRequired
from wtforms import FormField, StringField, URLField, FloatField, validators
from wtforms.fields.list import FieldList
from wtforms.form import Form


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


items_po_model = api.model(
    "ItemsPO",
    {
        "id": fields.Integer(required=False, description="The item id", example=0),
        "description": fields.String(
            required=True, description="The name or desciption"
        ),
        "quantity": fields.Float(required=True, description="The quantity"),
        "unit_price": fields.Float(required=True, description="The unit price"),
        "brand": fields.String(required=True, description="The brand"),
        "category": fields.String(required=True, description="The supplier"),
        "id_inventory": fields.Integer(
            required=True, description="The inventory id", example=0
        ),
        "url": fields.String(
            required=True, description="The url", example="https://www.example.com"
        ),
        "n_parte": fields.String(
            required=True, description="The part number", example="1234567890"
        ),
    },
)

history_purchase_model = api.model(
    "HistoryPurchase",
    {
        "user": fields.Integer(required=True, description="The user id", example=1),
        "event": fields.String(
            required=True, description="The event", example="Some event"
        ),
        "date": fields.String(
            required=True, description="The date", example="2024-03-01"
        ),
        "comment": fields.String(
            required=True, description="The comment", example="Some comment"
        ),
    },
)

purchase_order_post_model = api.model(
    "PurchaseOrderPost",
    {
        "folio": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "reference": fields.String(
            required=True, description="The quotation reference", example="Q-0001"
        ),
        "supplier": fields.Integer(
            required=True, description="The supplier id", example=1
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
    },
)

purchase_order_put_model = api.model(
    "PurchaseOrderPut",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "folio": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "reference": fields.String(
            required=True, description="The quotation reference", example="Q-0001"
        ),
        "supplier": fields.Integer(
            required=True, description="The supplier id", example=1
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
        "status": fields.Integer(
            required=True, description="The quotation status", example=0
        ),
        "approved_by": fields.Integer(
            required=True, description="The quotation approved by", example=1
        ),
        "created_by": fields.Integer(
            required=True, description="The quotation created by", example=1
        ),
        "total_amount": fields.Float(
            required=True, description="The quotation total amount", example=100.0
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
    },
)

purchase_order_delete_model = api.model(
    "PurchaseOrderDelete",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
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


class HistoryPurchaseForm(Form):
    user = IntegerField("user", [InputRequired()])
    event = StringField("event", [InputRequired()])
    date = DateTimeField("date", [InputRequired()], filters=[datetime_filter])
    comment = StringField("comment", [], default="")


class ItemsPOForm(Form):
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit_price = FloatField("unit_price", [InputRequired()])
    brand = StringField("brand", [InputRequired()])
    category = StringField("category", [InputRequired()])
    id_inventory = FloatField("id_inventory", [], default=0)
    url = URLField("url", [], default="")
    n_parte = StringField("n_parte", [], default="")


class PurchaseOrderPostForm(Form):
    folio = StringField("folio", [InputRequired()])
    reference = StringField("reference", [])
    supplier = StringField("supplier", [])
    comment = StringField("comment", [])
    items = FieldList(FormField(ItemsPOForm), "items", validators=[], default=[])


class ItemsPOUpdateForm(Form):
    id = IntegerField("id", [], default=-1)
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit_price = FloatField("unit_price", [InputRequired()])
    brand = StringField("brand", [InputRequired()])
    category = StringField("category", [InputRequired()])
    id_inventory = IntegerField(
        "id_inventory",
        [validators.number_range(min=-1, message="Invalid id")],
        default=-1,
    )
    url = URLField("url", [], default="")
    n_parte = StringField("n_parte", [], default="")


class PurchaseOrderPutForm(Form):
    id = IntegerField("id", [InputRequired()])
    folio = StringField("folio", [InputRequired()])
    reference = StringField("reference", [])
    supplier = StringField("supplier", [])
    comment = StringField("comment", [])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )
    approved_by = IntegerField("approved_by", [])
    created_by = IntegerField("created_by", [])
    total_amount = FloatField("total_amount", [])
    items = FieldList(FormField(ItemsPOUpdateForm), "items", validators=[], default=[])


class PurchaseOrderDeleteForm(Form):
    id = IntegerField("id", [InputRequired()])
