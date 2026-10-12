# -*- coding: utf-8 -*-
import json
import os
import tempfile
from datetime import datetime

import boto3
import pytz
from botocore.exceptions import ClientError, NoCredentialsError

from static.constants import (
    format_timestamps,
    log_file_sgi_chv,
    secrets,
    timezone_software,
)
from templates.controllers.vouchers.vouchers_controller import (
    append_history_voucher,
    create_voucher_general,
    create_voucher_item,
    create_voucher_safety,
    create_voucher_tools,
    create_voucher_vehicle,
    delete_items_voucher,
    delete_voucher_general,
    delete_voucher_item,
    delete_voucher_safety,
    delete_voucher_tools,
    delete_voucher_vehicle,
    get_voucher_vehicle_by_id,
    get_vouchers_safety_with_items,
    get_vouchers_tools_with_items_date,
    get_vouchers_vehicle_with_items,
    update_history_voucher,
    update_state_safety_voucher,
    update_state_tools_voucher,
    update_voucher_general_contract,
    update_voucher_general_from_delete,
    update_voucher_item,
    update_voucher_safety,
    update_voucher_tools,
    update_voucher_vehicle,
    update_voucher_vehicle_status,
)
from templates.forms.VehicleChecklistPDF import (
    FileVehicleChecklistPDF,
    FileVehicleChecklistPhotosPDF,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.resources.methods.Functions_Aux_Vouchers import attach_voucher_file, load_voucher
from templates.misc.Functions_Files import write_log_file

__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"


def create_voucher_tools_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"], data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el voucher general", "error": error}, 400
    flag, error, v_tools_id = create_voucher_tools(
        lastrowid,
        data["position"],
        data["type_transaction"],
        data["superior"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo crear el voucher de herramientas",
            "error": error,
        }, 400
    history = [
        {
            "id_voucher": v_tools_id,
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher creado",
        }
    ]
    flag, error, rows_updated = update_history_voucher(history, lastrowid, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, p_id = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            data_token,
            item["observations"],
        )
        if not flag:
            errors.append({"id_inventory": item["id_inventory"], "error": error})
    if data["items"] and len(errors) == len(data["items"]):
        delete_items_voucher(lastrowid, data_token)
        delete_voucher_tools(lastrowid, data_token)
        update_voucher_general_from_delete(lastrowid, [], data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún item del voucher; operación revertida",
            "error": errors,
        }, 400
    msg_out = f"Voucher de herramientas creado correctamente (ID {lastrowid})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron crear."
    return {
        "data": {"id_voucher": lastrowid},
        "msg": msg_out,
        "error": errors if errors else None,
    }, 201


def update_voucher_tools_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher_general"],
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher tools actualizado",
        }
    )
    flag, error, rows_updated = update_voucher_tools(
        data["id_voucher_general"],
        data["position"],
        data["type_transaction"],
        data["superior"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
        data["user_state"],
        data["superior_state"],
        data["storage_state"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher de herramientas",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, result = delete_voucher_item(item["id_item"], data_token)
        elif item["id_item"] > 0:
            flag, error, result = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        else:
            flag, error, result = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        if not flag:
            errors.append({"id_item": item["id_item"], "error": error})
    id_ = data["id_voucher_general"]
    msg_out = f"Voucher de herramientas actualizado correctamente (ID {id_})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron procesar."
    return {"data": {"id_voucher": id_}, "msg": msg_out, "error": errors if errors else None}, 200


def delete_voucher_tools_api(data, data_token):
    flag, error, rows_updated = delete_items_voucher(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron eliminar los items del voucher",
            "error": error,
        }, 400
    flag, error, rows_updated = delete_voucher_tools(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo eliminar el voucher de herramientas",
            "error": error,
        }, 400
    # Append en BD (el `history` del body se ignora: reescribirlo pisaba entradas
    # agregadas entretanto, p. ej. un anexo).
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, result = append_history_voucher(
        data["id"],
        {
            "id_voucher": data["id"],
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher eliminado",
        },
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher general",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id"]},
        "msg": f"Voucher de herramientas eliminado correctamente (ID {data['id']})",
        "error": None,
    }, 200


def create_voucher_safety_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, lastrowid = create_voucher_general(
        data["type"], timestamp, data_token.get("emp_id"), data["contract"], data_token
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el voucher general", "error": error}, 400
    flag, error, lastrowid_safety = create_voucher_safety(
        lastrowid,
        data["motive"],
        data["epp_emp"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo crear el voucher de seguridad",
            "error": error,
        }, 400
    history = [
        {
            "id_voucher": lastrowid_safety,
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher creado",
        }
    ]
    flag, error, rows_updated = update_history_voucher(history, lastrowid, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        flag, error, lastrowid_item = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            data_token,
            item["observations"],
        )
        if not flag:
            errors.append({"id_item": lastrowid_item, "error": error})
    if data["items"] and len(errors) == len(data["items"]):
        delete_items_voucher(lastrowid, data_token)
        delete_voucher_tools(lastrowid, data_token)
        update_voucher_general_from_delete(lastrowid, [], data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún item del voucher; operación revertida",
            "error": errors,
        }, 400
    msg_out = f"Voucher de seguridad creado correctamente (ID {lastrowid})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron crear."
    return {
        "data": {"id_voucher": lastrowid},
        "msg": msg_out,
        "error": errors if errors else None,
    }, 201


def update_voucher_safety_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher_general"],
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher safety actualizado",
        }
    )
    flag, error, rows_changed = update_voucher_safety(
        data["id_voucher_general"],
        data["epp_emp"],
        data["storage_emp"],
        data["designated_emp"],
        data_token,
        data["epp_state"],
        data["storage_state"],
        data["motive"],
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher de seguridad",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, lastrowid = delete_voucher_item(item["id_item"], data_token)
        elif item["id_item"] > 0:
            flag, error, lastrowid = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        else:
            flag, error, lastrowid = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        if not flag:
            errors.append({"id_inventory": item["id_inventory"], "error": error})
    id_ = data["id_voucher_general"]
    msg_out = f"Voucher de seguridad actualizado correctamente (ID {id_})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron procesar."
    return {"data": {"id_voucher": id_}, "msg": msg_out, "error": errors if errors else None}, 200


def delete_voucher_safety_api(data, data_token):
    flag, error, rows_updated = delete_items_voucher(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron eliminar los items del voucher",
            "error": error,
        }, 400
    # Antes borraba voucher_tools (tabla equivocada): la fila de voucher_safety quedaba.
    flag, error, rows_updated = delete_voucher_safety(data["id"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo eliminar el voucher de seguridad",
            "error": error,
        }, 400
    # Append en BD (el `history` del body se ignora: reescribirlo pisaba entradas
    # agregadas entretanto, p. ej. un anexo).
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    flag, error, result = append_history_voucher(
        data["id"],
        {
            "id_voucher": data["id"],
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher eliminado",
        },
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher general",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id"]},
        "msg": f"Voucher de seguridad eliminado correctamente (ID {data['id']})",
        "error": None,
    }, 200


def get_vouchers_tools_api(data, data_token):
    flag, error, result = get_vouchers_tools_with_items_date(
        data["date"], data_token, data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron obtener los vouchers de herramientas",
            "error": error,
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener vouchers: resultado inesperado",
            "error": str(result),
        }, 400
    data_out = []
    for item in result:
        data_out.append(
            {
                "id_voucher_general": item[0],
                "type": item[1],
                "date": item[2].strftime(format_timestamps)
                if not isinstance(item[2], str)
                else item[2],
                "contract": item[3],
                "position": item[4],
                "type_transaction": item[5],
                "user": item[6],
                "superior": item[7],
                "storage_emp": item[8],
                "designated_emp": item[9],
                "user_state": item[10],
                "superior_state": item[11],
                "storage_state": item[12],
                "extra_info": json.loads(item[13]),
                "items": json.loads(item[14]),
                "history": json.loads(item[15]),
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def get_vouchers_safety_api(data, data_token):
    flag, error, result = get_vouchers_safety_with_items(
        data["date"], data_token=data_token, user=data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron obtener los vouchers de seguridad",
            "error": error,
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener vouchers: resultado inesperado",
            "error": str(result),
        }, 400
    data_out = []
    for item in result:
        data_out.append(
            {
                "id_voucher_general": item[0],
                "type": item[1],
                "date": item[2].strftime(format_timestamps)
                if not isinstance(item[2], str)
                else item[2],
                "contract": item[3],
                "motive": item[4],
                "user": item[5],
                "epp_emp": item[6],
                "storage_emp": item[7],
                "designated_emp": item[8],
                "user_state": item[9],
                "epp_state": item[10],
                "storage_state": item[11],
                "extra_info": json.loads(item[12]),
                "items": json.loads(item[13]),
                "history": json.loads(item[14]),
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def update_status_tools(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher"],
            "type": 0,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher tools actualizado de estados: "
            f"{data['user_state']}-{data['superior_state']}-{data['storage_state']}",
        }
    )
    flag, error, rows_updated = update_state_tools_voucher(
        data["id_voucher"],
        data["user_state"],
        data["superior_state"],
        data["storage_state"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el estado del voucher de herramientas",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(history, data["id_voucher"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id_voucher"]},
        "msg": f"Estado del voucher de herramientas actualizado correctamente (ID {data['id_voucher']})",
        "error": None,
    }, 200


def update_status_safety(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher"],
            "type": 1,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher safety actualizado de estados: "
            f"{data['user_state']}-{data['epp_state']}-{data['storage_state']}",
        }
    )
    flag, error, rows_updated = update_state_safety_voucher(
        data["id_voucher"],
        data["user_state"],
        data["epp_state"],
        data["storage_state"],
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el estado del voucher de seguridad",
            "error": error,
        }, 400
    flag, error, rows_updated = update_history_voucher(history, data["id_voucher"], data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400
    return {
        "data": {"id_voucher": data["id_voucher"]},
        "msg": f"Estado del voucher de seguridad actualizado correctamente (ID {data['id_voucher']})",
        "error": None,
    }, 200


def get_vouchers_vehicle_api(data, data_token):
    flag, error, result = get_vouchers_vehicle_with_items(
        data["date"], data_token, data_token.get("emp_id")
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudieron obtener los vouchers vehiculares",
            "error": error,
        }, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {
            "data": None,
            "msg": "Error al obtener vouchers vehiculares: resultado inesperado",
            "error": str(result),
        }, 400
    data_out = []
    for item in result:
        extra_info = json.loads(item[20])
        # Tolera las filas viejas doble-codificadas (string con JSON adentro).
        accesories = _chv_json_field(item[15], [])
        data_out.append(
            {
                "id_voucher_general": item[0],
                "type": item[1],
                "date": item[2].strftime(format_timestamps)
                if not isinstance(item[2], str)
                else item[2],
                "contract": item[3],
                "realizado_por": item[4],
                "received_by": item[5],
                "brand": item[6],
                "model": item[7],
                "color": item[8],
                "year": item[9],
                "placas": item[10],
                "kilometraje": item[11],
                "registration_card": item[12],
                "insurance": item[13],
                "referendo": item[14],
                "accessories": accesories,
                "vehicle_type": item[16],
                "observations": item[17],
                "items": json.loads(item[18]),
                "history": json.loads(item[19]),
                "files": extra_info.get("files"),
                "status": item[21],
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def _vehicle_contract_or_none(value):
    """contracts.id del checklist vehicular, o None = sin contrato.

    null, omitido, 0 y negativos -> None: la FK de vouchers_general.contract
    solo acepta ids reales o NULL.
    """
    try:
        contract = int(value)
    except (TypeError, ValueError):
        return None
    return contract if contract > 0 else None


def _rollback_vehicle_voucher_create(id_voucher, data_token, vehicle_row=True):
    """Deshace un alta de checklist vehicular a medias: items, fila de
    voucher_vehicle (si llego a crearse) y la fila de vouchers_general, que sin
    hijo queda huerfana e invisible para los GET. Best-effort: lo que falle se
    anota en el log y el 400 del alta se responde igual."""
    steps = [("items", lambda: delete_items_voucher(id_voucher, data_token))]
    if vehicle_row:
        steps.append(("voucher_vehicle", lambda: delete_voucher_vehicle(id_voucher, data_token)))
    steps.append(("vouchers_general", lambda: delete_voucher_general(id_voucher, data_token)))
    for name, step in steps:
        flag, error, _ = step()
        if not flag:
            write_log_file(
                log_file_sgi_chv,
                f"Rollback del alta del voucher vehicular {id_voucher}: no se pudo borrar {name} ({error})",
                data_token,
            )
            return False
    return True


def create_voucher_vehicle_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    flag, error, lastrowid = create_voucher_general(
        data["type"],
        timestamp,
        data_token.get("emp_id"),
        _vehicle_contract_or_none(data.get("contract")),
        data_token,
    )
    if not flag:
        return {"data": None, "msg": "No se pudo crear el voucher general", "error": error}, 400
    # Lista tal cual: el controller hace el unico json.dumps. Antes se codificaba
    # aqui tambien y la columna JSON guardaba un string con JSON adentro.
    accessories = data["accessories"] or []

    flag, error, lastrowid_vehicle = create_voucher_vehicle(
        lastrowid,
        data["brand"],
        data["model"],
        data_token,
        data.get("color"),
        data.get("year"),
        data["placas"],
        data.get("kilometraje", 0),
        int(data["registration_card"]),
        int(data["insurance"]),
        int(data["referendo"]),
        accessories,
        data["type"],
        data["received_by"],
        data.get("observations"),
    )
    if not flag:
        # Rollback: sin la fila de voucher_vehicle, el vouchers_general recien
        # creado seria un huerfano invisible para todos los GET (JOIN).
        _rollback_vehicle_voucher_create(lastrowid, data_token, vehicle_row=False)
        return {
            "data": None,
            "msg": "No se pudo crear el voucher vehicular; operación revertida",
            "error": error,
        }, 400

    history = [
        {
            "id_voucher": lastrowid_vehicle,
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher creado",
        }
    ]
    flag, error, rows_updated = update_history_voucher(history, lastrowid, data_token)
    if not flag:
        _rollback_vehicle_voucher_create(lastrowid, data_token)
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher; operación revertida",
            "error": error,
        }, 400

    errors = []
    for item in data["items"]:
        flag, error, lastrowid_item = create_voucher_item(
            lastrowid,
            item["id_inventory"],
            item["quantity"],
            item["unit"],
            item["description"],
            data_token,
            item.get("observations"),
        )
        if not flag:
            errors.append({"id_item": lastrowid_item, "error": error})

    if data["items"] and len(errors) == len(data["items"]):
        _rollback_vehicle_voucher_create(lastrowid, data_token)
        return {
            "data": None,
            "msg": "No se pudo crear ningún item del voucher vehicular; operación revertida",
            "error": errors,
        }, 400

    msg_out = f"Voucher vehicular creado correctamente (ID {lastrowid})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron crear."
    return {
        "data": {"id_voucher": lastrowid},
        "msg": msg_out,
        "error": errors if errors else None,
    }, 201


def update_voucher_vehicle_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    history = data["history"]
    history.append(
        {
            "id_voucher": data["id_voucher_general"],
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher vehicular actualizado",
        }
    )
    # Lista tal cual: el controller hace el unico json.dumps. Antes se codificaba
    # aqui tambien y la columna JSON guardaba un string con JSON adentro.
    accessories = data["accessories"] or []
    # Antes que el resto: si la FK rechaza el contrato, no queda nada a medias.
    flag, error, rows_changed = update_voucher_general_contract(
        data["id_voucher_general"], _vehicle_contract_or_none(data.get("contract")), data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el contrato del voucher vehicular",
            "error": error,
        }, 400
    flag, error, rows_changed = update_voucher_vehicle(
        data["id_voucher_general"],
        data["brand"],
        data["model"],
        data_token,
        data.get("color"),
        data.get("year"),
        data["placas"],
        data.get("kilometraje", 0),
        int(data["registration_card"]),
        int(data["insurance"]),
        int(data["referendo"]),
        accessories,
        data["type"],
        data["received_by"],
        data.get("observations"),
        data.get("status"),
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher vehicular",
            "error": error,
        }, 400

    flag, error, rows_updated = update_history_voucher(
        history, data["id_voucher_general"], data_token
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el historial del voucher",
            "error": error,
        }, 400

    errors = []
    for item in data["items"]:
        if item["is_erased"] == 1:
            flag, error, lastrowid = delete_voucher_item(item["id_item"], data_token)
        elif item["id_item"] > 0:
            flag, error, lastrowid = update_voucher_item(
                item["id_item"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        else:
            flag, error, lastrowid = create_voucher_item(
                data["id_voucher_general"],
                item["id_inventory"],
                item["quantity"],
                item["unit"],
                item["description"],
                data_token,
                item["observations"],
            )
        if not flag:
            errors.append({"id_inventory": item["id_inventory"], "error": error})

    id_ = data["id_voucher_general"]
    msg_out = f"Voucher vehicular actualizado correctamente (ID {id_})"
    if errors:
        msg_out += f". {len(errors)} items no se pudieron procesar."
    return {"data": {"id_voucher": id_}, "msg": msg_out, "error": errors if errors else None}, 200


def delete_voucher_vehicle_api(data, data_token):
    # Sin ventana de fecha: un checklist de mas de un año tambien se puede
    # eliminar/cancelar (antes get_vouchers_vehicle_with_items con 365 dias).
    payload_error, code, head = load_voucher("vehicle", data["id"], data_token)
    if payload_error is not None:
        return payload_error, code
    status = head["status"]  # pyrefly: ignore
    if status == 0:
        # Todos los items del voucher (antes delete_voucher_item borraba por
        # id_item con el id del voucher: los items quedaban huerfanos).
        flag, error, result = delete_items_voucher(data["id"], data_token)
        if not flag:
            return {
                "data": None,
                "msg": "No se pudo eliminar el voucher vehicular",
                "error": error,
            }, 400
        flag, error, result = delete_voucher_vehicle(data["id"], data_token)
        if not flag:
            return {
                "data": None,
                "msg": "No se pudo eliminar el voucher vehicular",
                "error": error,
            }, 400
    else:
        flag, error, result = update_voucher_vehicle_status(3, data["id"], data_token)
        if not flag:
            return {
                "data": None,
                "msg": "No se pudo cancelar el voucher vehicular",
                "error": error,
            }, 400

    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)

    # Append en BD: no se lee ni se reescribe el history (sin carrera con una
    # subida de anexo simultanea).
    flag, error, rows_changed = append_history_voucher(
        data["id"],
        {
            "id_voucher": data["id"],
            "type": 2,
            "timestamp": timestamp,
            "user": data_token.get("emp_id"),
            "comment": "Voucher vehicular eliminado"
            if status == 0
            else "Voucher vehicular cancelado",
        },
        data_token,
    )
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo actualizar el voucher vehicular",
            "error": error,
        }, 400
    accion = "eliminado" if status == 0 else "cancelado"
    msg = (
        f"Voucher vehicular {accion} correctamente (ID {data['id']}) "
        f"por el empleado {data_token.get('name')}"
    )
    create_notification_permission_notGUI(
        msg,
        data_token,
        ["administracion", "operaciones", "sgi"],
        data_token.get("emp_id"),
        0,
    )
    write_log_file(log_file_sgi_chv, msg, data_token)
    return {
        "data": {"id_voucher": data["id"]},
        "msg": f"Voucher vehicular {accion} correctamente (ID {data['id']})",
        "error": None,
    }, 200


def create_voucher_vehicle_attachment_api(data, data_token):
    """{"filepath": filepath_download, "filename": filename, "id_voucher": id}, data_token.
    Receta compartida de los 3 tipos de vale (Functions_Aux_Vouchers, P-103)."""
    return attach_voucher_file("vehicle", data, data_token)


def download_voucher_vehicle_attachment_api(data, data_token):
    # Sin ventana de fecha (antes solo encontraba vouchers de los ultimos 365 dias).
    payload_error, code, head = load_voucher("vehicle", data.get("id_voucher"), data_token)
    if payload_error is not None:
        return payload_error, code
    files = head["files"]  # pyrefly: ignore
    name_file = data["filename"]
    flag_found = False
    path_aws = ""
    for file in files:
        if file["filename"] == name_file:
            flag_found = True
            path_aws = file["path"]
            break
    if not flag_found:
        return {"data": None, "msg": "Archivo no encontrado en el voucher", "error": None}, 400
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_CH_BUCKET")
    try:
        s3_client.download_file(Bucket=str(bucket_name), Key=path_aws, Filename=data["filepath"])
    except FileNotFoundError:
        return {"data": None, "msg": "Archivo local no encontrado", "error": None}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "Credenciales AWS no encontradas", "error": None}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket no existe: {bucket_name}", "error": str(e)}, 400
        elif error_code == "AccessDenied":
            return {
                "data": None,
                "msg": f"Acceso denegado al bucket: {bucket_name}",
                "error": str(e),
            }, 400
        elif error_code == "NoSuchKey":
            return {
                "data": None,
                "msg": f"Archivo no encontrado en S3: {path_aws}",
                "error": str(e),
            }, 400
        else:
            return {
                "data": None,
                "msg": f"Error al descargar archivo: {str(e)}",
                "error": str(e),
            }, 400
    return {"path": data["filepath"]}, 200


def _chv_json_field(value, default):
    """Campo JSON del voucher vehicular. `accessories` de filas anteriores al
    2026-10-09 puede venir doble-codificado (un string JSON que contiene otro
    JSON; el alta lo codificaba dos veces) y `extra_info` simple: decodifica
    hasta dos veces y valida el tipo final."""
    result = value
    for _ in range(2):
        if not isinstance(result, str):
            break
        try:
            result = json.loads(result)
        except (ValueError, TypeError):
            return default
    return result if isinstance(result, type(default)) else default


def _chv_downscale_signature_image(local_path, max_width=600):
    """Reduce la resolución de una firma grande para no engordar el PDF.
    Devuelve la misma ruta (reescrita in-place o intacta); no fatal."""
    try:
        from PIL import Image

        with Image.open(local_path) as img:
            if img.width <= max_width:
                return local_path
            ratio = max_width / float(img.width)
            new_size = (max_width, max(1, int(img.height * ratio)))
            img.resize(new_size, Image.Resampling.LANCZOS).save(local_path)
        return local_path
    except Exception as e:
        print("erro downscale chv signature", str(e))
        return local_path


def _chv_signature_from_files(files, marker, tmp_dir, data_token):
    """
    Busca en los attachments del voucher (``extra_info["files"]``) el último
    cuyo nombre contiene ``marker`` (``firma-aprobado`` / ``firma-recibido``,
    el mismo criterio con el que el alta mueve el status) y lo descarga de S3
    para incrustarlo en el PDF. No fatal: sin match, attachment no dibujable
    (pdf/zip) o falla de S3 -> None (el recuadro queda para firma a mano).
    """
    drawable = {"jpg", "jpeg", "png", "webp"}
    chosen = None
    for file in files:
        if not isinstance(file, dict):
            continue
        filename = str(file.get("filename") or "")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if marker in filename.lower() and ext in drawable and file.get("path"):
            chosen = file  # el último gana: una re-subida corrige la firma
    if chosen is None:
        return None
    try:
        s3_client = boto3.client("s3")
        local_path = os.path.join(
            tmp_dir, f"{marker}_{os.path.basename(chosen['path'])}"
        )
        s3_client.download_file(
            Bucket=str(secrets.get("S3_CH_BUCKET")),
            Key=chosen["path"],
            Filename=local_path,
        )
        return _chv_downscale_signature_image(local_path)
    except Exception as e:
        write_log_file(
            log_file_sgi_chv,
            f"No se pudo cargar la firma '{marker}' para el PDF del checklist: {str(e)}",
            data_token,
        )
        return None


_CHV_DRAWABLE_EXT = {"jpg", "jpeg", "png", "webp"}


def _chv_build_attachments(files, tmp_dir, data_token):
    """
    Baja de S3 los anexos del checklist para la variante combinada (?full=1).
    Los attachments vehiculares solo traen ``{filename, path}`` (sin categoria),
    asi que se clasifican por nombre/extension:

    - nombre con ``firma`` -> se omite (ya va incrustada en la pagina 1)
    - ``pdf`` -> anexo (se concatena tal cual)
    - ``jpg/jpeg/png/webp`` -> foto (hoja de EVIDENCIA FOTOGRAFICA)
    - otra cosa (zip, ...) -> se omite

    No fatal por archivo: una descarga fallida se omite + log.
    :return: ``(anexos, photos)``, listas de ``{"path", "filename"}`` en orden de subida.
    """
    anexos, photos = [], []
    s3_client = None
    for idx, file in enumerate(files, start=1):
        if not isinstance(file, dict) or not file.get("path"):
            continue
        filename = str(file.get("filename") or "")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if "firma" in filename.lower():
            continue
        if ext == "pdf":
            target = anexos
        elif ext in _CHV_DRAWABLE_EXT:
            target = photos
        else:
            continue
        local_path = os.path.join(tmp_dir, f"att_{idx}_{os.path.basename(file['path'])}")
        try:
            if s3_client is None:
                s3_client = boto3.client("s3")
            s3_client.download_file(
                Bucket=str(secrets.get("S3_CH_BUCKET")), Key=file["path"], Filename=local_path
            )
        except Exception as e:
            write_log_file(
                log_file_sgi_chv,
                f"No se pudo descargar el anexo '{filename}' del checklist: {str(e)}",
                data_token,
            )
            continue
        target.append({"path": local_path, "filename": filename})
    return anexos, photos


def _chv_pdf_pages(path) -> int:
    """Paginas de un PDF local (0 si no abre: la fusion tambien lo omitira)."""
    import fitz

    try:
        with fitz.open(path) as doc:
            return doc.page_count
    except Exception:
        return 0


def _chv_assemble_full_pdf(checklist_path, anexos, photos_pdf_path, out_path, data_token):
    """
    Fusiona (PyMuPDF/fitz) la pagina del checklist + los anexos PDF tal cual +
    la(s) hoja(s) de fotos. Mismo criterio que ``_assemble_remission_full_pdf``
    (MD_Admin_Collections): no fatal por anexo, y si la fusion falla completa
    devuelve el checklist solo (mejor un documento parcial que ninguno).
    """
    import fitz

    try:
        doc = fitz.open()
        with fitz.open(checklist_path) as base:
            doc.insert_pdf(base)
        for anexo in anexos:
            try:
                with fitz.open(anexo["path"]) as adoc:
                    doc.insert_pdf(adoc)
            except Exception as e:
                write_log_file(
                    log_file_sgi_chv,
                    f"No se pudo insertar el anexo '{anexo.get('filename')}' al checklist combinado: {str(e)}",
                    data_token,
                )
        if photos_pdf_path:
            with fitz.open(photos_pdf_path) as pdoc:
                doc.insert_pdf(pdoc)
        doc.save(out_path)
        doc.close()
        return out_path
    except Exception as e:
        write_log_file(
            log_file_sgi_chv,
            f"Error al fusionar el checklist combinado: {str(e)}",
            data_token,
        )
        return checklist_path


def download_voucher_vehicle_pdf_api(id_voucher, data_token, full: bool = False):
    """
    Genera el PDF del CHECK LIST VEHICULAR (FO-CDA-03 R3) de un voucher
    vehicular y devuelve la ruta local para `send_file`. Sin ventana de fecha:
    cualquier voucher existente es descargable. Las firmas se incrustan desde
    S3 cuando existen (no fatal si faltan o fallan). Con ``full=True`` agrega
    los anexos PDF y la hoja de EVIDENCIA FOTOGRAFICA
    (docs/checklist_vehicular_full_pdf.md).
    """
    flag, error, result = get_voucher_vehicle_by_id(id_voucher, data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo obtener el checklist vehicular",
            "error": error,
        }, 400
    if not isinstance(result, tuple) or len(result) == 0:
        return {
            "data": None,
            "msg": f"Checklist vehicular no encontrado (ID {id_voucher})",
            "error": None,
        }, 404

    def si_no(value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return None
        return value if value in (0, 1) else None

    date_voucher = result[1]
    fecha = (
        date_voucher.strftime("%d/%m/%Y")
        if hasattr(date_voucher, "strftime")
        else str(date_voucher or "")
    )
    accessories = _chv_json_field(result[14], [])
    extra_info = _chv_json_field(result[17], {})
    files = extra_info.get("files", []) if isinstance(extra_info, dict) else []
    if not isinstance(files, list):
        files = []
    try:
        vehicle_type = int(result[15])
    except (TypeError, ValueError):
        vehicle_type = None
    tmp_dir = tempfile.mkdtemp()
    dict_data = {
        "filename_out": os.path.join(tmp_dir, f"checklist_vehicular_{id_voucher}.pdf"),
        "id_voucher": id_voucher,
        "fecha_elaboracion": fecha,
        "marca": result[5],
        "modelo": result[6],
        "color": result[7],
        "anio": result[8],
        "placas": result[9],
        "kilometraje": result[10],
        "tarjeta_circulacion": si_no(result[11]),
        "poliza_seguro": si_no(result[12]),
        "comprobante_refrendo": si_no(result[13]),
        "accessories": accessories,
        "vehicle_type": vehicle_type,
        "observations": result[16],
        "realizado": {
            "name": result[19] or "",
            "signature_path": _chv_signature_from_files(
                files, "firma-aprobado", tmp_dir, data_token
            ),
        },
        "recibido": {
            "name": result[20] or "",
            "signature_path": _chv_signature_from_files(
                files, "firma-recibido", tmp_dir, data_token
            ),
        },
    }
    try:
        FileVehicleChecklistPDF(dict_data)
    except Exception as e:
        write_log_file(
            log_file_sgi_chv,
            f"Error al generar el PDF del checklist vehicular {id_voucher}: {str(e)}",
            data_token,
        )
        return {
            "data": None,
            "msg": "Error al generar el PDF del checklist vehicular",
            "error": str(e),
        }, 500
    out_path = dict_data["filename_out"]
    detail = ""
    if full:
        anexos, photos = _chv_build_attachments(files, tmp_dir, data_token)
        photos_pdf_path = None
        if photos:
            photos_pdf_path = os.path.join(tmp_dir, f"checklist_vehicular_{id_voucher}_fotos.pdf")
            try:
                # La hoja de fotos numera sus paginas a continuacion del checklist y los anexos.
                page_start = 1 + _chv_pdf_pages(out_path) + sum(_chv_pdf_pages(a["path"]) for a in anexos)
                FileVehicleChecklistPhotosPDF(
                    {**dict_data, "filename_out": photos_pdf_path, "photos": photos, "page_start": page_start}
                )
            except Exception as e:
                write_log_file(
                    log_file_sgi_chv,
                    f"No se pudo generar la hoja de fotos del checklist {id_voucher}: {str(e)}",
                    data_token,
                )
                photos_pdf_path = None
        out_path = _chv_assemble_full_pdf(
            out_path,
            anexos,
            photos_pdf_path,
            os.path.join(tmp_dir, f"checklist_vehicular_{id_voucher}_completo.pdf"),
            data_token,
        )
        detail = f" (combinado: {len(anexos)} anexo(s), {len(photos)} foto(s))"
    write_log_file(
        log_file_sgi_chv,
        f"PDF del checklist vehicular {id_voucher}{detail} generado por el empleado {data_token.get('name')}",
        data_token,
    )
    return out_path, 200
