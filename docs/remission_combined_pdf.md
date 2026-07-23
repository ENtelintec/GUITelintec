# PDF combinado de una remisión (Remisión + anexos + fotos)

Cierra el pendiente de [`remission_pdf_download.md`](remission_pdf_download.md):
generar en un solo documento el paquete completo que se entrega al cliente —
la **Remisión** (pág. 1, generada), los **anexos** (reporte de materiales
escaneado y demás soportes) y la **hoja de EVIDENCIA FOTOGRÁFICA** (generada a
partir de las fotos subidas). Replica la estructura del archivo de referencia
`PEDIDO 459 - REM 01 - FL.C1037-C2342 (Remision, Reporte, Fotos).pdf`.

Los anexos se suben con el endpoint de attachments (que **estaba roto**, ver
[Bugs corregidos](#bugs-corregidos)) y se guardan en `activity_reports.files`;
la descarga los baja de S3 y los fusiona con la remisión.

## Endpoints

### Subir un anexo

`POST /GUI/api/v1/admin/collections/remission/attachment-<id_report>`
— **multipart/form-data**. Departamentos: `["administracion", "operaciones"]`.

| Campo (form) | Req. | Descripción |
| --- | --- | --- |
| `file` | ✅ | El archivo. Extensiones válidas: `pdf, jpg, jpeg, png, webp, zip`. |
| `category` | ❌ | `photo` \| `anexo` \| `firma` \| `otro`. Si no se manda, se infiere del nombre/extensión (ver [Categorías](#categorías)). |
| `folio` | ❌ | Folio del reporte de materiales (los C-numbers, p. ej. `C1037`). Solo relevante para `photo`; alimenta el encabezado de la hoja de fotos. |
| `title` | ❌ | Etiqueta opcional del anexo (se guarda, aún no se imprime). |

Cada archivo se sube a S3 (`reportActivity/YYYY/MM/DD/<filename>`) y se agrega a
`files` como:

```json
{"filename": "459-foto1.jpg", "path": "reportActivity/2025/06/05/459-foto1.jpg",
 "category": "photo", "folio": "C1037", "title": "", "timestamp": "2025-06-05 12:00:00"}
```

Respuesta `201`: `{"data": {"path": "<key S3>", "category": "photo"}, "msg": "...", "error": null}`.

### Descargar el PDF (combinado o simple)

`GET /GUI/api/v1/admin/collections/remission/download/pdf/<int:id_report>?full=1&iva_rate=0.16`
— Departamentos: `["administracion", "purchases"]`. Devuelve el PDF (`send_file`).

- **`full=1`** (o `true`/`yes`) → documento **combinado**: Remisión → anexos → fotos.
- **sin `full`** (default) → solo la **página de la Remisión** (comportamiento
  histórico intacto; ver [`remission_pdf_download.md`](remission_pdf_download.md)).
- `iva_rate` opcional (default `0.16`), igual que antes.

## Categorías

`category` decide cómo se usa cada archivo en el documento combinado:

| Categoría | En el PDF combinado |
| --- | --- |
| `anexo` | Se **concatena tal cual** después de la Remisión. PDF → páginas tal cual; imagen → una página A4 ajustada; `zip`/no dibujable → se omite + log. |
| `photo` | Alimenta la(s) hoja(s) generada(s) de **EVIDENCIA FOTOGRÁFICA** (rejilla 2×3 vertical, 6 por página). |
| `firma` | Se **incrusta en la pág. 1** de la Remisión sobre las líneas de firma (no genera página propia). |
| `otro` | Se guarda en `files` pero **se excluye** del documento combinado. |

**Archivos viejos sin `category`** (subidos antes de este cambio) se clasifican
por heurística: nombre `firma-*` → `firma`; extensión `pdf`/`zip` → `anexo`;
imagen → `photo`; cualquier otra cosa → `otro`. (`_classify_remission_file` en
[`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py).)

### Firmas (detalle)

`category=firma` marca el archivo como firma, pero **el recuadro y el estatus
siguen resolviéndose por el nombre del archivo** (mecanismo existente):

- nombre con `firma-recibido` → recuadro **"Firma Autorizacion 2"** + estatus `2` (aprobado).
- nombre con `firma-realizado` → recuadro **"Firma Autorizacion 1"** + estatus `1` (firmado).
- otra firma → recuadro 1 por defecto, sin cambio de estatus.

Solo se incrustan firmas raster (`jpg/jpeg/png/webp`). Si no hay firma, la línea
queda en blanco para firmar a mano.

## Estructura del PDF combinado

```
[ Remisión ]           1 pág. generada (FileRemissionPDF) — firmas incrustadas
[ anexo 1 ]            \
[ anexo 2 ]             > en orden de subida (PDFs tal cual, imágenes ajustadas)
[ ... ]                /
[ EVIDENCIA FOTOG. ]   1..N págs. generadas (FileRemissionPhotosPDF), 6 fotos/pág
```

- Todo **vertical A4** (sin rotación al imprimir).
- Cada hoja de fotos es autocontenida: repite header Telintec + metadata. El
  campo **Folio** de esa hoja lista los folios **distintos de las fotos de esa
  página** (`C1037 – C2342`), no un folio global.
- Metadata de la hoja de fotos: `Fecha`=`ar.date`, `Pedido`/`Remito` de
  `extra_info`, `Planta`/`Área`/`Lugar` de las columnas base `ar.plant/area/location`.

## Capas tocadas

1. **HTTP** — [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py):
   `UploadActivityReportAttachment` ahora usa el parser
   `expected_files_attachment_remission` y lee `category`/`folio`/`title` del
   form (y pasa `id_report`, antes pasaba `id_voucher` — bug); `DownloadPDFRemission`
   lee `?full`.
2. **Validación/Swagger** — [`api_purchases_models.py`](../static/Models/api_purchases_models.py):
   nuevo parser `expected_files_attachment_remission` (propio de la remisión; no
   se tocó el genérico `expected_files_attachment` de SGI).
3. **Orquestación** — [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py):
   `create_activity_report_attachment_api` corregido y extendido (persiste
   `category/folio/title/timestamp`); `download_file_remission(..., full=False)`
   arma el combinado; helpers nuevos `_classify_remission_file`,
   `_build_remission_attachments` (descarga de S3, no fatal por archivo) y
   `_assemble_remission_full_pdf` (fusión con **PyMuPDF/fitz**).
4. **PDF** — [`RemissionForms.py`](../templates/forms/RemissionForms.py):
   `FileRemissionPDF` gana firmas incrustadas (`sign_realizado_path`/
   `sign_recibido_path`); función nueva `FileRemissionPhotosPDF` (hoja de fotos,
   estilo casa `pdf-design`) + helpers `_rm_*`.

## Bugs corregidos

El endpoint de attachments de la remisión **fallaba siempre** (nunca guardó nada
en `files`); tres bugs encadenados:

1. `create_activity_report_attachment_api` leía `data["id_report"]` pero el
   endpoint solo pasaba `id_voucher` → `KeyError`.
2. Trataba el resultado de `get_remission_by_id(id, ...)` como **lista** de
   filas (`isinstance(result, list)` + `for item in result`), pero con un id
   concreto ese controller usa `fetchone` → **una sola tupla** → rechazaba todo.
   (Mismo patrón que [`sm_attachment_delivery_title.md`](sm_attachment_delivery_title.md).)
3. Llamaba `update_report_activity_files(id, history, status, files)` con los
   argumentos **`files` y `status` invertidos** respecto a la firma real
   `(id, history, files, status)`.

`download_report_activity_attachment_api` tenía los bugs 1 y 2 (leía
`data["id_voucher"]`, esperaba lista). Ambos corregidos; not-found ahora → `404`.

## Para el front

### Subir anexos

Un `POST` multipart por archivo. Ejemplos (pseudo):

```js
// Reporte de materiales escaneado (PDF)
form.append("file", pdfFile);           // 459-reporte.pdf
form.append("category", "anexo");

// Foto de evidencia (una por request)
form.append("file", jpgFile);           // 459-foto1.jpg
form.append("category", "photo");
form.append("folio", "C1037");          // C-number del reporte que documenta la foto

// Firma de quien recibe -> nombra el archivo con "firma-recibido"
form.append("file", pngFirma);          // 459-firma-recibido.png
form.append("category", "firma");
```

- **Nombra las firmas con `firma-realizado` / `firma-recibido`** en el filename:
  de ahí salen el recuadro (1 ó 2) y el cambio de estatus. `category=firma` sola
  no basta para elegir recuadro.
- El `folio` de una foto es libre (string). En la hoja generada, las fotos se
  agrupan de a 6 por página y el encabezado muestra los folios **distintos** de
  esa página.
- `category=otro` sirve para guardar un archivo en la remisión **sin** que
  aparezca en el reporte combinado.

### Descargar

- Botón "Descargar remisión" → `GET .../remission/download/pdf/<id>` (como hoy).
- Botón "Descargar reporte completo" → el mismo con `?full=1`.
- Respuesta: binario PDF (`Content-Disposition: attachment`). En error, el
  envelope `{data, msg, error}` con `4xx` (p. ej. `404` si la remisión no existe).

### Casos borde a considerar en UI

- **Sin anexos**: `full=1` devuelve igual el PDF, solo la página de la Remisión
  (no es error).
- **Fallo de un anexo** (S3 caído, imagen corrupta, `zip`): es **no fatal** — el
  PDF se genera **sin ese archivo** y el faltante queda en el log/notificación,
  no en la respuesta. El documento puede verse "completo" aunque falte un anexo;
  si la completitud es crítica, avísale al usuario que revise que subió todo.
- **Orden**: los anexos salen en **orden de subida**. Si importa el orden en el
  documento, súbelos en ese orden.
- **Firmas**: si no se subió firma, la línea sale en blanco (para firmar a mano).

## Al modificar

- La rejilla de fotos es **2×3 vertical** (6/pág). Para cambiar densidad/orientación,
  editar `cols/rows` en `FileRemissionPhotosPDF` (respetar el skill `pdf-design`).
- El mapeo firma→recuadro y firma→estatus vive en
  `create_activity_report_attachment_api` (subida, estatus) y en
  `_build_remission_attachments` (recuadro), ambos por substring del nombre.
  Si se cambia la convención de nombres, tocar los dos.
- La fusión usa `fitz` (PyMuPDF, ya en `requirements.txt`). Un anexo que no sea
  PDF ni imagen dibujable se omite: si se necesita soportar otro tipo, extender
  `_assemble_remission_full_pdf`.

## Pendiente

- Pre-llenar el `title` del anexo en el documento (hoy se guarda pero no se
  imprime).
- Reporte de materiales formato Ternium **generado** (hoy solo se concatena el
  escaneo subido como `anexo`); no hay datos en el modelo para generarlo, ver
  `Docs/tareas_admin_windows.md`.
- Incrustar también la firma de "quien entrega" (hoy `firma-realizado` /
  `firma-recibido` cubren autorización 1 y 2).
