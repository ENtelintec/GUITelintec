# Cotización como OCD (orden de compra directa): `PUT /quotation/ocd` y llaves `document_type` / `client_po_number`

Fecha: 2026-09-28 · **Estado: hecho y verificado contra dev (35/35 checks HTTP, `Tests/tester_quotation_ocd.py`). Sin DDL: todo vive en `quotations.metadata` (JSON).**

Fase **F1** del plan [`planes/control_entregas_ocd_plan.md`](planes/control_entregas_ocd_plan.md) (junta con Administración 2026-09-23, grill 2026-09-28). Decisión de fondo: **la OCD no es una tabla, es una cotización marcada** (`document_type: "ocd"`) con el número de pedido del cliente. Reusa items, carga de Excel, el enlace `item_c_id` de los items de remisión y el PDF. Sobre esta marca se apoyan la F2 (control de entregas, que exige `document_type = ocd`) y la F5 (PDF FO-CXC-05).

## Qué cambia

- **Cinco llaves nuevas en `quotations.metadata`**, todas opcionales: `document_type` (`quotation` | `ocd`), `client_po_number` (pedido EXIROS / nº de OC del cliente, texto libre), `currency` (`MXN` | `USD`), `delivery_time` (texto), `approved_date` (`YYYY-MM-DD`, fecha en que el cliente aprobó).
- **`POST /quotation`** las acepta dentro de `metadata`; ausentes → defaults (`quotation`, `""`, `MXN`, `""`, `""`).
- **`PUT /quotation/ocd`** (nuevo): marca una cotización como OCD o ajusta esas llaves **sin tocar items ni el resto de la cabecera** (merge). Es la forma correcta de convertir: el `PUT /quotation` grande reemplaza metadata e items completos.
- **`PUT /quotation`** ahora **conserva** las llaves OCD y `status` cuando el payload no las trae (antes reemplazaba la metadata entera, lo que habría degradado una OCD a cotización y ya perdía el `status` que escribe el alta). Con valores explícitos, los aplica. Devuelve **404** si la cotización no existe (antes 400 genérico).
- **`GET /quotation/<id>`** y el listado (`/quotation/-1`) exponen las cinco llaves **siempre**, con defaults para las cotizaciones viejas que no las tienen. Listado con filtro nuevo `?document_type=ocd|quotation` (en Python: la llave vive dentro del JSON y las filas viejas no la traen).
- Revertir `ocd → quotation` está permitido hoy; la F2 lo bloqueará cuando exista un control de entregas activo.

## Las 4 capas

```
HTTP      rs_Admin_presales.py           PUT /quotation/ocd (nuevo) · GET /quotation/<id> lee ?document_type
modelos   api_contracts_models.py        MetadataQuotationForm + metadata_quotation_model ganan las 5 llaves (opcionales, AnyOf)
                                         QuotationOcdForm + quotation_ocd_model (nuevos)
mid       Functions_midleware_admin.py   _merge_ocd_keys (POST default / PUT conserva) · _normalize_quotation_metadata_out (GET)
                                         update_quotation_ocd_from_api (nuevo) · get_quotations(document_type=) · update_quoation_from_api lee antes de escribir
DB        quotations_controller.py       get_quotation_metadata (nuevo: SELECT metadata, timestamps sin agregar items)
```

En el form las llaves van con `default=""` y `AnyOf(("",) + …)`: `""` significa "no viene" y el midleware decide (default en el POST, conservar en el PUT). `approved_date` se valida en el midleware con `format_date` para dar el mensaje correcto en vez del genérico de WTForms.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permiso `administracion` en todo.
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` es `null` en éxito, lista de strings (midleware) u objeto por campo (form) en 400. 401 sin permiso: `{"error": "..."}` sin envelope.

### `PUT /quotation/ocd`

```json
{ "id_quotation": 51, "client_po_number": "3716578048", "currency": "MXN", "delivery_time": "2 semanas", "approved_date": "2026-09-20" }
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id_quotation` | int | sí | cotización existente |
| `document_type` | `ocd` \| `quotation` | no | default **`ocd`**; `quotation` = revertir |
| `client_po_number` | string | no | vacío conserva lo guardado (una cotización aprobada sin OC del cliente puede quedar sin número) |
| `currency` | `MXN` \| `USD` | no | vacío conserva |
| `delivery_time` | string | no | vacío conserva |
| `approved_date` | `YYYY-MM-DD` | no | vacío conserva |

| Código | Cuándo | Ejemplo |
|---|---|---|
| **200** | aplicado (aunque no cambie nada) | `data: {"id_quotation": 51, "document_type": "ocd", "client_po_number": "3716578048", "currency": "MXN", "delivery_time": "2 semanas", "approved_date": "2026-09-20", "changed": ["document_type", "client_po_number", "approved_date"]}` · `msg: "Cotización 51 marcada como OCD por … (cambios: …)"` |
| **400** | validación | `error: ["approved_date: se esperaba una fecha YYYY-MM-DD"]` (midleware) · `error: {"document_type": ["document_type debe ser quotation u ocd"]}` (form) |
| **404** | cotización inexistente | `msg: "No se encontró la cotización (ID 999)"` |

`data.changed` lista las llaves que realmente cambiaron (útil para no repintar); no toca items, así que no hace falta re-`GET` de productos.

### `POST /quotation` — cambios

Dentro de `metadata` se aceptan las mismas cinco llaves (mismos tipos). Ausentes → `document_type: "quotation"`, `currency: "MXN"`, resto `""`. Una OC del cliente por algo nunca cotizado se captura directo con `document_type: "ocd"` + `client_po_number`.

### `PUT /quotation` — cambios

- Si `metadata` **no trae** una llave OCD (o la manda vacía), **se conserva** la guardada. Con valor explícito, se aplica (mismas validaciones → 400).
- `status` de la metadata también se conserva.
- Cotización inexistente → **404** (antes 400).

### `GET /quotation/<id>` / `GET /quotation/-1` — cambios

- `metadata` trae siempre `document_type`, `client_po_number`, `currency`, `delivery_time`, `approved_date` (defaults si la fila es vieja).
- Listado: `?document_type=ocd` o `=quotation`; otro valor → 400.

### Gotchas

- Para convertir una cotización usar **`/quotation/ocd`**, no el `PUT /quotation`: el grande reemplaza los items con la lista que mande el front.
- `currency` aquí es la moneda de la cotización/OCD; la del control de saldos (`balance_controls.currency`) es independiente.

## Al modificar

- **Llave OCD nueva**: agregarla a `_OCD_DEFAULTS` (midleware; de ahí salen merge, normalización del GET y `changed`), al `MetadataQuotationForm` / `QuotationOcdForm` y a los dos `api.model`.
- **Bloquear la reversión con control activo** (F2): en `update_quotation_ocd_from_api`, antes del `update_quotation`, consultar `delivery_controls` por `quotation_id` con `status != 2` cuando `ocd_keys["document_type"] == "quotation"` → 400.
- `get_quotation_metadata` es la lectura ligera para cualquier merge de cabecera; no usar `get_quotation` (agrega items) solo para leer metadata.
- Ojo con el nombre del archivo de rutas: git lo rastrea como `rs_Admin_presales.py` (A mayúscula); un rename a minúsculas rompe `from templates.resources.rs_Admin_presales import …` en `app.py`.
