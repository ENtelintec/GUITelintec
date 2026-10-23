# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct./2026  at 21:10 $"

"""Cotizaciones CISCO (FO-PRE-02): envoltorios delgados de /quotation/cisco/*
sobre el midleware de cotizaciones. Ver docs/cotizaciones_cisco.md.

Reglas:
  * Mismas tablas: quotations.metadata.format = "cisco", separado de
    document_type (una CISCO se convierte en OCD con PUT /quotation/ocd sin
    perder formato) y los campos CISCO de la partida en quotation_items.extra_info
    (item, smart_account, service_months, delivery_time). n_parte va a la
    columna n_part y partida se deriva del orden del payload.
  * Validacion en lista (400) antes de escribir: concept obligatorio,
    limit_date >= emission, item entero o con un nivel decimal y unico, n_parte y
    description obligatorios, quantity > 0, price_unit >= 0, service_months > 0
    o null, al menos una partida viva.
  * quotation_code SIN candado (como preventa; el 409 es solo de OCD). Folio
    sugerido COT-CISCO-AAAA-NNN (GET /quotation/folio?format=cisco).
  * GET /quotation/-1 no las devuelve por default (?format=cisco las pide;
    ?document_type=ocd si las trae cuando ya son OCD).
  * PDF FO-PRE-02 (GET /quotation/cisco/download/pdf/<id>): docs/cotizacion_cisco_pdf.md.
"""
import os
import re
import tempfile
from datetime import date, datetime

from werkzeug.utils import secure_filename

from static.constants import format_date
from templates.controllers.employees.employees_controller import get_employee_info
from templates.forms.QuotationCiscoForms import FileQuotationCiscoPDF
from templates.resources.methods.Functions_Aux_RH import split_emails
from templates.resources.midleware.Functions_midleware_admin import (
    create_quotation_from_api,
    get_quotations,
    update_quoation_from_api,
)

QUOTATION_FORMAT_CISCO = "cisco"
CISCO_ITEM_RE = re.compile(r"^\d+(\.\d+)?$")


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], format_date).date()
    except ValueError:
        return None


def cisco_header_errors(metadata: dict) -> list:
    errors = []
    if not str(metadata.get("concept") or "").strip():
        errors.append("concept es obligatorio")
    emission, limit = _to_date(metadata.get("emission")), _to_date(metadata.get("limit_date"))
    if emission and limit and limit < emission:
        errors.append(f"limit_date ({limit.isoformat()}) no puede ser anterior a emission ({emission.isoformat()})")
    return errors


def cisco_items_errors(products: list) -> list:
    """Valida las partidas vivas (is_erased != 1) del payload; una lista de strings para el 400."""
    errors = []
    seen = {}
    active = [p for p in products if p.get("is_erased") != 1]
    if not active:
        errors.append("la cotización necesita al menos una partida")
    for index, p in enumerate(active, start=1):
        label = f"partida {index}"
        item = str(p.get("item") or "").strip()
        if not CISCO_ITEM_RE.match(item):
            errors.append(f"{label}: item '{item}' debe ser un entero o con un nivel decimal (1, 1.1, 2)")
        elif item in seen:
            errors.append(f"{label}: item '{item}' repetido (partida {seen[item]})")
        else:
            seen[item] = index
        if not str(p.get("n_parte") or "").strip():
            errors.append(f"{label}: n_parte es obligatorio")
        if not str(p.get("description") or "").strip():
            errors.append(f"{label}: description es obligatoria")
        quantity = p.get("quantity")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            errors.append(f"{label}: quantity debe ser un entero mayor a 0")
        price = p.get("price_unit")
        if price is None or float(price) < 0:
            errors.append(f"{label}: price_unit debe ser mayor o igual a 0")
        months = p.get("service_months")
        if months is not None and (not isinstance(months, int) or isinstance(months, bool) or months <= 0):
            errors.append(f"{label}: service_months debe ser un entero mayor a 0 o null")
    return errors


def _cisco_to_standard(products: list) -> list:
    """Partidas CISCO -> items del midleware de cotizaciones: partida = orden entre
    las vivas, n_parte -> n_part, udm PZA si no viene; las llaves CISCO viajan en
    el dict y _item_quotation_values las guarda en extra_info."""
    out, number = [], 0
    for p in products:
        erased = p.get("is_erased") == 1
        if not erased:
            number += 1
        out.append(
            {
                "qa_item_id": p.get("qa_item_id"),
                "partida": number if not erased else 0,
                "udm": str(p.get("udm") or "").strip() or "PZA",
                "n_parte": str(p.get("n_parte") or "").strip(),
                "description": str(p.get("description") or "").strip(),
                "quantity": p.get("quantity"),
                "price_unit": p.get("price_unit"),
                "delivery_date": p.get("delivery_date") or "",
                "is_erased": 1 if erased else 0,
                "item": str(p.get("item") or "").strip(),
                "smart_account": bool(p.get("smart_account")),
                "service_months": p.get("service_months"),
                "delivery_time": str(p.get("delivery_time") or "").strip(),
            }
        )
    return out


def _products_out(products: list) -> list:
    """Salida CISCO: n_parte, item (fallback a la partida), smart_account bool,
    total por partida; ordenadas por partida y sin la fila vacía del LEFT JOIN."""
    out = []
    for p in sorted(products, key=lambda x: int(x.get("partida") or 0)):
        if not p.get("qa_item_id"):
            continue
        q = dict(p)
        q["n_parte"] = p.get("n_part") or ""
        q["item"] = p.get("item") or str(p.get("partida") or "")
        q["smart_account"] = bool(p.get("smart_account"))
        q["service_months"] = p.get("service_months")
        q["delivery_time"] = p.get("delivery_time") or ""
        q["total"] = round(float(p.get("quantity") or 0) * float(p.get("price_unit") or 0), 2)
        out.append(q)
    return out


def get_quotations_cisco_api(id_q, data_token):
    """GET /quotation/cisco/-1 y /quotation/cisco/<id>: solo format = cisco (404 si no lo es)."""
    data_out, code = get_quotations(data_token, id_q, fmt=QUOTATION_FORMAT_CISCO)
    entries = data_out.get("data") if code == 200 else None
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            raw_products = entry.get("products")
            products = _products_out(raw_products if isinstance(raw_products, list) else [])
            entry["products"] = products
            entry["total"] = round(sum(p["total"] for p in products), 2)
    return data_out, code


def create_quotation_cisco_api(data, data_token):
    errors = cisco_header_errors(data["metadata"]) + cisco_items_errors(data["products"])
    if errors:
        return {"data": None, "msg": "Cotización CISCO inválida", "error": errors}, 400
    data["metadata"]["format"] = QUOTATION_FORMAT_CISCO
    data["products"] = _cisco_to_standard(data["products"])
    return create_quotation_from_api(data, data_token)


def update_quotation_cisco_api(data, data_token):
    errors = cisco_header_errors(data["metadata"]) + cisco_items_errors(data["products"])
    if errors:
        return {"data": None, "msg": "Cotización CISCO inválida", "error": errors}, 400
    data["metadata"]["format"] = QUOTATION_FORMAT_CISCO
    data["products"] = _cisco_to_standard(data["products"])
    return update_quoation_from_api(data, data_token, fmt=QUOTATION_FORMAT_CISCO)


def _telintec_contact(emp_id, data_token) -> tuple[str, str, str]:
    """(nombre, teléfono, correo) del empleado que capturó la cotización; vacíos
    si no hay emp_id o no existe. Correo: el institucional si tiene varios."""
    try:
        emp_id = int(emp_id or 0)
    except (TypeError, ValueError):
        return "", "", ""
    if emp_id <= 0:
        return "", "", ""
    flag, _error, row, _cols = get_employee_info(emp_id, data_token)
    if not flag or not isinstance(row, tuple) or len(row) < 8:
        return "", "", ""
    name = " ".join(str(part).strip() for part in (row[1], row[2]) if part)
    emails = split_emails(row[7])
    institutional = [e for e in emails if e.lower().endswith("@telintec.com.mx")]
    email = (institutional or emails or [""])[0]
    return name.title(), str(row[6] or "").strip(), email


def download_quotation_cisco_pdf(id_q: int, data_token):
    """PDF FO-PRE-02 de una cotización CISCO: (ruta, 200) o (envelope, 4xx).
    404 si no existe o no es CISCO (mismo criterio que GET /quotation/cisco/<id>)."""
    data_out, code = get_quotations_cisco_api(id_q, data_token)
    if code != 200:
        return data_out, code
    entries = data_out.get("data")
    entry = entries[0] if isinstance(entries, list) and entries and isinstance(entries[0], dict) else None
    if entry is None:
        return {"data": None, "msg": f"No se encontró la cotización CISCO (ID {id_q})", "error": "Quotation not found"}, 404
    metadata = entry.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    products = entry.get("products")
    contact_name, contact_phone, contact_email = _telintec_contact(metadata.get("emp_id"), data_token)
    code_q = str(metadata.get("quotation_code") or "")
    file_name = secure_filename(f"cotizacion_cisco_{code_q}_{id_q}.pdf") or f"cotizacion_cisco_{id_q}.pdf"
    download_path = os.path.join(tempfile.mkdtemp(), file_name)
    flag_pdf = FileQuotationCiscoPDF(
        {
            "filename_out": download_path,
            "quotation_code": code_q,
            "emission": str(metadata.get("emission") or "")[:10],
            "limit_date": str(metadata.get("limit_date") or "")[:10],
            "contact_name": contact_name,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "company": metadata.get("company") or "",
            "user": metadata.get("user") or "",
            "phone": metadata.get("phone") or "",
            "email": metadata.get("email") or "",
            "planta": metadata.get("planta") or "",
            "area": metadata.get("area") or "",
            "location": metadata.get("location") or "",
            "concept": metadata.get("concept") or "",
            "currency": metadata.get("currency") or "MXN",
            "delivery_time": metadata.get("delivery_time") or "",
            "products": products if isinstance(products, list) else [],
            "total": entry.get("total") or 0.0,
        }
    )
    if not flag_pdf:
        return {"data": None, "msg": "Error al generar el PDF de la cotización CISCO", "error": None}, 400
    return download_path, 200
