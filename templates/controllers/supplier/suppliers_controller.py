# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 19:30 $"

import json

from templates.database.connection import execute_sql


def get_supplier(limit=(0, 100)) -> list[list]:
    sql = "SELECT supplier_id, name, location FROM sql_telintec.suppliers LIMIT %s, %s"
    val = (limit[0], limit[1])
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    if not isinstance(out, list):
        return []
    return out


def insert_supplier(name: str, location: str) -> tuple[bool, str | None, int | None]:
    sql = "INSERT INTO sql_telintec.suppliers (name, location) VALUES (%s, %s)"
    val = (name, location)
    flag, e, out = execute_sql(sql, val, 4)
    if not isinstance(out, int):
        return False, str(e), 0
    return flag, None, out


def insert_multiple_suppliers_name_addres_amc(
    supplier_list: tuple,
) -> tuple[bool, str | None, int | None]:
    sql = "INSERT INTO sql_telintec.suppliers_amc (name, address) VALUES "
    for index, supplier in enumerate(supplier_list):
        if index > 0:
            sql += ", "
        sql += f"( '{supplier[0]}', '{supplier[1]}' )"
    flag, e, out = execute_sql(sql, None, 4)
    if not isinstance(out, int):
        return False, str(e), 0
    return flag, str(e), out


def update_supplier_DB(
    name: str, location: str, supplier_id: int
) -> tuple[bool, str | None, int | None]:
    sql = (
        "UPDATE sql_telintec.suppliers "
        "SET name = %s, location = %s "
        "WHERE supplier_id = %s"
    )
    val = (name, location, supplier_id)
    flag, e, out = execute_sql(sql, val, 3)
    if not isinstance(out, int):
        return False, str(e), 0
    return flag, str(e), out


def delete_supplier_DB(supplier_id: int) -> tuple[bool, str | None, int | None]:
    sql = "DELETE FROM sql_telintec.suppliers WHERE supplier_id = %s"
    val = (supplier_id,)
    flag, e, out = execute_sql(sql, val, 3)
    if not isinstance(out, int):
        return False, e, 0
    return flag, e, out


def get_supplier_amc(name: str, id_s: int):
    columns = ("id_supplier", "name", "phone", "type", "address")
    sql = (
        "SELECT id_supplier, name, phone, type, address "
        "FROM sql_telintec.suppliers_amc "
        "WHERE id_supplier = %s OR "
        "match(name) against (%s IN NATURAL LANGUAGE MODE ) "
        "LIMIT 10"
    )
    val = (id_s, name)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


# def get_all_suppliers_amc():
#     sql = (
#         "SELECT id_supplier, name, seller_name, seller_email, phone, address, web_url, type, extra_info "
#         "FROM sql_telintec.suppliers_amc "
#         "ORDER BY name"
#     )
#     flag, error, result = execute_sql(sql, None, 5)
#     if not isinstance(result, list):
#         return False, error, []
#     return flag, error, result


def get_all_suppliers_amc():
    sql = (
        "SELECT  "
        "    s.id_supplier, "
        "    s.name, "
        "    s.seller_name, "
        "    s.seller_email, "
        "    s.phone, "
        "    s.address, "
        "    s.web_url, "
        "    s.type, "
        "    s.extra_info, "
        "    COALESCE(items.items_json, JSON_ARRAY()) AS items "
        "FROM sql_telintec.suppliers_amc s "
        "LEFT JOIN ( "
        "    SELECT  "
        "        i.id_supplier_amc, "
        "        JSON_ARRAYAGG( "
        "            JSON_OBJECT( "
        "                'id_item', i.id, "
        "                'item_name', i.item_name, "
        "                'unit_price', i.unit_price, "
        "                'part_number', i.part_number, "
        "                'created_at', i.created_at, "
        "                'updated_at', i.updated_at "
        "                , 'currency', i.currency "
        "            ) "
        "        ) AS items_json "
        "    FROM sql_telintec_mod_admin.items_suppliers_amc i "
        "    WHERE i.id IS NOT NULL "
        "    GROUP BY i.id_supplier_amc "
        ") items ON s.id_supplier = items.id_supplier_amc "
        "ORDER BY s.name;"
    )
    flag, error, result = execute_sql(sql, None, 5)
    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def get_items_supplier_by_id(id_supplier=None):
    if id_supplier is None:
        sql = (
            "SELECT id, item_name, unit_price, part_number, created_at, updated_at, currency "
            "FROM sql_telintec_mod_admin.items_suppliers_amc "
            "ORDER BY item_name"
        )
        vals = None
        flag, error, result = execute_sql(sql, vals, 5)
    else:
        sql = (
            "SELECT id, item_name, unit_price, part_number, created_at, updated_at, currency "
            "FROM sql_telintec_mod_admin.items_suppliers_amc "
            "WHERE id_supplier_amc = %s "
        )
        vals = (id_supplier,)
        flag, error, result = execute_sql(sql, vals, 2)

    if not isinstance(result, list):
        return False, error, []
    return flag, error, result


def create_supplier_brands_amc(
    name_provider,
    seller_provider,
    email_provider,
    phone_provider,
    address_provider,
    web_provider,
    type_provider,
    brands=None,
):
    name_provider = str(name_provider)
    seller_provider = str(seller_provider)
    email_provider = str(email_provider)
    phone_provider = str(phone_provider)
    address_provider = str(address_provider)
    web_provider = str(web_provider)
    type_provider = str(type_provider)
    extra_info = {"brands": brands} if brands else {"brands": []}
    insert_sql = (
        "INSERT INTO sql_telintec.suppliers_amc "
        "(name, seller_name, seller_email, phone, address, web_url, type, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    vals = (
        name_provider,
        seller_provider,
        email_provider,
        phone_provider,
        address_provider,
        web_provider,
        type_provider,
        json.dumps(extra_info),
    )
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def create_supplier_amc(
    name_provider,
    seller_provider,
    email_provider,
    phone_provider,
    address_provider,
    web_provider,
    type_provider,
    extra_info,
):
    name_provider = str(name_provider)
    seller_provider = str(seller_provider)
    email_provider = str(email_provider)
    phone_provider = str(phone_provider)
    address_provider = str(address_provider)
    web_provider = str(web_provider)
    type_provider = str(type_provider)
    extra_info = (
        json.dumps(extra_info) if extra_info else json.dumps({"brands": [], "rfc": ""})
    )
    insert_sql = (
        "INSERT INTO sql_telintec.suppliers_amc "
        "(name, seller_name, seller_email, phone, address, web_url, type, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    vals = (
        name_provider,
        seller_provider,
        email_provider,
        phone_provider,
        address_provider,
        web_provider,
        type_provider,
        extra_info,
    )
    flag, error, result = execute_sql(insert_sql, vals, 4)
    return flag, error, result


def create_item_amc(
    item_name,
    unit_price,
    part_number,
    id_supplier_amc,
    currency="MXN",
    id_inventory=None
):
    insert_sql = (
        "INSERT INTO sql_telintec_mod_admin.items_suppliers_amc "
        "(id_supplier_amc, item_name, unit_price, part_number, currency, id_inventory) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    vals = (
        id_supplier_amc,
        item_name,
        unit_price,
        part_number,
        currency,
        id_inventory
    )
    flag, error, rows_changed = execute_sql(insert_sql, vals, 3)
    return flag, error, rows_changed


def update_item_amc(
    id_item,
    item_name,
    unit_price,
    part_number,
    id_supplier_amc,
    currency="MXN",
    id_inventory=None
):
    update_sql = (
        "UPDATE sql_telintec_mod_admin.items_suppliers_amc "
        "SET item_name = %s, unit_price = %s, part_number = %s, id_supplier_amc = %s, currency = %s, id_inventory = %s "
        "WHERE id = %s "
    )
    vals = (
        item_name,
        unit_price,
        part_number,
        id_supplier_amc,
        currency,
        id_inventory,
        id_item,
    )
    flag, error, rows_changed = execute_sql(update_sql, vals, 3)
    return flag, error, rows_changed


def delete_item_amc(id_item):
    delete_sql = "DELETE FROM sql_telintec_mod_admin.items_suppliers_amc WHERE id = %s "
    vals = (id_item,)
    flag, error, rows_changed = execute_sql(delete_sql, vals, 3)
    return flag, error, rows_changed


def update_supplier_brands_amc(
    id_provider,
    name_provider,
    seller_provider,
    email_provider,
    phone_provider,
    address_provider,
    web_provider,
    type_provider,
    brands=None,
):
    name_provider = str(name_provider)
    seller_provider = str(seller_provider)
    email_provider = str(email_provider)
    phone_provider = str(phone_provider)
    address_provider = str(address_provider)
    web_provider = str(web_provider)
    type_provider = str(type_provider)
    brands = brands if brands else []
    update_sql = (
        "UPDATE sql_telintec.suppliers_amc "
        "SET name = %s, seller_name = %s, seller_email = %s, phone = %s, address = %s, web_url = %s, type = %s, "
        " extra_info = JSON_SET(extra_info, '$.brands', %s)"
        "WHERE id_supplier = %s"
    )
    vals = (
        name_provider,
        seller_provider,
        email_provider,
        phone_provider,
        address_provider,
        web_provider,
        type_provider,
        json.dumps(brands),
        id_provider,
    )
    flag, error, result = execute_sql(update_sql, vals, 3)
    return flag, error, result


def update_supplier_amc(
    id_provider,
    name_provider,
    seller_provider,
    email_provider,
    phone_provider,
    address_provider,
    web_provider,
    type_provider,
    extra_info,
):
    name_provider = str(name_provider)
    seller_provider = str(seller_provider)
    email_provider = str(email_provider)
    phone_provider = str(phone_provider)
    address_provider = str(address_provider)
    web_provider = str(web_provider)
    type_provider = str(type_provider)
    extra_info = json.dumps(extra_info) if extra_info else f"{'brands': [], 'rfc': ''}"
    update_sql = (
        "UPDATE sql_telintec.suppliers_amc "
        "SET name = %s, seller_name = %s, seller_email = %s, phone = %s, address = %s, web_url = %s, type = %s, "
        " extra_info = %s "
        "WHERE id_supplier = %s"
    )
    vals = (
        name_provider,
        seller_provider,
        email_provider,
        phone_provider,
        address_provider,
        web_provider,
        type_provider,
        extra_info,
        id_provider,
    )
    flag, error, result = execute_sql(update_sql, vals, 3)
    return flag, error, result


def delete_supplier_amc(id_supplier):
    delete_sql = "DELETE FROM sql_telintec.suppliers_amc WHERE id_supplier = %s"
    vals = (id_supplier,)
    flag, error, result = execute_sql(delete_sql, vals, 4)
    return flag, error, result


def update_brands_supplier(supplier_id, brands: list):
    update_sql = (
        "UPDATE sql_telintec.suppliers_amc "
        "SET extra_info = JSON_SET(extra_info, '$.brands', %s) "
        "WHERE id_supplier = %s"
    )
    vals = (json.dumps(brands), supplier_id)
    # vals = (brands, supplier_id)
    flag, error, result = execute_sql(update_sql, vals, 4)
    return flag, error, result
