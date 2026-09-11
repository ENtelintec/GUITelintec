# Control de saldos (Cobranza): cabecera por contrato, formatos FO-CXC en BD, columnas dinámicas y movimientos

Fecha: 2026-09-11 · Origen: pedido del front en `telintec_webapp/docs/backend/pendientes-control-saldos.md` (secciones 2–7, 10 y 12), resuelto con un grill el mismo día.

Hasta hoy el "control de contrato" de Cobranza no existía en el back: los 5 archivos FO-CXC, sus contratos, las columnas de cada formato y las fechas de vigencia vivían hardcodeados en el front (`src/lib/control-saldos-archivos.ts`), y el único endpoint de saldos era `PUT /remissionBalance` (bloque de saldos **por remisión**, [`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md)). Este cambio crea la entidad, lleva el catálogo de formatos a la BD y cierra de paso la llave `remission_amount` que el front ya mandaba y el back descartaba.

## Decisiones (grill 2026-09-11)

| Tema | Decisión |
|---|---|
| Cardinalidad | **1 control activo por contrato** (validado en código; MySQL no tiene UNIQUE parcial y un control cancelado no debe bloquear re-crear). `month_period` / `currency` son informativos. |
| Membresía remisión → control | **`activity_reports.contract_id`**, que ya existía y las remisiones ya traen. No hay columna ni tabla puente nueva. El front cruza fila ↔ control por `contract_id` con `GET /balanceControl`. |
| `remissions[]` del POST | Opcional: valida ids y **adopta huérfanas** (`contract_id` NULL → contrato del control, con entrada en el `history` de la remisión). Inexistente u otro contrato → 400 listando cuáles. |
| Formatos FO-CXC | Son **catálogo de SGI** (mismos códigos ISO que los PDFs). Tabla nueva `iso_formats`: ids 1..8 = `files/settings.json["formats"]` (conservados para migrar `iso_form` de `PDFGenerator` después), 9..13 = FO-CXC-07..11 con `config` JSON (columnas fijas + campos de cabecera). El control guarda `format_id`. |
| Cabecera | Base común en columnas reales; campos propios del formato en `extra_info`, validados contra `config.header_fields` (llave declarada, tipo, opciones). **Validación floja**: solo `contract_id` y `format_id` obligatorios (precedente `purchase_management`). Llave no declarada → 400 (nada se descarta en silencio). |
| Columnas dinámicas | Inglés canónico: `custom_fields: [{key, label, value_type, comment}]`, `value_type ∈ text\|number\|date\|boolean`. **Mismo esquema** que `config.columns`/`config.header_fields` del formato. Lista completa en el PUT (idempotente) + **sweep** de los valores de las llaves quitadas en las remisiones del contrato. |
| Valores por remisión | `activity_reports.extra_info.custom_fields = {key: value}` vía `PUT /remissionBalance` (llave `custom_fields`), **estricto**: sin control activo → 400, llave no declarada → 400, tipo coercionado, `null` borra. El GET de remisiones lo aplana como objeto. |
| Monto contratado | Solo se fija en el POST; el PUT lo rechaza. Tabla `balance_control_movements` **inmutable** (solo INSERT) con usuario del token; el POST inserta el movimiento inicial (0 → monto). El endpoint de inyección/ajuste espera la maqueta F2 del front. |
| Permisos | Lecturas: `administracion` / `purchases` / `operaciones`. Escrituras (POST, PUT, fields, cancel): solo `administracion`. Catálogo además `sgi`. |
| Fuera | DELETE físico (solo cancel suave). Edición de `contract_id` / `format_id` (inmutables: cambiarlos rompería membresía y columnas). |

## Capas tocadas

1. **DDL** — [`scripts_db_handle/control_saldos.sql`](../scripts_db_handle/control_saldos.sql): `iso_formats` (+ seed idempotente de 13 formatos), `balance_controls`, `balance_control_movements`. FKs reales opcionales al final (**activadas en dev** el 2026-09-11: `contract_id`/`format_id` RESTRICT, movimientos CASCADE). Corrido en dev; **test/prod pendientes**.
2. **Controller** — [`templates/controllers/purchases/balance_control_controller.py`](../templates/controllers/purchases/balance_control_controller.py) (nuevo): `FORMAT_COLUMNS` / `CONTROL_COLUMNS` / `MOVEMENT_COLUMNS` (el midleware mapea por índice, append-only), listado con LEFT JOIN a formato y contrato + subquery `remissions_count`, `get_active_balance_control_by_contract`, movimientos, `get_remissions_by_ids` / `adopt_remission_to_contract` (solo si sigue `contract_id IS NULL`) y `remove_custom_field_keys_from_remissions` (`JSON_REMOVE` con paths parametrizados, scoped por `contract_id`).
3. **Midleware** — [`templates/resources/midleware/MD_BalanceControl.py`](../templates/resources/midleware/MD_BalanceControl.py) (nuevo): validación config-driven (`coerce_value`, `validate_custom_fields`, `_reserved_keys` = columnas reales + `columns[].key` + `columns[].source_key` + `header_fields[].key`), `_ApiError`/`_api_guard` para cortar con envelope, POST con movimiento inicial y reversa si falla, PUT parcial con diff curado en `history`, PUT fields con sweep, cancel, catálogo, y `validate_remission_custom_fields` (consumido por `MD_Admin_Collections`).
4. **Modelos** — [`static/Models/api_balance_control_models.py`](../static/Models/api_balance_control_models.py) (nuevo). Los campos propios del formato **no** se declaran en WTForms (son dinámicos): el midleware los lee del JSON crudo de `metadata`.
5. **Rutas** — [`templates/resources/rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py): `/balanceControl` (GET/POST/PUT), `/balanceControl/<int:id_control>`, `/balanceControl/catalogs`, `/balanceControl/fields`, `/balanceControl/cancel`.
6. **`PUT /remissionBalance` + `GET /remission-<id>`** ([`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py), [`api_purchases_models.py`](../static/Models/api_purchases_models.py)): llave nueva `remission_amount` (los 4 toques de la sección 12: form, `_BALANCE_EXTRA_KEY_MAP`, `_GET_EXTRA_NUMERIC_FIELDS`, `_HISTORY_EXTRA_FIELDS`+`_HISTORY_NUMERIC_FIELDS`, + Swagger y descripción corregida de `projection_balance`), y `custom_fields` (dict) en el PUT + aplanado en el GET + diff `custom_fields.<key>` en el `history`.

Verificado ciclo completo contra BD dev por HTTP (`test_client`): **61 checks** (catálogo y permisos, 15 validaciones del POST, adopción/ajena/inexistente, 409 duplicado, lista/detalle con movimientos y usuario, PUT parcial con `changes`, columnas + valores + sweep, cancel/re-crear). Datos temporales borrados; `pyrefly` 0 errores en los 6 archivos.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Todo responde JSON `{data, msg, error}`; `error` es `null`, string o **lista** de strings.
- Permisos: GETs con `administracion` / `purchases` / `operaciones`; POST / PUT / fields / cancel **solo `administracion`** (401 en otro caso); `/catalogs` además `sgi`.

### `GET /balanceControl/catalogs`

Formatos de control de saldos **activos** (solo los que tienen `config.kind = "balance_control"`) + catálogos. Con esto el front puede retirar `CONTROL_SALDOS_ARCHIVOS`, `CAMPOS_EXTRA_POR_ARCHIVO` y las listas de `campos`.

```json
{
  "data": {
    "formats": [
      {
        "id": 13, "code": "FO-CXC-11", "revision": "R4", "label": "FO-CXC-11 R4",
        "name": "Control Saldo Incluye Tickets y Cotización", "department": "administracion",
        "emission_date": "2026-03-09", "is_active": 1,
        "config": {
          "kind": "balance_control",
          "columns": [
            {"key": "ultimo_registro", "label": "Último registro", "value_type": "date", "source_key": "date_report"},
            {"key": "monto_remision", "label": "Monto remisión", "value_type": "number", "source_key": "remission_amount", "is_sum": true}
          ],
          "header_fields": [
            {"key": "quotation_number", "label": "Nº de cotización", "value_type": "text", "required": true},
            {"key": "ticket_system", "label": "Sistema de tickets", "value_type": "text", "required": true, "options": ["Mesa de ayuda", "SAP", "Otro"]},
            {"key": "requires_hes", "label": "Requiere HES", "value_type": "boolean", "required": false}
          ]
        }
      }
    ],
    "value_types": ["text", "number", "date", "boolean"],
    "currencies": ["MXN", "USD"],
    "movement_types": [{"code": 0, "label": "INICIAL"}, {"code": 1, "label": "INYECCION"}, {"code": 2, "label": "AJUSTE"}]
  },
  "msg": null, "error": null
}
```

- `columns` = columnas fijas de la tabla del formato, **en orden**; `key` es el id de columna que el front ya usa (`monto_remision`, `estatus_hes`…), `source_key` es la llave **aplanada de la fila de `GET /remission--1`** de donde sale el valor (`remission_amount`, `hes_status`, `date_report`, `folio`, `user`…), `is_sum` marca las que van al total.
- `header_fields` = campos de cabecera **propios del formato** (lo que antes era `CAMPOS_EXTRA_POR_ARCHIVO`); `required` es informativo para el front (el back **no** lo exige), `options` cerrado cuando viene.
- Ids de formato en dev/test/prod: 9 = FO-CXC-07 R2, 10 = FO-CXC-08 R3, 11 = FO-CXC-09 R3, 12 = FO-CXC-10 R3, 13 = FO-CXC-11 R4 (el seed fija los ids).

### `POST /balanceControl` — alta

```json
{
  "metadata": {
    "contract_id": 9, "format_id": 13,
    "month_period": "2026-08", "currency": "MXN",
    "contract_number": "6700373484", "pedido_exiros": "3716578048",
    "contracted_amount": 1250000.00,
    "start_date": "2026-03-09", "end_date": "2027-03-08",
    "plant": "San Nico", "coordinator": "Nombre del coordinador",
    "contract_object": "Cableado estructurado y accesorios",
    "quotation_number": "COT-2026-0148", "quotation_date": "2026-02-20", "quotation_validity": "2026-04-20",
    "ticket_system": "Mesa de ayuda", "ticket_number": "TK-99120", "requires_hes": true
  },
  "remissions": [341, 342, 350],
  "custom_fields": [
    {"key": "numero_estimacion", "label": "Número de estimación", "value_type": "number", "comment": "Estimación del contrato"}
  ]
}
```

- Obligatorios: solo `contract_id` y `format_id`. El resto de la base es opcional; `contract_number` vacío → se toma `contracts.code`; `pedido_exiros` vacío → `contracts.metadata.exiros` si el contrato lo tiene; `currency` vacío → `MXN`; `contracted_amount` ausente/`null` → `0`.
- Los **campos del formato van planos en `metadata`** con la `key` que declara `config.header_fields`. `boolean` acepta `true/false`, `1/0`, `"Sí"/"No"`; `date` = `YYYY-MM-DD`; `number` = numérico. Una opción fuera de `options` → 400.
- **Una llave en `metadata` que ni la base ni el formato declaren → 400** (`error: ["llave desconocida: foo"]`). Es deliberado: no se descarta nada en silencio.
- `remissions` es opcional. Solo tiene efecto sobre remisiones **sin contrato** (se adoptan). Las del mismo contrato se aceptan tal cual; inexistentes u otro contrato → 400 con la lista.
- `custom_fields` opcional; `key` snake_case (`^[a-z][a-z0-9_]{0,49}$`), única y sin chocar con `columns[].key`, `columns[].source_key`, `header_fields[].key` ni columnas reales del control → 400 diciendo cuál.

Respuestas:

| Código | Cuándo | `data` |
|---|---|---|
| **201** | creado | `{"id_control": 5, "id_movement": 5, "adopted_remissions": [341]}`; `msg` = `"Control de saldos creado correctamente (ID 5, FO-CXC-11 R4, contrato 6700373484); remisiones adoptadas: [341]"`. `error` puede traer una **lista** de adopciones parciales fallidas (no fatal). |
| **409** | el contrato ya tiene un control **activo** | `{"id_control": <existente>}` — el front puede navegar a él |
| **404** | contrato o formato inexistente | `null` |
| **400** | formato sin config de saldos / retirado, llave desconocida, tipos/opciones, `end_date < start_date`, monto negativo, `custom_fields` inválidos, remisiones inválidas, estructura (`error` = `validator.errors`) | `null`, `error` = lista de mensajes |

### `GET /balanceControl` — listado

Query params opcionales: `contract_id`, `format_id`, `is_active` (default `1`), `all=1` (activos y cancelados). Cada fila:

```json
{
  "id_control": 5, "contract_id": 9, "format_id": 13,
  "format_code": "FO-CXC-11", "format_revision": "R4", "format_name": "Control Saldo Incluye Tickets y Cotización", "format_label": "FO-CXC-11 R4",
  "contract_code": "6700373484", "contract_abbreviation": "CAMN", "contract_identifier": "CABLEADO AMN",
  "month_period": "2026-08", "currency": "MXN", "contract_number": "6700373484", "pedido_exiros": "3716578048",
  "contracted_amount": 1250000.0, "start_date": "2026-03-09", "end_date": "2027-03-08",
  "plant": "San Nico", "coordinator": "Nombre del coordinador", "contract_object": "Cableado estructurado y accesorios",
  "quotation_number": "COT-2026-0148", "quotation_date": "2026-02-20", "quotation_validity": "2026-04-20",
  "ticket_system": "Mesa de ayuda", "ticket_number": "TK-99120", "requires_hes": true,
  "custom_fields": [{"key": "numero_estimacion", "label": "Número de estimación", "value_type": "number", "comment": "Estimación del contrato"}],
  "remissions_count": 3, "is_active": 1, "created_by": 77, "timestamp": "2026-09-11 12:30:00",
  "history": [{"user": 77, "action": "Creación", "date": "2026-09-11 12:30:00", "comment": "..."}],
  "extra_info": {"quotation_number": "COT-2026-0148", "...": "..."}
}
```

- Los campos del formato vienen **aplanados** al nivel raíz (además de en `extra_info`); un campo no capturado viene `null`.
- **Cruce fila ↔ control** en la pantalla de saldos: `GET /balanceControl` una vez y mapear cada remisión de `GET /remission--1` por `contract_id`. Remisión "disponible" para el paso 3 = `contract_id` `null` (o un contrato sin control activo). `format_key` por fila = `format_code` del control de su contrato.
- `GET /balanceControl/<int:id_control>` (200/404) devuelve la misma fila más: `format` (`{id, code, revision, name, label, config}`), `remissions` (`[{id, folio, date, status}]` de las remisiones del contrato), `remissions_count`, y **`movements`** del más reciente al más antiguo:

```json
"movements": [
  {"id_movement": 5, "id_control": 5, "type": 0, "type_label": "INICIAL", "movement_date": "2026-09-11",
   "amount": 1250000.0, "previous_balance": 0.0, "resulting_balance": 1250000.0,
   "user_id": 77, "user_name": "Admin QA", "reason": "Monto contratado inicial", "document": "3716578048",
   "timestamp": "2026-09-11 12:30:00", "extra_info": {}}
]
```

### `PUT /balanceControl` — cabecera, parcial

```json
{ "metadata": { "id_control": 5, "coordinator": "Otro", "quotation_number": "COT-2" } }
```

- Solo se escribe lo **presente** en `metadata` (base o campo del formato); `""`/`null` vacía el campo. Llave desconocida → 400.
- **`contracted_amount`, `contract_id` y `format_id` → 400** siempre ("el monto solo cambia con movimientos de saldo"). Control cancelado → 400.
- 200 → `data: {"id_control": 5, "changes": [{"field": "coordinator", "before": "…", "after": "Otro"}]}` (el mismo diff queda en `history[].changes`).

### `PUT /balanceControl/fields` — columnas dinámicas (lista completa)

```json
{ "id_control": 5, "custom_fields": [
  {"key": "numero_estimacion", "label": "Número de estimación", "value_type": "number", "comment": ""},
  {"key": "fecha_estimacion", "label": "Fecha estimación", "value_type": "date"}
] }
```

- Reemplaza la lista: agregar, renombrar (`label`), reordenar y quitar son el mismo llamado; el **orden del arreglo es el orden de las columnas**. Lista vacía = sin columnas dinámicas.
- Quitar una `key` **borra sus valores** en todas las remisiones del contrato (sweep); cambiar la `key` de una columna cuenta como quitar + agregar (los valores se pierden).
- 200 → `data: {"id_control": 5, "custom_fields": [...], "added_keys": [...], "removed_keys": [...], "remissions_swept": 3}`; si el sweep falla, 200 con `error: ["no se pudieron limpiar…"]`. 400 con la regla violada (`key` repetida / choca con columna del formato / `value_type` fuera del catálogo).

### `PUT /balanceControl/cancel`

`{"id_control": 5, "comment": "Creado por error"}` → 200 (idempotente; `msg` dice si ya estaba cancelado). Cancelación suave: desaparece del listado por default, `all=1` lo trae; el contrato queda libre para un control nuevo. No toca remisiones ni movimientos.

### `PUT /remissionBalance` — valores de columnas dinámicas y `remission_amount`

```json
{ "metadata": { "id": 341, "remission_amount": 3500.50,
                "custom_fields": {"numero_estimacion": 12, "fecha_estimacion": "2026-09-01", "aprobada": null} } }
```

- `remission_amount` (float, opcional): **llave propia**, no toca `remission_total`; misma mecánica de merge que el resto del bloque de saldos; queda en el `history` de la remisión.
- `custom_fields` (objeto `{key: value}`, opcional): merge por llave; **`null` borra** la llave; tipo coercionado según la columna (`"12"` → `12.0`, `"Sí"` → `true`). Se valida contra el control **activo** del `contract_id` de la remisión: remisión sin contrato o contrato sin control → 400; llave no declarada → 400 (`"custom_fields.nope: columna no declarada en el control 5"`); tipo inválido → 400. Cada cambio entra al `history` como `{"field": "custom_fields.<key>", "before", "after"}`.
- `GET /remission-<id>` / `GET /remission--1`: cada fila trae `remission_amount` (float o `null`) en la raíz y `custom_fields` como objeto (`{}` si no hay).

### Gotchas

- Los ids de contrato **no son los mismos en dev, test y prod** (el catálogo hardcodeado del front traía los de prod): resolver siempre contra `GET /admin/presales/contracts/products` / `contract_code` del control, nunca por id fijo.
- La cabecera acepta `boolean` en varias formas, pero el GET siempre devuelve `true`/`false`; el front no debe comparar contra `"Sí"`.
- `error` es lista en los 400 de validación y en los 201/200 con fallos parciales (adopción, sweep); string en errores de BD; `null` en éxito limpio.
- Una remisión puede recibir `custom_fields` aunque no venga en `remissions` del POST: basta que su `contract_id` tenga control activo.

## Coherencia con lo que ya existía (barrido 2026-09-11)

Se revisó toda la documentación de control de saldos (back: `remission_module_fields_and_balance.md`, `remission_balance_get_filters_campos_nuevos.md`, `control_table_operaciones_y_campos_admin.md`, los 3 `.md` de `scripts_db_handle/campos_*`; front: `pendientes-control-saldos.md`, `control-table-contract-id-fk.md`, `campos-extra-por-contrato.md`, `llaves-pendientes-control-reportes.md`, spec `selector-contratos-remision-cobranza`) y las rutas de `rs_*.py`:

- **Sin endpoints duplicados.** Los dos niveles quedan separados como pidió el front: `PUT /remissionBalance` + `GET /remission-<id>` (bloque de saldos **por remisión**, filtros `month_period`/`general_status`/`include_items`) y `/balanceControl*` (**cabecera por contrato**). Ninguna ruta previa creaba/leía la cabecera. `quotation_number`, `ticket_number`, `month_period`, `coordinator`, `plant` y `pedido_exiros` existen en ambos niveles **a propósito** (fila vs cabecera, tablas distintas); una columna dinámica no puede llamarse como ninguno de ellos.
- **`remission_amount`**: la tabla de alias de `remission_module_fields_and_balance.md` decía "un solo campo, `remission_amount` no existe"; quedó anotado ahí que ahora son dos (`projection_balance` ≠ `remission_amount`).
- **Bug heredado que pegaba de lleno a la membresía** ([`control-table-contract-id-fk.md`](../../WebApps/telintec_webapp/docs/backend/control-table-contract-id-fk.md) del front, 2026-08-26, nunca registrado en el back): `PUT /remission` y `PUT /remissionControlTable` reescribían `activity_reports.contract_id` con el `0` del form cuando la llave no venía (FK `activity_contract_id` → 1452) y con `NULL` si venía `null` (la remisión salía del control en silencio). **Corregido**: `_resolve_contract_id` conserva el de la fila salvo valor `> 0`, los POST guardan `NULL` en vez de `0`, y `contract_id` entra a los campos vigilados del `history`. Verificado (12 checks) sin regresión de los 61.
- **`pedido_exiros`** del control ahora también se siembra desde `contracts.metadata.exiros` cuando el POST no lo manda (igual que `contract_number` ← `contracts.code`).
- **Campos legacy de saldos en `contracts.metadata`** (`saldo_pedido`, `remision_mxn`, `saldo_comprometido`, `saldo_hes`, `saldo_facturado`, `estatus_hes`, `num_hes`, `liberacion_hes`, `sgd`, `fecha_sg`, `estatus_remision`, `remitos_enviados`, `coordinador`, `ceco`…): un intento anterior de control de saldos **por contrato con un solo valor**, previo a las remisiones; vacíos en dev; los sigue escribiendo `PUT /contract` (`validate_metadata`) y solo los usa la pantalla vieja del front `administracion/control-saldos/ControlSaldos.tsx` (montada en `/dashboard/administracion/control-saldos`), que llama a un `/logs` **que no existe en este back**. Quedan **superseded** por `balance_controls` + `PUT /remissionBalance`; no se retiran del form de contratos (el front de contratos re-manda toda la metadata), pero no deben usarse para saldos. `exiros` sí sigue vivo (pantalla de contratos) y es la semilla de `pedido_exiros`.
- **`campos-extra-por-contrato.md` del front** (lado operaciones, 2026-06-23): pregunta de dónde sacar "qué campos extra tiene cada contrato" (`ot_ticket`, `centro_costos`, `responsable_centro_costos`, `personal_infra`, hoy `CONTRACT_CONFIG` hardcodeado). La respuesta natural ya existe: `config.columns[].source_key` del formato del control (`GET /balanceControl?contract_id=` → `format_id` → `/catalogs`). Ojo: el mapa del front **no coincide** con los formatos (p. ej. `auto_pesq`/`puebla`/`sala_juntas` son FO-CXC-07, que no tiene esas columnas) — a conciliar con Cobranza del lado del front.
- **`useControlSaldoResumen`** del front deriva el monto del contrato de Σ partidas y la vigencia del catálogo hardcodeado porque "el API no lo expone": ahora `contracted_amount`, `start_date`/`end_date` vienen del control.

## Al modificar

- **Columnas nuevas en `balance_controls`**: agregar al final de `CONTROL_COLUMNS` y del `SELECT` del controller (append-only: el midleware mapea por índice); si es editable, a `_BASE_COLS` (y a `_bc_base_fields` + `_BalanceControlBaseForm` en los modelos); si es fecha, a `_DATE_COLS`.
- **Campo nuevo de cabecera de un formato**: solo `config.header_fields` del formato en `iso_formats` (hoy por SQL; con el CRUD de SGI, por API). Sin código.
- **Columna fija nueva en la tabla de un formato**: `config.columns` (+ `source_key` a una llave que `GET /remission--1` exponga; si no existe, agregarla a `_GET_EXTRA_*_FIELDS` de `MD_Admin_Collections`).
- **Formato nuevo de saldos**: fila en `iso_formats` con `config.kind = "balance_control"`; el catálogo lo expone solo.
- **`value_type` nuevo**: `VALUE_TYPES` en midleware **y** modelos + rama en `coerce_value`.
- **Inyección de saldo (F2)**: `insert_balance_control_movement` con `type` 1/2 + `UPDATE balance_controls SET contracted_amount = %s WHERE id_control = %s AND contracted_amount = %s` (bloqueo optimista: `previous_balance` leído antes; 0 filas → 409 y reintentar). Nunca UPDATE/DELETE sobre movimientos.
- **`iso_form` de los PDFs**: `PDFGenerator` sigue leyendo `files/settings.json["formats"]`; los ids 1..8 de `iso_formats` son idénticos justo para migrarlo sin re-mapear.

## Pendientes

- **[back] DDL en test y prod** (`scripts_db_handle/control_saldos.sql`, con o sin el bloque de FKs según decida el usuario).
- **[front] Retirar la pantalla vieja** `administracion/control-saldos/ControlSaldos.tsx` (`/dashboard/administracion/control-saldos`, llama a `/logs` inexistente y edita los campos legacy de `contracts.metadata`); usar `contracted_amount`/`start_date`/`end_date` del control en el resumen (en vez de Σ partidas + catálogo); conciliar `CONTRACT_CONFIG` (campos extra por contrato, lado operaciones) con `config.columns` de los formatos.
- **[front] Enganchar `confirmarCreacion`** al `POST /balanceControl`, leer formatos/columnas de `/catalogs`, cruzar filas por `contract_id`, mandar `custom_fields` (inglés) y pintar/capturar las celdas vía `PUT /remissionBalance`.
- **[back] CRUD de formatos ISO para SGI** (`iso_formats`: alta/edición de código, revisión, vigencia y `config`; baja suave) — el catálogo ya vive en BD, falta la pantalla/endpoints de SGI.
- **[back] Migrar `iso_form` de `PDFGenerator` a `iso_formats`** (y retirar `settings.json["formats"]`).
- **[back] Endpoint de inyección/ajuste de saldo** (`POST /balanceControl/movement`) cuando el front cierre la maqueta F2 (montos negativos, adjunto, quién puede).
- **[front] Sección 11 (F1 discrepancia de totales, F2 maqueta del historial)**: sin dependencia del back.
