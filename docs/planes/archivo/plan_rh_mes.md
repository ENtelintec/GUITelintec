# Plan de trabajo — Módulo RH (1 mes)

> Plan de sprint de ~4 semanas para el módulo de RH. Dos frentes: (1) comprobación de endpoints y (2) refactor del módulo de encuestas centrado en la evaluación/interpretación. El front es un tercero a medio tiempo en evaluación.

## Estado — actualizado 2026-08-10 (arranque de S2 calendario)

**El back va adelantado ~2 semanas**: todo su trabajo de encuestas de S2–S4 salvo la salida (tipo 0) está hecho y verificado, más un bloque no planeado que absorbió la holgura (CRUD de modelos de encuesta y la migración de esquema completa, Fases 1 **y** 2). El polo largo del mes pasó del back al **front (las UIs) y al tren de deploy**.

| Frente | Hecho ✅ | Falta |
|---|---|---|
| Comprobación (S1) | Hoja cerrada + bugs CSV corregidos y re-probados | — |
| Motor + tipos | Motor config-driven · Norma 035 · clima laboral · eva 360 · CRUD de modelos ([`quizz_models_crud.md`](quizz_models_crud.md)) | **Salida (tipo 0)** — cualitativa, chica |
| Esquema/namespaces *(no planeado; grill 2026-08-07)* | Consolidación `misc`→`rrhh` · migración F1 (`quizz_tasks`) · **F2 adelantada** (5 privadas + `aptitude`) · seed `quizz_models` en test/prod | Regresión del tester (secciones F2) · **deploy de prod del tren S2+F2** · `DROP` de las 7 vistas puente |
| Front | — | Las **3 UIs del MVP** (asignación, captura, resultados) + cambiar prefijo `misc`→`rrhh` en 3 rutas; extras según alcance: tabla de clima, admin de modelos, UI eva 360 |

Detalle vivo por ítem en [`pendientes.md`](pendientes.md) (sección RH / Encuestas). Para integrar las UIs: **mapa completo de endpoints de encuestas y eva 360 en el [Anexo](#anexo--api-de-encuestas-y-eva-360-referencia-para-el-front)** al final de este doc.

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
| **Encuestas — arquitectura** | Motor **config-driven** (rúbrica en datos, ajustable por el back), ~~sobre `tasks_gui`, sin migración de esquema, sin UI de admin~~ → **revisado sobre la marcha**: la migración de esquema sí se hizo (F1+F2, grill 2026-08-07 → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md); la tabla ahora es `mod_rrhh.quizz_tasks`) y los modelos ganaron CRUD por API ([`quizz_models_crud.md`](quizz_models_crud.md)); sigue sin constructor visual |
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

- [x] **Sembrar `HOST_DB_TEST`**: empleado(s) con examen médico + vacaciones + una encuesta asignada de **cada** tipo (0-4). Sin esto, los GET devuelven vacío y la comprobación es humo.
- [x] Alta del **token/usuario `is_tester`** para el tercero.
- [x] Crear la **hoja de comprobación** (columnas: endpoint · método · request enviado · status recibido · esperado · ✅/❌ · nota).
- [x] **Diseño del motor config-driven**: formato de la config de rúbrica (cómo un tipo declara puntuación e interpretación). Timebox estricto — arrancar de Norma 035 concreto y generalizar; no sobre-diseñar.

### Semana 1 — Comprobación (front) ‖ Motor + contratos (back)

| Front (tercero) | Back (tú) |
|---|---|
| Comprobar los ~38 endpoints, llenar la hoja | Construir el esqueleto del motor config-driven (reemplaza `calculate_results_quizzes`/`recommendations_results_quizzes`) |
| | Escribir los **contratos** en `Docs/` (bloque "Contrato mínimo para el front") de asignación, captura y resultados |
| | Triar y empezar a cerrar los bugs que el front reporta |

**Checkpoint fin S1:** hoja llena. *Primera señal de throughput. Si aquí se cae, es alerta temprana.*

> ✅ **Cumplido (2026-08-07)**: hoja llena y cerrada; destapó 3 bugs reales (descargas CSV de RRHH, → [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md)) con diagnóstico correcto, corregidos el mismo día y re-probados sin más hallazgos. Señal de throughput del tercero: positiva.

### Semana 2 — Pivote a encuestas

| Front | Back |
|---|---|
| Integrar **≥1 UI** (empezar por asignación o captura, las de menor riesgo) contra los contratos | Terminar motor + **Norma 035 end-to-end** (scoring + interpretación + PDF) |
| | **Consolidar los dos namespaces** (`misc` + `rrhh`) de encuestas en uno + **migración de esquema Fase 1** en el mismo lote (`tasks_gui` → `mod_rrhh.quizz_tasks`, vista puente; → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md)) |
| | Cerrar bugs de la hoja; entregar contratos finales |

**Checkpoint fin S2:** ≥1 UI integrada.

> ✅ **Back de S2 cumplido por adelantado (2026-08-07)**: motor y Norma 035 venían hechos de S1; consolidación de namespaces + migración de esquema **Fase 1 y Fase 2** ejecutadas en un solo tren (DDL en las 3 BDs, corte duro `misc`→`rrhh`, 89+7 literales, smoke verde, `pyrefly` sin errores nuevos) y seed de `quizz_models` en test/prod. Queda del tren: regresión del tester, deploy de prod y `DROP` de las 7 vistas. **El front debe actualizar el prefijo de 3 rutas** → [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md). El gate de la semana es solo del front: ≥1 UI integrada.

### Semana 3 — Núcleo funcional

| Front | Back |
|---|---|
| Las **3 UIs funcionales con Norma 035** (asignación, captura, resultados mostrando la interpretación estructurada nueva) | ~~Clima laboral / Eva 360~~ (ya hechos en S1–S2) → **Salida (tipo 0)**, adelantada de S4 |
| Re-correr con la hoja las **secciones afectadas por Fase 2** (médicos, fichajes, bitácora, vacaciones, nómina) vs test | Soporte de integración al front; coordinar la regresión Fase 2 |

**Checkpoint fin S3:** 3 UIs funcionales con Norma 035 + regresión Fase 2 verde (gate del deploy de prod). *Punto de decisión de recorte: si el front va tarde, se congelan las UIs extra (clima/modelos/eva360) — el back ya no tiene nada que congelar.*

### Semana 4 — Cierre e integración

| Front | Back |
|---|---|
| Integrar **salida** (cualitativa), cerrar bugs de integración, pulir | **Deploy de prod del tren S2+Fase2** (post-regresión) + gracia + `DROP` de las 7 vistas puente (DDL del usuario) |
| | Cerrar bugs de integración; pulido según alcance (PDF Norma 035 leyendo `evaluation` directo, PDF agregado eva 360, borrar código muerto) |

**Checkpoint fin S4:** MVP integrado + tren desplegado en prod. **Veredicto sobre el tercero.**

## Degradación con gracia

*(Revisado 2026-08-10: la lista de recorte original — clima y eva 360 — ya se entregó, así que el recorte vive ahora del lado del front y del pulido.)* Si al **fin de S3** el núcleo no está sólido: se congelan las **UIs extra** (tabla de clima, admin de modelos, UI eva 360 — el backend de las tres ya está servido y documentado, quedan "listas para enchufar") y se prioriza que las 3 UIs del MVP + salida salgan firmes. El pulido (PDFs dedicados/rediseños, borrar código muerto) es lo primero que se corta, siempre. El **deploy del tren S2+Fase2 no se recorta**: sin él, prod convive indefinidamente con las vistas puente.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| **El tercero no rinde el medio tiempo** (objeto de la prueba) | Checkpoints semanales; señal temprana en S1 con la comprobación (que él hace rápido) |
| **Encuestas se alarga** (polo largo) | MVP definido + orden de recorte claro |
| **Sobre-diseño del motor** (Parkinson) | Timebox el diseño a S0-S1; de lo concreto (norma035) a lo general |
| **Bugs pre-existentes del back compiten por tus horas** — la comprobación destapará cosas ya conocidas: PUT `/employee/vacation` reusa el form de insert (`KeyError` latente en `prima`), `create_mail_payroll` sigue en SharePoint aunque nómina migró a S3, CSVs con rutas relativas hardcodeadas *(los unpacks rotos de los CSV ya salieron y se corrigieron en S1)* | Solo se arregla lo que el front destape o lo crítico; el resto a backlog. No abrir yaks |
| **Test DB sin datos** → comprobación humo | Seed en S0 (bloqueante) |
| **El tren S2+Fase2 se queda a medio desplegar** — cuanto más tarde el deploy de prod, más tiempo conviven el código viejo y las vistas puente (y el front integra contra rutas que prod aún no sirve) | Regresión del tester temprano en S3 como gate; deploy en cuanto esté verde; `DROP` de vistas solo tras la gracia |

> **Seguimiento vivo:** el estado actual de tareas front/back está en [`pendientes.md`](pendientes.md) (tracker general de todas las áreas, sección RH / Encuestas).

## Entregables del mes

- [x] Hoja de comprobación cerrada + bugs corregidos.
- [x] Motor de evaluación config-driven (back).
- [ ] Norma 035 ✅ + **salida** (pendiente, S3) end-to-end; clima ✅ / eva360 ✅ (dejaron de ser "según alcance": ya están).
- [ ] 3 UIs de encuestas integradas (front) — **el polo largo restante**.
- [x] `Docs/encuestas_refactor.md` con bloque de contrato para el front (+ los no planeados: [`quizz_models_crud.md`](quizz_models_crud.md), [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md), [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md)).
- [ ] **Tren S2+Fase2 desplegado en prod** + `DROP` de las 7 vistas puente (no estaba en el plan original; ahora es entregable del mes).
- [ ] **Veredicto documentado** sobre la viabilidad del tercero a medio tiempo.

---

## Anexo — API de encuestas y eva 360: referencia para el front

> Mapa consolidado de **todos** los endpoints de encuestas con su uso. El contrato completo de cada grupo (ejemplos de respuesta, códigos de error, esquemas) vive en su doc — esta tabla es para navegar y no perderse. Actualizado 2026-08-10.

**Común a todo:**
- **Base**: `/GUI/api/v1/rrhh` (tras la consolidación **ya no hay encuestas en `misc`**; las rutas viejas dan 404 → [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md)).
- **Auth**: header `Authorization` con el **JWT crudo** (NO `Bearer <token>`).
- **Envelope**: `{"data": ..., "msg": ..., "error": ...}`. La descarga de PDF devuelve **blob binario en 201** y el envelope JSON en 4xx (ramificar por status).

### 1. Modelos de encuesta — administración RH ([`quizz_models_crud.md`](quizz_models_crud.md))

| Método y ruta | Permiso | Uso |
|---|---|---|
| `GET /quizz/models` | `rrhh` | Listado ligero. Sin params = solo ACTIVAS (**el picker de "asignar encuesta"** — reemplaza los tipos hardcodeados); `?all=1` = todos los status (pantalla admin); `?status=N` |
| `GET /quizz/models/catalogs` | `rrhh` | Catálogos: `status`, `widget_types` (campo `type` del template que la captura debe saber renderizar), `response_layouts`, `transitions`, `rules` |
| `GET /quizz/models/<type_q>` | `rrhh` | Detalle completo: `template`, `rubric`, `history`, `tasks_total`/`tasks_answered` (para explicar en UI por qué el template está bloqueado o un DELETE se rechaza) |
| `POST /quizz/models` | `rrhh` | Crear: `{name, template, rubric?}` → nace en **borrador** (no asignable hasta publicar). 201 con `{type_q, warnings}` — los `warnings` se muestran, no bloquean |
| `PUT /quizz/models/<type_q>` | `rrhh` | Edición **parcial** (solo llaves presentes: `name`/`template`/`rubric`). 400 esperables: template con modelo publicado; `rubric: null` fuera de borrador; `status` aquí (usar `/status`) |
| `PUT /quizz/models/<type_q>/status` | `rrhh` | Ciclo de vida: `{"status": N}`. Válidas `0→1` (publicar), `1→2` (archivar), `2→1` (reactivar); mismo status = 200 idempotente |
| `DELETE /quizz/models/<type_q>` | `rrhh` | Físico, sin body. 400 si es protected o tiene tasks (el "borrar" cotidiano de la UI debe ser **archivar**) |

### 2. Asignación de encuestas — RH

| Método y ruta | Permiso | Uso |
|---|---|---|
| `POST /task/quizz` | `rrhh` | Asigna una encuesta a un empleado. Body: `{title, emp_destiny, emp_origin, date_limit, metadata: {type_quizz, name_emp, id_emp, position, ...}, data_raw: "{}"}`. 201 con `{id_task}` + notificación a RRHH. **400 si el modelo no está ACTIVO** (borrador/archivada/inexistente) — mostrar el `msg` |
| `DELETE /task/quizz` | `rrhh` | Desasignar: body `{id}` (id de la task) |

*Para eva 360 NO se usa este POST — ver sección 5 (el proceso crea sus propias tasks).*

### 3. Lado empleado — ver y contestar

| Método y ruta | Permiso | Uso |
|---|---|---|
| `GET /task/<emp_id>` | **auto-acceso** (el propio empleado con su token, o `rrhh`) | Sus encuestas asignadas: `[{id, body, data_raw, timestamp}]`. `data_raw: {}` = pendiente; `body.metadata.type_quizz` dice qué cuestionario pedir |
| `GET /download/quizz/<type_q>` | `rrhh` **o `common`** (desde 2026-08-10 el empleado puede) | El template del cuestionario para renderizar la captura (mismo shape histórico, ahora desde BD) |
| `PUT /task/quizz` | `rrhh` o `common` | **Contestar** (y el único "marcar realizada": no hay endpoint de completar — `data_raw` lleno = encuesta realizada). Body: `{id, body, data_raw}` |

**Gotchas del `PUT /task/quizz`** (los dos clásicos que rompen la integración):
1. `body` se re-manda completo **conservando `metadata` intacta** (trae `type_quizz` y, en eva 360, el linking del proceso; el validador borra llaves no declaradas) y **omitiendo las llaves de fecha vacías** (`""`/`null` las rechaza el form).
2. `data_raw` viaja como **JSON string** y su shape depende del layout del template: por **secciones** (Norma 035/clima: la sección lleva `answer` = lista posicional de pares `[etiqueta, indice]`) o **per-question** (eva 360: `{"4": {"answer": idx}}` con la llave = número de ítem; **índice 0 = la opción "5|..."**, la escala está en orden descendente).

### 4. Resultados — RH ([`encuestas_refactor.md`](encuestas_refactor.md), [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md))

| Método y ruta | Permiso | Uso |
|---|---|---|
| `GET /quizz/<id_task>/evaluation` | `rrhh` | **La UI de resultados**: evaluación on-read, shape uniforme (`total` + `breakdown` recursivo). Ramificar por `data`: `null` → mostrar `msg` (sin rúbrica / no evaluable); render defensivo (`level`/`actions` opcionales por nodo, `score` puede ser `null`) |
| `GET /quizzes` | `rrhh` | Todas las encuestas (con `body` y `data_raw`) — listado administrativo |
| `GET /quizzes/summary/<type_q>` | `rrhh` | Agregado organizacional (clima: % por categoría + total + `detail` por pregunta). Filtros `?date_from=YYYY-MM-DD&date_to=...` inclusivos |
| `POST /download/quizz/report` | `rrhh` | PDF: body `{id, body: {metadata...}, data_raw}` → **blob 201** / envelope 4xx. Tipos 0–4 = PDF dedicado; tipos nuevos = PDF genérico de resumen |

### 5. Eva 360 — proceso multi-evaluador ([`eva360_evaluation.md`](eva360_evaluation.md))

| Método y ruta | Permiso | Uso |
|---|---|---|
| `POST /eva360` | `rrhh` | Crea el proceso completo (task de control + 1 task por evaluador, ligadas por `evaluation_id` UUID). Body: `{evaluated_emp, evaluated_name?, date_limit?, raters: [{role, emp_id}]}` con `role` ∈ `self\|superior\|peer\|subordinate` (2–4, uno por rol) |
| `GET /eva360/<evaluation_id>` | `rrhh` | Seguimiento: `expected_roles`, `status_eval`, y por rater `{id_task, role, answered}` |
| `GET /eva360/<evaluation_id>/result` | `rrhh` | Agregado: `general.score_100` (promedia **solo respondidas**), `by_perspective`, por competencia `by_role`+`average`+`distribution`. **Rol ausente en `by_perspective`/`by_role` = aún no contesta** — cruzar contra `expected_roles` |
| `PUT /eva360/<evaluation_id>/complete` | `rrhh` | Cierra el proceso (idempotente, solo marca) |

*Cada evaluador contesta su task con el flujo normal de la sección 3 (`GET /task/<emp_id>` → `PUT /task/quizz`, shape per-question).*

### Flujos típicos (orden de llamadas)

- **Encuesta normal**: RH: `GET /quizz/models` → `POST /task/quizz` · Empleado: `GET /task/<emp_id>` → `GET /download/quizz/<type_q>` → `PUT /task/quizz` · RH: `GET /quizz/<id_task>/evaluation` (+ `POST /download/quizz/report` para el PDF).
- **Eva 360**: RH: `POST /eva360` · cada evaluador: flujo de la sección 3 · RH: `GET /eva360/<id>` (avance) → `GET /eva360/<id>/result` → `PUT /eva360/<id>/complete`.
- **Encuesta nueva de RH**: `POST /quizz/models` (borrador) → editar con `PUT` → `PUT /status {1}` (publicar) → ya aparece en el picker y se asigna como cualquier otra; resultados y PDF salen del motor sin trabajo extra del front.
