# -*- coding: utf-8 -*-
import json
import os
import re
import tempfile
from datetime import datetime
from typing import Iterable

import pytz

from static.constants import (
    format_date,
    format_timestamps,
    log_file_po,
    timezone_software,
)
from templates.controllers.contracts.contracts_controller import (
    get_contracts_abreviations_db,
)
from templates.controllers.heads.heads_controller import check_if_gerente
from templates.controllers.material_request.sm_controller import (
    get_sm_by_folio,
    get_sm_by_id,
    get_sm_entries,
    get_sm_item_deliveries_db,
    get_sm_items_deliveries_for_match_db,
    update_deliveries_sm_item_db,
)
from templates.controllers.order.orders_controller import (
    cancel_po_application,
    cancel_purchase_order,
    delete_po_application,
    delete_purchase_order,
    get_all_item_purchase_order_with_id_item_sm,
    get_all_item_sm_with_supplier_fast_order,
    get_folios_po_from_pattern,
    get_item_with_po_folio,
    get_pos_application_with_items,
    get_pos_application_with_items_to_approve,
    get_purchase_order_with_items_by_id,
    get_purchase_orders_with_items,
    insert_po_application,
    insert_purchase_order,
    insert_purchase_order_item,
    insert_purchase_order_item_from_applications,
    update_po_application,
    update_po_application_item,
    update_po_application_status,
    update_po_item,
    update_purchase_order,
    update_purchase_order_status,
)
from templates.controllers.product.movements_controller import get_ins_db_detail
from templates.forms.PurchaseForms import FilePoPDF
from templates.forms.StorageMovSM import FilePurchaseList
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.misc.Functions_Files import write_log_file
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
                "id_item_sm": extra_info.get("id_item_sm"),
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
        "id_item_sm": data.get("id_item_sm", 0),
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
        flag, error, result = check_if_gerente(data_token.get("emp_id"), data_token)
        emp_id = data_token.get("emp_id") if not flag and len(result) <= 0 else None
    status_map = {"pendiente": 0, "recibido": 1, "cancelado": 4}
    status = status_map.get(status, None)  # Si status no es válido, se usa None
    flag, error, result = get_purchase_orders_with_items(status, emp_id, data_token)
    if not flag:
        return {"data": [], "msg": "Error al obtener órdenes de compra", "error": error}, 400
    if not isinstance(result, Iterable):
        return {
            "data": [],
            "msg": "Error al obtener órdenes de compra: respuesta inesperada de la DB",
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
        metadata_telintec, metadata_supplier = create_metadatas_from_extra_info_po(extra_info)
        order_quotation = extra_info.get("order_quotation", "")
        folio_supplier = extra_info.get("folio_supplier", "")
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
                "folio_supplier": folio_supplier,
            }
        )

    return {"data": data_out, "msg": "ok", "error": None}, 200


def create_purchaser_order_api(data, data_token):
    sm_id = data.get("sm_id", 0)
    update_sm_control_table = True
    if sm_id >= 0:
        flag, error, result_sm = get_sm_by_id(sm_id, data_token)

    else:
        result_sm = [0]
        print("sm not found")
    if len(result_sm) < 2:
        update_sm_control_table = False
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    comment_history = f"Orden de compra creada por {data_token.get('name')}"
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
        "folio_supplier": data.get("folio_supplier", ""),
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
        data_token,
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear la orden de compra", "error": error}, 400
    if not isinstance(id_order, int) or id_order <= 0:
        return {
            "data": None,
            "msg": "No se pudo crear la orden de compra: ID inválido",
            "error": id_order,
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
                data_token,
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
                data_token,
                item["currency"],
            )
        if not flag:
            msg_moves.append(
                f"x-Error al actualizar item de orden de compra -{item['description']}-{error}"
                if update_item
                else f"x-Error al crear item de orden de compra -{item['description']}-{error}"
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
        flag, error, result = delete_purchase_order(id_order, data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún ítem; orden de compra eliminada"
            if flag
            else f"No se pudo crear ningún ítem ni eliminar la orden (ID {id_order})",
            "error": "\n".join(msg_moves),
        }, 400
    msg += "\n" + "\n".join(msg_moves)
    sync_msgs = sync_sm_deliveries_from_po(
        id_order,
        data["folio"],
        data.get("folio_supplier", ""),
        data["time_delivery"],
        data["items"],
        data_token,
        timestamp,
    )
    if sync_msgs:
        msg += "\n" + "\n".join(sync_msgs)
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
        msg, data_token, ["orders"], "Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg, data_token)
    if flag_error:
        return {
            "data": {"id_order": id_order},
            "msg": f"Orden de compra creada (ID {id_order}). Algunos ítems no se pudieron crear.",
            "error": "\n".join(msg_moves),
        }, 400
    return {
        "data": {"id_order": id_order},
        "msg": f"Orden de compra creada correctamente (ID {id_order})",
        "error": None,
    }, 201


DELIVERY_COMMENT_PREFIX = "Entrega estimada"
_delivery_comment_pattern = re.compile(r"\s*\[" + DELIVERY_COMMENT_PREFIX + r":[^\]]*\]")


def _upsert_delivery_comment(comment, time_delivery) -> str:
    """Reemplaza (o agrega) el segmento marcado de entrega estimada en el comment,
    conservando el resto del texto. Idempotente entre actualizaciones de la OC."""
    base = _delivery_comment_pattern.sub("", str(comment) if comment else "").strip()
    time_delivery = "" if time_delivery is None else str(time_delivery)
    segment = f"[{DELIVERY_COMMENT_PREFIX}: {time_delivery}]"
    return f"{base} {segment}".strip() if base else segment


def sync_sm_deliveries_from_po(
    po_id, folio, folio_supplier, time_delivery, items, data_token, timestamp
):
    """Rastrea cambios de la OC hacia los deliveries de los items de SM.

    Para cada item de la OC con un id_item_sm valido, busca el delivery cuyo
    id_order coincida con la OC (o crea uno nuevo) y mapea folio, folio_supplier
    y time_delivery (al comment). Tambien registra el cambio en el history de la
    SM. Devuelve una lista de mensajes (en español) para anexar a la respuesta/log.
    No es fatal: los errores se reportan como mensajes, no detienen el flujo.
    """
    msgs: list[str] = []
    for item in items:
        id_item_sm = item.get("id_item_sm", 0)
        try:
            id_item_sm = int(id_item_sm) if id_item_sm is not None else 0
        except (TypeError, ValueError):
            id_item_sm = 0
        if id_item_sm <= 0:
            continue
        flag, error, result = get_sm_item_deliveries_db(id_item_sm, data_token)
        if not flag or not (isinstance(result, (list, tuple))) or len(result) < 4:
            msgs.append(
                f"x-No se pudo rastrear el item de SM {id_item_sm} (OC {folio}): {error}"
            )
            continue
        _id_item, id_sm, deliveries_raw, history_raw = result[0], result[1], result[2], result[3]
        try:
            deliveries = json.loads(deliveries_raw) if deliveries_raw else []
            deliveries = deliveries if isinstance(deliveries, list) else []
            history_sm = json.loads(history_raw) if history_raw else []
            history_sm = history_sm if isinstance(history_sm, list) else []
        except (TypeError, ValueError) as e:
            msgs.append(
                f"x-Datos de SM invalidos para el item {id_item_sm} (OC {folio}): {e}"
            )
            continue
        delivery = next(
            (d for d in deliveries if isinstance(d, dict) and d.get("id_order") == po_id),
            None,
        )
        created = False
        if delivery is None:
            delivery = {
                "quantity": item.get("quantity", 0),
                "timestamp": timestamp,
                "comment": "",
                "state": 0,
                "folio": "",
                "color": "#ffffff",
                "id_order": po_id,
                "folio_supplier": "",
            }
            deliveries.append(delivery)
            created = True
        delivery["id_order"] = po_id
        delivery["folio"] = folio
        delivery["folio_supplier"] = folio_supplier
        delivery["comment"] = _upsert_delivery_comment(delivery.get("comment", ""), time_delivery)
        comment_history = (
            f"OC {folio} (ID {po_id}): se {'creó' if created else 'actualizó'} la entrega "
            f"del item de SM {id_item_sm} (folio_supplier: {folio_supplier}, entrega: {time_delivery})."
        )
        history_sm.append(
            {
                "user": data_token.get("emp_id"),
                "event": "Rastreo de entrega por OC",
                "date": timestamp,
                "comment": comment_history,
            }
        )
        flag, error, _ = update_deliveries_sm_item_db(
            deliveries, id_item_sm, history_sm, id_sm, data_token
        )
        if not flag:
            msgs.append(
                f"x-Error al actualizar la entrega del item de SM {id_item_sm} (OC {folio}): {error}"
            )
        else:
            msgs.append(comment_history)
    return msgs


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
        "folio_supplier": data.get("folio_supplier", ""),
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
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar la orden de compra",
            "error": error,
        }, 400
    msg = f"Orden de compra actualizada con ID-{data['id']}"
    msg_items: list[str] = []
    flag_error = False
    for item in data["items"]:
        extra_info = create_extra_info_product_from_data(item)
        update_item = True
        if item["id"] is None or item["id"] <= 0:
            flag, error, result = insert_purchase_order_item(
                data["id"],
                item["quantity"],
                item["unit_price"],
                item["description"],
                item["duration_services"],
                extra_info,
                data_token,
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
                data_token,
                item["currency"],
            )
        if not flag:
            msg_items.append(
                f"x-Error al actualizar item de orden de compra -{item['description']}-{error}"
                if update_item
                else f"x-Error al crear item de orden de compra -{item['description']}-{error}"
            )
            flag_error = True
        else:
            msg_items.append(
                f"Item de orden de compra actualizado con ID-{item['id']}-{item['description']}"
                if update_item
                else f"Item de orden de compra creado con ID-{result}-{item['description']}"
            )
    msg += "\n" + "\n".join(msg_items)
    sync_msgs = sync_sm_deliveries_from_po(
        data["id"],
        data["folio"],
        data.get("folio_supplier", ""),
        data["time_delivery"],
        data["items"],
        data_token,
        timestamp,
    )
    if sync_msgs:
        msg += "\n" + "\n".join(sync_msgs)
    create_notification_permission_notGUI(
        msg, data_token, ["orders"], "Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg, data_token)
    if flag_error:
        return {
            "data": {"id_order": data["id"]},
            "msg": f"Orden de compra actualizada (ID {data['id']}). Algunos ítems no se pudieron actualizar.",
            "error": "\n".join(msg_items),
        }, 400
    return {
        "data": {"id_order": data["id"]},
        "msg": f"Orden de compra actualizada correctamente (ID {data['id']})",
        "error": None,
    }, 200


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
        data_token,
    )

    if not flag:
        return {"data": None, "msg": "No se pudo cancelar la orden de compra", "error": error}, 400
    msg = f"Orden de compra cancelada correctamente (ID {data['id']})"
    create_notification_permission_notGUI(
        msg, data_token, ["orders"], "Orden de compra cancelada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg, data_token)
    return {"data": {"id_order": data["id"]}, "msg": msg, "error": None}, 200


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
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo cambiar el estado de la orden de compra",
            "error": error,
        }, 400
    msg = f"Estado de orden de compra actualizado (ID {data['id']}) a {data['status']}"
    create_notification_permission_notGUI(
        msg,
        data_token,
        ["orders", "administracion"],
        "Orden de compra actualizada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg, data_token)
    return {"data": {"id_order": data["id"]}, "msg": msg, "error": None}, 200


def fetch_pos_applications_to_approve(data_token):
    # permissions = data_token.get("permissions")
    # permissions_last = [item.lower().split(".")[-1] for item in permissions.values()]
    flag, error, result = get_pos_application_with_items_to_approve(data_token)
    if not flag:
        return {
            "data": [],
            "msg": "Error al obtener solicitudes de OC para aprobar",
            "error": error,
        }, 400
    data_out = []
    if not isinstance(result, Iterable):
        return {
            "data": [],
            "msg": "Error al obtener solicitudes de OC: respuesta inesperada de la DB",
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
        flag, error, result = check_if_gerente(data_token.get("emp_id"), data_token)
        emp_id = data_token.get("emp_id") if not flag and len(result) <= 0 else None
    status_map = {"pendiente": 0, "recibido": 1, "cancelado": 4}
    status = status_map.get(status, None)  # Si status no es válido, se usa None
    flag, error, result = get_pos_application_with_items(status, emp_id, data_token)
    if not flag:
        return {"data": [], "msg": "Error al obtener solicitudes de OC", "error": error}, 400
    data_out = []
    if not isinstance(result, Iterable):
        return {
            "data": [],
            "msg": "Error al obtener solicitudes de OC: respuesta inesperada de la DB",
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


def fetch_po_item_sm_item_id(data_token):
    flag, error, result = get_all_item_purchase_order_with_id_item_sm(data_token)
    if not flag:
        return {"data": [], "msg": "Error al obtener ítems de OC con ID de SM", "error": error}, 400
    data_out = []
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": [],
            "msg": "Error al obtener ítems de OC: respuesta inesperada de la DB",
            "error": None,
        }, 400
    for item in result:
        (
            id_item,
            id_order,
            folio,
            id_item_sm,
            quantity,
            fast_order,
            description,
            tool,
            id_supplier,
        ) = item
        data_out.append(
            {
                "id_item": id_item,
                "id_order": id_order,
                "folio": folio,
                "id_item_sm": id_item_sm,
                "quantity": quantity,
                "fast_order": fast_order,
                "description": description,
                "tool": tool,
                "id_supplier": id_supplier,
            }
        )
    return {"data": data_out, "msg": "ok", "error": None}, 200


def create_po_application_api(data, data_token):
    sm_id = data.get("sm_id", -1)
    if sm_id == -1:
        return {
            "data": None,
            "msg": "sm_id o reference son requeridos",
            "error": None,
        }, 400

    update_sm_control_table = False
    if sm_id > 0:
        flag, error, result_sm = get_sm_by_id(sm_id, data_token)
    else:
        flag, error, result_sm = get_sm_by_folio(data.get("reference"), data_token)
    if not (isinstance(result_sm, list) or isinstance(result_sm, tuple)):
        return {"data": None, "msg": "SM no encontrado", "error": None}, 400
    extra_info = {}
    if flag:
        update_sm_control_table = True
        extra_info = {"sm_id": result_sm[0]}
        data["reference"] = result_sm[1]
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = [
        {
            "user": data_token.get("emp_id"),
            "event": "Creación de solicitud",
            "date": timestamp,
            "comment": f"Se creo una solicitud de orden de compra con referencia {data['reference']} por el usuario {data_token.get('name')}.",
        }
    ]
    flag, error, id_po_app = insert_po_application(
        timestamp,
        1,
        data_token.get("emp_id"),
        data["reference"],
        history,
        data_token,
        extra_info=extra_info,
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear la solicitud de OC", "error": error}, 400
    if not isinstance(id_po_app, int):
        return {
            "data": None,
            "msg": "No se pudo crear la solicitud de OC: ID inválido",
            "error": error,
        }, 400
    msg = f"Solicitud de Orden de compra creada con ID-{id_po_app}"
    msg_moves: list[str] = []
    flag_error = False
    tool_detected = False
    count_errors = 0
    for item in data["items"]:
        extra_info = create_extra_info_product_from_data(item)
        flag, error, result = insert_purchase_order_item_from_applications(
            id_po_app,
            item["quantity"],
            item["unit_price"],
            item["description"],
            "0",
            extra_info,
            data_token,
            item["tool"],
        )
        if item["tool"] == 1:
            tool_detected = True
        if not flag:
            msg_moves.append(
                f"x-Error al crear item de orden de compra -{item['description']}-{error}"
            )
            flag_error = True
            count_errors += 1
        else:
            msg_moves.append(f"Item de orden de compra creado con ID-{result}")
    msg += "\n" + "\n".join(msg_moves)
    if count_errors == len(data["items"]):
        flag, error, result_del = delete_po_application(id_po_app, data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún ítem; solicitud de OC eliminada"
            if flag
            else f"No se pudo crear ningún ítem ni eliminar la solicitud (ID {id_po_app})",
            "error": "\n".join(msg_moves),
        }, 400

    if tool_detected:
        msg += "\n" + "Se detectó que se solicita una herramienta, esta requerirá aprobación."
        flag, error, result = update_po_application_status(id_po_app, history, 0, 0, data_token)
        if not flag:
            return {
                "data": None,
                "msg": "Error al actualizar estado de solicitud de OC",
                "error": error,
            }, 400
    if update_sm_control_table:
        code, data_out = update_sm_from_control_table(
            data={
                "id": result_sm[0],
                "info": {"warehouse_reviewed": 1, "admin_notification_date": timestamp},
            },
            data_token=data_token,
            sm_data=result_sm,
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
        data_token,
        ["orders", "almacen", "sm"],
        "Solicitud de orden de compra creada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg, data_token)
    if flag_error:
        return {
            "data": {"id_po_app": id_po_app},
            "msg": f"Solicitud de OC creada (ID {id_po_app}). Algunos ítems no se pudieron crear.",
            "error": "\n".join(msg_moves),
        }, 400
    return {
        "data": {"id_po_app": id_po_app},
        "msg": f"Solicitud de OC creada correctamente (ID {id_po_app})",
        "error": None,
    }, 201


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
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar la solicitud de OC",
            "error": error,
        }, 400
    msg = f"Solicitud de Orden de compra actualizada con ID-{data['id']}"
    msg_items: list[str] = []
    flag_error = False
    for item in data["items"]:
        extra_info = create_extra_info_product_from_data(item)
        if item["id"] == -1:
            flag, error, result = insert_purchase_order_item(
                data["id"],
                item["quantity"],
                item["unit_price"],
                item["description"],
                "0",
                extra_info,
                data_token,
            )
        else:
            flag, error, result = update_po_application_item(
                item["id"],
                item["quantity"],
                item["unit_price"],
                0,
                item["description"],
                extra_info,
                data_token,
            )
        if not flag:
            msg_items.append(
                f"x-Error al actualizar item de solicitud de orden de compra -{item['description']}-{error}"
            )
            flag_error = True
        else:
            msg_items.append(
                f"Item de solicitud de orden de compra actualizado con ID-{item['id']}-{item['description']}"
            )
    msg += "\n" + "\n".join(msg_items)
    create_notification_permission_notGUI(
        msg, data_token, ["orders"], "Solicitud de Orden de compra creada", data_token.get("emp_id")
    )
    write_log_file(log_file_po, msg, data_token)
    if flag_error:
        return {
            "data": {"id_po_app": data["id"]},
            "msg": f"Solicitud de OC actualizada (ID {data['id']}). Algunos ítems no se pudieron actualizar.",
            "error": "\n".join(msg_items),
        }, 400
    return {
        "data": {"id_po_app": data["id"]},
        "msg": f"Solicitud de OC actualizada correctamente (ID {data['id']})",
        "error": None,
    }, 200


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
        history,
        data["id"],
        data.get("status", 4),
        data_token,
    )
    if not flag:
        return {"data": None, "msg": "No se pudo cancelar la solicitud de OC", "error": error}, 400
    msg = f"Solicitud de OC cancelada correctamente (ID {data['id']})"
    create_notification_permission_notGUI(
        msg,
        data_token,
        ["orders"],
        "Solicitud de Orden de compra cancelada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg, data_token)
    return {"data": {"id_po_app": data["id"]}, "msg": msg, "error": None}, 200


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
        data["id"], history, data["status"], data["approved"], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo cambiar el estado de la solicitud de OC",
            "error": error,
        }, 400
    msg = f"Estado de solicitud de OC actualizado (ID {data['id']}) a {data['status']}"
    create_notification_permission_notGUI(
        msg,
        data_token,
        ["orders", "administracion"],
        "Solicitud de Orden de compra actualizada",
        data_token.get("emp_id"),
    )
    write_log_file(log_file_po, msg, data_token)
    return {"data": {"id_po_app": data["id"]}, "msg": msg, "error": None}, 200


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


def dowload_file_purchase(order_id: int, data_token):
    flag, error, result = get_purchase_order_with_items_by_id(order_id, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "Error al obtener la orden de compra",
            "error": error,
        }, 400
    if not isinstance(result, tuple) or len(result) == 0:
        return {
            "data": None,
            "msg": f"Orden de compra no encontrada (ID {order_id})",
            "error": error,
        }, 400
    date = result[0]
    download_path = os.path.join(
        tempfile.mkdtemp(), os.path.basename(f"oc_{result[5]}_{date.date()}.pdf")
    )
    products = []
    items = json.loads(result[8]) or []
    total_amount = 0.0
    # El LEFT JOIN + JSON_ARRAYAGG produce un placeholder de puros NULL cuando la OC no tiene items
    items = [item for item in items if item.get("id") is not None]
    for index, item in enumerate(items):
        extra_info_item = item["extra_info"] or {}
        quantity = item["quantity"] or 0
        unit_price = item["unit_price"] or 0
        subtotal = quantity * unit_price
        products.append(
            [
                index + 1,
                item["description"],
                extra_info_item.get("n_parte"),
                item["duration_services"],
                "NA",
                quantity,
                unit_price,
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
        return {
            "data": None,
            "msg": "Error al generar el PDF de la orden de compra",
            "error": None,
        }, 400
    return download_path, 200


def generate_folios_po(reference, data_token):
    flag, error, result_abb = get_contracts_abreviations_db(data_token)
    abbs_area = []
    for item in result_abb:
        if item[0] != "" and item[4] == 0:
            abbs_area.append(item[0])
        elif item[4] == 1:
            contract_code = item[5] if item[5] is not None else ""
            if contract_code == "":
                continue
            abbs_area.append(contract_code[-4:])

    # abbs_area = [item[0] for item in result_abb if item[0] != "" and item[4] == 0]
    reference_parts = reference.lower().split("-")
    if len(reference_parts) <= 2:
        return {"data": [], "msg": "Referencia no válida: formato incorrecto", "error": None}, 400
    print(reference_parts, abbs_area)
    if reference_parts[1].upper() not in abbs_area and reference_parts[1].lower() not in abbs_area:
        return {
            "data": [],
            "msg": "Referencia no válida: patrón no encontrado o contrato no en DB",
            "error": None,
        }, 400
    folio_normal = "OC-GC" + "-".join(reference_parts[-2:])
    folio_maestro = "OCM-GC" + f"{reference_parts[-2]}"
    folio_cotfc = "OC-GCCOTFC" + f"-{'-'.join(reference_parts[-2:])}"
    flag, error, result = get_folios_po_from_pattern(
        [folio_normal.lower(), folio_maestro.lower(), folio_cotfc.lower()], data_token
    )
    if not flag:
        return {"data": [], "msg": "Error al obtener folios de la DB", "error": error}, 400
    if not isinstance(result, Iterable):
        return {
            "data": [],
            "msg": "Error al obtener folios: respuesta inesperada de la DB",
            "error": None,
        }, 400

    def extract_count(folio_value, pattern):
        remainder = folio_value.lower().replace(pattern.lower(), "").split("-")
        for number in remainder:
            try:
                return int(number)
            except (ValueError, TypeError):
                continue
        return 0

    count_normal = 0
    count_maestro = 0
    count_cotfc = 0
    for po_order in result:
        id_order, folio = po_order
        folio_lower = folio.lower()
        if folio_cotfc.lower() in folio_lower:
            count_cotfc = max(count_cotfc, extract_count(folio, folio_cotfc))
        elif folio_normal.lower() in folio_lower:
            count_normal = max(count_normal, extract_count(folio, folio_normal))
        elif folio_maestro.lower() in folio_lower:
            count_maestro = max(count_maestro, extract_count(folio, folio_maestro))
    folios_out = [
        f"{folio_normal}-{count_normal + 1:03d}".upper(),
        f"{folio_maestro}-{count_maestro + 1:03d}-{reference_parts[-1]}".upper(),
        f"{folio_cotfc}-{count_cotfc + 1:03d}".upper(),
    ]
    return {"data": folios_out, "msg": None, "error": None}, 200


def group_item_by_supplier_and_inventory(items: list):
    dict_out = {}
    for item in items:
        supplier_id = item.get("supplier_id", 0)
        supplier_name = item.get("supplier_name", "Sin proveedor")
        id_inventory = item.get("id_inventory", 0)
        if supplier_id not in dict_out:
            dict_out[supplier_id] = {"supplier_name": supplier_name, "inventories": {}}
        inventories = dict_out[supplier_id]["inventories"]
        if id_inventory not in inventories:
            inventories[id_inventory] = {
                "items": [item],
                "total_qty": item.get("quantity_c", item["quantity"]),
                "total_amount": float(item.get("price_unit", 0))
                * float(item.get("quantity_c", item["quantity"])),
            }
        else:
            inventories[id_inventory]["items"].append(item)
            inventories[id_inventory]["total_qty"] += item.get("quantity_c", item["quantity"])
            inventories[id_inventory]["total_amount"] += float(item.get("price_unit", 0)) * float(
                item.get("quantity_c", item["quantity"])
            )
    return dict_out


def download_file_purchase_item_approved(data_token):
    flag, error, sm_data = get_sm_entries(data_token, None)
    if not flag:
        return {
            "data": [],
            "error": error,
            "msg": "Error at retrieving sm data",
        }, 400
    items_with_approved = []
    for sm in sm_data:
        sm_id = sm[0]
        items = json.loads(sm[10])
        for item in items:
            deliveries = item.get("deliveries", [])
            deliveries = [] if deliveries is None else deliveries
            if len(deliveries) > 0:
                for delivery in deliveries:
                    if delivery.get("state", 0) == 4:  # falta checar estado asignado al ok compra
                        flag, error, items_po = get_item_with_po_folio(
                            delivery["folio"], item["id"], data_token
                        )
                        try:
                            if not (isinstance(items_po, Iterable)):
                                price_unit = 0.0
                                supplier_id = 0
                                supplier_name = "None"
                            else:
                                price_unit = items_po[3]
                                supplier_id = items_po[7]
                                supplier_name = items_po[8]
                        except Exception:
                            price_unit = 0.0
                            supplier_id = 0
                            supplier_name = "None"

                        items_with_approved.append(
                            {
                                "id_item": item["id"],
                                "id_inventory": item["id_inventory"],
                                "name": item["name"],
                                "udm": item["udm"],
                                "id_sm": sm_id,
                                "folio": sm[1],
                                "quantity": item["quantity"],
                                "delivered": delivery["quantity"],
                                "quantity_c": delivery["quantity"],
                                "timestamp": delivery["timestamp"],
                                "comment": delivery["comment"],
                                "state": delivery["state"],
                                "folio_po": delivery["folio"],
                                "price_unit": price_unit,
                                "supplier_id": supplier_id,
                                "supplier_name": supplier_name,
                            }
                        )
                        break
    dict_items = group_item_by_supplier_and_inventory(items_with_approved)
    download_path = os.path.join(tempfile.mkdtemp(), os.path.basename("purchase_list.pdf"))
    flag = FilePurchaseList(dict_items, download_path)
    if not flag:
        return {
            "data": [],
            "error": "Error at generating pdf",
            "msg": "Error at generating pdf",
        }, 400
    return {"data": download_path, "error": None, "msg": "ok"}, 200


def get_items_with_fast_order(data_token):
    flag, error, result = get_all_item_sm_with_supplier_fast_order(data_token)
    if not flag:
        return {"data": [], "msg": "Error al obtener ítems con fast order", "error": error}, 400
    if not (isinstance(result, Iterable)):
        return {
            "data": [],
            "msg": "Error al obtener ítems con fast order: respuesta inesperada de la DB",
            "error": None,
        }, 400
    data_out = []
    for item in result:
        data_out.append(
            {
                "id_item": item[0],
                "id_purchase": item[1],
                "id_item_sm": item[2],
                "id_inventory": item[3],
                "quantity": item[4],
                "fast_order": item[5],
                "description": item[6],
                "tool": item[7],
                "id_supplier": item[8],
                "name_supplier": item[9],
                "unit_price": float(item[10]),
                "id_sm": item[11],
                "folio_sm": item[12],
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def _normalize_folio_match(value) -> str:
    """Normaliza folios/references para el match: sin espacios extremos y en mayusculas."""
    return str(value).strip().upper() if value else ""


def _safe_number(value):
    try:
        return float(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def match_po_movements_and_sms(params, data_token):
    """Concilia las OCs con los movimientos de entrada de almacen y sus SMs.

    Match OC<->movimiento: el reference del movimiento (extra_info.$.reference,
    guardado en mayusculas) contra folio y folio_supplier de la OC; primero
    exacto (case-insensitive, con trim) y, solo para movimientos que no pegaron
    exacto con ninguna OC, fallback contains (folio dentro del reference)
    marcado como match_type 'parcial'. Un movimiento puede aparecer bajo todas
    las OCs con las que pega. SMs relacionadas: primario por deliveries
    (id_order == id de la OC), fallback por extra_info.id_item_sm de los items
    de la OC. Ver Docs/po_movements_inbound_match.md.
    """
    params = params if isinstance(params, dict) else {}
    status = None
    status_raw = params.get("status")
    if status_raw not in (None, ""):
        try:
            status = int(status_raw)
        except (TypeError, ValueError):
            return {
                "data": [],
                "msg": "Parametro status invalido",
                "error": "status debe ser un entero",
            }, 400
    date_from = None
    date_to = None
    for key in ("date_from", "date_to"):
        raw = params.get(key)
        if raw in (None, ""):
            continue
        try:
            parsed = datetime.strptime(str(raw), format_date).date()
        except ValueError:
            return {
                "data": [],
                "msg": f"Parametro {key} invalido",
                "error": f"{key} debe tener formato {format_date}",
            }, 400
        if key == "date_from":
            date_from = parsed
        else:
            date_to = parsed
    folio_filter = _normalize_folio_match(params.get("folio"))
    # misma visibilidad que fetch_purchase_orders: no admin ni gerente -> solo sus OCs
    permissions = data_token.get("permissions")
    permissions_last = [item.lower().split(".")[-1] for item in permissions.values()]
    if "administrator" in permissions_last:
        emp_id = None
    else:
        flag, error, result = check_if_gerente(data_token.get("emp_id"), data_token)
        emp_id = data_token.get("emp_id") if not flag and len(result) <= 0 else None
    flag, error, result = get_purchase_orders_with_items(status, emp_id, data_token)
    if not flag:
        return {"data": [], "msg": "Error al obtener órdenes de compra", "error": error}, 400
    if not isinstance(result, Iterable):
        return {
            "data": [],
            "msg": "Error al obtener órdenes de compra: respuesta inesperada de la DB",
            "error": None,
        }, 400
    # pos: tuplas (id_order, base_out, folio_norm, folio_supplier_norm, ids_item_sm)
    pos = []
    ids_item_sm_all = set()
    for row in result:
        (
            id_order,
            timestamp,
            status_po,
            created_by,
            supplier,
            folio,
            history,
            extra_info,
            products,
            time_delivery,
        ) = row
        if date_from or date_to:
            ts = timestamp
            if isinstance(ts, str):
                try:
                    ts = datetime.strptime(ts, format_timestamps)
                except ValueError:
                    ts = None
            # timestamp no parseable -> la OC se incluye (no se filtra a ciegas)
            if ts is not None:
                if date_from and ts.date() < date_from:
                    continue
                if date_to and ts.date() > date_to:
                    continue
        extra_info = json.loads(extra_info) if extra_info else {}
        folio_supplier = extra_info.get("folio_supplier", "")
        folio_norm = _normalize_folio_match(folio)
        folio_supplier_norm = _normalize_folio_match(folio_supplier)
        if folio_filter and folio_filter not in (folio_norm, folio_supplier_norm):
            continue
        products = json.loads(products) if products else []
        products, _total = map_products_po(products)
        ids_item_sm = []
        for item in products:
            id_item_sm = item.get("id_item_sm")
            try:
                id_item_sm = int(id_item_sm) if id_item_sm is not None else 0
            except (TypeError, ValueError):
                id_item_sm = 0
            if id_item_sm > 0:
                ids_item_sm.append(id_item_sm)
                ids_item_sm_all.add(id_item_sm)
        base_out = {
            "id": id_order,
            "folio": folio,
            "folio_supplier": folio_supplier,
            "status": status_po,
            "supplier": supplier,
            "created_by": created_by,
            "timestamp": timestamp.strftime(format_timestamps)
            if not isinstance(timestamp, str)
            else timestamp,
            "time_delivery": time_delivery,
        }
        pos.append((id_order, base_out, folio_norm, folio_supplier_norm, ids_item_sm))
    if not pos:
        return {
            "data": [],
            "msg": "Se conciliaron 0 ordenes de compra: 0 con entradas y 0 sin entradas",
            "error": None,
        }, 200
    # movimientos de entrada con reference
    flag, error, result = get_ins_db_detail(data_token)
    if not flag:
        return {"data": [], "msg": "Error al obtener movimientos de entrada", "error": error}, 400
    movements = []  # tuplas (ref_norm, movimiento mapeado a dict de salida)
    for row in result:  # pyrefly: ignore
        reference_raw = row[11]
        try:
            reference = json.loads(reference_raw) if reference_raw else ""
        except (TypeError, ValueError):
            reference = str(reference_raw)
        ref_norm = _normalize_folio_match(reference)
        if not ref_norm:
            continue
        movement_date = row[5]
        movements.append(
            (
                ref_norm,
                {
                    "id_movement": row[0],
                    "id_product": row[1],
                    "sku": row[2],
                    "quantity": _safe_number(row[4]),
                    "movement_date": movement_date.strftime(format_timestamps)
                    if movement_date is not None and not isinstance(movement_date, str)
                    else movement_date,
                    "sm_id": row[6],
                    "product_name": row[7],
                    "udm": row[8],
                    "reference": reference,
                },
            )
        )
    by_folio = {}
    by_folio_supplier = {}
    for id_po, _base, folio_norm, folio_supplier_norm, _ids in pos:
        if folio_norm:
            by_folio.setdefault(folio_norm, []).append(id_po)
        if folio_supplier_norm:
            by_folio_supplier.setdefault(folio_supplier_norm, []).append(id_po)
    movements_by_po = {}
    for ref_norm, mov_data in movements:
        exact_matches = []
        seen_ids = set()
        for id_po in by_folio.get(ref_norm, []):
            exact_matches.append((id_po, "folio"))
            seen_ids.add(id_po)
        for id_po in by_folio_supplier.get(ref_norm, []):
            if id_po not in seen_ids:
                exact_matches.append((id_po, "folio_supplier"))
        if exact_matches:
            for id_po, matched_by in exact_matches:
                movements_by_po.setdefault(id_po, []).append(
                    {**mov_data, "matched_by": matched_by, "match_type": "exacto"}
                )
            continue
        for id_po, _base, folio_norm, folio_supplier_norm, _ids in pos:
            if folio_norm and folio_norm in ref_norm:
                movements_by_po.setdefault(id_po, []).append(
                    {**mov_data, "matched_by": "folio", "match_type": "parcial"}
                )
            elif folio_supplier_norm and folio_supplier_norm in ref_norm:
                movements_by_po.setdefault(id_po, []).append(
                    {**mov_data, "matched_by": "folio_supplier", "match_type": "parcial"}
                )
    # SMs relacionadas: por deliveries (primario) y por id_item_sm (fallback)
    flag, error, result = get_sm_items_deliveries_for_match_db(
        sorted(ids_item_sm_all), data_token
    )
    if not flag:
        return {
            "data": [],
            "msg": "Error al obtener los items de SM para el match",
            "error": error,
        }, 400
    deliveries_by_po = {}
    items_by_id = {}
    for row in result:  # pyrefly: ignore
        id_item, id_sm, folio_sm, status_sm, name, quantity, dispatched, deliveries_raw = row
        try:
            deliveries = json.loads(deliveries_raw) if deliveries_raw else []
        except (TypeError, ValueError):
            deliveries = []
        deliveries = deliveries if isinstance(deliveries, list) else []
        item_info = {
            "id_item": id_item,
            "id_sm": id_sm,
            "folio_sm": folio_sm,
            "status_sm": status_sm,
            "description": name,
            "quantity": _safe_number(quantity),
            "dispatched": _safe_number(dispatched),
        }
        items_by_id[id_item] = item_info
        for delivery in deliveries:
            if not isinstance(delivery, dict):
                continue
            id_order_dv = delivery.get("id_order")
            try:
                id_order_dv = int(id_order_dv) if id_order_dv is not None else 0
            except (TypeError, ValueError):
                id_order_dv = 0
            if id_order_dv > 0:
                deliveries_by_po.setdefault(id_order_dv, []).append((item_info, delivery))
    data_out = []
    for id_po, base_out, _folio_norm, _folio_supplier_norm, ids_item_sm in sorted(
        pos, key=lambda p: p[0], reverse=True
    ):
        entries = deliveries_by_po.get(id_po, [])
        link = "deliveries"
        if not entries:
            link = "id_item_sm"
            entries = [
                (items_by_id[id_item], None)
                for id_item in ids_item_sm
                if id_item in items_by_id
            ]
        sms_meta = {}
        sms_items = {}
        for item_info, delivery in entries:
            id_sm = item_info["id_sm"]
            sms_meta.setdefault(
                id_sm,
                {
                    "id_sm": id_sm,
                    "folio": item_info["folio_sm"],
                    "status": item_info["status_sm"],
                    "link": link,
                },
            )
            sms_items.setdefault(id_sm, []).append(
                {
                    "id_item": item_info["id_item"],
                    "description": item_info["description"],
                    "quantity": item_info["quantity"],
                    "dispatched": item_info["dispatched"],
                    "delivery": delivery,
                }
            )
        po_movements = movements_by_po.get(id_po, [])
        data_out.append(
            {
                **base_out,
                "reception_status": "con_entradas" if po_movements else "sin_entradas",
                "movements": po_movements,
                "sms": [
                    {**sms_meta[id_sm], "items": sms_items[id_sm]} for id_sm in sms_meta
                ],
            }
        )
    n_con = sum(1 for po in data_out if po["reception_status"] == "con_entradas")
    msg = (
        f"Se conciliaron {len(data_out)} ordenes de compra: "
        f"{n_con} con entradas y {len(data_out) - n_con} sin entradas"
    )
    return {"data": data_out, "msg": msg, "error": None}, 200
