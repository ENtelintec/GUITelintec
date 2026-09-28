# Control de saldos: extensión de vigencia en el ledger (`POST /balanceControl/movement` con `new_end_date`, tipo 3 VIGENCIA) y aviso "por vencer"

Fecha: 2026-09-28 · **Estado: hecho y verificado contra dev (30/30 checks HTTP, `Tests/tester_balance_vigencia.py`; los testers previos de saldos siguen en verde). DDL: las dos columnas de fecha vienen en [`control_entregas_ocd.sql`](../scripts_db_handle/control_entregas_ocd.sql) (corrido en dev; test/prod pendientes).**

Fase **F4** del plan [`planes/control_entregas_ocd_plan.md`](planes/control_entregas_ocd_plan.md) (junta 2026-09-23: "en la misma ventana donde se agrega saldo debe poder extenderse la fecha de fin y anotarse qué cambió: saldo, fecha o ambos; con historial de cuándo se registró y la fecha en que Ternium hizo el cambio; el aviso de contrato por vencer debe tomar la nueva fecha"). Extiende [`control_saldos_movimientos.md`](control_saldos_movimientos.md).

## Decisiones

| Tema | Regla |
|---|---|
| Un solo ledger | `balance_control_movements` gana `previous_end_date` / `new_end_date` (NULL cuando la fila no tocó la fecha) y el tipo **`3 = VIGENCIA`**. Sigue inmutable. Descartada una tabla de extensiones aparte. |
| Tres formas de mover | `type 1/2` con `amount` (como hoy) · `type 3` con `new_end_date` y **sin `amount`** (saldo intacto: `previous = resulting`) · `type 1/2` con `amount` **y** `new_end_date` = una sola fila que cambia ambos. |
| Validación de la fecha | `YYYY-MM-DD`; obligatoria en tipo 3; **distinta** a la `end_date` actual (400 "nada que cambiar"); **no anterior** a `start_date`. Puede ser anterior a la actual (recorte) y puede partir de `end_date` NULL. |
| Qué cambió | Derivado por fila: `changed: ["amount"]`, `["end_date"]` o `["amount", "end_date"]`, tanto en la respuesta del POST como en `movements[]` del detalle. `history` del control gana `changes` con before/after de `contracted_amount` y/o `end_date`. |
| Dos fechas | `movement_date` = fecha en que el cliente hizo el cambio (la captura el usuario, default hoy); `timestamp` = cuándo se registró en el sistema. Igual que ya funcionaba para el dinero. |
| Un solo escritor | **`PUT /balanceControl` ya no acepta `end_date`** → 400 "la fecha de fin solo cambia con POST /balanceControl/movement". El `POST` del control sigue aceptándola como valor inicial. |
| Bloqueo optimista | Igual que el monto: `expected_balance` (409 si no coincide) y `UPDATE … WHERE contracted_amount = <leído> AND is_active = 1` (0 filas → 409). La fecha se escribe en ese mismo `UPDATE`; si el `INSERT` del movimiento falla, la reversa restaura monto **y** fecha (incluso NULL). |
| Aviso "por vencer" | Listado y detalle ganan **`days_to_end`** = `DATEDIFF(end_date, hoy)` (negativo = vencido, `null` sin fecha). Filtro **`?expiring_days=N`** en `GET /balanceControl` (controles con `end_date` a ≤ N días, vencidos incluidos). Sin correos: el front decide el color. |
| Permisos | Sin cambio: solo `administracion`. |

## Capas tocadas

```
controller  purchases/balance_control_controller.py   MOVEMENT_COLUMNS + previous_end_date/new_end_date (append-only) · insert_balance_control_movement escribe ambas
                                                       update_balance_control_amount_optimistic(set_end_date, end_date) · CONTROL_COLUMNS + days_to_end · get_balance_controls(expiring_days)
midleware   MD_BalanceControl.py                       MOVEMENT_TYPES[3] · create_balance_movement_from_api (validación de fecha, changed, history.changes, reversa) · PUT bloquea end_date
                                                       _movement_to_dict.changed · _control_to_dict.days_to_end · listado lee expiring_days
models      api_balance_control_models.py              BalanceControlMovementForm: type AnyOf 1/2/3, new_end_date; api.model
routes      rs_Admin_collections.py                    GET /balanceControl lee ?expiring_days
```

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permiso `administracion` para el POST; lecturas como siempre.
- **Respuesta**: siempre `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400 de midleware, objeto por campo en 400 de form.

### `POST /balanceControl/movement` — cambios

```json
{ "id_control": 6, "type": 3, "new_end_date": "2026-11-30", "movement_date": "2026-09-22",
  "reason": "Extensión del contrato", "document": "Adenda 3", "expected_balance": 1250000.00 }
```

| Campo | Tipo | Notas |
|---|---|---|
| `type` | `1` \| `2` \| `3` | `3` = VIGENCIA (solo fecha) |
| `amount` | number | obligatorio en 1/2; **no mandarlo** en 3 (400 si va) |
| `new_end_date` | `YYYY-MM-DD` | obligatoria en 3, opcional en 1/2 |
| `movement_date` | `YYYY-MM-DD` | fecha en que el cliente hizo el cambio (default hoy) |
| `reason`, `document`, `expected_balance` | | igual que antes |

| Código | Cuándo | `data` |
|---|---|---|
| **201** | registrado | `{"id_control": 6, "id_movement": 14, "type": 3, "type_label": "VIGENCIA", "movement_date": "2026-09-22", "amount": 0.0, "previous_balance": 1250000.0, "resulting_balance": 1250000.0, "contracted_amount": 1250000.0, "previous_end_date": "2026-09-30", "new_end_date": "2026-11-30", "end_date": "2026-11-30", "days_to_end": 63, "changed": ["end_date"]}` · con `type 1` + `amount` + `new_end_date`: `changed: ["amount", "end_date"]` y ambos montos/fechas |
| **400** | validación | `error: ["una VIGENCIA requiere new_end_date (YYYY-MM-DD)"]` · `["una VIGENCIA no lleva amount (…)"]` · `["new_end_date 2026-09-30 es la fecha de fin actual; nada que cambiar"]` · `["new_end_date 2026-01-01 no puede ser anterior a start_date 2026-03-09"]` · `["new_end_date: se esperaba una fecha YYYY-MM-DD"]` · `{"type": ["type debe ser 1 (INYECCION), 2 (AJUSTE) o 3 (VIGENCIA)"]}` (form) |
| **400** / **404** / **409** | control cancelado / inexistente / carrera perdida | igual que [`control_saldos_movimientos.md`](control_saldos_movimientos.md) |

`previous_end_date` y `new_end_date` vienen `null` en un movimiento que no tocó la fecha; `end_date` siempre trae la vigente tras el movimiento.

### `GET /balanceControl` / `GET /balanceControl/<id>` — cambios

- Cada control gana **`days_to_end`** (int, negativo si venció, `null` sin `end_date`).
- Query nuevo `?expiring_days=30` (combina con los filtros existentes).
- `movements[]` del detalle: cada fila gana `previous_end_date`, `new_end_date` y `changed`. `type_label` `"VIGENCIA"` para el tipo 3; `/balanceControl/catalogs` lo lista en `movement_types`.
- `history[]` del control: las entradas de movimiento traen `changes: [{field, before, after}]` (`contracted_amount` y/o `end_date`).

### `PUT /balanceControl` — cambio

`metadata.end_date` → **400** `error: ["end_date es inmutable (la fecha de fin solo cambia con POST /balanceControl/movement, tipo 3 VIGENCIA)"]`. La pantalla de cabecera debe quitar ese campo del formulario de edición (queda solo en el alta).

### Gotchas

- Mandar `expected_balance` también en una VIGENCIA: protege contra un movimiento de dinero concurrente aunque la fecha no toque el saldo.
- `days_to_end` se calcula con la fecha del servidor de BD (`CURDATE()`), no con la del navegador.

## Al modificar

- **Bloquear recortes de fecha** (si Cobranza lo pide): en `create_balance_movement_from_api`, junto a la validación contra `start_date`, exigir `new_end_date > previous_end_date`.
- **Extender también `start_date`**: mismo patrón (columnas `previous_start_date`/`new_start_date` en el ledger, `set_end_date` → parámetro genérico); no reabrir el `PUT`.
- No agregar `UPDATE`/`DELETE` sobre `balance_control_movements`: un error de fecha se corrige con otra VIGENCIA.
