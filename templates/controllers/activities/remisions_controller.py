# -*- coding: utf-8 -*-
import json
from templates.database.connection import execute_sql

__author__ = "Edisson Naula"
__date__ = "$ 18/02/2026 at 16:35 $"


def insert_quotation_activity(
    date_activity: str,  # 'YYYY-MM-DD HH:MM:SS'
    folio: str,
    client_id: int,
    client_company_name: str,
    client_contact_name: str,
    client_phone: str,
    client_email: str,
    plant: str,
    area: str,
    location: str,
    general_description: str,
    comments: str,
    history: list,
    status: int = 0,  # 0: Pendiente, 1: Aprobada, 2: Rechazada, 3: Cancelada
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.quotations_activities "
        "(date_activity, folio, client_id, client_company_name, client_contact_name, "
        " client_phone, client_email, plant, area, location, general_description, "
        " comments, status, history) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        date_activity,
        folio,
        client_id,
        client_company_name,
        client_contact_name,
        client_phone,
        client_email,
        plant,
        area,
        location,
        general_description,
        comments,
        status,
        json.dumps(history),
    )
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_quotation_activity(
    qa_id: int,
    date_activity: str,
    folio: str,
    client_id: int,
    client_company_name: str,
    client_contact_name: str,
    client_phone: str,
    client_email: str,
    plant: str,
    area: str,
    location: str,
    general_description: str,
    comments: str,
    history: list,
    status: int,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.quotations_activities "
        "SET date_activity=%s, folio=%s, client_id=%s, client_company_name=%s, "
        "    client_contact_name=%s, client_phone=%s, client_email=%s, plant=%s, area=%s, "
        "    location=%s, general_description=%s, comments=%s, status=%s, history=%s "
        "WHERE qa_id=%s"
    )
    val = (
        date_activity,
        folio,
        client_id,
        client_company_name,
        client_contact_name,
        client_phone,
        client_email,
        plant,
        area,
        location,
        general_description,
        comments,
        status,
        json.dumps(history),
        qa_id,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_quotation_activity(qa_id: int):
    sql = "DELETE FROM sql_telintec_mod_admin.quotations_activities WHERE qa_id=%s"
    val = (qa_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_activity_report(
    date: str,
    folio: str,
    client_id: int,
    client_company_name: str,
    client_contact_name: str,
    client_phone: str,
    client_email: str,
    plant: str,
    area: str,
    location: str,
    general_description: str,
    comments: str,
    quotation_id: int,
    history: dict,
    status: int = 0,
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.activity_reports "
        "(date, folio, client_id, client_company_name, client_contact_name, client_phone, "
        " client_email, plant, area, location, general_description, comments, quotation_id, "
        " status, history) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        date,
        folio,
        client_id,
        client_company_name,
        client_contact_name,
        client_phone,
        client_email,
        plant,
        area,
        location,
        general_description,
        comments,
        quotation_id,
        status,
        json.dumps(history),
    )
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_activity_report(
    report_id: int,
    date: str,
    folio: str,
    client_id: int,
    client_company_name: str,
    client_contact_name: str,
    client_phone: str,
    client_email: str,
    plant: str,
    area: str,
    location: str,
    general_description: str,
    comments: str,
    quotation_id: int,
    status: int,
    history: dict,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.activity_reports "
        "SET date=%s, folio=%s, client_id=%s, client_company_name=%s, "
        "    client_contact_name=%s, client_phone=%s, client_email=%s, plant=%s, area=%s, "
        "    location=%s, general_description=%s, comments=%s, quotation_id=%s, "
        "    status=%s, history=%s "
        "WHERE id=%s"
    )
    val = (
        date,
        folio,
        client_id,
        client_company_name,
        client_contact_name,
        client_phone,
        client_email,
        plant,
        area,
        location,
        general_description,
        comments,
        quotation_id,
        status,
        json.dumps(history),
        report_id,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_activity_report(report_id: int):
    sql = "DELETE FROM sql_telintec_mod_admin.activity_reports WHERE id=%s"
    val = (report_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def insert_quotation_activity_item(
    quotation_id: int | None,
    report_id: int | None,
    description: str,
    udm: str,
    quantity: float,
    unit_price: float,
    history: list,
    item_c_id: int | None,
):
    sql = (
        "INSERT INTO sql_telintec_mod_admin.quotation_activity_items "
        "(quotation_id, report_id, item_c_id, description, udm, quantity, unit_price, history) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        quotation_id,
        report_id,
        item_c_id,
        description,
        udm,
        quantity,
        unit_price,
        json.dumps(history),
    )
    flag, e, out = execute_sql(sql, val, 4)
    return flag, e, out


def update_quotation_activity_item(
    qa_item_id: int,
    quotation_id: int,
    report_id: int,
    item_c_id: int,
    description: str,
    udm: str,
    quantity: float,
    unit_price: float,
    history: list,
):
    sql = (
        "UPDATE sql_telintec_mod_admin.quotation_activity_items "
        "SET description=%s, udm=%s, quantity=%s, unit_price=%s, history=%s, item_c_id=%s, report_id=%s , quotation_id=%s "
        "WHERE qa_item_id=%s"
    )
    val = (
        description,
        udm,
        quantity,
        unit_price,
        json.dumps(history),
        item_c_id,
        report_id,
        quotation_id,
        qa_item_id,
    )
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def delete_quotation_activity_item(qa_item_id: int):
    sql = "DELETE FROM sql_telintec_mod_admin.quotation_activity_items WHERE qa_item_id=%s"
    val = (qa_item_id,)
    flag, e, out = execute_sql(sql, val, 3)
    return flag, e, out


def get_quotation_activity_by_id(id_quotation):
    sql = (
        "SELECT "
        "qa.qa_id, "
        "qa.date_activity, "
        "qa.folio, "
        "qa.client_id, "
        "qa.client_company_name, "
        "qa.client_contact_name, "
        "qa.client_phone, "
        "qa.client_email, "
        "qa.plant, "
        "qa.area, "
        "qa.location, "
        "qa.general_description, "
        "qa.comments, "
        "qa.status, "
        "qa.history, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        " 'qa_item_id', qai.qa_item_id, "
        " 'quotation_id', qai.quotation_id, "
        " 'report_id', qai.report_id, "
        " 'item_c_id', qai.item_c_id "
        " 'description', qai.description, "
        " 'udm', qai.udm, "
        " 'quantity', qai.quantity, "
        " 'unit_price', qai.unit_price, "
        " 'line_total', qai.line_total"
        " 'history', qai.history, "
        ")) AS items "
        "FROM sql_telintec_mod_admin.quotations_activities AS qa "
        "LEFT JOIN sql_telintec_mod_admin.quotation_activity_items AS qai ON qa.qa_id = qai.quotation_id "
        "WHERE( qa.qa_id = %s  OR %s IS NULL)"
        "GROUP BY qa.qa_id"
    )
    val = (id_quotation, id_quotation)
    flag, e, out = (
        execute_sql(sql, val, 1)
        if id_quotation is not None
        else execute_sql(sql, val, 2)
    )
    return flag, e, out
