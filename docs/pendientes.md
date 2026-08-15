# Pendientes — backend y front (todas las áreas)

> Tracker general: solo listado con estado y link al doc que tiene la documentación completa. Cada ítem marca **[back]** / **[front]** (o ambos). Actualizado: 2026-08-15.

## RH / Encuestas

*Contexto: motor config-driven + Norma 035 ✅ ([`encuestas_refactor.md`](encuestas_refactor.md)), eva 360 ✅ verificado contra BD dev ([`eva360_evaluation.md`](eva360_evaluation.md)), clima laboral ✅ (rúbrica % positivo + agregado organizacional, [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md)) y CRUD de modelos de encuesta ✅ (template+rúbrica en BD, esquema nuevo `sql_telintec_mod_rrhh`, [`quizz_models_crud.md`](quizz_models_crud.md)). Plan del mes en [`plan_rh_mes.md`](plan_rh_mes.md).*

- [x] ~~**[back] Clima laboral (tipo 3)**~~ — hecho (2026-08-05): RH entregó criterio + cuestionario nuevo (45 preguntas); `files/rubrics/3.json`, motor con % positivo/neutral excluido/ítem 34 invertido, y endpoint nuevo `GET /rrhh/quizzes/summary/<type_q>` (tabla organizacional). Incluye fix del template JSON inválido que rompía `GET /misc/download/quizz/3`. → [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md)
- [x] ~~**[back] CRUD de modelos de encuesta**~~ — hecho (2026-08-05): crear/editar/publicar/archivar/borrar encuestas por API (`/rrhh/quizz/models`), tabla `quizz_models` en esquema nuevo `sql_telintec_mod_rrhh` (seed 0–4; Norma 035 `protected`), ciclo de vida con candado de template, `validate_rubric`+dry-run, PDF genérico de resumen para tipos sin generador. Verificado contra BD dev. → [`quizz_models_crud.md`](quizz_models_crud.md)
- [x] ~~**[back] Bugs S1 de la comprobación: descargas CSV (employees/medical/vacations)**~~ — hecho (2026-08-07): los 3 GET de descarga tronaban con 500 por desempaquetados desalineados con sus SELECT compartidos; unpacks alineados (CSV byte-idéntico) + guards de NULL + tupla de error → envelope 400. Verificado contra BD dev. → [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md)
- [x] ~~**[front] Comprobación de los ~38 endpoints**~~ — hecho (2026-08-07): hoja compartida llena y cerrada; destapó 3 bugs (descargas CSV → [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md)) y la re-prueba tras el fix salió sin más errores. **Checkpoint S1 del tercero cumplido.** → [`plan_rh_mes.md`](plan_rh_mes.md)
- [x] ~~**[back] Seed de `HOST_DB_TEST` + token `is_tester` + hoja de comprobación**~~ — cerrado con la comprobación (2026-08-07): la S1 corrió completa contra la BD de test con el token del tercero y la hoja quedó llena. → [`plan_rh_mes.md`](plan_rh_mes.md)

**Backend:**

- [ ] **[back] Encuesta de salida (tipo 0)** — rúbrica cualitativa (`mode:"qualitative"`, captura + reporte sin score; chica). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [x] ~~**[back] Consolidar namespaces** de encuestas (`misc` + `rrhh` en uno)~~ — hecho (2026-08-07) en el lote S2 con la migración Fase 1: los 3 recursos de `misc` (`/task/quizz`, `/task/<emp_id>`, `/download/quizz/<type_q>`) ahora en `rrhh`, **corte duro** (viejas → 404), shapes/permisos idénticos; smoke completo verde vs dev. **El front debe cambiar el prefijo `misc`→`rrhh` en esas 3 rutas.** → [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md)
- [x] ~~**[back] Migración de esquema — Fase 1 (encuestas)**~~ — hecho (2026-08-07): DDL corrido en las 3 BDs (`tasks_gui` → `sql_telintec_mod_rrhh.quizz_tasks` + vista puente, conteos verificados), 7 literales + docstrings actualizados. → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md)
- [ ] **[back] DROP de las 7 vistas puente** en las 3 BDs (`tasks_gui`, Paso 3 de `scripts_db_handle/migracion_quizz_tasks.sql`, + las 6 de Fase 2, bloque diferido de `migracion_fase2_rrhh.sql`) — **solo cuando prod ya corra el código del tren S2+Fase2** (un solo deploy, decidido 2026-08-07); mientras, las vistas mantienen vivo el código viejo. → [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md)
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

- [ ] **[front] UI de asignación** de encuestas (refactor menor sobre el CRUD existente). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[front] UI de captura de respuestas** — Norma 035 (shape por secciones) y eva 360 (per-question `{"4":{"answer":idx}}`; **conservar `metadata` intacta al re-mandar el `body` en el PUT** — trae el linking). → [`encuestas_refactor.md`](encuestas_refactor.md) · [`eva360_evaluation.md`](eva360_evaluation.md)
- [ ] **[front] UI de resultados** — componente recursivo sobre `breakdown` (`GET /quizz/<id>/evaluation`; ramificar por `data` null; `level`/`actions` opcionales por nodo; en clima `score` puede ser `null` = sin datos). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[front] Tabla organizacional de clima** — pintar `GET /quizzes/summary/3` (9 categorías + total, color por `level.key`, filtro anual con `date_from`/`date_to`). → [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md)
- [ ] **[front] Pantalla de administración de modelos de encuesta** — listado `?all=1`, crear/editar (template y rúbrica JSON), publicar/archivar, mostrar `warnings` y los 400 de candado; el picker de "crear encuesta" pasa a `GET /rrhh/quizz/models` (adiós tipos hardcodeados). → [`quizz_models_crud.md`](quizz_models_crud.md)
- [ ] **[front] UI de eva 360** — crear proceso, seguimiento (`answered` por rol), radar/comparativa (**rol ausente en `by_perspective`/`by_role` = pendiente**, cruzar contra `expected_roles`), botón completar. → [`eva360_evaluation.md`](eva360_evaluation.md)

## SM (solicitudes de material)

- [ ] **[back] Bug KPI** en `get_all_sm`: `(critical_date - critical_date)` siempre da 0. **Deliberadamente no tocar por ahora** — a futuro KPIs configurables por el usuario (agregar/quitar y definir fórmula). → [`sm_response_envelope.md`](sm_response_envelope.md)
- [ ] **[front+back] Firma de "quien entrega"** en el PDF de SM — hoy siempre en blanco; requiere que el front la capture primero y el back la incruste (mismo mecanismo que la de quien recibe). → [`sm_pdf_delivery_signatures.md`](sm_pdf_delivery_signatures.md)

## Remisiones (admin/collections)

- [ ] **[back] Bug latente `[null]`**: `get_quotation_activity_by_id` tiene el mismo `JSON_ARRAYAGG` sin proteger que ya se arregló en remisiones → `TypeError`/500 en `update_quotation_activity_from_api` con cotización de actividad sin items. → [`remission_items_json_remove_fix.md`](remission_items_json_remove_fix.md)
- [ ] **[back] PDF combinado**: pre-llenar el `title` del anexo en el documento (se guarda pero no se imprime). → [`remission_combined_pdf.md`](remission_combined_pdf.md)
- [ ] **[back] Reporte de materiales formato Ternium generado** (hoy solo se concatena el escaneo subido como `anexo`; falta modelo de datos — el doc referencia `tareas_admin_windows.md`, que no existe en `Docs/`). → [`remission_combined_pdf.md`](remission_combined_pdf.md)
- [ ] **[front+back] Firma de "quien entrega"** en la remisión (hoy `firma-realizado`/`firma-recibido` cubren autorización 1 y 2). → [`remission_combined_pdf.md`](remission_combined_pdf.md)
- [ ] **[front] Mandar `category` en el `POST` de anexos** — sin ella, una firma subida sin categoría explícita queda protegida solo por heurística de nombre. → [`remission_attachment_delete.md`](remission_attachment_delete.md)
- [ ] **[front+back] Borrado de anexos en lote** — solo si el front agrega selección múltiple. → [`remission_attachment_delete.md`](remission_attachment_delete.md)

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
