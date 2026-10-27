# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 27/oct./2026  at 12:00 $"

"""PDF del proceso eva 360 completo (P-017, docs/eva360_pdf.md): datos del
proceso, evaluadores con su resultado, radar de competencias y tabla
competencia x rol. Lo lee RH (lleva nombres de evaluadores).

Formato de la casa (skill pdf-design): reportlab canvas, cuadricula celeste,
Helvetica, header Telintec y pie en cada pagina. El radar se dibuja a mano en
escala fija 1-5 (SpiderChart de reportlab normaliza contra el maximo).
"""

from math import cos, pi, sin

from reportlab.pdfbase.pdfmetrics import stringWidth
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

_E3_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE
_E3_MARGIN = 25.0
_E3_WIDTH = a4_x - 2 * _E3_MARGIN
_E3_LIMIT_Y = 45.0
_E3_TOP_Y = 740.0
_E3_FONT = 8
_E3_SCALE_MAX = 5

# Rol -> (etiqueta, color RGB, trazo, marcador). Trazo y marcador distintos
# para que el radar se lea impreso en blanco y negro.
E3_ROLES = {
    "self": ("Autoevaluación", (0.12, 0.31, 0.62), None, "circle"),
    "superior": ("Jefe Inmediato", (0.85, 0.40, 0.05), (6, 3), "square"),
    "peer": ("Colega", (0.15, 0.55, 0.25), (1.5, 2.5), "triangle"),
    "subordinate": ("Subordinado", (0.50, 0.20, 0.60), (6, 2, 1.5, 2), "diamond"),
}


def _e3_role_label(role):
    return E3_ROLES.get(role, (str(role or "-"),))[0]


def _e3_fmt(value, decimals=1):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


def _e3_wrap(value, width_pt, font_size, bold=False):
    return wrap_text_width(value, width_pt - 8, font_size, font=FONT_BOLD if bold else FONT_REGULAR)


def _e3_draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False, align="left"):
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_E3_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)
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


def _e3_row_height(lines_per_cell, font_size):
    max_lines = max([len(lines) for lines in lines_per_cell] or [1])
    return max_lines * font_size * 1.25 + 6


def _e3_row(pdf, cols, values, y, font_size, header=False, aligns=None):
    """Una fila de la cuadricula. cols = [(titulo, ancho_pt), ...]; header ->
    celdas celestes en bold. Devuelve la y de abajo."""
    cells = [_e3_wrap(v, w, font_size, bold=header) for v, (_, w) in zip(values, cols)]
    h = _e3_row_height(cells, font_size)
    x = _E3_MARGIN
    for i, ((_, w), lines) in enumerate(zip(cols, cells)):
        align = aligns[i] if aligns else "left"
        _e3_draw_cell(pdf, x, y, w, h, lines, font_size, bold=header, fill=header, align=align)
        x += w
    return y - h


def _e3_row_fits(cols, values, y, font_size, header=False):
    cells = [_e3_wrap(v, w, font_size, bold=header) for v, (_, w) in zip(values, cols)]
    return y - _e3_row_height(cells, font_size) >= _E3_LIMIT_Y


def _e3_metadata_grid(pdf, entries, y, font_size):
    """2 pares label|valor por fila (bloque estandar de la casa)."""
    pair_w = _E3_WIDTH / 2
    label_w = 118.0
    value_w = pair_w - label_w
    for i in range(0, len(entries), 2):
        pair_cells = []
        for label, value in entries[i : i + 2]:
            pair_cells.append(
                (_e3_wrap(label, label_w, font_size, bold=True), _e3_wrap(value, value_w, font_size))
            )
        h = _e3_row_height([c for pair in pair_cells for c in pair], font_size)
        x = _E3_MARGIN
        for label_lines, value_lines in pair_cells:
            _e3_draw_cell(pdf, x, y, label_w, h, label_lines, font_size, bold=True, fill=True)
            x += label_w
            _e3_draw_cell(pdf, x, y, value_w, h, value_lines, font_size)
            x += value_w
        y -= h
    return y


def _e3_marker(pdf, kind, x, y, size=2.6):
    if kind == "square":
        pdf.rect(x - size, y - size, 2 * size, 2 * size, fill=1, stroke=0)
    elif kind == "triangle":
        path = pdf.beginPath()
        path.moveTo(x, y + size * 1.2)
        path.lineTo(x - size * 1.1, y - size * 0.8)
        path.lineTo(x + size * 1.1, y - size * 0.8)
        path.close()
        pdf.drawPath(path, fill=1, stroke=0)
    elif kind == "diamond":
        path = pdf.beginPath()
        path.moveTo(x, y + size * 1.3)
        path.lineTo(x + size * 1.1, y)
        path.lineTo(x, y - size * 1.3)
        path.lineTo(x - size * 1.1, y)
        path.close()
        pdf.drawPath(path, fill=1, stroke=0)
    else:
        pdf.circle(x, y, size, fill=1, stroke=0)


def _e3_set_style(pdf, rgb, dash):
    pdf.setStrokeColorRGB(*rgb)
    pdf.setFillColorRGB(*rgb)
    if dash:
        pdf.setDash(list(dash), 0)
    else:
        pdf.setDash([], 0)


def _e3_reset_style(pdf):
    pdf.setStrokeColorRGB(0, 0, 0)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setDash([], 0)
    pdf.setLineWidth(0.6)


def _e3_radar(pdf, competencies, roles, y_top, height):
    """Radar de competencias en escala fija 1-5, una linea por rol respondido.
    Ocupa [y_top - height, y_top]; leyenda a la derecha."""
    n = len(competencies)
    legend_w = 120.0
    area_w = _E3_WIDTH - legend_w
    cx = _E3_MARGIN + area_w / 2
    cy = y_top - height / 2
    radius = min(area_w / 2 - 95, height / 2 - 28)
    angles = [pi / 2 - 2 * pi * i / n for i in range(n)]

    # anillos 1..5 y rayos
    pdf.setLineWidth(0.4)
    pdf.setStrokeColorRGB(0.7, 0.7, 0.7)
    for ring in range(1, _E3_SCALE_MAX + 1):
        r = radius * ring / _E3_SCALE_MAX
        path = pdf.beginPath()
        for i, a in enumerate(angles):
            px, py = cx + r * cos(a), cy + r * sin(a)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.close()
        pdf.drawPath(path, fill=0, stroke=1)
    for a in angles:
        pdf.line(cx, cy, cx + radius * cos(a), cy + radius * sin(a))
    pdf.setFillColorRGB(0.45, 0.45, 0.45)
    pdf.setFont(FONT_REGULAR, 6)
    for ring in range(1, _E3_SCALE_MAX + 1):
        pdf.drawString(cx + 2, cy + radius * ring / _E3_SCALE_MAX + 1.5, str(ring))
    _e3_reset_style(pdf)

    # etiquetas de las competencias
    label_font = 7
    pdf.setFont(FONT_REGULAR, label_font)
    for comp, a in zip(competencies, angles):
        lx = cx + (radius + 10) * cos(a)
        ly = cy + (radius + 10) * sin(a)
        lines = wrap_text_width(comp.get("label") or comp.get("id") or "", 92, label_font)
        block_h = len(lines) * label_font * 1.15
        if sin(a) > 0.3:
            ty = ly + block_h - label_font * 0.9
        elif sin(a) < -0.3:
            ty = ly - label_font
        else:
            ty = ly + block_h / 2 - label_font * 0.8
        for line in lines:
            w = stringWidth(line, FONT_REGULAR, label_font)
            if cos(a) > 0.2:
                tx = lx
            elif cos(a) < -0.2:
                tx = lx - w
            else:
                tx = lx - w / 2
            pdf.drawString(tx, ty, line)
            ty -= label_font * 1.15

    # una linea por rol respondido
    for role in roles:
        _label, rgb, dash, marker = E3_ROLES.get(role, (role, (0, 0, 0), None, "circle"))
        points = []
        for comp, a in zip(competencies, angles):
            value = (comp.get("by_role") or {}).get(role)
            if value is None:
                points.append(None)
                continue
            r = radius * max(0.0, min(float(value), _E3_SCALE_MAX)) / _E3_SCALE_MAX
            points.append((cx + r * cos(a), cy + r * sin(a)))
        _e3_set_style(pdf, rgb, dash)
        pdf.setLineWidth(1.4)
        valid = [p for p in points if p is not None]
        if len(valid) == len(points) and valid:
            path = pdf.beginPath()
            path.moveTo(*valid[0])
            for p in valid[1:]:
                path.lineTo(*p)
            path.close()
            pdf.drawPath(path, fill=0, stroke=1)
        pdf.setDash([], 0)
        for p in valid:
            _e3_marker(pdf, marker, p[0], p[1])
        _e3_reset_style(pdf)

    # leyenda
    lx = _E3_MARGIN + area_w + 6
    ly = y_top - 14
    pdf.setFont(FONT_BOLD, _E3_FONT)
    pdf.drawString(lx, ly, "Perspectivas")
    ly -= 14
    for role in roles:
        label, rgb, dash, marker = E3_ROLES.get(role, (role, (0, 0, 0), None, "circle"))
        _e3_set_style(pdf, rgb, dash)
        pdf.setLineWidth(1.4)
        pdf.line(lx, ly + 3, lx + 26, ly + 3)
        pdf.setDash([], 0)
        _e3_marker(pdf, marker, lx + 13, ly + 3)
        _e3_reset_style(pdf)
        pdf.setFont(FONT_REGULAR, _E3_FONT)
        pdf.drawString(lx + 32, ly, label)
        ly -= 14
    pdf.setFont(FONT_REGULAR, 6.5)
    pdf.setFillColorRGB(0.35, 0.35, 0.35)
    pdf.drawString(lx, ly - 2, "Escala 1 (peor) a 5 (mejor)")
    _e3_reset_style(pdf)
    return y_top - height


def FileEva360ProcessPDF(dict_data):
    """Genera el PDF del proceso. Todo llega resuelto por el midleware (sin BD):

    dict_data = dict(
        path_file = ruta de salida,
        evaluation_id = str,
        evaluated_name = str, evaluated_position = str, date_limit = str,
        status_eval = "open" | "complete",
        assigned = int, answered = int,
        general = float | None (score /100),
        expected_roles = [rol, ...] en orden,
        raters = [dict(role, name, position, answered, score_100, raw_total), ...],
        competencies = [dict(id, label, by_role=dict(rol=valor 1-5), average), ...],
        issued = fecha de emision (str),
    )
    Devuelve True.
    """
    file_out = dict_data["path_file"]
    evaluation_id = str(dict_data.get("evaluation_id") or "")
    folio = f"Eva 360 {evaluation_id[:8]}"
    status_open = dict_data.get("status_eval", "open") != "complete"
    assigned = int(dict_data.get("assigned") or 0)
    answered = int(dict_data.get("answered") or 0)
    expected_roles = [r for r in (dict_data.get("expected_roles") or []) if r]
    raters = dict_data.get("raters") or []
    answered_roles = [r["role"] for r in raters if r.get("answered")]
    radar_roles = [r for r in expected_roles if r in answered_roles] + [
        r for r in answered_roles if r not in expected_roles
    ]
    competencies = dict_data.get("competencies") or []
    font_size = _E3_FONT

    pdf = canvas.Canvas(file_out, pagesize=(a4_x, a4_y))
    pdf.setTitle(f"Evaluación 360° — {dict_data.get('evaluated_name') or ''}")
    pages = 1

    def draw_page_header():
        create_header_telintec(
            pdf,
            title=["Recursos Humanos", "Evaluación 360°", str(dict_data.get("evaluated_name") or "")],
            page_x=a4_x,
            iso_form=1,
            orientation="vertical",
            title_font=12,
        )

    def new_page(cols=None):
        nonlocal pages
        print_footer_page_count(pdf, pages, right_text=folio, x_max=a4_x)
        pdf.showPage()
        pages += 1
        draw_page_header()
        y_new = _E3_TOP_Y
        if cols is not None:
            y_new = _e3_row(pdf, cols, [c[0] for c in cols], y_new, font_size, header=True)
        return y_new

    draw_page_header()
    y = _E3_TOP_Y
    progress = f"{answered} de {assigned} perspectivas respondidas"
    if status_open:
        banner = [("", _E3_WIDTH)]
        y = _e3_row(pdf, banner, [f"PRELIMINAR — {progress}"], y, 9, header=True, aligns=["center"])
        y -= 4
    y = _e3_metadata_grid(
        pdf,
        [
            ("Evaluado", dict_data.get("evaluated_name") or "-"),
            ("Puesto", dict_data.get("evaluated_position") or "-"),
            ("Fecha límite", dict_data.get("date_limit") or "-"),
            ("Estado", "Abierto (preliminar)" if status_open else "Cerrado"),
            ("Respondidas", progress),
            ("Fecha de emisión", dict_data.get("issued") or "-"),
            ("Proceso", evaluation_id or "-"),
            ("Resultado general", f"{_e3_fmt(dict_data.get('general'))} / 100"),
        ],
        y,
        font_size,
    )
    y -= 10

    # -------- Evaluadores y resultado por perspectiva ---------------------------
    rater_cols = [
        ("ROL", 82.0),
        ("EVALUADOR", 150.0),
        ("PUESTO", _E3_WIDTH - 82.0 - 150.0 - 58.0 - 72.0 - 60.0),
        ("RESPONDIÓ", 58.0),
        ("PUNTAJE /100", 72.0),
        ("CRUDO /45", 60.0),
    ]
    aligns = ["left", "left", "left", "center", "right", "right"]
    y = _e3_row(pdf, [("EVALUADORES Y RESULTADO POR PERSPECTIVA", _E3_WIDTH)], ["EVALUADORES Y RESULTADO POR PERSPECTIVA"], y, font_size, header=True)
    y = _e3_row(pdf, rater_cols, [c[0] for c in rater_cols], y, font_size, header=True, aligns=aligns)
    order = {role: i for i, role in enumerate(expected_roles)}
    for rater in sorted(raters, key=lambda r: order.get(r.get("role"), len(order))):
        values = [
            _e3_role_label(rater.get("role")),
            rater.get("name") or "-",
            rater.get("position") or "-",
            "Sí" if rater.get("answered") else "Pendiente",
            _e3_fmt(rater.get("score_100")),
            _e3_fmt(rater.get("raw_total"), 0),
        ]
        if not _e3_row_fits(rater_cols, values, y, font_size):
            y = new_page(rater_cols)
        y = _e3_row(pdf, rater_cols, values, y, font_size, aligns=aligns)
    general_cols = [("", _E3_WIDTH - 124.0), ("", 124.0)]
    y = _e3_row(
        pdf,
        general_cols,
        [f"RESULTADO GENERAL /100 (promedio de las {answered} perspectivas respondidas)", _e3_fmt(dict_data.get("general"))],
        y,
        font_size,
        header=True,
        aligns=["left", "right"],
    )
    y -= 12

    # -------- Radar -----------------------------------------------------------------
    radar_h = 230.0
    if competencies and radar_roles:
        if y - radar_h - 16 < _E3_LIMIT_Y:
            y = new_page()
        y = _e3_row(pdf, [("RADAR DE COMPETENCIAS", _E3_WIDTH)], ["RADAR DE COMPETENCIAS"], y, font_size, header=True)
        y = _e3_radar(pdf, competencies, radar_roles, y - 4, radar_h)
        y -= 10

    # -------- Competencia x rol -----------------------------------------------------
    table_roles = expected_roles or radar_roles
    role_w = 84.0
    avg_w = 58.0
    comp_cols = [("COMPETENCIA", _E3_WIDTH - role_w * len(table_roles) - avg_w)]
    comp_cols += [(_e3_role_label(r).upper(), role_w) for r in table_roles]
    comp_cols += [("PROMEDIO", avg_w)]
    comp_aligns = ["left"] + ["right"] * (len(table_roles) + 1)
    comp_rows = []
    for comp in competencies:
        by_role = comp.get("by_role") or {}
        values = [comp.get("label") or comp.get("id") or "-"]
        values += [_e3_fmt(by_role.get(r), 0) if r in by_role else "-" for r in table_roles]
        values += [_e3_fmt(comp.get("average"), 2)]
        comp_rows.append(values)
    if comp_rows:
        # La tabla va completa en una hoja si cabe en una: nada de renglones sueltos.
        table_h = 18 + _e3_row_height([_e3_wrap(c[0], c[1], font_size, bold=True) for c in comp_cols], font_size)
        table_h += sum(
            _e3_row_height([_e3_wrap(v, w, font_size) for v, (_, w) in zip(values, comp_cols)], font_size)
            for values in comp_rows
        ) + 14
        if y - table_h < _E3_LIMIT_Y and _E3_TOP_Y - table_h >= _E3_LIMIT_Y:
            y = new_page()
        elif y - 60 < _E3_LIMIT_Y:
            y = new_page()
        y = _e3_row(pdf, [("COMPETENCIAS POR PERSPECTIVA (1 a 5)", _E3_WIDTH)], ["COMPETENCIAS POR PERSPECTIVA (1 a 5)"], y, font_size, header=True)
        y = _e3_row(pdf, comp_cols, [c[0] for c in comp_cols], y, font_size, header=True, aligns=comp_aligns)
        for values in comp_rows:
            if not _e3_row_fits(comp_cols, values, y, font_size):
                y = new_page(comp_cols)
            y = _e3_row(pdf, comp_cols, values, y, font_size, aligns=comp_aligns)
        note = "\"-\" = perspectiva pendiente. El promedio de cada competencia va sobre las perspectivas respondidas."
        pdf.setFont(FONT_REGULAR, 6.5)
        if y - 12 < _E3_LIMIT_Y:
            y = new_page()
        pdf.drawString(_E3_MARGIN, y - 10, note)

    print_footer_page_count(pdf, pages, right_text=folio, x_max=a4_x)
    pdf.save()
    return True
