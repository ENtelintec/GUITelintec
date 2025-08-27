# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 26/ago/2025  at 15:30 $"

import textwrap

from reportlab.pdfgen import canvas

from static.constants import filepath_v_pdf
from templates.forms.PDFGenerator import a4_x, a4_y, create_header_telintec


dict_types = {
    "0": {"label": "Vale de EPP", "value": 5},
    "1": {"label": "Vale de Equipo y Herramienta", "value": 6},
}

dict_signings_voucher = {
    "0": {
        "labels": [
            "Empleado Solicitante: ",
            "Empleado de Seguridad: ",
            "Empleado de Almacen: ",
        ],
        "keys": ["user", "epp_emp", "storage_emp"],
    },
    "1": {
        "labels": [
            "Empleado Solicitante: ",
            "Superior a cargo:  ",
            "Empleado de Almacen: ",
        ],
        "keys": ["user", "superior", "storage_emp"],
    },
}

dict_wrappers_headers = {
    "voucher": {
        "Item": {10: 7, 8: 9},
        "Cantidad": {10: 10, 8: 12},
        "UDM": {10: 4, 8: 5},
        "Descripción": {10: 30, 8: 38},
        "Obervaciones": {10: 12, 8: 13},
        "ID Almacen": {10: 10, 8: 12},
    },
}


def calculate_last_y(item, y_limit, font_size, y_position, type_form="voucher"):
    headers = list(dict_wrappers_headers[type_form].keys())
    for index, key in enumerate(item):
        value = textwrap.wrap(
            str(key), width=dict_wrappers_headers[type_form][headers[index]][font_size]
        )
        y_hat = y_position - font_size * len(value) * 1.5
        if y_hat < y_limit:
            return True
    return False


def print_metadata(pdf, metadata, font_size=10, y_init=480, columns=2):
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
    for key in metadata:
        if count >= columns:
            count = 0
            y_position -= font_size * 1.5
            x_position = 20
        # pdf.drawString(x_position, y_position, f"{key}: {metadata[key]}")
        # Configurar la fuente en negrita para el key
        pdf.setFont("Courier-Bold", font_size)
        pdf.drawString(x_position, y_position, f"{key}: ")

        # Restaurar la fuente normal para el valor
        pdf.setFont("Courier", font_size)
        pdf.drawString(
            x_position + len(key) * font_size * 0.7, y_position, f"{metadata[key]}"
        )
        x_position += separation
        count += 1
    return y_position - font_size * 2.5


def print_headers_table_inventory(pdf, font_size=10, y_init=500, type_form="voucher"):
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
        if calculate_last_y(item, limit_y, font_size, y_init, type_form="voucher"):
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            pages += 1
            print_headers_table_inventory(pdf, y_init=535, type_form="voucher")
            y_init = 510
            last_y = y_init
            pdf.setFont("Courier", font_size)
        for index, key in enumerate(item):
            value = textwrap.wrap(
                str(key),
                width=dict_wrappers_headers["voucher"][headers[index]][font_size],
            )
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += (
                font_size
                * dict_wrappers_headers["voucher"][headers[index]][font_size]
                * 0.8
            )
    return last_y - font_size * 1.5, pages


def print_footer_page_count(pdf, page, font_size=6, right_text="", x_max=a4_x):
    """
    :param x_max:
    :param right_text:
    :param pdf:
    :param page:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier", font_size)
    pdf.drawString(5, 5, f"Página {page}")
    if right_text != "":
        pdf.drawString(x_max - len(right_text) * font_size * 0.7, 5, right_text)


def print_footer_signing(
    pdf,
    emp_names,
    font_size=10,
    y_position=50.0,
    margin_bottom=75.0,
    y_max=a4_y,
    pages=1,
    type_voucher="0",
):
    """
    Función para imprimir un footer en un PDF, creando una nueva página si no hay suficiente espacio.

    :param emp_names:
    :param type_voucher:
    :param pages:
    :param y_max: tamaño pagina y
    :param pdf: Objeto canvas de ReportLab.
    :param font_size: Tamaño de fuente.
    :param y_position: Posición Y en la página.
    :param margin_bottom: Margen mínimo antes de generar una nueva página.
    """
    # Si el espacio es insuficiente, generar una nueva página
    if y_position < margin_bottom:
        print_footer_page_count(pdf, pages)
        pdf.showPage()  # Crear nueva página
        y_position = y_max - 100  # Reiniciar la posición más arriba en la nueva página
        pages += 1
    else:
        y_position = margin_bottom
    pdf.setFont("Courier-Bold", font_size)
    x_start = 20
    # Imprimir etiquetas con líneas en blanco para rellenar
    labels = dict_signings_voucher.get(type_voucher, {}).get("labels", [])

    for i in range(len(labels)):
        # draw signin title
        pdf.drawString(x_start, y_position, labels[i])
        # draw signin name
        current_name = emp_names.get(
            dict_signings_voucher.get(type_voucher, {}).get("keys", [""])[i], ""
        )
        print(dict_signings_voucher.get(type_voucher, {}).get("keys", [""])[i])
        pdf.drawString(
            x_start + len(labels[i]) * font_size * 0.7, y_position, current_name
        )
        y_position -= font_size * 2.5
    return y_position - font_size * 2.5, pages


def FileVoucherPDF(dict_data: dict):
    """
    :param dict_data:
    :return:
    """
    file_name = (
        filepath_v_pdf
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )
    x_max = a4_x
    y_max = a4_y
    pdf = canvas.Canvas(file_name, pagesize=(x_max, y_max))
    pdf.setTitle("SOLICITUD DE MATERIAL")
    products = dict_data["items"]
    folio = dict_data.get("metadata", {}).get("Folio", "")
    create_header_telintec(
        pdf,
        title=dict_types.get(
            str(dict_data.get("type", 0)), {"label": "Vale de EPP"}
        ).get("label"),
        page_x=x_max,
        iso_form=dict_types.get(str(dict_data.get("type", 0)), {"value": 5}).get(
            "value"
        ),
        orientation="vertical",
        offset_title=(-18, 0),
    )
    pages = 1
    # ----------------------------------------Metadata---------------------------------------------------------------
    y_last_metada = print_metadata(pdf, dict_data["metadata"], y_init=740)
    # ----------------------------------------header table of products-----------------------------------------------
    y_last_headers = print_headers_table_inventory(
        pdf, type_form="voucher", y_init=y_last_metada
    )
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers["voucher"].keys())
    font_size = 8
    y_last_products, pages = print_products_list(
        pdf, products, headers, font_size, y_last_headers, pages
    )
    emp_names = {
        "user": dict_data.get("metadata", {}).get("Usuario", ""),
        "epp_emp": dict_data.get("metadata", {}).get("Empleado EPP", ""),
        "storage_emp": dict_data.get("metadata", {}).get("Empleado Almacen", ""),
        "superior": dict_data.get("metadata", {}).get("Superior", ""),
    }
    y_last_signs, pages = print_footer_signing(
        pdf, emp_names, font_size, y_last_products, pages=pages, y_max=y_max
    )
    print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=x_max)
    pdf.save()
    return True
