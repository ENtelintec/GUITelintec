# Pendientes — backend y front (todas las áreas)

> Tracker general: solo listado con estado y link al doc que tiene la documentación completa. Cada ítem marca **[back]** / **[front]** (o ambos). Actualizado: 2026-09-11 (mes 2, S1 → [`plan_mes_2.md`](plan_mes_2.md)).

## RH / Encuestas

*Contexto: motor config-driven + Norma 035 ✅ ([`encuestas_refactor.md`](encuestas_refactor.md)), eva 360 ✅ verificado contra BD dev ([`eva360_evaluation.md`](eva360_evaluation.md)), clima laboral ✅ (rúbrica % positivo + agregado organizacional, [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md)) y CRUD de modelos de encuesta ✅ (template+rúbrica en BD, esquema nuevo `sql_telintec_mod_rrhh`, [`quizz_models_crud.md`](quizz_models_crud.md)). Mes 1 cerrado ([`plan_rh_mes.md`](plan_rh_mes.md)): las 6 UIs entregadas. Mes 2 = constructor visual de encuestas con versiones → [`plan_mes_2.md`](plan_mes_2.md).*

- [x] ~~**[back] Clima laboral (tipo 3)**~~ — hecho (2026-08-05): RH entregó criterio + cuestionario nuevo (45 preguntas); `files/rubrics/3.json`, motor con % positivo/neutral excluido/ítem 34 invertido, y endpoint nuevo `GET /rrhh/quizzes/summary/<type_q>` (tabla organizacional). Incluye fix del template JSON inválido que rompía `GET /misc/download/quizz/3`. → [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md)
- [x] ~~**[back] CRUD de modelos de encuesta**~~ — hecho (2026-08-05): crear/editar/publicar/archivar/borrar encuestas por API (`/rrhh/quizz/models`), tabla `quizz_models` en esquema nuevo `sql_telintec_mod_rrhh` (seed 0–4; Norma 035 `protected`), ciclo de vida con candado de template, `validate_rubric`+dry-run, PDF genérico de resumen para tipos sin generador. Verificado contra BD dev. → [`quizz_models_crud.md`](quizz_models_crud.md)
- [x] ~~**[back] Bugs S1 de la comprobación: descargas CSV (employees/medical/vacations)**~~ — hecho (2026-08-07): los 3 GET de descarga tronaban con 500 por desempaquetados desalineados con sus SELECT compartidos; unpacks alineados (CSV byte-idéntico) + guards de NULL + tupla de error → envelope 400. Verificado contra BD dev. → [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md)
- [x] ~~**[front] Comprobación de los ~38 endpoints**~~ — hecho (2026-08-07): hoja compartida llena y cerrada; destapó 3 bugs (descargas CSV → [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md)) y la re-prueba tras el fix salió sin más errores. **Checkpoint S1 del tercero cumplido.** → [`plan_rh_mes.md`](plan_rh_mes.md)
- [x] ~~**[back] Seed de `HOST_DB_TEST` + token `is_tester` + hoja de comprobación**~~ — cerrado con la comprobación (2026-08-07): la S1 corrió completa contra la BD de test con el token del tercero y la hoja quedó llena. → [`plan_rh_mes.md`](plan_rh_mes.md)

**Backend:**

- [x] ~~**[back] Encuesta de salida (tipo 0)**~~ — hecho (2026-09-07, S1 mes 2): rúbrica cualitativa en BD (dev por API; test/prod con `scripts_db_handle/salida_rubrica_tipo0.sql`) y respuestas resueltas a texto en `GET /quizz/<id>/evaluation`. → [`encuesta_salida_cualitativa.md`](encuesta_salida_cualitativa.md)
- [x] ~~**[back] Constructor de encuestas — back (S1 mes 2)**~~ — código hecho (2026-09-07): candado por `tasks_total`, `POST /clone`, publicar-archiva (`replaced_by`), `PUT /migrate-tasks` + `migrate_pending`, `replaces`/`replaced_by` en GET, `migrated_from` en metadata. Migración verificada en dev con tasks desechables. → [`quizz_models_versionado.md`](quizz_models_versionado.md)
- [x] ~~**[back] DDL `quizz_models_versions.sql`**~~ — corrido en dev, test y prod (2026-09-08); ciclo completo verificado (32 checks). → [`quizz_models_versionado.md`](quizz_models_versionado.md)
- [ ] **[back] DML `salida_rubrica_tipo0.sql`** en test/prod (dev ya aplicado por API). → [`encuesta_salida_cualitativa.md`](encuesta_salida_cualitativa.md)
- [x] ~~**[back] Consolidar namespaces** de encuestas (`misc` + `rrhh` en uno)~~ — hecho (2026-08-07) en el lote S2 con la migración Fase 1: los 3 recursos de `misc` (`/task/quizz`, `/task/<emp_id>`, `/download/quizz/<type_q>`) ahora en `rrhh`, **corte duro** (viejas → 404), shapes/permisos idénticos; smoke completo verde vs dev. **El front debe cambiar el prefijo `misc`→`rrhh` en esas 3 rutas.** → [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md)
- [x] ~~**[back] Migración de esquema — Fase 1 (encuestas)**~~ — hecho (2026-08-07): DDL corrido en las 3 BDs (`tasks_gui` → `sql_telintec_mod_rrhh.quizz_tasks` + vista puente, conteos verificados), 7 literales + docstrings actualizados. → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md)
- [ ] **[back] DROP de las 7 vistas puente** (arrastre → S1 mes 2, DDL del usuario) en las 3 BDs (`tasks_gui`, Paso 3 de `scripts_db_handle/migracion_quizz_tasks.sql`, + las 6 de Fase 2, bloque diferido de `migracion_fase2_rrhh.sql`) — **solo cuando prod ya corra el código del tren S2+Fase2** (un solo deploy, decidido 2026-08-07); mientras, las vistas mantienen vivo el código viejo. → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md)
- [x] ~~**[back] Migración de esquema — Fase 2 (adelantada)**~~ — hecho (2026-08-07, mismo día que se adelantó por grill): las 5 tablas RRHH-privadas + `aptitude` a `mod_rrhh` en un lote; DDL corrido por el usuario en las 3 BDs (verificado: conteos vista=tabla, FKs cross-schema a `employees` intactas), barrido de los 89 reemplazos en 6 controllers, grep-cero, `pyrefly` sin errores nuevos, smoke verde vs dev (lecturas + ciclo de escritura en `bitacora_rh`). Mismo tren de deploy que S2. → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md)
- [ ] **[back+front] Regresión Fase 2 + deploy del tren S2+Fase2**: el tester re-corre las secciones afectadas de la hoja (médicos/fichajes/bitácora/vacaciones/nómina) vs test **antes del deploy de prod**; tras la gracia post-deploy, el `DROP` diferido de las 7 vistas (ítem de arriba). El seed de `quizz_models` en prod ya quedó hecho por adelantado (2026-08-07). → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md)
- [ ] **[back+front] Normalizar el shape de respuestas** de captura (eliminaría el adapter `flatten_responses`; coordinar con la UI de captura). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back] Rediseño del PDF de Norma 035** para leer `evaluation` directo (quita el shim `_legacy_shape_from_evaluation`; skill `pdf-design`). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back] PDF del agregado eva 360** (radar/tabla comparativa del proceso). → [`eva360_evaluation.md`](eva360_evaluation.md)
- [ ] **[back] Borrar código muerto deprecado** (`calculate_results_quizzes` / `recommendations_results_quizzes`, sin callers). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back] Bugs pre-existentes de RRHH** (triar según lo que destape la comprobación): `PUT /employee/vacation` reusa el form de insert (`KeyError` latente en `prima`); `create_mail_payroll` sigue en SharePoint aunque nómina migró a S3 (→ [`payroll_s3_upload.md`](payroll_s3_upload.md)); CSVs de descarga con rutas relativas hardcodeadas, **sin quoting** (comas/saltos de línea en valores parten filas — caso real en dev) y sin apellido en employees (`l_name` no se escribe). → [`plan_rh_mes.md`](plan_rh_mes.md) (Riesgos) · [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md)
- [ ] **[back] PDFs dedicados por encuesta** según pida RH (el genérico ya cubre el resumen de cualquier tipo) + editor amigable de rúbricas si RH crea encuestas seguido. → [`quizz_models_crud.md`](quizz_models_crud.md)
- [x] ~~**[back] Seed de `quizz_models` en test/prod**~~ — hecho (2026-08-07): test con `--test` (flag nuevo; el primer intento corrió sin el flag y pegó contra dev, donde el seed idempotente salió todo SKIP) y prod adelantado al deploy (inócuo: el código viejo de prod no lee la tabla). Verificado en ambas: 5 modelos ACTIVA, Norma 035 `protected`; test desbloquea encuestas con `is_tester`. El `GRANT` del recordatorio resultó innecesario: el usuario de app en test/prod tiene privilegios globales (verificado con `SHOW GRANTS`). → [`quizz_models_crud.md`](quizz_models_crud.md)

**Front:**

- [x] ~~**[front] UI de asignación** de encuestas~~ — hecho (cierre del mes 1, confirmado 2026-09-07). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [x] ~~**[front] UI de captura de respuestas**~~ — hecho (cierre del mes 1, confirmado 2026-09-07): Norma 035 por secciones y eva 360 per-question. → [`encuestas_refactor.md`](encuestas_refactor.md) · [`eva360_evaluation.md`](eva360_evaluation.md)
- [x] ~~**[front] UI de resultados**~~ — hecho (cierre del mes 1, confirmado 2026-09-07): componente recursivo sobre `breakdown`. → [`encuestas_refactor.md`](encuestas_refactor.md)
- [x] ~~**[front] Tabla organizacional de clima**~~ — hecho (cierre del mes 1, confirmado 2026-09-07). → [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md)
- [x] ~~**[front] Pantalla de administración de modelos de encuesta**~~ — hecho (cierre del mes 1, confirmado 2026-09-07) con editor JSON crudo de template y rúbrica; el picker ya lee `GET /rrhh/quizz/models`. → [`quizz_models_crud.md`](quizz_models_crud.md)
- [x] ~~**[front] UI de eva 360**~~ — hecho (cierre del mes 1, confirmado 2026-09-07). → [`eva360_evaluation.md`](eva360_evaluation.md)
- [ ] **[front] Constructor visual de encuestas (S2–S3 mes 2)** — sobre la admin de modelos: listado agrupando versiones (`replaces`/`replaced_by`), botón **clonar**, editor visual **solo del template** (agregar/quitar/reordenar preguntas, opciones, widget `1/2/3/5`, subpreguntas, rango `items`), rúbrica en pestaña "Avanzado" (JSON de hoy + `warnings`), publicar con checkbox "migrar pendientes" **desmarcado** por defecto. Sin widgets nuevos. → [`plan_mes_2.md`](plan_mes_2.md)

## RH / Nómina

*Contexto: los archivos ya viven en S3 ([`payroll_s3_upload.md`](payroll_s3_upload.md)); `POST /payroll/mail` sigue en SharePoint + borrador Outlook y está **roto y deprecado**. Prioridad 1 del mes 2 → [`plan_mes_2.md`](plan_mes_2.md) (Anexo A).*

- [x] ~~**[back] Nómina — back (S1 mes 2)**~~ — hecho (2026-09-07): `DELETE /payroll/files`, reemplazo en el `POST`, `POST /payroll/notify`, guard muerto fuera; de paso `get_employee_id_name`/`get_id_employee` siempre devolvían `None` (corregidos). Verificado vs dev con S3 simulado (21 checks). → [`nomina_gestion_archivos_y_notificacion.md`](nomina_gestion_archivos_y_notificacion.md)
- [ ] **[front] Pantallas de nómina (S1–S2 mes 2)**: carga por periodo **simulada** (año/mes/quincena una vez, RH asigna archivo→empleado, el front itera el `POST` un archivo por request), reemplazar, eliminar, notificar; lado empleado (sus recibos + descarga zip + bandeja). → [`plan_mes_2.md`](plan_mes_2.md)
- [x] ~~**[back] `POST /payroll/files/extract`**~~ — hecho (2026-09-07, adelantado de S4: el parser `get_data_xml_file_nomina` ya existía): sugiere RFC/NumEmpleado/periodo/`emp_id_sugerido` (`match_by` `num_empleado` | `nombre`); no sube nada. → [`nomina_gestion_archivos_y_notificacion.md`](nomina_gestion_archivos_y_notificacion.md)
- [ ] **[back] Correo al empleado por AWS SES** (2ª etapa, fuera del mes salvo holgura): mismo `POST /payroll/notify` con `channels: ["app","email"]`, adjuntos desde S3; retira definitivamente `POST /payroll/mail` y `create_mail_draft_with_attachment`. → [`plan_mes_2.md`](plan_mes_2.md)
- [ ] **[front] Link de WhatsApp** (3ª etapa): `wa.me/<tel>?text=…` armado en el front con el teléfono del empleado; sin endpoint. → [`plan_mes_2.md`](plan_mes_2.md)

## RH / Dashboard

- [x] ~~**[back] Dashboard RH — endpoints (S3 mes 2)**~~ ✅ adelantado a S1 (2026-09-10, 98 checks + 10 HTTP): `GET /dashboard/rrhh/summary?month=` + `POST /dashboard/rrhh/series` (`metric` ∈ `altas_bajas|headcount`; **fichajes fuera** por decisión del usuario). → [`dashboard_rrhh.md`](dashboard_rrhh.md)
- [ ] **[admin/RH] Calidad de datos que ensucia el dashboard**: 11 activos con fecha de baja arrastrada en `departure` (reingresos), inactivos sin fecha de baja, activos sin cumpleaños, y `dates` de vacaciones sin capturar (el tile `next_30_days` llega vacío). El `summary` los lista en `data_quality`. → [`dashboard_rrhh.md`](dashboard_rrhh.md)
- [x] ~~**[back] `GET /rrhh/employees/medical/all` nunca avisa vencimientos**~~ ✅ (2026-09-10): regla única `medical_due` en `Functions_Aux_RH.py` para endpoint, daemon y dashboard; `error` vuelve a traer los avisos y cada registro gana `alert`/`due_date`/`days_left`. → [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md)
- [ ] **[front] Exámenes médicos**: pintar `alert`/`due_date` y no tratar `error` lista como fallo en `GET /rrhh/employees/medical/all`. → [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md)
- [ ] **[back] Llave doble `alergies`/`allergies` en `examenes_med.extra_info`** (registros viejos con la vieja; el lector tolera ambas): migrar cuando se toque el CRUD de exámenes. → [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md)
- [ ] **[front] Pantalla del dashboard RH (S4 mes 2)**: tiles clicables a la lista filtrada + 2 gráficas de `series`. Contrato listo en [`dashboard_rrhh.md`](dashboard_rrhh.md). **Primero en recortarse** después de extract/SES. → [`plan_mes_2.md`](plan_mes_2.md)

## SM (solicitudes de material)

- [ ] **[back] Bug KPI** en `get_all_sm`: `(critical_date - critical_date)` siempre da 0. **Deliberadamente no tocar por ahora** — a futuro KPIs configurables por el usuario (agregar/quitar y definir fórmula). → [`sm_response_envelope.md`](sm_response_envelope.md)
- [ ] **[front+back] Firma de "quien entrega"** en el PDF de SM — hoy siempre en blanco; requiere que el front la capture primero y el back la incruste (mismo mecanismo que la de quien recibe). → [`sm_pdf_delivery_signatures.md`](sm_pdf_delivery_signatures.md)

## Almacén / Multisede

*Contexto: plan acordado (grill 2026-08-15) para una segunda sede que solo genera entradas/salidas + traslados desde el principal — [`almacen_multisede_plan.md`](almacen_multisede_plan.md). Nada implementado aún.*

- [ ] **[back] Multisede v1 — Fases 0–4**: ~~F0 DDL + permiso~~ ✅ (dev 2026-09-07; **test/prod pendientes**) → ~~F1 candado en las 11 lecturas del kardex + catálogo de sedes + consolidado~~ ✅ (2026-09-07, 27 checks, [`almacen_multisede_f1.md`](almacen_multisede_f1.md)) → ~~F2 namespace `sucursal`~~ ✅ (2026-09-08, 46 checks, [`almacen_multisede_f2.md`](almacen_multisede_f2.md)) → ~~F3 traslados con en-tránsito~~ ✅ (2026-09-10, 50 checks, [`almacen_multisede_f3.md`](almacen_multisede_f3.md)) → F4 exports/dashboard de sede + fix DELETE revierte stock (ambas sedes, **avisar a operación**). → [`almacen_multisede_plan.md`](almacen_multisede_plan.md)
- [ ] **[admin] Procedimiento de discrepancias de traslados**: quién resuelve un `RECIBIDO CON DIFERENCIAS` en el principal y con qué movimiento (reingreso vs merma); el back no ajusta nada solo. → [`almacen_multisede_f3.md`](almacen_multisede_f3.md)
- [ ] **[back] Plantear a administración los requisitos no-código** — **reunión hecha** (antes del 2026-09-07); **los datos siguen pendientes** (nombre/encargado de la sede, usuarios con `Sucursal-2`, fecha del cambio del DELETE). Mientras: dev/test con placeholders "Sucursal 2"; **prod de multisede fuera del mes 2**. → [`almacen_multisede_plan.md`](almacen_multisede_plan.md) · [`plan_mes_2.md`](plan_mes_2.md)
- [ ] **[back] Multisede — calendario mes 2**: F0, F1, F2 **y F3 hechas en S1** (2026-09-07/10; DDL corrido en las **3 BDs** por el usuario). Todo el back de multisede del mes está servido con contrato; queda F4 solo si sobra · F4 solo si sobra; **contrato de cada fase el lunes de su semana**, código después. El fix del DELETE del principal (F4) **no entra** este mes. → [`plan_mes_2.md`](plan_mes_2.md) · [`almacen_multisede_f1.md`](almacen_multisede_f1.md)
- [ ] **[front] Pantallas multisede — mes 2 (S3–S4)**: **inventario y movimientos de sede** primero (F2 ya servida: contrato en [`almacen_multisede_f2.md`](almacen_multisede_f2.md)), después **recepción de traslados** + formulario mínimo de crear traslado en el principal (F3 ya servida: contrato en [`almacen_multisede_f3.md`](almacen_multisede_f3.md)). Misma app, menú por permiso `Sucursal-<id>`. Fuera del mes: consolidado, catálogo de sedes, cancelar, exports y dashboard de sede. → [`plan_mes_2.md`](plan_mes_2.md) (Anexo C) · [`almacen_multisede_plan.md`](almacen_multisede_plan.md)

## Remisiones (admin/collections)

- [x] ~~**[back] Bug latente `[null]`** en `get_quotation_activity_by_id`~~ — hecho (2026-08-15): `IF(COUNT...)` aplicado, y de paso toda la actividad de cotización quedó sana: el `PUT` era **append-only** (leía `id`/`client_id` en vez de `qa_item_id`/`item_contract_id` del form → siempre creaba, nunca actualizaba/borraba), `PUT /activity/ChangeStatus` era 500 siempre (`KeyError`), FK de `item_c_id` con el default 0, rollback del POST roto, QA sin items ahora actualizable/borrable, 404s. Verificado ciclo completo vs BD dev (22 checks). → [`quotation_activity_upsert_null_fix.md`](quotation_activity_upsert_null_fix.md)
- [x] ~~**[back] PDF combinado**: pre-llenar el `title` del anexo~~ — hecho (2026-08-15): solo en páginas generadas — caption bajo cada foto (máx. 2 líneas) y banner celeste en la página A4 del anexo-imagen; anexos PDF intactos; sin `title`, todo queda como antes. → [`remission_combined_pdf.md`](remission_combined_pdf.md)
- [ ] **[front] Mandar `qa_item_id` e `item_contract_id`** (no `id`/`client_id`) en los items del `PUT /activity/quotation` — con `id` los items se duplican en cada guardado; el PUT sigue sin devolver los `qa_item_id` creados (re-`GET`). → [`quotation_activity_upsert_null_fix.md`](quotation_activity_upsert_null_fix.md)
- [ ] **[back] Reporte de materiales formato Ternium generado** (hoy solo se concatena el escaneo subido como `anexo`; falta modelo de datos — el doc referencia `tareas_admin_windows.md`, que no existe en `Docs/`). → [`remission_combined_pdf.md`](remission_combined_pdf.md)
- [ ] **[front+back] Firma de "quien entrega"** en la remisión (hoy `firma-realizado`/`firma-recibido` cubren autorización 1 y 2). → [`remission_combined_pdf.md`](remission_combined_pdf.md)
- [ ] **[front] Mandar `category` en el `POST` de anexos** — sin ella, una firma subida sin categoría explícita queda protegida solo por heurística de nombre. → [`remission_attachment_delete.md`](remission_attachment_delete.md)
- [ ] **[front+back] Borrado de anexos en lote** — solo si el front agrega selección múltiple. → [`remission_attachment_delete.md`](remission_attachment_delete.md)
- [ ] **[front] Pantalla de control de saldos** — consumir `GET /remission-0?include_items=0` + filtros (`date_from`/`date_to`/`month_period`/`general_status`) y mandar los 4 campos nuevos del `PUT /remissionBalance` (`ot_ticket`, `centro_costos`, `responsable_centro_costos`, `personal_infra`). → [`remission_balance_get_filters_campos_nuevos.md`](remission_balance_get_filters_campos_nuevos.md)
- [x] ~~**[back] Solicitud del front en Control de Reportes** (401 de Operaciones + 2 llaves del bloque administración)~~ — hecho (2026-08-26): `operaciones` en `POST`/`PUT /remissionControlTable` y `GET /remission-<id>` (los líderes capturan la remisión primero); campos propios `total_sin_iva_admi` y `remission_sent_date_client` (independientes de `total_sin_iva`/`remission_sent_date`, receta completa con history); de paso el `DELETE /remission` ya no da 400 en remisiones sin items. Verificado vs BD dev (27 checks). → [`control_table_operaciones_y_campos_admin.md`](control_table_operaciones_y_campos_admin.md)
- [ ] **[front] Apuntar Control de Reportes a las llaves nuevas** — `buildAdministracionControlPayload` escribe `total_sin_iva_admi`/`remission_sent_date_client`, el map del GET las lee, se retiran los avisos de "pendiente de backend"; decidir qué fecha muestra la columna del bloque Administración (`remission_sent_date` vs `remission_sent_date_client`) y re-verificar la carga de la pantalla de líderes con un token puro de Operaciones. → [`control_table_operaciones_y_campos_admin.md`](control_table_operaciones_y_campos_admin.md)


**Control de saldos (Cobranza)** — *contexto: entidad nueva `balance_controls` (1 control activo por contrato, membresía por `activity_reports.contract_id`), catálogo de formatos ISO de SGI en BD (`iso_formats`, ids 1..8 = `settings.json`, 9..13 = FO-CXC-07..11 con `config`), columnas dinámicas y movimientos de saldo inmutables; grill 2026-09-11 → [`control_saldos_cabecera.md`](control_saldos_cabecera.md).*

- [x] ~~**[back] `POST /balanceControl` + GETs + PUT parcial + `/fields` + `/cancel` + `/catalogs`**~~ — hecho (2026-09-11): 4 capas nuevas + DDL corrido en dev (con FKs opcionales); movimiento inicial en el POST; `remission_amount` (sección 12 del front) y `custom_fields` en `PUT /remissionBalance` / aplanado en el GET. Verificado vs dev (61 checks HTTP). → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [x] ~~**[back] `PUT /remission` y `PUT /remissionControlTable` reescribían `contract_id`**~~ — hecho (2026-09-11, destapado al cotejar docs): el `0` del form reventaba la FK (1452, `control-table-contract-id-fk.md` del front, 2026-08-26) y un `null` sacaba la remisión de su control de saldos; ahora se conserva el de la fila salvo valor `> 0`, los POST guardan `NULL`, `contract_id` vigilado en `history`. → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [ ] **[back] DDL `control_saldos.sql` en test y prod** (usuario; decidir si con el bloque de FKs, como en dev). → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [ ] **[front] Enganchar la pantalla de alta** (`confirmarCreacion` → `POST /balanceControl`), leer formatos/columnas/campos de cabecera de `GET /balanceControl/catalogs` en vez del catálogo hardcodeado, cruzar filas ↔ control por `contract_id`, renombrar `campos_mutables` → `custom_fields` (`key`/`label`/`value_type`/`comment`, tipos `text|number|date|boolean`) y capturar celdas vía `PUT /remissionBalance` (`custom_fields`). → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [ ] **[back] CRUD de formatos ISO para SGI** (`iso_formats`: código, revisión, vigencia, `config`, baja suave): el catálogo ya está en BD, faltan endpoints/pantalla de SGI. → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [ ] **[back] Migrar `iso_form` de `PDFGenerator` a `iso_formats`** y retirar `files/settings.json["formats"]` (ids 1..8 ya idénticos). → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [ ] **[back] Endpoint de inyección/ajuste de saldo** (`POST /balanceControl/movement`, bloqueo optimista sobre `contracted_amount`, usuario del token) — **espera la maqueta F2 del front** (montos negativos, adjunto, permisos). El PUT de cabecera ya rechaza el monto. → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [ ] **[front] Limpieza tras el barrido de coherencia**: retirar la pantalla vieja `administracion/control-saldos/ControlSaldos.tsx` (`/dashboard/administracion/control-saldos`, llama a `/logs` inexistente y edita campos legacy de `contracts.metadata`); resumen del contrato con `contracted_amount`/`start_date`/`end_date` del control (hoy Σ partidas + catálogo); conciliar `CONTRACT_CONFIG` de operaciones (campos extra por contrato) con `config.columns` de los formatos. → [`control_saldos_cabecera.md`](control_saldos_cabecera.md)
- [ ] **[front] F1 discrepancia `total_sin_iva` vs `total_sin_iva_admi`** y **F2 maqueta del historial de inyecciones** (sección 11 del doc del front; sin dependencia del back).

## SGI (vouchers)

- [ ] **[back] Variante combinada `?full=1` del PDF del checklist vehicular** (checklist + anexos + evidencia fotográfica, como remisiones). → [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md)
- [ ] **[back] Doble-codificación de `accessories`** en el alta del voucher vehicular (`json.dumps` en midleware y otro en el controller); el lector ya lo tolera, falta corregir el alta y normalizar datos. → [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md)

## CDA (Control de Activos — vehículos)

*Contexto: backend completo del FO-CDA-02 R3 ✅ verificado contra BD dev — [`control_vehiculos_cda.md`](control_vehiculos_cda.md).*

- [ ] **[back+front] Captura de archivo de foto del vehículo** en su expediente de CDA (pedido al acordar el PDF del checklist: las siluetas del FO-CDA-03 son genéricas; la idea es adjuntar fotos reales). → [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md)

- [ ] **[front] Pantallas del módulo**: las 6 vistas (`/view/*`) + CRUD de vehículos/pólizas/servicios/llantas/multas/compras. → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)
- [x] ~~**[back] Import inicial desde el Excel real**~~ — hecho en dev (2026-08-05) con `scripts_db_handle/import_vehiculos_excel.py` (idempotente, `--dry`); 16 vehículos + 16 pólizas. Falta correrlo en prod cuando el módulo salga. → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)
- [ ] **[back] Recordatorios programados** (vencimiento de póliza / mantenimiento próximo / refrendo) — hoy solo se notifica alta/baja de vehículo. → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)
- [ ] **[back] Otros activos** bajo el namespace `/cda` (el siguiente tipo de activo que defina el negocio). → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)

## PDFs (transversal)

*Contexto: tipografía Helvetica en todos los PDFs + tabla de items de la Remisión en cuadrícula ✅ — [`pdf_tipografia_helvetica_y_cuadricula_remision.md`](pdf_tipografia_helvetica_y_cuadricula_remision.md).*

- [ ] **[back] Migrar los PDFs legacy de texto suelto a cuadrícula** (PO, vale EPP/herramienta, cotización, devolución de materiales) — hoy solo cambiaron de fuente. → [`pdf_tipografia_helvetica_y_cuadricula_remision.md`](pdf_tipografia_helvetica_y_cuadricula_remision.md)

## Compras / PO

- [ ] **[back] Conciliación por cantidades** producto a producto (2ª iteración del match OC ↔ movimientos de entrada). → [`po_movements_inbound_match.md`](po_movements_inbound_match.md)

## Contratos / Presales

- [ ] **[back] El `PUT` de items no devuelve los `qa_item_id` creados** — el front hoy debe re-`GET` tras guardar; mejora: devolverlos en la respuesta. → [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md)
- [ ] **[back] `comment` es campo fantasma** en items de contrato/cotización: los forms y `api.model` lo aceptan pero no se guarda. Decidir: persistirlo o quitarlo del contrato. → [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md)
