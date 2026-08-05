# Plan de trabajo — Módulo RH (1 mes)

> Plan de sprint de ~4 semanas para el módulo de RH. Dos frentes: (1) comprobación de endpoints y (2) refactor del módulo de encuestas centrado en la evaluación/interpretación. El front es un tercero a medio tiempo en evaluación.

## Decisiones acordadas

| Tema | Decisión |
|---|---|
| **Comprobación — qué es** | Smoke test + documentar; el front descubre bugs, el back los arregla en paralelo |
| **Comprobación — alcance** | ~38 operaciones (32 de RRHH + los de encuestas en el namespace `misc`). Rápida; no es el polo largo |
| **Comprobación — entorno** | `HOST_DB_TEST` con token `is_tester`; el back siembra datos en S0 |
| **Comprobación — entregable** | Hoja/tabla compartida |
| **Equipo — back (tú)** | Full-time, ~160 h/mes. El motor del plan |
| **Equipo — front (tercero)** | Medio tiempo 15-20 h/sem (~60-80 h). Ex-full-time, conoce el código. En evaluación de si aguanta el medio tiempo |
| **Encuestas — meta** | Arreglar y completar; el peso está en la evaluación/interpretación |
| **Encuestas — arquitectura** | Motor **config-driven** (rúbrica en datos, ajustable por el back), sobre `tasks_gui`, sin migración de esquema, sin UI de admin, sin constructor |
| **Encuestas — rúbricas** | Existen todas. Salida = cualitativa (sin score) |
| **Encuestas — front construye** | UI de asignación (menor), captura de respuestas, y resultados/interpretación (la pesada) |
| **Encuestas — MVP intocable** | Motor + Norma 035 + salida + las 3 UIs |
| **Encuestas — orden de recorte** | Clima laboral → Eva 360 → pulido |
| **Medición del tercero** | Checkpoint semanal; barra = comprobación rápida en S1 + captura/resultados integradas al cierre |

## Objetivo del mes

1. **Comprobar** los ~38 endpoints del módulo RH y cerrar los bugs que salgan.
2. **Refactorizar encuestas** para que la evaluación/interpretación funcione adecuadamente (motor config-driven), con Norma 035 y salida operando end-to-end.
3. **Medir** si el tercero rinde el medio tiempo.

**Criterio de éxito (línea que no se cruza):** hoja de comprobación cerrada + motor de evaluación funcionando + Norma 035 y salida completas + las 3 UIs integradas. Clima/Eva 360 = bonus si el tiempo alcanza.

## Principio rector

El back tiene ~2.5× las horas del front → **el back produce contratos + backend por adelantado; el front nunca se bloquea esperando.** La comprobación (que no depende del back) llena la S1 del front mientras el back construye el motor.

## Calendario

### Semana 0 — Arranque (solo back, 2-3 días)

- [ ] **Sembrar `HOST_DB_TEST`**: empleado(s) con examen médico + vacaciones + una encuesta asignada de **cada** tipo (0-4). Sin esto, los GET devuelven vacío y la comprobación es humo.
- [ ] Alta del **token/usuario `is_tester`** para el tercero.
- [ ] Crear la **hoja de comprobación** (columnas: endpoint · método · request enviado · status recibido · esperado · ✅/❌ · nota).
- [ ] **Diseño del motor config-driven**: formato de la config de rúbrica (cómo un tipo declara puntuación e interpretación). Timebox estricto — arrancar de Norma 035 concreto y generalizar; no sobre-diseñar.

### Semana 1 — Comprobación (front) ‖ Motor + contratos (back)

| Front (tercero) | Back (tú) |
|---|---|
| Comprobar los ~38 endpoints, llenar la hoja | Construir el esqueleto del motor config-driven (reemplaza `calculate_results_quizzes`/`recommendations_results_quizzes`) |
| | Escribir los **contratos** en `Docs/` (bloque "Contrato mínimo para el front") de asignación, captura y resultados |
| | Triar y empezar a cerrar los bugs que el front reporta |

**Checkpoint fin S1:** hoja llena. *Primera señal de throughput. Si aquí se cae, es alerta temprana.*

### Semana 2 — Pivote a encuestas

| Front | Back |
|---|---|
| Integrar **≥1 UI** (empezar por asignación o captura, las de menor riesgo) contra los contratos | Terminar motor + **Norma 035 end-to-end** (scoring + interpretación + PDF) |
| | **Consolidar los dos namespaces** (`misc` + `rrhh`) de encuestas en uno |
| | Cerrar bugs de la hoja; entregar contratos finales |

**Checkpoint fin S2:** ≥1 UI integrada.

### Semana 3 — Núcleo funcional

| Front | Back |
|---|---|
| Las **3 UIs funcionales con Norma 035** (asignación, captura, resultados mostrando la interpretación estructurada nueva) | Agregar **Clima laboral** (config) + probar; empezar Eva 360 si da tiempo |
| | Soporte de integración al front |

**Checkpoint fin S3:** 3 UIs funcionales con Norma 035. *Punto de decisión de recorte: si vas tarde, congela clima/eva360.*

### Semana 4 — Cierre e integración

| Front | Back |
|---|---|
| Integrar **salida** (cualitativa), cerrar bugs de integración, pulir | **Salida** (captura + reporte, sin score); Eva 360 si cabe; cerrar bugs; escribir el `Docs/` final del refactor |

**Checkpoint fin S4:** MVP integrado. **Veredicto sobre el tercero.**

## Degradación con gracia

Si al **fin de S3** el núcleo no está sólido: **congela Clima y Eva 360** — quedan "listos para enchufar" (una config de distancia, porque el motor ya existe) y se prioriza que motor + Norma 035 + 3 UIs + salida salgan firmes. El pulido (PDF bonito de todos los tipos, reportes agregados) es lo primero que se corta, siempre.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| **El tercero no rinde el medio tiempo** (objeto de la prueba) | Checkpoints semanales; señal temprana en S1 con la comprobación (que él hace rápido) |
| **Encuestas se alarga** (polo largo) | MVP definido + orden de recorte claro |
| **Sobre-diseño del motor** (Parkinson) | Timebox el diseño a S0-S1; de lo concreto (norma035) a lo general |
| **Bugs pre-existentes del back compiten por tus horas** — la comprobación destapará cosas ya conocidas: PUT `/employee/vacation` reusa el form de insert (`KeyError` latente en `prima`), `create_mail_payroll` sigue en SharePoint aunque nómina migró a S3, CSVs con rutas relativas hardcodeadas | Solo se arregla lo que el front destape o lo crítico; el resto a backlog. No abrir yaks |
| **Test DB sin datos** → comprobación humo | Seed en S0 (bloqueante) |

> **Seguimiento vivo:** el estado actual de tareas front/back está en [`pendientes.md`](pendientes.md) (tracker general de todas las áreas, sección RH / Encuestas).

## Entregables del mes

- Hoja de comprobación cerrada + bugs corregidos.
- Motor de evaluación config-driven (back).
- Norma 035 + salida end-to-end; clima/eva360 según alcance.
- 3 UIs de encuestas integradas (front).
- `Docs/encuestas_refactor.md` con bloque de contrato para el front.
- **Veredicto documentado** sobre la viabilidad del tercero a medio tiempo.
