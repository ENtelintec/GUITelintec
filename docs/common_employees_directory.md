# Directorio de empleados de uso general (`GET /common/employees/<status>`)

`GET /rrhh/employees/info/<status>` ([`rs_RRHH.py`](../templates/resources/rs_RRHH.py))
devuelve la ficha completa del empleado (RFC, CURP, NSS, contacto de emergencia,
cumpleaños, examen médico, legajo...) y solo lo abren `rrhh`, `operaciones`,
`administracion` y `checkvehicular`. Para listas, selectores y directorios de otras
áreas se agrega un endpoint **de propósito general** con el permiso `Common`, que
devuelve **solo datos no confidenciales**.

## Las 4 capas

```
HTTP    rs_Common.py  /employees/<status>  (get)             -> token con department="common"
modelos — (GET sin payload; solo expected_headers_per)
mid     Functions_DB_midleware.py  get_employees_directory_with_status -> arma los dicts + envelope
DB      employees_controller.py    get_employees_directory     -> SELECT solo de columnas públicas
```

- [`get_employees_directory`](../templates/controllers/employees/employees_controller.py)
  es un **SELECT nuevo**, no un filtro sobre `get_all_data_employees`: no lee
  `rfc`/`curp`/`nss`/`emergency_contact`/`birthday`/`legajo`/fechas ni hace JOIN
  con `sql_telintec_mod_rrhh.examenes_med`. Así un cambio futuro en el mapeo no
  puede filtrar datos confidenciales. Solo hace JOIN con `departments` y
  `users_system` (`GROUP_CONCAT(usernames)`).
- Recibe `data_token` → respeta el switch a la BD de test (`is_tester`), a
  diferencia de `get_all_data_employees`.
- `status`: `all` → `%`, `inactivo` → `inactivo`, cualquier otro valor → `activo`
  (misma semántica que el endpoint de RRHH).
- `id_leader` sale de `extra_info.id_leader` (0 si no existe o si `extra_info`
  es NULL).

## Permiso

Solo `department="common"` (match por substring, case-insensitive →
`App.Department.Common`). Como todo endpoint, cualquier permiso con
`administrator` también pasa. **No** se abrió a `basic`: el substring `basic`
coincide con muchos permisos de grupo (SGI, vouchers, almacén...) y expondría
teléfonos/correos a casi todos los usuarios.

## Contrato mínimo para el front

- **Base path**: `/GUI/api/v1/common`
- **Endpoint**: `GET /employees/<status>` con `status` ∈ `activo | inactivo | all`
  (otro valor se trata como `activo`).
- **Auth header**: `Authorization: <jwt>` — el **JWT crudo, NO `Bearer <token>`**.
  El token debe tener el permiso `Common` (o `administrator`).
- **Request**: sin body ni query params.
- **Response**: siempre JSON `application/json` con el envelope `{data, msg, error}`.
  Orden alfabético por `name`, `lastname`. `name`/`lastname` en MAYÚSCULAS y sin
  espacios al inicio/final (`strip()`; en BD hay nombres con espacio final).

Campos de cada elemento de `data`:

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int | `employee_id` |
| `name` | str | mayúsculas |
| `lastname` | str | mayúsculas |
| `phone` | str \| null | |
| `email` | str \| null | |
| `dep` | str \| null | nombre del departamento |
| `dep_id` | int \| null | |
| `contract` | str \| null | |
| `position` | str \| null | puesto |
| `status` | str | `activo` / `inactivo` |
| `id_leader` | int | `0` = sin líder |
| `modality` | str \| null | |
| `username` | str \| null | si tiene varios usuarios vienen separados por coma |

**200 — con resultados**
```json
{
  "data": [
    {
      "id": 12, "name": "JUAN", "lastname": "PÉREZ LÓPEZ",
      "phone": "8112345678", "email": "juan.perez@telintec.com.mx",
      "dep": "Operaciones", "dep_id": 3, "contract": "CTR-001",
      "position": "Técnico", "status": "activo", "id_leader": 7,
      "modality": "Presencial", "username": "jperez"
    }
  ],
  "msg": null,
  "error": null
}
```

**200 — sin resultados** (no es error; p. ej. `inactivo` vacío)
```json
{"data": [], "msg": "No se encontraron empleados", "error": null}
```

**400 — falla de BD**
```json
{"data": [], "msg": "No se pudieron obtener los empleados", "error": "<error sql>"}
```

**401 — token inválido o sin `Common`**
```json
{"error": "No autorizado. Token invalido"}
```

Gotchas: la lista vacía es **200**, no 4xx; el 401 no trae `data`/`msg`
(patrón común de todos los endpoints).

## Al modificar

- **No agregar** campos confidenciales (RFC, CURP, NSS, contacto de emergencia,
  cumpleaños, fechas de ingreso/baja, legajo, exámenes). Si otra área los
  necesita, va por el endpoint de RRHH con su permiso.
- Un campo nuevo toca las dos capas: el `SELECT` + `GROUP BY` de
  `get_employees_directory` y el desempaquetado/dict de
  `get_employees_directory_with_status` (el orden de columnas debe coincidir).
- No ampliar el permiso a `basic` sin revisar los permisos que contienen ese substring
  en [`permissions_models.json`](../static/permissions_models.json).
