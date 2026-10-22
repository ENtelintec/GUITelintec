# Plan — junta con Administración del 2026-10-22: vigencia y avisos de saldos, reglas de OCD, remisiones de OCD, correos de empleados, check-in con foto y CISCO

> Plan por fases nacido de la **junta con Administración del 2026-10-22** (revisión de avances y cambios a los planes) y del doc del front [`19-octubre-dudas-y-pendientes.md`](../../../../WebApps/telintec_webapp/docs/backend/19-octubre-dudas-y-pendientes.md) (dudas de traslados, catálogos de contrato, CISCO). Decisiones cerradas en sesión de grill del **2026-10-22**. **Nada de esto está implementado aún**: este doc fija alcance, modelo y orden; cada fase produce su propio doc en `docs/` con "Contrato mínimo para el front". Extiende [`control_entregas_ocd_plan.md`](control_entregas_ocd_plan.md) (OCD, entregas, vigencia en el ledger) y [`tenders_control.md`](../tenders_control.md) (licitaciones).

## Estado

**2026-10-22 (noche, 8)**: **F9 hecha y verificada contra dev (10/10, `Tests/tester_transfer_over_receive.py`; resolve 64/64)** → nota del 2026-10-22 en [`almacen_multisede_f3.md`](../almacen_multisede_f3.md): `PUT /sucursal/transfer/receive` 400 con `data.over_received` cuando se recibe más de lo enviado. **Back del plan completo** salvo F8, que espera el DDL `checkins.sql` en dev (`P-165`) para cerrar `P-164` con el tester. Quedan del usuario los dos SQL (`P-163`, `P-165`), de administración el patrón de folios (`P-157`) y el permiso de Cobranza (`P-155`), el PDF FO-PRE-02 (`P-169`) y el front (`P-152`, `P-161`, `P-166`, `P-170`, `P-171`).

**2026-10-22 (noche, 7)**: **F10 hecha y verificada contra dev (46/46, `Tests/tester_quotation_cisco.py`; folio, OCD, licitaciones, PUT metadata y costos en verde)** → [`cotizaciones_cisco.md`](../cotizaciones_cisco.md): rutas `/quotation/cisco/*` sobre el mismo midleware, `metadata.format = cisco` + `concept`, partidas en `extra_info`, `GET /quotation/-1` sin CISCO por default (`?format=cisco|all`; con `document_type=ocd` sí salen), `PUT /quotation` grande bloqueado para CISCO; PDF FO-PRE-02 `P-169` después. Siguiente: F9 (traslados).

**2026-10-22 (noche, 6)**: **F3 hecha y verificada contra dev (32/32, `Tests/tester_folio_quotation.py`; OCD, licitaciones y PUT metadata en verde)** → [`folio_sugerido_cotizaciones.md`](../folio_sugerido_cotizaciones.md): `GET /quotation/folio` con el patrón provisional en `QUOTATION_FOLIO_PREFIXES` (`P-157` sigue abierto) y 409 del folio solo al marcar una OCD. **Revisión de correos**: nunca hubo dos columnas (institucional/personal) y en dev nadie tiene dos correos reales; el front pinta dos inputs fijos sobre `emails[]` (`P-171`), sin cambio de back. Siguiente: F10 (CISCO) → F9 (traslados).

**2026-10-22 (noche, 5)**: **F7 hecha y verificada contra dev (23/23, `Tests/tester_employee_emails.py`; nómina SES/descarga/vacaciones en verde)** → [`empleados_correos_y_nomina_activos.md`](../empleados_correos_y_nomina_activos.md); DML `employees_emails_normalize.sql` para el usuario (`P-163`). **F8 back hecho** → [`checkin_foto.md`](../checkin_foto.md): validaciones verificadas (15/15, `Tests/tester_checkin.py`); las pruebas sobre la tabla esperan el DDL `checkins.sql` en dev (`P-165`), el tester las corre solo al existir. Siguiente: F3 (folio) → F10 (CISCO) → F9 (traslados).

**2026-10-22 (noche, 4)**: **F2 hecha y verificada contra dev (35/35, `Tests/tester_balance_alerts.py`; regresión de saldos y entregas en verde)** → [`avisos_saldos_entregas_traslados.md`](../avisos_saldos_entregas_traslados.md). Con esto el bloque de Cobranza/OCD de la junta (F1, F2, F4, F5, F6) está completo en el back.

**2026-10-22 (noche, 3)**: **F5 hecha y verificada contra dev (26/26, `Tests/tester_delivery_vencimiento.py`; regresión de entregas, OCD, PDF, saldos y cancelación en verde)** → [`control_entregas_vencimiento.md`](../control_entregas_vencimiento.md).

**2026-10-22 (noche, 2)**: **F4 hecha y verificada contra dev (40/40, `Tests/tester_ocd_rules.py`; regresión de cotizaciones, OCD, licitaciones, costos y entregas en verde)** → [`ocd_reglas_po_vencimiento.md`](../ocd_reglas_po_vencimiento.md).

**2026-10-22 (noche)**: **F6 hecha y verificada contra dev (25/25, `Tests/tester_remission_no_attachments.py`; regresión de remisiones, saldos, anexos y entregas en verde)** → [`remision_ocd_campos_y_sin_anexos.md`](../remision_ocd_campos_y_sin_anexos.md).

**2026-10-22 (tarde)**: **F1 hecha y verificada contra dev (33/33, `Tests/tester_balance_vencido.py`; regresión de saldos, cancelación y entregas en verde)** → [`control_saldos_vencido_y_monto.md`](../control_saldos_vencido_y_monto.md).

**2026-10-22**: grill cerrado, plan escrito.

## Punto de partida (lo que el código ya resuelve)

- **Saldo consumido ya sigue al monto**: `consumed_amount` / `available_amount` se calculan en cada `GET /balanceControl*` como Σ `extra_info.remission_amount` de las remisiones no canceladas del control ([`remission_cancel.md`](../remission_cancel.md)). Cambiar `remission_amount` por `PUT /remissionBalance` ya descuenta o devuelve en la siguiente lectura. Lo que no existe: rechazar un monto `0` y devolver el saldo resultante en el mismo `PUT`.
- **Vigencia**: `balance_controls.end_date` + `days_to_end` + `?expiring_days=` ([`control_saldos_vigencia.md`](../control_saldos_vigencia.md)). No hay estado "vencido" ni "por vencer"; el front lo deduce del número. La tabla `contracts` **no tiene fecha fin**: la vigencia vive solo en el control.
- **Las dos fechas de un movimiento** ya existen: `movement_date` (cuándo lo cambió el cliente, editable con `PUT /balanceControl/movement`) y `timestamp` (cuándo se capturó). "Fecha de autorización → fecha de modificación" es solo la etiqueta del front.
- **Notificaciones de sistema**: receta de médicos y CDA — hilo `NotificationsSearch` que corre una vez al día cuando alguien pega al endpoint que lo dispara, con bandera y fecha en `files/flags_daemons.json`, y escribe a un permiso con `create_notification_permission_notGUI`. No hay nada para saldos, entregas ni traslados.
- **OCD** = cotización con `metadata.document_type = "ocd"` ([`quotation_ocd.md`](../quotation_ocd.md)): `client_po_number` **opcional**, `delivery_time` **texto libre**, sin fecha de vencimiento, `quotation_code` a mano y sin candado de duplicados; `PUT /quotation/ocd` rechaza `status ≠ 0`, así que la cotización interna de una licitación (`status 3`) no se puede convertir. Las partidas (`quotation_items`) tienen `extra_info` JSON y ninguna fecha de entrega.
- **Control de entregas**: detalle con pedido/entregado/pendiente por partida y `items_count`/`items_complete`; la lista solo trae cantidades, montos y `progress_pct` ([`control_entregas.md`](../control_entregas.md)).
- **Remisión** (`POST /remission`): `plant`, `activity`, `location`, `general_description`, `comments` y `area` son `InputRequired` (flujo Ternium). `files` es la lista de anexos y nada marca "sin anexos".
- **Empleados**: `employees.email` es `VARCHAR(255)`; en dev **ningún empleado guarda dos correos reales** (20 filas traen una coma suelta, herencia de una pantalla con dos cajas; corregido el 2026-10-22, antes decía 13 de 64). El API lo trata como string y nómina (`_first_email`) y el front (`correoDe`) usan solo el primero.
- **Nómina**: `get_payrolls(-1)` ya filtra `status = 'activo'`; `POST /payroll/notify` acepta cualquier `emp_id` (inactivos y `status` NULL incluidos).
- **Fichaje**: `sql_telintec_mod_rrhh.fichajes` es la carga del Excel del biométrico de Ternium. No hay check-in desde la app.
- **Traslados**: la diferencia al recibir queda sin movimiento hasta `PUT /almacen/transfer/<id>/resolve` (reingreso | merma); recibir más de lo enviado se acepta y descuadra ([`almacen_multisede_resolve.md`](../almacen_multisede_resolve.md)).
- **CISCO (FO-PRE-02)**: el front ya hizo pantallas contra rutas `/admin/presales/quotation/cisco/*` que no existen ([`cotizacion-cisco-contrato-propuesta.md`](../../../../WebApps/telintec_webapp/docs/backend/cotizacion-cisco-contrato-propuesta.md)). `quotation_item_costs` ya tiene `service_months` y `smart_account` (F6).

## Decisiones acordadas (grill 2026-10-22)

| Tema | Decisión |
|---|---|
| **Monto de remisión vs saldo** | El monto que consume saldo **sigue siendo `remission_amount`** (Control de saldos). Sin fallback a partidas ni a `total_sin_iva`. `PUT /remissionBalance` con `remission_amount` **`0` o negativo → 400**; el 200 devuelve `consumed_amount` / `available_amount` resultantes del control para repintar sin re-GET. Descartado el candado "consumido > contratado": una inyección de saldo es el camino cuando el cliente amplía. |
| **Vencido / por vencer** | Campo **derivado, numérico, nunca almacenado** `validity_status` en lista y detalle de controles: `0` vigente (más de 60 días o sin fecha) · `1` por vencer (≤ 60 días) · `2` vencido (`end_date < hoy`). Filtro `?validity_status=2` (o lista) en `GET /balanceControl`. **Vencido no bloquea nada** (Ternium manda la adenda tarde); una VIGENCIA lo regresa a vigente. Regla de estados numéricos del repo. |
| **Etiqueta "fecha de modificación"** | Solo front: la etiqueta de `movement_date` en el lápiz del historial, y pintar `movement_date` y `timestamp` por fila. Sin cambio de API. |
| **Avisos de saldos** | Barrido diario con la receta de CDA, **disparado desde `GET /balanceControl`** (`flag_balance` / `last_date_balance` en `flags_daemons.json`). Umbrales fijos en código: vigencia a **60, 30 y 15 días** de `end_date`; saldo cuando `available / contracted ≤ 25 %`, **10 %** y **0**. **Una vez por umbral y por control**: marca en `balance_controls.extra_info.notified` (`{"days_60": "2026-10-22", "pct_25": …}`); una VIGENCIA limpia las marcas de días, una INYECCIÓN las de porcentaje. Destinatario **`administracion`** (no existe permiso de Cobranza; crearlo queda pendiente). Un mensaje diario con una línea por control. Sin correo. |
| **Avisos de OCD y traslados** | Mismo barrido: controles de entregas abiertos con `due_date` a 60/30/15 días (marcas en `delivery_controls.extra_info.notified`) a `administracion`; traslados en `RECIBIDO CON DIFERENCIAS` (status 2) con más de 1 día sin resolver, a `almacen` + `administracion`, cada día mientras sigan así. |
| **Folio sugerido** | `GET /admin/presales/quotation/folio?document_type=ocd\|quotation&format=cisco` → `{"folio": …}` con la receta "patrón + max + 1" por año. **Patrón provisional** `OCD-AAAA-NNN` / `COT-AAAA-NNN` / `COT-CISCO-AAAA-NNN` en una sola constante: **administración lo manda** (pendiente). El front pre-llena, el usuario puede editar. **Candado 409 solo para OCD** (`POST /quotation` con `document_type = ocd` y `PUT /quotation/ocd`): preventa y CISCO siguen sin candado para no romper lo histórico. |
| **OCD desde licitación ganada** | La "licitación ganada" de la junta es la **cotización interna `status 3`**. `PUT /quotation/ocd` la acepta cuando su licitación está en `status 1` **y** sin `contract_id`; conserva `status 3` y gana `document_type = ocd`. `quotation_code` = `tender_number` (sin folio nuevo); `client_po_number` default = `tenders.po_number` (si la licitación no lo tiene, 400 pidiéndolo). **Exclusión**: licitación con OCD no crea contrato (`POST /contract` → 400) y licitación con contrato no se convierte. `GET /tender(s)` expone `document_type` de su cotización. Descartado clonar (duplica partidas y análisis F6, necesita DDL). |
| **Identificador de OC** | `client_po_number` **obligatorio** para crear o marcar una OCD (400 vacío; en un `PUT /quotation/ocd` que solo ajusta otra llave, vacío = conservar, pero nunca puede quedar sin él). **Único global** entre OCD como un número de contrato marco (409), comparado sin mayúsculas ni espacios al borde; vive en `metadata`, así que el candado va en código. `pedido_exiros` de la remisión sigue **opcional**. |
| **Vencimiento de la OCD y fecha por partida** | `metadata.due_date` (`YYYY-MM-DD`) **capturada** en `PUT /quotation/ocd` y `POST /quotation`: es el tiempo de entrega comprometido; `delivery_time` (texto) se conserva solo para el PDF. `quotation_items.extra_info.delivery_date` **opcional por partida** en `POST`/`PUT /quotation`, `PUT /tender/items` e import de Excel; 400 si alguna supera `due_date`. Descartado derivar `due_date` de las partidas. |
| **Control de entregas: vencimiento y conteos** | Lista y detalle ganan `due_date`, `days_to_due` y `validity_status` (mismos valores y 60 días que saldos), filtro `?validity_status=`; por partida `delivery_date`, `days_to_delivery` y `overdue` (pendiente > 0 y fecha pasada). La lista gana en `totals` **`items_count`, `items_complete`, `items_pending`**. El icono junto al avance lista las partidas con el **detalle al hacer clic** (sin endpoint nuevo). |
| **Remisión de OCD** | Los seis campos `plant`, `activity`, `location`, `general_description`, `comments`, `area` pasan a **opcionales siempre** (`default=""`) en `POST`/`PUT /remission` y `/remissionControlTable`. El back no distingue flujos; el front los exige con contrato y los oculta en OCD. Descartada la validación condicional. |
| **"Sin anexos"** | Bool **`extra_info.no_attachments`** (sin motivo), escrito **solo por `administracion`** en endpoint propio **`PUT /admin/collections/remission/noAttachments {id, no_attachments}`** (receta de `/cancel`: history, 400 si la remisión tiene anexos que no sean firmas). Subir un anexo a una remisión marcada **quita la marca** (history) en vez de rechazar. El GET la expone aplanada. Sin efecto en el PDF. |
| **Correos de empleados** | `emails: []` en `POST`/`PUT /rrhh/employee` y en todos los GET de empleados (`/rrhh/employees/*`, `/common/employees/*`, nómina); el back valida cada uno, quita duplicados y guarda `a@x,b@y` en la **misma columna** `employees.email`; `email` (string) sigue saliendo como el primero hasta que el front migre. DML de limpieza de lo que hay. **Nómina por correo a todos** los correos del empleado (`email_to` pasa a lista). Descartados `extra_info.emails` (dos lugares) y tabla aparte (DDL para 2 o 3 correos). **Revisión 2026-10-22**: nunca hubo columna institucional/personal aparte; el front pinta **dos inputs fijos** (institucional `@telintec.com.mx` y personal) sobre `emails[]` y etiqueta por dominio (`P-171`), sin cambio de back. |
| **Nómina solo activos** | `POST /payroll/notify` → **400 "empleado inactivo"** si `status` no es `activo` (NULL incluido), antes de escribir el aviso o mandar el correo; sin `force`. `POST /payroll/files/update` **sigue aceptando inactivos** (último recibo de una baja). |
| **Check-in con foto** | **Entra ya**, para todo el personal, como **respaldo cuando el biométrico no esté**; lo que hay de `fichajes` se ignora. Tabla nueva `sql_telintec_mod_rrhh.checkins`; `POST /common/checkin` multipart (foto obligatoria, una por request) sobre el `emp_id` del token, hora del **servidor** (`America/Mexico_City`), `lat`/`lon`/`accuracy` opcionales; **sin alternancia forzada** (el back acepta lo que llegue); `GET /common/checkin/me`; **RH hace todas las correcciones**: `PUT /rrhh/checkin/cancel` (status 1 + motivo) y `POST /rrhh/checkin` manual (hora capturada, sin foto, `manual: true`); `GET /rrhh/checkins` con **resumen por empleado y día calculado en lectura** (primera entrada, última salida, horas, pares incompletos); `GET /rrhh/checkin/<id>/photo` blob. Sin validación facial, geocerca, retardos ni tolerancias. Fotos en el bucket S3 de RH (receta de fotos de CDA). |
| **Traslados (`P-145`)** | (1) El faltante **sigue manual** (reingreso | merma). (2) Aviso diario de traslados sin resolver (arriba). (3) **400 al recibir más de lo enviado**; lo que llegue de más es una entrada normal en la sede. (4) **`almacen` resuelve** (default a falta de respuesta de administración); el botón "Resolver diferencia" sigue en el front. |
| **Cotizaciones CISCO** | **Entra ya.** Mismas tablas: `quotations.metadata.format = "cisco"` (plantilla FO-PRE-02; ausente = FO-PRE-01) **separado** de `document_type` (quotation \| ocd) para que una CISCO se convierta en OCD sin perder formato. Cabecera gana `concept`; `currency` y `delivery_time` ya existen. Partidas en `quotation_items`: `extra_info.item` texto (`1`, `1.1`) con `partida` derivado del orden, `n_part`, `extra_info.smart_account` / `service_months` / `delivery_time`; `udm` opcional con `format = cisco`. **Rutas del front** `GET /quotation/cisco/-1`, `GET /quotation/cisco/<id>`, `POST`/`PUT /quotation/cisco` (upsert por `qa_item_id`) como envoltorios delgados sobre el mismo midleware; `GET /quotation/-1` las **excluye** por default (`?format=cisco` las pide). `quotation_code` sin candado; folio sugerido `COT-CISCO-AAAA-NNN`. PDF FO-PRE-02 **después**. Conversión a OCD con `PUT /quotation/ocd` igual que preventa. |
| **Catálogos de contrato en Preventa (duda 2.3)** | Ya resuelto en [`tenders_control.md`](../tenders_control.md): `?status=0` y `/ocd` solo sobre `status 0`; copias huérfanas = `P-150`. Sin cambio. |
| **Fuera de este bloque** | Permiso propio de Cobranza para los avisos; patrón definitivo de folios; PDF FO-PRE-02; correos por SES de los avisos (`P-095`); retardos/tolerancias/geocerca del check-in; horas del check-in persistidas. Todos a `pendientes.md`. |
| **DDL / DML** | Solo **una tabla nueva** (`checkins`) y un **DML** (normalizar `employees.email`). Todo lo demás vive en `metadata` / `extra_info` JSON o se deriva en lectura. Scripts en [`scripts_db_handle/`](../../scripts_db_handle/), **los revisa y ejecuta el usuario**. |

## Modelo de datos

```
sql_telintec_mod_rrhh.checkins                       (F8, DDL scripts_db_handle/checkins.sql)
  id            INT PK AUTO_INCREMENT
  emp_id        INT NOT NULL            -> sql_telintec.employees(employee_id)  (índice emp_id, timestamp)
  type          TINYINT NOT NULL        0 entrada · 1 salida  (catálogo en Python)
  timestamp     DATETIME NOT NULL       hora del servidor (America/Mexico_City)
  lat / lon     DECIMAL(10,7) NULL · accuracy DECIMAL(8,2) NULL
  photo_key     VARCHAR(255) NULL       llave S3 (NULL solo en registros manuales de RH)
  is_manual     TINYINT(1) NOT NULL DEFAULT 0
  status        TINYINT NOT NULL DEFAULT 0   0 válido · 1 anulado (suave, con motivo en history)
  created_by    INT NULL                emp_id del token (el empleado, o RH en manuales)
  device_info   VARCHAR(255) NULL
  history JSON NULL · extra_info JSON NULL

sql_telintec.employees.email                          (F7, DML employees_emails_normalize.sql)
  misma columna VARCHAR(255): "a@x,b@y" normalizado (sin espacios, sin ';', sin tokens vacíos, dominio en minúsculas)

JSON sin DDL
  balance_controls.extra_info.notified     {"days_60": "YYYY-MM-DD", "days_30", "days_15", "pct_25", "pct_10", "pct_0"}
  delivery_controls.extra_info.notified    {"days_60", "days_30", "days_15"}
  quotations.metadata                      + due_date (OCD) · + format ("cisco") · + concept (CISCO)
  quotation_items.extra_info               + delivery_date · + item / smart_account / service_months / delivery_time (CISCO)
  activity_reports.extra_info              + no_attachments (bool)
  files/flags_daemons.json                 + flag_balance / last_date_balance
```

## Fases y orden (dependencias)

Orden de negocio: Cobranza primero, después OCD/Preventa, después RH. Cada fase: doc propio en `docs/` (4 capas + contrato del front + "Al modificar"), línea al final de su sección en `README.md`, ítem en `pendientes.md`, verificación contra dev con tester en `Tests/`.

| # | Bloque | Endpoints / piezas | Pendiente | Depende de |
|---|---|---|---|---|
| **F1** | Saldos: vencido y monto | `validity_status` + `?validity_status=` en `GET /balanceControl*`; `PUT /remissionBalance`: `remission_amount` ≤ 0 → 400, 200 con `consumed_amount`/`available_amount` | `P-153` | — |
| **F2** | Barrido diario de avisos | `NotificationsSearch(type_n="balance")` disparado desde `GET /balanceControl`: saldos (60/30/15 días, 25/10/0 %), OCD por vencer, traslados sin resolver; marcas `extra_info.notified`; flags nuevos | `P-154` | F1 (`validity_status`), F5 (`due_date` en entregas) para la parte de OCD |
| **F3** | Folio sugerido | `GET /quotation/folio`; 409 de `quotation_code` en OCD; patrón en constante | `P-156` | — |
| **F4** | Reglas OCD | `PUT /quotation/ocd` sobre `status 3` (licitación en 1 sin contrato) + exclusión con `POST /contract`; `client_po_number` obligatorio y único global; `due_date`; `delivery_date` por partida en `POST`/`PUT /quotation`, `PUT /tender/items`, import | `P-158` | — |
| **F5** | Control de entregas | `due_date`, `days_to_due`, `validity_status` + filtro; `delivery_date`/`days_to_delivery`/`overdue` por partida; `items_count`/`items_complete`/`items_pending` en la lista | `P-159` | F4 |
| **F6** | Remisión de OCD | Seis campos opcionales; `PUT /remission/noAttachments`; `no_attachments` en el GET; anexo nuevo quita la marca | `P-160` | — |
| **F7** | Correos y nómina | `emails[]` en empleados + DML; nómina a todos los correos; `notify` 400 inactivos | `P-162` · `P-163` | — |
| **F8** | Check-in con foto | DDL `checkins.sql`; `POST /common/checkin`, `GET /common/checkin/me`, `GET /rrhh/checkins` (resumen), `PUT /rrhh/checkin/cancel`, `POST /rrhh/checkin`, `GET /rrhh/checkin/<id>/photo` | `P-164` · `P-165` | DDL en dev |
| **F9** | Traslados | 400 al recibir más de lo enviado | `P-167` | — (el aviso va en F2) |
| **F10** | Cotizaciones CISCO | `format = cisco`, `concept`, partidas en `extra_info`, rutas `/quotation/cisco/*`, exclusión en `GET /quotation/-1` | `P-168` | F3 (folio) solo para la sugerencia |

F1, F3, F4, F6, F7, F9 y F10 no dependen entre sí. F2 cierra después de F5 (o sale primero solo con saldos y traslados, y gana la parte de OCD al terminar F5).

## Contratos preliminares (los definitivos van en el doc de cada fase)

Base `/GUI/api/v1/admin/collections` (saldos, entregas, remisiones), `/GUI/api/v1/admin/presales` (cotizaciones, folio, licitaciones), `/GUI/api/v1/rrhh` y `/GUI/api/v1/common` (empleados, nómina, check-in), `/GUI/api/v1/almacen` (traslados). Header `Authorization` con el **JWT crudo** (sin `Bearer `). Envelope `{data, msg, error}`; descargas de foto: blob en 200, envelope en 4xx.

- `GET /balanceControl?validity_status=2` → filas con `validity_status` (0/1/2), `days_to_end`, `consumed_amount`, `available_amount`. `GET /balanceControl/catalogs` lista `validity_statuses`.
- `PUT /remissionBalance` con `remission_amount: 0` → 400 `error: ["remission_amount debe ser mayor a 0"]`; con monto válido → 200 `data: {…, "balance_control": {"id_control": 6, "consumed_amount": 812000.0, "available_amount": 438000.0}}`.
- `GET /quotation/folio?document_type=ocd` → 200 `data: {"folio": "OCD-2026-007", "pattern": "OCD-AAAA-NNN"}`.
- `PUT /quotation/ocd` → `{"id_quotation": 51, "client_po_number": "4500123456", "currency": "MXN", "due_date": "2026-12-15", "approved_date": "2026-11-20"}` → 200; 400 `client_po_number` vacío / `due_date` inválida / licitación sin ganar o con contrato; **409** `client_po_number` repetido (`data.id_quotation` de la otra OCD). Sobre la cotización interna de una licitación ganada: mismo body.
- `POST /contract` con `quotation_id` de una licitación ya convertida a OCD → 400 `"La licitación ya es una OCD"`.
- `PUT /quotation` / `PUT /tender/items`: `products[].delivery_date: "2026-12-01"` opcional → 400 si supera `due_date`.
- `GET /deliveryControl` → cada fila con `due_date`, `days_to_due`, `validity_status` y `totals.items_count / items_complete / items_pending`; `?validity_status=1,2`. Detalle: `items[].delivery_date`, `days_to_delivery`, `overdue`.
- `PUT /remission/noAttachments` → `{"id": 71, "no_attachments": true}` → 200 `data: {"id_remission": 71, "no_attachments": true}`; 400 si tiene anexos (lista nombres) o está cancelada; 404. Solo `administracion`.
- `POST`/`PUT /remission`: `plant`, `activity`, `location`, `general_description`, `comments`, `area` opcionales (`""`).
- `PUT /rrhh/employee` → `{"emails": ["ana@x.com", "ana.p@y.com"], …}` → 400 por correo inválido; los GET devuelven `emails: [...]` y `email: "ana@x.com"`.
- `POST /rrhh/payroll/notify` con `channels: ["email"]` → 200 `data.email_to: ["ana@x.com", "ana.p@y.com"]`; empleado inactivo → 400 `"empleado inactivo"`.
- `POST /common/checkin` multipart `file` (jpg/png) + `type` (0/1) + `lat`/`lon`/`accuracy` opcionales → 201 `data: {"id": 12, "emp_id": 36, "type": 0, "timestamp": "2026-10-22 08:03:11", "photo_key": "…"}`; 400 sin foto. `GET /common/checkin/me?date_from&date_to` → eventos propios. `GET /rrhh/checkins?emp_id&date_from&date_to` → `data: {"events": [...], "summary": [{"emp_id": 36, "date": "2026-10-22", "first_in": "08:03", "last_out": "17:40", "hours": 9.6, "incomplete": false}]}`. `PUT /rrhh/checkin/cancel {id, reason}` → status 1. `POST /rrhh/checkin {emp_id, type, timestamp, reason}` → `manual: true`. `GET /rrhh/checkin/<id>/photo` → blob.
- `PUT /almacen/transfer/<id>/receive` con `quantity_received > quantity_sent` → 400 listando productos.
- `GET /quotation/cisco/-1` · `GET /quotation/cisco/<id>` · `POST`/`PUT /quotation/cisco` → el contrato de la propuesta del front, con `metadata.format = "cisco"`, `metadata.concept`, partidas `{qa_item_id, item, n_part, smart_account, description, service_months, delivery_time, quantity, price_unit}`; `GET /quotation/-1` sin `?format=cisco` no las devuelve.

## Respuesta al doc del front del 2026-10-19

| Sección | Respuesta |
|---|---|
| 1. Marcar | `P-125`, `P-142`, `P-143`, `P-045` → `[x]`. `P-043`: ok. `P-070`: sigue 🧪 hasta la cuenta SGI. |
| 2. `P-145` traslados | Ver decisión *Traslados*: manual, aviso diario (F2), 400 a sobrantes (F9), `almacen` resuelve. El front hace el botón "Resolver diferencia" (status 2) y pinta la resolución (status 4). |
| 2.1 Licitaciones | Ya contestado en [`tenders_control.md`](../tenders_control.md) (`P-147`). Nuevo: la licitación ganada también puede convertirse en OCD (F4). |
| 2.2 SES | Resuelto 2026-10-20 (`P-036` cerrado). |
| 2.3 Catálogos de contrato | `?status=0` y `/ocd` solo sobre `status 0` ([`tenders_control.md`](../tenders_control.md)); huérfanas `P-150`. Las CISCO también salen del listado por default (F10). |
| 2.4 CISCO | Entra (F10) con las rutas que el front construyó; `format` separado de `document_type`; `quotation_code` sin candado; PDF FO-PRE-02 después; conversión a OCD sí. |
| 4. Ventanas antiguas | Decisión del front; el back no cambia (remisión y control sin contrato siguen aceptados, `P-079`). |
| 5. `P-056`, `P-015` | Se quedan como están. |

## Pendientes que abre este plan

Ver [`pendientes.md`](../pendientes.md): `P-152` a `P-170` (ids en la tabla de fases; front en `P-152`, `P-161`, `P-166`, `P-170`; administración en `P-155`, `P-157`; usuario en `P-163`, `P-165`).
