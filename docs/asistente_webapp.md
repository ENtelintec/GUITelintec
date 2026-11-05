# Asistente de la webapp (F3): `POST /agents/assistant/chatkit`

> 2026-11-05. Fase F3 de [`agentes_openai.md`](agentes_openai.md) (`P-243` back, `P-244` front), sobre la misma base que [`agente_virtual_ventas_web.md`](agente_virtual_ventas_web.md). Código en el repo `telintec_agents`; aquí queda el contrato para el front y la operación. **Estado: back hecho y probado con OpenAI simulado y contra la BD de dev; faltan la revisión de las guías por el usuario y la prueba en vivo** (créditos de OpenAI, `P-247`).

## Qué se construyó (repo `telintec_agents`)

| Capa | Archivo | Qué hace |
|---|---|---|
| HTTP | `agents_service/routers/assistant.py` | `POST /agents/assistant/chatkit`: exige el JWT crudo ES256 en `Authorization` (401 con el envelope si falta, trae `Bearer`, es HS256 o venció), lee la ruta de la webapp de `X-Page-Context` y arma el `RequestContext` (agente asistente, canal web, `user_ref` = `emp:<emp_id>`, claims del token). Sin `OPENAI_API_KEY_ASSISTANT` → 503. `GET /agents/assistant/me` sigue igual. `routers/_chatkit.py` arma la respuesta (stream o JSON, 404 si el hilo no existe) para los dos agentes. |
| Chat | `agents_service/chat.py` | El mismo `TelintecChatKitServer` de ventas: topes → historial (40 items) → `Runner.run_streamed` → stream; contabilidad de tokens por conversación y por día. |
| Agente | `agents_service/agents/assistant.py` | Instrucciones **dinámicas por turno**: persona y reglas, nombre y permisos del usuario (del JWT), módulos a los que puede entrar, módulo de la pantalla actual, índice de guías y la **guía del módulo actual completa**. Tool `leer_guia(modulo)` para cualquier otra guía; `FileSearchTool` solo si hay `OPENAI_VECTOR_STORE_ID`. Guardrail de tema con el modelo nano (`agents/guard.py`, compartido con ventas). `gpt-5.4-mini` con `max_tokens` = 900. Cliente de OpenAI con la llave del proyecto del asistente. |
| Conocimiento | `agents_service/knowledge.py`, `knowledge/help/*.md` | `HelpBase`: carga las guías (encabezado `modulo`, `titulo`, `rutas`, `permisos`, `resumen`), resuelve ruta → módulo por el **prefijo más largo**, filtra por permisos para decir "no tienes acceso". Formato y lista en `knowledge/help/README.md`. `scripts/sync_kb.py` sube las guías al vector store del proyecto del asistente (opcional). |
| Topes | `agents_service/limits.py` | Presupuesto diario por agente (`LIMIT_TOKENS_PER_DAY_ASSISTANT`, 1 000 000) y mensajes por conversación (30, el mismo de ventas); el tope por IP no aplica (hay identidad). Retención: 90 días como toda conversación sin solicitud (`scripts/purge_conversations.py`). |

Pruebas: 57 en verde (todo el repo): parseo de guías y ruta → módulo, prompt según contexto y tools del asistente, 401/503 del endpoint y el camino completo del protocolo contra dev con el tope en 0 (texto fijo por el stream, conversación con `user_ref` y `page_context`, `threads.list` solo del usuario). `RUN_LIVE=1 pytest tests/test_assistant_chatkit.py::test_live_conversation` corre una conversación real (pendiente de créditos).

## Lo que verá el usuario

- Contesta **siempre en español**, tutea, breve; un procedimiento va en pasos numerados; pantallas, botones y estados en **negritas** con el nombre exacto de la guía.
- Sabe quién es (nombre del token) y qué permisos tiene: si pregunta por un módulo que no puede abrir, se lo dice y lo manda a pedir el permiso a sistemas.
- Sabe en qué pantalla está (`X-Page-Context`): la guía de ese módulo va completa en el prompt, así que la respuesta sale sin tool; para otro módulo lee su guía con `leer_guia`.
- **No ejecuta acciones ni consulta datos** (saldos, inventario, nómina): explica en qué pantalla se ve o se hace. Eso es F4 (`P-245`).
- Fuera de tema (abuso, tareas, programación general, otras empresas) → texto fijo "Soy el asistente de la webapp…". Al pasar un tope → texto fijo "Por hoy el asistente llegó a su límite…". Error del modelo → "Tuve un problema para responder…".
- Cada usuario tiene su lista de conversaciones (`threads.list` filtra por `user_ref`); nadie ve las de otro.

## Base de conocimiento (`knowledge/help/`)

Una guía por módulo del menú de la webapp (`src/constants/nav.ts` del front): `inicio`, `administracion`, `compras`, `cobranza`, `preventa`, `sgi`, `almacen` (con Sucursal e Inventario de Almacén), `vales_y_epp`, `control_activos` (con Checklist), `comun`, `rrhh`, `sm`, `operaciones`, `lideres`, `usuarios_y_cargos`. Cada una describe por pantalla: para qué sirve, quién entra (permisos del catálogo, los de `route-permissions.ts`), cómo se usa (botones y pestañas con su texto), estados y reglas, problemas frecuentes. Redactadas el 2026-11-05 desde el código del front, sus guías de prueba (`docs/pruebas/`) y las docs de este repo; **lo que no se pudo verificar lleva la marca "(por confirmar)" y lo revisa el usuario** (`P-243`). Sin jerga técnica: el lector es un empleado.

Mantenimiento: pantalla nueva o cambiada en la webapp → actualizar el `.md` de su módulo (y `rutas:` si cambia el prefijo) y reiniciar el servicio (las guías se cargan al arrancar). Una guía con el encabezado roto se omite con aviso en el log y hace fallar `tests/test_knowledge.py`. File Search es opcional: `python scripts/sync_kb.py` crea el vector store `telintec-webapp-help` en el proyecto del asistente, sube lo que cambió (por `sha256`) e imprime el id para `OPENAI_VECTOR_STORE_ID`; sin él el asistente trabaja igual con las guías locales.

## Contrato mínimo para el front (webapp, `P-244`)

- **URL:** `${NEXT_PUBLIC_AGENTS_URL}/assistant/chatkit` → `https://appinterna.telintec.mx/agents/assistant/chatkit` (en dev `http://127.0.0.1:8100/agents/assistant/chatkit`). La variable `NEXT_PUBLIC_AGENTS_URL` la crea el usuario en Amplify con `https://appinterna.telintec.mx/agents`.
- **Auth:** `Authorization: <JWT crudo>` (**sin** `Bearer `), el mismo token de la sesión (`session.user.token`). Solo ES256 firmado por la Lambda (`kid` `lambda`); 401 JSON `{"data": null, "msg": "No autorizado. Token invalido", "error": "<motivo>"}` si falta, trae prefijo, es HS256, el `kid` no se acepta o venció (tratarlo como el 401 global de la webapp: la sesión de 24 h caducó).
- **Permisos del catálogo:** ninguno nuevo; cualquier token válido entra. Lo que el asistente *dice* depende de los permisos del token, pero no hay endpoint que abrir ni cerrar.
- **Encabezado `X-Page-Context`:** la ruta actual de la webapp (`usePathname()`, sin query), p. ej. `/dashboard/sm/sm-control/123`. Opcional, pero sin él el asistente no sabe en qué pantalla está el usuario y pregunta. Se guarda en la conversación al crearla (`agent_conversations.page_context`) y se usa en cada turno.
- **Componente:** ChatKit self-hosted con `@openai/chatkit-react`; el `fetch` agrega los dos encabezados:

```ts
import { ChatKit, useChatKit } from "@openai/chatkit-react";
import { useSession } from "next-auth/react";
import { usePathname } from "next/navigation";

const { data: session } = useSession();
const pathname = usePathname();
const { control } = useChatKit({
  api: {
    url: `${process.env.NEXT_PUBLIC_AGENTS_URL}/assistant/chatkit`,
    domainKey: "<domainKey del dominio de la webapp, lo entrega el usuario (P-247)>",
    fetch: (input, init) =>
      fetch(input, {
        ...init,
        headers: {
          ...(init?.headers ?? {}),
          Authorization: session?.user?.token ?? "",   // JWT crudo, sin "Bearer "
          "X-Page-Context": pathname ?? "",
        },
      }),
  },
  startScreen: { greeting: "Hola, soy el asistente de la webapp. ¿Qué quieres hacer?" },
  composer: { attachments: { enabled: false } },   // adjuntos deshabilitados en el servidor
  threadItemActions: { feedback: false },
});
<ChatKit control={control} className="h-[600px] w-[380px]" />
```

  El front no arma mensajes a mano: el componente manda `threads.create`, `threads.add_user_message`, `threads.list`, `items.list`, etc., y el servidor contesta (stream `text/event-stream` o JSON según la operación). Si el widget ofrece historial, lo que lista son las conversaciones del usuario del token.
- **Códigos fuera del protocolo:** 401 (arriba); 503 `{"data": null, "msg": "Asistente no configurado", "error": "OPENAI_API_KEY_ASSISTANT"}` si el servicio no tiene llave; 404 `{"data": null, "msg": "Conversación no encontrada", "error": "..."}` si el widget manda un `thread_id` borrado por la retención de 90 días; 429 de nginx al pasar 30 peticiones por minuto por IP (`limit_req` de `/agents/`).
- **CORS:** lista cerrada en el servicio (`CORS_ORIGINS`): el origen de la webapp (`https://main.d2vgjmty2204yz.amplifyapp.com` y el dominio propio cuando lo tenga) debe estar; `Authorization` y `X-Page-Context` ya están en `allow_headers`. El preflight `OPTIONS` no lleva token.
- **Gotchas:** el stream necesita `proxy_buffering off` (ya en nginx); el `domainKey` de la webapp es distinto del de telintec.mx si se generaron por separado; mandar `X-Page-Context` con la ruta real (los ids dinámicos no estorban: el módulo se resuelve por prefijo).

## Topes y textos fijos (configurables en el `.env` del servicio)

| Tope | Valor | Qué pasa |
|---|---|---|
| mensajes del usuario por conversación | 30 (`LIMIT_MESSAGES_PER_CONVERSATION`, compartido) | texto fijo; el usuario abre otra conversación |
| tokens por día del asistente | 1 000 000 (`LIMIT_TOKENS_PER_DAY_ASSISTANT`) | texto fijo hasta el día siguiente (hora del centro) |
| tokens de salida por turno | 900 (`LIMIT_OUTPUT_TOKENS_ASSISTANT`) | el modelo corta la respuesta |
| fuera de tema (guardrail) | — | "Soy el asistente de la webapp…" |
| error del modelo o de la API | — | "Tuve un problema para responder…" |

Costo estimado por turno con la guía del módulo en el prompt (≈ 3 000 a 5 000 tokens de entrada, cacheados en buena parte, + ≤ 900 de salida): ≈ USD 0.005 a 0.008 con `gpt-5.4-mini`; sin File Search no hay cargo extra.

## Pendientes que quedan de F3

- `P-243` (usuario): **revisar las guías** de `knowledge/help/` (buscar "(por confirmar)") y corregir lo que no sea como en la webapp; decidir si se activa File Search (`sync_kb.py`); con créditos (`P-247`) correr `RUN_LIVE=1` sobre `tests/test_assistant_chatkit.py` y cerrar.
- `P-244` (front): integrar el componente con el contrato de arriba; el `domainKey` de la webapp y `NEXT_PUBLIC_AGENTS_URL` los da el usuario.
- `P-247` (usuario): créditos del proyecto del asistente y el modelo nano permitido en ese proyecto (si no, el guardrail no corre y el servicio sigue sin filtro de tema).
- Traces: la llave de exportación de traces del SDK es global, así que con las dos llaves configuradas los traces de los dos agentes se ven en el proyecto de ventas; el consumo sí queda en cada proyecto.

## Al modificar

- Cambiar textos fijos, reglas o el tono → `agents_service/agents/assistant.py` (`build_instructions`); se calculan por turno, pero el agente se arma al arrancar (reiniciar el servicio).
- Nueva pantalla o módulo → guía en `knowledge/help/` con su `rutas:`; `X-Page-Context` debe coincidir con la ruta real del front.
- F4 (`P-245`): las tools que lean datos del usuario van por HTTP al API reenviando **su** JWT (ya viaja en `RequestContext.token_data`); nunca SQL al ERP ni tokens de servicio.
- Cambiar topes → `.env` del servicio, no código.
