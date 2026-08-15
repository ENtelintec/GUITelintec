# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/jul/2026  at 17:30 $"

from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from static.constants import filepath_remission_pdf
from templates.forms.PDFGenerator import (
    FONT_BOLD,
    FONT_REGULAR,
    a4_x,
    a4_y,
    create_footer_sign,
    create_header_telintec,
    print_footer_page_count,
    wrap_text_width,
)

# Celeste institucional para labels/encabezados (ver skill pdf-design).
_RM_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE
_RM_MARGIN = 25.0

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

# Recuadro de metadata de la página 1 (a la derecha del bloque de la empresa).
_RM_META_X = 330.0
_RM_META_W = a4_x - _RM_META_X - _RM_MARGIN

# Columnas de la tabla de items: (encabezado, ancho pt, alineación). Los anchos
# suman el ancho útil (a4_x - 2 * _RM_MARGIN); DESCRIPCIÓN absorbe el resto.
# El orden sigue las llaves del dict de cada item (ver FileRemissionPDF).
_RM_ITEM_COLS = [
    ("POS.", 32.0, "left"),
    ("DESCRIPCIÓN", 258.27, "left"),
    ("CANT.", 50.0, "right"),
    ("UM", 40.0, "left"),
    ("PRECIO UNIT.", 80.0, "right"),
    ("TOTAL", 85.0, "right"),
]


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
        pdf.setFont(FONT_BOLD, font_size)
        pdf.drawString(x + 5, label_y, f"{label}:")
        pdf.setFont(FONT_REGULAR, font_size)
        pdf.drawString(x + 5 + stringWidth(f"{label}:", FONT_BOLD, font_size) + 5, label_y, str(lines[0]))
        line_y = label_y - row_h
        for extra in lines[1:]:
            pdf.drawString(x + 5, line_y, str(extra))
            line_y -= row_h
        y -= box_h
    return y


def _rm_draw_signature_image(pdf, img_path, x_start, x_end, y_base, max_h=38.0):
    """
    Dibuja una firma (imagen raster) centrada horizontalmente en el rango
    ``[x_start, x_end]`` y apoyada sobre ``y_base`` (justo encima de la línea de
    firma), preservando aspect ratio. No fatal: ante cualquier error no dibuja
    nada (la línea queda para firmar a mano).
    """
    try:
        reader = ImageReader(img_path)
        iw, ih = reader.getSize()
        if not iw or not ih or iw <= 0 or ih <= 0:
            return
        box_w = x_end - x_start
        ratio = min(box_w / iw, max_h / ih)
        draw_w = iw * ratio
        draw_h = ih * ratio
        img_x = x_start + (box_w - draw_w) / 2
        pdf.drawImage(reader, img_x, y_base, width=draw_w, height=draw_h, mask="auto")
    except Exception as e:
        print("erro remission signature image", str(e))


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
            # opcionales: rutas locales a firmas ya descargadas de S3
            "sign_realizado_path": str | None,   # -> "Firma Autorizacion 1"
            "sign_recibido_path": str | None,    # -> "Firma Autorizacion 2"
        }

    Más detalle del formato en ``docs/remission_pdf.md`` y del documento
    combinado en ``Docs/remission_combined_pdf.md``.

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
        pdf.setFont(FONT_REGULAR, 8)
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
                    *wrap_text_width(dict_data.get("project_description", "") or "", _RM_META_W - 10, font_size),
                ],
            ),
            ("No. Contrato Marco", dict_data.get("contract_marco", "")),
            ("No. Pedido Exiros", dict_data.get("pedido_exiros", "")),
            ("No. Pedido", dict_data.get("pedido", "")),
            ("Remito", dict_data.get("remito", "")),
        ]
        y_after_metadata = _draw_metadata_box(pdf, metadata_rows, _RM_META_X, 700, _RM_META_W)
        return min(text_y, y_after_metadata) - 20

    def print_column_headers(y):
        """Fila de encabezados de la tabla de items: celdas celestes (cuadrícula)."""
        h = (font_size - 1) * 1.25 + 6
        x = _RM_MARGIN
        for name, w, align in _RM_ITEM_COLS:
            _rm_draw_cell(pdf, x, y, w, h, [name], font_size - 1, bold=True, fill=True, align=align)
            x += w
        return y - h

    def check_page_break(y, needed=0.0, with_columns=False):
        nonlocal pages
        if y - needed < limit_y:
            print_footer_page_count(pdf, pages, right_text=f"Folio: {dict_data.get('folio', '')}", x_max=a4_x)
            pdf.showPage()
            pages += 1
            y = draw_header_and_metadata()
            if with_columns:
                y = print_column_headers(y)
            return y
        return y

    last_y = draw_header_and_metadata()
    last_y = print_column_headers(last_y)

    items = dict_data.get("items", [])
    for item in items:
        quantity = item.get("quantity", 0) or 0
        unit_price = item.get("unit_price", 0) or 0
        line_total = item.get("line_total", 0) or 0
        cells = [
            [str(item.get("pos", "") or "")],
            wrap_text_width(item.get("description", ""), _RM_ITEM_COLS[1][1] - 8, font_size - 1),
            [f"{quantity:g}"],
            [str(item.get("udm", "") or "")],
            [f"${unit_price:,.2f}"],
            [f"${line_total:,.2f}"],
        ]
        row_h = max(len(lines) for lines in cells) * (font_size - 1) * 1.25 + 6
        last_y = check_page_break(last_y, needed=row_h, with_columns=True)
        x = _RM_MARGIN
        for (_, w, align), lines in zip(_RM_ITEM_COLS, cells):
            _rm_draw_cell(pdf, x, last_y, w, row_h, lines, font_size - 1, align=align)
            x += w
        last_y -= row_h

    # Totales como continuación de la cuadrícula: label celeste sobre la columna
    # PRECIO UNIT. y monto sobre la columna TOTAL; el conteo de partidas a la izquierda.
    totals_x = _RM_MARGIN + sum(w for _, w, _ in _RM_ITEM_COLS[:4])
    totals_h = font_size * 1.25 + 6
    iva_rate = dict_data.get("iva_rate", 0.16)
    totals_rows = [
        ("SUBTOTAL", dict_data.get("subtotal", 0.0)),
        (f"IVA ({iva_rate:.0%})", dict_data.get("iva", 0.0)),
        ("TOTAL", dict_data.get("total", 0.0)),
    ]
    last_y = check_page_break(last_y, needed=3 * totals_h)
    pdf.setFont(FONT_BOLD, font_size)
    pdf.drawString(_RM_MARGIN, last_y - font_size - 3, f"TOTAL POS. {len(items)}")
    for label, amount in totals_rows:
        _rm_draw_cell(pdf, totals_x, last_y, _RM_ITEM_COLS[4][1], totals_h, [label], font_size, bold=True, fill=True)
        _rm_draw_cell(
            pdf, totals_x + _RM_ITEM_COLS[4][1], last_y, _RM_ITEM_COLS[5][1], totals_h,
            [f"${amount:,.2f}"], font_size, align="right",
        )
        last_y -= totals_h
    last_y -= font_size * 4

    # Firmas: si el midleware bajó de S3 una firma (category=firma) se incrusta
    # arriba de la línea; si no, la línea queda para firmar a mano.
    sign_realizado = dict_data.get("sign_realizado_path")
    sign_recibido = dict_data.get("sign_recibido_path")

    last_y = check_page_break(last_y)
    if sign_realizado:
        _rm_draw_signature_image(pdf, sign_realizado, 180, 340, last_y + 18)
    create_footer_sign(pdf, 200, last_y, "Firma Autorizacion 1")
    last_y -= font_size * (7 if sign_realizado else 4)
    last_y = check_page_break(last_y)
    if sign_recibido:
        _rm_draw_signature_image(pdf, sign_recibido, 180, 340, last_y + 18)
    create_footer_sign(pdf, 200, last_y, "Firma Autorizacion 2")

    print_footer_page_count(pdf, pages, right_text=f"Folio: {dict_data.get('folio', '')}", x_max=a4_x)
    pdf.save()
    return True


def _rm_draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False, align="left"):
    """Celda de cuadrícula estilo casa (ver skill pdf-design): recuadro, texto
    con padding y (opcional) relleno celeste para labels/encabezados.
    ``align="right"`` alinea el texto al borde derecho (columnas numéricas)."""
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_RM_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)  # SIEMPRE restaurar a negro
    else:
        pdf.rect(x, y_top - h, w, h, fill=0, stroke=1)
    pdf.setFont(FONT_BOLD if bold else FONT_REGULAR, font_size)
    text_y = y_top - font_size - 3
    for line in lines:
        if align == "right":
            pdf.drawRightString(x + w - 4, text_y, line)
        else:
            pdf.drawString(x + 4, text_y, line)
        text_y -= font_size * 1.25


def _rm_draw_photo_metadata(pdf, rows, y_top, usable_w, font_size):
    """
    Cuadrícula de metadata de la hoja de fotos: hasta dos pares ``label|valor``
    por fila (label celeste bold + valor). Un par con label y valor vacíos se
    omite (no se dibuja recuadro). Devuelve la ``y`` al terminar el bloque.
    """
    label_w = 60.0
    half_w = usable_w / 2
    value_w = half_w - label_w
    y = y_top
    for row in rows:
        pairs = [(row[0], row[1]), (row[2], row[3])]
        wrapped = {}
        max_lines = 1
        for pi, (label, value) in enumerate(pairs):
            if str(label) == "" and str(value) == "":
                continue
            l_lines = wrap_text_width(label, label_w - 8, font_size, font=FONT_BOLD)
            v_lines = wrap_text_width(value, value_w - 8, font_size)
            wrapped[pi] = (l_lines, v_lines)
            max_lines = max(max_lines, len(l_lines), len(v_lines))
        row_h = max_lines * font_size * 1.25 + 6
        for pi, _ in enumerate(pairs):
            if pi not in wrapped:
                continue
            l_lines, v_lines = wrapped[pi]
            x0 = _RM_MARGIN + pi * half_w
            _rm_draw_cell(pdf, x0, y, label_w, row_h, l_lines, font_size, bold=True, fill=True)
            _rm_draw_cell(pdf, x0 + label_w, y, value_w, row_h, v_lines, font_size)
        y -= row_h
    return y


def _rm_draw_photo_cell(pdf, img_path, x, y_top, w, h, pad=6.0):
    """
    Dibuja el recuadro de una foto y la imagen ajustada dentro preservando
    aspect ratio, centrada. No fatal: si la imagen no se puede leer, deja el
    recuadro vacío.
    """
    pdf.setLineWidth(0.6)
    pdf.rect(x + 2, y_top - h + 2, w - 4, h - 4, fill=0, stroke=1)
    try:
        reader = ImageReader(img_path)
        iw, ih = reader.getSize()
        if not iw or not ih or iw <= 0 or ih <= 0:
            return
        avail_w = w - 4 - 2 * pad
        avail_h = h - 4 - 2 * pad
        ratio = min(avail_w / iw, avail_h / ih)
        draw_w = iw * ratio
        draw_h = ih * ratio
        img_x = x + (w - draw_w) / 2
        img_y = (y_top - h) + (h - draw_h) / 2
        pdf.drawImage(reader, img_x, img_y, width=draw_w, height=draw_h, mask="auto")
    except Exception as e:
        print("erro remission photo cell", str(e))


def FileRemissionPhotosPDF(dict_data: dict):
    """
    Genera la(s) página(s) de EVIDENCIA FOTOGRÁFICA de una remisión (estilo casa
    pdf-design: encabezado Telintec + cuadrícula de metadata celeste + rejilla
    de fotos vertical 2×3 = 6 por página). Cada página es una hoja de evidencia
    autocontenida: repite el encabezado y la metadata, con el/los folio(s) de
    las fotos de esa página. Estructura esperada de ``dict_data``::

        {
            "filename_out": str,
            "date": str,
            "pedido": str,
            "remito": str,
            "plant": str,
            "area": str,
            "location": str,
            "folio": str,                 # folio general (fallback)
            "photos": [
                {"path": str, "folio": str},   # rutas locales ya descargadas
                ...
            ],
        }

    :return: True si generó el documento (aunque no haya fotos: una hoja vacía);
        False ante error irrecuperable.
    """
    file_name = (
        filepath_remission_pdf if dict_data.get("filename_out") is None else dict_data["filename_out"]
    )
    photos = [p for p in dict_data.get("photos", []) if isinstance(p, dict) and p.get("path")]
    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    pdf.setTitle("Evidencia fotografica")
    font_size = 9
    cols, rows = 2, 3
    per_page = cols * rows
    usable_w = a4_x - 2 * _RM_MARGIN
    limit_y = 45.0
    chunks = [photos[i : i + per_page] for i in range(0, len(photos), per_page)] or [[]]
    total_pages = len(chunks)
    for page_idx, chunk in enumerate(chunks, start=1):
        create_header_telintec(
            pdf,
            title="EVIDENCIA FOTOGRÁFICA",
            page_x=a4_x,
            iso_form=7,
            orientation="vertical",
        )
        folios = []
        for p in chunk:
            f = (p.get("folio") or "").strip()
            if f and f not in folios:
                folios.append(f)
        folio_txt = " – ".join(folios) if folios else (dict_data.get("folio") or "")
        meta_rows = [
            ("Fecha", dict_data.get("date", ""), "Pedido", dict_data.get("pedido", "")),
            ("Remito", dict_data.get("remito", ""), "Folio", folio_txt),
            ("Planta", dict_data.get("plant", ""), "Area", dict_data.get("area", "")),
            ("Lugar", dict_data.get("location", ""), "", ""),
        ]
        y = _rm_draw_photo_metadata(pdf, meta_rows, 740.0, usable_w, font_size)
        y_grid_top = y - 10
        grid_h = y_grid_top - limit_y
        row_h = grid_h / rows
        col_w = usable_w / cols
        for idx, p in enumerate(chunk):
            r = idx // cols
            c = idx % cols
            cell_x = _RM_MARGIN + c * col_w
            cell_top = y_grid_top - r * row_h
            _rm_draw_photo_cell(pdf, p.get("path"), cell_x, cell_top, col_w, row_h)
        print_footer_page_count(pdf, page_idx, right_text=f"Folio: {folio_txt}", x_max=a4_x)
        if page_idx < total_pages:
            pdf.showPage()
    pdf.save()
    return True
