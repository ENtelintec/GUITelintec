# Control de saldos: GET con filtros / sin items + 4 campos nuevos en el PUT

Extiende [`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md) (donde ya
existe `PUT /remissionBalance` y el GET único aplanado) con lo que faltaba para la pantalla de control
de saldos, según la tabla consolidada
[`campos_consolidados_remisiones_control_saldos_ctrolreporte.md`](../scripts_db_handle/campos_consolidados_remisiones_control_saldos_ctrolreporte.md):

1. **4 campos nuevos** en `PUT /admin/collections/remissionBalance` — la tabla los marcaba "falta en el
   back" y se decidió (2026-08-15) que son **campos propios, no alias** de los ya implementados:
   `ot_ticket` (independiente de `ot` + `ticket_number`; esto **revierte** la resolución previa que lo
   dejaba como columna de display armada por el front), `centro_costos` (independiente de `ceco_fap`),
   `responsable_centro_costos` y `personal_infra` (independiente de `infra_responsible`). Los cuatro son
   string opcionales; solo el PUT de saldos los escribe (los otros módulos no los pisan), el GET los
   expone aplanados y el `history` los vigila.
2. **Query params nuevos en `GET /admin/collections/remission-<id>`** (mismo GET para los 3 módulos, no
   se creó ruta nueva): `include_items` para listados ligeros y filtros de servidor `date_from`/`date_to`
   (sobre la fecha de actividad), `month_period` y `general_status` (sobre llaves de `extra_info`).

## Capas tocadas

1. **HTTP** — [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py):
   `FetchActivitieReportById.get` parsea los 5 query params (con `@ns.doc`) y los pasa al midleware.
2. **Orquestación** — [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py):
   los 4 campos nuevos en `_BALANCE_EXTRA_KEY_MAP`, `_HISTORY_EXTRA_FIELDS` y `_GET_EXTRA_STRING_FIELDS`;
   `get_remission_from_api` gana `include_items` (con `False` **omite la llave `items`** del response y
   se ahorra el parseo/aplanado) y reenvía los filtros al controller.
3. **DB** — [`remisions_controller.py`](../templates/controllers/presales/remisions_controller.py):
   `get_remission_by_id` gana 4 params opcionales estilo **param-or-NULL** (mismo patrón que
   `get_purchase_management_list`): `AND (DATE(ar.date) >= %s OR %s IS NULL)` etc.; los de `extra_info`
   van con `JSON_UNQUOTE(JSON_EXTRACT(...))` (y `CAST ... AS SIGNED` para `general_status`, tolera que el
   valor haya quedado guardado como número o como string). **Sin filtros la query es byte-idéntica a la
   histórica**, así los otros call sites (PUT/DELETE/PDF/attachments) no cambian de comportamiento.
   Sin cambios de esquema.
4. **Validación/swagger** — [`api_purchases_models.py`](../static/Models/api_purchases_models.py): los 4
   campos en `MetadataRemissionBalanceForm` y su espejo `remission_balance_metadata_model`.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (NO `Bearer <token>`).
- **Base**: `/GUI/api/v1/admin/collections`. Permisos: `administracion` o `purchases`.
- **Envelope**: siempre `{data, msg, error}`; en el GET `data` es **lista** aun pidiendo un id.

### `GET /remission-<id>` — query params nuevos (todos opcionales)

`<id>` = id numérico para una remisión, `0` (o no numérico) para el listado completo.

| Param | Tipo | Semántica |
| --- | --- | --- |
| `include_items` | `1` (default) / `0` | Con `0`, `false` o `no` la llave `items` **no viene** en cada fila (listado ligero para la tabla de saldos). Cualquier otro valor (incluido vacío) = incluir. `history` y `files` siempre vienen. |
| `date_from` | `YYYY-MM-DD` | `DATE(date) >= date_from` (fecha de actividad, inclusivo) |
| `date_to` | `YYYY-MM-DD` | `DATE(date) <= date_to` (inclusivo) |
| `month_period` | string | Igualdad **exacta** contra `extra_info.month_period` (el valor que guardó el PUT de saldos; una remisión sin el campo nunca matchea) |
| `general_status` | int | Igualdad contra `extra_info.general_status` (el "Estatus" de saldos; catálogo de etiquetas en el front) |

```
GET /remission-0?include_items=0&month_period=2026-08&general_status=2
→ 200 {"data": [{"id": 42, "folio": "...", "hes_balance": 123.45, "month_period": "2026-08",
        "general_status": 2, "ot_ticket": "OT-3321/TK-8871", "centro_costos": "CC-4451",
        "responsable_centro_costos": "María Pérez", "personal_infra": "Juan García",
        ...todos los campos aplanados, sin "items"...}], "msg": null, "error": null}
```

Filtros que no matchean nada → `200` con `data: []`. Un `general_status` no numérico en el query se
ignora (como si no viniera).

### `PUT /remissionBalance` — campos nuevos en `metadata`

Mismo contrato de siempre (`metadata.id` obligatorio, merge por llaves presentes: lo no enviado no se
toca, `""`/`null` vacía a propósito). Se agregan 4 llaves opcionales string:

```json
{"metadata": {"id": 42, "ot_ticket": "OT-3321/TK-8871", "centro_costos": "CC-4451",
              "responsable_centro_costos": "María Pérez", "personal_infra": "Juan García"}}
→ 200 {"data": {"id_remission": 42}, "msg": "...", "error": null}
```

Gotchas: `ot_ticket` se guarda tal cual y es **independiente** de `ot`/`ticket_number` (si el front
quiere consistencia entre ambos, la arma él); ídem `centro_costos` vs `ceco_fap` y `personal_infra` vs
`infra_responsible` — el back no sincroniza duplicados conceptuales.

## Verificación

Ciclo completo contra la BD dev (29 checks): GET sin/con `include_items` (llave ausente/presente, campos
nuevos aplanados, `history`/`files` intactos), create de control table → `PUT /remissionBalance` con los
4 campos + marcadores → merge preserva columnas base y llaves de otros módulos, `history` registra los
campos nuevos en `changes.metadata`, filtros `month_period`/`general_status`/`date_from`/`date_to`
(match exacto, no-match, bordes inclusivos), listado sin filtros idéntico al histórico, y borrado de la
fila temporal. `pyrefly check` sin errores nuevos en los 4 archivos tocados.

## Al modificar

- Sigue vigente la receta de [`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md)
  (campo nuevo = form + api.model + `_*_EXTRA_KEY_MAP` + `_HISTORY_EXTRA_FIELDS` + `_GET_EXTRA_*_FIELDS`).
- **Filtro nuevo en el GET**: agregar el param en `rs` (parseo + `@ns.doc`), pasarlo por
  `get_remission_from_api` y sumar una cláusula param-or-NULL en `get_remission_by_id` — nunca una rama
  de SQL dinámico, para que los call sites sin filtros sigan corriendo la query histórica.
- `include_items` vive solo en el midleware (la query siempre trae los items agregados); si algún día el
  listado pesa por el `JSON_ARRAYAGG`, la optimización sería otra query sin el join, cuidando que el
  orden de columnas es load-bearing (los call sites indexan por posición, `items` en 16).
