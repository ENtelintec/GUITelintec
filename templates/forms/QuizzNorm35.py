# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jul./2024  at 5:53 $"

"""PDF de Norma 035 (tipos 1 y 2) leido directo del resultado del motor
(`evaluation`), sin el shape viejo results/recommendations (P-016,
docs/norma035_pdf.md).

Pagina 1: datos del trabajador, resultado general con su nivel y acciones,
desglose categoria -> dominio -> dimension y acciones por categoria segun su
nivel. Anexo (pagina nueva): respuestas en tabla Pregunta | Respuesta.
Formato de la casa (skill pdf-design): cuadricula celeste, Helvetica, header
Telintec y pie en cada pagina.
"""

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

_N35_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE
_N35_MARGIN = 25.0
_N35_WIDTH = a4_x - 2 * _N35_MARGIN
_N35_LIMIT_Y = 45.0
_N35_TOP_Y = 740.0
_N35_FONT = 8
_N35_LABEL_W = 118.0

# Niveles desde los que la categoria pide intervencion: ahi se imprimen sus
# acciones propias; abajo de eso, solo la necesidad de accion del nivel.
N35_ACTION_LEVELS = ("medio", "alto", "muy_alto")


def _n35_text(value):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _n35_wrap(value, width_pt, font_size, bold=False):
    return wrap_text_width(value, width_pt - 8, font_size, font=FONT_BOLD if bold else FONT_REGULAR)


def _n35_draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False, align="left", indent=0.0):
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_N35_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)
    else:
        pdf.rect(x, y_top - h, w, h, fill=0, stroke=1)
    pdf.setFont(FONT_BOLD if bold else FONT_REGULAR, font_size)
    text_y = y_top - font_size - 3
    for line in lines:
        if align == "right":
            pdf.drawRightString(x + w - 4, text_y, line)
        else:
            pdf.drawString(x + 4 + indent, text_y, line)
        text_y -= font_size * 1.25


def _n35_row_height(lines_per_cell, font_size):
    max_lines = max([len(lines) for lines in lines_per_cell] or [1])
    return max_lines * font_size * 1.25 + 6


def _n35_cells(cols, values, font_size, bold):
    """bold: bool para toda la fila o lista por celda."""
    flags = bold if isinstance(bold, (list, tuple)) else [bold] * len(cols)
    return [_n35_wrap(v, w, font_size, bold=b) for v, (_, w), b in zip(values, cols, flags)]


def _n35_row(pdf, cols, values, y, font_size, bold=False, fill=False, aligns=None, indent=0.0):
    """Una fila de la cuadricula. cols = [(titulo, ancho_pt), ...]; bold y fill
    pueden ser un bool para toda la fila o una lista por celda; `indent` corre
    el texto de la primera celda (sangria del desglose)."""
    first_w = cols[0][1] - indent if cols else 0
    cells = _n35_cells([(cols[0][0], first_w)] + list(cols[1:]), values, font_size, bold) if cols else []
    flags_b = bold if isinstance(bold, (list, tuple)) else [bold] * len(cols)
    flags_f = fill if isinstance(fill, (list, tuple)) else [fill] * len(cols)
    h = _n35_row_height(cells, font_size)
    x = _N35_MARGIN
    for i, ((_, w), lines) in enumerate(zip(cols, cells)):
        align = aligns[i] if aligns else "left"
        _n35_draw_cell(pdf, x, y, w, h, lines, font_size, bold=flags_b[i], fill=flags_f[i], align=align,
                       indent=indent if i == 0 else 0.0)
        x += w
    return y - h


def _n35_height(cols, values, font_size, bold=False, indent=0.0):
    cols = [(cols[0][0], cols[0][1] - indent)] + list(cols[1:])
    return _n35_row_height(_n35_cells(cols, values, font_size, bold), font_size)


def _n35_metadata_grid(pdf, entries, y, font_size):
    """2 pares label|valor por fila (bloque estandar de la casa); los vacios
    no se pintan."""
    entries = [(k, v) for k, v in entries if v not in (None, "", "None")]
    pair_w = _N35_WIDTH / 2
    value_w = pair_w - _N35_LABEL_W
    for i in range(0, len(entries), 2):
        pair_cells = []
        for label, value in entries[i : i + 2]:
            pair_cells.append(
                (_n35_wrap(label, _N35_LABEL_W, font_size, bold=True), _n35_wrap(value, value_w, font_size))
            )
        h = _n35_row_height([c for pair in pair_cells for c in pair], font_size)
        x = _N35_MARGIN
        for label_lines, value_lines in pair_cells:
            _n35_draw_cell(pdf, x, y, _N35_LABEL_W, h, label_lines, font_size, bold=True, fill=True)
            x += _N35_LABEL_W
            _n35_draw_cell(pdf, x, y, value_w, h, value_lines, font_size)
            x += value_w
        y -= h
    return y


def _n35_bullets(items):
    return "\n".join(f"• {item}" for item in items if item)


def _n35_flatten(nodes, depth=0):
    """Arbol del motor -> filas (depth, kind, label, score, level_label, level_key, actions)."""
    rows = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        level = node.get("level") or {}
        rows.append((
            depth,
            node.get("kind") or "",
            node.get("label") or node.get("id") or "",
            node.get("score"),
            level.get("label") or "",
            level.get("key") or "",
            node.get("actions") or [],
        ))
        rows.extend(_n35_flatten(node.get("children"), depth + 1))
    return rows


def _n35_multiline(value, width_pt, font_size, bold=False):
    """Wrap respetando los saltos de linea del texto (bullets)."""
    lines = []
    for part in str(value).split("\n"):
        lines.extend(_n35_wrap(part, width_pt, font_size, bold=bold))
    return lines or [""]


def FileNorma035PDF(dict_data):
    """Genera el PDF. Todo llega resuelto por el midleware (sin BD):

    dict_data = dict(
        path_file = ruta de salida,
        title = nombre del modelo (p. ej. "Norma 035 (<=50) v1"),
        folio = texto del pie derecho,
        metadata = [(label, valor), ...] (los vacios no se pintan),
        evaluation = resultado del motor en modo scored (total, breakdown),
        levels = levels de la rubrica: clave -> dict(label, action_summary, actions),
        answers = engine.answered_sections(data_raw) para el anexo,
    )
    Devuelve True.
    """
    file_out = dict_data["path_file"]
    title = dict_data.get("title") or "Norma 035"
    folio = dict_data.get("folio") or ""
    evaluation = dict_data.get("evaluation") or {}
    levels = dict_data.get("levels") or {}
    answers = dict_data.get("answers") or []
    font_size = _N35_FONT

    pdf = canvas.Canvas(file_out, pagesize=(a4_x, a4_y))
    pdf.setTitle(title)
    pages = 1

    def draw_page_header():
        create_header_telintec(
            pdf,
            title=["Recursos Humanos", "NOM-035-STPS-2018", title],
            page_x=a4_x,
            iso_form=1,
            orientation="vertical",
            title_font=12,
        )

    def new_page(header=None):
        """header: (cols, valores) a repetir arriba de la hoja nueva."""
        nonlocal pages
        print_footer_page_count(pdf, pages, right_text=folio, x_max=a4_x)
        pdf.showPage()
        pages += 1
        draw_page_header()
        y_new = _N35_TOP_Y
        if header is not None:
            cols, values = header
            y_new = _n35_row(pdf, cols, values, y_new, font_size, bold=True, fill=True)
        return y_new

    def section_title(text, y):
        return _n35_row(pdf, [("", _N35_WIDTH)], [text], y, font_size, bold=True, fill=True)

    draw_page_header()
    y = _n35_metadata_grid(pdf, dict_data.get("metadata") or [], _N35_TOP_Y, font_size)
    y -= 10

    # -------- Resultado general ---------------------------------------------------
    total = evaluation.get("total") or {}
    total_level = total.get("level") or {}
    level_info = levels.get(total_level.get("key"), {}) if total_level else {}
    y = section_title("RESULTADO GENERAL", y)
    half = [("", _N35_LABEL_W), ("", _N35_WIDTH / 2 - _N35_LABEL_W), ("", _N35_LABEL_W), ("", _N35_WIDTH / 2 - _N35_LABEL_W)]
    y = _n35_row(
        pdf, half,
        ["Calificación final", _n35_text(total.get("score")), "Nivel de riesgo", total_level.get("label") or "-"],
        y, font_size, bold=[True, False, True, True], fill=[True, False, True, False],
    )
    for label, text in (
        ("Necesidad de acción", level_info.get("action_summary") or ""),
        ("Acciones", _n35_bullets(total.get("actions") or [])),
    ):
        if not text:
            continue
        lines = _n35_multiline(text, _N35_WIDTH - _N35_LABEL_W, font_size)
        h = _n35_row_height([lines], font_size)
        if y - h < _N35_LIMIT_Y:
            y = new_page()
        _n35_draw_cell(pdf, _N35_MARGIN, y, _N35_LABEL_W, h, _n35_wrap(label, _N35_LABEL_W, font_size, True), font_size, bold=True, fill=True)
        _n35_draw_cell(pdf, _N35_MARGIN + _N35_LABEL_W, y, _N35_WIDTH - _N35_LABEL_W, h, lines, font_size)
        y -= h
    y -= 10

    # -------- Desglose categoria -> dominio -> dimension ----------------------------
    detail_cols = [("CATEGORÍA / DOMINIO / DIMENSIÓN", _N35_WIDTH - 70.0 - 90.0), ("PUNTAJE", 70.0), ("NIVEL", 90.0)]
    detail_header = (detail_cols, [c[0] for c in detail_cols])
    rows = _n35_flatten(evaluation.get("breakdown"))
    if rows:
        if y - 50 < _N35_LIMIT_Y:
            y = new_page()
        y = section_title("DESGLOSE POR CATEGORÍA, DOMINIO Y DIMENSIÓN", y)
        y = _n35_row(pdf, detail_cols, detail_header[1], y, font_size, bold=True, fill=True,
                     aligns=["left", "right", "left"])
        for depth, kind, label, score, level_label, _key, _actions in rows:
            values = [label, _n35_text(score), level_label or "-"]
            is_category = depth == 0
            indent = 12.0 * depth
            bold = depth < 2  # categoria y dominio en negritas; la dimension, normal y con sangria
            if y - _n35_height(detail_cols, values, font_size, bold=bold, indent=indent) < _N35_LIMIT_Y:
                y = new_page(detail_header)
            y = _n35_row(pdf, detail_cols, values, y, font_size, bold=bold,
                         fill=[is_category, False, False], aligns=["left", "right", "left"], indent=indent)
        y -= 10

    # -------- Acciones por categoria segun su nivel ---------------------------------
    categories = [r for r in rows if r[0] == 0]
    if categories:
        if y - 50 < _N35_LIMIT_Y:
            y = new_page()
        y = section_title("ACCIONES POR CATEGORÍA (SEGÚN SU NIVEL)", y)
        for _depth, _kind, label, _score, level_label, level_key, actions in categories:
            if level_key in N35_ACTION_LEVELS and actions:
                text = _n35_bullets(actions)
            else:
                text = (levels.get(level_key) or {}).get("action_summary") or "Sin acciones para este nivel."
            head = f"{label} — {level_label or 'sin nivel'}"
            head_lines = _n35_wrap(head, _N35_LABEL_W + 40, font_size, True)
            body_lines = _n35_multiline(text, _N35_WIDTH - _N35_LABEL_W - 40, font_size)
            h = _n35_row_height([head_lines, body_lines], font_size)
            if y - h < _N35_LIMIT_Y:
                y = new_page()
            _n35_draw_cell(pdf, _N35_MARGIN, y, _N35_LABEL_W + 40, h, head_lines, font_size, bold=True, fill=True)
            _n35_draw_cell(pdf, _N35_MARGIN + _N35_LABEL_W + 40, y, _N35_WIDTH - _N35_LABEL_W - 40, h, body_lines, font_size)
            y -= h

    # -------- Anexo: respuestas -----------------------------------------------------
    if answers:
        answer_cols = [("PREGUNTA", _N35_WIDTH * 0.72), ("RESPUESTA", _N35_WIDTH * 0.28)]
        answer_header = (answer_cols, [c[0] for c in answer_cols])
        y = new_page()
        y = section_title("ANEXO — RESPUESTAS DEL CUESTIONARIO", y)
        y = _n35_row(pdf, answer_cols, answer_header[1], y, font_size, bold=True, fill=True)
        for section in answers:
            question = str(section.get("question") or "").strip()
            details = section.get("details")
            if details:
                pairs = [(d.get("subquestion") or "", d.get("answer") or "") for d in details]
            else:
                pairs = [("", section.get("answer") or "")]
            title_values = [question, "" if details else (pairs[0][1] or "Sin respuesta")]
            if y - _n35_height(answer_cols, title_values, font_size, bold=[True, False]) < _N35_LIMIT_Y:
                y = new_page(answer_header)
            y = _n35_row(pdf, answer_cols, title_values, y, font_size, bold=[True, False], fill=[True, False])
            if not details:
                continue
            for subquestion, answer in pairs:
                values = [f"    {subquestion}".rstrip(), answer or "Sin respuesta"]
                if y - _n35_height(answer_cols, values, font_size) < _N35_LIMIT_Y:
                    y = new_page(answer_header)
                y = _n35_row(pdf, answer_cols, values, y, font_size)

    print_footer_page_count(pdf, pages, right_text=folio, x_max=a4_x)
    pdf.save()
    return True
