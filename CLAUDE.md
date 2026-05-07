# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Internal Telintec back-office REST API — Flask + flask-restx — exposing endpoints under `/GUI/api/v1/<area>` for RRHH (HR), SM (material requests), Almacén (inventory), SGI, Bitácora, Dashboards, Admin/Presales, Admin/Collections, Common, Misc, and Login/UserSystem. The Flask app is consumed by separate desktop GUI clients (the repo's name is historical; this project is the API, not a GUI). MySQL is the backing store; JWT bearer tokens carry user permissions.

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
