# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/jul/2026  at 17:30 $"

import textwrap

from reportlab.pdfgen import canvas

from static.constants import filepath_remission_pdf
from templates.forms.PDFGenerator import (
    a4_x,
    a4_y,
    create_footer_sign,
    create_header_telintec,
    print_footer_page_count,
)

# Bloque estático de la empresa (mismo para todas las remisiones); ver ejemplo en
# Docs/remission_pdf.md.
_COMPANY_INFO_LINES = [
    "TELINTEC SA DE CV",
    "RFC: TEL140211BD5",
    "Av. Lazaro Cardenas 306 1er piso oficina A-1",
    "Col. Residencial San Agustin",
    "San Pedro Garza Garcia, N.L., C.P. 66260",
    "Contacto: Carolina Torres y/o Georgina Saenz",
    "Tel.: 8121080577 - 8119647324",
    "E-Mail: admon01@telintec.com.mx",
    "   y/o georgina.saenz@telintec.com.mx",
    "Representante Legal: Omar Ugarte",
]

# Anclas de columna de la tabla de items (página vertical, ancho = a4_x).
_RM_X_POS = 45
_RM_X_DESC = 70
_RM_X_CANT = 360
_RM_X_UM = 395
_RM_X_PUNIT = 480
_RM_X_TOTAL = 565


def _draw_metadata_box(pdf, rows, x, y_top, width, font_size=9):
    """
    Dibuja el bloque de metadata (Remision Telintec, Proyecto, No. Contrato Marco,
    No. Pedido Exiros, No. Pedido, Remito) como una serie de filas con recuadro,
    etiqueta en negrita seguida del valor; filas con más de una línea (Proyecto)
    dejan las líneas extra debajo, sin repetir la etiqueta.

    :param rows: lista de tuplas (label, value) o (label, [linea1, linea2, ...])
    :return: y al terminar de dibujar el bloque
    """
    row_h = font_size * 1.6
    y = y_top
    for label, value in rows:
        lines = value if isinstance(value, list) else [str(value)]
        lines = lines if lines else [""]
        box_h = row_h * len(lines)
        pdf.rect(x, y - box_h, width, box_h, fill=0, stroke=1)
        label_y = y - font_size - 2
        pdf.setFont("Courier-Bold", font_size)
        pdf.drawString(x + 5, label_y, f"{label}:")
        pdf.setFont("Courier", font_size)
        pdf.drawString(x + 5 + (len(label) + 1) * font_size * 0.6 + 4, label_y, str(lines[0]))
        line_y = label_y - row_h
        for extra in lines[1:]:
            pdf.drawString(x + 5, line_y, str(extra))
            line_y -= row_h
        y -= box_h
    return y


def FileRemissionPDF(dict_data: dict):
    """
    Genera el PDF de una REMISIÓN (documento formal de un solo registro de
    ``activity_reports``, con header/logo Telintec, metadata de contrato/pedido,
    tabla de items y totales). Estructura esperada de ``dict_data``::

        {
            "filename_out": str,
            "folio": str,               # "Remision Telintec"
            "date": str,
            "project": str,
            "project_description": str,
            "contract_marco": str,      # contracts.code
            "pedido": str,
            "pedido_exiros": str,
            "remito": str,
            "items": [
                {"pos": str, "description": str, "udm": str, "quantity": float,
                 "unit_price": float, "line_total": float},
                ...
            ],
            "subtotal": float,
            "iva_rate": float,
            "iva": float,
            "total": float,
        }

    Más detalle del formato en ``docs/remission_pdf.md``.

    :param dict_data: datos de la remisión ya resueltos por el midleware
    :return: True si el PDF se generó correctamente
    """
    file_name = (
        filepath_remission_pdf if dict_data.get("filename_out") is None else dict_data["filename_out"]
    )
    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    pdf.setTitle("Remision")

    pages = 1
    font_size = 9
    limit_y = 60

    def draw_header_and_metadata():
        create_header_telintec(
            pdf,
            title="REMISIÓN",
            page_x=a4_x,
            iso_form=7,
            orientation="vertical",
            offset_title=(0, 0),
        )
        pdf.setFont("Courier", 8)
        text_y = 700.0
        for line in _COMPANY_INFO_LINES:
            pdf.drawString(30, text_y, line)
            text_y -= 8 * 1.4

        metadata_rows = [
            ("Fecha", dict_data.get("date", "")),
            ("Remision Telintec", dict_data.get("folio", "")),
            (
                "Proyecto",
                [
                    dict_data.get("project", ""),
                    *textwrap.wrap(dict_data.get("project_description", "") or "", width=38),
                ],
            ),
            ("No. Contrato Marco", dict_data.get("contract_marco", "")),
            ("No. Pedido Exiros", dict_data.get("pedido_exiros", "")),
            ("No. Pedido", dict_data.get("pedido", "")),
            ("Remito", dict_data.get("remito", "")),
        ]
        y_after_metadata = _draw_metadata_box(pdf, metadata_rows, 330, 700, a4_x - 330 - 25)
        return min(text_y, y_after_metadata) - 20

    def print_column_headers(y):
        pdf.setFillColorRGB(0.10, 0.45, 0.75)
        pdf.rect(25, y - 4, a4_x - 50, font_size + 6, fill=1, stroke=0)
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Courier-Bold", font_size - 1)
        pdf.drawString(_RM_X_POS, y, "POS.")
        pdf.drawString(_RM_X_DESC, y, "DESCRIPCION")
        pdf.drawRightString(_RM_X_CANT, y, "CANT.")
        pdf.drawString(_RM_X_UM, y, "UM")
        pdf.drawRightString(_RM_X_PUNIT, y, "PRECIO UNIT.")
        pdf.drawRightString(_RM_X_TOTAL, y, "TOTAL")
        pdf.setFillColorRGB(0, 0, 0)
        return y - font_size * 1.8

    def check_page_break(y, with_columns=False):
        nonlocal pages
        if y < limit_y:
            print_footer_page_count(pdf, pages, right_text=f"Folio: {dict_data.get('folio', '')}", x_max=a4_x)
            pdf.showPage()
            pages += 1
            y = draw_header_and_metadata()
            if with_columns:
                y = print_column_headers(y)
                pdf.setFont("Courier", font_size - 1)
            return y
        return y

    last_y = draw_header_and_metadata()
    last_y = print_column_headers(last_y)

    pdf.setFont("Courier", font_size - 1)
    items = dict_data.get("items", [])
    for item in items:
        last_y = check_page_break(last_y, with_columns=True)
        description_lines = textwrap.wrap(str(item.get("description", "")), width=42)
        quantity = item.get("quantity", 0) or 0
        unit_price = item.get("unit_price", 0) or 0
        line_total = item.get("line_total", 0) or 0
        row_y = last_y
        pdf.drawString(_RM_X_POS, row_y, str(item.get("pos", "") or ""))
        pdf.drawString(_RM_X_UM, row_y, str(item.get("udm", "") or ""))
        pdf.drawRightString(_RM_X_CANT, row_y, f"{quantity:g}")
        pdf.drawRightString(_RM_X_PUNIT, row_y, f"${unit_price:,.2f}")
        pdf.drawRightString(_RM_X_TOTAL, row_y, f"${line_total:,.2f}")
        for line in description_lines or [""]:
            pdf.drawString(_RM_X_DESC, last_y, line)
            last_y -= font_size * 1.3
        last_y -= font_size * 0.4
        pdf.setLineWidth(0.3)
        pdf.line(25, last_y + font_size * 0.9, a4_x - 25, last_y + font_size * 0.9)

    last_y = check_page_break(last_y - font_size)
    pdf.setFont("Courier-Bold", font_size)
    pdf.drawString(_RM_X_DESC, last_y, f"TOTAL POS. {len(items)}")
    pdf.drawRightString(_RM_X_TOTAL, last_y, f"SUBTOTAL ${dict_data.get('subtotal', 0.0):,.2f}")
    last_y -= font_size * 1.6
    iva_rate = dict_data.get("iva_rate", 0.16)
    pdf.drawRightString(_RM_X_TOTAL, last_y, f"IVA ({iva_rate:.0%}) ${dict_data.get('iva', 0.0):,.2f}")
    last_y -= font_size * 1.6
    pdf.drawRightString(_RM_X_TOTAL, last_y, f"TOTAL ${dict_data.get('total', 0.0):,.2f}")
    last_y -= font_size * 5

    last_y = check_page_break(last_y)
    create_footer_sign(pdf, 200, last_y, "Firma Autorizacion 1")
    last_y -= font_size * 4
    last_y = check_page_break(last_y)
    create_footer_sign(pdf, 200, last_y, "Firma Autorizacion 2")

    print_footer_page_count(pdf, pages, right_text=f"Folio: {dict_data.get('folio', '')}", x_max=a4_x)
    pdf.save()
    return True
