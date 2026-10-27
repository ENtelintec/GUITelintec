# PDF de la orden de compra en cuadrícula, FO-COM-04 (`GET /purchase/download/pdf/<po_id>`)

Fecha: 2026-10-27 · **Estado: hecho y verificado contra dev (PDFs renderizados y revisados; descarga por HTTP con `test_client`; `tester_iso_formats` 48/48). SQL `scripts_db_handle/iso_format_fo_com_04.sql` corrido en dev, test y prod (`P-184`, verificado en solo lectura).** Cierra `P-114`, `P-184` y `P-185`.

Decisiones del grill del 2026-10-27, sobre el plan [`planes/plan_back_sin_bloqueo_2026_10_27.md`](planes/plan_back_sin_bloqueo_2026_10_27.md). El ejemplo `OC-GC000-0283` del formato FO-COM-04 R0 sirvió de **base, no de regla**: de él se tomó la estructura (banda con folio y fecha, datos de Telintec, datos del proveedor, lista de componentes, totales); el estilo es el de la casa (skill `pdf-design`: celeste con negro, Helvetica, sin cursivas). Términos en [`GLOSSARY.md`](../GLOSSARY.md): *Partida*, *Formato*, *Fecha de emisión (de una OC)*.

## Qué cambia

- **Encabezado con el formato correcto**: la OC imprimía `FO-ALM-01 R1` (`iso_form=4`, compartido con la SM y la lista de compra). Ahora pide el **id 16 = `FO-COM-04 R0`**, con inicio de vigencia 2023-05-11. Esa fila **no existía en ninguna BD**: la da de alta el SQL de `P-184`, que además le quita "Orden de compra" al nombre del id 4.
- **Página 1**, de arriba abajo:
  - banda `ORDEN DE COMPRA | <folio de la OC>`;
  - debajo, a la derecha, `Fecha de emisión`: la del evento "Creación de orden" del `history`, o `po.timestamp` si no hay evento;
  - `Última modificación` (`po.timestamp`, que se reescribe en cada `PUT`), solo si cae en un día posterior a la emisión;
  - bloques **Datos de Telintec** y **Datos del proveedor**, con un par label | valor por fila y el orden del formato. El tiempo de entrega (`po.time_delivery`) ya no es una columna por partida (antes salía `"NA"` fijo). Ahora es el renglón **Plazo de entrega / ejecución** del bloque del proveedor.
- **Lista de componentes**: `No. | Descripción | No. de parte | UM | [Duración (meses)] | Cantidad pedida | [Moneda] | Precio unitario | Importe`.
  - **UM** sale del producto ligado (`extra_info.id_inventory` → `products_amc.udm`). Va vacía si la partida no está ligada.
  - **Duración** solo aparece si alguna partida tiene meses > 0; en las partidas sin meses, la celda va vacía.
  - **Moneda**: con una sola moneda va en el encabezado de los importes (`Precio unitario (MXN)`). Si se mezclan, aparece la columna `Moneda` y los encabezados van sin moneda.
  - El número de parte vacío ya no imprime `None`.
  - Las cantidades van sin `.0` (`3`, `2.5`, `1,250`) y el dinero como `$1,234.50`.
- **Totales**: `Subtotal / IVA (16%) / Total` en cuadrícula bajo las dos últimas columnas, con el IVA fijo al 16 %. Si se mezclan monedas, sale un bloque por moneda (`Subtotal USD`…). Los bloques nunca se parten entre páginas.
- **Multipágina**: el encabezado y los títulos de columna se repiten en cada página; la página 1 lleva lo demás.
- **Pie**: número de página y `Folio: <folio de la OC>`. Antes salía vacío, porque se leía la llave `"Folio"` y la llave es `"folio"`.
- **OC cancelada** (`status = 4`): marca diagonal gris "CANCELADA" con transparencia en cada página.
- **Fechas** en `YYYY-MM-DD`.
- **Permiso de la descarga** (`P-185`): pedía `department=["administration"]`, que no coincide con ningún permiso, así que solo descargaban los administradores. Ahora pide `["administracion", "compras"]` (decisión del usuario).
- **Limpieza**:
  - Se borran tres módulos sin quién los llame: `templates/forms/VouchersFormsPDF.py` (vale EPP/herramienta), `quotation.py` (cotización FO-PRE-01) y `Materials.py` (devolución y solicitud de materiales).
  - De `StorageMovSM.py` se borran `ReturnMaterials` y sus helpers de texto suelto: `dict_wrappers_headers`, `print_headers_table_inventory`, `print_metadata`, `print_products_list`, `print_footer_signing` y `calculate_last_y`.
  - De `PDFGenerator.py` se borran `create_header_materials` y `create_info_materials_request`, y de `constants.py`, `filepath_v_pdf`.
  - Un PDF de vale o de devolución, si se pide, se hace nuevo sobre la cuadrícula.
- **`ISO_FORM_IDS_IN_CODE`** = `{1, 2, 4, 7, 8, 14, 15, 16}`: entra el 16 y salen 3, 5 y 6, que solo pedían los generadores borrados. SGI ya puede retirarlos o borrarlos por el CRUD si no tienen controles de saldos.

## Capas tocadas

```
rs          rs_Admin_collections.py      GET /purchase/download/pdf/<int:po_id>: permiso ["administracion", "compras"] (send_file en 200, sin otro cambio)
midleware   MD_Purchases.py              dowload_file_purchase arma dict_data nuevo · create_metadata_for_pdf_po(extra_info, time_delivery)
                                         en el orden del formato · _po_emission_date (history "Creación de orden", respaldo timestamp)
controller  orders_controller.py         get_purchase_order_with_items_by_id: 'udm' por partida (LEFT JOIN products_amc por id_inventory)
forms       PurchaseForms.py (reescrito) FilePoPDF + helpers _po_* (celda, banda, par label|valor, columnas condicionales, marca cancelada)
forms       PDFGenerator.py              ISO_FORM_IDS_IN_CODE; fuera create_header_materials / create_info_materials_request
forms       StorageMovSM.py              fuera ReturnMaterials y helpers de texto suelto
forms       VouchersFormsPDF.py, quotation.py, Materials.py   borrados
static      constants.py                 fuera filepath_v_pdf
sql         scripts_db_handle/iso_format_fo_com_04.sql (P-184, sin correr)
```

`dict_data` de `FilePoPDF` (documentado en su docstring): `filename_out`, `folio`, `cancelled`, `emission`, `modified`, `metadata_telintec`, `metadata_supplier`, `products` (dicts con `no`, `description`, `n_parte`, `udm`, `duration`, `quantity`, `currency`, `unit_price`, `subtotal`), `totals` (moneda → subtotal sin IVA).

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. Permiso: `administracion` o `compras`, que coinciden por subcadena con `App.Department.Administracion`, `adminCompras` y `comprasCreate`; los administradores siempre pasan. Antes solo descargaban los administradores.
- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Request**: `GET /purchase/download/pdf/<po_id>`, sin body ni query. **No cambió**.
- **Respuesta**: **200 = blob binario** `application/pdf` con `Content-Disposition: attachment; filename=oc_<folio>_<fecha de emisión>.pdf`. Antes llevaba la fecha de `po.timestamp`, la última modificación. **4xx = JSON** `{data, msg, error}`. El front decide por el **status**, no por el content-type.

| Código | Cuándo | Cuerpo |
|---|---|---|
| **200** | la OC existe | blob PDF, p. ej. `oc_OC-DUMMY-1_2026-07-10.pdf` |
| **401** | sin token | `{"error": "Token not found"}` |
| **401** | token sin permiso (p. ej. `App.Department.Operaciones`, `Almacen`) | `{"error": "No autorizado. Token invalido"}` |
| **400** | el id no existe | `{"data": null, "msg": "Orden de compra no encontrada (ID 999999)", "error": "None"}` |
| **400** | falla la lectura en BD o la generación | `{"data": null, "msg": "Error al obtener la orden de compra" o "Error al generar el PDF de la orden de compra", "error": "..."}` |

### Gotchas

- Descargar con `responseType: "blob"`; si el status no es 200, leer el blob como texto y parsear el JSON para pintar `msg`.
- El encabezado lee `Codigo: FO-COM-04 R0` e `I. Vigencia: 2023-05-11` del catálogo (id 16, ya en las 3 BDs). Si la fila faltara, saldría vacío sin tumbar el PDF.
- Una OC cancelada **sí** se descarga, con la marca "CANCELADA".

## Al modificar

- **Columnas**: `_po_item_cols` arma la lista `(clave, encabezado, ancho, alineación)` y las celdas se llenan por **clave** con `_po_cell_text`. Descripción absorbe el ancho que dejan las demás; si se agrega una columna fija, quitarle ancho a las otras para que Descripción no baje de ~120 pt.
- **Campos de los bloques**: se agregan en `create_metadata_for_pdf_po`, en el orden de impresión; el PDF no conoce las llaves.
- **Nueva revisión del formato** (R1): solo en `iso_formats` por el CRUD de SGI ([`iso_formats_crud.md`](iso_formats_crud.md)). El id 16 no cambia.
- **Despliegue**: primero el SQL en la BD del entorno y después el código. Al revés no truena, solo deja el encabezado vacío hasta 5 min después de correr el SQL (caché de `iso_format_header`).

## Verificación (2026-10-27, dev)

- PDFs renderizados y revisados:
  - sintético de 45 partidas en 3 páginas, cancelado, con duración, descripciones y números de parte largos, montos de 9 dígitos y última modificación;
  - monedas mezcladas USD/MXN, con dos bloques de totales;
  - OC sin partidas;
  - las 12 OCs de dev por el midleware, con la UM del producto ligado (`PIEZA`).
- HTTP con `test_client`: 200 `application/pdf` con el nombre nuevo, 400 con un id inexistente y 401 sin token. Por permiso: 200 con `Administrator`, `Administracion`, `adminCompras` y `comprasCreate`; 401 con `Operaciones` y `Almacen`.
- `tester_iso_formats` 48/48 (esperado de `ids_bound_to_pdf` actualizado).
- Smoke de `FileSmPDF` e `InventoryStoragePDF` tras la limpieza de `StorageMovSM.py`.
- `import app` sin errores; `pyrefly check --python-version 3.11` sin errores en los archivos tocados.

## Pendientes

- ~~`P-184`~~ cerrado el mismo día: el usuario corrió el SQL en las 3 BDs; verificado en solo lectura (id 16 y nombre del id 4).
- ~~`P-185`~~ cerrado el mismo día: la descarga pide `["administracion", "compras"]`.

## Notas posteriores

- **2026-10-27 — permiso exacto** ([`permisos_compras_y_baja.md`](permisos_compras_y_baja.md)): la descarga pasó a `permissions=_PO_PERMS`, es decir, exacto `App.Department.Administracion` o `App.Department.adminCompras` (Administrator siempre). `comprasCreate` ya no descarga; lo había ganado con la subcadena `compras` de `P-185`. El contrato de arriba queda con esa corrección.
