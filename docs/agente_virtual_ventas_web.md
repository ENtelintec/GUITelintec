# Agente virtual de ventas en la web (F1): `POST /agents/sales/chatkit`

> 2026-11-05. Fase F1 de [`agentes_openai.md`](agentes_openai.md) (`P-240`). El código vive en el repo `telintec_agents` (servicio FastAPI, no en este API); aquí queda el contrato para el front y la operación. **Estado: back hecho y probado contra la BD de dev; la conversación real contra OpenAI está bloqueada porque el proyecto no tiene créditos** (`P-247`), aunque la petición ya llega a OpenAI y el servicio responde con el texto de error previsto.

## Qué se construyó (repo `telintec_agents`)

| Capa | Archivo | Qué hace |
|---|---|---|
| HTTP | `agents_service/routers/sales.py` | `POST /agents/sales/chatkit`: recibe la petición del protocolo de ChatKit, arma el `RequestContext` (agente ventas, canal web, `ip_hash` de la IP o de `X-Forwarded-For` con `TRUST_PROXY=1`) y responde `text/event-stream` o JSON. Sin `OPENAI_API_KEY_SALES` → 503. |
| Chat | `agents_service/chat.py` | `TelintecChatKitServer`: revisa topes, carga los últimos 40 items, corre el agente con `Runner.run_streamed` y transmite con `stream_agent_response`; al terminar registra tokens en `agent_conversations` y `agent_usage_daily`. Textos fijos para tope, fuera de tema (guardrail) y error. |
| Agente | `agents_service/agents/sales.py` | "Robotín": prompt (persona, reglas, `knowledge/servicios.md`, contacto), tools `buscar_productos`, `detalle_producto`, `registrar_solicitud`; guardrail de tema con `gpt-5.4-nano`; `gpt-5.4-mini` con `max_tokens` = 600; cliente de OpenAI con la llave del proyecto de ventas. |
| Datos | `catalog.py`, `quotes.py`, `limits.py`, `notify.py`, `retention.py` | búsqueda FULLTEXT del catálogo (≤ 5 productos por respuesta, precio de lista MXN con IVA, foto; nunca `price_provider`); solicitudes de cotización en `agent_quote_requests` + **aviso por el sistema interno de notificaciones** (`sql_telintec.notifications_gui`, `body.app = ["administracion", "adminpreventa"]`, mismo formato que `NotificationForm`; lo ve la webapp en `GET /misc/notifications/all/<status>`); el correo SES queda como canal secundario apagado hasta configurar `SES_SENDER`; topes; borrado a 90 días (`scripts/purge_conversations.py`). |
| Operación | `deploy/` | `telintec-agents.service` (uvicorn 127.0.0.1:8100), `nginx-agents.conf` (`location /agents/`, `limit_req` 30/min por IP, sin buffering), `telintec-agents-purge.timer` (04:00 hora del centro). |

Pruebas: 37 en verde (unitarias + BD de dev con `agents_svc`), incluido el camino completo del protocolo de ChatKit con el tope en 0 (respuesta fija por el stream y persistencia de la conversación). `RUN_LIVE=1` corre una conversación real: hoy falla con "You have no credits remaining".

## Contrato mínimo para el front (telintec.mx, `P-241`)

- **URL:** `https://appinterna.telintec.mx/agents/sales/chatkit` (en dev: `http://127.0.0.1:8100/agents/sales/chatkit`). **Sin token.** Orígenes permitidos por CORS: `https://telintec.mx`, `https://telintec.com.mx` (lista cerrada; otro origen no recibe los encabezados CORS).
- **Componente:** ChatKit self-hosted. Web component `<openai-chatkit>` o `@openai/chatkit-react`:

```ts
import { ChatKit, useChatKit } from "@openai/chatkit-react";

const { control } = useChatKit({
  api: {
    url: "https://appinterna.telintec.mx/agents/sales/chatkit",
    domainKey: "<domainKey de telintec.mx, lo da el usuario desde el dashboard de OpenAI (P-247)>",
  },
  startScreen: { greeting: "Hola, soy Robotín. ¿Qué estás buscando?" },
  composer: { attachments: { enabled: false } },   // adjuntos deshabilitados en el servidor
  threadItemActions: { feedback: false },
});
<ChatKit control={control} className="h-[600px] w-[380px]" />
```

  El botón flotante con el personaje "robotín" se conserva; lo que abre es esta ventana. El front no arma mensajes a mano: el componente manda las operaciones `threads.create`, `threads.add_user_message`, `items.list`, etc., y el servidor contesta.
- **Dónde ve ventas las solicitudes:** como notificación interna en la webapp (permisos `adminPreventa` y `Administracion`), con folio, nombre, contacto, productos y el id de la conversación; la fila completa está en `sql_telintec_mod_agents.agent_quote_requests` (pantalla para listarlas y cambiar de estado: backlog del front).
- **Comportamiento que verá el visitante:** respuestas en markdown con hasta 5 productos (nombre, marca, modelo, precio de lista MXN con IVA, disponibilidad y foto desde `ftp3.syscom.mx`); al pedir cotizar, el agente pide nombre y teléfono o correo y confirma un folio; fuera de tema responde un texto fijo; al pasar un tope responde con el WhatsApp del sitio y el correo de ventas sin llamar al modelo.
- **Códigos fuera del protocolo:** 503 `{"data": null, "msg": "Agente de ventas no configurado", "error": "OPENAI_API_KEY_SALES"}` si el servicio no tiene llave; 404 `{"data": null, "msg": "Conversación no encontrada", "error": "..."}` si el widget manda un `thread_id` que ya no existe (retención de 90 días); 429 de nginx al pasar 30 peticiones por minuto por IP.
- **Gotchas:** el stream es `text/event-stream` (nginx con `proxy_buffering off`); el visitante no tiene lista de conversaciones (`threads.list` devuelve vacío: sin identidad); las imágenes solo se renderizan de `ftp3.syscom.mx` (`allowed_image_domains`).

## Cómo se obtiene el `domainKey` (usuario, `P-247`)

ChatKit self-hosted es un iframe que sirve OpenAI; al cargarse llama `POST https://api.openai.com/v1/chatkit/domain_keys/verify_hosted` para comprobar que el dominio que lo incrusta está autorizado. Pasos (fuentes: hilo [openai/chatkit-js#62](https://github.com/openai/chatkit-js/issues/62) con respuestas de OpenAI, y el [quickstart de chatkit-js](https://openai.github.io/chatkit-js/quickstart/); la documentación oficial todavía no lo explica, cosa que OpenAI reconoce en ese hilo):

1. Entrar con la cuenta de la organización a **`https://platform.openai.com/settings/organization/security/domain-allowlist`** (la página no aparece en el menú del dashboard; hay que ir por la URL).
2. Crear una **domain key** y agregarle los dominios donde vivirá el widget: `telintec.mx` y `telintec.com.mx` para el agente virtual de ventas; el dominio de la webapp en Amplify (y el propio si lo tiene) cuando entre el asistente. Una sola llave puede cubrir varios dominios.
3. Copiar la llave en el front, en `api: { url: "...", domainKey: "<llave>" }` del componente (con `url` como string; con `getCustomConfig` no se acepta). No es secreta: va en el código del sitio.
4. Esperar la propagación: en el hilo reportan de unos minutos a 20–30 minutos (a veces más) antes de que la verificación pase.
5. Síntoma de dominio no registrado o llave inválida: el iframe se monta y desaparece de inmediato, con `verify_hosted` → 401 en la consola del navegador.

En desarrollo local el quickstart usa `url: "http://localhost:8000/chatkit"` con `domainKey: "local-dev"` como marcador; no está documentado si `localhost` exige registro, así que si el widget no carga en local, registrar también `localhost` (o probar directamente en el dominio real).

## Topes y textos fijos (configurables en el `.env` del servicio)

| Tope | Valor | Qué pasa |
|---|---|---|
| mensajes del visitante por conversación | 30 | texto fijo con WhatsApp y correo |
| conversaciones nuevas por IP y día | 20 | igual |
| tokens por día del agente | 3 000 000 | igual |
| tokens de salida por turno | 600 | el modelo corta la respuesta |
| fuera de tema (guardrail) | — | "Soy Robotín… ¿Qué estás buscando?" |
| error del modelo o de la API | — | "Tuve un problema… WhatsApp…" |

## Pendientes que quedan de F1

- `P-247` (usuario): **agregar créditos al proyecto de OpenAI** (la API contestó "no credits remaining") y registrar `telintec.mx`/`telintec.com.mx` para el `domainKey`. Con eso corro `RUN_LIVE=1` y cierro la validación.
- `P-248` (usuario): correr [`scripts_db_handle/agentes_grants_v3.sql`](../scripts_db_handle/agentes_grants_v3.sql) (`INSERT` en `notifications_gui` para `agents_svc`; sin él la solicitud se guarda pero el aviso falla y queda en el log), instalar `deploy/` en prod, parar la unidad `chatbot` vieja. SES (usuario IAM con `ses:SendEmail`) queda para después, decisión del usuario del 2026-11-05.
- `P-249` (ventas): corregir `knowledge/servicios.md`.
- `P-241` (front): integrar el componente.

## Al modificar

- Cambiar textos fijos o reglas del prompt → `agents_service/agents/sales.py`; el prompt se arma al crear la app (reiniciar el servicio).
- Nueva tool del agente de ventas → solo lectura del catálogo o escritura en `sql_telintec_mod_agents`; nunca SQL al ERP.
- Cambiar topes → `.env` del servicio, no código.
- Si el front necesita widgets de ChatKit (tarjetas de producto) en vez de markdown → se agregan en `chat.py` sin tocar el contrato.
