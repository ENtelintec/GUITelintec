# -*- coding: utf-8 -*-
from templates.controllers.order.orders_controller import delete_purchase_order
from typing import Iterable
import os
import tempfile
from datetime import datetime

import pytz

from static.constants import (
    timezone_software,
    format_timestamps,
    log_file_po,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.contracts.contracts_controller import (
    get_contracts_abreviations_db,
)
from templates.controllers.departments.heads_controller import check_if_gerente
from templates.controllers.material_request.sm_controller import (
    get_sm_by_id,
    get_sm_by_folio,
)
from templates.controllers.order.orders_controller import (
    insert_purchase_order,
    insert_purchase_order_item,
    update_purchase_order,
    update_po_application_item,
    cancel_purchase_order,
    get_purchase_orders_with_items,
    update_purchase_order_status,
    get_pos_application_with_items,
    insert_po_application,
    update_po_item,
    update_po_application,
    cancel_po_application,
    update_po_application_status,
    get_purchase_order_with_items_by_id,
    get_pos_application_with_items_to_approve,
    get_folios_po_from_pattern,
)
from templates.forms.PurchaseForms import FilePoPDF
from templates.misc.Functions_Files import write_log_file

import json

from templates.resources.midleware.MD_SM import update_sm_from_control_table


__author__ = "Edisson Naula"
__date__ = "$ 02/jun/2025  at 11:09 $"


def map_products_po(products: list):
    products_out = []
    total_amount = 0.0
    for item in products:
        extra_info = item.get("extra_info", {})
        extra_info = extra_info if extra_info else {}
        if item.get("quantity") is None:
            continue
        products_out.append(
            {
                "id": item.get("id"),
                "purchase_id": item.get("purchase_id"),
                "description": item.get("description"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price"),
                "id_inventory": int(extra_info.get("id_inventory", 0)),
                "brand": extra_info.get("brand"),
                "category": extra_info.get("category"),
                "url": extra_info.get("url"),
                "n_parte": extra_info.get("n_parte"),
                "duration_services": item.get("duration_services"),
                "supplier": extra_info.get("supplier"),
                "tool": item.get("tool"),
                "comment": extra_info.get("comment"),
            }
        )
        total_amount += float(item.get("unit_price")) * float(item.get("quantity"))
    return products_out, total_amount


def create_extra_info_product_from_data(data: dict):
    extra_info = {
        "id_inventory": data.get("id_inventory", 0),
        "brand": data.get("brand", ""),
        "category": data.get("category", ""),
        "url": data.get("url", ""),
        "n_parte": data.get("n_parte", ""),
        "duration_services": data.get("duration_services", ""),
        "supplier": data.get("supplier", 0),
        "comment": data.get("comment", ""),
    }
    return extra_info


def create_metadatas_from_extra_info_po(extra_info: dict):
    extra_info_telintec = extra_info.get("metadata_telintec", {})
    extra_info_supplier = extra_info.get("metadata_supplier", {})
    metadata_telintec = {
        "name": extra_info_telintec.get("name", ""),
        "address_invoice": extra_info_telintec.get("address_invoice", ""),
        "address_comercial": extra_info_telintec.get("address_comercial", ""),
        "phone": extra_info_telintec.get("phone", ""),
        "email": extra_info_telintec.get("email", ""),
        "rfc": extra_info_telintec.get("rfc", ""),
        "responsable": extra_info_telintec.get("responsable", ""),
    }
    metadata_supplier = {
        "name": extra_info_supplier.get("name", ""),
        "address_invoice": extra_info_supplier.get("address_invoice", ""),
        "rfc": extra_info_supplier.get("rfc", ""),
        "salesman": extra_info_supplier.get("salesman", ""),
        "payment_method": extra_info_supplier.get("payment_method", ""),
        "delivery_conditions": extra_info_supplier.get("delivery_conditions", ""),
        "delivery_address": extra_info_supplier.get("delivery_address", ""),
        "transport": extra_info_supplier.get("transport", ""),
        "insurance": extra_info_supplier.get("insurance", ""),
        "guarantee": extra_info_supplier.get("guarantee", ""),
    }
    return metadata_telintec, metadata_supplier


def fetch_purchase_orders(status, data_token):
    permissions = data_token.get("permissions")
    permissions_last = [item.lower().split(".")[-1] for item in permissions.values()]
    if "administrator" in permissions_last:
        emp_id = None
    else:
        flag, error, result = check_if_gerente(data_token.get("emp_id"))
        emp_id = data_token.get("emp_id") if not flag and len(result) <= 0 else None
    status_map = {"pendiente": 0, "recibido": 1, "cancelado": 4}
    status = status_map.get(status, None)  # Si status no es válido, se usa None
    flag, error, result = get_purchase_orders_with_items(status, emp_id)
    if not flag:
        return {"data": result, "msg": "error", "error": str(error)}, 400
    if not isinstance(result, Iterable):
        return {
            "data": result,
            "msg": "Error at retrieving data from db",
            "error": None,
        }, 400
    data_out = []
    for item in result:
        (
            id_order,
            timestamp,
            status,
            created_by,
            supplier,
            folio,
            history,
            extra_info,
            products,
            time_delivery,
        ) = item
        extra_info = json.loads(extra_info)
        metadata_telintec, metadata_supplier = create_metadatas_from_extra_info_po(
            extra_info
        )
        order_quotation = extra_info.get("order_quotation", "")
        products = json.loads(products)
        products, total_amount = map_products_po(products)
        data_out.append(
            {
                "id": id_order,
                "timestamp": timestamp.strftime(format_timestamps)
                if not isinstance(timestamp, str)
                else timestamp,
                "status": status,
                "supplier": supplier,
                "folio": folio,
                "comment": extra_info.get("comment"),
                "history": json.loads(history),
                "items": products,
                "total_amount": total_amount,
                "created_by": created_by,
                "time_delivery": time_delivery,
                "metadata_telintec": metadata_telintec,
                "metadata_supplier": metadata_supplier,
                "order_quotation": order_quotation,
            }
        )

    return {"data": data_out, "msg": "ok", "error": None}, 200


def create_purchaser_order_api(data, data_token):
    sm_id = data.get("sm_id", 0)
    update_sm_control_table = False
    if sm_id != 0:
        flag, error, result_sm = get_sm_by_id(sm_id)
        if not flag:
            update_sm_control_table = True
    else:
        result_sm = [0]
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    comment_history = f"Orden de compra creada por {data_token.get('emp_id')}"
    history = [
        {
            "user": data_token.get("emp_id"),
            "event": "Creación de orden",
            "date": timestamp,
            "comment": comment_history,
        }
    ]
    extra_info = {
        "comment": data.get("comment", ""),
        "metadata_telintec": data.get("metadata_telintec", {}),
        "metadata_supplier": data.get("metadata_supplier", {}),
        "sm_id": sm_id,
        "order_quotation": data.get("order_quotation", ""),
    }
    flag, error, id_order = insert_purchase_order(
        timestamp,
        0,
        data_token.get("emp_id"),
        data["supplier"],
        data["folio"],
        history,
        data["time_delivery"],
        extra_info,
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    if not isinstance(id_order, int) or id_order <= 0:
        return {
            "data": id_order,
            "msg": "error al crear orden",
            "error": "No se pudo crear la orden",
        }, 400
    msg = f"Orden de compra creada con ID-{id_order}"
    msg_moves: list[str] = []
    flag_error = False
    n_errors = 0
    for item in data["items"]:
        extra_info = create_extra_info_product_from_data(item)
        update_item = True
        duration_services = item.get("duration_services")
        if duration_services is None or duration_services == "":
            item["duration_services"] = "0"
        if item["id"] is None or item["id"] <= 0:
            flag, error, result = insert_purchase_order_item(
                id_order,
                item["quantity"],
                item["unit_price"],
                item["description"],
                duration_services,
                extra_info,
                item["tool"],
                item["currency"],
            )
            update_item = False
        else:
            flag, error, result = update_po_item(
                item["id"],
                id_order,
                item["quantity"],
                item["unit_price"],
                item["description"],
                duration_services,
                extra_info,
                item["currency"],
            )
        if not flag:
            msg_moves.append(
                f"x-Error al actualizar item de orden de compra -{item['description']}-{str(error)}"
                if update_item
                else f"x-Error al crear item de orden de compra -{item['description']}-{str(error)}"
            )
            flag_error = True
            n_errors += 1
        else:
            msg_moves.append(
                f"Item de orden de compra creado con ID-{result}"
                if not update_item
                else f"Item de orden de compra actualizado con ID-{item['id']}"
            )
    # falta comprobar si algun item se creo sino eliminar po.
    if n_errors == len(data["items"]):
        flag, error, result = delete_purchase_order(id_order)
        return {
            "data": [id_order if not flag else None],
            "msg": f"Error al crear los items de la orden {id_order}"
            if not flag
            else "Error al crear los items de la orden, orden eliminada",
            "error": "\n".join(msg_moves),
        }, 400
    msg += "\n" + "\n".join(msg_moves)
    if update_sm_control_table:
        code, data_out = update_sm_from_control_table(
            {
                "id": sm_id,
                "info": {"admin_reviewed": 1, "warehouse_notification_date": timestamp},
            },
            data_token,
            result_sm,
        )
        if code != 200:
            msg += (
                "\n"
                + f"Error al actualizar la tabla de control de sm con id {sm_id}: {data_out['msg']}"
            )

        else:
            msg += "\n" + f"Tabla de control de SM con id {sm_id} actualizada"
    create_notification_permission_notGUI(
        msg, ["orders"], "Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg)
    if flag_error:
        return {
            "data": [id_order],
            "msg": "Error al crear los items de la orden",
            "error": "\n".join(msg_moves),
        }, 400
    return {"data": [id_order], "msg": "ok", "error": None}, 200


def update_purchase_order_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data.get("history", [])
    history.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Actualización de orden",
            "date": timestamp,
            "comment": "Update purchase order",
        }
    )
    extra_info = {
        "comment": data.get("comment", ""),
        "metadata_telintec": data.get("metadata_telintec", {}),
        "metadata_supplier": data.get("metadata_supplier", {}),
        "sm_id": data.get("sm_id", 0),
        "order_quotation": data.get("order_quotation", ""),
    }
    flag, error, result = update_purchase_order(
        data["id"],
        timestamp,
        data["status"],
        data["created_by"],
        data["supplier"],
        data["folio"],
        history,
        extra_info,
        data["time_delivery"],
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Orden de compra actualizada con ID-{data['id']}"
    msg_items: list[str] = []
    flag_error = False
    for item in data["items"]:
        extra_info = create_extra_info_product_from_data(item)
        update_item = True
        print("items", item)
        if item["id"] is None or item["id"] <= 0:
            flag, error, result = insert_purchase_order_item(
                data["id"],
                item["quantity"],
                item["unit_price"],
                item["description"],
                item["duration_services"],
                extra_info,
                item["tool"],
                item["currency"],
            )
            update_item = False
        else:
            flag, error, result = update_po_item(
                item["id"],
                data["id"],
                item["quantity"],
                item["unit_price"],
                item["description"],
                item["duration_services"],
                extra_info,
                item["currency"],
            )
        if not flag:
            msg_items.append(
                f"x-Error al actualizar item de orden de compra -{item['description']}-{str(error)}"
                if update_item
                else f"x-Error al crear item de orden de compra -{item['description']}-{str(error)}"
            )
            flag_error = True
        else:
            msg_items.append(
                f"Item de orden de compra actualizado con ID-{item['id']}-{item['description']}"
                if update_item
                else f"Item de orden de compra creado con ID-{result}-{item['description']}"
            )
    msg += "\n" + "\n".join(msg_items)
    create_notification_permission_notGUI(
        msg, ["orders"], "Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg)
    if flag_error:
        return {
            "data": [data["id"]],
            "msg": "Error at updating order items",
            "error": "\n".join(msg_items),
        }, 400
    return {"data": [data["id"]], "msg": "ok", "error": None}, 200


def cancel_purchase_order_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data.get("history", [])
    history.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Cancelado",
            "date": timestamp,
            "comment": data.get("comment", ""),
        }
    )
    flag, error, result = cancel_purchase_order(
        history,
        data["id"],
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Orden de compra cancelada con ID-{data['id']}"
    create_notification_permission_notGUI(
        msg, ["orders"], "Orden de compra cancelada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg)
    return {"data": [data["id"]], "msg": "ok", "error": None}, 200


def change_state_order_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data.get("history", [])
    history.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Cambio de estado",
            "date": timestamp,
            "comment": data.get("comment", ""),
        }
    )
    flag, error, result = update_purchase_order_status(
        data["id"],
        history,
        data["status"],
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Orden de compra actualizada con ID-{data['id']} a estado {data['status']}"
    create_notification_permission_notGUI(
        msg,
        ["orders", "administracion"],
        "Orden de compra actualizada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg)
    return {"data": [result], "msg": "ok", "error": None}, 200


def fetch_pos_applications_to_approve(data_token):
    # permissions = data_token.get("permissions")
    # permissions_last = [item.lower().split(".")[-1] for item in permissions.values()]
    flag, error, result = get_pos_application_with_items_to_approve()
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    data_out = []
    if not isinstance(result, Iterable):
        return {
            "data": result,
            "msg": "Error at retrieving data from db",
            "error": None,
        }, 400
    for item in result:
        (
            id_order,
            timestamp,
            status,
            created_by,
            reference,
            history,
            products,
            extra_info,
        ) = item
        products = json.loads(products)
        products, total_amount = map_products_po(products)
        data_out.append(
            {
                "id": id_order,
                "timestamp": timestamp.strftime(format_timestamps)
                if not isinstance(timestamp, str)
                else timestamp,
                "status": status,
                "reference": reference,
                "history": json.loads(history),
                "items": products,
                "total_amount": total_amount,
                "created_by": created_by,
            }
        )

    return {"data": data_out, "msg": "ok", "error": None}, 200


def fetch_pos_applications(status, data_token):
    permissions = data_token.get("permissions")
    permissions_last = [item.lower().split(".")[-1] for item in permissions.values()]
    if "administrator" in permissions_last:
        emp_id = None
    else:
        flag, error, result = check_if_gerente(data_token.get("emp_id"))
        emp_id = data_token.get("emp_id") if not flag and len(result) <= 0 else None
    status_map = {"pendiente": 0, "recibido": 1, "cancelado": 4}
    status = status_map.get(status, None)  # Si status no es válido, se usa None
    flag, error, result = get_pos_application_with_items(status, emp_id)
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    data_out = []
    if not isinstance(result, Iterable):
        return {
            "data": result,
            "msg": "Error at retrieving data from db",
            "error": None,
        }, 400
    for item in result:
        (
            id_order,
            timestamp,
            status,
            created_by,
            reference,
            history,
            products,
            extra_info,
        ) = item
        products = json.loads(products)
        products, total_amount = map_products_po(products)
        extra_info = json.loads(extra_info)
        data_out.append(
            {
                "id": id_order,
                "timestamp": timestamp.strftime(format_timestamps)
                if not isinstance(timestamp, str)
                else timestamp,
                "status": status,
                "reference": reference,
                "history": json.loads(history),
                "items": products,
                "total_amount": total_amount,
                "created_by": created_by,
                "sm_id": extra_info.get("sm_id", 0),
            }
        )

    return {"data": data_out, "msg": "ok", "error": None}, 200


def create_po_application_api(data, data_token):
    sm_id = data.get("sm_id", 0)
    update_sm_control_table = False
    if sm_id > 0:
        flag, error, result_sm = get_sm_by_id(sm_id)
    else:
        flag, error, result_sm = get_sm_by_folio(data.get("folio", ""))
    if not isinstance(result_sm, list) or not isinstance(result_sm, tuple):
        return {"data": None, "msg": "error", "error": "SM not found"}, 400

    extra_info = {}
    if flag:
        update_sm_control_table = True
        extra_info = {"sm_id": result_sm[0]}

    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = [
        {
            "user": data_token.get("emp_id"),
            "event": "Creación de solicitud",
            "date": timestamp,
            "comment": f"Se creo una solicitud de orden de compra con referencia {data['reference']} "
            f"por el usuario {data_token.get('emp_id')}.",
        }
    ]
    flag, error, id_po_app = insert_po_application(
        timestamp,
        1,
        data_token.get("emp_id"),
        data["reference"],
        history,
        extra_info=extra_info,
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    if not isinstance(id_po_app, int):
        return {
            "data": None,
            "msg": "error in id of order application",
            "error": str(error),
        }, 400
    msg = f"Solicitud de Orden de compra creada con ID-{id_po_app}"
    msg_moves: list[str] = []
    flag_error = False
    tool_detected = False
    for item in data["items"]:
        extra_info = create_extra_info_product_from_data(item)
        flag, error, result = insert_purchase_order_item(
            id_po_app,
            item["quantity"],
            0.0,
            item["description"],
            "0",
            extra_info,
            item["tool"],
        )
        if item["tool"] == 1:
            tool_detected = True
        if not flag:
            msg_moves.append(
                f"x-Error al crear item de orden de compra -{item['description']}-{str(error)}"
            )
            flag_error = True
        else:
            msg_moves.append(f"Item de orden de compra creado con ID-{result}")
    msg += "\n" + "\n".join(msg_moves)
    if tool_detected:
        msg += (
            "\n"
            + "Se detectó que se solicita una herramienta, esta requerira aprobacion."
        )
        flag, error, result = update_po_application_status(id_po_app, history, 0, 0)
        if not flag:
            return {"data": None, "msg": msg + "\nerror", "error": str(error)}, 400
    if update_sm_control_table:
        code, data_out = update_sm_from_control_table(
            {
                "id": result_sm[0],
                "info": {"warehouse_reviewed": 1, "admin_notification_date": timestamp},
            },
            data_token,
            result_sm,
        )
        if code != 200:
            msg += (
                "\n"
                + f"Error al actualizar la tabla de control de sm con id {result_sm[0]}: {data_out['msg']}"
            )

        else:
            msg += "\n" + f"Tabla de control de SM con id {result_sm[0]} actualizada"

    create_notification_permission_notGUI(
        msg,
        ["orders", "almacen", "sm"],
        "Solicitud de orden de compra creada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg)
    if flag_error:
        return {
            "data": [id_po_app],
            "msg": "Error al crear los items en la solicitud de compras",
            "error": "\n".join(msg_moves),
        }, 400
    return {"data": [id_po_app], "msg": "ok", "error": None}, 200


def update_po_application_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data.get("history", [])
    history.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Actualización de solicitud",
            "date": timestamp,
            "comment": "Update purchase order",
        }
    )
    flag, error, result = update_po_application(
        data["id"],
        timestamp,
        data["status"],
        data["created_by"],
        data["reference"],
        history,
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Solicitud de Orden de compra actualizada con ID-{data['id']}"
    msg_items: list[str] = []
    flag_error = False
    for item in data["items"]:
        extra_info = create_extra_info_product_from_data(item)
        if item["id"] == -1:
            flag, error, result = insert_purchase_order_item(
                data["id"],
                item["quantity"],
                0.0,
                item["description"],
                "0",
                extra_info,
            )
        else:
            flag, error, result = update_po_application_item(
                item["id"],
                item["quantity"],
                0.0,
                0,
                item["description"],
                extra_info,
            )
        if not flag:
            msg_items.append(
                f"x-Error al actualizar item de solicitud de orden de compra -{item['description']}-{str(error)}"
            )
            flag_error = True
        else:
            msg_items.append(
                f"Item de solicitud de orden de compra actualizado con ID-{item['id']}-{item['description']}"
            )
    msg += "\n" + "\n".join(msg_items)
    create_notification_permission_notGUI(
        msg, ["orders"], "Solicitud de Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg)
    if flag_error:
        return {
            "data": [data["id"]],
            "msg": "Error at creating order application items",
            "error": "\n".join(msg_items),
        }, 400
    return {"data": [data["id"]], "msg": "ok", "error": None}, 200


def cancel_po_application_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data.get("history", [])
    history.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Cancelado",
            "date": timestamp,
            "comment": data.get("comment", ""),
        }
    )
    flag, error, result = cancel_po_application(
        data.get("status", 4),
        history,
        data["id"],
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Solicitud de Orden de compra cancelada con ID-{data['id']}"
    create_notification_permission_notGUI(
        msg,
        ["orders"],
        "Solicitud de Orden de compra cancelada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg)
    return {"data": [data["id"]], "msg": "ok", "error": None}, 200


def change_state_po_application_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data.get("history", [])
    history.append(
        {
            "user": data_token.get("emp_id"),
            "event": "Cambio de estado",
            "date": timestamp,
            "comment": data.get("comment", "")
            + f"status: {data['status']}, approved: {data['approved']}",
        }
    )
    flag, error, result = update_po_application_status(
        data["id"], history, data["status"], data["approved"]
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Solicitud de Orden de compra actualizada con ID-{data['id']} a estado {data['status']}"
    create_notification_permission_notGUI(
        msg,
        ["orders", "administracion"],
        "Solicitud de Orden de compra actualizada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg)
    return {"data": [result], "msg": "ok", "error": None}, 200


def create_metadata_for_pdf_po(extra_info: dict):
    extra_info_telintec = extra_info.get("metadata_telintec", {})
    extra_info_supplier = extra_info.get("metadata_supplier", {})
    metadata_telintec = {
        "Empresa solicitante": extra_info_telintec.get("name", ""),
        "RFC": extra_info_telintec.get("rfc", ""),
        "Domicilio de facturación": extra_info_telintec.get("address_invoice", ""),
        "Domicilio comercial": extra_info_telintec.get("address_comercial", ""),
        "Responsable en compras": extra_info_telintec.get("responsable", ""),
        "Teléfono comercial": extra_info_telintec.get("phone", ""),
        "Correo de facturación": extra_info_telintec.get("email", ""),
    }
    metadata_supplier = {
        "Nombre del proveedor": extra_info_supplier.get("name", ""),
        "Dirección del proveedor": extra_info_supplier.get("address_invoice", ""),
        "RFC del proveedor": extra_info_supplier.get("rfc", ""),
        "Vendedor": extra_info_supplier.get("salesman", "NA"),
        "Forma de pago": extra_info_supplier.get("payment_method", ""),
        "Condiciones de entrega": extra_info_supplier.get("delivery_conditions", ""),
        "Dirección de entrega": extra_info_supplier.get("delivery_address", ""),
        "Transporte": extra_info_supplier.get("transport", ""),
        "Seguro": extra_info_supplier.get("insurance", ""),
        "Garantias": extra_info_supplier.get("guarantee", ""),
    }
    return metadata_telintec, metadata_supplier


def dowload_file_purchase(order_id: int):
    flag, error, result = get_purchase_order_with_items_by_id(order_id)
    if not isinstance(result, list):
        print("error at getting purchase order", result)
        return None, 400
    if not flag or len(result) == 0:
        print("error at getting purchase order", result)
        return None, 400
    date = result[0]
    download_path = os.path.join(
        tempfile.mkdtemp(), os.path.basename(f"oc_{result[5]}_{date.date()}.pdf")
    )
    products = []
    items = json.loads(result[8])
    total_amount = 0.0
    for index, item in enumerate(items):
        extra_info_item = item["extra_info"]
        subtotal = item["quantity"] * item["unit_price"]
        products.append(
            [
                index + 1,
                item["description"],
                extra_info_item["n_parte"],
                item["duration_services"],
                "NA",
                item["quantity"],
                item["unit_price"],
                subtotal,
            ]
        )
        total_amount += subtotal
    extra_info = json.loads(result[7])
    metadata_telintec, metadata_supplier = create_metadata_for_pdf_po(extra_info)
    flag = FilePoPDF(
        {
            "filename_out": download_path,
            "products": products,
            "folio": result[5],
            "status": result[1],
            "total_amount": total_amount,
            "created_by": f"{result[2]} {result[3]}",
            "supplier": result[4],
            "timestamp": result[0],
            "history": json.loads(result[6]),
            "time_delivery": result[9],
            "metadata_telintec": metadata_telintec,
            "metadata_supplier": metadata_supplier,
        },
    )
    if not flag:
        print("error at generating pdf", download_path)
        return None, 400
    return download_path, 200


def generate_folios_po(reference, data_token):
    flag, error, result_abb = get_contracts_abreviations_db()
    abbs_area = []
    dict_abbs = {}
    for item in result_abb:
        if item[0] != "" and item[4] == 0:
            abbs_area.append(item[0])
            dict_abbs[item[0].lower()] = {"initial": item[0].split("-")[0]}
        elif item[4] == 1:
            extra_info = json.loads(item[2])
            contract_number = extra_info.get("contract_number", "")
            if contract_number == "":
                continue
            abbs_area.append(contract_number[-4:])
            dict_abbs[contract_number[-4:].lower()] = {"initial": item[3]}

    # abbs_area = [item[0] for item in result_abb if item[0] != "" and item[4] == 0]
    reference_parts = reference.lower().split("-")
    if len(reference_parts) <= 2:
        return {"data": [], "error": "Bad reference"}, 400
    if (
        reference_parts[1].upper() not in abbs_area
        and reference_parts[1].lower() not in abbs_area
    ):
        return {"data": [], "error": "Bad reference, not in patterns"}, 400
    folio_normal = "OC-GC" + "-".join(reference_parts[-2:])
    folio_maestro = "OCM-GC" + f"{reference_parts[-2]}"
    folio_cotfc = "OC-GCCOTFC" + f"-{'-'.join(reference_parts[-2:])}"
    flag, error, result = get_folios_po_from_pattern(
        [folio_normal.lower(), folio_maestro.lower(), folio_cotfc.lower()]
    )
    if not flag:
        return {"data": [], "error": str(error)}, 400
    if not isinstance(result, Iterable):
        return {
            "data": result,
            "error": "Error at retrieving data from db",
        }, 400
    folios_out = []
    for po_order in result:
        id_order, folio = po_order
        count = 0
        if folio_normal.lower() in folio.lower():
            folio_temp = folio.lower().replace(folio_normal.lower(), "").split("-")
            for number in folio_temp:
                try:
                    count = int(number)
                    break
                except Exception:
                    continue
            folios_out.append(f"{folio_normal}-{count + 1:03d}".upper())
        elif folio_maestro.lower() in folio.lower():
            folio_temp = folio.lower().replace(folio_maestro.lower(), "").split("-")
            for number in folio_temp:
                try:
                    count = int(number)
                    break
                except Exception:
                    continue
            folios_out.append(
                f"{folio_maestro}-{count + 1:03d}-{dict_abbs[reference_parts[-2]].get('initial', '')}{reference_parts[-1]}".upper()
            )
        else:
            folio_temp = folio.lower().replace(folio_cotfc.lower(), "").split("-")
            for number in folio_temp:
                try:
                    count = int(number)
                    break
                except Exception:
                    continue
            folios_out.append(f"{folio_cotfc}-{count + 1:03d}".upper())
    if len(folios_out) == 0:
        folios_out = [
            f"{folio_normal}".upper(),
            f"{folio_maestro}-{dict_abbs[reference_parts[-2]].get('initial', '')}{reference_parts[-1]}".upper(),
            f"{folio_cotfc}".upper(),
        ]
    return {"data": folios_out, "error": None}, 200
