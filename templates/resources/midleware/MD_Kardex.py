# -*- coding: utf-8 -*-
"""Kardex acotado por fecha (docs/almacen_kardex_ventana.md).

Ventana compartida por `GET /almacen/kardex`, `GET /almacen/kardex/epp` y
`GET /sucursal/movements/<type_m>`: sin `date_from` se devuelven los últimos
`KARDEX_DEFAULT_MONTHS` meses calendario (anclados en `date_to` si viene, si
no en hoy); histórico más antiguo solo con `date_from` explícito; nunca más
de `KARDEX_MAX_LIMIT` filas por llamada. La respuesta normaliza el producto
fuera de cada movimiento (`data.movements` + `data.products`) y agrega
`meta` con la ventana aplicada y si el tope recortó.

Los tres GET responden con ETag débil + 304 (`kardex_conditional`,
docs/almacen_kardex_etag.md).
"""
__author__ = "Edisson Naula"
__date__ = "$ 12/oct/2026  at 12:30 $"

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta
from werkzeug.datastructures import ETags
from werkzeug.http import quote_etag

from static.constants import format_date, format_timestamps, timezone_software
from templates.controllers.product.movements_controller import get_kardex_main_db

KARDEX_DEFAULT_MONTHS = 3
KARDEX_MAX_LIMIT = 5000
MOVEMENT_TYPES = ("entrada", "salida")


def _parse_day(raw, field) -> tuple[date | None, str | None]:
    """'YYYY-MM-DD' -> date | None. (None, msg) si viene mal formada."""
    raw = (raw or "").strip() if isinstance(raw, str) else raw
    if not raw:
        return None, None
    try:
        return datetime.strptime(raw, format_date).date(), None
    except (TypeError, ValueError):
        return None, f"{field} inválida: {raw!r} (formato YYYY-MM-DD)"


@dataclass
class KardexWindow:
    date_from: date  # siempre resuelta (explícita o por defecto)
    date_to: date | None
    is_default: bool  # date_from no vino: ventana de KARDEX_DEFAULT_MONTHS
    limit: int  # 1..KARDEX_MAX_LIMIT

    @property
    def sql_from(self) -> datetime:
        return datetime.combine(self.date_from, datetime.min.time())

    @property
    def sql_to_exclusive(self) -> datetime | None:
        """00:00:00 del día siguiente a date_to (cota exclusiva, usa índice)."""
        if self.date_to is None:
            return None
        return datetime.combine(self.date_to + timedelta(days=1), datetime.min.time())


def resolve_kardex_window(params: dict) -> tuple[KardexWindow | None, str | None]:
    """-> (window, None) | (None, msg_error) a partir de los query params
    `date_from`, `date_to`, `limit` (strings o None)."""
    date_from, err = _parse_day(params.get("date_from"), "date_from")
    if err:
        return None, err
    date_to, err = _parse_day(params.get("date_to"), "date_to")
    if err:
        return None, err
    is_default = date_from is None
    if date_from is None:
        anchor = date_to or datetime.now(pytz.timezone(timezone_software)).date()
        # relativedelta devuelve date al restarse de un date (los stubs no lo saben)
        date_from = anchor - relativedelta(months=KARDEX_DEFAULT_MONTHS)  # pyrefly: ignore
        assert isinstance(date_from, date)
    if date_to is not None and date_from > date_to:
        return None, f"date_from ({date_from}) es posterior a date_to ({date_to})"
    raw_limit = params.get("limit")
    try:
        limit = int(raw_limit) if raw_limit not in (None, "") else KARDEX_MAX_LIMIT
    except (TypeError, ValueError):
        return None, f"limit inválido: {raw_limit!r}"
    limit = max(1, min(limit, KARDEX_MAX_LIMIT))
    return KardexWindow(date_from=date_from, date_to=date_to, is_default=is_default, limit=limit), None


def kardex_meta(window: KardexWindow, rows: list) -> tuple[list, dict]:
    """La BD se consulta con `limit + 1`: si vuelve una fila de más, hubo
    recorte. -> (rows recortadas a limit, meta)."""
    truncated = len(rows) > window.limit
    rows = rows[: window.limit]
    meta = {
        "date_from": window.date_from.strftime(format_date),
        "date_to": window.date_to.strftime(format_date) if window.date_to else None,
        "default_window": window.is_default,
        "limit": window.limit,
        "count": len(rows),
        "truncated": truncated,
    }
    return rows, meta


def kardex_conditional(data_out: dict, code: int, if_none_match: ETags) -> tuple:
    """P-128: ETag débil (`W/`) con la huella del cuerpo + `Cache-Control:
    private, no-cache`. Sin DDL y siempre exacto; la consulta se sigue
    haciendo, pero un refresco sin cambios responde 304 sin cuerpo (werkzeug
    quita el cuerpo y los Content-* de los 304). `if_none_match` =
    `request.if_none_match`. Solo los 200 llevan ETag.
    -> (body, code, headers) listo para devolver desde el Resource."""
    if code != 200:
        return data_out, code, {}
    body = json.dumps(data_out, separators=(",", ":"), default=str).encode()
    digest = hashlib.blake2b(body, digest_size=16).hexdigest()
    headers = {"ETag": quote_etag(digest, weak=True), "Cache-Control": "private, no-cache"}
    if if_none_match.contains_weak(digest):
        return None, 304, headers
    return data_out, code, headers


def _sku_fabricante(codes_raw) -> str:
    try:
        codes = json.loads(codes_raw) if codes_raw else []
    except (TypeError, ValueError):
        return ""
    for code in codes if isinstance(codes, list) else []:
        if isinstance(code, dict) and code.get("tag") == "sku_fabricante":
            return code.get("value") or ""
    return ""


def get_kardex_api(type_m, params: dict, data_token, epp=False):
    """GET /almacen/kardex[/epp]?type_m=&date_from=&date_to=&limit=.
    Mismos campos por movimiento que `GET /movements/<type_m>` menos los del
    producto (`sku`, `supplier`, `sku_fabricante`, `description`), que van
    una sola vez por `id_product` en `data.products`."""
    type_m = (type_m or "all").strip().lower()
    if type_m not in MOVEMENT_TYPES + ("all",):
        return {"data": None, "msg": f"type_m inválido: {type_m!r} (entrada | salida | all)", "error": None}, 400
    window, err = resolve_kardex_window(params)
    if window is None:
        return {"data": None, "msg": err, "error": None}, 400
    flag, error, rows = get_kardex_main_db(
        type_m if type_m in MOVEMENT_TYPES else "%",
        window.sql_from,
        window.sql_to_exclusive,
        window.limit + 1,
        data_token,
        epp=epp,
    )
    if not flag:
        return {"data": None, "msg": "No se pudieron obtener los movimientos", "error": error}, 400
    rows, meta = kardex_meta(window, rows if isinstance(rows, list) else [])
    movements = []
    products: dict = {}
    for (id_m, id_product, mtype, quantity, movement_date, sm_id, reference, sku, supplier, codes, name) in rows:
        movements.append(
            {
                "id": id_m,
                "id_product": id_product,
                "type_m": mtype,
                "quantity": quantity,
                "movement_date": movement_date.strftime(format_timestamps) if movement_date else None,
                "sm_id": sm_id,
                "reference": json.loads(reference) if reference is not None else None,
            }
        )
        if id_product not in products:
            products[id_product] = {
                "sku": sku,
                "supplier": supplier,
                "sku_fabricante": _sku_fabricante(codes),
                "description": name,
            }
    return {
        "data": {"movements": movements, "products": products},
        "meta": meta,
        "msg": f"{len(movements)} movimientos del {meta['date_from']} al {meta['date_to'] or 'hoy'}"
        + (" (recortado al tope)" if meta["truncated"] else ""),
        "error": None,
    }, 200
