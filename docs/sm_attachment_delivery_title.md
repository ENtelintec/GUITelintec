# Attachment de SM: `timestamp` y `title` por entrega (y fix del endpoint roto)

`POST /sm/attachment-<id_sm>` sube la firma de una entrega (S3) y ahora cada
objeto de `extra_info["files"]` guarda **cuándo** fue la entrega y **qué número
de entrega** es — la base para pre-llenar la tabla de entregas/firmas del PDF
de la SM ([`sm_pdf_grid_redesign.md`](sm_pdf_grid_redesign.md)).

## Las capas tocadas

```
HTTP    rs_SM.py  /attachment-<string:id_sm>      -> lee `title` del form multipart
modelos api_sm_models.py  expected_files_attachment_sm -> parser propio de SM (file + title)
mid     MD_SM.py  create_sm_attachment_api        -> fix de resolución de SM + campos nuevos
```

El endpoint usaba el parser genérico `expected_files_attachment` de
`api_sgi_models`; ahora tiene el suyo (`expected_files_attachment_sm`) para no
alterar el swagger de los endpoints SGI al agregar `title`.

## El objeto de `files`

```json
{
    "filename": "12-firma-recibido.pdf",
    "path": "smData/2025/03/03/12-firma-recibido.pdf",
    "timestamp": "2026-07-10 13:55:19",
    "title": "Entrega 2 parcial"
}
```

- `timestamp`: momento del upload (`format_timestamps`, tz del software) — es
  la fecha de la entrega.
- `title`: viene del campo de form `title` (opcional, multipart); si no se
  manda, se genera `"Entrega N"` con `N = len(files) + 1`.
- Los files viejos (solo `filename`/`path`) siguen siendo válidos: los
  consumidores deben leer estos campos con `.get(...)`.

Reglas previas que se conservan: el filename debe contener `firma-recibido`
(cambia el status de la SM a 5 "firmado"), extensiones válidas
`pdf|jpg|jpeg|png|zip|webp`, key S3 `smData/<fecha de la SM>/<filename>`.

## Contrato para el front

```
POST /GUI/api/v1/sm/attachment-<id_sm>
Authorization: <token JWT crudo, sin "Bearer ">
Content-Type: multipart/form-data
```

| Parte | Tipo | Requerido | Notas |
|---|---|---|---|
| `file` | archivo (files) | sí | El **nombre del archivo** debe ser `<id_sm>-firma-recibido.<ext>` (debe contener `firma-recibido` y empezar con el id de la SM). Extensiones: `pdf`, `jpg`, `jpeg`, `png`, `zip`, `webp`. |
| `title` | texto (form) | no | Título de la entrega, p. ej. `"Entrega 2"` o `"Entrega parcial tubería"`. Si se omite o va vacío, el back genera `"Entrega N"` según cuántos attachments ya tenga la SM. |

Ejemplo:

```bash
curl -X POST "$HOST/GUI/api/v1/sm/attachment-12" \
  -H "Authorization: $TOKEN" \
  -F "file=@12-firma-recibido.pdf" \
  -F "title=Entrega 2"
```

Respuestas:

- **201** — `{"data": "smData/2025/03/03/12-firma-recibido.pdf", "msg": "Archivo adjunto agregado: ...", "error": null}` (`data` = key S3). El status de la SM pasa a **5 (firmado)** y el file queda registrado en `extra_info["files"]` con `timestamp` y `title`.
- **400** — `{"data": null, "msg": <motivo>, "error": ...}`. Motivos: sin archivo, filename sin `firma-recibido`, extensión inválida, id del filename no corresponde a la SM, SM inexistente, error de S3.
- **401** — token inválido o sin permiso (`administracion` u `operaciones`).

Cambio necesario en el front: **solo agregar la parte `title` al FormData** que ya
manda (opcional — sin `title` todo sigue funcionando y el back autonumera). Los
GET de SM exponen los files con los campos nuevos dentro de `extra_info`.

## Bug corregido: el endpoint fallaba siempre

`create_sm_attachment_api` trataba el resultado de `get_sm_by_id` como **lista
de SMs** (iteraba buscando `item[0] == id_sm` y antes exigía
`isinstance(result, list)`), pero `get_sm_by_id` devuelve **una sola fila**
(tupla, `fetchone`). El guard rechazaba todo con
`"No se pudo obtener la SM: resultado no es una lista"` → el endpoint nunca
llegó a subir un archivo. Ahora usa la tupla directa con guard de
`result[0] is None` / id mismatch. También se protegieron
`json.loads(sm_data[14])`/`[13]` contra NULL.

## Al modificar

- Si el attachment gana más campos (quién entrega/recibe, etc.), agregarlos al
  parser `expected_files_attachment_sm`, leerlos en `rs_SM` con
  `request.form.get(...)` y anexarlos al objeto en `create_sm_attachment_api` —
  es un form multipart, **no** JSON (no hay WTForms aquí).
- Pendiente (siguiente paso): `print_deliveries_sign_table_sm` debe recibir la
  lista de `files` (no el conteo) y pre-llenar la columna "Fecha de Entrega"
  con `timestamp` y el `No.`/título con `title`; las firmas siempre en blanco.
