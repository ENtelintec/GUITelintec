# Plan de acción — pendientes abiertos (octubre 2026)

> **Estado: acordado** (grill del 2026-10-12: orden del front Cobranza → nómina → RH → multisede, SES tras nómina en test, custom_fields se conservan, defaults a 2 semanas, backlog se lee del repo). **Avance 2026-10-12**: Bloque A del back cerrado — anexos del checklist vehicular sin carrera + rollback del alta ([`checklist_vehicular_anexos_sin_carrera.md`](../checklist_vehicular_anexos_sin_carrera.md), 31/31) y los dos DML de RH entregados ([`rh_calidad_datos_dml.md`](../rh_calidad_datos_dml.md), pendientes de correr por el usuario). `P-121` sugerencias de costos hecho el mismo día (22/22, [`quotation_cost_suggest.md`](../quotation_cost_suggest.md)). `P-103` anexos EPP/herramientas hecho el mismo día (29/29 + regresión del vehicular, helper compartido, [`vales_anexos_sin_carrera.md`](../vales_anexos_sin_carrera.md)). Sigue el Bloque B: `P-017` PDF del agregado eva 360. **Avance del front 2026-10-13** (reporte `docs/avance-plan-accion-2026-10.md` de su repo): lote 1 completo; nómina (`P-032`/`P-037`) se hizo antes que Cobranza; Cobranza tiene todo su código **🧪 listo para probar** y espera la sesión de prueba en test (`P-094`); `P-079` cerrado por decisión; sigue `P-070`. Los bugs de integración que levantó quedaron resueltos el mismo día en el back: `P-131` (`PUT /quotation` conserva `exchange_rate`; `codigo` sale del contrato, DML de limpieza `P-138`) y `P-132` (descarga del recibo de nómina: además cerraba una fuga entre empleados). **Avance 2026-10-16**: respuesta al reporte del front del 2026-10-15 ([`respuesta_front_2026_10_16.md`](../respuesta_front_2026_10_16.md)): lotes 4, 5 y 6 del front con código hecho; cerrados `P-030`, `P-043`, `P-109`, `P-133`, `P-134`, `P-137`, `P-047` (resolve de traslados) y `P-054` (decisión); Cobranza sigue 🧪 (prueba local, falta test); back: PUT de vales conserva anexos + descarga/borrado, `quizz_name`, `PUT /balanceControl/movement`, firma de quien entrega en SM, multisede resolve/meta/formatos; DML de nómina limpia (`P-141`). Sustituye a los planes de mes ([`plan_rh_mes.md`](archivo/plan_rh_mes.md), [`plan_mes_2.md`](archivo/plan_mes_2.md), ambos archivados): ya no hay un tercero de front con calendario por semanas; el **equipo de front principal** absorbe el backlog y lo toma en el orden de la sección 4. Nace de la revisión de [`pendientes.md`](../pendientes.md) (55 ítems abiertos). El back (usuario + agente) trabaja en el orden de la sección 3. Las decisiones y datos que faltan están en la sección 2, cada una con un *default* para no quedarse esperando. Sin fechas duras: el orden es la decisión; el ritmo lo marca el front.

## 1. Diagnóstico

| Tipo | Abiertos | Qué son |
|---|---|---|
| `[back]` | 18 | 4 deuda/bugs reales · 5 piezas sin dependencia de front · 4 esperan dato o decisión del negocio · 5 congelados |
| `[front]` | 27 | 10 ajustes de contrato chicos (varios corrigen datos que hoy se ensucian en prod) · 17 pantallas nuevas con back servido |
| mixtos (`[front+back]`, `[back+front]`) | 4 | el front captura primero y el back incrusta después |
| `[admin]` / `[ops]` / `[decisión]` | 6 | no son código: dato de administración/RH, decisión del usuario o acceso de AWS |

Lo que se ve al leer el tracker completo:

- **El back va dos bloques por delante del front.** Todo el back del mes 2 (nómina, constructor, multisede F0–F3, dashboard RH) y todo el bloque de administración (saldos, entregas/OCD, cancelar remisión, vigencia, costos, formatos ISO, CDA) tiene contrato publicado y verificado contra dev, y **ninguna** pantalla consumidora cerrada.
- **Lo urgente de verdad está en el lote chico del front**: el `PUT /activity/quotation` duplica items en cada guardado, las firmas de anexos solo quedan protegidas por heurística de nombre, y Control de Reportes sigue escribiendo en llaves viejas. Son días de trabajo, no semanas, y corrigen datos de prod.
- **La deuda abierta del back es chica y está en SGI**: anexos del checklist vehicular (carrera + validación muerta + ventana de 365 días) y el alta sin rollback. Lo demás del back o no tiene consumidor todavía o espera un dato del negocio.
- **Seis ítems no avanzan con código.** Sin respuesta se quedan abiertos para siempre; por eso cada uno lleva un *default* abajo.

## 2. Decisiones y datos que faltan

| # | Qué falta | Quién | Qué desbloquea | Default si no hay respuesta |
|---|---|---|---|---|
| 1 | `P-036` **SES a producción**: *production access*, `SES_SENDER`/`SES_REGION` en `.env` de test/prod, MAIL FROM corregido ([`nomina_correo_ses.md`](../nomina_correo_ses.md)) | usuario (AWS) | correo real de nómina; correos internos | **Decidido 2026-10-12**: se pide *production access* cuando nómina esté integrada en test; mientras, test/prod sin canal `email` (el `notify` lo reporta en `channels_failed`) |
| 2 | `P-048` **Datos de la sede**: nombre/encargado, usuarios con `Sucursal-2`, **fecha del cambio del DELETE** ([`almacen_multisede_plan.md`](almacen_multisede_plan.md)) | administración | prod de multisede; F4 (fix DELETE) | **Decidido 2026-10-12**: se piden 2 semanas antes de que el front arranque el lote 5; hasta entonces F4 no se toca y prod de multisede sigue bloqueado |
| 3 | `P-047` **Procedimiento de discrepancias de traslados** (`RECIBIDO CON DIFERENCIAS`: quién resuelve y con qué movimiento) ([`almacen_multisede_f3.md`](../almacen_multisede_f3.md)) | administración / operación | nada de código | documentar la respuesta en el doc de F3 y cerrar |
| 4 | `P-039` **Calidad de datos RH**: 11 activos con `departure` arrastrada, inactivos sin baja, activos sin cumpleaños, vacaciones sin `dates` ([`dashboard_rrhh.md`](../dashboard_rrhh.md)) | RH | dashboard limpio | DML entregado ([`rh_calidad_datos_dml.md`](../rh_calidad_datos_dml.md)). **Decidido 2026-10-12**: el bloque A (`status` NULL del 123) espera la respuesta de RH; el bloque B (`puesto` `'None'`) corre ya en dev; el resto lo corrige RH desde la pantalla |
| 5 | **`custom_fields` / `delivery_fields` al re-adoptar o retirar** ([`remission_atomic_writes.md`](../remission_atomic_writes.md)) | usuario | nada hoy | **Decidido 2026-10-12: se conservan.** Ítem cerrado en `pendientes.md` |
| 6 | `P-094` **Cobranza en el ambiente de test** + lista de usuarios de test (líderes incluidos) | usuario / ops | que Cobranza pruebe saldos y entregas antes de que el front cierre | crear los usuarios al arrancar el lote 3 del front; el esquema ya está completo en test |
| 7 | `P-053` **Modelo de datos del reporte Ternium** ([`remission_combined_pdf.md`](../remission_combined_pdf.md)) | administración | back del reporte generado | sigue fuera; el escaneo como anexo cubre hoy |
| 8 | `P-123` **Control de licitaciones FO-PRE-04** (formato recibido, sin tarea) | administración / usuario | ¿entra o no? | **Decidido 2026-10-19: entra.** Preventa lo pidió y el front ya tiene pantallas; back hecho y verificado en dev el mismo día ([`tenders_control.md`](../tenders_control.md)); DDL en las 3 BDs (`P-146`); falta el front (`P-147`) |
| 9 | `P-098` **DML `voucher_vehicle_accessories_normalize.sql`** en dev/test/prod ([`checklist_vehicular_accessories.md`](../checklist_vehicular_accessories.md)) | usuario | nada (los lectores toleran ambas formas) | correrlo con el siguiente tren de deploy |
| 10 | **Orden del front** (sección 4): Cobranza antes que constructor y multisede | usuario + front principal | todo el front | **Decidido 2026-10-12** (ajustado el mismo día): **Cobranza → nómina → RH → multisede**; la prioridad de negocio es Cobranza |

## 3. Back — orden de trabajo

**Regla del periodo:** el back no abre contratos nuevos que necesiten pantalla hasta que el front consuma los que ya hay. Primero deuda y desbloqueos, después lo que no depende del front; los bugs de integración que levante el front van **antes** que cualquier cosa del bloque B. Verificación contra dev y doc por pieza como siempre; DDL/DML en `scripts_db_handle/`, los corre el usuario.

### Bloque A — deuda y bugs (primero)

1. ~~`P-100`~~ **Anexos del checklist vehicular** ([`checklist_vehicular_full_pdf.md`](../checklist_vehicular_full_pdf.md)): `extra_info.files` con escritura condicional + reintentos (mismo patrón de [`remission_anexos_sin_carrera.md`](../remission_anexos_sin_carrera.md)), validación nombre↔voucher con `or`, quitar la ventana de 365 días del alta. Doc nuevo con contrato (el front gana el 409 de contención, igual que en remisiones).
2. ~~`P-101`~~ **Alta del voucher vehicular con rollback** ([`checklist_vehicular_accessories.md`](../checklist_vehicular_accessories.md)): si falla el insert de `voucher_vehicle`, borrar el `vouchers_general` recién creado. Mismo doc que el punto 1.
3. `P-039` **Calidad de datos RH, parte mecánica** (decisión 4): DML idempotente para `status` NULL (emp 123) y `'None'` → NULL en `puesto` (7 y 39), más el listado de los 11 `departure` para RH. Sin código.
4. `P-042` **`alergies`/`allergies`** ([`notificaciones_medicas_fix.md`](../notificaciones_medicas_fix.md)): DML idempotente que renombra la llave vieja + lector con una sola llave. Chico; va junto con el punto 3.

### Bloque B — sin dependencia del front (después, en este orden)

5. `P-121` **Sugerencias de análisis de costos**: `GET /quotation/costAnalysis/suggest?n_part=` desde análisis anteriores e items cotizados (el índice `quotation_items(n_part)` ya existe) → [`quotation_cost_analysis.md`](../quotation_cost_analysis.md). Es la única pieza nueva con contrato pendiente que el front consumirá en el lote 2. **Diseño acordado (2026-10-12)**: `?n_part=` exacto (valores genéricos → lista vacía con aviso) y `?description=` por texto (mín. 3 caracteres, sin FULLTEXT: ~2,000 filas), dos fuentes: `analyses` (últimos análisis con su comparativa) y `quoted` (últimos items cotizados con precio, moneda, fecha y cliente); permiso `administracion`. **Grill 2026-10-12**: `quoted` sale de **todas** las cotizaciones con `quotation.{status, document_type}` por fila y `?exclude_quotation_id=`; n_part genérico (GENERICO, S/N, N/A, NA, -, ., < 3 caracteres) → 200 con listas vacías y `generic: true`.
5b. `P-103` **Anexos de vales EPP y herramientas sin carrera**: misma receta que el vehicular ([`checklist_vehicular_anexos_sin_carrera.md`](../checklist_vehicular_anexos_sin_carrera.md)), tester reutilizado. Va justo después del punto 5 (decisión 2026-10-12). **Grill 2026-10-12**: receta completa (carrera + nombre real + sin ventana de 365 días en alta/descarga) para EPP y herramientas, más el fix de `delete_voucher_safety_api` (borra `voucher_tools` en vez de `voucher_safety`); el ciclo CAS y el lookup pasan a un helper compartido en `templates/resources/methods/Functions_Aux_Vouchers.py` que usan los 3 tipos de vale (el vehicular se refactoriza sobre él y se re-verifica).
6. `P-017` **PDF del agregado eva 360** (radar/tabla comparativa del proceso; skill `pdf-design`) → [`eva360_evaluation.md`](../eva360_evaluation.md).
7. `P-016` **Rediseño del PDF de Norma 035** leyendo `evaluation` directo (quita `_legacy_shape_from_evaluation`) → [`encuestas_refactor.md`](../encuestas_refactor.md).
8. `P-115` **Conciliación por cantidades** OC ↔ entradas, producto a producto → [`po_movements_inbound_match.md`](../po_movements_inbound_match.md).
9. `P-114` **PDFs legacy a cuadrícula**: PO y cotización primero, vale EPP/herramienta y devolución después → [`pdf_tipografia_helvetica_y_cuadricula_remision.md`](../pdf_tipografia_helvetica_y_cuadricula_remision.md).

### Bloque C — condicionados (entran cuando llegue el dato o el front dé el paso)

10. `P-046` **Multisede F4**: fix "DELETE revierte stock" en ambas sedes con la fecha de administración y aviso a operación (decisión 2); exports/dashboard de sede solo cuando el front los pida.
11. `P-036` · `P-095` **SES**: variables a test/prod cuando haya *production access* (decisión 1); después revisar qué correos internos saldrán por SES.
12. `P-045` · `P-054` **Firma de "quien entrega"** en SM y remisión: el back incrusta cuando el front la capture (mismo mecanismo que la de quien recibe) → [`sm_pdf_delivery_signatures.md`](../sm_pdf_delivery_signatures.md) · [`remission_combined_pdf.md`](../remission_combined_pdf.md).
13. `P-015` **Normalizar el shape de respuestas de captura** (quita `flatten_responses`): coordinado con el front cuando toque la UI de captura.
14. `P-056` **Borrado de anexos en lote**: solo si el front agrega selección múltiple.

### Bloque D — congelados (se quedan en `pendientes.md` con su razón; no se trabajan)

`P-044` Bug KPI de SM (KPIs configurables a futuro) · `P-091` `operaciones` en lectura de `deliveryControl` (fuera, 2026-09-28) · `P-092` saldo comprometido FO-PRE-03 (posibilidad) · `P-113` otros activos CDA (sin definición) · `P-022` PDFs dedicados por encuesta y editor de rúbricas (según pida RH) · `P-053` reporte Ternium (sin modelo) · `P-095` notificación in-app de correos (sin alcance) · ~~`P-123` control de licitaciones~~ (entró el 2026-10-19 → [`tenders_control.md`](../tenders_control.md)) · import de vehículos CDA en prod (con el deploy del módulo).

## 4. Front — backlog priorizado para el equipo de front principal

Cada ítem lleva su id `P-NNN` de [`pendientes.md`](../pendientes.md) (estable; el front reporta por id, p. ej. "P-052 hecho") y tiene su contrato en el doc enlazado (sección "Contrato mínimo para el front"); el back no reexplica por chat, apunta al doc. Criterio de orden: **corrige datos en prod** > **desbloquea un proceso de negocio con back ya servido** > **pantalla nueva**. Un lote se da por cerrado cuando está integrado contra dev y probado en test.

### Lote 1 — ajustes de contrato (chicos; primero porque varios corrigen datos de prod)

| # | Id | Qué | Doc |
|---|---|---|---|
| 1 | `P-052` | `PUT /activity/quotation`: mandar `qa_item_id` e `item_contract_id` (con `id`/`client_id` los items se **duplican** en cada guardado) | [`quotation_activity_upsert_null_fix.md`](../quotation_activity_upsert_null_fix.md) |
| 2 | `P-055` | Mandar `category` en el `POST` de anexos de remisión (firmas protegidas hoy solo por heurística de nombre) | [`remission_attachment_delete.md`](../remission_attachment_delete.md) |
| 3 | `P-063` | Reintentar tal cual el **409** de `POST`/`DELETE /remission/attachment-<id>`; subir en paralelo ya es seguro | [`remission_anexos_sin_carrera.md`](../remission_anexos_sin_carrera.md) |
| 4 | `P-059` | Control de Reportes: escribir/leer `total_sin_iva_admi` y `remission_sent_date_client`, decidir qué fecha pinta la columna, probar la pantalla de líderes con token puro de Operaciones | [`control_table_operaciones_y_campos_admin.md`](../control_table_operaciones_y_campos_admin.md) |
| 5 | `P-119` | `PUT /contract` y `PUT /quotation`: refrescar `qa_item_id` desde `data.items` (por `index`) y dejar de mandar `comment` | [`contract_items_put_resultado.md`](../contract_items_put_resultado.md) |
| 6 | `P-020` | Descargas CSV de RRHH con parser CSV; vacaciones `POST` duplicado → 409, `PUT` sin registro → 404 | [`rrhh_vacaciones_y_csv.md`](../rrhh_vacaciones_y_csv.md) |
| 7 | `P-041` | Exámenes médicos: pintar `alert`/`due_date`; `error` lista no es fallo | [`notificaciones_medicas_fix.md`](../notificaciones_medicas_fix.md) |
| 8 | `P-107` | Selector de contrato del checklist vehicular (`GET /common/contracts`, "Sin contrato" manda `null`) | [`checklist_vehicular_contrato.md`](../checklist_vehicular_contrato.md) |
| 9 | `P-099` | Botón "PDF completo" del checklist vehicular (`?full=1`, blob en 200) | [`checklist_vehicular_full_pdf.md`](../checklist_vehicular_full_pdf.md) |
| 10 | `P-037` | Link de WhatsApp de nómina (`wa.me/<tel>?text=…`, sin endpoint) | [`plan_mes_2.md`](archivo/plan_mes_2.md) (Anexo A) |
| 11 | `P-102` | Anexos del checklist vehicular: reintentar el **409** tal cual y manejar el **404** de voucher inexistente | [`checklist_vehicular_anexos_sin_carrera.md`](../checklist_vehicular_anexos_sin_carrera.md) |

### Lote 2 — Cobranza / Administración (**prioridad 1 de negocio**; back completo; junta del 2026-09-23)

| Orden | Id | Pantalla | Doc |
|---|---|---|---|
| a | `P-068` | Control de saldos: alta (`POST /balanceControl`), catálogos, `custom_fields` por `balance_control_id` | [`control_saldos_cabecera.md`](../control_saldos_cabecera.md) |
| b | `P-079` | Controles sin contrato: rama `client_id`+`title`, selector de remisiones disponibles, `PUT /balanceControl/remissions`, 400 nuevo | [`control_saldos_sin_contrato.md`](../control_saldos_sin_contrato.md) |
| c | `P-073` | Movimientos de saldo con `expected_balance` y 409 | [`control_saldos_movimientos.md`](../control_saldos_movimientos.md) |
| d | `P-088` | Ventana de inyección/vigencia (`type 3`, `new_end_date`, `changed`, `days_to_end`, `?expiring_days=`), quitar `end_date` de la cabecera | [`control_saldos_vigencia.md`](../control_saldos_vigencia.md) |
| e | `P-057` | Pantalla de control de saldos sobre `GET /remission-0?include_items=0` + filtros + 4 campos del `PUT /remissionBalance` | [`remission_balance_get_filters_campos_nuevos.md`](../remission_balance_get_filters_campos_nuevos.md) |
| f | `P-074` | Limpieza: retirar `ControlSaldos.tsx` viejo, resumen con datos del control, conciliar `CONTRACT_CONFIG` con `config.columns` | [`control_saldos_cabecera.md`](../control_saldos_cabecera.md) |
| g | `P-080 · P-093` | F1 discrepancia `total_sin_iva` vs `_admi` · F2 maqueta del historial · responsive de Control de Saldos | doc del front |
| h | `P-090` | Control de Entregas / OCD: lista + detalle por partida, conversión a OCD, **cancelar remisión**, aviso por vencer; retirar "crear control de saldos" para OCD | [`control_entregas.md`](../control_entregas.md) · [`quotation_ocd.md`](../quotation_ocd.md) · [`remission_cancel.md`](../remission_cancel.md) · [`control_entregas_ocd_plan.md`](control_entregas_ocd_plan.md) |
| i | `P-122` | Análisis de costos por item + "aplicar precios" (y sugerencias cuando el back cierre el punto 5) | [`quotation_cost_analysis.md`](../quotation_cost_analysis.md) |
| j | `P-070` | Catálogo SGI de formatos ISO (lista/alta/revisión/retirar) | [`iso_formats_crud.md`](../iso_formats_crud.md) |

Al arrancar este lote (es el siguiente tras el lote 1) se crean los usuarios de test de Cobranza (`P-094`, decisión 6).

### Lote 3 — Nómina (`P-032`; arrastre del mes 2; después de Cobranza por decisión del 2026-10-12)

Pantallas de RH (carga por periodo simulada, reemplazar, eliminar, notificar con `channels`) y del empleado (sus recibos, zip, bandeja) → [`nomina_gestion_archivos_y_notificacion.md`](../nomina_gestion_archivos_y_notificacion.md) · [`nomina_correo_ses.md`](../nomina_correo_ses.md) · Anexo A de [`plan_mes_2.md`](archivo/plan_mes_2.md). El canal `email` se enciende solo con la decisión 1.

### Lote 4 — RH (`P-030` constructor · `P-043` dashboard; arrastre del mes 2)

Constructor visual de encuestas (listado por versiones, clonar, editor visual del template, pestaña "Avanzado", publicar con "migrar pendientes" desmarcado) → [`quizz_models_versionado.md`](../quizz_models_versionado.md) · [`quizz_models_crud.md`](../quizz_models_crud.md). Pantalla del dashboard RH (tiles clicables + 2 gráficas) → [`dashboard_rrhh.md`](../dashboard_rrhh.md).

### Lote 5 — Almacén multisede (`P-049`; arrastre del mes 2; prod bloqueado por la decisión 2)

Inventario y movimientos de sede ([`almacen_multisede_f2.md`](../almacen_multisede_f2.md)) → recepción de traslados + crear traslado en el principal ([`almacen_multisede_f3.md`](../almacen_multisede_f3.md)). Menú por permiso `Sucursal-<id>`. Segunda etapa: consolidado, catálogo de sedes, cancelar, exports, dashboard de sede.

### Lote 6 — CDA (`P-109` galería/alertas · `P-110` módulo)

Galería de fotos + tile de alertas ([`cda_alertas_y_fotos.md`](../cda_alertas_y_fotos.md)); las 6 vistas y el CRUD de vehículos/pólizas/servicios/llantas/multas/compras ([`control_vehiculos_cda.md`](../control_vehiculos_cda.md)). Al salir: import del Excel en prod (back).

### Mixtos (el front da el primer paso; el back responde en el bloque C)

Firma de "quien entrega" en SM (`P-045`) y remisión (`P-054`) · borrado de anexos en lote (`P-056`, solo si hay selección múltiple) · normalizar el shape de respuestas de captura.

> **Por qué Cobranza primero** (decisión 10, ajustada el 2026-10-12 por el usuario: la prioridad de negocio es Cobranza): la junta del 2026-09-23 pidió ambiente de prueba y responsive, y el bloque tiene 10 docs de back esperando pantalla. Nómina sigue inmediatamente después (su back está completo y el canal SES se pide cuando esté en test); constructor y multisede no tienen fecha de negocio detrás.

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| El equipo de front principal entra sin el contexto del mes 2 | Cada ítem del backlog apunta a su doc con contrato; los anexos del plan archivado siguen legibles. Primer paso del front: leer `pendientes.md` + este doc, no el histórico |
| Datos de prod se siguen ensuciando mientras el lote 1 no se integra (duplicación de items, firmas sin categoría) | Lote 1 va antes que cualquier pantalla nueva; es trabajo de días |
| El back se adelanta todavía más y crece la pila de contratos sin consumidor | Regla de la sección 3: nada nuevo con pantalla hasta que el front consuma; el bloque B es trabajo sin front |
| Las decisiones de la sección 2 no llegan | Cada una tiene *default*; si en dos semanas no hay respuesta se aplica el default y se anota en el doc correspondiente |
| F4 cambia el comportamiento del DELETE del principal sin aviso | No se toca sin fecha de administración y aviso explícito a operación |

## 6. Seguimiento

- Estado por ítem: [`pendientes.md`](../pendientes.md) (fuente de verdad). Este doc solo fija el **orden**. El equipo de front principal **lee ambos del repo**; no hay copia aparte (decisión 2026-10-12).
- Deploy: lo hecho en dev (vehicular, sugerencias de costos, DML de test/prod) sale **con el próximo tren planeado**, sin tren propio.
- Regla de los defaults (sección 2) confirmada: a las 2 semanas sin respuesta se aplica y se anota en el doc del ítem.
- Al cerrar un lote del front o un bloque del back: actualizar `pendientes.md`, y aquí solo la línea de *Estado* del encabezado.
- El doc se archiva cuando el lote 1 del front esté integrado, el bloque A del back cerrado y las 10 decisiones con respuesta o default aplicado; entonces se repriorizan los lotes 3–6 en un doc nuevo.
