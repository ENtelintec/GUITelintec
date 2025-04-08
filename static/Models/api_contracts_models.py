# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:08 $"

from werkzeug.datastructures import FileStorage
from wtforms.form import Form
from wtforms.validators import InputRequired

from static.Models.api_models import date_filter
from static.constants import api
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
        "emp_id": fields.Integer(required=True, description="The quotation emp id"),
    },
)
products_quotation_model = api.model(
    "ProductsQuotation",
    {
        "partida": fields.Integer(
            required=True,
            description="The product partida (numeration item)",
            example=1,
        ),
        "revision": fields.Integer(
            required=True, description="The product revision", example=0
        ),
        "type_p": fields.String(required=True, description="The product type"),
        "marca": fields.String(required=True, description="The product marca"),
        "n_parte": fields.String(required=True, description="The product part number"),
        "description_small": fields.String(
            required=True, description="The product descripcion_corta"
        ),
        "description": fields.String(
            required=True, description="The product description"
        ),
        "quantity": fields.Integer(required=True, description="The product quantity"),
        "udm": fields.String(required=True, description="The product udm"),
        "price_unit": fields.Float(
            required=True, description="The quotation price unit"
        ),
        "comment": fields.String(required=False, description="The product comment"),
        "id": fields.Integer(
            required=False, description="The product id in the database"
        ),
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
        "remitos": fields.String(required=False, description="The remitos information"),
        "fecha_solicitud": fields.String(
            required=False, description="The request date"
        ),
        "coordinador": fields.String(required=False, description="The coordinator"),
        "ceco": fields.String(required=False, description="The CECO (cost center)"),
        "descripcion": fields.String(required=False, description="The description"),
        "estatus": fields.String(required=False, description="The status"),
        "sgd": fields.String(required=False, description="The SGD information"),
        "fecha_sg": fields.String(required=False, description="The SGD date"),
        "estatus_remision": fields.String(
            required=False, description="The remision status"
        ),
        "remitos_enviados": fields.String(
            required=False, description="The remitos sent"
        ),
        "estatus_hes": fields.String(required=False, description="The HES status"),
        "num_hes": fields.String(required=False, description="The HES number"),
        "liberacion_hes": fields.String(required=False, description="The HES release"),
        "saldo_pedido": fields.String(required=False, description="The order balance"),
        "remision_mxn": fields.String(
            required=False, description="The remision in MXN"
        ),
        "saldo_comprometido": fields.String(
            required=False, description="The committed balance"
        ),
        "saldo_hes": fields.String(required=False, description="The HES balance"),
        "saldo_facturado": fields.String(
            required=False, description="The invoiced balance"
        ),
        "observaciones": fields.String(required=False, description="The observations"),
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
        "quotation_id": fields.Integer(
            required=True, description="The quotation id", example=1
        ),
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
        "products": fields.List(
            fields.Nested(products_quotation_model), required=False
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


expected_files_quotation = api.parser()
expected_files_quotation.add_argument(
    "file",
    type=FileStorage,
    location="files",
    required=True,
)

expected_files_contract = api.parser()
expected_files_contract.add_argument(
    "file",
    type=FileStorage,
    location="files",
    required=True,
)

expected_files_contract_comparison = api.parser()
expected_files_contract_comparison.add_argument(
    "file",
    type=FileStorage,
    location="files",
    required=True,
)
expected_files_contract_comparison.add_argument(
    "id_quotation",
    type=int,
    location="form",
    required=True,
)

contract_settings_model = api.model(
    "ContractSettings",
    {
        "phrase": fields.String(required=True, description="The contract phrase"),
        "pattern": fields.String(required=True, description="The contract pattern"),
    },
)


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
    client_id = IntegerField(
        "client_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    emp_id = IntegerField(
        "emp_id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )


class ProductsQuotationForm(Form):
    partida = IntegerField("partida", validators=[InputRequired()])
    revision = IntegerField("revision", validators=[], default=0)
    type_p = StringField("type_p", validators=[InputRequired()])
    marca = StringField("marca", validators=[InputRequired()])
    n_parte = StringField("n_parte", validators=[InputRequired()])
    description = StringField("description", validators=[], default="")
    description_small = StringField("description_small", validators=[], default="")
    quantity = IntegerField("quantity", validators=[], default=0)
    udm = StringField("udm", validators=[InputRequired()])
    price_unit = FloatField("price_unit", validators=[], default=0.0)
    id = IntegerField("id", validators=[], default=None)
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
        "client_id", validators=[InputRequired(message="Invalid id or 0 not accepted")]
    )
    contract_number = StringField("contract_number", validators=[InputRequired()])
    identifier = StringField("identifier", validators=[InputRequired()])
    abbreviation = StringField("abbreviation", validators=[InputRequired()])
    remitos = StringField("remitos", validators=[], default="")
    fechaSolicitud = StringField("fechaSolicitud", validators=[], filters=[date_filter])
    coordinador = StringField("coordinador", validators=[], default="")
    ceco = StringField("ceco", validators=[], default="")
    descripcion = StringField("descripcion", validators=[], default="")
    estatus = StringField("estatus", validators=[], default="")
    sgd = StringField("sgd", validators=[], default="")
    fecha_sg = StringField("fecha_sg", validators=[], filters=[date_filter])
    estatus_remision = StringField("estatus_remision", validators=[], default="")
    remitos_enviados = StringField("remitos_enviados", validators=[], default="")
    estatus_hes = StringField("estatus_hes", validators=[], default="")
    num_hes = StringField("num_hes", validators=[], default="")
    liberacion_hes = StringField("liberacion_hes", validators=[], default="")
    saldo_pedido = StringField("saldo_pedido", validators=[], default="")
    remision_mxn = StringField("remision_mxn", validators=[], default="")
    saldo_comprometido = StringField("saldo_comprometido", validators=[], default="")
    saldo_hes = StringField("saldo_hes", validators=[], default="")
    saldo_facturado = StringField("saldo_facturado", validators=[], default="")
    observaciones = StringField("observaciones", validators=[], default="")


class ContractInsertForm(Form):
    metadata = FormField(MetadataContractForm, "metadata")
    quotation_id = IntegerField("quotation_id", validators=[], default=0)
    products = FieldList(FormField(ProductsQuotationForm, "products"))


class ContractUpdateForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )
    metadata = FormField(MetadataContractForm, "metadata")
    quotation_id = IntegerField("quotation_id", validators=[], default=None)
    timestamps = FormField(TimestampsQuotationForm, "timestamps")


class ContractDeleteForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="Invalid id or 0 not acepted")]
    )


class ContractSettingsForm(Form):
    phrase = StringField("phrase", validators=[InputRequired()])
    pattern = StringField("pattern", validators=[InputRequired()])
