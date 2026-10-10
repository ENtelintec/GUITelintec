# PDF combinado del checklist vehicular (`?full=1`): checklist + anexos + evidencia fotográfica

Fecha: 2026-10-09 · **Estado: hecho y verificado contra dev con S3 simulado (15/15 checks, `Tests/tester_checklist_full_pdf.py`; páginas renderizadas y revisadas).** Sin DDL.

Cierra el pendiente de [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md): en un solo documento, el paquete completo del checklist, como ya existe para remisiones ([`remission_combined_pdf.md`](remission_combined_pdf.md)).

## Estructura

```
[ CHECK LIST VEHICULAR ]   1 pág. horizontal (FileVehicleChecklistPDF, sin cambios) — firmas incrustadas
[ anexo PDF 1 ]            \
[ anexo PDF 2 ]             > en orden de subida, tal cual
[ ... ]                    /
[ EVIDENCIA FOTOGRÁFICA ]  1..N págs. A4 vertical (FileVehicleChecklistPhotosPDF), 6 fotos/pág
```

Los anexos vehiculares solo guardan `{filename, path}` en `extra_info.files`, **sin categoría**, así que se clasifican por nombre y extensión:

| Archivo | En el combinado |
|---|---|
| nombre con `firma` | se omite: ya va incrustada en la pág. 1 (`firma-aprobado` / `firma-recibido`) |
| `.pdf` | anexo, concatenado tal cual |
| `.jpg/.jpeg/.png/.webp` | foto de la hoja de EVIDENCIA FOTOGRÁFICA |
| `.zip` u otro | se omite |

Hoja de fotos:

- **Estilo casa** (skill `pdf-design`: celeste `#BDD7EE`, A4 vertical, rejilla 2×3). No es parte del FO-CDA-03, así que el azul `#00AFEF` se queda solo en la pág. 1.
- Header `EVIDENCIA FOTOGRÁFICA` con el código del formato (`iso_form=8`, FO-CDA-03).
- Metadata del vehículo en cada hoja: Fecha, Checklist, Marca, Modelo, Placas, Tipo, Kilometraje, Realizado por y Recibido por.
- Pie: `Página N` **continua** con el resto del documento (arranca después del checklist y los anexos) y `Checklist: <id>`.

No fatal: si un anexo falla en S3 o no abre, se omite y se registra en el log. Si la fusión falla completa, se entrega el checklist solo.

## Capas tocadas

```
HTTP   rs_SGI.py                 DownloadVehicleChecklistPDF lee ?full (1/true/yes) + @ns.doc del parámetro
mid    MD_SGI.py                 download_voucher_vehicle_pdf_api(..., full=False); _chv_build_attachments (S3 + clasificación),
                                 _chv_assemble_full_pdf (PyMuPDF), _chv_pdf_pages (numeración continua)
PDF    VehicleChecklistPDF.py    FileVehicleChecklistPhotosPDF + helpers _chv_house_cell / _chv_photo_metadata / _chv_photo_cell
```

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Departamentos `sgi` / `voucher`.
- **Ruta**: `GET /GUI/api/v1/sgi/voucher/vehicle/download/pdf/<id_voucher>?full=1`
  - `full` = `1`, `true` o `yes` → combinado. Sin `full` (o cualquier otro valor) → **solo el checklist**, como siempre.
- **200** → **blob** PDF, attachment `checklist_vehicular_<id>_completo.pdf` (sin `full`: `checklist_vehicular_<id>.pdf`). **4xx/5xx** → envelope JSON `{data, msg, error}`. El front ramifica por status code.

  ```
  200 → (binario PDF)
  404 → {"data": null, "msg": "Checklist vehicular no encontrado (ID 999)", "error": null}
  500 → {"data": null, "msg": "Error al generar el PDF del checklist vehicular", "error": "<detalle>"}
  401 → {"error": "No autorizado. Token invalido"}
  ```
- **Gotchas**:
  - Una foto debe subirse como imagen (`POST /sgi/voucher/vehicle/attachment-<id>`). Un PDF siempre cuenta como anexo.
  - Cualquier archivo con `firma` en el nombre queda fuera del combinado, aunque no sea la firma que se incrusta.
  - Sin fotos no hay hoja de evidencia.

## Al modificar

- La fusión replica el criterio de `_assemble_remission_full_pdf` (`MD_Admin_Collections.py`) a propósito, sin compartir código: si cambia una regla común (orden, no fatal por anexo, fallback al documento base), revisar las dos.
- Si los anexos vehiculares ganan `category`/`title` (como remisiones), la clasificación vive en `_chv_build_attachments`.
- La hoja de fotos usa helpers propios (`_chv_house_cell`, `_chv_photo_*`). No tocar los `_rm_*` de remisiones ni los compartidos de `PDFGenerator.py`.

## Verificación

Contra BD dev (2026-10-09), [`Tests/tester_checklist_full_pdf.py`](../Tests/tester_checklist_full_pdf.py) (gitignored), **15/15**. Usa un voucher temporal con 12 anexos simulados en S3 (firma, 2 PDFs de 2 y 1 páginas, 8 fotos de proporciones distintas y un zip) y lo borra al final. Cubre:

- **Sin `full`**: 1 página y el nombre de siempre.
- **Con `full`**: 6 páginas (checklist horizontal + 3 de anexos en orden + 2 hojas de fotos verticales con 6 y 2 fotos), con la metadata del vehículo, la numeración continua (Página 5 y 6) y el zip y la firma sin página propia.
- **Fallos**: un anexo que falla en S3 se omite (4 páginas); voucher inexistente → 404 JSON.

Páginas renderizadas a PNG (`Tests/out/checklist_full/`) y revisadas: cuadrícula y celeste de la casa, el texto largo hace wrap y las fotos quedan centradas sin deformar.

`pyrefly`: 0 errores en los 3 archivos.

## Pendientes

Hallazgos en el alta de anexos vehiculares (`create_voucher_vehicle_attachment_api`), sin tocar en este cambio:

- `extra_info.files` sigue en **lectura-modificación-escritura**: dos subidas simultáneas pueden perder una entrada. Es la misma carrera que se corrigió en remisiones ([`remission_anexos_sin_carrera.md`](remission_anexos_sin_carrera.md)).
- La validación "el nombre del archivo corresponde al voucher" usa `and` en vez de `or`, así que **nunca rechaza**.
- El voucher se busca con ventana de 365 días: uno más viejo responde 400 "Voucher vehicular no encontrado" y ya no acepta anexos.
- Si se quiere controlar qué va a la hoja de fotos vs. anexos (en vez de inferirlo por extensión), el alta puede aceptar `category`/`title` como remisiones.
