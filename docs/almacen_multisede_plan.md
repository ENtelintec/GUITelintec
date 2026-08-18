# Plan — Almacén multisede (sucursales con entradas/salidas)

> Plan por fases para soportar una **segunda sede de almacén** (y N a futuro): la sede principal sigue operando **tal cual** (catálogo, SMs, reservas, EPP, compras), y la sede nueva solo **genera entradas y salidas para actualizar su inventario**, recibe material enviado desde el principal y consulta. Decisiones cerradas en sesión de grill del 2026-08-15. **Nada de esto está implementado aún** — este doc es el diseño acordado; cada fase producirá su propio doc con "Contrato mínimo para el front" al implementarse.

## Decisiones acordadas

| Tema | Decisión |
|---|---|
| **Alcance sedes** | Catálogo genérico de sedes (tabla `warehouses_amc`); hoy se dan de alta 2 (principal + nueva), una tercera mañana es un INSERT |
| **Modelo de stock** | **Híbrido**: `products_amc.stock` sigue siendo el stock de la sede principal (los 6 sitios de escritura y todos los lectores quedan intactos); tabla nueva `warehouse_stock_amc (id_product, id_warehouse, stock)` **solo para sedes secundarias** |
| **Catálogo de productos** | Compartido (`products_amc`, mismos SKUs/`id_product`); la sede **no crea productos** — si llega material nuevo, el principal da de alta el SKU primero |
| **Kardex** | Un solo kardex: `ALTER TABLE product_movements_amc ADD id_warehouse INT NULL` (FK al catálogo; **NULL = sede principal**, cero backfill; los INSERTs existentes nombran columnas → no se tocan) |
| **Transferencias** | **Dos pasos con estado en tránsito** (tabla `warehouse_transfers_amc`): el principal registra el envío (genera SU salida, descuenta su stock) → la sede confirma recepción (genera SU entrada). Origen/destino genéricos en el modelo; **v1 solo valida origen = principal** |
| **Discrepancias** | La sede captura lo **realmente recibido** por item; el traslado guarda enviado vs recibido y cierra en `recibido con diferencias`. La diferencia **no se ajusta sola en ningún lado** — el principal la resuelve a mano viendo el traslado |
| **Recepción** | **Una sola confirmación por traslado** (envío en dos camiones = dos traslados); sin recepciones parciales acumulativas |
| **Movimientos de la sede** | Entradas libres + salidas libres (con `reference`, validación de no-negativo contra su stock) + **editar/borrar sus movimientos**. La entrada nacida de un traslado **no** es editable/borrable |
| **DELETE de movimiento** | **Arreglar en ambos lados**: el DELETE pasa a revertir stock (sede en `warehouse_stock_amc`, principal en `products_amc.stock` — cierra el gap conocido), validando no-negativo (400 si la reversa no alcanza). ⚠️ Cambia comportamiento actual del principal: **avisar a operación** (si hoy borran y ajustan a mano, el auto-revertir doble-corregiría) |
| **Permisos** | Permiso nuevo **por sede**: `App.Department.Sucursal-<id_warehouse>` (p.ej. `Sucursal-2`). Los endpoints de sede checan `department="sucursal"` (match substring existente) y el midleware valida que el permiso incluya el id de la sede pedida. **Restricción dura**: el nombre no puede contener `almacen` ni `administrator` (heredaría acceso por el match substring). El lado principal (traslados, consolidado) sigue bajo `almacen` |
| **Visibilidad** | El principal ve el stock de **todas** las sedes (consolidado por producto: principal + por sede + en tránsito). La sede ve **su** stock y además el del principal (solo lectura). Sede↔sede: no (sin transferencias entre sedes en v1) |
| **Endpoints** | **Namespace nuevo `GUI/api/v1/sucursal`** para el lado sede (patrón CDA: 4 capas nuevas + registro en `app.py`) + **rutas nuevas dentro de `rs_Almacen.py`** para el lado principal (`/transfer*`, `/warehouses`, `/inventory/consolidated`). Los endpoints actuales de `/almacen` no se tocan y siguen significando "sede principal" |
| **Alcance v1 sede** | Core (movimientos, recepción, inventario, ver principal) + **exports PDF/Excel** de su inventario/movimientos + **dashboard** de sus movimientos. Fuera: reservas, carga Excel, SMs/despacho (→ Pendientes) |
| **DDL** | Como siempre: script en [`scripts_db_handle/`](../scripts_db_handle/), **lo revisa/ejecuta el usuario** en las 3 BDs; ningún agente corre DDL. No hace falta vista puente: tablas nuevas + columna nueva NULL → el código viejo sigue funcionando, el DDL queda desacoplado del deploy |

## Modelo de datos (DDL de la Fase 0, esquema `sql_telintec`)

Las tablas nuevas van en `sql_telintec` (no en `mod_admin`): sus FKs apuntan a `products_amc`, que vive ahí — misma razón de localidad que mantuvo el núcleo compartido en su lugar en la migración RRHH.

- **`warehouses_amc`** — catálogo de sedes: `id_warehouse` PK AUTO_INCREMENT, `name`, `is_main` TINYINT (exactamente una fila en 1), `is_active` TINYINT default 1 (baja suave), `extra_info` JSON (dirección, encargado…). Seed: fila 1 = "Almacén Principal" (`is_main=1`), fila 2 = la sede nueva.
- **`warehouse_stock_amc`** — stock de sedes **secundarias** (el principal NO tiene filas aquí): `id_stock` PK, `id_product` FK→`products_amc`, `id_warehouse` FK→`warehouses_amc`, `stock` DECIMAL(14,4) default 0, `UNIQUE (id_product, id_warehouse)`. Se upsertea al primer movimiento del producto en la sede.
- **`warehouse_transfers_amc`** — traslados: `id_transfer` PK, `folio` (consecutivo `TRS-####`), `id_warehouse_origin` FK, `id_warehouse_dest` FK, `status` INT (0 en tránsito, 1 recibido, 2 recibido con diferencias, 3 cancelado), `items` JSON `[{id_product, quantity_sent, quantity_received (null hasta recibir), comment}]`, `comment`, `history` JSON (timestamp/user/acción — aquí vive quién envió y quién recibió, el kardex no tiene columna de usuario), `created_at`, `received_at` DATETIME NULL.
- **`ALTER TABLE product_movements_amc ADD COLUMN id_warehouse INT NULL`** + FK + índice. NULL = principal. En los movimientos ligados a traslado, `extra_info` lleva `{"reference": "<folio TRS>", "id_transfer": N}` — **con `JSON_SET`, no sobrescribir la columna** (la llave `reference` la consume la conciliación OC↔movimientos).

## Reglas de negocio

**Crear traslado** (`almacen`): valida stock del principal por item → inserta el transfer (status 0) → genera **una salida por item** en el kardex (id_warehouse NULL, reference = folio) → descuenta `products_amc.stock`. **Cancelar** (solo en status 0): entradas de reversa en el kardex del principal + reintegro de stock, status 3 (el material nunca se recibió; aquí sí es automático porque físicamente regresa/nunca salió).

**Recibir** (`sucursal-<dest>`): captura `quantity_received` por item (una sola vez) → entradas en el kardex con `id_warehouse = dest` y reference = folio → upsert-suma en `warehouse_stock_amc` → status 1 (exacto) o 2 (con diferencias) + `received_at` + history. Las entradas de traslado quedan **protegidas** contra PUT/DELETE del CRUD de la sede (se detectan por `extra_info.id_transfer`).

**Movimientos libres de sede**: POST valida no-negativo contra `warehouse_stock_amc`; PUT compensa por diferencia (patrón `previous_q` actual); DELETE revierte con validación no-negativo. Todo con `id_warehouse` de la sede, validado contra el permiso.

**Atomicidad**: `execute_sql` no da transacciones entre llamadas; un traslado son varias escrituras. Orden defensivo (transfer → movimientos → stock), y si algo falla a la mitad: reversa best-effort + detalle a `msg`/log/notificación — mismo patrón no-fatal que `sync_sm_deliveries_from_po`. No es peor que hoy: `insert_movement` ya hace lectura/escritura de stock no atómica.

## Candado sobre el código existente (Fase 1 — crítico)

En cuanto la sede escriba en el kardex compartido, **todas las lecturas actuales de `product_movements_amc` deben filtrar `id_warehouse IS NULL`** o empezarían a mezclar sedes: `get_all_movements`, `get_epp_movements`, exports (`create_file_movements_amc`), dashboard (`get_movements_type`), y la conciliación OC (`get_ins_db_detail` en el match de `MD_Purchases.py`). Es la única cirugía sobre código existente que exige el "el almacén actual sigue tal cual". **Al modificar**: cualquier query futura sobre el kardex debe decidir explícitamente qué sede(s) lee.

Notas de alcance que se mantienen: el chatbot/tools OpenAI y `available_stock` de SM siguen leyendo `products_amc.stock` → siguen significando "principal" (correcto: las SMs se despachan del principal). La conciliación OC v1 solo ve entradas del principal (entradas de sede por compra local → Pendientes).

## Endpoints

**Lado principal — rutas nuevas en [`rs_Almacen.py`](../templates/resources/rs_Almacen.py)** (permiso `almacen`; el CRUD del catálogo, `["administracion", "almacen"]`):

| Ruta | Método | Qué hace |
|---|---|---|
| `/warehouses` | GET | Catálogo de sedes |
| `/warehouse` | POST / PUT | Alta / edición / baja suave de sede |
| `/transfer` | POST | Crea traslado (items) → salidas + descuento en principal |
| `/transfer/cancel` | PUT | Cancela (solo en tránsito) → reversa automática al principal |
| `/transfers` | GET | Listado con filtros (status, sede destino, fechas) |
| `/transfer/<id>` | GET | Detalle enviado vs recibido |
| `/inventory/consolidated` | GET | Por producto: stock principal + por sede + en tránsito |

**Lado sede — namespace nuevo `GUI/api/v1/sucursal`** (`rs_Sucursal.py`; permiso `sucursal-<id>`, id de sede en el request validado contra el permiso — helper nuevo tipo `verify_warehouse_permission(data_token, id_warehouse)`):

| Ruta | Método | Qué hace |
|---|---|---|
| `/inventory` | GET | Su inventario (catálogo + stock de su sede) |
| `/inventory/main` | GET | Stock del principal (solo lectura) |
| `/movements/<type_m>` | GET | Su kardex |
| `/movement` | POST / PUT / DELETE | Entrada/salida libre; editar; borrar con reversa de stock |
| `/transfers` | GET | Traslados hacia su sede (en tránsito + históricos) |
| `/transfer/receive` | PUT | Confirma recepción (cantidades por item) |
| `/file/download/products/{pdf,excel}` | GET | Export de su inventario |
| `/file/download/movements/{pdf,excel}` | POST | Export de sus movimientos (fechas/tipo) |
| `/dashboard/movements` | POST | Gráfica de movimientos de su sede |

Capas nuevas del patrón CDA: `rs_Sucursal.py` + `MD_Sucursal.py` + controller `templates/controllers/product/warehouses_controller.py` + `static/Models/api_sucursal_models.py` + registro en `app.py` + `log_file_sucursal`. Todo con envelope `{data, msg, error}` desde el día 1.

## Fases

1. **Fase 0 — DDL + permiso**: script `scripts_db_handle/almacen_multisede.sql` (3 tablas + ALTER + seed de las 2 sedes) → revisión del usuario → corre en las **3 BDs** (dev/test/prod; `is_tester` comparte test entre versiones, pero columna NULL + tablas nuevas son inocuas para el código viejo). Alta de `App.Department.Sucursal-2` en [`permissions_models.json`](../static/permissions_models.json) — verificando por grep que ningún check existente sea substring de `sucursal-2` ni viceversa.
2. **Fase 1 — candado + catálogo**: filtro `id_warehouse IS NULL` en las 5 lecturas existentes del kardex; CRUD de `warehouses_amc`; `GET /inventory/consolidated`.
3. **Fase 2 — namespace `sucursal`**: movimientos libres (POST/PUT/DELETE con stock por sede), su inventario, ver principal.
4. **Fase 3 — traslados**: crear/cancelar/listar/detalle (lado `almacen`) + listar/recibir (lado `sucursal`), folio `TRS-####`.
5. **Fase 4 — extras + de paso**: exports y dashboard de sede (reusando generadores con filtro); **fix del DELETE del principal** (revertir stock) con aviso a operación.

Cada fase: smoke vs BD dev, `pyrefly check`, doc propio con "Contrato mínimo para el front", y actualización de [`pendientes.md`](pendientes.md). El inventario inicial de la sede nueva se captura como entradas libres o un traslado grande (no hay carga Excel de sede en v1).

## Contrato mínimo para el front (preliminar — el definitivo por fase)

- Auth: header `Authorization` con el **JWT crudo** (sin `Bearer`), como todo el API. Envelope `{data, msg, error}`; descargas = blob en 200 / envelope JSON en 4xx.
- El front de la sede consume **solo** el prefijo `GUI/api/v1/sucursal` + su `id_warehouse` (implícito en su permiso `Sucursal-<id>`); mandar un id de sede ajeno → 403.
- El front del principal gana pantallas: traslados (crear/cancelar/seguimiento con enviado-vs-recibido) y consolidado por producto; sus pantallas actuales no cambian de contrato.
- Estatus de traslado como **integer** (0 en tránsito, 1 recibido, 2 con diferencias, 3 cancelado) + catálogo en la respuesta o doc.

## Puntos clave a plantear a administración (requisitos del plan)

Cosas que **no son código** y que administración debe definir/autorizar antes o durante las fases:

1. **Datos de la sede nueva** para el seed del catálogo: nombre oficial, dirección, encargado (Fase 0).
2. **Personal y permisos**: quiénes operarán la sede → alta de sus usuarios con el permiso nuevo `Sucursal-2` (y confirmar que el personal del principal que gestionará traslados ya tiene `almacen`).
3. **Cambio de comportamiento en el principal**: el DELETE de un movimiento pasará a **revertir stock automáticamente** (hoy no lo hace). Si la operación actual borra y ajusta a mano, hay riesgo de doble corrección — avisar y acordar fecha del cambio (Fase 4).
4. **Procedimiento de discrepancias**: cuando un traslado llega incompleto/dañado, la diferencia **no se ajusta sola** — definir responsable y criterio en el principal para resolverla (reingreso vs merma).
5. **Inventario inicial de la sede**: decidir cómo se captura (un traslado grande desde el principal o entradas libres capturadas por la sede) y quién lo valida físicamente.
6. **Política de catálogo**: la sede no da de alta productos; definir el canal para que la sede solicite SKUs nuevos al principal.
7. **Alcance v1 asumido por operación**: las SMs se siguen despachando **solo** del principal; las compras locales de la sede entran como entradas libres **sin** conciliación contra OC.
8. **Ventana de DDL**: autorizar la corrida del script en las 3 BDs (dev/test/prod) — inocuo para el código viejo, pero es prod.
9. **Front**: se requieren pantallas nuevas (operación de sede + traslados/consolidado en el principal) — coordinar con quien lleve el front y su calendario.

## Pendientes (fuera de v1)

- **[back]** Reservas de stock en sedes; carga Excel de sede; SMs/despacho desde sede.
- **[back]** Transferencias sede→principal y sede↔sede (el modelo ya lo soporta; es quitar la validación de origen y definir quién confirma).
- **[back]** Conciliación OC↔movimientos considerando entradas de sede (compras locales).
- **[back]** Recepciones parciales múltiples por traslado (v1: una confirmación).
- **[back]** Columna de usuario en `product_movements_amc` (hoy la trazabilidad de persona vive solo en logs/history).
- **[back]** Edición de movimientos de sede por el principal (supervisión).
- **[front]** Pantallas: operación de sede (inventario/movimientos/recepción) y traslados+consolidado en el principal.
