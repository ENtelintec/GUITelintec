# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 04/jun/2025  at 15:17 $"

import json

from templates.database.connection import execute_sql

# Agrega una entrada al history (JSON) sin reescribir lo leido; un history
# NULL o que no sea arreglo arranca en []. Mismo criterio que activity_reports.
_HISTORY_APPEND_SQL = (
    "history = JSON_ARRAY_APPEND(IF(JSON_TYPE(history) = 'ARRAY', history, JSON_ARRAY()), "
    "'$', CAST(%s AS JSON))"
)


def _json_param(value) -> str:
    """Valor -> texto JSON para CAST(%s AS JSON)."""
    return json.dumps(value, ensure_ascii=False)


def create_voucher_general(voucher_type, date, user, contract, data_token):
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
    flag, error, lastrowid = execute_sql(
        sql, val, 4, data_token
    )  # Ejecuta la inserción
    return flag, error, lastrowid


def delete_voucher_general(id_voucher, data_token):
    """
    Borra fisicamente una fila de vouchers_general. Solo para revertir un alta
    a medias (la fila acaba de nacer y no tiene hijos); el borrado de negocio
    deja la fila como rastro (ver delete_voucher_vehicle_api).

    :param id_voucher: ID del voucher general
    :return: (flag, error, filas borradas)
    """
    sql = "DELETE FROM sql_telintec_mod_admin.vouchers_general WHERE id_voucher = %s"
    flag, error, rows_changed = execute_sql(sql, (id_voucher,), 3, data_token)
    return flag, error, rows_changed


def append_history_voucher(id_voucher, entry: dict, data_token):
    """
    Agrega una entrada al history de vouchers_general en BD (JSON_ARRAY_APPEND),
    sin leer ni reescribir la lista: dos escritores simultaneos no se pisan.

    :param id_voucher: ID del voucher general
    :param entry: dict con la entrada (id_voucher, type, timestamp, user, comment)
    :return: (flag, error, filas afectadas)
    """
    sql = (
        f"UPDATE sql_telintec_mod_admin.vouchers_general SET {_HISTORY_APPEND_SQL} "
        "WHERE id_voucher = %s"
    )
    flag, error, rows_changed = execute_sql(sql, (_json_param(entry), id_voucher), 3, data_token)
    return flag, error, rows_changed


def create_voucher_tools(
    id_voucher_general,
    position,
    type_transaction,
    superior,
    storage_emp,
    desiganted_emp,
    data_token,
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
    flag, error, lastrowid = execute_sql(sql, val, 4, data_token)
    return flag, error, lastrowid


def update_voucher_tools(
    id_voucher_general,
    position,
    type_transaction,
    superior,
    storage_emp,
    designated_emp,
    data_token,
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
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def create_voucher_safety(
    id_voucher_general,
    motive,
    epp_emp,
    storage_emp,
    designated_emp,
    data_token,
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
    flag, error, lastrowid = execute_sql(sql, val, 4, data_token)
    return flag, error, lastrowid


def update_voucher_safety(
    id_voucher_general,
    epp_emp,
    storage_emp,
    designated_emp,
    data_token,
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
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def create_voucher_item(
    id_voucher,
    id_inventory,
    quantity,
    unit,
    description,
    data_token,
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
    flag, error, lastrowid = execute_sql(sql, val, 4, data_token)
    return flag, error, lastrowid


def update_history_voucher(history: list, id_voucher, data_token):
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
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def update_voucher_general_contract(id_voucher, contract, data_token):
    """
    Actualiza el contrato de un voucher en la tabla vouchers_general.

    :param id_voucher: ID del voucher general a actualizar
    :param contract: ID del contrato (contracts.id) o None = sin contrato
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "UPDATE sql_telintec_mod_admin.vouchers_general "
        "SET contract = %s "
        "WHERE id_voucher = %s"
    )
    val = (contract, id_voucher)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def update_voucher_general_from_delete(id_voucher, history, data_token):
    """
    Actualiza el historial de un voucher en la tabla vouchers_general.

    :param id_voucher: ID del voucher a actualizar
    :param history: Nuevo historial en formato JSON
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "UPDATE sql_telintec_mod_admin.vouchers_general "
        "SET history = %s  "
        "WHERE id_voucher = %s"
    )
    val = (json.dumps(history), id_voucher)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


# Status "cancelado" del checklist vehicular (delete_voucher_vehicle_api); una
# firma subida despues no lo reactiva. EPP y herramientas no tienen cancelado.
VEHICLE_VOUCHER_CANCELLED_STATUS = 3

# Tabla propia de cada tipo de vale (P-103): el helper de anexos elige por `kind`.
VOUCHER_TABLES = {
    "vehicle": "sql_telintec_mod_admin.voucher_vehicle",
    "epp": "sql_telintec_mod_admin.voucher_safety",
    "tools": "sql_telintec_mod_admin.voucher_tools",
}


def get_voucher_head(kind: str, id_voucher, data_token):
    """
    Cabecera minima de un vale por id, **sin ventana de fecha**:
    (id_voucher_general, vg.date, extra_info, status, vg.type). [] si no existe.
    type_sql=1. Para anexos y borrado; los GET de listado siguen con sus consultas.
    """
    table = VOUCHER_TABLES[kind]
    sql = (
        "SELECT v.id_voucher_general, vg.date, v.extra_info, v.status, vg.type "
        f"FROM {table} AS v "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vg.id_voucher = v.id_voucher_general "
        "WHERE v.id_voucher_general = %s"
    )
    flag, error, row = execute_sql(sql, (id_voucher,), 1, data_token)
    return flag, error, row


def update_voucher_files(
    kind: str,
    id_voucher,
    history_entry: dict,
    files: list,
    data_token,
    status: int | None = None,
    expected_files: list | None = None,
    cancelled_status: int | None = None,
):
    """
    Escribe la lista de anexos (`<tabla del vale>.extra_info.$.files`) y agrega
    una entrada al history de vouchers_general en **una sola sentencia**
    (UPDATE multi-tabla): solo se toca la llave `files` de extra_info, nunca el
    resto, y el history crece con JSON_ARRAY_APPEND sin reescribir lo leido.
    `status` solo se escribe cuando el anexo lo cambia (firmas) y, si el tipo
    tiene `cancelled_status`, nunca reactiva un vale cancelado.
    Con `expected_files` (la lista leida) el UPDATE es condicional: solo aplica
    si `files` sigue igual en BD. 0 filas = otro request la cambio entretanto y
    el midleware re-lee y reintenta (docs/checklist_vehicular_anexos_sin_carrera.md).
    Nunca hay 0 filas por "sin cambios": el history siempre crece. type_sql=3.
    """
    table = VOUCHER_TABLES[kind]
    sets = [
        "v.extra_info = JSON_SET(IF(JSON_TYPE(v.extra_info) = 'OBJECT', v.extra_info, JSON_OBJECT()), "
        "'$.files', CAST(%s AS JSON))",
        "vg." + _HISTORY_APPEND_SQL,
    ]
    val: list = [_json_param(files), _json_param(history_entry)]
    if status is not None:
        if cancelled_status is not None:
            sets.append(
                f"v.status = CASE WHEN COALESCE(v.status, 0) = {int(cancelled_status)} THEN v.status ELSE %s END"
            )
        else:
            sets.append("v.status = %s")
        val.append(status)
    sql = (
        f"UPDATE {table} AS v "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vg.id_voucher = v.id_voucher_general "
        f"SET {', '.join(sets)} WHERE v.id_voucher_general = %s"
    )
    val.append(id_voucher)
    if expected_files is not None:
        # Comparacion JSON por contenido (no por texto): sin llave cuenta como [].
        sql += " AND COALESCE(JSON_EXTRACT(v.extra_info, '$.files'), JSON_ARRAY()) = CAST(%s AS JSON)"
        val.append(_json_param(expected_files))
    flag, error, rows_changed = execute_sql(sql, tuple(val), 3, data_token)
    return flag, error, rows_changed


def update_voucher_vehicle_files(
    id_voucher, history_entry: dict, files: list, data_token, status: int | None = None, expected_files: list | None = None
):
    """Anexos del checklist vehicular (ver update_voucher_files); un cancelado (3) no se reactiva."""
    return update_voucher_files(
        "vehicle", id_voucher, history_entry, files, data_token, status=status, expected_files=expected_files,
        cancelled_status=VEHICLE_VOUCHER_CANCELLED_STATUS,
    )


def update_voucher_epp_files(
    id_voucher, history_entry: dict, files: list, data_token, status: int | None = None, expected_files: list | None = None
):
    """Anexos del vale EPP (voucher_safety); ver update_voucher_files."""
    return update_voucher_files("epp", id_voucher, history_entry, files, data_token, status=status, expected_files=expected_files)


def update_voucher_tools_files(
    id_voucher, history_entry: dict, files: list, data_token, status: int | None = None, expected_files: list | None = None
):
    """Anexos del vale de herramientas (voucher_tools); ver update_voucher_files."""
    return update_voucher_files("tools", id_voucher, history_entry, files, data_token, status=status, expected_files=expected_files)


def update_voucher_item(
    id_item,
    id_inventory,
    quantity,
    unit,
    description,
    data_token,
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
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def delete_voucher_item(id_item: int, data_token):
    sql = "DELETE FROM sql_telintec_mod_admin.voucher_items WHERE id_item = %s"
    val = (id_item,)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def get_vouchers_tools_with_items_date(
    start_date, data_token, user=None, id_voucher=None
):
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
        "vg.history, "
        "vt.status "
        "FROM sql_telintec_mod_admin.voucher_tools AS vt "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vt.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE ((vg.date >= %s) AND (vg.user = %s OR %s IS NULL) OR (vt.id_voucher_general = %s OR %s IS NULL)) "
        "GROUP BY vt.id_voucher_general"
    )
    val = (start_date, user, user, id_voucher, id_voucher)
    flag, error, vouchers = execute_sql(sql, val, 2, data_token)
    return flag, error, vouchers


def get_vouchers_safety_with_items(start_date, data_token, user=None, id_voucher=None):
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
        "vg.history, "
        "vs.status "
        "FROM sql_telintec_mod_admin.voucher_safety AS vs "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vs.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE ((vg.date >= %s) AND (vg.user = %s OR %s IS NULL) OR (vs.id_voucher_general = %s OR %s IS NULL)) "
        "GROUP BY vs.id_voucher_general "
    )
    val = (start_date, user, user, id_voucher, id_voucher)
    flag, error, vouchers = execute_sql(sql, val, 2, data_token)
    return flag, error, vouchers


def update_state_tools_voucher(
    id_voucher, user_state, superior_state, storage_state, data_token
):
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
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def delete_items_voucher(id_voucher, data_token):
    """
    Elimina los ítems asociados a un voucher en la tabla voucher_items.

    :param id_voucher: ID del voucher del cual se eliminarán los ítems
    :return: Estado de la operación (éxito/error)
    """
    sql = "DELETE FROM sql_telintec_mod_admin.voucher_items WHERE id_voucher = %s"
    val = (id_voucher,)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def delete_voucher_tools(id_voucher, data_token):
    """
    Elimina un voucher de herramientas de la tabla voucher_tools.

    :param id_voucher: ID del voucher de herramientas a eliminar
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "DELETE FROM sql_telintec_mod_admin.voucher_tools WHERE id_voucher_general = %s"
    )
    val = (id_voucher,)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def delete_voucher_safety(id_voucher, data_token):
    """
    Elimina un voucher de seguridad de la tabla voucher_safety.

    :param id_voucher: ID del voucher de seguridad a eliminar
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "DELETE FROM sql_telintec_mod_admin.voucher_safety "
        "WHERE id_voucher_general = %s"
    )
    val = (id_voucher,)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def update_state_safety_voucher(
    id_voucher, user_state, epp_state, storage_state, data_token
):
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
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def get_vouchers_vehicle_with_items(start_date, data_token, user=None, id_voucher=None):
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
        "vg.history, "
        "vv.extra_info, "
        " vv.status "
        "FROM sql_telintec_mod_admin.voucher_vehicle AS vv "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg ON vv.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec_mod_admin.voucher_items AS vi ON vg.id_voucher = vi.id_voucher "
        "WHERE (vg.date >= %s) AND ((vg.user = %s OR %s IS NULL) OR (vv.id_voucher_general = %s OR %s IS NULL)) "
        "GROUP BY vv.id_voucher_general"
    )
    val = (start_date, user, user, id_voucher, id_voucher)
    flag, error, vouchers = execute_sql(sql, val, 2, data_token)
    return flag, error, vouchers


def get_voucher_vehicle_by_id(id_voucher, data_token):
    """
    Obtiene un voucher vehicular (checklist vehicular) por su ID, con los
    nombres de quien lo realizó (vg.user) y quien lo recibió (vv.received_by)
    resueltos desde employees. Sin ventana de fecha: el PDF del checklist debe
    poder descargarse para cualquier voucher existente.

    :param id_voucher: ID del voucher (vouchers_general.id_voucher)
    :return: (flag, error, tupla) — [] si no existe
    """
    sql = (
        "SELECT "
        "vv.id_voucher_general, "
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
        "vv.extra_info, "
        "vv.status, "
        "CONCAT(er.name, ' ', er.l_name) AS realizado_name, "
        "CONCAT(ee.name, ' ', ee.l_name) AS received_name "
        "FROM sql_telintec_mod_admin.voucher_vehicle AS vv "
        "JOIN sql_telintec_mod_admin.vouchers_general AS vg "
        "ON vv.id_voucher_general = vg.id_voucher "
        "LEFT JOIN sql_telintec.employees AS er ON vg.user = er.employee_id "
        "LEFT JOIN sql_telintec.employees AS ee ON vv.received_by = ee.employee_id "
        "WHERE vv.id_voucher_general = %s"
    )
    val = (id_voucher,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def create_voucher_vehicle(
    id_voucher_general,
    brand,
    model,
    data_token,
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
    flag, error, lastrowid = execute_sql(sql, val, 4, data_token)
    return flag, error, lastrowid


def update_voucher_vehicle(
    id_voucher_general,
    brand,
    model,
    data_token,
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
    status=None,
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
    :param extra_info: Información adicional sobre el voucher.
    :param status: Estado del voucher (pendiente, aprobado, rechazado).
    :return: Estado de la operación (éxito/error)
    """
    if accessories is None:
        accessories = []

    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_vehicle "
        "SET brand = %s, model = %s, color = %s, year = %s, placas = %s, kilometraje = %s, "
        "registration_card = %s, insurance = %s, referendo = %s, accessories = %s, "
        "type = %s, received_by = %s, observations = %s, status = %s "
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
        status,
        id_voucher_general,
    )
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def delete_voucher_vehicle(id_voucher, data_token):
    """
    Elimina un registro de la tabla voucher_vehicle.

    :param id_voucher: ID del voucher vehicular a eliminar
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "DELETE FROM sql_telintec_mod_admin.voucher_vehicle "
        "WHERE id_voucher_general = %s"
    )
    val = (id_voucher,)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed


def update_voucher_vehicle_status(status, id_voucher_general, data_token):
    """
    Actualiza el estado de un voucher vehicular en la tabla voucher_vehicle.

    :param status: Nuevo estado del voucher (0: Pendiente, 1: firmado revisado, 2: aceptado, 3: cancelado)
    :param id_voucher_general: ID del voucher general asociado
    :return: Estado de la operación (éxito/error)
    """
    sql = (
        "UPDATE sql_telintec_mod_admin.voucher_vehicle "
        "SET status = %s "
        "WHERE id_voucher_general = %s"
    )
    val = (status, id_voucher_general)
    flag, error, rows_changed = execute_sql(sql, val, 3, data_token)
    return flag, error, rows_changed
