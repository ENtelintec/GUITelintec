# Items de contrato / cotización: `qa_item_id` y upsert real

`PUT /contract` **no creaba** los items nuevos: respondía `200 "Contrato actualizado
correctamente"` y en la BD no aparecía nada. El front mandaba los items nuevos con la
llave del id en `null` y los existentes con su id real.

Este documento describe la causa raíz, el renombre de la llave a `qa_item_id` (corte
duro, request y response) y los bugs vecinos que se corrigieron de paso.

## La causa raíz: `null` no es `0`

[`wtforms_json`](../.venv/Lib/site-packages/wtforms_json/__init__.py) parchea
`Field.process` y, cuando la llave **viene en el JSON con valor `null`**, asigna
`self.data = None` y **se salta el `process` original**, así que el `default` del campo
nunca se aplica:

```python
if formdata and self.name in formdata:
    if formdata.getlist(self.name) == [None]:
        call_original_func = False
        self.data = None          # el default=0 del IntegerField NO aplica
```

El midleware decidía crear vs actualizar con `if new_product.get("id", 0) == 0`. Como
`None == 0` es `False`, el item nuevo caía en la rama de **actualizar**:

| el front manda | `data["..."]` | `== 0` | rama | resultado |
| --- | --- | --- | --- | --- |
| llave ausente | `0` (default) | `True` | create | ✅ |
| `"qa_item_id": null` | `None` | **`False`** | **update** | ❌ `UPDATE ... WHERE id = NULL` |
| `"qa_item_id": 0` | `0` | `True` | create | ✅ |

Y ese `UPDATE` no fallaba: `execute_sql` con `type_sql=3` devuelve el `rowcount` con
`flag=True` aunque no afecte filas
([`connection.py`](../templates/database/connection.py)), así que el endpoint
respondía `200` sin escribir nada. **Silencio total.**

El módulo de remisiones nunca tuvo el bug porque usa la comparación correcta
([`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py)):

```python
if item["qa_item_id"] is not None and item["qa_item_id"] > 0:
    if item["is_erased"] == 1:  delete
    else:                       update
else:                           create
```

El contrato de items de contrato/cotización ahora es **ese mismo**.

## Las 4 capas

```
HTTP    rs_Admin_presales.py  /contract (put), /quotation (put), /compare, /quotation/<id>
modelos api_contracts_models.py  ProductsPutQuotationForm + products_quotation_*_model
mid     Functions_midleware_admin.py  update_contract_from_api / update_items_quotation_from_api
DB      quotations_controller.py + contracts_controller.py  SQL crudo vía execute_sql
```

## Qué cambió

### 1. `id` → `qa_item_id` (corte duro, request **y** response)

La llave del PK `quotation_items.id` tenía **tres nombres** distintos según el
endpoint. Ahora es `qa_item_id` en todos:

| endpoint | antes | ahora |
| --- | --- | --- |
| `GET /admin/presales/quotation/<id>` | `id` | `qa_item_id` |
| `GET /admin/presales/contracts/products` | `item_id` | `qa_item_id` |
| `PUT /admin/presales/contract` (request) | `id` | `qa_item_id` |
| `PUT /admin/presales/quotation` (request) | `id` | `qa_item_id` |

`ProductsPutQuotationForm` es **compartido** por `ContractUpdateForm` y
`QuotationUpdateForm`, así que el renombre aplica a los dos `PUT` a la vez.

`qi.id AS item_id` en `get_items_contract_string` y
`get_contract_and_items_from_number` **no** se tocó: son alias de SQL sobre resultados
en tupla, se consumen por posición y no se exponen como llave JSON.

### 2. Upsert real, con guard de pertenencia

`update_items_quotation_from_api` ahora:

- `qa_item_id` **null / `0` / ausente / no numérico / negativo → crea**. La
  normalización vive en `_resolve_positive_int`, no en una comparación contra `0`.
- `qa_item_id > 0` que **no está en los items de esa cotización → crea** (un id viejo,
  o borrado por otro usuario, no debe tumbar el guardado). Queda en el log y se cuenta
  aparte en el `msg` (`N con id ajeno recreado(s)`).
- `is_erased == 1` → borra. **Comparación por igualdad**: antes era `!= 0`, así que un
  `is_erased: null` (→ `None`, y `None != 0` es `True`) **borraba el item** en lugar de
  actualizarlo.
- Un item que **no viene** en el arreglo no se toca (no se borra por diferencia).

El guard de pertenencia es lo que elimina el silencio: un `qa_item_id` inválido ya no
puede terminar en un `UPDATE` que no afecta filas, porque se crea. Además
`update_item_quotation` y `delete_item_quotation` llevan **`AND quotation_id = %s`**,
así que un id ajeno tampoco puede reescribir el item de otra cotización.

> **Por qué el `rowcount` solo se revisa en el `DELETE`:** en un `UPDATE` de MySQL
> `cursor.rowcount` son las filas **cambiadas**, no las coincidentes
> (`mysql.connector` no activa `CLIENT_FOUND_ROWS`). Guardar un item sin editarlo da
> `rowcount = 0`, así que tratar ese `0` como fallo reportaría 99 falsos errores de 100
> items. La pertenencia ya se valida antes de tocar la BD, que es la garantía real.

### 3. Coerción defensiva de numéricos

`_num_item_field` convierte `None` / vacío / no numérico al default del tipo, así que
un `quantity: null` o `price_unit: null` ya no se escribe como `NULL` en la columna.
`_item_quotation_values` centraliza el armado de las 11 columnas y **lo comparten**
`create_items_from_api` (POST) y `update_items_quotation_from_api` (PUT), que antes
duplicaban el bloque.

### 4. `quotation_id` sale de la BD, no del payload

`ContractUpdateForm.quotation_id` tiene `default=None`, así que **omitirlo** hacía
`not id_quotation → True` y `update_contract_from_api` creaba una **cotización nueva**;
`update_contract` entonces escribía `quotation_id = <nueva>` sin condición. Los items
previos conservaban el `quotation_id` viejo y, como
`get_contracts_with_items` une por `qi.quotation_id = c.quotation_id`, **desaparecían
de la vista del contrato**. Dos guardados seguidos y se veía igual que el bug de items.

Ahora la cotización ligada se lee del contrato con `get_contract` y el payload solo
puede **repuntar** mandando un `quotation_id > 0` (queda en el log). Solo se crea una
cotización nueva si el contrato realmente no tiene ninguna (`NULL`).

### 5. `GET /contracts/products` completa el viaje redondo

Devolvía únicamente `qa_item_id`, `partida`, `id_inventory`, `description`, `udm`,
`quantity`, `unit_price`. Como el `PUT` hace **reemplazo total** de columnas y
`wtforms_json` fuerza los `StringField` ausentes a `""`, un front que cargaba de ese
endpoint y guardaba **vaciaba 5 columnas**. Ahora el `GET` también manda
`description_small`, `brand`, `n_part`, `type_p` y `revision`.

### 6. Bugs vecinos corregidos de paso

- **`POST /contract` creaba los items con `contract_id = NULL`.**
  `create_items_from_api(products, id_quotation, data_token, id_contract=None)` se
  llamaba como `(data["products"], id_quotation, id_contract)`, así que `id_contract`
  caía en el slot de `data_token` y `contract_id` se quedaba en `None`. Rompía el
  enlace SM ↔ partida del contrato (`WHERE contract_id = %s` en
  `get_items_quotation_from_cotract` y `update_quotation_item_partida_from_sm`).
- **Tres `get_quotation` posicionales.** La firma es
  `get_quotation(data_token, id_quotation=None)`; se llamaba `get_quotation(<id>)`, así
  que el id caía en `data_token`, `id_quotation` quedaba en `None` y la query devolvía
  **todas** las cotizaciones (y se perdía el cambio de BD del permiso `tester`):
  - `get_quotations` (`GET /quotation/<id_q>`) → desempacaba una lista de N filas en 5
    variables → **500**. Ahora usa `result[0]` y devuelve **404** si no existe.
  - `update_quoation_from_api` (`PUT /quotation`) → `json.loads(result[2])` sobre una
    fila-tupla → **500**.
  - `compare_file_and_quotation` (`POST /compare`) → comparaba contra la fila
    equivocada. Ahora recibe `data_token` desde la ruta.
- **`contract_id = result[5]` en `update_quoation_from_api`.** `get_quotation` devuelve
  5 columnas; el índice 5 no existe. `quotations` no tiene `contract_id` (el enlace
  vive en `contracts.quotation_id`), así que se agregó
  `get_contract_id_by_quotation(id_quotation, data_token)`.
- **`create_item_quotation` usaba `type_sql=3`** (rowcount) para un `INSERT`; ahora `4`
  (lastrowid), igual que `create_items_quotation`.
- **Cotización sin items.** `JSON_ARRAYAGG` + `LEFT JOIN` devuelve
  `[{"qa_item_id": null, ...}]`; `_dict_products_from_quotation` filtra esas entradas
  para no dejar una llave `None` en el índice.
- **`msg` con conteos**: `"Items: 1 creado(s), 99 actualizado(s), 0 eliminado(s)"`.

## Al modificar

- **No compares el id contra `0`.** Usa `_resolve_positive_int`. `wtforms_json` deja un
  `null` de JSON como `None` sin aplicar el `default`, y `None == 0` es `False`. La
  misma trampa aplica a cualquier `IntegerField` del repo (`is_erased`, `id_inventory`,
  `quantity`, …): un `.get(key, default)` **no** protege contra un `None` explícito,
  porque la llave sí existe.
- **El orden de las llaves del `JSON_OBJECT` de `get_quotation` es load-bearing.**
  `compare_file_quotation` arma un `DataFrame` con esos registros y compara **por
  posición** contra un vector de 12 elementos
  ([`Functions_Aux_Admin.py`](../templates/resources/methods/Functions_Aux_Admin.py)).
  No agregues ni reordenes llaves ahí; si necesitas campos nuevos, agrégalos a
  `get_contracts_with_items`, que se consume por llave.
- **`ProductsPutQuotationForm` es compartido** por `ContractUpdateForm` y
  `QuotationUpdateForm`: cualquier campo que agregues aplica a los dos `PUT`.
- **`comment` es un campo fantasma**: los forms y los `api.model` lo aceptan, y ningún
  SQL de `quotation_items` lo escribe. Si algún día debe persistirse, hay que agregar
  la columna y meterlo en `create_item_quotation` / `update_item_quotation`.
- Al agregar un campo al item hay que tocar **los dos** lados del modelo (el
  `api.model` para swagger y el `Form` de WTForms, que es el validador real) más
  `_item_quotation_values`.

---

## Contrato mínimo para el front

### Auth

Header `Authorization` con el **JWT crudo, NO `Bearer <token>`** (`jwt.decode` se
aplica al header tal cual, sin quitar prefijo). Permiso: `administracion`.

Base path: `/GUI/api/v1/admin/presales`

Todas las respuestas usan el envelope `{data, msg, error}`.

### Tabla de traducción de llaves (no cambió, hay que traducir)

Solo el id se unificó. Estas tres siguen con nombre distinto entre el `GET` y el `PUT`:

| columna | en los `GET` | en el `PUT` |
| --- | --- | --- |
| `quotation_items.id` | `qa_item_id` | `qa_item_id` ✅ igual |
| `brand` | `brand` | `marca` |
| `n_part` | `n_part` | `n_parte` |
| `price_unit` | `price_unit` (en `/quotation/<id>`) · `unit_price` (en `/contracts/products`) | `price_unit` |

### `PUT /contract`

```json
{
  "id": 13,
  "quotation_id": 7,
  "metadata": {
    "emission": "2026-07-29",
    "client_id": 40,
    "contract_number": "4500123456",
    "identifier": "C-001",
    "abbreviation": "ACERA",
    "quotation_code": "21218",
    "planta": "1",
    "area": "ACERA",
    "location": "nuevoleon"
  },
  "timestamps": {"complete": {"timestamp": "", "comment": ""}, "update": []},
  "products": [
    {
      "qa_item_id": 12,
      "partida": 1,
      "udm": "SRV",
      "description": "SUMINISTRO DE SOPORTERIA Y MONTAJE DE CAMARA",
      "description_small": "SUMINISTRO DE SOPORTERIA",
      "quantity": 1,
      "revision": 0,
      "price_unit": 863.3,
      "marca": "",
      "n_parte": "",
      "type_p": "",
      "id_inventory": 0,
      "is_erased": 0
    },
    {
      "qa_item_id": null,
      "partida": 101,
      "udm": "PZA",
      "description": "ITEM NUEVO",
      "description_small": "ITEM NUEVO",
      "quantity": 5,
      "price_unit": 120.0
    }
  ]
}
```

**Reglas de `products`:**

| `qa_item_id` | `is_erased` | qué pasa |
| --- | --- | --- |
| `null`, `0`, ausente | cualquiera | **se crea** |
| `> 0` que existe en esa cotización | `1` | **se borra** |
| `> 0` que existe en esa cotización | `0`, `null`, ausente | **se actualiza** |
| `> 0` que **no** pertenece a esa cotización | cualquiera | **se crea** (id viejo) |
| — | — | un item que no venga en el arreglo **no se toca** |

**Gotchas:**

- `partida` y `udm` son **obligatorios** en cada item (`InputRequired`). Ojo: un
  `partida: 0` o `udm: ""` **falla la validación** y tumba todo el request con `400`.
- El update es **reemplazo total** de las columnas del item: manda las 12 llaves. Si
  omites `marca` / `n_parte` / `type_p`, se guardan como `""`.
- `quantity`, `revision`, `price_unit` e `id_inventory` en `null` se guardan como `0`
  (o `NULL` en `id_inventory`), no truenan.
- `comment` se acepta pero **no se guarda**.
- **`quotation_id` puede omitirse**: se usa el del contrato en la BD. Mándalo solo si
  quieres repuntar el contrato a otra cotización.
- Después de crear items **el `PUT` no devuelve los `qa_item_id` nuevos**: hay que
  volver a hacer `GET` del contrato para refrescar el grid. Si guardas dos veces sin
  recargar, los items nuevos se crean **otra vez**.

**`200` OK**

```json
{
  "data": {"id_contract": 13, "id_quotation": 7},
  "msg": "Contrato actualizado correctamente (ID 13). Items: 1 creado(s), 99 actualizado(s), 0 eliminado(s)",
  "error": null
}
```

**`200` con items parcialmente fallidos** — `error` es la lista de los que fallaron:

```json
{
  "data": {"id_contract": 13, "id_quotation": 7},
  "msg": "Contrato actualizado correctamente (ID 13). Items: 0 creado(s), 98 actualizado(s), 0 eliminado(s). 2 items no se pudieron crear/actualizar.",
  "error": ["Data too long for column 'udm' at row 1", "..."]
}
```

**`400` estructura inválida** (falta `partida`, `udm` vacío, …)

```json
{
  "data": null,
  "msg": "Estructura de datos inválida",
  "error": {"products": [{}, {"partida": ["This field is required."]}]}
}
```

**`404` contrato inexistente**

```json
{
  "data": null,
  "msg": "No se encontró el contrato a actualizar (ID 13)",
  "error": "Contract not found"
}
```

**`401` sin permiso**

```json
{"error": "No autorizado. Token invalido"}
```

### `GET /contracts/products`

Un objeto por contrato; `items` ahora trae los 12 campos:

```json
{
  "data": [
    {
      "id": 13,
      "metadata": {"contract_number": "4500123456", "client_id": 40, "abbreviation": "ACERA"},
      "creation": "2026-07-29 13:22:58",
      "quotation_id": 7,
      "timestamps": {"complete": {"timestamp": "", "comment": ""}, "update": []},
      "items": [
        {
          "qa_item_id": 12,
          "partida": 1,
          "id_inventory": null,
          "description": "SUMINISTRO DE SOPORTERIA Y MONTAJE DE CAMARA",
          "description_small": "SUMINISTRO DE SOPORTERIA",
          "udm": "SRV",
          "quantity": 1,
          "unit_price": 863.3,
          "brand": "",
          "n_part": "",
          "type_p": "",
          "revision": 0
        }
      ]
    }
  ],
  "msg": null,
  "error": null
}
```

Un contrato **sin items** devuelve `items: [{"qa_item_id": null, ...}]` (efecto del
`LEFT JOIN` + `JSON_ARRAYAGG`): filtra por `qa_item_id != null` antes de pintar el
grid.

### `PUT /quotation`

Mismo `products` que `PUT /contract` (comparten el form). `data` es
`{"id_quotation": <id>}`.

### `GET /quotation/<id_q>`

`products[].qa_item_id` (antes `id`). Con `id_q = -1` devuelve todas. Si el id no
existe ahora responde **`404`** (antes tiraba `500`).
