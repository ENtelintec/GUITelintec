# Análisis de costos por partida (`PUT /quotation/costAnalysis`, `GET /quotation/<id>?with_costs=1`)

Fecha: 2026-09-28 · **Estado: hecho y verificado contra dev (37/37 checks HTTP, `Tests/tester_quotation_costs.py`). DDL: tablas `quotation_item_costs` y `quotation_item_supplier_quotes` de [`control_entregas_ocd.sql`](../scripts_db_handle/control_entregas_ocd.sql) (corrido en dev con FKs; test/prod pendientes).**

Fase **F6** del plan [`planes/control_entregas_ocd_plan.md`](planes/control_entregas_ocd_plan.md). Origen: las hojas "ANÁLISIS DE COSTOS" de FO-PRE-01 R2 (Cotización) y FO-PRE-02 R2 (COT CISCO), el paso previo con el que Preventa arma el precio: costo unitario sin ganancia (USD/MXN), tipo de cambio, `% ganancia`, precio con ganancia, tiempo de entrega al cliente y la comparativa "Proveedor 1 / 2" (precio, moneda, tiempo de entrega, comentarios). Decisión del grill: **tablas propias** (no JSON en `quotation_items.extra_info`) por volumen; primera etapa = **captura manual**; etapa 2 (pendiente) = sugerir desde análisis anteriores por `n_part`.

## Modelo

- **`quotation_item_costs`** — una fila por partida (`quotation_item_id` UNIQUE → `quotation_items.id`, el `qa_item_id` que devuelve `GET /quotation`), `quotation_id` desnormalizado, `currency`, `unit_cost`, `exchange_rate` (snapshot), `unit_cost_mxn`, `profit_pct`, `unit_price_profit`, `delivery_time`, `service_months`, `smart_account` (CISCO), `history`, `extra_info`.
- **`quotation_item_supplier_quotes`** — N por partida: `position` (1 = Proveedor 1…), `supplier_id` (catálogo `suppliers_amc`, opcional) o `supplier_name` libre, `unit_price`, `currency`, `delivery_time`, `comments`, `is_selected` (a lo más uno).
- FK `ON DELETE CASCADE` desde `quotation_items`: borrar la cotización o una partida borra su análisis.

## Reglas

| Tema | Regla |
|---|---|
| Cálculo (back) | `unit_cost_mxn = unit_cost × exchange_rate` (`= unit_cost` si MXN, y el snapshot queda `null`) · `unit_price_profit = unit_cost_mxn × (1 + profit_pct / 100)`. **`profit_pct` en porcentaje** (30 = 30 %). 4 decimales en costos; 2 al aplicar a `price_unit`. |
| Tipo de cambio | El del item manda; si no viene, el `exchange_rate` de la cabecera del PUT; si tampoco, `quotations.metadata.exchange_rate` (que el PUT guarda cuando se manda). Costo en USD sin ninguno → 400. |
| Upsert | Una fila por partida: el PUT crea o actualiza **la misma fila** (`history` acumula con `changes`). `suppliers` presente = **reemplaza** la comparativa completa del item; ausente = no se toca. `cost: null` = borra análisis y comparativa del item. Items no mencionados no se tocan. |
| Validación | Todo antes de escribir (400 con lista): partida inexistente/ajena, repetida, `currency` fuera de MXN/USD, `unit_cost` faltante o < 0, `profit_pct` < 0, `supplier_id` inexistente en catálogo, proveedor sin id ni nombre, `position` repetida, más de un `is_selected`. |
| `apply_prices` | `true` → escribe `unit_price_profit` (2 dp) en `quotation_items.price_unit` **solo de los items enviados**. Flujo: cotización en borrador con `price_unit 0` → análisis → `apply_prices` → cotización lista. |
| Lectura | `GET /quotation/<id>?with_costs=1` agrega `cost_analysis` (con `suppliers[]`) a cada producto, `cost_totals` y `exchange_rate` de cabecera. Sin el query no viaja nada: el PDF al cliente y el listado normal no ven costos. |
| Permisos | `administracion` (como el resto de `/quotation`). |

## Capas tocadas

```
controller  contracts/quotation_costs_controller.py   (nuevo) SELECT/INSERT/UPDATE/DELETE de las dos tablas, update_quotation_item_price, get_supplier_names
midleware   MD_QuotationCosts.py                       (nuevo) update_quotation_cost_analysis_from_api (validar → escribir → totales), get_quotation_costs_map, costs_totals
midleware   Functions_midleware_admin.py               get_quotations(with_costs=) → _attach_costs
models      api_quotation_costs_models.py              (nuevo) QuotationCostAnalysisForm (cabecera) + api.model anidado; items[] se valida en el midleware (cost puede ser null)
routes      rs_Admin_presales.py                       PUT /quotation/costAnalysis · GET /quotation/<id> lee ?with_costs
```

`get_quotation_order_items` (partidas) se reusa del controller de control de entregas. `execute_sql` no da transacciones: la escritura es item por item y un fallo a mitad se reporta en `error` junto con lo que sí se aplicó.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permiso `administracion`.
- **Respuesta**: siempre `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400 de midleware, objeto por campo en 400 de form (`id_quotation`).

### `PUT /quotation/costAnalysis`

```json
{ "id_quotation": 51, "exchange_rate": 18.25, "apply_prices": false,
  "items": [
    { "id": 900,
      "cost": { "currency": "USD", "unit_cost": 0.55, "profit_pct": 30, "delivery_time": "2 semanas" },
      "suppliers": [
        { "position": 1, "supplier_id": 12, "unit_price": 0.55, "currency": "USD", "delivery_time": "10 días", "is_selected": true },
        { "position": 2, "supplier_name": "Distribuidor X", "unit_price": 0.60, "currency": "USD", "comments": "más caro" } ] },
    { "id": 901, "cost": { "unit_cost": 80, "profit_pct": 25, "service_months": 12, "smart_account": true } },
    { "id": 902, "cost": null }
  ] }
```

| Campo | Notas |
|---|---|
| `items[].id` | `quotation_items.id` (= `qa_item_id` de `GET /quotation`) |
| `items[].cost` | objeto, o `null` para borrar. `unit_cost` obligatorio; `currency` default MXN; `exchange_rate` opcional (cae a cabecera/metadata); `profit_pct` default 0; `delivery_time`, `service_months`, `smart_account` opcionales |
| `items[].suppliers` | lista completa (reemplaza); ausente = no tocar. `position` default = orden en la lista |
| `exchange_rate` | cabecera; se guarda en `metadata.exchange_rate` |
| `apply_prices` | default `false` |

| Código | Cuándo | `data` |
|---|---|---|
| **200** | aplicado | `{"id_quotation": 51, "exchange_rate": 18.25, "items": [{"id": 900, "id_cost": 7, "partida": 1, "currency": "USD", "unit_cost": 0.55, "exchange_rate": 18.25, "unit_cost_mxn": 10.0375, "profit_pct": 30.0, "unit_price_profit": 13.0488, "applied_price_unit": null, "suppliers_count": 2}, {"id": 902, "deleted": true}], "totals": {"items_count": 3, "items_analyzed": 2, "total_cost_mxn": 10837.5, "total_with_profit_mxn": 14048.8, "profit_mxn": 3211.3}}` · `error` lista solo si alguna escritura falló después de validar |
| **400** | validación | `error: ["items[0] (id 900): costo en USD requiere exchange_rate (del item o de la cabecera)", "supplier_id 999 no existe en el catálogo", …]` |
| **404** | cotización inexistente | `null` |

### `GET /quotation/<id>?with_costs=1`

Cada `products[]` gana `cost_analysis` (`null` si la partida no tiene análisis):

```json
"cost_analysis": {"id_cost": 7, "quotation_item_id": 900, "currency": "USD", "unit_cost": 0.55, "exchange_rate": 18.25, "unit_cost_mxn": 10.0375,
                  "profit_pct": 30.0, "unit_price_profit": 13.0488, "delivery_time": "2 semanas", "service_months": null, "smart_account": null,
                  "history": [...], "suppliers": [{"id_quote": 3, "position": 1, "supplier_id": 12, "supplier_name": "ABSA", "unit_price": 0.55, "currency": "USD", "delivery_time": "10 días", "comments": null, "is_selected": true}]}
```

y la cotización gana `cost_totals` (mismo objeto que `totals` del PUT) y `exchange_rate`. También funciona en el listado (`/quotation/-1?with_costs=1`), con dos queries por cotización.

### Gotchas

- `price_unit` de la cotización **no** cambia hasta mandar `apply_prices: true`; el front puede mostrar `unit_price_profit` como sugerido mientras tanto.
- `supplier_name` en la respuesta es el snapshot: si vino `supplier_id`, se copia el nombre del catálogo al guardar.
- El MXN no guarda `exchange_rate` aunque la cabecera lo traiga.

## Al modificar

- **Etapa 2 (sugerencias)**: `GET /quotation/costAnalysis/suggest?n_part=…` leyendo `quotation_item_costs` JOIN `quotation_items` por `n_part` (índice `idx_qi_n_part` ya existe) ordenado por `timestamp DESC`; devolver los últimos N análisis con su comparativa. No tocar el PUT.
- **Otra fórmula de ganancia** (factor en vez de porcentaje): solo `_compute` en el midleware; el contrato del front sigue en porcentaje.
- **Indicador FO-PRE-03 (ventas/costo/ganancia por mes)**: `costs_totals` ya calcula por cotización; agregarlo por `quotations.creation` es una query sobre `quotation_item_costs` JOIN `quotations`.
