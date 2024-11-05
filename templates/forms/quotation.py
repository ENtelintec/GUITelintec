# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct/2024  at 16:32 $"

import textwrap

from reportlab.pdfgen import canvas

from templates.forms.PDFGenerator import a4_x, a4_y, create_header

dict_wrappers_headers_quotation = {
    "Movements": {
        "Hoja de Registro": {10: 8, 8: 10},
        "Fecha": {10: 10, 8: 12},
        "Codigo": {10: 6, 8: 7},
        "Descripción": {10: 20, 8: 26},
        "Fabricante": {10: 15, 8: 19},
        "UDM": {10: 4, 8: 5},
        "Movimiento": {10: 10, 8: 12},
        "Entregado A": {10: 15, 8: 18},
        "Observaciones": {10: 20, 8: 24},
    },
    "Materials": {
        "Codigo": {10: 6, 8: 7},
        "Descripción": {10: 30, 8: 38},
        "UDM": {10: 4, 8: 5},
        "Categoria": {10: 13, 8: 16},
        "Almacen": {10: 15, 8: 19},
        "Stock Min.": {10: 10, 8: 12},
        "Stock": {10: 10, 8: 12},
        "Solicitar": {10: 20, 8: 24},
    },
}


def print_headers_table_quotation(pdf, font_size=10, y_init=500, type_form="Movements"):
    """
    :param type_form:
    :param y_init:
    :param pdf:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier-Bold", font_size)
    x_position = 20
    headers = list(dict_wrappers_headers_quotation[type_form].keys())
    for header_key in headers:
        header = textwrap.wrap(
            header_key,
            width=dict_wrappers_headers_quotation[type_form][header_key][font_size],
        )
        y_position = y_init
        for letter in header:
            pdf.drawString(x_position, y_position, letter)
            y_position -= font_size
        # pdf.drawString(x_position, y_position, header)
        x_position += (
            font_size
            * dict_wrappers_headers_quotation[type_form][header_key][font_size]
            * 0.8
        )


def print_info_quotation(master, info_dict, font_size=10, y_init=500):
    position_y = y_init - font_size * 1.5
    position_x = 170
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Fecha: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Fecha: ") * font_size * 0.7,
        position_y,
        f"{info_dict['date']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Cliente: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Cotizacion: ") * font_size * 0.7,
        position_y,
        f"{info_dict['id_quotation']}",
    )
    position_y -= font_size * 1.5
    position_x = 20
    # nombre de la compañia, nombre de contacto, telefono, correo Telintec
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Compañia: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Compañia: ") * font_size * 0.7,
        position_y,
        "Telintec S.A. DE C.V.",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Contacto: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Contacto: ") * font_size * 0.7,
        position_y,
        f"{info_dict['contact']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Correo: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Correo: ") * font_size * 0.7,
        position_y,
        f"{info_dict['email_contact']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Telefono: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Telefono: ") * font_size * 0.7,
        position_y,
        f"{info_dict['phone_contact']}",
    )
    #  info usuario: compañia, nombre de usuario, telefono, email, planta, area, ubicacion
    position_y -= font_size * 3.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Compañia Usuario: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Compañia Usuario: ") * font_size * 0.7,
        position_y,
        f"{info_dict['user_company']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Usuario: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Usuario: ") * font_size * 0.7,
        position_y,
        f"{info_dict['user']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Telefono: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Telefono: ") * font_size * 0.7,
        position_y,
        f"{info_dict['user_phone']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Email: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Email: ") * font_size * 0.7,
        position_y,
        f"{info_dict['user_email']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Planta: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Planta: ") * font_size * 0.7,
        position_y,
        f"{info_dict['plant']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Area: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Area: ") * font_size * 0.7,
        position_y,
        f"{info_dict['area']}",
    )
    position_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(position_x, position_y, "Ubicacion: ")
    master.setFont("Courier", font_size)
    master.drawString(
        position_x + len("Ubicacion: ") * font_size * 0.7,
        position_y,
        f"{info_dict['location']}",
    )
    position_y -= font_size * 1.5


def print_footer_page_count(pdf, page, font_size=6):
    """
    :param pdf:
    :param page:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier", font_size)
    pdf.drawString(5, 5, f"Página {page}")


def calculate_last_y(item, y_limit, font_size, y_position, type_form="Movements"):
    headers = list(dict_wrappers_headers_quotation[type_form].keys())
    for index, key in enumerate(item):
        value = textwrap.wrap(
            str(key),
            width=dict_wrappers_headers_quotation[type_form][headers[index]][font_size],
        )
        y_hat = y_position - font_size * len(value) * 1.5
        if y_hat < y_limit:
            return True
    return False


def QuotationForm(dict_data: dict, type_form="Movements"):
    """
    :param type_form:
    :param dict_data:
    :return:
    """
    date_emision = (
        dict_data["date_emision"] if "date_emision" in dict_data else "2024-08-21"
    )
    data_info = dict_data["info"]
    file_name = (
        "files/quoatation.pdf"
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )

    pdf = canvas.Canvas(file_name, pagesize=(a4_y, a4_x))
    pdf.setTitle("Cotización")
    products = dict_data["products"]
    create_header(
        pdf,
        title="Cotización",
        page_x=a4_y,
        date_int=date_emision,
        iso_form=3,
        orientation="Vertical",
        title_font=14,
    )
    pages = 1
    # ----------------------------------------Info of the quotation----------------------------------------------
    y_init = 480
    print_info_quotation(pdf, dict_data["info"], y_init=y_init)
    # ----------------------------------------header table of products-----------------------------------------------
    y_init = 300
    print_headers_table_quotation(pdf, type_form=type_form, y_init=y_init)
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers_quotation[type_form].keys())
    font_size = 8
    pdf.setFont("Courier", font_size)
    y_init = 280
    last_y = y_init
    limit_y = 10
    for index_products, item in enumerate(products):
        x_position = 20
        y_init = last_y
        if calculate_last_y(item, limit_y, font_size, y_init, type_form=type_form):
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            print_headers_table_quotation(pdf, y_init=535, type_form=type_form)
            y_init = 510
            last_y = y_init
            pdf.setFont("Courier", font_size)
        for index, key in enumerate(item):
            value = textwrap.wrap(
                str(key),
                width=dict_wrappers_headers_quotation[type_form][headers[index]][
                    font_size
                ],
            )
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += (
                font_size
                * dict_wrappers_headers_quotation[type_form][headers[index]][font_size]
                * 0.8
            )

    pages += 1
    print_footer_page_count(pdf, pages)
    pdf.save()
    return True
