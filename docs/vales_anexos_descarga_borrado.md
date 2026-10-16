# Vales EPP, herramientas y vehicular: el `PUT` conserva los anexos; descarga y borrado individual de anexos

Fecha: 2026-10-16 · **Estado: hecho y verificado contra dev (49/49 checks, `Tests/tester_vales_put_anexos.py`; regresión 29/29 + 31/31).** Sin DDL. Cierra el bloqueo del front en `P-125` (reporte del 2026-10-15, [`respuesta_front_2026_10_16.md`](respuesta_front_2026_10_16.md)).

## Qué estaba mal

| Dónde | Defecto | Efecto |
|---|---|---|
| `PUT /voucher/tools` · `PUT /voucher/safety` | `update_voucher_tools` / `update_voucher_safety` hacían `SET ... extra_info = '{}'` (el midleware nunca pasaba `extra_info`) | **Guardar el formulario del vale borraba todos sus anexos** (`extra_info.files`) y cualquier otra llave |
| idem | El history se reescribía con el que mandaba el front más la entrada nueva | Un cliente que no mandara `history` completo (el formulario EPP hasta el 2026-10-15) dejaba el vale con una sola entrada |
| Anexos de EPP y herramientas | Solo existía el alta; el vehicular tenía descarga pero ningún tipo tenía borrado individual (`DELETE /voucher/safety|tools` borra el vale completo) | El front no podía cerrar `P-125` |

Misma clase de defecto que se corrigió en remisiones ([`remission_atomic_writes.md`](remission_atomic_writes.md)): un escritor que pisa llaves de `extra_info` que no son suyas.

## Qué cambió

- **Controller** (`vouchers_controller.py`): `update_voucher_tools` y `update_voucher_safety` ya **no tocan `extra_info`** (quedó fuera del `SET` y del parámetro). Los anexos solo los escribe `update_voucher_files` con `JSON_SET` de `$.files`.
- **Midleware** (`MD_SGI.py`): `update_voucher_tools_api` / `update_voucher_safety_api` agregan su entrada ("Voucher tools/safety actualizado") con `append_history_voucher` (`JSON_ARRAY_APPEND` en BD) e **ignoran el `history` del body** (el form lo sigue aceptando: el front no cambia nada). Igual que ya hacían los `DELETE` desde `P-103`.
- **Helper compartido** (`Functions_Aux_Vouchers.py`): `download_voucher_file(kind, …)` y `delete_voucher_file(kind, …)` para los 3 tipos, más `is_signature_file(kind, filename)`. El vehicular pasa a usar el helper (`download_voucher_vehicle_attachment_api` queda como wrapper).
- **Rutas** (`rs_SGI.py`): `POST /voucher/epp/attachment/download`, `POST /voucher/tools/attachment/download` y `DELETE /voucher/{vehicle|epp|tools}/attachment-<id>`; las tres subidas comparten `_voucher_attachment_upload`.
- **Modelos** (`api_sgi_models.py`): `voucher_download_att_model` / `VoucherDownloadAttachmentForm` (alias del vehicular, mismo body) y `voucher_attachment_delete_model` / `VoucherAttachmentDeleteForm` (`filename`, `reason?`).

### Reglas del borrado

| Caso | Resultado |
|---|---|
| Anexo normal (`<id>-foto.jpg`, `<id>-evidencia.pdf`…) | Se quita de `extra_info.files` y se borra de S3 (la llave lleva el id del vale: no la comparte otro vale) |
| Nombre con marcador de firma del tipo (`firma-aprobado`, `firma-despachado`, `firma-recibido`) | **400 siempre**: la firma movió el status al subirse y borrarla dejaría el vale firmado sin respaldo. Se corrige re-subiendo con el mismo nombre (el alta reemplaza) |
| Archivo que no está en el vale | 404 |
| Vale inexistente | 404 |
| Lista cambiada entre lectura y escritura | Misma escritura condicional del alta (hasta 8 reintentos); si no se logra, 409 y se repite el request |
| Status del vale | Nunca cambia por un borrado |

Orden: MySQL primero (`files` + history en una sentencia), S3 después y best-effort: si S3 falla, el anexo ya no está en el vale y la respuesta lleva `s3_deleted: false` (queda un objeto huérfano, solo ocupa espacio; se registra en el log del área).

## Capas tocadas

```
routes      rs_SGI.py                      _voucher_attachment_upload/_delete/_download (helpers del módulo),
                                           DELETE en Upload{Vehicle,Epp,Tools}VoucherAttachment, Download{Epp,Tools}VoucherAttachment
models      api_sgi_models.py              voucher_download_att_model, VoucherDownloadAttachmentForm (alias), voucher_attachment_delete_model, VoucherAttachmentDeleteForm
midleware   MD_SGI.py                      update_voucher_{tools,safety}_api (append_history_voucher), download/delete_voucher_vehicle_attachment_api (wrappers)
            MD_SGI_Vouchers.py             download/delete_voucher_{epp,tools}_attachment_api (wrappers)
methods     Functions_Aux_Vouchers.py      download_voucher_file, delete_voucher_file, is_signature_file, _find_file
controller  vouchers/vouchers_controller.py update_voucher_tools / update_voucher_safety sin extra_info
```

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/sgi`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permisos `sgi` o `voucher`. Envelope JSON `{data, msg, error}` en todo menos el blob de descarga.
- `<kind>` ∈ `vehicle | epp | tools`. `filename` es el `files[].filename` que devuelve el GET del vale (`<id>-<archivo>`).

### `PUT /voucher/tools` · `PUT /voucher/safety` (sin cambio de request)

Mismo body de siempre. Lo que cambia: **los anexos sobreviven** al guardado y `history` del body **se ignora** (el back agrega su entrada; mandarlo vacío o completo da lo mismo). Ya no hace falta "guardar primero el formulario y subir los anexos al final".

### `POST /voucher/<kind>/attachment/download`

```json
{ "id_voucher": 25, "filename": "25-evidencia.pdf" }
```

- **200** → **blob** del archivo (`Content-Disposition: attachment`); el front decide por el status.
- **404** `{"data": null, "msg": "Archivo no encontrado en el voucher", "error": null}` · **404** `{"data": null, "msg": "Voucher EPP no encontrado (ID 99)", "error": null}` · **400** id inválido, form o S3 (`"Archivo no encontrado en S3: …"`, credenciales, bucket) · **401** `{"error": "..."}`.
- El vehicular tenía esta ruta; **cambia** solo que "archivo no encontrado" ahora es **404** (antes 400) y que ya no hay ventana de 365 días.

### `DELETE /voucher/<kind>/attachment-<id_voucher>`

```json
{ "filename": "25-evidencia.pdf", "reason": "foto repetida" }
```

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `filename` | string | sí | tal cual `files[].filename`; un archivo por llamada |
| `reason` | string | no | va al history del vale: `"Archivo adjunto eliminado: <llave S3> (<reason>)"` |

| Código | Cuándo | Ejemplo |
|---|---|---|
| **200** | eliminado | `{"data": {"id_voucher": 25, "filename": "25-evidencia.pdf", "path": "eppVoucher/2026/10/16/25-evidencia.pdf", "s3_deleted": true, "files": [ …los anexos que quedan, mismo shape que files[] del GET… ]}, "msg": "Archivo adjunto eliminado: 25-evidencia.pdf del voucher 25 por el empleado X", "error": null}` |
| **400** | firma | `{"data": null, "msg": "El archivo 25-firma-recibido.png es una firma y no se puede eliminar (para corregirla vuelve a subirla con el mismo nombre)", "error": "firma protegida"}` |
| **400** | sin `filename` | `{"data": null, "msg": "Estructura de datos inválida", "error": {"filename": ["This field is required."]}}` |
| **404** | archivo no está en el vale | `{"data": null, "msg": "Archivo no encontrado en el voucher", "error": null}` |
| **404** | vale inexistente | `{"data": null, "msg": "Voucher de herramientas no encontrado (ID 99)", "error": null}` |
| **409** | contención (8 choques seguidos) | `{"data": null, "msg": "La lista de anexos cambió mientras se guardaba (escrituras simultáneas). Vuelve a intentar", "error": "conflicto de escritura en files"}` → repetir el request tal cual |
| **401** | token/permiso | `{"error": "No autorizado. Token invalido"}` |

Gotchas: `data.files` del 200 ya es la lista nueva, no hace falta releer el vale. Borrar y subir en paralelo sobre el mismo vale es seguro (misma escritura condicional). Un `filename` que empiece con otro id no existe en ese vale → 404, no 400.

## Al modificar

- Un marcador de firma nuevo va en `VOUCHER_FILE_KINDS[kind]["signatures"]`: el alta lo convierte en status y el borrado lo protege solos.
- Si algún día `extra_info` del vale gana una llave que escriba el `PUT` (p. ej. `notes`), escribirla con `JSON_SET` de esa llave, nunca con `extra_info = %s` completo.
- Remisiones siguen con su propio borrado (`remission_attachment_delete.md`: categorías, `force` para falsos positivos); aquí no hay `force` porque los nombres de firma de los vales son fijos.

## Verificación

Contra BD dev (2026-10-16), `Tests/tester_vales_put_anexos.py` (gitignored), **49/49**: por EPP y herramientas, `PUT` por HTTP con 3 anexos (uno firma) y otra llave en `extra_info` → los 3 anexos y la llave siguen, status intacto (3), history +1 en BD con "actualizado" y la entrada "del front" del body no se escribe. Por los 3 tipos: descarga 200 blob / archivo 404 / vale 404; borrado de firma 400, archivo 404, vale 404, sin `filename` 400 form, borrado 200 con `files` restantes y `s3_deleted`, BD sin el anexo, status intacto, history +1 con motivo, `delete_object` con la llave propia, 6 borrados en paralelo sin pérdida y history +1 por cada uno. Regresión: `tester_voucher_files_epp_tools.py` 29/29, `tester_voucher_vehicle_attachments.py` 31/31. `pyrefly`: 0 errores nuevos en los 7 archivos tocados.

## Pendientes

- **[front]** `P-125`: botones Descargar y Eliminar (con confirmación) en la lista de anexos de Editar vale, consumiendo estas rutas; retirar el aviso "guarda primero el formulario".
