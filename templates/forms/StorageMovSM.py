# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jul./2024  at 6:05 $"

import textwrap

from reportlab.lib.utils import ImageReader
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
        header = textwrap.wrap(header_key, width=dict_wrappers_headers[type_form][header_key][font_size])
        y_position = y_init
        for letter in header:
            pdf.drawString(x_position, y_position, letter)
            y_position -= font_size
        # pdf.drawString(x_position, y_position, header)
        x_position += font_size * dict_wrappers_headers[type_form][header_key][font_size] * 0.8
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
        pdf.drawString(x_position + len(key) * font_size * 0.7, y_position, f"{metadata[key]}")
        x_position += separation
        count += 1
    return y_position - font_size * 2.5


def print_products_list(pdf, products, headers, font_size=8, y_last_headers=500.0, pages=1):
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
            x_position += font_size * dict_wrappers_headers["SM"][headers[index]][font_size] * 0.8
    return last_y - font_size * 1.5, pages


def print_footer_signing(pdf, font_size=10, y_position=50.0, margin_bottom=75.0, y_max=a4_y, pages=1):
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
        value = textwrap.wrap(str(key), width=dict_wrappers_headers[type_form][headers[index]][font_size])
        y_hat = y_position - font_size * len(value) * 1.5
        if y_hat < y_limit:
            return True
    return False


# Columnas de InventoryStoragePDF (página horizontal, ancho útil = a4_y - 2 * margen).
# El orden sigue el tuple que arma el midleware de almacén (Functions_midleware_almacen).
_INV_COLS = {
    "Movements": [
        ("Codigo", 70),
        ("Fecha", 65),
        ("Descripción", 220),
        ("UDM", 38),
        ("Proveedor", 90),
        ("Movimiento", 90),
        ("SM", 70),
        ("Referencia", 78),
        ("Ubicacion", 70.89),
    ],
    "Materials": [
        ("Codigo", 90),
        ("Proveedor", 110),
        ("Descripción", 280),
        ("UDM", 40),
        ("Stock Min.", 70),
        ("Stock", 60),
        ("Ubicacion", 141.89),
    ],
}


def InventoryStoragePDF(dict_data: dict, type_form="Movements"):
    """
    Reporte de almacén en cuadrícula (encabezados celestes): registro de
    entradas/salidas (``Movements``, 9 columnas) o de materiales
    (``Materials``, 7 columnas). Página horizontal. Estructura esperada::

        {"filename_out": str, "products": [tuple por fila, orden = _INV_COLS]}

    Multipágina: header Telintec + fila de encabezados en cada página.
    """
    file_name = "files/inventory_storage.pdf" if dict_data["filename_out"] is None else dict_data["filename_out"]
    pdf = canvas.Canvas(file_name, pagesize=(a4_y, a4_x))
    title = (
        "Inventario: Registro de Entradas y Salidas"
        if type_form == "Movements"
        else "Inventario: Registro de Materiales"
    )
    pdf.setTitle(title)
    products = dict_data["products"]
    cols = _INV_COLS[type_form]
    font_size = 8
    limit_y = 40
    pages = 1

    def draw_page_header():
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

    def new_page():
        nonlocal pages
        print_footer_page_count(pdf, pages, right_text=title, x_max=a4_y)
        pdf.showPage()
        pages += 1
        draw_page_header()
        return print_grid_header_row(pdf, cols, 500.0, font_size)

    draw_page_header()
    y = print_grid_header_row(pdf, cols, 500.0, font_size)
    for item in products:
        if y - grid_row_height(cols, item, font_size) < limit_y:
            y = new_page()
        y = print_grid_row(pdf, cols, item, y, font_size)
    print_footer_page_count(pdf, pages, right_text=title, x_max=a4_y)
    pdf.save()
    return True


def ReturnMaterials(dict_data: dict):
    """
    :param dict_data:
    :return:
    """
    file_name = "files/return_materials.pdf" if dict_data["filename_out"] is None else dict_data["filename_out"]
    pdf = canvas.Canvas(file_name, pagesize=(a4_y, a4_x))
    pdf.setTitle("Devolucion de Materiales")
    products = dict_data["products"]
    create_header_telintec(pdf, title="DEVOLUCION DE MATERIALES", page_x=a4_y, date_int="2023-06-14")
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
            x_position += font_size * dict_wrappers_headers["Materials"][headers[index]][font_size] * 0.8

    pages += 1
    print_footer_page_count(pdf, pages)
    pdf.save()
    return True


# ------------------------- PDFs en cuadrícula (diseño celeste) -------------------------
# Helpers genéricos `_grid_*`/`print_grid_*` compartidos por FileSmPDF e
# InventoryStoragePDF; ReturnMaterials sigue usando los helpers de texto suelto
# de arriba. Estilo de celdas tomado de RemissionForms.py; formato documentado
# en la skill .claude/skills/pdf-design/.

_GRID_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE, fondo de labels/encabezados
_GRID_MARGIN = 25.0

# alias históricos del bloque SM
_SM_CELESTE = _GRID_CELESTE
_SM_MARGIN = _GRID_MARGIN
_SM_GRID_WIDTH = a4_x - 2 * _GRID_MARGIN

# (encabezado, ancho en pt); los anchos suman _SM_GRID_WIDTH.
# El orden sigue el tuple de products: (no, nombre, cantidad, udm, suministrado, estatus)
_SM_ITEM_COLS = [
    ("No.", 32),
    ("Descripción", 225),
    ("Cantidad", 62),
    ("UDM", 38),
    ("C. Suministrado", 100),
    ("Estatus", 88.27),
]
_SM_DELIVERY_COLS = [
    ("No.", 32),
    ("Fecha de Entrega", 120),
    ("Firma de Quien Entrega", 196),
    ("Firma de Quien Recibe", 197.27),
]


def _grid_wrap_cell(value, width_pt, font_size):
    chars = max(1, int((width_pt - 8) / (font_size * 0.6)))
    return textwrap.wrap("" if value is None else str(value), width=chars) or [""]


def _grid_draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False):
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_GRID_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)
    else:
        pdf.rect(x, y_top - h, w, h, fill=0, stroke=1)
    pdf.setFont("Courier-Bold" if bold else "Courier", font_size)
    text_y = y_top - font_size - 3
    for line in lines:
        pdf.drawString(x + 4, text_y, line)
        text_y -= font_size * 1.25


def print_grid_header_row(pdf, cols, y_init, font_size=8, margin=_GRID_MARGIN):
    """Fila de encabezados de tabla: una celda celeste bold por columna."""
    h = font_size * 1.25 + 6
    x = margin
    for name, w in cols:
        _grid_draw_cell(pdf, x, y_init, w, h, [name], font_size, bold=True, fill=True)
        x += w
    return y_init - h


def grid_row_height(cols, item, font_size=8):
    return (
        max(len(_grid_wrap_cell(value, w, font_size)) for value, (_, w) in zip(item, cols))
        * font_size
        * 1.25
        + 6
    )


def print_grid_row(pdf, cols, item, y_init, font_size=8, margin=_GRID_MARGIN):
    """Fila de datos: celdas alineadas por posición con `cols`; crece con el wrap."""
    cells = [_grid_wrap_cell(value, w, font_size) for value, (_, w) in zip(item, cols)]
    h = max(len(lines) for lines in cells) * font_size * 1.25 + 6
    x = margin
    for lines, (_, w) in zip(cells, cols):
        _grid_draw_cell(pdf, x, y_init, w, h, lines, font_size)
        x += w
    return y_init - h


def print_metadata_grid_sm(pdf, metadata, y_init, font_size=8):
    """
    Cuadrícula de metadata: 2 pares label|valor por fila. La celda del label va
    en celeste con bold; el valor hace wrap dentro de su celda y la fila crece
    en alto (no hay desbordes de valores largos).
    """
    pair_w = _SM_GRID_WIDTH / 2
    label_w = 118.0
    value_w = pair_w - label_w
    entries = list(metadata.items())
    y = y_init
    for i in range(0, len(entries), 2):
        pair_cells = []
        max_lines = 1
        for label, value in entries[i : i + 2]:
            label_lines = _grid_wrap_cell(label, label_w, font_size)
            value_lines = _grid_wrap_cell(value, value_w, font_size)
            pair_cells.append((label_lines, value_lines))
            max_lines = max(max_lines, len(label_lines), len(value_lines))
        h = max_lines * font_size * 1.25 + 6
        x = _SM_MARGIN
        for label_lines, value_lines in pair_cells:
            _grid_draw_cell(pdf, x, y, label_w, h, label_lines, font_size, bold=True, fill=True)
            _grid_draw_cell(pdf, x + label_w, y, value_w, h, value_lines, font_size)
            x += pair_w
        y -= h
    return y


# Alto de fila de entrega: 26pt cuando solo lleva texto, ~60pt cuando incrusta
# la firma (imagen), para que la firma sea legible como comprobante.
_SM_PLAIN_ROW_H = 26.0
_SM_SIGN_ROW_H = 60.0
# tope de ancho para las firmas incrustadas (px); el pre-redimensionado real
# (para no engordar el PDF) lo hace la capa midleware antes de pasar la ruta.
_SM_SIGN_MAX_W = 600


def _sm_delivery_row_height(entry, font_size=8):
    """Alto de una fila de entrega: el mayor entre el texto (fecha+título con
    wrap) y el espacio de la firma cuando la fila trae imagen dibujable."""
    date_w = _SM_DELIVERY_COLS[1][1]
    lines = 0
    if entry.get("date"):
        lines += len(_grid_wrap_cell(entry["date"], date_w, font_size))
    if entry.get("title"):
        lines += len(_grid_wrap_cell(entry["title"], date_w, font_size))
    text_h = max(1, lines) * font_size * 1.25 + 6
    img_h = _SM_SIGN_ROW_H if entry.get("image_path") else 0.0
    return max(_SM_PLAIN_ROW_H, text_h, img_h)


def _sm_draw_signature_image(pdf, img_path, cell_x, cell_y_top, cell_w, cell_h, pad=3.0):
    """Dibuja la firma dentro de la celda preservando aspect ratio y centrada.
    No fatal: si la imagen no se puede leer, deja la celda vacía (firma a mano)."""
    try:
        reader = ImageReader(img_path)
        iw, ih = reader.getSize()
        if not iw or not ih or iw <= 0 or ih <= 0:
            return
        max_w = cell_w - 2 * pad
        max_h = cell_h - 2 * pad
        scale = min(max_w / iw, max_h / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        img_x = cell_x + (cell_w - draw_w) / 2
        img_y = (cell_y_top - cell_h) + (cell_h - draw_h) / 2
        # mask="auto" respeta la transparencia (PNG de firma sobre fondo)
        pdf.drawImage(reader, img_x, img_y, width=draw_w, height=draw_h, mask="auto")
    except Exception as e:
        print("erro sm signature image", str(e))


def _sm_draw_delivery_row(pdf, y_top, entry, row_h, font_size=8):
    """Una fila de la tabla de entregas: No. | Fecha+Título | (firma entrega en
    blanco) | firma de quien recibe (imagen si existe)."""
    date_lines = []
    if entry.get("date"):
        date_lines += _grid_wrap_cell(entry["date"], _SM_DELIVERY_COLS[1][1], font_size)
    if entry.get("title"):
        date_lines += _grid_wrap_cell(entry["title"], _SM_DELIVERY_COLS[1][1], font_size)
    if not date_lines:
        date_lines = [""]
    cells = ([str(entry.get("no", ""))], date_lines, [""], [""])
    x = _SM_MARGIN
    for (_, w), lines in zip(_SM_DELIVERY_COLS, cells):
        _grid_draw_cell(pdf, x, y_top, w, row_h, lines, font_size)
        x += w
    # firma de quien recibe: última columna, imagen sobre la celda ya dibujada
    img_path = entry.get("image_path")
    if img_path:
        recibe_x = _SM_MARGIN + sum(w for _, w in _SM_DELIVERY_COLS[:3])
        recibe_w = _SM_DELIVERY_COLS[3][1]
        _sm_draw_signature_image(pdf, img_path, recibe_x, y_top, recibe_w, row_h)


def print_deliveries_sign_table_sm(pdf, y_init, delivery_files, font_size=8, new_page_cb=None, limit_y=40):
    """
    Tabla de entregas: encabezados en celeste y una fila por entrega
    (``delivery_files``). Cada fila pre-llena No./Fecha+Título; la firma de quien
    recibe se incrusta como imagen cuando el attachment es un raster dibujable
    (si no, la celda queda en blanco para firmar a mano). Al final el campo
    "Fecha de Entrega Completa". Con muchas entregas la tabla pagina por fila
    (``new_page_cb``) repitiendo el encabezado de columnas.

    ``delivery_files``: [{"no": int, "date": str, "title": str,
    "image_path": str|None}, ...] (mínimo 1).
    """
    head_h = font_size * 1.25 + 6
    y = print_grid_header_row(pdf, _SM_DELIVERY_COLS, y_init, font_size)
    for entry in delivery_files:
        row_h = _sm_delivery_row_height(entry, font_size)
        if y - row_h < limit_y and new_page_cb is not None:
            y = new_page_cb()
            y = print_grid_header_row(pdf, _SM_DELIVERY_COLS, y, font_size)
        _sm_draw_delivery_row(pdf, y, entry, row_h, font_size)
        y -= row_h
    y -= 8
    label_w = 145.0
    value_w = 150.0
    if y - head_h < limit_y and new_page_cb is not None:
        y = new_page_cb()
    _grid_draw_cell(pdf, _SM_MARGIN, y, label_w, head_h, ["Fecha de Entrega Completa"], font_size, bold=True, fill=True)
    _grid_draw_cell(pdf, _SM_MARGIN + label_w, y, value_w, head_h, [""], font_size)
    return y - head_h


def FileSmPDF(dict_data: dict):
    """
    Genera el PDF de una SOLICITUD DE MATERIAL con metadata e items en
    cuadrícula (labels/encabezados con fondo celeste) y al final la tabla de
    entregas/firmas. Estructura esperada de ``dict_data``::

        {
            "filename_out": str,
            "metadata": {label: valor, ...},
            "products": [(no, nombre, cantidad, udm, suministrado, estatus), ...],
            "delivery_files": [                    # una entrega por attachment (>= 1)
                {"no": int, "date": str, "title": str, "image_path": str|None}, ...
            ],
        }

    Cada entrega pre-llena No./Fecha+Título y, si el attachment es una imagen
    dibujable, incrusta la firma de quien recibe (``image_path``); si no, la
    celda queda en blanco para firmar a mano. Multipágina: el header Telintec y
    los encabezados de columna se repiten en cada página; la metadata solo va en
    la página 1; la tabla de entregas pagina por fila.
    """
    file_name = filepath_sm_pdf if dict_data["filename_out"] is None else dict_data["filename_out"]
    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    pdf.setTitle("SOLICITUD DE MATERIAL")
    products = dict_data["products"]
    folio = dict_data.get("metadata", {}).get("Folio", "")
    # cap a 20: más entregas que esas no valen la pena en el documento
    delivery_files = list(dict_data.get("delivery_files") or [])[:20]
    if not delivery_files:
        delivery_files = [{"no": 1, "date": "", "title": "", "image_path": None}]
    font_size = 8
    limit_y = 40
    pages = 1

    def draw_page_header():
        create_header_telintec(
            pdf,
            title="SOLICITUD DE MATERIAL",
            page_x=a4_x,
            iso_form=4,
            orientation="vertical",
            offset_title=(-18, 0),
        )

    def new_page(with_columns):
        nonlocal pages
        print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=a4_x)
        pdf.showPage()
        pages += 1
        draw_page_header()
        y = 740.0
        if with_columns:
            y = print_grid_header_row(pdf, _SM_ITEM_COLS, y, font_size)
        return y

    draw_page_header()
    # ----------------------------------------Metadata en cuadrícula----------------------------------------------
    y = print_metadata_grid_sm(pdf, dict_data["metadata"], y_init=740, font_size=font_size)
    y -= 10
    # ----------------------------------------Items en cuadrícula-------------------------------------------------
    y = print_grid_header_row(pdf, _SM_ITEM_COLS, y, font_size)
    for item in products:
        if y - grid_row_height(_SM_ITEM_COLS, item, font_size) < limit_y:
            y = new_page(with_columns=True)
        y = print_grid_row(pdf, _SM_ITEM_COLS, item, y, font_size)
    # ----------------------------------------Entregas / firmas---------------------------------------------------
    y -= 14
    head_h = font_size * 1.25 + 6
    first_h = _sm_delivery_row_height(delivery_files[0], font_size)
    if y - (head_h + first_h) < limit_y:
        y = new_page(with_columns=False)
    print_deliveries_sign_table_sm(
        pdf,
        y,
        delivery_files,
        font_size=font_size,
        new_page_cb=lambda: new_page(with_columns=False),
        limit_y=limit_y,
    )
    print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=a4_x)
    pdf.save()
    return True


# Anclas de columna de la lista de compra (página horizontal, ancho = a4_y).
# Las columnas de dinero/cantidad usan drawRightString: el valor TERMINA en la x dada.
# Las columnas de texto (Descripción, PO, SM) usan drawString: el valor EMPIEZA en la x dada.
_PL_X_DESC = 45     # Descripción (izquierda)
_PL_X_CANT = 410    # Cant (derecha)
_PL_X_PUNIT = 515   # P. Unit (derecha)
_PL_X_PO = 550      # PO (izquierda)
_PL_X_SM = 660      # SM (izquierda)
_PL_X_TOTAL = 820   # Total / subtotal (derecha)


def FilePurchaseList(dict_data: dict, path):
    """
    Genera un PDF de LISTA DE COMPRA agrupada por proveedor e inventario, con
    apariencia de tabla/ticket de compra.

    Estructura esperada de ``dict_data`` (ver
    ``group_item_by_supplier_and_inventory`` en MD_Purchases.py)::

        {
            supplier_id: {
                "supplier_name": str,
                "inventories": {
                    id_inventory: {
                        "items": [ {  # una fila por ítem
                            "name": str,
                            "id_item": int,
                            "quantity_c": int,      # cantidad comprada
                            "price_unit": float,    # precio unitario
                            "folio_po": str,        # folio de la PO
                            "folio": str,           # folio de la SM
                        }, ... ],
                        "total_qty": int,           # suma de cantidades
                        "total_amount": float,      # suma de price_unit*quantity_c
                    },
                },
            },
        }

    Layout por página (horizontal):
      - Barra azul por proveedor con su nombre e ID.
      - Fila de encabezados de columna (Descripción | Cant | P. Unit | PO | SM |
        Total) una sola vez por proveedor.
      - Por inventario: línea resumen (Cant. total / Monto total) y luego sus
        ítems; Cant, P. Unit y Total se alinean a la derecha.
      - Subtotal por proveedor en negrita alineado a la derecha al cerrar cada
        proveedor.
      - GRAN TOTAL global en barra resaltada al final del documento.

    Columnas alineadas según las anclas ``_PL_X_*`` definidas a nivel de módulo.
    Más detalle del formato en ``docs/purchase_list_pdf.md``.

    :param dict_data: diccionario con items agrupados por supplier_id -> inventories -> id_inventory
    :param path: ruta de salida del PDF
    :return: True si el PDF se generó correctamente
    """
    pdf = canvas.Canvas(path, pagesize=(a4_y, a4_x))
    pdf.setTitle("LISTA DE COMPRA")
    create_header_telintec(
        pdf,
        title="LISTA DE COMPRA",
        page_x=a4_y,
        iso_form=4,
        orientation="horizontal",
        offset_title=(0, 0),
    )

    pages = 1
    font_size = 9
    limit_y = 40
    last_y = 500

    def check_page_break(y):
        nonlocal pages, last_y
        if y < limit_y:
            print_footer_page_count(pdf, pages)
            pdf.showPage()
            create_header_telintec(
                pdf,
                title="LISTA DE COMPRA",
                page_x=a4_y,
                iso_form=4,
                orientation="horizontal",
                offset_title=(0, 0),
            )
            pages += 1
            last_y = 500
            return last_y
        return y

    def print_column_headers(y):
        """Fila de encabezados de columna (una vez por proveedor)."""
        pdf.setFont("Courier-Bold", font_size - 1)
        pdf.drawString(_PL_X_DESC, y, "Descripcion")
        pdf.drawRightString(_PL_X_CANT, y, "Cant")
        pdf.drawRightString(_PL_X_PUNIT, y, "P. Unit")
        pdf.drawString(_PL_X_PO, y, "PO")
        pdf.drawString(_PL_X_SM, y, "SM")
        pdf.drawRightString(_PL_X_TOTAL, y, "Total")
        y -= 3
        pdf.setLineWidth(0.5)
        pdf.line(_PL_X_DESC, y, _PL_X_TOTAL, y)
        return y - font_size

    grand_total = 0.0

    for supplier_id, supplier_data in dict_data.items():
        supplier_name = supplier_data.get("supplier_name", "Sin proveedor")
        inventories = supplier_data.get("inventories", {})
        supplier_subtotal = 0.0

        last_y = check_page_break(last_y)

        # --- Encabezado de proveedor ---
        pdf.setFillColorRGB(0.15, 0.35, 0.6)
        pdf.rect(20, last_y - 4, a4_y - 40, font_size + 8, fill=1, stroke=0)
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Courier-Bold", font_size + 1)
        pdf.drawString(25, last_y, f"Proveedor: {supplier_name}  (ID: {supplier_id})")
        pdf.setFillColorRGB(0, 0, 0)
        last_y -= font_size * 2.2

        # --- Encabezados de columna (una vez por proveedor) ---
        last_y = print_column_headers(last_y)

        for id_inventory, inv_data in inventories.items():
            items = inv_data["items"]
            total_qty = inv_data["total_qty"]
            total_amount = inv_data["total_amount"]
            supplier_subtotal += total_amount

            last_y = check_page_break(last_y)

            # --- Encabezado de inventario ---
            pdf.setFont("Courier-Bold", font_size)
            pdf.drawString(30, last_y, f"Inventario: {id_inventory}")
            pdf.drawString(220, last_y, f"Cant. total: {total_qty}")
            pdf.drawString(360, last_y, f"Monto total: ${total_amount:,.2f}")
            last_y -= font_size * 1.8

            # --- Items del inventario ---
            pdf.setFont("Courier", font_size - 1)
            for item in items:
                last_y = check_page_break(last_y)
                price_unit = float(item.get("price_unit", 0))
                qty_c = item.get("quantity_c", 0)
                subtotal = price_unit * qty_c
                lines_name = textwrap.wrap(f"{item['name']} (ID:{item['id_item']})", width=40)
                line_y = last_y
                for line in lines_name:
                    pdf.drawString(_PL_X_DESC, last_y, line)
                    last_y -= font_size
                pdf.drawRightString(_PL_X_CANT, line_y, f"{qty_c}")
                pdf.drawRightString(_PL_X_PUNIT, line_y, f"${price_unit:,.2f}")
                pdf.drawString(_PL_X_PO, line_y, f"{item.get('folio_po', '')}")
                pdf.drawString(_PL_X_SM, line_y, f"{item.get('folio', '')}")
                pdf.drawRightString(_PL_X_TOTAL, line_y, f"${subtotal:,.2f}")
                last_y -= font_size * 0.8

            last_y -= font_size * 0.5

        # --- Subtotal por proveedor (negrita, alineado a la derecha) ---
        last_y = check_page_break(last_y)
        pdf.setFont("Courier-Bold", font_size)
        pdf.drawRightString(_PL_X_TOTAL, last_y, f"Subtotal proveedor: ${supplier_subtotal:,.2f}")
        last_y -= font_size * 2.0
        grand_total += supplier_subtotal

    # --- GRAN TOTAL global (barra resaltada al final) ---
    last_y = check_page_break(last_y)
    pdf.setFillColorRGB(0.10, 0.25, 0.50)
    pdf.rect(20, last_y - 5, a4_y - 40, font_size + 10, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Courier-Bold", font_size + 2)
    pdf.drawString(25, last_y, "GRAN TOTAL")
    pdf.drawRightString(_PL_X_TOTAL, last_y, f"${grand_total:,.2f}")
    pdf.setFillColorRGB(0, 0, 0)

    print_footer_page_count(pdf, pages)
    pdf.save()
    return True
