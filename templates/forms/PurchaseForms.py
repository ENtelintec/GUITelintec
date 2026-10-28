# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jun/2025  at 16:27 $"

from reportlab.pdfgen import canvas

from static.constants import filepath_po_pdf
from templates.forms.PDFGenerator import (
    FONT_BOLD,
    FONT_REGULAR,
    a4_x,
    a4_y,
    create_header_telintec,
    print_footer_page_count,
    wrap_text_width,
)

# PDF FO-COM-04 R0 (orden de compra) en la cuadrícula de la casa (skill
# pdf-design), tomando como base la estructura del formato: banda con el folio,
# datos de Telintec, datos del proveedor, lista de componentes y totales. Ver
# docs/po_pdf_cuadricula.md.
_PO_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE
_PO_MARGIN = 25.0
_PO_USABLE_W = a4_x - 2 * _PO_MARGIN
_PO_ISO_FORM = 16  # iso_formats.id de FO-COM-04
_PO_IVA = 0.16
_PO_LABEL_W = 150.0  # bloques de datos: un par label|valor por fila

# Tabla de partidas: (clave, encabezado, ancho pt, alineación). Descripción toma
# el ancho que dejan las demás; Duración y Moneda solo aparecen cuando aplican
# (ver _po_item_cols). El encabezado de los importes lleva la moneda cuando la
# OC tiene una sola.
_PO_COL_NO = ("no", "No.", 26.0, "left")
_PO_COL_DESCRIPTION = ("description", "Descripción", 0.0, "left")
_PO_COL_N_PARTE = ("n_parte", "No. de parte", 70.0, "left")
_PO_COL_UDM = ("udm", "UM", 34.0, "left")
_PO_COL_DURATION = ("duration", "Duración (meses)", 50.0, "right")
_PO_COL_QUANTITY = ("quantity", "Cantidad pedida", 52.0, "right")
_PO_COL_CURRENCY = ("currency", "Moneda", 42.0, "left")
_PO_COL_UNIT_PRICE = ("unit_price", "Precio unitario", 70.0, "right")
_PO_COL_SUBTOTAL = ("subtotal", "Importe", 74.0, "right")


def _po_draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False, align="left"):
    """Celda de cuadrícula (skill pdf-design): recuadro, texto con padding y
    relleno celeste opcional para labels/encabezados. align: left | right | center."""
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_PO_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)  # SIEMPRE restaurar a negro
    else:
        pdf.rect(x, y_top - h, w, h, fill=0, stroke=1)
    pdf.setFont(FONT_BOLD if bold else FONT_REGULAR, font_size)
    text_y = y_top - font_size - 3
    for line in lines:
        if align == "right":
            pdf.drawRightString(x + w - 4, text_y, line)
        elif align == "center":
            pdf.drawCentredString(x + w / 2, text_y, line)
        else:
            pdf.drawString(x + 4, text_y, line)
        text_y -= font_size * 1.25


def _po_row_h(lines_per_cell, font_size):
    return max(len(lines) for lines in lines_per_cell) * font_size * 1.25 + 6


def _po_money(value):
    return f"${float(value or 0):,.2f}"


def _po_qty(value):
    """Cantidades sin ".0" sobrante: 3 -> "3", 2.5 -> "2.5", 1250 -> "1,250"."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.4f}".rstrip("0").rstrip(".")


def _po_duration(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return _po_qty(number) if number > 0 else ""


def _po_item_cols(products, currencies):
    """Columnas de la tabla según la OC: Duración si alguna partida es un
    servicio con meses; Moneda si se mezclan monedas (si no, la moneda va en el
    encabezado de los importes). Los anchos suman el ancho útil."""
    cols = [_PO_COL_NO, _PO_COL_DESCRIPTION, _PO_COL_N_PARTE, _PO_COL_UDM]
    if any(_po_duration(p.get("duration")) for p in products):
        cols.append(_PO_COL_DURATION)
    cols.append(_PO_COL_QUANTITY)
    unit_price, subtotal = _PO_COL_UNIT_PRICE, _PO_COL_SUBTOTAL
    if len(currencies) > 1:
        cols.append(_PO_COL_CURRENCY)
    else:
        unit_price = (unit_price[0], f"{unit_price[1]} ({currencies[0]})", unit_price[2], unit_price[3])
        subtotal = (subtotal[0], f"{subtotal[1]} ({currencies[0]})", subtotal[2], subtotal[3])
    cols += [unit_price, subtotal]
    rest = _PO_USABLE_W - sum(w for _, _, w, _ in cols)
    return [(key, name, rest if key == "description" else w, align) for key, name, w, align in cols]


def _po_cell_text(product, key):
    if key == "quantity":
        return _po_qty(product.get("quantity"))
    if key == "duration":
        return _po_duration(product.get("duration"))
    if key in ("unit_price", "subtotal"):
        return _po_money(product.get(key))
    return str(product.get(key) or "")


def _po_draw_band(pdf, y, text, font_size):
    """Banda de título de sección: celda celeste a todo el ancho, centrada."""
    lines = wrap_text_width(text, _PO_USABLE_W - 8, font_size, font=FONT_BOLD)
    h = _po_row_h([lines], font_size)
    _po_draw_cell(pdf, _PO_MARGIN, y, _PO_USABLE_W, h, lines, font_size, bold=True, fill=True, align="center")
    return y - h


def _po_pair_lines(label, value, font_size, label_w=_PO_LABEL_W, value_w=_PO_USABLE_W - _PO_LABEL_W):
    return (
        wrap_text_width(label, label_w - 8, font_size, font=FONT_BOLD),
        wrap_text_width(value, value_w - 8, font_size),
    )


def _po_draw_pair(pdf, x, y, label_w, value_w, label_lines, value_lines, font_size, value_bold=False):
    h = _po_row_h([label_lines, value_lines], font_size)
    _po_draw_cell(pdf, x, y, label_w, h, label_lines, font_size, bold=True, fill=True)
    _po_draw_cell(pdf, x + label_w, y, value_w, h, value_lines, font_size, bold=value_bold)
    return y - h


def _po_draw_cancelled_mark(pdf):
    """Marca diagonal gris de OC cancelada; se dibuja al cerrar cada página para
    que quede encima de las celdas celestes (con transparencia, el texto se lee)."""
    pdf.saveState()
    pdf.translate(a4_x / 2, a4_y / 2)
    pdf.rotate(45)
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.setFillAlpha(0.25)
    pdf.setFont(FONT_BOLD, 96)
    pdf.drawCentredString(0, -34, "CANCELADA")
    pdf.restoreState()


def FilePoPDF(dict_data: dict):
    """
    Genera el PDF FO-COM-04 R0 de una orden de compra. dict_data trae todo
    resuelto por el midleware (sin acceso a BD), con estas llaves:

        filename_out: str          ruta del PDF a escribir (None = filepath_po_pdf)
        folio: str                 folio de la OC (banda y pie)
        cancelled: bool            True si la OC está cancelada (marca diagonal)
        emission: str              fecha de emisión de la OC (YYYY-MM-DD)
        modified: str              última modificación (YYYY-MM-DD) o "" si no
                                   se editó después del día de emisión
        metadata_telintec: dict    label -> valor, en orden de impresión
        metadata_supplier: dict    label -> valor, en orden de impresión
        products: list de dicts con no, description, n_parte, udm,
                  duration (meses o None), quantity, currency, unit_price y
                  subtotal (números sin formato)
        totals: dict               moneda -> suma de importes sin IVA, en el
                                   orden de aparición de las partidas

    :param dict_data: datos de la OC ya resueltos por el midleware
    :return: True si el PDF se generó correctamente
    """
    file_name = dict_data.get("filename_out") or filepath_po_pdf
    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    pdf.setTitle("Orden de Compra")

    pages = 1
    font_size = 8
    limit_y = 50
    folio = str(dict_data.get("folio") or "")
    cancelled = bool(dict_data.get("cancelled"))
    products = list(dict_data.get("products") or [])
    totals = dict(dict_data.get("totals") or {}) or {"MXN": 0.0}
    currencies = list(totals.keys())
    cols = _po_item_cols(products, currencies)

    def draw_header():
        create_header_telintec(
            pdf,
            title="ORDEN DE COMPRA",
            page_x=a4_x,
            iso_form=_PO_ISO_FORM,
            orientation="vertical",
            offset_title=(-18, 0),
        )
        return 740.0

    def print_column_headers(y):
        cells = [wrap_text_width(name, w - 8, font_size, font=FONT_BOLD) for _, name, w, _ in cols]
        h = _po_row_h(cells, font_size)
        x = _PO_MARGIN
        for (_, _, w, align), lines in zip(cols, cells):
            _po_draw_cell(pdf, x, y, w, h, lines, font_size, bold=True, fill=True, align=align)
            x += w
        return y - h

    def close_page():
        if cancelled:
            _po_draw_cancelled_mark(pdf)
        print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=a4_x)

    def check_page_break(y, needed=0.0, with_columns=False):
        nonlocal pages
        if y - needed >= limit_y:
            return y
        close_page()
        pdf.showPage()
        pages += 1
        y = draw_header()
        if with_columns:
            y = print_column_headers(y)
        return y

    # Página 1: banda con el folio, fecha de emisión y bloques de datos.
    y = draw_header()
    half_w = _PO_USABLE_W / 2
    band_h = 10 * 1.25 + 8
    _po_draw_cell(pdf, _PO_MARGIN, y, half_w, band_h, ["ORDEN DE COMPRA"], 10, bold=True, fill=True, align="center")
    _po_draw_cell(pdf, _PO_MARGIN + half_w, y, half_w, band_h, [folio], 10, bold=True, align="center")
    y -= band_h
    dates = [("Fecha de emisión", dict_data.get("emission") or "")]
    if dict_data.get("modified"):
        dates.append(("Última modificación", dict_data["modified"]))
    date_label_w = 100.0
    for label, value in dates:
        label_lines, value_lines = _po_pair_lines(label, value, font_size, date_label_w, half_w - date_label_w)
        y = _po_draw_pair(
            pdf, _PO_MARGIN + half_w, y, date_label_w, half_w - date_label_w, label_lines, value_lines, font_size
        )
    for title, metadata in (
        ("DATOS DE TELINTEC", dict_data.get("metadata_telintec") or {}),
        ("DATOS DEL PROVEEDOR", dict_data.get("metadata_supplier") or {}),
    ):
        y -= 8
        y = check_page_break(y, needed=40)
        y = _po_draw_band(pdf, y, title, font_size)
        for label, value in metadata.items():
            label_lines, value_lines = _po_pair_lines(label, value, font_size)
            y = check_page_break(y, needed=_po_row_h([label_lines, value_lines], font_size))
            y = _po_draw_pair(
                pdf, _PO_MARGIN, y, _PO_LABEL_W, _PO_USABLE_W - _PO_LABEL_W, label_lines, value_lines, font_size
            )

    # Lista de componentes: encabezados de columna repetidos en cada página.
    y -= 12
    y = check_page_break(y, needed=60)
    y = _po_draw_band(pdf, y, "LISTA DE COMPONENTES", font_size)
    y = print_column_headers(y)
    for product in products:
        cells = [wrap_text_width(_po_cell_text(product, key), w - 8, font_size) for key, _, w, _ in cols]
        row_h = _po_row_h(cells, font_size)
        y = check_page_break(y, needed=row_h, with_columns=True)
        x = _PO_MARGIN
        for (_, _, w, align), lines in zip(cols, cells):
            _po_draw_cell(pdf, x, y, w, row_h, lines, font_size, align=align)
            x += w
        y -= row_h

    # Totales: Subtotal / IVA / Total bajo las dos últimas columnas, un bloque
    # por moneda; todos los bloques juntos en la misma página.
    row_h = font_size * 1.25 + 6
    value_w = cols[-1][2]
    label_w = cols[-2][2] + (cols[-3][2] if len(currencies) > 1 else 0.0)
    x_label = _PO_MARGIN + _PO_USABLE_W - value_w - label_w
    y -= 4
    y = check_page_break(y, needed=len(currencies) * (3 * row_h + 4))
    for currency, subtotal in totals.items():
        iva = float(subtotal or 0) * _PO_IVA
        suffix = f" {currency}" if len(currencies) > 1 else ""
        for label, amount, bold in (
            (f"Subtotal{suffix}", subtotal, True),
            (f"IVA (16%){suffix}", iva, False),
            (f"Total{suffix}", float(subtotal or 0) + iva, True),
        ):
            _po_draw_cell(pdf, x_label, y, label_w, row_h, [label], font_size, bold=True, fill=True)
            _po_draw_cell(pdf, x_label + label_w, y, value_w, row_h, [_po_money(amount)], font_size, bold=bold, align="right")
            y -= row_h
        y -= 4

    close_page()
    pdf.save()
    return True
