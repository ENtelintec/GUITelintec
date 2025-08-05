# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jun/2025  at 16:27 $"

import math
import textwrap

from reportlab.pdfgen import canvas

from static.constants import filepath_po_pdf
from templates.forms.PDFGenerator import (
    a4_x,
    a4_y,
    create_header,
    print_footer_page_count,
)

dict_wrappers_headers = {
    "PO": {
        "Item": {10: 7, 8: 9},
        "Descripción": {10: 16, 8: 20},
        "Nro Parte": {10: 6, 8: 8},
        "Duracion Servicio (Meses)": {10: 8, 8: 10},
        "Tiempo de entrega": {10: 7, 8: 9},
        "Cantidad": {10: 8, 8: 10},
        "Precio Unitario": {10: 10, 8: 12},
        "Sub Total": {10: 10, 8: 12},
    },
}


def print_metadata_po(pdf, metadata, font_size=10, y_init=480, columns=2):
    """
    :param pdf:
    :param metadata:
    :param font_size:
    :param y_init:
    :param columns:
    :return:
    """
    pdf.setFont("Courier", font_size)
    y_position = y_init
    x_position = 20
    separation = a4_x / columns
    count = 0
    width_text_colum = int(separation / font_size)
    for key in metadata:
        if count >= columns:
            count = 0
            y_position -= font_size * 1.2
            x_position = 20
        # pdf.drawString(x_position, y_position, f"{key}: {metadata[key]}")
        # Configurar la fuente en negrita para el key
        pdf.setFont("Courier-Bold", font_size)
        pdf.drawString(x_position, y_position, f"{key}:")

        # Restaurar la fuente normal para el valor
        pdf.setFont("Courier", font_size)
        content = textwrap.wrap(
            str(metadata[key]),
            width=width_text_colum,
        )
        adjustment = 15 / math.sqrt(len(key) + 1)
        for letter in content:
            pdf.drawString(
                x_position + len(key) * font_size * 0.63 + adjustment,
                y_position,
                f"{letter}",
            )
            y_position -= font_size
        # pdf.drawString(
        #     x_position + len(key) * font_size * 0.7, y_position, f"{metadata[key]}"
        # )
        x_position += separation
        count += 1
    return y_position - font_size * 2.5


def print_headers_table_po(pdf, font_size=10, y_init=500, type_form="PO"):
    """
    :param type_form:
    :param y_init:
    :param pdf:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier-Bold", font_size)
    x_position = 20
    headers = list(dict_wrappers_headers[type_form].keys())
    for header_key in headers:
        header = textwrap.wrap(
            header_key, width=dict_wrappers_headers[type_form][header_key][font_size]
        )
        y_position = y_init
        for letter in header:
            pdf.drawString(x_position, y_position, letter)
            y_position -= font_size
        # pdf.drawString(x_position, y_position, header)
        x_position += (
            font_size * dict_wrappers_headers[type_form][header_key][font_size] * 0.8
        )
    return y_init - font_size * 1.5


def print_products_list(
    pdf, products, headers, font_size=8, y_last_headers=500.0, pages=1
):
    pdf.setFont("Courier", font_size)
    y_init = y_last_headers
    last_y = y_init
    limit_y = 10
    for index_products, item in enumerate(products):
        x_position = 20
        y_init = last_y
        if calculate_last_y(item, limit_y, font_size, y_init, type_form="PO"):
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            pages += 1
            print_headers_table_po(pdf, y_init=535, type_form="PO")
            y_init = 510
            last_y = y_init
            pdf.setFont("Courier", font_size)
        # draw a line to separe
        pdf.line(20, y_init - 2, a4_x - 20, y_init - 2)
        for index, value_text in enumerate(item):
            value = textwrap.wrap(
                str(value_text),
                width=dict_wrappers_headers["PO"][headers[index]][font_size],
            )
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += (
                font_size * dict_wrappers_headers["PO"][headers[index]][font_size] * 0.8
            )
        # draw a line to separe
        pdf.line(20, last_y - 2, a4_x - 20, last_y - 2)
    return last_y - font_size * 1.5, pages


def print_total_products(
    pdf,
    font_size=10,
    y_last_products=500,
    pages=1,
    y_max=800,
    subtotal=0.0,
    iva=0.0,
    total=0.0,
):
    pdf.setFont("Courier-Bold", font_size)
    y_init = y_last_products
    y_position = y_init
    if y_position - 20 < 0:
        print_footer_page_count(pdf, pages)
        pdf.showPage()
        pages += 1
        y_position = y_max - 20
    # subtoital
    pdf.drawString(a4_x - 170, y_position - 10, "Sub Total")
    pdf.drawString(a4_x - 100, y_position - 10, f"{subtotal:.2f}")
    # iva
    pdf.drawString(a4_x - 170, y_position - 20, "IVA (16%)")
    pdf.drawString(a4_x - 100, y_position - 20, f"{iva:.2f}")
    # total
    pdf.drawString(a4_x - 170, y_position - 30, "Total")
    pdf.drawString(a4_x - 100, y_position - 30, f"{total:.2f}")
    return y_position - font_size * 1.5, pages


def calculate_last_y(item, y_limit, font_size, y_position, type_form="Movements"):
    headers = list(dict_wrappers_headers[type_form].keys())
    for index, key in enumerate(item):
        value = textwrap.wrap(
            str(key), width=dict_wrappers_headers[type_form][headers[index]][font_size]
        )
        y_hat = y_position - font_size * len(value) * 1.5
        if y_hat < y_limit:
            return True
    return False


def FilePoPDF(dict_data: dict):
    """
    :param dict_data:
    :return:
    """

    file_name = (
        filepath_po_pdf
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )
    x_max = a4_x
    y_max = a4_y
    pdf = canvas.Canvas(file_name, pagesize=(x_max, y_max))
    pdf.setTitle("Orden de Compra")
    products = dict_data["products"]
    folio = dict_data.get("Folio", "")
    create_header(
        pdf,
        title="Orden de Compra",
        page_x=x_max,
        iso_form=4,
        orientation="vertical",
        offset_title=(-18, 0),
    )
    pages = 1
    # ----------------------------------------Metadata---------------------------------------------------------------
    y_last_metada = print_metadata_po(
        pdf, dict_data.get("metadata_telintec", {}), y_init=740, columns=1
    )
    y_last_metada = print_metadata_po(
        pdf,
        dict_data.get("metadata_supplier", {}),
        y_init=y_last_metada - 20,
        columns=1,
    )
    # ----------------------------------------header table of products-----------------------------------------------
    y_last_headers = print_headers_table_po(pdf, type_form="PO", y_init=y_last_metada)
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers["PO"].keys())
    font_size = 8
    y_last_products, pages = print_products_list(
        pdf, products, headers, font_size, y_last_headers - font_size * 0.75, pages
    )
    font_size = 10
    sub_total = dict_data.get("total_amount", 0.0)
    iva = sub_total * 0.16
    total = sub_total + iva
    y_last_signs, pages = print_total_products(
        pdf,
        font_size,
        y_last_products,
        pages=pages,
        y_max=int(y_max),
        subtotal=sub_total,
        iva=iva,
        total=total,
    )
    print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=x_max)
    pdf.save()
    return True
