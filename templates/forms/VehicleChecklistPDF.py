# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 15/ago./2026  at 10:00 $"

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

# Página horizontal: el ancho útil es el largo de la A4 vertical.
_CHV_PAGE_X = a4_y
_CHV_PAGE_Y = a4_x
_CHV_MARGIN = 25.0
_CHV_WIDTH = _CHV_PAGE_X - 2 * _CHV_MARGIN
# Réplica del FO-CDA-03 R3: barras azul brillante con texto blanco (muestreado
# del formato oficial, #00AFEF), a diferencia del celeste de los demás PDFs.
_CHV_AZUL = (0.0, 0.686, 0.937)
_CHV_GRIS = (0.45, 0.45, 0.45)
_CHV_LIMIT_Y = 15.0

# Catálogo fijo del FO-CDA-03 R3: 6 grupos de columnas con 6 conceptos cada
# uno, en su posición oficial. Los dos últimos grupos llevan columna N/A.
# El marcado se resuelve por lookup del label capturado en la BD; un concepto
# sin dato queda con las casillas en blanco.
_CHV_GROUPS = [
    (
        False,
        [
            "Espejo lateral derecho",
            "Espejo lateral izquierdo",
            "Espejo retrovisor",
            "Tapetes",
            "Limpiadores parabrisas",
            "Claxon",
        ],
    ),
    (
        False,
        [
            "Viseras",
            "Cinturones de seguridad",
            "Parabrisas",
            "Cristales de puertas (laterales)",
            "Nivel de fluidos",
            "Faros y luces",
        ],
    ),
    (
        False,
        [
            "Parrilla frontal",
            "Defensas",
            "Manija o botones eleva vidrios",
            "Estado Caucho repuesto",
            "Manijas puertas int/ext",
            "Extintor",
        ],
    ),
    (
        False,
        [
            "Tapón de gasolina o tapa",
            "Sticker de accesos",
            "Sticker de accesos Telintec",
            "Llave o cruceta y gato",
            "Triángulo de seguridad",
            "Empaques de puertas",
        ],
    ),
    (
        True,
        [
            "Estado de llantas y birlos de seguridad",
            "tarjeta de gasolina o TAG",
            "Placa delantera o trasera",
            "Aire acondicionado",
            "Antena",
            "Torreta",
        ],
    ),
    (
        True,
        [
            "Radio/CD",
            "Porta escalera o RollBar",
            "Sirena de reversa",
            "Topes de bloqueo",
            "Eslingas o matracas",
            "Cables paso de corrientes",
        ],
    ),
]

# Casillas de TIPO DE VEHICULO en el orden oficial; vehicle_type es el índice.
_CHV_VEHICLE_TYPES = [
    ("img/checklist_sedan.png", "SEDÁN"),
    ("img/checklist_pickup.png", "PICK-UP"),
    ("img/checklist_van.png", "VAN"),
]


def _chv_norm(label):
    return " ".join(str(label or "").split()).lower()


def _chv_state(value):
    """Estado de un accesorio capturado -> 'bien' | 'mal' | 'na' | None."""
    text = _chv_norm(value)
    if text == "bien":
        return "bien"
    if text == "mal":
        return "mal"
    if text in ("n/a", "na", "no aplica"):
        return "na"
    return None


def _chv_wrap(value, width_pt, font_size):
    return wrap_text_width(value, width_pt - 8, font_size)


def _chv_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False):
    """Celda de la cuadrícula. `fill=True` la pinta con el azul del formato y
    el texto va en blanco bold (los labels del FO-CDA-03 son así); sin fill es
    celda blanca con texto negro."""
    pdf.setLineWidth(0.6)
    if fill:
        pdf.setFillColorRGB(*_CHV_AZUL)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(1, 1, 1)
    else:
        pdf.rect(x, y_top - h, w, h, fill=0, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont(FONT_BOLD if bold else FONT_REGULAR, font_size)
    text_y = y_top - font_size - 3
    for line in lines:
        pdf.drawString(x + 4, text_y, line)
        text_y -= font_size * 1.25
    pdf.setFillColorRGB(0, 0, 0)


def _chv_section_bar(pdf, y_top, text, font_size=8):
    """Barra de sección azul a todo lo ancho con el título centrado en blanco."""
    h = font_size * 1.25 + 4
    pdf.setLineWidth(0.6)
    pdf.setFillColorRGB(*_CHV_AZUL)
    pdf.rect(_CHV_MARGIN, y_top - h, _CHV_WIDTH, h, fill=1, stroke=1)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont(FONT_BOLD, font_size)
    pdf.drawCentredString(_CHV_PAGE_X / 2, y_top - h + (h - font_size) / 2 + 1, text)
    pdf.setFillColorRGB(0, 0, 0)
    return y_top - h


def _chv_draw_check(pdf, cx, cy, size):
    """Palomita dibujada con dos trazos (no depende de glifos de fuentes)."""
    pdf.setLineWidth(1.1)
    pdf.line(cx - size * 0.32, cy + size * 0.02, cx - size * 0.08, cy - size * 0.30)
    pdf.line(cx - size * 0.08, cy - size * 0.30, cx + size * 0.36, cy + size * 0.34)


def _chv_checkbox(pdf, x, y_center, size, checked):
    pdf.setLineWidth(0.6)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.rect(x, y_center - size / 2, size, size, fill=1, stroke=1)
    pdf.setFillColorRGB(0, 0, 0)
    if checked:
        _chv_draw_check(pdf, x + size / 2, y_center, size)


def _chv_pairs_row(pdf, y_top, pairs, font_size=7):
    """Fila de pares label|valor; los anchos vienen en cada par y deben sumar
    el ancho útil. La fila crece con el wrap del valor más largo."""
    cells = []
    max_lines = 1
    for label, value, label_w, value_w in pairs:
        value_lines = _chv_wrap(value, value_w, font_size)
        cells.append((label, value_lines, label_w, value_w))
        max_lines = max(max_lines, len(value_lines))
    h = max_lines * font_size * 1.25 + 5
    x = _CHV_MARGIN
    for label, value_lines, label_w, value_w in cells:
        _chv_cell(pdf, x, y_top, label_w, h, [label], font_size, bold=True, fill=True)
        _chv_cell(pdf, x + label_w, y_top, value_w, h, value_lines, font_size)
        x += label_w + value_w
    return y_top - h


def _chv_yes_no_row(pdf, y_top, groups, font_size=7):
    """Fila de grupos label azul + casillas SI/NO. `groups`:
    [(label, valor 1|0|None, label_w, value_w), ...]; None = sin capturar
    (ambas casillas en blanco)."""
    h = font_size * 1.25 + 6
    box = 8.0
    x = _CHV_MARGIN
    for label, value, label_w, value_w in groups:
        _chv_cell(pdf, x, y_top, label_w, h, [label], font_size, bold=True, fill=True)
        _chv_cell(pdf, x + label_w, y_top, value_w, h, [""], font_size)
        y_center = y_top - h / 2
        _chv_checkbox(pdf, x + label_w + 6, y_center, box, value == 1)
        pdf.setFont(FONT_REGULAR, font_size - 1)
        pdf.drawString(x + label_w + 6 + box + 2, y_center - (font_size - 1) / 2 + 1, "SI")
        _chv_checkbox(pdf, x + label_w + 6 + box + 18, y_center, box, value == 0)
        pdf.setFont(FONT_REGULAR, font_size - 1)
        pdf.drawString(
            x + label_w + 6 + 2 * box + 20, y_center - (font_size - 1) / 2 + 1, "NO"
        )
        x += label_w + value_w
    return y_top - h


def _chv_accessories_table(pdf, y_top, states, font_size=6):
    """
    Tabla de ESTADO DE ACCESORIOS Y HERRAMIENTAS: los 6 grupos del catálogo
    oficial lado a lado (DESCRIPCIÓN | BIEN | MAL, últimos dos grupos con N/A),
    filas de alto fijo para que los grupos queden alineados. `states` es un
    dict {label normalizado: 'bien'|'mal'|'na'}.
    """
    mark_w = 15.0
    desc_w_plain = 90.0
    plain_total = 4 * (desc_w_plain + 2 * mark_w)
    desc_w_na = (_CHV_WIDTH - plain_total) / 2 - 3 * mark_w
    head_h = 10.0
    row_h = 2 * font_size * 1.25 + 3.0
    x = _CHV_MARGIN
    for has_na, labels in _CHV_GROUPS:
        desc_w = desc_w_na if has_na else desc_w_plain
        marks = ["BIEN", "MAL"] + (["N/A"] if has_na else [])
        # encabezados del grupo (texto centrado, sin padding: las columnas
        # de marca son angostas)
        pdf.setFillColorRGB(*_CHV_AZUL)
        pdf.setLineWidth(0.6)
        pdf.rect(x, y_top - head_h, desc_w, head_h, fill=1, stroke=1)
        mx = x + desc_w
        for _ in marks:
            pdf.rect(mx, y_top - head_h, mark_w, head_h, fill=1, stroke=1)
            mx += mark_w
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont(FONT_BOLD, 5.5)
        pdf.drawCentredString(x + desc_w / 2, y_top - head_h + 2.5, "DESCRIPCIÓN")
        pdf.setFont(FONT_BOLD, 4.5)
        mx = x + desc_w
        for mark in marks:
            pdf.drawCentredString(mx + mark_w / 2, y_top - head_h + 3, mark)
            mx += mark_w
        pdf.setFillColorRGB(0, 0, 0)
        # filas del grupo
        y = y_top - head_h
        for label in labels:
            lines = _chv_wrap(label, desc_w, font_size)[:2]
            _chv_cell(pdf, x, y, desc_w, row_h, lines, font_size)
            state = states.get(_chv_norm(label))
            mx = x + desc_w
            for mark in marks:
                _chv_cell(pdf, mx, y, mark_w, row_h, [""], font_size)
                checked = (
                    (mark == "BIEN" and state == "bien")
                    or (mark == "MAL" and state == "mal")
                    or (mark == "N/A" and state == "na")
                )
                if checked:
                    _chv_draw_check(pdf, mx + mark_w / 2, y - row_h / 2, 8)
                mx += mark_w
            y -= row_h
        x += desc_w + len(marks) * mark_w
    return y_top - head_h - 6 * row_h


def _chv_extra_accessories(pdf, y_top, extras, font_size=6):
    """Accesorios capturados fuera del catálogo oficial: filas DESCRIPCIÓN |
    ESTADO al final de la tabla (solo si existen)."""
    desc_w = 300.0
    state_w = 100.0
    y = y_top
    for label, value in extras:
        lines = _chv_wrap(label, desc_w, font_size)
        h = max(len(lines), 1) * font_size * 1.25 + 4
        _chv_cell(pdf, _CHV_MARGIN, y, desc_w, h, lines, font_size)
        _chv_cell(
            pdf, _CHV_MARGIN + desc_w, y, state_w, h, [str(value or "")], font_size
        )
        y -= h
    return y


def _chv_signature_image(pdf, img_path, x, y_top, w, h, pad=4.0):
    """Incrusta la firma centrada en su recuadro preservando aspect ratio.
    No fatal: si la imagen no se puede leer, el recuadro queda para firma a
    mano."""
    try:
        reader = ImageReader(img_path)
        iw, ih = reader.getSize()
        if not iw or not ih or iw <= 0 or ih <= 0:
            return
        scale = min((w - 2 * pad) / iw, (h - 2 * pad) / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        pdf.drawImage(
            reader,
            x + (w - draw_w) / 2,
            (y_top - h) + (h - draw_h) / 2,
            width=draw_w,
            height=draw_h,
            mask="auto",
        )
    except Exception as e:
        print("erro chv signature image", str(e))


def _chv_vehicle_type_section(pdf, y_top, vehicle_type, height=100.0):
    """Tres recuadros con la silueta oficial (sedán / pickup / van) y su
    casilla; se marca la que corresponde a `vehicle_type` (0/1/2)."""
    cell_w = _CHV_WIDTH / 3
    x = _CHV_MARGIN
    for idx, (asset, _label) in enumerate(_CHV_VEHICLE_TYPES):
        pdf.setLineWidth(0.6)
        pdf.rect(x, y_top - height, cell_w, height, fill=0, stroke=1)
        _chv_checkbox(pdf, x + 6, y_top - 12, 10.0, vehicle_type == idx)
        try:
            reader = ImageReader(asset)
            iw, ih = reader.getSize()
            scale = min((cell_w - 34) / iw, (height - 10) / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            pdf.drawImage(
                reader,
                x + 24 + (cell_w - 34 - draw_w) / 2,
                (y_top - height) + (height - draw_h) / 2,
                width=draw_w,
                height=draw_h,
            )
        except Exception as e:
            print("erro chv vehicle type image", str(e))
        x += cell_w
    return y_top - height


def _chv_signatures_section(pdf, y_top, realizado, recibido, font_size=7):
    """Bloque REALIZADO POR | RECIBIDO POR: barra azul por mitad, recuadro de
    firma (imagen incrustada si existe) y fila NOMBRE COMPLETO."""
    half = _CHV_WIDTH / 2
    bar_h = font_size * 1.25 + 4
    sign_h = 62.0
    name_h = font_size * 1.25 + 5
    for i, (title, entry) in enumerate(
        [("REALIZADO POR", realizado), ("RECIBIDO POR:", recibido)]
    ):
        x = _CHV_MARGIN + i * half
        pdf.setLineWidth(0.6)
        pdf.setFillColorRGB(*_CHV_AZUL)
        pdf.rect(x, y_top - bar_h, half, bar_h, fill=1, stroke=1)
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont(FONT_BOLD, font_size)
        pdf.drawCentredString(x + half / 2, y_top - bar_h + (bar_h - font_size) / 2 + 1, title)
        pdf.setFillColorRGB(0, 0, 0)
        # recuadro de firma
        pdf.rect(x, y_top - bar_h - sign_h, half, sign_h, fill=0, stroke=1)
        pdf.setFillColorRGB(*_CHV_GRIS)
        pdf.setFont(FONT_REGULAR, 6)
        pdf.drawCentredString(x + half / 2, y_top - bar_h - sign_h + 4, "FIRMA")
        pdf.setFillColorRGB(0, 0, 0)
        if entry.get("signature_path"):
            _chv_signature_image(
                pdf, entry["signature_path"], x, y_top - bar_h, half, sign_h
            )
        # nombre completo
        name_y = y_top - bar_h - sign_h
        label_w = 110.0
        _chv_cell(
            pdf, x, name_y, label_w, name_h, ["NOMBRE COMPLETO:"], font_size, bold=True, fill=True
        )
        _chv_cell(
            pdf,
            x + label_w,
            name_y,
            half - label_w,
            name_h,
            _chv_wrap(entry.get("name"), half - label_w, font_size)[:1],
            font_size,
        )
    return y_top - bar_h - sign_h - name_h


def FileVehicleChecklistPDF(dict_data: dict):
    """
    Genera el PDF del CHECK LIST VEHICULAR (FO-CDA-03 R3) de un voucher
    vehicular de SGI: página horizontal que replica el formato oficial (barras
    azules #00AFEF, catálogo fijo de accesorios con BIEN/MAL/N/A por lookup,
    siluetas de tipo de vehículo y firmas incrustadas). Estructura esperada de
    ``dict_data``::

        {
            "filename_out": str,
            "id_voucher": int,
            "fecha_elaboracion": str,
            "marca": str, "modelo": str, "color": str, "anio": str,
            "placas": str, "kilometraje": str,
            "tarjeta_circulacion": 1 | 0 | None,   # None = casillas en blanco
            "poliza_seguro": 1 | 0 | None,
            "comprobante_refrendo": 1 | 0 | None,
            "accessories": [{"label": str, "value": "Bien|Mal|N/A"}, ...],
            "vehicle_type": 0 | 1 | 2 | None,      # sedán | pickup | van
            "observations": str,
            "realizado": {"name": str, "signature_path": str | None},
            "recibido": {"name": str, "signature_path": str | None},
        }

    Todo viene resuelto por el midleware (sin acceso a BD). El documento es de
    una página; si unas observaciones o accesorios extra desbordaran, continúa
    en una segunda página con el mismo header.
    """
    pdf = canvas.Canvas(dict_data["filename_out"], pagesize=(_CHV_PAGE_X, _CHV_PAGE_Y))
    pdf.setTitle("CHECK LIST VEHICULAR")
    font_size = 7
    pages = 1
    right_text = f"Checklist: {dict_data.get('id_voucher', '')}"

    def draw_page_header():
        create_header_telintec(
            pdf,
            title="CHECK LIST VEHICULAR",
            page_x=_CHV_PAGE_X,
            iso_form=8,
            orientation="horizontal",
        )

    def ensure_space(y, needed):
        nonlocal pages
        if y - needed >= _CHV_LIMIT_Y:
            return y
        print_footer_page_count(pdf, pages, right_text=right_text, x_max=_CHV_PAGE_X)
        pdf.showPage()
        pages += 1
        draw_page_header()
        return 515.0

    draw_page_header()
    y = 515.0
    # ------------------------------- Fecha de elaboración -------------------------------
    # fila corta a la izquierda, como en el formato oficial
    y = _chv_pairs_row(
        pdf,
        y,
        [("FECHA DE ELABORACIÓN:", dict_data.get("fecha_elaboracion"), 130.0, 100.0)],
        font_size,
    )
    y -= 4
    # ------------------------------- Datos del vehículo ---------------------------------
    y = _chv_section_bar(pdf, y, "DATOS DEL VEHÍCULO")
    y -= 2
    value_w = (_CHV_WIDTH - 318.0) / 6
    y = _chv_pairs_row(
        pdf,
        y,
        [
            ("MARCA:", dict_data.get("marca"), 48.0, value_w),
            ("MODELO:", dict_data.get("modelo"), 55.0, value_w),
            ("COLOR:", dict_data.get("color"), 45.0, value_w),
            ("AÑO:", dict_data.get("anio"), 35.0, value_w),
            ("PLACAS:", dict_data.get("placas"), 50.0, value_w),
            ("KILOMETRAJE:", dict_data.get("kilometraje"), 85.0, value_w),
        ],
        font_size,
    )
    y = _chv_yes_no_row(
        pdf,
        y,
        [
            ("TARJETA DE CIRCULACIÓN:", dict_data.get("tarjeta_circulacion"), 180.0, 90.0),
            ("PÓLIZA DE SEGURO:", dict_data.get("poliza_seguro"), 150.0, 90.0),
            (
                "COMPROBANTE DE REFRENDO:",
                dict_data.get("comprobante_refrendo"),
                _CHV_WIDTH - 180.0 - 150.0 - 3 * 90.0,
                90.0,
            ),
        ],
        font_size,
    )
    y -= 4
    # ------------------------------- Accesorios -----------------------------------------
    y = _chv_section_bar(pdf, y, "ESTADO DE ACCESORIOS Y HERRAMIENTAS")
    y -= 2
    states = {}
    extras = []
    for acc in dict_data.get("accessories") or []:
        if not isinstance(acc, dict):
            continue
        label = _chv_norm(acc.get("label"))
        state = _chv_state(acc.get("value"))
        if not label:
            continue
        catalog = any(
            label == _chv_norm(known) for _, labels in _CHV_GROUPS for known in labels
        )
        if catalog:
            if state is not None:
                states[label] = state
        else:
            extras.append((acc.get("label"), acc.get("value")))
    y = _chv_accessories_table(pdf, y, states)
    if extras:
        y = _chv_extra_accessories(pdf, y, extras)
    y -= 4
    # ------------------------------- Observaciones --------------------------------------
    obs_lines = _chv_wrap(dict_data.get("observations"), _CHV_WIDTH - 110.0, font_size)
    obs_h = len(obs_lines) * font_size * 1.25 + 5
    y = ensure_space(y, obs_h)
    y = _chv_pairs_row(
        pdf,
        y,
        [("OBSERVACIONES:", dict_data.get("observations"), 110.0, _CHV_WIDTH - 110.0)],
        font_size,
    )
    y -= 4
    # ------------------------------- Tipo de vehículo -----------------------------------
    type_h = 100.0
    y = ensure_space(y, 14 + 2 + type_h)
    y = _chv_section_bar(pdf, y, "TIPO DE VEHICULO")
    y -= 2
    y = _chv_vehicle_type_section(pdf, y, dict_data.get("vehicle_type"), type_h)
    y -= 6
    # ------------------------------- Firmas ---------------------------------------------
    y = ensure_space(y, 14 + 62 + 14)
    _chv_signatures_section(
        pdf,
        y,
        dict_data.get("realizado") or {},
        dict_data.get("recibido") or {},
        font_size,
    )
    print_footer_page_count(pdf, pages, right_text=right_text, x_max=_CHV_PAGE_X)
    pdf.save()
    return True
