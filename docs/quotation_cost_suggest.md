# Sugerencias para el análisis de costos: `GET /quotation/costAnalysis/suggest`

Fecha: 2026-10-12 · **Estado: hecho y verificado contra dev (22/22 checks, `Tests/tester_quotation_cost_suggest.py`; regresión F6 37/37).** Sin DDL (el índice `idx_qi_n_part` ya existía). Pendiente `P-121`.

Etapa 2 del análisis de costos ([`quotation_cost_analysis.md`](quotation_cost_analysis.md)): al capturar el costo de una partida, Preventa quiere ver qué se analizó y qué se cotizó antes para el mismo producto. Diseño cerrado en el grill del 2026-10-12 ([`planes/plan_accion_2026_10.md`](planes/plan_accion_2026_10.md)).

## Qué devuelve

Dos fuentes, cada una con las filas más recientes primero y el mismo tope (`limit`):

| Fuente | Qué es | De dónde |
|---|---|---|
| `analyses` | Análisis de costos previos de partidas que coinciden, **con su comparativa de proveedores**, el item y la cabecera de su cotización | `quotation_item_costs` ⋈ `quotation_items` ⋈ `quotations`, orden `timestamp DESC` |
| `quoted` | Partidas cotizadas antes que coinciden (tengan o no análisis), con el `price_unit` que vio el cliente y la cabecera de su cotización; `has_analysis`/`id_cost` cruzan con la otra lista | `quotation_items` ⋈ `quotations`, orden `creation DESC` |

**Match.** `n_part` **exacto** (sensible a mayúsculas: la columna es `utf8mb4_bin`) **o** `description` por texto (`LIKE` sobre `description` y `description_small`, sin distinguir mayúsculas; mínimo 3 caracteres). Si vienen los dos, basta que uno coincida. Hoy 3 de cada 4 items cotizados no traen `n_part`; por eso la descripción.

**n_part genérico.** `GENERICO`, `GENÉRICO`, `S/N`, `SN`, `N/A`, `NA`, `-`, `.`, `NINGUNO` o menos de 3 caracteres (lista fija `GENERIC_N_PARTS` en el midleware): no se busca por `n_part`, `generic: true`, y si no hay `description` las dos listas vienen vacías con **200** (no es error del front).

**`quoted` sale de todas las cotizaciones**: no hay columna `status` en BD (vive en `metadata`, valores libres). Cada fila trae `quotation.status` y `quotation.document_type` para que el front filtre; `exclude_quotation_id` evita que la cotización que se está analizando se sugiera a sí misma.

## Capas tocadas

```
HTTP        rs_Admin_presales.py                         GET /quotation/costAnalysis/suggest (permiso administracion; solo query string)
midleware   MD_QuotationCosts.py                         suggest_cost_analysis_api, GENERIC_N_PARTS, SUGGEST_LIMIT_DEFAULT/MAX, _quotation_header, _quoted_cols_to_dict
controller  contracts/quotation_costs_controller.py      search_cost_analyses, search_quoted_items, get_supplier_quotes_by_items, QUOTED_ITEM_COLUMNS
```

Sin modelos/forms nuevos (no hay body) ni DDL. El `PUT /costAnalysis` y el `GET ?with_costs=1` no cambian.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permiso `administracion` (otros → 401). Respuesta JSON `{data, msg, error}`.
- `GET /quotation/costAnalysis/suggest?n_part=&description=&exclude_quotation_id=&limit=`
  - `n_part` y/o `description`: al menos uno. `description` ≥ 3 caracteres. `limit` default **5**, tope **20** (más se recorta, no falla). `exclude_quotation_id` entero opcional.
  - Llamarlo al abrir el análisis de una partida (o al teclear el n_part). Es solo lectura; se puede repetir.
- **200**:

  ```json
  { "data": {
      "n_part": "FAP6WBUDLCZ", "description": "", "generic": false, "limit": 5,
      "analyses": [
        { "id_cost": 7, "quotation_item_id": 900, "quotation_id": 51, "currency": "USD", "unit_cost": 0.5, "exchange_rate": 18.0,
          "unit_cost_mxn": 9.0, "profit_pct": 30.0, "unit_price_profit": 11.7, "delivery_time": "10 días", "service_months": null,
          "smart_account": null, "created_by": 9999, "timestamp": "2026-10-12 10:00:00", "history": [...], "extra_info": {},
          "suppliers": [ { "id_quote": 3, "position": 1, "supplier_id": 12, "supplier_name": "ABSA", "unit_price": 0.5, "currency": "USD",
                           "delivery_time": null, "comments": null, "is_selected": true } ],
          "item": { "id": 900, "partida": 1, "n_part": "FAP6WBUDLCZ", "description": "Fibra …", "description_small": "", "udm": "m", "quantity": 100.0, "price_unit": 12.5 },
          "quotation": { "id": 51, "code": "COT-2026-051", "company": "TERNIUM", "client_id": 40, "creation": "2026-10-12 09:58:00", "status": null, "document_type": "quotation" },
          "id_cost": 7 } ],
      "quoted": [
        { "item": { "id": 905, "partida": 1, "n_part": "FAP6WBUDLCZ", "description": "FIBRA …", "description_small": "", "udm": "m", "quantity": 50.0, "price_unit": 14.0 },
          "quotation": { "id": 52, "code": "COT-2026-052", "company": "TERNIUM", "client_id": 40, "creation": "2026-10-12 10:05:00", "status": null, "document_type": "quotation" },
          "has_analysis": false, "id_cost": null },
        { "item": { "id": 900, "...": "..." }, "quotation": { "id": 51, "...": "..." }, "has_analysis": true, "id_cost": 7 } ] },
    "msg": "1 análisis previos y 2 items cotizados", "error": null }
  ```

  Los campos de cada `analyses[]` son los mismos de `cost_analysis` del `GET /quotation/<id>?with_costs=1` más `item`, `quotation` e `id_cost`. Para pre-llenar, el front toma `analyses[0]` (el más reciente) y deja que el usuario confirme.
- **200 con n_part genérico y sin description**: `data.generic = true`, `analyses` y `quoted` vacíos, `msg` lo explica. Con `description` sí busca (por texto).
- **400**: sin `n_part` ni `description` · `description` corta · `limit` no entero o < 1 · `exclude_quotation_id` no entero. Ejemplo: `{ "data": null, "msg": "description debe tener al menos 3 caracteres", "error": null }`.
- Gotchas: `n_part` es exacto (`fap6…` no encuentra `FAP6…`); `quoted` incluye la partida analizada (con `has_analysis: true`), no se deduplica contra `analyses`; `creation`/`timestamp` vienen como texto `YYYY-MM-DD HH:MM:SS`.

## Al modificar

- Otra llave de match (marca, `id_inventory`): agregar la condición en `_suggest_match` del controller; las dos consultas la comparten.
- Más campos por fila: `QUOTED_ITEM_COLUMNS` es append-only y `_SELECT_QUOTED` va en el mismo orden; `search_cost_analyses` devuelve `COST_COLUMNS` + `QUOTED_ITEM_COLUMNS` y el midleware corta por `len(COST_COLUMNS)`.
- Si se agrega una columna `status` real a `quotations`, filtrar ahí y quitar la nota del contrato.
- Sugerencias por proveedor (`?supplier_id=`): etapa 3, otra consulta sobre `quotation_item_supplier_quotes`; no mezclar con estas dos listas.

## Verificación

Contra BD dev (2026-10-12), [`Tests/tester_quotation_cost_suggest.py`](../Tests/tester_quotation_cost_suggest.py) (gitignored), **22/22**. Dos cotizaciones temporales con un `n_part` único, una analizada con 2 proveedores; se borran al final. Cubre: validaciones (400 ×5, 401), match exacto con análisis + comparativa + item + cabecera, orden por fecha y `has_analysis`, `exclude_quotation_id`, `limit` 1 y recorte a 20, descripción en mayúsculas, n_part en minúsculas (no coincide), genéricos (`GENERICO`, `S/N`, 2 caracteres) con y sin descripción. Regresión `tester_quotation_costs.py` 37/37. `pyrefly`: 0 errores en los 3 archivos.

## Pendientes

- **[front]** `P-122` Pantalla de análisis de costos: llamar al abrir la partida, mostrar `analyses` (pre-llenar con el más reciente) y `quoted`, filtrar por `quotation.status`/`document_type` si hace falta.
- **[back]** Sugerencias por proveedor (etapa 3), solo si Preventa lo pide.
