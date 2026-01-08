# -*- coding: utf-8 -*-
from templates.controllers.supplier.suppliers_controller import delete_item_amc
from datetime import datetime
from templates.controllers.supplier.suppliers_controller import get_items_supplier_by_id
import json
import pandas as pd

from templates.controllers.supplier.suppliers_controller import update_item_amc
from templates.controllers.supplier.suppliers_controller import create_item_amc
from static.constants import (
    filepath_settings,
    log_file_admin,
    dict_deps,
    format_timestamps,
)
from templates.Functions_Utils import create_notification_permission
from templates.controllers.contracts.contracts_controller import (
    get_contract,
    create_contract,
    get_contracts_abreviations_db,
    update_contract,
    get_contract_by_client,
    get_contracts_by_ids,
    delete_contract,
)
from templates.controllers.contracts.quotations_controller import (
    get_quotation,
    create_quotation,
    create_items_quotation,
    delete_quotation,
    update_quotation,
    create_item_quotation,
    delete_item_quotation,
    update_item_quotation,
    delete_quotation_items,
    delete_contract_from_item_quotation,
)
from templates.controllers.customer.customers_controller import (
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
    get_heads_list_db,
    check_if_gerente,
    check_if_head_not_auxiliar,
    check_if_leader,
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
    read_exel_products_partidas,
)

__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:23 $"


def get_quotations(id_quotation: int | None = None):
    try:
        id_quotation = (
            id_quotation
            if id_quotation is not None and int(id_quotation) != -1
            else None
        )
    except ValueError:
        return {"data": None, "msg": "Id invalido"}, 400
    flag, error, result = get_quotation(id_quotation)
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    if id_quotation is not None:
        id_q, metadata, products, creation, timestamps = result
        creation = (
            creation.strftime(format_timestamps)
            if not isinstance(creation, str)
            else creation
        )
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
            creation = (
                creation.strftime(format_timestamps)
                if not isinstance(creation, str)
                else creation
            )
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
        # "emission": metadata.get("emission", ""),
        "quotation_code": metadata.get("quotation_code", ""),
        "planta": metadata.get("planta", ""),
        "area": metadata.get("area", ""),
        "location": metadata.get("location", ""),
        # "client_id": metadata.get("client_id", 0),
        # "contract_number": metadata.get("contract_number", ""),
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
    result = [result] if id_contract is not None else result
    # if id_contract is not None:
    #     id_c, metadata, creation, quotation_id, timestamps = result
    #     metadata = validate_metadata(json.loads(metadata))
    #     data_out = {
    #         "id": id_c,
    #         "metadata": metadata,
    #         "creation": creation,
    #         "quotation_id": quotation_id,
    #         "timestamps": json.loads(timestamps),
    #     }
    #     return {"data": [data_out], "msg": None}, 200
    # else:
    data_out = []
    for item in result:
        (
            id_c,
            metadata,
            creation,
            quotation_id,
            timestamps,
            code,
            client_id,
            emission,
        ) = item
        metadata = validate_metadata(json.loads(metadata))
        metadata["contract_number"] = code
        metadata["client_id"] = client_id
        metadata["emission"] = emission
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


def get_folio_from_contract_ternium(data_token):
    permissions = data_token.get("permissions", {}).values()
    contracts = []
    if any("administrator" in item.lower().split(".")[-1] for item in permissions):
        flag, error, contracts = get_contract_by_client(40)
        if not flag:
            return {"data": None, "msg": str(error)}, 400
    else:
        for check_func in (check_if_leader,):
            flag, error, result = check_func(data_token.get("emp_id"))
            if flag and len(result) > 0:
                ids = []
                for item in result:
                    print(item)
                    extra_info = json.loads(item[7])
                    ids += extra_info.get("contracts", [])
                    ids += extra_info.get("contracts_temp", [])
                print(ids)
                ids = list(set(ids))
                print(ids)
                flag, error, contracts = get_contracts_by_ids(ids)
                if not flag or len(contracts) == 0:
                    return {"data": None, "msg": str(error)}, 400
                break
            else:
                return {"data": None, "msg": str(error)}, 400
    data = []

    for result in contracts:
        folio_sm = "SM"
        metadata = json.loads(result[1])
        contract_number = result[5]
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
        data.append(
            {
                "folio": folio,
                "planta": metadata["planta"],
                "area": metadata["area"],
                "location": metadata["location"],
                "identifier": metadata["identifier"],
            }
        )
    return {"data": data, "msg": "Ok"}, 200


def get_department_identifiers(result):
    abbs = []
    for item in result:
        # print("dep", item)
        if item[9]:
            abbs.append(item[8])
        else:
            abbs.append(item[10])
            abbs.append(item[8]) if item[8] else None
    return abbs


def get_iddentifiers(data_token, all_data_keys):
    permissions = data_token.get("permissions", {}).values()
    if any(item.lower().split(".")[-1] in all_data_keys for item in permissions):
        flag, error, result_abb = get_contracts_abreviations_db()
        abbs_area = [item[0] for item in result_abb if item[4] == 0 and item[0] != ""]
    else:
        abbs_area = []
        for check_func in (check_if_gerente, check_if_head_not_auxiliar):
            flag, error, result = check_func(data_token.get("emp_id"))
            if flag and result:
                abbs_area = get_department_identifiers(result)
                break
            elif not flag:
                return {"data": None, "msg": str(error)}, 400
    identifiers = abbs_area
    if not identifiers:
        return {"data": None, "msg": "Folios for user not found"}, 401
    return identifiers, 200


def folio_from_department(data_token):
    abbs_list, code = get_iddentifiers(data_token, ["administrator"])
    if code != 200:
        return abbs_list, code
    folio_list = [
        f"SM-{abbreviation.upper()}"
        for abbreviation in abbs_list
        if isinstance(abbs_list, (str, list))
    ]
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
    try:
        settings = json.loads(filepath_settings)
        settings["phrase_pdf_contract"] = data["phrase"]
        settings["pattern_pdf_contract"] = data["pattern"]
        with open(filepath_settings, "w") as file:
            json.dump(settings, file, indent=4)
    except Exception as e:
        print(e)
        return False, str(e)
    return True, "None"


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
                "seller_email": item[3],
                "phone": item[4],
                "address": item[5],
                "web_url": item[6],
                "type": item[7],
                "brands": brands,
                "rfc": extra_info.get("rfc", ""),
                "items": json.loads(item[9])
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def get_items_supplier_name(id_supplier: str):
    try:
        id_s = int(id_supplier)
    except Exception as e:
        print(str(e))
        id_s = None
    flag, error, results = get_items_supplier_by_id(id_s)
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in results:
        data_out.append(
            {
                "id": item[0],
                "item_name": item[1],
                "unit_price": item[2],
                "part_number": item[3],
                "created_at": item[4].strftime(format_timestamps)
                if isinstance(item[4], datetime)
                else str(item[4]),
                "updated_at": item[5].strftime(format_timestamps)
                if isinstance(item[5], datetime)
                else str(item[5]),
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def insert_supplier(data):
    # name, seller_name, seller_email, phone, address, web_url, type, extra_info
    flag, error, id_supplier = create_supplier_amc(
        data.get("name").upper(),
        data.get("seller_name").upper(),
        data.get("seller_email").upper(),
        data.get("phone"),
        data.get("address"),
        data.get("web"),
        data.get("type"),
        data.get("extra_info"),
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    # create items
    items = data.get("items", [])
    errors_i = []
    for item in items:
        flag, error, result = create_item_amc(
            item.get("item_name"),
            item.get("unit_price"),
            item.get("part_number"),
            id_supplier,
        )
        if not flag:
            errors_i.append(error)
    if len(errors_i) > 0:
        return {
            "data": None,
            "msg": f"Supplier created with id {id_supplier} but some items failed to create: {errors_i}",
        }, 422
    else:
        return {"data": id_supplier, "msg": "Ok"}, 201


def update_supplier(data):
    flag, error, result = update_supplier_amc(
        data.get("id"),
        data.get("name").upper(),
        data.get("seller_name", "").upper(),
        data.get("seller_email", "").upper(),
        data.get("phone"),
        data.get("address"),
        data.get("web"),
        data.get("type"),
        data.get("extra_info"),
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    # update items
    errors_i = []
    items = data.get("items", [])
    for item in items:
        id_item = item.get("id")
        if id_item == 0:
            flag, error, result = create_item_amc(
                item.get("item_name"),
                item.get("unit_price"),
                item.get("part_number"),
                item.get("id_supplier"),
            )
            if not flag:
                errors_i.append(error)
            continue
        if data.get("is_erased", 0)==1:
            flag, error, result = delete_item_amc(id_item)
            if not flag:
                errors_i.append(error)
            continue
        flag, error, result = update_item_amc(
            id_item,
            item.get("item_name"),
            item.get("unit_price"),
            item.get("part_number"),
            data.get("id_supplier"),
        )
        if not flag:
            errors_i.append(error)
    if len(errors_i) > 0:
        return {
            "data": None,
            "msg": f"Supplier updated with id {data.get('id')} but some items failed to update: {errors_i}",
        }, 422
    return {"data": result, "msg": "Ok"}, 200


def delete_supplier(data):
    flag, error, result = delete_supplier_amc(data.get("id"))
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    return {"data": result, "msg": "Ok"}, 200


def fetch_heads_main(data_token):
    dep_id = data_token.get("dep_id")
    permissions = data_token.get("permissions")
    permissions_last = [item.lower().split(".")[-1] for item in permissions.values()]
    flag, error, result = check_if_gerente(data_token.get("emp_id"))
    if len(result) == 0 and "administrator" not in permissions_last:
        return {"data": [], "msg": str(error)}, 400
    dep_ids_list = [dep_id]
    for k, v in dict_deps.items():
        if "administrator" in permissions_last:
            dep_ids_list.append(v)
            continue
        if k.lower() in permissions_last:
            dep_ids_list.append(v)
    flag, error, result = get_heads_list_db(dep_ids_list)
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in result:
        extra_info = json.loads(item[7])
        data_out.append(
            {
                "id": item[0],
                "name": item[1],
                "employee": item[2],
                "department": item[3],
                "department_name": item[4],
                "employee_name": item[5],
                "employee_email": item[6],
                "contracts": extra_info.get("contracts", []),
                "contracts_temp": extra_info.get("contracts_temp", []),
                "other_leaders": extra_info.get("other_leaders", []),
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def fetch_heads(id_dep: int):
    id_department: int | None = int(id_dep) if id_dep >= 0 else None
    flag, error, result = get_heads_db(id_department)
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in result:
        extra_info = json.loads(item[7])
        data_out.append(
            {
                "id": item[0],
                "name": item[1],
                "employee": item[2],
                "department": item[3],
                "department_name": item[4],
                "employee_name": item[5],
                "employee_email": item[6],
                "contracts": extra_info.get("contracts", []),
                "contracts_temp": extra_info.get("contracts_temp", []),
                "other_leaders": extra_info.get("other_leaders", []),
            }
        )
    # data_abb, code_abb = get_contracts_abreviations()
    # return {"data": data_out, "msg": "Ok", "data_abbreviations": data_abb}, 200
    return {"data": data_out, "msg": "Ok"}, 200


def insert_head_from_api(data, data_token):
    extra_info = (
        json.loads(data["extra_info"])
        if isinstance(data["extra_info"], str)
        else data["extra_info"]
    )
    if "other_leaders" not in extra_info:
        extra_info["other_leaders"] = []
    if "contracts" not in extra_info:
        extra_info["contracts"] = []
    if "contracts_temp" not in extra_info:
        extra_info["contracts_temp"] = []
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
    if "contracts" not in extra_info:
        extra_info["contracts"] = []
    if "contracts_temp" not in extra_info:
        extra_info["contracts_temp"] = []
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


def items_contract_from_file(data):
    products = read_exel_products_partidas(data["path"])
    if products is None:
        return {"data": None, "msg": "Error at file structure"}, 400
    return {"data": products, "msg": "Ok"}, 200


def items_supplier_from_file(data):
    """
    Read excel file and parse items for supplier. Required column in excel:
    - ITEM
    - UDM
    - PRECIO UNITARIO
    - MARCA
    - NRO. PARTE
    - DESCRIPCIÓN LARGA
    - DESCRIPCIÓN CORTA
    """
    df = pd.read_excel(data["path"])
    df = df.fillna("")
    data_excel = df.to_dict("records")
    products = []
    for index, item in enumerate(data_excel):
        product = {
            "partida": item.get("ITEM", index),
            "udm": item.get("UDM"),
            "price_unit": item.get("PRECIO UNITARIO", 0.0),
            "marca": item.get("MARCA", ""),
            "n_parte": item.get("NRO. PARTE", ""),
            "description": item.get("DESCRIPCIÓN LARGA", ""),
            "description_small": item.get("DESCRIPCIÓN CORTA", ""),
        }
        products.append(product)
    if len(products) == 0:
        return {"data": None, "msg": "Error at file structure"}, 400
    return {"data": products, "msg": "Ok"}, 200


def get_contracts_abreviations():
    flag, error, result = get_contracts_abreviations_db()
    if not flag:
        return {"data": [], "msg": str(error)}, 400
    data_out = []
    for item in result:
        metadata = json.loads(item[2])
        data_out.append(
            {
                "abreviation": item[0],
                "id": item[1],
                "metadata": metadata,
                "initial": item[3],
                "isContract": item[4],
            }
        )
    return {"data": data_out, "msg": "Ok"}, 200


def create_items_from_api(products, id_quotation, id_contract=None):
    products_list = []
    for product in products:
        description = product.get("description", "")
        description_small = product.get("description_small", "")
        products_list.append(
            {
                "quotation_id": id_quotation,
                "contract_id": id_contract,
                "partida": product.get("partida", None),
                "udm": product.get("udm", "PZA"),
                "brand": product.get("marca", ""),
                "type_p": product.get("type_p", ""),
                "n_part": product.get("n_parte", ""),
                "quantity": product.get("quantity", 0.0),
                "revision": product.get("revision", 0),
                "price_unit": product.get("price_unit", 0.0),
                "description": description
                if len(description) <= 1024
                else description[:1024],
                "description_small": description_small
                if len(description_small) <= 255
                else description_small[:255],
                "id_inventory": product.get("id", None),
            }
        )
    flag_list, error_list, result_list = create_items_quotation(products_list)
    return flag_list, error_list, result_list


def create_quotation_from_api(data, data_token):
    flag, error, id_quotation = create_quotation(data["metadata"])
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg = f"Cotizacion creada con ID-{id_quotation} por el empleado {data_token.get('emp_id')}"
    flag_list, error_list, result_list = create_items_from_api(
        data["products"], id_quotation
    )
    if flag_list.count(True) == len(flag_list):
        msg += "\nItems de cotizacion creados correctamente"
    elif flag_list.count(False) == len(flag_list):
        print("No items created")
        flag, error, result = delete_quotation(id_quotation)
        return {
            "data": {result_list},
            "error": error_list,
            "msg": str(error) if not flag else "Cotización no creada",
        }, 400
    else:
        msg += "\nError al crear ciertos items de la cotización"
    create_notification_permission(
        msg, ["administracion"], "Cotizacion Creada", data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": id_quotation, "msg": "Ok"}, 201


def update_items_quotation_from_api(products, id_quotation, id_contract, dict_products):
    flag_list = []
    error_list = []
    result_list = []
    for new_product in products:
        description = new_product.get("description", "")
        description_small = new_product.get("description_small", "")
        id_item = new_product.get("id", 0)
        if id_item == 0:
            flag, error, result = create_item_quotation(
                {
                    "quotation_id": id_quotation,
                    "contract_id": id_contract,
                    "partida": new_product.get("partida", None),
                    "udm": new_product.get("udm", "PZA"),
                    "brand": new_product.get("marca", ""),
                    "type_p": new_product.get("type_p", ""),
                    "n_part": new_product.get("n_parte", ""),
                    "quantity": new_product.get("quantity", 0.0),
                    "revision": new_product.get("revision", 0),
                    "price_unit": new_product.get("price_unit", 0.0),
                    "description": description
                    if len(description) <= 1024
                    else description[:1024],
                    "description_small": description_small
                    if len(description_small) <= 255
                    else description_small[:255],
                    "id_inventory": new_product.get("id", None),
                }
            )
        else:
            if new_product.get("is_erased", 0) != 0:
                flag, error, result = delete_item_quotation(id_item)
            else:
                old_product = dict_products.get(id_item, {})
                old_product["partida"] = new_product.get("partida", None)
                old_product["udm"] = new_product.get("udm", "PZA")
                old_product["brand"] = new_product.get("marca", "")
                old_product["type_p"] = new_product.get("type_p", "")
                old_product["n_part"] = new_product.get("n_parte", "")
                old_product["quantity"] = new_product.get("quantity", 0.0)
                old_product["revision"] = new_product.get("revision", 0)
                old_product["price_unit"] = new_product.get("price_unit", 0.0)
                old_product["description"] = (
                    description if len(description) <= 1024 else description[:1024]
                )
                old_product["description_small"] = (
                    description_small
                    if len(description_small) <= 255
                    else description_small[:255]
                )
                old_product["id_inventory"] = new_product.get("id", None)
                flag, error, result = update_item_quotation(id_item, old_product)
        flag_list.append(flag)
        error_list.append(error)
        result_list.append(result)
    return flag_list, error_list, result_list


def update_quoation_from_api(data, data_token):
    flag, error, result = update_quotation(data["id"], data["metadata"])
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg = f"Cotizacion actualizada con ID-{data['id']} por el empleado {data_token.get('emp_id')}"
    flag, error, result = get_quotation(data["id"])
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    old_products = json.loads(result[2])
    dict_products = {item["id"]: item for item in old_products}
    products = data["products"]
    contract_id = result[5]
    flag_list, error_list, result_list = update_items_quotation_from_api(
        products, data["id"], contract_id, dict_products
    )
    if flag_list.count(True) == len(flag_list):
        msg += "\nItems de cotizacion actualizados correctamente"
    elif flag_list.count(False) == len(flag_list):
        return {
            "data": {"data": result_list},
            "error": error_list,
            "msg": "Error al actualizar items de cotización",
        }, 400
    else:
        msg += "\nError al actualizar ciertos items de la cotización"
    create_notification_permission(
        msg, ["administracion"], "Cotizacion Actualizada", data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result_list, "error": error_list, "msg": msg}, 200


def delete_quotation_from_api(data, data_token):
    flag, error, result_items = delete_quotation_items(data["id"])
    if not flag:
        return {"data": "Items cant be erased", "msg": str(error)}, 400
    flag, error, result = delete_quotation(data["id"])
    if not flag:
        return {"data": "Quoation unable to be deleted", "msg": str(error)}, 400
    msg = f"Cotizacion eliminada con ID-{data['id']} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg, ["administracion"], "Cotizacion Eliminada", data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 200


def create_contract_from_api(data, data_token):
    # Extraer y eliminar claves específicas del metadata
    contract_number = data["metadata"].pop("contract_number", "error cnumber")
    client_id = data["metadata"].pop("client_id", 50)
    emission = data["metadata"].pop("emission", "error edate")
    msg = ""
    if data.get("quotation_id", 0) == 0:
        flag, error, id_quotation = create_quotation(data["metadata"], status=2)
        if not flag:
            return {"data": None, "msg": str(error)}, 400
        msg += f"Cotizacion creada con ID-{id_quotation} por el empleado {data_token.get('emp_id')}"
        flag, error, id_contract = create_contract(
            id_quotation, data["metadata"], contract_number, client_id, emission
        )

    else:
        flag, error, id_contract = create_contract(
            data["quotation_id"], data["metadata"], contract_number, client_id, emission
        )
        id_quotation = data["quotation_id"]
    if not flag:
        flag, error, result = delete_quotation(id_quotation)
        return {
            "data": "Not posible to create contract",
            "error": result,
            "msg": str(error),
        }, 400
    flag_list, error_list, result_list = create_items_from_api(
        data["products"], id_quotation, id_contract
    )
    if flag_list.count(True) == len(flag_list):
        msg += "\nItems de cotizacion creados correctamente"
    elif flag_list.count(False) == len(flag_list):
        flag, error_q, result_q = delete_quotation(id_quotation)
        flag, error_c, result_c = delete_contract(id_contract)
        return {
            "data": {result_list},
            "error": error_list + [error_q, error_c],
            "msg": str(result_q) + " " + str(result_c)
            if not flag
            else "Cotización no creada",
        }, 400
    else:
        msg += "\nError al crear ciertos items de la cotización"
    msg += f"Contrato creado con ID-{id_contract} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg, ["administracion"], "Contrato Creado", data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result_list, "msg": "Ok"}, 201


def update_contract_from_api(data, data_token):
    msg = ""
    if data.get("quotation_id", 0) == 0 and len(data.get("products", [])) > 0:
        id_contract = data["id"]
        flag, error, result = create_quotation(data["metadata"], status=1)
        if not flag:
            return {
                "data": None,
                "msg": "No se pudo crear una cotizacion para relacionar con el contrato"
                + str(error),
            }, 400
        id_quotation = result if isinstance(result, int) and result > 0 else 0
        if id_quotation == 0:
            return {
                "data": None,
                "msg": "No se pudo obtener el id correcto de una cotizacion para relacionar con el contrato",
            }, 400
        msg += f"Se creo una cotizacion con ID-{id_quotation} para relacionar con el contrato por el empleado {data_token.get('emp_id')}"
        flag_list, error_list, result_list = create_items_from_api(
            data["products"], id_quotation, data["id"]
        )

    else:
        id_quotation = data["quotation_id"]
        id_contract = data["id"]
        flag, error, result = get_quotation(data["id"])
        if not flag:
            return {"data": None, "msg": str(error)}, 400
        old_products = json.loads(result[2])
        dict_products = {item["id"]: item for item in old_products}
        products = data["products"]
        contract_id = result[5]
        flag_list, error_list, result_list = update_items_quotation_from_api(
            products, data["id"], contract_id, dict_products
        )
    if flag_list.count(True) == len(flag_list):
        msg += "\nItems de cotizacion creados/actualizados correctamente"
    elif flag_list.count(False) == len(flag_list):
        flag, error_q, result_q = delete_quotation(id_quotation)
        flag, error_c, result_c = delete_contract(id_contract)
        return {
            "data": {result_list},
            "error": error_list + [error_q, error_c],
            "msg": str(result_q) + " " + str(result_c)
            if not flag
            else "Cotización no creada",
        }, 400
    else:
        msg += (
            "\nError al crear o actualizar ciertos items de la cotización"
            + str(error_list)
            + "\n"
            + str(result_list)
        )
    contract_number = data["metadata"].pop("contract_number", "error cnumber")
    client_id = data["metadata"].pop("client_id", 50)
    emission = data["metadata"].pop("emission", "error edate")
    # actualizar contrato
    flag, error, result = update_contract(
        data["id"],
        data["metadata"],
        contract_number,
        client_id,
        emission,
        data["timestamps"],
        id_quotation,
    )
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg += f"Contrato actualizado con ID-{data['id']} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg, ["administracion"], "Contrato Actualizado", data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "error": error_list, "msg": result_list}, 200


def delete_contract_from_api(data, data_token):
    flag, error, result = delete_contract_from_item_quotation(data["id"])
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    flag, error, result = delete_contract(data["id"])
    if not flag:
        return {"data": None, "msg": str(error)}, 400
    msg = f"Contrato eliminado con ID-{data['id']} por el empleado {data_token.get('emp_id')}"
    create_notification_permission(
        msg, ["administracion"], "Contrato Eliminado", data_token.get("emp_id"), 0
    )
    write_log_file(log_file_admin, msg)
    return {"data": result, "msg": "Ok"}, 200
