# Sincronización del catálogo SYSCOM (`products_services` / `products_simple`) y márgenes desde la webapp

> Pedido del usuario el 2026-11-05 (`P-251`): "lo que hacía era descargar un JSON con los productos (~50 000), debería correr cada 2 semanas; el margen de ganancia lo pondríamos desde una ventana del front; ¿hay alguna forma de bajo costo?". **Estado: aprobada, en curso** (grill cerrado el 2026-11-05; abre `P-252` a `P-255`). Consumidores del catálogo: el sitio telintec.mx (Lambdas `productSearch`/`productsGetTelintec`), el agente virtual de ventas ([`agentes_openai.md`](agentes_openai.md)) y la pantalla de productos. Vocabulario: sección "Catálogo público" de [`GLOSSARY.md`](../GLOSSARY.md).

## Lo que hay hoy (verificado en dev el 2026-11-05)

| Dato | Valor |
|---|---|
| `sql_telintec.products_services` | 32 014 productos, ids 19 … 220 155 (son los `producto_id` de SYSCOM), 482 marcas, 718 rutas de categoría (`category` = ids SYSCOM separados por coma, p. ej. `66302,65772,25`), 15 179 con existencia, **4 143 sin precio** (`price_provider = 0` y `price_retail = 0`) |
| Regla de precio actual | `price_retail / price_provider` = **1.40** en 27 464 de 27 871 productos con precio (el resto entre 1.33 y 1.50, redondeos). No hay tabla de márgenes |
| `products_simple.name` | **No es un recorte**: es el nombre en minúsculas, sin acentos, sin dígitos ni puntuación y sin muletillas ("Conector N macho en A/R de anillo plegable para cable RG-142/U." → `conector n macho ar anillo plegable cable rgu`), largo medio 63, máximo 194. Tiene 3 índices FULLTEXT; es lo que usa `catalog.py` del agente |
| Sincronización | La hacía Telintec a mano: descarga de un JSON (~50 000 productos) y carga a la BD; el código no está en esta máquina. Sin fecha de última sincronización en la BD |
| API de SYSCOM (docs públicas, leídas el 2026-11-05) | OAuth2 `client_credentials` en `POST /api/v1/oauth/token`, **token de 365 días**; `GET /api/v1/productos` exige `categoria`, `marca` o `busqueda`, con `limit` 10–**1000** y `pagina` 1–1000; detalle por ids `GET /api/v1/productos/{id1,id2,…}` (hasta 300); `GET /api/v1/marcas`, `GET /api/v1/categorias?todas=true`; **`GET /api/v1/tipocambio` público** (`normal`, `preferencial`, plazos); precios en **USD** por defecto (`moneda=mxn` disponible; flag `iva`); campos `producto_id`, `modelo`, `titulo`, `marca`, `categorias[{id,nombre,nivel}]`, `total_existencia`, `img_portada`, `precios{precio_1, precio_especial, precio_descuento, precio_lista, …}`; límite de peticiones no numerado: 429 con `Retry-After` |

## Diseño (bajo costo = cero infraestructura nueva)

```
 systemd timer (días 1 y 15, 03:00 hora del centro)   webapp Preventa: pantalla "Márgenes"       agente de ventas / sitio
   telintec-catalog-sync.service                        │ /admin/presales/pricing-rules            (solo leen products_*)
   │ scripts/sync_catalog.py (repo telintec_agents)      ▼
   │  1. token (cacheado 365 d) · tipocambio.normal    API GUITelintec: CRUD de pricing_rules + POST recalculate
   │  2. marcas → productos?marca=X&limit=1000&pagina=N   (≈ 60–120 peticiones para 50 000)
   │  3. snapshot JSON gz → S3 catalog/<entorno>/syscom_<fecha>.json.gz   ┐
   │  4. upsert products_services (price_usd, costo MXN, stock, foto)      ├─ usuario MySQL catalog_sync
   │  5. regenerar products_simple (misma normalización que el agente)     │
   │  6. recalcular price_retail con pricing_rules                         ┘
   │  7. catalog_sync_runs: cuándo (hora del centro), cuántos, tipo de cambio, errores
```

### Decisiones cerradas (2026-11-05)

| # | Tema | Decisión | Nota |
|---|---|---|---|
| S1 | Dónde corre | **Timer de systemd** en el servidor de prod que lanza `scripts/sync_catalog.py` del repo `telintec_agents` (Python 3.12, mismo venv); `systemctl start telintec-catalog-sync` lo corre a mano. `OnCalendar=*-*-01,15 03:00` con `TZ=America/Mexico_City` en la unidad. | Lambda + EventBridge también sale ≈ 0, pero exige empaquetar, VPC y ventanas de 15 min; GitHub Actions no alcanza la RDS. |
| S2 | Qué baja | **Todas las marcas**: `GET /marcas` y por cada una `productos?marca=<slug>&limit=1000&pagina=N&moneda=usd` hasta vaciar; ≈ 60–120 peticiones (minutos). Backoff con `Retry-After` ante 429. | El detalle por ids solo para completar campos que la lista no traiga. |
| S3 | Snapshot | El JSON completo de la corrida, comprimido, **en S3** bajo `catalog/<entorno>/syscom_<AAAA-MM-DD>.json.gz` (regla `<raíz>/<entorno>/…` de [`s3_rutas_por_entorno.md`](s3_rutas_por_entorno.md)), en el **bucket de Administración** que ya usa el API (`S3_ADMIN_BUCKET`; decisión del usuario, 2026-11-05), configurado como `S3_CATALOG_BUCKET` en el `.env` del servicio; regla de ciclo de vida sobre el prefijo `catalog/` para expirar a los 180 días. Nada en disco. | El usuario eligió S3 por el tamaño que puede alcanzar; ≈ 15 MB por corrida en gz. |
| S4 | Costo | `price_usd = precios.precio_descuento`; `price_provider = round(price_usd × tipocambio.normal, 2)` del día de la corrida; el tipo de cambio queda en `catalog_sync_runs.exchange_rate`. | Guardar el USD permite recalcular con otro tipo de cambio sin bajar de nuevo. |
| S5 | Precio de lista | `price_retail = round(price_provider × (1 + margen/100) × (1 + IVA/100), 2)` con **IVA 16 %** y **margen global 40 %** (`pricing_rules`, regla global + excepciones por marca y por categoría; gana la más específica). | **Aviso:** hoy el factor es 1.40 = costo × 1.40; con 40 % + 16 % el factor pasa a **1.624**, es decir el precio publicado **sube 16 %** en el primer recálculo. Para dejar los precios como hoy, el margen global sería 20.690 %. Se fija desde la pantalla antes del primer recálculo. |
| S6 | Recalcular sin SYSCOM | Cambiar una regla y pulsar "Recalcular" llama `POST /admin/presales/pricing-rules/recalculate`: un `UPDATE` sobre `products_services` (segundos), registrado en `catalog_sync_runs` con `status 4`. | Las Lambdas del sitio leen `price_retail` tal cual, por eso se guarda. |
| S7 | Productos que ya no vienen | Quedan con `available_quantity = 0` (no se borran: el sitio y conversaciones viejas los enlazan); los nuevos entran con `is_service = 0`, `support_offered = 0`. | — |
| S8 | `products_simple` | Se regenera completa en cada corrida con la **misma normalización** que `normalize_query` del agente (minúsculas, sin acentos, solo letras, sin muletillas); `brand` en minúsculas, `model` tal cual. | El recorte de n caracteres que recordaba el usuario no es lo que hay en la tabla. |
| S9 | Accesos | Usuario MySQL **`catalog_sync`** (`SELECT, INSERT, UPDATE` en `products_services`; `SELECT, INSERT, UPDATE, DELETE` en `products_simple`; `SELECT` en `pricing_rules`; `SELECT, INSERT, UPDATE` en `catalog_sync_runs`); `agents_svc` sigue solo lectura. `SYSCOM_CLIENT_ID`/`SYSCOM_CLIENT_SECRET`, `CATALOG_DB_USER`/`CATALOG_DB_PASSWORD` y `S3_CATALOG_BUCKET` en el `.env` del servicio; el usuario IAM del servicio (`P-248`) suma `s3:PutObject` sobre ese prefijo. | — |
| S10 | Pantalla de márgenes | En **Preventa** de la webapp, permiso **`App.Department.adminPreventa`** (y `Administracion`, como el resto de `/admin/presales/*`): lista de reglas, alta/edición/baja, "Recalcular precios" con el conteo de productos cambiados y "última sincronización". | — |
| S11 | Fechas | `started_at`, `finished_at`, `synced_at` y `updated_at` en **hora del centro de México** (`America/Mexico_City`, sin horario de verano), que el servicio escribe explícitamente sin depender del TZ del host. | Igual que `timezone_software` del API. |

### Tablas (DDL en [`scripts_db_handle/catalogo_sync_reglas.sql`](../scripts_db_handle/catalogo_sync_reglas.sql), lo revisa y corre el usuario, `P-255`)

| Tabla (`sql_telintec`) | Columnas |
|---|---|
| `pricing_rules` | `rule_id` INT AI PK · `scope` TINYINT (0 global, 1 marca, 2 categoría) · `scope_value` VARCHAR(100) ('' en la global; slug de marca o id de categoría) · `margin_pct` DECIMAL(6,3) · `iva_pct` DECIMAL(5,2) · `status` TINYINT (0 activa, 1 inactiva) · `valid_from` DATE · `updated_by` INT · `updated_at`; único `(scope, scope_value)`; `CHECK` margen 0–300 e IVA 0–100. El script siembra la global (40 %, 16 %). |
| `catalog_sync_runs` | `run_id` INT AI PK · `started_at`, `finished_at` · `status` TINYINT (0 corriendo, 1 ok, 2 con errores, 3 fallida, 4 solo recálculo) · `exchange_rate` DECIMAL(8,4) · `products_seen`, `products_inserted`, `products_updated`, `products_zeroed`, `prices_updated` INT · `snapshot_key` VARCHAR(255) · `error` TEXT |
| `products_services` | columnas nuevas `price_usd` DECIMAL(12,4) y `synced_at` DATETIME (solo si faltan) |

### Costo y tiempos

| Concepto | Estimación |
|---|---|
| Infraestructura | 0 (servidor existente; API de SYSCOM sin costo para distribuidores; S3 centavos al mes) |
| Peticiones por corrida | 60–120 listados de 1 000 + 1 de marcas + 1 de tipo de cambio |
| Duración | minutos; con 429 y `Retry-After`, decenas de minutos como peor caso |
| Snapshot | ≈ 100 MB sin comprimir, ≈ 15 MB en gz por corrida; 180 días ≈ 12 corridas ≈ 180 MB |
| Trabajo | back: script y timer (`P-252`) + 5 endpoints (`P-253`) ≈ 2–3 días; front: una pantalla (`P-254`) |

### Pendientes que abre

| Id | Qué |
|---|---|
| `P-252` [back, `telintec_agents`] | `scripts/sync_catalog.py` + unidad y timer de systemd |
| `P-253` [back, este repo] | `/admin/presales/pricing-rules` (CRUD + `recalculate`) y `GET /admin/presales/catalog/sync-runs`; doc propio con el contrato definitivo |
| `P-254` [front] | pantalla "Márgenes" en Preventa |
| `P-255` [usuario] | correr el `.sql` en dev → test → prod; credenciales SYSCOM, `catalog_sync` y bucket en el `.env` del servicio; `s3:PutObject` al usuario IAM; instalar unit + timer en prod; fijar el margen antes del primer recálculo |

## Contrato mínimo para el front (tentativo: se fija en el doc de `P-253`)

- **Base:** `/GUI/api/v1/admin/presales` (API GUITelintec). `Authorization`: JWT crudo, sin `Bearer`. Permisos: `App.Department.adminPreventa` o `App.Department.Administracion`; `Administrator` pasa.
- `GET /pricing-rules` → 200 `{"data": [{"rule_id": 1, "scope": 0, "scope_value": "", "margin_pct": 40.0, "iva_pct": 16.0, "status": 0, "valid_from": "2026-11-05", "updated_by": null, "updated_at": "2026-11-05 10:00:00"}], "msg": "ok", "error": null}`.
- `POST /pricing-rules` `{scope, scope_value, margin_pct, iva_pct, valid_from}` → 201 con la regla; 400 `{data: null, msg, error}` si el ámbito se repite, el margen no está entre 0 y 300 o el IVA entre 0 y 100.
- `PUT /pricing-rules/<id>` mismo cuerpo → 200; `DELETE /pricing-rules/<id>` → 200 (`status` 1, no borra; la global no se puede desactivar).
- `POST /pricing-rules/recalculate` → 200 `{"data": {"products_updated": 27871, "run_id": 7}, "msg": "ok", "error": null}`; tarda segundos; 409 si hay una sincronización corriendo (`catalog_sync_runs.status = 0`).
- `GET /catalog/sync-runs?limit=10` → 200 con las últimas corridas (fechas en hora del centro, `YYYY-MM-DD HH:MM:SS`).
- Estados numéricos; el front mapea etiquetas. Gotcha: tras "Recalcular", el sitio público muestra los precios nuevos de inmediato.

## Al modificar

- Cambiar la fórmula de precio → cambiar `recalculate` (API) y el paso 6 del script a la vez; nunca una sola.
- Columna nueva en `products_services` que use el sitio → avisar al front del sitio (las Lambdas leen la tabla directo).
- Cambiar la normalización de `products_simple.name` → cambiar también `normalize_query` en `telintec_agents/agents_service/catalog.py`.
- Reglas nuevas de precio (promociones, redondeo a .90) → columna en `pricing_rules`, no en código.
- Cambiar la frecuencia → solo el `OnCalendar` del timer; el script no asume periodicidad.

## Fuentes

- Documentación pública de la API de SYSCOM, leída el 2026-11-05: [developers.syscom.mx/docs](https://developers.syscom.mx/docs) · [autenticación](https://developers.syscom.mx/docs/autenticacion) · [productos](https://developers.syscom.mx/docs/productos) · [catálogos y tipo de cambio](https://developers.syscom.mx/docs/catalogos) · [marcas](https://developers.syscom.mx/docs/marcas) · [errores](https://developers.syscom.mx/docs/errores)
