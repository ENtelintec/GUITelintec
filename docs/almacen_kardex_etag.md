# ETag + 304 en el kardex — `GET /almacen/kardex`, `/kardex/epp` y `/sucursal/movements/<type_m>`

> `P-128`, decidido en el grill del 2026-10-27 ([`plan_back_sin_bloqueo_2026_10_27.md`](planes/plan_back_sin_bloqueo_2026_10_27.md)). Es el segundo paso después de la ventana por fecha ([`almacen_kardex_ventana.md`](almacen_kardex_ventana.md)). Los tres GET del kardex responden con un **ETag débil**, calculado con la huella del cuerpo. Cuando un refresco no trae cambios, el navegador recibe **304 sin cuerpo** y reusa la respuesta que ya tenía. La consulta a la BD se sigue haciendo en cada llamada: el ahorro está en lo que viaja por la red, no en el tiempo del servidor. No hay DDL ni cambio de contrato, y **el front no cambia**.

## Decisiones (grill)

| Decisión | Resultado |
|---|---|
| Validador | **ETag débil (`W/"…"`)** con la huella del cuerpo completo (`blake2b` de 128 bits sobre el JSON), lo que incluye `msg` y `meta`. Siempre es exacto y no necesita columna de versión. Un `max(id)` no bastaría porque los movimientos se editan y se borran en duro. |
| Por qué débil | nginx comprime con gzip en prod y, al comprimir, convierte un ETag fuerte en débil. Si nace débil, llega igual al navegador. |
| Cabeceras del 200 | `ETag` + `Cache-Control: private, no-cache`. El navegador guarda la respuesta, pero revalida antes de cada uso. Los proxies compartidos no la guardan. |
| Front | Sin cambios. `fetch` con su modo de caché por defecto manda solo `If-None-Match`, y ante un 304 le entrega a JS el 200 que tenía guardado. |
| Alcance | `GET /almacen/kardex`, `GET /almacen/kardex/epp` y `GET /sucursal/movements/<type_m>`. Los `/movements/*` deprecados no cambian. |

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Almacen.py`](../templates/resources/rs_Almacen.py) · [`rs_Sucursal.py`](../templates/resources/rs_Sucursal.py) | Los tres Resources devuelven `kardex_conditional(data_out, code, request.if_none_match)` en vez de `data_out, code`. En swagger aparece la respuesta `304`. |
| **Orquestación** | [`MD_Kardex.py`](../templates/resources/midleware/MD_Kardex.py) | `kardex_conditional` (nueva): solo a los 200 calcula la huella, arma las cabeceras y responde `(None, 304, headers)` si `If-None-Match` coincide en comparación débil. Si no, devuelve `(data_out, 200, headers)`. Cualquier otro código pasa intacto. |
| **DB** | — | Sin cambios. |
| **Modelos** | — | Sin cambios. |

### Reglas

- **Solo los 200 llevan ETag.** Un 400 (validación) o un 401 sale sin `ETag` ni `Cache-Control` y nunca se vuelve 304, aunque el header coincida o sea `*`. El token se valida antes que el ETag.
- **El 304 no lleva cuerpo**: werkzeug quita el cuerpo y las cabeceras `Content-*` de los 304. Sí lleva `ETag` y `Cache-Control`.
- **Comparación débil**, como manda el RFC 9110 para `If-None-Match`: `W/"x"` y `"x"` coinciden; una lista coincide si incluye la huella; `*` coincide.
- **No hace falta `Vary: Authorization`.** La huella se calcula sobre el cuerpo que corresponde al token actual (sus permisos y la BD de tester o normal), así que el 304 sale solo si ese cuerpo es idéntico al que el navegador ya tiene. Si en el mismo navegador cambia el usuario o cambia la BD, el 304 no expone datos de otro.
- El cuerpo del 200 no cambia: es la salida de `get_kardex_api` / `get_sede_movements_api` tal cual.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`; `jwt.decode` sobre el header tal cual).
- **Permisos exactos** (sin cambio respecto a [`permisos_almacen.md`](permisos_almacen.md); `App.Department.Administrator` siempre pasa):
  - `GET /GUI/api/v1/almacen/kardex`: `App.Department.ALMACEN`, `App.Department.ALMACEN-VISUAL`;
  - `GET /GUI/api/v1/almacen/kardex/epp`: `App.Department.Epp`, `App.Department.eppVisual`, `App.Department.eppApprove`;
  - `GET /GUI/api/v1/sucursal/movements/<type_m>`: `App.Department.Sucursal-<id>` (su propia sede) o, para supervisar desde el principal con `id_warehouse`, `App.Department.ALMACEN`, `App.Department.ALMACEN-VISUAL`, `App.Department.Administracion`.
- **Request**: los mismos query params de [`almacen_kardex_ventana.md`](almacen_kardex_ventana.md). El header `If-None-Match` es opcional y lo pone el navegador solo; el código del front no lo manda.
- **Respuestas**: `200` JSON (envelope `{data, msg, error}` + `meta`, sin cambios) con `ETag` y `Cache-Control`. `304` sin cuerpo. `400` / `401` con el envelope JSON y sin `ETag`.

```text
GET /GUI/api/v1/almacen/kardex
Authorization: <jwt>

200 OK
ETag: W/"9f2c41d7a0b3e8c56d1f04ab72e9c3d1"
Cache-Control: private, no-cache
Content-Type: application/json
{"data": {"movements": [...], "products": {...}}, "meta": {...}, "msg": "2069 movimientos del 2026-07-28 al hoy", "error": null}

GET /GUI/api/v1/almacen/kardex            (refresco: el navegador agrega If-None-Match)
Authorization: <jwt>
If-None-Match: W/"9f2c41d7a0b3e8c56d1f04ab72e9c3d1"

304 Not Modified                          (sin cuerpo; fetch() le entrega a JS el 200 guardado)
ETag: W/"9f2c41d7a0b3e8c56d1f04ab72e9c3d1"
Cache-Control: private, no-cache
```

```json
// 400 y 401: sin ETag, igual que antes
{"data": null, "msg": "type_m inválido: 'entradas' (entrada | salida | all)", "error": null}
{"data": null, "msg": null, "error": "No autorizado. Token invalido"}
```

**Gotchas**:

- `fetchWithAuth` hoy no pasa opción `cache`, así que aprovecha el cambio sin tocarlo. Con `cache: "no-store"`, con `cache: "reload"` o con un parámetro anti-caché en la URL (`?_=timestamp`), el navegador no manda `If-None-Match` y cada refresco vuelve a bajar el cuerpo completo.
- En DevTools el refresco sin cambios aparece como `304`, pero `response.status` en JS es `200` y `response.json()` trae el cuerpo guardado. Si algún día el front manda `If-None-Match` a mano, entonces sí recibe el 304 en JS y le toca manejarlo.
- Cuando cambia la ventana (`date_from` por defecto cambia a medianoche), `type_m`, `limit` o cualquier movimiento, el cuerpo cambia y la respuesta es un 200 completo con otro ETag.

## Verificación

Dev (2026-10-28), `Tests/tester_kardex_etag.py`, **54/54**. En cada uno de los tres GET se comprobó: 200 con `W/"…"` y `Cache-Control`, ETag estable entre dos llamadas, `If-None-Match` igual → 304 sin cuerpo y sin `Content-Type`/`Content-Length`, el 304 repite las cabeceras, un ETag distinto → 200 con el mismo cuerpo, lista que lo incluye → 304, sin `W/` → 304, `*` → 304. Además: `type_m` y `limit` distintos dan otro ETag y 200; 400 de validación y 401 (sin token, `/kardex/epp` sin permiso EPP) sin ETag aunque venga `*`; la sede inexistente responde error sin ETag; el `/movements/all` deprecado sigue sin ETag; el 200 es igual a la salida de `get_kardex_api`; cambiar una cantidad cambia la huella. **Costo**: la huella de la ventana por defecto (2,069 movimientos) tarda 4.7 ms por llamada.

Regresión: `Tests/tester_permisos_almacen.py` 18/18 y `Tests/tester_multisede_resolve.py` 64/64. `pyrefly check --python-version 3.11` no marca nada en los archivos tocados.

**Al desplegar** conviene comprobar a través de nginx (gzip): `curl -sD - -o /dev/null -H "Authorization: <jwt>" -H "Accept-Encoding: gzip" https://<host>/GUI/api/v1/almacen/kardex` debe traer `ETag: W/"…"`, y repetirlo con `-H 'If-None-Match: W/"…"'` debe dar `304`.

## Al modificar

- Otro GET pesado que quiera ETag: devolver `kardex_conditional(data_out, code, request.if_none_match)` desde el Resource. Si se usa fuera del kardex, conviene moverlo a un helper común.
- **No meter en el cuerpo nada que cambie en cada llamada** (hora de generación, contadores de tiempo, ids aleatorios): el ETag cambiaría siempre y nunca habría 304. Si hace falta un dato así, dejarlo fuera de la huella.
- Un ETag que se ahorre la consulta necesitaría versión por tabla o sede, actualizada por cada alta, edición y borrado de movimiento. Eso pide DDL y tocar todos los escritores, y se descartó en el grill.

## Notas posteriores

- **2026-10-28 — prod todavía sin `P-128`.** `GET /almacen/kardex` con un token `ALMACEN-VISUAL` responde 200 con `Content-Encoding: gzip` (2,094 movimientos: 462 KB sin comprimir, 51 KB por la red), pero sin `ETag` ni `Cache-Control`. La prueba con `curl` de "Al desplegar" queda para después del deploy; ese token alcanza para hacerla.
