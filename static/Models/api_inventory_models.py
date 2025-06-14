# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 17:04 $"

from flask_restx import fields
from werkzeug.datastructures import FileStorage
from wtforms.fields.list import FieldList

from static.Models.api_models import date_filter
from static.constants import api
from wtforms.fields.form import FormField
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import StringField, BooleanField
from wtforms.form import Form
from wtforms import IntegerField
from wtforms.validators import InputRequired, NumberRange

code_model = api.model(
    "CodeAMC",
    {
        "tag": fields.String(required=True, description="The code tag"),
        "value": fields.String(required=True, description="The code value"),
    },
)
locations_model = api.model(
    "LocationAMC",
    {
        "location_1": fields.String(required=True, description="The location 1"),
        "location_2": fields.String(required=True, description="The location 2"),
    },
)

product_model_new = api.model(
    "ProductAMCNew",
    {
        "name": fields.String(required=True, description="The product name"),
        "sku": fields.String(required=True, description="The product sku"),
        "udm": fields.String(required=True, description="The product udm"),
        "stock": fields.Float(required=True, description="The product stock"),
        "category_name": fields.String(
            required=True, description="The product category name or id for edition"
        ),
        "supplier_name": fields.String(
            required=True, description="The product supplier name or id for edition"
        ),
        "is_tool": fields.Integer(required=True, description="The product is tool"),
        "is_internal": fields.Integer(
            required=True, description="The product is internal"
        ),
        "quantity_move": fields.Float(
            required=False,
            description="The product quantity movement in for news (optional)",
        ),
        "codes": fields.List(fields.Nested(code_model), required=False),
        "locations": fields.Nested(locations_model, required=False),
        "brand": fields.String(required=False, description="The product brand."),
        "epp":  fields.Integer(required=True, description="The product epp", example=0),
    },
)

product_model_update = api.model(
    "ProductAMCUpdate",
    {
        "id": fields.Integer(required=True, description="The product id", example=1),
        "name": fields.String(required=True, description="The product name"),
        "sku": fields.String(required=True, description="The product sku"),
        "udm": fields.String(required=True, description="The product udm"),
        "stock": fields.Float(required=True, description="The product stock"),
        "category_name": fields.String(
            required=True, description="The product category name or id for edition"
        ),
        "supplier_name": fields.String(
            required=True, description="The product supplier name or id for edition"
        ),
        "is_tool": fields.Integer(required=True, description="The product is tool"),
        "is_internal": fields.Integer(
            required=True, description="The product is internal"
        ),
        "quantity_move": fields.Float(
            required=False,
            description="The product quantity movement in or out, for movements creation. "
            "If negative, out movements with abs(value), else in movements with value",
        ),
        "codes": fields.List(fields.Nested(code_model), required=False),
        "locations": fields.Nested(locations_model, required=False),
        "brand": fields.String(required=False, description="The product brand."),
        "epp":  fields.Integer(required=True, description="The product epp", example=0),
    },
)

products_output_model = api.model(
    "ProductsOutAMC",
    {
        "data": fields.List(fields.Nested(product_model_update)),
        "msg": fields.String(required=False, description="The message"),
        "error": fields.String(required=False, description="The error"),
    },
)

product_insert_model = api.model(
    "ProductInputAMC",
    {
        "info": fields.Nested(product_model_new),
    },
)

product_update_model = api.model(
    "ProductUpdateAMC",
    {
        "info": fields.Nested(product_model_new),
        "id": fields.Integer(required=True, description="The product id to modify"),
    },
)

product_delete_model = api.model(
    "ProductDeleteAMC",
    {"id": fields.Integer(required=True, description="The product id to delete")},
)


products_list_post_model = api.model(
    "ProductsListPostAMC",
    {
        "products_insert": fields.List(fields.Nested(product_model_new)),
        "products_update": fields.List(fields.Nested(product_model_update)),
    },
)


category_model = api.model(
    "CategoryAMC",
    {
        "id": fields.Integer(required=True, description="The category id"),
        "name": fields.String(required=True, description="The category name"),
    },
)

categories_output_model = api.model(
    "CategoriesOutAMC",
    {
        "data": fields.List(fields.Nested(category_model)),
        "msg": fields.String(required=False, description="The message"),
        "error": fields.String(required=False, description="The error"),
    },
)

movement_model = api.model(
    "MovementSAMC",
    {
        "id_product": fields.Integer(
            required=True, description="The product id", example=1
        ),
        "type_m": fields.String(
            required=True, description="The movement type", example="entrada"
        ),
        "quantity": fields.Float(required=True, description="The movement quantity"),
        "sm_id": fields.String(
            required=True, description="The movement id", example="folio-sm"
        ),
        "old_stock": fields.Float(
            required=True, description="The movement old stock", example=1.0
        ),
        "reference": fields.String(
            required=True, description="The movement reference", example="reference"
        ),
    },
)

movements_list_post_model = api.model(
    "MovementsListPostAMC",
    {
        "movements": fields.List(fields.Nested(movement_model)),
    },
)

expected_files_almacen = api.parser()
expected_files_almacen.add_argument(
    "file", type=FileStorage, location="files", required=True
)

file_movements_request_model = api.model(
    "FileMovementsAMC",
    {
        "date_init": fields.String(
            required=True,
            description="The date init for movements",
            example="2024-01-01",
        ),
        "date_end": fields.String(
            required=True,
            description="The date end for movements",
            example="2024-01-01",
        ),
        "type": fields.String(
            required=True, description="The type of movements", example="entrada"
        ),
    },
)

format_barcode_model = api.model(
    "FormatBarcodeAMC",
    {
        "tilte": fields.String(required=True, example="Title example"),
        "title_font": fields.Integer(required=True, example=14),
        "title_offset": fields.List(fields.Float, required=True, example=[0, 0]),
        "code": fields.String(required=True, example="A123456789"),
        "code_font": fields.Integer(required=True, example=7),
        "code_offset": fields.List(fields.Float, required=True, example=[0, 0]),
        "sku": fields.String(required=True, example="SKU123456789"),
        "sku_font": fields.Integer(required=True, example=6),
        "sku_offset": fields.List(fields.Float, required=True, example=[0, 0]),
        "name": fields.String(required=True, example="Producto de prueba"),
        "name_font": fields.Integer(required=True, example=9),
        "name_offset": fields.List(fields.Float, required=True, example=[0, 0]),
        "name_width": fields.Integer(required=True, example=20),
        "type_code": fields.String(required=True, example="128"),
        "codebar_size": fields.List(fields.Float, required=True, example=[0.4, 20]),
        "codebar_offset": fields.List(fields.Float, required=True, example=[0, -7]),
        "pagesize": fields.String(required=True, example="default"),
        "orientation": fields.String(required=True, example="horizontal"),
        "border_on": fields.Boolean(required=True, example=True),
    },
)

file_barcode_request_model = api.model(
    "FileBarcodeAMC",
    {
        "id_product": fields.Integer(
            required=True, description="The product id", example=1
        ),
        "format": fields.Nested(format_barcode_model),
    },
)

file_barcode_multiple_request_model = api.model(
    "FileBarcodeMultipleRequestAMC",
    {
        "data": fields.List(fields.Nested(file_barcode_request_model)),
    },
)


class CodesForm(Form):
    tag = StringField("tag", validators=[])
    value = StringField("value", validators=[])


class LocationsForm(Form):
    location_1 = StringField("location_1", validators=[], default="")
    location_2 = StringField("location_2", validators=[], default="")


class ProductInsertForm(Form):
    name = StringField("name", validators=[InputRequired()])
    sku = StringField("sku", validators=[InputRequired()])
    udm = StringField("udm", validators=[InputRequired()])
    stock = FloatField("stock", validators=[], default=0.0)
    category_name = StringField("category_name", validators=[], default=None)
    supplier_name = StringField("supplier_name", validators=[], default=None)
    is_tool = IntegerField("is_tool", validators=[], default=0)
    is_internal = IntegerField("is_internal", validators=[], default=0)
    codes = FieldList(FormField(CodesForm), validators=[], default=[])
    locations = FormField(LocationsForm)
    brand = StringField("brand", validators=[], default="")
    epp = IntegerField("epp", validators=[], default=0)


class ProductUpdateForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
    name = StringField("name", validators=[InputRequired()])
    sku = StringField("sku", validators=[InputRequired()])
    udm = StringField("udm", validators=[InputRequired()])
    stock = FloatField("stock", validators=[InputRequired()])
    category_name = StringField("category_name", validators=[], default=None)
    supplier_name = StringField("supplier_name", validators=[], default=None)
    is_tool = IntegerField("is_tool", validators=[], default=0)
    is_internal = IntegerField("is_internal", validators=[], default=0)
    quantity_move = FloatField("quantity_move", validators=[], default=0)
    codes = FieldList(FormField(CodesForm), validators=[], default=[])
    locations = FormField(LocationsForm)
    brand = StringField("brand", validators=[], default="")
    epp = IntegerField("epp", validators=[], default=0)


class ProductPostForm(Form):
    info = FormField(ProductInsertForm)


class ProductPutForm(Form):
    info = FormField(ProductUpdateForm)
    # id = IntegerField(
    #     "id",
    #     validators=[InputRequired(message="Id is required or value 0 not accepted")],
    # )


class ProductsListPostForm(Form):
    products_insert = FieldList(FormField(ProductInsertForm))
    products_update = FieldList(FormField(ProductUpdateForm))


class MovementForm(Form):
    id_product = IntegerField(
        "id_product",
        validators=[
            InputRequired(message="Id product is required or value 0 not accepted")
        ],
    )
    type_m = StringField("type", validators=[InputRequired()], default="entrada")
    quantity = FloatField("quantity", validators=[InputRequired()])
    sm_id = StringField("sm_id", validators=[], default="")
    old_stock = FloatField(
        "old_stock", validators=[NumberRange(min=-100.0)], default=0.0
    )
    # old_stock = FloatField("old_stock", validators=[], default=0.0)
    reference = StringField("reference", validators=[], default="")


class MovementsListPostForm(Form):
    movements = FieldList(FormField(MovementForm))


class ProductDeleteForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )


class FileMovementsForm(Form):
    date_init = StringField(
        "date_init", validators=[InputRequired()], filters=[date_filter]
    )
    date_end = StringField(
        "date_end", validators=[InputRequired()], filters=[date_filter]
    )
    type = StringField("type", validators=[], default="all")


class FormatBarcodeForm(Form):
    title = StringField("title", validators=[], default="Title example")
    title_font = IntegerField("title_font", validators=[], default=14)
    title_offset = FieldList(FloatField(), validators=[], default=[0, 0])
    code = StringField("code", validators=[], default="A123456789")
    code_font = IntegerField("code_font", validators=[], default=7)
    code_offset = FieldList(FloatField(), validators=[], default=[0, 0])
    sku = StringField("sku", validators=[], default="SKU123456789")
    sku_font = IntegerField("sku_font", validators=[], default=6)
    sku_offset = FieldList(FloatField(), validators=[], default=[0, 0])
    name = StringField("name", validators=[], default="Producto de prueba")
    name_font = IntegerField("name_font", validators=[], default=9)
    name_offset = FieldList(FloatField(), validators=[], default=[0, 0])
    name_width = FloatField("name_width", validators=[], default=20)
    type_code = StringField("type_code", validators=[], default="128")
    codebar_size = FieldList(FloatField(), validators=[], default=[0.4, 20])
    codebar_offset = FieldList(FloatField(), validators=[], default=[0, -7])
    pagesize = StringField("pagesize", validators=[], default="default")
    orientation = StringField("orientation", validators=[], default="horizontal")
    border_on = BooleanField("border_on", validators=[], default=True)


class FileBarcodeForm(Form):
    id_product = IntegerField(
        "id_product",
        validators=[
            InputRequired(message="Id product is required or value 0 not accepted")
        ],
    )
    format = FormField(FormatBarcodeForm, "format")


class FileBarcodeMultipleForm(Form):
    data = FieldList(FormField(FileBarcodeForm), "data")
