# docs/ — índice

Notas de diseño por cambio del API de Telintec (una `.md` por cambio, en español). Este archivo es **solo el mapa**: una línea por doc, agrupadas por área de negocio y en **orden cronológico ascendente** dentro de cada sección (los docs se encadenan: "extiende…", "cierra el pendiente de…" — leídos de arriba a abajo cuentan la historia del módulo).

- **Pendientes abiertos de todas las áreas** → [`pendientes.md`](pendientes.md) (fuente de verdad; la marca `⏳` de este índice es solo un puntero).
- **Planes con calendario / por fases** → [`planes/`](planes/): [`plan_mes_2.md`](planes/plan_mes_2.md) (vivo), [`almacen_multisede_plan.md`](planes/almacen_multisede_plan.md) (vivo). Cerrados → [`planes/archivo/`](planes/archivo/): [`plan_rh_mes.md`](planes/archivo/plan_rh_mes.md) (mes 1 RH, cerrado 2026-09-07).
- **Reglas para escribir un doc nuevo** (bloque "Contrato mínimo para el front", formato de la línea de este índice, ciclo de vida) → [`../CLAUDE.md`](../CLAUDE.md), sección *Change docs*. Doc nuevo = línea nueva **al final** de su sección.

Formato de cada línea: `doc — endpoint principal: qué hace · fecha · ⏳ pendiente abierto (si lo hay)`. Un doc que cruza áreas vive donde está su endpoint principal y aparece en el `Ver también` de la otra.

## Administración — Contratos y cotizaciones

- [`contract_crud_response_envelope.md`](contract_crud_response_envelope.md) — `POST·PUT·DELETE /admin/presales/contract` y `/quotation`: CRUD alineado al envelope fijo `{data, msg, error}`; incluye la receta reutilizable y la tabla viva de endpoints ya migrados (todas las áreas). · 2026-06-22
- [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md) — `PUT /admin/presales/contract`: items de contrato/cotización con llave `qa_item_id` (corte duro en request y response) y upsert real: crear, actualizar o borrar con guard de pertenencia. · 2026-07-29 · ⏳ el PUT no devuelve los ids creados
- [`contract_items_file_import_sections.md`](contract_items_file_import_sections.md) — `POST /admin/presales/contract/items/file`: import de partidas desde Excel con parser multi-plantilla, errores detallados y secciones (`section_index`); enlace SM ↔ ítem por `(contract_id, section_index, partida)`. · 2026-07-30
- [`quotation_activity_upsert_null_fix.md`](quotation_activity_upsert_null_fix.md) — `PUT /admin/collections/activity/quotation`: actividad de cotización con upsert real de items por `qa_item_id`, QA sin items editable/borrable, `PUT /activity/ChangeStatus` funcional y 404 en id inexistente. · 2026-08-15 · ⏳ front debe mandar `qa_item_id`/`item_contract_id`
- [`common_contracts_catalog.md`](common_contracts_catalog.md) — `GET /common/contracts`: catálogo de contratos de uso general (permiso `Common`) para selectores: id, número, abreviaturas, nombre, planta/área/ubicación y cliente; sin saldos. · 2026-09-23
- [`contracts_products_sort_memory_fix.md`](contracts_products_sort_memory_fix.md) — `GET /admin/presales/contracts/products`: contratos grandes ya no dan 1038 "Out of sort memory" (orden en Python, no sobre el JSON agregado); mismo patrón preventivo en proveedores. · 2026-09-24

Ver también: [`quotation_remission_unit_price_split.md`](quotation_remission_unit_price_split.md) · [`remission_items_json_remove_fix.md`](remission_items_json_remove_fix.md) · [`remission_pdf_download.md`](remission_pdf_download.md) (fix de `get_contract` por id) · [`po_folio_generation_from_contract_code.md`](po_folio_generation_from_contract_code.md) · [`control_saldos_cabecera.md`](control_saldos_cabecera.md)

## Administración — Remisiones

- [`quotation_remission_unit_price_split.md`](quotation_remission_unit_price_split.md) — el `unit_price` del ítem compartido cotización/remisión separa sugerido (`extra_info["unit_price_quotation"]`) y real (`unit_price`); la remisión preserva el sugerido y los GET lo exponen plano. · 2026-06-25
- [`remission_history_changes.md`](remission_history_changes.md) — `activity_reports.history` registra un objeto `changes` (metadata e items con `before`/`after`, campos curados) en cada actualización de remisión y de control table. · 2026-06-25
- [`remission_pdf_download.md`](remission_pdf_download.md) — `GET /remission/download/pdf/<int:id_report>?iva_rate=0.16`: PDF formal de la remisión (pág. 1: header Telintec, metadata de contrato/pedido, items con `partida`, totales calculados por el back). · 2026-07-08
- [`remission_combined_pdf.md`](remission_combined_pdf.md) — `GET /remission/download/pdf/<id>?full=1`: PDF combinado (remisión con firmas + anexos + hojas de evidencia fotográfica); `POST /remission/attachment-<id>` acepta `category`/`folio`/`title`. · 2026-07-23 · ⏳ reporte Ternium generado; firma de quien entrega
- [`remission_items_json_remove_fix.md`](remission_items_json_remove_fix.md) — `GET /admin/collections/remission-<id>`: el detalle devuelve todas las partidas (sin items → `[]`) y editar la primera ya no da 500; patrón `IF(COUNT…)` para `JSON_ARRAYAGG` con `LEFT JOIN`. · 2026-07-30
- [`remission_attachment_delete.md`](remission_attachment_delete.md) — `DELETE /admin/collections/remission/attachment-<id_report>`: quita un anexo de `files` y de S3 (best-effort); las firmas no se borran; el `POST` usa llave S3 con id de reporte y re-subir reemplaza. · 2026-08-03 · ⏳ borrado en lote; front manda `category`
- [`control_table_operaciones_y_campos_admin.md`](control_table_operaciones_y_campos_admin.md) — `POST·PUT /remissionControlTable`: permiso `operaciones` (también en `GET /remission-<id>`), campos propios `total_sin_iva_admi` y `remission_sent_date_client`; `DELETE /remission` acepta remisiones sin items. · 2026-08-26 · ⏳ [front] apuntar a las llaves nuevas

Ver también: toda la sección **Control de saldos** (mismos endpoints de remisión) · [`quotation_activity_upsert_null_fix.md`](quotation_activity_upsert_null_fix.md) · [`contract_items_qa_item_id_upsert.md`](contract_items_qa_item_id_upsert.md) · [`pdf_tipografia_helvetica_y_cuadricula_remision.md`](pdf_tipografia_helvetica_y_cuadricula_remision.md) · [`sm_pdf_delivery_signatures.md`](sm_pdf_delivery_signatures.md) (mismo patrón de firmas desde S3) · [`contracts_products_sort_memory_fix.md`](contracts_products_sort_memory_fix.md) (columna `files` que faltaba en test)

## Administración — Control de saldos

- [`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md) — `PUT /admin/collections/remissionBalance`: campos por módulo (Remisiones / Control de Reportes / Control de Saldos) acumulados en `extra_info` de la misma remisión, con merge por módulo y por llaves presentes; un solo GET aplanado. · 2026-07-08
- [`remission_balance_get_filters_campos_nuevos.md`](remission_balance_get_filters_campos_nuevos.md) — `GET /admin/collections/remission-<id>`: query params `include_items=0` (listado ligero) y filtros `date_from`/`date_to`/`month_period`/`general_status`; 4 campos propios nuevos en `PUT /remissionBalance`. · 2026-08-15 · ⏳ pantalla de saldos del front
- [`control_saldos_cabecera.md`](control_saldos_cabecera.md) — `POST /admin/collections/balanceControl`: entidad `balance_controls` (cabecera del control), formatos FO-CXC como catálogo `iso_formats` en BD, columnas dinámicas `custom_fields` y movimientos de saldo inmutables. · 2026-09-11 · ⏳ DDL test/prod, front, CRUD de formatos SGI
- [`control_saldos_sin_contrato.md`](control_saldos_sin_contrato.md) — `PUT /admin/collections/balanceControl/remissions`: controles sin contrato (`client_id` + `title`); la membresía remisión → control pasa a la columna explícita `activity_reports.balance_control_id`, con reglas de adopción y auto-enlace. · 2026-09-14 · ⏳ DDL en test/prod y front
- [`control_saldos_movimientos.md`](control_saldos_movimientos.md) — `POST /admin/collections/balanceControl/movement`: inyección (1) o ajuste (2) de saldo sobre un control activo, saldo nunca negativo, bloqueo optimista (`expected_balance` + `UPDATE` condicional → 409), movimiento inmutable con usuario del token. · 2026-09-17 · ⏳ adjunto por movimiento; front

Ver también: [`iso_formats_crud.md`](iso_formats_crud.md) (administración del catálogo `iso_formats` que consumen los controles)
· [`control_table_operaciones_y_campos_admin.md`](control_table_operaciones_y_campos_admin.md) (permiso `operaciones` en el mismo GET) · [`remission_history_changes.md`](remission_history_changes.md) · [`remission_items_json_remove_fix.md`](remission_items_json_remove_fix.md) · [`gestion_de_compras.md`](gestion_de_compras.md) (precedente de validación floja)

## Administración — Compras / OC

- [`purchase_list_pdf.md`](purchase_list_pdf.md) — PDF de lista de compra (`FilePurchaseList`): ítems de SM con compra aprobada agrupados por proveedor e inventario, con subtotales por nivel y gran total. · 2026-06-01
- [`po_folio_generation_from_contract_code.md`](po_folio_generation_from_contract_code.md) — `GET /admin/collections/purchase/folio/<folio>`: genera los 3 folios de OC (normal, maestro, cotfc) con los últimos 4 dígitos de `contracts.code` y consecutivo max+1 por patrón. · 2026-06-08
- [`po_sm_deliveries_tracking.md`](po_sm_deliveries_tracking.md) — `POST·PUT /admin/collections/order`: al crear o actualizar una OC sincroniza `folio`, `folio_supplier` y entrega estimada hacia los `deliveries` de los items de SM vinculados; no fatal. · 2026-06-25
- [`po_movements_inbound_match.md`](po_movements_inbound_match.md) — `GET /admin/collections/purchase/movements/match`: concilia cada OC con sus entradas de almacén (por `reference` vs folio, exacto o parcial) y sus SMs relacionadas. · 2026-07-10 · ⏳ conciliación por cantidades por producto
- [`gestion_de_compras.md`](gestion_de_compras.md) — `GET·POST·PUT·DELETE /admin/collections/purchaseManagement`: CRUD de la bitácora FO-COM-01 R3 con FK anulables, texto de respaldo en `extra_info`, catálogos, PUT parcial y cancelación suave. · 2026-07-24

Ver también: [`sm_response_envelope.md`](sm_response_envelope.md) · [`almacen_multisede_f1.md`](almacen_multisede_f1.md) (candado `id_warehouse IS NULL` en el kardex que lee el match) · [`control_vehiculos_cda.md`](control_vehiculos_cda.md) (`vehicle_purchases.po_id`)

## SM (solicitudes de material)

- [`sm_items_extra_info_url_fix.md`](sm_items_extra_info_url_fix.md) — al despachar una SM se conservan `url` e `is_tool` del `extra_info` de cada ítem (`update_items_sm` cae al valor guardado cuando falta la llave). · 2026-06-03
- [`sm_response_envelope.md`](sm_response_envelope.md) — `/sm/*`: los 24 endpoints alineados al envelope `{data, msg, error}`; `msg` en español con ID y `data` `{"id_*": N}` en escrituras. · 2026-06-24 · ⏳ bug KPI `critical_date`
- [`sm_attachment_delivery_title.md`](sm_attachment_delivery_title.md) — `POST /sm/attachment-<id_sm>`: sube la firma de una entrega a S3 y guarda `timestamp` y `title` ("Entrega N") en cada objeto de `extra_info["files"]`. · 2026-07-10
- [`sm_download_not_found_and_parsing.md`](sm_download_not_found_and_parsing.md) — `GET /sm/download/pdf|excel/<sm_id>`: SM inexistente responde 404 con envelope; parseo defensivo de NULLs; columna "C. Suministrado" y contador de items corregidos. · 2026-07-10
- [`sm_pdf_grid_redesign.md`](sm_pdf_grid_redesign.md) — `GET /sm/download/pdf/<sm_id>`: PDF de SM en cuadrícula celeste (metadata e items con wrap), multipágina con encabezados repetidos y tabla de entregas/firmas por attachment; origen de la skill `pdf-design`. · 2026-07-10
- [`sm_pdf_delivery_signatures.md`](sm_pdf_delivery_signatures.md) — `GET /sm/download/pdf/<sm_id>`: incrusta la firma de quien recibe (imagen de S3 redimensionada) en la tabla de entregas y pre-llena fecha y título; paginación por fila, no fatal. · 2026-07-22 · ⏳ firma de quien entrega
- [`sm_pdf_item_status_colors.md`](sm_pdf_item_status_colors.md) — `GET /sm/download/pdf/<sm_id>`: semáforo de surtido en los items (verde fila completa, amarillo/rojo en `No.`, sin color si `quantity <= 0`); estatus "Semidespachado" corregido. · 2026-07-23

Ver también: [`po_sm_deliveries_tracking.md`](po_sm_deliveries_tracking.md) (la OC escribe los `deliveries` de la SM) · [`po_movements_inbound_match.md`](po_movements_inbound_match.md) · [`purchase_list_pdf.md`](purchase_list_pdf.md) · [`contract_items_file_import_sections.md`](contract_items_file_import_sections.md) (Fase 3: enlace SM ↔ partida por sección) · [`pdf_tipografia_helvetica_y_cuadricula_remision.md`](pdf_tipografia_helvetica_y_cuadricula_remision.md) (los PDFs de SM ya son Helvetica)

## Almacén

- [`almacen_response_envelope.md`](almacen_response_envelope.md) — `/almacen/*`: endpoints de Almacén alineados al envelope `{data, msg, error}`; GET con `data` intacto, escrituras `{"id_*": N}`, errores de masivos a `error`. · 2026-06-24
- [`almacen_multisede_f1.md`](almacen_multisede_f1.md) — `GET /almacen/warehouses` · `GET /almacen/inventory/consolidated`: multisede F0+F1 — DDL y permiso `Sucursal-2`, candado `id_warehouse IS NULL` en el kardex del principal, catálogo de sedes e inventario consolidado. · 2026-09-08 · ⏳ datos reales de la sede 2; pantallas front
- [`almacen_multisede_f2.md`](almacen_multisede_f2.md) — `POST·PUT·DELETE /sucursal/movement`: multisede F2 — namespace `sucursal` con inventario de sede, stock del principal en lectura, kardex y movimientos con stock por sede nunca negativo. · 2026-09-08 · ⏳ pantallas front de la sede
- [`almacen_multisede_f3.md`](almacen_multisede_f3.md) — `POST /almacen/transfer` · `PUT /sucursal/transfer/receive`: multisede F3 — traslados principal → sede en dos pasos con en-tránsito, folio `TRS-####`, cancelación con reversa y recepción única con diferencias. · 2026-09-10 · ⏳ front de recepción; procedimiento de discrepancias

Ver también: [`planes/almacen_multisede_plan.md`](planes/almacen_multisede_plan.md) (plan de la iniciativa) · [`po_movements_inbound_match.md`](po_movements_inbound_match.md) (OC ↔ entradas de almacén) · [`purchase_list_pdf.md`](purchase_list_pdf.md) · [`contracts_products_sort_memory_fix.md`](contracts_products_sort_memory_fix.md) (listado de proveedores sin sort sobre el JSON)

## RRHH — Encuestas

- [`encuestas_refactor.md`](encuestas_refactor.md) — `GET /rrhh/quizz/<id_task>/evaluation`: motor de evaluación config-driven (`quizz_eval_engine.py`) con rúbrica en datos y salida uniforme `total`/`breakdown` recursiva (contrato de la UI de resultados); Norma 035 migrada. · 2026-07-28 · ⏳ rediseño PDF Norma 035; normalizar respuestas
- [`eva360_evaluation.md`](eva360_evaluation.md) — `POST /rrhh/eva360`: Eva 360 como proceso multi-evaluador (task de control + 2-4 tasks por rol ligadas por `evaluation_id`), con detalle, resultado agregado 0-100 por perspectiva/competencia y cierre. · 2026-08-05 · ⏳ PDF del agregado
- [`clima_laboral_rubrica.md`](clima_laboral_rubrica.md) — `GET /rrhh/quizzes/summary/<type_q>`: clima laboral (tipo 3) en el motor con % de percepción positiva (neutral excluido, ítem 34 invertido, 9 categorías) y tabla organizacional. · 2026-08-06 · ⏳ PDF individual y export de la tabla
- [`quizz_models_crud.md`](quizz_models_crud.md) — `/rrhh/quizz/models`: CRUD de modelos de encuesta (template + rúbrica) en `sql_telintec_mod_rrhh.quizz_models`, ciclo de vida borrador/activa/archivada, validación con dry-run y PDF genérico de resumen. · 2026-08-06 · ⏳ PDFs dedicados y editor de rúbricas
- [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md) — `/rrhh/task/quizz`: los 3 recursos de encuestas de `misc` movidos a `rrhh` en corte duro; incluye tabla de traducción de rutas. · 2026-08-07
- [`encuesta_salida_cualitativa.md`](encuesta_salida_cualitativa.md) — `GET /rrhh/quizz/<id_task>/evaluation`: encuesta de salida (tipo 0) con rúbrica `mode:"qualitative"` y respuestas resueltas a texto (`answer`, `answer_raw`, `details`). · 2026-09-08 · ⏳ DML de la rúbrica tipo 0 en test/prod
- [`quizz_models_versionado.md`](quizz_models_versionado.md) — `POST /rrhh/quizz/models/<id>/clone`: versionado de modelos: candado del template por tasks, clonar, publicar archiva la versión anterior y migración de encuestas pendientes (`PUT /migrate-tasks`). · 2026-09-08 · ⏳ constructor visual del front

Ver también: [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md) (`quizz_tasks`, vistas puente) · [`dashboard_rrhh.md`](dashboard_rrhh.md) (tile de encuestas) · [`planes/plan_mes_2.md`](planes/plan_mes_2.md)

## RRHH — Nómina, médicos, dashboard, esquema y cargos

- [`payroll_s3_upload.md`](payroll_s3_upload.md) — `POST /rrhh/payroll/files/update`: sube archivos de nómina (pdf/xml, uno por request) al bucket S3 de RH e indexa el key en `payroll.files_data`. El contrato vigente está en `nomina_gestion_archivos_y_notificacion.md`. · 2026-05-29
- [`heads_crud_fields_sync.md`](heads_crud_fields_sync.md) — `POST·PUT·DELETE /admin/db/head`: CRUD de cargos alineado con su `fetch`: `name` editable, `employee` vacante como `NULL` y `extra_info.area` de extremo a extremo. Template de referencia para docs nuevos. · 2026-06-03
- [`migracion_esquemas_rrhh.md`](migracion_esquemas_rrhh.md) — plan por fases para mover las tablas de RRHH a `sql_telintec_mod_rrhh` con vistas puente: Fase 1 (`tasks_gui`→`quizz_tasks`) y Fase 2 (5 privadas + `aptitude`) ejecutadas; sin cambio de API. · 2026-08-07
- [`rrhh_download_csv_unpack_fix.md`](rrhh_download_csv_unpack_fix.md) — `GET /rrhh/download/employees/<status>` (+ `/medical`, `/vacations`): descargas CSV alineadas con sus SELECT compartidos (CSV byte-idéntico), guards de NULL y error como envelope 400. · 2026-08-07 · ⏳ CSV sin quoting, apellido, rutas relativas
- [`nomina_gestion_archivos_y_notificacion.md`](nomina_gestion_archivos_y_notificacion.md) — `DELETE /rrhh/payroll/files` (+ `POST /payroll/notify`, `POST /payroll/files/extract`): eliminar/reemplazar archivos de nómina en S3, notificación in-app y sugerencia de empleado/periodo desde el XML del CFDI; `/payroll/mail` deprecado. · 2026-09-08 · ⏳ correo por SES y pantallas front
- [`dashboard_rrhh.md`](dashboard_rrhh.md) — `GET /dashboard/rrhh/summary` (+ `POST /dashboard/rrhh/series`): tiles de RH (plantilla, altas/bajas, exámenes por vencer, vacaciones, encuestas, cumpleaños, calidad de datos) y series por mes o departamento; sin fichajes. · 2026-09-10 · ⏳ pantalla front y limpieza de datos RH
- [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md) — `GET /rrhh/employees/medical/all`: regla única `medical_due` (12/6/3 meses por aptitud, aviso a 30 días) para endpoint, daemon y dashboard; cada registro gana `alert`/`due_date`/`days_left`. · 2026-09-10 · ⏳ front pinta `alert`; migrar llave `alergies`
- [`nomina_correo_ses.md`](nomina_correo_ses.md) — `POST /rrhh/payroll/notify` (`channels: ["email"]`): correo al empleado por AWS SES con el pdf/xml del recibo adjuntos desde S3 (`Functions_Mail.py` genérico); `channels_failed`/`email_to` nuevos; `POST /payroll/mail` retirado. · 2026-09-17 · ⏳ SES production access; front
- [`common_employees_directory.md`](common_employees_directory.md) — `GET /common/employees/<status>`: directorio de empleados de uso general (permiso `Common`) solo con datos no confidenciales (nombre, contacto, departamento, contrato, puesto, líder, usuario). · 2026-09-23

Ver también: [`consolidacion_namespaces_encuestas.md`](consolidacion_namespaces_encuestas.md) y [`quizz_models_crud.md`](quizz_models_crud.md) (mismo tren de deploy que la migración) · [`planes/plan_mes_2.md`](planes/plan_mes_2.md) (Anexo A nómina, Anexo D dashboard)

## SGI / CDA

- [`control_vehiculos_cda.md`](control_vehiculos_cda.md) — `/cda/*`: namespace nuevo (Control De Activos) para vehículos FO-CDA-02: CRUD de vehículos, pólizas, servicios, llantas, multas y compras, más 6 vistas `GET /view/*` con campos calculados. · 2026-08-05 · ⏳ pantallas del front y recordatorios
- [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md) — `GET /sgi/voucher/vehicle/download/pdf/<id_voucher>`: PDF del Check List Vehicular FO-CDA-03 R3 con colores oficiales, 36 accesorios fijos, siluetas por tipo y firmas desde S3. · 2026-08-15 · ⏳ variante `?full=1`; doble-encode de `accessories`
- [`cda_alertas_y_fotos.md`](cda_alertas_y_fotos.md) — `GET /cda/alerts` · `GET /cda/notifications` · `POST /cda/vehicle/photo-<id>`: alertas de vehículos calculadas on-read (pólizas, pagos, mantenimiento, refrendo, llantas), barrido diario a notificación de sistema y fotos del expediente en S3. · 2026-09-17 · ⏳ tile/galería del front
- [`iso_formats_crud.md`](iso_formats_crud.md) — `GET·POST·PUT·DELETE /sgi/format(s)`: CRUD del catálogo de formatos ISO (`iso_formats`: código, revisión en la misma fila, vigencia, `config` validado, baja suave) y los PDFs leen `Codigo:`/`I. Vigencia:` de la BD (`settings.json["formats"]` retirado). · 2026-09-17 · ⏳ pantalla SGI; versionar `config`
- [`checklist_vehicular_contrato.md`](checklist_vehicular_contrato.md) — `POST·PUT /sgi/voucher/vehicle`: `contract` editable en el `PUT` y opcional en el checklist vehicular (`null`/`0` = sin contrato; `vouchers_general.contract` NULL-able). · 2026-09-23 · ⏳ selector del front

Ver también: [`common_contracts_catalog.md`](common_contracts_catalog.md) (lista para el selector de contrato del checklist) · [`control_saldos_cabecera.md`](control_saldos_cabecera.md) (catálogo `iso_formats` de SGI) · [`remission_combined_pdf.md`](remission_combined_pdf.md) (la fusión que reusaría `?full=1`) · [`contracts_products_sort_memory_fix.md`](contracts_products_sort_memory_fix.md) (`status` de `voucher_tools`/`voucher_safety` que le faltaba a dev)

## Transversal

- [`pdf_tipografia_helvetica_y_cuadricula_remision.md`](pdf_tipografia_helvetica_y_cuadricula_remision.md) — todos los PDFs pasan de Courier a Helvetica (wrapping por `stringWidth` con `wrap_text_width`) y la tabla de items de la Remisión pasa a cuadrícula completa; sin cambio de contrato. · 2026-08-15 · ⏳ migrar PDFs legacy a cuadrícula

Ver también: [`iso_formats_crud.md`](iso_formats_crud.md) (el encabezado `Codigo`/`Vigencia` de todos los PDFs sale de `iso_formats`) · serie de envelopes `{data, msg, error}` → [`contract_crud_response_envelope.md`](contract_crud_response_envelope.md) (receta + tabla viva), [`sm_response_envelope.md`](sm_response_envelope.md), [`almacen_response_envelope.md`](almacen_response_envelope.md) · PDFs con el estilo de la casa → [`sm_pdf_grid_redesign.md`](sm_pdf_grid_redesign.md), [`remission_pdf_download.md`](remission_pdf_download.md), [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md), [`quizz_models_crud.md`](quizz_models_crud.md) · regla del sort buffer (1038 "Out of sort memory") para cualquier `ORDER BY` que lea JSON, con el barrido de todo el SQL y el arreglo de notificaciones → [`contracts_products_sort_memory_fix.md`](contracts_products_sort_memory_fix.md)
