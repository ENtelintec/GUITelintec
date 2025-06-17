# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/jun/2025  at 11:09 $"

from datetime import datetime

import pytz

from static.constants import timezone_software, format_timestamps, log_file_po
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.departments.heads_controller import check_if_gerente
from templates.controllers.order.orders_controller import (
    insert_purchase_order,
    insert_purchase_order_item,
    update_purchase_order,
    update_purchase_order_item,
    cancel_purchase_order,
    get_purchase_orders_with_items,
    update_purchase_order_status,
)
from templates.misc.Functions_Files import write_log_file

import json


def map_products_po(products: list):
    products_out = []
    total_amount = 0.0
    for item in products:
        extra_info = item.get("extra_info", {})
        products_out.append(
            {
                "id": item.get("id"),
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
            }
        )
        total_amount += float(item.get("unit_price")) * float(item.get("quantity"))
    return products_out, total_amount


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
        return {"data": None, "msg": "error", "error": str(error)}, 400
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
            }
        )

    return {"data": data_out, "msg": "ok", "error": None}, 200


def create_purchaser_order_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = [
        {
            "user": data_token.get("emp_id"),
            "event": "create",
            "date": timestamp,
            "comment": "Create purchase order",
        }
    ]
    extra_info = {
        "comment": data.get("comment", ""),
    }
    flag, error, id_order = insert_purchase_order(
        timestamp,
        0,
        data_token.get("emp_id"),
        None,
        data["supplier"],
        None,
        data["folio"],
        data["reference"],
        history,
        extra_info,
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Orden de compra creada con ID-{id_order}"
    msg_moves = []
    flag_error = False
    for item in data["items"]:
        extra_info = {
            "id_inventory": item.get("id_inventory", 0),
            "brand": item.get("brand", ""),
            "category": item.get("category", ""),
            "n_parte": item.get("n_parte", ""),
            "url": item.get("url", ""),
        }
        flag, error, result = insert_purchase_order_item(
            id_order,
            item["quantity"],
            item["unit_price"],
            item["description"],
            extra_info,
        )
        if not flag:
            msg_moves.append(
                f"x-Error al crear item de orden de compra -{item['description']}-{str(error)}"
            )
            flag_error = True
        else:
            msg_moves.append(f"Item de orden de compra creado con ID-{result}")
    msg += "\n" + "\n".join(msg_moves)
    create_notification_permission_notGUI(
        msg, ["orders"], "Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg)
    if flag_error:
        return {
            "data": [id_order],
            "msg": "Error at creating order items",
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
            "event": "update",
            "date": timestamp,
            "comment": "Update purchase order",
        }
    )
    extra_info = {
        "comment": data.get("comment", ""),
    }
    flag, error, result = update_purchase_order(
        data["id"],
        timestamp,
        data["status"],
        data["created_by"],
        data["approved_by"],
        data["supplier"],
        data["total_amount"],
        data["folio"],
        data["reference"],
        history,
        extra_info,
    )
    if not flag:
        return {"data": None, "msg": "error", "error": str(error)}, 400
    msg = f"Orden de compra actualizada con ID-{data['id']}"
    msg_items = []
    flag_error = False
    for item in data["items"]:
        extra_info = {
            "id_inventory": item.get("id_inventory", 0),
            "brand": item.get("brand", ""),
            "category": item.get("category", ""),
            "n_parte": item.get("n_parte", ""),
            "url": item.get("url", ""),
        }
        if item["id"] == -1:
            flag, error, result = insert_purchase_order_item(
                data["id"],
                item["quantity"],
                item["unit_price"],
                item["description"],
                extra_info,
            )
        else:
            flag, error, result = update_purchase_order_item(
                item["id"],
                data["id"],
                item["quantity"],
                item["unit_price"],
                item["description"],
                extra_info,
            )
        if not flag:
            msg_items.append(
                f"x-Error al actualizar item de orden de compra -{item['description']}-{str(error)}"
            )
            flag_error = True
        else:
            msg_items.append(
                f"Item de orden de compra actualizado con ID-{item['id']}-{item['description']}"
            )
    msg += "\n" + "\n".join(msg_items)
    create_notification_permission_notGUI(
        msg, ["orders"], "Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg)
    if flag_error:
        return {
            "data": [data["id"]],
            "msg": "Error at creating order items",
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
            "event": "cancel",
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
            "event": "change_state",
            "date": timestamp,
            "comment": data.get("comment", ""),
        }
    )
    flag, error, result = update_purchase_order_status(
        data["id"],
        history,
        data["status"],
        data_token.get("emp_id"),
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
