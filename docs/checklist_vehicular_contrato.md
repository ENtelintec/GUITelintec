# Contrato del checklist vehicular: editable y opcional (`POST·PUT /sgi/voucher/vehicle`)

Salió del grill del catálogo [`common_contracts_catalog.md`](common_contracts_catalog.md)
(2026-09-23), cuyo primer consumidor es el selector de contrato del checklist
vehicular (FO-CDA-03). Dos huecos del flujo del checklist:

1. **El `PUT` ignoraba el contrato.** `VoucherVehiclePutForm` exigía `contract`
   (`InputRequired`) pero ni el midleware ni ningún controller hacían
   `UPDATE ... SET contract`: un contrato mal elegido no se podía corregir.
2. **No existía "sin contrato".** `vouchers_general.contract` era `INT NOT NULL` con
   FK a `contracts(id)`: un vehículo que no pertenece a ningún contrato (casos
   escasos: oficina, dirección, almacén) no se podía registrar, o se registraba con un
   contrato cualquiera y ensuciaba los datos.

Descartado: un "pseudo-contrato" `INTERNO` en `contracts` (aparecería en listados de
Administración, remisiones, control de saldos y folios SM, con `code`/`client_id`
inventados).

## Las 4 capas

```
HTTP    rs_SGI.py  /voucher/vehicle  (post, put)                 -> sin cambios
modelos api_sgi_models.py  voucher_vehicle_post/put_model          -> contract required=False
        VoucherVehiclePostForm / VoucherVehiclePutForm             -> contract [validators.Optional()]
mid     MD_SGI.py  _vehicle_contract_or_none                       -> null/omitido/0/negativo -> None
        create_voucher_vehicle_api                                 -> INSERT con contract normalizado
        update_voucher_vehicle_api                                 -> UPDATE del contrato ANTES que el resto
DB      vouchers_controller.py  update_voucher_general_contract    -> UPDATE vouchers_general SET contract
DDL     scripts_db_handle/vouchers_general_contract_nullable.sql   -> contract INT NULL (FK se conserva)
```

- **Solo el checklist vehicular.** `vouchers_general` la comparten los vales de
  herramientas y seguridad; sus forms (`VoucherToolsFormPost/Put`,
  `VoucherSafetyFormPost/Put`) **siguen exigiendo** `contract`.
- `_vehicle_contract_or_none`: `null`, clave omitida, `0` y negativos → `NULL` en BD
  (la FK solo acepta ids reales o `NULL`, y un front suele mandar `0` por defecto).
- En el `PUT` el `UPDATE` del contrato va **primero**: si la FK rechaza el id, responde
  400 sin haber tocado el vehículo, el historial ni los items.
- Las lecturas no cambian: los 4 SELECT de vouchers solo leen `vg.contract` (sin JOIN
  a `contracts`), así que un voucher sin contrato sale con `"contract": null` y no
  desaparece de ninguna lista. El PDF del checklist no imprime el contrato.

## DDL

[`scripts_db_handle/vouchers_general_contract_nullable.sql`](../scripts_db_handle/vouchers_general_contract_nullable.sql):
`DROP FOREIGN KEY vouchers_general_ibfk_2` → `MODIFY contract INT NULL` → la misma FK
re-creada (patrón de `control_saldos_sin_contrato.sql`). Paso 0: verificar el nombre de
la FK en cada BD.

- **dev, test y prod**: corrido por el usuario (2026-09-23); verificado en las 3 BDs
  `IS_NULLABLE = YES` y la FK `vouchers_general_ibfk_2 → contracts(id)` de vuelta.
- Era aditivo: el código viejo siempre manda contrato, así que el orden de deploy
  respecto al código nuevo es indistinto.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permisos
  `sgi` o `voucher` (sin cambios).
- **Base**: `/GUI/api/v1/sgi/voucher/vehicle` — `POST` (alta) y `PUT` (edición),
  mismo body de siempre; **solo cambia `contract`**.
- **Lista de contratos para el selector**: `GET /GUI/api/v1/common/contracts` (permiso
  `Common`) → guardar su `id`. Contrato completo en
  [`common_contracts_catalog.md`](common_contracts_catalog.md).
- **`contract`** (int, opcional en `POST` y `PUT`):
  - id de contrato → se guarda (en el `PUT` ahora **sí** se actualiza);
  - `null`, `0` o clave omitida → **sin contrato**. El front ofrece una opción
    "Sin contrato" que manda `null`.
  - En el `PUT` mandar **siempre** el valor actual: omitirlo significa "sin contrato",
    no "no cambiar".
- **Respuestas**: siempre JSON `{data, msg, error}`.
- **Lecturas** (`GET /voucher/vehicle/<y>&<m>&<d>`): `contract` puede venir `null`;
  pintarlo como "Sin contrato".

Ejemplos:

```
POST 201 → {"data": {"id_voucher": 12}, "msg": "Voucher vehicular creado correctamente (ID 12)", "error": null}

PUT  200 → {"data": {"id_voucher": 12}, "msg": "Voucher vehicular actualizado correctamente (ID 12)", "error": null}

PUT  400 (contrato inexistente; nada se modificó)
     → {"data": null, "msg": "No se pudo actualizar el contrato del voucher vehicular",
        "error": "1452 (23000): Cannot add or update a child row: a foreign key constraint fails (...)"}

POST 400 (contrato inexistente)
     → {"data": null, "msg": "No se pudo crear el voucher general", "error": "<error sql>"}

400 (contract no entero)
     → {"data": null, "msg": "Estructura de datos inválida", "error": {"contract": ["Not a valid integer value."]}}

401 → {"error": "No autorizado. Token invalido"}
```

Gotchas: el alta responde **201** (no 200); el 401 no trae `data`/`msg`.

## Verificación

Contra BD dev con el DDL ya aplicado, `app.test_client()` y token `SGI`/`Voucher`
firmado con `TOKEN_MASTER_KEY`, sobre vouchers **desechables** borrados al final
(el voucher real id 1 quedó intacto):

- forms: `contract` `null` / omitido / `0` / `1` validan; `"abc"` → error; el form de
  herramientas sigue exigiendo `contract`; `-3` → `None`;
- `POST` con `contract: null` → 201 y `NULL` en BD; `POST` omitido → 201 y el `GET`
  de lista lo devuelve con `"contract": null`;
- `PUT` con `contract: 3` → 200 y `3` en BD (antes se ignoraba);
- `PUT` con `99999` → 400 con el mensaje nuevo y **nada a medias** (contrato y
  `brand` intactos);
- `PUT` con `0` → 200 y `NULL` en BD;
- PDF del voucher sin contrato → 200 `%PDF`.

`pyrefly` sin errores nuevos.

## Al modificar

- No volver a hacer `contract` obligatorio en los forms del vehicular sin decidir qué
  pasa con los vouchers que ya quedaron en `NULL`.
- Si herramientas/seguridad llegan a necesitar "sin contrato", basta con su form +
  el mismo `_vehicle_contract_or_none` (el DDL ya lo permite a nivel tabla).
- Un JOIN futuro de vouchers a `contracts` debe ser `LEFT JOIN`: con `INNER` los
  vouchers sin contrato desaparecen.
