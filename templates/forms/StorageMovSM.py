# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jul./2024  at 6:05 $"

import textwrap

from reportlab.pdfgen import canvas

from static.constants import filepath_sm_pdf
from templates.forms.PDFGenerator import a4_x, a4_y, create_header_telintec

dict_wrappers_headers = {
    "Movements": {
        "Codigo": {10: 9, 8: 11},
        "Fecha": {10: 9, 8: 11},
        "Descripción": {10: 20, 8: 26},
        "UDM": {10: 4, 8: 5},
        "Proveedor": {10: 12, 8: 14},
        "Movimiento": {10: 10, 8: 12},
        "SM": {10: 8, 8: 11},
        "Referencia": {10: 18, 8: 24},
        "Ubicacion": {10: 10, 8: 12},
    },
    "Materials": {
        "Codigo": {10: 10, 8: 13},
        "Proveedor": {10: 13, 8: 16},
        "Descripción": {10: 30, 8: 38},
        "UDM": {10: 4, 8: 5},
        "Stock Min.": {10: 10, 8: 12},
        "Stock": {10: 10, 8: 12},
        "Ubicacion": {10: 20, 8: 24},
    },
    "SM": {
        "Item": {10: 7, 8: 9},
        "Descripción": {10: 30, 8: 38},
        "UDM": {10: 4, 8: 5},
        "Cantidad": {10: 10, 8: 12},
        "C. Suministrado": {10: 12, 8: 13},
        "Estado": {10: 10, 8: 12},
    },
}


def print_headers_table_inventory(pdf, font_size=10, y_init=500, type_form="Movements"):
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
        if calculate_last_y(item, limit_y, font_size, y_init, type_form="SM"):
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            pages += 1
            print_headers_table_inventory(pdf, y_init=535, type_form="SM")
            y_init = 510
            last_y = y_init
            pdf.setFont("Courier", font_size)
        for index, key in enumerate(item):
            value = textwrap.wrap(
                str(key),
                width=dict_wrappers_headers["SM"][headers[index]][font_size],
            )
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += (
                font_size * dict_wrappers_headers["SM"][headers[index]][font_size] * 0.8
            )
    return last_y - font_size * 1.5, pages


def print_footer_signing(
    pdf, font_size=10, y_position=50.0, margin_bottom=75.0, y_max=a4_y, pages=1
):
    """
    Función para imprimir un footer en un PDF, creando una nueva página si no hay suficiente espacio.

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
    labels = [
        "Nombre y Firma de Quien Entrega: ___________________________",
        "Nombre y Firma de Quien Recibe: ___________________________",
        "Fecha 1° Entrega: ___________________________",
        "Fecha Entrega Completa: ___________________________",
    ]

    for i in range(len(labels)):
        pdf.drawString(x_start, y_position, labels[i])
        y_position -= font_size * 2.5
    return y_position - font_size * 2.5, pages


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


def InventoryStoragePDF(dict_data: dict, type_form="Movements"):
    """
    :param type_form:
    :param dict_data:
    :return:
    """
    file_name = (
        "files/inventory_storage.pdf"
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )
    pdf = canvas.Canvas(file_name, pagesize=(a4_y, a4_x))
    pdf.setTitle(
        "Inventario: Registro de Entradas y Salidas"
    ) if type_form == "Movements" else pdf.setTitle(
        "Inventario: Registro de Materiales"
    )
    products = dict_data["products"]
    create_header_telintec(
        pdf,
        title=["Inventario", "Registro de Entradas y Salidas", "Almacen-Nogalar"]
        if type_form == "Movements"
        else ["Inventario", "Registro de Materiales", "Almacen-Nogalar"],
        page_x=a4_y,
        iso_form=2,
        orientation="Horizontal",
        title_font=14,
    )
    pages = 1
    # ----------------------------------------header table of products-----------------------------------------------
    print_headers_table_inventory(pdf, type_form=type_form)
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers[type_form].keys())
    font_size = 8
    pdf.setFont("Courier", font_size)
    y_init = 480
    last_y = y_init
    limit_y = 10
    for index_products, item in enumerate(products):
        x_position = 20
        y_init = last_y
        if calculate_last_y(item, limit_y, font_size, y_init, type_form=type_form):
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            pages += 1
            print_headers_table_inventory(pdf, y_init=535, type_form=type_form)
            y_init = 510
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
    print_footer_page_count(pdf, pages)
    pdf.save()
    return True


def ReturnMaterials(dict_data: dict):
    """
    :param dict_data:
    :return:
    """
    file_name = (
        "files/return_materials.pdf"
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )
    pdf = canvas.Canvas(file_name, pagesize=(a4_y, a4_x))
    pdf.setTitle("Devolucion de Materiales")
    products = dict_data["products"]
    create_header_telintec(
        pdf, title="DEVOLUCION DE MATERIALES", page_x=a4_y, date_int="2023-06-14"
    )
    pages = 1
    # ----------------------------------------header table of products-----------------------------------------------
    print_headers_table_inventory(pdf, type_form="Materials")
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers["Materials"].keys())
    font_size = 8
    pdf.setFont("Courier", font_size)
    y_init = 480
    last_y = y_init
    limit_y = 10
    for index_products, item in enumerate(products):
        x_position = 20
        y_init = last_y
        if calculate_last_y(item, limit_y, font_size, y_init, type_form="Materials"):
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            print_headers_table_inventory(pdf, y_init=535, type_form="Materials")
            y_init = 510
            last_y = y_init
            pdf.setFont("Courier", font_size)
        for index, key in enumerate(item):
            value = textwrap.wrap(
                str(key),
                width=dict_wrappers_headers["Materials"][headers[index]][font_size],
            )
            y_position = y_init - font_size * 1.5
            for letter in value:
                pdf.drawString(x_position, y_position, letter)
                y_position -= font_size
                last_y = y_position if y_position < last_y else last_y
            x_position += (
                font_size
                * dict_wrappers_headers["Materials"][headers[index]][font_size]
                * 0.8
            )

    pages += 1
    print_footer_page_count(pdf, pages)
    pdf.save()
    return True


def FileSmPDF(dict_data: dict):
    """
    :param dict_data:
    :return:
    """
    file_name = (
        filepath_sm_pdf
        if dict_data["filename_out"] is None
        else dict_data["filename_out"]
    )
    x_max = a4_x
    y_max = a4_y
    pdf = canvas.Canvas(file_name, pagesize=(x_max, y_max))
    pdf.setTitle("SOLICITUD DE MATERIAL")
    products = dict_data["products"]
    folio = dict_data.get("metadata", {}).get("Folio", "")
    create_header_telintec(
        pdf,
        title="SOLICITUD DE MATERIAL",
        page_x=x_max,
        iso_form=4,
        orientation="vertical",
        offset_title=(-18, 0),
    )
    pages = 1
    # ----------------------------------------Metadata---------------------------------------------------------------
    y_last_metada = print_metadata(pdf, dict_data["metadata"], y_init=740)
    # ----------------------------------------header table of products-----------------------------------------------
    y_last_headers = print_headers_table_inventory(
        pdf, type_form="SM", y_init=y_last_metada
    )
    # ---------------------------------------------products---------------------------------------------------------
    headers = list(dict_wrappers_headers["SM"].keys())
    font_size = 8
    y_last_products, pages = print_products_list(
        pdf, products, headers, font_size, y_last_headers, pages
    )
    y_last_signs, pages = print_footer_signing(
        pdf, font_size, y_last_products, pages=pages, y_max=y_max
    )
    print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=x_max)
    pdf.save()
    return True


def FilePurchaseList(dict_data: dict, path):
    """
    Genera un PDF con la lista de compra:
    - Imprime cada inventario como un ítem general con su total.
    - Luego imprime el desglose de cada entrega asociada.
    :param dict_data: diccionario con items agrupados por id_inventory
    :param path: ruta de salida del PDF
    :return:
    """
    pdf = canvas.Canvas(path, pagesize=(a4_y, a4_x))
    pdf.setTitle("LISTA DE COMPRA")

    create_header_telintec(
        pdf,
        title="LISTA DE COMPRA",
        page_x=a4_y,
        iso_form=4,
        orientation="vertical",
        offset_title=(-18, 0),
    )

    pages = 1
    font_size = 9
    pdf.setFont("Courier", font_size)

    y_init = 500
    limit_y = 40
    last_y = y_init

    for id_inventory, values in dict_data.items():
        items = values["items"]
        total = values["total"]

        # --- Imprimir encabezado general del inventario ---
        pdf.setFont("Courier-Bold", font_size)
        pdf.drawString(30, last_y, f"Inventario: {id_inventory}")
        pdf.drawString(200, last_y, f"Total: {total}")
        last_y -= font_size * 2

        # --- Imprimir desglose de cada item ---
        pdf.setFont("Courier", font_size)
        for item in items:
            if last_y < limit_y:  # salto de página
                print_footer_page_count(pdf, pages)
                pdf.showPage()
                create_header_telintec(
                    pdf,
                    title="LISTA DE COMPRA",
                    page_x=a4_y,
                    iso_form=4,
                    orientation="vertical",
                    offset_title=(-18, 0),
                )
                pages += 1
                pdf.setFont("Courier", font_size)
                last_y = 500

            pdf.drawString(40, last_y, f"Item: {item['name']} ({item['id_item']})")
            pdf.drawString(250, last_y, f"Cantidad: {item['quantity']}")
            pdf.drawString(350, last_y, f"Entrega: {item.get('quantity_c', 0)}")
            pdf.drawString(450, last_y, f"Folio PO: {item.get('folio_po', '')}")
            last_y -= font_size * 1.5

    # --- Footer final ---
    print_footer_page_count(pdf, pages)
    pdf.save()
    return True
