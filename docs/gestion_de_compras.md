# Gestión de Compras (FO-COM-01 R3)

CRUD nuevo para la bitácora semanal de solicitudes de compra / gasto del formato
**FO-COM-01 R3** (una fila por solicitud: proveedor, descripción, clasificación,
solicitante, montos USD/MXN, estatus, aprobación de gerencia y columnas de
análisis). Vive en el área **admin/collections**, bajo la ruta
`/GUI/api/v1/admin/collections/purchaseManagement`.

Es un seguimiento **flojo** (no estricto): casi todos los campos son opcionales,
los enlaces a otras entidades son FK **anulables** y lo que no matchea contra la
BD se guarda como texto en `extra_info`.

## Las 4 capas

```
DDL      scripts_db_handle/gestion_de_compras.sql                      -> CREATE TABLE (se corre a mano en MySQL)
HTTP     rs_Admin_collections.py  /purchaseManagement*                 -> auth + *Form.from_json + midleware
modelos  api_purchase_management_models.py  PurchaseManagement*Form     -> validador (Form) + swagger (api.model)
mid      MD_PurchaseManagement.py  *_purchase_management_api            -> envelope {data,msg,error} + history + extra_info
db       purchases/purchase_management_controller.py  *_purchase_management -> SQL crudo vía execute_sql
```

- **DDL:** [`scripts_db_handle/gestion_de_compras.sql`](../scripts_db_handle/gestion_de_compras.sql)
- **HTTP:** [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py) (clases `PurchaseManagement*`)
- **Modelos/forms:** [`api_purchase_management_models.py`](../static/Models/api_purchase_management_models.py)
- **Midleware:** [`MD_PurchaseManagement.py`](../templates/resources/midleware/MD_PurchaseManagement.py)
- **Controller:** [`purchase_management_controller.py`](../templates/controllers/purchases/purchase_management_controller.py)

## La tabla `sql_telintec_mod_admin.purchase_management`

PK `id_pm` (autoincrement). Columnas base + dos JSON (`history`, `extra_info`).

Enlaces (FK **lógico**, anulable; texto crudo cuando no hay match -> `extra_info`):

| Columna | Referencia | Texto de respaldo (extra_info) |
| --- | --- | --- |
| `supplier_id` | `sql_telintec.suppliers_amc(id_supplier)` | `supplier_text` |
| `client_id` | `sql_telintec.customers_amc(id_customer)` | `client_text` |
| `contract_id` | `sql_telintec_mod_admin.contracts(id)` | `contract_text` / `department_text` |
| `po_id` | `sql_telintec_mod_admin.purchase_orders(id_order)` | `invoice_number` |

> Las FK reales (CONSTRAINT) vienen **comentadas** al final del `.sql`; por defecto
> son solo columnas INT con índice, igual que el resto del repo. `SOLICITANTE` **no**
> es FK: va como `requester_text` en `extra_info`.

Enteros con catálogo (mapeo código↔etiqueta en Python, expuesto en `/catalogs`):

- `classification` (CLASIFICACIÓN): `0 HERRAMIENTAS · 1 EPP · 2 INVERSION · 3 GASTOS · 4 REEMBOLSO · 5 CREDITO · 6 VIATICOS`
- `status` (ESTATUS, default `0`): `0 PENDIENTE · 1 PAGADO · 2 URGENTE · 3 POR_PAGAR · 4 PUEDE_ESPERAR`
- `debt_type` (DEUDA/GASTO/INVERSION): `0 DEUDA · 1 GASTO · 2 INVERSION`

Columnas de análisis (`profit_percentage`, `cost_ternium_iva`, `profit`) se guardan
**tal cual las captura el usuario**; el back no calcula nada. `approved`/`approval_date`
son campos planos (cualquiera con permiso los edita). Ciclo de vida: `is_active`
(1=activo, 0=cancelado suave) + borrado físico aparte.

`extra_info` (JSON) — llaves conocidas: `supplier_text`, `client_text`, `contract_text`,
`department_text`, `requester_text`, `invoice_number`, `income_date`, `bank_deposit`.
En los GET estas llaves se **aplanan** al nivel superior de la fila (además de venir
dentro de `extra_info`).

---

## Contrato mínimo para el front

**Base:** `/GUI/api/v1/admin/collections/purchaseManagement`
**Permiso:** `administracion` o `purchases` (cualquier permiso con substring
`administrator` también pasa).

**Auth header:** `Authorization` lleva el **JWT crudo, NO `Bearer <token>`**
(el back hace `jwt.decode` sobre el header tal cual, sin quitar prefijo).

**Content-type:** siempre JSON. Todas las respuestas usan el envelope
`{"data": ..., "msg": ..., "error": ...}`. En 2xx `error` es `null`; en 4xx `data`
es `null` y `error` trae el detalle (string o lista). No hay descargas de archivo en
este módulo.

### Endpoints

| Método | Ruta | Qué hace |
| --- | --- | --- |
| `GET` | `/purchaseManagement` | Lista con filtros (query params) |
| `GET` | `/purchaseManagement/<id_pm>` | Un registro |
| `POST` | `/purchaseManagement` | Crea |
| `PUT` | `/purchaseManagement` | Actualiza (**parcial**) |
| `PUT` | `/purchaseManagement/cancel` | Cancela (suave, recuperable) |
| `DELETE` | `/purchaseManagement` | Elimina (físico, irreversible) |
| `GET` | `/purchaseManagement/catalogs` | Etiquetas de los enteros |

### Cuerpo de escritura (POST / PUT)

Todos los campos son opcionales (en PUT solo se requiere el `id_pm`). Fechas como
string `"YYYY-MM-DD"`. Enteros de catálogo como número.

```jsonc
{
  "id_pm": 5,                       // SOLO en PUT / cancel / delete
  "request_date": "2026-07-20",     // FECHA DE SOLICITUD
  "description": "Compra de taladro",
  "classification": 0,              // 0..6
  "supplier_id": 12,                // FK suppliers_amc (o null)
  "supplier_text": "Ferretería X",  // si no hay FK -> extra_info
  "client_id": 3,                   // FK customers_amc (o null)
  "client_text": "Ternium",
  "contract_id": 8,                 // FK contracts (o null)
  "department_text": "Operaciones",
  "po_id": 44,                      // FK purchase_orders (o null)
  "invoice_number": "A-1234",
  "requester_text": "Juan Pérez",   // SOLICITANTE (texto)
  "amount_usd": 120.5,
  "amount_mxn": 2100.0,
  "status": 0,                      // 0..4
  "payment_date": "2026-07-25",
  "approved": 0,                    // 0/1
  "approval_date": "2026-07-24",    // auto = hoy si approved=1 y no lo mandas
  "comments": "Urgente para obra",
  "debt_type": 1,                   // 0..2
  "profit_percentage": 15.0,        // se guarda tal cual
  "cost_ternium_iva": 2436.0,
  "profit": 336.0,
  "income_date": "2026-07-26",
  "bank_deposit": "BASE-001"
}
```

**PUT es parcial:** solo se sobreescriben las llaves **presentes** en el JSON. Una
llave omitida conserva su valor actual; mandarla en `null` la **vacía** a propósito.
Aplica igual a las llaves de `extra_info`.

### Filtros del listado (GET `/purchaseManagement`)

Todos opcionales, como query params: `status` (int), `classification` (int),
`client_id` (int), `date_from` / `date_to` (`YYYY-MM-DD` sobre `request_date`),
`is_active` (`1`=activos [default], `0`=cancelados), `all` (`1` -> todos, ignora
`is_active`). Orden: `request_date DESC, id_pm DESC`.

### Ejemplos de respuesta

`POST` -> **201**
```json
{ "data": { "id_pm": 5 }, "msg": "Registro de gestión de compras creado correctamente (ID 5)", "error": null }
```

`GET /purchaseManagement` -> **200** (cada fila trae columnas + llaves de extra_info aplanadas + `history` + `extra_info`)
```json
{
  "data": [
    {
      "id_pm": 5, "timestamp": "2026-07-24T12:00:00", "created_by": 17,
      "request_date": "2026-07-20", "description": "Compra de taladro",
      "classification": 0, "supplier_id": 12, "client_id": 3, "contract_id": 8,
      "po_id": 44, "amount_usd": 120.5, "amount_mxn": 2100.0, "status": 0,
      "payment_date": null, "approved": 0, "approval_date": null,
      "comments": "Urgente para obra", "debt_type": 1, "profit_percentage": 15.0,
      "cost_ternium_iva": 2436.0, "profit": 336.0, "is_active": 1,
      "history": [ { "user": 17, "action": "Creación", "date": "2026-07-24 12:00:00", "comment": "..." } ],
      "extra_info": { "supplier_text": "Ferretería X", "client_text": "Ternium", "requester_text": "Juan Pérez", "invoice_number": "A-1234" },
      "supplier_text": "Ferretería X", "client_text": "Ternium", "contract_text": null,
      "department_text": "Operaciones", "requester_text": "Juan Pérez",
      "invoice_number": "A-1234", "income_date": null, "bank_deposit": null
    }
  ],
  "msg": "1 registros", "error": null
}
```

`PUT` -> **200** `{ "data": { "id_pm": 5 }, "msg": "... actualizado correctamente (ID 5)", "error": null }`
`PUT /purchaseManagement/cancel` -> **200** `{ "data": { "id_pm": 5 }, "msg": "... cancelado (ID 5)", "error": null }`
`DELETE` -> **200** `{ "data": { "id_pm": 5 }, "msg": "... eliminado (ID 5)", "error": null }`

`GET /purchaseManagement/catalogs` -> **200**
```json
{
  "data": {
    "classification": [ { "code": 0, "label": "HERRAMIENTAS" }, { "code": 1, "label": "EPP" }, "..." ],
    "status": [ { "code": 0, "label": "PENDIENTE" }, "..." ],
    "debt_type": [ { "code": 0, "label": "DEUDA" }, { "code": 1, "label": "GASTO" }, { "code": 2, "label": "INVERSION" } ]
  },
  "msg": "ok", "error": null
}
```

**Errores comunes:**
- **401** `{ "error": "No autorizado. Token invalido" }` — token inválido / sin permiso.
- **400** `{ "data": null, "msg": "Estructura de datos inválida", "error": { "amount_usd": ["..."] } }` — falla WTForms.
- **400** `{ "data": null, "msg": "Valor de catálogo inválido", "error": ["status=9 no es un valor valido [0, 1, 2, 3, 4]"] }` — entero fuera de catálogo.
- **404** `{ "data": null, "msg": "No existe el registro (ID 5)", "error": "No encontrado" }` — PUT/cancel/delete/detalle sobre id inexistente.

**Gotchas:**
- `Authorization` = JWT **crudo** (sin `Bearer`).
- Enteros de catálogo: pide las etiquetas a `/catalogs` (no las hardcodees).
- FK anulables: si el cliente/proveedor/contrato/OC no está en la BD, deja el `*_id`
  en `null` y manda el texto (`client_text`, etc.); el GET te lo devuelve aplanado.
- **Cancelar** ≠ **eliminar**: `cancel` es reversible (oculta con `is_active=0`),
  `DELETE` borra la fila para siempre. El listado por defecto solo muestra activos.
- `approval_date` se auto-sella a hoy si mandas `approved=1` sin fecha.

---

## Al modificar

- **Agregar un campo:** si es columna base, tócala en las **5** piezas — `.sql`
  (`ALTER TABLE`), el `INSERT`/`UPDATE`/`SELECT_COLUMNS` del controller, el `row`/merge
  del midleware, y **ambos** (api.model + WTForms Form) en los modelos. Si es un campo
  suelto, mételo a `extra_info`: basta agregar la llave a `PM_EXTRA_KEY_MAP` y su
  `StringField`/`fields.String` en el modelo — sin DDL.
- **Agregar un valor de catálogo:** edita el dict correspondiente (`PM_CLASSIFICATION`
  / `PM_STATUS` / `PM_DEBT_TYPE`) en `MD_PurchaseManagement.py`; `/catalogs` y la
  validación se actualizan solos.
- **`SELECT_COLUMNS` es la fuente del mapeo tupla→dict** del GET: si cambias el orden
  o las columnas del SELECT, actualiza esa tupla en el controller (el midleware mapea
  por índice contra ella).
- **PUT parcial** depende de `raw_payload` (= `ns.payload`): el midleware compara
  `col in raw_payload` para saber qué mandó el front. No lo cambies por `validator.data`
  o perderás la distinción "no enviado" vs "enviado en null".
