# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/feb./2024  at 15:54 $"

import textwrap
import time

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from templates.controllers.sgi.iso_formats_controller import get_iso_format_headers
from templates.misc.Functions_Files import write_log_file
from static.constants import log_file_sgi_formats

a4_x = 595.27
a4_y = 841.89
image_logo = "img/logo_docs.png"

# Tipografía de la casa: sans-serif contemporánea. Antes era Courier
# (monospace); como Helvetica es proporcional, el wrapping y las posiciones
# derivadas del texto se calculan con el ancho real (stringWidth /
# wrap_text_width), no con conteo de caracteres.
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# --- Codigo / vigencia del formato ISO en el encabezado -------------------------
# Antes venia de files/settings.json["formats"]; desde docs/iso_formats_crud.md se
# lee del catalogo sql_telintec_mod_admin.iso_formats (el CRUD de SGI lo edita).
# Excepcion deliberada a "forms no tocan BD": create_header_telintec no recibe
# data_token, asi que se lee sin token (BD del environment) con cache de
# modulo; el CRUD la invalida al escribir. ISO_FORM_IDS_IN_CODE = ids que los PDFs
# piden por literal (iso_form=N): no se pueden borrar del catalogo, solo retirar.
ISO_FORM_IDS_IN_CODE = frozenset({1, 2, 4, 7, 8, 14, 15, 16})  # 14 remision OCD, 15 cotizacion CISCO, 16 OC
_ISO_CACHE_TTL = 300  # segundos
_iso_cache: dict = {"at": 0.0, "rows": {}}


def invalidate_iso_formats_cache():
    _iso_cache["at"] = 0.0


def iso_format_header(iso_form) -> tuple[str, str]:
    """('FO-ALM-01 R1', '2024-06-14') para el id; ('', '') si no existe. Con la BD
    caida reusa la ultima lectura buena y, si no hay, deja el encabezado en blanco
    (el PDF sale igual) y lo anota en el log."""
    now = time.time()
    if now - _iso_cache["at"] > _ISO_CACHE_TTL:
        flag, error, rows = get_iso_format_headers()
        if flag:
            _iso_cache["rows"] = {
                int(r[0]): (f"{r[1]} {r[2]}".strip(), r[3].isoformat() if hasattr(r[3], "isoformat") else (str(r[3]) if r[3] else ""))
                for r in rows
            }
            _iso_cache["at"] = now
        else:
            write_log_file(log_file_sgi_formats, f"iso_formats no disponible para el encabezado del PDF ({error}); se usa cache")
            _iso_cache["at"] = now - _ISO_CACHE_TTL + 30  # reintenta en 30 s
    try:
        return _iso_cache["rows"].get(int(iso_form), ("", ""))
    except (ValueError, TypeError):
        return "", ""


def wrap_text_width(value, width_pt, font_size, font=FONT_REGULAR):
    """
    Word-wrap por ancho real en puntos (``pdfmetrics.stringWidth``), apto para
    fuentes proporcionales. Una palabra sola más ancha que ``width_pt`` se
    parte por caracteres. Devuelve siempre al menos una línea (puede ser "").
    """
    text = "" if value is None else str(value)
    if width_pt <= 0:
        return [text]
    lines = []
    for raw_line in text.splitlines() or [""]:
        words = raw_line.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            candidate = f"{current} {word}" if current else word
            if stringWidth(candidate, font, font_size) <= width_pt:
                current = candidate
                continue
            if current:
                lines.append(current)
            piece = ""
            for char in word:
                if piece and stringWidth(piece + char, font, font_size) > width_pt:
                    lines.append(piece)
                    piece = char
                else:
                    piece += char
            current = piece
        lines.append(current)
    return lines or [""]


def print_footer_page_count(pdf, page, font_size=6, right_text="", x_max=a4_x):
    """
    :param x_max:
    :param right_text:
    :param pdf:
    :param page:
    :param font_size:
    :return:
    """
    pdf.setFont(FONT_REGULAR, font_size)
    pdf.drawString(5, 5, f"Página {page}")
    if right_text != "":
        pdf.drawRightString(x_max - 5, 5, right_text)


def wrap_text(text, width=30):
    return "\n".join(textwrap.wrap(text, width=width))


def create_header_telintec(
    master: canvas.Canvas,
    img=None,
    title=None,
    page_x=841.89,
    date_int=None,
    iso_form=1,
    orientation="vertical",
    title_font=None,
    offset_title=(0, 0),
):
    position_header_y = 770 if orientation == "vertical" else 535
    position_header_x = 25 if orientation == "vertical" else 25
    height_logo = 30
    title_height = 16 if title_font is None else title_font
    codes_h_height = 10
    codes_width = 150  # right codes and emision width
    start_box_x = 10 if orientation == "vertical" else 10
    height_box = 50
    pady = 10
    padx = 15
    width_logo = 106.6
    img = img if img is not None else image_logo
    # header
    # bottom line
    master.line(
        start_box_x,
        position_header_y + height_box - pady,
        page_x - start_box_x,
        position_header_y + height_box - pady,
    )
    # first vertical line
    master.line(
        start_box_x,
        position_header_y + height_box - pady,
        start_box_x,
        position_header_y - pady,
    )
    # last vertical line
    master.line(
        page_x - start_box_x,
        position_header_y + height_box - pady,
        page_x - start_box_x,
        position_header_y - pady,
    )
    # top line
    master.line(
        start_box_x,
        position_header_y - pady,
        page_x - start_box_x,
        position_header_y - pady,
    )
    # first separator
    master.line(
        start_box_x + (position_header_x - start_box_x) + width_logo + padx,
        position_header_y + height_box - pady,
        start_box_x + (position_header_x - start_box_x) + width_logo + padx,
        position_header_y - pady,
    )
    # second separator
    master.line(
        page_x - start_box_x - codes_width - padx,
        position_header_y + height_box - pady,
        page_x - start_box_x - codes_width - padx,
        position_header_y - pady,
    )
    # logo
    master.drawInlineImage(
        img,
        position_header_x,
        position_header_y,
        height=30,
        width=106.6,
        preserveAspectRatio=False,
        showBoundary=False,
    )
    if isinstance(title, str):
        title = title.upper()
        master.setFont(FONT_BOLD, title_height)
        master.drawCentredString(
            page_x / 2 + offset_title[0],
            position_header_y + height_logo / 2 - title_height / 2 + offset_title[1],
            title.upper(),
        )
    else:
        # pyrefly: ignore [bad-argument-type]
        nlines = len(title)
        x_title = page_x / 2 + offset_title[0]
        y_title = (position_header_y + height_logo / 2 + ((nlines - 1) * title_height) / 2) + offset_title[1]
        # pyrefly: ignore [bad-argument-type]
        for index, line in enumerate(title):
            master.setFont(FONT_BOLD, title_height - 2 * index)
            master.drawCentredString(x_title, y_title, line)
            y_title -= title_height
    master.setFont(FONT_REGULAR, codes_h_height)
    code_label, emission_date = iso_format_header(iso_form)
    master.drawString(
        page_x - codes_width - padx,
        position_header_y + height_logo - codes_h_height,
        f"Codigo: {code_label}",
    )
    master.drawString(
        page_x - codes_width - padx,
        position_header_y,
        f"I. Vigencia: {emission_date}",
    )


def create_footer_sign(pdf, position_x, position_y, text="Firma"):
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(position_x, position_y, text)
    pdf.line(
        position_x - 20,
        position_y + 15,
        position_x + stringWidth(text, FONT_REGULAR, 10) + 20,
        position_y + 15,
    )
