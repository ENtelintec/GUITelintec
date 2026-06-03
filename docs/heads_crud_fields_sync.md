# Sincronización de campos en el CRUD de `heads` (cargos / cabezas de departamento)

Los endpoints de escritura de `heads` (`POST`/`PUT`/`DELETE` en
[`rs_Admin_DB.py`](../templates/resources/rs_Admin_DB.py), ruta `/head`) habían
quedado **desfasados** respecto al `fetch` (la fuente de verdad). Este documento
describe el estado actual tras alinearlos.

## La tabla `heads`

Columnas escribibles: `name`, `department`, `employee`, `extra_info` (JSON).
`position_id` es la PK.

- `employee` es **FK** a `employees.employee_id`. Puede ser `NULL` → puesto
  **vacante**. El `fetch` usa `LEFT JOIN employees`, así que un `employee` NULL
  devuelve `employee_name`/`employee_email` nulos sin romper.
- `extra_info` (JSON) contiene cuatro claves de contrato:
  `contracts`, `contracts_temp`, `other_leaders` (listas de ids) y `area`
  (entero, id de `areas.id`).

El `area` se lee en todo el [`heads_controller.py`](../templates/controllers/heads/heads_controller.py)
vía `JSON_UNQUOTE(heads.extra_info->'$.area') = areas.id` (en `check_if_gerente`,
`check_if_leader`, `check_if_auxiliar`, etc.) para resolver permisos/rol. **No lo
escribe ningún otro endpoint** — antes solo se poblaba a mano en la BD.

## Las 4 capas

```
HTTP    rs_Admin_DB.py  /head  (post/put/delete)         -> validan con *Form.from_json
modelos api_employee_models.py  Head*Form + head_*_model  -> validador (Form) + swagger (api.model)
mid     Functions_midleware_admin.py  *_head_from_api      -> normaliza extra_info / employee
DB      heads_controller.py  insert_head_DB/update_head_DB -> SQL crudo vía execute_sql
```

El `fetch` (referencia) es [`fetch_heads` / `fetch_heads_main`](../templates/resources/midleware/Functions_midleware_admin.py)
y devuelve por cargo: `id`, `name`, `employee`, `department`, `department_name`,
`employee_name`, `employee_email`, `contracts`, `contracts_temp`,
`other_leaders`, `area`.

## Qué se corrigió

### 1. `PUT /head` ahora edita `name`

El nombre del cargo **era inmutable** (cambiaron las condiciones de negocio). El
`POST` lo escribía y el `fetch` lo devolvía, pero el `PUT` no podía cambiarlo:
`HeadUpdateForm` no tenía `name` y `update_head_DB` no lo incluía en el `SET`.

- [`api_employee_models.py`](../static/Models/api_employee_models.py): `name`
  agregado a `HeadUpdateForm` (`InputRequired`) y a `head_update_model`.
- `update_head_from_api` pasa `data["name"]`.
- `update_head_DB` agrega `name = %s` al `SET` (nuevo parámetro `position_name`).

### 2. `update_head_DB` usaba el `type_sql` equivocado

Era `execute_sql(..., 4, ...)` (`4 = lastrowid`, para INSERT) en un **UPDATE**.
Corregido a `3` (rowcount). Un `rowcount = 0` (id inexistente o sin cambios) se
devuelve como **`200` con `data: 0`** — comportamiento aceptado, sin manejo de
"not found".

### 3. `employee` vacante vía `NULL` (no `0`)

`employee = 0` rompía la **FK** (no existe empleado id 0). Antes el `PUT` exigía
`employee` (`InputRequired`) mientras el `POST` lo dejaba opcional con
`default=0` — inconsistente, y el default 0 hacía fallar el INSERT de un puesto
vacante.

- `HeadUpdateForm.employee` relajado a `validators=[], default=0` (igual que
  `HeadInputForm`).
- En **ambos** `insert_head_from_api` y `update_head_from_api` se convierte
  `employee` *falsy* (`0`/`None`) a `None` antes de la query → la FK recibe
  `NULL`:

  ```python
  employee = data["employee"] if data["employee"] else None
  ```

- Las firmas `insert_head_DB`/`update_head_DB` se ampliaron a `employee: int | None`.

### 4. `area` cableado de extremo a extremo (opcional)

`area` se consumía en las queries de rol pero no era escribible ni se devolvía.
Además, como las formas reconstruyen `extra_info` desde cero en cada `PUT`, un
update **borraba** silenciosamente un `area` previo. Ahora es parte explícita del
contrato:

- `ExtraInfoHeadsForm`: `area = IntegerField(default=0)`.
- `extra_info_heads_model`: `"area": fields.Integer(required=False)`.
- `insert_head_from_api` / `update_head_from_api`: backfill `extra_info["area"] = 0`
  si falta (junto a los otros tres campos).
- `fetch_heads` y `fetch_heads_main`: agregan `"area": extra_info.get("area", 0)`.

`area = 0` significa "sin área": el `LEFT JOIN areas` simplemente no matchea y
devuelve `abbreviation` NULL.

## Contrato actual de `/head`

| Campo | POST | PUT | Tipo | Notas |
|---|---|---|---|---|
| `id` | — | requerido | int | `position_id` |
| `name` | requerido | requerido | str | editable en update |
| `department` | requerido | requerido | int | FK `departments` |
| `employee` | opcional (0) | opcional (0) | int | `0`/ausente → `NULL` (vacante) |
| `extra_info.contracts` | opcional `[]` | opcional `[]` | list[int] | |
| `extra_info.contracts_temp` | opcional `[]` | opcional `[]` | list[int] | |
| `extra_info.other_leaders` | opcional `[]` | opcional `[]` | list[int] | |
| `extra_info.area` | opcional `0` | opcional `0` | int | id de `areas.id` |

`DELETE` solo recibe `id` (sin cambios).

## Al modificar

- Cualquier campo nuevo del cargo debe tocar **las 4 capas**: `Head*Form` y
  `head_*_model` (validador + swagger), el `*_head_from_api` (normalización) y
  `insert_head_DB`/`update_head_DB` (SQL), y además exponerse en `fetch_heads` /
  `fetch_heads_main` si debe leerse.
- Como `extra_info` se reconstruye completo en cada `PUT`, **toda** clave que
  deba persistir tiene que estar en `ExtraInfoHeadsForm` con su `default`, o se
  perderá en el update.
- `employee` vacante es `NULL`, nunca `0`. No agregar `0` como id válido.
