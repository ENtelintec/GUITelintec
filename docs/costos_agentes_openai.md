# Costos de los agentes de IA (OpenAI)

> 2026-11-06 · Para Administración. Precios oficiales de OpenAI y consumo medido con conversaciones reales en dev. Diseño de los agentes: [`agentes_openai.md`](agentes_openai.md).

Los dos agentes cuestan alrededor de **medio centavo de dólar por mensaje**. Con el uso esperado, el gasto sería de **15 a 65 USD al mes**, y los topes del sistema impiden que pase de **unos 130 USD al mes**.

## Gasto estimado

| Agente | Quién lo usa | Gasto mensual estimado | Máximo por tope |
|---|---|---|---|
| Robotín (ventas) | visitantes de telintec.mx y Telegram | 12–60 USD | ~95 USD |
| Asistente de la webapp | 1 persona por ahora | 1–3 USD | ~32 USD |

Supuestos: de 20 a 100 conversaciones de ventas al día (unos 5 mensajes cada una) y de 10 a 20 preguntas al asistente por día hábil. El volumen real de ventas está por confirmar.

Medido el 2026-11-06: ventas, ~0.4 centavos por mensaje; asistente, ~0.5 centavos (~0.9 cuando busca en las guías).

## Qué se paga

Se paga a **OpenAI** por uso, con créditos prepagados. Cada agente tiene su propio proyecto en OpenAI, así que el gasto de cada uno se ve por separado.

| Concepto | Para qué se usa | Precio (USD) |
|---|---|---|
| Modelo `gpt-5.4-mini` | redactar las respuestas de los dos agentes | 0.75 por millón de tokens leídos (0.075 si los leyó hace poco: caché) · 4.50 por millón escritos |
| Modelo `gpt-6-luna` | filtro que bloquea temas ajenos a la empresa | 0.10 por millón leídos · 0.50 por millón escritos |
| Búsqueda en las guías (File Search) | el asistente busca en las guías de la webapp | 0.0025 por búsqueda |
| Almacenamiento de las guías | 11 guías, 132 KB | gratis (el primer GB no se cobra) |

Un token es un fragmento de palabra. Cada mensaje lee de 3 000 a 7 000 tokens (instrucciones, catálogo o guía e historial de la conversación) y escribe de 100 a 800.

## Topes que limitan el gasto

Al llegar a un tope, el agente contesta con un texto fijo (ventas: el enlace de WhatsApp) sin llamar a OpenAI, así que ya no genera costo.

| Tope | Valor | Equivale a |
|---|---|---|
| Tokens por día, ventas | 3 000 000 | ~580 mensajes · 2.30–3.20 USD al día |
| Tokens por día, asistente | 1 000 000 | ~145 preguntas · ~1 USD al día |
| Conversaciones nuevas por visitante (IP) al día | 20 | evita que una sola persona agote el tope del día |
| Mensajes por conversación | 30 | limita el costo de una conversación larga |
| Largo máximo de una respuesta | 1 000 tokens (ventas) · 900 (asistente) | una respuesta escribe como máximo ~0.5 centavos |

El tope diario cuenta solo el modelo que redacta. El filtro de tema y las búsquedas en guías van aparte: suman ~3 % en ventas y hasta ~20 % en el asistente.

## Seguimiento

- **Gasto real:** panel de uso de OpenAI, por proyecto (ventas y asistente). El servicio además guarda los tokens por día y por agente (`sql_telintec_mod_agents.agent_usage_daily`).
- **Alerta de presupuesto (por configurar):** un presupuesto mensual con aviso en cada proyecto de OpenAI, como respaldo de los topes.
- **Por revisar:** el asistente no aprovecha el descuento de caché que sí usa ventas; corregirlo bajaría su costo.

## Cambios

| Fecha | Cambio | Efecto en el costo |
|---|---|---|
| 2026-11-06 | Filtro de tema de `gpt-5.4-nano` a `gpt-6-luna`: OpenAI retira `gpt-5.4-nano` el 2027-04-01 | el filtro cuesta la mitad; como es ~3 % del gasto, el total casi no cambia |
| 2026-11-06 | Respuesta máxima de ventas de 600 a 1 000 tokens: las listas de 5 productos con foto se cortaban | solo las respuestas largas cuestan más; el tope diario no cambia |

## Fuentes

Consultadas el 2026-11-06:

- [Precios de la API de OpenAI](https://developers.openai.com/api/docs/pricing)
- Modelos: [`gpt-5.4-mini`](https://developers.openai.com/api/docs/models/gpt-5.4-mini) · [`gpt-6-luna`](https://developers.openai.com/api/docs/models/gpt-6-luna) · [`gpt-5.4-nano`](https://developers.openai.com/api/docs/models/gpt-5.4-nano)
- [Retiros de modelos de OpenAI](https://developers.openai.com/api/docs/deprecations)
