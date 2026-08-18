# -*- coding: utf-8 -*-
"""
PDF generico de resumen de una encuesta evaluada con el motor config-driven.

Renderiza el shape uniforme `evaluation` ({total, breakdown recursivo} o
{qualitative}) para CUALQUIER tipo de encuesta — es el fallback de
`generate_pdf_from_json` cuando el tipo no tiene generador dedicado en
`dict_typer_quizz_generator` (modelos nuevos creados via /rrhh/quizz/models).
Formato de la casa (skill pdf-design): cuadricula celeste, tipografia
Helvetica, header Telintec en cada pagina.
"""

__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026  at 12:00 $"

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

_QZ_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE
_QZ_MARGIN = 25.0
_QZ_WIDTH = a4_x - 2 * _QZ_MARGIN
_QZ_LIMIT_Y = 45.0
_QZ_TOP_Y = 740.0


def _qz_wrap(value, width_pt, font_size):
    return wrap_text_width(value, width_pt - 8, font_size)


def _qz_draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False):
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_QZ_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)
    else:
        pdf.rect(x, y_top - h, w, h, fill=0, stroke=1)
    pdf.setFont(FONT_BOLD if bold else FONT_REGULAR, font_size)
    text_y = y_top - font_size - 3
    for line in lines:
        pdf.drawString(x + 4, text_y, line)
        text_y -= font_size * 1.25


def _qz_row_height(lines_per_cell, font_size):
    max_lines = max([len(lines) for lines in lines_per_cell] or [1])
    return max_lines * font_size * 1.25 + 6


def _qz_header_row(pdf, cols, y, font_size):
    """Fila de encabezados celestes. cols = [(titulo, ancho_pt), ...]."""
    cells = [_qz_wrap(title, w, font_size) for title, w in cols]
    h = _qz_row_height(cells, font_size)
    x = _QZ_MARGIN
    for (title, w), lines in zip(cols, cells):
        _qz_draw_cell(pdf, x, y, w, h, lines, font_size, bold=True, fill=True)
        x += w
    return y - h


def _qz_row(pdf, cols, values, y, font_size, fills=None):
    cells = [_qz_wrap(v, w, font_size) for v, (_, w) in zip(values, cols)]
    h = _qz_row_height(cells, font_size)
    x = _QZ_MARGIN
    for i, ((_, w), lines) in enumerate(zip(cols, cells)):
        fill = bool(fills[i]) if fills else False
        _qz_draw_cell(pdf, x, y, w, h, lines, font_size, bold=fill, fill=fill)
        x += w
    return y - h


def _qz_metadata_grid(pdf, metadata, y, font_size):
    """2 pares label|valor por fila (bloque estandar de la casa)."""
    pair_w = _QZ_WIDTH / 2
    label_w = 118.0
    value_w = pair_w - label_w
    entries = [(k, v) for k, v in metadata.items() if v not in (None, "")]
    for i in range(0, len(entries), 2):
        pair_cells = []
        for label, value in entries[i : i + 2]:
            pair_cells.append(
                (_qz_wrap(label, label_w, font_size), _qz_wrap(value, value_w, font_size))
            )
        h = _qz_row_height([c for pair in pair_cells for c in pair], font_size)
        x = _QZ_MARGIN
        for label_lines, value_lines in pair_cells:
            _qz_draw_cell(pdf, x, y, label_w, h, label_lines, font_size, bold=True, fill=True)
            x += label_w
            _qz_draw_cell(pdf, x, y, value_w, h, value_lines, font_size)
            x += value_w
        y -= h
    return y


def _qz_flatten_breakdown(nodes, depth=0):
    """Arbol -> filas (depth, label, score, level_label, actions)."""
    rows = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        level = node.get("level") or {}
        rows.append(
            (
                depth,
                node.get("label") or node.get("id") or "",
                node.get("score"),
                level.get("label") or "",
                node.get("actions") or [],
            )
        )
        rows.extend(_qz_flatten_breakdown(node.get("children"), depth + 1))
    return rows


def create_generic_quizz_report(dict_data):
    """Genera el PDF de resumen. Todo llega resuelto por el midleware:

    dict_data = {
        "path_file": ruta de salida del PDF,
        "title": nombre del modelo de encuesta,
        "folio": texto del pie derecho (p.ej. "Encuesta 123 / tipo 7"),
        "metadata": {label: valor, ...} ya curado (solo se pintan no vacios),
        "evaluation": shape uniforme del motor (scored o qualitative),
    }
    """
    file_out = dict_data["path_file"]
    title = dict_data.get("title") or "Reporte de encuesta"
    folio = dict_data.get("folio") or ""
    evaluation = dict_data.get("evaluation") or {}
    font_size = 8

    pdf = canvas.Canvas(file_out, pagesize=(a4_x, a4_y))
    pages = 1

    def draw_page_header():
        create_header_telintec(
            pdf,
            title=["Recursos Humanos", "Reporte de Encuesta", title],
            page_x=a4_x,
            iso_form=1,
            orientation="vertical",
            title_font=12,
        )

    def new_page(header_cols=None):
        nonlocal pages
        print_footer_page_count(pdf, pages, right_text=folio, x_max=a4_x)
        pdf.showPage()
        pages += 1
        draw_page_header()
        y_new = _QZ_TOP_Y
        if header_cols is not None:
            y_new = _qz_header_row(pdf, header_cols, y_new, font_size)
        return y_new

    draw_page_header()
    y = _qz_metadata_grid(pdf, dict_data.get("metadata") or {}, _QZ_TOP_Y, font_size)
    y -= 10

    if evaluation.get("mode") == "qualitative":
        # -------- Cualitativa: tabla Pregunta | Respuesta --------------------
        cols = [("PREGUNTA", _QZ_WIDTH * 0.55), ("RESPUESTA", _QZ_WIDTH * 0.45)]
        y = _qz_header_row(pdf, cols, y, font_size)
        for qa in evaluation.get("qualitative") or []:
            values = (qa.get("question"), qa.get("answer"))
            cells = [_qz_wrap(v, w, font_size) for v, (_, w) in zip(values, cols)]
            if y - _qz_row_height(cells, font_size) < _QZ_LIMIT_Y:
                y = new_page(cols)
            y = _qz_row(pdf, cols, values, y, font_size)
    else:
        # -------- Resultado general -----------------------------------------
        total = evaluation.get("total") or {}
        level = total.get("level") or {}
        general_cols = [
            ("PUNTAJE", _QZ_WIDTH * 0.25),
            ("PUNTAJE /100", _QZ_WIDTH * 0.25),
            ("NIVEL", _QZ_WIDTH * 0.5),
        ]
        y = _qz_header_row(pdf, [("RESULTADO GENERAL", _QZ_WIDTH)], y, font_size)
        y = _qz_header_row(pdf, general_cols, y, font_size)
        scaled = total.get("scaled")
        y = _qz_row(
            pdf,
            general_cols,
            (
                total.get("score") if total.get("score") is not None else "Sin datos",
                scaled if scaled is not None else "-",
                level.get("label") or "-",
            ),
            y,
            font_size,
        )
        actions = total.get("actions") or []
        if actions:
            action_cols = [("Recomendaciones", 118.0), ("", _QZ_WIDTH - 118.0)]
            text = " | ".join(str(a) for a in actions)
            cells = [
                _qz_wrap("Recomendaciones", 118.0, font_size),
                _qz_wrap(text, _QZ_WIDTH - 118.0, font_size),
            ]
            if y - _qz_row_height(cells, font_size) < _QZ_LIMIT_Y:
                y = new_page()
            y = _qz_row(
                pdf, action_cols, ("Recomendaciones", text), y, font_size, fills=(1, 0)
            )
        y -= 10

        # -------- Desglose (arbol recursivo aplanado con sangria) -----------
        detail_cols = [
            ("SECCIÓN", _QZ_WIDTH - 70.0 - 110.0),
            ("PUNTAJE", 70.0),
            ("NIVEL", 110.0),
        ]
        rows = _qz_flatten_breakdown(evaluation.get("breakdown"))
        if rows:
            if y - 40 < _QZ_LIMIT_Y:
                y = new_page()
            y = _qz_header_row(pdf, [("DESGLOSE POR SECCIÓN", _QZ_WIDTH)], y, font_size)
            y = _qz_header_row(pdf, detail_cols, y, font_size)
            for depth, label, score, level_label, node_actions in rows:
                indent = "  " * depth
                values = (
                    f"{indent}{label}",
                    score if score is not None else "-",
                    level_label or "-",
                )
                cells = [_qz_wrap(v, w, font_size) for v, (_, w) in zip(values, detail_cols)]
                if y - _qz_row_height(cells, font_size) < _QZ_LIMIT_Y:
                    y = new_page(detail_cols)
                y = _qz_row(pdf, detail_cols, values, y, font_size)
                if node_actions:
                    text = f"{indent}Recomendaciones: " + " | ".join(
                        str(a) for a in node_actions
                    )
                    lines = _qz_wrap(text, _QZ_WIDTH, font_size)
                    if y - _qz_row_height([lines], font_size) < _QZ_LIMIT_Y:
                        y = new_page(detail_cols)
                    y = _qz_row(pdf, [("", _QZ_WIDTH)], (text,), y, font_size)

    print_footer_page_count(pdf, pages, right_text=folio, x_max=a4_x)
    pdf.save()
    return True
