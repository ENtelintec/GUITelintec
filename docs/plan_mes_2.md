# Plan de trabajo — Mes 2: RH (nómina, constructor de encuestas, dashboard) + Almacén multisede

> Plan de sprint de 4 semanas (**2026-09-07 → 2026-10-02**). Continúa al [`plan_rh_mes.md`](plan_rh_mes.md), que cerró con las 6 UIs de encuestas entregadas. Cuatro tareas, decididas y ordenadas en la sesión de grill del 2026-09-07. Back y front a **tiempo completo** (~160 h cada uno). Cada pieza de back produce su doc en `docs/` con "Contrato mínimo para el front"; este plan solo fija alcance, orden y contratos **preliminares** (anexos al final).

## Punto de partida

- **Mes 1 cerrado**: motor config-driven, Norma 035, clima, eva 360, CRUD de modelos y las **6 UIs** (asignación, captura, resultados, tabla de clima, admin de modelos con editor JSON, eva 360) integradas.
- **Arrastre del back** (entra en S1, antes que cualquier back nuevo): encuesta de **salida (tipo 0)** cualitativa; y el tren **S2+Fase 2**: si ya corre en prod → `DROP` de las 7 vistas puente (DDL del usuario); si no → el deploy es lo **primero** de S1, porque todo lo de este mes sale por ese mismo tren.
- **Multisede**: nada implementado. La reunión con administración ya ocurrió; **los datos de la sede siguen pendientes** (nombre, encargado, usuarios, fecha del cambio del DELETE).

## Decisiones acordadas

| Tema | Decisión |
|---|---|
| **Equipo** | Back full-time (~160 h). Front (el tercero) pasa a **full-time** (~160 h) tras el veredicto positivo del mes 1 |
| **Prioridad** | 1) Nómina · 2) Constructor de encuestas · 3) Multisede (back desde S1, front en la segunda mitad) · 4) Dashboard RH. Sin fecha dura de negocio detrás de ninguna |
| **Línea que no se cruza** | Nómina + constructor **completos** en front y back; multisede con Fases 0–2 en back y **inventario + movimientos de sede** en front |
| **Nómina — disponibilidad** | v1 = **dentro del sistema**: notificación in-app al empleado + descarga desde su pantalla. Correo (AWS SES o similar) = 2ª etapa. Link de WhatsApp (`wa.me/<tel>?text=…`, lo arma el front con el teléfono del empleado) = última etapa. `POST /payroll/mail` (borrador Outlook vía Graph + SharePoint) queda **deprecado**, el front no lo llama |
| **Nómina — carga** | Ideal: por periodo leyendo el XML del CFDI. **Este mes**: carga por periodo **simulada por el front** (RH asigna archivo→empleado en pantalla y el front itera el endpoint actual, un archivo por request). `POST /payroll/files/extract` (lee el XML y sugiere empleado/periodo) = pieza chica de back **solo si sobra** (S4) |
| **Nómina — reemplazar / eliminar** | `DELETE /payroll/files` con `kind` ∈ `pdf\|xml\|both` (BD primero, S3 best-effort). Reemplazar = el `POST` actual, que pasa a borrar el objeto anterior del mismo `kind` cuando cambia el nombre. Sin protección por "ya notificado". Rastro en log/`history` |
| **Constructor — candado** | Se **relaja a "sin tasks"**: template editable en cualquier status mientras `tasks_total = 0`. Con tasks, editar = **nueva versión** |
| **Constructor — versiones** | `POST /quizz/models/<id>/clone` (template + rúbrica + name con sufijo, nace borrador, `replaces: <id>`). **Publicar la nueva archiva la vieja automáticamente**; la vieja se queda en BD evaluando su historial |
| **Constructor — migrar pendientes** | `PUT /quizz/models/<new>/migrate-tasks` reapunta las tasks **sin contestar** del tipo viejo al nuevo; las contestadas **nunca** se mueven; eva 360 fuera. `PUT /status` con `migrate_pending: true` lo hace al publicar en un paso |
| **Constructor — alcance visual** | El editor visual edita **solo el template** (preguntas, opciones, widget del catálogo actual `1/2/3/5`, subpreguntas, rango `items`). La rúbrica se hereda al clonar y vive en pestaña "Avanzado" con el JSON de hoy + `warnings`. Desde cero sin rúbrica = cualitativa. **Sin widgets nuevos** |
| **Multisede — back** | Fases según [`almacen_multisede_plan.md`](almacen_multisede_plan.md): F0+F1 en S1 (dev con placeholders "Sucursal 2" + permiso `Sucursal-2`), F2 en S2, F3 en S3, F4 solo si sobra. **Prod de multisede fuera del mes** salvo que lleguen los datos de administración |
| **Multisede — front** | Lo principal y más sencillo primero: **inventario y movimientos de sede**; después **recepción de traslados** (+ formulario mínimo de "crear traslado" en el principal para probar punta a punta). Fuera: consolidado, catálogo de sedes, cancelar, exports y dashboard de sede. Misma app, menú por permiso |
| **Dashboard RH** | Lista v1 cerrada (tiles + 2 series). Back: `GET /dashboard/rrhh/summary` + `POST /dashboard/rrhh/series` (`metric` extensible). Sin caché. Front: una pantalla, tiles clicables a la lista filtrada |
| **Contratos antes que código** | El back publica el contrato de cada fase/pieza **al inicio de su semana** (doc con bloque del front); el front arma la pantalla con mocks y conecta cuando el endpoint aterriza |
| **DDL** | Como siempre: scripts en `scripts_db_handle/`, los revisa/ejecuta el usuario; ningún agente corre DDL |

## Objetivo del mes

1. **Nómina operable de punta a punta** desde el front nuevo: carga por periodo (simulada), reemplazar, eliminar, notificar al empleado dentro del sistema.
2. **Constructor de encuestas**: RH edita preguntas, clona/versiona y crea desde cero sin tocar JSON (salvo la rúbrica en pestaña avanzada).
3. **Multisede**: back Fases 0–3 sobre dev/test; front con inventario + movimientos de sede y recepción de traslados.
4. **Dashboard de RH** v1.

**Criterio de éxito (línea que no se cruza):** nómina + constructor integrados y en test · multisede F0–F2 en back con inventario y movimientos de sede en front · arrastre del back cerrado.

## Principio rector

El cuello de botella ya no son horas: son **dependencias**. Tres de las cuatro tareas necesitan back nuevo antes de la primera pantalla, y multisede necesita tres fases. Por eso el back trabaja **contrato primero, código después**, y el orden de sus semanas está fijado para que el front nunca se quede sin trabajo: nómina y constructor tienen contrato en S1 mientras el front hace nómina; multisede tiene contrato de F2 al abrir S2 y de F3 al abrir S3, justo cuando el front termina el constructor.

## Calendario

### Semana 1 — 07–11 sep · Arrastre + contratos ‖ Nómina front

| Back | Front |
|---|---|
| **Arrastre**: salida tipo 0 · `DROP` de las 7 vistas (o deploy del tren si no está en prod) | Pantallas de nómina contra el contrato del Anexo A: carga por periodo simulada (elige año/mes/quincena una vez, asigna archivo→empleado, itera el `POST`), reemplazar, eliminar, notificar |
| **Nómina** (doc + código): `DELETE /payroll/files`, semántica de reemplazo en el `POST`, `POST /payroll/notify`, quitar el guard muerto `update_files_nomina` | Pantalla del empleado: sus recibos (`GET /common/payroll/employee/<id>`) + descarga zip + bandeja de notificaciones |
| **Constructor** (doc + código): candado por `tasks_total`, `POST …/clone`, `PUT …/migrate-tasks`, `migrate_pending` en `PUT /status`, `replaces`/`replaced_by` en el detalle | |
| **Multisede F0**: `scripts_db_handle/almacen_multisede.sql` (3 tablas + `ALTER` + seed placeholder) → revisión del usuario → dev/test · `Sucursal-2` en `permissions_models.json` (grep de colisiones) · **F1**: candado `id_warehouse IS NULL` en las 5 lecturas del kardex + CRUD `warehouses_amc` | |

**Checkpoint vie 11**: contratos de nómina y constructor publicados; DDL F0 corrido en dev; front con la carga por periodo funcionando contra dev. *Si la semana se aprieta, F1 pasa a S2; nómina y constructor no se mueven.*

### Semana 2 — 14–18 sep · Multisede F2 ‖ Nómina integrada + arranca constructor

| Back | Front |
|---|---|
| **Contrato F2 el lunes** (doc del namespace `sucursal`) → código: `rs_Sucursal.py` + `MD_Sucursal.py` + `warehouses_controller.py` + `api_sucursal_models.py` + registro en `app.py` + `log_file_sucursal`; movimientos libres con stock por sede (POST/PUT/DELETE), `/inventory`, `/inventory/main`, `/movements/<type_m>` | **Nómina integrada end-to-end** y en test (checkpoint) |
| Soporte a nómina; bugs de integración | Arranca el **constructor**: listado con versiones (`replaces`), botón clonar, editor visual de template, pestaña "Avanzado" (rúbrica JSON + `warnings`) |

**Checkpoint vie 18**: nómina en test con el tester; F2 en dev; constructor a medio camino.

### Semana 3 — 21–25 sep · Multisede F3 + dashboard back ‖ Constructor integrado + sede

| Back | Front |
|---|---|
| **Contrato F3 el lunes** → traslados: `POST /almacen/transfer`, `PUT /almacen/transfer/cancel`, `GET /almacen/transfers`, `GET /almacen/transfer/<id>`, `GET /sucursal/transfers`, `PUT /sucursal/transfer/receive`, folio `TRS-####`, `history` con quién envía/recibe | **Constructor integrado** con publicar-y-archivar + checkbox de migrar pendientes (checkpoint) |
| **Dashboard RH** (doc + código): `GET /dashboard/rrhh/summary` + `POST /dashboard/rrhh/series` | **Inventario y movimientos de sede** contra F2 (menú por permiso `Sucursal-<id>`) |

**Checkpoint vie 25**: constructor en test; sede con inventario y movimientos en dev; F3 en dev. *Punto de decisión de recorte (ver abajo).*

### Semana 4 — 28 sep–02 oct · Cierre

| Back | Front |
|---|---|
| Cierre de integración (multisede, dashboard) · regresión del tester sobre nómina/encuestas | **Recepción de traslados** + formulario mínimo de "crear traslado" en el principal |
| **Si sobra** (en este orden): `POST /payroll/files/extract` · correo por SES · F4 de multisede | **Dashboard RH** |
| Docs cerrados + [`pendientes.md`](pendientes.md) al día | Pulido |

**Checkpoint vie 02 oct**: veredicto del mes contra "Entregables".

## Degradación con gracia

Lo primero que se cae, en orden: **extract de XML y correo SES** → **dashboard RH** (si se recorta, el back deja el endpoint y el front lo pinta el mes siguiente) → **recepción de traslados** en front (F3 se queda en back con su contrato, "lista para enchufar"). **Nunca se recorta**: nómina, constructor, multisede F0–F2 con inventario y movimientos de sede, ni el arrastre del back. El fix del DELETE del principal (F4) **no entra** este mes: queda explícito para que operación no lo espere.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| **El front se queda sin trabajo en S3** si el back no publica el contrato de F2/F3 a tiempo (polo largo del back) | Contrato el lunes de cada fase, código después; el front arma contra mocks. Si F2 se atrasa, el front adelanta el dashboard (su back es chico y puede subir a S2) |
| **S1 del back cargada** (arrastre + 2 contratos + F0/F1) | Orden fijo: arrastre → nómina → constructor → multisede. F1 es lo único que puede correrse a S2 |
| **Datos de la sede no llegan** de administración | Dev/test con placeholders; prod de multisede declarado fuera del mes desde el día 1 |
| **Candado relajado** permite editar un template con tasks | El guard es por conteo (`tasks_total`, cualquier task, contestada o no), no por status; con tasks → 400 sugiriendo clonar |
| **Migrar pendientes** cambia el cuestionario que ve el empleado a medio camino | Solo tasks con `data_raw` vacío; contestadas nunca; eva 360 excluida; la UI lo ofrece como checkbox explícito al publicar, no por defecto |
| **Notificación in-app no llega** a empleados sin usuario en el sistema | `POST /payroll/notify` reporta `notified: false` con motivo; el front lo muestra por empleado. Es la razón de la 2ª etapa (correo) |
| **Reemplazo/borrado en S3** falla a medias | BD primero, S3 best-effort con `s3_deleted` en la respuesta: nunca queda un `path` muerto en el índice |
| **Dashboard abre un yak** de KPIs | Lista v1 cerrada; KPI nuevo = `metric` nuevo en `series`, sin tocar el front |

> **Seguimiento vivo:** estado por ítem en [`pendientes.md`](pendientes.md) (secciones RH / Encuestas, RH / Nómina, RH / Dashboard, Almacén / Multisede).

## Entregables del mes

- [ ] Arrastre del back cerrado: salida tipo 0 + `DROP` de las 7 vistas (o deploy del tren).
- [ ] **Nómina**: doc con contrato · `DELETE /payroll/files` · reemplazo en el `POST` · `POST /payroll/notify` · guard muerto fuera · front integrado (RH + empleado) y en test.
- [ ] **Constructor**: doc con contrato · candado por tasks · clonar · publicar-archiva · migrar pendientes · front con editor visual de template + pestaña avanzada, integrado y en test.
- [ ] **Multisede**: DDL F0 en dev/test (`almacen_multisede.sql`) · F1 candado + catálogo · F2 namespace `sucursal` · F3 traslados · docs por fase · front con inventario, movimientos y recepción de sede.
- [ ] **Dashboard RH**: doc con contrato · `summary` + `series` · pantalla.
- [ ] Si sobra: `extract` de XML · correo SES · F4.
- [ ] [`pendientes.md`](pendientes.md) actualizado al cierre.

---

## Anexo A — Nómina: API para el front (contrato preliminar)

> El definitivo va en el doc de la pieza. Común a todo: base `/GUI/api/v1`, header `Authorization` con el **JWT crudo** (sin `Bearer`), envelope `{data, msg, error}`; descargas = blob en 200 / envelope JSON en 4xx. Multipart = **un archivo por request**.

**Lo que ya existe (no cambia de contrato):**

| Método y ruta | Permiso | Uso |
|---|---|---|
| `POST /rrhh/payroll/files/update` | `rrhh` | Subir **un** archivo (`file` pdf/xml + form `year`, `month`, `emp_id`, `key`). 201 con `data` = key S3 `payroll/<año>/<mes>/<emp_id>/<archivo>`. La "carga por periodo" del front es iterar esto por archivo. **Nuevo comportamiento**: si el `key`+`kind` ya tenía un objeto con otro nombre, se borra el anterior (reemplazo) |
| `GET /rrhh/payroll/files/list/<emp_id>` | `rrhh` | Índice del empleado: `data: [{id, name, data: files_data}]` con `files_data[año][mes][key][pdf\|xml]` = key S3 |
| `PUT /rrhh/payroll/data/update` | `rrhh` | Edita el índice a mano (`{id, data_dict}`); lo usa poco el front nuevo |
| `GET /rrhh/payroll/update/employees` | `rrhh` | Sincroniza empleados → tabla `payroll` (crea la fila de índice de los que no la tienen). Correr antes de la primera carga del periodo |
| `GET /common/payroll/employee/<emp_id>` | auto-acceso | Lado empleado: sus recibos |
| `POST /common/payroll/employee/file` | auto-acceso | Descarga: body `{emp_id, pdf, xml}` (keys S3 del índice) → **zip** blob |
| `GET /misc/notifications/employee/<id_emp>&<status>` | auto-acceso | Bandeja del empleado: aquí aparece "Recibo disponible" |
| ~~`POST /rrhh/payroll/mail`~~ | — | **Deprecado**: creaba un borrador en Outlook bajando de SharePoint; el front no lo llama. Lo sustituye la 2ª etapa (correo SES) |

**Nuevo este mes:**

| Método y ruta | Permiso | Contrato |
|---|---|---|
| `DELETE /rrhh/payroll/files` | `rrhh` | Body `{emp_id, year, month, key, kind}` con `kind` ∈ `"pdf"\|"xml"\|"both"`. Borra la entrada del índice (BD primero) y el objeto S3 best-effort. 200 `{data: {files_data: <índice ya actualizado>, s3_deleted: bool}, msg, error}` (si S3 falla → 200 con `s3_deleted: false` y motivo en `error`). 404 empleado sin fila de nómina; 400 `key`/`kind` inexistente en el índice. Si el `key` queda vacío se elimina del mes |
| `POST /rrhh/payroll/notify` | `rrhh` | Body `{emp_id, year, month, key, message?}`. Crea notificación in-app al empleado (`receiver_id = emp_id`, título "Recibo de nómina disponible", `msg` con periodo). 201 `{data: {id_notification, notified: bool, reason?}, msg, error}` — `notified: false` si el empleado no tiene usuario. 400 si el `key` no tiene al menos un archivo. **Preparado para etapas**: acepta `channels: ["app"]` (default); `"email"` se habilita en la 2ª etapa sin cambiar el contrato |
| `POST /rrhh/payroll/files/extract` *(solo si sobra, S4)* | `rrhh` | Multipart `file` (xml CFDI de nómina) → 200 `{data: {rfc, num_empleado, nombre, periodo: {inicio, fin, pago}, emp_id_sugerido: int\|null}, msg, error}`. **Solo sugiere**; no sube nada |

**Gotchas del front:** `month` se normaliza a 2 dígitos; las quincenas se distinguen por `key` (convención del front, p.ej. `2026-09-Q1`); el par se sube en dos requests con el mismo `key`; el link de WhatsApp (3ª etapa) lo arma el front con el teléfono del empleado, sin endpoint.

## Anexo B — Constructor de encuestas: API para el front (contrato preliminar)

> Base `/GUI/api/v1/rrhh`, permiso `rrhh`. El CRUD completo y el catálogo de widgets están en [`quizz_models_crud.md`](quizz_models_crud.md); aquí solo lo que **cambia o se agrega**.

| Método y ruta | Cambio / contrato |
|---|---|
| `GET /quizz/models` · `GET /quizz/models/<type_q>` | Ganan `replaces` (id del modelo del que se clonó, o `null`) y `replaced_by` (id de la versión que lo archivó, o `null`). El listado `?all=1` deja que la UI agrupe versiones |
| `PUT /quizz/models/<type_q>` | **Candado relajado**: `template` editable en cualquier status mientras `tasks_total = 0`. Con tasks → 400 con `msg` "tiene N encuestas asignadas; clona para editar preguntas" |
| `POST /quizz/models/<type_q>/clone` | Body `{name?}` (default `"<name> (v2)"`). Copia template + rúbrica, nace **borrador** (`status 0`), guarda `replaces: <type_q>`, `history`. 201 `{data: {type_q: <nuevo>, replaces, warnings}, msg, error}`. 404 si no existe |
| `PUT /quizz/models/<type_q>/status` | Body `{status, migrate_pending?: bool}`. Al **publicar** (`→1`) un modelo con `replaces` cuyo origen está ACTIVO: lo archiva automáticamente (history en ambos, `replaced_by` en el viejo) y, si `migrate_pending: true`, migra las pendientes. 200 `{data: {status, archived: <type_q_viejo>\|null, migrated: N, skipped_answered: M, skipped_eva360: K}, msg, error}` |
| `PUT /quizz/models/<type_q>/migrate-tasks` | Body `{from_type, only_pending: true}` (v1 solo acepta `true`). Reapunta `metadata.type_quizz` de las tasks **sin contestar** (`data_raw` vacío) de `from_type` a `type_q`; contestadas y eva 360 nunca. 200 `{data: {migrated, skipped_answered, skipped_eva360}, msg, error}`. 400 si `type_q` no está ACTIVO |

**Gotchas del front:** el editor visual solo produce `template`; la rúbrica va en la pestaña avanzada como JSON y los `warnings` del `PUT` se muestran, no bloquean. Al publicar una versión con `replaces`, el checkbox "migrar encuestas pendientes" va **desmarcado** por defecto.

## Anexo C — Multisede: qué consume el front este mes

> Contratos por fase en sus docs (`almacen_multisede_f*.md`, uno por fase). Rutas y reglas de negocio en [`almacen_multisede_plan.md`](almacen_multisede_plan.md). Permiso de sede `Sucursal-<id>`; el `id_warehouse` va implícito en el permiso, un id ajeno → 403.

| Pantalla (front) | Endpoints (back) | Fase |
|---|---|---|
| Inventario de sede + stock del principal (lectura) | `GET /sucursal/inventory` · `GET /sucursal/inventory/main` | F2 |
| Movimientos de sede: kardex + entrada/salida libre, editar, borrar | `GET /sucursal/movements/<type_m>` · `POST/PUT/DELETE /sucursal/movement` | F2 |
| Recepción de traslados: bandeja en tránsito + capturar recibido por item | `GET /sucursal/transfers` · `PUT /sucursal/transfer/receive` | F3 |
| Crear traslado (principal, formulario mínimo) | `POST /almacen/transfer` (+ `GET /almacen/transfers` para verlo) | F3 |

Fuera del mes en front: `/almacen/warehouses` (catálogo), `/almacen/transfer/cancel`, `/almacen/inventory/consolidated`, exports y dashboard de sede.

## Anexo D — Dashboard RH: API para el front (contrato preliminar)

> Namespace `/GUI/api/v1/dashboard`, permiso `rrhh`.

| Método y ruta | Contrato |
|---|---|
| `GET /rrhh/summary` | Todos los tiles en un JSON: `headcount: {total, by_department: [{department, count}]}`, `movements_month: {altas, bajas}`, `medical_expiring: {d30, d60, d90}` (+ lista de ids para el click), `vacations: {pending_approval, next_30_days}`, `quizzes: [{type_q, name, assigned, answered}]`, `birthdays_month: [{emp_id, name, day}]`. Query opcional `?month=YYYY-MM` (default mes actual) |
| `POST /rrhh/series` | Body `{metric, date_from, date_to, group_by?}` con `metric` ∈ `altas_bajas \| faltas \| retardos` y `group_by` ∈ `month` (default) `\| department`. 200 `data: {labels: [...], series: [{name, values: [...]}]}`. KPI nuevo = `metric` nuevo, mismo shape |

**Gotchas:** sin caché (agregados chicos); los tiles "por vencer" traen ids para que el click lleve a la lista filtrada sin otra llamada.
