# `PUT /quotation` conserva `exchange_rate` y `codigo` sale del contrato

Fecha: 2026-10-13 · **Estado: hecho y verificado contra dev (18/18 checks, `Tests/tester_quotation_put_metadata.py`; regresión: `tester_quotation_ocd` 35/35, `tester_items_put_ids` 21/21, `tester_quotation_costs` 37/37, `tester_quotation_cost_suggest` 22/22, `tester_delivery_control` 71/71).** Sin DDL; DML de limpieza `quotations_metadata_sin_codigo.sql` pendiente de correr (`P-138`). Pendientes `P-131` (back, hecho), `P-133` (front) y `P-138` (DML).

Lo reportó el front el 2026-10-13 al construir las pantallas de alta y edición de cotización de preventa (`P-119`):

1. **`PUT /quotation` borraba `metadata.exchange_rate`.** El `PUT` reemplazaba la `metadata` completa con lo que trae `MetadataQuotationForm` y solo rescataba las llaves OCD y `status`. El tipo de cambio de cabecera lo escribe `PUT /quotation/costAnalysis` y el form no lo declara, así que **editar la cabecera o las partidas después del análisis de costos lo borraba**. El siguiente análisis en USD sin `exchange_rate` en el request daba 400.
2. **`codigo` era obligatorio y nadie lo lee.** `InputRequired` en el form, pero ninguna lógica, PDF ni consulta viva del back lo usaba (la referencia visible es `quotation_code`; la única lectura era `get_quotation_data_display`, sin llamadores). El Excel de cotización no trae ese dato, así que el front mandaba el folio repetido para pasar la validación. **Decisión del usuario (2026-10-13): si el back no lo usa, se quita.**

## Capas tocadas

```
modelos  api_contracts_models.py       MetadataQuotationForm y metadata_quotation_model sin `codigo`
mid      Functions_midleware_admin.py  update_quoation_from_api: las llaves que el form no declara
                                       se conservan (setdefault sobre la metadata guardada)
ctrl     quotations_controller.py      get_quotation_data_display (sin llamadores) ya no selecciona $.codigo
sql      scripts_db_handle/quotations_metadata_sin_codigo.sql   JSON_REMOVE de $.codigo (idempotente)
```

**Regla nueva del `PUT`:** reemplaza **solo las llaves que declara el form**. Las demás llaves de `metadata` se conservan tal cual: `status` (lo escribe el create), `exchange_rate` (lo escribe el análisis de costos) y cualquier otra que agregue otro endpoint. Las OCD siguen su regla de antes: vacío conserva. Antes `status` tenía su caso aparte y `exchange_rate` se perdía.

Consecuencia para `codigo`: como ya no está en el form, un `codigo` que mande el front **se ignora**, y el que ya traiga una cotización vieja **se conserva** en cada `PUT`. Para que desaparezca de verdad está el DML (dev 6 de 15 cotizaciones con la llave, test 1 de 15).

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/presales`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Respuestas JSON `{data, msg, error}`. Permiso `administracion`.
- **`codigo` ya no existe** en `POST /quotation` ni en `PUT /quotation` (`metadata.codigo`). Si se manda se ignora sin error, pero el front debe **quitar el campo "Código interno"** y dejar de mandarlo. Las cotizaciones viejas pueden traerlo en el `GET` hasta que corra el DML: no pintarlo.
- `quotation_code` **sigue obligatorio** (400 si falta o va vacío). Es la referencia visible de la cotización.
- **`exchange_rate` sobrevive al `PUT /quotation`**. El front no lo manda en ese endpoint (no está en el form y se ignora); se cambia solo con `PUT /quotation/costAnalysis` (`exchange_rate` de cabecera). `GET /quotation/<id>?with_costs=1` lo sigue exponiendo en `data[0].exchange_rate`.
- Respuestas sin cambio:

  ```json
  // PUT /quotation 200
  {"data": {"id_quotation": 51, "items": [{"index": 0, "partida": 1, "qa_item_id": 812, "action": "updated"}]},
   "msg": "Cotización actualizada correctamente (ID 51). Items: 1 actualizado(s)", "error": null}
  // POST/PUT 400 (form), p. ej. sin quotation_code
  {"data": null, "msg": "Estructura de datos inválida", "error": {"metadata": {"quotation_code": ["This field is required."]}}}
  // PUT 404
  {"data": null, "msg": "No se encontró la cotización (ID 99999999)", "error": "Quotation not found"}
  ```

## Al modificar

- **Llave nueva en `quotations.metadata` escrita por otro endpoint** (como `exchange_rate`): no hace falta tocar el `PUT`, se conserva sola. Si en cambio la llave debe poder editarse desde el `PUT`, va al form **y** al `api.model`, y entonces el `PUT` la reemplaza.
- **Quitar una llave del form** no la borra de las cotizaciones guardadas: el `PUT` la conservará. Para retirarla de verdad hace falta un DML, como el de `codigo`.

## Verificación

Contra BD dev (2026-10-13), [`Tests/tester_quotation_put_metadata.py`](../Tests/tester_quotation_put_metadata.py) (gitignored), **18/18**. Crea una cotización temporal y la borra al final. Cubre:

- `POST` sin `codigo` → 201 sin la llave; con `codigo` (front viejo) → 201 y se ignora; `quotation_code` vacío sigue en 400.
- Análisis de costos con `exchange_rate: 18.25` y después varios `PUT /quotation`: `exchange_rate`, `status` y las llaves OCD siguen; `planta` sí se aplica.
- `PUT` con `codigo` → se ignora; una cotización con `codigo` legado lo conserva aunque el request mande otro.
- El `UPDATE` del DML, acotado a la cotización temporal: quita `codigo`, deja el resto, y la segunda corrida toca 0 filas.
- `GET ?with_costs=1` expone el 18.25 y un `costAnalysis` en USD sin `exchange_rate` vuelve a usar el de cabecera (antes del fix daba 400).

`pyrefly`: sin errores nuevos en los archivos tocados.

## Notas posteriores

- **2026-10-28 — `P-138` cerrado.** El usuario corrió el DML en las 3 BDs. verificado en solo lectura en dev y test el 2026-10-28; prod, según el usuario (el modo automático no deja leer su BD): 0 cotizaciones con `metadata.codigo` (dev 16, test 15).
