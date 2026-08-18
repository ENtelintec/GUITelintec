# Descarga de SM (PDF/Excel): SM inexistente y parseo defensivo de fechas/valores

Descargar una SM con un `sm_id` inexistente (p. ej. `GET /sm/download/pdf/1`
cuando los ids reales empiezan en 12) **tronaba con 500**
(`AttributeError: 'NoneType' object has no attribute 'strftime'`) en vez de
responder "no encontrada". Este documento describe la causa raíz y el estado
actual tras corregirla.

## Causa raíz: `JSON_ARRAYAGG` sin `GROUP BY`

`get_sm_by_id` / `get_sm_by_folio`
([`sm_controller.py`](../templates/controllers/material_request/sm_controller.py))
agregan los items con `JSON_ARRAYAGG(JSON_OBJECT(...))`. Un agregado **sin
`GROUP BY`** siempre produce exactamente una fila: si el `WHERE` no matchea,
MySQL devuelve **una fila con las 15 columnas en NULL** en lugar de cero filas.
El check `len(result) == 0` del midleware pasaba (len = 15) y el código seguía
con puros `None`.

**Fix**: `GROUP BY mr.sm_id` en ambas queries. Con él, un id/folio inexistente
devuelve cero filas → `fetchone()` no regresa tupla → el guard existente
`isinstance(result, tuple)` convierte eso en
`(False, "No SM entries found or error in query", [])`. A `get_sm_by_folio` se
le agregó el mismo guard que ya tenía `get_sm_by_id`.

Esto protege **todos** los call sites (6 en
[`MD_SM.py`](../templates/resources/midleware/MD_SM.py), 2 en
[`MD_Purchases.py`](../templates/resources/midleware/MD_Purchases.py)): todos
chequean `flag` y antes recibían `flag=True` con la fila de NULLs (los que hacen
`json.loads(result[10])` habrían tronado igual).

## Las capas tocadas

```
HTTP  rs_SM.py  /download/pdf/<id> y /download/excel/<id>  -> pasan el envelope de error tal cual
mid   MD_SM.py  dowload_file_sm                            -> not-found 404 + parseo defensivo
DB    sm_controller.py  get_sm_by_id / get_sm_by_folio     -> GROUP BY mr.sm_id + guard de tupla
```

(No hay capa de modelos: son GET por path param, sin body.)

## Contrato de error de `dowload_file_sm`

Antes devolvía el string `"None"` con 400 para cualquier fallo y `rs_SM`
respondía el genérico "No se pudo descargar el archivo". Ahora (alineado a
[`sm_response_envelope.md`](sm_response_envelope.md)):

- SM inexistente → `{"data": None, "msg": "SM con id {id} no encontrada", "error": ...}`, **404**
- Falla `FileSmPDF` → `{"data": None, "msg": "No se pudo generar el PDF de la SM con id {id}", "error": ...}`, **400**
- Éxito → `(ruta_del_archivo, 200)` y `rs_SM` hace `send_file`.

`rs_SM` (pdf y excel) devuelve `data, code` sin re-empaquetar cuando
`code != 200`. Los `# pyrefly: ignore` en los `send_file` son porque el retorno
es unión `dict | str` y pyrefly no narrowea por `code == 200`.

## Parseo defensivo en `dowload_file_sm`

Para SMs existentes con campos NULL (el esquema lo permite aunque hoy la BD dev
no tenga casos), la política es **normalizar a defaults y siempre generar el
documento** (celda vacía donde falte dato), no rechazar:

- `date` / `critical_date`: `pd.to_datetime(x, errors="coerce")` solo si el
  valor no es falsy; al formatear, `strftime` solo si
  `isinstance(x, datetime) and not pd.isnull(x)`, si no → `""`. (Antes
  `critical_date.strftime(...)` iba sin guard — ahí reventaba el 500.)
- `comment` del item: `item.get("comment") or ""` antes de `.lower()` (la
  detección de estatus cae a `"pendiente"`).
- `observations` NULL → `[]` (antes acababa como `[None]`).
- Items: una SM **sin items** produce `[{'id': None, ...}]` por el
  `LEFT JOIN sm_items` + `JSON_ARRAYAGG`; se filtran los items con
  `id` NULL antes de iterar.

## Bugs de valores corregidos de paso

- **Typo `dispached`**: el código leía `item["dispached"]` pero el SQL emite la
  clave `dispatched` → la columna de cantidad suministrada imprimía `"None"` en
  **todos** los PDFs/Excels. Ahora `item.get("dispatched") or 0`.
- **Contador de items congelado**: `counter = 1` nunca se incrementaba → la
  columna "Item"/"No." decía 1 en todas las filas. Ahora
  `enumerate(items, start=1)`.
- **Encabezado del Excel**: la columna decía `"Stock"` pero contiene lo
  despachado; renombrada a `"C. Suministrado"`, igual que el PDF
  ([`dict_wrappers_headers["SM"]`](../templates/forms/StorageMovSM.py)).

## Al modificar

- Cualquier query nueva que use `JSON_ARRAYAGG`/agregados con un `WHERE` por id
  **necesita `GROUP BY`** (o un check de `result[0] is None` en el caller) — si
  no, un id inexistente devuelve una fila de NULLs que pasa los checks de
  "encontrado".
- Si `dowload_file_sm` gana campos nuevos en el documento, mantener la política:
  default vacío + documento generado; los errores siempre como envelope
  `{data, msg, error}` con el ID en el `msg`.
- La clave del item es `dispatched` (con t); `dispached` no existe en el JSON
  del SQL.
