# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jul./2024  at 14:47 $"

import textwrap

from reportlab.pdfgen import canvas

from templates.forms.PDFGenerator import (
    a4_y,
    a4_x,
    create_header_materials,
    create_footer_sign,
    create_header_telintec,
    create_info_materials_request,
)

dict_wrappers_headers = {
    "ReturnMaterials": {
        "SM": {10: 4, 8: 5},
        "Material": {10: 15, 8: 18},
        "Motivo Devolución": {10: 39, 8: 50},
        "Cantidad": {10: 8, 8: 10},
        "UDM": {10: 4, 8: 5},
    },
    "MaterialsRequest": {
        "Item": {10: 4, 8: 5},
        "Descripción": {10: 32, 8: 40},
        "Cantidad Solicitada": {10: 10, 8: 13},
        "UDM": {10: 5, 8: 6},
        "Cantidad Suministrada": {10: 12, 8: 14},
        "Estado": {10: 10, 8: 12},
    },
}


def print_headers_table_inventory(
    pdf, font_size=10, y_init=635, type_form="ReturnMaterials"
):
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


def print_footer_page_count(pdf, page, font_size=6):
    """
    :param pdf:
    :param page:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier", font_size)
    pdf.drawString(5, 5, f"Página {page}")


def calculate_last_y(
    item, y_limit, font_size, y_position, type_form="Movements", width=None
):
    headers = list(dict_wrappers_headers[type_form].keys())
    print(headers, type_form, item)
    for index, key in enumerate(item):
        if width is None:
            value = textwrap.wrap(
                str(key),
                width=dict_wrappers_headers[type_form][headers[index]][font_size],
            )
        else:
            value = textwrap.wrap(str(key), width=width)
        y_hat = y_position - font_size * len(value) * 1.5
        if y_hat < y_limit:
            return True
    return False


def ReturnMaterialsForm(dict_data: dict, type_form="ReturnMaterials"):
    """
    :param type_form:
    :param dict_data:
    :return:
    """
    file_name = (
        "files/return_materials.pdf"
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )
    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    limit_y = 10
    pdf.setTitle("Devolucion de Materiales")
    products = dict_data["products"]
    create_header_materials(
        pdf,
        title="DEVOLUCION DE MATERIALES",
        page_x=a4_x,
        date_int=dict_data["date_emision"],
        type_form=3,
        info_dict=dict_data["info"],
    )
    pages = 0
    # ----------------------------------------header table of products-----------------------------------------------
    print_headers_table_inventory(pdf, type_form=type_form)
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers[type_form].keys())
    font_size = 8
    pdf.setFont("Courier", font_size)
    y_init = 620
    last_y = y_init
    for index_products, item in enumerate(products):
        x_position = 20
        y_init = last_y
        if calculate_last_y(item, limit_y, font_size, y_init, type_form=type_form):
            pages += 1
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            print_headers_table_inventory(pdf, y_init=780, type_form=type_form)
            y_init = 765
            last_y = y_init
            pdf.setFont("Courier", font_size)
        for index, key in enumerate(item):
            value = textwrap.wrap(
                str(key),
                width=dict_wrappers_headers[type_form][headers[index]][font_size],
            )
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += (
                font_size
                * dict_wrappers_headers[type_form][headers[index]][font_size]
                * 0.8
            )
    # --------------------------------------------------observaciones---------------------------------------------------------
    font_size = 10
    pdf.setFont("Courier-Bold", font_size)
    y_init = last_y - font_size * 1.5
    pdf.drawString(20, y_init, "Observaciones:")
    pdf.setFont("Courier", font_size)
    y_init = y_init - font_size * 1.5
    item = (dict_data["observations"],)
    if calculate_last_y(
        item,
        limit_y,
        font_size,
        y_init,
        type_form=type_form,
        width=int(a4_x / (font_size * 0.7)),
    ):
        pages += 1
        print_footer_page_count(pdf, pages)
        pdf.showPage()
        y_init = 780
    value = textwrap.wrap(
        str(dict_data["observations"]), width=int(a4_x / (font_size * 0.7))
    )
    for letter in value:
        pdf.drawString(20, y_init, letter)
        y_init -= font_size
    pages += 1
    print_footer_page_count(pdf, pages)
    if y_init < 40:
        pages += 1
        pdf.showPage()
        print_footer_page_count(pdf, pages)
        y_init = 780
    create_footer_sign(pdf, 80, 30, "Personal que devuelve")
    create_footer_sign(pdf, 400, 30, "Personal que recibe")
    pdf.save()
    return True


def MaterialsRequest(dict_data: dict, type_form="MaterialsRequest"):
    """
    :param type_form:
    :param dict_data:
    :return:
    """
    file_name = (
        "files/materials_request.pdf"
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )
    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    limit_y = 10
    pdf.setTitle("Solicitud de Material")
    products = dict_data["products"]
    create_header_telintec(
        pdf,
        title="SOLICITUD DE MATERIALES",
        page_x=a4_x,
        date_int="2023-06-14",
        iso_form=4,
    )
    create_info_materials_request(pdf, dict_data["info"], 20, 740)
    pages = 0
    # ----------------------------------------header table of products-----------------------------------------------
    y_init = 650
    print_headers_table_inventory(pdf, type_form=type_form, y_init=y_init)
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers[type_form].keys())
    print(headers, type_form)
    font_size = 8
    pdf.setFont("Courier", font_size)
    y_init = 640
    last_y = y_init
    for index_products, item in enumerate(products):
        x_position = 20
        y_init = last_y
        if calculate_last_y(item, limit_y, font_size, y_init, type_form=type_form):
            pages += 1
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            print_headers_table_inventory(pdf, y_init=780, type_form=type_form)
            y_init = 765
            last_y = y_init
            pdf.setFont("Courier", font_size)
        for index, key in enumerate(item):
            value = textwrap.wrap(
                str(key),
                width=dict_wrappers_headers[type_form][headers[index]][font_size],
            )
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += (
                font_size
                * dict_wrappers_headers[type_form][headers[index]][font_size]
                * 0.8
            )
    if y_init < 40:
        pages += 1
        pdf.showPage()
        print_footer_page_count(pdf, pages)
        y_init = 780
    pdf.setFont("Courier-Bold", font_size)
    y_init = last_y - font_size * 1.5
    pdf.drawString(20, y_init, "Fecha de primera entrega:")
    pdf.setFont("Courier", font_size)
    y_init = y_init - font_size * 1.4
    pdf.drawString(20, y_init, dict_data["date_first_delivery"])
    pdf.setFont("Courier-Bold", font_size)
    y_init = y_init - font_size * 1.5
    pdf.drawString(20, y_init, "Fecha de entrega completa:")
    pdf.setFont("Courier", font_size)
    y_init = y_init - font_size * 1.4
    pdf.drawString(20, y_init, dict_data["date_complete_delivery"])
    y_init -= font_size
    if y_init < 40:
        pages += 1
        pdf.showPage()
        print_footer_page_count(pdf, pages)
        y_init = 780
    create_footer_sign(pdf, 50, 30, "Nombre y firma de quien entrega")
    create_footer_sign(pdf, 350, 30, "Nombre y firma de quien recibe")
    pdf.save()
    return True
