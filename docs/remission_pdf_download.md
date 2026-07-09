# Descarga de PDF de una remisión

Nuevo endpoint que genera e imprime el PDF formal de **una remisión ya creada**
(`activity_reports`), replicando el formato "REMISIÓN" de Telintec (logo, datos
de contrato/pedido, tabla de items, totales y firmas). Sigue el mismo patrón que
`GET /purchase/download/pdf/<int:po_id>`: por ID, un solo documento.

Alcance: solo la **página 1** del documento de referencia (encabezado + metadata +
items + totales). Los anexos que puede llevar el paquete completo entregado al
cliente (reporte de materiales formato Ternium, evidencia fotográfica) **no** se
generan aquí — son otros documentos/procesos.

## Endpoint

`GET /GUI/api/v1/admin/collections/remission/download/pdf/<int:id_report>?iva_rate=0.16`

- `iva_rate` es opcional en query string (default `0.16`); el back calcula
  `iva = subtotal * iva_rate` — el front no manda el monto ya calculado, para
  que el back sea la única fuente de verdad del cálculo.
- Departamentos: `["administracion", "purchases"]` (mismos que el resto de rutas
  de remisión).
- Remisión sin items: no es error, genera el PDF con la tabla vacía
  (`TOTAL POS. 0`, subtotal/iva/total en `$0.00`).

## Capas tocadas

1. **HTTP** — [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py):
   ruta nueva `DownloadPDFRemission`, usa `send_file` igual que la descarga de PDF de OC.
2. **Orquestación** — [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py):
   función nueva `download_file_remission(id_report, iva_rate, data_token)` — arma
   `products`/metadata desde `get_remission_by_id` + `get_contract`, calcula
   subtotal/iva/total, llama a `FileRemissionPDF` y devuelve la ruta temporal.
3. **DB** — [`remisions_controller.py`](../templates/controllers/presales/remisions_controller.py):
   `get_remission_by_id` gana un `LEFT JOIN` a `quotation_items` (vía
   `qai.item_c_id = qi.id`) para incluir `partida` en cada item; sin cambio de
   esquema (la columna ya existía en `quotation_items`).
4. **PDF** — [`RemissionForms.py`](../templates/forms/RemissionForms.py) (archivo
   nuevo): `FileRemissionPDF(dict_data)`, header/logo vía `create_header_telintec`
   (mismo helper que usan las OC), paginación propia para la tabla de items.

Además: `filepath_remission_pdf` nuevo en
[`static/constants.py`](../static/constants.py), y el código de formato
`FO-CXC-01 R0` / vigencia `2023-05-11` agregado como `iso_form=7` en
`files/settings.json` (`formats.dict_codes_forms` / `formats.dates_emision`).

## Mapeo de campos (encabezado)

| Campo del PDF | Origen |
| --- | --- |
| Fecha | `ar.date` |
| Remision Telintec | `ar.folio` |
| Proyecto (código + descripción) | `extra_info.project` + `extra_info.project_description` |
| No. Contrato Marco | `contracts.code`, vía `ar.contract_id` → `get_contract` |
| No. Pedido Exiros | `extra_info.pedido_exiros` |
| No. Pedido | `extra_info.pedido` |
| Remito | `extra_info.remito` |
| Bloque empresa (RFC, dirección, contacto, representante legal) | Estático, hardcodeado en `RemissionForms.py` (`_COMPANY_INFO_LINES`) |
| POS. (por item) | `quotation_items.partida`, vía `item_c_id` — vacío si el item no viene de una cotización |
| Descripción / Cant. / UM / Precio Unit. / Total (por item) | `quotation_activity_items.description/quantity/udm/unit_price/line_total` |
| SUBTOTAL | `Σ line_total` de los items impresos (no `extra_info.total_sin_iva`, que es un campo capturado a mano en Control de Reportes y no siempre coincide) |
| IVA / TOTAL | `subtotal * iva_rate` / `subtotal + iva` |

## Bug corregido de paso

`get_contract(data_token, id_contract)` en
[`contracts_controller.py`](../templates/controllers/contracts/contracts_controller.py)
tenía `if not isinstance(result, tuple) or not isinstance(result, list):` —
siempre `True` para un `tuple` encontrado (nunca es tuple y list a la vez), así
que **siempre devolvía `flag=False`** al pedir un contrato por ID específico.
Rompía también el endpoint existente `GET /contract/<id>`
(`get_contracts(id_contract=X)` en `Functions_midleware_admin.py`). Se corrigió a
`if not (isinstance(result, tuple) or isinstance(result, list)):`, verificado
contra la BD de dev (`get_contract(data_token, 4)` ahora sí devuelve el contrato).

## Al modificar

- El bloque de empresa (`_COMPANY_INFO_LINES`) es texto fijo — si cambia el
  domicilio/contacto/representante legal de Telintec, se edita solo ahí.
- El código de control documental (`FO-CXC-01 R0`) y su vigencia viven en
  `files/settings.json` bajo `iso_form=7`; si el formato de remisión cambia de
  revisión, actualizar esa entrada (no hardcodear el string en el PDF).
- Si se agrega un campo nuevo a la metadata impresa, añadirlo a `metadata_rows`
  dentro de `draw_header_and_metadata()` en `RemissionForms.py` y resolver su
  origen en `download_file_remission`.
- Pendiente a futuro (fuera de este alcance): anexar al PDF final el reporte de
  materiales (formato Ternium) y las fotos ya subidas en `ar.files`, si se pide
  como un solo documento combinado.
