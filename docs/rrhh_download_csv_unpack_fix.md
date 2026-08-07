# Descargas CSV de RRHH: desempaquetados desalineados con sus SELECT (500 en los 3 endpoints)

Los tres GET de descarga de CSV del módulo RRHH tronaban con 500
(`ValueError: too many values to unpack`) — destapados por la comprobación de
la S1 del plan del mes ([`plan_rh_mes.md`](plan_rh_mes.md)). Corroborados y
corregidos el 2026-08-07; la re-prueba del tercero cerró el mismo día **sin más
hallazgos** (hoja de comprobación cerrada — checkpoint S1 cumplido).

## Causa raíz: controllers compartidos extendidos, sitios CSV nunca actualizados

Los tres endpoints leen de controllers **compartidos con consumidores JSON**.
En algún momento los `SELECT` ganaron columnas para esos consumidores y los
desempaquetados de los sitios CSV se quedaron con el conteo viejo:

| Endpoint | Controller | SELECT | Unpack (antes) | Columnas que faltaban |
|---|---|---|---|---|
| `GET /rrhh/download/employees/<status>` | `get_all_data_employees` ([`employees_controller.py`](../templates/controllers/employees/employees_controller.py)) | 22 | 20 | `department_id`, `usernames` |
| `GET /rrhh/download/employees/medical` | `get_all_examenes` ([`em_controller.py`](../templates/controllers/employees/em_controller.py)) | 9 | 8 | `extra_info` |
| `GET /rrhh/download/employees/vacations` | `get_vacations_data` ([`vacations_controller.py`](../templates/controllers/employees/vacations_controller.py)) | 6 | 5 | `renovacion` |

**Los SELECT no se recortan**: las columnas extra son load-bearing en los otros
call sites (`get_info_employees_with_status` desempaqueta las 22;
`fetch_medicals`/`fetch_medical_employee` las 9). La excepción es `renovacion`
en vacations, que hoy **nadie** consume (los otros dos call sites indexan
`item[0..4]`) — se dejó en el SELECT igual para no tocar una query compartida.

El fix es alinear los desempaquetados en los sitios CSV. El contenido de los
CSV **no cambia** (byte-idéntico): las columnas nuevas se descartan.

## Las capas tocadas

```
HTTP  rs_RRHH.py                 medical y vacations: unpack alineado + guards NULL;
                                 employees: maneja la tupla de error del midleware
mid   Functions_DB_midleware.py  create_csv_file_employees: unpack 20→22; error → envelope {data,msg,error}
```

(Controllers y modelos intactos; son GET sin body.)

## Endurecimiento de paso (misma clase de falla, mismos endpoints)

Fallas latentes que el smoke test no pisó por los datos que había, pero que
darían el mismo 500 en la siguiente vuelta:

- **employees**: si la BD no devuelve lista, `create_csv_file_employees`
  regresa `({"data": None, "msg": "No se encontraron empleados", "error": ...}, 400)`
  y antes `rs_RRHH` hacía `send_file(str(tupla))` → 500. Ahora el resource
  detecta la tupla y la responde tal cual.
- **medical**: `fechas.replace(...)` / `aptitud.replace(...)` con columna NULL →
  `AttributeError`. Ahora `(x or "").replace(",", ";")`.
- **vacations**: ídem con `seniority`.

Verificado contra la BD dev: 105 empleados (todas las filas ancho 22), 15
exámenes (ancho 9, sin NULLs hoy), 47 vacaciones (ancho 6), y el CSV de
empleados generado end-to-end con el header intacto.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**;
  permiso de departamento `rrhh`.
- **Rutas** (base `/GUI/api/v1/rrhh`):
  - `GET /download/employees/<status>` — `status` en el path: contiene `"all"` →
    todos; contiene `"inactivo"` → inactivos; cualquier otro valor → activos.
  - `GET /download/employees/medical`
  - `GET /download/employees/vacations`
- **200** → **blob** (archivo CSV como attachment, sin envelope). **4xx** →
  envelope JSON `{data, msg, error}`; el front ramifica por status code.
  - 401: `{"error": "No autorizado. Token invalido"}`
  - 400 (sin datos / error de BD): `{"data": null, "msg": "No se encontraron empleados", "error": "..."}`
    (medical/vacations responden `msg` "Error al obtener los datos del empleado")
- **Columnas de cada CSV** (sin cambios respecto a antes del fix):
  - employees: `id,name,phone,department,modality,email,contract,admission,rfc,curp,nss,emergency,position,status,departure,exam_id,birthday,legajo`
  - medical: `id_exam,nombre,sangre,estatus,aptitudes,fechas,apt_actual,emp_id`
  - vacations: `emp_id, Nombre, Apellido, fecha_inicio, body` (los valores
    reales son `emp_id, name, l_name, date_admission, seniority`)
- **Gotchas**: el CSV se arma a mano **sin quoting** — solo algunos campos
  reemplazan `,` por `;`; un valor con salto de línea embebido parte la fila en
  dos (hay un caso real en dev). `name` en employees **no incluye el apellido**
  (`l_name` se lee pero no se escribe). Campos NULL imprimen `None` literal.
  Todo esto es pre-existente y está en pendientes; no parsear estos CSV por
  máquina sin tolerancia a eso.

## Al modificar

- Si un `SELECT` de un controller compartido gana columnas, **grep de todos los
  call sites** y alinear cada unpack (columnas nuevas siempre al final). Este
  bug fue exactamente eso, tres veces.
- Los sitios CSV descartan las columnas extra (`_extra`, `_renovacion`,
  `department_id`/`usernames` sin uso); si un CSV debe exponerlas, es cambio de
  contrato del archivo → avisar al front y actualizar este doc.
- Los `.replace` sobre columnas nullable siempre con `(x or "")`.

## Pendientes

- Apellido omitido en el CSV de employees (decidir con el front si `name` pasa
  a nombre completo o se agrega columna al final).
- CSV sin quoting/escaping (comas y saltos de línea dentro de valores rompen
  filas) — evaluar `csv.writer` con `QUOTE_MINIMAL` en los tres.
- Rutas relativas hardcodeadas (`files/emp.csv`, `files/medical.csv`,
  `files/vacations.csv`) y archivo compartido entre requests concurrentes — ya
  listado en riesgos de [`plan_rh_mes.md`](plan_rh_mes.md).
