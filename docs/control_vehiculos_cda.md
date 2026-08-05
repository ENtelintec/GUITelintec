# Control de Estado de Vehículos (FO-CDA-02 R3) — módulo CDA

> Namespace **nuevo** `GUI/api/v1/cda` (Control De Activos; los autos son el primer activo, otros se agregarán bajo el mismo namespace). Reemplaza el Excel FO-CDA-02 R3 (8 hojas). **Todo campo calculado del Excel lo computa el back en los GET, nunca se almacena**: próximo mantenimiento (km/fecha), ¿requiere mantenimiento?, días restantes, KPIs, refrendo AL DIA/Vencido, llanta vencida, pagos vencidos de póliza, TOTAL de compras y semana del año.

## Modelo de datos

DDL a mano en [`scripts_db_handle/control_vehiculos.sql`](../scripts_db_handle/control_vehiculos.sql) (sin sistema de migraciones), esquema `sql_telintec_mod_admin`:

| Tabla | Rol | Puntos clave |
|---|---|---|
| `vehicles` | Maestro | `code` **UNIQUE** (TEL-XXX); catálogos `status`/`oil_type`; `current_km`+fecha; medidas rin/llanta; `refrendo_last_paid` (el estatus se **deriva**); `accessories` JSON (12 llaves 0/1); `is_active` (baja suave) |
| `vehicle_policies` | Hija, historial | Renovación = **fila nueva** (no se pisa); `payments` JSON con slots derivados de `payment_form` (12/4/1); `inciso`/`notification` texto libre |
| `vehicle_services` | Hija, historial | Mantenimientos + reparaciones + servicios en **una** tabla (`service_type`); registrar km mayor **auto-actualiza** el odómetro del vehículo |
| `vehicle_tires` | Hija | **UNIQUE (vehicle_id, position)**, 5 posiciones fijas; upsert en sitio + cambios en `history` JSON |
| `vehicle_fines` | Hija | (year, month 1..12) + monto/desc/responsable; **varias por mes permitidas** (el Excel no podía) |
| `vehicle_purchases` | Hija | `status` catálogo; `po_id` enlace **flojo** (sin constraint ni lógica); TOTAL y semana derivados |

Todas las hijas con `FK ... ON DELETE CASCADE`: el `DELETE` físico del vehículo se lleva su historial; el camino normal es la baja suave.

## Reglas de negocio (constantes en `MD_CDA.py`, no configurables)

- **Mantenimiento**: próximo km = km del último mantenimiento + **5,000** (aceite mineral) / **10,000** (sintético, según `oil_type` del vehículo); próxima fecha = última + **6 meses**; *requiere* = km actual ≥ próximo km **o** fecha vencida; sin mantenimiento registrado → requiere por definición.
- **Pólizas**: slots de pago = MENSUAL 12 / TRIMESTRAL 4 / ANUAL 1 / CONTADO 1; `expected_date` del pago n = `date_start` + (n−1)×período; `overdue` = no pagado y fecha esperada < hoy.
- **Refrendo**: `AL_DIA` si `refrendo_last_paid` cae en el año consultado o después; `VENCIDO` si es anterior; `SIN_REGISTRO` si nulo.
- **Llantas**: `expired` = `expiry_date` < hoy (derivado); `needs_change` lo captura el usuario.
- **Compras**: `total` = `quantity × cost`; `week`/`week_year` = ISO week de `created_at`.

## Las 4 capas

| Capa | Archivo |
|---|---|
| HTTP | [`templates/resources/rs_CDA.py`](../templates/resources/rs_CDA.py) (**nuevo**, registrado en [`app.py`](../app.py)) |
| Orquestación | [`templates/resources/midleware/MD_CDA.py`](../templates/resources/midleware/MD_CDA.py) (**nuevo**) — CRUD + vistas + reglas |
| DB | [`templates/controllers/vehicles/vehicles_controller.py`](../templates/controllers/vehicles/vehicles_controller.py) (**nuevo**, dominio `vehicles/`) |
| Modelos | [`static/Models/api_cda_models.py`](../static/Models/api_cda_models.py) (**nuevo**) — api.model + WTForms |

Además: `log_file_cda` en [`static/constants.py`](../static/constants.py) (logs en `files/logs/cda_log_<fecha>.txt`).

---

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)**. Departamentos: `administracion` o `sgi` (o `administrator`).
**Base:** `/GUI/api/v1/cda` · **Envelope:** `{data, msg, error}` siempre.
**PUT = parcial**: solo se sobreescriben las llaves **presentes en el JSON**; mandar `null` explícito vacía el campo. Convención de ids: cada entidad acepta `id_<entidad>` (o `id`).

### Catálogos — `GET /catalogs`
```jsonc
{ "data": { "vehicle_status": [{"code":0,"label":"ACTIVO"},{"code":1,"label":"DETENIDO"},{"code":2,"label":"BAJA"}],
            "oil_type": [...], "payment_form": [...], "service_type": [...],
            "tire_position": [...], "purchase_status": [...],
            "accessory_keys": ["torreta_ambar","luces","sticker_acceso","eslinga_matracas","topes_bloqueo","extintor","gato","llave_cruz","triangulo","limpiaparabrisas","llanta_repuesto","cables_corriente"],
            "rules": { "oil_interval_km": {"MINERAL":5000,"SINTETICO":10000}, "maintenance_interval_months": 6,
                       "payment_slots": {"MENSUAL":12,"TRIMESTRAL":4,"ANUAL":1,"CONTADO":1} } },
  "msg": "ok", "error": null }
```

### Vehículos
- `GET /vehicles?status=&is_active=&all=` — lista. Default **solo activos**; `all=1` incluye bajas; `is_active=0` solo bajas. Cada fila trae labels (`status_label`, `oil_type_label`), `accessories` normalizado (las 12 llaves siempre presentes, 0/1), `refrendo_status` derivado.
- `GET /vehicle/<id>` — detalle: vehículo + `policies` (historial completo) + `tires`.
- `POST /vehicle` — `{"code":"TEL-017","model":"...","plate":"...","brand":"...","niv":"...","oil_type":0,"current_km":10000,"accessories":{"extintor":1}}` → `201 {"data":{"id_vehicle":N}}`. Código duplicado → `400` con msg "Ya existe un vehículo con el código ...".
- `PUT /vehicle` — parcial: `{"id_vehicle":N, "current_km":12500}` toca **solo** `current_km`.
- `PUT /vehicle/cancel` — `{"id_vehicle":N, "comment":"..."}` baja suave (idempotente).
- `DELETE /vehicle` — `{"id_vehicle":N}` físico, **borra todo el historial en cascada**.

### Pólizas — `POST|PUT|DELETE /policy`
POST: `{"vehicle_id":N,"inciso":"...","insurer":"...","date_start":"2026-01-15","date_end":"2027-01-15","payment_form":1,"payments":[{"n":1,"date":"2026-01-15","amount":2500,"paid":1}]}`. Los `payments` se **normalizan a los slots** de la forma de pago (los que no mandes quedan `{date:null,amount:null,paid:0}`). **Renovación = POST nuevo** (no PUT sobre la vieja); la vigente por vehículo es la de `date_end` más reciente activa.

### Servicios — `POST|PUT|DELETE /service`
POST: `{"vehicle_id":N,"service_type":0,"date":"2026-03-01","description":"...","km":11000,"workshop":"...","cost":1800.5}`. Un `km` mayor al actual del vehículo **actualiza su odómetro automáticamente** (no mandar dos requests).

### Llantas — `PUT /tire` (upsert) · `DELETE /tire`
`PUT {"vehicle_id":N,"position":0,"brand":"...","dot":"...","expiry_date":"...","physical_state":"texto libre","needs_change":1}` → `201` si la posición no existía, `200` si actualizó (cambios quedan en `history`). DELETE por `id_tire` **o** `{vehicle_id, position}`.

### Multas — `POST|PUT|DELETE /fine`
POST: `{"vehicle_id":N,"year":2026,"month":3,"amount":1500,"description":"...","responsible":"..."}`; `month` fuera de 1..12 → 400.

### Compras — `POST|PUT|DELETE /purchase`
POST: `{"vehicle_id":N,"problem":"...","quantity":2,"unit":"PZA","cost":150,"supplier":"...","checklist_sent":1}`. `cost` es **unitario**. El ítem "sale de la lista" con `PUT {"id_purchase":N,"status":1}` (comprado), no borrándolo.

### Vistas (las hojas del Excel) — solo GET
| Endpoint | Hoja | `data` |
|---|---|---|
| `GET /view/policies` | Control de Pólizas | lista por vehículo con `policy` (la vigente; `null` si no tiene) y `payments[]` con `expected_date`/`overdue` calculados |
| `GET /view/maintenance` | C.Mantenimientos | `{vehicles:[{last_maintenance, next_maintenance:{date,km}, requires_maintenance, days_remaining, maintained_last_6_months, ...}], kpis:{vehicles_in_control, pending_maintenance, pct_maintained_last_6_months}}` |
| `GET /view/services?vehicle_id=&service_type=&date_from=&date_to=` | Rep. y Serv. | `{services:[...con code/model/plate y service_type_label], total_cost}` |
| `GET /view/tires` | Sta.Llantas | por vehículo **siempre 5 posiciones** (vacías con `id:null`), `expired` derivado |
| `GET /view/refrendos?year=` | Refrendos | `{year, vehicles:[{refrendo_status, fines_by_month:{"1":[...],...,"12":[...]}, fines_total}], fines_grand_total}` |
| `GET /view/purchases?status=&vehicle_id=&date_from=&date_to=` | Pendiente de Compra | `{purchases:[...con total, week, week_year, code], total_pending}` (suma de pendientes) |

**Gotchas:**
- `days_remaining` puede ser **negativo** (ya vencido) y `null` sin mantenimiento registrado; `requires_maintenance` es `true` para vehículos sin ningún mantenimiento.
- `refrendo_status` ∈ `AL_DIA | VENCIDO | SIN_REGISTRO` (tres valores, no dos).
- En `/view/policies`, `policy` es `null` para vehículos sin póliza — renderizar defensivamente.
- Las llaves de `fines_by_month` son **strings** `"1".."12"` (JSON).
- Query params truthy: `all=1|true|yes`.

---

## Verificación
Sin framework de tests (gitignored): ciclo de vida completo corrido contra la **BD dev** con el token de `test.py` — alta (201) / código duplicado (400) / PUT parcial (campo único, resto intacto) / póliza trimestral con 4 slots y `overdue` correcto / fórmulas de mantenimiento (próximo = 11,000+5,000 km y +6 meses, días restantes, KPIs) / auto-update de odómetro desde reparación / upsert de llanta ×2 con `history.changes` y `expired` / multa + refrendo `SIN_REGISTRO→AL_DIA` / compra con total y semana / cancel suave (fuera del listado default) / DELETE físico con cascade (404 después). BD dev limpia al terminar. Pyrefly 0 errores en las 5 capas.

## Import inicial (hecho)
[`scripts_db_handle/import_vehiculos_excel.py`](../scripts_db_handle/import_vehiculos_excel.py) — one-off **idempotente** (`--dry` para ver el plan; si el `code` ya existe lo salta). Importado a dev el 2026-08-05: **16 vehículos + 16 pólizas + estado DETENIDO de TEL-010** — lo único con datos reales en el xlsm; servicios/llantas/accesorios/refrendos/compras venían vacíos (los `SI/False` de llantas son artefactos de fórmula, no datos). Nota: la póliza de TEL-014 viene con vigencia invertida (2021→2017) **desde el Excel**; se importó tal cual — corregir por PUT cuando tengan el dato real. Para poblar prod/test: correr el script con el entorno apuntando allá.

## Pendientes
- **Front**: construir las pantallas de las 6 vistas + CRUD (repo del cliente GUI).
- Recordatorios/notificaciones programadas (vencimiento de póliza, mantenimiento próximo) — hoy solo se notifica alta/baja de vehículo.
- Otros activos bajo `/cda` (el namespace ya está montado para crecer).
