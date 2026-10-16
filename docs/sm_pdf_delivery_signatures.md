# Firmas de entrega incrustadas en el PDF de la SM

El PDF de SOLICITUD DE MATERIAL (`GET /sm/download/pdf/<sm_id>`) ahora **incrusta
la firma de quien recibe** en la tabla de entregas, en vez de dejar la celda en
blanco para firmar a mano. Cada attachment de la SM
(`extra_info["files"]`, ver [`sm_attachment_delivery_title.md`](sm_attachment_delivery_title.md))
es una entrega: su firma (imagen capturada por el front) se baja de S3 y se
dibuja dentro de la celda **"Firma de Quien Recibe"**, y la fila pre-llena
**No. / Fecha + Título** con el `timestamp` y el `title` del attachment. Cierra
el pendiente de [`sm_pdf_grid_redesign.md`](sm_pdf_grid_redesign.md).

## Las capas tocadas

```
mid    MD_SM.py  dowload_file_sm            -> arma delivery_files (descarga+downscale S3)
mid    MD_SM.py  _build_sm_delivery_files   -> una fila por attachment; firma no fatal
mid    MD_SM.py  _downscale_signature_image -> baja resolución con PIL (no engordar el PDF)
forms  StorageMovSM.py  print_deliveries_sign_table_sm -> recibe delivery_files, dibuja firma
forms  StorageMovSM.py  FileSmPDF           -> contrato delivery_files (antes delivery_rows)
```

(Endpoint y controller de DB sin cambios; el contrato HTTP es el mismo. Solo PDF
— el Excel de la SM queda igual.)

## Contrato de `FileSmPDF` (cambió)

Antes recibía `"delivery_rows": int`; ahora recibe la lista completa:

```python
{
    "filename_out": str,
    "metadata": {label: valor, ...},
    "products": [(no, nombre, cantidad, udm, suministrado, estatus), ...],
    "delivery_files": [
        {"no": int, "date": str, "title": str, "image_path": str | None}, ...
    ],
}
```

- `image_path`: ruta **local** de la firma ya descargada/redimensionada, o
  `None` si el attachment no es imagen dibujable o falló la descarga.
- La descarga de S3 vive en la capa midleware (`dowload_file_sm`); el form
  **solo recibe rutas locales**, nunca toca la red.

## Cómo se dibuja la tabla de entregas

- **Alto de fila dinámico** (`_sm_delivery_row_height`): `26pt` si la fila solo
  lleva texto; `~60pt` cuando incrusta firma (para que sea legible). También
  crece si la fecha/título hace wrap.
- **Firma** (`_sm_draw_signature_image`): `drawImage` con `ImageReader`,
  preservando aspect ratio, centrada con padding, `mask="auto"` (respeta la
  transparencia del PNG). No fatal: si la imagen no se puede leer, la celda
  queda vacía.
- **Pre-llenado**: "No." = secuencial; "Fecha de Entrega" = fecha del
  `timestamp` (`YYYY-MM-DD`) + `title` en segunda línea; **"Firma de Quien
  Entrega" siempre en blanco** (hoy el back solo captura `firma-recibido`).
- **Paginación por fila** (`new_page_cb`): con muchas entregas la tabla salta de
  página repitiendo el encabezado de columnas (el supuesto viejo "cap 20 = una
  página" ya no aplica con filas de ~60pt). Cap **20** como tope duro.
- Se conserva el campo "Fecha de Entrega Completa" al final.

## Manejo de errores (no fatal)

La generación del PDF **nunca** se cae por una firma:

- Attachment no dibujable (`pdf`/`zip`) o sin `path` → celda en blanco (a mano).
- Falla la descarga de S3 o el decode de la imagen → celda en blanco + entrada
  en el log de SM (`write_log_file(log_file_sm_path, ...)`).
- SM sin attachments → una fila en blanco (comportamiento previo).

## Escalado de imágenes

Dos escalados distintos:

1. **En la página**: `drawImage` con `width/height` calculados por aspect ratio
   → encaja en la celda sin deformar.
2. **Resolución incrustada** (`_downscale_signature_image`, PIL/LANCZOS, tope
   `600px` de ancho): reportlab incrusta la imagen a su resolución de origen
   aunque la muestre chica, así que una firma gigante (p. ej. 2400×900) se baja a
   600px **antes** de pasarla al form para no engordar el PDF.

## Al modificar

- Si el front empieza a capturar también la **firma de quien entrega**, agregar
  su `image_path` al dict de `delivery_files` y llenar la 3ª columna en
  `_sm_draw_delivery_row` (hoy va `[""]`).
- Extensiones dibujables: `{jpg, jpeg, png, webp}` (set `drawable` en
  `_build_sm_delivery_files`). Si algún día se quiere anexar un PDF firmado,
  habría que renderizar su página a imagen aparte (reportlab no dibuja PDF).
- El tope de `600px` y el alto de fila de firma (`_SM_SIGN_ROW_H = 60.0`) son
  ajustables; si se suben, revisar que la fila siga cabiendo en una página
  (la paginación por fila lo tolera, pero una fila más alta que la hoja no).
- Para agregar columnas a la tabla de entregas: editar `_SM_DELIVERY_COLS` (los
  anchos suman `_SM_GRID_WIDTH`) y alinear `_sm_draw_delivery_row` por posición.

## Notas posteriores

- La firma se baja del bucket `S3_ADMIN_BUCKET` (leído de `secrets` en
  `_build_sm_delivery_files`, [`MD_SM.py`](../templates/resources/midleware/MD_SM.py));
  la key de S3 es el `file["path"]` del attachment.
- Pendiente abierto: capturar (front) e incrustar (back) también la **firma de
  quien entrega**; listado en [`pendientes.md`](pendientes.md).

### 2026-10-16 — Firma de quien entrega (P-045, back)

El back ya incrusta la **firma de quien entrega** en la 3ª columna. Para no
ensuciar la tabla (hoy cada anexo con `firma` era una fila), las dos firmas de
una misma entrega se **emparejan por una marca compartida** al final del nombre:

```
<sm_id>-firma-recibido-<marca>.<ext>   -> la entrega (fila del PDF; status -> 5)
<sm_id>-firma-entrega-<marca>.<ext>    -> firma de quien entrega (NO es fila; status intacto)
```

- `_sm_sign_kind_and_mark` ([`MD_SM.py`](../templates/resources/midleware/MD_SM.py))
  extrae `(tipo, marca)` con la regex tolerante
  `firma-(recibido|entrega)(?:-([^./\\]*))?` (case-insensitive): la marca es lo
  que sigue a `firma-recibido-`/`firma-entrega-` hasta la extensión; sin marca
  (anexos viejos `12-firma-recibido.png`) es `""` y la fila queda sin pareja.
- `_build_sm_delivery_files`: primero separa las `firma-entrega` en un mapa por
  marca (la última gana), luego arma **una fila por anexo que no sea
  `firma-entrega`** (cap 20 filas). Si la fila es `firma-recibido` con marca y
  hay `firma-entrega` con la misma marca, baja esa imagen de S3 (misma descarga
  y mismo `_downscale_signature_image`) y la pasa como `delivery_image_path`;
  si la descarga falla, `None` (celda en blanco, log, no fatal). Una
  `firma-entrega` sin pareja (o sin marca) se ignora en el PDF y deja log en
  `log_file_sm_path`.
- `_sm_draw_delivery_row` ([`StorageMovSM.py`](../templates/forms/StorageMovSM.py))
  dibuja `delivery_image_path` en la columna "Firma de Quien Entrega" con
  `_sm_draw_signature_image`; `_sm_delivery_row_height` usa el alto de firma
  (`_SM_SIGN_ROW_H`) si cualquiera de las dos imágenes existe. Sin cambio de
  layout: la columna ya existía.
- Contrato `FileSmPDF`: cada entrega gana la clave **opcional**
  `delivery_image_path: str | None` (ausente = celda en blanco).
- Subida (`create_sm_attachment_api`): `firma-entrega` se acepta como anexo
  normal (misma validación de extensión, misma key S3 `smData/<fecha SM>/`,
  entrada en `extra_info["files"]` con `timestamp`/`title`, history y
  notificación) pero **no cambia el status**; solo `firma-recibido` lo pone en
  5. El autonumerado `"Entrega N"` (cuando no viene `title`) cuenta solo los
  anexos que no son `firma-entrega`. Cualquier otro nombre sigue dando 400
  (`"Nombre de archivo incorrecto"`).
- Revisado el resto del flujo de SM: no hay listados/contadores de "firmada"
  por nombre de archivo, ni endpoint de borrado/descarga individual de anexos de
  SM; el GET de la SM expone `extra_info["files"]` tal cual (el front verá ambos
  archivos). Ningún otro módulo usa `"firma" in filename` sobre anexos de SM.

#### Contrato mínimo para el front

```
POST /GUI/api/v1/sm/attachment-<id_sm>
Authorization: <JWT crudo>          (NO "Bearer <token>")
Content-Type: multipart/form-data   (UN archivo por request)
```

| Parte | Tipo | Req. | Notas |
|---|---|---|---|
| `file` | archivo | sí | Nombre **exacto**: `<id_sm>-firma-recibido-<marca>.png` o `<id_sm>-firma-entrega-<marca>.png` (`png`/`jpg`/`jpeg`/`webp`; `pdf`/`zip` se aceptan pero no se dibujan). |
| `title` | texto | no | Título de la entrega. Viaja en el request de la **`firma-recibido`**; en la `firma-entrega` se ignora para el PDF. Si falta, el back pone `"Entrega N"`. |

- `<marca>`: epoch en ms (`Date.now()`), la **misma** en los dos archivos de la
  entrega; es lo que las empareja. Dos requests por entrega:
  1. `<id>-firma-recibido-<marca>.png` (+ `title`) → **status de la SM pasa a 5
     (firmado)**, aparece una fila en el PDF.
  2. `<id>-firma-entrega-<marca>.png` (opcional, antes o después) → anexo
     normal, **el status NO cambia**, no agrega fila; su imagen va en la columna
     "Firma de Quien Entrega" de la fila con la misma marca.
- Una `firma-entrega` cuya marca no coincida con ninguna `firma-recibido` se
  guarda como anexo pero **no se dibuja** en el PDF (el back deja un log); si
  después llega la `firma-recibido` con esa marca, se empareja sola.
- Re-subir una `firma-entrega` con la misma marca: la última gana en el PDF
  (ambos anexos quedan en `extra_info["files"]`).
- Entregas viejas (sin `firma-entrega` o sin marca): columna de quien entrega
  en blanco, como hoy.

Respuestas (`{data, msg, error}`):

- **201** recibido: `{"data": "smData/2026/10/16/61-firma-recibido-1760640000000.png", "msg": "Archivo adjunto agregado: 61-firma-recibido-1760640000000.png al sm 61 por el empleado X y estado actualizado a (firmado)", "error": null}`
- **201** entrega: `{"data": "smData/2026/10/16/61-firma-entrega-1760640000000.png", "msg": "Archivo adjunto agregado: 61-firma-entrega-1760640000000.png al sm 61 por el empleado X", "error": null}` (sin la coletilla de estado).
- **400**: `{"data": null, "msg": "Nombre de archivo incorrecto", "error": "filename"}` (nombre sin `firma-recibido`/`firma-entrega`), `"Formato de archivo no valido"`, `"El nombre del archivo no corresponde al sm"`, `"No se pudo obtener la SM: SM con id N no encontrada"`, errores de S3.
- **401**: `{"error": "..."}` token inválido o sin permiso (`administracion`, `operaciones` o `almacen`).

`GET /GUI/api/v1/sm/download/pdf/<id_sm>` no cambia: **200 → blob PDF**
(`Content-Disposition: attachment; filename=sm_<folio>.pdf`), **4xx → JSON**
`{data, msg, error}`; el front decide por el status.

Pendiente front (P-045): segundo pad "Firma de quien entrega" en
`/dashboard/almacen/procesamiento/firmas/<id>` que suba
`<id>-firma-entrega-<marca>.png` con la marca compartida.
