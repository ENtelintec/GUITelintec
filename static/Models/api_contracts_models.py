# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:08 $"

from wtforms.form import Form
from wtforms.validators import InputRequired
from static.extensions import api, format_date
from flask_restx import fields
from wtforms.fields.datetime import DateField, DateTimeField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import FloatField, IntegerField
from wtforms.fields.simple import StringField, EmailField

from wtforms import FormField

metadata_quotation_model = api.model(
    "MetadataQuotation",
    {
        "emission": fields.String(
            required=True,
            description="The quotation emission date",
            example="2024-03-01",
        ),
        "limit_date": fields.String(
            required=True, description="The quotation limit date", example="2024-03-01"
        ),
        "quotation_code": fields.String(
            required=True, description="The quotation code"
        ),
        "codigo": fields.String(required=True, description="The quotation codigo"),
        "company": fields.String(required=True, description="The quotation company"),
        "user": fields.String(required=True, description="The quotation user"),
        "phone": fields.String(required=True, description="The quotation phone number"),
        "email": fields.String(required=True, description="The quotation email"),
        "planta": fields.String(required=True, description="The quotation planta"),
        "area": fields.String(required=True, description="The quotation area"),
        "location": fields.String(required=True, description="The quotation location"),
        "client_id": fields.Integer(
            required=True, description="The quotation client id"
        ),
    },
)

products_quotation_model = api.model(
    "ProductsQuotation",
    {
        "id": fields.Integer(required=True, description="The quotation id"),
        "description": fields.String(
            required=True, description="The quotation description"
        ),
        "quantity": fields.Integer(required=True, description="The quotation quantity"),
        "udm": fields.String(required=True, description="The quotation udm"),
        "price_unit": fields.Float(
            required=True, description="The quotation price unit"
        ),
        "comment": fields.String(required=True, description="The quotation comment"),
    },
)

timestamp_model_admin = api.model(
    "TimestampAdmin",
    {
        "timestamp": fields.String(
            required=True, description="The quotation timestamp"
        ),
        "comment": fields.String(required=True, description="The quotation comment"),
    },
)

timestamps_quotation_model = api.model(
    "TimestampQuotation",
    {
        "complete": fields.Nested(timestamp_model_admin),
        "update": fields.List(fields.Nested(timestamp_model_admin)),
    },
)

quotation_model = api.model(
    "Quotation",
    {
        "id": fields.Integer(required=True, description="The quotation id"),
        "metadata": fields.Nested(metadata_quotation_model),
        "products": fields.List(fields.Nested(products_quotation_model)),
        "creation": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "timestamps": fields.Nested(timestamps_quotation_model),
    },
)

answer_quotation_model = api.model(
    "AnswerQuotation",
    {
        "msg": fields.String(required=True, description="The message"),
        "data": fields.List(fields.Nested(quotation_model)),
    },
)

quotation_model_insert = api.model(
    "QuotationInsert",
    {
        "metadata": fields.Nested(metadata_quotation_model, required=True),
        "products": fields.List(fields.Nested(products_quotation_model), required=True),
    },
)
quotation_model_update = api.model(
    "QuotationUpdate",
    {
        "id": fields.Integer(required=True, description="The quotation id"),
        "metadata": fields.Nested(metadata_quotation_model),
        "products": fields.List(fields.Nested(products_quotation_model)),
        "timestamps": fields.Nested(timestamps_quotation_model),
    },
)
quotation_model_delete = api.model(
    "QuotationDelete",
    {"id": fields.Integer(required=True, description="The quotation id")},
)

metadata_contract_model = api.model(
    "MetadataContract",
    {
        "emission": fields.String(
            required=True,
            description="The quotation emission date",
            example="2024-03-01",
        ),
        "quotation_code": fields.String(
            required=True, description="The quotation code"
        ),
        "planta": fields.String(required=True, description="The quotation planta"),
        "area": fields.String(required=True, description="The quotation area"),
        "location": fields.String(required=True, description="The quotation location"),
        "client_id": fields.Integer(
            required=True, description="The quotation client id", example=1
        ),
        "contract_number": fields.String(
            required=True,
            description="The quotation contract number",
            example="12334534",
        ),
        "identifier": fields.String(
            required=True,
            description="The contract text identifier",
            example="contract for client automatización",
        ),
        "abbreviation": fields.String(
            required=True,
            description="The contract abbreviation",
            example="contrato auto",
        ),
    },
)

contract_model = api.model(
    "ContractAdmin",
    {
        "id": fields.Integer(required=True, description="The contract id"),
        "metadata": fields.Nested(metadata_contract_model),
        "creation": fields.String(
            required=True,
            description="The contract creation date",
            example="2024-03-01",
        ),
        "timestamps": fields.Nested(timestamps_quotation_model),
        "quotation_id": fields.Nested(quotation_model),
    },
)

answer_contract_model = api.model(
    "AnswerContract",
    {
        "msg": fields.String(required=True, description="The message"),
        "data": fields.List(fields.Nested(contract_model)),
    },
)

contract_model_insert = api.model(
    "ContractInsert",
    {
        "metadata": fields.Nested(metadata_contract_model, required=True),
        "quotation_id": fields.Integer(
            required=True, description="The quotation id", example=1
        ),
    },
)
contract_model_update = api.model(
    "ContractUpdate",
    {
        "id": fields.Integer(required=True, description="The contract id"),
        "metadata": fields.Nested(metadata_contract_model),
        "quotation_id": fields.Integer(
            required=True, description="The quotation id", example=1
        ),
        "timestamps": fields.Nested(timestamps_quotation_model),
    },
)
contract_model_delete = api.model(
    "ContractDelete",
    {"id": fields.Integer(required=True, description="The contract id", example=1)},
)


def date_filter(date):
    # Example filter function to format the date
    if date is not None:
        return date.strftime(format_date) if not isinstance(date, str) else date
    return None


class MetadataQuotationForm(Form):
    emission = DateField(
        "emission", validators=[InputRequired()], filters=[date_filter]
    )
    limit_date = DateField(
        "limit_date", validators=[InputRequired()], filters=[date_filter]
    )
    quotation_code = StringField("quotation_code", validators=[InputRequired()])
    codigo = StringField("codigo", validators=[InputRequired()])
    company = StringField("company", validators=[InputRequired()])
    user = StringField("user", validators=[InputRequired()])
    phone = StringField("phone", validators=[InputRequired()])
    email = EmailField("email", validators=[InputRequired()])
    planta = StringField("planta", validators=[InputRequired()])
    area = StringField("area", validators=[InputRequired()])
    location = StringField("location", validators=[InputRequired()])
    client_id = FloatField(
        "client_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )


class ProductsQuotationForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    description = StringField("description", validators=[InputRequired()])
    quantity = IntegerField("quantity", validators=[], default=0)
    udm = StringField("udm", validators=[InputRequired()])
    price_unit = FloatField("price_unit", validators=[], default=0.0)
    comment = StringField("comment", validators=[], default="")


class QuotationInsertForm(Form):
    metadata = FormField(MetadataQuotationForm, "metadata")
    products = FieldList(FormField(ProductsQuotationForm, "products"))


class TimestampsAdminForm(Form):
    timestamps = DateTimeField(
        "timestamps", validators=[], filters=[date_filter], default=None
    )
    comment = StringField("comment", validators=[], default="")


class TimestampsQuotationForm(Form):
    complete = FormField(TimestampsAdminForm, "complete")
    update = FieldList(FormField(TimestampsAdminForm, "update"))


class QuotationUpdateForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    metadata = FormField(MetadataQuotationForm, "metadata")
    products = FieldList(FormField(ProductsQuotationForm, "products"))
    timestamps = FormField(TimestampsQuotationForm, "timestamps")


class QuotationDeleteForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )


class MetadataContractForm(Form):
    emission = DateField(
        "emission", validators=[InputRequired()], filters=[date_filter]
    )
    quotation_code = StringField("quotation_code", validators=[], default="")
    planta = StringField("planta", validators=[], default="")
    area = StringField("area", validators=[], default="")
    location = StringField("location", validators=[], default="")
    client_id = IntegerField(
        "client_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    contract_number = StringField("contract_number", validators=[InputRequired()])
    identifier = StringField("identifier", validators=[InputRequired()])
    abbreviation = StringField("abbreviation", validators=[InputRequired()])


class ContractInsertForm(Form):
    metadata = FormField(MetadataContractForm, "metadata")
    quotation_id = IntegerField(
        "quotation_id",
        validators=[InputRequired(message="Invalid id or 0 not acepted")],
    )


class ContractUpdateForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    metadata = FormField(MetadataContractForm, "metadata")
    quotation_id = IntegerField(
        "quotation_id",
        validators=[InputRequired(message="Invalid id or 0 not acepted")],
    )
    timestamps = FormField(TimestampsQuotationForm, "timestamps")


class ContractDeleteForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
