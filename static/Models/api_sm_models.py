# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 10/may./2024  at 16:31 $"


from flask_restx import fields
from wtforms.fields.datetime import DateField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import StringField, URLField, EmailField

from static.Models.api_models import date_filter, datetime_filter
from static.constants import api
from wtforms.form import Form
from wtforms import validators, IntegerField, FormField

from wtforms.validators import InputRequired

client_emp_sm_response_model = api.model(
    "EmployeeSMResponse",
    {
        "data": fields.List(fields.List(fields.String)),
        "comment": fields.String(description="comment"),
        "error": fields.Raw(
            required=False,
            description="The error message",
        ),
    },
)

product_model_SM_selection = api.model(
    "Product Data",
    {
        "id": fields.String(required=True, description="The product id"),
        "name": fields.String(required=True, description="The product name"),
        "udm": fields.String(required=True, description="The product unit of measure"),
        "stock": fields.Float(required=True, description="The product stock"),
    },
)

items_model_sm = api.model(
    "ItemsModel",
    {
        "id": fields.Integer(required=True, description="The product id"),
        "name": fields.String(required=True, description="The product name"),
        "stock": fields.Float(required=True, description="The product stock"),
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
        "msg": fields.String(required=False, description="The message"),
        "error": fields.Raw(
            required=False,
            description="The error message",
        ),
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

sm_model_post = api.model(
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
        "comment": fields.String(required=True, description="The comment"),
        "destination": fields.String(
            required=True, description="The destination area in telintec"
        ),
    },
)

sm_model_put = api.model(
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
        # New fields added
        "urgent": fields.Integer(required=False, description="Urgent", example=0),
        "project": fields.String(required=False, description="The project"),
        "activity_description": fields.String(
            required=False, description="Description of activity"
        ),
        "request_date": fields.String(
            required=True, description="Request date", example="2024-06-29 12:00:00"
        ),
        "requesting_user_status": fields.Integer(
            required=False,
            description="Status of the requesting user (pendiente:1, recibido:2, cancelado:3, reprogramado:4)",
            example=0,
        ),
        "warehouse_reviewed": fields.Integer(
            required=False, description="Reviewed by warehouse", example=0
        ),
        "warehouse_status": fields.Integer(
            required=False,
            description="Warehouse status (no disponible:1, disponible:2)",
            example=1,
        ),
        "admin_notification_date": fields.String(
            required=False, description="Date of notification to administration"
        ),
        "kpi_warehouse": fields.Integer(
            required=False,
            description="Key performance indicator (cumple: 0, no cumple:1)",
            example=0,
        ),
        "warehouse_comments": fields.String(
            required=False, description="Warehouse comments"
        ),
        "admin_reviewed": fields.Integer(
            required=False, description="Reviewed by administration", example=0
        ),
        "admin_status": fields.Integer(
            required=False,
            description="Administration status (disponible:1, no disponible:2)",
            example=1,
        ),
        "warehouse_notification_date": fields.String(
            required=False,
            description="Date of notification to warehouse",
            example="2024-06-29 12:00:00",
        ),
        "purchasing_kpi": fields.Integer(
            required=False,
            description="Key performance indicator (cumple=0, no cumple=1)",
            example=0,
        ),
        "admin_comments": fields.String(
            required=False, description="Administration comments"
        ),
        "general_request_status": fields.String(
            required=False,
            description="General request status (disponible en almacén: 1, "
            "pendiente: 2, entregado: 3, reprogramado:3, "
            "cancelado: 4, en recolección: 5)",
            example=1,
        ),
        "operations_notification_date": fields.String(
            required=False,
            description="Date of notification to operations",
            example="2024-06-29 12:00:00",
        ),
        "operations_kpi": fields.Integer(
            required=False,
            description="Key performance indicator (Operations)",
            example=0,
        ),
        "requesting_user_state": fields.String(
            required=False, description="State of the requesting user"
        ),
    },
)


control_table_sm_model = api.model(
    "ControlTableSM",
    {
        "urgent": fields.Integer(required=False, description="Urgent", example=0),
        "project": fields.String(required=False, description="The project"),
        "activity_description": fields.String(
            required=False, description="Description of activity"
        ),
        "request_date": fields.String(
            required=True, description="Request date", example="2024-06-29 12:00:00"
        ),
        "requesting_user_status": fields.Integer(
            required=False,
            description="Status of the requesting user (pendiente:1, recibido:2, cancelado:3, reprogramado:4)",
            example=0,
        ),
        "warehouse_reviewed": fields.Integer(
            required=False, description="Reviewed by warehouse", example=0
        ),
        "warehouse_status": fields.Integer(
            required=False,
            description="Warehouse status (no disponible:1, disponible:2)",
            example=1,
        ),
        "admin_notification_date": fields.String(
            required=False, description="Date of notification to administration"
        ),
        "kpi_warehouse": fields.Integer(
            required=False,
            description="Key performance indicator (cumple: 0, no cumple:1)",
            example=0,
        ),
        "warehouse_comments": fields.String(
            required=False, description="Warehouse comments"
        ),
        "admin_reviewed": fields.Integer(
            required=False, description="Reviewed by administration", example=0
        ),
        "admin_status": fields.Integer(
            required=False,
            description="Administration status (disponible:1, no disponible:2)",
            example=1,
        ),
        "warehouse_notification_date": fields.String(
            required=False,
            description="Date of notification to warehouse",
            example="2024-06-29 12:00:00",
        ),
        "purchasing_kpi": fields.Integer(
            required=False,
            description="Key performance indicator (cumple=0, no cumple=1)",
            example=0,
        ),
        "admin_comments": fields.String(
            required=False, description="Administration comments"
        ),
        "general_request_status": fields.String(
            required=False,
            description="General request status (disponible en almacén: 1, "
            "pendiente: 2, entregado: 3, reprogramado:3, "
            "cancelado: 4, en recolección: 5)",
            example=1,
        ),
        "operations_notification_date": fields.String(
            required=False,
            description="Date of notification to operations",
            example="2024-06-29 12:00:00",
        ),
        "operations_kpi": fields.Integer(
            required=False,
            description="Key performance indicator (Operations)",
            example=0,
        ),
        "requesting_user_state": fields.String(
            required=False, description="State of the requesting user"
        ),
    },
)

control_table_sm_put_model = api.model(
    "ControlTableSMPut",
    {
        "id": fields.Integer(required=True, description="The id of the sm to update"),
        "info": fields.Nested(control_table_sm_model),
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
        "info": fields.Nested(sm_model_post),
        "items": fields.List(fields.Nested(items_model_sm)),
    },
)

sm_put_model = api.model(
    "material_requestPut",
    {
        "info": fields.Nested(sm_model_put),
        "items": fields.List(fields.Nested(items_model_sm)),
        "id": fields.Integer(required=True, description="The id"),
    },
)

delete_request_sm_model = api.model(
    "DeleteRequestmaterial_request",
    {
        "id": fields.Integer(required=True, description="The id"),
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
        "supplier": fields.Integer(required=True, description="The  id"),
        "stock": fields.Float(required=True, description="The stock"),
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
        "error": fields.String(required=False, description="The error message"),
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
        "msg": fields.String(required=False, description="The message"),
        "data": fields.Nested(data_response_dispatch_model),
        "error": fields.String(required=False, description="The error message"),
    },
)


class ItemsFormSM(Form):
    id = IntegerField(
        "id",
        validators=[],
        default=-1,
    )
    name = StringField("name", validators=[InputRequired()])
    stock = FloatField(
        "stock", validators=[validators.number_range(min=-100, message="Invalid stock")]
    )
    comment = StringField("comment", validators=[], default="")
    quantity = FloatField(
        "quantity",
        validators=[validators.number_range(min=0, message="Invalid quantity")],
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


class HistoryFormSM(Form):
    date = StringField("date", validators=[InputRequired()])
    event = StringField("event", validators=[InputRequired()])
    user = IntegerField("user", validators=[InputRequired()])


class SMInfoForm(Form):
    id = IntegerField(
        "id", validators=[validators.number_range(min=0, message="Invalid id sm info")]
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
    date = DateField("date", validators=[InputRequired()], filters=[date_filter])
    critical_date = StringField("critical_date", validators=[InputRequired()])
    status = IntegerField(
        "status", validators=[validators.number_range(min=0, message="Invalid id")]
    )
    comment = StringField("comment", validators=[], default="")
    destination = StringField("destination", validators=[InputRequired()])
    # history = StringField("history", validators=[], default="[]")
    history = FieldList(FormField(HistoryFormSM, "history"))
    items = FieldList(FormField(ItemsFormSM, "items"))
    items_new = FieldList(FormField(ItemsFormSM, "items_new"))


class SMInfoControlTableForm(Form):
    project = StringField("project", validators=[], default="")
    urgent = IntegerField("urgent", validators=[], default=0)
    activity_description = StringField(
        "activity_description", validators=[], default=""
    )
    request_date = StringField(
        "request_date", validators=[InputRequired()], filters=[datetime_filter]
    )
    requesting_user_status = IntegerField(
        "requesting_user_status", validators=[], default=0
    )
    warehouse_reviewed = (IntegerField("warehouse_reviewed", validators=[], default=0),)
    warehouse_status = (IntegerField("warehouse_status", validators=[], default=1),)
    admin_notification_date = StringField(
        "admin_notification_date", validators=[], filters=[datetime_filter]
    )
    kpi_warehouse = (IntegerField("kpi_warehouse", validators=[], default=0),)
    warehouse_comments = StringField("warehouse_comments", validators=[], default="")
    admin_reviewed = (IntegerField("admin_reviewed", validators=[], default=0),)
    admin_status = (IntegerField("admin_status", validators=[], default=1),)
    warehouse_notification_date = StringField(
        "warehouse_notification_date", validators=[], filters=[datetime_filter]
    )
    purchasing_kpi = (IntegerField("purchasing_kpi", validators=[], default=0),)
    admin_comments = StringField("admin_comments", validators=[], default="")
    general_request_status = (
        IntegerField("general_request_status", validators=[InputRequired()], default=1),
    )
    operations_notification_date = StringField(
        "operations_notification_date", validators=[], filters=[datetime_filter]
    )
    operations_kpi = (IntegerField("operations_kpi", validators=[], default=0),)
    requesting_user_state = StringField(
        "requesting_user_state", validators=[], default=""
    )


class SMInfoControlTablePutForm(Form):
    id = IntegerField("id", validators=[InputRequired(message="Invalid id control sm")])
    info = FormField(SMInfoControlTableForm, "info")


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


class NewClienteForm(Form):
    name = StringField("name", validators=[InputRequired()])
    address = StringField("address", validators=[InputRequired()])
    phone = StringField("phone", validators=[InputRequired()])
    email = EmailField("email", validators=[InputRequired()])
    rfc = StringField("rfc", validators=[])


class NewProductForm(Form):
    name = StringField("name", validators=[InputRequired()])
    udm = StringField("udm", validators=[InputRequired()])
    supplier = IntegerField("supplier", validators=[])
    stock = FloatField("stock", validators=[InputRequired()])
    sku = StringField("sku", validators=[InputRequired()])
    category = IntegerField("category", validators=[InputRequired()])


class RequestSMDispatchForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    emp_id = IntegerField(
        "emp_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    comment = StringField("comment", validators=[InputRequired()])
    items = FieldList(FormField(ItemsFormSM, "items"))
