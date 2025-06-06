# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 04/jun/2025  at 15:17 $"

import json

from templates.database.connection import execute_sql


def create_voucher_general(voucher_type, date, user, contract):
    """
    Crea un nuevo registro en la tabla vouchers_general.

    :param voucher_type: Tipo de vale (0: 'Tools', 1: 'Safety')
    :param date: Fecha del vale (YYYY-MM-DD)
    :param user: ID del usuario que solicita el vale
    :param contract: ID del contrato relacionado
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "INSERT INTO sql_telintec_mod_admin.vouchers_general "
        "(type, date, user, contract) "
        "VALUES (%s, %s, %s, %s)"
    )
    val = (voucher_type, date, user, contract)
    flag, error, lastrowid = execute_sql(sql, val, 4)  # Ejecuta la inserción
    return flag, error, lastrowid


def create_voucher_tools(
    id_voucher_general,
    position,
    type_transaction,
    superior,
    storage_emp,
    user_state=0,
    superior_state=0,
    extra_info=None,
):
    """
    Crea un nuevo registro en la tabla voucher_tools.

    :param id_voucher_general: ID del voucher general creado previamente.
    :param position: Puesto del usuario que solicita el vale
    :param type_transaction: Tipo de transacción (0=default)
    :param superior: ID del superior responsable
    :param storage_emp: ID del empleado encargado del almacenamiento
    :param user_state: Estado del usuario (default=0)
    :param superior_state: Estado del superior (default=0)
    :param extra_info: Información extra en formato JSON
    :return: Estado de la operación (éxito/error)
    """
    if extra_info is None:
        extra_info = {}
    sql = (
        "INSERT INTO sql_telintec_mod_admin.voucher_tools "
        "(id_voucher_general, position, type_transaction, superior, "
        "storage_emp, user_state, superior_state, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        id_voucher_general,
        position,
        type_transaction,
        superior,
        storage_emp,
        user_state,
        superior_state,
        json.dumps(extra_info),
    )
    flag, error, lastrowid = execute_sql(sql, val, 4)
    return flag, error, lastrowid


def update_voucher_tools(
    id_voucher_general,
    position,
    type_transaction,
    superior,
    storage_emp,
    user_state=0,
    superior_state=0,
    extra_info=None,
):
    """
    Actualiza un registro existente en la tabla voucher_tools.

    :param id_voucher_general: ID del voucher general.
    :param position: Puesto del usuario que solicita el vale.
    :param type_transaction: Tipo de transacción.
    :param superior: ID del superior responsable.
    :param storage_emp: ID del empleado encargado del almacenamiento.
    :param user_state: Estado del usuario (default=0).
    :param superior_state: Estado del superior (default=0).
    :param extra_info: Información extra en formato JSON.
    :return: Estado de la operación (éxito/error).
    """
    if extra_info is None:
        extra_info = {}
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_tools "
        "SET position = %s, type_transaction = %s, superior = %s, "
        "storage_emp = %s, user_state = %s, superior_state = %s, extra_info = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (
        position,
        type_transaction,
        superior,
        storage_emp,
        user_state,
        superior_state,
        json.dumps(extra_info),
        id_voucher_general,
    )
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


def create_voucher_safety(
    id_voucher_general,
    superior,
    epp_emp,
    epp_state=0,
    superior_state=0,
    motive=0,
    extra_info=None,
):
    """
    Crea un nuevo registro en la tabla voucher_safety.

    :param id_voucher_general: ID del voucher general creado previamente.
    :param superior: ID del superior responsable
    :param epp_emp: ID del empleado que recibe los elementos de seguridad
    :param epp_state: Estado del EPP (default=0)
    :param superior_state: Estado del superior (default=0)
    :param motive: Motivo del vale (default=0)
    :param extra_info: Información extra en formato JSON
    :return: Estado de la operación (éxito/error)
    """
    if extra_info is None:
        extra_info = {}
    sql = (
        "INSERT INTO sql_telintec_mod_admin.voucher_safety "
        "(id_voucher_general, superior, epp_emp, epp_state, superior_state, motive, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        id_voucher_general,
        superior,
        epp_emp,
        epp_state,
        superior_state,
        motive,
        json.dumps(extra_info),
    )
    flag, error, lastrowid = execute_sql(sql, val, 4)
    return flag, error, lastrowid


def update_voucher_safety(
    id_voucher_general,
    superior,
    epp_emp,
    epp_state=0,
    superior_state=0,
    motive=None,
    extra_info=None,
):
    """
    Actualiza un registro existente en la tabla voucher_safety.

    :param id_voucher_general: ID del voucher general.
    :param superior: ID del superior responsable.
    :param epp_emp: ID del EPP asignado al empleado.
    :param epp_state: Estado del EPP (default=0).
    :param superior_state: Estado del superior (default=0).
    :param motive: Motivo de la solicitud.
    :param extra_info: Información extra en formato JSON.
    :return: Estado de la operación (éxito/error).
    """
    if motive is None:
        motive = ""
    if extra_info is None:
        extra_info = {}
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_safety "
        "SET superior = %s, epp_emp = %s, epp_state = %s, "
        "superior_state = %s, motive = %s, extra_info = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (
        superior,
        epp_emp,
        epp_state,
        superior_state,
        motive,
        json.dumps(extra_info),
        id_voucher_general,
    )
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


def create_voucher_item(
    id_voucher,
    id_inventory,
    quantity,
    unit,
    description,
    observations=None,
    extra_info=None,
):
    """
    Crea un nuevo ítem asociado a un voucher en la tabla voucher_items.

    :param id_voucher: ID del voucher al que pertenece el ítem
    :param id_inventory: ID del inventario del item
    :param quantity: Cantidad del ítem
    :param unit: Unidad de medida del ítem
    :param description: Descripción del ítem
    :param observations: Observaciones opcionales sobre el ítem
    :param extra_info: Información extra en formato JSON
    :return: Estado de la operación (éxito/error)
    """
    if observations is None:
        observations = ""
    if extra_info is None:
        extra_info = {"id_inventory": id_inventory}
    else:
        extra_info["id_inventory"] = id_inventory
    sql = (
        "INSERT INTO sql_telintec_mod_admin.voucher_items "
        "(id_voucher, quantity, unit, description, observations, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    val = (
        id_voucher,
        quantity,
        unit,
        description,
        observations,
        json.dumps(extra_info),
    )
    flag, error, lastrowid = execute_sql(sql, val, 4)
    return flag, error, lastrowid


def update_voucher_item(
    id_item,
    id_inventory,
    quantity,
    unit,
    description,
    observations=None,
    extra_info=None,
):
    """
    Actualiza un ítem específico en la tabla voucher_items.

    :param id_item: ID del ítem a actualizar
    :param id_inventory: Id in the inventory
    :param quantity: Nueva cantidad del ítem
    :param unit: Nueva unidad de medida del ítem
    :param description: Nueva descripción del ítem
    :param observations: Nuevas observaciones del ítem
    :param extra_info: Nueva información extra en formato JSON
    :return: Estado de la operación (éxito/error)
    """
    if observations is None:
        observations = ""
    if extra_info is None:
        extra_info = {"id_inventory": id_inventory}
    else:
        extra_info["id_inventory"] = id_inventory
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_items "
        "SET quantity = %s, unit = %s, description = %s, observations = %s, extra_info = %s "
        "WHERE id_item = %s"
    )
    val = (
        quantity,
        unit,
        description,
        observations,
        json.dumps(extra_info),
        id_item,
    )
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


def get_vouchers_tools_with_items_date(start_date):
    """
    Obtiene vouchers de herramientas desde una fecha específica, incluyendo su metadata e ítems relacionados.

    :param start_date: Fecha de inicio (YYYY-MM-DD)
    :return: Lista de vouchers de herramientas con sus ítems agregados como JSON o mensaje de error
    """
    sql = (
        "SELECT "
        "vt.id_voucher_general, "
        "vg.type, "
        "vg.date, "
        "vg.user, "
        "vg.contract, "
        "vt.position, "
        "vt.type_transaction, "
        "vt.superior, "
        "vt.storage_emp, "
        "vt.user_state, "
        "vt.superior_state, "
        "vt.extra_info, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        "'id_item', vi.id_item, "
        "'quantity', vi.quantity, "
        "'unit', vi.unit, "
        "'description', vi.description, "
        "'observations', vi.observations, "
        "'extra_info', vi.extra_info)"
        ") AS items "
        "FROM sql_telintec_mod_admin.voucher_tools AS vt "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vt.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE vg.date >= %s GROUP BY vt.id_voucher_general"
    )
    val = (start_date,)
    flag, error, vouchers = execute_sql(sql, val, 2)
    return flag, error, vouchers


def get_vouchers_safety_with_items(start_date):
    """
    Obtiene vouchers de seguridad desde una fecha específica, incluyendo su metadata e ítems relacionados.

    :param start_date: Fecha de inicio (YYYY-MM-DD)
    :return: Lista de vouchers de seguridad con sus ítems agregados como JSON o mensaje de error
    """
    sql = (
        "SELECT "
        "vs.id_voucher_general, "
        "vg.type, "
        "vg.date, "
        "vg.user, "
        "vg.contract, "
        "vs.superior, "
        "vs.epp_emp, "
        "vs.epp_state, "
        "vs.superior_state, "
        "vs.motive, "
        "vs.extra_info, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        "'id_item', vi.id_item, "
        "'quantity', vi.quantity, "
        "'unit', vi.unit, "
        "'description', vi.description, "
        "'observations', vi.observations, "
        "'extra_info', vi.extra_info)"
        ") AS items "
        "FROM sql_telintec_mod_admin.voucher_safety AS vs "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vs.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE vg.date >= %s GROUP BY vs.id_voucher_general "
    )
    val = (start_date,)
    flag, error, vouchers = execute_sql(sql, val, 2)
    return flag, error, vouchers
