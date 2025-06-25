# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/nov/2024  at 16:15 $"

from wtforms.fields.numeric import IntegerField

from static.Models.api_models import datetime_filter
from static.constants import api
from flask_restx import fields
from wtforms.fields.datetime import DateTimeField
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
        "duration_services": fields.String(
            required=True, description="The duration services", example="2024-03-01"
        ),
        "purchase_id": fields.Integer(
            required=False, description="The purchase id", example=0
        ),
        "tool": fields.Integer(
            required=True, description="The state if is a tool 1", example=0
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


metadata_telintec_order_model = api.model(
    "MetadataTelintecOrder",
    {
        "name": fields.String(
            required=True, description="The name", example="TELINTEC S.A. DE CV"
        ),
        "address_invoice": fields.String(
            required=True,
            description="The address of the invoice",
            example="Av. Lázaro Cárdenas 306 1er piso oficina A-1 Col. Residencial San Agustín San Pedro Garza García, NL, C.P. 66260",
        ),
        "address_comercial": fields.String(
            required=True,
            description="The address of the comercial",
            example="Calle La barca 140 Col. Mitras Sur C.P.64020 Monterrey, N.L CP 64030 Monterrey, N.L.",
        ),
        "phone": fields.String(
            required=True, description="The phone", example="1234567890"
        ),
        "email": fields.String(
            required=True, description="The email", example="email@email.com"
        ),
        "rfc": fields.String(
            required=True, description="The RFC", example="RFC1234567890"
        ),
        "responsable": fields.String(
            required=True,
            description="The person responsable name",
            example="Carolina Torres",
        ),
    },
)

metadata_supplier_model = api.model(
    "MetadataSupplier",
    {
        "name": fields.String(
            required=True, description="The name", example="TELINTEC S.A. DE CV"
        ),
        "address_invoice": fields.String(
            required=True,
            description="The address of the invoice",
            example="Av. Lázaro Cárdenas 306 1er piso oficina A-1 Col. Residencial San Agustín San Pedro Garza García, NL, C.P. 66260",
        ),
        "rfc": fields.String(
            required=True, description="The RFC", example="RFC1234567890"
        ),
        "salesaman": fields.String(
            required=True,
            description="The person salesanan name",
            example="Carolina Torres",
        ),
        "payment_method": fields.String(
            required=True, description="The payment method"
        ),
        "delivery_conditions": fields.String(
            required=True, description="The delivery conditions"
        ),
        "delivery_address": fields.String(
            required=True,
            description="The delivery address",
            example="Calle La barca 140 Col. Mitras Sur C.P.64020 Monterrey, N.L CP 64030 Monterrey, N.L.",
        ),
        "transport": fields.String(
            required=True, description="The transport", example="proveedor"
        ),
        "insurance": fields.String(
            required=True, description="The insurance", example="proveedor"
        ),
        "guarantee": fields.String(
            required=True, description="The guarantee", example="proveedor"
        ),
    },
)

pos_application_post_model = api.model(
    "PurchaseOrderApplicationPost",
    {
        "reference": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
    },
)


pos_application_put_model = api.model(
    "PurchaseOrderApplicationPut",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "reference": fields.String(
            required=True,
            description="The application reference",
            example="alm-xxx-xx",
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
        "status": fields.Integer(
            required=True, description="The quotation status", example=0
        ),
        "created_by": fields.Integer(
            required=True, description="The quotation created by", example=1
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
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
        "supplier": fields.Integer(
            required=True, description="The supplier id", example=1
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "time_delivery": fields.String(
            required=True, description="The quotation time delivery", example="3 weeks"
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
        "metadata_telintec": fields.Nested(
            metadata_telintec_order_model, required=True
        ),
        "metadata_supplier": fields.Nested(metadata_supplier_model, required=True),
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
        "created_by": fields.Integer(
            required=True, description="The quotation created by", example=1
        ),
        "time_delivery": fields.String(
            required=True, description="The quotation time delivery", example="3 weeks"
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
        "metadata_telintec": fields.Nested(
            metadata_telintec_order_model, required=True
        ),
        "metadata_supplier": fields.Nested(metadata_supplier_model, required=True),
    },
)

purchase_order_delete_model = api.model(
    "PurchaseOrderDelete",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
    },
)

purchase_order_update_status_model = api.model(
    "PurchaseOrderDelete",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
        "status": fields.Integer(
            required=True, description="The quotation status", example=0
        ),
        "approved": fields.Integer(
            required=True, description="The quotation approved", example=1
        ),
    },
)


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
    duration_services = StringField("duration_services", [], default="0")
    supplier = StringField("supplier", [], default="")
    purchase_id = IntegerField("purchase_id", [], default=0)
    id = IntegerField("id", [InputRequired()])


class ItemsPOApplicationForm(Form):
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    brand = StringField("brand", [InputRequired()])
    category = StringField("category", [InputRequired()])
    id_inventory = FloatField("id_inventory", [], default=0)
    url = URLField("url", [], default="")
    n_parte = StringField("n_parte", [], default="")
    supplier = StringField("supplier", [], default="")
    purchase_id = IntegerField("purchase_id", [], default=0)
    tool = IntegerField("tool", [InputRequired()])


class MetadataTelitencForm(Form):
    name = StringField("name", [InputRequired()])
    address_invoice = StringField("address_invoice", [InputRequired()])
    address_comercial = StringField("address_comercial", [InputRequired()])
    phone = StringField("phone", [InputRequired()])
    email = StringField("email", [InputRequired()])
    rfc = StringField("rfc", [InputRequired()])
    responsable = StringField("responsable", [InputRequired()])


class MetadataSupplierForm(Form):
    name = StringField("name", [InputRequired()])
    address_invoice = StringField("address_invoice", [InputRequired()])
    rfc = StringField("rfc", [InputRequired()])
    salesaman = StringField("salesaman", [InputRequired()])
    payment_method = StringField("payment_method", [InputRequired()])
    delivery_conditions = StringField("delivery_conditions", [InputRequired()])
    delivery_address = StringField("delivery_address", [InputRequired()])
    transport = StringField("transport", [InputRequired()])
    insurance = StringField("insurance", [InputRequired()])
    guarantee = StringField("guarantee", [InputRequired()])


class PurchaseOrderPostForm(Form):
    folio = StringField("folio", [InputRequired()])
    supplier = IntegerField("supplier", [InputRequired()])
    comment = StringField("comment", [])
    time_delivery = StringField("time_delivery", [])
    items = FieldList(FormField(ItemsPOForm), "items", validators=[], default=[])
    metadata_telintec = FormField(MetadataTelitencForm)
    metadata_supplier = FormField(MetadataSupplierForm)


class ItemsPOUpdateForm(Form):
    id = IntegerField("id", [], default=-1)
    id_purchase = IntegerField("id_purchase", [], default=0)
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
    duration_services = StringField("duration_services", [], default="")
    supplier = StringField("supplier", [], default="")


class ItemsPOApplicationUpdateForm(Form):
    id = IntegerField("id", [], default=-1)
    purchase_id = IntegerField("purchase_id", [], default=0)
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
    supplier = StringField("supplier", [], default="")
    tool = IntegerField("tool", [InputRequired()])


class PurchaseOrderPutForm(Form):
    id = IntegerField("id", [InputRequired()])
    folio = StringField("folio", [InputRequired()])
    comment = StringField("comment", [])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )
    created_by = IntegerField("created_by", [])
    items = FieldList(FormField(ItemsPOUpdateForm), "items", validators=[], default=[])
    time_delivery = StringField("time_delivery", [])
    supplier = IntegerField("supplier", [InputRequired()])
    metadata_telintec = FormField(MetadataTelitencForm)
    metadata_supplier = FormField(MetadataSupplierForm)


class PurchaseOrderDeleteForm(Form):
    id = IntegerField("id", [InputRequired()])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])


class PurchaseOrderUpdateStatusForm(Form):
    id = IntegerField("id", [InputRequired()])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )
    approved = IntegerField(
        "approved", [validators.number_range(min=-1, message="Invalid id")]
    )


class POsApplicationPostForm(Form):
    reference = StringField("reference", [])
    comment = StringField("comment", [])
    items = FieldList(
        FormField(ItemsPOApplicationForm), "items", validators=[], default=[]
    )


class POsApplicationPutForm(Form):
    id = IntegerField("id", [InputRequired()])
    reference = StringField("reference", [InputRequired()])
    comment = StringField("comment", [])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )
    created_by = IntegerField("created_by", [])
    items = FieldList(
        FormField(ItemsPOApplicationUpdateForm), "items", validators=[], default=[]
    )
