# Control de saldos sin contrato: membresía explícita remisión → control

Fecha: 2026-09-14 · **Estado: propuesta cerrada en grill, pendiente de visto bueno. Nada implementado ni DDL corrido.**
Origen: nueva información de Cobranza — deben poder crearse controles de saldos **a partir de remisiones que no tienen contrato padre** (trabajos por cotización/pedido/ticket sin contrato marco). Extiende [`control_saldos_cabecera.md`](control_saldos_cabecera.md) (grill 2026-09-11) y se apoya en [`remission_module_fields_and_balance.md`](remission_module_fields_and_balance.md).

## Qué ya funciona y qué no (hallazgos en código y BD dev)

- **Remisiones sin cotización ni contrato ya se pueden crear hoy.** `activity_reports.quotation_id` y `contract_id` son anulables (FK `SET NULL` / `CASCADE`), y `POST /remission` / `POST /remissionControlTable` convierten `0`/ausente en `NULL`. Obligatorios reales: `date`, `folio` (UNIQUE), `client_id`; control table además `plant`/`area`/`location`; `/remission` además `items`. En dev las 5 remisiones ya traen `quotation_id NULL`. **No hay cambio que hacer en el alta de remisiones.**
- **Contratos sin cotización también existen** (5 de 10 en dev): `POST /contract` con `quotation_id = 0` crea una cotización vacía por dentro. Tampoco cambia.
- **El hueco está únicamente en el control de saldos.** `balance_controls.contract_id` es `NOT NULL` (FK RESTRICT en dev), la regla es "1 control activo por contrato" y la membresía remisión → control **se deriva** de `activity_reports.contract_id` en 6 puntos: `remissions_count` del listado, `remissions` del detalle, sweep de `custom_fields`, `validate_remission_custom_fields` (`PUT /remissionBalance`), adopción del POST (`adopt_remission_to_contract`) y `_resolve_contract_id`. Una remisión sin contrato no tiene por dónde entrar a ningún control.

## Decisiones (grill 2026-09-14)

| Tema | Decisión |
|---|---|
| Llave de membresía | **Columna nueva `activity_reports.balance_control_id`** (INT NULL). Pasa a ser **la única** llave de membresía para todos los controles, con o sin contrato; `balance_controls.contract_id` se vuelve anulable. Sustituye la membresía derivada por `contract_id` del grill anterior (esa premisa ya no se sostiene con controles sin contrato). Backfill en el DDL desde `contract_id` → control activo. Descartadas: membresía dual (`OR` de dos caminos en 6 queries + riesgo de una remisión en dos controles) y "contrato sombra" por cliente (contamina el catálogo de presales). |
| Identidad sin contrato | **`balance_controls.client_id` siempre** (NOT NULL; con contrato se copia de `contracts.client_id`, sin contrato lo manda el front) **+ `title`** (obligatorio sin contrato; con contrato default = `identifier` del contrato). Regla: **solo se adoptan remisiones del mismo `client_id`**. Listado pinta `title` y `client_name`; filtro nuevo `?client_id=`. |
| Unicidad | Con contrato sigue **1 control activo por contrato** (409). Sin contrato **no hay unicidad**: N controles por cliente. |
| Gestión de membresía | Endpoint nuevo **`PUT /balanceControl/remissions`** `{id_control, add:[], remove:[]}`, solo `administracion`, history en el control y en cada remisión. `add` con las **mismas reglas** que `remissions[]` del POST. Una remisión que ya está en **otro control activo → 400** listando cuáles (mover = `remove` explícito primero). |
| Reglas de adopción | Control **con contrato**: acepta remisiones con ese `contract_id` o con `contract_id NULL` (se les asigna el contrato, como hoy). Control **sin contrato**: solo remisiones con `contract_id NULL`. Siempre mismo `client_id`. Remisión en un control **cancelado** = libre (se re-adopta sin paso previo). |
| Auto-enlace | `POST /remission` / `POST /remissionControlTable` con `contract_id` cuyo contrato tenga control activo → la remisión nace ligada. `POST /balanceControl` con contrato → adopta automáticamente las remisiones del contrato que estén libres o en un control cancelado (conserva la semántica "todas las remisiones del contrato están en su control"). |
| Contrato tardío | **`contract_id` sigue inmutable.** Si un control nació sin contrato y después se firma el marco: `PUT /cancel` del huérfano → `POST` con `contract_id` (adopta las libres del contrato) → `PUT /remissions add` para traer las del cancelado. Movimientos del viejo quedan como estaban; el monto contratado se captura de nuevo. Descartada la transición única NULL → contrato (cascada sobre remisiones). |
| Cancel | **No toca remisiones** (conservan `balance_control_id` apuntando al cancelado; el detalle del cancelado sigue listándolas). El GET de remisiones expone `balance_control_id` + `balance_control_active` para que el front sepa si una fila está "disponible". `PUT /remissionBalance` con `custom_fields` sobre una remisión cuyo control está cancelado → 400. |
| PUT de remisión | `PUT /remission` / `PUT /remissionControlTable` que cambien `contract_id` (valor `> 0` distinto al de la fila) o `client_id` de una remisión ligada a un control **activo** → **400** "quítala del control N con `PUT /balanceControl/remissions` antes". Mover remisiones entre controles queda como acción explícita de `administracion`; operaciones/compras no alteran Cobranza sin querer. El resto del PUT (items, fechas, `extra_info`) no cambia. |
| Formatos | Sin restricción por tener o no contrato: cualquier FO-CXC vale (FO-CXC-10/11 "incluye cotización" son los naturales sin contrato, pero es decisión del usuario). |
| `contract_number` / `pedido_exiros` sin contrato | Texto libre opcional (ya no hay `contracts.code` / `metadata.exiros` de dónde sembrar). |

## DDL propuesto (se entregará como `scripts_db_handle/control_saldos_sin_contrato.sql` tras el visto bueno; lo corre el usuario)

```sql
-- 1) balance_controls: contrato opcional + identidad propia
--    En dev existe fk_bc_contract (bloque opcional del 09-11): soltarla antes del MODIFY y re-crearla al final.
ALTER TABLE sql_telintec_mod_admin.balance_controls DROP FOREIGN KEY fk_bc_contract;
ALTER TABLE sql_telintec_mod_admin.balance_controls
    MODIFY contract_id INT NULL COMMENT '-> contracts(id); NULL = control sin contrato',
    ADD COLUMN client_id INT NULL AFTER format_id COMMENT '-> sql_telintec.customers_amc(id_customer); con contrato = contracts.client_id',
    ADD COLUMN title     VARCHAR(255) NULL AFTER client_id COMMENT 'Nombre visible; obligatorio sin contrato, con contrato default = identifier',
    ADD KEY idx_bc_client (client_id);
UPDATE sql_telintec_mod_admin.balance_controls bc
    JOIN sql_telintec_mod_admin.contracts c ON c.id = bc.contract_id
    SET bc.client_id = c.client_id,
        bc.title = COALESCE(bc.title, JSON_UNQUOTE(JSON_EXTRACT(c.metadata, '$.identifier')));
ALTER TABLE sql_telintec_mod_admin.balance_controls MODIFY client_id INT NOT NULL;

-- 2) activity_reports: membresía explícita
ALTER TABLE sql_telintec_mod_admin.activity_reports
    ADD COLUMN balance_control_id INT NULL COMMENT '-> balance_controls(id_control); NULL = sin control',
    ADD KEY idx_ar_balance_control (balance_control_id);
-- backfill de la membresía derivada (contract_id -> control activo). dev: 0 controles, 0 filas.
UPDATE sql_telintec_mod_admin.activity_reports ar
    JOIN sql_telintec_mod_admin.balance_controls bc ON bc.contract_id = ar.contract_id AND bc.is_active = 1
    SET ar.balance_control_id = bc.id_control
    WHERE ar.balance_control_id IS NULL;

-- 3) OPCIONAL: FKs reales (mismo criterio que el bloque del 09-11; en dev van)
ALTER TABLE sql_telintec_mod_admin.balance_controls
    ADD CONSTRAINT fk_bc_contract FOREIGN KEY (contract_id) REFERENCES sql_telintec_mod_admin.contracts (id) ON DELETE RESTRICT ON UPDATE CASCADE,
    ADD CONSTRAINT fk_bc_client   FOREIGN KEY (client_id)   REFERENCES sql_telintec.customers_amc (id_customer) ON DELETE RESTRICT;
ALTER TABLE sql_telintec_mod_admin.activity_reports
    ADD CONSTRAINT fk_ar_balance_control FOREIGN KEY (balance_control_id) REFERENCES sql_telintec_mod_admin.balance_controls (id_control) ON DELETE SET NULL ON UPDATE CASCADE;
```

Orden: dev → test → prod, **después** de que test/prod tengan `control_saldos.sql` (pendiente del 09-11). Sin sistema de migraciones.

## Capas a tocar

1. **Controller** [`balance_control_controller.py`](../templates/controllers/purchases/balance_control_controller.py): `CONTROL_COLUMNS`/`_SELECT_CONTROL` ganan `client_id`, `title` y `client_name` (LEFT JOIN `sql_telintec.customers_amc`), **append-only** (el midleware mapea por índice); `remissions_count` pasa a `WHERE ar.balance_control_id = bc.id_control`; `get_remissions_summary_by_contract` → `get_remissions_summary_by_control`; `remove_custom_field_keys_from_remissions` scoped por `balance_control_id`; `adopt_remission_to_contract` → `attach_remission_to_control(id_report, id_control, contract_id_or_None, history)` con guard en el `UPDATE` (`balance_control_id IS NULL OR balance_control_id NOT IN (activos)`) + `detach_remission_from_control`; `get_remissions_by_ids` devuelve también `client_id` y `balance_control_id`; listado con filtros `client_id` / `has_contract`; `get_free_remissions_by_contract` para la auto-adopción.
2. **Controller** [`remisions_controller.py`](../templates/controllers/presales/remisions_controller.py): `get_remission_by_id` agrega **al final** del SELECT `ar.balance_control_id` (índice 20) y un escalar `(SELECT is_active FROM balance_controls WHERE id_control = ar.balance_control_id)` (índice 21) — sin tocar `GROUP BY` ni el orden previo (los 8 call sites indexan por posición); filtros param-or-NULL nuevos `client_id`, `balance_control_id`, `available_for_control` (= `balance_control_id IS NULL OR` control no activo). `insert_remission` / `update_remission` reciben `balance_control_id`.
3. **Midleware** [`MD_BalanceControl.py`](../templates/resources/midleware/MD_BalanceControl.py): POST con `contract_id` opcional (rama con contrato: copia `client_id`, default `title`, unicidad, auto-adopción; rama sin contrato: exige `client_id` + `title`), reglas de adopción en un solo helper `_check_adoptable(control, remission)` reusado por POST y por el endpoint nuevo `attach_detach_remissions_from_api`; `validate_remission_custom_fields(balance_control_id, ...)` por control activo; PUT rechaza `client_id`/`title` vacío (title editable con contrato y sin él); cancel sin cambios.
4. **Midleware** [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py): `_resolve_balance_control_id` (hermano de `_resolve_contract_id`) en los dos POST de remisión; guard 400 en los dos PUT cuando cambian `contract_id`/`client_id` con control activo; `update_remission_balance_from_api` valida `custom_fields` por `result_ra[20]`; el GET expone `balance_control_id` (int|null) y `balance_control_active` (bool|null).
5. **Modelos** [`api_balance_control_models.py`](../static/Models/api_balance_control_models.py): `contract_id` deja de ser `InputRequired` (default 0), `client_id` (default 0) y `title` nuevos en POST/PUT + `api.model`; `BalanceControlRemissionsForm` (`id_control`, `add`, `remove`) + modelo Swagger. [`api_purchases_models.py`](../static/Models/api_purchases_models.py): sin cambios en forms de remisión (la llave no la manda el front).
6. **Rutas** [`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py): `PUT /balanceControl/remissions` (`_BC_WRITE`); `GET /remission-<id>` lee los 3 query params nuevos; `GET /balanceControl` lee `client_id`/`has_contract`.
7. **Docs**: este archivo pasa a "hecho", `control_saldos_cabecera.md` gana nota de que la membresía cambió, `pendientes.md`.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Todo responde JSON `{data, msg, error}`; `error` es `null`, string o **lista** de strings.
- Permisos igual que hoy: GETs `administracion`/`purchases`/`operaciones`; POST / PUT / `/remissions` / `/fields` / `/cancel` **solo `administracion`**.
- **Cambio de cruce**: la fila de `GET /remission--1` se cruza con su control por **`balance_control_id`**, ya no por `contract_id`. Remisión "disponible" para crear/agregar = `balance_control_id === null || balance_control_active === false` (o simplemente `GET /remission--1?available_for_control=1&client_id=40`).

### `POST /balanceControl` — cambios

```json
{ "metadata": { "format_id": 13, "client_id": 40, "title": "Cotización COT-2026-0148 / Ticket TK-99120",
                "currency": "MXN", "contracted_amount": 85000.00, "quotation_number": "COT-2026-0148", "ticket_system": "Mesa de ayuda", "ticket_number": "TK-99120" },
  "remissions": [7, 8],
  "custom_fields": [] }
```

- `contract_id` ahora **opcional** (`0`/`null`/ausente = sin contrato). **Sin contrato: `client_id` y `title` obligatorios** (400 si faltan). **Con contrato**: `client_id` se toma del contrato (si viene y no coincide → 400), `title` default = `identifier` del contrato; sigue 1 activo por contrato (409) y se **auto-adoptan** las remisiones del contrato libres o en control cancelado.
- `remissions[]`: cada id debe existir, ser del mismo `client_id`, tener `contract_id NULL` (o el del control, si lo hay) y no estar en **otro control activo**. Cualquier falla → 400 con `error: ["remisión 7: pertenece al control activo 3", "remisión 9: cliente distinto (12 ≠ 40)"]` y **no se crea nada**.
- 201 → `data: {"id_control": 6, "id_movement": 6, "adopted_remissions": [7, 8]}` (incluye las auto-adoptadas por contrato).

### `PUT /balanceControl/remissions` — nuevo

```json
{ "id_control": 6, "add": [9, 10], "remove": [7] }
```

| Código | Cuándo | `data` |
|---|---|---|
| **200** | aplicado (validación completa antes de escribir; todo o nada) | `{"id_control": 6, "added": [9, 10], "removed": [7], "remissions_count": 3}` |
| **400** | alguna regla falla: id inexistente, cliente distinto, contrato distinto/incompatible, ya en otro control activo, `remove` de una que no está en este control, control cancelado, ambas listas vacías | `null`, `error` = lista `["remisión 9: …"]` |
| **404** | control inexistente | `null` |

- `add` en un control **con contrato** también escribe `contract_id` en las remisiones que lo tenían `NULL` (como la adopción de hoy). `remove` pone `balance_control_id = NULL` y **no toca `contract_id`** (una remisión de contrato X quitada de su control volverá a entrar si se crea un control nuevo para X: la auto-adopción toma las libres del contrato).
- Cada remisión recibe una entrada en `history` (`action: "Adopción a control de saldos"` / `"Retiro de control de saldos"`, `changes.metadata` con `balance_control_id` y, si aplica, `contract_id`); el control recibe una con `added`/`removed`.

### `GET /balanceControl` / `GET /balanceControl/<id>` — cambios

- Filas ganan `client_id`, `client_name`, `title`; `contract_id`, `contract_code`, `contract_abbreviation`, `contract_identifier` vienen **`null`** en un control sin contrato. Query params nuevos: `client_id=<n>`, `has_contract=0|1`.
- `remissions` del detalle y `remissions_count` = las ligadas por `balance_control_id` (incluye las de un control cancelado consultado con `all=1`).

### `PUT /balanceControl` — cambios

- `title` editable (con y sin contrato); `client_id` y `contract_id` → 400 (inmutables, igual que `format_id`/`contracted_amount`).

### `GET /remission-<id>` — cambios

- Cada fila trae `balance_control_id` (int | `null`) y `balance_control_active` (`true`/`false`, `null` sin control). Query params nuevos, combinables con los existentes: `client_id=<n>`, `balance_control_id=<n>`, `available_for_control=1`.

### `PUT /remission` / `PUT /remissionControlTable` — gotcha nuevo

- Si la remisión está en un control **activo** y el `metadata` trae `contract_id > 0` distinto al actual o `client_id` distinto → **400** `error: "la remisión está en el control de saldos 6; quítala con PUT /balanceControl/remissions antes de cambiar contrato/cliente"`. Mandar el mismo valor (o omitir `contract_id`) sigue siendo 200.
- `POST /remission` / `POST /remissionControlTable` con `contract_id` de un contrato con control activo → la remisión nace con ese `balance_control_id` (la respuesta 201 lo incluye: `data: {"id_remission": 12, "balance_control_id": 6}`).

### `PUT /remissionBalance` — cambios

- `custom_fields` se valida contra el control de **`balance_control_id`** de la remisión, no contra el contrato: sin control → 400 `"la remisión no está en ningún control de saldos"`; control cancelado → 400 `"el control 6 está cancelado"`; el resto igual (llave no declarada / tipo).

### Gotchas

- Un control sin contrato **no** tiene `contract_number` ni `pedido_exiros` sembrados: son texto libre opcional.
- `DELETE /remission` sigue permitido aunque esté en un control (la fila desaparece del control; sin bloqueo).
- Los ids de cliente sí coinciden entre BDs para TERNIUM (`40`), pero resolver siempre por catálogo.

## Al modificar

- **Toda query nueva que relacione remisiones con un control usa `activity_reports.balance_control_id`**, nunca `contract_id` (ese solo dice bajo qué contrato marco se ejecutó el trabajo).
- Regla de adopción en un solo lugar (`_check_adoptable`): si cambia (p. ej. permitir cliente distinto), cambia para POST y para `/remissions`.
- Columnas nuevas en `balance_controls`: al final de `CONTROL_COLUMNS` y del `SELECT` (append-only); `get_remission_by_id`: al final del SELECT, índices 20/21 son load-bearing.

## Verificación prevista (vs BD dev, `test_client`)

POST sin contrato (faltan `client_id`/`title` → 400; ok → 201 + movimiento inicial), POST con contrato (auto-adopción + unicidad 409 + `client_id` discordante 400), `remissions[]` con los 4 rechazos, `PUT /remissions` add/remove/atomicidad/400s, cancel → re-adopción sin paso previo, `custom_fields` por control (sin control / cancelado / ok + sweep scoped), guard 400 en los dos PUT de remisión, auto-enlace en los dos POST de remisión, GET remisiones con los 3 filtros e índices 20/21, GET controles con `client_id`/`has_contract`; regresión de los 61 checks del 09-11. Datos temporales borrados al final.

## Pendientes

- **[usuario] Visto bueno a esta propuesta** y al DDL; después implementación de las 4 capas + `.sql` en `scripts_db_handle/`.
- **[back] DDL en test y prod** (este y el de `control_saldos.sql`, en ese orden).
- **[front]** Cruzar por `balance_control_id`, pantalla de alta con la rama "sin contrato" (`client_id` + `title`), selector de remisiones disponibles (`available_for_control=1`), y botón agregar/quitar remisiones (`PUT /balanceControl/remissions`).
