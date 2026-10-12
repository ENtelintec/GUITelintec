# Anexos del checklist vehicular sin carrera, sin ventana de fecha y alta con rollback

Fecha: 2026-10-12 · **Estado: hecho y verificado contra dev (31/31 checks, `Tests/tester_voucher_vehicle_attachments.py`; regresión de accesorios 7/7 y PDF completo 15/15).** Sin DDL.

Cierra los hallazgos que dejó [`checklist_vehicular_full_pdf.md`](checklist_vehicular_full_pdf.md) en el alta de anexos y el "alta sin rollback" de [`checklist_vehicular_accessories.md`](checklist_vehicular_accessories.md). Es el primer ítem del Bloque A de [`planes/plan_accion_2026_10.md`](planes/plan_accion_2026_10.md).

## Qué estaba mal

| Dónde | Defecto | Efecto |
|---|---|---|
| `POST /voucher/vehicle/attachment-<id>` | `extra_info.files` y `vouchers_general.history` se leían, se modificaban en Python y se reescribían completos | Dos subidas simultáneas al mismo voucher: una **perdía su entrada** (el objeto quedaba en S3, pero no en el voucher) |
| idem | La validación "el archivo se llama `<id>-…`" llevaba `and` en vez de `or` | **Nunca rechazaba** un archivo nombrado con otro id |
| idem, `POST …/attachment/download` y `DELETE /voucher/vehicle` | Buscaban el voucher entre los de los **últimos 365 días** | Un checklist de más de un año respondía 400 "no encontrado": sin anexos nuevos, sin descargar los que tenía y sin poder eliminarse/cancelarse |
| `POST /voucher/vehicle` | Si fallaba el `INSERT` de `voucher_vehicle` (p. ej. `model` > 100 caracteres, 1406) o el del history, la fila de `vouchers_general` recién creada se quedaba | **Huérfano** invisible para todos los GET (van por `JOIN`). El "revertido" de "ningún item se pudo crear" tampoco la borraba |
| `DELETE /voucher/vehicle` (status 0) | Llamaba a `delete_voucher_item(id_voucher)`, que borra **por `id_item`** | Los items del voucher quedaban huérfanos (y de paso podía borrar un item ajeno con ese número) |

## Qué cambió

**Anexos.** El `UPDATE` de `files` es ahora **una sola sentencia multi-tabla y condicional**:

```sql
UPDATE voucher_vehicle AS vv JOIN vouchers_general AS vg ON vg.id_voucher = vv.id_voucher_general
SET vv.extra_info = JSON_SET(IF(JSON_TYPE(vv.extra_info) = 'OBJECT', vv.extra_info, JSON_OBJECT()), '$.files', CAST(%s AS JSON)),
    vg.history   = JSON_ARRAY_APPEND(IF(JSON_TYPE(vg.history) = 'ARRAY', vg.history, JSON_ARRAY()), '$', CAST(%s AS JSON))
    [, vv.status = CASE WHEN COALESCE(vv.status, 0) = 3 THEN vv.status ELSE %s END]
WHERE vv.id_voucher_general = %s
  AND COALESCE(JSON_EXTRACT(vv.extra_info, '$.files'), JSON_ARRAY()) = CAST(%s AS JSON)   -- la lista leída
```

- Solo se escribe la llave `files` de `extra_info` (las demás se conservan) y el history **crece** en BD, sin reescribir lo leído.
- La comparación es JSON por contenido; sin llave `files` cuenta como `[]`.
- **0 filas significa siempre que otro request cambió la lista** (el history siempre crece, así que nunca hay "0 filas por sin cambios"). El midleware re-lee y recalcula: si ya hay un archivo con ese nombre lo reemplaza (misma llave S3 → una sola entrada); si es firma, recalcula el `status`; un voucher **cancelado (3) no se reactiva** con una firma (el `CASE` está en SQL porque la cancelación pudo llegar después de la lectura).
- Reintenta hasta **8 veces** con espera aleatoria creciente (peor caso ~1.4 s). Si se agotan, responde **409**. El upload a S3 ocurre una vez, antes del ciclo (llave determinista `checklistV/<fecha del voucher>/<archivo>`).
- Cada entrada de `files` gana `timestamp` (las viejas siguen con `filename`/`path` nada más; los lectores no lo necesitan).
- La validación de nombre es real: el archivo **debe** llamarse `<id del voucher>-<archivo>` (así los sube el front y así están en BD: `1-img-1.png` en dev, `<vid>-firma-aprobado.png` en el tester del PDF completo). Otro id → 400; sin número al inicio → 400.

**Sin ventana de fecha.** Alta de anexos, descarga y borrado cargan el voucher con `get_voucher_vehicle_by_id` (el mismo del PDF) a través de `_load_vehicle_voucher`: id inválido → 400, inexistente → **404** (antes 400).

**Rollback del alta.** `_rollback_vehicle_voucher_create` borra items, `voucher_vehicle` (si llegó a crearse) y la fila de `vouchers_general` cuando falla el `INSERT` vehicular, el history inicial o todos los items. Best-effort: si un paso falla se anota en el log de SGI y el 400 se responde igual. Verificado: el alta con `model` de 150 caracteres responde 400 y `COUNT(vouchers_general)` no cambia. En dev no quedaban huérfanos (0 al 2026-10-12).

**Borrado.** `delete_items_voucher(id_voucher)` (todos los items) en vez de `delete_voucher_item`; el history del borrado/cancelación se agrega con `append_history_voucher` (`JSON_ARRAY_APPEND`), sin leerlo. La fila de `vouchers_general` **sigue quedando como rastro** con la entrada "eliminado"/"cancelado": ese comportamiento no cambió.

## Capas tocadas

```
controller  vouchers/vouchers_controller.py   update_voucher_vehicle_files(id, history_entry, files, data_token, status=None, expected_files=None)
                                              (firma nueva: antes recibía history y extra_info completos)
                                              delete_voucher_general(id)  · append_history_voucher(id, entry)
                                              VEHICLE_VOUCHER_CANCELLED_STATUS = 3 · _HISTORY_APPEND_SQL / _json_param
midleware   MD_SGI.py                         _load_vehicle_voucher, _chv_files_from_row, _CHV_FILES_WRITE_ATTEMPTS = 8,
                                              _chv_files_retry_pause, _rollback_vehicle_voucher_create;
                                              create_voucher_vehicle_attachment_api (ciclo de reintento),
                                              download_voucher_vehicle_attachment_api y delete_voucher_vehicle_api (sin ventana),
                                              create_voucher_vehicle_api (rollback)
```

Sin cambios en rutas, modelos/forms ni DDL. Los anexos de vales EPP/herramientas (`update_voucher_epp_files` / `update_voucher_tools_files`) **no se tocaron**: siguen con lectura-modificación-escritura (ver Pendientes).

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/sgi`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Respuestas JSON `{data, msg, error}`. Permisos `sgi` o `voucher`.
- `POST /voucher/vehicle/attachment-<id>` (multipart, **un archivo por request**, campo `file`): request y respuesta 201 **iguales que antes** (`data` = llave S3 del archivo). El archivo **debe llamarse `<id>-<nombre>`** (ya era la convención; ahora se valida de verdad).

  ```json
  { "data": "checklistV/2026/10/12/7-foto1.jpg", "msg": "Archivo adjunto agregado: 7-foto1.jpg al voucher 7 por el empleado …", "error": null }
  ```

- **Ya se pueden subir varios anexos en paralelo** al mismo voucher: ninguna subida aceptada (201) se pierde (verificado con 10 simultáneas: 10/10). Re-subir con el mismo nombre reemplaza la entrada, nunca duplica.
- **Códigos nuevos**:
  - **404** voucher inexistente (antes 400): `{ "data": null, "msg": "Voucher vehicular no encontrado (ID 7)", "error": null }`.
  - **400** nombre con otro id: `msg` = `"El nombre del archivo no corresponde al voucher (empieza con 8, el voucher es 7)"`; sin número al inicio: `"Error al procesar el nombre del archivo (debe empezar con el id del voucher: <id>-<archivo>)"`.
  - **409** solo si la lista cambió 8 veces seguidas mientras se guardaba (contención extrema). No se guardó la entrada; el archivo ya está en S3 y el request **se puede repetir tal cual**:

    ```json
    { "data": null,
      "msg": "La lista de anexos cambió mientras se guardaba (subidas simultáneas). El archivo ya está en S3: vuelve a subirlo con el mismo nombre",
      "error": "conflicto de escritura en files" }
    ```

- Firmas: `…-firma-aprobado.*` → `status 1`, `…-firma-recibido.*` → `status 2`; sobre un voucher **cancelado** (`status 3`) la firma se guarda pero el estado no cambia (el `msg` lo dice).
- `POST /voucher/vehicle/attachment/download` (`{id_voucher, filename}`) y `DELETE /voucher/vehicle` (`{id}`): sin cambio de forma; ahora funcionan para **cualquier** voucher, no solo los del último año, y responden **404** si el id no existe (antes 400).
- `POST /voucher/vehicle`: si falla, responde 400 con `msg` terminado en "operación revertida" y **no queda nada en BD** (antes quedaba un registro invisible).

## Al modificar

- **Todo escritor de `files` del vehicular pasa `expected_files`** (la lista que leyó) y trata 0 filas como "re-leer y recalcular". Sin `expected_files` el `UPDATE` vuelve a ser incondicional y regresa la carrera.
- Lo que depende de la lectura (reemplazo, `status` de firma) va **dentro** del ciclo; lo que no (upload a S3, `timestamp`, validaciones) va fuera. No meter al ciclo efectos no repetibles (notificaciones, logs): van después del `break`.
- El history de `vouchers_general` se agrega con `append_history_voucher` o dentro de `update_voucher_vehicle_files`; no volver a `update_history_voucher`/`update_voucher_general_from_delete` (reescriben la lista completa) salvo en el alta, donde el history nace.
- Si se agrega un borrado de anexos vehiculares, copiar `delete_activity_report_attachment_api` (remisiones): mismo ciclo con `expected_files`.
- Para arreglar lo mismo en EPP/herramientas: `update_voucher_epp_files`/`update_voucher_tools_files` con la misma firma y el mismo ciclo en sus `create_voucher_*_attachment_api`.

## Verificación

Contra BD dev (2026-10-12), [`Tests/tester_voucher_vehicle_attachments.py`](../Tests/tester_voucher_vehicle_attachments.py) (gitignored), **31/31** en dos corridas. S3, notificaciones y logs simulados; voucher temporal borrado al final. Cubre:

- **Rollback**: alta con `model` de 150 caracteres → 400 "revertida" y `COUNT(vouchers_general)` igual que antes.
- **Validaciones**: otro id → 400; sin id → 400; voucher inexistente → 404; extensión inválida → 400; nada llega a S3 en esos casos.
- **Alta por HTTP** → 201 con la llave S3, entrada con `timestamp`, history +1.
- **Voucher de hace 2 años**: acepta anexo, re-subida reemplaza (una entrada), descarga 200.
- **Firmas**: aprobado → 1, recibido → 2; sobre cancelado → 201 y sigue 3.
- **Solo la llave `files`**: otra llave de `extra_info` sobrevive a la subida.
- **Escritura condicional determinista**: `UPDATE` con lista vieja → 0 filas y la subida intermedia sobrevive; con lista fresca → filas > 0; sin llave `files` cuenta como `[]`.
- **Concurrencia real**: 10 subidas simultáneas → 10/10 aceptadas, lista exacta, history +10.
- **Borrado**: voucher de 2 años con 2 items → 200, items 0, fila vehicular fuera, `vouchers_general` con history +1; inexistente → 404.

Regresión: `tester_voucher_vehicle_accessories.py` 7/7 y `tester_checklist_full_pdf.py` 15/15. `pyrefly`: 0 errores en los 2 archivos.

## Pendientes

- **[front]** Manejar el **409** (repetir el request tal cual) y el **404** nuevo; nombrar siempre `<id>-<archivo>` (ya lo hace).
- ~~**[back]** Anexos de vales **EPP y herramientas**~~ — hecho el 2026-10-12 en [`vales_anexos_sin_carrera.md`](vales_anexos_sin_carrera.md).
- **[back]** `category`/`title` en el alta de anexos vehiculares, si el PDF completo necesita clasificar sin inferir por extensión (sigue abierto en [`checklist_vehicular_full_pdf.md`](checklist_vehicular_full_pdf.md)).

## Notas posteriores

- **2026-10-12** (`P-103`): la receta se movió al helper compartido `templates/resources/methods/Functions_Aux_Vouchers.py` (`load_voucher`, `attach_voucher_file`) y el controller quedó genérico por tipo (`update_voucher_files(kind, …)`; `update_voucher_vehicle_files` es un wrapper). `_load_vehicle_voucher`, `_chv_files_from_row` y las constantes de reintento ya no existen en `MD_SGI.py`. Comportamiento y contrato del vehicular sin cambios (31/31). → [`vales_anexos_sin_carrera.md`](vales_anexos_sin_carrera.md)
