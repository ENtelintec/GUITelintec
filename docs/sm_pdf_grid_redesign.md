# Rediseño del PDF de SM: metadata e items en cuadrícula, celeste, tabla de entregas

El PDF de SOLICITUD DE MATERIAL (`GET /sm/download/pdf/<sm_id>`) pasó de texto
suelto (labels y columnas por posición fija, sin líneas) a un diseño en
**cuadrícula** con los nombres de campos y encabezados de columna resaltados en
**celeste** (`#BDD7EE`, fondo con texto negro Courier-Bold). También corrige el
desborde de valores largos de metadata (p. ej. "Personal Telintec"): ahora el
valor hace wrap dentro de su celda y la fila crece en alto.

## Las capas tocadas

```
mid    MD_SM.py  dowload_file_sm        -> calcula delivery_rows desde extra_info["files"]
forms  StorageMovSM.py  FileSmPDF       -> reescrito; helpers _sm_* nuevos solo para SM
```

(Endpoint y controller sin cambios; el contrato HTTP es el mismo.)

## Diseño del documento

- **Técnica**: canvas + `pdf.rect()` por celda (estilo `RemissionForms.py`), sin
  platypus. El wrapping usa `textwrap` con ancho en caracteres derivado del
  ancho de la celda — fiable porque todo el documento es Courier (monospace).
- **Metadata**: cuadrícula de 4 columnas — 2 pares `label|valor` por fila, los
  10 campos actuales (se conservan "Área Dirigida Telintec" y
  "Área / Ubicación" aunque ambas impriman `location`; decisión explícita del
  usuario). Label en celda celeste; la fila crece si el label o el valor hacen
  wrap.
- **Items**: cuadrícula completa con fila de encabezados celeste. Columnas (en
  el orden del tuple de `products`): `No. | Descripción | Cantidad | UDM |
  C. Suministrado | Estatus`. **Ojo**: el PDF anterior tenía los encabezados
  UDM/Cantidad cruzados respecto a los datos (la cantidad caía bajo "UDM");
  quedó corregido alineando `_SM_ITEM_COLS` al tuple.
- **Multipágina**: cada página nueva repite el header Telintec y la fila de
  encabezados de columna; la metadata solo va en la página 1. Folio y número de
  página en el pie de cada página.
- **Observaciones**: fuera del documento (antes ya no se imprimían; ahora
  tampoco se pasan a `FileSmPDF`). El `comment` de la SM sigue disponible en
  `result[13]` si se quiere reintroducir.
- **Entregas/firmas**: reemplaza los 4 renglones de línea punteada por una
  tabla para llenar a mano — `No. | Fecha de Entrega | Firma de Quien Entrega |
  Firma de Quien Recibe` con **una fila por attachment** de la SM
  (`extra_info["files"]`, mínimo 1, cap 20 para no exceder una página) y debajo
  un campo único "Fecha de Entrega Completa". Ya no existen "fecha de 1ª
  entrega" ni los valores hardcodeados `date_first_delivery`/
  `date_complete_delivery` que se pasaban y nunca se usaban.

## Contrato de `FileSmPDF`

```python
{
    "filename_out": str,
    "metadata": {label: valor, ...},          # se imprime en el orden del dict
    "products": [(no, nombre, cantidad, udm, suministrado, estatus), ...],
    "delivery_rows": int,                     # filas de la tabla de entregas (>=1, cap 20)
}
```

`dowload_file_sm` calcula `delivery_rows = max(1, len(extra_info["files"]))`.
La idea (del usuario): cada attachment representa una entrega; a futuro el
attachment podrá cargar más info (fecha, etc.) y pre-llenar la fila.

## Helpers nuevos (solo SM)

En [`StorageMovSM.py`](../templates/forms/StorageMovSM.py), prefijo `_sm_`/`*_sm`:
`_sm_wrap_cell`, `_sm_draw_cell`, `print_metadata_grid_sm`,
`print_items_grid_headers_sm`, `_sm_item_row`, `_sm_item_row_height`,
`print_deliveries_sign_table_sm`, `sm_deliveries_block_height`; constantes
`_SM_CELESTE`, `_SM_MARGIN`, `_SM_ITEM_COLS`, `_SM_DELIVERY_COLS` (los anchos de
columna suman `_SM_GRID_WIDTH`).

Los helpers viejos (`print_metadata`, `print_headers_table_inventory`,
`print_products_list`, `print_footer_signing`, `dict_wrappers_headers["SM"]`)
**siguen existiendo** porque los comparten `InventoryStoragePDF` y
`ReturnMaterials` — el rediseño no los toca.

## Al modificar

- Para agregar/cambiar una columna de items: editar `_SM_ITEM_COLS` (nombre y
  ancho, los anchos deben sumar `_SM_GRID_WIDTH`) **y** mantener el orden del
  tuple que arma `dowload_file_sm` en `products`. El header y la celda se
  alinean por posición, no por nombre.
- Campos nuevos de metadata: solo agregarlos al dict `metadata` en
  `dowload_file_sm`; la cuadrícula acomoda pares en orden y la última fila
  puede quedar con un solo par.
- Si un attachment debe pre-llenar su fila de entrega (fecha, nombre),
  extender `print_deliveries_sign_table_sm` para recibir la lista de files en
  vez del conteo.
- `_SM_MARGIN` es `25.0` (float) a propósito — con `25` (int) pyrefly marca
  `bad-assignment` en los `x += w` acumulativos.

## Pendiente

- **Firmas/entregas pre-llenadas desde los attachments**: los attachments ya
  guardan `timestamp` y `title` por entrega
  (ver [`sm_attachment_delivery_title.md`](sm_attachment_delivery_title.md));
  falta que `print_deliveries_sign_table_sm` reciba la lista de files (no el
  conteo) y pre-llene la columna "Fecha de Entrega" con `timestamp` y el
  número/título con `title` — las firmas siempre quedan en blanco (se firman
  en papel).
