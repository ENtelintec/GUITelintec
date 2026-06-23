# Envelope de respuesta unificado en el CRUD de `contract` y `quotation`

Los endpoints de escritura de contratos (`POST`/`PUT`/`DELETE` en
[`rs_Admin_presales.py`](../templates/resources/rs_Admin_presales.py), ruta
`/admin/presales/contract`) y los hermanos de cotización (ruta `/quotation`)
devolvían respuestas con **claves inconsistentes**, mezcla de español/inglés y
varios bugs (un `set` literal no serializable, `msg` con listas dentro,
ternarios de rollback con la condición invertida). Este documento describe el
estado tras alinearlos.

## Las 2 capas tocadas

```
HTTP    rs_Admin_presales.py  /contract, /quotation (post/put/delete)
mid     Functions_midleware_admin.py  create/update/delete_(contract|quotation)_from_api
```

La capa DB (`create_contract`, `update_contract`, `delete_contract`,
`create_quotation`, ...) **no se tocó**. La capa de validación (`*Form`) tampoco.

## Envelope unificado

Todas las operaciones devuelven **siempre** las tres claves, en éxito y en error:

```json
{ "data": <obj|null>, "msg": "<texto humano en español>", "error": <detalle|null> }
```

- `error` está **siempre presente**: `null` en éxito, detalle técnico (string o
  lista) en fallo. El front puede chequear `if error != null` de forma
  predecible, leyendo el detalle por separado de `msg`.
- `msg` es conciso, en español y orientado al usuario, **con el ID** de la
  entidad afectada: `"Contrato creado correctamente (ID 123)"`.
- `data` en éxito lleva los IDs de forma estructurada (no la lista cruda de items
  como antes):
  - create/update contrato → `{"id_contract": …, "id_quotation": …}`
  - create/update/delete cotización → `{"id_quotation": …}`
  - delete contrato → `{"id_contract": …}`
- `data` en error es `null`.

El detalle largo (conteo de items, empleado, IDs intermedios) sigue yendo **solo**
a `write_log_file` y `create_notification_permission` — no contamina el `msg` de
la respuesta HTTP.

### Códigos

| Operación | Éxito | Validación form | Negocio/DB |
|---|---|---|---|
| create | `201` | `400` | `400` |
| update | `200` | `400` | `400` |
| delete | `200` | `400` | `400` |

El `400` de validación de la capa resource también se alineó:
`{"data": null, "msg": "Estructura de datos inválida", "error": validator.errors}`
(los errores de campo van en `error`, su lugar natural). El `401` de token
**no** se tocó (usa el patrón común a todo el proyecto).

## Éxito parcial (algunos items fallan)

Cuando **algunos** items de la cotización fallan pero la entidad principal sí se
creó/actualizó, la operación sigue contando como éxito (`201`/`200`) pero se
refleja de forma coherente:

- `msg` → `"Contrato creado correctamente (ID 123). N items no se pudieron crear."`
- `error` → lista de los errores de esos items (no `null`).

Si fallan **todos** los items, se revierte (contrato y/o cotización se borran) y
se devuelve `400` con `data: null` y `error` con la lista de errores.

## Lecturas (GET)

Los endpoints de lectura usan el **mismo** envelope `{data, msg, error}` con dos
matices propios:

- **En éxito:** `msg: null` y `error: null` (no hay acción que reportar; la data
  habla por sí sola). `data` es la lista/objeto como hoy.
- **En error (4xx):** `data` vacío **del tipo que devuelve el éxito** — `[]` para
  endpoints que devuelven lista, `null` para los que devuelven un objeto — para
  que un cliente que itera `data` sin chequear el código no truene. `msg` describe
  la causa en español y `error` lleva el detalle técnico.
- **Sin cambio de semántica de status**: no se agregó `404`; un id inexistente
  sigue devolviendo `200` con lista (posiblemente vacía). Solo se alineó la forma.
- **`marshal_with`**: se quitó `@ns.marshal_with(answer_contract_model)` del GET
  `/contract/<id_c>` (y su import) — filtraba la clave `error` y reformateaba el
  `data` de los errores contra `contract_model`.
- **Helpers compartidos** (`get_iddentifiers`,
  `get_iddentifiers_creation_contracts`): **no se tocaron**; su salida se
  **envuelve** en el envelope dentro de `folio_from_department` y
  `fetch_products_contracts` (el mensaje del helper va a `error`).

## Bugs corregidos (además de los mensajes)

- **`set` literal no serializable**: `{"data": {result_list}}` (en
  `create_quotation_from_api` y `create_contract_from_api`) construía un `set`
  con una lista dentro → `TypeError` al serializar a JSON. Eliminado.
- **`data` anidado**: `{"data": {"data": result_list}}` en
  `update_quoation_from_api`. Eliminado.
- **`msg` con lista**: `update_contract_from_api` devolvía
  `{"data": result, "error": error_list, "msg": result_list}` — `msg` era una
  **lista**, no texto. Corregido a string conciso.
- **Ternario de rollback invertido**: `str(result_q)+" "+str(result_c) if not flag
  else "Cotización no creada"` — el `flag` venía del último `delete_contract`, así
  que el texto "Cotización no creada" salía cuando el borrado **sí** tuvo éxito.
  Reemplazado por mensajes fijos coherentes.
- **Textos en inglés**: `"Ok"`, `"Error at structure"`, `"Not posible to create
  contract"`, `"Items cant be erased"`, `"Quoation unable to be deleted"` →
  español.
- **`@ns.marshal_with(quotation_model_delete)`** sobraba en el `delete` de
  `/quotation`: `quotation_model_delete` es el modelo del *request* (`{id}`), así
  que marshalear la respuesta contra él la filtraba a basura. Decorador eliminado
  (y su import, ya sin uso).

## Endpoints alineados al envelope (seguimiento)

Lista viva de los endpoints migrados al envelope `{data, msg, error}`. Al alinear
uno nuevo con este patrón, agrégalo aquí.

| Ruta | Métodos | Archivo midleware | Estado | Fecha |
|---|---|---|---|---|
| `/admin/presales/contract` | POST · PUT · DELETE | `create/update/delete_contract_from_api` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/quotation` | POST · PUT · DELETE | `create/update/delete_quotation_from_api` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/quotation/<id_q>` | GET | `get_quotations` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/contract/<id_c>` | GET | `get_contracts` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/contracts/products` | GET | `get_contractsWithItems` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/folio/ternium` | GET | `get_folio_from_contract_ternium` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/folio/cotfc` | GET | `folio_from_department` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/contracts/abreviations` | GET | `get_contracts_abreviations` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/products/contracts` | GET | `fetch_products_contracts` | ✅ Hecho | 2026-06-22 |
| `/admin/presales/contract/settings` | POST | `modify_pattern_phrase_contract_pdf` | ✅ Hecho | 2026-06-23 |
| `/admin/presales/quotation/products/upload` | POST | `products_quotation_from_file` | ✅ Hecho | 2026-06-23 |
| `/admin/presales/contract/review/products/upload` | POST | `products_contract_from_file` | ✅ Hecho | 2026-06-23 |
| `/admin/presales/quotation/items/file` | POST | `items_quotation_from_file` | ✅ Hecho | 2026-06-23 |
| `/admin/presales/contract/items/file` | POST | `items_contract_from_file` | ✅ Hecho | 2026-06-23 |
| `/admin/presales/compare` | POST | `compare_file_and_quotation` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee` | POST · PUT · DELETE | `create_new_employee_db / update_employee_db` | ⬜ Pendiente | — |
| `/rrhh/employee/terminate` | DELETE | `terminate_employee_from_api` | ⬜ Pendiente | — |
| `/rrhh/employees/info/<status>` | GET | `get_info_employees_with_status` | ⬜ Pendiente | — |
| `/rrhh/employee/info/<id_emp>` | GET | `get_info_employee_id` | ⬜ Pendiente | — |
| `/rrhh/employee/medical/<id_emp>` | GET | `fetch_medical_employee` | ⬜ Pendiente | — |
| `/rrhh/employees/medical/all` | GET | `fetch_medicals` (quitar `marshal_with`) | ⬜ Pendiente | — |
| `/rrhh/medical/employes/less` | GET | `fetch_employees_without_records` | ⬜ Pendiente | — |
| `/rrhh/employee/medical` | POST · PUT · DELETE | `insert_medical_db / update_medical_db` | ⬜ Pendiente | — |
| `/rrhh/employees/vacations/all` | GET | `get_all_vacations` (quitar `marshal_with`) | ⬜ Pendiente | — |
| `/rrhh/employee/vacations/<id_emp>` | GET | `get_vacations_employee` | ⬜ Pendiente | — |
| `/rrhh/employee/vacation` | POST · PUT · DELETE | `insert_new_vacation / update_vacation` | ⬜ Pendiente | — |
| `/rrhh/quizzes` | GET | `get_all_quizzes` | ⬜ Pendiente | — |
| `/rrhh/employees/fichaje/all` | GET | `fetch_fichajes_all_employees` (quitar `marshal_with`) | ⬜ Pendiente | — |
| `/rrhh/employee/fichaje/<id_emp>` | GET | `fetch_fichaje_employee` | ⬜ Pendiente | — |
| `/rrhh/payroll/files/update` | POST | `create_payroll_file_attachment_api` | ⬜ Pendiente | — |
| `/rrhh/payroll/mail` | POST | `create_mail_payroll` | ⬜ Pendiente | — |
| `/rrhh/payroll/files/list/<emp_id>` | GET | `get_files_list_nomina_RH` (clave `data_raw` → `data`) | ⬜ Pendiente | — |
| `/rrhh/payroll/data/update` | PUT | `update_data_employee` | ⬜ Pendiente | — |
| `/rrhh/payroll/update/employees` | GET | `update_payroll_list_employees` | ⬜ Pendiente | — |
| `/rrhh/fichajes/files` | GET | `get_files_fichaje` (quitar `marshal_with`) | ⬜ Pendiente | — |
| `/rrhh/fichajes/data/fromfiles` | POST | `get_fichaje_data` (`msg` con lista → `error`; quitar `marshal_with`) | ⬜ Pendiente | — |
| `/rrhh/upload/fichaje/file` | POST | — (códigos 401 erróneos → 400) | ⬜ Pendiente | — |

## Patrón reutilizable (para aplicar a otros endpoints)

Esta es la receta para alinear **cualquier** endpoint de escritura al mismo
estilo. Copia las plantillas y ajusta nombres.

### Regla de oro del envelope

| Campo | Éxito | Error |
|---|---|---|
| `data` | objeto con IDs estructurados (`{"id_<entidad>": …}`) | `null` |
| `msg` | texto corto, español, con ID: `"<Entidad> <acción> correctamente (ID N)"` | texto corto que describe la causa |
| `error` | `null` (o lista de errores si hubo éxito parcial) | detalle técnico (`str(error)` o lista) |

Códigos: `201` create, `200` update/delete, `400` validación y negocio/DB.
El `401` de token se deja como está (patrón global del proyecto).

### Plantilla — capa resource (`rs_<area>.py`)

```python
@ns.expect(expected_headers_per, <modelo_request>)
def post(self):  # o put / delete
    flag, data_token, msg = token_verification_procedure(request, department="<dep>")
    if not flag:
        return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
    # noinspection PyUnresolvedReferences
    validator = <Entidad><Accion>Form.from_json(ns.payload)  # pyrefly: ignore
    if not validator.validate():
        return {"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}, 400
    data = validator.data
    data_out, code = <accion>_<entidad>_from_api(data, data_token)
    return data_out, code
```

No agregar `@ns.marshal_with(...)` sobre estos métodos: marshalea/filtra el
envelope y rompe `msg`/`error`. (Si se quiere documentar la respuesta en swagger,
crear un `api.model` que refleje `{data, msg, error}` y usarlo, no el modelo del
request.)

### Plantilla — capa midleware (`*_from_api`)

```python
def <accion>_<entidad>_from_api(data, data_token):
    flag, error, result = <operacion_db>(...)        # capa controllers/DB
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo <accion> <entidad>",   # causa, corta, español
            "error": str(error),                      # detalle técnico
        }, 400
    # auditoría: detalle largo SOLO al log y la notificación, nunca al msg de salida
    msg = f"<Entidad> <accion> con ID-{result} por el empleado {data_token.get('name')}"
    create_notification_permission(msg, data_token, ["<dep>"], "<Titulo>", data_token.get("emp_id"), 0)
    write_log_file(<log_file_area>, msg, data_token)
    return {
        "data": {"id_<entidad>": result},
        "msg": f"<Entidad> <accion> correctamente (ID {result})",
        "error": None,
    }, 201  # 200 para update/delete
```

### Patrón de éxito parcial (operaciones con lista de sub-items)

Cuando una operación procesa una lista (p. ej. items) y el resultado viene como
`flag_list, error_list, result_list`:

```python
error_items = None
if flag_list.count(True) == len(flag_list):
    pass                                          # todo bien
elif flag_list.count(False) == len(flag_list):
    <revertir entidad principal>                  # rollback
    return {"data": None, "msg": "No se pudo <accion> ningún item; revertido",
            "error": error_list}, 400
else:
    error_items = [e for f, e in zip(flag_list, error_list) if not f]

# ... operación principal exitosa ...
msg_out = f"<Entidad> <accion> correctamente (ID {id_})"
if error_items is not None:
    msg_out += f". {len(error_items)} items no se pudieron <accion>."
return {"data": {"id_<entidad>": id_}, "msg": msg_out, "error": error_items}, 201
```

La operación principal cuenta como éxito (`201`/`200`) aunque algunos sub-items
fallen; el front detecta el problema con `error != null`.

## Al modificar

- Mantener el envelope `{data, msg, error}` en las **tres** claves siempre. Si
  agregas un caso de retorno, incluye `error` (`null` en éxito).
- El `msg` de la respuesta HTTP es para el usuario: corto, español, con ID. El
  detalle técnico va en `error`; el detalle largo de auditoría va al log y la
  notificación, no al `msg`.
- `data` en éxito expone IDs estructurados (`id_contract`/`id_quotation`), no la
  lista cruda de items.
- El `/quotation` quedó alineado junto con `/contract`. Si tocas uno, mantén el
  otro consistente.
- Todos los endpoints de `admin/presales` están alineados al envelope, incluyendo
  los de carga de archivo y `/contract/settings`.
