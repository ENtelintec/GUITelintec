# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 20/jun./2024  at 15:08 $'
from flask_restx import fields
from static.extensions import api, format_timestamps


class MyDateFormat(fields.Raw):
    def format(self, value):
        return value.strftime(format_timestamps)


metadata_quotation_model = api.model("MetadataQuotation", {
    "emission": fields.String(required=True, description="The quotation emission date", example="2024-03-01"),
    "limit_date": fields.String(required=True, description="The quotation limit date", example="2024-03-01"),
    "quotation_code": fields.String(required=True, description="The quotation code"),
    "codigo": fields.String(required=True, description="The quotation codigo"),
    "company": fields.String(required=True, description="The quotation company"),
    "user": fields.String(required=True, description="The quotation user"),
    "phone": fields.String(required=True, description="The quotation phone number"),
    "email": fields.String(required=True, description="The quotation email"),
    "planta": fields.String(required=True, description="The quotation planta"),
    "area": fields.String(required=True, description="The quotation area"),
    "location": fields.String(required=True, description="The quotation location"),
    "client_id":  fields.Integer(required=True, description="The quotation client id")
})

products_quotation_model = api.model("ProductsQuotation", {
    "id": fields.Integer(required=True, description="The quotation id"),
    "description": fields.String(required=True, description="The quotation description"),
    "quantity": fields.Integer(required=True, description="The quotation quantity"),
    "udm": fields.String(required=True, description="The quotation udm"),
    "price_unit": fields.Float(required=True, description="The quotation price unit"),
    "comment": fields.String(required=True, description="The quotation comment")
})

timestamp_model_admin = api.model("TimestampAdmin", {
    "timestamp": fields.String(required=True, description="The quotation timestamp"),
    "comment": fields.String(required=True, description="The quotation comment")
})

timestamps_quotation_model = api.model("TimestampQuotation", {
    "complete": fields.Nested(timestamp_model_admin),
    "update": fields.List(fields.Nested(timestamp_model_admin))
})

quotation_model = api.model('Quotation', {
    "id": fields.Integer(required=True, description="The quotation id"),
    "metadata": fields.Nested(metadata_quotation_model),
    "products": fields.List(fields.Nested(products_quotation_model)),
    "creation": fields.String(required=True, description="The quotation creation date", example="2024-03-01"),
    "timestamps": fields.Nested(timestamps_quotation_model)
})    

answer_quotation_model = api.model('AnswerQuotation', {
    "msg": fields.String(required=True, description="The message"),
    "data": fields.List(fields.Nested(quotation_model))
})

quotation_model_insert = api.model('QuotationInsert', {
    "metadata": fields.Nested(metadata_quotation_model, required=True),
    "products": fields.List(fields.Nested(products_quotation_model), required=True)
})
quotation_model_update = api.model('QuotationUpdate', {
    "id": fields.Integer(required=True, description="The quotation id"),
    "metadata": fields.Nested(metadata_quotation_model),
    "products": fields.List(fields.Nested(products_quotation_model)),
    "timestamps": fields.Nested(timestamps_quotation_model)
})
quotation_model_delete = api.model('QuotationDelete', {
    "id": fields.Integer(required=True, description="The quotation id")
})

metadata_contract_model = api.model("MetadataContract", {
    "emission": fields.String(required=True, description="The quotation emission date", example="2024-03-01"),
    "limit_date": fields.String(required=True, description="The quotation limit date", example="2024-03-01"),
    "quotation_code": fields.String(required=True, description="The quotation code"),
    "codigo": fields.String(required=True, description="The quotation codigo"),
    "company": fields.String(required=True, description="The quotation company"),
    "user": fields.String(required=True, description="The quotation user"),
    "phone": fields.String(required=True, description="The quotation phone number"),
    "email": fields.String(required=True, description="The quotation email"),
    "planta": fields.String(required=True, description="The quotation planta"),
    "area": fields.String(required=True, description="The quotation area"),
    "location": fields.String(required=True, description="The quotation location"),
    "client_id":  fields.Integer(required=True, description="The quotation client id")
})

contract_model = api.model('ContractAdmin', {
    "id": fields.Integer(required=True, description="The contract id"),
    "metadata":  fields.Nested(metadata_contract_model),
    "creation": fields.String(required=True, description="The contract creation date", example="2024-03-01"),
    "timestamps": fields.Nested(timestamps_quotation_model),
    "quotation_id": fields.Nested(quotation_model)
})

answer_contract_model = api.model('AnswerContract', {
    "msg": fields.String(required=True, description="The message"),
    "data": fields.List(fields.Nested(contract_model))
})

contract_model_insert = api.model('ContractInsert', {
    "metadata": fields.Nested(metadata_contract_model, required=True),
    "quotation_id": fields.Nested(quotation_model, required=True)
})
contract_model_update = api.model('ContractUpdate', {
    "id": fields.Integer(required=True, description="The contract id"),
    "metadata": fields.Nested(metadata_contract_model),
    "quotation_id": fields.Nested(quotation_model),
    "timestamps": fields.Nested(timestamps_quotation_model)
})
contract_model_delete = api.model('ContractDelete', {
    "id": fields.Integer(required=True, description="The contract id")
})
