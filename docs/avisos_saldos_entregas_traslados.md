# Avisos de sistema: barrido diario de saldos por vencer y saldo bajo, OCD por vencer y traslados con diferencias (`GET /balanceControl` lo dispara)

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (35/35 checks, `Tests/tester_balance_alerts.py`, con la notificación capturada; regresión en verde: `tester_balance_vencido` 33/33, `tester_balance_vigencia` 30/30, `tester_balance_movement` 31/31, `tester_delivery_vencimiento` 26/26, `tester_control_saldos_sin_contrato` 50/50). Sin DDL: las marcas viven en `extra_info.notified` de `balance_controls` / `delivery_controls`; `files/flags_daemons.json` gana `flag_balance` / `last_date_balance`.**

Fase **F2** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "notificaciones de fecha de vigencia de control de saldos a los 2 meses, al 1 mes y a los 15 días el último", "notificaciones de porcentajes de contrato, 25 % de saldo"; más el aviso de traslados sin resolver que pidió el front en `P-145` y el de OCD por vencer decidido en el grill). Misma receta que [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md) y [`cda_alertas_y_fotos.md`](cda_alertas_y_fotos.md): un hilo diario que escribe una "Notificación de sistema" a un permiso. Usa `validity_status` / `days_to_end` de [`control_saldos_vencido_y_monto.md`](control_saldos_vencido_y_monto.md) y `days_to_due` de [`control_entregas_vencimiento.md`](control_entregas_vencimiento.md).

## Qué hace

| Fuente | Condición | Línea | Destinatarios |
|---|---|---|---|
| Control de saldos **activo** | `end_date` a **60, 30 o 15 días** o menos (vencido incluido) | `[Saldos] Control de saldos 6 (AUTO PESQUERIA, 6700293122): vence el 2026-12-15 (faltan 24 días)` · `…: venció el 2026-10-19 (hace 3 días)` | `administracion` |
| Control de saldos **activo** | `available_amount / contracted_amount ≤ 25 %, 10 % o 0` | `[Saldos] Control de saldos 6 (…): saldo disponible 180,000.00 de 1,250,000.00 MXN (14 %)` · `… (0 %) — saldo agotado` | `administracion` |
| Control de entregas **abierto** (`status 0`) con `due_date` | `due_date` a 60, 30 o 15 días o menos | `[Entregas] Control de entregas 3 (OCD-2026-007, TERNIUM): vence el … (faltan N días)` | `administracion` |
| Traslado `RECIBIDO CON DIFERENCIAS` (`status 2`) | 1 día o más desde la recepción sin resolver | `[Traslados] Traslado TR-0007 (Principal → Sucursal 2) recibido con diferencias el 2026-10-20: 2 día(s) sin resolver` | `almacen` + `administracion` |

- **Una notificación por audiencia y por día**: "Notificaciones de sistema — Control de saldos y entregas" (una línea por control) y "Notificaciones de sistema — Traslados con diferencias sin resolver". Nada si no hay líneas. Sin correo (`P-095` aparte).
- **Una vez por umbral y por control**: cada umbral cruzado deja una marca `extra_info.notified["days_60" | "days_30" | "days_15" | "pct_25" | "pct_10" | "pct_0"] = {"at": "YYYY-MM-DD", "ref": …}`. Un control a 10 días sin marcas genera **una** línea y marca los tres umbrales de días a la vez; al día siguiente no repite.
- **La marca guarda la referencia que la hizo válida** y solo vale mientras coincida: `ref` = `end_date` para los días (saldos) / `due_date` (entregas), y `contratado#id del último movimiento de dinero` para los porcentajes. Así una **VIGENCIA** (cambia `end_date`), una **INYECCIÓN o AJUSTE** (cambia el id del último movimiento) o un **`due_date` nuevo** vuelven a armar el aviso sin que los endpoints de movimiento tengan que limpiar nada. Es el "VIGENCIA limpia las de días, INYECCIÓN las de porcentaje" del grill, implementado por comparación.
- **Las marcas solo se escriben si la notificación se guardó**; si el `INSERT` falla, el umbral se reintenta al día siguiente. Los traslados no llevan marca: se repiten cada día hasta `PUT /almacen/transfer/<id>/resolve`.
- **Disparo**: la primera llamada del día a **`GET /admin/collections/balanceControl`** (la lista que Cobranza abre a diario) lanza el hilo `NotificationsSearch(type_n="balance")`; banderas `flag_balance` (False mientras corre) y `last_date_balance` en `files/flags_daemons.json` (`start_daily_sweep`, reutilizable para otros barridos). Cualquier fallo del disparo se registra en el log de admin y **nunca tumba la lista**. El hilo corre con el token de quien disparó (un `is_tester` barre la BD de test).
- Umbrales fijos en código (`DAY_THRESHOLDS`, `PCT_THRESHOLDS`); los 60 días coinciden con `VALIDITY_EXPIRING_DAYS`. Fechas con la hora del servidor del API en `America/Mexico_City`.

## Capas tocadas

```
midleware   MD_BalanceAlerts.py (nuevo)                    build_balance_alerts · build_delivery_alerts · transfer_alert_lines / build_transfer_alerts · run_balance_sweep(notify=)
daemon      daemons/NotificationsSearch.py                 case "balance" (+ flag_balance) · start_daily_sweep(type_n, data_token, starter=) (receta de médicos/CDA, genérica)
controller  purchases/balance_control_controller.py        get_last_amount_movement_ids · set_balance_control_notified (JSON_SET '$.notified')
controller  purchases/delivery_control_controller.py       set_delivery_control_notified
routes      rs_Admin_collections.py                        GET /balanceControl llama start_daily_sweep("balance") en try/except
archivo     files/flags_daemons.json                       + flag_balance / last_date_balance (se crean solos)
```

Reusa `_control_to_dict` de `MD_BalanceControl` y `MD_DeliveryControl` (los mismos `days_to_end` / `days_to_due` / `available_amount` que ve el front) y `get_transfers_db` de almacén.

## Contrato mínimo para el front

- No hay endpoint nuevo. Las notificaciones salen por el mecanismo de siempre: `GET /misc/notifications/...` por permiso (`body.app` = `["administracion"]` o `["almacen", "administracion"]`, `body.title` = `"Notificaciones de sistema"`, `body.msg` = encabezado + una línea por renglón, `body.sender_id` = 0). El front las pinta como las de médicos y CDA.
- `GET /balanceControl` y `GET /deliveryControl*` siguen igual; `extra_info.notified` viaja dentro de `extra_info` del control (informativo; el front puede ignorarlo o mostrar "avisado el …").
- `GET /balanceControl` puede tardar unos milisegundos más la **primera vez del día** (escribe las banderas y arranca el hilo); el resto del día no cambia.

### Gotchas

- Si nadie abre la lista de controles un día, ese día no hay barrido; al siguiente se ponen al corriente (un umbral cruzado se avisa aunque haya pasado de largo).
- Un control **cancelado** (saldos `is_active = 0`, entregas `status 2`) no avisa; uno **completo** de entregas (`status 1`) tampoco.
- Borrar la marca a mano (`JSON_REMOVE(extra_info, '$.notified')`) vuelve a avisar en el siguiente barrido.
- El permiso propio de Cobranza para estos avisos es `P-155`; mientras, `administracion`.

## Al modificar

- **Otro umbral** (p. ej. 50 % de saldo): agregarlo a `PCT_THRESHOLDS`; la marca `pct_50` nace sola.
- **Otra fuente** (p. ej. exámenes de vehículos): una función `build_<x>_alerts(data_token) -> (lines, updates, error)` en `MD_BalanceAlerts` y sumarla en `run_balance_sweep`, con su permiso; si no necesita marcas, seguir el patrón de traslados.
- **Correo además de la notificación in-app** (`P-095`): en `run_balance_sweep`, junto a `notify`, mandar el mismo `msg` por SES (`send_email_ses`) a la lista que decida administración; no mover las marcas antes de que al menos un canal se guarde.
- **Otro disparo** (cron del contenedor, `P-139`): llamar `run_balance_sweep(data_token_de_sistema)` directo o `start_daily_sweep("balance", …)`; las banderas evitan duplicados aunque también lo dispare la lista.
- Migrar médicos/CDA a `start_daily_sweep` solo cambia nombres de banderas (`flag_medical` / `last_date_medicals` no siguen el patrón `<type_n>`); no es obligatorio.

## Notas posteriores

- **2026-10-22 — Correo (`P-095`)**: la notificación "Control de saldos y entregas" sale también por SES a gerentes y jefes de Administración, solo en prod y sin token tester; las marcas se escriben si sale **al menos un canal** (antes solo la notificación) → [`avisos_saldos_correo.md`](avisos_saldos_correo.md). `run_balance_sweep` gana `send_email=` (stub en pruebas) y la llave `email` en su resultado. Traslados sin correo.
- **2026-10-28 — destinatarios (`P-155`)**: la notificación de saldos y entregas se guarda con `app = ["administracion", "admincobranza"]`, así que también la ven los usuarios con `App.Department.adminCobranza` (permiso nuevo, alta en `P-207`). Los traslados y el correo no cambian. → [`permisos_administracion.md`](permisos_administracion.md)
