# Envelope de respuesta `{data, msg, error}` en los endpoints de SM

Alineación de los **24 endpoints** de [`rs_SM.py`](../templates/resources/rs_SM.py)
(`/GUI/api/v1/sm/*`) al envelope `{data, msg, error}` descrito en
[`contract_crud_response_envelope.md`](contract_crud_response_envelope.md).

A diferencia del refactor de `contract`, estos endpoints son **clave para los
clientes GUI**, así que la prioridad fue **mantener compatibilidad**: el cuerpo de
**éxito** se conserva tal cual y solo se le **agrega `error`** de forma aditiva; lo
que cambiaría demasiado el éxito quedó listado en **Pendientes**. Las ramas de
**error** sí se alinearon por completo (forma fija + español + detalle en `error`).

## Las 2 capas tocadas

```
HTTP    rs_SM.py            /GUI/api/v1/sm/*  (resource: validación, marshals, passthrough)
mid     midleware/MD_SM.py  *_from_api / *_sm  (lógica de negocio y forma de respuesta)
```

La capa DB (`controllers/material_request/sm_controller.py`, etc.) y la de
validación (`*Form`) **no se tocaron**.

## Regla aplicada

| Campo | Éxito | Error |
|---|---|---|
| `data` | **valor actual intacto** (objeto/lista/string ya existente) | `[]` o `None` según el tipo que devuelve el éxito |
| `msg` | valor actual intacto (incl. `"ok"`) | texto corto en español que describe la causa |
| `error` | `None` (agregado aditivo) | detalle técnico (`error`, lista, etc.) |

- El `400` de validación de form se unificó a
  `{"data": None, "msg": "Estructura de datos inválida", "error": validator.errors}`.
- El `401` de token se dejó **exactamente** como estaba (patrón global del proyecto).
- En lecturas (GET) el éxito lleva `error: None` (y `msg: None` donde no había `msg`).

## Marshals eliminados

Se quitaron los 4 `@ns.marshal_with` del archivo porque filtraban claves y
**ocultaban errores lógicos**. Antes de quitar cada uno se verificó que la consulta
no expusiera **datetime crudo** (string↔int es aceptable; un datetime sin formatear
no lo es porque rompe/cambia la serialización JSON):

| Endpoint | Modelo retirado | Efecto al quitarlo |
|---|---|---|
| `/employees` | `client_emp_sm_response_model` | `data` deja de coaccionar a `List[List[String]]`; `employee_id` pasa de string→int. Sin fechas (verificado en `get_sm_employees`). |
| `/clients` | `client_emp_sm_response_model` | `id_customer` string→int. Sin fechas (verificado en `get_sm_clients`). |
| `/employee` | `table_sm_model` | Aparecen claves antes filtradas (p. ej. `percentage`); las fechas ya venían como string desde `get_all_sm`. |
| `/plot/<typerange>` | `request_sm_plot_data_model` | Prácticamente pass-through; sin cambio relevante de éxito. |
| `/almacen/employees` | `employees_answer_model` | Prácticamente pass-through; sin cambio relevante de éxito. |

Los `api.model(...)` siguen **definidos** en
[`api_sm_models.py`](../static/Models/api_sm_models.py) (otros archivos podrían
importarlos); solo se quitaron del bloque de imports de `rs_SM.py`.

## Bugs corregidos

- **`/add/urgent` (POST):** el resource hacía `return data, code` — devolvía el
  **payload de entrada** en vez de `data_out` del midleware. Corregido a
  `return data_out, code`.
- **`/cancel` (POST):** `cancel_sm` devolvía `(code, data_out)` pero el resource
  desempacaba `data_out, code` — **invertido y roto** (devolvía 500). Se pasó
  `cancel_sm` al orden estándar `(data_out, code)` con envelope, lo que corrige el
  bug sin tocar el resource.
- **`update_items_sm_from_api`:** devolvía `msg: "ok"` incluso cuando el code era
  `400` (algunos items fallaban). Ahora el `msg` refleja el caso
  (`"Algunos items no se pudieron actualizar"`); el éxito `200` queda idéntico.
- Mensajes de error traducidos de inglés a español en todas las ramas
  (`"error at downloading"` → `"No se pudo descargar el archivo"`, ramas S3 del
  attachment, etc.).

## Firmas de tupla invertida (intencionalmente conservadas)

`dispatch_sm` y `update_sm_from_control_table` retornan `(code, data_out)` (orden
inverso al resto). El resource ya las desempaca correctamente
(`code, data_out = ...`), así que la **firma se dejó intacta** y solo se normalizó
el **dict** que devuelven al envelope. Listas crudas de error
(`return 400, ["No item..."]`) se reemplazaron por dicts `{data, msg, error}`.

## Tabla de seguimiento (24 endpoints)

| Ruta | Métodos | Función midleware | Tratamiento | Estado |
|---|---|---|---|---|
| `/employees` | GET | `get_sm_employees` (controller) | marshal removido; `comment` eliminado; éxito `{data, msg: None, error: None}` | ✅ |
| `/clients` | GET | `get_sm_clients` (controller) | marshal removido; `comment` eliminado; éxito `{data, msg: None, error: None}` | ✅ |
| `/products/<contract>` | GET | `get_products_sm` | ramas de error con `msg`+`error` español; éxito + `msg/error: None` | ✅ |
| `/all` | GET | `get_all_sm` | passthrough; éxito + `msg/error: None` | ✅ |
| `/permission` | GET | `fetch_all_sm_with_permissions` | error `data: {}`; éxito + `msg/error: None` | ✅ |
| `/employee` | GET | `get_all_sm` | marshal `table_sm_model` removido; passthrough | ✅ |
| `/add` | POST·PUT·DELETE | `create/update/delete_sm_from_api` | validación 400 unificada; errores español; éxito: `data: {"id_sm": N}` + `msg` español-con-ID + `id_sm` hermano | ✅ |
| `/add/urgent` | POST | `create_urgent_sm_from_api` | **bug `return data` corregido**; éxito: `data: {"id_sm": N}` + `msg` español-con-ID | ✅ |
| `/cancel` | POST | `cancel_sm` | **tupla invertida/rota corregida**; éxito `msg` español-con-ID | ✅ |
| `/newclient` | POST | `create_customer` | éxito `data: {"id_customer": N}` + `msg` español-con-ID; error español | ✅ |
| `/newproduct` | POST | `create_product` | éxito `data: {"id_product": N}` + `msg` español-con-ID; error español | ✅ |
| `/plot/<typerange>` | GET | `get_data_sm_per_range` | marshal removido; éxito + `error: None` | ✅ |
| `/almacen/employees` | GET | `get_employees_almacen` | marshal removido; éxito `msg` español + `error: None` | ✅ |
| `/manage/dispatch` | POST | `dispatch_sm` | firma invertida intacta; éxito `msg` español; error lee `msg/error` del dict | ✅ |
| `/download/pdf/<sm_id>` | GET | `dowload_file_sm` | éxito = `send_file` intacto; error con envelope español | ✅ |
| `/download/excel/<sm_id>` | GET | `dowload_file_sm` | éxito = `send_file` intacto; error con envelope español | ✅ |
| `/control/table` | PUT | `update_sm_from_control_table` | firma invertida intacta; éxito `msg` español-con-ID | ✅ |
| `/control/table/all` | GET | `get_all_sm_control_table` | error `data: {}`; éxito + `msg/error: None` | ✅ |
| `/item` | PUT | `update_items_sm_from_api` | **fix `msg:"ok"` en 400**; éxito `data: {"id_sm": N}` + `msg` español; `error`=lista concisa | ✅ |
| `/folioSmAll` | GET | `get_sm_folios_from_api` | error `data: []`; éxito `msg: None, error: None` | ✅ |
| `/items/state-<state>` | GET | `get_sm_items_from_api` | error `data: []`; éxito `msg: None, error: None` | ✅ |
| `/item/inventory` | PUT | `update_sm_item_state_and_inventory` | errores español; éxito `msg` español + `error: None` | ✅ |
| `/item/stateUpdate` | POST | `update_sm_item_state` | errores español; éxito `msg` español + `error: None` | ✅ |
| `/items/bulk` | PUT | `update_items_bulk_sm_from_api` | `msg` español; clave `errors` eliminada (solo `error`) | ✅ |
| `/item/approveRequired` | POST | `update_sm_item_approve` | errores español; éxito `msg` español + `error: None` | ✅ |
| `/attachment-<id_sm>` | POST | `create_sm_attachment_api` | errores español + `error`; **éxito aplanado** (`data`=path) + `msg` español | ✅ |

## Pendientes aplicados (2026-06-24)

Tras confirmar con el dueño de la API que el front **no mapea `msg` a nada visible**
ni lee las claves `comment`/`errors`/el anidamiento de `/attachment`, se aplicaron
estos cambios (estrategia: aditivo donde rompía, limpio donde el cliente no leía):

- **`msg: "ok"` → español** en todos los éxitos de escritura (con ID donde es
  natural: `"SM creada correctamente (ID N)"`, `"Cliente creado correctamente (ID N)"`,
  etc.). En los GET `get_sm_folios_from_api` / `get_sm_items_from_api`, `msg → None`.
- **`id_sm` aditivo** en el éxito de `create_sm_from_api`,
  `create_urgent_sm_from_api`, `update_sm_from_api` y `delete_sm_from_api` (clave
  hermana de nivel superior; el cliente viejo sigue leyendo `data`/`msg`).
- **`/items/bulk`:** `msg` a español y **clave `errors` eliminada** (queda solo
  `error`). El cliente debe ramificar por código HTTP (200/207/400).
- **`comment` eliminado** de `/employees` y `/clients`; éxito limpio
  `{data, msg: None, error: None}`.
- **`/attachment` aplanado:** el éxito ahora es `{"data": <path>, "msg": <español>,
  "error": None}` (antes `data.data`). El path igual queda en BD y se obtiene al
  pedir las SM.

## `data` estructurado en escrituras (2026-06-24, lockstep)

Se migró el `data` de éxito de las escrituras de SM de **string largo de auditoría**
a **estructura ordenada con IDs**. El detalle largo se conserva **íntegro** en el log
(`write_log_file`) y en la notificación (`create_notification_permission`, que maneja
título + mensaje largo) — solo se quita de la respuesta HTTP.

| Función | `data` nuevo | `error` |
|---|---|---|
| `create_sm_from_api` | `{"id_sm": N}` | `None`, o lista de strings concisos (items/partidas) en éxito parcial |
| `create_urgent_sm_from_api` | `{"id_sm": N}` | idem |
| `update_sm_from_api` | `{"id_sm": data["id"]}` | `None` / lista concisa |
| `delete_sm_from_api` | `{"id_sm": data["id"]}` | `None` |
| `update_items_sm_from_api` | `{"id_sm": data["id_sm"]}` | `None` / lista concisa |
| `create_customer` | `{"id_customer": N}` | `None` |
| `create_product` | `{"id_product": N}` | `None` |

Detalles:
- Se **conserva** la clave `id_sm`/`id_*` hermana de nivel superior (transición;
  payload despreciable). El front puede leer `data.id_sm` o `id_sm` indistintamente.
- **Sin rollback nuevo**: los códigos siguen `201`/`200` aunque algunos items/partidas
  fallen (éxito parcial); los fallos van a `error` (lista de strings) + nota en `msg`
  (`"... N elemento(s) no se pudieron crear."`).
- `update_sm_from_api` usa `data["id"]` (canónico, igual que `update_sm_db` que hace
  `data["id"] = data["info"]["id"]`) para alinear las 4 operaciones de `/add`.
- **Ruptura**: `data` cambió de string/int → objeto. Desplegar API y clientes GUI
  juntos.

## Pendientes (siguen abiertos)

1. **Bug KPI** en `get_all_sm` (línea ~238):
   `kpi_operations = "CUMPLE" if (critical_date - critical_date).days >= 1 ...` —
   resta una fecha consigo misma, siempre `0`. **No se toca por ahora**: a futuro se
   manejará con un esquema de **KPIs configurables por el usuario** (agregar/quitar
   KPIs y definir su fórmula), así que no tiene sentido fijar una fórmula ahora. El
   KPI de almacén (`(admin_not_date - date_creation).days <= 2`) sí parece correcto y
   se deja como referencia del patrón esperado.

## Al modificar

- Mantener las **3 claves** `{data, msg, error}` en toda rama nueva (`error: None`
  en éxito).
- En **éxito** el `msg` ya es español (con ID en escritura, `None` en lectura). El
  único cambio de éxito que **falta** es sacar el string largo de `data` (ver
  Pendientes #1); no lo hagas sin coordinar el lockstep del cliente. En **error**:
  `data` vacío del tipo del éxito, `msg` corto en español, detalle en `error`.
- En escritura, exponer el id afectado como `id_sm` (clave hermana). No reusar `data`
  para el id mientras siga llevando el string de auditoría.
- No re-agregar `@ns.marshal_with` sobre estos métodos: filtra el envelope y oculta
  errores lógicos. Para documentar en swagger, usar un modelo que refleje
  `{data, msg, error}`, no el modelo del request.
- `dispatch_sm` y `update_sm_from_control_table` conservan firma `(code, data_out)`;
  respétala si las tocas.
- El `401` de token no se toca (patrón global).
- **`"error": error`, no `str(error)`** — el `error` de `execute_sql` ya es `str`; el
  `str()` redundante dispara el warning `Unnecessary str() call` de pyrefly. Reserva
  `str(...)` para el `Exception` de un `except` (`str(e)`) y para `result`
  (union-typado); en f-strings usa `f"...{error}"`.
