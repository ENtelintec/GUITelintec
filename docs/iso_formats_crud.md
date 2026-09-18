# Formatos ISO (SGI): CRUD del catálogo `iso_formats` y encabezado de los PDFs desde la BD

Fecha: 2026-09-17 · **Estado: hecho y verificado contra dev (48/48 checks HTTP + PDF real, `Tests/tester_iso_formats.py`). Sin DDL: usa `iso_formats` de [`control_saldos.sql`](../scripts_db_handle/control_saldos.sql).**

Cierra dos pendientes de [`control_saldos_cabecera.md`](control_saldos_cabecera.md): el **CRUD de SGI** sobre el catálogo (hasta hoy solo se editaba por SQL) y la **migración de `iso_form`**: los PDFs ya no leen `files/settings.json["formats"]` (retirado) sino el catálogo en BD, así que subir una revisión desde el CRUD se refleja en todos los PDFs sin tocar código.

## Reglas

| Tema | Decisión |
|---|---|
| Unicidad | `(code, revision)` es la `UNIQUE` de la tabla → **409** con el `id` existente. `code` se guarda en mayúsculas. |
| Nueva revisión | **En la misma fila**: `PUT` con `revision` nueva (+ `emission_date`); la anterior queda en `history` (`action: "Nueva revisión"`, `'R2' -> 'R3'`). Nunca una fila nueva por revisión: los ids 1..8 están atados por literal a los PDFs (`iso_form=N`) y una fila nueva los dejaría imprimiendo la revisión vieja. |
| `config` | `null` = formato solo-PDF. Con `kind: "balance_control"` se valida la estructura que consume [`MD_BalanceControl.py`](../templates/resources/midleware/MD_BalanceControl.py): `columns[{key,label,value_type,source_key?,is_sum?}]` y `header_fields[{key,label,value_type,required?,options?}]`, llaves únicas (regex `^[a-z][a-z0-9_]{0,49}$`), sin repetirse entre ambas listas, `value_type` ∈ `text|number|date|boolean`, `options` solo en `header_fields`. Otros `kind` se guardan tal cual. |
| `config` y controles existentes | Quitar el `config` (`null`) a un formato que usan controles de saldos → **400**. Cambiarlo sí se permite, con `warnings` en la respuesta: los valores ya capturados en llaves que desaparecen no se migran (quedan en `extra_info`). |
| Baja suave | `PUT /format/status` `is_active: 0`. El formato deja de ofrecerse para controles nuevos (`GET /balanceControl/catalogs` solo lista activos) y **los PDFs y los controles existentes lo siguen imprimiendo**. Reactivable. |
| Borrado físico | `DELETE` solo si **ningún** control de saldos lo referencia (la FK es `RESTRICT`) y el id **no está atado a un PDF** (`ISO_FORM_IDS_IN_CODE` = 1..8). Si no, 400 con `usage`. |
| Permisos | Lecturas `sgi` + `administracion` (el catálogo lo consumen saldos). Escrituras **solo `sgi`**, dueño del catálogo. |
| `department` | Catálogo cerrado: `rrhh, almacen, presales, sgi, administracion, cda, sm, compras` (o `null`). |

## PDFs: `Codigo:` e `I. Vigencia:` desde la BD

`create_header_telintec` / `create_header_materials` en [`PDFGenerator.py`](../templates/forms/PDFGenerator.py) ahora llaman a `iso_format_header(iso_form)` → `("FO-ALM-01 R1", "2024-06-14")`.

- Lee `id, code, revision, emission_date` de **todos** los formatos (activos o no) vía `get_iso_format_headers` y los guarda en un **caché de módulo con TTL de 5 min**; el CRUD lo invalida en cada escritura (`invalidate_iso_formats_cache`).
- Con la BD caída reusa la última lectura buena, y si no hay ninguna imprime el encabezado en blanco (el PDF sale igual) y lo anota en `files/logs/sgi_formats`. Antes un `KeyError` en `settings.json` tumbaba el PDF.
- Id inexistente o no numérico → `("", "")`.
- **Excepción deliberada** a "los forms no tocan la BD": `create_header_*` no recibe `data_token` (12 call sites en `templates/forms/`), así que la lectura va sin token, a la BD del environment. Consecuencia: un tester (`is_tester`) ve el catálogo de dev en el encabezado, no el de test. Aceptable: es un dato de catálogo idéntico en las 3 BDs.
- `files/settings.json["formats"]` **retirado** (era la única lectura). La fecha del id 2 venía como `06-03-2025`; en BD ya está normalizada a `2025-03-06`.

## Las capas tocadas

```
controller  sgi/iso_formats_controller.py (nuevo)   get_iso_formats_filtered · get_iso_format_by_code_rev · insert/update/delete_iso_format
                                                    set_iso_format_active · count_balance_controls_by_format · get_iso_format_headers
                                                    (reusa FORMAT_COLUMNS / get_iso_formats / get_iso_format_by_id de purchases/balance_control_controller.py)
midleware   MD_IsoFormats.py (nuevo)                 validate_format_config · *_from_api (7) — reusa _format_to_dict / coerce_value / VALUE_TYPES de MD_BalanceControl
models      api_sgi_models.py                        iso_format_{post,put,status,delete}_model + IsoFormat{Post,Put,Status,Delete}Form
routes      rs_SGI.py                                GET /formats · GET /formats/catalogs · POST/PUT/DELETE /format · PUT /format/status · GET /format/<id>
forms       PDFGenerator.py                          ISO_FORM_IDS_IN_CODE · iso_format_header · invalidate_iso_formats_cache (settings.json fuera)
constants   static/constants.py                      log_file_sgi_formats
files       files/settings.json                      bloque "formats" retirado
```

`config` viaja por `ns.payload` crudo (WTForms no modela dicts, mismo criterio que `template`/`rubric` en [`quizz_models_crud.md`](quizz_models_crud.md)); los forms validan los escalares. `is_active` va sin `InputRequired` (trata `0` como vacío), `AnyOf([0,1])` rechaza `None`.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Lecturas `sgi`/`administracion`; escrituras `sgi`.
- **Base**: `/GUI/api/v1/sgi`.
- **Respuesta**: siempre `{data, msg, error}`; en 400 de validación `error` es **lista** de strings (del form: objeto `{campo: [msgs]}`).

| Método y ruta | Body / query | Éxito |
|---|---|---|
| `GET /formats` | `?all=1` (incluye retirados) · `?department=almacen` · `?kind=balance_control` | `200` `data: [formato]` ordenados por `id` |
| `GET /formats/catalogs` | — | `200` `{departments, value_types, kinds, ids_bound_to_pdf: [1..8], config_schema}` |
| `GET /format/<id>` | — | `200` formato + `usage: {balance_controls, balance_controls_active, bound_to_pdf}` · `404` |
| `POST /format` | `{code*, revision?="R0", name*, department?, emission_date?, config?}` | `201` `data: {id, label}` · `409` duplicado (`data.id` del existente) |
| `PUT /format` | `{id*, ...solo las llaves a cambiar}` — `config` reemplaza completo, `null` lo quita | `200` `data: {id, label, changes: [{field, before, after}], warnings: []}` · `200` "Sin cambios" · `409` · `400` |
| `PUT /format/status` | `{id*, is_active*: 0\|1, comment?}` | `200` `data: {id, is_active, usage}` (idempotente) |
| `DELETE /format` | `{id*}` | `200` · `400` si tiene controles o está atado a un PDF (`data.usage` dice cuál) · `404` |

Objeto **formato** (igual en lista y detalle):

```json
{"id": 9, "code": "FO-CXC-07", "revision": "R2", "label": "FO-CXC-07 R2", "name": "Control Saldo",
 "department": "administracion", "emission_date": "2025-05-29", "is_active": 1,
 "config": {"kind": "balance_control", "columns": [...], "header_fields": []},
 "history": [{"user": 9999, "action": "Nueva revisión", "date": "...", "comment": "revision: 'R1' -> 'R2'; emission_date: ..."}],
 "created_by": null, "timestamp": "2026-09-11 12:00:00"}
```

Ejemplos de error: `400` `error: ["config.columns[0].value_type debe ser uno de ['text', 'number', 'date', 'boolean']", "config.header_fields[1].key repetida: 'site'"]` · `400` `error: ["no se puede quitar el config: 2 control(es) de saldos usan este formato"]` · `409` `msg: "Ya existe el formato FO-CXC-12 R0 (ID 14)"`.

### Gotchas

- Para la pantalla de saldos el catálogo sigue siendo `GET /admin/collections/balanceControl/catalogs` (solo activos, con `kind: balance_control`); estas rutas son la **administración** del catálogo.
- `ids_bound_to_pdf` sirve para deshabilitar el botón de borrar en la UI; retirar sí se puede.
- Tras editar un formato, los PDFs lo reflejan de inmediato en este proceso (el CRUD invalida el caché) y en ≤ 5 min en otro worker.

## Al modificar

- **PDF nuevo con formato ISO**: fila en `iso_formats` (por el CRUD) y su `id` en `ISO_FORM_IDS_IN_CODE` de `PDFGenerator.py` para protegerlo del borrado.
- **`kind` nuevo con config estructurada**: rama en `validate_format_config` y en `KINDS`.
- **Departamento nuevo**: `DEPARTMENTS` en `MD_IsoFormats.py` (el catálogo lo expone solo).
- Las lecturas por id/lista **siguen en** `purchases/balance_control_controller.py` (`FORMAT_COLUMNS` append-only); el controller de SGI las re-exporta, no las duplica.

## Pendientes

- **[front]** Pantalla de SGI para el catálogo (lista con filtro `all`, alta, edición/revisión, retirar/reactivar, borrar solo si `usage` lo permite).
- **[back]** Al subir revisión de un formato de saldos, versionar el `config` (hoy el `history` guarda el diff escalar y "config actualizado", no el `config` anterior completo).
