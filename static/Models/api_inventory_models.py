# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/may./2024  at 17:04 $"

from flask_restx import fields
from werkzeug.datastructures import FileStorage
from static.extensions import api
from wtforms.fields.form import FormField
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import StringField
from wtforms.form import Form
from wtforms import IntegerField
from wtforms.validators import InputRequired

product_model = api.model(
    "ProductAMC",
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
            required=True, description="The product quantity movement in"
        ),
    },
)

products_output_model = api.model(
    "ProductsOutAMC",
    {
        "data": fields.List(fields.Nested(product_model)),
        "msg": fields.String(required=True, description="The message"),
    },
)

product_insert_model = api.model(
    "ProductInputAMC",
    {
        "info": fields.Nested(product_model),
    },
)

product_delete_model = api.model(
    "ProductDeleteAMC",
    {"id": fields.Integer(required=True, description="The product id to delete")},
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

expected_files_almacen = api.parser()
expected_files_almacen.add_argument(
    "file", type=FileStorage, location="files", required=True
)


class ProductInsertForm(Form):
    name = StringField("name", validators=[InputRequired()])
    sku = StringField("sku", validators=[InputRequired()])
    udm = StringField("udm", validators=[InputRequired()])
    stock = FloatField("stock", validators=[InputRequired()])
    category_name = StringField("category_name", validators=[InputRequired()])
    supplier_name = StringField("supplier_name", validators=[InputRequired()])
    is_tool = IntegerField("is_tool", validators=[], default=0)
    is_internal = IntegerField("is_internal", validators=[], default=0)


class ProductUpdateForm(Form):
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
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )


class ProductPostForm(Form):
    info = FormField(ProductInsertForm)


class ProductPutForm(Form):
    info = FormField(ProductUpdateForm)


class ProductDeleteForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="Id is required or value 0 not accepted")],
    )
