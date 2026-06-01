# Lista de compra (PDF) — `FilePurchaseList`

PDF con apariencia de **tabla / ticket de compra**: agrupa los ítems aprobados
por **proveedor** y, dentro de cada proveedor, por **inventario**. Cada nivel
muestra sus totales y al final del documento se imprime un **GRAN TOTAL** global.

Definida en [`templates/forms/StorageMovSM.py`](../templates/forms/StorageMovSM.py)
(`FilePurchaseList`). La genera el midleware
[`download_file_purchase_item_approved`](../templates/resources/midleware/MD_Purchases.py)
a partir de los ítems con entrega en estado de compra OK.

## Flujo

```
download_file_purchase_item_approved(data_token)
  → recolecta ítems SM con delivery.state == 4 y su PO (precio, proveedor)
  → group_item_by_supplier_and_inventory(items)   # arma dict_data
  → FilePurchaseList(dict_data, download_path)     # genera el PDF
  → devuelve {"data": <ruta_pdf>}                  # se descarga
```

El PDF se escribe en un directorio temporal (`tempfile.mkdtemp()`).

## Estructura de `dict_data`

Producida por `group_item_by_supplier_and_inventory`:

```python
{
    supplier_id: {
        "supplier_name": str,
        "inventories": {
            id_inventory: {
                "items": [
                    {
                        "name": str,
                        "id_item": int,
                        "quantity_c": int,    # cantidad comprada
                        "price_unit": float,  # precio unitario (de la PO)
                        "folio_po": str,      # folio de la orden de compra
                        "folio": str,         # folio de la SM
                    },
                    ...
                ],
                "total_qty": int,             # suma de cantidades del inventario
                "total_amount": float,        # suma de price_unit * quantity_c
            },
        },
    },
}
```

## Layout del PDF

Página **horizontal** (ancho = `a4_y` = 841.89 pts). Por cada proveedor:

1. **Barra azul** con `Proveedor: <nombre> (ID: <id>)`.
2. **Fila de encabezados de columna** (una sola vez por proveedor):
   `Descripcion | Cant | P. Unit | PO | SM | Total`, con línea separadora.
3. Por cada **inventario**: línea resumen `Inventario: <id> · Cant. total · Monto total`.
4. **Filas de ítems** del inventario (valores alineados, sin etiquetas en línea).
5. Al cerrar el proveedor: **`Subtotal proveedor: $...`** en negrita, alineado a la derecha.

Al final del documento: **barra resaltada `GRAN TOTAL` $...`** con la suma de todos
los proveedores.

### Columnas y alineación

Las posiciones se controlan con las anclas `_PL_X_*` a nivel de módulo. Las
columnas de número/dinero usan `drawRightString` (el valor **termina** en la x);
las de texto usan `drawString` (el valor **empieza** en la x).

| Columna      | Ancla        | x   | Alineación |
|--------------|--------------|-----|------------|
| Descripción  | `_PL_X_DESC` | 45  | Izquierda  |
| Cant         | `_PL_X_CANT` | 410 | Derecha    |
| P. Unit      | `_PL_X_PUNIT`| 515 | Derecha    |
| PO           | `_PL_X_PO`   | 550 | Izquierda  |
| SM           | `_PL_X_SM`   | 660 | Izquierda  |
| **Total**    | `_PL_X_TOTAL`| 820 | Derecha    |

> El **Total** (subtotal por ítem = `price_unit * quantity_c`) queda en el
> **extremo derecho** de cada fila, como en una lista de compras.

La descripción se envuelve a 40 caracteres (`textwrap.wrap`); si ocupa varias
líneas, los valores numéricos se alinean con la **primera** línea del ítem.

### Niveles de totales

| Nivel       | Origen                                  | Estilo                       |
|-------------|-----------------------------------------|------------------------------|
| Inventario  | `inv_data["total_amount"]` (ya existía) | Línea resumen del inventario |
| Proveedor   | Σ de los `total_amount` del proveedor   | Negrita, alineado a derecha  |
| Global      | Σ de los subtotales de proveedor        | Barra resaltada al final     |

## Saltos de página

`check_page_break` reinicia en `y < 40`: imprime el folio de página, llama a
`pdf.showPage()`, redibuja el encabezado Telintec y vuelve a `y = 500`. Los
encabezados de columna se imprimen **una vez por proveedor**, no se repiten tras
un salto de página dentro del mismo proveedor.

## Al modificar

- Para mover columnas, ajusta las constantes `_PL_X_*` (no hay valores mágicos
  dispersos en el cuerpo de la función).
- Si cambia la estructura de `dict_data`, actualiza también
  `group_item_by_supplier_and_inventory` en `MD_Purchases.py`.
