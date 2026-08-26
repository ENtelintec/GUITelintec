# Control de Reportes: permiso operaciones + campos propios del bloque administración

Atiende la solicitud del front (`llaves-pendientes-control-reportes.md`, 2026-08-25) sobre
`PUT /GUI/api/v1/admin/collections/remissionControlTable`, revisada contra
[`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md) y
[`remission_balance_get_filters_campos_nuevos.md`](remission_balance_get_filters_campos_nuevos.md).
Tres cambios (decididos en grill 2026-08-26):

1. **Permiso `operaciones`** en `POST`/`PUT /remissionControlTable` **y** en `GET /remission-<id>`.
   Los líderes de operaciones (permiso `App.Department.Operaciones`) son quienes **capturan la
   remisión por primera vez** desde control table, y el matching por substring de
   `verify_department_permission` no encontraba `administracion`/`purchases` en su permiso → 401 al
   guardar. El GET también se abrió (el front afirmaba que "la pantalla carga por otra ruta", pero
   ninguna ruta de remisiones de este repo aceptaba `operaciones`; quien edita necesita leer el
   aplanado). El "control por bloque" que el front dejaba como pendiente se **descartó como no-tema**:
   operaciones no es un bloque de llaves sino el departamento de captura inicial; ambos departamentos
   comparten escritura sobre el endpoint.
2. **`total_sin_iva_admi`** (float): total sin IVA del bloque administración, **campo propio, no
   alias** de `total_sin_iva` (que captura operaciones vía `totalSinIva`). Antes ambos bloques
   escribían la misma llave y ganaba el último guardado.
3. **`remission_sent_date_client`** (string): fecha de envío de la remisión **al cliente**, campo
   propio independiente de `remission_sent_date` (fecha en que líderes envió la remisión, compartida
   por los 3 módulos). Mismo precedente que `ot_ticket`/`centro_costos`/`personal_infra`: **el back
   no sincroniza duplicados conceptuales** — si el front quiere consistencia, la arma él.

Ambos campos siguen la receta completa de 5 lugares (no la versión de 3 que proponía el front, que
omitía el espejo `api.model`): form + `api.model` + `_CONTROL_EXTRA_KEY_MAP` + `_GET_EXTRA_*_FIELDS` +
`_HISTORY_EXTRA_FIELDS` (y `_HISTORY_NUMERIC_FIELDS` para el float). Solo el módulo Control de
Reportes los escribe; remisiones y saldos no los tienen en sus mapas y por el merge por módulo jamás
los pisan.

## Capas tocadas

1. **HTTP** — [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py):
   `"operaciones"` agregado a las listas de `department` de `POST`/`PUT /remissionControlTable` y
   `GET /remission-<id>`.
2. **Orquestación** — [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py):
   las 2 llaves en `_CONTROL_EXTRA_KEY_MAP` (payload = canónico, snake_case),
   `total_sin_iva_admi` en `_GET_EXTRA_NUMERIC_FIELDS` + `_HISTORY_NUMERIC_FIELDS`,
   `remission_sent_date_client` en `_GET_EXTRA_STRING_FIELDS`, ambas en `_HISTORY_EXTRA_FIELDS`.
3. **DB** — sin cambios de esquema ni de controllers (todo va al JSON `extra_info` existente).
4. **Validación/swagger** — [`api_purchases_models.py`](../static/Models/api_purchases_models.py):
   los 2 campos opcionales en `MetadataControlTableRemissionForm` (los hereda el update form) y en
   `basic_control_table_report_model`.

## Bug corregido de paso

`DELETE /remission` devolvía `400` ("Error al obtener ítems del reporte") para **cualquier remisión
sin items** — justo lo que crea `POST /remissionControlTable`, que no maneja items: el guard de
`delete_remission_from_api` trataba la lista vacía como error en vez de saltarse el borrado de items
(misma clase de guard sobrante que se quitó en la QA,
[`quotation_activity_upsert_null_fix.md`](quotation_activity_upsert_null_fix.md)). Ahora una remisión
sin items se borra igual (el loop vacío no hace nada y se pasa directo al delete de la fila).

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (NO `Bearer <token>`).
- **Base**: `/GUI/api/v1/admin/collections`. Permisos: `administracion`, `purchases` **o ahora
  `operaciones`** en `POST`/`PUT /remissionControlTable` y `GET /remission-<id>`.
- **Envelope**: siempre `{data, msg, error}`; en el GET `data` es **lista** aun pidiendo un id.

### `PUT /remissionControlTable` — llaves nuevas en `metadata`

Mismo contrato de siempre (`metadata.id` obligatorio + los campos base requeridos; merge por llaves
presentes: lo no enviado no se toca, `""`/`null` vacía a propósito). Se agregan 2 llaves opcionales:

| Llave | Tipo | Semántica |
| --- | --- | --- |
| `total_sin_iva_admi` | number | Total sin IVA del bloque **administración**. Independiente de `totalSinIva` → `total_sin_iva` (bloque operaciones); el back no los sincroniza. |
| `remission_sent_date_client` | string | Fecha de envío de la remisión **al cliente** (bloque administración). Independiente de `remission_sent_date` (fecha de envío de líderes). |

```json
{"metadata": {"id": 42, "date": "...", "folio": "...", "client_id": 7, "plant": "...",
              "activity": "...", "location": "...", "general_description": "...", "comments": "...",
              "total_sin_iva_admi": 15100.00, "remission_sent_date_client": "2026-03-20"}}
→ 200 {"data": {"id_remission": 42}, "msg": "Tabla de control de remisión actualizada correctamente (ID 42)", "error": null}
```

El `POST` acepta las mismas llaves. Ambas entran al `history` (`changes.metadata` con
`{field, before, after}`), igual que `status_rep_admi`/`total_sin_iva`.

### `GET /remission-<id>` — lectura

Las 2 llaves vienen **aplanadas** en cada fila: `total_sin_iva_admi` numérico (`null` si nunca se ha
guardado) y `remission_sent_date_client` string (`""` si nunca se ha guardado). Registros viejos sin
las llaves no truenan.

```json
→ 200 {"data": [{"id": 42, "folio": "...", "total_sin_iva": 15200.50, "total_sin_iva_admi": 15100.00,
        "remission_sent_date": "2026-03-19", "remission_sent_date_client": "2026-03-20", ...}],
       "msg": null, "error": null}
```

### Gotchas

- Un token con solo `App.Department.Operaciones` **ya puede** crear/editar control table y leer el
  GET. Ojo: la afirmación del doc del front de que la pantalla de líderes "carga bien" con ese token
  no cuadraba con el código previo (el GET también daba 401) — conviene que el front re-verifique su
  flujo de carga con un token puro de Operaciones.
- No hay filtrado de llaves por departamento: un token de operaciones puede escribir las llaves de
  administración y viceversa (aceptado en el grill; el endpoint es uno solo).
- La decisión de qué fecha muestra la columna "Fecha de envío de remisión" del bloque Administración
  (`remission_sent_date` vs `remission_sent_date_client`) es 100% del front.

## Verificación

Ciclo completo contra la BD dev (27 checks, script de scratch): fila vieja expone
`total_sin_iva_admi: null` / `remission_sent_date_client: ""` sin tronar; `POST` con las 2 llaves +
sus contrapartes → `GET` aplana las 4 con valores distintos (independencia); `PUT` con **solo**
`total_sin_iva_admi` en el JSON crudo actualiza esa llave, no toca `remission_sent_date_client` ni
`total_sin_iva`, y el `history` registra `before/after` solo de ella; ídem con solo
`remission_sent_date_client`; `PUT /remissionBalance` escribiendo `remission_sent_date` **no pisa**
`remission_sent_date_client` ni `total_sin_iva_admi`; `DELETE` de la fila temporal (verifica además
el fix del guard de items vacíos, también contra la fila huérfana real del primer intento).
`pyrefly check` sin errores nuevos en los 3 archivos tocados.

## Al modificar

- Sigue vigente la receta de [`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md):
  campo nuevo = form + `api.model` + `_*_EXTRA_KEY_MAP` + `_HISTORY_EXTRA_FIELDS` (+
  `_HISTORY_NUMERIC_FIELDS` si es numérico) + `_GET_EXTRA_*_FIELDS`.
- Si algún día se separa la escritura por bloque (operaciones vs administración), el camino acordado
  sería filtrar el set de llaves permitidas en `_extra_info_updates` según el departamento del token —
  no dos endpoints.
- El `DELETE /remission` ya tolera remisiones sin items; si se agrega otra vía de creación sin items,
  no hace falta tocar nada ahí.
