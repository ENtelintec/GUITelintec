# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:23 $"

import json

from static.extensions import filepath_settings
from templates.controllers.contracts.contracts_controller import (
    get_contract,
    get_contract_from_abb,
)
from templates.controllers.contracts.quotations_controller import get_quotation
from templates.controllers.customer.customers_controller import get_customer_amc_by_id
from templates.controllers.material_request.sm_controller import get_folios_by_pattern
from templates.resources.methods.Functions_Aux_Admin import (
    read_file_tenium_contract,
    read_exel_products_quotation,
    compare_file_quotation,
)

dict_depts_identifiers = {
    "administracion": "ADMON",
    "almacen": "ALM",
    "control de activos": ["CDA-VEH", "TI"],
    "direccion": "DIRE",
    "operaciones": "OP",
    "recursos humanos": "RH",
    "seguridad": "sst",
    "sistema de gestion integral": "sgi",
}


def get_quotations(id_quotation=None):
    try:
        id_quotation = id_quotation if int(id_quotation) != -1 else None
    except ValueError:
        return {"data": None, "msg": "Id invalido"}, 400
    flag, error, result = get_quotation(id_quotation)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    if id_quotation is not None:
        id_q, metadata, products, creation, timestamps = result
        data_out = {
            "id": id_q,
            "metadata": json.loads(metadata),
            "products": json.loads(products),
            "creation": creation,
            "timestamps": json.loads(timestamps),
        }
        return {"data": [data_out], "msg": None}, 200
    else:
        data_out = []
        for item in result:
            id_q, metadata, products, creation, timestamps = item
            data_out.append(
                {
                    "id": id_q,
                    "metadata": json.loads(metadata),
                    "products": json.loads(products),
                    "creation": creation,
                    "timestamps": json.loads(timestamps),
                }
            )
        return {"data": data_out, "msg": "Ok"}, 200


def get_contracts(id_contract=None):
    id_contract = id_contract if id_contract != -1 else None
    flag, error, result = get_contract(id_contract)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    if id_contract is None:
        id_c, metadata, creation, quotation_id, timestamps = result
        data_out = {
            "id": id_c,
            "metadata": json.loads(metadata),
            "creation": creation,
            "quotation_id": quotation_id,
            "timestamps": json.loads(timestamps),
        }
        return {"data": [data_out], "msg": None}, 200
    else:
        data_out = []
        for item in result:
            id_c, metadata, creation, quotation_id, timestamps = item
            data_out.append(
                {
                    "id": id_c,
                    "metadata": json.loads(metadata),
                    "creation": creation,
                    "quotation_id": quotation_id,
                    "timestamps": json.loads(timestamps),
                }
            )
        return {"data": data_out, "msg": "Ok"}, 200


def get_folio_from_contract_ternium(contract_abb: str):
    flag, error, result = get_contract_from_abb(contract_abb)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    folio_sm = "SM"
    metadata = json.loads(result[1])
    contract_number = metadata["contract_number"]
    idn_contract = contract_number[-4:]
    folio = folio_sm + "-" + idn_contract
    flag, error, folios = get_folios_by_pattern(folio)
    numbers = []
    for item in folios:
        try:
            numbers.append(int(item[0][-3:]))
        except Exception as e:
            print(e, "item: ", item)
            continue
    numbers = numbers if len(numbers) > 0 else [0]
    numbers.sort()
    folio = folio + "-" + str(numbers[-1] + 1).zfill(3)
    flag, error, client_data = get_customer_amc_by_id(metadata["client_id"])
    client_data = client_data if flag else [metadata["client_id"], "", "", "", "", ""]
    data = {
        "folio": folio,
        "planta": metadata["planta"],
        "area": metadata["area"],
        "location": metadata["location"],
        "client": {
            "id": metadata["client_id"],
            "name": client_data[1],
            "email": client_data[2],
            "phone": client_data[3],
            "rfc": client_data[4],
            "address": client_data[5],
        },
        "identifier": metadata["identifier"],
    }
    return {"data": data, "msg": "Ok"}, 200


def folio_from_department(department_key: str):
    identifier = dict_depts_identifiers.get(department_key.lower())
    if identifier is None:
        return {"data": None, "msg": "Department not found"}, 400
    folio_list = []
    if isinstance(identifier, str):
        folio = f"SM-{identifier.upper()}"
        folio_list.append(folio)
    elif isinstance(identifier, list):
        for idd in identifier:
            folio = f"SM-{idd.upper()}"
            folio_list.append(folio)
    folios_out = []
    for folio in folio_list:
        flag, error, folios = get_folios_by_pattern(folio)
        numbers = []
        for item in folios:
            try:
                numbers.append(int(item[0][-3:]))
            except Exception as e:
                print(e, "item: ", item)
                continue
        numbers = numbers if len(numbers) > 0 else [0]
        numbers.sort()
        folio = folio + "-" + str(numbers[-1] + 1).zfill(3)
        folios_out.append(folio)
    data = {"folios": folios_out}
    return {"data": data, "msg": "Ok"}, 200


def products_quotation_from_file(path: str):
    products = read_exel_products_quotation(path)
    return {"data": products, "msg": "Ok"}, 200


def products_contract_from_file(data: dict):
    settings = json.loads(filepath_settings)
    flag = False
    data["phrase"] = settings.get("phrase_pdf_contract")
    data["pattern"] = settings.get("pattern_pdf_contract")
    if data["phrase"] is None or data["pattern"] is None:
        flag = True
        data["phrase"] = settings.get("phrase_pdf_contract_default")
        data["pattern"] = settings.get("pattern_pdf_contract_default")
    products = read_file_tenium_contract(data["path"], data["pattern"], data["phrase"])
    if len(products) == 0 and not flag:
        data["phrase"] = settings.get("phrase_pdf_contract_default")
        data["pattern"] = settings.get("pattern_pdf_contract_default")
        products = read_file_tenium_contract(
            data["path"], data["pattern"], data["phrase"]
        )
    return {"data": products, "msg": "Ok"}, 200


def modify_pattern_phrase_contract_pdf(data: dict):
    e = None
    try:
        settings = json.loads(filepath_settings)
        settings["phrase_pdf_contract"] = data["phrase"]
        settings["pattern_pdf_contract"] = data["pattern"]
        with open(filepath_settings, "w") as file:
            json.dump(settings, file, indent=4)
    except Exception as e:
        print(e)
    return True, str(e)


def compare_file_and_quotation(data: dict):
    settings = json.loads(filepath_settings)
    data["phrase"] = settings.get("phrase_pdf_contract")
    data["pattern"] = settings.get("pattern_pdf_contract")
    if data["phrase"] is None or data["pattern"] is None:
        data["phrase"] = settings.get("phrase_pdf_contract_default")
        data["pattern"] = settings.get("pattern_pdf_contract_default")
    flag, error, data_quotation = get_quotation(data["id_quotation"])
    products_contract = read_file_tenium_contract(
        data["path"], data["pattern"], data["phrase"]
    )
    data_out, code = compare_file_quotation(data_quotation, products_contract)
    return data_out, code
