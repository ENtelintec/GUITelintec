# Cancelación de remisiones (`PUT /remission/cancel`) y saldo consumido / disponible en el control de saldos

Fecha: 2026-09-28 · **Estado: hecho y verificado contra dev (32/32 checks HTTP, `Tests/tester_remission_cancel.py`; los testers de saldos previos siguen en verde). Sin DDL.**

Fase **F3** del plan [`planes/control_entregas_ocd_plan.md`](planes/control_entregas_ocd_plan.md) (junta 2026-09-23: "si se cancela una remisión que ya estaba en Control de Saldos, se debe quitar su monto del saldo consumido y devolverlo al disponible"). Se apoya en [`control_saldos_cabecera.md`](control_saldos_cabecera.md) (controles, `remission_amount` en `PUT /remissionBalance`) y en [`control_entregas.md`](control_entregas.md) (lo entregado ya excluía `status = 3`).

## Qué había

`activity_reports.status` tenía el valor `3 = Cancelada` declarado pero **nada lo escribía**; solo existía `DELETE /remission` (borrado físico, sin rastro). El saldo consumido no lo calculaba el back: cada remisión guarda `extra_info.remission_amount` y el front sumaba.

## Decisiones

| Tema | Regla |
|---|---|
| Cancelar | **`PUT /remission/cancel {id, reason}`** → `status = 3` + entrada en `history` (`action: "Cancelación"`, motivo en `comment`, `changes.metadata` con `status` before/after). Solo `administracion`. Ya cancelada → 400; inexistente → 404. |
| Sin reactivación | No hay endpoint para volver a 0. Un error se corrige con una remisión nueva. `PUT /remission` con `status: 3` → 400 "usa `/remission/cancel`" (el status 3 no se escribe por el PUT). |
| Cancelada = inmutable | `PUT /remission`, `PUT /remissionControlTable`, `PUT /remissionBalance` y **`DELETE /remission`** sobre una cancelada → 400 `"La remisión N está cancelada; no se puede …"`. Los anexos (`POST`/`DELETE /remission/attachment`) siguen permitidos (evidencia de por qué se canceló). |
| Devolución del saldo **por exclusión** | El back calcula en `GET /balanceControl` y `GET /balanceControl/<id>`: `consumed_amount` = Σ `extra_info.remission_amount` de las remisiones del control (`balance_control_id`) con `status <> 3`, y `available_amount = contracted_amount − consumed_amount`. Cancelar saca la fila de la suma: **no se inserta ningún movimiento** (el contratado no cambió; un AJUSTE habría doble-contado). `balance_control_movements` sigue significando solo cambios del contratado. |
| Control de entregas | Ya excluía `status <> 3` (F2): al cancelar, lo entregado por partida baja, el control recalcula su status (COMPLETO → ABIERTO) y vuelve a caber una remisión por lo pendiente. La respuesta del cancel trae `delivery_control_id` y `delivery_control_status`. |
| Membresías | La cancelada **conserva** `balance_control_id` y `delivery_control_id`: sigue listada en ambos detalles con `cancelled: true` (rastro), pero sin sumar. |

## Capas tocadas

```
controller  presales/remisions_controller.py           set_remission_status (nuevo: UPDATE status + history)
controller  purchases/balance_control_controller.py    CONTROL_COLUMNS + consumed_amount (subquery, append-only) · get_remissions_summary_by_control gana remission_amount
midleware   MD_Admin_Collections.py                    cancel_remission_from_api (nuevo) · _cancelled_remission_error en los 3 PUT y el DELETE · guard status 3 en PUT /remission
midleware   MD_BalanceControl.py                       _control_to_dict: consumed_amount / available_amount · detalle: remissions[].cancelled / remission_amount
models      api_purchases_models.py                    ReportActivityCancelForm + report_activity_cancel_model
routes      rs_Admin_collections.py                    PUT /remission/cancel (administracion)
```

El subquery de `consumed_amount` castea `remission_amount` a `DECIMAL(15,2)` solo cuando el texto es numérico (`REGEXP`), así una captura vieja con texto no tumba el listado.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `).
- **Respuesta**: siempre JSON `{data, msg, error}`. 401 sin envelope.

### `PUT /remission/cancel` — permiso `administracion`

```json
{ "id": 71, "reason": "El cliente indica que la remisión no le corresponde" }
```

| Código | Cuándo | `data` |
|---|---|---|
| **200** | cancelada | `{"id_remission": 71, "status": 3, "balance_control_id": 6, "delivery_control_id": 3, "delivery_control_status": 0}` · `msg: "Remisión cancelada (ID 71, folio TL-0045-001): El cliente…"` |
| **400** | ya cancelada | `data: {"id_remission": 71, "status": 3}`, `msg: "La remisión 71 está cancelada; no se puede cancelar de nuevo"` |
| **404** | inexistente | `null` |

`balance_control_id` / `delivery_control_id` vienen `null` si la remisión no está en ese control; `delivery_control_status` es el recalculado (0/1/2) o `null`.

### Efectos en otros endpoints

- `GET /balanceControl` y `GET /balanceControl/<id>`: cada control gana **`consumed_amount`** y **`available_amount`** (números, 2 decimales). El detalle lista `remissions[]` con `cancelled` (bool) y `remission_amount` (número o `null` si no se ha capturado). Ya no hace falta sumar en el front; si se sigue sumando, excluir `cancelled`.
- `GET /remission-<id>`: `status: 3` identifica la cancelada (pintar en gris; `history[-1]` trae el motivo).
- `PUT /remission` / `PUT /remissionControlTable` / `PUT /remissionBalance` / `DELETE /remission` sobre cancelada → **400** `error: "remisión cancelada"`, `data.status: 3`.
- `PUT /remission` con `metadata.status = 3` → **400** `"Para cancelar una remisión usa PUT /remission/cancel"`.
- `GET /deliveryControl/<id>`: la cancelada aparece en `remissions[]` con `cancelled: true` y no suma en `items[]` ni en `totals`.

### Gotchas

- `consumed_amount` solo suma remisiones **ligadas al control** (`balance_control_id`) con `remission_amount` capturado vía `PUT /remissionBalance`; una remisión del contrato sin capturar el monto consume 0.
- Cancelar no cambia `contracted_amount` ni crea movimiento: el historial de inyecciones no se toca.

## Al modificar

- **Reactivación** (si algún día se pide): un `PUT /remission/reactivate` que ponga `status = 0` con history; los cálculos se corrigen solos. No relajar los candados de los PUT: son lo que garantiza que una cancelada no se edite "por accidente".
- **Bloquear anexos en canceladas**: agregar `_cancelled_remission_error` en `create_activity_report_attachment_api` / `delete_activity_report_attachment_api`.
- Cualquier consulta nueva que sume montos o cantidades de remisiones debe filtrar `COALESCE(status, 0) <> 3`.
