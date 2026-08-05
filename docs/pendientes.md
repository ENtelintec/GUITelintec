# Pendientes — backend y front (todas las áreas)

> Tracker general: solo listado con estado y link al doc que tiene la documentación completa. Cada ítem marca **[back]** / **[front]** (o ambos). Actualizado: 2026-08-05.

## RH / Encuestas

*Contexto: motor config-driven + Norma 035 ✅ ([`encuestas_refactor.md`](encuestas_refactor.md)) y eva 360 ✅ verificado contra BD dev ([`eva360_evaluation.md`](eva360_evaluation.md)). Plan del mes en [`plan_rh_mes.md`](plan_rh_mes.md).*

**Bloqueado (dependencia externa):**

- [ ] **[back] Clima laboral (tipo 3)** — esperando el documento de rúbrica (en revisión con RH). Al llegar: `files/rubrics/3.json` + validación; el motor ya lo soporta. → [`encuestas_refactor.md`](encuestas_refactor.md)

**Backend:**

- [ ] **[back] Encuesta de salida (tipo 0)** — rúbrica cualitativa (`mode:"qualitative"`, captura + reporte sin score; chica). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back] Seed de `HOST_DB_TEST` + token `is_tester`** para el tercero (S0 del plan) + crear la hoja de comprobación. → [`plan_rh_mes.md`](plan_rh_mes.md)
- [ ] **[back] Consolidar namespaces** de encuestas (`misc` + `rrhh` en uno). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back+front] Normalizar el shape de respuestas** de captura (eliminaría el adapter `flatten_responses`; coordinar con la UI de captura). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back] Rediseño del PDF de Norma 035** para leer `evaluation` directo (quita el shim `_legacy_shape_from_evaluation`; skill `pdf-design`). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back] PDF del agregado eva 360** (radar/tabla comparativa del proceso). → [`eva360_evaluation.md`](eva360_evaluation.md)
- [ ] **[back] Borrar código muerto deprecado** (`calculate_results_quizzes` / `recommendations_results_quizzes`, sin callers). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[back] Bugs pre-existentes de RRHH** (triar según lo que destape la comprobación): `PUT /employee/vacation` reusa el form de insert (`KeyError` latente en `prima`); `create_mail_payroll` sigue en SharePoint aunque nómina migró a S3 (→ [`payroll_s3_upload.md`](payroll_s3_upload.md)); CSVs de medical/vacations con rutas relativas hardcodeadas. → [`plan_rh_mes.md`](plan_rh_mes.md) (Riesgos)

**Front:**

- [ ] **[front] Comprobación de los ~38 endpoints** (32 RRHH + encuestas en `misc`) contra `HOST_DB_TEST`; entregable = hoja compartida. → [`plan_rh_mes.md`](plan_rh_mes.md)
- [ ] **[front] UI de asignación** de encuestas (refactor menor sobre el CRUD existente). → [`encuestas_refactor.md`](encuestas_refactor.md)
- [ ] **[front] UI de captura de respuestas** — Norma 035 (shape por secciones) y eva 360 (per-question `{"4":{"answer":idx}}`; **conservar `metadata` intacta al re-mandar el `body` en el PUT** — trae el linking). → [`encuestas_refactor.md`](encuestas_refactor.md) · [`eva360_evaluation.md`](eva360_evaluation.md)
- [ ] **[front] UI de resultados** — componente recursivo sobre `breakdown` (`GET /quizz/<id>/evaluation`; ramificar por `data` null; `level`/`actions` opcionales por nodo). → [`encuestas_refactor.md`](encuestas_refactor.md)
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

## CDA (Control de Activos — vehículos)

*Contexto: backend completo del FO-CDA-02 R3 ✅ verificado contra BD dev — [`control_vehiculos_cda.md`](control_vehiculos_cda.md).*

- [ ] **[front] Pantallas del módulo**: las 6 vistas (`/view/*`) + CRUD de vehículos/pólizas/servicios/llantas/multas/compras. → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)
- [x] ~~**[back] Import inicial desde el Excel real**~~ — hecho en dev (2026-08-05) con `scripts_db_handle/import_vehiculos_excel.py` (idempotente, `--dry`); 16 vehículos + 16 pólizas. Falta correrlo en prod cuando el módulo salga. → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)
- [ ] **[back] Recordatorios programados** (vencimiento de póliza / mantenimiento próximo / refrendo) — hoy solo se notifica alta/baja de vehículo. → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)
- [ ] **[back] Otros activos** bajo el namespace `/cda` (el siguiente tipo de activo que defina el negocio). → [`control_vehiculos_cda.md`](control_vehiculos_cda.md)

## Compras / PO

- [ ] **[back] Conciliación por cantidades** producto a producto (2ª iteración del match OC ↔ movimientos de entrada). → [`po_movements_inbound_match.md`](po_movements_inbound_match.md)

## Contratos / Presales

- [ ] **[back] El `PUT` de items no devuelve los `qa_item_id` creados** — el front hoy debe re-`GET` tras guardar; mejora: devolverlos en la respuesta. → [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md)
- [ ] **[back] `comment` es campo fantasma** en items de contrato/cotización: los forms y `api.model` lo aceptan pero no se guarda. Decidir: persistirlo o quitarlo del contrato. → [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md)
