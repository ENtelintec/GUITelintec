# Plan de permisos — diagnóstico y decisiones

> Estado: en curso (grill cerrado el 2026-10-27). Este doc reúne cómo funcionan hoy los permisos entre el API y la app de usuarios, y las decisiones del grill (D1–D15). Primer paso implementado: [`permisos_compras_y_baja.md`](permisos_compras_y_baja.md) (D6, D8, D12, D13). Abiertos: `P-187` a `P-198` en [`pendientes.md`](pendientes.md).

## Las dos piezas

- **App de usuarios** (`GUI_System`, repo `ENtelintec/GUI_System`, escritorio ttkbootstrap; aquí solo se usa como referencia). Da de alta las cuentas en `sql_telintec.users_system`:
  - usuario y hash MD5;
  - permisos: un checkbox por entrada de su `static/permissions.json` (31 permisos), guardados como dict por índice (`{"0": "App.Department.Basic", ...}`);
  - el **JWT HS256** firmado con `TOKEN_MASTER_KEY`, con payload `permissions, emp_id, name, contrato, user, dep_id`.
  - Cada cambio de permisos re-firma el token.
  - Si hay que cambiar algo allá, se escribe un doc aquí y el usuario lo hace allá.
- **Este API**: no tiene login. Recibe el JWT crudo en `Authorization` y lo valida con `token_verification_procedure` ([`Functions_Aux_Login.py`](../templates/resources/methods/Functions_Aux_Login.py)).
  - Cada endpoint pasa `department` (un string o una lista, con OR entre elementos).
  - Pasa si **algún permiso del token contiene el string** (subcadena, sin distinguir mayúsculas) o contiene `administrator`.
  - La sede de almacén se valida aparte, con el sufijo exacto de `Sucursal-<id>` (`verify_warehouse_permission`).
  - El API también crea usuarios: `POST /UserSystem/user` firma el token igual que la app de usuarios. Además, `GET /UserSystem/permissions` sirve **su propia copia** del catálogo ([`static/permissions_models.json`](../static/permissions_models.json)).

## Hallazgos (2026-10-27)

1. **Dos catálogos que ya divergen.**
   - El del API trae `Sucursal-2` y no `testerUser`.
   - El de la app de usuarios trae `testerUser` y no `Sucursal-2`, así que **nadie puede recibir `Sucursal-2`** desde la app.
   - Los 4 endpoints de escritura de `/sucursal` (`POST/PUT/DELETE /movement`, `PUT /transfer/receive`) hoy solo los usan los administradores.
2. **Los tokens no vencen.**
   - El payload no lleva `exp`, así que `jwt.decode` nunca los rechaza. La columna `exp` (1 año) solo se guarda.
   - No hay forma de revocar un token: un empleado dado de baja conserva el suyo. En dev, 27 de 92 usuarios son de empleados inactivos.
   - Los tokens de dev están al día con la columna `permissions`. En prod no se revisó: el clasificador de seguridad bloqueó la lectura de usuarios de prod.
3. **Strings que no alcanzan ningún permiso** (en una lista con otros solo estorban; solos dejan pasar únicamente a los administradores):

   | string | usos | nota |
   |---|---|---|
   | `purchases` | 28 | compras/OC; casi siempre junto a `administracion` |
   | `sucursal` | 10 | solo alcanzaría `Sucursal-<id>`, que la app no puede asignar |
   | `orders` | 8 | OC |
   | `credentials` | 4 | `/UserSystem/*`; `POST /user` lo pide solo |
   | `remission`, `iaotros`, `respe` | 1 c/u | siempre en lista con otros |

4. **Permisos que ningún endpoint pide** (fuera de pasar por `administrator`): `Director`, `adminDB`, `adminRem`, `checkvehicular`, `checkvApprove`. Un usuario que solo tenga `Director` no entra a nada.
5. **La subcadena da acceso de más.**
   - `sm` (32 usos) abre con `SM`, `SM-URGENT`, `smControl`, `smCreate`, `smDespachar` y `smEntregasAdmin`.
   - `almacen` abre también con `ALMACEN-VISUAL`; `epp` con `eppVisual`; `voucher` con los 4 de vales.
   - Un permiso de "solo ver" pasa por los mismos endpoints de escritura que el permiso completo.
   - Un permiso nuevo cuyo nombre contenga `administrator` sería administrador en todo el API.
6. **Uso real (dev, 92 usuarios).**
   - Casi todos tienen `Basic` y `Common`; luego siguen `SM` (23), `Bitacoras` (17), `ALMACEN` (9), `RRHH` (7), `Operaciones` y `Epp` (6), `Administracion` (5) y `Administrator` (4).
   - Además hay permisos fuera del catálogo actual (`DemoRRHH`, `DemoALMACEN`).
7. **El front tiene una tercera lista** (`WebApps/telintec_webapp/src/constants/route-permissions.ts`).
   - Decide qué pantallas muestra comparando el nombre **exacto, con mayúsculas**.
   - Escribe `EppVisual` y `EppApprove`, pero el catálogo dice `eppVisual` y `eppApprove`: esos usuarios no ven sus pantallas, aunque el API sí los deja pasar por la subcadena `epp`.
   - Ya prevé `Sucursal-<id>`.
8. **La pantalla de usuarios del front llama rutas que el API no tiene.**
   - Llama `POST /UserSystem/create-user`; el API expone `POST /UserSystem/user`.
   - Llama `GET /UserSystem/usernames-<status>/<id>`; el API solo tiene `/usernames-<status>`.
   - `POST /user` pide solo `credentials`, que no coincide con ningún permiso.

Inventario completo: 354 endpoints; 313 llaman a `token_verification_procedure` y los demás lo hacen por un helper del módulo (`_auth` de CDA, vales de SGI). Uso por string, sin distinguir mayúsculas:

| string | usos | permisos que lo cumplen |
|---|---|---|
| `administracion` | 133 | `Administracion` |
| `rrhh` | 77 | `RRHH` |
| `almacen` | 62 | `ALMACEN`, `ALMACEN-VISUAL` |
| `sm` | 32 | `SM`, `SM-URGENT`, `smControl`, `smCreate`, `smDespachar`, `smEntregasAdmin` |
| `sgi` | 24 | `SGI` |
| `operaciones` | 18 | `Operaciones` |
| `voucher` | 16 | `Voucher`, `voucherSafe`, `voucherTool`, `voucherApprove` |
| `bitacoras` / `bitacora` | 13 | `Bitacoras` |
| `basic` | 11 | `Basic` |
| `common` | 10 | `Common` |
| `epp` | 7 | `Epp`, `eppVisual`, `eppApprove` |
| `compras` | 1 | `adminCompras`, `comprasCreate` |

## Decisiones (grill del 2026-10-27)

- **D1 — Una sola lista: tabla `permissions` en `sql_telintec`** (nombre, descripción, área, activo).
  - La app de usuarios pinta sus checkboxes desde la tabla, `GET /UserSystem/permissions` la sirve y el front la consulta.
  - Los permisos de cada usuario se siguen guardando por nombre en `users_system`, así que el token no cambia.
  - El DDL y las tareas de la app de usuarios se escriben al cerrar el grill.
- **D2 — El alta de usuarios y permisos sigue siendo manual** y la hace el equipo en la app de usuarios.
  - Migrar esa gestión a la webapp se planea aparte (`P-188`).
  - Ese plan decide qué pasa con `POST /UserSystem/user` (pide `credentials`, que no corresponde a ningún permiso) y con las rutas que la pantalla del front llama y el API no tiene.
- **D3 — `Sucursal-2` entra ya a la lista de la app de usuarios** (`P-189`, [`gui_system_tareas.md`](gui_system_tareas.md)). Asignárselo a alguien espera los datos de `P-048`.
- **D4 — Regla para endpoints nuevos**:
  - el contrato para el front de cada doc de cambio dice **qué permisos exactos del catálogo** abren el endpoint;
  - si un permiso no existe, va a [`gui_system_tareas.md`](gui_system_tareas.md) y el endpoint no se cierra hasta que exista.
  - La regla quedó en `CLAUDE.md`.
- **D5 — Errores del front**: `EppVisual`/`EppApprove` va a `P-187`; las rutas de `/UserSystem` van dentro de `P-188`.

- **D6 — Comparación exacta en lo nuevo**:
  - los endpoints nuevos, y los que se toquen, listan nombres completos del catálogo en un parámetro nuevo `permissions=[...]` y el API compara exacto;
  - `department=` sigue por subcadena hasta migrar cada área en su turno;
  - `Administrator` pasa en ambos;
  - el API sigue leyendo solo el token, sin consultas a la BD.
  - Motivo: con la subcadena, `ALMACEN-VISUAL` puede usar los 18 endpoints de escritura que solo piden `almacen` (`DELETE /almacen/movement`…), y `smEntregasAdmin` los 9 que solo piden `sm`.
- **D7 — La baja se avisa; no se revoca en el API.**
  - El API sigue confiando solo en el token.
  - Cuando RH da de baja a un empleado que tiene usuario, el sistema avisa que hay que darlo de baja de la app de usuarios.
  - Automatizarlo entra en el plan de migración (`P-188`).
- **D8 — Aviso de baja a los administradores** (`P-191`):
  - cuando un empleado pasa de activo a `inactivo`, por la baja de RH (`terminate_employee_from_api`) o por el `PUT` del empleado con `status`, y tiene usuario en `users_system`, el API notifica a `App.Department.Administrator`: dar de baja del sistema de usuarios a `<usuario>` (empleado N, motivo);
  - RH sigue recibiendo su aviso; no requiere DDL.
- **D9 — La lista de pendientes de baja vive en la app de usuarios** (T2 de [`gui_system_tareas.md`](gui_system_tareas.md), `P-190`), porque ahí se editan los usuarios.
  - Es calculada (empleado inactivo con fila en `users_system`), sin bandera guardada.
  - Un endpoint del API con esa lista llega con la migración (`P-188`).
- **D10 — Sin `exp` por ahora.**
  - Tras borrar al usuario ya no se puede iniciar sesión, y la sesión del front muere en 24 h o menos.
  - Queda vivo solo un token copiado y usado directo contra el API. Es un riesgo aceptado hasta `P-188`, cuando el API firme tokens de vida corta al iniciar sesión.
  - Un `exp` de 1 año obligaría a re-firmar a todos cada año y casi no reduce el riesgo.
- **D11 — Tabla `sql_telintec.permissions`** (`P-193`, DDL [`permissions_catalog.sql`](../scripts_db_handle/permissions_catalog.sql)):
  - columnas `id`, `name` (único, nombre completo y exacto), `description`, `area`, `is_active` (retirar = 0; nunca se borra) y `created_at`;
  - carga inicial: los 31 permisos de la app en su orden (ids 1 a 31) más `Sucursal-2` (id 32);
  - la app de usuarios la lee y escribe (T3, `P-195`); `GET /UserSystem/permissions` la sirve y se borra `static/permissions_models.json` (`P-194`).
- **D12 — Compras es la primera área con comparación exacta** (hecho: [`permisos_compras_y_baja.md`](permisos_compras_y_baja.md)):
  - OC, solicitudes, bitácora de compras y lista de compra: `Administracion` y `adminCompras`;
  - listar, crear y editar solicitudes: además `comprasCreate`;
  - lista de compra: además `ALMACEN` y `ALMACEN-VISUAL`.
- **D13 — Fuera los textos que no corresponden a ningún permiso** cuando van en una lista con otros (hecho): `remission`, `iaotros`, `respe`, y `purchases` en los endpoints que no son de Compras. No cambia quién entra.
- **D14 — Los permisos que nadie pide se ligan al migrar su área** (`P-198`):
  - `adminRem` a remisiones; `adminDB` a clientes, proveedores y contratos; `checkvehicular` y `checkvApprove` al checklist vehicular;
  - `Director` se define con los dashboards.
- **D15 — Los permisos fuera del catálogo se quitan en prod** desde la app de usuarios (T4, `P-196`). La tabla no los incluye.

## Notas posteriores

- **2026-10-27 — `P-198`, Almacén** (grill del mismo día; hecho: [`permisos_almacen.md`](permisos_almacen.md)):
  - `ALMACEN-VISUAL` solo lee, y las descargas y los códigos de barras cuentan como lectura;
  - EPP: lecturas para `Epp`, `eppVisual` y `eppApprove`; `POST`/`PUT /movement` para `ALMACEN` y `Epp`;
  - sedes y reservas: lectura `Administracion`, `ALMACEN` y `ALMACEN-VISUAL`; escritura `Administracion` y `ALMACEN`;
  - `/sucursal` conserva `department="sucursal"` como puerta de la sede, una excepción a D6 porque el permiso lleva el id; lecturas del principal exactas;
  - dashboards de inventario: `ALMACEN` y `ALMACEN-VISUAL`.
- **2026-10-27 — `P-198`, SM** (grill del mismo día; hecho: [`permisos_sm.md`](permisos_sm.md)):
  - `SM` y `SM-URGENT` son el grupo base; las urgentes son solo de `SM-URGENT`;
  - `smControl`, `smCreate`, `smDespachar` y `smEntregasAdmin` no abren nada y quedan **pendientes de asignación**: se usarán más adelante y no se retiran (usuario, mismo día; `P-199`);
  - `ALMACEN` conserva sus 10 endpoints de SM y `ALMACEN-VISUAL` solo las 4 lecturas;
  - Administración y Operaciones sin cambios.
- **2026-10-27 — `P-198`, SGI** (grill del mismo día; hecho: [`permisos_sgi.md`](permisos_sgi.md)):
  - formatos ISO sin cambios;
  - vales de herramienta: `SGI`, `Voucher` y `voucherTool`; el listado y el estado también para `voucherApprove` y `ALMACEN`;
  - vales de EPP: `SGI`, `Voucher` y `voucherSafe`; el listado y la aprobación también para `voucherApprove`, `Epp`, `eppApprove` y `ALMACEN`;
  - checklist vehicular: `SGI`, `Voucher`, `checkvehicular`, `checkvApprove`, `Operaciones`, `Administracion` y `RRHH` (borrar: `SGI`, `Voucher` y `checkvApprove`), lo que liga `checkvehicular` y `checkvApprove` (D14);
  - el catálogo del control de saldos espera a Administración.
