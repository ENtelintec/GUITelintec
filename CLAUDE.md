# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Internal Telintec back-office REST API — Flask + flask-restx — exposing endpoints under `/GUI/api/v1/<area>` for RRHH (HR), SM (material requests), Almacén (inventory), SGI, Bitácora, Dashboards, Admin/Presales, Admin/Collections, Common, Misc, and Login/UserSystem. The Flask app is consumed by separate desktop GUI clients (the repo's name is historical; this project is the API, not a GUI). MySQL is the backing store; JWT bearer tokens carry user permissions.

## Change docs

Per-change design notes live in [`Docs/`](Docs/) (Spanish, one `.md` per change, relative `../` links into the code). When you make a non-trivial change — new/altered endpoint, cross-layer refactor, schema/contract change — add a short doc there following the existing style ([`heads_crud_fields_sync.md`](Docs/heads_crud_fields_sync.md) is a good template: the 4 layers touched, what changed, and an "Al modificar" section). Current docs:

- [`contract_crud_response_envelope.md`](Docs/contract_crud_response_envelope.md) — `/contract` and `/quotation` CRUD aligned to a fixed `{data, msg, error}` response envelope (Spanish, concise `msg` with ID, `error` always present); fixes set-literal/nested-data/inverted-rollback bugs and removes a misapplied `marshal_with`.
- [`po_folio_generation_from_contract_code.md`](Docs/po_folio_generation_from_contract_code.md) — PO folio generation now reads the contract `code` column (last 4 digits) instead of `metadata.contract_number`; max+1-per-pattern consecutive logic; `get_purchase_orders` (no-items listing).
- [`heads_crud_fields_sync.md`](Docs/heads_crud_fields_sync.md) — `/head` CRUD aligned with its `fetch` (editable `name`, vacant `employee` as `NULL`, `area` wired end-to-end).
- [`purchase_list_pdf.md`](Docs/purchase_list_pdf.md) — purchase list PDF generation.
- [`sm_items_extra_info_url_fix.md`](Docs/sm_items_extra_info_url_fix.md) — SM items `extra_info` URL fix.
- [`payroll_s3_upload.md`](Docs/payroll_s3_upload.md) — payroll S3 upload.
- [`po_sm_deliveries_tracking.md`](Docs/po_sm_deliveries_tracking.md) — al crear/actualizar una OC se rastrean los cambios hacia los `deliveries` de los items de SM vinculados (vía `id_item_sm`): mapea `folio`/`folio_supplier` (sobrescriben) y `time_delivery` (segmento marcado `[Entrega estimada: …]` en `comment`), match por `delivery.id_order`, crea el delivery si no existe; registra en el `history` de la SM; no fatal (la OC sigue 200/201, detalle a `msg`/log/notificación). Helper `sync_sm_deliveries_from_po` + controllers `get_sm_item_deliveries_db`/`update_deliveries_sm_item_db`.
- [`remission_history_changes.md`](Docs/remission_history_changes.md) — historial resumido de cambios de la remisión en el mismo campo `activity_reports.history` (json): corrige el bug del key `timestamp` (era `timestamp: timestamp` → la fecha como clave; ahora `"timestamp": timestamp`, 13 ocurrencias) y agrega un objeto `changes:{metadata:[{field,before,after}], items:[{qa_item_id,description,action:'updated|added|removed',fields:[...]}]}`. Campos curados (no diff genérico); el front mapea `field→etiqueta`; entrada siempre se agrega aunque `changes` quede vacío. Cubre `update_remission_from_api` (metadata+items) y `update_remission_control_table_from_api` (solo metadata). Helpers `_diff_history_fields`/`_diff_remission_items`/`_remission_meta_from_*`.
- [`quotation_remission_unit_price_split.md`](Docs/quotation_remission_unit_price_split.md) — el `unit_price` del ítem (fila compartida cotización/remisión en `quotation_activity_items`) ahora separa sugerido vs real: el sugerido de la cotización se conserva en `extra_info["unit_price_quotation"]` y `unit_price` pasa a ser el real de la remisión. Sugerido siempre escrito desde la cotización; remisión preserva (el form sigue mandando un solo `unit_price`); editar cotización con `report_id` ya presente protege el real (solo actualiza el sugerido); ítem sin cotización → `unit_price_quotation=0`; los GET exponen `unit_price_quotation` plano. Pendiente: historial de remisiones por ítem.
- [`remission_module_fields_and_balance.md`](Docs/remission_module_fields_and_balance.md) — campos por módulo (REMISIONES / Control de Reportes / CONTROL SALDOS) acumulados en `extra_info` de la misma fila de `activity_reports`; endpoint nuevo `PUT /remissionBalance` (solo edita, no crea; no toca columnas base); merge por módulo y por llaves presentes en el JSON crudo (`_extra_info_updates` + `_*_EXTRA_KEY_MAP`); ningún campo nuevo obligatorio en back, estatus como integer; nombres canónicos resueltos (`totalSinIva`→`total_sin_iva`, `statusReport`→`status_report`, `projection_balance`, `ot`+`ticket_number` separados, sin `ot_ticket_number`); un solo GET de remisiones expone todo aplanado; fixes: `KeyError 'items'` en POST control table, `project` guardado como tupla, `quotation_id or > 0` TypeError.
- [`sm_response_envelope.md`](Docs/sm_response_envelope.md) — los 24 endpoints de `/sm` alineados al envelope `{data, msg, error}`; 4 `marshal_with` removidos; bugs corregidos (`/add/urgent` `return data`, `/cancel` tupla invertida, `msg:"ok"` en 400 de `/item`); `msg` español-con-ID y `data` estructurado a `{"id_*": N}` en escrituras (detalle largo solo a log/notificación; fallos parciales a `error` como lista); único pendiente abierto: bug KPI `(critical_date - critical_date)` (a futuro KPIs configurables).
- [`remission_pdf_download.md`](Docs/remission_pdf_download.md) — `GET /remission/download/pdf/<int:id_report>?iva_rate=0.16`, descarga el PDF formal de una remisión (header/logo Telintec, metadata de contrato/pedido, tabla de items, totales); solo la página 1 del documento de referencia (sin anexos de reporte de materiales/fotos). `partida` por item resuelto con `LEFT JOIN` nuevo a `quotation_items` en `get_remission_by_id` (sin cambio de esquema); `No. Contrato Marco` = `contracts.code` vía `get_contract`; SUBTOTAL = `Σ line_total` de items (no `extra_info.total_sin_iva`); `iva_rate` opcional en query, default 0.16. De paso corrige un bug real en `get_contract(data_token, id_contract)` que hacía fallar siempre la búsqueda de un contrato por ID (afectaba también `GET /contract/<id>`). Pendiente: anexar al PDF los `files` (adjuntos S3) de la remisión y el reporte de materiales formato Ternium.
- [`sm_download_not_found_and_parsing.md`](Docs/sm_download_not_found_and_parsing.md) — descarga de SM (PDF/Excel) con `sm_id` inexistente ya no truena con 500: causa raíz `JSON_ARRAYAGG` sin `GROUP BY` en `get_sm_by_id`/`get_sm_by_folio` (una fila de NULLs para ids inexistentes; el fix protege los 8 call sites), not-found → envelope `{data, msg, error}` con 404; parseo defensivo en `dowload_file_sm` (fechas NULL → celda vacía, `comment` NULL → estatus "pendiente", `observations` NULL → `[]`, filtra items con `id` NULL de SMs sin items). De paso: typo `dispached`→`dispatched` (la columna de suministrado imprimía "None" siempre), contador de items congelado en 1, encabezado Excel "Stock"→"C. Suministrado" (igual que el PDF).
- [`sm_pdf_grid_redesign.md`](Docs/sm_pdf_grid_redesign.md) — PDF de SM rediseñado en cuadrícula: metadata (2 pares label|valor por fila) e items con celdas `rect` y labels/encabezados en celeste `#BDD7EE` (texto negro bold); valores largos hacen wrap dentro de la celda (fix del desborde de "Personal Telintec"); multipágina repite header Telintec + encabezados de columna (metadata solo pág. 1); tabla de entregas/firmas para llenar a mano (una fila por attachment de `extra_info["files"]`, mínimo 1, cap 20) + campo "Fecha de Entrega Completa"; corrige encabezados UDM/Cantidad cruzados respecto a los datos del PDF anterior; helpers `_sm_*` nuevos solo para SM (los compartidos con `InventoryStoragePDF`/`ReturnMaterials` intactos); observaciones fuera del documento. El formato de diseño está capturado como skill en `.claude/skills/pdf-design/`. Pendiente: pre-llenar las filas de entrega/firmas con la info de cada attachment (fecha, quién entrega/recibe) cuando `create_sm_attachment_api` la guarde en `extra_info["files"]`.

## Run / lint

- **Run dev server**: `python wsgi.py` — binds 127.0.0.1:5000 with `debug=True`. `app.py` is the Flask app factory; `wsgi.py` is the entry point.
- **Type check**: `pyrefly check` — config in [pyrefly.toml](pyrefly.toml). Uses `.venv/Scripts/python.exe`. Note: many DB call sites carry `# pyrefly: ignore` because `execute_sql`'s return type is union-typed (see below).
- **Tests**: there is no test framework wired up. `Tests/`, `tester*.py`, `*test.py`, and `*_test.json` are all gitignored — treat any file matching those patterns as scratch.
- **Dependencies**: `pip install -r requirements.txt`. Heavy ML/data deps (tensorflow, keras, sklearn, matplotlib, pandas) are present because some endpoints generate reports/PDFs and run model inference; don't drop them when trimming.

## Environment & secrets

[static/constants.py](static/constants.py) hard-codes `environment = "dev"` at the top and that flag drives:
- which `.env` to load (`.env` in dev vs `../.env` in prod)
- which secret keys to read for DB host/user/pass (`HOST_DB` vs `HOST_DB_AWS`, etc.)
- where `domain.pem` is found

When promoting/testing prod behavior, flip that constant — there is no `FLASK_ENV` or env-var override.

`.env` is at repo root (gitignored). Required keys include `HOST_DB`/`USER_SQL`/`PASS_SQL` (dev), `HOST_DB_AWS`/... (prod), `HOST_DB_TEST`/... (test), and `TOKEN_MASTER_KEY` (JWT signing key).

## Architecture — the layers that matter

The codebase has a strict 4-layer pattern. Stay inside it; cross-layer shortcuts will surprise reviewers.

```
HTTP                templates/resources/rs_<area>.py        flask-restx Namespaces, route definitions
  ↓
Orchestration       templates/resources/midleware/*.py      business logic, multi-controller composition
  ↓                 templates/resources/methods/*.py        login/auth helpers, area-specific aux
  ↓
DB                  templates/controllers/<domain>/*.py     raw SQL via execute_sql
  ↓
Driver              templates/database/connection.py        mysql.connector wrapper

Validation/swagger  static/Models/api_*_models.py           flask-restx api.model + WTForms Forms
```

Each `rs_<area>.py` defines one `Namespace("GUI/api/v1/<area>")` and is registered in [app.py](app.py). To add a new area: create the namespace module, add `from ... import ns as ns_<area>` and `api.add_namespace(ns_<area>)` in app.py.

The `controllers/` subtree is organized by domain (`employees/`, `product/`, `purchases/`, `material_request/`, `tickets/`, `vouchers/`, `chatbot/`, `notifications/`, etc.), not by HTTP route — a single namespace can pull from many controllers via its midleware.

## The `execute_sql` convention (important)

Every DB call goes through [templates/database/connection.py](templates/database/connection.py). It returns `(flag: bool, error: str, result)` and the shape of `result` depends on the integer `type_sql`:

- `1` → `fetchone()` (single tuple or `[]`)
- `2` → `fetchall()` (list of tuples)
- `3` → `rowcount` (int, after commit) — for UPDATE/DELETE
- `4` → `lastrowid` (int, after commit) — for INSERT
- `5` → `fetchall()` without param substitution (raw query)

There is also `execute_sql_multiple(sql, values_list, type_sql, data_token)` that iterates `values_list` column-major (transposes inside the function) — read it before calling, the indexing is unusual.

Both accept an optional `data_token`; if `data_token["is_tester"]` is true, they redirect to the test DB host (`HOST_DB_TEST` etc.). This is how the "tester" permission swaps databases at runtime.

**`error` is already a `str`** (the second tuple element). When you put it in a response envelope's `error` field, write `"error": error` — **not** `str(error)`, which pyrefly flags as `Unnecessary str() call`. Reserve `str(...)` for things that genuinely aren't strings: `Exception` objects caught in `except` blocks (`str(e)`), and the union-typed `result` (whose shape varies by `type_sql`). Same rule for f-strings — `f"...{error}"`, not `f"...{str(error)}"`.

## Auth pattern — every endpoint starts the same way

```python
flag, data_token, msg = token_verification_procedure(request, department="rrhh")
if not flag:
    return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
validator = SomeForm.from_json(ns.payload)   # WTForms validation
if not validator.validate():
    return {"errors": validator.errors}, 400
data = validator.data
data_out, code = some_midleware_fn(data, data_token)
return data_out, code
```

[templates/resources/methods/Functions_Aux_Login.py](templates/resources/methods/Functions_Aux_Login.py) implements this. Two things to know:

1. **`department` can be a string or a list** — list = OR-match across departments.
2. **Permission match is substring + case-insensitive** (`verify_department_permission`), AND any permission containing `"administrator"` always passes. Adding a new permission name with the substring `"administrator"` would silently grant admin everywhere — be careful when editing [static/permissions_models.json](static/permissions_models.json).

Endpoints conventionally return `(dict, http_code)`. Midleware functions follow the same shape so `rs_*` can pass results through unchanged.

## Models / forms duality

Each `static/Models/api_<area>_models.py` defines two parallel things for each endpoint:
- a `flask_restx` `api.model(...)` — used in `@ns.expect(...)` for swagger docs and the `expected_headers_per` model adds the `Authorization` header expectation.
- a WTForms `Form` subclass (e.g. `EmployeeInsertForm`) — used at runtime via `Form.from_json(ns.payload)` (enabled by `wtforms_json.init`). This is the actual validator; the api.model is doc-only.

When adding a field, update **both**. The `# pyrefly: ignore` on `from_json` calls is intentional — wtforms-json patches the class dynamically and pyrefly can't see it.

## Daemons and side processes

[templates/daemons/](templates/daemons/) holds background workers (medical notification sweeps, file/peripheral watchers). They are NOT started by `app.py` — they're invoked via separate scripts or threads spawned from specific endpoints. `files/flags_daemons.json` is the on-disk flag store coordinating their state. If you're touching anything daemon-related, grep for `update_flag_daemons` to find the lifecycle calls.

## File-based state under `files/`

Several caches, logs, and config live as files (paths centralized in [static/constants.py](static/constants.py)):
- `files/logs/<area>/...` — per-area log files (bitacora, sm, sgi_chv, sgi_vouchers, db, admin, almacen, po, rh, users)
- `files/*_cache.pkl` and `files/*_cache.json` — endpoint-level caches; gitignored
- `files/contracts/`, `files/files_fichaje/`, `files/quizz_out/` — generated artifacts
- `files/Pmodels/` — pickled / Keras models (for ML-backed endpoints)
- `files/settings.json`, `files/flags_daemons.json` — runtime config

Don't read or write under `files/` from new code without using the constants — paths are referenced from many places.

## Naming / locale notes

- Naming mixes English and Spanish (`midleware/` is intentional spelling, `bitacora`, `almacen`, `fichaje`, `nomina`, `RRHH`). Don't "fix" these — they are referenced by string in dozens of places (permission checks, log paths, namespace URLs).
- Module headers carry `__author__` / `__date__` strings on most files; preserve that style for new files in this repo.

## Common pitfalls

- **Don't bypass `execute_sql`** with raw `mysql.connector` calls — you'll lose the test-DB switching and the consistent `(flag, error, result)` shape.
- **Don't add `try/except` around `from_json` validation** — the form layer already returns 400 with field-level errors.
- **The `secrets` dict** loaded from `.env` is read once at import time in `static/constants.py`; restart the app after `.env` changes.
- **Adding a new namespace** requires both the import and `api.add_namespace(...)` in [app.py](app.py); flask-restx silently ignores routes from un-registered namespaces.
