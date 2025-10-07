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
    desiganted_emp,
    extra_info=None,
):
    """
    Crea un nuevo registro en la tabla voucher_tools.

    :param id_voucher_general: ID del voucher general creado previamente.
    :param position: Puesto del usuario que solicita el vale
    :param type_transaction: Tipo de transacción (0=default)
    :param superior: ID del superior responsable
    :param storage_emp: ID del empleado encargado del almacenamiento
    :param desiganted_emp: ID del empleado designado
    :param extra_info: Información extra en formato JSON
    :return: Estado de la operación (éxito/error)
    """
    if extra_info is None:
        extra_info = {}
    sql = (
        "INSERT INTO sql_telintec_mod_admin.voucher_tools "
        "(id_voucher_general, position, type_transaction, superior, storage_emp, designated_emp, "
        "user_state, superior_state, storage_state, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        id_voucher_general,
        position,
        type_transaction,
        superior,
        storage_emp,
        desiganted_emp,
        1,
        0,
        0,
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
    designated_emp,
    user_state=0,
    superior_state=0,
    storage_state=0,
    extra_info=None,
):
    """
    Actualiza un registro existente en la tabla voucher_tools.

    :param id_voucher_general: ID del voucher general.
    :param position: Puesto del usuario que solicita el vale.
    :param type_transaction: Tipo de transacción.
    :param superior: ID del superior responsable.
    :param storage_emp: ID del empleado encargado del almacenamiento.
    :param designated_emp: ID del empleado designado
    :param user_state: Estado del usuario (default=0).
    :param superior_state: Estado del superior (default=0).
    :param storage_state: Estado del almacenamiento (default=0).
    :param extra_info: Información extra en formato JSON.
    :return: Estado de la operación (éxito/error)
    """
    if extra_info is None:
        extra_info = {}
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_tools "
        "SET position = %s, type_transaction = %s, "
        "superior = %s, storage_emp = %s, designated_emp = %s, "
        "user_state = %s, superior_state = %s, storage_state = %s, extra_info = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (
        position,
        type_transaction,
        superior,
        storage_emp,
        designated_emp,
        user_state,
        superior_state,
        storage_state,
        json.dumps(extra_info),
        id_voucher_general,
    )
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


def create_voucher_safety(
    id_voucher_general,
    motive,
    epp_emp,
    storage_emp,
    designated_emp,
    extra_info=None,
):
    """
    Crea un nuevo registro en la tabla voucher_safety.

    :param id_voucher_general: ID del voucher general creado previamente.
    :param epp_emp: ID del empleado que recibe los elementos de seguridad
    :param storage_emp: ID del empleado de almacen
    :param designated_emp: ID del empleado designado
    :param motive: Motivo del vale (default=0)
    :param extra_info: Información extra en formato JSON
    :return: Estado de la operación (éxito/error)
    """
    if extra_info is None:
        extra_info = {}
    sql = (
        "INSERT INTO sql_telintec_mod_admin.voucher_safety "
        "(id_voucher_general, epp_emp, storage_emp, designated_emp, user_state, epp_state, storage_state, motive, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        id_voucher_general,
        epp_emp,
        storage_emp,
        designated_emp,
        1,
        0,
        0,
        motive,
        json.dumps(extra_info),
    )
    flag, error, lastrowid = execute_sql(sql, val, 4)
    return flag, error, lastrowid


def update_voucher_safety(
    id_voucher_general,
    epp_emp,
    storage_emp,
    designated_emp,
    user_state=1,
    epp_state=0,
    storage_state=0,
    motive=0,
    extra_info=None,
):
    """
    Actualiza un registro existente en la tabla voucher_safety.

    :param id_voucher_general: ID del voucher general.
    :param epp_emp: ID del empleado que recibe los elementos de seguridad.
    :param storage_emp: ID del empleado de almacen.
    :param designated_emp: ID del empleado designado.
    :param user_state: Estado del usuario (default=0).
    :param epp_state: Estado de los elementos de seguridad (default=0).
    :param storage_state: Estado del almacenamiento (default=0).
    :param motive: Motivo del vale (default=0).
    :param extra_info: Información extra en formato JSON.
    :return: Estado de la operación (éxito/error)
    """
    if extra_info is None:
        extra_info = {}
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_safety "
        "SET epp_emp = %s, storage_emp = %s, designated_emp = %s, "
        "user_state = %s, epp_state = %s, storage_state = %s, "
        "motive = %s, extra_info = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (
        epp_emp,
        storage_emp,
        designated_emp,
        user_state,
        epp_state,
        storage_state,
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


def update_history_voucher(history: list, id_voucher):
    """
    Actualiza el historial de un voucher en la tabla vouchers_general.

    :param history: Nuevo historial en formato JSON
    :param id_voucher: ID del voucher a actualizar
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "UPDATE sql_telintec_mod_admin.vouchers_general "
        "SET history = %s "
        "WHERE id_voucher = %s"
    )
    val = (json.dumps(history), id_voucher)
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


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


def delete_voucher_item(id_item: int):
    sql = "DELETE FROM sql_telintec_mod_admin.voucher_items " "WHERE id_item = %s"
    val = (id_item,)
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


def get_vouchers_tools_with_items_date(start_date, user=None):
    """
    Obtiene vouchers de herramientas desde una fecha específica, incluyendo su metadata e ítems relacionados.

    :param start_date: Fecha de inicio (YYYY-MM-DD)
    :param user: user ID that creates the voucher
    :return: Lista de vouchers de herramientas con sus ítems agregados como JSON o mensaje de error
    """
    sql = (
        "SELECT "
        "vt.id_voucher_general, "
        "vg.type, "
        "vg.date, "
        "vg.contract, "
        "vt.position, "
        "vt.type_transaction, "
        "vg.user, "
        "vt.superior, "
        "vt.storage_emp, "
        "vt.designated_emp, "
        "vt.user_state, "
        "vt.superior_state, "
        "vt.storage_state, "
        "vt.extra_info, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        "'id_item', vi.id_item, "
        "'quantity', vi.quantity, "
        "'unit', vi.unit, "
        "'description', vi.description, "
        "'observations', vi.observations, "
        "'extra_info', vi.extra_info)"
        ") AS items, "
        "vg.history "
        "FROM sql_telintec_mod_admin.voucher_tools AS vt "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vt.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE (vg.date >= %s) AND (vg.user = %s OR %s IS NULL) GROUP BY vt.id_voucher_general"
    )
    val = (start_date, user, user)
    flag, error, vouchers = execute_sql(sql, val, 2)
    return flag, error, vouchers


def get_vouchers_safety_with_items(start_date, user=None):
    """
    Obtiene vouchers de seguridad desde una fecha específica, incluyendo su metadata e ítems relacionados.

    :param start_date: Fecha de inicio (YYYY-MM-DD)
    :param user: user ID that creates the voucher
    :return: Lista de vouchers de seguridad con sus ítems agregados como JSON o mensaje de error
    """
    sql = (
        "SELECT "
        "vs.id_voucher_general, "
        "vg.type, "
        "vg.date, "
        "vg.contract, "
        "vs.motive, "
        "vg.user, "
        "vs.epp_emp, "
        "vs.storage_emp, "
        "vs.designated_emp, "
        "vs.user_state, "
        "vs.epp_state, "
        "vs.storage_state, "
        "vs.extra_info, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        "'id_item', vi.id_item, "
        "'quantity', vi.quantity, "
        "'unit', vi.unit, "
        "'description', vi.description, "
        "'observations', vi.observations, "
        "'extra_info', vi.extra_info)"
        ") AS items, "
        "vg.history "
        "FROM sql_telintec_mod_admin.voucher_safety AS vs "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vs.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE (vg.date >= %s) AND (vg.user = %s OR %s IS NULL) GROUP BY vs.id_voucher_general "
    )
    val = (start_date, user, user)
    flag, error, vouchers = execute_sql(sql, val, 2)
    return flag, error, vouchers


def update_state_tools_voucher(id_voucher, user_state, superior_state, storage_state):
    """
    Actualiza los estados de un voucher de herramientas en la tabla voucher_tools.

    :param id_voucher: ID del voucher de herramientas
    :param user_state: Nuevo estado del usuario
    :param superior_state: Nuevo estado del superior
    :param storage_state: Nuevo estado del almacenamiento
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_tools "
        "SET user_state = %s, superior_state = %s, storage_state = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (user_state, superior_state, storage_state, id_voucher)
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


def update_state_safety_voucher(id_voucher, user_state, epp_state, storage_state):
    """
    Actualiza los estados de un voucher de seguridad en la tabla voucher_safety.

    :param id_voucher: ID del voucher de seguridad
    :param user_state: Nuevo estado del usuario
    :param epp_state: Nuevo estado de los elementos de seguridad
    :param storage_state: Nuevo estado del almacenamiento
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_safety "
        "SET user_state = %s, epp_state = %s, storage_state = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (user_state, epp_state, storage_state, id_voucher)
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed


def get_vouchers_vehicle_with_items(start_date, user=None):
    """
    Obtiene vouchers de vehículos desde una fecha específica, incluyendo su metadata e ítems relacionados.

    :param start_date: Fecha de inicio (YYYY-MM-DD)
    :param user: user ID que creó el voucher
    :return: Lista de vouchers vehiculares con sus ítems agregados como JSON o mensaje de error
    """
    sql = (
        "SELECT "
        "vv.id_voucher_general, "
        "vg.type, "
        "vg.date, "
        "vg.contract, "
        "vg.user AS realizado_por, "
        "vv.received_by, "
        "vv.brand, "
        "vv.model, "
        "vv.color, "
        "vv.year, "
        "vv.placas, "
        "vv.kilometraje, "
        "vv.registration_card, "
        "vv.insurance, "
        "vv.referendo, "
        "vv.accessories, "
        "vv.type AS vehicle_type, "
        "vv.observations, "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        "'id_item', vi.id_item, "
        "'quantity', vi.quantity, "
        "'unit', vi.unit, "
        "'description', vi.description, "
        "'observations', vi.observations, "
        "'extra_info', vi.extra_info)"
        ") AS items, "
        "vg.history "
        "FROM sql_telintec_mod_admin.voucher_vehicle AS vv "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vv.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE (vg.date >= %s) AND (vg.user = %s OR %s IS NULL) "
        "GROUP BY vv.id_voucher_general"
    )
    val = (start_date, user, user)
    flag, error, vouchers = execute_sql(sql, val, 2)
    return flag, error, vouchers


def create_voucher_vehicle(
    id_voucher_general,
    brand,
    model,
    color=None,
    year=None,
    placas=None,
    kilometraje=0,
    registration_card=0,
    insurance=0,
    referendo=0,
    accessories=None,
    type_v=2,
    received_by=None,
    observations=None,
):
    """
    Crea un nuevo registro en la tabla voucher_vehicle.

    :param id_voucher_general: ID del voucher general creado previamente
    :param brand: Marca del vehículo
    :param model: Modelo del vehículo
    :param color: Color del vehículo (opcional)
    :param year: Año del vehículo (opcional)
    :param placas: Placas del vehículo
    :param kilometraje: Kilometraje (default=0)
    :param registration_card: ¿Tiene tarjeta de circulación? (0/1)
    :param insurance: ¿Tiene póliza de seguro? (0/1)
    :param referendo: ¿Tiene comprobante de refrendo? (0/1)
    :param accessories: Estado de accesorios en formato JSON
    :param type_v: Tipo de vehículo (default=2)
    :param received_by: ID del empleado que recibe el vehículo
    :param observations: Observaciones generales
    :return: Estado de la operación (éxito/error)
    """
    if accessories is None:
        accessories = {}

    sql = (
        "INSERT INTO sql_telintec_mod_admin.voucher_vehicle "
        "(id_voucher_general, brand, model, color, year, placas, kilometraje, "
        "registration_card, insurance, referendo, accessories, type, received_by, observations) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        id_voucher_general,
        brand,
        model,
        color,
        year,
        placas,
        kilometraje,
        registration_card,
        insurance,
        referendo,
        json.dumps(accessories),
        type_v,
        received_by,
        observations,
    )
    flag, error, lastrowid = execute_sql(sql, val, 4)
    return flag, error, lastrowid


def update_voucher_vehicle(
    id_voucher_general,
    brand,
    model,
    color=None,
    year=None,
    placas=None,
    kilometraje=0,
    registration_card=0,
    insurance=0,
    referendo=0,
    accessories=None,
    type_v=2,
    received_by=None,
    observations=None,
):
    """
    Actualiza un registro existente en la tabla voucher_vehicle.

    :param id_voucher_general: ID del voucher general.
    :param brand: Marca del vehículo.
    :param model: Modelo del vehículo.
    :param color: Color del vehículo (opcional).
    :param year: Año del vehículo (opcional).
    :param placas: Placas del vehículo.
    :param kilometraje: Kilometraje (default=0).
    :param registration_card: ¿Tiene tarjeta de circulación? (0/1).
    :param insurance: ¿Tiene póliza de seguro? (0/1).
    :param referendo: ¿Tiene comprobante de refrendo? (0/1).
    :param accessories: Estado de accesorios en formato JSON.
    :param type_v: Tipo de vehículo (default=2).
    :param received_by: ID del empleado que recibe el vehículo.
    :param observations: Observaciones generales.
    :return: Estado de la operación (éxito/error)
    """
    if accessories is None:
        accessories = {}

    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_vehicle "
        "SET brand = %s, model = %s, color = %s, year = %s, placas = %s, kilometraje = %s, "
        "registration_card = %s, insurance = %s, referendo = %s, accessories = %s, "
        "type = %s, received_by = %s, observations = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (
        brand,
        model,
        color,
        year,
        placas,
        kilometraje,
        registration_card,
        insurance,
        referendo,
        json.dumps(accessories),
        type_v,
        received_by,
        observations,
        id_voucher_general,
    )
    flag, error, rows_changed = execute_sql(sql, val, 3)
    return flag, error, rows_changed
