# Catálogo de contratos de uso general (`GET /common/contracts`)

Las pantallas que relacionan algo con un contrato (activos, vouchers, el checklist
vehicular de SGI...) guardan `contracts.id`, pero no tenían de dónde sacar la lista:
`GET /admin/presales/contract/-1` solo lo abre `administracion`, y
`GET /admin/presales/contracts/abreviations` (administracion/rrhh/operaciones/sm)
devuelve la `metadata` completa **con saldos** y mezcla departamentos y áreas por
`UNION`. Se agrega un catálogo **de propósito general** con el permiso `Common`,
con solo datos no sensibles. Mismo patrón que
[`common_employees_directory.md`](common_employees_directory.md).

## Las 4 capas

```
HTTP    rs_Common.py  /contracts  (get)                     -> token con department="common"
modelos — (GET sin payload; solo expected_headers_per)
mid     Functions_midleware_admin.py  get_contracts_catalog  -> arma los dicts + envelope
DB      contracts_controller.py       get_contracts_catalog_db -> SELECT solo de campos públicos
```

- [`get_contracts_catalog_db`](../templates/controllers/contracts/contracts_controller.py)
  es un **SELECT nuevo**, no un filtro sobre `get_contract`: extrae de `metadata`
  solo `identifier`, `planta`, `area`, `location` y `abbreviation_sm`
  (`JSON_EXTRACT` puntual), nunca la metadata entera, así un cambio futuro no puede
  filtrar saldos. `LEFT JOIN sql_telintec.customers_amc` para `client_name`.
- `NULLIF(JSON_UNQUOTE(...), 'null')`: `JSON_UNQUOTE` de un `null` JSON devuelve la
  **cadena** `'null'`; así sale `null` real. Clave ausente → `NULL` también.
- Recibe `data_token` → respeta el switch a la BD de test (`is_tester`).
- **Sin filtro de vigencia**: la tabla no tiene noción de contrato activo
  (`metadata.status` es `0`/`1`/`None` sin semántica y `estatus` es texto libre
  vacío), así que se devuelven todos.
- Orden: `identifier`, luego `id`.
- Sin `GET /common/contract/<id>`: quien tenga un `contract` guardado resuelve la
  etiqueta desde la lista.

## Permiso

Solo `department="common"` (`App.Department.Common`; en dev lo tienen 90 de 92
usuarios, en la práctica "cualquier usuario logueado"). Cualquier permiso con
`administrator` también pasa. Un usuario solo con `SGI`/`Voucher` **no** entra: se le
asigna `Common`.

## Contrato mínimo para el front

- **Base path**: `/GUI/api/v1/common`
- **Endpoint**: `GET /contracts`
- **Auth header**: `Authorization: <jwt>` — el **JWT crudo, NO `Bearer <token>`**.
  El token debe tener el permiso `Common` (o `administrator`).
- **Request**: sin body ni query params.
- **Response**: siempre JSON `application/json` con el envelope `{data, msg, error}`.
- **Valor para guardar**: `id` (es `contracts.id`, lo que piden por ejemplo
  `vouchers_general.contract`, `balance_controls.contract_id`,
  `purchase_management.contract_id`). Etiqueta sugerida en selectores:
  `identifier` + `abbreviation`.

Campos de cada elemento de `data`:

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int | `contracts.id` — el valor a guardar |
| `code` | str | número de contrato (`6700305000`) |
| `abbreviation` | str \| null | columna `abbreviation` (`CI`, `G`, `MTTO`...) |
| `abbreviation_sm` | str \| null | `metadata.abbreviation_sm` (la que usan los lookups de SM) |
| `identifier` | str \| null | nombre legible (`CCTV INFRA AMN`) |
| `planta` | str \| null | tal cual está en BD (en dev casi siempre `"0"`) |
| `area` | str \| null | |
| `location` | str \| null | |
| `client_id` | int | `sql_telintec.customers_amc.id_customer` |
| `client_name` | str \| null | nombre del cliente (`null` si el cliente ya no existe) |

**200 — con resultados**
```json
{
  "data": [
    {
      "id": 4, "code": "6700319971", "abbreviation": "A", "abbreviation_sm": null,
      "identifier": "AUTO 2023", "planta": "0", "area": "", "location": "location temporal",
      "client_id": 40, "client_name": "TERNIUM"
    }
  ],
  "msg": null,
  "error": null
}
```

**200 — tabla vacía** (no es error)
```json
{"data": [], "msg": null, "error": null}
```

**400 — falla de BD**
```json
{"data": [], "msg": "No se pudo obtener el catálogo de contratos", "error": "<error sql>"}
```

**401 — token inválido o sin `Common`**
```json
{"error": "No autorizado. Token invalido"}
```

Gotchas: la lista vacía es **200**, no 4xx; el 401 no trae `data`/`msg`; los campos
de `metadata` pueden venir `""` o `null` (no se normalizan).

## Verificación

Contra BD dev con `app.test_client()` y tokens firmados con `TOKEN_MASTER_KEY`
(12 checks): 200 con `Common` y con `administrator`; envelope; exactamente los 10
campos; los 10 contratos de la tabla; orden por `identifier`; `abbreviation_sm` `null`
real (no `'null'`); `client_name` por JOIN; ningún `saldo` en el cuerpo; 401 con solo
`SGI`/`Voucher`, sin header y con `Bearer <jwt>`. `pyrefly` sin errores nuevos.

## Al modificar

- **No agregar** saldos (`saldo_*`, `remision_mxn`), `ceco`, `coordinador`, HES,
  `timestamps` ni `quotation_id`: son datos de Administración y van por
  `/admin/presales/*` con su permiso.
- Un campo nuevo toca las dos capas: el `SELECT` de `get_contracts_catalog_db` y el
  desempaquetado/dict de `get_contracts_catalog` (el orden de columnas debe
  coincidir). Si sale de `metadata`, con el mismo `NULLIF(JSON_UNQUOTE(...), 'null')`.
- Si algún día existe "contrato vigente", el filtro va aquí (query param opcional),
  no en el front.
- Primer consumidor: el selector de contrato del checklist vehicular →
  [`checklist_vehicular_contrato.md`](checklist_vehicular_contrato.md).
