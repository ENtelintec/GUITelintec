# Contratos del selector de remisiones (`P-230`)

Fecha: 2026-11-03 · **Estado: hecho y verificado contra dev** (`Tests/tester_contratos_lider.py` 23/23; regresión `tester_remision_limitada` 21/21). Sin DDL. Lo pidió el front al hacer `P-217` (`docs/backend/lideres-sin-catalogo-de-sus-contratos.md` de su repo). Regla de negocio en [`remision_limitada_lideres.md`](remision_limitada_lideres.md).

## Qué cambia

Nuevo `GET /admin/collections/remission/contracts`: una sola llamada para el selector de contratos de remisiones, y el back decide qué lista devuelve.

- **Token limitado** (solo `Operaciones`, sin ningún permiso de `_REM`): solo sus contratos, con la regla de `_leader_contract_ids`. Es exactamente lo que acepta el `POST /remissionControlTable`, así que un contrato del selector ya no puede dar 400 `contrato fuera de alcance`.
- **Cualquier otro token que entre**: todos los contratos.
- **Quién es "líder" aquí**: primero se busca como líder y, solo si no lo es, como auxiliar. Si un empleado es líder del contrato 4 y auxiliar del 9, ve únicamente el 4 (misma regla de SM y de `P-216`).

Antes el líder recibía 401 en `contracts/products`, caía a `abreviations` (todos los contratos) y se enteraba con el 400 al guardar.

**Sin saldos.** Usa la misma consulta sin montos de `GET /common/contracts` (`get_contracts_catalog_db`, ahora con `contract_ids` opcional), no la `metadata` de `contracts/products`, que incluye `saldo_pedido`, `saldo_facturado`, etc. Un selector no los necesita y un líder no debe recibirlos.

## Capas tocadas

```
rs    templates/resources/rs_Admin_collections.py            GET /remission/contracts (_REM_OPS)
mid   templates/resources/midleware/MD_Admin_Collections.py  get_remission_contracts_from_api
db    templates/controllers/contracts/contracts_controller.py get_contracts_catalog_db(data_token, contract_ids=None)
```

Sin modelo ni form: el endpoint no recibe parámetros.

## Contrato mínimo para el front

- **Endpoint**: `GET /GUI/api/v1/admin/collections/remission/contracts`, sin parámetros.
- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Permisos** (cualquiera): `App.Department.Administracion`, `App.Department.adminCobranza`, `App.Department.adminRem`, `App.Department.Operaciones`. `App.Department.Administrator` siempre pasa.
- **200** (`application/json`):

  ```json
  {
    "data": [
      {
        "id": 4,
        "metadata": {
          "contract_number": "6700319971",
          "abbreviation": "A",
          "abbreviation_sm": null,
          "identifier": "AUTO 2023",
          "planta": "0",
          "area": "",
          "location": "location temporal",
          "client_id": 40,
          "client_name": "TERNIUM"
        }
      }
    ],
    "msg": null,
    "error": null
  }
  ```

- **200 con `"data": []`**: un token de solo `Operaciones` que no es líder ni auxiliar de ningún contrato. No es error.
- **401**: `{"error": "No autorizado. Token invalido"}`, también con `adminPreventa`, `adminDB`, `SM` o `RRHH`, y `{"error": "Token not found"}` sin header.
- **400**: `{"data": null, "msg": "No se pudieron obtener los contratos", "error": "<detalle>"}`.
- **Gotchas**:
  - la fila solo trae `id` y `metadata`: **no hay** `items`, `creation`, `timestamps` ni `quotation_id`;
  - la `metadata` trae solo las 9 llaves del ejemplo, sin saldos, y cualquiera puede venir `null` o vacía (`planta` puede ser `"0"`, como en los demás catálogos);
  - `client_name` es `null` si el contrato no tiene cliente en el catálogo, y ya evita pedir `GET /admin/db/clients/allClients`, que a un líder le da 401;
  - con este endpoint, `useContratosLideres` ya no necesita caer a `abreviations` (`P-232`).

## Verificación (2026-11-03, dev)

`Tests/tester_contratos_lider.py` 23/23:

- el líder 17 recibe justo `_leader_contract_ids`, con el contrato 4 y su cliente;
- llaves exactas de la `metadata`, sin saldos ni `items`;
- un contrato fuera de la lista da 400 `contrato fuera de alcance` en el `POST` real;
- `Operaciones` sin ser líder: 200 y lista vacía;
- `Administracion`, `adminCobranza`, `adminRem`, `Operaciones` + `adminRem` y `Administrator` ven todos;
- `Basic`, `adminPreventa`, `adminDB`, `SM`, `RRHH` y sin token: 401;
- auxiliar 110 de dev: sus contratos;
- `GET /common/contracts` no cambia.

## Al modificar

- **Regla de alcance**: vive en `_leader_contract_ids`; el selector y el `POST` deben seguir leyendo la misma.
- **Llave nueva en la `metadata`**: agregarla a `get_contracts_catalog_db` afecta también a `GET /common/contracts`, abierto a más permisos. Nunca meter montos ahí.
