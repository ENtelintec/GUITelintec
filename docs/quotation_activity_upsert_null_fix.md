# Actividad de cotización: fix del `[null]` sin items + upsert real de items + ChangeStatus

Cierra el pendiente de [`remission_items_json_remove_fix.md`](remission_items_json_remove_fix.md):
`get_quotation_activity_by_id` tenía el mismo `JSON_ARRAYAGG` sin proteger que
ya se había corregido en remisiones — una cotización de actividad (QA) **sin
items** devolvía `items = [null]` y tronaba con 500 río arriba. Al ejercitar el
fix contra la BD dev aparecieron más bugs encadenados en la misma función y se
corrigieron todos: **el `PUT` de la QA nunca actualizaba items** (era
append-only por leer llaves que el form no produce), **`PUT
/activity/ChangeStatus` fallaba siempre** (`KeyError`), el default `0` del form
violaba la FK de `item_c_id`, y el rollback del `POST` tronaba por un argumento
faltante.

## Endpoints afectados

Base: `/GUI/api/v1/admin/collections`. Departamentos: `["administracion", "purchases"]`.

| Endpoint | Antes | Ahora |
| --- | --- | --- |
| `GET /activity/quotations-<id>` | QA sin items → 500 (`AttributeError` sobre `[null]`) | `items: []` |
| `PUT /activity/quotation` | items **siempre** se creaban (nunca update/delete); QA sin items → 400; id inexistente → 500 | upsert real por `qa_item_id`; QA sin items acepta re-agregar; 404 |
| `DELETE /activity/quotation` | QA sin items → imposible de borrar (500/400); id inexistente → 500 | borra directo; 404 |
| `PUT /activity/ChangeStatus` | **500 siempre** (`KeyError 'items'`) | cambia solo `status` + `history` |
| `POST /activity/quotation` | item sin contrato → FK error; rollback → `TypeError` | `0/ausente → NULL`; rollback funciona |

## Causa raíz, bug por bug

1. **`[null]`**: `JSON_ARRAYAGG` con `LEFT JOIN` sin filas **sí** agrega el
   `NULL` (a diferencia de casi todos los agregados) → `items = [null]` →
   `json.loads` da `[None]` → `None["qa_item_id"]` / `None.get(...)` → 500 en
   el GET, el PUT y el DELETE. Fix: `IF(COUNT(qai.qa_item_id) = 0,
   JSON_ARRAY(), JSON_ARRAYAGG(...))` — decide por conteo, mismo patrón que
   `get_remission_by_id` ([`remisions_controller.py`](../templates/controllers/presales/remisions_controller.py)).
2. **PUT append-only**: el midleware leía `new_item.get("id", 0)` y
   `new_item.get("client_id")`, pero `QuotationUpsertItemForm` (la data
   validada que llega) produce **`qa_item_id`** y **`item_contract_id`** — `id`
   nunca existe → `item_id` siempre 0 → todo item caía en "crear". Guardar una
   QA duplicaba sus items y `is_erased` no borraba. Con esto, además, la
   protección del `unit_price` real documentada en
   [`quotation_remission_unit_price_split.md`](quotation_remission_unit_price_split.md)
   vivía en código inalcanzable; ahora sí corre.
3. **`is_erased` por truthiness**: antes `!= 0`, y un `null` de JSON queda como
   `None` en WTForms (`None != 0` → `True` → borraba). Mismo bug que se corrigió
   en items de contrato ([`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md)).
4. **Guard de pertenencia**: un `qa_item_id` ajeno a la QA ahora es error
   por-item (`"El ítem N no pertenece a la cotización M"`), nunca actualiza ni
   borra filas de otra cotización.
5. **QA sin items**: los guards `len(items) <= 0 → 400` del PUT y el DELETE se
   quitaron. Una QA queda sin items por camino legítimo (`is_erased` sobre
   todos); ahora se le pueden re-agregar items y se puede borrar.
6. **`ChangeStatus`**: reusaba `update_quotation_activity_from_api`, que exige
   el payload completo del PUT → `KeyError 'items'` 500 con su form de solo
   `id`+`status`. Midleware nuevo `update_quotation_activity_status_from_api` +
   controller `update_quotation_activity_status` (UPDATE de solo
   `status`+`history`, sin reenviar la fila — no pisa columnas).
7. **FK de `item_c_id`**: `quotation_activity_items.item_c_id` tiene FK real a
   `quotation_items(id)` (`ON DELETE SET NULL`); el default `0` del form
   reventaba el INSERT. Ahora `0/ausente → NULL` en create y update (también
   `report_id`, sin FK pero `0` no enlaza nada). En el update, un `0` del
   payload **conserva** el enlace de la BD (el PUT de cotización no es el
   camino para desenlazar remisión/partida).
8. **Rollback del POST**: si todos los items fallaban, llamaba
   `delete_quotation_activity(id)` sin `data_token` → `TypeError` 500 y la QA
   quedaba huérfana (así se encontró: una huérfana real en dev).
9. **Not-found**: id inexistente daba `IndexError` 500 (la rama por id usa
   `fetchone` → `[]`); ahora 404 con envelope en PUT/DELETE/ChangeStatus.

## Capas tocadas

1. **DB** — [`remisions_controller.py`](../templates/controllers/presales/remisions_controller.py):
   `get_quotation_activity_by_id` (IF/COUNT), `update_quotation_activity_status`
   (nuevo), `update_quotation_activity_item` (`report_id: int | None`).
2. **Orquestación** — [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py):
   `update_quotation_activity_from_api` (llaves reales, pertenencia, QA vacía,
   404, FK→NULL), `delete_quotation_activity_from_api` (QA vacía, 404),
   `create_quotation_activity_from_api` (FK→NULL, rollback),
   `update_quotation_activity_status_from_api` (nuevo).
3. **HTTP** — [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py):
   `PUT /activity/ChangeStatus` apunta al midleware nuevo.
4. **Modelos** — sin cambios: `QuotationUpsertItemForm` ya declaraba el
   contrato correcto; el midleware era el desalineado.

## Contrato mínimo para el front

**Auth (¡ojo!):** header `Authorization` con el **token JWT crudo** — **NO**
`Bearer <token>`. Respuestas con envelope `{data, msg, error}`.

### `PUT /activity/quotation` — upsert de items

Cada item del arreglo `items` decide su acción con **`qa_item_id`** (la llave
`id` NO existe en el form y se ignora — si el front la manda hoy, debe migrar):

```jsonc
{
  "id": 6,                       // id de la QA (este sí se llama id)
  "date_activity": "2026-08-15 10:00:00",
  "folio": "COT-...", "client_id": 1, "client_company_name": "...",
  "client_contact_name": "...", "client_phone": "...", "client_email": "...",
  "plant": "...", "area": "...", "location": "...",
  "general_description": "...", "comments": "...", "status": 0,
  "items": [
    // qa_item_id ausente / -1 / 0  -> CREAR
    {"description": "nuevo", "udm": "PZA", "quantity": 1, "unit_price": 5.0},
    // qa_item_id > 0               -> ACTUALIZAR (debe pertenecer a esta QA)
    {"qa_item_id": 12, "description": "editado", "udm": "PZA", "quantity": 3, "unit_price": 12.5},
    // is_erased: true              -> BORRAR (por truthiness; null/false NO borran)
    {"qa_item_id": 13, "is_erased": true, "description": "x", "udm": "PZA", "quantity": 0, "unit_price": 0}
  ]
}
```

- `item_contract_id` (opcional): id de `quotation_items` para enlazar la
  partida de contrato. `0`/ausente → crea sin enlace (`NULL`); en update
  **conserva** el enlace existente.
- `items: []` es válido (p. ej. editar solo metadata de una QA vacía).
- Un `qa_item_id` de otra cotización → error por-item en `error` (lista); si
  todos los items fallan → `400`.
- `200` → `{"data": {"id_quotation": 6}, "msg": "Actividad de cotización actualizada correctamente (ID 6)", "error": null}`.
- Id de QA inexistente → `404`. **El PUT no devuelve los `qa_item_id` creados**
  (re-`GET`, mismo pendiente que items de contrato).

### `PUT /activity/ChangeStatus`

Body `{"id": 6, "status": 2}` → `200` con
`{"data": {"id_quotation": 6}, "msg": "Estatus...", "error": null}`; solo toca
`status` e `history` (los items/metadata no se reenvían ni se pisan). `404` si
no existe.

### `GET /activity/quotations-<id>` y `DELETE /activity/quotation`

- QA sin items: el GET trae `"items": []` (ya no truena); el DELETE la borra
  normal (`200`).
- `DELETE` con id inexistente → `404` (antes 500).

## Al modificar

- La receta del upsert (crear/actualizar/borrar por `qa_item_id`, pertenencia,
  truthiness de `is_erased`) es la misma de items de contrato y de remisión —
  mantener las tres en paralelo si cambia el contrato.
- `items` sale en la posición **15** de `get_quotation_activity_by_id`; los 3
  call sites indexan por posición.
- Verificado ciclo completo contra BD dev (22 checks): crear → editar item
  (sin duplicar, `unit_price_quotation` actualizado) → id ajeno rechazado →
  vaciar → `[]` en GET → re-agregar → ChangeStatus → vaciar → borrar QA vacía →
  404s → listado completo.

## Pendiente

- **[front]** Mandar `qa_item_id` (no `id`) e `item_contract_id` (no
  `client_id`) en los items del `PUT` — con `id` los items se duplican en cada
  guardado (comportamiento viejo).
- El `PUT` no devuelve los `qa_item_id` creados (el front debe re-`GET`).
