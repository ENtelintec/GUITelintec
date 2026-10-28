# Correo SES del aviso diario de saldos y entregas (gerentes y jefes de Administración)

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (18/18 checks, `Tests/tester_balance_alerts_email.py`: destinatarios reales de dev en solo lectura; envío, notificación y marcas con stubs; regresión `tester_balance_alerts` 35/35). Sin DDL ni endpoint nuevo.** Cierra la parte de correo de `P-095`.

Sigue a [`avisos_saldos_entregas_traslados.md`](avisos_saldos_entregas_traslados.md) (F2 de [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md)) y usa el helper de [`nomina_correo_ses.md`](nomina_correo_ses.md) (SES en producción desde el 2026-10-21, `P-036`).

## Decisiones (usuario, 2026-10-22)

| Tema | Decisión |
|---|---|
| Qué sale por correo | Solo la notificación **"Control de saldos y entregas"**: vigencia de saldos a 60/30/15 días, saldo al 25/10/0 % y OCD por vencer. **Traslados no** (se repiten a diario hasta resolverse). Médicos y CDA, fuera. |
| A quién | **Gerentes y jefes de Administración**: empleados `activo` con `department_id = 3` (Administración) cuyo `puesto` empieza con `GERENTE` o `JEFE`, sin distinguir mayúsculas. Hoy en dev y prod son Carolina Torres (Gerente de Administración, `admon01@`) y Georgina López Sáenz (Jefe de Administración). Los jefes de RRHH y Operaciones quedan fuera. |
| Qué correo | Solo los **institucionales** (`@telintec.com.mx`) de `employees.email`, que es una lista: [`empleados_correos_y_nomina_activos.md`](empleados_correos_y_nomina_activos.md). Un solo correo con todos en `To`. |
| Dónde se manda | **Solo con `environment == "prod"` y sin token tester**: los destinatarios son personas reales y dev/test tienen copias de controles reales. Fuera de eso el correo sale `skipped` y la notificación in-app sigue igual. |

## Qué hace

- `run_balance_sweep` guarda la notificación in-app como siempre y, con el **mismo `msg`**, llama a `email_balance_alert`. Asunto `Avisos de control de saldos y entregas — AAAA-MM-DD`; el cuerpo es el texto de la notificación más un pie de correo automático. Texto plano.
- **Las marcas** (`extra_info.notified`) se escriben si **al menos un canal salió** (notificación guardada **o** correo enviado). Si fallan los dos, no hay marcas y el umbral se reintenta al día siguiente. Antes dependían solo de la notificación.
- `email.status`: `sent` · `failed` (SES rechazó, sin destinatarios o error de BD; va a `errors` y al log) · `pending` (SES sin configurar, falta `SES_SENDER`) · `skipped` (fuera de prod o token tester). `pending` y `skipped` no son error.
- El log del barrido (`files/logs/admin`) ahora dice `correo <status> a [<destinatarios>]`, y el dict que devuelve `run_balance_sweep` gana la llave `email`.

## Capas tocadas

```
midleware   MD_BalanceAlerts.py              EMAIL_* (depto 3, GERENTE/JEFE, dominio, asunto) · balance_alert_recipients ·
                                             email_balance_alert(msg, data_token, send=None) · run_balance_sweep(send_email=None)
controller  employees/employees_controller   get_active_employees_by_puesto(department_id, puesto_prefixes, data_token)
misc        Functions_Mail.py                sin cambios (send_email_ses / is_ses_configured)
```

`send_email_ses` y `email_balance_alert` se resuelven **al llamar** (defaults `None`), así que una prueba puede parchear `MD_BalanceAlerts.send_email_ses` y cubrir también el hilo que lanza `GET /balanceControl`.

## Contrato mínimo para el front

No hay endpoint nuevo ni cambia ninguna respuesta: `GET /admin/collections/balanceControl` sigue disparando el barrido la primera vez del día y las notificaciones in-app no cambian. Nada que integrar.

## Al modificar

- **Otro destinatario o regla**: `EMAIL_DEPARTMENT_ID` / `EMAIL_PUESTO_PREFIXES` / `EMAIL_DOMAIN` en `MD_BalanceAlerts`. Si cambia el puesto de alguien en `employees`, el correo lo sigue solo. Si administración prefiere una lista fija, cambiar solo `balance_alert_recipients`.
- **Traslados por correo**: llamar `send_email` en la rama de `t_lines` con su propia regla de destinatarios (almacén no tiene gerente en el depto 3).
- **Permiso propio de Cobranza** (`P-155`): no afecta al correo, que va por puesto y no por permiso.
- **Probar sin mandar correo real**: pasar `send_email=` o parchear `MD_BalanceAlerts.send_email_ses`. **Ojo**: el guard lee el `environment` de `constants.py`, que se commitea en `"prod"` para desplegar. Un tester corrido mientras está en `"prod"`, aunque redirija la BD a dev, **sí** mandaría el correo a los destinatarios reales si no hay stub.

## Notas posteriores

- **2026-10-28 — `environment` sale del `.env`** ([`entorno_desde_env.md`](entorno_desde_env.md)). Ya no se commitea `"prod"` en `constants.py`: el guard lee `API_ENVIRONMENT` del `.env` de la máquina (o de la variable del sistema). Un tester local solo abre el correo si ese `.env` dice `prod`; para forzar dev sin editarlo, `API_ENVIRONMENT=dev`. El consejo del stub sigue en pie.
