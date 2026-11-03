# Solo tokens de 24 h: regla, interruptor y corte (`P-224`)

Fecha: 2026-11-03 · **Estado: código hecho y verificado contra dev** (`Tests/tester_token_24h.py` 29/29 con el interruptor en 0; regresión `tester_token_es256` 23/23 sin él). **El corte en prod sigue pendiente y espera a `P-221`.** Sin DDL. Decisión del grill del 2026-11-03 ([`planes/login_y_usuarios_plan.md`](planes/login_y_usuarios_plan.md), U14 a U16). Parte de [`token_es256_por_kid.md`](token_es256_por_kid.md).

## La regla

Con `TOKEN_LEGACY_ENABLED=0`, el API solo acepta tokens que cumplan todo esto:

- `alg: ES256`, de un `kid` aceptado: `lambda`, y `dev` solo con `API_ENVIRONMENT=dev`;
- con `exp` e `iat`;
- con `exp - iat` de 24 h como máximo, para que ningún firmante pueda emitir por error un token largo.

Lo demás da 401: HS256 con o sin `exp`, `gui_system`, sin `exp`, sin `iat`, más de 24 h o vencido. Los 30 s de tolerancia de reloj siguen.

La Lambda es el único firmante en prod. `GUI_System` sigue gestionando usuarios, pero deja de firmar (`P-222`). Si necesitas un token, inicias sesión con tu usuario.

## El interruptor

`TOKEN_LEGACY_ENABLED`: la variable del sistema gana sobre la llave del `.env`. Se lee al arrancar, así que cambiarla requiere reiniciar el API.

| Valor | Efecto |
|---|---|
| sin la llave, o cualquier valor distinto de `0` | como hasta hoy: HS256, `gui_system` y ES256 con `exp` opcional. `POST /UserSystem/user` firma HS256 |
| `0` | la regla de arriba. `POST /UserSystem/user` no firma: deja `token`, `exp` y `timestamp_token` en `NULL` |

Existe para poder desplegar este código en cualquier momento sin riesgo, y para que el corte y su reversa sean cambiar una llave y reiniciar. Se borra junto con el código HS256 cuando el corte esté estable.

## Por qué no se puede limpiar hoy

El front en prod sigue en login v1: la Lambda le devuelve el **token guardado** y `src/lib/auth.ts` del front lo verifica con HS256. Si hoy se limpian los tokens o se pone el interruptor en 0, **nadie puede entrar a la webapp**. Por eso el orden empieza en `P-221`; a partir de ahí, la limpia se puede hacer cuando se quiera.

## Orden del corte

1. **Desplegar el API** con este código, sin la llave. No cambia nada.
2. **`P-221` en prod**: login v2, que además cierra la sesión si el token no trae `exp`. Al desplegarlo todos vuelven a entrar una vez y ya traen ES256.
3. **Revisar**:
   - que `authapi`, `chatbot` y `products` no usen tokens del API ni `TOKEN_MASTER_KEY` (confirmado por el usuario el 2026-11-03). Como comprobación, en prod: `grep -rIlE --exclude-dir={env,envg,envg2,.git,__pycache__} 'TOKEN_MASTER_KEY|HS256' /home/ec2-user/opt` solo debería mostrar `GUITelintec`;
   - que el log de la Lambda ya no muestre inicios de sesión `v1`.
4. **Prod: `TOKEN_LEGACY_ENABLED=0` en `/home/ec2-user/opt/.env` y reiniciar `guitelintec`.** Comprobar el login y que un token HS256 da 401. Reversa: quitar la llave y reiniciar.
5. **Limpia**: correr [`limpia_tokens_24h.sql`](../scripts_db_handle/limpia_tokens_24h.sql) en dev → test → prod. A partir de aquí, regresar al front v1 requiere volver a firmar los tokens.
6. **Lambda**: quitar el modo v1 (repo `telintec_login_lambda`) y publicar.
7. **Limpieza de código y llaves**, con el corte ya estable:
   - en el API: el interruptor, el camino HS256 de `unpack_token`, la copia de [`Functions_Utils.py`](../templates/Functions_Utils.py), `_legacy_stored_token` y el `kid` `gui_system`;
   - pasar los testers a la privada `dev` con `exp` (55 de 75 firman HS256);
   - quitar `TOKEN_MASTER_KEY` del `.env` del API, del front y de `GUI_System`.
8. **Columna `password`, al final y por separado.** La contraseña solo migra cuando el usuario inicia sesión, y borrarla deja fuera a quien no haya entrado. Se borra cuando la consulta 3 de [`usuarios_revision_solo_lectura.sql`](../scripts_db_handle/usuarios_revision_solo_lectura.sql) dé 0 en prod. DDL revisado por el usuario.

## Capas tocadas

```
const  static/constants.py                                 TOKEN_LEGACY_ENABLED, TOKEN_MAX_LIFETIME_SECONDS, TOKEN_PUBLIC_KIDS sin gui_system tras el corte
auth   templates/resources/methods/Functions_Aux_Login.py  unpack_token con la regla
mid    templates/resources/midleware/MD_UserSystem.py      _legacy_stored_token: el alta no firma tras el corte
sql    scripts_db_handle/limpia_tokens_24h.sql             limpia de tokens guardados (sin correr)
sql    scripts_db_handle/usuarios_revision_solo_lectura.sql  consultas para prod (sin correr)
```

## Contrato mínimo para el front

Se suma al contrato de `P-221` en [`planes/login_y_usuarios_plan.md`](planes/login_y_usuarios_plan.md).

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Sin cambio en los permisos de ningún endpoint.
- **Token aceptado tras el corte**: el de la Lambda con `version: 2`, siempre con `exp`, `{"alg": "ES256", "kid": "lambda"}`.
- **401**: `{"error": "No autorizado. Token invalido"}` en cualquier endpoint con un token vencido, HS256 o de otro firmante.
- **Pedido para `P-221`**: `src/hooks/useSessionCheck.ts` hoy ignora un token sin `exp` y el front no tiene manejo global del 401. **Si el token no trae `exp`, debe cerrar la sesión.** Sin eso, en el corte quien siga con sesión vieja ve errores en todas las pantallas hasta salir a mano.
- **Gotcha**: la sesión dura 24 h y no hay renovación: quien entró ayer a las 9:00 vuelve a iniciar sesión hoy a las 9:00, también en el check-in del celular.

## Verificación (2026-11-03, dev)

`Tests/tester_token_24h.py` 29/29, que arranca el API con el interruptor en 0 sin tocar el `.env`:

- `TOKEN_PUBLIC_KIDS` en dev y en prod, con 0, con 1 y sin la llave;
- pasan: `lambda` de 24 h y de 1 h, recién vencido dentro de la tolerancia, `dev` con `exp` e `iat`, `Administrator`;
- 401: 24 h + 1 s, un año, sin `exp`, sin `iat`, vencido, `dev` sin `exp`, `gui_system` con y sin `exp`, HS256 con y sin `exp`, `alg: none`, otra llave, `kid` desconocido, basura;
- alta de usuario con un token de 24 h: 201 y sin token guardado.

Sin la llave, `tester_token_es256` sigue 23/23: el comportamiento actual no cambió. El corte real no se ha probado de punta a punta, porque el front v2 aún no existe.

## Al modificar

- **Otro firmante**: `kid` nuevo en `TOKEN_PUBLIC_KIDS`, con `exp` e `iat`. El tope de 24 h aplica igual.
- **Cambiar la vigencia**: `TOKEN_MAX_LIFETIME_SECONDS` en el API y `token_ttl_seconds` en la Lambda. Primero se sube el tope del API; si no, sus tokens darían 401.
