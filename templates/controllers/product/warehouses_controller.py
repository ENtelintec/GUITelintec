# -*- coding: utf-8 -*-
"""
Multisede de almacén — acceso a datos (docs/almacen_multisede_plan.md).

Tablas (DDL: scripts_db_handle/almacen_multisede.sql, esquema sql_telintec):
  * warehouses_amc          catálogo de sedes (is_main=1 = principal, única).
  * warehouse_stock_amc     stock por producto en sedes SECUNDARIAS; el
                            principal sigue en products_amc.stock.
  * warehouse_transfers_amc traslados con en-tránsito (F3).
  * product_movements_amc   kardex único; id_warehouse NULL = principal. Las
                            lecturas del principal (movements_controller.py)
                            filtran IS NULL; las de sede viven aquí (F2).
"""
__author__ = "Edisson Naula"
__date__ = "$ 07/sep./2026  at 12:00 $"

import json

from templates.database.connection import execute_sql

_TABLE = "sql_telintec.warehouses_amc"

# Columnas del catálogo de sedes; el midleware mapea por posición con esta tupla.
WAREHOUSE_COLUMNS = (
    "id_warehouse",
    "name",
    "is_main",
    "is_active",
    "extra_info",
    "history",
    "created_at",
    "updated_at",
)

# Columnas que un UPDATE parcial puede tocar (whitelist del SET dinámico).
_UPDATABLE_COLS = ("name", "is_active", "extra_info", "history")


# --- Catálogo de sedes ------------------------------------------------------
def get_warehouses_db(only_active, data_token):
    """Listado de sedes. only_active=1 -> solo is_active=1; None -> todas.
    type_sql=2 -> fetchall."""
    sql = (
        f"SELECT {', '.join(WAREHOUSE_COLUMNS)} FROM {_TABLE} "
        "WHERE (%s IS NULL OR is_active = %s) "
        "ORDER BY is_main DESC, id_warehouse"
    )
    val = (only_active, only_active)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


def get_warehouse_db(id_warehouse, data_token):
    """Una sede por id. type_sql=1 -> fetchone (tupla o [])."""
    sql = f"SELECT {', '.join(WAREHOUSE_COLUMNS)} FROM {_TABLE} WHERE id_warehouse = %s"
    val = (id_warehouse,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def get_main_warehouse_db(data_token):
    """La sede principal (is_main=1). type_sql=1."""
    sql = f"SELECT {', '.join(WAREHOUSE_COLUMNS)} FROM {_TABLE} WHERE is_main = 1 LIMIT 1"
    flag, error, result = execute_sql(sql, None, 1, data_token)
    return flag, error, result


def insert_warehouse_db(data: dict, data_token):
    """Alta de sede secundaria (is_main siempre 0: el principal nace del seed).
    type_sql=4 -> lastrowid."""
    sql = (
        f"INSERT INTO {_TABLE} (name, is_main, is_active, extra_info, history) "
        "VALUES (%s, 0, 1, %s, %s)"
    )
    val = (
        data.get("name"),
        json.dumps(data.get("extra_info") or {}, ensure_ascii=False),
        json.dumps(data.get("history") or [], ensure_ascii=False),
    )
    flag, error, result = execute_sql(sql, val, 4, data_token)
    return flag, error, result


def update_warehouse_fields_db(id_warehouse, updates: dict, data_token):
    """UPDATE parcial: solo las columnas presentes en `updates` (whitelist).
    dict/list se serializan a JSON. type_sql=3 -> rowcount (filas *cambiadas*:
    un UPDATE sin cambios da 0 sin ser error)."""
    cols, vals = [], []
    for col in _UPDATABLE_COLS:
        if col not in updates:
            continue
        value = updates[col]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        cols.append(f"{col} = %s")
        vals.append(value)
    if not cols:
        return True, "None", 0
    sql = f"UPDATE {_TABLE} SET {', '.join(cols)} WHERE id_warehouse = %s"
    vals.append(id_warehouse)
    flag, error, result = execute_sql(sql, tuple(vals), 3, data_token)
    return flag, error, result


# --- Inventario consolidado (lado principal) --------------------------------
CONSOLIDATED_COLUMNS = (
    "id_product",
    "sku",
    "name",
    "udm",
    "stock_main",
    "by_warehouse",   # JSON [{id_warehouse, name, stock}] o NULL
    "in_transit",     # suma de quantity_sent de traslados en tránsito (status 0)
)


def get_consolidated_stock_db(search, only_multisede, data_token):
    """Por producto: stock del principal (products_amc.stock) + stock por sede
    secundaria (warehouse_stock_amc, como JSON) + cantidad en tránsito
    (items JSON de los traslados con status 0, vía JSON_TABLE). `search`
    filtra por sku/nombre (LIKE); only_multisede=1 deja solo productos con
    stock en alguna sede o en tránsito. type_sql=2 -> fetchall."""
    like = f"%{search}%" if search else None
    sql = (
        "SELECT p.id_product, p.sku, p.name, p.udm, p.stock, "
        "(SELECT JSON_ARRAYAGG(JSON_OBJECT('id_warehouse', ws.id_warehouse, 'name', w.name, 'stock', ws.stock)) "
        " FROM sql_telintec.warehouse_stock_amc ws "
        " JOIN sql_telintec.warehouses_amc w ON w.id_warehouse = ws.id_warehouse "
        " WHERE ws.id_product = p.id_product) AS by_warehouse, "
        "IFNULL((SELECT SUM(jt.quantity_sent) "
        " FROM sql_telintec.warehouse_transfers_amc t, "
        " JSON_TABLE(t.items, '$[*]' COLUMNS (id_product INT PATH '$.id_product', "
        "   quantity_sent DECIMAL(14,4) PATH '$.quantity_sent')) jt "
        " WHERE t.status = 0 AND jt.id_product = p.id_product), 0) AS in_transit "
        "FROM sql_telintec.products_amc p "
        "WHERE (%s IS NULL OR p.sku LIKE %s OR p.name LIKE %s) "
        "HAVING (%s IS NULL OR by_warehouse IS NOT NULL OR in_transit > 0) "
        "ORDER BY p.name"
    )
    val = (like, like, like, only_multisede)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


# =============================================================================
# Lado SEDE (namespace sucursal, F2) — inventario, stock y kardex por sede.
# =============================================================================
SEDE_INVENTORY_COLUMNS = (
    "id_product",
    "sku",
    "name",
    "udm",
    "category_name",
    "stock",        # stock de la sede (warehouse_stock_amc; 0 si no hay fila)
    "stock_main",   # stock del principal (products_amc.stock), solo lectura
    "is_tool",
    "is_internal",
    "name_short",
)


def get_warehouse_inventory_db(id_warehouse, search, only_with_stock, data_token):
    """Catálogo compartido con el stock de UNA sede secundaria (LEFT JOIN a
    warehouse_stock_amc por sede) y el del principal al lado. `search` LIKE
    por sku/nombre; only_with_stock=1 deja solo productos con stock > 0 en
    la sede. type_sql=2 -> fetchall."""
    like = f"%{search}%" if search else None
    sql = (
        "SELECT p.id_product, p.sku, p.name, p.udm, c.name, "
        "IFNULL(ws.stock, 0), p.stock, p.is_tool, p.is_internal, p.name_short "
        "FROM sql_telintec.products_amc p "
        "LEFT JOIN sql_telintec.product_categories_amc c ON c.id_category = p.id_category "
        "LEFT JOIN sql_telintec.warehouse_stock_amc ws "
        "  ON ws.id_product = p.id_product AND ws.id_warehouse = %s "
        "WHERE (%s IS NULL OR p.sku LIKE %s OR p.name LIKE %s) "
        "AND (%s IS NULL OR IFNULL(ws.stock, 0) > 0) "
        "ORDER BY p.name"
    )
    val = (id_warehouse, like, like, like, only_with_stock)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


def get_main_inventory_db(search, only_with_stock, data_token):
    """Catálogo con el stock del PRINCIPAL (products_amc.stock), para que la
    sede lo consulte en solo lectura. Mismas columnas que la sede: `stock`
    y `stock_main` traen el mismo valor. type_sql=2."""
    like = f"%{search}%" if search else None
    sql = (
        "SELECT p.id_product, p.sku, p.name, p.udm, c.name, "
        "p.stock, p.stock, p.is_tool, p.is_internal, p.name_short "
        "FROM sql_telintec.products_amc p "
        "LEFT JOIN sql_telintec.product_categories_amc c ON c.id_category = p.id_category "
        "WHERE (%s IS NULL OR p.sku LIKE %s OR p.name LIKE %s) "
        "AND (%s IS NULL OR p.stock > 0) "
        "ORDER BY p.name"
    )
    val = (like, like, like, only_with_stock)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


# --- Stock por sede -----------------------------------------------------------
def get_warehouse_stock_db(id_warehouse, id_product, data_token):
    """Stock de un producto en una sede. type_sql=1 -> (stock,) o [] si el
    producto nunca se ha movido en esa sede (= 0)."""
    sql = (
        "SELECT stock FROM sql_telintec.warehouse_stock_amc "
        "WHERE id_warehouse = %s AND id_product = %s"
    )
    val = (id_warehouse, id_product)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def add_warehouse_stock_db(id_warehouse, id_product, delta, data_token):
    """Suma `delta` (puede ser negativo) al stock del producto en la sede;
    crea la fila si no existe (upsert atómico). La validación de no-negativo
    la hace el midleware ANTES. type_sql=3 -> rowcount (1 insert, 2 update
    por la semántica de ON DUPLICATE KEY; 0 solo si delta == 0)."""
    sql = (
        "INSERT INTO sql_telintec.warehouse_stock_amc (id_product, id_warehouse, stock) "
        "VALUES (%s, %s, %s) AS new "
        "ON DUPLICATE KEY UPDATE stock = warehouse_stock_amc.stock + new.stock"
    )
    val = (id_product, id_warehouse, delta)
    flag, error, result = execute_sql(sql, val, 3, data_token)
    return flag, error, result


# --- Kardex por sede -----------------------------------------------------------
SEDE_MOVEMENT_COLUMNS = (
    "id_movement",
    "id_product",
    "sku",
    "name",
    "udm",
    "movement_type",
    "quantity",
    "movement_date",
    "sm_id",
    "extra_info",
    "id_warehouse",
)

_SEDE_MOVEMENT_SELECT = (
    "SELECT m.id_movement, m.id_product, p.sku, p.name, p.udm, m.movement_type, "
    "m.quantity, m.movement_date, m.sm_id, m.extra_info, m.id_warehouse "
    "FROM sql_telintec.product_movements_amc m "
    "JOIN sql_telintec.products_amc p ON p.id_product = m.id_product "
)


def get_warehouse_movements_db(id_warehouse, type_m, date_from, date_to, limit, data_token):
    """Kardex de UNA sede (id_warehouse = %s, nunca NULL). `type_m` LIKE
    ('%' = todos), fechas inclusivas sobre DATE(movement_date), `limit`
    tope de filas (más recientes primero). type_sql=2."""
    sql = (
        _SEDE_MOVEMENT_SELECT
        + "WHERE m.id_warehouse = %s AND m.movement_type LIKE %s "
        "AND (%s IS NULL OR DATE(m.movement_date) >= %s) "
        "AND (%s IS NULL OR DATE(m.movement_date) <= %s) "
        "ORDER BY m.movement_date DESC, m.id_movement DESC "
        "LIMIT %s"
    )
    val = (id_warehouse, type_m, date_from, date_from, date_to, date_to, int(limit))
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


def get_warehouse_movement_db(id_movement, data_token):
    """Un movimiento por id, de cualquier sede (el midleware valida la
    pertenencia con `id_warehouse`). type_sql=1."""
    sql = _SEDE_MOVEMENT_SELECT + "WHERE m.id_movement = %s"
    val = (id_movement,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def insert_warehouse_movement_db(
    id_warehouse, id_product, movement_type, quantity, movement_date, extra_info, data_token
):
    """Movimiento del kardex con sede (id_warehouse NOT NULL). sm_id queda
    NULL: las SMs se despachan solo del principal. type_sql=4 -> lastrowid."""
    sql = (
        "INSERT INTO sql_telintec.product_movements_amc "
        "(id_product, movement_type, quantity, movement_date, sm_id, id_warehouse, extra_info) "
        "VALUES (%s, %s, %s, %s, NULL, %s, %s)"
    )
    val = (
        id_product,
        movement_type,
        quantity,
        movement_date,
        id_warehouse,
        json.dumps(extra_info or {}, ensure_ascii=False),
    )
    flag, error, result = execute_sql(sql, val, 4, data_token)
    return flag, error, result


_SEDE_MOVEMENT_UPDATABLE = ("movement_type", "quantity", "movement_date", "extra_info")


def update_warehouse_movement_db(id_movement, id_warehouse, updates: dict, data_token):
    """UPDATE parcial de un movimiento de sede (whitelist), acotado a su
    sede por seguridad. type_sql=3 -> rowcount."""
    cols, vals = [], []
    for col in _SEDE_MOVEMENT_UPDATABLE:
        if col not in updates:
            continue
        value = updates[col]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        cols.append(f"{col} = %s")
        vals.append(value)
    if not cols:
        return True, "None", 0
    sql = (
        f"UPDATE sql_telintec.product_movements_amc SET {', '.join(cols)} "
        "WHERE id_movement = %s AND id_warehouse = %s"
    )
    vals.extend([id_movement, id_warehouse])
    flag, error, result = execute_sql(sql, tuple(vals), 3, data_token)
    return flag, error, result


def delete_warehouse_movement_db(id_movement, id_warehouse, data_token):
    """Borra un movimiento de sede (acotado a su sede). type_sql=3."""
    sql = (
        "DELETE FROM sql_telintec.product_movements_amc "
        "WHERE id_movement = %s AND id_warehouse = %s"
    )
    val = (id_movement, id_warehouse)
    flag, error, result = execute_sql(sql, val, 3, data_token)
    return flag, error, result
