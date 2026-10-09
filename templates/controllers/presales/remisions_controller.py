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
    data_token,
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
    flag, e, out = execute_sql(sql, val, 4, data_token)
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
    data_token,
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
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def update_quotation_activity_status(qa_id: int, status: int, history: list, data_token):
    # Cambio de estatus puntual: solo status + history, sin reenviar la fila
    # entera (evita pisar columnas con datos viejos del cliente).
    sql = (
        "UPDATE sql_telintec_mod_admin.quotations_activities "
        "SET status=%s, history=%s "
        "WHERE qa_id=%s"
    )
    val = (status, json.dumps(history), qa_id)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_quotation_activity(qa_id: int, data_token):
    sql = "DELETE FROM sql_telintec_mod_admin.quotations_activities WHERE qa_id=%s"
    val = (qa_id,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def insert_remission(
    date: str,
    folio: str,
    client_id: int,
    plant: str,
    area: str,
    location: str,
    general_description: str,
    comments: str,
    quotation_id: int | None,
    history: list,
    data_token,
    status: int = 0,
    contract_id: int | None = None,
    pedido: str = "",
    pedido_exiros: str = "",
    extra_info=None,
    balance_control_id: int | None = None,
    delivery_control_id: int | None = None,
):
    # balance_control_id: control de saldos al que nace ligada la remision (auto-enlace
    # cuando su contrato tiene control activo; Docs/control_saldos_sin_contrato.md).
    # delivery_control_id: control de entregas (OCD), explicito o resuelto por los
    # items (docs/control_entregas.md).
    if extra_info is None:
        extra_info = {}
    if "pedido" not in extra_info.keys():
        extra_info["pedido"] = pedido
    if "pedido_exiros" not in extra_info.keys():
        extra_info["pedido_exiros"] = pedido_exiros
    sql = (
        "INSERT INTO sql_telintec_mod_admin.activity_reports "
        "(date, folio, client_id, plant, area, location, general_description, comments, quotation_id, "
        " status, history, contract_id, extra_info, balance_control_id, delivery_control_id) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (
        date,
        folio,
        client_id,
        plant,
        area,
        location,
        general_description,
        comments,
        quotation_id,
        status,
        json.dumps(history),
        contract_id,
        json.dumps(extra_info),
        balance_control_id,
        delivery_control_id,
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_items_quotation_w_remission(remission_id, id_quotation, data_token):
    sql = "UPDATE sql_telintec_mod_admin.quotation_activity_items SET report_id=%s WHERE quotation_id=%s"
    val = (remission_id, id_quotation)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


# --- Escrituras parciales de activity_reports (docs/remission_atomic_writes.md) ------
# Los modulos (remisiones, control de reportes, control de saldos, controles,
# anexos) escriben la MISMA fila. Nada reescribe extra_info ni history completos
# con lo leido antes: extra_info cambia solo en las llaves del modulo (JSON_SET /
# JSON_MERGE_PATCH) y el history solo crece (JSON_ARRAY_APPEND), en el mismo
# UPDATE. Asi dos guardados simultaneos de modulos distintos ya no se pisan.
_REMISSION_CANCELLED_STATUS = 3
# Un valor no-objeto / no-arreglo (o NULL) se trata como vacio, igual que al leer.
EXTRA_INFO_OBJECT_SQL = "IF(JSON_TYPE(extra_info) = 'OBJECT', extra_info, JSON_OBJECT())"
HISTORY_APPEND_SQL = (
    "history = JSON_ARRAY_APPEND(IF(JSON_TYPE(history) = 'ARRAY', history, JSON_ARRAY()), "
    "'$', CAST(%s AS JSON))"
)
# Columnas base que patch_activity_report acepta (whitelist: van interpoladas).
_PATCHABLE_COLUMNS = (
    "date", "folio", "client_id", "plant", "area", "location",
    "general_description", "comments", "quotation_id", "status", "contract_id",
)


def json_param(value) -> str:
    """Valor -> texto JSON para CAST(%s AS JSON)."""
    return json.dumps(value, ensure_ascii=False)


def patch_activity_report(
    report_id: int,
    data_token,
    columns: dict | None = None,
    extra_info_set: dict | None = None,
    custom_fields_patch: dict | None = None,
    history_entry: dict | None = None,
):
    """UPDATE parcial de una remision NO cancelada. type_sql=3 -> filas afectadas;
    0 = no existe o se cancelo entre la lectura y la escritura (el history siempre
    crece, asi que una fila que hace match siempre cuenta).

    - columns: columnas base {col: valor} (solo _PATCHABLE_COLUMNS).
    - extra_info_set: llaves de primer nivel -> JSON_SET (None se guarda como null);
      las demas llaves de extra_info no se tocan.
    - custom_fields_patch: {key: valor | None} -> JSON_MERGE_PATCH sobre
      extra_info.custom_fields (None borra la llave).
    - history_entry: una entrada -> JSON_ARRAY_APPEND.
    """
    sets: list = []
    values: list = []
    for col, value in (columns or {}).items():
        if col not in _PATCHABLE_COLUMNS:
            raise ValueError(f"columna no editable en activity_reports: {col}")
        sets.append(f"{col} = %s")
        values.append(value)
    extra_expr = EXTRA_INFO_OBJECT_SQL
    extra_values: list = []
    if extra_info_set:
        pairs = []
        for key, value in extra_info_set.items():
            pairs.append("%s, CAST(%s AS JSON)")
            extra_values += [f'$."{key}"', json_param(value)]
        extra_expr = f"JSON_SET({extra_expr}, {', '.join(pairs)})"
    if custom_fields_patch:
        # Base = custom_fields de la fila (no de extra_expr: ninguna llave de modulo
        # se llama custom_fields). Un no-objeto se mezcla como {} (regla de MERGE_PATCH).
        extra_expr = (
            f"JSON_SET({extra_expr}, '$.custom_fields', JSON_MERGE_PATCH("
            "COALESCE(JSON_EXTRACT(extra_info, '$.custom_fields'), JSON_OBJECT()), CAST(%s AS JSON)))"
        )
        extra_values.append(json_param(custom_fields_patch))
    if extra_values:
        sets.append(f"extra_info = {extra_expr}")
        values += extra_values
    if history_entry is not None:
        sets.append(HISTORY_APPEND_SQL)
        values.append(json_param(history_entry))
    if not sets:
        return True, None, 0
    sql = (
        f"UPDATE sql_telintec_mod_admin.activity_reports SET {', '.join(sets)} "
        f"WHERE id = %s AND COALESCE(status, 0) <> {_REMISSION_CANCELLED_STATUS}"
    )
    values.append(report_id)
    flag, e, out = execute_sql(sql, tuple(values), 3, data_token)
    return flag, e, out


def set_remission_status(report_id: int, status: int, history_entry: dict, data_token):
    """Cambia solo status + agrega una entrada al history (cancelacion: status 3).
    Guard: solo si NO esta cancelada -> 0 filas = ya estaba cancelada (o no
    existe). type_sql=3 -> filas afectadas (docs/remission_cancel.md)."""
    sql = (
        f"UPDATE sql_telintec_mod_admin.activity_reports SET status = %s, {HISTORY_APPEND_SQL} "
        f"WHERE id = %s AND COALESCE(status, 0) <> {_REMISSION_CANCELLED_STATUS}"
    )
    val = (status, json_param(history_entry), report_id)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_remission_db(report_id: int, data_token):
    sql = "DELETE FROM sql_telintec_mod_admin.activity_reports WHERE id=%s"
    val = (report_id,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def insert_quotation_activity_item(
    quotation_id: int | None,
    report_id: int | None,
    description: str,
    udm: str,
    quantity: float,
    unit_price: float,
    history: list,
    data_token,
    item_c_id: int | None,
    extra_info: dict | None = None,
):
    # unit_price = precio real (sugerido durante la cotizacion, real tras la remision);
    # el precio sugerido de la cotizacion se conserva en extra_info["unit_price_quotation"].
    if extra_info is None:
        extra_info = {}
    sql = "INSERT INTO sql_telintec_mod_admin.quotation_activity_items (quotation_id, report_id, item_c_id, description, udm, quantity, unit_price, history, extra_info) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = (
        quotation_id,
        report_id,
        item_c_id,
        description,
        udm,
        quantity,
        unit_price,
        json.dumps(history),
        json.dumps(extra_info),
    )
    flag, e, out = execute_sql(sql, val, 4, data_token)
    return flag, e, out


def update_quotation_activity_item(
    qa_item_id: int,
    quotation_id: int | None,
    report_id: int | None,
    item_c_id: int | None,
    description: str,
    udm: str,
    quantity: float,
    unit_price: float,
    history: list,
    data_token,
    extra_info: dict | None = None,
):
    # El llamador decide el unit_price a escribir (protege el real cuando ya hay remision)
    # y entrega el extra_info ya resuelto (con unit_price_quotation preservado).
    if extra_info is None:
        extra_info = {}
    sql = "UPDATE sql_telintec_mod_admin.quotation_activity_items SET description=%s, udm=%s, quantity=%s, unit_price=%s, history=%s, item_c_id=%s, report_id=%s , quotation_id=%s, extra_info=%s WHERE qa_item_id=%s"
    val = (
        description,
        udm,
        quantity,
        unit_price,
        json.dumps(history),
        item_c_id,
        report_id,
        quotation_id,
        json.dumps(extra_info),
        qa_item_id,
    )
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def delete_quotation_activity_item(qa_item_id: int, data_token):
    sql = "DELETE FROM sql_telintec_mod_admin.quotation_activity_items WHERE qa_item_id=%s"
    val = (qa_item_id,)
    flag, e, out = execute_sql(sql, val, 3, data_token)
    return flag, e, out


def get_quotation_activity_items(quotation_id, data_token):
    sql = """
    SELECT qa_item_id,
    description,
    udm,
    quantity,
    unit_price,
    line_total,
    history,
    item_c_id,
    report_id,
    quotation_id,
    extra_info
    FROM sql_telintec_mod_admin.quotation_activity_items
    WHERE quotation_id = %s
    """
    val = (quotation_id,)
    flag, e, out = execute_sql(sql, val, 2, data_token)
    return flag, e, out


def get_quotation_activity_by_id(id_quotation, data_token):
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
        # JSON_ARRAYAGG con LEFT JOIN sin items da [null] (si agrega el NULL,
        # a diferencia de casi todos los agregados); decidir por conteo evita
        # el TypeError rio arriba. Mismo patron que get_remission_by_id.
        "IF(COUNT(qai.qa_item_id) = 0, JSON_ARRAY(), "
        "JSON_ARRAYAGG("
        "JSON_OBJECT("
        " 'qa_item_id', qai.qa_item_id, "
        " 'quotation_id', qai.quotation_id, "
        " 'report_id', qai.report_id, "
        " 'item_c_id', qai.item_c_id, "
        " 'description', qai.description, "
        " 'udm', qai.udm, "
        " 'quantity', qai.quantity, "
        " 'unit_price', qai.unit_price, "
        " 'line_total', qai.line_total, "
        " 'history', qai.history, "
        " 'extra_info', qai.extra_info "
        "))) AS items "
        "FROM sql_telintec_mod_admin.quotations_activities AS qa "
        "LEFT JOIN sql_telintec_mod_admin.quotation_activity_items AS qai ON qa.qa_id = qai.quotation_id "
        "WHERE( qa.qa_id = %s  OR %s IS NULL)"
        "GROUP BY qa.qa_id"
    )
    val = (id_quotation, id_quotation)
    flag, e, out = (
        execute_sql(sql, val, 1, data_token)
        if id_quotation is not None
        else execute_sql(sql, val, 2, data_token)
    )
    return flag, e, out


def get_remission_by_id(
    id_report: int | None,
    data_token,
    date_from: str | None = None,
    date_to: str | None = None,
    month_period: str | None = None,
    general_status: int | None = None,
    client_id: int | None = None,
    balance_control_id: int | None = None,
    available_for_control: int | None = None,
    delivery_control_id: int | None = None,
):
    # Filtros opcionales (param-or-NULL): sin filtros la query es identica a la
    # historica, asi los demas call sites no cambian de comportamiento.
    # Indices 20..23 (append-only, los call sites indexan por posicion):
    #   20 = ar.balance_control_id (membresia del control de saldos)
    #   21 = is_active de ese control (NULL si la remision no apunta a ninguno)
    #   22 = ar.delivery_control_id (membresia del control de entregas, OCD)
    #   23 = status de ese control (0 abierto / 1 completo / 2 cancelado; NULL sin control)
    # available_for_control (cualquier valor no NULL) = remisiones "disponibles":
    # sin control o apuntando a uno cancelado.
    sql = """
    SELECT 
        ar.id, 
        ar.date, 
        ar.folio, 
        ar.client_id, 
        ar.client_company_name, 
        ar.client_contact_name, 
        ar.client_phone, 
        ar.client_email, 
        ar.plant, 
        ar.area, 
        ar.location, 
        ar.general_description, 
        ar.comments, 
        ar.quotation_id, 
        ar.status, 
        ar.history, 
        IF(
            COUNT(qai.qa_item_id) = 0,
            JSON_ARRAY(),
            JSON_ARRAYAGG(
                JSON_OBJECT(
                    'qa_item_id', qai.qa_item_id,
                    'quotation_id', qai.quotation_id,
                    'report_id', qai.report_id,
                    'item_c_id', qai.item_c_id,
                    'description', qai.description,
                    'udm', qai.udm,
                    'quantity', qai.quantity,
                    'unit_price', qai.unit_price,
                    'line_total', qai.line_total,
                    'history', qai.history,
                    'extra_info', qai.extra_info,
                    'partida', qi.partida
                )
            )
            ) AS items,
        ar.files,
        ar.contract_id,
        ar.extra_info,
        ar.balance_control_id,
        (SELECT bcx.is_active FROM sql_telintec_mod_admin.balance_controls AS bcx
            WHERE bcx.id_control = ar.balance_control_id) AS balance_control_active,
        ar.delivery_control_id,
        (SELECT dcx.status FROM sql_telintec_mod_admin.delivery_controls AS dcx
            WHERE dcx.id_control = ar.delivery_control_id) AS delivery_control_status
        FROM sql_telintec_mod_admin.activity_reports AS ar
        LEFT JOIN sql_telintec_mod_admin.quotation_activity_items AS qai ON ar.id = qai.report_id
        LEFT JOIN sql_telintec_mod_admin.quotation_items AS qi ON qi.id = qai.item_c_id
        WHERE( ar.id = %s  OR %s IS NULL)
        AND (DATE(ar.date) >= %s OR %s IS NULL)
        AND (DATE(ar.date) <= %s OR %s IS NULL)
        AND (JSON_UNQUOTE(JSON_EXTRACT(ar.extra_info, '$.month_period')) = %s OR %s IS NULL)
        AND (CAST(JSON_UNQUOTE(JSON_EXTRACT(ar.extra_info, '$.general_status')) AS SIGNED) = %s OR %s IS NULL)
        AND (ar.client_id = %s OR %s IS NULL)
        AND (ar.balance_control_id = %s OR %s IS NULL)
        AND (%s IS NULL OR ar.balance_control_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM sql_telintec_mod_admin.balance_controls AS bca
            WHERE bca.id_control = ar.balance_control_id AND bca.is_active = 1))
        AND (ar.delivery_control_id = %s OR %s IS NULL)
        GROUP BY ar.id"""

    val = (
        id_report, id_report,
        date_from, date_from,
        date_to, date_to,
        month_period, month_period,
        general_status, general_status,
        client_id, client_id,
        balance_control_id, balance_control_id,
        available_for_control,
        delivery_control_id, delivery_control_id,
    )
    flag, e, out = (
        execute_sql(sql, val, 1, data_token)
        if id_report is not None
        else execute_sql(sql, val, 2, data_token)
    )
    return flag, e, out


def update_report_activity_files(id_report, history_entry: dict, files: list, data_token, status: int | None = None):
    """Escribe la lista de anexos y agrega una entrada al history. `status` solo
    se escribe cuando el anexo lo cambia (firmas) y nunca reactiva una cancelada
    (CASE en SQL: la cancelacion pudo llegar despues de la lectura). La lista
    `files` sigue siendo lectura-modificacion-escritura (pendiente en
    docs/remission_atomic_writes.md). type_sql=3."""
    sets = ["files = %s", HISTORY_APPEND_SQL]
    val: list = [json.dumps(files), json_param(history_entry)]
    if status is not None:
        sets.append(
            f"status = CASE WHEN COALESCE(status, 0) = {_REMISSION_CANCELLED_STATUS} THEN status ELSE %s END"
        )
        val.append(status)
    sql = f"UPDATE sql_telintec_mod_admin.activity_reports SET {', '.join(sets)} WHERE id = %s"
    val.append(id_report)
    flag, e, out = execute_sql(sql, tuple(val), 3, data_token)
    return flag, e, out
