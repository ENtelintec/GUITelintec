# Remisión: el detalle devolvía N-1 partidas (`JSON_REMOVE '$[0]'`)

Reportado desde el front: `GET /admin/collections/remission-<id>` **perdía una
partida**. Una remisión con 2 items devolvía 1; con 1 item devolvía 0 y en
pantalla se veía "sin partidas". El `PUT` respondía `200` y la BD quedaba
correcta — lo que fallaba era la lectura.

## Causa raíz

[`templates/controllers/presales/remisions_controller.py`](../templates/controllers/presales/remisions_controller.py),
`get_remission_by_id`. El array de items se armaba así:

```sql
JSON_REMOVE(
  COALESCE(
    JSON_ARRAYAGG(
      CASE WHEN qai.qa_item_id IS NOT NULL THEN JSON_OBJECT(...) ELSE NULL END
    ),
    JSON_ARRAY()
  ),
  '$[0]'
) AS items
```

El `'$[0]'` estaba para limpiar la **fila fantasma del `LEFT JOIN`**: una
remisión sin items produce una fila con `qai` en `NULL`, el `CASE` la convierte
en `null` y `JSON_ARRAYAGG` **sí incluye ese `null`** (a diferencia de casi todos
los agregados de MySQL), así que el array quedaba `[null]`. Quitar el índice 0 lo
dejaba en `[]`.

El problema: **el recorte se aplicaba siempre**, no solo cuando había fila
fantasma. Verificado contra el MySQL de dev:

| items reales | `JSON_ARRAYAGG` | tras `JSON_REMOVE '$[0]'` | con el fix |
| --- | --- | --- | --- |
| 0 | `[null]` | `[]` ✅ | `[]` ✅ |
| 1 | `[o1]` | `[]` ❌ | `[o1]` ✅ |
| 2 | `[o1, o2]` | `[o2]` ❌ | `[o1, o2]` ✅ |
| N | `[o1 … oN]` | `[o2 … oN]` ❌ N-1 | `[o1 … oN]` ✅ |

El mismo efecto ya estaba documentado para `get_contracts_with_items`, que usa
`JSON_ARRAYAGG` sin `JSON_REMOVE` y devuelve `[{"qa_item_id": null, ...}]` en
contratos sin partidas.

**Segundo síntoma, mismo origen:** ese GET alimenta `old_items_map` en
`update_remission_from_api`
([`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py)).
Como el mapa no contenía la primera partida, editarla (`qa_item_id > 0`, rama de
update) reventaba con `KeyError` → `500`. No se había visto porque el caso
reportado eran partidas nuevas, que caen en el `insert`.

## El arreglo: decidir por conteo, no recortar por posición

```sql
IF(
  COUNT(qai.qa_item_id) = 0,
  JSON_ARRAY(),
  JSON_ARRAYAGG(JSON_OBJECT( ... 'partida', qi.partida ))
) AS items,
```

Para un `ar.id` dado el `LEFT JOIN` produce **o** una sola fila con `qai` en
`NULL` **o** K filas todas con `qai` no nulo — no hay caso mixto, así que el
`COUNT` distingue los dos escenarios sin tocar datos reales. El `CASE … ELSE
NULL` deja de ser necesario: ya no puede colarse un `null` al array. Los `JOIN`,
el `GROUP BY` y **el orden de las columnas no cambian** (los 8 call sites de
`get_remission_by_id` indexan por posición; `items` sigue en el índice 16).

Dos arreglos de paso en el mismo camino:

- `get_remission_by_id` **no pasaba `data_token`** en la rama por id
  (`execute_sql(sql, val, 1)`), así que un usuario con permiso `tester` leía de
  la BD de dev en vez de la de test. Corregido.
- `update_remission_from_api`: `dict_items[item["qa_item_id"]]` → `.get(...) or
  {}`. Con el SQL corregido el mapa ya trae todas las partidas, pero un
  `qa_item_id` ajeno o de un estado viejo del front seguiría tumbando el request
  con `500`; ahora se trata como item sin historial previo.

## Verificación

Contra el MySQL de dev (`docs`-only, sin escrituras):

- Barrido de las remisiones existentes: el largo de `items` coincide con
  `COUNT(qai.qa_item_id)` en **todas**, sin `null` en el array. Incluye el caso
  de 1 partida (antes devolvía 0) y el de 0 partidas (sigue `[]`).
- Caso N≥2 (no existe en dev) reproducido con una tabla derivada: la tabla de
  arriba salió tal cual del servidor.

## Contrato mínimo para el front

**No requiere cambios en el front.** Mismo endpoint, mismo shape; solo deja de
faltar una partida.

- **Auth**: header `Authorization` con el **JWT crudo**, NO `Bearer <token>`.
  Departamentos: `administracion` o `purchases`.
- **Base**: `GET /GUI/api/v1/admin/collections/remission-<id_report>` — el id va
  como string en la ruta y se castea; un id `<= 0` o no numérico **no es 404**:
  cae a `None` y devuelve **todas** las remisiones.
- **Respuesta 200** — envelope `{data, msg, error}`. `data` es **siempre una
  lista**, también al pedir un id concreto (`data[0]`); `msg` y `error` van en
  `null` en el camino feliz:

```json
{
  "data": [
    {
      "id": 6,
      "folio": "R-0001",
      "items": [
        {
          "qa_item_id": 41,
          "quotation_id": 12,
          "report_id": 6,
          "item_c_id": 88,
          "description": "Suministro de cable",
          "udm": "m",
          "quantity": 100.0,
          "unit_price": 25.5,
          "unit_price_quotation": 24.0,
          "line_total": 2550.0,
          "partida": "1.1",
          "history": [],
          "extra_info": {}
        }
      ]
    }
  ],
  "msg": null,
  "error": null
}
```

(el objeto de remisión trae además `date`, `client_*`, `plant`, `area`,
`location`, `general_description`, `comments`, `quotation_id`, `status`,
`history`, `files`, `contract_id` y los campos aplanados de `extra_info`.)

- **400** — `{"data": null, "msg": "Error al obtener remisiones", "error": "..."}`
  o `{"data": [], "msg": "No se encontraron remisiones válidas", "error": null}`.
- **401** — `{"error": "No autorizado. Token invalido"}`.
- Remisión **sin partidas** → `"items": []` (nunca `[null]`, nunca un objeto con
  `qa_item_id: null`).
- El **orden** de `items` es el del `LEFT JOIN`, no está garantizado: ordenar en
  el front por `partida`.
- En el `PUT`, partida nueva = `qa_item_id` `null`/`0`/ausente; borrar =
  `is_erased == 1` (igualdad exacta). Ver
  [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md).

## Al modificar

- `'$[0]'` **ya no aparece en ninguna consulta del repo**. Si vuelve a hacer
  falta limpiar la fila fantasma de un `LEFT JOIN`, usar el patrón
  `IF(COUNT(fk) = 0, JSON_ARRAY(), JSON_ARRAYAGG(...))`, no recortar por índice.
- ~~**Pendiente / mismo patrón sin arreglar**: `get_quotation_activity_by_id`
  usa `JSON_ARRAYAGG` **sin** protección~~ — hecho (2026-08-15): mismo
  `IF(COUNT(...))` aplicado, y de paso se destaparon/corrigieron más bugs de la
  misma función (el PUT de la QA era append-only, ChangeStatus 500 siempre, FK
  de `item_c_id`, rollback del POST). Ver
  [`quotation_activity_upsert_null_fix.md`](quotation_activity_upsert_null_fix.md).
- Riesgo latente **del lado del front** (anotado por ellos, sin cambio en
  backend): el agrupador fusiona dos líneas de remisión que compartan número de
  `partida`, y `partida` viene de `quotation_items.partida`, que se repite entre
  grupos de un mismo contrato. Se atiende agrupando por `qa_item_id`.
