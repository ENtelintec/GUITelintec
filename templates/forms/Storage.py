# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 23/jul./2024  at 6:05 $'

import textwrap

from reportlab.pdfgen import canvas

from templates.forms.PDFGenerator import a4_x, a4_y, create_header


dict_wrappers_headers = {
    "Hoja de Registro": {10: 8, 
                         8: 10},
    "Fecha": {10: 10, 
              8: 12},
    "Codigo": {10: 6, 
               8: 7},
    "Descripción": {10: 20, 
                    8: 26},
    "Fabricante": {10: 15, 
                   8: 19},
    "UDM": {10: 4, 
            8: 5},
    "Movimiento": {10: 10, 
                   8: 12},
    "Entregado A": {10: 15, 
                    8: 18},
    "Observaciones": {10: 20, 
                      8: 24},
}
headers = list(dict_wrappers_headers.keys())


def print_headers_table_inventory(pdf, font_size=10, y_init=500):
    """
    :param y_init: 
    :param pdf:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier-Bold", font_size)
    x_position = 20
    for header_key in headers:
        header = textwrap.wrap(header_key, width=dict_wrappers_headers[header_key][font_size])
        y_position = y_init
        for letter in header:
            pdf.drawString(x_position, y_position, letter)
            y_position -= font_size
        # pdf.drawString(x_position, y_position, header)
        x_position += font_size * dict_wrappers_headers[header_key][font_size] * 0.8


def print_footer_page_count(pdf, page, font_size=6):
    """
    :param pdf:
    :param page:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier", font_size)
    pdf.drawString(5, 5, f"Página {page}")


def calculate_last_y(item, y_limit, font_size, y_position):
    for index, key in enumerate(item):
        value = textwrap.wrap(str(key), width=dict_wrappers_headers[headers[index]][font_size])
        y_hat = y_position - font_size * len(value) * 1.5
        if y_hat < y_limit:
            return True
    return False


def InventoryStorage(dict_data: dict):
    """
    :param dict_data: 
    :return: 
    """
    file_name = "files/inventory_storage.pdf" if dict_data["filename_out"] is None else dict_data["filename_out"]
    pdf = canvas.Canvas(file_name, pagesize=(a4_y, a4_x))
    pdf.setTitle("Inventario: Registro de Entradas y Salidas")
    products = dict_data["products"]
    create_header(pdf, title=["Inventario", "Registro de Entradas y Salidas", "Almacen-Nogalar"], 
                  page_x=a4_y, date_int=dict_data["date_emision"], type_form=2, orientation="Horizontal",
                  title_font=14)
    pages = 1
    # ----------------------------------------header table of products-----------------------------------------------
    print_headers_table_inventory(pdf)
    # ---------------------------------------------products---------------------------------------------------------
    font_size = 8
    pdf.setFont("Courier", font_size)
    y_init = 480
    last_y = y_init
    limit_y = 10
    for index_products, item in enumerate(products):
        x_position = 20
        y_init = last_y
        if calculate_last_y(item, limit_y, font_size, y_init):
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            print_headers_table_inventory(pdf, y_init=535)
            y_init = 510
            last_y = y_init
            pdf.setFont("Courier", font_size)
        for index, key in enumerate(item):
            value = textwrap.wrap(str(key), width=dict_wrappers_headers[headers[index]][font_size])
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += font_size*dict_wrappers_headers[headers[index]][font_size]*0.8
            
    pages += 1
    print_footer_page_count(pdf, pages)
    pdf.save()
    return True
