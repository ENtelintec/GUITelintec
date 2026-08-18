# Historial resumido de cambios de la remisión

## Contexto

El campo `activity_reports.history` (JSON) registraba acciones genéricas, pero con dos problemas:

1. **Bug del key timestamp**: las entradas se construían con `timestamp: timestamp` (la *variable*
   como clave), produciendo `{"2026-04-14 16:45:43": "2026-04-14 16:45:43", ...}` en vez de
   `{"timestamp": "2026-04-14 16:45:43", ...}`. El resto del repo usa la convención
   `"timestamp": timestamp`.
2. No registraba **qué** cambió: ni los items modificados ni los campos de metadata, así que el front
   no podía mostrar un "antes y después".

## Cambio

### 1. Corrección del bug
Las 13 entradas en [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py)
pasan de `timestamp: timestamp,` a `"timestamp": timestamp,`. (Solo afecta entradas nuevas; las ya
guardadas con la clave-fecha quedan como están, no se reescriben retroactivamente.)

### 2. Diff resumido en `history`
Se mantiene el **mismo campo** `history` (sin tabla nueva ni columna nueva). Cada entrada de
actualización ahora incluye un objeto `changes`:

```json
{
  "timestamp": "2026-04-14 16:45:43",
  "user": 16,
  "action": "Actualización",
  "comment": "Actualización de remision de actividad.",
  "changes": {
    "metadata": [
      {"field": "folio", "before": "REM-001", "after": "REM-002"}
    ],
    "items": [
      {"qa_item_id": 5, "description": "Cable", "action": "updated",
       "fields": [{"field": "unit_price", "before": 100.0, "after": 120.0}]},
      {"qa_item_id": null, "description": "Conector", "action": "added",
       "fields": [{"field": "unit_price", "before": null, "after": 50.0}]},
      {"qa_item_id": 7, "description": "Tornillo", "action": "removed", "fields": []}
    ]
  }
}
```

Reglas resueltas:

- **Almacenamiento**: enriquecer `history` (mismo campo JSON). Bajo volumen, el front ya lo lee.
- **Campos curados** (no diff genérico):
  - metadata: `date, folio, client_id, plant, area, location, general_description, comments, status,
    pedido, pedido_exiros, remision, remito, date_report, date_sign, date_delivery`.
  - items: `description, udm, quantity, unit_price, unit_price_quotation`.
  - Se ignoran computados (`line_total`) y ruido (`history`).
- **Etiquetas**: el backend manda solo `field`; el front mapea `field → etiqueta` legible.
- **Items**: se registran `updated` (con `fields` prev/actual), `added` (item nuevo) y `removed`
  (`is_erased == 1`). Un item sin cambios reales no se incluye.
- **Diff vacío**: siempre se agrega la entrada de "Actualización" (deja constancia del guardado),
  con `changes: {metadata: [], items: []}` si no hubo cambios.
- **Flujos cubiertos**: `update_remission_from_api` (metadata + items) y
  `update_remission_control_table_from_api` (solo metadata; la tabla de control no maneja items).
  La **creación** de remisión y los flujos de **cotización** quedan fuera (no tienen "previo" o no se
  pidieron).

## Capas tocadas

Solo orquestación —
[`templates/resources/midleware/MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py):

- Helpers nuevos: `_normalize_history_value` (numéricos→float, fechas→str), `_diff_history_fields`,
  `_remission_meta_from_row`, `_remission_meta_from_payload`, `_diff_remission_items`. Constantes
  `_HISTORY_META_FIELDS`, `_HISTORY_ITEM_FIELDS`, `_HISTORY_NUMERIC_FIELDS`.
- `update_remission_from_api`: calcula `changes` contra el estado previo (`result_ra`) **antes** del
  `update_activity_report`; reutiliza `old_items_map` en el loop de items (se eliminó un reparse).
- `update_remission_control_table_from_api`: calcula `changes.metadata` (forzando `area`/`status`
  conservados para que no marquen cambio espurio).

Sin cambios de DB/controllers ni de Forms/models.

## Al modificar

- El diff compara **el estado previo guardado vs. el estado que se va a escribir** (para metadata de
  `extra_info` se usa el dict ya computado por `create_extra_info_remision`). Si agregas un campo a
  vigilar, añádelo a `_HISTORY_META_FIELDS`/`_HISTORY_ITEM_FIELDS` y, si es numérico, a
  `_HISTORY_NUMERIC_FIELDS`.
- El diff debe calcularse **antes** de mutar la fila (usa `result_ra`). No lo muevas después de
  `update_activity_report`.
- `unit_price_quotation` (sugerido) se preserva en la remisión y no se envía por payload, por eso el
  diff de items lo compara contra sí mismo (nunca marca cambio en estos flujos). Ver
  [`quotation_remission_unit_price_split.md`](quotation_remission_unit_price_split.md).
- `created_at` lo pone MySQL (`DEFAULT CURRENT_TIMESTAMP`); el `timestamp` de cada entrada de
  `history` es el del momento de la acción en software-timezone.
