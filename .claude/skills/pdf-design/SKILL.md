---
name: pdf-design
description: Formato de diseño para los PDFs de este repo (reportlab canvas + cuadrícula celeste). Usar SIEMPRE que se cree un PDF nuevo o se modifique el diseño/layout de uno existente en templates/forms/ (SM, remisiones, compras, inventario, vouchers, etc.).
---

# Formato de diseño de PDFs (Telintec)

Guía para generar o rediseñar PDFs en este repo. La implementación canónica es
el PDF de SM: helpers `_sm_*` en [templates/forms/StorageMovSM.py](../../../templates/forms/StorageMovSM.py)
(ver `FileSmPDF`, `print_metadata_grid_sm`, `_sm_draw_cell`). Antecedente:
[templates/forms/RemissionForms.py](../../../templates/forms/RemissionForms.py).
Diseño documentado en [Docs/sm_pdf_grid_redesign.md](../../../Docs/sm_pdf_grid_redesign.md).

## Stack y reglas base

- **reportlab canvas puro** (`canvas.Canvas`), NO platypus. Todo se dibuja con
  `rect`/`drawString`/`drawRightString` a coordenadas absolutas.
- Página vertical: `pagesize=(a4_x, a4_y)` con `a4_x=595.27`, `a4_y=841.89`
  importados de `templates/forms/PDFGenerator.py`.
- Fuente **Helvetica** (valores) y **Helvetica-Bold** (labels/encabezados),
  vía las constantes `FONT_REGULAR` / `FONT_BOLD` de `PDFGenerator.py` — nunca
  hardcodear el nombre de la fuente. Es proporcional: el wrapping y cualquier
  posición derivada del texto se calculan con el ancho real
  (`wrap_text_width(...)` / `pdfmetrics.stringWidth`), **no** con conteo de
  caracteres (`len(texto) * factor` era de la era Courier y desborda celdas).
- Margen lateral `25.0` pt (**float, no int** — con int pyrefly marca
  `bad-assignment` en los `x += w` acumulativos). Ancho útil:
  `a4_x - 2 * margen`.
- Header institucional en **cada página**: `create_header_telintec(...)` de
  `PDFGenerator.py` (título del documento, `iso_form` según formato,
  `orientation="vertical"`). El contenido arranca en `y = 740`.
- Pie en cada página: `print_footer_page_count(pdf, pages,
  right_text=f"Folio: {folio}", x_max=a4_x)` — número de página a la izquierda,
  folio a la derecha.
- Font size del cuerpo: 8 pt (9 pt en documentos con pocos campos).

## Celdas y color

Todo campo/columna va en **cuadrícula**: un `rect` por celda. Los nombres de
campos y encabezados de columna van resaltados en **celeste**:

```python
from templates.forms.PDFGenerator import FONT_BOLD, FONT_REGULAR, wrap_text_width

_CELESTE = (0.74, 0.84, 0.93)  # #BDD7EE

def _draw_cell(pdf, x, y_top, w, h, lines, font_size, bold=False, fill=False, align="left"):
    pdf.setLineWidth(0.6)
    if fill:  # celda celeste (labels/encabezados)
        pdf.setFillColorRGB(*_CELESTE)
        pdf.rect(x, y_top - h, w, h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)   # SIEMPRE restaurar a negro
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
```

- Labels/encabezados: `bold=True, fill=True` (celeste + negro bold). Nunca
  texto blanco sobre celeste (no contrasta).
- Wrapping por celda: `wrap_text_width(v, w - 8, font_size)` (de
  `PDFGenerator.py`; mide con stringWidth) — 8 pt de padding horizontal
  (4 por lado). Para labels en bold, pasar `font=FONT_BOLD`.
- Columnas numéricas (cantidades, dinero): `align="right"` en header y celdas
  (ver la tabla de items de `RemissionForms.py`).
- Interlineado `font_size * 1.25`; alto de fila
  `max_lineas * font_size * 1.25 + 6`. La fila crece con el wrap — **nunca**
  dejar que un valor largo desborde la celda o la página.

## Bloques estándar

- **Metadata**: cuadrícula de 2 pares `label|valor` por fila (4 columnas).
  Label ~118 pt; el valor toma el resto del medio-ancho. El alto de la fila es
  el máximo de líneas entre las 4 celdas. Solo en la página 1.
- **Tabla de items**: lista de columnas como `[(encabezado, ancho_pt), ...]`
  cuyos anchos **suman el ancho útil**. El orden de columnas DEBE seguir el
  orden del tuple/lista de datos — header y celda se alinean por posición, no
  por nombre (ya hubo un bug de encabezados UDM/Cantidad cruzados por esto).
  Fila de encabezados celeste al inicio de la tabla **y en cada página nueva**.
- **Salto de página**: antes de dibujar cada fila, calcular su alto; si
  `y - alto < limit_y` (~40-60), cerrar página (pie), `showPage()`, redibujar
  header Telintec + encabezados de columna y continuar. La metadata NO se
  repite.
- **Tabla de entregas/firmas** (documentos de almacén): encabezados celestes
  `No. | Fecha de Entrega | Firma de Quien Entrega | Firma de Quien Recibe`,
  filas en blanco de 26 pt de alto para llenar a mano, y debajo el campo
  `Fecha de Entrega Completa` (label celeste + celda vacía). Verificar que el
  bloque completo quepa antes de dibujarlo; si no, nueva página.

## Convenciones de código

- Helpers **por documento**, con prefijo (p. ej. `_sm_*`): no modificar helpers
  compartidos por otros PDFs (`print_metadata`, `print_products_list`, etc. de
  StorageMovSM.py los usan `InventoryStoragePDF` y `ReturnMaterials`).
- La función pública `File*PDF(dict_data)` recibe todo resuelto por el
  midleware (sin acceso a BD) y devuelve `True`; documentar la estructura de
  `dict_data` en su docstring.
- Módulos con `__author__` / `__date__` en el header.
- Verificar SIEMPRE generando un PDF real (con datos de la BD dev vía el
  midleware y/o un dict sintético con valores extremos: textos larguísimos,
  muchas filas para multipágina) y leyendo el PDF renderizado antes de dar por
  bueno el diseño.
