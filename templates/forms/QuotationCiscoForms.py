# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 22/oct./2026  at 23:40 $"

from reportlab.pdfgen import canvas

from templates.forms.PDFGenerator import (
    FONT_BOLD,
    FONT_REGULAR,
    a4_x,
    a4_y,
    create_header_telintec,
    print_footer_page_count,
    wrap_text_width,
)

# PDF FO-PRE-02 R2 (cotización CISCO): misma hoja "COT CISCO" del Excel del
# formato, en la cuadrícula de la casa (skill pdf-design). Ver
# docs/cotizacion_cisco_pdf.md.
_QC_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE
_QC_MARGIN = 25.0
_QC_USABLE_W = a4_x - 2 * _QC_MARGIN
_QC_ISO_FORM = 15  # iso_formats.id de FO-PRE-02
_QC_COMPANY = "TELINTEC S.A. DE C.V."

# Metadata: 2 pares label|valor por fila.
_QC_LABEL_W = 118.0
_QC_HALF_W = _QC_USABLE_W / 2
_QC_VALUE_W = _QC_HALF_W - _QC_LABEL_W

# Tabla de partidas: (encabezado, ancho pt, alineación), en el orden del Excel.
# Los anchos suman el ancho útil; DESCRIPCIÓN absorbe el resto. El orden sigue
# la lista de celdas que arma FileQuotationCiscoPDF (header y celda por posición).
_QC_ITEM_COLS = [
    ("ITEM", 30.0, "left"),
    ("NÚMERO DE PARTE", 76.0, "left"),
    ("SMART ACCOUNT OBLIGATORIO", 58.0, "left"),
    ("DESCRIPCIÓN", 109.27, "left"),
    ("DURACIÓN DEL SERVICIO (MESES)", 50.0, "right"),
    ("TIEMPO DE ENTREGA", 56.0, "left"),
    ("CANTIDAD", 46.0, "right"),
    ("PRECIO UNIT.", 60.0, "right"),
    ("TOTAL", 60.0, "right"),
]


def _qc_draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False, align="left"):
    """Celda de cuadrícula (skill pdf-design): recuadro, texto con padding y
    relleno celeste opcional para labels/encabezados. align: left | right | center."""
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_QC_CELESTE)
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


def _qc_row_h(lines_per_cell, font_size):
    return max(len(lines) for lines in lines_per_cell) * font_size * 1.25 + 6


def _qc_money(value):
    return f"${float(value or 0):,.2f}"


def _qc_draw_pairs_row(pdf, y, pairs, font_size):
    """Una fila de metadata con 1 o 2 pares (label, valor). Con un solo par el
    valor toma el resto del ancho. Devuelve la y de abajo."""
    cells = []
    x = _QC_MARGIN
    for index, (label, value) in enumerate(pairs):
        value_w = _QC_VALUE_W if len(pairs) > 1 or index > 0 else _QC_USABLE_W - _QC_LABEL_W
        cells.append((x, _QC_LABEL_W, wrap_text_width(label, _QC_LABEL_W - 8, font_size, font=FONT_BOLD), True))
        cells.append((x + _QC_LABEL_W, value_w, wrap_text_width(value, value_w - 8, font_size), False))
        x += _QC_LABEL_W + value_w
    h = _qc_row_h([lines for _, _, lines, _ in cells], font_size)
    for cx, cw, lines, is_label in cells:
        _qc_draw_cell(pdf, cx, y, cw, h, lines, font_size, bold=is_label, fill=is_label)
    return y - h


def _qc_draw_full_row(pdf, y, text, font_size, header=False, align="left"):
    lines = wrap_text_width(text, _QC_USABLE_W - 8, font_size, font=FONT_BOLD if header else FONT_REGULAR)
    h = _qc_row_h([lines], font_size)
    _qc_draw_cell(pdf, _QC_MARGIN, y, _QC_USABLE_W, h, lines, font_size, bold=header, fill=header, align=align)
    return y - h


def FileQuotationCiscoPDF(dict_data: dict):
    """
    Genera el PDF FO-PRE-02 R2 de una cotización CISCO (una fila de quotations
    con metadata.format = cisco). dict_data trae todo resuelto por el midleware
    (sin acceso a BD), con estas llaves:

        filename_out: str          ruta del PDF a escribir
        quotation_code: str        "Cotización" (y folio del pie)
        emission: str              "Fecha" (YYYY-MM-DD)
        limit_date: str            comentario 3, vigencia de la cotización
        contact_name / contact_phone / contact_email: str
                                   contacto de Telintec (empleado que capturó)
        company / user / phone / email / planta / area / location: str
                                   datos del cliente
        concept: str               CONCEPTO
        currency: str              TIPO DE MONEDA (MXN | USD)
        delivery_time: str         comentario 2, tiempo de entrega general
        products: list de dicts con item, n_parte, smart_account (bool),
                  description, service_months (int o None), delivery_time,
                  quantity, price_unit y total, ya ordenadas por partida
        total: float               suma de los totales por partida, sin IVA

    :param dict_data: datos de la cotización ya resueltos por el midleware
    :return: True si el PDF se generó correctamente
    """
    pdf = canvas.Canvas(dict_data["filename_out"], pagesize=(a4_x, a4_y))
    pdf.setTitle("Cotizacion CISCO")

    pages = 1
    font_size = 8
    table_font = 7
    limit_y = 50
    folio = str(dict_data.get("quotation_code") or "")

    def draw_header():
        create_header_telintec(
            pdf,
            title="COTIZACIÓN CISCO",
            page_x=a4_x,
            iso_form=_QC_ISO_FORM,
            orientation="vertical",
            offset_title=(0, 0),
        )
        return 740.0

    def print_column_headers(y):
        cells = [wrap_text_width(name, w - 8, table_font, font=FONT_BOLD) for name, w, _ in _QC_ITEM_COLS]
        h = _qc_row_h(cells, table_font)
        x = _QC_MARGIN
        for (_, w, align), lines in zip(_QC_ITEM_COLS, cells):
            _qc_draw_cell(pdf, x, y, w, h, lines, table_font, bold=True, fill=True, align=align)
            x += w
        return y - h

    def check_page_break(y, needed=0.0, with_columns=False):
        nonlocal pages
        if y - needed >= limit_y:
            return y
        print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=a4_x)
        pdf.showPage()
        pages += 1
        y = draw_header()
        if with_columns:
            y = print_column_headers(y)
        return y

    def text(key):
        return str(dict_data.get(key) or "")

    # Página 1: fecha/cotización, datos de Telintec y del cliente, concepto, moneda.
    last_y = draw_header()
    last_y = _qc_draw_pairs_row(pdf, last_y, [("Fecha", text("emission")), ("Cotización", folio)], font_size)
    last_y -= 6
    last_y = _qc_draw_full_row(pdf, last_y, "DATOS DE TELINTEC", font_size, header=True, align="center")
    last_y = _qc_draw_pairs_row(
        pdf, last_y, [("Nombre de la compañía", _QC_COMPANY), ("Nombre de contacto", text("contact_name"))], font_size
    )
    last_y = _qc_draw_pairs_row(
        pdf, last_y, [("Teléfono", text("contact_phone")), ("Email", text("contact_email"))], font_size
    )
    last_y -= 6
    last_y = _qc_draw_full_row(pdf, last_y, "DATOS DEL CLIENTE", font_size, header=True, align="center")
    last_y = _qc_draw_pairs_row(pdf, last_y, [("Nombre de la compañía", text("company")), ("Usuario", text("user"))], font_size)
    last_y = _qc_draw_pairs_row(pdf, last_y, [("Teléfono", text("phone")), ("Email", text("email"))], font_size)
    last_y = _qc_draw_pairs_row(pdf, last_y, [("Planta", text("planta")), ("Área", text("area"))], font_size)
    last_y = _qc_draw_pairs_row(pdf, last_y, [("Ubicación", text("location"))], font_size)
    last_y -= 6
    last_y = _qc_draw_full_row(pdf, last_y, "CONCEPTO", font_size, header=True, align="center")
    last_y = _qc_draw_full_row(pdf, last_y, text("concept"), font_size)
    last_y -= 8

    # TIPO DE MONEDA a la derecha, sobre las columnas PRECIO UNIT. y TOTAL.
    currency_h = font_size * 1.25 + 6
    last_y = check_page_break(last_y, needed=currency_h)
    total_w = _QC_ITEM_COLS[8][1]
    label_w = _QC_ITEM_COLS[7][1] + _QC_ITEM_COLS[6][1]
    currency_x = _QC_MARGIN + _QC_USABLE_W - total_w - label_w
    _qc_draw_cell(pdf, currency_x, last_y, label_w, currency_h, ["TIPO DE MONEDA"], font_size, bold=True, fill=True)
    _qc_draw_cell(
        pdf, currency_x + label_w, last_y, total_w, currency_h, [text("currency") or "MXN"], font_size, bold=True,
        align="center",
    )
    last_y -= currency_h

    last_y = check_page_break(last_y, needed=40)
    last_y = print_column_headers(last_y)
    for product in dict_data.get("products", []):
        item = str(product.get("item") or "")
        months = product.get("service_months")
        values = [
            item,
            str(product.get("n_parte") or ""),
            "Sí" if product.get("smart_account") else "No",
            str(product.get("description") or ""),
            "" if months in (None, "") else str(months),
            str(product.get("delivery_time") or ""),
            f"{float(product.get('quantity') or 0):g}",
            _qc_money(product.get("price_unit")),
            _qc_money(product.get("total")),
        ]
        cells = [wrap_text_width(v, w - 8, table_font) for v, (_, w, _) in zip(values, _QC_ITEM_COLS)]
        row_h = _qc_row_h(cells, table_font)
        last_y = check_page_break(last_y, needed=row_h, with_columns=True)
        x = _QC_MARGIN
        # Las partidas enteras (1, 2, 3) van en negrita en ITEM, como en el Excel.
        parent = "." not in item
        for index, ((_, w, align), lines) in enumerate(zip(_QC_ITEM_COLS, cells)):
            _qc_draw_cell(pdf, x, last_y, w, row_h, lines, table_font, bold=index == 0 and parent, align=align)
            x += w
        last_y -= row_h

    # TOTAL como continuación de la cuadrícula (sin IVA, ver comentario 1).
    totals_h = font_size * 1.25 + 6
    last_y = check_page_break(last_y, needed=totals_h)
    totals_x = _QC_MARGIN + sum(w for _, w, _ in _QC_ITEM_COLS[:7])
    _qc_draw_cell(pdf, totals_x, last_y, _QC_ITEM_COLS[7][1], totals_h, ["TOTAL"], font_size, bold=True, fill=True)
    _qc_draw_cell(
        pdf, totals_x + _QC_ITEM_COLS[7][1], last_y, total_w, totals_h, [_qc_money(dict_data.get("total"))],
        font_size, bold=True, align="right",
    )
    last_y -= totals_h + 14

    # COMENTARIOS: el bloque completo en la misma página.
    comments = [
        "1) Precios no incluyen IVA",
        f"2) Tiempo de entrega: {text('delivery_time')}",
        f"3) Vigencia de cotización: {text('limit_date')}",
    ]
    needed = sum(
        _qc_row_h([wrap_text_width(c, _QC_USABLE_W - 8, font_size)], font_size) for c in ["COMENTARIOS", *comments]
    )
    last_y = check_page_break(last_y, needed=needed)
    last_y = _qc_draw_full_row(pdf, last_y, "COMENTARIOS", font_size, header=True)
    for comment in comments:
        last_y = _qc_draw_full_row(pdf, last_y, comment, font_size)

    print_footer_page_count(pdf, pages, right_text=f"Folio: {folio}", x_max=a4_x)
    pdf.save()
    return True
