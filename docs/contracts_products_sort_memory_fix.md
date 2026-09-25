# `contracts/products`: 1038 "Out of sort memory" al ordenar el JSON agregado

Reportado 2026-09-24: `GET /admin/presales/contracts/products` respondía **400**
con `1038 (HY001): Out of sort memory, consider increasing server sort buffer
size`. En la misma pantalla `GET /admin/collections/remission--1` también daba
400, pero por otra causa: a la BD de test le faltaba una columna (ver
[Remisiones](#remisiones--no-tenía-el-problema-su-400-era-de-esquema)).

| Capa | Archivo | Cambio |
| --- | --- | --- |
| Controller | [`contracts_controller.py`](../templates/controllers/contracts/contracts_controller.py) | `get_contracts_with_items`: sin `ORDER BY` en SQL, orden en Python. |
| Controller | [`suppliers_controller.py`](../templates/controllers/supplier/suppliers_controller.py) | `get_all_suppliers_amc`: items en subconsulta correlacionada (preventivo). |
| BD (test) | [`activity_reports_files.sql`](../scripts_db_handle/activity_reports_files.sql) | Columna `activity_reports.files` que faltaba en test. |

Midleware, rutas y modelos no cambian.

## Causa raíz

`get_contracts_with_items` arma un `JSON_ARRAYAGG` con todas las partidas de
cada contrato y **después** ordenaba con `ORDER BY c.creation DESC`. El plan
(`EXPLAIN FORMAT=TREE`):

```
-> Sort: c.creation DESC
    -> Stream results
        -> Group aggregate: json_arrayagg(json_object('qa_item_id', qi.id, ...))
            -> Nested loop left join
                -> Sort: c.id
                    -> Table scan on c
                -> Index lookup on qi using quotation_id (quotation_id=c.quotation_id)
```

El `Sort: c.creation DESC` recibe filas **ya agregadas**: cada una lleva el JSON
completo de su contrato. MySQL 8.4 ordena "por valor" (la fila entera va al sort
buffer), y si **una sola fila** no cabe en `sort_buffer_size` (256 KB, el
default, igual en dev, test y prod) truena con 1038.

JSON de `items` del contrato más grande, medido el 2026-09-24:

| BD | Contrato | Partidas | JSON | ¿Truena? |
| --- | --- | --- | --- | --- |
| dev | 4 | 317 | 161 KB | no |
| test | 5 | 683 | 337 KB | **sí** |
| prod | 4 | 317 | 161 KB | no (le quedan ~95 KB) |

A ~500 bytes por partida, el límite anda por las **~500 partidas en un solo
contrato**. Por eso solo se veía con el token `tester` (BD de test); dev y prod
iban a tronar igual en cuanto un contrato creciera.

## El arreglo

### Contratos: ordenar en Python

Se quitó el `ORDER BY` del SQL y el resultado se ordena antes del `return` con
`sorted(result, key=lambda row: row[2], reverse=True)`; `row[2]` es `creation`,
`datetime NOT NULL` en las 3 BDs. Sin `ORDER BY`, el único sort del plan es
`Sort: c.id` sobre la tabla base `contracts` (filas chicas, antes del join): el
JSON ya no pasa por el sort buffer. La función sigue devolviendo las filas
ordenadas, así que `get_contractsWithItems` no cambió.

### Proveedores: subconsulta correlacionada (preventivo)

`get_all_suppliers_amc` tenía el mismo patrón: `LEFT JOIN` a una derivada con
`JSON_ARRAYAGG` + `ORDER BY s.name`. Hoy no truena (el proveedor más grande
pesa 2.3 KB), pero se corrigió de paso.

Aquí el `ORDER BY` **se queda en SQL**: `suppliers_amc.name` usa
`utf8mb4_0900_ai_ci` (no distingue mayúsculas ni acentos) y un `sorted` de
Python no reproduce ese orden. Los items pasan a una subconsulta en la
proyección:

```sql
COALESCE((
    SELECT JSON_ARRAYAGG(JSON_OBJECT('id_item', i.id, ...))
    FROM sql_telintec_mod_admin.items_suppliers_amc i
    WHERE i.id_supplier_amc = s.id_supplier
), JSON_ARRAY()) AS items
...
ORDER BY s.name
```

Plan: `Sort: s.name → Table scan on s`, y la subconsulta (`subquery in
projection; dependent`) se evalúa **después** del sort, por fila ya ordenada.
El `COALESCE(..., JSON_ARRAY())` conserva el `[]` de los proveedores sin items.
El `WHERE i.id IS NOT NULL` de la derivada se quitó: `id` es la PK, siempre era
verdadero. `items_suppliers_amc.id_supplier_amc` tiene índice en las 3 BDs.

### Remisiones: no tenía el problema, su 400 era de esquema

`get_remission_by_id` (`GET /remission-<id>`) no tiene `ORDER BY`. MySQL sí
ordena, pero **antes** de agrupar (`Sort: ar.id` sobre las filas del join, una
por partida), nunca el JSON ya armado. Con el `sort_buffer_size` mínimo (32 KB)
pasa en las 3 BDs.

Su 400 en test era `1054 Unknown column 'ar.files'`: **a la BD de test le
faltaba `activity_reports.files`**, la única columna distinta contra dev (prod
es igual a dev). Se arregla con
[`activity_reports_files.sql`](../scripts_db_handle/activity_reports_files.sql),
solo en test. Mientras no corra, **todos** los endpoints de remisión dan 400 en
test.

## Verificación

Solo lectura contra dev, test y prod (prod con la sesión en `READ ONLY`). Se
comparó el controller de `HEAD` (referencia; en test con
`/*+ SET_VAR(sort_buffer_size = 64MB) */` para que corriera) contra el nuevo:

- **Contratos**: en las 3 BDs, mismo contenido, mismo orden e `items`
  byte-idénticos (10/10, 11/11, 12/12). En test, `get_contractsWithItems` pasa
  de 400 a **200**.
- **Proveedores**: filas byte-idénticas y en el mismo orden (78/78, 79/79,
  80/80). `GET /admin/db/suppliers/allSuppliers` y
  `GET /almacen/inventory/suppliers/allSuppliers` responden 200.
- **Margen**: los dos SQL nuevos corren con `sort_buffer_size` = 32 KB (el
  mínimo) en las 3 BDs. Además, la subconsulta correlacionada + `ORDER BY`
  devuelve el JSON de 337 KB del contrato 5 de test con ese buffer: el JSON no
  pasa por el sort.
- `pyrefly check` de los dos controllers: 0 errores.

## Contrato mínimo para el front

**No requiere cambios en el front.** Mismos endpoints, mismo shape y mismo
orden; solo deja de fallar.

- **Auth**: header `Authorization` con el **JWT crudo**, NO `Bearer <token>`.
- **Endpoints**: los tres son `GET`, sin body ni query params, y responden JSON
  con el envelope `{data, msg, error}`.

| Endpoint | Departamento | Orden de `data` |
| --- | --- | --- |
| `GET /GUI/api/v1/admin/presales/contracts/products` | `administracion` | `creation` descendente |
| `GET /GUI/api/v1/admin/db/suppliers/allSuppliers` | `administracion` | `name` ascendente, sin distinguir mayúsculas ni acentos |
| `GET /GUI/api/v1/almacen/inventory/suppliers/allSuppliers` | `almacen` | igual que el anterior |

**200 — `contracts/products`** (recortado; el ítem trae siempre las 15 llaves):

```json
{
  "data": [
    {
      "id": 5,
      "metadata": {"contract_number": "4500123456", "client_id": 40, "emission": "2026-04-14 10:18:40", "abbreviation": "ACERA"},
      "creation": "2026-04-14 10:18:40",
      "quotation_id": 5,
      "timestamps": {"complete": {"timestamp": "", "comment": ""}, "update": []},
      "items": [
        {
          "qa_item_id": 2847,
          "partida": 2,
          "id_inventory": null,
          "description": "",
          "description_small": "Organizador de cableado Horizontal 2U",
          "udm": "PZA",
          "quantity": 1.0,
          "unit_price": 717.9000244140625,
          "brand": null,
          "n_part": null,
          "type_p": null,
          "revision": 0,
          "section_index": 0,
          "section_title": "General",
          "section_type": "general"
        }
      ]
    }
  ],
  "msg": null,
  "error": null
}
```

**200 — `admin/db/suppliers/allSuppliers`** (`items` es una **lista**):

```json
{
  "data": [
    {
      "id": 12,
      "name": "PROVEEDOR EJEMPLO SA DE CV",
      "seller_name": "Nombre Vendedor",
      "seller_email": "ventas@proveedor.mx",
      "phone": "8110000000",
      "address": "Monterrey, N.L.",
      "web_url": "",
      "type": "",
      "extra_info": {"brands": ["BOSCH"], "fast_order": 0, "rfc": "XAXX010101000"},
      "rfc": "XAXX010101000",
      "items": [
        {
          "id_item": 11,
          "item_name": "Taladro eléctrico industrial",
          "unit_price": 1250.5,
          "part_number": "BOS-AX34",
          "currency": "MXN",
          "created_at": "2026-01-08 16:27:13.000000",
          "updated_at": "2026-01-08 16:27:13.000000",
          "id_inventory": null
        }
      ]
    }
  ],
  "msg": null,
  "error": null
}
```

**200 — `almacen/inventory/suppliers/allSuppliers`**: mismas llaves base, con
`brands` en lugar de `extra_info`/`rfc`, e `items` como **string JSON** (hay que
parsearlo): `"items": "[{\"id_item\": 11, ...}]"`; sin items → `"[]"`.

**400** — error de BD (ya no por el 1038):

```json
{"data": [], "msg": "No se pudieron obtener los contratos con items", "error": "<mensaje de MySQL>"}
```

(en proveedores: `"msg": "No se pudieron obtener los proveedores"`.)

**401**:

```json
{"error": "No autorizado. Token invalido"}
```

Gotchas (todos previos a este cambio):

- Un contrato **sin partidas** sigue devolviendo `items: [{"qa_item_id": null,
  ...}]` (fila vacía del `LEFT JOIN`); filtrar `qa_item_id != null` antes de
  pintar. Ver
  [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md).
- `unit_price` de contratos viene de una columna `FLOAT`: puede traer ruido
  (`717.9000244140625`), así que hay que redondear al pintar.
- El orden de `items` **dentro** de cada contrato o proveedor no está
  garantizado: ordenar en el front (`partida` / `item_name`).

## Al modificar

- **No ordenar en SQL filas que ya traen un `JSON_ARRAYAGG` (o cualquier blob
  grande) agregado**, ni con `GROUP BY … ORDER BY` ni con `LEFT JOIN` a una
  derivada agregada + `ORDER BY`. Hay dos salidas: ordenar en Python (contratos)
  o mover el agregado a una subconsulta en la proyección (proveedores). Si el
  orden es por texto, conviene la subconsulta: Python no replica la collation.
- **No arreglarlo subiendo `sort_buffer_size`** (en el servidor o con
  `SET_VAR`): solo aplaza el error hasta que otro registro crezca, y cada
  consulta gasta más memoria.
- **Para medir el margen de una consulta**, correrla con
  `SELECT /*+ SET_VAR(sort_buffer_size = 32768) */ …` (el mínimo). Si pasa, su
  sort no depende del tamaño del JSON.
- `get_contracts_with_items` devuelve las filas ya ordenadas por `creation`
  descendente y el midleware no las reordena. Otro criterio de orden va en ese
  `sorted(...)`, no en el SQL.
- No agregarle `ORDER BY` a `get_remission_by_id`. Su sort interno (antes de
  agrupar) solo truena si **una** remisión junta ~256 KB entre `history`,
  `files` y `extra_info`; hoy el `history` más grande mide 1.4 KB.
