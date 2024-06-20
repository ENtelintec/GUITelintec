# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 20/jun./2024  at 15:23 $'

import json

from templates.controllers.contracts.contracts_controller import get_contract
from templates.controllers.contracts.quotations_controller import get_quotation


def get_quotations(id_quotation=None):
    id_quotation = id_quotation if id_quotation != -1 else None
    flag, error, result = get_quotation(id_quotation)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    if id_quotation is None:
        id_q, metadata, products, creation, timestamps = result
        data_out = {"id": id_q, "metadata": json.loads(metadata), "products": json.loads(products),
                    "creation": creation, "timestamps": json.loads(timestamps)}
        return {"data": [data_out], "msg": None}, 200
    else:
        data_out = []
        for item in result:
            id_q, metadata, products, creation, timestamps = item
            data_out.append({"id": id_q, "metadata": json.loads(metadata), "products": json.loads(products),
                             "creation": creation, "timestamps": json.loads(timestamps)})
        return {"data": data_out, "msg": "Ok"}, 200  


def get_contracts(id_contract=None):
    id_contract = id_contract if id_contract != -1 else None
    flag, error, result = get_contract(id_contract)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    if id_contract is None:
        id_c, metadata, creation, quotation_id, timestamps = result
        data_out = {"id": id_c, "metadata": json.loads(metadata), "creation": creation,
                    "quotation_id": quotation_id, "timestamps": json.loads(timestamps)}
        return {"data": [data_out], "msg": None}, 200
    else:
        data_out = []
        for item in result:
            id_c, metadata, creation, quotation_id, timestamps = item
            data_out.append({"id": id_c, "metadata": json.loads(metadata), "creation": creation,
                             "quotation_id": quotation_id, "timestamps": json.loads(timestamps)})
        return {"data": data_out, "msg": "Ok"}, 200
