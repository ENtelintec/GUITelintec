# Empleados: correos múltiples (`emails[]` sobre `employees.email`) y nómina solo a activos (`POST /rrhh/payroll/notify`)

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (23/23 checks, `Tests/tester_employee_emails.py`, con SES y S3 simulados). Sin DDL; DML [`employees_emails_normalize.sql`](../scripts_db_handle/employees_emails_normalize.sql) para revisión del usuario (`P-163`).**

Fase **F7** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "añadir direcciones múltiples de correo de empleados de RH", "para enviar nóminas enviar solo empleados activos"). Extiende [`nomina_correo_ses.md`](nomina_correo_ses.md) (canal `email`) y [`common_employees_directory.md`](common_employees_directory.md).

## Qué cambia

- **`employees.email` es una lista separada por coma** (`a@x,b@y`) en la misma columna `VARCHAR(255)`: sin DDL, sin tabla aparte. El API es el único que la lee y escribe, con dos helpers en `Functions_Aux_RH`: `split_emails` (lectura tolerante: ignora tokens que no son correo, quita duplicados, baja a minúsculas solo el dominio) y `normalize_emails` (escritura estricta: un token que no es correo → 400).
- **`emails[]`** (lista) en `POST`/`PUT /rrhh/employee` dentro de `info`; `email` (string, puede traer comas) se conserva por compatibilidad y **deja de ser obligatorio**. Si `emails` trae algo, manda; si no, se usa `email`. Sin correos es válido (columna vacía). Correo inválido → 400 listándolo.
- **Todos los GET de empleados** (`GET /rrhh/employees/info/<status>`, `GET /rrhh/employee/info/<id>`, `GET /common/employees/<status>`) devuelven **`emails: []`** además de `email` (string tal cual está guardado). El front migra a `emails`.
- **Nómina por correo a todos**: `POST /rrhh/payroll/notify` con canal `email` manda el recibo a todos los correos del empleado en un solo envío SES; **`data.email_to` pasa a ser lista** (`["a@x", "b@y"]`, `null` si no se intentó).
- **Solo activos**: `POST /rrhh/payroll/notify` responde **400 `"empleado inactivo"`** si `employees.status` no es `activo` (`inactivo` y `NULL` incluidos), antes de escribir el aviso o mandar el correo; 404 si el empleado no existe. `POST /payroll/files/update` (subir el recibo) **sigue aceptando inactivos** (el último recibo de una baja se guarda, no se notifica).
- **DML** `employees_emails_normalize.sql`: deja la columna en forma canónica (`;` → `,`, sin espacios ni comas al borde o repetidas). En dev la "limpieza" encontró sobre todo comas finales y `','` solas; el API ya tolera ambas al leer, así que el DML es ordenación, no requisito.

## Capas tocadas

```
methods     Functions_Aux_RH.py                 split_emails · normalize_emails · join_emails (nuevos)
models      api_employee_models.py              EmployeeInputForm: email opcional + emails (FieldList) · api.model con emails en alta y detalle
midleware   Functions_midleware_RRHH.py         _employee_email_column (alta/edición) · notify: guard de activo (test_id_employee) · _send_payroll_email: split_emails → lista a SES
midleware   Functions_DB_midleware.py           emails en los 3 builders de empleados (lista RH, directorio común, detalle)
DML         scripts_db_handle/employees_emails_normalize.sql   (usuario, dev → test → prod)
```

`_first_email` desaparece: la única lectura de correos es `split_emails`.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/rrhh` (permiso `rrhh`) y `/GUI/api/v1/common` (permiso `common`). **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400 de midleware, objeto por campo en 400 de form. 401: `{"error": "..."}` sin envelope.

### `POST`/`PUT /rrhh/employee` — cambios

```json
{ "id": 36, "info": { "name": "Ana", "lastname": "Pérez", "...": "...", "emails": ["ana@telintec.com.mx", "ana.p@gmail.com"] } }
```

| Campo | Tipo | Notas |
|---|---|---|
| `info.emails` | `string[]` | lista de correos; se guarda `ana@telintec.com.mx,ana.p@gmail.com`. Vacía u omitida → se usa `info.email` |
| `info.email` | string | compatibilidad; puede traer varios separados por coma; **ya no es obligatorio** |

| Código | Cuándo | Ejemplo |
|---|---|---|
| **201 / 200** | guardado | igual que antes |
| **400** | un token no es correo | `msg: "Correo inválido"` · `error: ["emails: noesmail no es un correo válido"]`; nada se escribe |

El dominio se guarda en minúsculas; la parte local tal cual (SES compara la parte local contra las identidades).

**Pantalla (revisión 2026-10-22)**: nunca hubo columna aparte para el correo institucional y el personal, y en dev ningún empleado tiene dos correos reales (las comas sueltas vienen de una pantalla vieja con dos cajas). El formulario pinta **dos inputs fijos**, institucional (`@telintec.com.mx`) y personal, y manda `emails` con los que estén llenos (`P-171`); al leer, el institucional es el del dominio `telintec.com.mx`. La lista admite más por si hiciera falta, sin cambio de back.

### GET de empleados — cambio

Cada empleado gana `emails` (lista, `[]` si no hay) junto a `email` (string). `GET /common/employees/<status>`, `GET /rrhh/employees/info/<status>`, `GET /rrhh/employee/info/<id>`. Para pintar o mandar correo usar `emails`; `email` se queda por compatibilidad.

### `POST /rrhh/payroll/notify` — cambios

| Código | Cuándo | Respuesta |
|---|---|---|
| **201** | notificado | `data.email_to` ahora es **lista** (`["ana@telintec.com.mx", "ana.p@gmail.com"]`) o `null` si el canal `email` no se intentó; `channels_sent` / `channels_failed` igual |
| **400** | empleado no activo | `data: {"emp_id": 36, "status": "inactivo"}` · `msg: "El empleado 36 está inactivo (status 'inactivo'); la nómina solo se notifica a activos"` · `error: ["empleado inactivo"]` |
| **404** | empleado inexistente | `msg: "No existe el empleado 999"` |

"Notificar a todos" del front ya parte de la lista de activos; el guard solo evita que un `emp_id` inactivo mandado a mano reciba aviso o correo.

### Gotchas

- Un empleado con `status` **NULL** (`P-039`, datos sucios) cuenta como **no activo** para nómina.
- `emails` quita duplicados comparando sin mayúsculas; el orden se conserva.
- El correo de nómina va a todos los correos en **un** envío (un solo `MessageId`); si uno rebota, el `bounce` de SES llega a `Software@telintec.com.mx` como siempre (`P-036`).

## Al modificar

- **Tope de correos por empleado**: `normalize_emails` + un 400 en `_employee_email_column`; la columna es `VARCHAR(255)` (≈ 6 correos largos).
- **Correo "principal"**: hoy es el primero de la lista (`email` string lo expone así); si RH quiere marcarlo aparte, `extra_info.primary_email` sin DDL.
- **Pasar a tabla propia** (si llegan a necesitar por correo tipo/verificado): sustituir `split_emails`/`join_emails` por el controller nuevo; los tres builders y `_send_payroll_email` son los únicos lectores.
- **Permitir notificar a inactivos** en un caso puntual: `force: true` en `NotifyPayrollForm` y saltar el guard; hoy no (decisión 2026-10-22).

## Notas posteriores

- **2026-10-22 — DML corrido y corrección por PAD SPACE** (`P-163`): `employees_emails_normalize.sql` ya corrió en las 3 BDs; no queda ninguna coma suelta. Queda el empleado 32 (`'jess31438@gmail.com '`, espacio final) en las 3: `employees.email` es `utf8mb4_bin`, que es **PAD SPACE**, así que el `<>` del WHERE ignoraba el espacio final. El script compara ahora con `CAST(... AS BINARY)`; basta volver a correr los bloques 1–3. No afecta al API: `split_emails` ya recorta al leer.
