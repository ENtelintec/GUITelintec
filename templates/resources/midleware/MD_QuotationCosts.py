# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/sep./2026  at 19:30 $"

"""Análisis de costos por item cotizado (Preventa): captura manual del costo,
tipo de cambio, % ganancia y comparativa de proveedores por partida; el back
calcula unit_cost_mxn y unit_price_profit y, si se pide, los aplica como
price_unit de la cotización. Ver docs/quotation_cost_analysis.md.

Reglas:
  * Un análisis por partida (quotation_item_id UNIQUE): el PUT hace upsert por
    item y REEMPLAZA su comparativa completa. `cost: null` borra ambos.
  * unit_cost_mxn = unit_cost x exchange_rate (= unit_cost si MXN);
    unit_price_profit = unit_cost_mxn x (1 + profit_pct / 100). profit_pct en
    porcentaje (30 = 30 %). 4 decimales en costos, 2 al aplicar a price_unit.
  * exchange_rate: el de cada item manda; si no viene, el de la cabecera
    (que ademas se guarda en quotations.metadata.exchange_rate). USD sin tipo
    de cambio -> 400.
  * Todo se valida antes de escribir (400 con lista). Escritura item por item
    (execute_sql no da transacciones): un fallo de BD a mitad se reporta en
    `error` con lo que si se aplico.
  * El PDF al cliente nunca imprime estas tablas; solo GET /quotation/<id>?with_costs=1.
"""

import json
from decimal import Decimal, InvalidOperation

from static.constants import format_timestamps, log_file_admin
from templates.controllers.contracts.quotation_costs_controller import (
    COST_COLUMNS,
    SUPPLIER_QUOTE_COLUMNS,
    delete_cost_by_item,
    delete_supplier_quotes_by_item,
    get_costs_by_quotation,
    get_supplier_names,
    get_supplier_quotes_by_quotation,
    insert_cost,
    insert_supplier_quote,
    update_cost,
    update_quotation_item_price,
)
from templates.controllers.contracts.quotations_controller import get_quotation_metadata, update_quotation
from templates.controllers.purchases.delivery_control_controller import (
    ORDER_ITEM_COLUMNS,
    get_quotation_order_items,
)
from templates.misc.Functions_Files import write_log_file
from templates.resources.midleware.MD_BalanceControl import _json_safe, _load_json, _now

CURRENCIES = ("MXN", "USD")
_Q4 = Decimal("0.0001")
_Q2 = Decimal("0.01")


# --- Helpers ---------------------------------------------------------------------
def _dec(value, places=_Q4):
    """Decimal o None; lanza ValueError si no es numérico."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("booleano")
    try:
        return Decimal(str(value)).quantize(places)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("no numérico") from exc


def _f(value):
    return float(value) if value is not None else None


def _int_or_none(value):
    try:
        return int(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _bool_or_none(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "si", "sí", "yes"):
        return True
    if text in ("0", "false", "no"):
        return False
    return None


def _cost_row_to_dict(row) -> dict:
    d = {col: _json_safe(val) for col, val in zip(COST_COLUMNS, row)}
    d["history"] = _load_json(d.get("history"), []) or []
    d["extra_info"] = _load_json(d.get("extra_info"), {}) or {}
    d["smart_account"] = bool(d["smart_account"]) if d.get("smart_account") is not None else None
    return d


def _quote_row_to_dict(row) -> dict:
    d = {col: _json_safe(val) for col, val in zip(SUPPLIER_QUOTE_COLUMNS, row)}
    d["is_selected"] = bool(d.get("is_selected"))
    d["supplier_name"] = d.get("supplier_name") or d.get("catalog_name")
    d.pop("catalog_name", None)
    return d


def _compute(unit_cost, currency, exchange_rate, profit_pct):
    """(unit_cost_mxn, unit_price_profit) en Decimal 4 dp."""
    if unit_cost is None:
        return None, None
    if currency == "MXN":
        mxn = unit_cost
    else:
        mxn = (unit_cost * exchange_rate).quantize(_Q4)
    pct = profit_pct if profit_pct is not None else Decimal("0")
    price = (mxn * (Decimal("1") + pct / Decimal("100"))).quantize(_Q4)
    return mxn, price


def get_quotation_costs_map(quotation_id: int, data_token) -> tuple[dict, dict, str | None]:
    """{quotation_item_id: cost_dict_con_suppliers}, totales, error. Para el
    GET /quotation/<id>?with_costs=1."""
    flag, error, rows = get_costs_by_quotation(quotation_id, data_token)
    if not flag:
        return {}, {}, error
    costs = {int(r[COST_COLUMNS.index("quotation_item_id")]): _cost_row_to_dict(r) for r in rows}
    for c in costs.values():
        c["suppliers"] = []
    flag, error, q_rows = get_supplier_quotes_by_quotation(quotation_id, data_token)
    if flag:
        for r in q_rows:
            q = _quote_row_to_dict(r)
            item_id = int(q["quotation_item_id"])
            costs.setdefault(item_id, {"quotation_item_id": item_id, "suppliers": []})["suppliers"].append(q)
    return costs, {}, error if not flag else None


def costs_totals(items: list, costs: dict) -> dict:
    """Totales sin/con ganancia de la cotización: Σ cantidad x unitario por partida analizada."""
    total_cost = Decimal("0")
    total_profit = Decimal("0")
    analyzed = 0
    for it in items:
        c = costs.get(int(it["id"]))
        if not c or c.get("unit_cost_mxn") is None:
            continue
        qty = Decimal(str(it.get("quantity") or 0))
        total_cost += qty * Decimal(str(c["unit_cost_mxn"]))
        total_profit += qty * Decimal(str(c.get("unit_price_profit") or 0))
        analyzed += 1
    return {
        "items_count": len(items),
        "items_analyzed": analyzed,
        "total_cost_mxn": float(total_cost.quantize(_Q2)),
        "total_with_profit_mxn": float(total_profit.quantize(_Q2)),
        "profit_mxn": float((total_profit - total_cost).quantize(_Q2)),
    }


# --- PUT /quotation/costAnalysis ------------------------------------------------------
def update_quotation_cost_analysis_from_api(data, raw_payload, data_token):
    now = _now()
    timestamp = now.strftime(format_timestamps)
    user = data_token.get("emp_id")
    id_quotation = _int_or_none(data.get("id_quotation"))
    if not id_quotation:
        return {"data": None, "msg": "Falta la cotización", "error": ["id_quotation requerido"]}, 400
    raw_items = (raw_payload or {}).get("items")
    if not isinstance(raw_items, list) or not raw_items:
        return {"data": None, "msg": "Estructura de datos inválida", "error": ["items debe ser una lista con al menos un item"]}, 400

    flag, error, row = get_quotation_metadata(id_quotation, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo leer la cotización", "error": error}, 400
    if not row:
        return {"data": None, "msg": f"No se encontró la cotización (ID {id_quotation})", "error": "Quotation not found"}, 404
    metadata = _load_json(row[0], {}) or {}  # pyrefly: ignore
    timestamps = _load_json(row[1], None)  # pyrefly: ignore

    errors = []
    header_rate = None
    try:
        header_rate = _dec(data.get("exchange_rate"), Decimal("0.000001"))
        if header_rate is not None and header_rate <= 0:
            errors.append("exchange_rate debe ser > 0")
    except ValueError:
        errors.append("exchange_rate debe ser numérico")
    if header_rate is None:
        try:
            header_rate = _dec(metadata.get("exchange_rate"), Decimal("0.000001"))
        except ValueError:
            header_rate = None

    flag, error, item_rows = get_quotation_order_items(id_quotation, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron leer las partidas", "error": error}, 400
    items_by_id = {int(r[0]): {col: _json_safe(val) for col, val in zip(ORDER_ITEM_COLUMNS, r)} for r in item_rows}
    existing, _t, err_map = get_quotation_costs_map(id_quotation, data_token)
    if err_map:
        return {"data": None, "msg": "No se pudo leer el análisis actual", "error": err_map}, 400

    # --- Validar todo antes de escribir -------------------------------------------
    plan: list[dict] = []  # [{item_id, delete, cost, suppliers}]
    seen_items: set[int] = set()
    supplier_ids: set[int] = set()
    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            errors.append(f"items[{idx}] debe ser un objeto")
            continue
        item_id = _int_or_none(raw.get("id"))
        label = f"items[{idx}] (id {item_id})"
        if not item_id or item_id not in items_by_id:
            errors.append(f"{label}: la partida no existe o no pertenece a la cotización {id_quotation}")
            continue
        if item_id in seen_items:
            errors.append(f"{label}: partida repetida en la lista")
            continue
        seen_items.add(item_id)
        if "cost" in raw and raw.get("cost") is None:
            plan.append({"item_id": item_id, "delete": True})
            continue
        cost_in = raw.get("cost")
        if not isinstance(cost_in, dict):
            errors.append(f"{label}: cost debe ser un objeto (o null para borrar)")
            continue
        currency = str(cost_in.get("currency") or "MXN").strip().upper()
        if currency not in CURRENCIES:
            errors.append(f"{label}: currency debe ser MXN o USD")
            continue
        try:
            unit_cost = _dec(cost_in.get("unit_cost"))
            rate = _dec(cost_in.get("exchange_rate"), Decimal("0.000001"))
            pct = _dec(cost_in.get("profit_pct"))
        except ValueError:
            errors.append(f"{label}: unit_cost / exchange_rate / profit_pct deben ser numéricos")
            continue
        if unit_cost is None or unit_cost < 0:
            errors.append(f"{label}: unit_cost es obligatorio y >= 0")
            continue
        if pct is not None and pct < 0:
            errors.append(f"{label}: profit_pct no puede ser negativo")
            continue
        if rate is None:
            rate = header_rate
        if currency == "USD" and (rate is None or rate <= 0):
            errors.append(f"{label}: costo en USD requiere exchange_rate (del item o de la cabecera)")
            continue
        if currency == "MXN":
            rate = None  # no aplica: el snapshot solo tiene sentido cuando se convirtió
        service_months = _int_or_none(cost_in.get("service_months"))
        smart_account = _bool_or_none(cost_in.get("smart_account"))
        mxn, price = _compute(unit_cost, currency, rate, pct)
        suppliers_in = raw.get("suppliers")
        suppliers = []
        if suppliers_in is not None:
            if not isinstance(suppliers_in, list):
                errors.append(f"{label}: suppliers debe ser una lista")
                continue
            positions = set()
            selected = 0
            for j, s in enumerate(suppliers_in):
                if not isinstance(s, dict):
                    errors.append(f"{label}: suppliers[{j}] debe ser un objeto")
                    continue
                pos = _int_or_none(s.get("position")) or (j + 1)
                if pos in positions:
                    errors.append(f"{label}: suppliers position {pos} repetida")
                    continue
                positions.add(pos)
                s_currency = str(s.get("currency") or "MXN").strip().upper()
                if s_currency not in CURRENCIES:
                    errors.append(f"{label}: suppliers[{j}].currency debe ser MXN o USD")
                    continue
                try:
                    s_price = _dec(s.get("unit_price"))
                except ValueError:
                    errors.append(f"{label}: suppliers[{j}].unit_price debe ser numérico")
                    continue
                s_id = _int_or_none(s.get("supplier_id"))
                s_name = (s.get("supplier_name") or "").strip() or None
                if not s_id and not s_name:
                    errors.append(f"{label}: suppliers[{j}] requiere supplier_id o supplier_name")
                    continue
                if s_id:
                    supplier_ids.add(s_id)
                is_sel = bool(_bool_or_none(s.get("is_selected")))
                selected += 1 if is_sel else 0
                suppliers.append({
                    "position": pos, "supplier_id": s_id, "supplier_name": s_name, "unit_price": s_price,
                    "currency": s_currency, "delivery_time": (s.get("delivery_time") or "").strip() or None,
                    "comments": (s.get("comments") or "").strip() or None, "is_selected": is_sel,
                })
            if selected > 1:
                errors.append(f"{label}: solo un proveedor puede ir is_selected")
        plan.append({
            "item_id": item_id, "delete": False,
            "cost": {
                "currency": currency, "unit_cost": unit_cost, "exchange_rate": rate, "unit_cost_mxn": mxn,
                "profit_pct": pct, "unit_price_profit": price,
                "delivery_time": (cost_in.get("delivery_time") or "").strip() or None,
                "service_months": service_months, "smart_account": smart_account,
            },
            "suppliers": suppliers if suppliers_in is not None else None,
        })
    names = {}
    if supplier_ids:
        flag, error, names = get_supplier_names(sorted(supplier_ids), data_token)
        if not flag:
            errors.append(f"no se pudieron validar los proveedores: {error}")
        else:
            for s_id in sorted(supplier_ids - set(names)):
                errors.append(f"supplier_id {s_id} no existe en el catálogo")
    if errors:
        return {"data": None, "msg": "Análisis de costos inválido", "error": errors}, 400

    # --- Escribir ---------------------------------------------------------------------------
    write_errors = []
    out_items = []
    apply_prices = bool(data.get("apply_prices"))
    for step in plan:
        item_id = step["item_id"]
        if step["delete"]:
            flag, error, _ = delete_supplier_quotes_by_item(item_id, data_token)
            flag2, error2, _ = delete_cost_by_item(item_id, data_token)
            if not flag or not flag2:
                write_errors.append(f"partida {item_id}: no se pudo borrar ({error or error2})")
            else:
                out_items.append({"id": item_id, "deleted": True})
            continue
        cost = step["cost"]
        prev = existing.get(item_id) or {}
        history = list(prev.get("history") or [])
        changes = [
            {"field": k, "before": prev.get(k), "after": _json_safe(cost.get(k))}
            for k in ("currency", "unit_cost", "exchange_rate", "profit_pct", "delivery_time", "service_months", "smart_account")
            if str(prev.get(k) if prev.get(k) is not None else "") != str(_json_safe(cost.get(k)) if cost.get(k) is not None else "")
        ]
        history.append({"user": user, "action": "Actualización" if prev.get("id_cost") else "Creación", "date": timestamp,
                        "comment": "Análisis de costos de la partida.", "changes": changes})
        payload = {**{k: (str(v) if isinstance(v, Decimal) else v) for k, v in cost.items()},
                   "quotation_item_id": item_id, "quotation_id": id_quotation, "created_by": user,
                   "timestamp": timestamp, "history": history, "extra_info": prev.get("extra_info") or {}}
        if prev.get("id_cost"):
            flag, error, _ = update_cost(int(prev["id_cost"]), payload, data_token)
            id_cost = int(prev["id_cost"])
        else:
            flag, error, id_cost = insert_cost(payload, data_token)
        if not flag:
            write_errors.append(f"partida {item_id}: no se pudo guardar el costo ({error})")
            continue
        if step["suppliers"] is not None:
            flag, error, _ = delete_supplier_quotes_by_item(item_id, data_token)
            if not flag:
                write_errors.append(f"partida {item_id}: no se pudo reemplazar la comparativa ({error})")
            for s in step["suppliers"]:
                s_payload = {**s, "quotation_item_id": item_id,
                             "unit_price": str(s["unit_price"]) if s["unit_price"] is not None else None,
                             "supplier_name": s["supplier_name"] or names.get(s["supplier_id"] or 0)}
                flag, error, _ = insert_supplier_quote(s_payload, data_token)
                if not flag:
                    write_errors.append(f"partida {item_id}: proveedor {s['position']} no guardado ({error})")
        applied_price = None
        if apply_prices and cost["unit_price_profit"] is not None:
            applied_price = float(cost["unit_price_profit"].quantize(_Q2))
            flag, error, _ = update_quotation_item_price(item_id, id_quotation, applied_price, data_token)
            if not flag:
                write_errors.append(f"partida {item_id}: no se pudo aplicar price_unit ({error})")
                applied_price = None
        out_items.append({
            "id": item_id, "id_cost": id_cost, "partida": items_by_id[item_id].get("partida"),
            "currency": cost["currency"], "unit_cost": _f(cost["unit_cost"]), "exchange_rate": _f(cost["exchange_rate"]),
            "unit_cost_mxn": _f(cost["unit_cost_mxn"]), "profit_pct": _f(cost["profit_pct"]),
            "unit_price_profit": _f(cost["unit_price_profit"]), "applied_price_unit": applied_price,
            "suppliers_count": len(step["suppliers"]) if step["suppliers"] is not None else len(prev.get("suppliers") or []),
        })

    # Cabecera: tipo de cambio de referencia en metadata (merge, sin tocar items).
    if data.get("exchange_rate") is not None and header_rate is not None:
        if str(metadata.get("exchange_rate")) != str(float(header_rate)):
            metadata["exchange_rate"] = float(header_rate)
            if timestamps is not None and not isinstance(timestamps.get("update"), list):
                timestamps["update"] = []
            flag, error, _ = update_quotation(id_quotation, metadata, data_token, timestamps)
            if not flag:
                write_errors.append(f"no se pudo guardar exchange_rate en la cotización ({error})")

    costs_now, _t, _e = get_quotation_costs_map(id_quotation, data_token)
    totals = costs_totals(list(items_by_id.values()), costs_now)
    msg = f"Análisis de costos guardado en la cotización {id_quotation}: {len(out_items)} partida(s)" + (" (precios aplicados)" if apply_prices else "")
    write_log_file(log_file_admin, msg + (f" | parciales: {write_errors}" if write_errors else ""), data_token)
    return {
        "data": {"id_quotation": id_quotation, "exchange_rate": _f(header_rate), "items": out_items, "totals": totals},
        "msg": msg,
        "error": write_errors or None,
    }, 200
