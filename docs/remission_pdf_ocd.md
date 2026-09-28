# PDF de remisión "en limpio" para OCD (FO-CXC-05): layout automático en `GET /remission/download/pdf/<id>`

Fecha: 2026-09-28 · **Estado: hecho y verificado contra dev (17/17 checks, `Tests/tester_remission_pdf_ocd.py`; PDF real renderizado y revisado). Sin DDL: el código FO-CXC-05 R0 viene sembrado en `iso_formats` (id 14) por [`control_entregas_ocd.sql`](../scripts_db_handle/control_entregas_ocd.sql).**

Fase **F5** del plan [`planes/control_entregas_ocd_plan.md`](planes/control_entregas_ocd_plan.md) (junta 2026-09-23: "Óscar genera la remisión con un formato en limpio, sin partir de Control de Reportes"; formato FO-CXC-05 R0 "REM OC Directas" enviado por Cobranza). Extiende [`remission_pdf_download.md`](remission_pdf_download.md) y [`remission_combined_pdf.md`](remission_combined_pdf.md); usa la membresía de [`control_entregas.md`](control_entregas.md).

## Qué cambia

El PDF de remisión ya tenía casi todo lo que pide FO-CXC-05 (bloque fiscal de Telintec, `POS.`/descripción/cantidad/UM/precio unitario/total, subtotal/IVA/total, dos firmas de autorización). Lo que faltaba era el **encabezado y la metadata** del formato sin contrato. Ahora `FileRemissionPDF` tiene dos layouts:

| Layout | Formato ISO | Título | Metadata (página 1) |
|---|---|---|---|
| `contract` (histórico) | FO-CXC-01 R0 (id 7) | REMISIÓN | Fecha · Remisión Telintec · Proyecto · **No. Contrato Marco** · No. Pedido Exiros · No. Pedido · Remito |
| `ocd` (nuevo) | **FO-CXC-05 R0 (id 14)** | REMISIÓN OC DIRECTA | Fecha · Remisión Telintec · **No. Pedido Exiros** · **Tipo de moneda** · **Cotización / OCD** · No. Pedido · Proyecto · Remito |

- **Selección automática**: sin `contract_id` → `ocd`; con contrato → `contract`. **`?layout=ocd|contract`** lo fuerza (p. ej. una remisión de contrato que el cliente pidió "en limpio").
- En el layout `ocd`, si la remisión está ligada a un control de entregas (`delivery_control_id`), el **pedido EXIROS** (`client_po_number`), la **moneda** y el **código de la cotización OCD** salen del control; sin control, `pedido_exiros` de la remisión y `MXN`.
- El cuerpo (tabla de items en cuadrícula celeste, totales, firmas, `?full=1` con anexos y fotos, saltos de página) es el mismo en ambos layouts. El código y la vigencia del encabezado se leen del catálogo `iso_formats` (SGI puede subir la revisión sin tocar código).
- De paso: `Proyecto` ya no imprime `None` cuando la remisión no tiene proyecto (afectaba a ambos layouts).

## Capas tocadas

```
forms       templates/forms/RemissionForms.py          _RM_LAYOUTS {"contract": 7, "ocd": 14} · FileRemissionPDF(dict_data["layout"|"currency"|"quotation_code"]) decide iso_form, título y filas de metadata
midleware   MD_Admin_Collections.py                    download_file_remission(layout=None): auto por contract_id, lee el control de entregas (índice 22 de get_remission_by_id) para PO/moneda/cotización
routes      rs_Admin_collections.py                    GET /remission/download/pdf/<id> lee ?layout=
```

Sin cambios en `_assemble_remission_full_pdf` ni en `FileRemissionPhotosPDF` (la hoja de fotos sigue con FO-CXC-01: es un anexo, no la remisión).

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permisos `administracion` / `purchases` (sin cambio).
- **`GET /remission/download/pdf/<id_report>`** — query: `iva_rate` (default `0.16`), `full=1` (combinado), **`layout=ocd|contract`** (opcional).
- **200** → **blob `application/pdf`** (`send_file`, `as_attachment`); el front lo descarga tal cual. **4xx** → JSON `{data, msg, error}` (404 remisión inexistente, 400 error al generar). El front decide por el status.
- Regla de default que el front puede anticipar para el nombre del botón: `contract_id === null` → sale FO-CXC-05; si el usuario quiere el otro formato, mandar `layout`.

### Gotchas

- El pedido EXIROS impreso prioriza el que la remisión trae en `extra_info.pedido_exiros`; solo si está vacío toma el `client_po_number` del control. Capturar uno u otro, no ambos distintos.
- `Tipo de moneda` es la del control de entregas / cotización OCD, no la del control de saldos.

## Al modificar

- **Otro layout** (p. ej. remisión de servicio con reporte): agregar la entrada a `_RM_LAYOUTS` con su `iso_formats.id`, su rama de `metadata_rows` en `draw_header_and_metadata` y el valor aceptado en `download_file_remission`; el resto se hereda.
- Si SGI sube FO-CXC-05 a R1, no hay que tocar código: `iso_format_header` lee code + revision + vigencia por id (caché de 5 min).
- Cualquier dato nuevo del control de entregas que deba imprimirse se toma en el midleware por `DELIVERY_CONTROL_COLUMNS` (append-only) y se pasa en `dict_data`; el form no consulta BD.
