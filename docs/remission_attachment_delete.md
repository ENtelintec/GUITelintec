# Eliminar un anexo de la remisión (`DELETE /remission/attachment-<id>`)

Los anexos de una remisión (fotos, PDFs, firmas) se suben con
`POST /remission/attachment-<id_report>` y viven en `activity_reports.files`
([`remission_combined_pdf.md`](remission_combined_pdf.md)), pero **no había
forma de quitarlos**: una foto mal subida quedaba en el expediente y en el PDF
combinado para siempre. Este cambio agrega el `DELETE` sobre el mismo recurso, y
de paso corrige dos cosas del `POST` que hacían inseguro el borrado físico.

## Las capas tocadas

```
HTTP    rs_Admin_collections.py  UploadActivityReportAttachment.delete()  -> nuevo método en el Resource existente
modelos api_purchases_models.py  report_activity_delete_att_model
                                 ReportActivityDeleteAttForm              -> filename / reason / force
mid     MD_Admin_Collections.py  delete_activity_report_attachment_api    -> nuevo
                                 _load_remission_for_files                -> helper compartido (alta/descarga/borrado)
                                 _remission_attachment_key                -> llave S3 con id de reporte
                                 _is_protected_signature                  -> qué firma no se borra
                                 _remission_key_belongs_to_report         -> qué llave sí se borra de S3
                                 create_activity_report_attachment_api    -> llave nueva + reemplazo de entrada
BD      remisions_controller.py  update_report_activity_files             -> sin cambios (ya escribía files/history/status)
```

No hay cambio de esquema: `files` sigue siendo la misma columna JSON.

## Reglas del borrado

| Caso | Resultado |
|---|---|
| Archivo con categoría efectiva distinta de `firma` | Se elimina |
| Categoría `firma` **guardada** (`category: "firma"`) o nombre con `firma-realizado` / `firma-recibido` | **400 siempre**, ni con `force` |
| Categoría `firma` **inferida** por la heurística del nombre (`firmado_cliente.pdf` cae en `startswith("firma")`) | 400 sin `force`; se elimina con `force: true` |
| Estatus de la remisión (0 creada / 1 firmada / 2 aprobada) | No limita nada, y el borrado **nunca** toca `activity_reports.status` |
| Mismo `filename` repetido en `files` | Se van **todas** las entradas con ese nombre (apuntan al mismo objeto en S3) |

Las firmas son intocables precisamente para que el estatus no quede huérfano: el
`POST` sube `firma-realizado` → `status = 1` y `firma-recibido` → `status = 2`,
así que borrar una firma dejaría la remisión en "aprobado" sin nada que lo
respalde. **Para corregir una firma equivocada se vuelve a subir con el mismo
nombre**, y el `POST` reemplaza la entrada (ver abajo).

La categoría se resuelve con `_classify_remission_file`, la misma función que
decide qué incrusta el PDF combinado: lo que el PDF trata como firma es
exactamente lo que no se puede borrar.

## Orden de operaciones (MySQL primero, S3 después)

No hay transacción que abarque los dos, así que:

1. `UPDATE activity_reports SET files, history` (el `status` se re-escribe con
   su valor actual). Si falla → **400** y S3 queda intacto.
2. `s3.delete_object` **best-effort**. Si falla, el anexo ya desapareció de la
   remisión (que es lo que se pidió) y solo queda un objeto huérfano en el
   bucket: se responde **200** con `s3_deleted: false`, el motivo en `error` y
   una línea en el log.

Al revés (S3 primero) un fallo del `UPDATE` dejaría una entrada apuntando a una
llave inexistente → el download da 400 y el PDF combinado omite el archivo.

## Llave S3 con id de reporte (cambio en el `POST`)

Antes la llave era `reportActivity/<fecha del reporte>/<filename>`. La fecha es
la **del reporte**, no la de subida, así que dos remisiones de la misma fecha con
un archivo llamado igual (`firma-recibido.png`, `evidencia.jpg`) compartían
objeto y **ya se pisaban al subir**. Con borrado físico eso se vuelve grave:
borrar el anexo de una le borraría el archivo a la otra.

Ahora el `POST` escribe:

```
reportActivity/2026/07/15/459/evidencia-1.jpg
                          ^^^ id_report
```

y el `DELETE` borra de S3 **solo** si la llave trae ese `/<id_report>/`
(`_remission_key_belongs_to_report`). Las llaves heredadas (formato plano) se
desvinculan del reporte pero el objeto se conserva; la respuesta lo dice con
`s3_deleted: false` + `s3_detail`. Los archivos viejos siguen funcionando: cada
uno guarda su propio `path` y todos los lectores (download, PDF) usan ese campo.

## Re-subir reemplaza la entrada (cambio en el `POST`)

Si ya existe una entrada con el mismo `path`, el `POST` la quita antes de
agregar la nueva en vez de hacer `append`. En S3 el objeto ya se sobreescribió
(misma llave), así que dos entradas apuntarían al mismo archivo, y en la lista
del front aparecería duplicado. La respuesta del `POST` gana `replaced: true|false`
y el `history` anota "(reemplaza el archivo previo con el mismo nombre)".

## Auditoría

Igual que el alta: entrada en `activity_reports.history`
(`action: "Eliminar archivo"`, con `reason` y la marca de `force` dentro del
`comment`), `create_notification_permission_notGUI` a `administracion` /
`operaciones` / `sgi`, y `write_log_file`. Es el único rastro que queda de un
archivo que ya no está ni en S3.

## Contrato mínimo para el front

```
DELETE /GUI/api/v1/admin/collections/remission/attachment-<id_report>
Authorization: <token JWT crudo, SIN "Bearer ">
Content-Type: application/json
```

Permisos: `administracion` u `operaciones` (los mismos que para subir).

**Body**

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `filename` | string | sí | Tal cual viene en `files[].filename` del GET de la remisión. Un archivo por llamada. |
| `reason` | string | no | Motivo; se guarda en el `history` del reporte. |
| `force` | bool | no | Solo vence el falso positivo de la heurística de firmas. Sobre una firma real no sirve. |

```bash
curl -X DELETE "$HOST/GUI/api/v1/admin/collections/remission/attachment-459" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "evidencia-1.jpg", "reason": "foto repetida"}'
```

**200 — eliminado**

```json
{
  "data": {
    "id_report": 459,
    "filename": "evidencia-1.jpg",
    "path": "reportActivity/2026/07/15/459/evidencia-1.jpg",
    "category": "photo",
    "removed": 1,
    "s3_deleted": true,
    "s3_detail": "Objeto eliminado de S3",
    "files": [
      {"filename": "anexo-ternium.pdf", "path": "reportActivity/2026/07/15/459/anexo-ternium.pdf",
       "category": "anexo", "folio": "C-1122", "title": "", "timestamp": "2026-07-15 10:12:03"}
    ]
  },
  "msg": "Anexo 'evidencia-1.jpg' eliminado del reporte (ID 459)",
  "error": null
}
```

`data.files` es **la lista ya actualizada**: el front repinta con eso, sin
volver a pegarle al GET de la remisión (que trae items, extra_info, etc.).

**200 — eliminado del reporte pero el objeto sigue en S3**

```json
{
  "data": {"...": "...", "s3_deleted": false,
           "s3_detail": "El anexo se elimino del reporte pero no se pudo borrar el objeto de S3"},
  "msg": "Anexo 'evidencia-1.jpg' eliminado del reporte (ID 459)",
  "error": "An error occurred (AccessDenied) when calling the DeleteObject operation..."
}
```

Para el usuario esto **es un éxito** (el anexo ya no está en la remisión); el
`error` es informativo. Mismo caso con `s3_detail: "Llave heredada (sin id de
reporte): el objeto se conserva en S3"`, que ahí sale con `error: null`.

**400 — el archivo no está en el reporte**

```json
{"data": null, "msg": "Archivo no encontrado en el reporte", "error": null}
```

Borrar dos veces cae aquí (no es idempotente). Es el mismo código que ya usa el
download de anexos para este caso.

**400 — es una firma**

```json
{"data": null,
 "msg": "No se pueden eliminar firmas del reporte. Para corregirla, vuelve a subir el archivo con el mismo nombre y reemplazara a la anterior",
 "error": null}
```

**400 — parece firma por el nombre** (reintentar con `force: true`)

```json
{"data": null,
 "msg": "El archivo 'firmado_cliente.pdf' se clasifica como firma por su nombre. Envia force=true si aun asi quieres eliminarlo",
 "error": null}
```

**404 — el reporte no existe** · **401 — token inválido o sin permiso**

Gotchas:

- El id del reporte va en la **URL**, no en el body.
- `filename`, no `path`: el back resuelve la llave S3 (y borra todas las
  entradas con ese nombre, que comparten objeto).
- `s3_deleted: false` **no** es un fallo del borrado; el anexo sí se quitó.
- `force` se lee del payload crudo y acepta booleano JSON (`true`/`false`) o las
  cadenas `"1"`/`"true"`/`"yes"`/`"si"`. Cualquier otra cosa cuenta como
  `false`; omitirlo es lo normal.
- Para reemplazar una firma: `POST` con el **mismo** `filename`; la respuesta
  trae `replaced: true`.

## Al modificar

- La lectura de la remisión para operar sobre anexos está centralizada en
  `_load_remission_for_files` (alta, descarga y borrado). Si cambia el orden de
  columnas del `SELECT` de `get_remission_by_id`, los índices posicionales
  (`[1]` fecha, `[14]` status, `[15]` history, `[17]` files) se corrigen **ahí y
  solo ahí**.
- La llave S3 se arma únicamente en `_remission_attachment_key`. Si se vuelve a
  cambiar el formato, hay que ajustar en paralelo
  `_remission_key_belongs_to_report`, que es quien decide si el objeto es
  borrable.
- Si algún día se permite borrar firmas, hay que revertir el `status` de forma
  simétrica al alta (2 → 1 si queda `firma-realizado`, si no 0) — es justo la
  razón por la que hoy están bloqueadas.
- Pendiente: no hay borrado en lote. Si el front agrega selección múltiple,
  itera (cada borrado deja su propia entrada de `history`, que es lo deseable).
