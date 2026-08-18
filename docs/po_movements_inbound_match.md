# Match OC ↔ movimientos de entrada de almacén ↔ SMs

Endpoint nuevo de conciliación: para cada orden de compra, qué movimientos de
entrada de almacén ya se registraron con su folio (el campo `reference` del
movimiento se llena con el folio de la OC al crear una entrada) y qué SMs están
relacionadas a esa OC.

## Endpoint

`GET /GUI/api/v1/admin/collections/purchase/movements/match`

- Permisos: `department=["administracion", "purchases"]`.
- Sin body; query params opcionales:
  - `status` (entero): filtra por status de la OC. Las canceladas (status 4) se
    excluyen **siempre** (misma regla que `get_purchase_orders_with_items`).
  - `date_from` / `date_to` (`YYYY-MM-DD`): rango sobre `po.timestamp`. Una OC
    con timestamp no parseable **se incluye** (no se filtra a ciegas).
  - `folio`: limita el resultado a la OC cuyo `folio` **o** `folio_supplier`
    coincida (exacto, case-insensitive).
- Visibilidad: misma regla que `fetch_purchase_orders` — un usuario que no es
  administrator ni gerente solo ve sus propias OCs (`created_by`).
- Respuesta: envelope `{data, msg, error}`; `msg` con el conteo de OCs
  conciliadas con/sin entradas.

## Regla de match OC ↔ movimiento

El `reference` del movimiento vive en
`product_movements_amc.extra_info->'$.reference'` y se guarda **en mayúsculas**;
el `folio` de la OC es columna y el `folio_supplier` vive en
`purchase_orders.extra_info` (JSON). Ambos lados se normalizan con
`UPPER(TRIM(...))`:

1. **Exacto**: `reference == folio` o `reference == folio_supplier` (vacíos se
   ignoran) → `match_type: "exacto"`, `matched_by: "folio" | "folio_supplier"`.
2. **Fallback contains**: solo para movimientos que no pegaron exacto con
   *ninguna* OC, se busca el folio (o folio_supplier) *dentro* del reference
   (p.ej. `reference = "OC-0012 FACT 33"`) → `match_type: "parcial"`.
3. Un movimiento que pega con varias OCs aparece bajo **todas** (el front puede
   detectar duplicados por `id_movement`).
4. Movimientos con reference vacío no matchean; no hay sección de huérfanos (la
   vista es OC-céntrica).

Por OC se deriva `reception_status: "con_entradas" | "sin_entradas"` (la
conciliación por cantidades producto a producto quedó para una segunda
iteración).

## SMs relacionadas

- **Primario** — `deliveries`: items de SM (`sm_items.deliveries`, JSON) cuyos
  deliveries traigan `id_order == id_order` de la OC (los escribe
  `sync_sm_deliveries_from_po`, ver
  [`po_sm_deliveries_tracking.md`](po_sm_deliveries_tracking.md)). Trae el
  objeto `delivery` completo (folio, folio_supplier, comment con la entrega
  estimada).
- **Fallback** — `id_item_sm`: si la OC no aparece en ningún delivery (OCs
  anteriores a la sincronización), se resuelve por
  `purchase_order_items.extra_info.id_item_sm`; en ese caso `delivery: null`.
- Cada SM lleva `link: "deliveries" | "id_item_sm"` y por item vinculado:
  `id_item`, `description`, `quantity`, `dispatched` (cantidad suministrada) y
  `delivery`.

## Para el front

### Ejemplo de respuesta (real, generado con el flujo dummy en dev)

`GET .../purchase/movements/match?folio=OC-DUMMY-1` → `200`:

```json
{
  "data": [
    {
      "id": 25,
      "folio": "OC-DUMMY-1",
      "folio_supplier": "FAC-DUMMY-1",
      "status": 0,
      "supplier": 1,
      "created_by": 16,
      "timestamp": "2026-07-10 15:10:50",
      "time_delivery": "2026-07-20",
      "reception_status": "con_entradas",
      "movements": [
        {
          "id_movement": 6871,
          "id_product": 1,
          "sku": "10010000001",
          "quantity": 4.0,
          "movement_date": "2026-07-10 15:10:50",
          "sm_id": "61",
          "product_name": "ABRAZADERA CLIP 1/2",
          "udm": "PIEZA ",
          "reference": "OC-DUMMY-1",
          "matched_by": "folio",
          "match_type": "exacto"
        },
        {
          "id_movement": 6873,
          "id_product": 1,
          "sku": "10010000001",
          "quantity": 1.0,
          "movement_date": "2026-07-10 15:10:50",
          "sm_id": "61",
          "product_name": "ABRAZADERA CLIP 1/2",
          "udm": "PIEZA ",
          "reference": "OC-DUMMY-1 FACTURA 999",
          "matched_by": "folio",
          "match_type": "parcial"
        }
      ],
      "sms": [
        {
          "id_sm": 61,
          "folio": "SM-DUMMY-1",
          "status": 0,
          "link": "deliveries",
          "items": [
            {
              "id_item": 208,
              "description": "ABRAZADERA CLIP 1/2",
              "quantity": 4.0,
              "dispatched": 0.0,
              "delivery": {
                "color": "#ffffff",
                "folio": "OC-DUMMY-1",
                "state": 0,
                "comment": "[Entrega estimada: 2026-07-20]",
                "id_order": 25,
                "quantity": 4.0,
                "timestamp": "2026-07-10 15:10:50",
                "folio_supplier": "FAC-DUMMY-1"
              }
            }
          ]
        }
      ]
    }
  ],
  "msg": "Se conciliaron 1 ordenes de compra: 1 con entradas y 0 sin entradas",
  "error": null
}
```

### Referencia de campos

`data[]` — una entrada por OC, ordenadas por `id` **descendente** (más
recientes primero):

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int | `id_order` de la OC |
| `folio` | string | folio Telintec de la OC |
| `folio_supplier` | string | folio del proveedor; **puede venir `""`** (OCs sin capturarlo) |
| `status` | int | status de la OC: `0` pendiente, `1` recibido (`4` cancelado nunca aparece) |
| `supplier` | int | id del proveedor (`suppliers_amc`); el nombre no viene, resolverlo con el catálogo ya cargado |
| `created_by` | int | `employee_id` del creador |
| `timestamp` | string | `YYYY-MM-DD HH:MM:SS`, fecha de creación de la OC |
| `time_delivery` | string | fecha de entrega prometida (texto libre; puede venir `""`) |
| `reception_status` | string | `"con_entradas"` \| `"sin_entradas"` (derivado: hay o no movimientos matcheados) |
| `movements` | array | entradas de almacén matcheadas; `[]` si no hay |
| `sms` | array | SMs relacionadas; `[]` si la OC no tiene vínculo a ninguna SM |

`movements[]` — ordenados por `movement_date` **descendente**:

| Campo | Tipo | Notas |
|---|---|---|
| `id_movement` | int | id del movimiento en almacén |
| `id_product` / `sku` / `product_name` / `udm` | int / string | producto del movimiento |
| `quantity` | float | cantidad que entró en **ese** movimiento |
| `movement_date` | string | `YYYY-MM-DD HH:MM:SS` |
| `sm_id` | **string** | se envía **crudo**, tal cual lo capturó almacén. Históricamente empezó siendo el id numérico de la SM pero mutó a referencia libre: a veces es el id (`"61"`), a veces el folio/referencia de la SM (`"SM-0701-194"`), a veces una referencia extra de una factura de la SM. Puede ser `"0"` o vacío. **No usarlo como FK** ni asumirle formato; para el vínculo confiable OC↔SM usar `sms[]` — este campo es informativo/para cruce manual |
| `reference` | string | el reference original tal como lo capturó almacén (sin normalizar) |
| `matched_by` | string | `"folio"` \| `"folio_supplier"` — contra qué campo de la OC pegó |
| `match_type` | string | `"exacto"` \| `"parcial"` (parcial = el folio aparece *dentro* del reference; conviene distinguirlo visualmente, p.ej. badge amarillo) |

`sms[]`:

| Campo | Tipo | Notas |
|---|---|---|
| `id_sm` / `folio` / `status` | int / string / int | identificación de la SM (status de `materials_request`, mismo enum que usa el módulo SM) |
| `link` | string | `"deliveries"` (vínculo con detalle de entrega) \| `"id_item_sm"` (fallback para OCs viejas, sin detalle) |
| `items[]` | array | solo los items de esa SM vinculados a esta OC |

`sms[].items[]`:

| Campo | Tipo | Notas |
|---|---|---|
| `id_item` | int | id en `sm_items` |
| `description` | string | nombre del material |
| `quantity` | float | cantidad solicitada en la SM |
| `dispatched` | float | cantidad ya suministrada por almacén (avance: `dispatched/quantity`) |
| `delivery` | object \| **null** | la entrega de este item que apunta a esta OC; **`null` cuando `link == "id_item_sm"`** |

`delivery` (llaves escritas por `sync_sm_deliveries_from_po` y por el form de
deliveries del módulo SM — pass-through, pueden faltar llaves en registros
viejos, leer con defaults): `id_order`, `folio`, `folio_supplier`, `quantity`,
`comment` (la fecha estimada viaja embebida como `[Entrega estimada: ...]`),
`timestamp`, `state`, `color`.

### Códigos y errores

- `200` — siempre con `{data, msg, error: null}`; sin resultados → `data: []`
  (no es 404). `msg` trae el resumen contable ("Se conciliaron N...").
- `400` — query param inválido: `{"data": [], "msg": "Parametro status invalido",
  "error": "status debe ser un entero"}` (igual para fechas mal formadas).
- `401` — token inválido o sin permiso: `{"error": "..."}` (sin `data`).

### Casos borde que la UI debe manejar

- **Movimiento repetido entre OCs**: si un reference pega con más de una OC
  (folio_supplier compartido, contains ambiguo), el mismo `id_movement` aparece
  bajo cada una. Para totales globales deduplicar por `id_movement`.
- **`delivery: null`** en todos los items cuando `link == "id_item_sm"` — la UI
  debe degradar a mostrar solo la identificación de la SM y el avance
  `dispatched/quantity`.
- **Payload sin filtros crece con el histórico** — para pantallas de consulta
  usar `date_from`/`date_to` o `status`; `folio` sirve para la vista de detalle
  de una sola OC.
- `quantity`/`dispatched` llegan como float aunque sean enteros (`4.0`).

## Capas tocadas

1. **HTTP** — [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py):
   resource `PurchaseMovementsMatch` (`/purchase/movements/match`), solo
   `expected_headers_per` (GET sin body, sin WTForms; los query params se
   validan en el midleware → 400 con envelope si son inválidos).
2. **Orquestación** — [`MD_Purchases.py`](../templates/resources/midleware/MD_Purchases.py):
   `match_po_movements_and_sms(params, data_token)` hace todo el match en
   Python (el fallback contains y el `folio_supplier` dentro de JSON hacen
   impráctico resolverlo en SQL). Helpers `_normalize_folio_match` y
   `_safe_number` (Decimal/None → float, para que la respuesta sea
   JSON-serializable).
3. **DB** — [`sm_controller.py`](../templates/controllers/material_request/sm_controller.py):
   `get_sm_items_deliveries_for_match_db(id_items, data_token)` — una sola
   query que trae los sm_items con deliveries no vacíos (vínculo primario) MÁS
   los `id_item` pasados (fallback), con folio/status de su SM. Reutiliza sin
   cambios `get_purchase_orders_with_items` y `get_ins_db_detail`
   ([`movements_controller.py`](../templates/controllers/product/movements_controller.py)).
4. **Modelos** — sin cambios (no hay payload que validar/documentar).

## Al modificar

- Si el `reference` deja de guardarse en mayúsculas (o se mueve de
  `extra_info`), ajustar `_normalize_folio_match` y el índice de columna (11)
  de `get_ins_db_detail` en el midleware.
- Si `sync_sm_deliveries_from_po` cambia las llaves del delivery
  (`id_order`/`folio`/`folio_supplier`), este match se rompe silenciosamente —
  actualizar `match_po_movements_and_sms` a la par.
- Si se agrega `folio_supplier` como columna real de `purchase_orders`,
  simplificar la extracción del JSON aquí y en `fetch_purchase_orders`.
- Pendiente (2.ª iteración): conciliación por cantidades cruzando
  `movement.id_product` vs `purchase_order_items.extra_info.id_inventory`
  (status `parcial`/`completo` por item).
