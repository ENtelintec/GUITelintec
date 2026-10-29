# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/oct./2026  at 18:00 $"

"""PDF del check-in con foto para RH (GET /rrhh/checkins/download/pdf; contrato en
docs/checkin_exportar_y_tramos.md). Cuadrícula celeste de la skill pdf-design:
metadata en la página 1, resumen por día y cada registro con su foto reducida."""

import io

from reportlab.lib.utils import ImageReader
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

_CK_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE
_CK_LINK = (0.0, 0.35, 0.7)
_CK_MARGIN = 25.0
_CK_WIDTH = a4_x - 2 * _CK_MARGIN
_CK_TITLE = "REPORTE DE CHECK-IN"
_CK_ISO_FORM = 1  # FO-GRH-08, el de los reportes de RH (Eva360, encuestas)
_CK_FONT = 8
_CK_TOP_Y = 740.0
_CK_LIMIT_Y = 40.0
_CK_PHOTO_ROW_H = 92.0
_CK_META_LABEL_W = 118.0

# (encabezado, ancho pt, alineación); los anchos suman _CK_WIDTH y el orden sigue
# las listas que arman _ck_summary_values / _ck_event_values.
_CK_SUMMARY_COLS = [
    ("EMPLEADO", 140.0, "left"),
    ("FECHA", 60.0, "left"),
    ("ENTRADA", 48.0, "left"),
    ("SALIDA", 48.0, "left"),
    ("TRAMOS", 141.27, "left"),
    ("HORAS", 58.0, "right"),
    ("ESTADO", 50.0, "left"),
]
_CK_EVENT_COLS = [
    ("FOTO", 80.0, "left"),
    ("EMPLEADO", 135.0, "left"),
    ("FECHA Y HORA", 80.0, "left"),
    ("TIPO", 55.0, "left"),
    ("UBICACIÓN", 130.27, "left"),
    ("ORIGEN", 65.0, "left"),
]


def _ck_hours(hours) -> str:
    """9.62 -> `9 h 37 min`; None -> `—` (mismo formato que la pantalla de RH)."""
    if hours is None:
        return "—"
    total = round(float(hours) * 60)
    h, m = divmod(total, 60)
    if h == 0:
        return f"{m} min"
    return f"{h} h" if m == 0 else f"{h} h {m} min"


def _ck_lines(value, width, bold=False) -> list:
    return wrap_text_width(value, width - 8, _CK_FONT, font=FONT_BOLD if bold else FONT_REGULAR)


def _ck_text_height(n_lines: int) -> float:
    return n_lines * _CK_FONT * 1.25 + 6


def _ck_draw_cell(pdf, x, y_top, w, h, lines, bold=False, fill=False, align="left", color=None):
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_CK_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)
    else:
        pdf.rect(x, y_top - h, w, h, fill=0, stroke=1)
    if color:
        pdf.setFillColorRGB(*color)
    pdf.setFont(FONT_BOLD if bold else FONT_REGULAR, _CK_FONT)
    text_y = y_top - _CK_FONT - 3
    for line in lines:
        if align == "right":
            pdf.drawRightString(x + w - 4, text_y, line)
        else:
            pdf.drawString(x + 4, text_y, line)
        text_y -= _CK_FONT * 1.25
    if color:
        pdf.setFillColorRGB(0, 0, 0)


def _ck_draw_photo(pdf, jpeg: bytes, x, y_top, w, h) -> bool:
    """Foto centrada en la celda (aspect ratio). False si no se pudo dibujar."""
    try:
        reader = ImageReader(io.BytesIO(jpeg))
        iw, ih = reader.getSize()
        ratio = min((w - 8) / iw, (h - 8) / ih)
        draw_w, draw_h = iw * ratio, ih * ratio
        pdf.drawImage(reader, x + (w - draw_w) / 2, y_top - h + (h - draw_h) / 2, width=draw_w, height=draw_h)
        return True
    except Exception:
        return False


def _ck_header_row(pdf, cols, y) -> float:
    h = max(_ck_text_height(len(_ck_lines(name, w, bold=True))) for name, w, _a in cols)
    x = _CK_MARGIN
    for name, w, align in cols:
        _ck_draw_cell(pdf, x, y, w, h, _ck_lines(name, w, bold=True), bold=True, fill=True, align=align)
        x += w
    return y - h


def _ck_section_bar(pdf, text, y) -> float:
    h = _ck_text_height(1)
    _ck_draw_cell(pdf, _CK_MARGIN, y, _CK_WIDTH, h, [text], bold=True, fill=True)
    return y - h


def _ck_metadata(pdf, pairs, y) -> float:
    """2 pares label|valor por fila (4 columnas)."""
    half = _CK_WIDTH / 2
    value_w = half - _CK_META_LABEL_W
    for i in range(0, len(pairs), 2):
        row = pairs[i:i + 2]
        cells = []
        for label, value in row:
            cells.append((_ck_lines(label, _CK_META_LABEL_W, bold=True), _ck_lines(value, value_w)))
        h = max(_ck_text_height(max(len(lab), len(val))) for lab, val in cells)
        x = _CK_MARGIN
        for lab, val in cells:
            _ck_draw_cell(pdf, x, y, _CK_META_LABEL_W, h, lab, bold=True, fill=True)
            _ck_draw_cell(pdf, x + _CK_META_LABEL_W, y, value_w, h, val)
            x += half
        y -= h
    return y


def _ck_summary_values(s: dict) -> list:
    name = s.get("emp_name") or "Empleado"
    return [
        f"{name} (ID {s['emp_id']})",
        s["date"],
        s.get("first_in") or "—",
        s.get("last_out") or "—",
        s.get("segments_text") or "—",
        _ck_hours(s.get("hours")),
        "Incompleto" if s.get("incomplete") else "Completo",
    ]


def _ck_event_values(ev: dict) -> list:
    """Textos de las columnas 2..6 (la 1 es la foto)."""
    stamp = str(ev.get("timestamp") or "")
    if ev.get("lat") is not None and ev.get("lon") is not None:
        location = f"{float(ev['lat']):.6f}, {float(ev['lon']):.6f}"
        if ev.get("accuracy") is not None:
            location += f"\n± {float(ev['accuracy']):.0f} m"
    else:
        location = "Sin ubicación"
    origin = "Manual RH" if ev.get("manual") else "App"
    if ev.get("status") == 1:
        origin += "\nANULADO"
    name = ev.get("emp_name") or "Empleado"
    return [f"{name}\nID {ev['emp_id']}", f"{stamp[:10]}\n{stamp[11:19]}", ev.get("type_label") or "", location, origin]


def FileCheckinsPDF(dict_data: dict):
    """
    Reporte de check-in (vertical, FO-GRH-08). Todo llega resuelto por el
    midleware (MD_Checkin.export_checkins_pdf_api)::

        {
            "filename_out": str | BytesIO,
            "period": "2026-10-01 a 2026-10-28",
            "employee": "Todos" | "ANA PÉREZ (ID 36)",
            "include_cancelled": bool,
            "generated_at": "2026-10-28 17:40",
            "photos_text": "10 de 11 (1 no disponibles)",
            "summary": [build_daily_summary + segments_text],   # empleado, fecha asc
            "events": [_row_to_dict + maps_url],                 # empleado, cronológico
            "photos": dict id -> bytes JPEG reducido,
        }

    Multipágina: header Telintec y fila de encabezados de la tabla en curso en
    cada página; la metadata solo en la 1.
    """
    pdf = canvas.Canvas(dict_data["filename_out"], pagesize=(a4_x, a4_y))
    pdf.setTitle(f"Check-in {dict_data['period']}")
    footer = f"Check-in {dict_data['period']}"
    summary = dict_data.get("summary") or []
    events = dict_data.get("events") or []
    photos = dict_data.get("photos") or {}
    pages = 1

    def draw_page_header():
        create_header_telintec(
            pdf, title=_CK_TITLE, page_x=a4_x, iso_form=_CK_ISO_FORM, orientation="vertical", offset_title=(-18, 0), title_font=14
        )

    def break_page():
        nonlocal pages
        print_footer_page_count(pdf, pages, right_text=footer, x_max=a4_x)
        pdf.showPage()
        pages += 1
        draw_page_header()

    def new_page(cols) -> float:
        break_page()
        return _ck_header_row(pdf, cols, _CK_TOP_Y)

    def start_section(title, cols, first_row_h, y) -> float:
        """Barra + encabezados + la primera fila van juntas en la misma página."""
        needed = 8 + _ck_text_height(1) + _ck_text_height(2) + first_row_h
        if y - needed < _CK_LIMIT_Y:
            break_page()
            y = _CK_TOP_Y
        else:
            y -= 8
        y = _ck_section_bar(pdf, title, y)
        return _ck_header_row(pdf, cols, y)

    draw_page_header()
    cancelled = sum(1 for ev in events if ev.get("status") == 1)
    worked = [s["hours"] for s in summary if s.get("hours") is not None]
    incomplete = sum(1 for s in summary if s.get("incomplete"))
    y = _ck_metadata(pdf, [
        ("Periodo", dict_data["period"]),
        ("Empleado", dict_data["employee"]),
        ("Registros", f"{len(events)}" + (f" ({cancelled} anulados)" if cancelled else "")),
        ("Incluye anulados", "Sí" if dict_data.get("include_cancelled") else "No"),
        ("Días", f"{len(summary)}" + (f" ({incomplete} incompletos)" if incomplete else "")),
        ("Horas trabajadas", _ck_hours(sum(worked)) if worked else "—"),
        ("Fotos", dict_data.get("photos_text") or "—"),
        ("Generado", dict_data["generated_at"]),
    ], _CK_TOP_Y)

    # --- Resumen por día ---
    rows = [_ck_summary_values(s) for s in summary] or [["Sin días con registros válidos", "", "", "", "", "", ""]]
    heights = [max(_ck_text_height(len(_ck_lines(v, w))) for v, (_n, w, _a) in zip(vals, _CK_SUMMARY_COLS)) for vals in rows]
    y = start_section("RESUMEN POR DÍA", _CK_SUMMARY_COLS, heights[0], y)
    for vals, h in zip(rows, heights):
        if y - h < _CK_LIMIT_Y:
            y = new_page(_CK_SUMMARY_COLS)
        x = _CK_MARGIN
        for value, (_n, w, align) in zip(vals, _CK_SUMMARY_COLS):
            _ck_draw_cell(pdf, x, y, w, h, _ck_lines(value, w), align=align)
            x += w
        y -= h

    # --- Registros con foto ---
    photo_w = _CK_EVENT_COLS[0][1]

    def event_height(ev, vals) -> float:
        # +1 línea en UBICACIÓN (índice 3) para el "Ver en mapa"
        counts = [len(_ck_lines(v, w)) + (1 if i == 3 and ev.get("maps_url") else 0)
                  for i, (v, (_n, w, _a)) in enumerate(zip(vals, _CK_EVENT_COLS[1:]))]
        text_h = _ck_text_height(max(counts))
        return max(text_h, _CK_PHOTO_ROW_H) if photos.get(ev["id"]) else max(text_h, _ck_text_height(2))

    prepared = [(ev, _ck_event_values(ev)) for ev in events]
    if prepared:
        y = start_section("REGISTROS", _CK_EVENT_COLS, event_height(*prepared[0]), y)
    for ev, vals in prepared:
        h = event_height(ev, vals)
        if y - h < _CK_LIMIT_Y:
            y = new_page(_CK_EVENT_COLS)
        jpeg = photos.get(ev["id"])
        if jpeg and _ck_draw_photo(pdf, jpeg, _CK_MARGIN, y, photo_w, h):
            pdf.setLineWidth(0.6)
            pdf.rect(_CK_MARGIN, y - h, photo_w, h, fill=0, stroke=1)
        else:
            label = "Manual (sin foto)" if not ev.get("photo_key") else "Foto no disponible"
            _ck_draw_cell(pdf, _CK_MARGIN, y, photo_w, h, _ck_lines(label, photo_w))
        x = _CK_MARGIN + photo_w
        for index, (value, (_n, w, align)) in enumerate(zip(vals, _CK_EVENT_COLS[1:])):
            lines = _ck_lines(value, w)
            url = ev.get("maps_url") if index == 3 else None
            _ck_draw_cell(pdf, x, y, w, h, lines, align=align)
            if url:
                link_y = y - _CK_FONT - 3 - len(lines) * _CK_FONT * 1.25
                pdf.setFillColorRGB(*_CK_LINK)
                pdf.setFont(FONT_REGULAR, _CK_FONT)
                pdf.drawString(x + 4, link_y, "Ver en mapa")
                pdf.setFillColorRGB(0, 0, 0)
                pdf.linkURL(url, (x, y - h, x + w, y), relative=0)
            x += w
        y -= h
    print_footer_page_count(pdf, pages, right_text=footer, x_max=a4_x)
    pdf.save()
    return True
