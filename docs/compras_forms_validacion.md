# Forms de Compras que aceptaban `{}` — `PUT /order/status`, `PUT /application/order/status` y `POST /purchaseManagement`

> `P-197`, detectado el 2026-10-27 al probar los permisos de Compras ([`permisos_compras_y_baja.md`](permisos_compras_y_baja.md)): una corrida que mandó `{}` dejó registros vacíos y avisos en dev. Había dos causas:
>
> - **Los dos PUT de estatus no llamaban `validator.validate()`**: leían `validator.data` directo. El form ya pedía `id`, pero nadie lo revisaba. Un body sin `id` respondía 200, no tocaba filas y dejaba un aviso "ID None". Son los únicos dos endpoints del repo con ese patrón.
> - **El form del alta de gestión de compras tenía todos los campos opcionales**, así que `{}` creaba un registro vacío. Decisión del usuario (2026-10-28): el back exige lo mismo que el formulario del front.
>
> Sin DDL. El front no cambia: ya manda todo lo que ahora se exige.

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py) | Los dos PUT de estatus llaman `validate()` y responden 400 con el envelope del área. `PUT /application/order/status` usa el form nuevo `POApplicationUpdateStatusForm`. |
| **Orquestación** | — | Sin cambios: los midleware reciben el mismo `data` que antes. |
| **DB** | — | Sin cambios. |
| **Modelos** | [`api_purchases_models.py`](../static/Models/api_purchases_models.py) | `PurchaseOrderUpdateStatusForm.approved` pasa a opcional, porque el endpoint no lo guarda y el front no lo manda. `POApplicationUpdateStatusForm` (nuevo) lo deja obligatorio, porque ahí sí se guarda. |
| | [`api_purchase_management_models.py`](../static/Models/api_purchase_management_models.py) | `PurchaseManagementPostForm` gana tres validadores en línea: `description` no vacía, `request_date` como fecha real `YYYY-MM-DD`, y al menos uno de `amount_usd` / `amount_mxn`. El `api.model` del POST marca esos campos. El PUT sigue siendo parcial y no los exige. |

### Reglas

- **Activar `validate()` en los PUT de estatus no podía romper a nadie.** Por eso:
  - `approved` quedó opcional en `PUT /order/status`. Con el form tal cual, la llamada del front habría recibido 400, porque solo manda `id`, `history` y `status`.
  - Se revisó que el `history` que el front reenvía pase el form. Las 12 OC y 4 solicitudes de dev, y las 5 y 4 de test, pasan completas por su form. Las entradas que escribe el back llevan siempre `user`, `event` y `date` con `format_timestamps`.
- **Un `history` mal formado ahora da 400.** Por ejemplo, una entrada sin `event` o con la fecha en otro formato. Antes pasaba sin revisión.
- **El monto 0 cuenta como capturado**, igual que en el front: solo falla si los dos montos vienen `null` o ausentes.
- La fecha de solicitud se valida como fecha real (`2026-13-01` → 400), no solo por el patrón.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`; `jwt.decode` sobre el header tal cual). Base `/GUI/api/v1/admin/collections`. Body JSON.
- **Permisos exactos** (sin cambio): `App.Department.Administracion` o `App.Department.adminCompras` en los tres endpoints (`App.Department.Administrator` siempre pasa).
- **400 nuevo**: envelope `{"data": null, "msg": "Estructura de datos inválida", "error": {<campo>: [<mensajes>]}}`. Con un 400 no se escribe nada y no se crea ningún aviso.

### `PUT /order/status`

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id` | int | sí | `id_order` de la OC. |
| `status` | int | sí | `>= -1`. |
| `history` | lista de `{user: int, event: str, date: "YYYY-MM-DD HH:MM:SS", comment?: str}` | no (default `[]`) | El historial que trajo el GET; el back agrega la entrada "Cambio de estado". |
| `approved` | int | **no** | Si viene, `>= -1`. Este endpoint no lo guarda. |

### `PUT /application/order/status`

Igual que el anterior, pero **`approved` es obligatorio** (`>= -1`), porque se guarda en la solicitud. Es lo que ya manda `ApprovePurchases` (`{id, status: 1, history, approved: 1}`).

```json
// 400: {} (antes respondía 200 y dejaba un aviso "ID None")
{"data": null, "msg": "Estructura de datos inválida", "error": {"id": ["This field is required."], "status": ["Invalid id"]}}
// 400: application sin approved
{"data": null, "msg": "Estructura de datos inválida", "error": {"approved": ["Invalid id"]}}
```

### `POST /purchaseManagement`

Ahora exige lo mismo que `compraPmSchema` del front. Los demás campos siguen opcionales y sin cambio.

| Campo | Regla | Mensaje |
|---|---|---|
| `description` | texto no vacío (sin contar espacios) | "La descripción es obligatoria" |
| `request_date` | fecha real `YYYY-MM-DD` | "La fecha de solicitud es obligatoria (YYYY-MM-DD)" |
| `amount_usd` / `amount_mxn` | al menos uno distinto de `null` (0 vale) | "Captura al menos un monto, en USD o en MXN" (en `amount_mxn`) |

```json
// 400: {}
{"data": null, "msg": "Estructura de datos inválida",
 "error": {"description": ["La descripción es obligatoria"],
           "request_date": ["La fecha de solicitud es obligatoria (YYYY-MM-DD)"],
           "amount_mxn": ["Captura al menos un monto, en USD o en MXN"]}}
```

La respuesta del alta no cambia: `201` con `{"data": {"id_pm": N}, ...}` ([`gestion_de_compras.md`](gestion_de_compras.md)). `PUT /purchaseManagement` sigue aceptando cambios parciales.

## Verificación

Dev (2026-10-28), `Tests/tester_compras_forms.py`, **29/29**. Los midleware se reemplazan por espías, así que no hay escrituras.

- **`PUT /order/status`**: `{}` → 400 sin llamar al midleware y con error en `id`. El body del front sin `approved` pasa y el midleware recibe el mismo `data` (fecha del historial como texto, `approved` `None`). Con `approved` pasa; con `approved < -1`, sin `status` o con una fecha de historial mal formada → 400.
- **`PUT /application/order/status`**: `{}` → 400. El body de `ApprovePurchases` pasa; sin `approved` → 400.
- **Historial real**: todas las filas de `purchase_orders` y `pos_applications` de dev y de test validan con su form.
- **`POST /purchaseManagement`**: `{}` → 400 con los tres errores y sin crear nada. El body del front (`aCompraPmPayload`, vacíos en `null`) pasa sin cambios en `data`; también pasan solo `amount_usd` y monto 0. Sin montos, descripción en blanco o `null`, fecha `null`, `2026-13-01` o `28/10/2026` → 400.
- **`PUT /purchaseManagement`**: un cambio parcial sigue pasando.

Regresión: `Tests/tester_permisos_compras_baja.py` 113/113 y `Tests/tester_po_match_cantidades.py` 41/41. `pyrefly check --python-version 3.11` sigue en 166 errores (ninguno en lo tocado). El historial de prod no se revisó: prod no se consultó, y dev es copia de prod del 2026-10-09.

## Al modificar

- **Todo endpoint con form llama `validate()` antes de leer `validator.data`.** Leer `data` sin validar acepta cualquier cosa.
- Quien escriba en `purchase_orders.history` o `pos_applications.history` debe usar `user` (int), `event` (texto) y `date` con `format_timestamps`. Si no, el siguiente cambio de estatus de esa fila dará 400.
- Si el formulario del front cambia sus obligatorios (`compraPmSchema`), cambiar también `PurchaseManagementPostForm` y su `api.model`.
