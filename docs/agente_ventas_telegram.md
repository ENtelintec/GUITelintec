# Agente virtual de ventas en Telegram (F2): `POST /agents/sales/telegram`

> 2026-11-05. Fase F2 de [`agentes_openai.md`](agentes_openai.md) (`P-242`), sobre la F1 de [`agente_virtual_ventas_web.md`](agente_virtual_ventas_web.md). Código en el repo `telintec_agents`. **Estado: back hecho y probado con Telegram y OpenAI simulados; la prueba real va después del despliegue de F1 (decisión del usuario, 2026-11-05) y de los créditos de OpenAI (`P-247`).** No hay front: el canal es el bot `@telintec_AI_bot` que ya enlaza telintec.mx.

## Qué se construyó (repo `telintec_agents`)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Turno compartido | `agents_service/turn.py` | `run_turn`: guarda el mensaje del usuario en el Store, aplica los topes, corre el agente **sin streaming** (`Runner.run`), guarda la respuesta y registra tokens. Mismo agente, Store, guardrail y textos fijos que la web. |
| Canal | `agents_service/channels/telegram.py` | `TelegramClient` (Bot API con httpx: `getUpdates`, `sendMessage`, `sendChatAction`, `setWebhook`, `getWebhookInfo`); `TelegramChannel`: cada chat es una conversación del Store (`channel` 1, `user_ref` `telegram:<user_id>`); `/start` o 24 h sin mensajes abren conversación nueva y cierran la anterior; convierte el markdown del agente a HTML de Telegram (negritas, código, enlaces; las fotos van como enlace 📷); parte respuestas de más de 4 096 caracteres; sin texto responde un aviso fijo. |
| Webhook | `agents_service/routers/sales.py` | `POST /agents/sales/telegram`: exige el encabezado `X-Telegram-Bot-Api-Secret-Token` igual a `TELEGRAM_WEBHOOK_SECRET` (403 si no), responde 200 de inmediato y procesa el update en segundo plano; 503 si no hay token. |
| Scripts | `scripts/telegram_polling.py`, `scripts/telegram_webhook.py` | polling para dev (se niega si el bot tiene webhook); `info` / `set --yes` / `delete --yes` del webhook (los dos últimos cambian a dónde manda Telegram los mensajes del bot en vivo). |
| Config | `.env` del servicio | `TELEGRAM_TOKEN` (el mismo del `.env` del API), `TELEGRAM_WEBHOOK_SECRET` (generado), `TELEGRAM_WEBHOOK_URL` (`https://appinterna.telintec.mx/agents/sales/telegram`), `TELEGRAM_SESSION_HOURS` (24). |

Pruebas: 46 en verde; las de Telegram usan un cliente falso y un `Runner.run` falso contra la BD de dev (ciclo `/start` → turno → historial → sin texto → inactividad de 24 h → tope).

## Lo que encontré al revisar el bot (2026-11-05)

- El token del `.env` del API sigue vivo: `getMe` responde `@telintec_AI_bot` (id 6083119202).
- **El bot tiene hoy un webhook apuntando al chatbot viejo**: `https://appinterna.telintec.mx/chatbot/telegram`, sin updates pendientes ni errores. Mientras exista, Telegram no permite `getUpdates`, así que el polling de dev no arranca; borrarlo deja al chatbot viejo sin Telegram (hoy corre sobre un stack muerto, pero es la unidad `chatbot` de prod). **Decisión del usuario (2026-11-05): se espera al despliegue de F1 y ahí se apunta el bot al servicio nuevo** (paso 6 de `deploy/README.md`: `scripts/telegram_webhook.py set --yes`); el webhook viejo no se toca antes.

## Contrato (operación; no hay front)

- **Entrada:** Telegram manda `POST https://appinterna.telintec.mx/agents/sales/telegram` con el update en JSON y el encabezado `X-Telegram-Bot-Api-Secret-Token`. Respuestas: 200 `{"ok": true}`; 403 `{data: null, msg: "No autorizado", error: "secret_token"}`; 503 si falta `TELEGRAM_TOKEN`.
- **Alta del webhook:** en el servidor, con el servicio ya detrás de nginx: `python scripts/telegram_webhook.py set --yes` (usa la URL y el secreto del `.env`; descarta los updates pendientes del chatbot viejo). `info` muestra el estado; `delete --yes` lo quita.
- **nginx:** el webhook tiene su propio `location = /agents/sales/telegram` **sin** `limit_req` (los updates llegan desde pocas IPs de Telegram y el tope por IP los frenaría); está en `deploy/nginx-agents.conf` junto al `location /agents/`.
- **Dev:** `python scripts/telegram_polling.py` (requiere que no haya webhook).
- **Comportamiento del visitante:** igual que en la web (productos con precio de lista MXN con IVA, servicios, solicitud de cotización con aviso interno, topes y textos fijos), en HTML de Telegram; las fotos se ven como enlace porque Telegram no renderiza imágenes dentro del texto. `/start` reinicia la conversación.

## Pendientes

- `P-242`: prueba real contra Telegram y OpenAI tras el despliegue de F1 (`P-248`, paso 6 de la guía) y con saldo (`P-247`).
- `P-247`: además de los créditos, el proyecto de ventas (`proj_Rx37GOT0TzGhuBlNCV3UBavp`) **no tiene permitidos** `gpt-5.4-nano` ni `gpt-5-nano` (403 "does not have access to model"); hay que agregarlos en los límites del proyecto o el guardrail no corre (el servicio sigue, sin filtro de tema).

## Al modificar

- Un canal nuevo (WhatsApp, Facebook) es otro módulo en `agents_service/channels/` que llama `run_turn`; no un agente aparte ni otra tabla.
- Cambiar la ventana de 24 h → `TELEGRAM_SESSION_HOURS`.
- Si Telegram cambia de bot (otro token), cambiar `TELEGRAM_TOKEN` y volver a `set` el webhook.
