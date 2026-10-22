# Folio sugerido de cotizaciones y OCD (`GET /quotation/folio`) y candado del folio al marcar una OCD

Fecha: 2026-10-22 · **Estado: hecho y verificado contra dev (32/32 checks, `Tests/tester_folio_quotation.py`). Sin DDL. Patrón provisional: el definitivo lo manda administración (`P-157`).**

Fase **F3** del plan [`planes/plan_junta_2026_10_22.md`](planes/plan_junta_2026_10_22.md) (junta con Administración del 2026-10-22: "folios predeterminados de OCD"). Extiende [`quotation_ocd.md`](quotation_ocd.md) y [`ocd_reglas_po_vencimiento.md`](ocd_reglas_po_vencimiento.md); misma receta "patrón + max + 1" que los folios de SM (`GET /folio/cotfc`) y de OC ([`po_folio_generation_from_contract_code.md`](po_folio_generation_from_contract_code.md)).

## Qué cambia

- **`GET /admin/presales/quotation/folio?document_type=quotation|ocd&format=cisco`** devuelve el siguiente folio libre del año con el patrón **provisional** `PREFIJO-AAAA-NNN`: `OCD-2026-007`, `COT-2026-041`, `COT-CISCO-2026-003`. `document_type = ocd` manda sobre `format` (una OCD siempre sugiere `OCD-`); `format = cisco` solo cambia el prefijo de una cotización (F10, [`P-168`](pendientes.md)). El front **pre-llena** `metadata.quotation_code` y el usuario puede editarlo: la sugerencia no reserva nada.
- **Receta**: se leen los `metadata.quotation_code` de **todas** las cotizaciones (cualquier `document_type`) que empiezan con `PREFIJO-AAAA-`, sin mayúsculas; cuentan solo los que terminan en dígitos (`OCD-2026-ABC` u `OCD-2026-007-R1` se ignoran); número = máximo + 1, con 3 dígitos mínimo (`1000` sigue valiendo). Sin folios del año → `001`.
- **Patrón en una sola constante** (`QUOTATION_FOLIO_PREFIXES` + `QUOTATION_FOLIO_DIGITS` en `Functions_midleware_admin`): cuando administración mande el definitivo (`P-157`) se cambia ahí y el `pattern` de la respuesta lo refleja. `provisional: true` en la respuesta mientras tanto.
- **Candado 409 del folio solo en OCD**: al **marcar** una OCD (`POST /quotation` con `document_type = ocd`, `PUT /quotation/ocd` sobre una cotización que aún no es OCD, `PUT /quotation` grande que la marca) y al **renombrar** el folio de una OCD desde el `PUT /quotation` grande, el `quotation_code` no puede coincidir con el de **ninguna otra cotización** (de cualquier tipo), comparado sin mayúsculas ni espacios al borde. Preventa y CISCO **siguen sin candado** (lo histórico tiene repetidos); una OCD ya marcada ajusta sus datos (`/ocd` con `due_date`, `currency`…) y sus partidas sin re-chequear, aunque después alguien haya creado una preventa con su mismo folio. Vive en `metadata` JSON, así que el candado va en código (`find_quotation_by_code`), igual que `client_po_number`.

## Capas tocadas

```
rs          rs_Admin_presales.py                 GET /quotation/folio (administracion) -> suggest_quotation_folio(request.args)
midleware   Functions_midleware_admin.py         QUOTATION_FORMATS · QUOTATION_FOLIO_PREFIXES · QUOTATION_FOLIO_DIGITS · suggest_quotation_folio ·
                                                 _ocd_folio_conflict · _folio_conflict_envelope · create_quotation_from_api / update_quotation_ocd_from_api /
                                                 update_quoation_from_api (409 del folio)
controller  quotations_controller.py             get_quotation_codes_by_prefix (LIKE sin mayúsculas) · find_quotation_by_code (UPPER(TRIM()) = …)
```

Sin cambios en `api_contracts_models.py`: el GET va por query string y el 409 reutiliza las llaves que ya existen.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales` (permiso `administracion`). **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Respuesta**: siempre JSON `{data, msg, error}`; `error` `null` en éxito, lista de strings en 400/409 de midleware. 401: `{"error": "..."}` sin envelope.

### `GET /quotation/folio`

| Query | Valores | Default |
|---|---|---|
| `document_type` | `quotation` · `ocd` (sin mayúsculas) | `quotation` |
| `format` | `cisco` o vacío | vacío |

| Código | Cuándo | Respuesta |
|---|---|---|
| **200** | siempre que lea la BD | `data: {"folio": "OCD-2026-007", "pattern": "OCD-AAAA-NNN", "document_type": "ocd", "format": "", "year": 2026, "number": 7, "last_folio": "OCD-2026-006", "provisional": true}` · `msg: "Folio sugerido OCD-2026-007"` |
| **400** | parámetro inválido | `error: ["document_type debe ser quotation u ocd"]` / `["format debe ser cisco o vacío"]` |

`last_folio` es `null` cuando el año no tiene folios con el patrón. Pedirlo al abrir el formulario (nuevo) y volver a pedirlo si el usuario cambia el tipo o el formato; el usuario puede sobreescribir el valor.

### 409 del folio (`POST /quotation` · `PUT /quotation/ocd` · `PUT /quotation`)

```json
{
  "data": {"id_quotation": 51, "quotation_code": "OCD-2026-007", "conflict_quotation_id": 48},
  "msg": "Ya existe la cotización 48 con el folio 'OCD-2026-007'",
  "error": ["quotation_code repetido: el folio de una OCD no se repite"]
}
```

`id_quotation` es `null` en el `POST`. Se distingue del 409 de `client_po_number` ([`ocd_reglas_po_vencimiento.md`](ocd_reglas_po_vencimiento.md)) por la llave en `data` (`quotation_code` vs `client_po_number`) y por el texto de `error`. Orden de validación: llaves OCD (400) → `client_po_number` (400/409) → folio (409) → fechas de entrega (400).

### Gotchas

- La sugerencia **no reserva** el folio: dos usuarios que abren el formulario a la vez reciben el mismo número y el segundo en guardar como OCD recibe el 409 (basta con volver a pedir el folio). En preventa el segundo se guarda repetido, como hoy.
- El contador mira **todas** las cotizaciones, no solo las OCD: una preventa guardada a mano como `OCD-2026-050` hace que la siguiente OCD sugiera `051`.
- El año es el del **servidor** al momento de pedirlo (`datetime.now()`), no el de `emission`.
- La licitación ganada que se marca OCD conserva `tender_number` como folio ([`ocd_reglas_po_vencimiento.md`](ocd_reglas_po_vencimiento.md)); el candado la cubre igual (409 si alguna cotización ya tiene ese código, cosa que la `UNIQUE` de `tenders` evita entre licitaciones).

## Al modificar

- **Patrón definitivo (`P-157`)**: cambiar `QUOTATION_FOLIO_PREFIXES` (prefijo por tipo) y `QUOTATION_FOLIO_DIGITS`; si el patrón deja de ser `PREFIJO-AAAA-NNN` (p. ej. sin año o con mes), ajustar `suggest_quotation_folio` (el `prefix` y el `pattern`) y la cola numérica que se parsea; los folios ya guardados con el provisional no se tocan.
- **Candado también en preventa/CISCO**: quitar la condición `document_type != "ocd"` de `_ocd_folio_conflict` y, antes, limpiar los repetidos históricos (DML) o el `PUT` grande de esas cotizaciones empezará a dar 409.
- **Reservar el folio** (sin repetidos entre dos usuarios): necesitaría una tabla de secuencias o un `UNIQUE` sobre una columna generada de `metadata.quotation_code` (DDL); hoy no.
- **Otro tipo de documento**: agregar su prefijo a `QUOTATION_FOLIO_PREFIXES` y su valor a `QUOTATION_DOCUMENT_TYPES` / `QUOTATION_FORMATS`; la receta es la misma.
