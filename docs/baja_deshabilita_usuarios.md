# La baja del empleado deshabilita sus usuarios (`P-223`, F2a)

Fecha: 2026-11-03 · **Estado: hecho y verificado contra dev** (`Tests/tester_baja_deshabilita.py` 44/44; regresión `tester_permisos_compras_baja` 113/113). Sin DDL (`is_active` viene de `P-220`). Es la parte de `P-223` que no necesita pantalla ([`planes/login_y_usuarios_plan.md`](planes/login_y_usuarios_plan.md), U3 y U17). Reemplaza el aviso de `P-191` ([`permisos_compras_y_baja.md`](permisos_compras_y_baja.md)).

## Qué cambia

**Baja.** Al pasar un empleado a `inactivo` (`DELETE /rrhh/employee/terminate` o `PUT` del empleado con `status`), el API pone `is_active = 0` y `token = NULL` en **todos** sus usuarios, incluido el de prueba. La fila no se borra. La Lambda rechaza a los deshabilitados en v1 y v2.

| Status anterior → nuevo | Qué hace | Aviso a administradores |
|---|---|---|
| cualquiera menos `inactivo` → `inactivo` (incluido `status` vacío) | deshabilita a sus usuarios activos | "Usuario deshabilitado", con usuarios y motivo |
| lo mismo, pero falla la escritura | la baja **queda guardada** y responde 200 | "Usuario sin deshabilitar", con el error; pide hacerlo a mano |
| lo mismo, sin usuarios o ya deshabilitados | nada | ninguno |
| `inactivo` → `inactivo` | nada | ninguno |
| `inactivo` → `activo` (reingreso) | **no reactiva** | "Usuario por reactivar", si tiene usuarios deshabilitados |

Reactivar sigue en `GUI_System` ("Enable") hasta la F2b.

**Lo que no corta.** Solo se bloquean los inicios de sesión nuevos. Una sesión abierta sigue hasta que venza su token, porque el API no consulta la BD ([`permisos_plan.md`](permisos_plan.md), D8). Con tokens de 24 h ([`tokens_solo_24h.md`](tokens_solo_24h.md)) son 24 h como máximo; hoy, un token v1 copiado no vence.

**Quienes ya estaban de baja no cambian.** F2a solo actúa cuando un empleado pasa a inactivo. Los usuarios de empleados que ya estaban inactivos se deshabilitan con "Pending removal" de `GUI_System` (`P-233`): en dev son 27 usuarios de 25 empleados y en test 22 de 20. Incluye `demo_rrhh` y `demo_almacen`, ligados al empleado 60.

**Permisos en `/UserSystem`.** Sale `credentials`, que no existe en el catálogo, y se pasa a comparación exacta. Nadie del catálogo pierde acceso.

| Endpoint | Antes | Ahora |
|---|---|---|
| `GET /usernames-<status>`, `POST /update-biocredentials` | `department=["credentials", "administracion"]` | `App.Department.Administracion` |
| `POST /user` | `department=["credentials"]` (solo pasaba `Administrator`) | `App.Department.Administrator` |

**Arreglo de `POST /UserSystem/user`.** `permissions` era `StringField`: tomaba el texto del primer elemento y lo guardaba letra por letra. En test, `adrian.cruz.test` quedó con `{"0": "{", "1": "'", "2": "p", ...}`, así que ese usuario entra sin permisos válidos. Ahora es una lista de `{permission, description}` y se guarda como las demás filas, `{"0": "App.Department.Basic", ...}`. `emp_id` y `dep_id` pasan a enteros, para que el token guardado no los lleve como texto. Sigue firmando HS256 mientras `TOKEN_LEGACY_ENABLED` esté activo; después del corte no firma nada. Los usuarios ya dañados se corrigen en `GUI_System` (`P-233`).

## Capas tocadas

```
rs     templates/resources/rs_login.py                          permissions= exacto, sin credentials
model  static/Models/api_login_models.py                        PermissionModelForm, PostUserModelForm con FieldList e IntegerField
mid    templates/resources/midleware/Functions_midleware_RRHH.py  _disable_employee_users, _notify_user_rehire (reemplazan _notify_user_offboarding)
mid    templates/resources/midleware/MD_UserSystem.py           permisos por nombre, _legacy_stored_token
db     templates/controllers/employees/us_controller.py         get_users_by_emp_id, disable_users_by_emp_id
```

`get_user_by_emp_id` se queda: con `LIMIT 1` sirve para saber si una notificación le llega a alguien, no para deshabilitar.

## Contrato mínimo para el front

El front no tiene que cambiar nada: el cuerpo de la pantalla Usuarios del Sistema ya es el correcto.

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Base: `/GUI/api/v1/UserSystem`.
- **`GET /usernames-<status>`** y **`POST /update-biocredentials`**: `App.Department.Administracion`. Respuestas sin cambio.
- **`POST /user`**: `App.Department.Administrator`.

  ```json
  {
    "permissions": [{"permission": "App.Department.Basic", "description": "Básico"}],
    "emp_id": 123, "name": "ANA PEREZ", "contract": "AMC", "user": "ana.perez", "dep_id": 2,
    "hashpass": "<md5 hex de la contraseña>"
  }
  ```

  - **201**: `{"data": {"id_user": 150}, "msg": "Usuario creado correctamente (ID 150)", "error": null}`
  - **400** (lista vacía, un elemento sin `permission` o `emp_id` no numérico): `{"data": null, "msg": "Estructura de datos inválida", "error": {"permissions": ["This field is required."]}}`
  - **401**: `{"error": "No autorizado. Token invalido"}`
- **Baja de empleado** (`DELETE /rrhh/employee/terminate`, `PUT` del empleado): request y response sin cambio. Lo nuevo se ve en las notificaciones de los administradores, con títulos `Usuario deshabilitado`, `Usuario sin deshabilitar` y `Usuario por reactivar`, en lugar de `Usuario pendiente de baja`.

## Verificación (2026-11-03, dev)

`Tests/tester_baja_deshabilita.py` 44/44, con empleados y usuarios temporales que se borran al final (0 restantes):

- baja con dos usuarios: los dos deshabilitados y sin token, un aviso con ambos nombres y el motivo;
- baja repetida, sin usuarios y con usuario ya deshabilitado: sin aviso;
- `status` NULL: también deshabilita;
- fallo simulado al deshabilitar: la baja queda, el usuario sigue activo y el aviso pide hacerlo a mano;
- `PUT` en sus cuatro transiciones, y reingreso sin reactivar y con aviso;
- `usernames` y `update-biocredentials`: entran `Administracion` y `Administrator`; `Basic`, `RRHH`, `adminCobranza` y `credentials` dan 401;
- alta con el cuerpo del front: permisos por nombre, enteros en el token, `Administracion`, `RRHH` y `credentials` dan 401, lista vacía y `emp_id` no numérico dan 400; con el interruptor en 0 no firma.

Que la Lambda rechace a los deshabilitados se revisó en su código (`login/service.py`), no se probó de punta a punta.

## Al modificar

- **Otro camino que cambie `status`**: llamar a `_disable_employee_users` y `_notify_user_rehire` igual que `update_employee_db`.
- **Reactivación desde el API (F2b)**: sin firma, depende de `P-221` en prod, porque el front v1 usa el token guardado.
