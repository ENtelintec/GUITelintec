# Tareas para la app de usuarios (`GUI_System`)

> Cambios que este API necesita en la app de usuarios (`C:\Users\L03508427\PycharmProjects\GUI_System\GUI_System`, repo `ENtelintec/GUI_System`). Desde este repo no se toca: cada tarea la hace el usuario allá y avisa para cerrarla aquí. Contexto y decisiones: [`permisos_plan.md`](permisos_plan.md).

## T1 — Agregar `App.Department.Sucursal-2` al catálogo (`P-189`)

> **Hecha (2026-10-27).** `Sucursal-2` está en la tabla `sql_telintec.permissions` (id 32) desde el SQL de `P-193`, que es la fuente desde T3.

- **Por qué**:
  - Los 4 endpoints de escritura de `/sucursal` (`POST/PUT/DELETE /movement`, `PUT /transfer/receive`) piden la subcadena `sucursal`.
  - La sede se valida con el sufijo exacto del permiso (`Sucursal-<id_warehouse>`, [`almacen_multisede_f2.md`](almacen_multisede_f2.md)).
  - Sin el permiso en la app nadie puede recibirlo, así que hoy solo los usan los administradores.
  - El API (`static/permissions_models.json`) y el front (`route-permissions.ts`) ya lo tienen.
- **Qué**: botón **"Add Permission"** de la app. En Name, el sufijo `Sucursal-2`; la app antepone `App.Department.`.
  - Description: `the warehouse permission for branch 2 (sede de almacén id 2)`.
  - La app valida el nombre y lo agrega **al final** de `static/permissions.json`. Al final, la UI no mueve los checkboxes existentes, y lo guardado no se rompe porque se guarda por nombre.
  - El nombre va exacto, con esa capitalización: el front compara el nombre exacto.
- **Asignarlo** espera a que administración diga qué usuarios operan la sede (`P-048`). Al asignarlo:
  - la app re-firma el token (`update_perms` → `refresh_token`);
  - el usuario vuelve a iniciar sesión para que el front reciba el token nuevo.
- **Verificar**: dar el permiso a un usuario `.tester` y, con su token nuevo, un endpoint de escritura de `/sucursal` deja de responder 401.

## T2 — Lista de usuarios pendientes de baja (`P-190`)

> **Hecha (2026-10-27, revisado en solo lectura).** Columnas `Employee status` / `Departure`, botón "Pending removal", borrado de todas las filas del empleado inactivo (normal y `.tester`) con confirmación y de sus `files/{user}.json`; la recarga masiva salta a los inactivos.

- **Por qué**:
  - El API confía en el token y no revisa si el empleado sigue activo ([`permisos_plan.md`](permisos_plan.md), D7 y D10).
  - Cuando RH da de baja a un empleado, el usuario hay que borrarlo a mano en la app.
  - El API avisará a los administradores en cada baja (`P-191`), pero la lista tiene que vivir en la app, donde se editan los usuarios.
  - La lista cubre los avisos que se pierdan y las bajas que ya existen (en la copia de dev, 27 de 92 usuarios son de empleados inactivos; en prod no se ha medido).
- **Qué**:
  1. En `templates/controllers/user_system.py`, `get_all_users_data` agrega al final del `SELECT` `employees.status` y `employees.departure`. `departure` es JSON `{"date": "YYYY-MM-DD HH:MM:SS", "reason": "..."}` y lo escribe la baja de RH.
  2. En `Frame_UsersSystem.create_table`, dos columnas nuevas al final de `columns`: `Employee status` y `Departure`. La tabla ya es `searchable`, así que escribir `inactivo` en el buscador ya filtra.
  3. Opcional: un botón **"Pending removal"** que deje en la tabla solo los usuarios con `status = 'inactivo'`.
  4. Al borrar el usuario de un empleado inactivo, borrar **todas** sus filas: la normal y la `.tester`, que tienen el mismo `emp_id`.
     - Hoy `delete_user` borra por `U_id` y no pide confirmación.
     - Sugerido: `messagebox.askyesno` con el usuario y el motivo de baja, y luego `DELETE ... WHERE emp_id = %s`.
- **Ojo**:
  - Borrar el usuario impide volver a iniciar sesión, porque el login lee `users_system`, y la sesión abierta del front muere en 24 h o menos.
  - Un token copiado sigue sirviendo contra el API hasta `P-188` (riesgo aceptado en D10).
- **Verificar**: dar de baja en dev o test un empleado de prueba que tenga usuario; aparece en la lista; al borrarlo desaparece, junto con su `.tester`.

## T3 — Leer y escribir el catálogo en la tabla `sql_telintec.permissions` (`P-195`)

> **Hecha (2026-10-27, revisado en solo lectura).** Los checkboxes salen de la tabla (activos, por `id`); "Add Permission" inserta con área y avisa el duplicado 1062 aunque esté retirado; `static/permissions.json` se borró. El botón opcional de retirar no se hizo.

- **Depende de** `P-193`: correr `scripts_db_handle/permissions_catalog.sql` al menos en prod, porque la app solo se conecta a la BD de AWS.
- **Por qué** (D1/D11 de [`permisos_plan.md`](permisos_plan.md)):
  - las tres listas de permisos (la de la app, la del API y la del front) ya divergieron;
  - la tabla pasa a ser la única fuente;
  - la carga inicial trae los 31 permisos de `static/permissions.json` en el mismo orden (ids 1 a 31) más `Sucursal-2` (id 32), así que los checkboxes no se mueven.
- **Qué**:
  1. `load_permissions()` lee `SELECT name, description FROM sql_telintec.permissions WHERE is_active = 1 ORDER BY id` (un controller nuevo en `templates/controllers/user_system.py`) en lugar de abrir `static/permissions.json`. El resto del código ya trabaja con la lista `{name, description}`.
  2. **"Add Permission"** hace `INSERT INTO sql_telintec.permissions (name, description, area) VALUES (...)`.
     - Hay que agregar un selector de `area`: `rrhh`, `almacen`, `administracion`, `compras`, `sgi`, `cda`, `sm`, `operaciones` o `general`.
     - Se conserva la validación del sufijo.
     - El `UNIQUE` de la tabla no distingue mayúsculas: un duplicado da error 1062, que se muestra como "ya existe".
  3. Opcional: un botón para **retirar** un permiso (`UPDATE ... SET is_active = 0`); nunca `DELETE`.
     - Un usuario que tenga un permiso retirado lo pierde la siguiente vez que se guarden sus permisos, porque ya no tiene checkbox.
  4. Al terminar, borrar `static/permissions.json` para que no vuelva a usarse como fuente.
- **Verificar**: la app pinta los mismos 31 checkboxes en el mismo orden, más `Sucursal-2`; un permiso agregado desde la app aparece en `GET /GUI/api/v1/UserSystem/permissions` (cuando `P-194` esté hecho).

## T4 — Quitar permisos que no están en el catálogo (`P-196`)

- **Por qué**:
  - en dev hay usuarios con `App.Department.DemoRRHH` y `App.Department.DemoALMACEN`;
  - como el API compara `department` por subcadena, `DemoRRHH` entra a los 77 endpoints de RRHH;
  - la carga inicial de la tabla no los incluye;
  - en prod no se ha medido, porque el API no puede leer los usuarios de prod.
- **Qué**: con la tabla ya creada (`P-193`), correr en prod esta consulta (probada en dev contra la lista del catálogo):

  ```sql
  SELECT us.U_id, us.usernames, jt.perm
  FROM sql_telintec.users_system us,
       JSON_TABLE(JSON_EXTRACT(us.permissions, '$.*'), '$[*]' COLUMNS (perm VARCHAR(100) PATH '$')) jt
  WHERE jt.perm COLLATE utf8mb4_bin NOT IN (
      SELECT name COLLATE utf8mb4_bin FROM sql_telintec.permissions WHERE is_active = 1)
  ORDER BY jt.perm, us.usernames;
  ```

  - El `COLLATE utf8mb4_bin` hace que también salgan las diferencias de mayúsculas (`admincompras` contra `adminCompras`), que el API nuevo y el front no aceptan.
  - Por cada usuario listado: abrirlo en la app, guardar sus permisos con los checkboxes (el nombre fuera de catálogo se cae al guardar) y dejar que la app re-firme el token. Si algún permiso sí se necesita, darlo de alta antes con "Add Permission".
- **Verificar**: la consulta devuelve 0 filas.

## T5 — Usuarios con permisos granulares de SM (`P-199`)

- **Por qué** ([`permisos_sm.md`](permisos_sm.md)):
  - `smControl`, `smCreate`, `smDespachar` y `smEntregasAdmin` se usarán más adelante, así que **no se retiran**: quedan activos en el catálogo como pendientes de asignación;
  - mientras no se defina qué abre cada uno, con la comparación exacta de SM **no abren nada**: antes pasaban por la subcadena `sm`;
  - si alguien en prod los tiene **sin** `SM`, perdió el acceso a SM.
- **Qué**:
  1. En prod, ver quién los tiene:

     ```sql
     SELECT us.U_id, us.usernames, jt.perm
     FROM sql_telintec.users_system us,
          JSON_TABLE(JSON_EXTRACT(us.permissions, '$.*'), '$[*]' COLUMNS (perm VARCHAR(100) PATH '$')) jt
     WHERE jt.perm IN ('App.Department.smControl', 'App.Department.smCreate',
                       'App.Department.smDespachar', 'App.Department.smEntregasAdmin')
     ORDER BY us.usernames;
     ```

  2. A cada usuario listado que no tenga `SM` ni `SM-URGENT`, marcarle `SM` (o `SM-URGENT` si crea urgentes) y guardar; la app re-firma el token. El permiso granular puede quedarse marcado.
  3. **No retirarlos** del catálogo.
- **Verificar**: ningún usuario de la consulta se queda sin `SM` ni `SM-URGENT`.

## T6 — Alta de `adminCobranza` y `adminPreventa` (`P-207`)

- **Por qué** ([`permisos_administracion.md`](permisos_administracion.md)):
  - el usuario pidió separar Cobranza de Preventa dentro de Administración (2026-10-28);
  - el API ya compara `App.Department.adminCobranza` y `App.Department.adminPreventa`, pero mientras no estén en el catálogo nadie puede tenerlos;
  - `Administracion` sigue abriendo todo, así que nadie pierde acceso mientras tanto.
- **Qué**:
  1. Darlos de alta en el catálogo: con "Add Permission" (área `administracion`) o con `scripts_db_handle/permissions_admin_cobranza_preventa.sql`, que también deja dev y test iguales.
  2. Asignarlos:
     - `adminCobranza` a quien solo lleva cobranza: remisiones, control de saldos y control de entregas. Además recibe los avisos diarios de saldos y entregas.
     - `adminPreventa` a quien solo lleva cotizaciones, CISCO, OCD y licitaciones.
     - Quien hoy tiene `Administracion` y debe quedarse solo con una parte: quitarle `Administracion` y marcarle el nuevo. La app re-firma el token.
- **Verificar**:
  - los dos aparecen activos en los checkboxes;
  - un usuario solo con `adminPreventa` recibe 401 en `POST /admin/collections/remission` y 200 en `GET /admin/presales/tenders`.
