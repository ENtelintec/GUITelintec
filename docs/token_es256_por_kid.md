# El API acepta tokens ES256 por `kid` (`P-218`)

Fecha: 2026-10-29 · **Estado: hecho y verificado contra dev** (`Tests/tester_token_es256.py` 23/23; regresión `tester_permisos_sm` 10/10 y `tester_permisos_almacen` 18/18). Sin DDL. Primer paso de la F1 de [`planes/login_y_usuarios_plan.md`](planes/login_y_usuarios_plan.md) (U5, U6).

## Qué cambia

`token_verification_procedure` sigue igual por fuera; cambia solo cómo se decodifica el token (`unpack_token`):

- **`alg: ES256`** → se verifica con la llave pública de su `kid` y se valida `exp` si viene, con 30 s de tolerancia de reloj (`TOKEN_LEEWAY_SECONDS`).
  - `lambda`: tokens de sesión de la Lambda de login (24 h).
  - `gui_system`: tokens de `GUI_System` (sin `exp`).
  - `dev`: tokens de los testers; **solo existe con `API_ENVIRONMENT=dev`**, así que en prod un token `dev` siempre da 401.
- **Cualquier otro `alg`** → camino HS256 de siempre con `TOKEN_MASTER_KEY`. Se retira en la F3 (`P-224`). Un token HS256 con `kid` sigue necesitando la llave maestra, así que no hay confusión de algoritmos.
- **Rechazos (401)**: `kid` desconocido o ausente, `kid` sin su archivo, firma de otra llave, vencido, `alg: none` o token mal formado.
- Los datos del token no cambian (`permissions`, `emp_id`, `name`, `contrato`, `user`, `dep_id`), y tampoco `is_tester` ni la comparación de permisos.
- El API **no guarda ninguna llave privada**. Las públicas se leen una vez por proceso.

## Llaves públicas

Archivos junto al `.env` que encuentra `constants.py` (como `domain.pem`), ignorados por `*.pem`:

| Archivo | Quién lo pone | Dónde |
|---|---|---|
| `token_public_lambda.pem` | usuario, al generar el par `lambda` (`P-219`); en dev ya copiado el 2026-10-29 | dev y prod |
| `token_public_gui_system.pem` | usuario, al generar el par `gui_system` (`P-222`) | dev y prod |
| `token_public_dev.pem` | ya copiado en dev el 2026-10-29 (par generado en el repo de la Lambda) | solo dev |

El API solo corre en dev (local) y en prod; test es una BD, no un despliegue, y los tokens de prueba pasan por el mismo API. En prod el `.env` está en `/home/ec2-user/opt/`, así que los archivos van en esa misma carpeta. Si falta el archivo de un `kid`, sus tokens dan 401 y el log del API muestra `errort at token public key <kid>`. Los HS256 siguen pasando, así que **el código se puede desplegar antes de tener las llaves**. Un archivo nuevo se lee sin reiniciar; uno que **cambia** (rotación) requiere reiniciar el API.

## Capas tocadas

```
const   static/constants.py                               TOKEN_PUBLIC_KIDS, token_public_key_paths, TOKEN_LEEWAY_SECONDS
auth    templates/resources/methods/Functions_Aux_Login.py  unpack_token por alg/kid + _public_key (cache por proceso)
deps    requirements.txt                                   cryptography==43.0.0 explícita (PyJWT la usa para ES256; ya estaba en constraints.txt y en el venv de prod)
```

`unpack_token` de [`Functions_Utils.py`](../templates/Functions_Utils.py) es otra copia HS256 sin ningún uso; se borra en la F3.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Igual que siempre, ahora aceptando también el token ES256 de la Lambda (`kid: lambda`).
- **Permisos de cada endpoint**: sin cambio (los de su doc).
- **Errores**:
  - token vencido o de un `kid` no aceptado → **401** `{"error": "No autorizado. Token invalido"}`;
  - sin header → **401** `{"error": "Token not found"}`.
- **Gotcha**: el token de la Lambda vence a las 24 h; con un token vencido todos los endpoints dan 401 hasta volver a iniciar sesión (`useSessionCheck` ya cierra la sesión con el `exp`).

## Verificación (2026-10-29, dev)

`Tests/tester_token_es256.py` 23/23:
- HS256 legado con y sin el permiso pedido;
- ES256 `dev` leído del archivo, con los mismos datos e `is_tester`;
- `lambda` vigente, vencido, dentro del leeway y con `iat` 10 s adelantado;
- `gui_system` sin `exp`, y `Administrator`;
- los rechazos: `kid` desconocido o ausente, otra llave, HS256 con `kid`, `alg: none`, basura, archivo faltante sin tronar;
- `TOKEN_PUBLIC_KIDS` con `API_ENVIRONMENT=prod` (`lambda,gui_system`);
- HTTP con `GET /UserSystem/permissions`: ES256 → 200, vencido → 401, HS256 → 200.

pyrefly (`--python-version 3.11`): los 7 errores de `Functions_Aux_Login.py` ya existían (la línea HS256 y la firma de `verify_token`); la línea ES256 no agrega ninguno.

## Al modificar

- **`kid` nuevo** (rotación): agregarlo a `TOKEN_PUBLIC_KIDS` y poner su `.pem`; luego cambiar el firmante. Retirar el `kid` viejo cuando ya no haya tokens vivos con él.
- **F3 (`P-224`)**: quitar el camino HS256 de `unpack_token` y la copia de `Functions_Utils.py`, y pasar los testers a la privada `dev`. Hasta entonces los testers siguen firmando con `TOKEN_MASTER_KEY`.
- El contrato de los datos del token lo fija [`planes/login_y_usuarios_plan.md`](planes/login_y_usuarios_plan.md); el API no debe empezar a exigir llaves nuevas sin que la Lambda y `GUI_System` las manden.

## Notas posteriores

- **2026-10-29 — Pública `lambda` en prod; la Lambda v2 está en vivo** (`P-219`). `token_public_lambda.pem` ya está en `/home/ec2-user/opt/` (usuario). Un token real de la Lambda (`kid: lambda`) verifica con esa pública. Falta desplegar este código del API en prod antes de que el front mande `version: 2` (`P-221`).
