# Remisión limitada de los líderes (`P-216`)

Fecha: 2026-10-29 · **Estado: hecho y verificado contra dev** (`Tests/tester_remision_limitada.py` 21/21; regresión `tester_remission_cancel` 32/32 y `tester_remission_no_attachments` 25/25). Sin DDL. Decisiones del grill del 2026-10-29 (Q6, Q8 y Q9) en [`permisos_administracion.md`](permisos_administracion.md), Notas posteriores.

## Qué cambia

Un token que entra a la tabla de control **sin ningún permiso de remisiones de Cobranza** (`Administracion`, `adminCobranza`, `adminRem` o `Administrator`) llegó solo por `Operaciones`: es un líder y captura la **remisión limitada** (ver `GLOSSARY.md`). Para ese token:

- **`POST·PUT /remissionControlTable` no aceptan las llaves del bloque de administración**: `received_date`, `status_rep_admi`, `remission_sent_date_client`, `remission_sent_by`, `total_sin_iva_admi` y `remission_total` → 400. Sí acepta las comunes, como `pedido` y `remito`, que también captura el líder.
- **`PUT` rechaza una remisión que ya tiene partidas**, porque Administración ya la completó → 400.
- **Solo sus contratos**: `contracts` y `contracts_temp` de `heads`, la misma regla que SM (líder y, si no es líder, auxiliar).
  - `GET /remission-<id>`, incluido `-1`, filtra a las remisiones de esos contratos. Una ajena responde como si no existiera: `200` con `data: []`.
  - `POST` exige un `contract_id` de sus contratos. Sin contrato, el líder no vería después la remisión que creó.
  - `PUT` exige que la remisión sea de sus contratos y que el `contract_id` nuevo, si lo cambia, también lo sea.
- `DELETE /remission` sigue cerrado: es solo de `_REM`.
- Para `Administracion`, `adminCobranza`, `adminRem` y `Administrator` nada cambia. Tampoco para `Operaciones` junto con alguno de ellos.

**Anexos, sin alcance por contrato** (`P-225`, decisión del usuario del 2026-10-29): `POST·DELETE /remission/attachment-<id>` siguen filtrando solo por permiso.
- `Operaciones` hoy equivale a los líderes.
- El front ya les oculta los archivos de las remisiones que no son suyas.
- Filtrar los anexos por contrato se considerará a largo plazo.

## Capas tocadas

```
rs    rs_Admin_collections.py   _is_limited_remission (no tiene _REM); se pasa limited= al POST/PUT de
                                /remissionControlTable y al GET /remission-<id>; el POST pasa las llaves crudas
mw    MD_Admin_Collections.py   _CONTROL_ADMIN_ONLY_KEYS, _leader_contract_ids, _limited_admin_keys_error,
                                _limited_contract_error, _remission_has_items; checks en create/update de la
                                tabla de control y filtro en get_remission_from_api
db    heads_controller.py       sin cambios (check_if_leader / check_if_auxiliar_with_contract, los de SM)
```

Los parámetros nuevos son keyword con default `False`, así que los demás llamadores no cambian.

## Contrato mínimo para el front

- **Base** `/GUI/api/v1/admin/collections` · **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Permisos exactos**:
  - `POST·PUT /remissionControlTable` y `GET /remission-<id>`: `App.Department.Operaciones`, `Administracion`, `adminCobranza` o `adminRem` (`Administrator` pasa siempre).
  - Las reglas de arriba aplican cuando el token solo tiene `Operaciones` de esa lista.
- **Crear (líder)**: `POST /remissionControlTable` con `{"metadata": {...}}`, sin `items`:
  - obligatorios `date`, `folio`, `client_id` y **`contract_id` de uno de sus contratos**;
  - opcionales los del bloque de operaciones: `plant`, `location`, `general_description`, `comments`, `activity`, `area`, `pedido`, `remision`, `remito`, `user`, `user_id`, `quotation_id`, `totalSinIva`, `statusReport`, `date_report`, `date_sign`, `date_office` y `remission_sent_date`.

  ```json
  {"metadata": {"date": "2026-10-29 09:00:00", "folio": "R-123", "client_id": 40, "contract_id": 4,
                "activity": "Mantenimiento", "pedido": "PED-1", "totalSinIva": 1500.0, "statusReport": 1}}
  → 201 {"data": {"id_remission": 210, "balance_control_id": null, "delivery_control_id": null},
         "msg": "Ítem de tabla de control creado correctamente (ID 210)", "error": null}
  ```
- **Editar (líder)**: `PUT /remissionControlTable` con el mismo `metadata` más `id`. Mismo merge de siempre: lo no enviado no se toca.
- **Errores** (todos `400` con envelope):

  | Caso | `error` | `data` |
  |---|---|---|
  | manda una llave de administración | `"campos de administración"` | `{"keys": ["status_rep_admi", ...]}` |
  | `contract_id` ausente o ajeno, o la remisión es de otro contrato | `"contrato fuera de alcance"` | `{"contract_id": 10}` |
  | la remisión ya tiene partidas | `"remisión completada"` | `{"id_remission": 42}` |

  Por ejemplo:

  ```json
  400 {"data": {"keys": ["remission_total"]},
       "msg": "Los campos de administración solo los captura Administración: remission_total",
       "error": "campos de administración"}
  ```
- **Leer**: `GET /remission--1` le devuelve al líder solo las de sus contratos (misma forma de siempre). `GET /remission-<id>` de una remisión ajena responde `200 {"data": [], ...}`.
- **Gotchas**:
  - el bloque de operaciones del front no debe mandar ninguna llave de administración, ni vacía: con un token de líder, mandar `"remission_total": null` también da 400;
  - una remisión con partidas sigue visible para el líder, pero ya no la edita;
  - sin pertenecer a `heads` como líder o auxiliar, un token de solo `Operaciones` no ve ni crea nada.

## Verificación (2026-10-29, dev)

`Tests/tester_remision_limitada.py` 21/21, con el líder 17 y su contrato 4. Crea una remisión desechable y la borra al final; se revisó en solo lectura que ya no está.
- **POST:** llave de administración, contrato ajeno, sin contrato y un token de Operaciones que no es líder dan 400; el alta válida da 201.
- **PUT:** llave de administración, cambio a contrato ajeno, remisión con partidas y remisión de otro contrato dan 400; el válido da 200. `Administracion` con llaves de administración y `Operaciones` + `adminRem` siguen en 200.
- **GET:** el líder ve solo su contrato, incluida la que creó, con las llaves guardadas. `Administracion` ve más. La ajena regresa lista vacía, la propia una fila, y quien no es líder ve lista vacía.
- **DELETE:** del líder, 401.

`tester_permisos_administracion` da 68/69. El que falla ("P-209 vs HEAD: ganan exactamente…") espera un cambio contra `HEAD` que ya se commiteó en `ddd37b0`: es una expectativa vieja, no una regresión. "Nadie pierde" pasa.

pyrefly (`--python-version 3.11`): sin errores en las líneas cambiadas.

## Al modificar

- **Llave nueva de la tabla de control**: decidir de qué bloque es. Si es de administración, agregarla a `_CONTROL_ADMIN_ONLY_KEYS`, además de la receta de 5 lugares de [`control_table_operaciones_y_campos_admin.md`](control_table_operaciones_y_campos_admin.md).
- **Permiso nuevo de Cobranza que deba editar todo**: agregarlo a `_REM`. `_is_limited_remission` lo toma de ahí.
- **Endpoint nuevo abierto a `Operaciones` sobre remisiones**: pasar `limited=_is_limited_remission(data_token)` y aplicar el mismo alcance por contrato.
