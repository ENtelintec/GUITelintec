# Anexos de vales EPP y herramientas sin carrera: una receta para los 3 tipos de vale

Fecha: 2026-10-12 · **Estado: hecho y verificado contra dev (29/29 checks, `Tests/tester_voucher_files_epp_tools.py`; regresión del vehicular 31/31 + 7/7 + 15/15).** Sin DDL. Pendiente `P-103`.

Lleva a los vales **EPP** (`voucher_safety`) y **de herramientas** (`voucher_tools`) la receta que [`checklist_vehicular_anexos_sin_carrera.md`](checklist_vehicular_anexos_sin_carrera.md) aplicó al checklist vehicular, y la saca a un helper compartido para que los tres tipos usen el mismo código (decisión del grill del 2026-10-12, [`planes/plan_accion_2026_10.md`](planes/plan_accion_2026_10.md)).

## Qué estaba mal en EPP y herramientas

| Dónde | Defecto | Efecto |
|---|---|---|
| `POST /voucher/epp/attachment-<id>` · `POST /voucher/tools/attachment-<id>` | `extra_info.files` y `history` en lectura-modificación-escritura | Dos subidas simultáneas: una perdía su entrada |
| idem | Validación de nombre con `and` | Nunca rechazaba un archivo con otro id |
| idem | Vale buscado entre los de los últimos 365 días | Un vale viejo ya no aceptaba anexos |
| `POST /voucher/tools/attachment-<id>` | Buscaba el vale en **`voucher_safety`** (el getter de EPP) | Los anexos de herramientas **nunca encontraban su vale** (400 "no encontrado") salvo que un vale EPP tuviera el mismo id |
| `DELETE /voucher/safety` | Llamaba a `delete_voucher_tools` | Borraba los items pero **dejaba la fila de `voucher_safety`**; `delete_voucher_safety` existía sin usarse |
| `DELETE /voucher/safety` · `DELETE /voucher/tools` | Reescribían el history con la lista que mandaba el front | Pisaban entradas agregadas entretanto (p. ej. un anexo) |

## Qué cambió

- **Helper compartido** `templates/resources/methods/Functions_Aux_Vouchers.py`: `VOUCHER_FILE_KINDS` (por tipo: prefijo S3, `type` del history, firmas → status, status "cancelado" si existe, log), `load_voucher(kind, id)` (lookup por id sin ventana; 400 id inválido, 404 inexistente) y `attach_voucher_file(kind, data, data_token)` con toda la receta: nombre `<id>-<archivo>`, extensión, S3 una vez, escritura condicional con hasta 8 reintentos y 409.
- **Controller genérico**: `VOUCHER_TABLES`, `get_voucher_head(kind, id)` y `update_voucher_files(kind, …, expected_files, cancelled_status)` (una sola sentencia multi-tabla: `JSON_SET` de `$.files` + `JSON_ARRAY_APPEND` del history + `status` opcional). `update_voucher_vehicle_files`/`update_voucher_epp_files`/`update_voucher_tools_files` quedan como wrappers con la firma nueva.
- **Midleware**: `MD_SGI_Vouchers.py` se reduce a dos wrappers (`epp`, `tools`); el vehicular (`MD_SGI.py`) también llama al helper (sus helpers locales desaparecen) y su borrado/descarga usan `load_voucher`.
- **Borrados**: `delete_voucher_safety_api` borra `voucher_safety`; ambos borrados agregan "Voucher eliminado" al history **en BD** (`append_history_voucher`) e **ignoran** el `history` del body (el form lo sigue aceptando para no romper al front).
- Firmas por tipo: EPP y herramientas `firma-aprobado` → 1, `firma-despachado` → 2, `firma-recibido` → 3 (la última que aparezca en el nombre manda, como antes); no tienen estado cancelado, así que la firma siempre escribe. Vehicular sin cambios (1/2, cancelado 3 no se reactiva).

## Capas tocadas

```
methods     Functions_Aux_Vouchers.py (nuevo)   VOUCHER_FILE_KINDS, FILES_WRITE_ATTEMPTS, load_voucher, attach_voucher_file
controller  vouchers/vouchers_controller.py     VOUCHER_TABLES, get_voucher_head, update_voucher_files (+ 3 wrappers)
midleware   MD_SGI_Vouchers.py                  create_voucher_epp_attachment_api, create_voucher_tools_attachment_api (wrappers)
            MD_SGI.py                           create_voucher_vehicle_attachment_api (wrapper), download/delete con load_voucher,
                                                delete_voucher_safety_api (tabla correcta), deletes con append_history_voucher
```

Sin cambios en rutas, modelos/forms ni DDL.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/sgi`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permisos `sgi` o `voucher`. Respuestas JSON `{data, msg, error}`.
- `POST /voucher/epp/attachment-<id>` y `POST /voucher/tools/attachment-<id>` (multipart, **un archivo por request**, campo `file`): request y 201 **iguales que antes** (`data` = llave S3: `eppVoucher/<fecha>/<archivo>` o `toolsVoucher/<fecha>/<archivo>`). El archivo **debe llamarse `<id del vale>-<nombre>`** (ya era la convención; ahora se valida).
- **Ya se pueden subir varios anexos en paralelo** al mismo vale (10 simultáneas → 10/10). Re-subir con el mismo nombre reemplaza, no duplica.
- **Códigos**: **404** vale inexistente (antes 400) · **400** nombre con otro id / sin número al inicio / extensión inválida · **409** solo tras 8 choques seguidos: no se guardó la entrada, el archivo ya está en S3 y el request **se repite tal cual**:

  ```json
  { "data": null,
    "msg": "La lista de anexos cambió mientras se guardaba (subidas simultáneas). El archivo ya está en S3: vuelve a subirlo con el mismo nombre",
    "error": "conflicto de escritura en files" }
  ```

- Herramientas: los anexos **ahora sí funcionan** (antes el alta nunca encontraba el vale).
- `DELETE /voucher/safety` y `DELETE /voucher/tools` (`{id, history}`): misma forma; `history` se ignora (el back agrega la entrada). EPP ahora borra de verdad su fila.

## Al modificar

- Un tipo de vale nuevo = una entrada en `VOUCHER_FILE_KINDS` (helper) y en `VOUCHER_TABLES` (controller); el midleware solo agrega el wrapper y la ruta.
- Todo escritor de `files` pasa `expected_files` y trata 0 filas como "re-leer y recalcular"; nada de efectos no repetibles dentro del ciclo.
- Remisiones (`MD_Admin_Collections`) siguen con su propio ciclo a propósito: otra tabla, categorías y firmas protegidas. Si un fix aplica a ambos, hacerlo dos veces.
- Si EPP/herramientas ganan "cancelado", poner el status en `cancelled_status` del tipo: el `CASE` del controller lo respeta solo.

## Verificación

Contra BD dev (2026-10-12), [`Tests/tester_voucher_files_epp_tools.py`](../Tests/tester_voucher_files_epp_tools.py) (gitignored), **29/29**: por cada tipo, nombre ajeno 400, inexistente 404, alta por HTTP con prefijo propio, vale de 2 años, re-subida, `firma-despachado` → 2 y `firma-recibido` → 3, otras llaves de `extra_info` intactas, 10 subidas en paralelo sin pérdida, history +1 por subida, y `DELETE` por HTTP que borra items + fila propia y agrega "Voucher eliminado" en BD. Regresión del vehicular sobre el helper: `tester_voucher_vehicle_attachments.py` 31/31, accesorios 7/7, PDF completo 15/15. `pyrefly`: 0 errores en los 4 archivos.

## Pendientes

- **[front]** Manejar **409** (repetir) y **404** en los anexos de EPP/herramientas; nombrar `<id>-<archivo>` (ya lo hace).
- **[back]** Descarga de anexos de EPP/herramientas: hoy solo existe `POST /voucher/vehicle/attachment/download`; si el front la pide, es `load_voucher(kind)` + S3 (10 líneas).
