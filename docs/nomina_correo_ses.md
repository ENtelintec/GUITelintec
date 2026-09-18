# Nómina: correo al empleado por AWS SES (canal `email` de `POST /rrhh/payroll/notify`)

Fecha: 2026-09-17 · **Estado: hecho y verificado contra dev con SES y S3 simulados (18/18 checks, `Tests/tester_nomina_ses.py`). Falta configurar SES en `.env` para que el canal deje de reportarse como pendiente.**

Segunda etapa de [`nomina_gestion_archivos_y_notificacion.md`](nomina_gestion_archivos_y_notificacion.md): el mismo `POST /payroll/notify` con `channels: ["email"]` ahora **envía el correo** con el pdf/xml del recibo adjuntos (leídos de `S3_RH_BUCKET`). `POST /payroll/mail` (borrador Outlook + SharePoint, deprecado desde 2026-09-07) **queda retirado** junto con `create_mail_payroll`, `CreateMailForm`/`create_mail_model` y `create_mail_draft_with_attachment` de `Functions_Sharepoint.py`.

## Configuración (`.env`, la lee `secrets` al arrancar)

| Llave | Obligatoria | Qué es |
|---|---|---|
| `SES_SENDER` | sí | remitente, **identidad verificada en SES** (p.ej. `nomina@telintec.com.mx`). Sin ella `is_ses_configured()` es `False` y el canal se reporta en `channels_pending` — el endpoint nunca truena por falta de config |
| `SES_REGION` | no | región de SES si es distinta a la default de boto (p.ej. `us-east-1`) |
| `SES_REPLY_TO` | no | `Reply-To` del correo |

Credenciales: las mismas que ya usa S3 (perfil/variables de AWS del servidor). En SES **sandbox** solo se puede enviar a destinatarios verificados: para producción hay que pedir la salida del sandbox en la cuenta AWS. Reiniciar la app tras editar `.env`.

## Reglas

| Tema | Decisión |
|---|---|
| Destinatario | `employees.email` del empleado, **saneado** (`_first_email`): primer token con `@` separando por `,` `;` espacios, en minúsculas. En dev hay correos como `X@GMAIL.COM,` y `,`; el primero se envía a `x@gmail.com`, el segundo cuenta como "sin correo". |
| Adjuntos | `pdf` y `xml` del `key` (los que existan), leídos con `get_object` de `S3_RH_BUCKET`, nombre = base del key. Tope 9 MB en total (SES rechaza raw > 10 MB). |
| Asunto / cuerpo | `Recibo de nómina <key> (<MM>/<YYYY>) — Telintec`; cuerpo = `message` del body (o el default) + aviso de correo automático. Solo texto plano (el helper acepta `body_html` para después). |
| Resultado por canal | `channels_sent` (enviado), `channels_pending` (SES sin configurar), **`channels_failed`** nuevo: `[{channel, reason}]` — sin correo, S3 ilegible, SES rechazó (`MessageRejected`: remitente/destinatario no verificados o sandbox), credenciales. `email_to` nuevo: correo usado (o `null`). `notified` = algo se envió (app **o** email). |
| Errores | Nunca 4xx por el correo: el canal falla "suave" y queda en `channels_failed` + `msg`; los 400/404 siguen siendo los de siempre (periodo inválido, sin registro, key sin archivos, canal inválido). |
| Envío | `send_raw_email` (MIME multipart: `alternative` texto/html + `application` por adjunto). |

## Las capas tocadas

```
misc        Functions_Mail.py (nuevo)              is_ses_configured · send_email_ses(to, subject, body_text, attachments, body_html) -> (ok, error, message_id)
midleware   Functions_midleware_RRHH.py            notify_payroll_file_api: rama email real · _send_payroll_email · _first_email
                                                   create_mail_payroll RETIRADO
routes      rs_RRHH.py                             POST /payroll/mail RETIRADO (404)
models      api_payroll_models.py                  create_mail_model / CreateMailForm RETIRADOS
sharepoint  Functions_Sharepoint.py                create_mail_draft_with_attachment RETIRADO (sin callers)
```

`Functions_Mail.py` es genérico: cualquier otro módulo que necesite correo (recordatorios de CDA, avisos médicos) lo puede usar tal cual.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permiso `rrhh`.
- **Base**: `/GUI/api/v1/rrhh`. **Sin cambios de request**: el contrato de [`nomina_gestion_archivos_y_notificacion.md`](nomina_gestion_archivos_y_notificacion.md) sigue igual; solo se agregan dos llaves a `data`.

`POST /payroll/notify` · body `{"emp_id": 5, "year": 2026, "month": 9, "key": "2026-09-Q1", "message": "opcional", "channels": ["app", "email"]}`

| Caso | `201` `data` |
|---|---|
| enviado | `{"emp_id": 5, "year": "2026", "month": "09", "key": "2026-09-Q1", "notified": true, "id_notification": 4855, "reason": null, "channels_sent": ["app", "email"], "channels_pending": [], "channels_failed": [], "email_to": "angel@hotmail.com"}` |
| SES sin configurar | `channels_sent: ["app"]`, `channels_pending: ["email"]`, `email_to: null` · `msg` termina en `Canal(es) pendiente(s) de configurar: email (falta SES_SENDER en .env)` |
| sin correo en el empleado | `channels_failed: [{"channel": "email", "reason": "el empleado 4 no tiene correo registrado"}]`, `email_to: null` |
| SES rechaza | `channels_failed: [{"channel": "email", "reason": "SES rechazó el mensaje: Email address is not verified… (¿remitente/destinatario verificados? ¿sandbox?)"}]`, `email_to: "x@y.com"` |
| S3 ilegible | `channels_failed: [{"channel": "email", "reason": "no se pudo leer pdf de S3 (payroll/…): …"}]` |

`400`: `channels` inválido (`sms`), periodo inválido, key sin archivos · `404`: empleado sin registro de nómina · `404` también para `POST /payroll/mail` (retirado).

### Gotchas

- Con `["app", "email"]` cada canal se resuelve por separado: el in-app puede quedar en `reason` (sin usuario) y el correo en `channels_failed`, y viceversa. Pintar los tres arreglos.
- `notified: true` con `channels_failed` no vacío es válido (se notificó por app pero el correo falló).
- Antes de habilitar el canal en la UI, RH debe limpiar los correos de `employees` (hay muchos vacíos o con coma): [`dashboard_rrhh.md`](dashboard_rrhh.md) ya reporta `data_quality`; un conteo de "sin correo válido" sería el siguiente tile.

## Al modificar

- **HTML en el correo**: pasar `body_html` a `send_email_ses` (ya soportado por el MIME `alternative`).
- **Otro módulo que envíe correo**: importar `send_email_ses` de `templates/misc/Functions_Mail.py`; el guard `is_ses_configured()` primero, para reportar "pendiente" en vez de fallar.
- **Plantillas de SES** (`send_templated_email`) no se usan: el cuerpo se arma en código para no depender de configuración en la consola AWS.

## Pendientes

- **[back] Levantar SES en AWS**: verificar la identidad remitente (correo o dominio con DKIM), pedir *production access* (salir del sandbox), permiso IAM `ses:SendRawEmail` al rol de la API, `SES_SENDER`/`SES_REGION` en `.env` de las 3 BDs, y prueba real a un correo propio. Listado en [`pendientes.md`](pendientes.md).
- **[front]** Mostrar `channels_failed`/`email_to` en la pantalla de nómina; checkbox "enviar por correo".
- **[back]** Correo también en los recordatorios de CDA y avisos médicos (helper listo, falta decidir destinatarios).
