# Semáforo de surtido en los items del PDF de SM

La tabla de items del PDF de SOLICITUD DE MATERIAL
(`GET /sm/download/pdf/<sm_id>`) ahora **se colorea según lo surtido**: verde
cuando la cantidad suministrada cubre la pedida, amarillo cuando hay surtido
parcial y rojo cuando no se ha despachado nada. Continúa el diseño de
[`sm_pdf_grid_redesign.md`](sm_pdf_grid_redesign.md) y
[`sm_pdf_delivery_signatures.md`](sm_pdf_delivery_signatures.md).

## Las capas tocadas

```
forms  StorageMovSM.py  _grid_draw_cell   -> nuevo param fill_color (RGB explícito)
forms  StorageMovSM.py  print_grid_row    -> nuevo param cell_fills (lista por columna)
forms  StorageMovSM.py  _sm_item_fills    -> clasifica la fila y devuelve sus colores
forms  StorageMovSM.py  FileSmPDF         -> pasa cell_fills al imprimir cada item
mid    MD_SM.py  dowload_file_sm          -> reconoce "(Semidespachado)" en el estatus
```

(Endpoint, controller y contrato HTTP sin cambios. El **Excel** de la SM queda
igual — es un `df.to_excel` plano y no gana color.)

## Regla de color

Cascada evaluada por item, en este orden:

| Condición | Resultado |
|---|---|
| `quantity <= 0` (o valor no numérico) | **sin color** — dato incompleto |
| `dispatched >= quantity` | **verde** en **toda la fila** (las 6 celdas) |
| `dispatched > 0` | **amarillo** solo en la celda `No.` |
| resto | **rojo** solo en la celda `No.` |

Decisiones detrás de la cascada:

- **El sobre-despacho (`dispatched > quantity`) cuenta como completo** y se pinta
  verde. `add_dispatch_sm` ya trata ese caso como anomalía en su propio flujo
  ([MD_SM.py](../templates/resources/midleware/MD_SM.py)); el PDF no lo vuelve a
  señalar.
- **`quantity <= 0` no se pinta.** Una SM con captura incompleta saldría entera
  en rojo y daría una lectura falsa de "nada surtido".
- **Solo el verde ocupa la fila completa**; amarillo y rojo se limitan a la
  columna `No.` para no estorbar la lectura de la descripción, que es la celda
  con más texto.

## Paleta

Pasteles de formato condicional tipo Excel, misma familia de tintes que el
celeste `#BDD7EE` de la casa (ver la skill `.claude/skills/pdf-design/`), así que
el texto negro Courier sigue siendo legible encima:

```python
_SM_VERDE    = (0.78, 0.94, 0.81)  # #C6EFCE  surtido completo
_SM_AMARILLO = (1.00, 0.92, 0.61)  # #FFEB9C  surtido parcial
_SM_ROJO     = (1.00, 0.78, 0.81)  # #FFC7CE  sin surtir
```

**No lleva leyenda**: la propia fila ya trae `Cantidad`, `C. Suministrado` y
`Estatus` en texto, así que el color es refuerzo visual y nadie depende de él
para entender el documento (importa para impresión en B/N y para daltonismo).

## `cell_fills` en los helpers genéricos

`print_grid_row` y `_grid_draw_cell` son **compartidos** con
`InventoryStoragePDF`, así que el color entra por parámetros opcionales cuyo
default reproduce el comportamiento previo:

```python
def _grid_draw_cell(pdf, x, y_top, w, h, lines, font_size,
                    bold=False, fill=False, fill_color=None)
def print_grid_row(pdf, cols, item, y_init, font_size=8,
                   margin=_GRID_MARGIN, cell_fills=None)
```

- `fill=True` sigue significando celeste (labels/encabezados); `fill_color` es un
  RGB explícito y **tiene precedencia**.
- `cell_fills` es una lista alineada a `cols`, con `None` en las celdas sin
  relleno. Se rellena con `None` hasta el largo de `cols`, así que una lista
  corta (o `None`) no rompe nada.
- `InventoryStoragePDF` no pasa nada → sale idéntico a antes.

`_sm_item_fills(item)` lee la cantidad y lo suministrado **por posición**
(`item[2]`, `item[4]`), igual que el resto de la cuadrícula de SM, que alinea
encabezados y celdas por índice contra `_SM_ITEM_COLS`.

Los valores se coercionan con `_sm_num` antes de comparar: vienen del JSON de la
SM y un string colado haría reventar la comparación (`"8" >= 20` →
`TypeError`) tumbando la generación del PDF completo. Valor no numérico → sin
color, nunca excepción.

## Fix: "(Semidespachado)" en la columna Estatus

`add_dispatch_sm` marca el comment del item con `" ;(Despachado) "` o
`" ;(Semidespachado) "` según el despacho sea total o parcial, pero el parser de
`dowload_file_sm` solo buscaba `"(despachado)"`, `"(pedido)"` y `"(nuevo)"` — y
**`"(despachado)"` no es substring de `"(semidespachado)"`** (la `i` de "semi" se
interpone). Un item con 8 de 20 surtidos caía hasta el `else` e imprimía
`"pendiente"`, contradiciendo su propia celda `C. Suministrado`.

Se agregó la rama `"(semidespachado)"` → `"Semidespachado"`, **después** de la de
`"(despachado)"`: el comment **acumula** marcadores a lo largo del historial de
despachos, así que un item que fue parcial y luego se completó lleva los dos y
debe ganar el completo. Esto sí cambia el texto de la columna `Estatus` también
en el Excel — corrigiendo un valor que hoy es incorrecto.

## Al modificar

- **Cambiar umbrales o colores**: todo vive en `_sm_item_fills` y las tres
  constantes `_SM_VERDE`/`_SM_AMARILLO`/`_SM_ROJO`. No hay lógica de color en el
  midleware.
- **Si se agregan o reordenan columnas de items** (`_SM_ITEM_COLS`): revisar los
  índices `item[2]`/`item[4]` de `_sm_item_fills` y que el verde siga generando
  `len(_SM_ITEM_COLS)` entradas.
- **Colorear otra tabla** (entregas, o el PDF de inventario): pasarle
  `cell_fills` a `print_grid_row`; el helper genérico ya lo soporta.
- **Si alguna vez se quiere el semáforo en el Excel**, hay que abandonar el
  `df.to_excel` de `dowload_file_sm` y usar `openpyxl` con `PatternFill`; hoy es
  deliberadamente solo PDF.
