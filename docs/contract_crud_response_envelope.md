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
| `/rrhh/employee` | POST · PUT · DELETE | `create_new_employee_db / update_employee_db` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee/terminate` | DELETE | `terminate_employee_from_api` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employees/info/<status>` | GET | `get_info_employees_with_status` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee/info/<id_emp>` | GET | `get_info_employee_id` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee/medical/<id_emp>` | GET | `fetch_medical_employee` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employees/medical/all` | GET | `fetch_medicals` (marshal_with eliminado) | ✅ Hecho | 2026-06-23 |
| `/rrhh/medical/employes/less` | GET | `fetch_employees_without_records` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee/medical` | POST · PUT · DELETE | `insert_medical_db / update_medical_db` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employees/vacations/all` | GET | `get_all_vacations` (marshal_with eliminado; datetime fix) | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee/vacations/<id_emp>` | GET | `get_vacations_employee` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee/vacation` | POST · PUT · DELETE | `insert_new_vacation / update_vacation` | ✅ Hecho | 2026-06-23 |
| `/rrhh/quizzes` | GET | `get_all_quizzes` | ✅ Hecho | 2026-06-23 |
| `/rrhh/employees/fichaje/all` | GET | `fetch_fichajes_all_employees` (marshal_with eliminado) | ✅ Hecho | 2026-06-23 |
| `/rrhh/employee/fichaje/<id_emp>` | GET | `fetch_fichaje_employee` | ✅ Hecho | 2026-06-23 |
| `/rrhh/payroll/files/update` | POST | `create_payroll_file_attachment_api` | ✅ Hecho | 2026-06-23 |
| `/rrhh/payroll/mail` | POST | `create_mail_payroll` | ✅ Hecho | 2026-06-23 |
| `/rrhh/payroll/files/list/<emp_id>` | GET | `get_files_list_nomina_RH` (clave `data_raw` → `data`) | ✅ Hecho | 2026-06-23 |
| `/rrhh/payroll/data/update` | PUT | `update_data_employee` | ✅ Hecho | 2026-06-23 |
| `/rrhh/payroll/update/employees` | GET | `update_payroll_list_employees` | ✅ Hecho | 2026-06-23 |
| `/rrhh/fichajes/files` | GET | `get_files_fichaje` (marshal_with eliminado) | ✅ Hecho | 2026-06-23 |
| `/rrhh/fichajes/data/fromfiles` | POST | `get_fichaje_data` (marshal_with eliminado; timestamps serializados) | ✅ Hecho | 2026-06-23 |
| `/rrhh/upload/fichaje/file` | POST | — (códigos 401 → 400 corregidos) | ✅ Hecho | 2026-06-23 |
| `/admin/db/clients/allClients` | GET | `get_all_clients_data` | ✅ Hecho | 2026-06-23 |
| `/admin/db/client` | POST · PUT · DELETE | `insert/update/delete_customer` | ✅ Hecho | 2026-06-23 |
| `/admin/db/suppliers/allSuppliers` | GET | `get_all_suppliers_data` | ✅ Hecho | 2026-06-23 |
| `/admin/db/suppliers/items-<id>` | GET | `get_items_supplier_name` | ✅ Hecho | 2026-06-23 |
| `/admin/db/supplier` | POST · PUT · DELETE | `insert/update/delete_supplier` | ✅ Hecho | 2026-06-23 |
| `/admin/db/extraInfoSupplier` | POST | `update_extra_info_supplier` | ✅ Hecho | 2026-06-23 |
| `/admin/db/heads` | GET | `fetch_heads_main` | ✅ Hecho | 2026-06-23 |
| `/admin/db/heads/<id_d>` | GET | `fetch_heads` | ✅ Hecho | 2026-06-23 |
| `/admin/db/head` | POST · PUT · DELETE | `insert/update/delete_head_from_api` | ✅ Hecho | 2026-06-23 |
| `/admin/db/suppliers/items/file` | POST | `items_supplier_from_file` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/orders/<status>` | GET | `fetch_purchase_orders` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/application/orders/<status>` | GET | `fetch_pos_applications` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/application/orderstoApprove` | GET | `fetch_pos_applications_to_approve` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/application/order` | POST · PUT · DELETE | `create/update/cancel_po_application_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/order` | POST · PUT · DELETE | `create/update/cancel_purchase_order_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/order/status` | PUT | `change_state_order_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/application/order/status` | PUT | `change_state_po_application_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/POItemsFoDelivery` | GET | `fetch_po_item_sm_item_id` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/APOItemsFastOrder` | GET | `get_items_with_fast_order` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/purchase/folio/<folio>` | GET | `generate_folios_po` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/activity/quotation` | POST · PUT · DELETE | `create/update/delete_quotation_activity_from_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/activity/quotations-<id>` | GET | `get_quotations_from_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/activity/ChangeStatus` | PUT | `update_quotation_activity_from_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/remission` | POST · PUT · DELETE | `create/update/delete_remission_from_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/remissionControlTable` | POST · PUT | `create/update_remission_control_table_from_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/remission-<id>` | GET | `get_remission_from_api` | ✅ Hecho | 2026-06-23 |
| `/admin/collections/remission/attachment-<id>` | POST | `create_activity_report_attachment_api` (passthrough) | ✅ Hecho | 2026-06-23 |
| `/admin/collections/voucher/vehicle/attachment/download` | POST | `download_report_activity_attachment_api` (error branches) | ✅ Hecho | 2026-06-23 |
| `/admin/collections/purchase/download/pdf/<id>` | GET | `dowload_file_purchase` (error branches) | ✅ Hecho | 2026-06-23 |
| `/admin/collections/purchase/download/pdfItemsPurchaseStorage` | GET | `download_file_purchase_item_approved` (error branches) | ✅ Hecho | 2026-06-23 |
| `/common/payroll/employee/<emp_id>` | GET | `get_files_list_nomina` (orden normalizado; error check añadido) | ✅ Hecho | 2026-06-23 |
| `/common/payroll/employee/file` | POST | `download_nomina_docs` (error branches; passthrough en resource) | ✅ Hecho | 2026-06-23 |
| `/common/vacations/events` | GET | `get_all_vacations_data_date` (shapes de error unificados) | ✅ Hecho | 2026-06-23 |
| `/dashboard/inventory/movements` | POST | `get_data_chart_movements` (bug 400→401 en token; passthrough) | ✅ Hecho | 2026-06-23 |
| `/dashboard/inventory/sm/<range>/<type>` | GET | `get_data_chart_sm` (passthrough) | ✅ Hecho | 2026-06-23 |
| `/dashboard/fichaje/emp` | POST | `get_data_chart_fichaje_emp` (passthrough) | ✅ Hecho | 2026-06-23 |
| `/dashboard/notifications/medicals` | GET | — (solo resource; `data: null, error: null` en todos los estados) | ✅ Hecho | 2026-06-23 |
| `/UserSystem/usernames-<status>` | GET | `fectchUsersDBApi` (bug `{data: []}` → `{"data": None}`; `error: ""` → `None`) | ✅ Hecho | 2026-06-24 |
| `/UserSystem/update-biocredentials` | POST | `update_biocredentials_from_api` (`error: ""` → `None`; `data: [result]` → `None`) | ✅ Hecho | 2026-06-24 |
| `/UserSystem/user` | POST | `create_employee_user_from_api` (`data: [id]` → `{"id_user": id}`; `error: ""` → `None`) | ✅ Hecho | 2026-06-24 |
| `/UserSystem/permissions` | GET | `fetch_permissions_from_api` (`error: ""` → `None`) | ✅ Hecho | 2026-06-24 |
| `/misc/notifications/employee/<id>&<status>` | GET | `get_all_notification_db_user_status` (orden normalizado; `@marshal_with` removido) | ✅ Hecho | 2026-06-24 |
| `/misc/notifications/all/<status>` | GET | `get_all_notification_db_permission` (orden normalizado; `@marshal_with` removido) | ✅ Hecho | 2026-06-24 |
| `/misc/notification` | POST · PUT | `create_notification_from_api` / `update_notification_status_from_api` (Functions_midleware_misc.py; arquitectura alineada) | ✅ Hecho | 2026-06-24 |
| `/misc/download/gui/settings` | GET | — (try/except mantenido; mensaje y shape de error corregidos) | ✅ Hecho | 2026-06-24 |
| `/misc/AV/response` | POST | — (solo error branches; éxito `{answer, files, id}` intacto; `@marshal_with` removido) | ✅ Hecho | 2026-06-24 |
| `/misc/AV/files/<department>` | GET | — (solo error branches; éxito `{files}` intacto; `@marshal_with` removido) | ✅ Hecho | 2026-06-24 |
| `/misc/task/quizz` | POST · PUT · DELETE | `create/update/delete_task_from_api` (`msg: "Ok"` en error corregido; `data` y `error` alineados) | ✅ Hecho | 2026-06-24 |
| `/misc/task/<emp_id>` | GET | `get_task_by_id_employee` (passthrough; shapes de error unificados) | ✅ Hecho | 2026-06-24 |
| `/misc/download/quizz/<type_q>` | GET | — (try/except; `error: null` en éxito; shape de error corregido) | ✅ Hecho | 2026-06-24 |
| `/misc/dashboard` | GET | `get_all_dashboard_data` (passthrough; shapes de error unificados) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/tools` | POST · PUT · DELETE | `create/update/delete_voucher_tools_api` (éxito parcial items; rollback total; `errors`→`error`; español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/toolsState` | PUT | `update_status_tools` (structured `data`; español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/safety` | POST · PUT · DELETE | `create/update/delete_voucher_safety_api` (éxito parcial items; rollback total; español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/safetyState` | PUT | `update_status_safety` (structured `data`; español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/tools/<date>` | GET | `get_vouchers_tools_api` (`msg: null, error: null` en éxito; español en errores) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/safety/<date>` | GET | `get_vouchers_safety_api` (`msg: null, error: null` en éxito; español en errores) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/vehicle/<date>` | GET | `get_vouchers_vehicle_api` (`msg: null, error: null` en éxito; español en errores) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/vehicle` | POST · PUT · DELETE | `create/update/delete_voucher_vehicle_api` (éxito parcial items; rollback total; structured `data`; español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/vehicle/attachment-<id>` | POST | `create_voucher_vehicle_attachment_api` (passthrough; `error` en todas las ramas S3; español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/vehicle/attachment/download` | POST | `download_voucher_vehicle_attachment_api` (success=`send_file` intacto; error branches con `error` y español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/epp/attachment-<id>` | POST | `create_voucher_epp_attachment_api` (passthrough; `error` en todas las ramas; español) | ✅ Hecho | 2026-06-24 |
| `/sgi/voucher/tools/attachment-<id>` | POST | `create_voucher_tools_attachment_api` (passthrough; `error` en todas las ramas; español) | ✅ Hecho | 2026-06-24 |

## Bugs datetime GET /rrhh (2026-06-23)

Tres bugs de serialización detectados en los GET de RRHH:

| Función | Archivo | Bug | Fix |
|---|---|---|---|
| `get_info_employee_id` | `Functions_DB_midleware.py` | `admission.strftime()` y `birthday.strftime()` sin guardia de `None` → `AttributeError` | Guard `if field is None or isinstance(field, str) else field.strftime(...)` |
| `get_vacations_employee` | `Functions_DB_midleware.py` | `result[3].strftime()` (date_admission) sin guardia de `None` | Mismo patrón |
| `fetch_medical_employee` | `Functions_midleware_RRHH.py` | Desempaqueta 8 campos; `get_all_examenes` devuelve 9 (`extra_info` añadido a la query) → `ValueError` | Añadir `_extra` al unpack |

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
