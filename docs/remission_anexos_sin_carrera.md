# Anexos de remisión sin carrera: escritura condicional de `activity_reports.files`

Fecha: 2026-10-09 · **Estado: hecho y verificado contra dev (19/19 checks, `Tests/tester_remission_files_cas.py`).** Sin DDL.

Cierra el pendiente que dejó [`remission_atomic_writes.md`](remission_atomic_writes.md). La lista `files` de anexos era el último escritor de `activity_reports` que hacía lectura-modificación-escritura. Dos subidas en paralelo a la misma remisión (el front sube varios anexos a la vez), o una subida y un borrado simultáneos, podían **perder una entrada**: el objeto quedaba en S3, pero desaparecía de la remisión.

## Qué cambió

El `UPDATE` de `files` ahora es **condicional**: solo aplica si `files` sigue igual a lo que se leyó.

```sql
UPDATE activity_reports SET files = %s, history = JSON_ARRAY_APPEND(...)[, status = CASE ...]
 WHERE id = %s AND COALESCE(files, JSON_ARRAY()) = CAST(%s AS JSON)   -- la lista leída
```

- La comparación es JSON por contenido, no por texto; `NULL` cuenta como `[]`.
- **0 filas significa siempre que otro request cambió la lista**: el `history` crece en cada escritura, así que nunca hay "0 filas por sin cambios".
- Con 0 filas, el midleware **re-lee la remisión y recalcula** con la lista nueva:
  - **Alta**: si ya hay un archivo con ese nombre, lo reemplaza; si es firma, recalcula el `status`, y una cancelada sigue sin reactivarse.
  - **Baja**: vuelve a validar que el anexo exista, si es una firma protegida y si trae `force`.
- Reintenta hasta **8 veces**, con una espera aleatoria creciente (`random.uniform(0, 0.05 × intento)`; peor caso ~1.4 s). Si se agotan, responde **409**.
- El upload a S3 ocurre **una vez, antes** del ciclo. La llave es determinista (`reportActivity/<fecha>/<id>/<archivo>`), así que reintentar no sube otra vez.

## Capas tocadas

```
controller  presales/remisions_controller.py   update_report_activity_files(..., expected_files=None): WHERE condicional
midleware   MD_Admin_Collections.py            create_/delete_activity_report_attachment_api: ciclo de reintento,
                                               _FILES_WRITE_ATTEMPTS = 8, _files_retry_pause
```

Sin cambios en rutas, modelos/forms ni DDL.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/admin/collections`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Respuestas JSON `{data, msg, error}`.
- `POST /remission/attachment-<id>` (multipart, **un archivo por request**: `file` + `category`/`folio`/`title` opcionales) y `DELETE /remission/attachment-<id>`: requests y respuestas 2xx **iguales que antes**.
- **Ya se pueden subir varios anexos en paralelo** a la misma remisión: ninguna subida aceptada (201) se pierde. Verificado con 10 simultáneas: 10/10 aceptadas.
- **409 nuevo**, solo si la lista cambió 8 veces seguidas mientras se guardaba (contención extrema). No se guardó la entrada y el request **se puede repetir tal cual**:

  ```json
  { "data": null,
    "msg": "La lista de anexos cambió mientras se guardaba (subidas simultáneas). El archivo ya está en S3: vuelve a subirlo con el mismo nombre",
    "error": "conflicto de escritura en files" }
  ```

  En el `DELETE` el `msg` es `"La lista de anexos cambió mientras se eliminaba (cambios simultáneos); vuelve a intentarlo"`. Re-subir con el mismo nombre reemplaza el objeto, así que nunca duplica.
- Bajo carrera, un `DELETE` puede responder **400 "Archivo no encontrado"** si otro request lo borró primero, o el 400 de firma protegida si otro lo reemplazó por una firma. Son las mismas respuestas de siempre.

## Al modificar

- **Todo escritor de `files` pasa `expected_files`** (la lista que leyó) y trata 0 filas como "re-leer y recalcular". Sin `expected_files`, el `UPDATE` vuelve a ser incondicional y regresa la carrera.
- Lo que se calcula de la lectura (reemplazo, `status` de firma, reglas de borrado) va **dentro** del ciclo; lo que no depende de ella (upload a S3, categoría, `timestamp`) va fuera.
- No agregar al ciclo efectos que no se puedan repetir (notificaciones, logs, S3 delete): van después del `break`.

## Verificación

Contra BD dev (2026-10-09), [`Tests/tester_remission_files_cas.py`](../Tests/tester_remission_files_cas.py) (gitignored), **19/19** en dos corridas. S3, notificaciones y logs están simulados; la remisión temporal se borra al final. Cubre:

- **Regresión secuencial**: alta por HTTP, reemplazo por mismo nombre, firma → `status 1`, firma protegida 400, inexistente 400, borrado 200.
- **Determinista**: una subida entre la lectura y la escritura → el `UPDATE` con la lectura vieja da 0 filas y la subida intermedia sobrevive; lectura fresca → 1 fila; `files NULL` = `[]`.
- **Concurrencia real** (hilos con barrera):
  - 10 subidas simultáneas → 10 aceptadas, 0 conflictos y `history` +10. Sin la espera aleatoria eran 5/5.
  - 4 borrados + 4 subidas simultáneos → la lista final es exactamente la esperada y el `status` de la firma queda intacto.

`pyrefly`: 0 errores en los 2 archivos.
