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
from wtforms.fields.simple import StringField
from wtforms.form import Form
from wtforms import IntegerField
from wtforms.validators import InputRequired


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
        "quantity_move": fields.Integer(
            required=False,
            description="The product quantity movement in or out, for movements creation. "
            "If negative, out movements with abs(value), else in movements with value",
        ),
        "codes": fields.List(fields.Nested(code_model), required=False),
        "locations": fields.Nested(locations_model, required=False),
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
        "quantity_move": fields.Integer(
            required=False,
            description="The product quantity movement in for news (optional)",
        ),
        "codes": fields.List(fields.Nested(code_model), required=False),
        "locations": fields.Nested(locations_model, required=False),
    },
)


products_output_model = api.model(
    "ProductsOutAMC",
    {
        "data": fields.List(fields.Nested(product_model_update)),
        "msg": fields.String(required=True, description="The message"),
    },
)

product_insert_model = api.model(
    "ProductInputAMC",
    {
        "info": fields.Nested(product_model_new),
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
        "msg": fields.String(required=True, description="The message"),
    },
)


supplier_model = api.model(
    "SupplierAMC",
    {
        "id": fields.Integer(required=True, description="The supplier id"),
        "name": fields.String(required=True, description="The supplier name"),
        "seller_email": fields.String(
            required=True, description="The supplier seller email"
        ),
        "seller_name": fields.String(
            required=True, description="The supplier seller name"
        ),
        "phone": fields.String(required=True, description="The supplier phone"),
        "address": fields.String(required=True, description="The supplier address"),
        "web_url": fields.String(required=True, description="The supplier web url"),
        "type": fields.String(required=True, description="The supplier type"),
    },
)

suppliers_output_model = api.model(
    "SuppliersOutAMC",
    {
        "data": fields.List(fields.Nested(supplier_model)),
        "msg": fields.String(required=True, description="The message"),
    },
)

# item["id_product"],
#             item["type_m"],
#             item["quantity"],
#             item["movement_date"],
#             item["sm_id"]
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
        "sm_id": fields.Integer(
            required=True, description="The movement id", example=1
        ),
        "old_stock": fields.Float(
            required=True, description="The movement old stock", example=1
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


class CodesForm(Form):
    tag = StringField("tag", validators=[InputRequired()])
    value = StringField("value", validators=[InputRequired()])


class LocationsForm(Form):
    location_1 = StringField("location_1", validators=[], default="")
    location_2 = StringField("location_2", validators=[], default="")


class ProductInsertForm(Form):
    name = StringField("name", validators=[InputRequired()])
    sku = StringField("sku", validators=[InputRequired()])
    udm = StringField("udm", validators=[InputRequired()])
    stock = FloatField("stock", validators=[InputRequired()])
    category_name = StringField("category_name", validators=[InputRequired()])
    supplier_name = StringField("supplier_name", validators=[InputRequired()])
    is_tool = IntegerField("is_tool", validators=[], default=0)
    is_internal = IntegerField("is_internal", validators=[], default=0)
    codes = FieldList(FormField(CodesForm), validators=[], default=[])
    locations = FormField(LocationsForm)


class ProductUpdateForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
    name = StringField("name", validators=[InputRequired()])
    sku = StringField("sku", validators=[InputRequired()])
    udm = StringField("udm", validators=[InputRequired()])
    stock = FloatField("stock", validators=[InputRequired()])
    category_name = StringField("category_name", validators=[InputRequired()])
    supplier_name = StringField("supplier_name", validators=[InputRequired()])
    is_tool = IntegerField("is_tool", validators=[], default=0)
    is_internal = IntegerField("is_internal", validators=[], default=0)
    quantity_move = IntegerField(
        "quantity_move",
        validators=[
            InputRequired(message="Quantity move is required or value 0 not accepted")
        ],
    )
    codes = FieldList(FormField(CodesForm), validators=[], default=[])
    locations = FormField(LocationsForm)


class ProductPostForm(Form):
    info = FormField(ProductInsertForm)


class ProductPutForm(Form):
    info = FormField(ProductUpdateForm)


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
    sm_id = IntegerField(
        "sm_id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
    old_stock = FloatField("old_stock", validators=[], default=0.0)


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
    type_m = StringField("type", validators=[], default="all")
