# Tipografía Helvetica en todos los PDFs + tabla de items de la Remisión en cuadrícula

Dos cambios visuales, **sin cambio de contrato para el front** (mismos
endpoints y mismos shapes; solo cambia el binario del PDF que se descarga):

1. **Tipografía de la casa**: todos los PDFs generados en
   [`templates/forms/`](../templates/forms/) pasan de **Courier/Courier-Bold**
   (monospace, aspecto "máquina de escribir") a **Helvetica/Helvetica-Bold**
   (sans-serif contemporánea, built-in de reportlab: no hay que registrar TTF
   ni se incrustan fuentes — los PDFs no engordan).
2. **La tabla de items de la Remisión**
   ([`remission_pdf_download.md`](remission_pdf_download.md),
   [`remission_combined_pdf.md`](remission_combined_pdf.md)) deja las filas de
   texto con una línea separadora y pasa a **cuadrícula completa** estilo casa
   (skill `pdf-design`): un `rect` por celda, fila de encabezados en celeste
   `#BDD7EE` (antes barra azul con texto blanco), columnas numéricas (`CANT.`,
   `PRECIO UNIT.`, `TOTAL`) alineadas a la derecha, y los totales
   (`SUBTOTAL` / `IVA (x%)` / `TOTAL`) como continuación de la cuadrícula bajo
   las dos últimas columnas (label celeste + monto), con `TOTAL POS. N` a la
   izquierda. Multipágina repite header Telintec + encabezados de columna
   (comportamiento previo intacto).

## La mecánica del cambio de fuente (leer antes de tocar un PDF)

Courier es monospace: `len(texto) * font_size * 0.6` daba el ancho exacto y el
wrapping se hacía con `textwrap` por conteo de caracteres. Helvetica es
**proporcional**: ese conteo desborda celdas con texto en MAYÚSCULAS (el
promedio de una mayúscula es ~0.68 em > 0.6). Por eso:

- [`PDFGenerator.py`](../templates/forms/PDFGenerator.py) gana las constantes
  **`FONT_REGULAR` / `FONT_BOLD`** (nunca hardcodear el nombre de la fuente en
  los forms) y el helper **`wrap_text_width(value, width_pt, font_size,
  font=FONT_REGULAR)`**: word-wrap por ancho real con
  `pdfmetrics.stringWidth`; una palabra sola más ancha que la celda se parte
  por caracteres; devuelve siempre ≥ 1 línea.
- Los wraps de **celdas de cuadrícula** ahora miden con ese helper:
  `_grid_wrap_cell` (SM / inventario), los `_rm_*` (remisión / hoja de fotos),
  `_chv_wrap` (checklist vehicular) y `_qz_wrap` (reporte genérico de quizz)
  son wrappers de una línea sobre `wrap_text_width` (restan los 8 pt de
  padding).
- Las posiciones label→valor que usaban `len(label) * factor` ahora usan
  `stringWidth(label, FONT_BOLD, size)` (PDFGenerator, StorageMovSM,
  PurchaseForms, quotation, VouchersFormsPDF); `print_footer_page_count`
  posiciona el folio con `drawRightString` en vez de aritmética de caracteres.
- Los PDFs **legacy** de texto suelto (PO, vale EPP/herramienta, cotización,
  devolución de materiales) conservan sus tablas de conteo de caracteres para
  el wrap: el avance de columna (`font_size * chars * 0.8`) ya traía ~25% de
  holgura sobre el ancho Courier y Helvetica promedia menos, así que solo
  cambió la fuente. Verificado sin encimes de columnas.

## Capas tocadas

Solo la capa PDF ([`templates/forms/`](../templates/forms/)); HTTP, midleware
y controllers intactos.

- [`PDFGenerator.py`](../templates/forms/PDFGenerator.py) — constantes de
  fuente + `wrap_text_width`; `create_footer_sign` mide la línea con
  `stringWidth`; footer con `drawRightString`.
- [`RemissionForms.py`](../templates/forms/RemissionForms.py) — rediseño de la
  tabla de items: `_RM_ITEM_COLS` (`(encabezado, ancho_pt, align)`, suman el
  ancho útil, `DESCRIPCIÓN` absorbe el resto) reemplaza las anclas `_RM_X_*`;
  `_rm_draw_cell` gana `align="left|right"`; el salto de página ahora calcula
  el alto de la fila **antes** de dibujarla (`check_page_break(y, needed)`);
  totales en mini-cuadrícula. El recuadro de metadata de la pág. 1 y la hoja
  de fotos solo cambian de fuente/medición.
- [`StorageMovSM.py`](../templates/forms/StorageMovSM.py),
  [`VehicleChecklistPDF.py`](../templates/forms/VehicleChecklistPDF.py),
  [`QuizzGenericReport.py`](../templates/forms/QuizzGenericReport.py) — fuente
  + wrap por `stringWidth` (helpers `_grid_/_chv_/_qz_`); layout intacto
  (semáforo de SM y azul `#00AFEF` del checklist incluidos).
- [`Materials.py`](../templates/forms/Materials.py),
  [`PurchaseForms.py`](../templates/forms/PurchaseForms.py),
  [`quotation.py`](../templates/forms/quotation.py),
  [`VouchersFormsPDF.py`](../templates/forms/VouchersFormsPDF.py),
  [`BarCodeGenerator.py`](../templates/forms/BarCodeGenerator.py) — solo
  fuente (y offsets label→valor con `stringWidth` donde aplicaba; en
  `quotation.py` se corrigió de paso el offset del valor de `Cliente:` que
  medía el string `"Cotizacion: "`).
- Skill [`.claude/skills/pdf-design/`](../.claude/skills/pdf-design/SKILL.md)
  actualizada: tipografía nueva, wrapping por `wrap_text_width`, `align` para
  columnas numéricas.

Los PDFs de encuestas dedicados (QuizzNorm35, QuizzSalida, ClimaLaboral,
Eva360) ya usaban Helvetica; no se tocaron.

## Verificación

Generados y revisados 11 PDFs con datos sintéticos extremos (descripciones
larguísimas en mayúsculas, stress `WWW…MMM`, multipágina): remisión (2 págs.,
cuadrícula + totales + firmas), hoja de fotos (2 págs.), SM (semáforo +
entregas), checklist vehicular, PO, vale, cotización, solicitud de materiales,
inventario, lista de compra y reporte genérico de quizz — sin desbordes ni
encimes. `pyrefly check`: 191 errores vs 194 de línea base (ninguno nuevo; los
de `forms/` son el patrón preexistente int/float de `x_position` en los loops
legacy).

## Al modificar

- **Nunca** volver al conteo de caracteres para wrapping o posiciones: con
  fuente proporcional desborda. Usar `wrap_text_width` / `stringWidth`.
- Para cambiar la tipografía de todos los PDFs (p. ej. una TTF corporativa):
  registrar la fuente y cambiar `FONT_REGULAR`/`FONT_BOLD` en
  `PDFGenerator.py` — todo lo demás mide con `stringWidth` y se adapta solo.
- Los anchos de `_RM_ITEM_COLS` deben seguir sumando `a4_x - 2 * _RM_MARGIN`
  (545.27); si se agrega una columna, restarle a `DESCRIPCIÓN`.

## Pendiente

- Migrar los PDFs legacy de texto suelto (PO, vale EPP/herramienta,
  cotización, devolución de materiales) a la cuadrícula de la casa.
