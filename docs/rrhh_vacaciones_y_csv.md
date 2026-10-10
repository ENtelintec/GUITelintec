# Vacaciones (`POST`/`PUT /employee/vacation`) y descargas CSV de RRHH: bugs pre-existentes

Fecha: 2026-10-09 · **Estado: hecho y verificado contra dev (30/30 checks HTTP, `Tests/tester_rrhh_vacations_csv.py`).** Sin DDL.

Cierra los "bugs pre-existentes de RRHH" que quedaron en [`pendientes.md`](pendientes.md) tras la comprobación del mes 1 ([`plan_rh_mes.md`](planes/archivo/plan_rh_mes.md)), más el código muerto de encuestas.

## Qué estaba mal

- **El alta de vacaciones descartaba `prima`.** `insert_new_vacation` guardaba solo `status`/`comentarios`/`dates`. Los dos GET de vacaciones leen `v["prima"]`, así que **la primera vacación creada por API tumbaba con 500 (`KeyError`)** `GET /employees/vacations/all` y `GET /employee/vacations/<id>`. Era latente: las 72 filas de las 3 BDs vienen de antes del API y todas traen `prima`. El tracker lo atribuía al `PUT` (que "reusa el form de insert"), pero el `PUT` sí recibía `prima`: el `FormField` siempre la trae con sus defaults.
- **`id_vacation` era basura.** `vacations` tiene PK = `emp_id`, sin autoincremental: el `POST` devolvía `lastrowid` (siempre `0`) y el `PUT` el `rowcount`.
- **`PUT` sin registro respondía 200 "ID 0"**, y un `POST` duplicado daba un 400 genérico.
- **CSV armados a mano**, sin quoting: comas o saltos de línea dentro de un valor partían la fila. Algunos campos cambiaban `,` por `;`, NULL salía como `None` y se escribía a rutas relativas compartidas (`files/emp.csv`, `files/medical.csv`, `files/vacations.csv`), con carrera entre requests. El CSV de empleados no traía el apellido.
- **`get_all_data_employees` ignoraba `data_token`**: el CSV de empleados y `GET /employees/info/<status>` siempre leían la BD default, también con un token `is_tester`.

## Las 4 capas

```
HTTP     rs_RRHH.py                   POST/PUT /employee/vacation pasan el (dict, code) del midleware;
                                      las 3 descargas mandan el buffer en memoria (download_name + text/csv)
mid      Functions_midleware_RRHH.py  _seniority_from_form (mismo shape alta/edición), 409/404/id_vacation;
                                      borradas calculate_results_quizzes / recommendations_results_quizzes
mid      Functions_DB_midleware.py    _seniority_list (lector tolerante), _csv_buffer + create_csv_file_{employees,medical,vacations}
db       employees_controller.py      get_all_data_employees(status, data_token=None)
```

Modelos y forms sin cambios.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permiso de departamento `rrhh`.
- **Base**: `/GUI/api/v1/rrhh`.

**`POST /employee/vacation`**: body JSON `{emp_id: int, seniority: [{year: int, status: str, comentarios: str, prima: {status: str, fecha_pago: str}, dates: ["YYYY-MM-DD", …]}]}` (sin cambios).

| Status | Respuesta |
|---|---|
| 201 | `{"data": {"id_vacation": 89}, "msg": "Vacaciones registradas correctamente (ID 89)", "error": null}`: `id_vacation` **es el `emp_id`** (antes siempre `0`) |
| 409 | `{"data": null, "msg": "El empleado ya tiene registro de vacaciones; usa PUT para actualizarlo", "error": "1062 (23000): Duplicate entry …"}` (**antes 400**) |
| 400 | `seniority` vacío → `msg: "No hay informacion que insertar"`; error de validación → `{"data": null, "msg": "Estructura de datos inválida", "error": {…}}` |

**`PUT /employee/vacation`**: mismo body. **Reemplaza** el `seniority` completo: los periodos que no se manden se pierden.

| Status | Respuesta |
|---|---|
| 200 | `{"data": {"id_vacation": 89}, "msg": "Vacaciones actualizadas correctamente (ID 89)", "error": null}`: también con datos idénticos (antes `id_vacation` era el `rowcount`) |
| 404 | `{"data": null, "msg": "No existe registro de vacaciones para el empleado 92", "error": null}` (**antes 200 "ID 0"**) |

**`GET /employees/vacations/all`** y **`GET /employee/vacations/<emp_id>`**: mismo shape. Cada periodo trae siempre `prima` (default `{"status": "No", "fecha_pago": ""}` si falta) y `dates` (default `[]`). `dates` es **nuevo en el GET de uno**.

**Descargas** (`GET /download/employees/<status>`, `/download/employees/medical`, `/download/employees/vacations`):

- **200** → blob `text/csv` UTF-8 sin BOM, attachment con el mismo nombre de antes (`emp.csv`, `medical.csv`, `vacations.csv`). **4xx** → envelope JSON `{data, msg, error}`. El front ramifica por status code.
- **Cambios en el archivo**:
  - CSV estándar (RFC 4180, `QUOTE_MINIMAL`): los valores con coma, comilla o salto de línea van **entre comillas**. Hay que leerlo con un parser CSV, no con `split(",")`.
  - Ya no se cambia `,` por `;`: `aptitudes`/`fechas` (médicos) y `body` (vacaciones) salen como su JSON original, entrecomillados.
  - NULL sale **vacío** (antes `None`).
  - **employees** gana la columna **`l_name` al final** (19 columnas; las 18 de antes no se mueven).
  - **vacations**: header sin espacios: `emp_id,Nombre,Apellido,fecha_inicio,body`.
- `status` en el path de empleados: contiene `"all"` → todos (excepto empleados con `status` NULL); contiene `"inactivo"` → inactivos; otro valor → activos.

Ejemplo (vacations):

```
emp_id,Nombre,Apellido,fecha_inicio,body
12,JUAN,PEREZ,2019-03-04,"{""1"": {""status"": ""7 PTES"", ""comentarios"": """", ""prima"": {""status"": ""Si"", ""fecha_pago"": ""2Q JUL 23""}}}"
```

## Al modificar

- **Un periodo de `seniority` siempre lleva** `status`, `comentarios`, `prima` y `dates`. Escríbelo con `_seniority_from_form` y léelo con `_seniority_list` (tolera periodos viejos sin `prima`/`dates`). No vuelvas a indexar `v["prima"]` directo.
- `vacations` tiene PK = `emp_id`: no hay id propio. No uses `lastrowid` ni `rowcount` como identificador.
- Los CSV se arman con `_csv_buffer(header, rows)`: columnas nuevas **al final** y sin `open()` a disco. Si un `SELECT` compartido gana columnas, alinea los unpacks de `create_csv_file_*` (ver [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md)).
- Toda consulta nueva de RRHH recibe `data_token` y lo pasa a `execute_sql` (permiso tester).

## Verificación

Contra BD dev (2026-10-09), [`Tests/tester_rrhh_vacations_csv.py`](../Tests/tester_rrhh_vacations_csv.py) (gitignored), **30/30**. Crea una fila temporal en `vacations` para un empleado activo sin registro y la borra en un `finally`. Cubre:

- **POST**: 201 con `id_vacation = emp_id`, `prima`/`dates` guardados, duplicado → 409, `seniority` vacío → 400 sin fila.
- **GET**: los dos GET con la fila nueva, y con un periodo legado sin `prima` → 200 con el default.
- **PUT**: 200, idéntico → 200, sin registro → 404 sin crear fila.
- **CSV**: las 3 descargas parseadas con `csv.reader`, con ancho fijo por fila y una fila por registro (contra la BD); `l_name` escrito, NULL vacío, `body` JSON válido y sin archivos tocados en `files/`.
- **Listado**: `GET /employees/info/activo` con `data_token`.

`pyrefly check` de los 4 archivos: 0 errores nuevos contra `HEAD` (5 menos, del código muerto borrado).

## Pendientes

- **[admin/RH] Datos**: el empleado 123 tiene `status` NULL (el CSV de "todos" lo excluye, igual que antes) y los empleados 7 y 39 tienen guardado el **texto** `'None'` en `puesto`. Sumado al ítem de calidad de datos en [`pendientes.md`](pendientes.md).
- ~~`templates/Functions_GUI_Utils.py`~~ (utilidades de la GUI de tkinter, sin ningún import y con su propia copia de las dos funciones deprecadas): **borrado** el mismo día por decisión del usuario.
