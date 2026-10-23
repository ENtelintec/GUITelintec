# PDF FO-PRE-02 de cotización CISCO (`GET /quotation/cisco/download/pdf/<id>`)

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (27/27 checks, `Tests/tester_quotation_cisco_pdf.py`, PDFs renderizados y revisados; regresión en verde: `tester_quotation_cisco` 46/46, `tester_folio_quotation` 32/32, `tester_quotation_ocd` 35/35, `tester_quotation_put_metadata` 18/18, `tester_tenders` 61/61, `tester_iso_formats` 48/48, `tester_remission_pdf_ocd` 17/17). Sin DDL.** Cierra `P-169`.

Sigue a [`cotizaciones_cisco.md`](cotizaciones_cisco.md) (F10 de [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md)). Fuente del diseño: hoja "COT CISCO" de `FO-PRE-02 R2 COT CISCO.xlsx`, dibujada en la cuadrícula de la casa (skill `pdf-design`).

## Qué cambia

- **Endpoint nuevo** `GET /admin/presales/quotation/cisco/download/pdf/<id>`: descarga el PDF de una cotización con `metadata.format = "cisco"` (también si ya es OCD). Mismo criterio de 404 que `GET /quotation/cisco/<id>`.
- **El back no tenía PDF de cotización**: [`cotizaciones_cisco.md`](cotizaciones_cisco.md) decía que `GET /quotation/download/pdf/<id>` imprimía el FO-PRE-01, pero esa ruta no existe (`templates/forms/quotation.py` es un resto sin uso). Este es el primer PDF de cotización del API.
- **Contenido**, en el orden del Excel:
  - encabezado ISO `iso_formats` id 15 (`Codigo: FO-PRE-02 R2`);
  - fecha y cotización;
  - datos de Telintec: compañía fija, y nombre, teléfono y correo institucional del empleado `metadata.emp_id`;
  - datos del cliente: `company`, `user`, `phone`, `email`, `planta`, `area`, `location`;
  - concepto y tipo de moneda;
  - tabla de 9 columnas: ITEM, número de parte, smart account (Sí/No), descripción, duración del servicio en meses, tiempo de entrega, cantidad, precio unitario y total, con ITEM en negritas en las partidas enteras;
  - TOTAL sin IVA;
  - comentarios: precios sin IVA, `delivery_time` general y vigencia `limit_date`.
- **Multipágina**: el encabezado y las columnas se repiten en cada página nueva; la cabecera no. El bloque de comentarios nunca se parte entre páginas. Pie con número de página y `Folio: <quotation_code>`.
- **`ISO_FORM_IDS_IN_CODE`** gana 15, y también 14: el PDF de remisión OCD ya lo pedía por literal sin protegerlo, así que el CRUD de SGI lo dejaba borrar.
- **Fix de paso**: `GET /quotation/<id>` y `GET /quotation/cisco/<id>` con un id inexistente respondían **400** ("No se pudieron obtener las cotizaciones"), porque el controller marca el no-encontrado como fallo. Ahora responden **404**, como ya decía el doc de CISCO.

## Capas tocadas

```
rs          rs_Admin_presales.py                 GET /quotation/cisco/download/pdf/<int:id_q> (send_file en 200, envelope en 4xx)
midleware   MD_QuotationCisco.py                 download_quotation_cisco_pdf · _telintec_contact (emp_id -> nombre/teléfono/correo institucional)
midleware   Functions_midleware_admin.py         get_quotations: "Quotation not found" del controller -> 404
forms       QuotationCiscoForms.py (nuevo)       FileQuotationCiscoPDF · helpers _qc_* (celda, filas de metadata, fila completa)
forms       PDFGenerator.py                      ISO_FORM_IDS_IN_CODE + 14, 15
```

Datos: los mismos de `GET /quotation/cisco/<id>` (`get_quotations_cisco_api`, partidas ya ordenadas por `partida` y con `total`) más `get_employee_info(emp_id)`.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales` · permiso `administracion`.
- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Request**: `GET /quotation/cisco/download/pdf/<id>`, sin body ni query.
- **Respuesta**: **200 = blob binario** `application/pdf` con `Content-Disposition: attachment; filename=cotizacion_cisco_<quotation_code>_<id>.pdf` (el código pasa por `secure_filename`: sin acentos ni espacios). **4xx = JSON** `{data, msg, error}`. El front decide por el **status**, no por el content-type.

| Código | Cuándo | Cuerpo |
|---|---|---|
| **200** | cotización CISCO (cotización u OCD) | blob PDF |
| **401** | sin token o token inválido | `{"error": "No autorizado. Token invalido"}` |
| **404** | el id no existe | `{"data": [], "msg": "No se encontró la cotización (ID 999)", "error": "Quotation not found"}` |
| **404** | existe pero no es CISCO | `{"data": [], "msg": "No se encontró la cotización CISCO (ID 1)", "error": "Quotation not found"}` |
| **400** | falla la lectura en BD o la generación | `{"data": [] o null, "msg": "...", "error": "..."}` |

### Gotchas

- Descargar con `responseType: "blob"`; si el status no es 200, leer el blob como texto y parsear el JSON para pintar `msg`.
- El contacto de Telintec sale del empleado `metadata.emp_id` (quien capturó). Si no existe, el bloque sale con nombre, teléfono y correo vacíos (no es error). Con varios correos se usa el `@telintec.com.mx`.
- `I. Vigencia:` del encabezado sale vacío mientras la fila 15 de `iso_formats` no tenga `emission_date` (hoy es `NULL` en las 3 BDs): lo llena SGI desde su pantalla de formatos, sin código.
- Montos con `$` y 2 decimales; la moneda va en el recuadro TIPO DE MONEDA (`MXN` si falta).

## Al modificar

- **Columnas**: `_QC_ITEM_COLS` (encabezado, ancho, alineación) y la lista `values` de `FileQuotationCiscoPDF` van **por posición**. Los anchos deben sumar `_QC_USABLE_W` y cada palabra de un encabezado debe caber en su columna a 7 pt bold. `tester_quotation_cisco_pdf.py` revisa las dos cosas.
- **FO-PRE-01** (cotización de preventa): no existe; si se pide, módulo gemelo `QuotationForms` con su `iso_formats` id y su id en `ISO_FORM_IDS_IN_CODE`, ramificando la descarga por `metadata.format`.
- **Nueva revisión del formato** (R3): solo en `iso_formats` por el CRUD de SGI ([`iso_formats_crud.md`](iso_formats_crud.md)); el id 15 no cambia.
