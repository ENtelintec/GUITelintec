# Agentes OpenAI — agente virtual de ventas (telintec.mx) y asistente de la webapp

> Grill 2026-11-05, **cerrado** (30 preguntas en 4 rondas; `P-237`). **Estado: aprobada, en curso** (F0 pendiente, `P-239`). Pregunta de origen: "actualizar todo lo que tenemos de OpenAI y del chatbot para usar agentes de OpenAI: (1) un agente que reciba mensajes en la página de Telintec y venda productos y servicios, (2) un asistente de la webapp que explique su funcionalidad y después crezca a un asistente real. ¿Qué arquitectura, en qué repo y qué opciones de puesta en producción?". El retiro del asistente virtual viejo (`P-238`) ya está hecho en este repo. Vocabulario: sección "Agentes de chat" de [`GLOSSARY.md`](../GLOSSARY.md).

## Lo que había (y lo que ya se retiró)

**En este repo — asistente virtual interno (`/misc/AV/*`), retirado el 2026-11-05 (`P-238`).**

- `POST /misc/AV/response` y `GET /misc/AV/files/<department>` en [`rs_Misc.py`](../templates/resources/rs_Misc.py) creaban **un assistant y un thread por pregunta** con la **Assistants API beta** (`client.beta.assistants`, `openai==1.22.0`, `gpt-4-1106-preview`), con `code_interpreter` y funciones de inventario, clientes, proveedores, movimientos, empleados y fichajes declaradas en `files/tools_AV_<departamento>.json`.
- OpenAI apagó la Assistants API el **2026-08-26** (el usuario lo confirmó en el dashboard el 2026-11-05: ya solo existe "Agents"). El front no llamaba a estos endpoints. `Functions_tools_openAI.py:226` llamaba a `get_orders_amc`, que no existía (bug diferido del 2026-10-26; se fue con el archivo).
- `Functions_Observer.py` (Bard + `openai.ChatCompletion` 0.28) y `controllers/chatbot/` eran huérfanos.
- Todo quedó en `GUITelintec_legacy/chatbot_av/` (README + `cambios_9ed0ecf.patch`); se borra en `P-250`. Qué salió exactamente: sección "Qué se retiró" abajo.

**Fuera de este repo — el bot de ventas viejo ("OrderBot").**

- Corre como la unidad **`chatbot`** del servidor de prod (systemd, venv `env` viejo: `bardapi`, `heyoo`, `pymessenger`, `python-gemini-api`, `openai` 0.28; [`dependencias_python.md`](dependencias_python.md)). Su código no está en esta máquina. Se para al entrar F1 (`P-248`).
- Escribe en `sql_telintec.chats` (`context` JSON, `platform`, `sender_id`, `is_alive`, `is_review`): 1 268 chats en dev (`webchat` 918, `whatsapp` 278, `telegram` 48, `facebook` 24; el último del 2025-10-27). Su prompt pedía al modelo emitir `/search: [name=…, brand=…, model=…]` y el servicio lo parseaba. `virtual_orders`, `orders_amc` y `order_details_amc` (0 filas) eran su destino de pedidos. **Nada de esto se toca**: `chats` queda como histórico.
- El sitio **telintec.mx** es Next.js detrás de CloudFront, con el widget "robotín" (`Chatbot`, `robotin-chatbot-logo`), enlace a WhatsApp Business (`wa.me/message/…`) y al bot de Telegram `@telintec_AI_bot`. Su buscador de productos ya es serverless: Lambdas `productSearch`, `productsGetTelintec` y `categoriesProducts` en el API Gateway `9jsqjxcuye` (us-east-2), sin autorizador y con acceso a la VPC de RDS (`P-235`, [`tokens_solo_24h.md`](tokens_solo_24h.md)).
- Llaves de canales en los `.env` (dev y `../`): `TELEGRAM_TOKEN`, `ID_WA_BUSS`, `VERIFY_TOKEN_WA`, `PAGE_ACCESS_TOKEN_FB`, `PAGE_ACCESS_TOKEN_FB2`, `VERIFY_TOKEN_FB`, `VERIFY_TOKEN_INSTA`. Telegram se reutiliza; los tokens de página de Meta caducan y el acceso a WhatsApp hay que reanudarlo.

**Catálogo para vender (las "tablas reducidas").**

| Tabla | Filas (dev) | Qué tiene | Para qué sirve al agente |
|---|---|---|---|
| `sql_telintec.products_services` | 32 014 (15 179 con `available_quantity > 0`) | catálogo SYSCOM: `name`, `model`, `marca`, `description`, `price_retail`, `price_provider`, `available_quantity`, `support_offered`, `is_service`, `category` (ids SYSCOM), `image` (URL en ftp3.syscom.mx); FULLTEXT en `name` | precio de lista, disponibilidad, foto. **`price_provider` nunca sale al visitante.** `is_service = 0` en todas: **no hay catálogo de servicios en BD.** |
| `sql_telintec.products_simple` | 32 014 | `name` normalizado (minúsculas, sin acentos ni números sueltos), `model`, `brand`, `available_quantity`; **3 índices FULLTEXT** en `name` | la versión reducida para buscar con pocos tokens: el agente busca aquí y solo pide el detalle de los ids que va a mostrar |
| `products_amc`, `product_categories_amc`, … | — | el inventario interno de Almacén | **no** es para vender: lo usaba el asistente interno |

**Webapp, servidor y OpenAI.**

- Webapp: Next.js 15 con SSR, `next-auth`, llama al API con el JWT crudo en `Authorization`; Amplify `d2vgjmty2204yz` (us-west-2). Sus docs: 80 `.md`, con guías de prueba por pantalla en `docs/pruebas/`.
- Prod del API: Amazon Linux 2023, nginx + gunicorn (3 workers sync, 1 hilo, timeout 30 s) en `guitelintec.service`; en el mismo host corren `authapi`, `chatbot` y `products` ([`despliegue_docker.md`](despliegue_docker.md)).
- OpenAI al 2026-11-05 (PyPI): `openai` 3.46.0; `openai-agents` 0.24.0 (exige `openai>=3,<4` y Python ≥ 3.10); `openai-chatkit` 1.6.5. Modelos permitidos en la cuenta (dashboard, 2026-11-05): `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5-nano` (y sus variantes con fecha).

## Objetivo

| Agente | Quién lo usa | Primera versión | A dónde crece |
|---|---|---|---|
| **Agente virtual de ventas** ("Robotín") | visitantes de telintec.mx; después Telegram, WhatsApp, Facebook e Instagram | saluda, entiende qué busca el visitante, **busca productos** (precio de lista, disponibilidad, foto), presenta los **servicios**, levanta una **solicitud de cotización** y la manda a ventas por correo; ofrece el WhatsApp del sitio | más canales, búsqueda semántica, cotización automática en Preventa |
| **Asistente de la webapp** | usuarios con sesión | explica **cómo se usa la webapp** por módulo, sabiendo en qué pantalla está el usuario; rechaza lo demás | consultas de datos del usuario con su token y acciones con confirmación; nunca puede más que el usuario |

## Arquitectura

```
 telintec.mx (Next.js / CloudFront)             webapp (Next.js / Amplify)          Telegram (F2) · WhatsApp/FB/IG (F5)
   <openai-chatkit> (público)                     @openai/chatkit-react (sesión)            webhooks de cada canal
        │ POST …/agents/sales/chatkit                   │ POST …/agents/assistant/chatkit        │ POST …/agents/sales/<canal>
        │ (sin token; domainKey + CORS)                  │ Authorization: <JWT crudo> · X-Page-Context
        ▼                                                ▼                                        ▼
 ┌──────────────────── telintec_agents — FastAPI + uvicorn + openai-agents + openai-chatkit ──────────────────────┐
 │  sales_agent      tools: buscar_productos · detalle_producto · servicios · registrar_solicitud                  │
 │                   guardrails de entrada/salida · topes por conversación, IP y día · correo SES                  │
 │  assistant_agent  tools: file_search (base de conocimiento) · [F4] consultas al API con el JWT del usuario       │
 │  Store de ChatKit: conversaciones, mensajes y solicitudes en MySQL (`sql_telintec_mod_agents`) · traces OpenAI │
 └───────────┬──────────────────────────────────────────┬──────────────────────────────────────────────────────────┘
             │ SQL solo lectura (usuario MySQL `agents_svc`)│ HTTP con el JWT del usuario (permisos del API)
             ▼                                              ▼
   RDS: products_simple + products_services          API GUITelintec (`/GUI/api/v1/*`)
             ▲
   OpenAI: Responses API (gpt-5.4-mini / gpt-5.4-nano) · File Search (vector store de la webapp) · Traces
```

| Pieza | Qué es | Por qué así |
|---|---|---|
| `telintec_agents` | repo y servicio Python nuevos (FastAPI + uvicorn, Python 3.12, `pytest`), routers `/sales` público y `/assistant` con JWT, adaptadores de canal | un solo runtime y un solo deploy; cada agente con su prompt, sus tools, su proyecto de OpenAI y sus límites |
| `openai-agents` | `Agent` + `Runner` sobre la Responses API: function tools tipadas, guardrails, sesiones, tracing | sucesor oficial de la Assistants API; evita el loop de tool calls a mano que hacía `retrieve_runs_openai` |
| `openai-chatkit` + ChatKit | la UI la sirve OpenAI (streaming, hilos, tarjetas, formularios, feedback); nosotros implementamos `respond()` y el `Store` | sin escribir un widget de chat; el mismo componente en el sitio y en la webapp |
| Store en MySQL | conversaciones, mensajes y solicitudes en `sql_telintec_mod_agents` | ventas revisa las solicitudes y sus conversaciones desde nuestra BD, no desde OpenAI |
| Tools de catálogo | SQL de solo lectura sobre `products_simple` (FULLTEXT) + `products_services` | reutiliza las tablas reducidas: ≤ 5 productos por respuesta, campos cortos, nunca `price_provider` |
| Tools del asistente | F3: File Search; F4: HTTP al API reenviando el JWT del usuario | el API decide permisos con el token; el asistente no toca la BD del ERP |

## Decisiones cerradas en el grill (2026-11-05)

| # | Tema | Decisión | Descartado y por qué |
|---|---|---|---|
| D1 | Repo | **`telintec_agents`**, repo propio en la organización de `telintec_login_lambda`, Python 3.12 en su venv, `pytest` versionado, `CLAUDE.md` propio que apunta a los docs y pendientes de aquí (el tracker es global). | Este repo: gunicorn sync (3 workers, 30 s) bloquea un worker por turno, Flask no hace streaming y `openai>=3` tira `/AV/*` de todos modos. |
| D2 | Framework | `openai-agents` sobre la Responses API. | Assistants (apagada); Agent Builder + ChatKit alojado (OpenAI lo marca en transición; las tools exigirían un servidor MCP público nuestro); LangChain. |
| D3 | Servidor | FastAPI + uvicorn (async, streaming nativo; lo que documenta `openai-chatkit`). | Flask. |
| D4 | Interfaz | **ChatKit self-hosted en ambos frentes**: `<openai-chatkit>` en telintec.mx, `@openai/chatkit-react` en la webapp, `domainKey` por dominio. El botón con el personaje "robotín" se queda; cambia la ventana. El front integra ambos desde el contrato. | Widget propio sobre SSE: mismo costo en dinero, 2–3 semanas de front contra 2–3 días; se puede cambiar solo el widget después sin tocar el agente. |
| D5 | Catálogo | Tool `buscar_productos(consulta, marca?, modelo?, solo_disponibles=true)` → `MATCH(name) AGAINST(...)` en `products_simple` JOIN `products_services`; solo con existencia por defecto, sin existencia si el visitante insiste; `detalle_producto(id)` para la descripción. Precio = `price_retail` como "precio de lista, sujeto a confirmación del asesor". Máximo 5 productos por respuesta con nombre, marca, modelo, precio y foto. | Catálogo en el prompt (32 k filas); File Search/embeddings del catálogo → F5. Las Lambdas del sitio pueden ser la misma consulta por HTTP si se prefiere no dar BD. |
| D6 | Servicios | `servicios.md` escrito por ventas (qué vende Telintec, para quién, qué preguntar), inyectado en el prompt (≈ 1–2 k tokens, cacheados). Si no llega para F1, arranca con las páginas de servicios de telintec.mx y ventas corrige. | Tabla `services`; scrapear el sitio a un vector store (cuando crezca). |
| D7 | Qué es "vender" | **Solicitud de cotización**: nombre, teléfono o correo (uno obligatorio), empresa y mensaje opcionales, productos de interés (también fuera de catálogo: lo que escribió el visitante). Estados 0 nueva, 1 contactada, 2 cotizada, 3 descartada. En F1 ventas la recibe solo por **correo SES**; la pantalla en la webapp va al backlog del front. | Pedido en firme con carrito; crear la cotización en Preventa (posterior, cuando ventas defina el flujo). |
| D8 | Estado | Conversaciones, mensajes y solicitudes en **MySQL** (`sql_telintec_mod_agents`, Store de ChatKit); `chats` vieja sin escribir. Ventas revisa solicitudes y las conversaciones de las que salieron. **Retención:** solicitudes sin caducidad; conversaciones sin solicitud y las del asistente, 90 días. | `OpenAIConversationsSession` (estado en OpenAI); SQLite en disco. |
| D9 | Modelos | **`gpt-5.4-mini`** para ambos agentes, **`gpt-5.4-nano`** para guardrails y clasificación, `gpt-5-nano` como opción más barata. Son los permitidos en la cuenta. | Modelo grande. |
| D10 | Auth y abuso | **Ventas:** anónimo; CORS solo `telintec.mx`/`telintec.com.mx`; `domainKey`; `limit_req` por IP en nginx; topes (tabla abajo). **Asistente:** `Authorization: <JWT crudo>` ES256 verificado con las llaves públicas `token_public_<kid>.pem`; **no acepta HS256** (consistente con `P-224`); cualquier token válido entra, sin permiso nuevo. | Validar el JWT llamando al API; Turnstile desde el inicio (F5 si hay abuso). |
| D11 | Conocimiento del asistente | Carpeta `help/` en el repo de agentes, un `.md` por módulo, redactada por el back desde `docs/pruebas/` del front y revisada por el usuario; `sync_kb.py` la sube al vector store de OpenAI (File Search) con metadatos; el widget manda `X-Page-Context`. Solo español. Si después el front la mantiene, se mueve a su repo. | Las 80 docs del front en el prompt; RAG propio. |
| D12 | Despliegue | **Servidor de prod actual**: unidad systemd `telintec-agents` (uvicorn en `127.0.0.1:8100`), nginx `location /agents/` en `appinterna.telintec.mx` (`proxy_buffering off`, `proxy_read_timeout 120`, `limit_req`), reemplaza a `chatbot`. Código 12-factor para mover sin tocarlo. | Lambda Web Adapter + Function URL (si el tráfico del sitio crece); Docker (al retomar `P-139`); subdominio `agentes.telintec.mx` (si el tráfico lo justifica). |
| D13 | Canales | **Web → Telegram → WhatsApp → Facebook e Instagram.** Telegram reutiliza `@telintec_AI_bot` y `TELEGRAM_TOKEN`: webhook con `secret_token` en prod, polling en dev; cada chat es una conversación; `/start` o 24 h sin mensajes abren una nueva. WhatsApp cuando se reanude el acceso a Meta. | — |
| D14 | Cuenta de OpenAI | Un **proyecto por agente** (`telintec-agente-ventas`, `telintec-asistente-webapp`) con llave y presupuesto propios; llaves solo en el `.env` del servicio; traces en el dashboard; contador de tokens por conversación y por día. | Una llave para todo. |
| D15 | Persona | "Robotín, el agente virtual de Telintec"; tutea; contesta en el idioma en que le escriben, español por defecto. | — |
| D16 | Paso a humano | Sin asesor en vivo en el chat en F1: el agente levanta la solicitud y ofrece el enlace de WhatsApp del sitio. | Asesor dentro de la misma conversación (posterior). |
| D17 | Correo | SES con la misma identidad remitente del API y un usuario IAM propio del servicio limitado a `ses:SendEmail`. | Reusar credenciales del API. |
| D18 | Alcance del asistente | F3 solo explica la webapp; F4 consultas y acciones **según los permisos del usuario**, reenviando su JWT; acciones con confirmación. | Token de servicio con permisos amplios. |

### Topes del agente público (ajustables por configuración)

| Tope | Valor |
|---|---|
| Mensajes por conversación | 30 |
| Conversaciones nuevas por IP y día | 20 |
| Tokens por día del agente virtual de ventas | 3 millones (≈ 3 USD con `gpt-5.4-mini`) |
| Tokens de salida por turno | 600 |

Al pasar cualquiera, el agente responde con el enlace de WhatsApp y el formulario de solicitud, sin llamar al modelo.

### Fases (sin calendario; cada una con su doc al implementarse)

| Fase | Entrega | Pendiente |
|---|---|---|
| **F0** | esqueleto de `telintec_agents`; `.sql` del esquema y del usuario MySQL revisado por el usuario | `P-239`, `P-248` |
| **F1** | agente virtual de ventas en telintec.mx (ChatKit), solicitudes por correo, topes, nginx + systemd en prod | `P-240` back, `P-241` front, `P-247`/`P-249` usuario |
| **F2** | Telegram | `P-242` |
| **F3** | asistente de la webapp con base de conocimiento | `P-243` back, `P-244` front |
| **F4** | asistente con consultas y acciones según permisos | `P-245` |
| **F5** | WhatsApp, Facebook e Instagram; búsqueda semántica; Turnstile; cotización en Preventa | `P-246` |
| limpieza | borrar el legacy, llaves viejas fuera de los `.env` y de OpenAI | `P-250` |

### Opciones de puesta en producción (referencia)

| Opción | Cómo | A favor | En contra |
|---|---|---|---|
| **A. Servidor de prod (systemd + nginx)** — elegida | venv propio, `telintec-agents.service`, nginx `/agents/` con rate limit; mismo RDS con `agents_svc` | pagado y operado; nginx y TLS listos; sustituye `chatbot`; async → casi sin CPU | tráfico anónimo en la máquina del ERP (acotado por `limit_req` y topes); un deploy más en `P-180` |
| B. Lambda (us-east-2) + Function URL | FastAPI bajo Lambda Web Adapter con `response_stream`; rol propio (lección de `P-235`); RDS por la VPC | aislamiento del ERP; escala sola; costo por uso | API Gateway no hace streaming; arranques en frío; paquete grande |
| C. Contenedor | `Dockerfile` + compose ([`despliegue_docker.md`](despliegue_docker.md)) | reproducible; buen piloto de Docker | Docker en el host está pospuesto; ECS/App Runner suma costo fijo |
| D. Alojado por OpenAI | Agent Builder + ChatKit hosted; tools tras un MCP público | casi sin infraestructura | OpenAI lo marca en transición; el MCP sería nuestro igual; prompts fuera de git |

## Esquema nuevo (DDL en [`scripts_db_handle/agentes_schema_y_usuario.sql`](../scripts_db_handle/agentes_schema_y_usuario.sql), lo revisa y corre el usuario, `P-248`)

Esquema `sql_telintec_mod_agents` (mismo patrón que `sql_telintec_mod_rrhh` / `_mod_admin`):

| Tabla | Columnas principales |
|---|---|
| `agent_conversations` | `conversation_id` VARCHAR(64) PK · `agent` TINYINT (0 ventas, 1 asistente) · `channel` TINYINT (0 web, 1 telegram, 2 whatsapp, 3 facebook, 4 instagram) · `user_ref` (emp_id del JWT o id del canal; NULL = visitante web) · `ip_hash` CHAR(64) (tope por IP/día) · `page_context` · `status` TINYINT (0 abierta, 1 cerrada, 2 revisada) · `tokens_in`, `tokens_out` · `created_at`, `updated_at` |
| `agent_messages` | `message_id` VARCHAR(64) PK · `conversation_id` FK `ON DELETE CASCADE` · `seq` · `item_type` · `payload` JSON (el item de ChatKit tal cual) · `created_at`; único `(conversation_id, seq)` |
| `agent_quote_requests` | `request_id` AI PK · `conversation_id` FK (sin cascade: se conservan) · `name` · `phone`, `email` (`CHECK` al menos uno) · `company` · `message` · `products` JSON (`[{product_id|null, name, quantity}]`) · `status` TINYINT (0 nueva, 1 contactada, 2 cotizada, 3 descartada) · `created_at`, `notified_at` |
| `agent_usage_daily` | `day`, `agent` PK · `turns` · `tokens_in`, `tokens_out` (presupuesto diario) |

Usuario `agents_svc`: `SELECT` en `sql_telintec.products_simple` y `products_services`; `SELECT, INSERT, UPDATE, DELETE` en `sql_telintec_mod_agents.*`. La retención la corre el servicio con ese usuario.

## Contrato mínimo para el front (se fija al implementar; versión definitiva en el doc de `P-240` y `P-243`)

- **Base:** `https://appinterna.telintec.mx/agents`. `GET /agents/health` → `OK` (texto, 200).
- **ChatKit (ambos agentes):** el componente habla el protocolo de ChatKit (POST con streaming de eventos); el front no arma mensajes a mano:
  - telintec.mx: `<openai-chatkit>` con `api: { url: "https://appinterna.telintec.mx/agents/sales/chatkit", domainKey: "<domainKey de telintec.mx>" }`. Sin encabezado de auth. Origen fuera de la lista → **403** JSON `{"data": null, "msg": "Origen no permitido", "error": "..."}`. Al pasar un tope, la respuesta llega dentro del chat (WhatsApp + formulario), con 200.
  - webapp: `@openai/chatkit-react` con `api: { url: ".../agents/assistant/chatkit", domainKey, fetch }`, donde `fetch` agrega `Authorization: <JWT crudo, sin "Bearer ">` y `X-Page-Context: <ruta actual, p. ej. /dashboard/sm/control>`. Token ausente, inválido, HS256 o vencido → **401** JSON `{"data": null, "msg": "No autorizado. Token invalido", "error": "..."}` (la webapp lo trata como su 401 global). Cualquier token ES256 válido entra; las tools de F4 heredan los permisos del API porque le reenvían el mismo token.
- **Permisos del catálogo:** ninguno nuevo. Ventas es público; el asistente pide solo un token válido.
- **Gotchas:** streaming → `proxy_buffering off` en nginx; CORS del servicio es lista cerrada, no `*` como el API; los `domainKey` se registran en el proyecto de OpenAI de cada agente (`P-247`).

## Seguridad y límites (agente público)

- Solo tools de lectura más `registrar_solicitud`; sin acceso a `sql_telintec` fuera de las dos tablas de catálogo (usuario `agents_svc`).
- Guardrail de entrada (`gpt-5.4-nano`): fuera de tema, abuso, inyección ("ignora tus instrucciones", pedir precios de proveedor, datos de otros clientes) → respuesta fija. Guardrail de salida: sin `price_provider`, sin promesas de fecha de entrega ni de precio final.
- Topes de la tabla de arriba; `limit_req` en nginx; `max_output_tokens` por turno; timeout de OpenAI 60 s.
- Datos personales solo en `agent_quote_requests` y en el correo a ventas.

## Costos (precios de agregadores al 2026-11; verificar en la página oficial al implementar)

| Concepto | Dato |
|---|---|
| `gpt-5.4-mini` | ≈ USD 0.75 / 1 M tokens de entrada · 4.50 / 1 M de salida (cacheada ≈ 10 %) |
| `gpt-5.4-nano` | ≈ USD 0.20 / 1 M entrada · 1.25 / 1 M salida |
| Turno típico de ventas (prompt + servicios + 1 búsqueda) | ≈ 3 000 entrada + 300 salida ≈ USD 0.004 |
| 1 000 turnos al mes | ≈ USD 4 (+ guardrails con nano, centavos) |
| File Search (asistente) | USD 2.50 / 1 000 llamadas; almacenamiento gratis hasta 1 GB |
| ChatKit | sin cuota: solo tokens |

## Qué se retiró de este repo (`P-238`, hecho el 2026-11-05)

`POST /misc/AV/response`, `GET /misc/AV/files/<department>` y `_AV` en [`rs_Misc.py`](../templates/resources/rs_Misc.py); `get_response_AV` y `get_files_openai` en [`Functions_midleware_misc.py`](../templates/resources/midleware/Functions_midleware_misc.py); `RequestAVResponseForm` y `request_av_response_model` en [`api_models.py`](../static/Models/api_models.py); `Functions_openAI.py`, `Functions_tools_openAI.py`, `Functions_Observer.py`, `controllers/chatbot/`; `department_tools_openAI` y `tools_AV_avaliable` en [`constants.py`](../static/constants.py); `files/tools_AV_*.json`; las 11 funciones de controladores que solo usaba el chatbot (`get_products_almacen`, `get_high_stock_products`, `get_low_stock_products`, `get_no_stock_products`, `get_product_categories`, `get_supply_inv_amc`, `get_product_movement_amc`, `get_costumers_amc`, `get_supplier_amc`, `get_employees_w_status`, `get_fichaje_emp_AV`); `openai==1.22.0` en [`requirements.txt`](../requirements.txt) y en [`constraints.txt`](../constraints.txt) sus 13 transitivas exclusivas (57 → 43 paquetes en la resolución para Linux y 3.11, sin cambios de versión; [`dependencias_python.md`](dependencias_python.md)). Verificado: `import app` y `pyrefly check` limpios en los archivos tocados. Copia en `GUITelintec_legacy/chatbot_av/` con README y `cambios_9ed0ecf.patch` (`git apply -R` lo revierte); se borra en `P-250`. Las llaves `OPENAI_API_KEY_*` y `PSID*` siguen en los `.env` hasta `P-250`.

## Datos pendientes del usuario (`P-247`, `P-248`, `P-249`)

- OpenAI: proyectos, presupuestos, llaves y `domainKey` (lo demás del dashboard ya está: Assistants fuera, modelos permitidos).
- Accesos: correr el `.sql`; usuario IAM de SES; nginx y systemd al llegar F1.
- Negocio: correos de ventas; si `price_retail` es MXN con IVA; si `products` sincroniza `products_services` desde SYSCOM y cada cuánto; `servicios.md`.

## Al modificar

- Toda tool nueva del agente virtual de ventas es de lectura o escribe solo en `sql_telintec_mod_agents`; si necesita datos del ERP, va por HTTP al API con un token, nunca por SQL directo.
- Toda tool del asistente que lea datos de un usuario reenvía **su** JWT al API; no se crean tokens de servicio con permisos amplios.
- Cambiar de modelo o de precios → actualizar la tabla de costos y el presupuesto diario.
- Nueva pantalla en la webapp → agregar o actualizar su `.md` en `help/` y correr `sync_kb.py`; el `X-Page-Context` debe coincidir con la ruta real.
- Nuevo canal → un adaptador nuevo sobre el mismo `sales_agent`, valor nuevo de `channel`; nunca un agente aparte.
- Cambiar el destino de despliegue (B o C) no cambia el código: solo empaquetado, `proxy_pass` y CORS.
- Los pendientes de este tema viven en [`pendientes.md`](pendientes.md) aunque el código esté en `telintec_agents` (criterio de `telintec_login_lambda`); cada fase trae su doc aquí con el contrato definitivo.

## Fuentes consultadas (2026-11-05)

- Apagado de la Assistants API el 2026-08-26 (aviso retransmitido; confirmado por el usuario en el dashboard): [Zoho community](https://help.zoho.com/portal/en/community/topic/deprecation-notice-openai-assistants-api-will-be-shut-down-on-august-26-2026) · [Make community](https://community.make.com/t/depreciation-of-the-assistants-api-by-openai-how-to-replace-assistants/90619)
- ChatKit self-hosted (servidor Python + Agents SDK, Store propio, `domainKey`): [Advanced integrations with ChatKit — OpenAI](https://developers.openai.com/api/docs/guides/custom-chatkit) · [chatkit-js](https://openai.github.io/chatkit-js/)
- Versiones: PyPI `openai` 3.46.0, `openai-agents` 0.24.0 (`openai>=3`, Python ≥ 3.10), `openai-chatkit` 1.6.5 (`pypi.org/pypi/<paquete>/json`) · [novedades del Agents SDK 2026](https://www.developersdigest.tech/blog/openai-agents-sdk-whats-new-2026)
- Precios (agregadores; verificar en OpenAI): [morphllm](https://morphllm.com/openai-api-pricing) · [intuitionlabs](https://intuitionlabs.ai/articles/chatgpt-api-pricing-2026-token-costs-limits) · [gpt-5.4-nano](https://pricepertoken.com/pricing-page/model/openai-gpt-5.4-nano) · [gpt-5.4-mini](https://anotherwrapper.com/llm-pricing/gpt-5.4-mini)
