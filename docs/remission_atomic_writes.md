# Escrituras parciales en `activity_reports` (los módulos ya no se pisan) y limpieza de `custom_fields` al retirar de un control

Fecha: 2026-10-09 · Origen: pregunta de si el control de saldos necesitaba tabla propia para sus filas. **Decisión: no**; se queda en `activity_reports.extra_info` y se corrigen sus dos puntos débiles: (a) escrituras atómicas y (b) valores huérfanos al retirar una remisión de un control.

## Por qué no hay tabla propia para las filas del control de saldos

Las filas del control **son** remisiones: remisiones, control de reportes, control de saldos, controles de saldos/entregas y anexos escriben la misma fila de `activity_reports` ([`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md)). Ventajas de seguir así: una sola fuente de verdad (cancelar/borrar la remisión mueve el saldo sin sincronizar nada; `consumed_amount` excluye `status = 3` en la misma fila), un solo GET para los 3 módulos, las columnas dinámicas (`custom_fields`) caben natural en JSON, la membresía 1 remisión → 1 control ya la da `balance_control_id`, y es el mismo patrón que control de entregas. Una tabla aparte valdría la pena solo si una remisión repartiera su monto entre **varios** controles o hicieran falta reportes pesados por periodo sobre SQL. Queda como desventaja aceptada que `remission_amount` vive en JSON (sin `DECIMAL` ni índice; el `REGEXP` del subquery cubre el texto basura).

## El problema

1. **Se perdían cambios entre módulos.** Cada escritor leía la fila, mezclaba en Python y reescribía `extra_info` **y** `history` completos (más las columnas base). Dos guardados casi simultáneos sobre la misma remisión (p. ej. Cobranza en saldos y Operaciones en control de reportes) → gana el último y desaparecen las llaves y la entrada de historial del otro.
2. **`PUT /remissionControlTable` y `PUT /remissionBalance` reescribían columnas que no editan** (`area`, `status`; saldos además `date`, `folio`, `client_id`…) con lo leído: podían revertir un cambio concurrente, incluida una cancelación (la remisión "des-cancelada").
3. **Subir un anexo de firma a una remisión cancelada la reactivaba** (`firma-realizado` → `status 1`, `firma-recibido` → `2`); los anexos siguen permitidos en canceladas ([`remission_cancel.md`](remission_cancel.md)) pero el status no debía moverse.
4. **(b)** `PUT /balanceControl/remissions` con `remove` dejaba en `extra_info.custom_fields` los valores del control anterior; el GET los seguía devolviendo aunque la remisión ya no estuviera en ese control.

## Capas tocadas

```
controller  presales/remisions_controller.py           patch_activity_report (nuevo; reemplaza a update_activity_report, borrado),
                                                        HISTORY_APPEND_SQL / EXTRA_INFO_OBJECT_SQL / json_param,
                                                        set_remission_status(entrada) con guard status <> 3,
                                                        update_report_activity_files(entrada, files, status=None) con CASE anti-reactivación
controller  purchases/balance_control_controller.py    attach/detach con entrada de history; detach borra $.custom_fields;
                                                        REMISSION_LINK_COLUMNS gana extra_info (append-only)
controller  purchases/delivery_control_controller.py   attach/detach con entrada de history; set_remission_delivery_fields = parche
midleware   MD_Admin_Collections.py                     los 3 PUT de módulo, cancelación, alta/baja de anexos; _cancelled_meanwhile_error
midleware   MD_BalanceControl.py                        _attach_rows y el remove (history con before de cada custom_field)
midleware   MD_DeliveryControl.py                       _remission_history_entry; PUT values manda solo las llaves enviadas
```

Sin cambios en rutas, modelos/forms ni DDL.

## Reglas de escritura (las nuevas)

| Qué | Cómo | Efecto |
|---|---|---|
| Llaves de primer nivel de `extra_info` | `JSON_SET(extra_info, '$."k"', CAST(%s AS JSON), …)` con **solo** las llaves del módulo presentes en el JSON crudo (`_extra_info_updates`) | lo de otros módulos ni se lee ni se reescribe; `null` se guarda como `null` (igual que antes) |
| `extra_info.custom_fields` (saldos) y `extra_info.delivery_fields` (entregas) | `JSON_MERGE_PATCH(<objeto actual>, <parche>)` | solo las llaves enviadas; `null` borra la llave (misma semántica que ya tenía el API) |
| `history` | `JSON_ARRAY_APPEND(history, '$', <entrada>)` | solo crece; nunca se reescribe desde una lectura |
| Columnas base | solo las que el módulo edita (`PUT /remission`: todas las de antes; control table: sin `area`/`status`; saldos: ninguna) | — |
| Guard de cancelada | `WHERE … AND COALESCE(status, 0) <> 3` en `patch_activity_report` y `set_remission_status` | 0 filas → 400 `remisión cancelada` (se canceló entre la lectura y la escritura) |
| `status` desde anexos | solo si la firma lo cambia, con `CASE WHEN status = 3 THEN status ELSE %s END` | una cancelada nunca se reactiva |
| Retirar de un control de saldos | `JSON_REMOVE(extra_info, '$.custom_fields')` en el mismo UPDATE que `balance_control_id = NULL` | `remission_amount` y el resto de `extra_info` se conservan |

El diff que va al `history` se sigue calculando contra la lectura (es una foto del momento); bajo carrera puede omitir un cambio ajeno simultáneo, pero ya no borra entradas.

## Verificación

Contra BD dev por HTTP (`test_client`) + llamadas directas a midleware/controller, con 2 remisiones y 1 control temporales (borrados al final; notificaciones y logs silenciados): **37/37 checks**.
- Bloque de cada módulo sin tocar al resto: `remission_total` vs `remission_amount`, llave legacy intacta, `area`/`status` intactos, history +1 por PUT.
- `custom_fields` como parche (coerción, `null` borra solo esa llave, llave no declarada → 400, diff en history); `consumed_amount`/`available_amount` y el GET aplanado.
- **Lectura vieja determinista**: foto de la fila → otro módulo escribe → saldos guarda con la foto: sobreviven ambos cambios y ambas entradas del history.
- **Concurrencia real**: 2 hilos × 15 PUT (`remissionControlTable` y `remissionBalance`) sobre la misma remisión: 30/30 entradas de history, últimos valores de ambos módulos, `remission_amount` intacto.
- `PUT /remission` escribe base + su bloque y conserva saldos.
- (b) `remove` borra `custom_fields`, conserva `remission_amount`, history con `before` de cada columna.
- Cancelación: PUT con lectura previa a la cancelación → 400 sin cambios; doble cancelación → 400; status sigue 3.
- Anexos: firma en cancelada no cambia status (sí guarda `files` y history); firma en activa sí; borrar anexo no toca status.
- `delivery_fields` como parche.

Regresión con los testers previos (crean y borran sus propios datos; dev no guarda controles de entregas persistentes, la tabla está vacía pero con esquema completo, así que **no hace falta SQL**): `tester_delivery_control` 71/71 (cubre `attach`/`detach` de entregas, `values`, re-adopción tras cancelar), `tester_control_saldos_sin_contrato` 50/50, `tester_remission_cancel` 32/32, `tester_balance_movement` 31/31, `tester_balance_vigencia` 30/30.

`pyrefly` 0 errores en los 6 archivos.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Respuestas JSON `{data, msg, error}`.
- **Sin endpoints nuevos ni cambios de shape.** Requests y respuestas 200 iguales que antes.
- **400 nuevo (carrera con una cancelación)** en `PUT /remission`, `PUT /remissionControlTable`, `PUT /remissionBalance`: la remisión se canceló entre que el back la leyó y la escribió; no se guardó nada. Mismo `error` que el 400 de cancelada que ya existía, así que basta la rama actual:

  ```json
  { "data": {"id_remission": 71, "status": 3},
    "msg": "La remisión 71 está cancelada o ya no existe; no se puede actualizar",
    "error": "remisión cancelada" }
  ```

  `PUT /remission/cancel` doble y simultáneo → el segundo recibe ese mismo 400 (`"…no se puede cancelar de nuevo"`).
- **`PUT /balanceControl/remissions` con `remove`**: además de sacar la remisión, **borra sus valores de columnas dinámicas** (`custom_fields`); si se vuelve a agregar hay que capturarlos de nuevo. El `history` de la remisión guarda cada valor borrado (`{"field": "custom_fields.<key>", "before": …, "after": null}`). `remission_amount` **no** se borra.
- **`POST /remission/attachment-<id>` con firma sobre una remisión cancelada**: 200 como siempre, pero `status` se queda en 3 (antes pasaba a 1/2).
- **`PUT /deliveryControl/values`**: mismo contrato; ahora solo se escriben las llaves enviadas (`data.delivery_fields` sigue siendo la vista resultante).

### Gotchas

- Lo que **sigue** siendo "gana el último": la **misma** llave escrita por dos usuarios a la vez, y las columnas base que editan tanto `PUT /remission` como `PUT /remissionControlTable` (`date`, `folio`, `client_id`, `plant`, `location`, `general_description`, `comments`, `quotation_id`, `contract_id`).
- La lista `files` de anexos todavía se reescribe completa: dos subidas **en paralelo** a la misma remisión pueden perder una entrada (ver Pendientes). Subir anexos en serie mientras tanto.

## Al modificar

- **Escritor nuevo sobre `activity_reports`**: usar `patch_activity_report` (o `HISTORY_APPEND_SQL` + `JSON_SET` en un UPDATE propio). **Nunca** escribir `extra_info` ni `history` completos a partir de una lectura.
- **Columna base editable nueva**: agregarla a `_PATCHABLE_COLUMNS` (se interpola en el SQL; la whitelist es la protección).
- **Objeto anidado en `extra_info` editado por llaves**: patrón `JSON_MERGE_PATCH` de `custom_fields` / `delivery_fields` (`null` = borrar). Las llaves de primer nivel salen de los mapas `_*_EXTRA_KEY_MAP` (código, no del usuario); no meter llaves con `"` en esos mapas (rompen el path `$."k"`).
- **Escritura de un módulo**: mantener el guard `status <> 3` y tratar 0 filas como "cancelada entretanto".
- **Agregar llaves al `SELECT` de membresía** (`REMISSION_LINK_COLUMNS`): solo al final (el midleware indexa por posición).

## Pendientes

- **[back] Lista `files` de anexos**: sigue siendo lectura-modificación-escritura. Arreglo propuesto: `JSON_ARRAY_APPEND` cuando la subida no reemplaza (el caso de subidas en paralelo) y comparar-y-reintentar para reemplazo/borrado.
- **[decisión] `custom_fields` al adoptar una remisión que viene de un control cancelado** (flujo "contrato tardío" de [`control_saldos_sin_contrato.md`](control_saldos_sin_contrato.md)): hoy se **conservan**, así que reaparecen si el control nuevo declara las mismas llaves y quedan como basura si no. Decidir si se limpian también al adoptar.
- **[decisión] `delivery_fields` al retirar de un control de entregas**: hoy se conservan (equivalente de (b) para entregas, no pedido).
- **[back, opcional] Columnas base entre `PUT /remission` y `PUT /remissionControlTable`**: si llegara a doler, bloqueo optimista (columna `version` = DDL, o comparar-y-reintentar).
