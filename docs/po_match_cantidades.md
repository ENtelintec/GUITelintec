# Conciliación de OC por cantidades (match OC ↔ entradas, 2.ª iteración)

Fecha: 2026-10-27 · **Estado: hecho y verificado contra dev (41/41, `Tests/tester_po_match_cantidades.py`).** Sin DDL. Cierra `P-115`; el front queda en `P-183`. Decisiones del grill en [`plan_back_sin_bloqueo_2026_10_27.md`](planes/plan_back_sin_bloqueo_2026_10_27.md) (sección `P-115`). El endpoint y su primera iteración están en [`po_movements_inbound_match.md`](po_movements_inbound_match.md).

`GET /admin/collections/purchase/movements/match` casaba las entradas de almacén con la OC por folio, pero nunca sumaba cantidades. Ahora dice cuánto llegó de cada partida y da un estado de recepción por cantidades para cada OC. Sigue siendo de solo lectura: el estado "recibido" de la OC lo sigue poniendo administración a mano.

## Capas tocadas

```
rs    (sin cambios)                rs_Admin_collections.py, PurchaseMovementsMatch
mid   MD_Purchases.py              match_po_movements_and_sms: items[] y quantity_status por OC,
                                   counted/not_counted_reason por entrada, dueño de cada entrada
                                   contra los folios de todas las OCs, entradas acotadas por fecha;
                                   _movement_owner, _quantity_status, _allocate_received y
                                   _po_quantity_status nuevos.
                                   update_po_application_api: la partida nueva de una solicitud
                                   se guarda con order_id (arreglo, ver abajo)
DB    orders_controller.py         get_purchase_orders_with_items: date_from/date_to opcionales en
                                   el SQL; get_purchase_orders_folios nuevo
      movements_controller.py      get_ins_db_detail: date_from opcional (cota de las entradas)
modelos (sin cambios)
```

## Reglas

- **Solo suman las entradas que casaron exacto** (referencia = folio o folio de proveedor). Las `parcial` (el folio aparece dentro de la referencia) se siguen mostrando, pero no suman.
- **A qué OC pertenece una entrada (OC dueña).** Se decide contra los folios de **todas** las OCs no canceladas, no solo las de la respuesta, para que el resultado no dependa de los filtros:
  - Si casa con una sola OC, suma ahí.
  - Si casa con varias, suma en la que casó por su folio propio.
  - Si sigue empatada (dos OCs con el mismo folio, o solo por folio de proveedor), no suma en ninguna: `ambigua`.
  - El fallback `parcial` también usa esos folios: solo aplica a entradas que no casaron exacto con **ninguna** OC (antes era ninguna de la respuesta).
- **Partida ligada**: `extra_info.id_inventory > 0` (id de `products_amc`). A una partida solo le suman las entradas del mismo `id_product`. Una partida sin ligar (0, -1 o sin la llave) queda `sin_ligar` con `received: null`; no se adivina por número de parte ni por descripción.
- **Mismo producto en varias partidas**: lo recibido se reparte en orden de `id_item` hasta llenar cada una, y el sobrante queda en la última (`excedente`).
- **Estado por partida**: `pendiente` (nada) · `parcial` · `completa` · `excedente`. Las cantidades se comparan redondeadas a 4 decimales, porque las columnas son FLOAT.
- **Estado por OC** (`quantity_status`):
  - `sin_entradas`: ninguna entrada exacta es de esta OC.
  - `completa`: todas sus partidas están ligadas y completas.
  - `excedente`: todas están cubiertas y al menos una se pasa.
  - `parcial`: cualquier otro caso. Una partida sin ligar deja la OC en `parcial`, porque no se puede confirmar que llegó.
- **Entrada sin partida**: si una entrada es de esta OC pero su producto no está en ninguna partida ligada, no suma (`sin_partida`). Casi siempre indica una partida sin ligar.
- **`reception_status` no cambia** (`con_entradas` | `sin_entradas`): cuenta cualquier entrada que aparezca bajo la OC, incluidas las `parcial` y las que suman en otra OC. El front lo usa tal cual.
- **Consulta acotada**:
  - El filtro de fechas de las OCs pasó al SQL (`po.timestamp`; `date_to` incluye el día completo). Una OC sin timestamp se sigue incluyendo, como antes.
  - Las entradas se leen desde la fecha de la OC más vieja de la respuesta (con `folio`, desde la fecha de esa OC), y la consulta usa `idx_movements_warehouse_date`. Si alguna OC no tiene fecha, no hay cota.
  - **Una entrada registrada antes de que la OC existiera en el sistema ya no aparece.**

## Revisión de `insert_purchase_order_item_from_applications`

El grill pidió revisarla en solo lectura antes de programar.

- `purchase_order_items` guarda las partidas de OC (`purchase_id`) y las de solicitud de OC (`order_id`, FK a `pos_applications`). Esta función inserta con `order_id`: **está bien**. Al convertir la solicitud en OC, `update_po_item` pone `purchase_id` en la misma fila y conserva `order_id`. Por eso hay filas con las dos columnas (1 en prod, 3 en test).
- **El error estaba en `update_po_application_api`.** La partida nueva (id -1) que se agrega al editar una solicitud se guardaba con `insert_purchase_order_item`, es decir con `purchase_id = <id de la solicitud>`. La solicitud no la veía, porque lee por `order_id`, y quedaba colgada de la OC que tuviera ese mismo id. La conciliación la habría contado como partida de esa OC. Ahora usa `insert_purchase_order_item_from_applications` y manda `tool`, igual que el alta.
- **Datos (solo lectura, 2026-10-27)**: en las 3 BDs, todo `purchase_id` apunta a una OC que existe. En prod no hay ninguna partida mal colgada: su única partida de OC viene de una solicitud convertida. Dev (10) y test (2) tienen partidas solo con `purchase_id`. Con los datos no se puede distinguir una mal colgada de una legítima, y son datos de prueba, así que no se corrió DML.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permiso `administracion` o `purchases`.
- **Base**: `/GUI/api/v1/admin/collections`. Envelope `{data, msg, error}`.
- **Visibilidad**: sin cambios. Quien no es administrador ni gerente solo ve sus OCs.

### `GET /purchase/movements/match`

Usa los mismos query params (`status`, `date_from`, `date_to` en `YYYY-MM-DD`, `folio`). **Solo agrega campos**: no quita ninguno ni cambia sus valores.

Nuevos por OC (`data[]`):

| Campo | Tipo | Notas |
|---|---|---|
| `quantity_status` | string | `sin_entradas` \| `parcial` \| `completa` \| `excedente` |
| `items` | array | partidas de la OC en orden de `id_item`; `[]` si no tiene |

`items[]`:

| Campo | Tipo | Notas |
|---|---|---|
| `id_item` | int | id en `purchase_order_items` |
| `description` | string | |
| `quantity` | float | cantidad pedida |
| `id_inventory` | int | producto ligado; `0` o `-1` = sin ligar |
| `received` | float \| null | lo que le tocó del reparto; `null` si `sin_ligar` |
| `quantity_status` | string | `pendiente` \| `parcial` \| `completa` \| `excedente` \| `sin_ligar` |

Nuevos en `movements[]`:

| Campo | Tipo | Notas |
|---|---|---|
| `counted` | bool | `true` = sumó en una partida de **esta** OC |
| `not_counted_reason` | string \| null | `null` si cuenta. Si no: `parcial` (folio dentro de la referencia), `ambigua` (empate entre OCs), `otra_oc` (suma en otra OC) o `sin_partida` (es de esta OC, pero su producto no está en ninguna partida ligada) |

**200**: ejemplo ilustrativo, armado con los casos del tester. Se omiten los campos que ya existían y no cambiaron:

```json
{
  "data": [
    {
      "id": 123,
      "folio": "OC-0001",
      "folio_supplier": "FAC-77",
      "status": 0,
      "reception_status": "con_entradas",
      "quantity_status": "parcial",
      "items": [
        {"id_item": 501, "description": "ABRAZADERA CLIP 1/2", "quantity": 5.0, "id_inventory": 1, "received": 5.0, "quantity_status": "completa"},
        {"id_item": 502, "description": "ABRAZADERA CLIP 1/2", "quantity": 3.0, "id_inventory": 1, "received": 4.0, "quantity_status": "excedente"},
        {"id_item": 503, "description": "ABRAZADERA UNICANAL 1/2\"", "quantity": 2.0, "id_inventory": 2, "received": 1.0, "quantity_status": "parcial"},
        {"id_item": 504, "description": "FLETE", "quantity": 1.0, "id_inventory": 0, "received": null, "quantity_status": "sin_ligar"}
      ],
      "movements": [
        {"id_movement": 9001, "id_product": 1, "quantity": 4.0, "reference": "OC-0001", "matched_by": "folio", "match_type": "exacto", "counted": true, "not_counted_reason": null},
        {"id_movement": 9003, "id_product": 2, "quantity": 1.0, "reference": "FAC-77", "matched_by": "folio_supplier", "match_type": "exacto", "counted": true, "not_counted_reason": null},
        {"id_movement": 9004, "id_product": 3, "quantity": 7.0, "reference": "OC-0001", "matched_by": "folio", "match_type": "exacto", "counted": false, "not_counted_reason": "sin_partida"},
        {"id_movement": 9005, "id_product": 1, "quantity": 10.0, "reference": "OC-0001 FACT 1", "matched_by": "folio", "match_type": "parcial", "counted": false, "not_counted_reason": "parcial"}
      ],
      "sms": []
    }
  ],
  "msg": "Se conciliaron 1 ordenes de compra: 1 con entradas y 0 sin entradas; por cantidades 0 completas, 1 parciales y 0 con excedente",
  "error": null
}
```

Sin resultados también responde 200, con `data: []`.

**400**: un query param inválido, igual que antes:

```json
{"data": [], "msg": "Parametro status invalido", "error": "status debe ser un entero"}
```

Con BD caída, `msg` dice qué lectura falló. Hay un mensaje nuevo: `"Error al obtener los folios de las órdenes de compra"`.

**401**: `{"error": "No autorizado. Token invalido"}`, o `{"error": "Token not found"}` sin header.

### Gotchas

- `reception_status` y `quantity_status` pueden no coincidir. Una OC cuyas entradas son todas `parcial` o de otra OC queda `con_entradas` / `sin_entradas`.
- **Para totales globales, sumar solo las entradas con `counted: true`.** Una entrada que aparece bajo varias OCs cuenta en una sola.
- `received` solo puede pasar de `quantity` en la última partida de cada producto.
- `folio=` sigue casando el folio **o** el folio de proveedor, así que puede traer más de una OC.
- No aparecen las entradas capturadas antes de la fecha de la OC.
- `quantity_status` es una ayuda. El "recibido" (`status: 1`) lo sigue poniendo administración.

## Al modificar

- Si cambia cómo se liga una partida al inventario (`extra_info.id_inventory`), ajustar `_allocate_received`.
- Si la OC llega a tener unidad de medida, comparar unidades antes de sumar. Hoy se asume la `udm` del producto.
- Si se permite capturar entradas antes de la OC, quitar la cota o restarle días en `match_po_movements_and_sms`.
- Las partidas de solicitud siempre van con `order_id` (`insert_purchase_order_item_from_applications`) y las de OC con `purchase_id` (`insert_purchase_order_item`).
- `get_purchase_orders_folios` no filtra por usuario a propósito, porque decide a qué OC pertenece cada entrada. No usarla para listar.

## Verificación

[`Tests/tester_po_match_cantidades.py`](../Tests/tester_po_match_cantidades.py) (gitignored), contra BD dev. Crea 6 OCs (folios `ZZP115-*`), 9 partidas, 8 entradas y una solicitud, y borra todo al final (0 filas restantes). **41/41**:

- Helpers: OC dueña (única, folio propio, empates), redondeo (0.1 + 0.2 contra 0.3 = completa) y reparto por `id_item`, no por el orden del JSON.
- Casos de partida: completa, excedente en la última, parcial por folio de proveedor, `sin_ligar`.
- Casos de entrada: `sin_partida`, contains sin sumar, `otra_oc`, `ambigua`.
- Estados de OC: `parcial`, `completa`, `excedente` y `sin_entradas`.
- Filtros:
  - `folio=B` conserva `otra_oc` (los folios de todas las OCs).
  - Con `folio`, la cota de entradas es la fecha de la OC.
  - Los filtros de fecha y status se aplican en el SQL.
  - Status o fecha inválidos dan 400.
- HTTP con `app.test_client()`: 200 y 401.
- Editar una solicitud con una partida nueva la guarda con `order_id` y `purchase_id` NULL.

Además, sobre los datos reales de dev y sin filtros, respondió 200 en 0.2 s. `pyrefly check --python-version 3.11`: 0 errores en los 3 archivos.

## Pendientes

- `P-183` **[front]** Conciliación OC ↔ almacén: pintar `items[]` (pedido, recibido, estado) en el detalle, `quantity_status` en la lista, y marcar las entradas que no cuentan con su motivo.
- `P-129` sigue abierto. La parte de acotar las entradas de la conciliación quedó hecha aquí.
