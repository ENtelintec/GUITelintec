# Login y gestión de usuarios — plan (`P-188`)

> Estado: aprobado (grill del 2026-10-29, que también cerró `P-209` y definió `P-199`). Reemplaza en parte a D2, D7, D9 y D10 de [`permisos_plan.md`](../permisos_plan.md). Fases y pendientes: `P-218` a `P-224` en [`pendientes.md`](../pendientes.md). Repo nuevo de la Lambda: `C:\Users\L03508427\PycharmProjects\telintec_login_lambda`.

## Cómo funciona hoy

- **Login**: NextAuth (servidor del front, `src/lib/auth.ts`) llama a una Lambda de AWS (`…/V1/LoginUP`, API Gateway) con `{username, password: md5(contraseña)}` y `Authorization` = md5 de una llave compartida. La Lambda ([`codigo_lambda.py`](../../scripts_db_handle/codigo_lambda.py)) compara el MD5 contra `users_system.password` y devuelve el **token guardado** en la fila.
- **Tokens**: los firma `GUI_System` con HS256 y `TOKEN_MASTER_KEY`, sin `exp`. La misma llave está en el API, en `GUI_System` y en el `.env` del front (`NEXT_PUBLIC_TOKEN_MASTER_KEY`): con HS256 quien verifica puede fabricar un token de `Administrator`.
- **Contraseñas**: MD5 sin sal, calculado en el front; el MD5 guardado sirve como la contraseña misma.
- **Alta de usuarios**: `GUI_System`, y en el API `POST /UserSystem/user` (solo pasa `Administrator`: pide `credentials`, que no es un permiso). Ese endpoint firma el token y tiene un bug: `permissions` es `StringField` y `enumerate` lo recorre letra por letra. El front lo llama desde Usuarios del Sistema y desde `rrhh/personal` (RH, solo `Common` y `Basic`), y además tiene `POST /UserSystem/create-user` (código muerto) y `/usernames-<status>/<id>` (no se usa).
- **Problemas de la Lambda v1**: abre dos conexiones por login y no cierra ninguna; sin SSL a RDS; un usuario sin empleado la tira con 502; compara la llave con `!=`.

## Decisiones (grill del 2026-10-29)

- **U1 — `GUI_System` se queda.** Es la herramienta del lead dev de back (solo él tiene acceso): firma tokens y queda de respaldo para la gestión. La webapp gestiona usuarios para `Administrator` y `RRHH` (F2). Las dos escriben `users_system`.
- **U2 — Quién gestiona.**
  - `Administrator`: alta con cualquier permiso, edición de permisos, deshabilitar y reactivar, catálogo.
  - `RRHH`: alta **solo con `Basic` y `Common`**, validado en el API (no solo en el modal).
  - `Administracion`: lista de usuarios (`GET /usernames-<status>`) y biocredenciales, con comparación exacta.
  - `credentials` sale del código.
- **U3 — La baja deshabilita.** Cuando RH da de baja a un empleado, el API pone `is_active = 0` en sus usuarios (el normal y el de prueba); la fila no se borra. En un reingreso, el administrador los reactiva a mano y revisa permisos. La Lambda rechaza a los deshabilitados.
- **U4 — El login vive en la Lambda**, no en el API: un ataque de fuerza bruta contra el hash ocuparía los 3 workers del API; en la Lambda escala aparte y API Gateway lo frena. Repo propio, `telintec_login_lambda`.
- **U5 — Firma asimétrica ES256, una llave por firmante** (`kid` en el encabezado):
  - `lambda`: tokens de sesión; privada en Secrets Manager.
  - `gui_system`: privada solo en la máquina del lead dev de back, junto al `.env` de `GUI_System`.
  - `dev`: privada en el `.env` de dev, para los testers; el API acepta este `kid` **solo con `API_ENVIRONMENT=dev`**.
  - El API, el front y los clientes guardan **solo llaves públicas**. Si se filtra una privada, se rota solo ese `kid`.
- **U6 — Vigencia.** Tokens de la Lambda con `exp` de 24 h (igual que la sesión de NextAuth). Tokens de `GUI_System` sin `exp`, como hoy: los emite a propósito una sola persona y se revocan todos rotando su llave.
- **U7 — Contraseñas: argon2id sobre el md5 que manda el front.** El front sigue mandando `md5(contraseña)`; la Lambda guarda `argon2id(md5)` y deja `password` en `NULL` en el primer inicio de sesión, venga de v1 o de v2. La BD queda protegida desde el día del despliegue, la contraseña en claro no viaja y las dos versiones del front funcionan con usuarios migrados. Quien cambie una contraseña escribe el MD5 nuevo en `password` y pone `password_hash = NULL`.
- **U8 — Respuesta igual a la de hoy** (`{verified, user, token, timestamp_token, expires_in, permissions}`); errores `401` genéricos (usuario inexistente, contraseña incorrecta, deshabilitado o sin empleado) y `429` por bloqueo.
- **U9 — Endurecimiento**: una conexión cerrada por invocación, SSL a RDS, `hmac.compare_digest`, bloqueo de **5 intentos / 15 minutos**, throttling del stage de **5 peticiones/s con ráfaga de 10**.
- **U10 — Usuario de prueba** sigue siendo un usuario aparte (`nombre.tester`, con `testerUser`).
- **U11 — Transición sin corte coordinado**: la Lambda v2 tiene modo legado (sin `version` responde como hoy), así que se despliega antes que el front.
- **U12 — Despliegue**: la misma Lambda y el mismo API Gateway de la consola; el repo arma el zip y se publica como versión con alias `live`. python3.13, sin SAM/CDK por ahora.
- **U13 — El API deja de firmar tokens.** `POST /UserSystem/user` y las altas de F2 solo escriben la fila; el token de sesión nace en el login.

## Fases

**F1 — Login** (en este orden):

1. `P-220` [usuario] DDL [`users_system_login_v2.sql`](../../scripts_db_handle/users_system_login_v2.sql) en dev → test → prod. No rompe el código actual.
2. `P-218` [back] el API acepta ES256 por `kid`, además de HS256. Diseño abajo.
3. `P-219` [usuario] desplegar la Lambda v2 (pasos en el README del repo). Desde aquí las contraseñas se migran solas.
4. `P-221` [front] login v2 (contrato abajo).
5. `P-222` [usuario] `GUI_System` firma ES256 con su par (T7 de [`gui_system_tareas.md`](../gui_system_tareas.md)). Puede ir en paralelo desde el paso 2.

**F2 — Gestión en la webapp** (`P-223`): endpoints del API para alta (U2), edición de permisos, deshabilitar/reactivar y catálogo; deshabilitar en automático en la baja (U3, junto al aviso de `P-191`); rehacer `POST /UserSystem/user` (bug de `StringField`, sin firma); retirar `credentials`; pantallas del front y quitar `create-user` y la variante `/<id>`. Se diseña en un doc propio con su contrato.

**F3 — Retiro de HS256** (`P-224`): cuando ningún cliente use tokens HS256 (antes revisar `authapi`, `chatbot` y `products` de prod) y `GUI_System` haya re-firmado los suyos: el API deja de aceptar HS256, se cambia `TOKEN_MASTER_KEY` (mueren los tokens viejos copiados), la Lambda pierde el modo legado y se borra la columna `password`.

## `P-218` — el API acepta ES256

- En `token_verification_procedure` ([`Functions_Aux_Login.py`](../../templates/resources/methods/Functions_Aux_Login.py)): leer el encabezado sin verificar; `alg: HS256` sin `kid` → camino actual con `TOKEN_MASTER_KEY`; `alg: ES256` → llave pública de ese `kid`, `jwt.decode(..., algorithms=["ES256"])` (PyJWT valida `exp` cuando viene). `kid` desconocido o `dev` fuera de dev → 401. Nada más cambia: los datos del token son los mismos.
- Llaves públicas como archivos junto al `.env` (igual que `domain.pem`): `token_public_lambda.pem`, `token_public_gui_system.pem`, `token_public_dev.pem` (este solo en dev). `cryptography` ya estaba en `constraints.txt` (43.0.0); pasa a `requirements.txt` porque PyJWT la necesita para ES256.
- Los testers siguen con `TOKEN_MASTER_KEY` hasta la F3 y entonces pasan a la privada `dev`.
- **Hecho el 2026-10-29** → [`token_es256_por_kid.md`](../token_es256_por_kid.md).

## Contrato mínimo para el front (`P-221`, login v2)

Lo consume el servidor de NextAuth (`authorize()` en `src/lib/auth.ts`), no el navegador.

- **URL**: la misma de hoy (`NEXT_PUBLIC_LOGIN_HOST`, `…/V1/LoginUP`). `POST`, `Content-Type: application/json`.
- **Auth del login**: `Authorization` = la misma llave compartida de hoy (no es un JWT). Pasa a una variable **sin** `NEXT_PUBLIC_` (p. ej. `LOGIN_LAMBDA_KEY`): con ese prefijo Next la mete al JS del navegador si un componente cliente la importa.
- **Cuerpo**: `{"username": "ana.perez", "password": "<md5 hex de la contraseña>", "version": 2}`. La contraseña se sigue mandando como md5.
- **200**:

  ```json
  {"verified": true, "user": "ana.perez", "token": "<JWT ES256>", "timestamp_token": "2026-10-29 18:00:00",
   "expires_in": 86400, "permissions": [{"role": "App.Department.Basic"}, {"role": "App.Department.Common"}]}
  ```

  El token lleva `{"alg": "ES256", "kid": "lambda"}` y los mismos datos de hoy (`permissions`, `emp_id`, `name`, `contrato`, `user`, `dep_id`) más `iat` y `exp`.
- **Verificar**: `jwt.verify(user.token, LOGIN_TOKEN_PUBLIC_KEY, { algorithms: ['ES256'] })` con la pública `lambda` (PEM, no es secreta). Se borra `NEXT_PUBLIC_TOKEN_MASTER_KEY` del `.env` del front.
- **Errores** (el front hoy solo mira `res.ok`; basta con mostrar el mensaje):
  - `400 {"error": "Estructura de datos inválida"}`
  - `401 {"error": "Unauthorized"}` — llave compartida incorrecta
  - `401 {"error": "Usuario o contraseña incorrectos"}` — también si el usuario está deshabilitado
  - `429 {"error": "Usuario bloqueado temporalmente por intentos fallidos", "retry_after": 812}` — segundos
  - `500 {"error": "Error interno"}`
- **Al API**: sin cambio. `Authorization` lleva el **JWT crudo, NO `Bearer <token>`**; los permisos de cada endpoint no cambian.
- **Gotchas**: el token vence a las 24 h y `useSessionCheck` ya cierra la sesión con su `exp`; sin `version: 2` la Lambda responde como hoy (token HS256 guardado), así que el front puede regresar a la versión anterior sin dejar fuera a nadie.

## Al modificar

- Contrato de la Lambda o datos del token: cambia aquí primero; el API (`P-218`), el front y `GUI_System` dependen de él.
- Esquema de `users_system`: `.sql` en `scripts_db_handle/` revisado por el usuario. Regla de contraseñas de U7 para cualquier código que la cambie.
- Llave nueva o rotación: un `kid` nuevo; primero la pública en el API y el front, luego la privada en el firmante.
