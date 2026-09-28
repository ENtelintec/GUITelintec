# Plan — Control de Entregas por OCD/cotización, cancelación de remisiones, vigencia de saldos y análisis de costos

> Plan por fases nacido de la **junta con Administración del 2026-09-23** ([`anotaciones_junta_administracion-23-09-26.md`](../../scripts_db_handle/anotaciones_junta_administracion-23-09-26.md)) y de los formatos que mandó Preventa/Cobranza (FO-PRE-01 R2 Cotización, FO-PRE-02 R2 COT CISCO, FO-PRE-03 R3 Control de Cotizaciones, FO-PRE-04 R1 Control de licitaciones, FO-CXC-05 R0 REM OC Directas). Decisiones cerradas en sesión de grill del **2026-09-28**. **Nada de esto está implementado aún**: este doc fija alcance, modelo y orden; cada fase produce su propio doc en `docs/` con "Contrato mínimo para el front". Extiende la iniciativa de Control de saldos ([`control_saldos_cabecera.md`](../control_saldos_cabecera.md) · [`control_saldos_sin_contrato.md`](../control_saldos_sin_contrato.md) · [`control_saldos_movimientos.md`](../control_saldos_movimientos.md)).

## Estado

**2026-09-28 (noche)**: **F0 corrida en dev** por el usuario (con FKs). **F2 codificada** → [`control_entregas.md`](../control_entregas.md), con un **ajuste al plan**: `activity_reports.quotation_id` es FK a `quotations_activities` (la QA de admin/collections), no a `quotations`, así que la membresía remisión → control **no** se deriva de esa columna; se agregó `activity_reports.delivery_control_id` (DDL chico [`control_entregas_ocd_membresia.sql`](../../scripts_db_handle/control_entregas_ocd_membresia.sql), pendiente de correr) con auto-enlace por items y `PUT /deliveryControl/remissions`. Lo entregado por partida sí se deriva de `item_c_id` como estaba previsto. **F2 verificada contra dev (71/71 checks)** tras correr el DDL de membresía. **F3 hecha y verificada (32/32)** → [`remission_cancel.md`](../remission_cancel.md). **F4 hecha y verificada (30/30)** → [`control_saldos_vigencia.md`](../control_saldos_vigencia.md). **F5 hecha y verificada con PDF real (17/17)** → [`remission_pdf_ocd.md`](../remission_pdf_ocd.md). **F6 hecha y verificada (37/37)** → [`quotation_cost_analysis.md`](../quotation_cost_analysis.md). **Todo el back del plan (F0–F6) está servido con contrato y verificado en dev el 2026-09-28.** Quedan: DDL de `control_entregas_ocd.sql` + `control_entregas_ocd_membresia.sql` en test/prod (usuario, después de los de saldos), el front de cada pieza y la etapa 2 del análisis de costos (ver `pendientes.md`).

**2026-09-28 (tarde)**: **F0** entregada para revisión del usuario ([`control_entregas_ocd.sql`](../../scripts_db_handle/control_entregas_ocd.sql); sin correr en ninguna BD). **F1 hecha y verificada contra dev** (35 checks) → [`quotation_ocd.md`](../quotation_ocd.md): no necesitaba DDL. Siguiente: F2 (control de entregas) en cuanto el DDL corra en dev; F3/F4 pueden ir antes si Cobranza aprieta (F4 sí necesita las columnas de fecha del DDL).

**2026-09-28**: grill cerrado, plan escrito.

## Punto de partida (lo que el código ya resuelve)

- **No existe la "orden de compra directa" como entidad.** Las remisiones cargan `extra_info.pedido` / `pedido_exiros` como texto y `quotation_id` anulable. Sí existe la cotización (`quotations` + `quotation_items`) y los items de remisión (`quotation_activity_items`) ya apuntan al item cotizado por `item_c_id` (`products[].item_contract_id` en `POST /remission`). Por eso "entregado vs pendiente por partida" es derivable hoy para remisiones nacidas de una cotización.
- **Inyección de saldo ya existe**: `POST /balanceControl/movement` con `movement_date` (la fecha que captura el usuario), `timestamp` (cuándo se registró), `reason` y `document`. Cubre "la fecha en que Ternium lo modificó vs cuándo lo capturó Carolina" para el dinero.
- **`end_date` ya vive en `balance_controls`** y se edita por el `PUT` de cabecera (diff `before/after` en `history`). Falta un registro fechado de la extensión y el aviso "por vencer" en el back.
- **Evidencias de servicios ya existen**: `POST /remission/attachment-<id>` con `category` (fotos, cotización firmada, reporte a mano) y el PDF combinado `?full=1`. Nada que construir.
- **Cancelar remisión no existe.** `activity_reports.status` tiene el valor `3 = Cancelada` pero nada lo escribe; solo hay `DELETE /remission`. El saldo consumido tampoco lo calcula el back: cada remisión guarda `remission_amount` en `extra_info` y el front suma.
- **Análisis de costos no existe** en ninguna tabla; el único costo/ganancia del sistema es a nivel cabecera de `purchase_management`.
- Los formatos: **FO-PRE-01** ≈ cotización del sistema (empresa, contacto, usuario, teléfono, email, planta/área/ubicación, moneda, items descripción/cantidad/UM/PU/total, comentarios); **FO-CXC-05** = remisión existente con `No. PEDIDO EXIROS`, moneda, `POS`/descripción/cantidad/UM/PU/total, subtotal/IVA/total y dos firmas; **FO-PRE-03** = el Control de Cotizaciones de Operaciones (folio, cliente/contrato, planta/área/ubicación, descripción, responsable, medio, fechas recepción/envío, monto USD/MXN, respuesta usuario/fecha/estado, costo, ganancia, indicador ≤ 12 días hábiles); **FO-PRE-04** = licitaciones (fuera de alcance).

## Decisiones acordadas (grill 2026-09-28)

| Tema | Decisión |
|---|---|
| **OCD (orden de compra directa)** | **Es una cotización con `metadata.document_type = "ocd"`** + `client_po_number` (pedido EXIROS o nº de OC del cliente no Ternium) + `currency` + `delivery_time` + `approved_date`. Sin DDL (metadata es JSON). Reusa `quotation_items`, la carga de items, el enlace `item_c_id` y el PDF. Una OC del cliente por algo nunca cotizado se captura directo como cotización tipo OCD (misma pantalla). Descartadas: tabla `customer_orders` (duplica items/import/PDF) y "contrato sin marco" (contamina el catálogo de contratos) |
| **Convertir a OCD** | `document_type`/`client_po_number` aceptados en `POST /quotation` + **`PUT /quotation/ocd`** `{id_quotation, client_po_number, currency, approved_date}` que hace merge de esas llaves sin tocar items (el `PUT /quotation` grande reemplaza items y no debe usarse para esto). Solo `administracion` |
| **Control de Entregas** | **Entidad almacenada `delivery_controls`** (decisión del usuario; descartada la vista puramente calculada). Dueña de: `quotation_id` (NOT NULL, **1 control activo por cotización → 409**), `client_id` (copiado de la cotización), `title` (default folio), `client_po_number` (copiado, editable), `currency`, `status` (0 abierto · 1 completo · 2 cancelado; el back lo pone en completo cuando todo está entregado, editable), `custom_fields` (mismo contrato `{key,label,value_type,comment}` de saldos para reusar el grid), `created_by`, `timestamp`, `history`, `extra_info`. **Derivado en lectura, nunca almacenado**: por partida pedido / entregado / pendiente (cantidades y montos) a partir de los items de remisión con `item_c_id` y remisión no cancelada |
| **Membresía remisión → control de entregas** | ~~Derivada de `activity_reports.quotation_id`~~ **Corregido al implementar (2026-09-28)**: esa columna es FK a `quotations_activities` (QA), no a `quotations`. Membresía **explícita `activity_reports.delivery_control_id`** (igual que saldos), auto-enlace al crear la remisión por `metadata.delivery_control_id` o por sus items, `PUT /deliveryControl/remissions {add, remove}`. Ver [`control_entregas.md`](../control_entregas.md) |
| **Gate de creación** | `POST /deliveryControl` exige cotización existente y `document_type = "ocd"`; cotización normal → 400 "conviértela a OCD primero" |
| **Sobre-entrega** | `POST`/`PUT /remission` cuya cantidad deje entregado > pedido para ese `item_c_id`, **solo si la cotización tiene control activo** → **400** listando partidas (`"partida 3: pedido 20000, entregado 15000, esta remisión 6000"`). Descartado el aviso suave (deja el pendiente negativo). Flujos de contrato Ternium no se tocan |
| **Items fuera de la orden** | Items de remisión sin `item_c_id` se permiten; el detalle del control los lista en un bloque aparte "fuera de la orden" (extras de servicio) |
| **Precio** | Sin regla nueva: la remisión conserva el split `unit_price_quotation` (sugerido) / `unit_price` (real); el monto entregado usa el real |
| **Cambios en la cotización con control activo** | `PUT /quotation` puede agregar partidas o subir cantidades (change orders); **quitar una partida o bajarla por debajo de lo entregado → 400** listando; `DELETE /quotation` → 400. Cancelar el control levanta estas reglas |
| **Cancelación de remisión** | **`PUT /remission/cancel`** `{id, reason}` → `status = 3`, history con usuario y motivo, solo `administracion`. Cancelada: `PUT /remission`, `/remissionControlTable`, `/remissionBalance` → 400; `DELETE` → 400 (queda el rastro). **Sin reactivación** (error = remisión nueva) |
| **Devolución del saldo** | **Por exclusión, no por movimiento**: el back calcula en `GET /balanceControl` y `GET /balanceControl/<id>` `consumed_amount` = Σ `remission_amount` de las remisiones del control con `status != 3` y `available_amount = contracted_amount − consumed_amount`. Cancelar saca la remisión de la suma. Descartado insertar un AJUSTE (el contratado no cambió; doble conteo). Misma exclusión en el control de entregas |
| **Extensión de fecha fin** | **Mismo ledger `balance_control_movements`, extendido**: columnas anulables `previous_end_date` / `new_end_date` y tipo **`3 = VIGENCIA`** (solo fecha: `amount = 0`, `previous = resulting`). `POST /balanceControl/movement` acepta `new_end_date` junto o en lugar de `amount`: solo monto → INYECCION/AJUSTE como hoy; solo fecha → VIGENCIA; ambos → una fila INYECCION/AJUSTE que además trae las fechas. La fila actualiza `balance_controls.end_date` en el mismo `UPDATE` optimista. "Qué cambió" se deriva por fila (`amount != 0`, `new_end_date` presente, ambos); `movement_date` = fecha en que el cliente hizo el cambio, `timestamp` = cuándo se capturó. El `PUT` de cabecera **deja de aceptar `end_date`** (un solo escritor). Descartada tabla `balance_control_extensions` (dos listas que el front tendría que mezclar) |
| **Aviso "por vencer"** | El back agrega `days_to_end` (puede ser negativo) al listado y detalle de controles + filtro `?expiring_days=N` en `GET /balanceControl`. Sin correos |
| **Permisos** | `deliveryControl` lectura `administracion` + `purchases` (seguimiento de Luis Hurtado), escritura `administracion`. `PUT /remission/cancel`, movimiento con fecha y OCD: `administracion`. **`almacen` nunca** (el ingreso de material de Óscar sigue en su flujo de inventario; la remisión pasa por los permisos actuales de remisión). `operaciones` fuera por ahora → pendiente |
| **PDF "remisión en limpio" (FO-CXC-05)** | **Mismo endpoint** `GET /remission/download/pdf/<id>`: layout FO-CXC-05 **automático cuando `contract_id IS NULL`** (sin bloque de contrato, `No. PEDIDO EXIROS` prominente, moneda, `POS`, subtotal/IVA/total, "Firma Autorización 1/2"); con contrato, el layout de hoy. `?layout=ocd` / `?layout=contract` para forzar. Código/revisión desde `iso_formats` (seed FO-CXC-05 R0, vigencia 2023-05-11). `?full=1`, firmas y anexos igual que hoy. Skill `pdf-design`. Descartado endpoint aparte |
| **Análisis de costos** | **Tablas nuevas** `quotation_item_costs` (1:1 con `quotation_items.id`) + `quotation_item_supplier_quotes` (N por item) — decisión del usuario por volumen (evitar JSON gordo en `quotation_items.extra_info` y los `Out of sort memory` ya vistos). Primera etapa: **el usuario llena los datos**; segunda etapa (pendiente): sugerir desde análisis anteriores / items cotizados (`n_part`, descripción, `id_inventory`). `profit_pct` en **porcentaje** (30 = 30 %), el back calcula `unit_cost_mxn = unit_cost × exchange_rate` y `unit_price_profit = unit_cost_mxn × (1 + profit_pct/100)`; el front nunca manda factor. El item debe existir antes (cotización en borrador, `price_unit 0` → análisis → `apply_prices: true` escribe `price_unit`). El PDF al cliente **nunca** imprime costos; `GET /quotation/<id>?with_costs=1` los expone |
| **Fuera de este bloque** | Saldo comprometido / Control de Cotizaciones (FO-PRE-03): Carolina lo sigue en Excel, "posibilidad, no tarea" → pendiente con las columnas ya inventariadas. Licitaciones (FO-PRE-04): sin tarea. Evidencias de servicio: ya cubierto. Responsive de saldos (front), Cobranza en ambiente de prueba + lista de usuarios (ops; depende de los DDL de test/prod del 09-11 y 09-14), correos internos por SES (revisión aparte), notificación de correos recibidos (sin alcance): todos a `pendientes.md`, ninguno se construye aquí |
| **DDL** | Como siempre: un script en [`scripts_db_handle/`](../../scripts_db_handle/), **lo revisa/ejecuta el usuario**; ningún agente corre DDL |

## Modelo de datos (DDL de la F0 — `scripts_db_handle/control_entregas_ocd.sql`, esquema `sql_telintec_mod_admin`)

```
delivery_controls
  id_control        INT PK AUTO_INCREMENT
  quotation_id      INT NOT NULL            -> quotations(id)   (1 activo por cotización, validado en código; índice)
  client_id         INT NOT NULL            -> sql_telintec.customers_amc(id_customer) (copiado de la cotización)
  title             VARCHAR(255) NOT NULL   default: folio/quotation_code de la cotización
  client_po_number  VARCHAR(50)  NULL       copiado de metadata.client_po_number, editable
  currency          VARCHAR(3)   NOT NULL DEFAULT 'MXN'
  status            INT NOT NULL DEFAULT 0  0 abierto · 1 completo · 2 cancelado
  custom_fields     JSON NULL               [{key,label,value_type,comment}]
  created_by INT NULL · timestamp DATETIME NULL · history JSON NULL · extra_info JSON NULL

balance_control_movements (ALTER)
  + previous_end_date DATE NULL
  + new_end_date      DATE NULL
  (type gana el valor 3 = VIGENCIA; catálogo en Python)

quotation_item_costs                       (1 fila por item, 1:1)
  id_cost            INT PK AUTO_INCREMENT
  quotation_item_id  INT NOT NULL UNIQUE    -> quotation_items(id)  FK ON DELETE CASCADE
  quotation_id       INT NOT NULL           -> quotations(id)  (desnormalizado + índice: "todos los costos de X" sin pasar por items)
  currency           VARCHAR(3) NOT NULL DEFAULT 'MXN'   moneda del costo
  unit_cost          DECIMAL(15,4) NULL     precio unit. sin ganancia, en `currency`
  exchange_rate      DECIMAL(12,6) NULL     snapshot del tipo de cambio usado (la cabecera lo propone, la fila lo guarda)
  unit_cost_mxn      DECIMAL(15,4) NULL     calculado por el back
  profit_pct         DECIMAL(8,4)  NULL     porcentaje (30 = 30 %)
  unit_price_profit  DECIMAL(15,4) NULL     calculado por el back
  delivery_time      VARCHAR(100)  NULL     tiempo de entrega para el cliente
  service_months     INT           NULL     CISCO
  smart_account      TINYINT(1)    NULL     CISCO (NULL = no aplica)
  created_by · timestamp · history JSON · extra_info JSON

quotation_item_supplier_quotes             (N por item)
  id_quote           INT PK AUTO_INCREMENT
  quotation_item_id  INT NOT NULL           -> quotation_items(id)  FK ON DELETE CASCADE (índice)
  position           TINYINT NOT NULL DEFAULT 1        "Proveedor 1 / 2 / …"
  supplier_id        INT NULL               -> sql_telintec.suppliers_amc(id_supplier)
  supplier_name      VARCHAR(255) NULL      texto libre si no está en catálogo
  unit_price         DECIMAL(15,4) NULL
  currency           VARCHAR(3) NOT NULL DEFAULT 'MXN'
  delivery_time      VARCHAR(100) NULL
  comments           TEXT NULL
  is_selected        TINYINT(1) NOT NULL DEFAULT 0     el que alimenta unit_cost
  UNIQUE (quotation_item_id, position)

quotation_items (ALTER)
  + KEY idx_qi_n_part (n_part)             para la futura sugerencia de análisis anteriores

iso_formats (seed)
  FO-CXC-05 R0 "Remisión OC directas" (administracion, vigencia 2023-05-11, config NULL)
  FO-PRE-01 R2 "Cotización" (presales) · FO-PRE-02 R2 "Cotización CISCO" (presales)
```

Convenciones del repo: FKs "flojas" (columnas indexadas, bloque de FKs reales opcional al final, como en `control_saldos.sql`); `history`/`extra_info` JSON; enteros con catálogo en Python expuestos en `/catalogs`. Orden: dev → test → prod, **después** de que test/prod tengan `control_saldos.sql` y `control_saldos_sin_contrato.sql` (pendientes del 09-11 y 09-14). Ninguna columna nueva rompe el código viejo (todas NULL o tablas nuevas), así que el DDL queda desacoplado del deploy salvo F4, que lee las columnas de fecha.

## Fases y orden (dependencias)

| # | Bloque | Endpoints / piezas | Depende de |
|---|---|---|---|
| **F0** | DDL | `scripts_db_handle/control_entregas_ocd.sql` (todo lo de arriba) → revisión y ejecución del usuario en dev | — |
| **F1** | OCD | `document_type` / `client_po_number` / `currency` / `delivery_time` en `POST /quotation`; **`PUT /quotation/ocd`**; reglas de change order en `PUT` / `DELETE /quotation` (solo aplican con control activo, así que la validación real aterriza con F2) | F0 solo para el gate |
| **F2** | Control de Entregas | `POST /deliveryControl` · `GET /deliveryControl` (lista con progreso: % entregado, última entrega, status; filtros `client_id`, `status`, `quotation_id`) · `GET /deliveryControl/<id>` (cabecera + partidas pedido/entregado/pendiente en cantidad y monto + bloque "fuera de la orden" + remisiones folio/fecha/status/monto) · `PUT /deliveryControl` (title, client_po_number, status) · `PUT /deliveryControl/fields` · `PUT /deliveryControl/cancel` · `GET /deliveryControl/catalogs`; **400 de sobre-entrega** en `POST`/`PUT /remission`; el `GET /remission-<id>` expone `delivery_control_id` / `delivery_control_active` derivados | F1 |
| **F3** | Cancelación de remisión | `PUT /remission/cancel`; candados sobre canceladas; `consumed_amount` / `available_amount` en `GET /balanceControl*`; exclusión en F2 | F2 para la exclusión (el resto, independiente) |
| **F4** | Vigencia | `new_end_date` + tipo 3 en `POST /balanceControl/movement`; `PUT /balanceControl` deja de escribir `end_date`; `days_to_end` + `?expiring_days=` | F0 (columnas de fecha) |
| **F5** | PDF FO-CXC-05 | layout por `contract_id` en `GET /remission/download/pdf/<id>`, `?layout=`, código desde `iso_formats` | F0 (seed) |
| **F6** | Análisis de costos | `PUT /quotation/costAnalysis {id_quotation, exchange_rate, items:[{id, cost:{…}, suppliers:[…]}], apply_prices}` (upsert todo o nada); `GET /quotation/<id>?with_costs=1` con totales sin/con ganancia por item y por cotización; `apply_prices` escribe `price_unit` | F0 |

F3 y F4 no dependen de F1/F2; si Cobranza aprieta, pueden adelantarse. F6 es flujo de Preventa y puede correr en paralelo o al final. Cada fase: doc propio en `docs/` (4 capas tocadas + contrato del front + "Al modificar"), línea al final de su sección en `README.md`, ítem en `pendientes.md`, verificación contra dev con tester en `Tests/`.

## Contratos preliminares (los definitivos van en el doc de cada fase)

Base `/GUI/api/v1/admin/collections` (control de entregas, remisiones, saldos) y `/GUI/api/v1/admin/presales` (cotización, análisis de costos). Header `Authorization` con el **JWT crudo** (sin `Bearer `). Envelope `{data, msg, error}`.

- `PUT /quotation/ocd` → `{"id_quotation": 51, "client_po_number": "3716578048", "currency": "MXN", "approved_date": "2026-09-20"}` → 200 `{"id_quotation": 51, "document_type": "ocd"}`; 404 si no existe.
- `POST /deliveryControl` → `{"quotation_id": 51, "title": "OCD fibra óptica Guerrero", "custom_fields": []}` → 201 `{"id_control": 3}`; 400 si la cotización no es OCD; 409 si ya tiene control activo.
- `GET /deliveryControl/<id>` → `data: {header…, "items": [{"id": 900, "partida": 1, "description": "Fibra óptica…", "udm": "m", "ordered_qty": 20000, "delivered_qty": 15000, "pending_qty": 5000, "unit_price": 12.5, "ordered_amount": 250000, "delivered_amount": 187500}], "off_order_items": [...], "remissions": [{"id": 71, "folio": "TL-0045-001", "date": "2026-09-10", "status": 1, "amount": 187500}], "totals": {...}}`.
- `PUT /remission/cancel` → `{"id": 71, "reason": "El cliente indica que no corresponde"}` → 200; 400 si ya estaba cancelada.
- `POST /balanceControl/movement` con fecha → `{"id_control": 6, "type": 3, "new_end_date": "2026-11-30", "movement_date": "2026-09-22", "reason": "Extensión Ternium", "document": "Adenda 3"}` → 201 `{…, "previous_end_date": "2026-09-30", "new_end_date": "2026-11-30"}`; `type 1` con `amount` y `new_end_date` = ambos en una fila.
- `GET /balanceControl?expiring_days=30` → filas con `days_to_end`, `consumed_amount`, `available_amount`.
- `PUT /quotation/costAnalysis` → `{"id_quotation": 51, "exchange_rate": 18.25, "apply_prices": true, "items": [{"id": 900, "cost": {"currency": "USD", "unit_cost": 0.55, "profit_pct": 30, "delivery_time": "2 semanas"}, "suppliers": [{"position": 1, "supplier_id": 12, "unit_price": 0.55, "currency": "USD", "delivery_time": "10 días", "comments": "", "is_selected": true}]}]}` → 200 con los calculados por item.

## Pendientes que abre este plan

Ver [`pendientes.md`](../pendientes.md), secciones *Remisiones (admin/collections) → Control de Entregas / OCD* y *Contratos / Presales*.
