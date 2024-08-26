# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 10/may./2024  at 16:31 $"

from flask_restx import fields
from wtforms.fields.datetime import DateField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import StringField, URLField

from static.extensions import api
from wtforms.form import Form
from wtforms import validators, IntegerField, FormField

from wtforms.validators import InputRequired

client_emp_sm_response_model = api.model(
    "EmployeeSMResponse",
    {
        "data": fields.List(fields.List(fields.String)),
        "comment": fields.String(description="comment"),
    },
)

product_model_SM_selection = api.model(
    "Product Data",
    {
        "id": fields.String(required=True, description="The product id"),
        "name": fields.String(required=True, description="The product name"),
        "udm": fields.String(required=True, description="The product unit of measure"),
        "stock": fields.Integer(required=True, description="The product stock"),
    },
)

items_model_sm = api.model(
    "ItemsModel",
    {
        "id": fields.String(required=True, description="The product id"),
        "name": fields.String(required=True, description="The product name"),
        "stock": fields.Integer(required=True, description="The product stock"),
        "comment": fields.String(required=True, description="The product comment"),
        "quantity": fields.Float(required=True, description="The product quantity"),
        "movement": fields.String(required=False, description="The product movement"),
        "url": fields.String(
            required=True, description="The product url", example="https://example.com"
        ),
        "sku": fields.String(required=False, description="The product sku"),
    },
)

history_model_sm = api.model(
    "HistoryModel",
    {
        "date": fields.String(required=True, description="The product id"),
        "user": fields.Integer(required=True, description="The product name"),
        "event": fields.String(
            required=True, description="The product unit of measure"
        ),
    },
)

products_answer_model = api.model(
    "AnswerProducts",
    {
        "data": fields.List(fields.Nested(product_model_SM_selection)),
        "page": fields.Integer(required=True, description="The page number send"),
        "pages": fields.Integer(
            required=True,
            description="The total number of" " pages with the selected limit",
        ),
        "error": fields.Raw(
            required=False,
            description="The error message",
        ),
    },
)

emp_almacen_model = api.model(
    "EmployeeAlmacen",
    {
        "id": fields.Integer(required=True, description="The employee id"),
        "name": fields.String(required=True, description="The employee name"),
    },
)

employees_answer_model = api.model(
    "AnswerEmployees",
    {
        "data": fields.List(fields.Nested(emp_almacen_model)),
        "msg": fields.String(required=True, description="The message"),
    },
)

products_request_model = api.model(
    "ProductSearch",
    {
        "limit": fields.Integer(
            required=True, description="The results limit", example=10
        ),
        "page": fields.Integer(
            required=True, description="The output page default: 1", example=0
        ),
    },
)

sm_model = api.model(
    "MaterialRequest",
    {
        "id": fields.Integer(
            required=True, description="The id <ignored on add event>"
        ),
        "folio": fields.String(required=True, description="The folio"),
        "contract": fields.String(required=True, description="The contract"),
        "facility": fields.String(required=True, description="The facility"),
        "contract_contact": fields.String(
            required=True, description="The contract contact"
        ),
        "client_id": fields.Integer(
            required=True, description="The client id", example=1
        ),
        "location": fields.String(required=True, description="The location"),
        "order_quotation": fields.String(
            required=True, description="The order or quotation"
        ),
        "emp_id": fields.Integer(
            required=True, description="The employee id", example=1
        ),
        "date": fields.String(
            required=True, description="The date", example="2024-06-29"
        ),
        "critical_date": fields.String(
            required=True, description="The critical date", example="2024-07-15"
        ),
        "status": fields.Integer(required=True, description="The status of the sm"),
        "history": fields.List(fields.Nested(history_model_sm)),
        "comment": fields.String(required=True, description="The comment"),
        "destination": fields.String(
            required=True, description="The destination area in telintec"
        ),
    },
)

sm_model_out = api.model(
    "MaterialRequestTable",
    {
        "id": fields.Integer(
            required=True, description="The id <ignored on add event>"
        ),
        "folio": fields.String(required=True, description="The folio"),
        "contract": fields.String(required=True, description="The contract"),
        "facility": fields.String(required=True, description="The facility"),
        "contract_contact": fields.String(
            required=True, description="The contract contact"
        ),
        "client_id": fields.Integer(
            required=True, description="The client id", example=1
        ),
        "location": fields.String(required=True, description="The location"),
        "order_quotation": fields.String(
            required=True, description="The order or quotation"
        ),
        "emp_id": fields.Integer(
            required=True, description="The employee id", example=1
        ),
        "date": fields.String(
            required=True, description="The date", example="2024-06-29"
        ),
        "critical_date": fields.String(
            required=True, description="The critical date", example="2024-07-15"
        ),
        "status": fields.Integer(required=True, description="The status of the sm"),
        "history": fields.List(fields.Nested(history_model_sm)),
        "comment": fields.String(required=True, description="The comment"),
        "destination": fields.String(
            required=True, description="The destination area in telintec"
        ),
        "items": fields.List(fields.Nested(items_model_sm), required=False),
        "items_new": fields.List(fields.Nested(items_model_sm), required=False),
    },
)

table_sm_model = api.model(
    "TableMaterialRequest",
    {
        "data": fields.List(fields.Nested(sm_model_out)),
        "page": fields.Integer(required=True, description="The page number send"),
        "pages": fields.Integer(
            required=True,
            description="The total number of" " pages with the selected limit",
        ),
        "error": fields.Raw(
            required=False,
            description="The error message",
        ),
    },
)

table_request_model = api.model(
    "TableRequest",
    {
        "limit": fields.Integer(
            required=True, description="The results limit", example=10
        ),
        "page": fields.Integer(
            required=True, description="The output page default: 1", example=0
        ),
        "emp_id": fields.Integer(
            required=True, description="The employee id", example=-1
        ),
    },
)

sm_product_request_model = api.model(
    "material_requestProductRequest",
    {
        "id": fields.Integer(required=True, description="The product id", example=1),
        "quantity": fields.Integer(required=True, description="The quantity"),
        "comment": fields.String(required=True, description="The comment"),
    },
)

sm_post_model = api.model(
    "material_requestPost",
    {
        "info": fields.Nested(sm_model),
        "items": fields.List(fields.Nested(items_model_sm)),
    },
)

sm_put_model = api.model(
    "material_requestPut",
    {
        "info": fields.Nested(sm_model),
        "items": fields.List(fields.Nested(items_model_sm)),
        "id": fields.Integer(required=True, description="The id"),
    },
)

delete_request_sm_model = api.model(
    "DeleteRequestmaterial_request",
    {
        "id": fields.Integer(required=True, description="The id"),
        "id_emp": fields.Integer(required=True, description="The employee id"),
    },
)

new_cliente_model = api.model(
    "NewClienteSM",
    {
        "name": fields.String(required=True, description="The name"),
        "address": fields.String(required=True, description="The address"),
        "phone": fields.String(required=True, description="The phone"),
        "email": fields.String(required=True, description="The email"),
        "rfc": fields.String(required=True, description="The rfc"),
    },
)

new_product_model = api.model(
    "NewProductSM",
    {
        "name": fields.String(required=True, description="The name"),
        "udm": fields.String(required=True, description="The udm"),
        "supplier": fields.Float(required=True, description="The supplier"),
        "stock": fields.Integer(required=True, description="The stock"),
        "sku": fields.String(required=True, description="The sku"),
        "category": fields.Integer(required=True, description="The category"),
    },
)

data_sm_plots = api.model(
    "DataSMBoard",
    {
        "data": fields.Raw(required=False, description="The data"),
        "val_x": fields.List(fields.String, required=False, description="The x values"),
        "val_y": fields.List(
            fields.List(fields.Float, required=False, description="The y values")
        ),
        "title": fields.String(required=True, description="The title"),
        "ylabel": fields.String(required=True, description="The y label"),
        "legend": fields.List(fields.String, required=True, description="The legend"),
    },
)

request_sm_plot_data_model = api.model(
    "RequestSMPlotData",
    {
        "data": fields.List(fields.Nested(data_sm_plots)),
        "type": fields.String(required=True, description="The type of plot"),
    },
)

request_sm_dispatch_model = api.model(
    "RequestSMDispatch",
    {
        "id": fields.Integer(required=True, description="The id"),
        "emp_id": fields.Integer(required=True, description="The employee id"),
        "comment": fields.String(required=True, description="The date"),
        "items": fields.List(fields.Nested(items_model_sm), required=False),
    },
)

data_response_dispatch_model = api.model(
    "DataResponseDispatch",
    {
        "to_dispatch": fields.List(fields.Nested(items_model_sm)),
        "to_request": fields.List(fields.Nested(items_model_sm)),
        "new_products": fields.List(fields.Nested(new_product_model)),
        "msg": fields.String(required=True, description="The message"),
    },
)

response_sm_dispatch_model = api.model(
    "ResponseSMDispatch",
    {
        "msg": fields.String(required=True, description="The message"),
        "data": fields.Nested(data_response_dispatch_model),
    },
)


class ItemsFormSM(Form):
    id = IntegerField(
        "id", validators=[validators.number_range(min=-1, message="Invalid id")]
    )
    name = StringField("name", validators=[InputRequired()])
    stock = IntegerField(
        "stock", validators=[validators.number_range(min=-100, message="Invalid stock")]
    )
    comment = StringField("comment", validators=[], default="")
    quantity = FloatField(
        "quantity", validators=[validators.number_range(min=0, message="Invalid id")]
    )
    movement = StringField("movement", validators=[], default="")
    url = URLField("url", validators=[], default="")
    sku = StringField("sku", validators=[], default="")


class ProductRequestForm(Form):
    limit = IntegerField(
        "limit", validators=[InputRequired(message="Invalid limit or 0 not acepted")]
    )
    page = IntegerField(
        "page",
        validators=[
            validators.number_range(
                min=0, message="Invalid page value o missing 'page' field"
            )
        ],
    )


class SMInfoForm(Form):
    id = IntegerField(
        "id", validators=[validators.number_range(min=0, message="Invalid id")]
    )
    folio = StringField("folio", validators=[InputRequired()])
    contract = StringField("contract", validators=[InputRequired()])
    facility = StringField("facility", validators=[InputRequired()])
    contract_contact = StringField("contract_contact", default="")
    client_id = IntegerField(
        "client_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    location = StringField("location", validators=[InputRequired()])
    order_quotation = StringField("order_quotation", validators=[InputRequired()])
    emp_id = IntegerField(
        "emp_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    date = DateField("date", validators=[InputRequired()])
    critical_date = StringField("critical_date", validators=[InputRequired()])
    status = IntegerField(
        "status", validators=[validators.number_range(min=0, message="Invalid id")]
    )
    comment = StringField("comment", validators=[], default="")
    destination = StringField("destination", validators=[InputRequired()])
    items = FieldList(FormField(ItemsFormSM, "items"))
    items_new = FieldList(FormField(ItemsFormSM, "items_new"))


class TableRequestForm(Form):
    limit = IntegerField(
        "limit", validators=[InputRequired(message="Invalid limit or 0 not acepted")]
    )
    page = IntegerField(
        "page",
        validators=[
            validators.number_range(
                min=0, message="Invalid page value o missing 'page' field"
            )
        ],
    )
    emp_id = IntegerField(
        "emp_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )


class SMPostForm(Form):
    info = FormField(SMInfoForm, "info")
    items = FieldList(FormField(ItemsFormSM, "items"))


class SMPutForm(Form):
    info = FormField(SMInfoForm, "info")
    items = FieldList(FormField(ItemsFormSM, "items"))
    id = IntegerField(
        "id", validators=[validators.number_range(min=0, message="Invalid id")]
    )


class SMDeleteForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    id_emp = IntegerField(
        "id_emp", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
