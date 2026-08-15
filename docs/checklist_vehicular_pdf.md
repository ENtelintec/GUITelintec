# Descarga de PDF del Check List Vehicular (FO-CDA-03 R3)

Nuevo endpoint que genera y descarga el PDF formal del **checklist vehicular**
(voucher vehicular de SGI: `vouchers_general` + `voucher_vehicle`), replicando
el formato oficial **FO-CDA-03 R3** — página horizontal con DATOS DEL VEHÍCULO
(casillas SI/NO de tarjeta/seguro/refrendo), ESTADO DE ACCESORIOS Y
HERRAMIENTAS (catálogo fijo de 36 conceptos con BIEN/MAL/N/A), OBSERVACIONES,
TIPO DE VEHICULO (siluetas sedán/pickup/van) y firmas REALIZADO/RECIBIDO
incrustadas desde S3. Sigue el patrón de descarga de
`GET /sm/download/pdf/<sm_id>` y `GET /remission/download/pdf/<id>`.

A diferencia de los demás PDFs de la casa (celeste `#BDD7EE` + texto negro),
este documento usa deliberadamente los **colores del formato oficial**: barras
azul brillante `#00AFEF` con texto blanco bold (decisión de diseño acordada;
muestreado del PDF de referencia
[`scripts_db_handle/FO-CDA-03 R3 Check list vehicular.pdf`](../scripts_db_handle/FO-CDA-03%20R3%20Check%20list%20vehicular.pdf)).
El resto de la mecánica sí es la del skill `pdf-design` (canvas puro, Courier,
cuadrícula de `rect`s, wrap por celda, header institucional, pie con folio).

## Endpoint

`GET /GUI/api/v1/sgi/voucher/vehicle/download/pdf/<int:id_voucher>`

- Departamentos: `["sgi", "voucher"]` (los mismos del resto de rutas
  `/voucher/vehicle*`).
- **Sin ventana de fecha**: cualquier voucher existente es descargable (las
  otras rutas de vouchers filtran al último año; aquí se buscó por ID con una
  query dedicada). El "borrado" de un voucher solo marca el `history` — no hay
  columna de estatus que filtrar, así que un voucher eliminado/cancelado sigue
  siendo descargable.
- El documento es de **una página**; si unas observaciones larguísimas o muchos
  accesorios fuera de catálogo desbordan, continúa en una segunda página con el
  mismo header (paginación defensiva, no debería ocurrir con capturas normales).

## Capas tocadas

1. **HTTP** — [`rs_SGI.py`](../templates/resources/rs_SGI.py): ruta nueva
   `DownloadVehicleChecklistPDF`; `send_file` en 200, envelope en 4xx/5xx.
2. **Orquestación** — [`MD_SGI.py`](../templates/resources/midleware/MD_SGI.py):
   `download_voucher_vehicle_pdf_api(id_voucher, data_token)` — resuelve
   campos, decodifica `accessories`/`extra_info`, baja las firmas de S3
   (`_chv_signature_from_files`, no fatal) y llama al generador. Helpers
   `_chv_json_field` (decodifica hasta 2 veces: `accessories` se persiste
   **doble-codificado** — un string JSON que contiene otro string JSON) y
   `_chv_downscale_signature_image` (tope 600px, mismo mecanismo que el PDF de
   SM).
3. **DB** — [`vouchers_controller.py`](../templates/controllers/vouchers/vouchers_controller.py):
   `get_voucher_vehicle_by_id` nueva — por ID sin filtro de fecha, con
   `LEFT JOIN` doble a `sql_telintec.employees` para los nombres de
   `vg.user` (realizado) y `vv.received_by` (recibido). No se reutilizó
   `get_vouchers_vehicle_with_items` porque su `WHERE` con `OR` no filtra por
   id cuando `user` va en `NULL` (devuelve todo y los callers filtran en
   Python). Sin cambio de esquema.
4. **PDF** — [`VehicleChecklistPDF.py`](../templates/forms/VehicleChecklistPDF.py)
   (archivo nuevo): `FileVehicleChecklistPDF(dict_data)`, helpers `_chv_*`
   propios (no toca los compartidos de `StorageMovSM.py`). El catálogo oficial
   de accesorios vive ahí (`_CHV_GROUPS`, 6 grupos × 6 conceptos, los últimos
   dos con columna N/A).

Además: siluetas extraídas del PDF oficial como assets
[`img/checklist_sedan.png`](../img/checklist_sedan.png) /
[`img/checklist_pickup.png`](../img/checklist_pickup.png) /
[`img/checklist_van.png`](../img/checklist_van.png), y el código de formato
`FO-CDA-03 R3` / vigencia `2025-04-24` agregado como `iso_form=8` en
`files/settings.json` (`formats.dict_codes_forms` / `formats.dates_emision`).

## Mapeo de campos

| Campo del PDF | Origen |
| --- | --- |
| FECHA DE ELABORACIÓN | `vouchers_general.date` (formateada `dd/mm/aaaa`) |
| MARCA / MODELO / COLOR / AÑO / PLACAS / KILOMETRAJE | `voucher_vehicle.brand/model/color/year/placas/kilometraje` |
| TARJETA DE CIRCULACIÓN / PÓLIZA DE SEGURO / COMPROBANTE DE REFRENDO | `registration_card` / `insurance` / `referendo`: `1`→SI, `0`→NO, `-1` u otro → ambas casillas en blanco |
| ESTADO DE ACCESORIOS | `accessories` (`[{label, value}]`): lookup case-insensitive del `label` contra el catálogo fijo; `value` `Bien`/`Mal`/`N/A` marca su columna; concepto sin dato = casillas en blanco; labels fuera del catálogo se agregan como filas DESCRIPCIÓN\|ESTADO al final |
| TIPO DE VEHICULO | `voucher_vehicle.type`: `0`=sedán, `1`=pickup, `2`=van (marca la casilla de su silueta) |
| OBSERVACIONES | `voucher_vehicle.observations` |
| REALIZADO POR (nombre) | `vouchers_general.user` → `employees` (`name + l_name`) |
| RECIBIDO POR (nombre) | `voucher_vehicle.received_by` → `employees` |
| Firma REALIZADO / RECIBIDO | último attachment de `extra_info["files"]` cuyo nombre contiene `firma-aprobado` / `firma-recibido` (el mismo criterio con el que el alta de attachment mueve `status` a 1/2), descargado de `S3_CH_BUCKET`; no dibujable o falla de S3 → recuadro en blanco para firma a mano |

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**
  (el back hace `jwt.decode` del header tal cual, sin quitar prefijos).
- **Base**: `GET /GUI/api/v1/sgi/voucher/vehicle/download/pdf/<id_voucher>`
  — `id_voucher` es el `id_voucher_general` que ya manejan las pantallas de
  vouchers. Sin body ni query params.
- **Respuesta 200**: **blob binario** del PDF (attachment
  `checklist_vehicular_<id>.pdf`). En error el body es el envelope JSON
  `{data, msg, error}` — **el front debe ramificar por status code**, no por
  content-type.

Ejemplos:

```
200 → (binario PDF)

404 → {"data": null, "msg": "Checklist vehicular no encontrado (ID 999)", "error": null}

400 → {"data": null, "msg": "No se pudo obtener el checklist vehicular", "error": "<detalle SQL>"}

500 → {"data": null, "msg": "Error al generar el PDF del checklist vehicular", "error": "<detalle>"}

401 → {"error": "No autorizado. Token invalido"}
```

Gotchas:

- Las firmas se incrustan solo si el archivo subido vía
  `POST /sgi/voucher/vehicle/attachment-<id>` se llamó con `firma-aprobado` /
  `firma-recibido` en el nombre **y** es imagen (`jpg/jpeg/png/webp`); un PDF
  escaneado con ese nombre mueve el estatus pero no se dibuja.
- Si el mismo nombre de firma se subió varias veces, **gana la última** entrada
  de `extra_info["files"]`.
- Los tres SI/NO: el front manda `-1` como "sin capturar" en el alta — el PDF
  los deja en blanco (no marca NO).

## Al modificar

- El catálogo de accesorios (`_CHV_GROUPS`) replica el FO-CDA-03 R3 **posición
  por posición**; si el formato cambia de revisión, se edita ahí y se actualiza
  `iso_form=8` en `files/settings.json` (código y vigencia).
- El azul `#00AFEF` (`_CHV_AZUL`) es exclusivo de este documento — no
  propagarlo a otros PDFs (la casa usa el celeste del skill `pdf-design`).
- El lookup de accesorios matchea por label normalizado (trim + colapso de
  espacios + lower). Si el front renombra un label del catálogo, ese concepto
  dejará de marcarse y la captura caerá a las filas de "fuera de catálogo" —
  mantener los labels idénticos al formato.
- Las siluetas son renders del PDF oficial (clips con PyMuPDF); si se
  reemplazan, cuidar que el fondo sea blanco/limpio — el generador las dibuja
  tal cual (sin máscara).
- `get_voucher_vehicle_by_id` indexa por posición en el midleware (0–20, los
  nombres al final); columnas nuevas van **al final** del SELECT.

## Pendientes

- **[back] Variante combinada `?full=1`** (checklist + anexos + evidencia
  fotográfica, como remisiones) — la maquinaria de fusión con PyMuPDF ya existe
  en `MD_Admin_Collections`.
- **[back+front] Captura de archivo de foto del vehículo en CDA** (Control de
  Activos, namespace `/cda`) — pedido al acordar este PDF: hoy las siluetas son
  genéricas; la idea es poder adjuntar fotos reales del vehículo en su
  expediente de CDA.
- **[back] Doble-codificación de `accessories`**: el alta persiste el JSON de
  los accesorios como string dentro de la columna JSON (`json.dumps` dos
  veces); el lector ya lo tolera (`_chv_json_field`), pero valdría corregir el
  alta y normalizar los datos existentes.
