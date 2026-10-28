# Permisos exactos en Administración: Cobranza, Preventa y BD — `/admin/collections/*` · `/admin/presales/*` · `/admin/db/*`

> `P-198`, última área (2026-10-28), con el mismo patrón de [`permisos_compras_y_baja.md`](permisos_compras_y_baja.md) y [`permisos_rrhh_bitacoras_cda_comun.md`](permisos_rrhh_bitacoras_cda_comun.md). Las **84 llamadas** de los tres namespaces que seguían con `department=` (comparación por subcadena) pasan a `permissions=[...]` (nombre exacto del catálogo); Compras ya estaba migrado. Con esto ningún endpoint del API usa `department=`, salvo dos que siguen así a propósito: `/sucursal` (puerta de sede, [`permisos_almacen.md`](permisos_almacen.md)) y `/UserSystem` con `credentials` (`P-188`).
>
> **Decisión del usuario (2026-10-28): separar Cobranza de Preventa.** Hay dos permisos nuevos, `adminCobranza` y `adminPreventa`, que se dan de alta en el catálogo (`P-207`, T6 de [`gui_system_tareas.md`](gui_system_tareas.md)). Además se ligan `adminRem` y `adminDB` (D14 de [`permisos_plan.md`](permisos_plan.md)). `Administracion` sigue abriendo todo, así que nadie del catálogo pierde acceso.

## Decisiones (grill del 2026-10-28)

| Decisión | Resultado |
|---|---|
| Permisos nuevos | `App.Department.adminCobranza` y `App.Department.adminPreventa`, con el estilo de `adminCompras`. |
| `adminCobranza` | Remisiones, control de saldos y control de entregas. |
| `adminRem` | Solo remisiones: crear, editar, cancelar, anexos, PDF, ver y "sin anexos"; también la cotización de actividad, que alimenta la remisión. Lee el control de entregas porque sus pantallas lo consultan; no toca saldos. |
| `adminPreventa` | Cotizaciones (incluidas CISCO y OCD), folio sugerido, análisis de costos, comparación, licitaciones. |
| `adminDB` | Contratos, clientes, proveedores y jefes de departamento. |
| Catálogos compartidos | Los leen los cinco (`Administracion` y los cuatro de arriba): lista y detalle de cotizaciones/OCD, contrato, productos de contratos, proveedores y clientes. Escribir sigue siendo de cada uno. Constante `ADMIN_CATALOG_READERS` en [`Functions_midleware_admin.py`](../templates/resources/midleware/Functions_midleware_admin.py). |
| Avisos diarios (`P-155`) | Los de saldos y entregas llegan a `administracion` **y** a `admincobranza`. |
| Otras áreas | Conservan lo que ya leían: `Operaciones` (remisiones, anexos, tabla de control, saldos en lectura, jefes), `SGI` (catálogo de saldos), `RRHH`, `Bitacoras`, `ALMACEN`/`ALMACEN-VISUAL`, `SM`/`SM-URGENT`. |

**Quién deja de entrar** (la subcadena los dejaba pasar): `DemoRRHH` y `DemoALMACEN`, que están fuera del catálogo y se quitan con `P-196`. También los cuatro permisos granulares de SM (`smControl`, `smCreate`, `smDespachar`, `smEntregasAdmin`) en 6 lecturas que pedían `"sm"`; es coherente con [`permisos_sm.md`](permisos_sm.md), donde no abren nada (`P-199`). En dev y test ningún usuario tiene un granular de SM sin `SM`, `SM-URGENT` o `Administracion`.

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py) | `_COBRANZA`, `_REM`, `_REM_OPS`. `_BC_READ`, `_BC_WRITE`, `_BC_CATALOGS`, `_DC_READ` y `_DC_WRITE` pasan a nombres del catálogo. 36 llamadas. |
| | [`rs_Admin_presales.py`](../templates/resources/rs_Admin_presales.py) | `_PREVENTA`, `_DB`, `_SM_READ`, `_SM_FOLIO`, `_ABBREVIATIONS_READ` y `_CONTRACT_PRODUCTS_READ`. 32 llamadas. |
| | [`rs_Admin_DB.py`](../templates/resources/rs_Admin_DB.py) | `_DB`, `_SM_READ`, `_CLIENTS_READ`, `_HEADS_WRITE`, `_HEADS_LIST_READ` y `_HEADS_READ`. 16 llamadas. |
| **Orquestación** | [`Functions_midleware_admin.py`](../templates/resources/midleware/Functions_midleware_admin.py) | `ADMIN_CATALOG_READERS` (nueva). |
| | [`MD_BalanceAlerts.py`](../templates/resources/midleware/MD_BalanceAlerts.py) | `PERM_BALANCE = ["administracion", "admincobranza"]`. |
| **DB** | [`permissions_admin_cobranza_preventa.sql`](../scripts_db_handle/permissions_admin_cobranza_preventa.sql) | Alta de los dos permisos en `sql_telintec.permissions` (ids 33 y 34; re-ejecutable). Lo corre el usuario (`P-207`). |
| **Modelos** | — | Sin cambios. |

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`; `jwt.decode` sobre el header tal cual). Sin el permiso → `401` con `{"error": "No autorizado. Token invalido"}`. Request y respuestas no cambian.
- **Permisos exactos** (nombres completos; `App.Department.Administrator` siempre pasa). Abajo, **Adm** = `App.Department.Administracion` y **Catálogos** = Adm + `adminCobranza` + `adminPreventa` + `adminRem` + `adminDB`.

### `/GUI/api/v1/admin/collections` (Cobranza; Compras sin cambio)

| Endpoints | Permisos |
|---|---|
| `POST·PUT·DELETE /remission`, `PUT /remission/cancel`, `PUT /remission/noAttachments`, `GET /remission/download/pdf/<id>`, `PUT /activity/ChangeStatus` | Adm, `adminCobranza`, `adminRem` |
| `GET /remission-<id>`, `POST·PUT /remissionControlTable`, `POST·DELETE /remission/attachment-<id>`, `POST·PUT·DELETE /activity/quotation`, `GET /activity/quotations-<id>` | Adm, `adminCobranza`, `adminRem`, `Operaciones` |
| `POST·PUT /balanceControl`, `PUT /balanceControl/{fields,remissions,cancel}`, `POST·PUT /balanceControl/movement`, `PUT /remissionBalance` | Adm, `adminCobranza` |
| `GET /balanceControl`, `GET /balanceControl/<id>` | Adm, `adminCobranza`, `Operaciones` |
| `GET /balanceControl/catalogs` | Adm, `adminCobranza`, `Operaciones`, `SGI` |
| `GET /deliveryControl`, `GET /deliveryControl/<id>`, `GET /deliveryControl/catalogs` | Adm, `adminCobranza`, `adminRem` |
| `POST·PUT /deliveryControl`, `PUT /deliveryControl/{fields,values,remissions,cancel}` | Adm, `adminCobranza` |

### `/GUI/api/v1/admin/presales`

| Endpoints | Permisos |
|---|---|
| `POST·PUT·DELETE /quotation`, `POST /quotation/products/upload`, `POST /quotation/items/file`, `GET /quotation/folio`, `PUT /quotation/ocd`, `PUT /quotation/costAnalysis`, `GET /quotation/costAnalysis/suggest`, `GET·POST·PUT /quotation/cisco…` (incluye el PDF), `GET /tenders`, `GET /tender/<id>`, `POST·PUT /tender`, `PUT /tender/items`, `POST /compare` | Adm, `adminPreventa` |
| `POST·PUT·DELETE /contract`, `POST /contract/settings`, `POST /contract/review/products/upload`, `POST /contract/items/file` | Adm, `adminDB` |
| `GET /quotation/<id>` (lista con `-1` y detalle), `GET /contract/<id>`, `GET /contracts/products` | Catálogos |
| `GET /contracts/abreviations` | Catálogos, `RRHH`, `Operaciones`, `SM`, `SM-URGENT` |
| `GET /products/contracts` | Catálogos, `Operaciones`, `SM`, `SM-URGENT` |
| `GET /folio/ternium`, `GET /folio/cotfc` | Adm, `ALMACEN`, `ALMACEN-VISUAL`, `SM`, `SM-URGENT` |

### `/GUI/api/v1/admin/db`

| Endpoints | Permisos |
|---|---|
| `POST·PUT·DELETE /client`, `POST·PUT·DELETE /supplier`, `POST /extraInfoSupplier`, `POST /suppliers/items/file` | Adm, `adminDB` |
| `GET /suppliers/allSuppliers` | Catálogos, `ALMACEN`, `ALMACEN-VISUAL` |
| `GET /suppliers/items-<id>` | Catálogos |
| `GET /clients/allClients` | Catálogos, `SM`, `SM-URGENT` |
| `GET /heads` | Catálogos, `Operaciones`, `RRHH` |
| `POST·PUT·DELETE /head` | Adm, `adminDB`, `Operaciones`, `RRHH` |
| `GET /heads/<id_d>` | Catálogos, `Operaciones`, `RRHH`, `ALMACEN`, `ALMACEN-VISUAL`, `Bitacoras`, `SM`, `SM-URGENT` |

```json
// 401: por ejemplo, un usuario solo con adminPreventa en POST /admin/collections/remission
{"error": "No autorizado. Token invalido"}
```

**Gotchas**:

- **`adminCobranza` y `adminPreventa` ya están en el catálogo** (`P-207`, ids 33 y 34). Quien no los tenga asignados sigue entrando con `Administracion`.
- **El front cierra hoy todo Administración, Cobranza y Preventa** a `Administrator` y `Administracion` en `route-permissions.ts`. Un usuario solo con `adminCobranza`, `adminPreventa`, `adminRem` o `adminDB` no verá sus pantallas hasta `P-208`.
- **Los avisos diarios** llegan a quien tenga `adminCobranza`: el lector de notificaciones cruza la etiqueta `admincobranza` con el nombre del permiso en minúsculas.

## Hallazgos (`P-209`)

- **Cotización de actividad desde Líderes.** Resuelto el 2026-10-28 (ver Notas posteriores): `Operaciones` ya abre `/admin/collections/activity/quotation*`.
- **Lista de proveedores desde Almacén.** Resuelto el 2026-10-28: el catálogo de proveedores de almacén (`almacen/proveedores`) llama a `GET /admin/db/suppliers/allSuppliers`, que ya abre a `ALMACEN` y `ALMACEN-VISUAL`. El alta de proveedor sigue cerrada a Administración.
- **Lista de proveedores desde SM, Compras y EPP (abierto).** Esas pantallas (`sm/PurchaseOrderMultiForm`, `purchases/CreatePOApplicationForm`, `almacen_epp/inventario_epp`) llaman a la ruta de almacén, `GET /almacen/inventory/suppliers/allSuppliers`, que solo abre a `ALMACEN` y `ALMACEN-VISUAL`. Sin uno de esos dos, reciben 401.
- **Rutas que el front llama y el API no tiene (abierto).** `/activity/report*` no existe en el API.

## Verificación

Dev (2026-10-28):

- **`Tests/tester_permisos_administracion.py`: 53/53.**
  - Compara la regla vieja (`department=` leído de `git HEAD`) contra la nueva en los 109 endpoints de los 3 namespaces (Compras incluido) y 59 permisos: el catálogo, los dos nuevos y los permisos reales de los usuarios de dev y test.
  - **Ganan acceso solo** `adminCobranza` (46 endpoints), `adminPreventa` (29), `adminRem` (29) y `adminDB` (27). **Pierden solo** `DemoRRHH` (6), `DemoALMACEN` (3) y los cuatro granulares de SM (6 lecturas cada uno).
  - 40 casos de reparto pasan; por ejemplo, `adminRem` no toca saldos, `adminPreventa` no crea remisiones ni contratos y `adminDB` no edita cotizaciones.
  - La matriz HTTP con los midleware en stub (109 endpoints × 15 permisos) no tiene diferencias contra el cálculo.
  - Avisos: `PERM_BALANCE` incluye `admincobranza`. El `REGEXP` del lector en MySQL lo encuentra para `adminCobranza` y `Administracion`, y no para `adminRem`.
- **Regresión contra la BD de dev, todo en verde:**
  - permisos y Compras: permisos de Compras 113/113, forms de Compras 29/29;
  - cotizaciones y licitaciones: licitaciones 61/61, OCD 35/35, reglas OCD 40/40, folio 32/32, CISCO 46/46, costos 37/37, sugerencias 22/22, metadata de cotización 18/18;
  - control de entregas: 71/71, vencimiento 26/26;
  - avisos 35/35;
  - control de saldos: vigencia 30/30, movimientos 31/31 y 34/34, sin contrato 50/50;
  - remisiones: cancelación 32/32, sin anexos 25/25, anexos 19/19;
  - formatos ISO 48/48.
- **Testers ajustados:**
  - `tester_balance_alerts` filtra los avisos por los dos destinatarios.
  - `tester_delivery_control` esperaba 200 para un token `App.Department.Purchases`. Esa expectativa estaba vieja desde el 2026-10-27, cuando `purchases` salió de `_DC_READ` (D13), así que ahora espera 401.
- `pyrefly check --python-version 3.11`: 166 errores, sin cambio.

## Al modificar

- Un endpoint nuevo de Administración usa la constante de su grupo. Una lectura que sirva a varias pantallas va con `ADMIN_CATALOG_READERS`.
- Un permiso nuevo se da de alta primero en el catálogo, desde la app de usuarios.
- Si un aviso nuevo es de Cobranza, se manda a `PERM_BALANCE`. Las etiquetas van en minúsculas y el lector las busca por `REGEXP`, así que no conviene usar una que sea subcadena de otra.

## Notas posteriores

- **2026-10-28 — `P-209`, decisión del usuario.** Cambios:
  - `Operaciones` abre la cotización de actividad, que usan las pantallas de Líderes: `POST·PUT·DELETE /activity/quotation` y `GET /activity/quotations-<id>`, con `_REM_OPS`. `PUT /activity/ChangeStatus` sigue sin abrirle, porque el front no lo llama desde Líderes.
  - `ALMACEN` y `ALMACEN-VISUAL` leen `GET /admin/db/suppliers/allSuppliers` (`_SUPPLIERS_LIST_READ` en [`rs_Admin_DB.py`](../templates/resources/rs_Admin_DB.py)). No reciben escrituras de proveedores ni `GET /suppliers/items-<id>`.
  - `P-207` está hecho: los dos permisos están en el catálogo de dev y test (ids 33 y 34), y el usuario los dio de alta.
  - **Verificación:** `Tests/tester_permisos_administracion.py` da 69/69.
    - Contra el commit anterior a `P-198`, ganan los cuatro de Administración más los de `P-209`, solo en sus endpoints.
    - Contra `HEAD` ganan exactamente `Operaciones` (4 endpoints), `ALMACEN` (1) y `ALMACEN-VISUAL` (1), y nadie pierde.
    - Hay 6 casos nuevos: `ChangeStatus`, el alta de proveedor, `items-<id>` y `Epp` siguen con 401.
  - pyrefly: 166 errores, sin cambio.
