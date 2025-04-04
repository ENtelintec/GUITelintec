# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:23 $"

import json

import pandas as pd

from static.constants import filepath_settings, log_file_admin
from templates.Functions_Utils import create_notification_permission
from templates.controllers.contracts.contracts_controller import (
    get_contract,
    get_contract_from_abb,
    create_contract,
)
from templates.controllers.contracts.quotations_controller import (
    get_quotation,
    create_quotation,
)
from templates.controllers.customer.customers_controller import (
    get_customer_amc_by_id,
    get_all_customers_db,
    create_customer_db,
    update_customer_db,
    delete_customer_db,
)
from templates.controllers.departments.heads_controller import (
    get_heads_db,
    insert_head_DB,
    update_head_DB,
    delete_head_DB,
)
from templates.controllers.material_request.sm_controller import get_folios_by_pattern
from templates.controllers.purchases.purchases_admin_controller import (
    get_purchases_admin_db,
)
from templates.controllers.supplier.suppliers_controller import (
    create_supplier_amc,
    update_supplier_amc,
    delete_supplier_amc,
    get_all_suppliers_amc,
)
from templates.misc.Functions_Files import write_log_file
from templates.resources.methods.Functions_Aux_Admin import (
    read_file_tenium_contract,
    read_exel_products_quotation,
    compare_file_quotation,
    read_exel_products_bidding,
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
        id_q, metadata, products, creation, timestamps, company, emission = result
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
            id_q, metadata, products, creation, timestamps, company, emission = item
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


def validate_metadata(metadata: dict):
    return {
        "emission": metadata.get("emission", ""),
        "quotation_code": metadata.get("quotation_code", ""),
        "planta": metadata.get("planta", ""),
        "area": metadata.get("area", ""),
        "location": metadata.get("location", ""),
        "client_id": metadata.get("client_id", 0),
        "contract_number": metadata.get("contract_number", ""),
        "identifier": metadata.get("identifier", ""),
        "abbreviation": metadata.get("abbreviation", ""),
        "remitos": metadata.get("remitos", ""),
        "fecha_solicitud": metadata.get("fecha_solicitud", ""),
        "coordinador": metadata.get("coordinador", ""),
        "ceco": metadata.get("ceco", ""),
        "descripcion": metadata.get("descripcion", ""),
        "estatus": metadata.get("estatus", ""),
        "sgd": metadata.get("sgd", ""),
        "fecha_sg": metadata.get("fecha_sg", ""),
        "estatus_remision": metadata.get("estatus_remision", ""),
        "remitos_enviados": metadata.get("remitos_enviados", ""),
        "estatus_hes": metadata.get("estatus_hes", ""),
        "num_hes": metadata.get("num_hes", ""),
        "liberacion_hes": metadata.get("liberacion_hes", ""),
        "saldo_pedido": metadata.get("saldo_pedido", ""),
        "remision_mxn": metadata.get("remision_mxn", ""),
        "saldo_comprometido": metadata.get("saldo_comprometido", ""),
        "saldo_hes": metadata.get("saldo_hes", ""),
        "saldo_facturado": metadata.get("saldo_facturado", ""),
        "observaciones": metadata.get("observaciones", ""),
    }


def get_contracts(id_contract=None):
    id_contract = None if id_contract == -1 or id_contract == "-1" else id_contract
    flag, error, result = get_contract(id_contract)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    if id_contract is not None:
        id_c, metadata, creation, quotation_id, timestamps = result
        metadata = validate_metadata(json.loads(metadata))
        data_out = {
            "id": id_c,
            "metadata": metadata,
            "creation": creation,
            "quotation_id": quotation_id,
            "timestamps": json.loads(timestamps),
        }
        return {"data": [data_out], "msg": None}, 200
    else:
        data_out = []
        for item in result:
            id_c, metadata, creation, quotation_id, timestamps = item
            metadata = validate_metadata(json.loads(metadata))
            data_out.append(
                {
                    "id": id_c,
                    "metadata": metadata,
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


def get_data_dict_purchases(data):
    limit = (data.get("limit_min"), data.get("limit_max"))
    flag, error, result = get_purchases_admin_db(limit)
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in result:
        data_out.append(
            {
                "id": item[0],
                "metadata": json.loads(item[1]),
                "creation": item[2],
                "timestamps": json.loads(item[3]),
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def get_data_table_purchases(data):
    limit = (data.get("limit_min"), data.get("limit_max"))
    flag, error, result = get_purchases_admin_db(limit)
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in result:
        metadata = json.loads(item[1])
        timestamps = json.loads(item[3])
        data_out.append(
            [
                item[0],
                metadata.get("name", ""),
                metadata.get("quantity", ""),
                metadata.get("supplier", ""),
                metadata.get("link", ""),
                metadata.get("comments", ""),
                metadata.get("date_required", ""),
                item[2],
                timestamps.get("complete", ""),
                timestamps.get("update", ""),
            ]
        )
    columns = [
        "ID",
        "Nombre",
        "Cantidad",
        "Proveedor",
        "Link",
        "Comentarios",
        "Fecha requerida",
        "Creacion",
        "Completado",
        "Actualizado",
    ]

    return {"data": data_out, "columns": columns, "msg": "Ok"}, 200


def get_all_clients_data():
    flag, error, data = get_all_customers_db()

    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in data:
        data_out.append(
            {
                "id": item[0],
                "name": item[1].upper(),
                "email": item[2],
                "phone": item[3],
                "rfc": item[4],
                "address": item[5],
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def insert_customer(data):
    flag, error, result = create_customer_db(
        data.get("name").upper(),
        data.get("email").upper(),
        data.get("phone"),
        data.get("rfc").upper(),
        data.get("address"),
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    return {"data": result, "msg": "Ok"}, 201


def update_customer(data):
    flag, error, result = update_customer_db(
        data.get("id"),
        data.get("name").upper(),
        data.get("email").upper(),
        data.get("phone"),
        data.get("rfc").upper(),
        data.get("address"),
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    return {"data": result, "msg": "Ok"}, 200


def delete_customer(data):
    flag, error, result = delete_customer_db(data.get("id"))
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    return {"data": result, "msg": "Ok"}, 200


def get_all_suppliers_data():
    flag, error, data = get_all_suppliers_amc()
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in data:
        extra_info = json.loads(item[8])
        brands = extra_info.get("brands", [])
        brands.sort()
        data_out.append(
            {
                "id": item[0],
                "name": item[1],
                "seller_name": item[2],
                "email": item[3],
                "phone": item[4],
                "address": item[5],
                "web_url": item[6],
                "type": item[7],
                "brands": brands,
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def insert_supplier(data):
    # name, seller_name, seller_email, phone, address, web_url, type, extra_info
    flag, error, result = create_supplier_amc(
        data.get("name").upper(),
        data.get("seller_name").upper(),
        data.get("email").upper(),
        data.get("phone"),
        data.get("address"),
        data.get("web"),
        data.get("type"),
        data.get("extra_info"),
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    return {"data": result, "msg": "Ok"}, 201


def update_supplier(data):
    flag, error, result = update_supplier_amc(
        data.get("id"),
        data.get("name").upper(),
        data.get("seller_name").upper(),
        data.get("email").upper(),
        data.get("phone"),
        data.get("address"),
        data.get("web"),
        data.get("type"),
        data.get("extra_info"),
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    return {"data": result, "msg": "Ok"}, 200


def delete_supplier(data):
    flag, error, result = delete_supplier_amc(data.get("id"))
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    return {"data": result, "msg": "Ok"}, 200


def create_contract_from_api(data, data_token):
    if data.get("quotation_id", 0) == 0:
        flag, error, result = create_quotation(
            data["metadata"], data["products"], status=2
        )
        if not flag:
            return {"data": None, "msg": str(error)}, 400
        id_quotation = result
        flag, error, result = create_contract(id_quotation, data["metadata"])
    else:
        flag, error, result = create_contract(data["quotation_id"], data["metadata"])

    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg = f"Contrato creado con ID-{result} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg, ["administracion"], "Contrato Creado", data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 201


def fetch_heads(id_department: int):
    id_department = int(id_department) if id_department >= 0 else None
    flag, error, result = get_heads_db(id_department)
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in result:
        # heads.id, heads.name, heads.employee, heads.department, departments.name, UPPER(CONCAT(employees.name, ' ', employees.l_name)) as name_emp, employees.email, heads.extra_info "
        data_out.append(
            {
                "id": item[0],
                "name": item[1],
                "employee": item[2],
                "department": item[3],
                "department_name": item[4],
                "employee_name": item[5],
                "employee_email": item[6],
                "extra_info": json.loads(item[7]),
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def insert_head_from_api(data, data_token):
    extra_info = (
        json.loads(data["extra_info"])
        if isinstance(data["extra_info"], str)
        else data["extra_info"]
    )
    if "other_leaders" not in extra_info:
        extra_info["other_leaders"] = []
    flag, error, result = insert_head_DB(
        data["name"],
        data["department"],
        data["employee"],
        extra_info,
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg = f"Encargado creado con ID-{result} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg,
        ["administracion", "operaciones"],
        "Encargado Creado",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 201


def update_head_from_api(data, data_token):
    extra_info = (
        json.loads(data["extra_info"])
        if isinstance(data["extra_info"], str)
        else data["extra_info"]
    )
    if "other_leaders" not in extra_info:
        extra_info["other_leaders"] = []
    flag, error, result = update_head_DB(
        data["id"],
        data["department"],
        data["employee"],
        extra_info,
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg = f"Encargado actualizado con ID-{data['id']} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg,
        ["administracion", "operaciones"],
        "Encargado Actualizado",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 200


def delete_head_from_api(data, data_token):
    flag, error, result = delete_head_DB(data["id"])
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg = f"Encargado eliminado con ID-{data['id']} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg,
        ["administracion", "operaciones"],
        "Encargado Eliminado",
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 200


def items_quotation_from_file(data):
    products = read_exel_products_bidding(data["path"])
    if products is None:
        return {"data": None, "msg": "Error at file structure"}, 400
    return {"data": products, "msg": "Ok"}, 200
