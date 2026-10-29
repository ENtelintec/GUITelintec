# Nómina: subida y borrado sin huérfanos en S3, y conciliación S3 contra índice

Fecha: 2026-10-23 · **Estado: hecho y verificado contra dev con S3 simulado (36/36, `Tests/tester_nomina_huerfanos.py`).** Sin DDL. Pendientes `P-175` (back, hecho), `P-176` (huérfanos que ya existen) y `P-177` (llave S3 compartida).

Origen: la pregunta de qué pasa con los archivos que quedan huérfanos en S3, es decir, objetos bajo `payroll/` que ningún `payroll.files_data` referencia. La respuesta era que solo se anotaban en el log cuando fallaba el borrado. Al revisar el flujo salieron más casos, algunos sin ningún rastro:

| # | Caso | Antes | Ahora |
|---|---|---|---|
| 1 | Reemplazo con otro nombre y falla el borrado del anterior en S3 | Huérfano anotado en el log y en `error` | Igual (se reporta en la conciliación) |
| 2 | `DELETE` con S3 caído | Huérfano anotado en el log y con `s3_deleted: false` | Igual (se reporta en la conciliación) |
| 3 | El archivo sube a S3 y falla el `UPDATE` del índice | El nuevo quedaba huérfano. Si era un reemplazo, **el anterior ya se había borrado** y el índice quedaba apuntando a un objeto que no existe | El anterior se borra **después** de guardar el índice. Si el índice falla, se retira de S3 lo que subió este request |
| 4 | Empleado sin fila en `payroll` | `UPDATE` de 0 filas y **201** sin indexar | **404** antes de subir |
| 5 | Falla la lectura del índice | Se tomaba como índice vacío y el `UPDATE` **pisaba todo el `files_data`** del empleado | **404** con el error de BD, antes de subir |
| 6 | Mismo nombre de archivo en dos `key` del mes (misma llave S3) | Reemplazar o borrar uno borraba el objeto que el otro seguía usando | No se borra de S3 una llave que otra entrada del índice usa |
| 7 | Temporal del servidor | La subida nunca borraba la copia del recibo; `extract` dejaba la carpeta | Se borra la carpeta temporal en un `finally` (también si la función truena) |

## Capas tocadas

```
rs    rs_RRHH.py                    POST /payroll/files/update y /payroll/files/extract: carpeta temporal
                                    propia + shutil.rmtree en finally
mid   Functions_midleware_RRHH.py   create_payroll_file_attachment_api: índice antes de subir (404),
                                    head_object para saber si la llave ya existía, índice guardado antes
                                    de borrar el anterior, retiro del objeto nuevo si el UPDATE falla,
                                    no borra una llave que el índice sigue usando;
                                    _payroll_s3_exists nuevo; delete_payroll_file_api: mismo guard
DB    (sin cambios)
modelos (sin cambios)
script scripts_db_handle/nomina_s3_conciliacion.py (gitignored): reporte de solo lectura
```

## Reglas

- **Orden de la subida**: validar → leer índice (sin fila o BD caída: 404, no sube nada) → `head_object` → subir → guardar índice → borrar el anterior. El anterior se borra solo si cambió el nombre y si ninguna otra entrada del índice usa esa llave.
- **Si el `UPDATE` falla**, el índice queda como estaba y el anterior sigue vigente. El objeto nuevo se retira de S3 **solo si este request lo creó**: si la llave ya existía (mismo nombre, otra quincena u otra BD), S3 la pisó, pero no se borra.
- **`_payroll_s3_exists`**: un error de S3 que no sea 404 cuenta como "existe". Quien pregunta solo borra lo que sabe que creó.
- No se revisa el `rowcount` del `UPDATE`. MySQL devuelve 0 cuando el valor no cambia (subir otra vez el mismo nombre al mismo `key`), y la fila ya se comprobó al leer el índice.

## Conciliación S3 contra índice

[`scripts_db_handle/nomina_s3_conciliacion.py`](../scripts_db_handle/nomina_s3_conciliacion.py) (gitignored, como el resto de la carpeta). **Solo reporte**: lista `payroll/` del bucket y lee `payroll.files_data` de **las 3 BDs** en transacciones `READ ONLY`.

- Lee las 3 BDs porque **dev, test y prod comparten el bucket `S3_RH_BUCKET` y la misma llave** `payroll/<año>/<mes>/<emp_id>/<archivo>`. Está confirmado: los 2 objetos indexados hoy los referencia prod. Un objeto es huérfano solo si ninguna BD lo tiene, y si una BD no responde el script aborta.
- Credenciales del `.env` de la raíz, sin pasar por `static/constants.py`, así que no depende de `environment`.
- Secciones del reporte JSON: `huerfanos` (más de 24 h; los recientes van aparte), `faltantes` por BD (`legacy: true` = llave de SharePoint, las quita `P-141`), `compartidos` (2+ referencias) e `indices_ilegibles`.
- Uso: `.venv/Scripts/python.exe scripts_db_handle/nomina_s3_conciliacion.py [--out <ruta>]`. Sin `--out` escribe `scripts_db_handle/nomina_s3_conciliacion_<fecha>.json`, que git ignora. No mandar el reporte a la raíz del repo: ahí git sí lo sigue.

**Primera corrida (2026-10-23):** 9 objetos bajo `payroll/`. Dos los indexa prod: emp 21, `2026-10-Q2`, pdf y xml, subidos el 2026-10-23. Los **7 restantes son huérfanos** (1.44 MB): 5 del emp 21 (meses 01, 09 y 10) y uno del 85 y otro del 87 con el mismo nombre de archivo, subidos entre el 15 y el 22 de octubre. Los 3 empleados tienen fila en las 3 BDs y no hay rastro en los logs locales, así que pasaron por el servidor. La causa probable es un reemplazo o borrado cuyo borrado en S3 falló (`P-176`). Además hay 238 llaves *legacy* por BD sin objeto en S3. 0 compartidos y 0 índices ilegibles.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permiso `rrhh`. **Base**: `/GUI/api/v1/rrhh`. Envelope `{data, msg, error}`. **Sin cambios obligatorios en el front**: `subirArchivoNomina` ya muestra el `msg` de cualquier status distinto de 2xx.

### `POST /payroll/files/update` (multipart `file` + form `year`, `month`, `emp_id`, `key`; un archivo por request)

| Status | Cuerpo | Cuándo |
|---|---|---|
| 201 | `{"data": "payroll/2026/10/34/recibo.pdf", "msg": "Archivo de nomina recibo.pdf (pdf) subido para el empleado 34 en 2026/10 (key 2026-10-Q2)", "error": null}` | alta o mismo nombre |
| 201 | `msg` termina en `; reemplaza a payroll/2026/10/34/viejo.pdf (Objeto eliminado de S3)` | reemplazo con otro nombre |
| 201 | `...; reemplaza a ... (se conserva en S3: otra nómina del índice lo usa)` | el anterior lo usa otro `key` del mes |
| 201 | `...(No se pudo borrar el objeto de S3 (queda huérfano))` + `error: "<motivo>"` | S3 no borró el anterior; el índice ya apunta al nuevo |
| 400 | `{"data": null, "msg": "No se pudo guardar el índice de nómina del empleado 34; recibo.pdf no quedó registrado (Objeto eliminado de S3)", "error": "<error BD>"}` | **cambió**: antes era `data: <llave>` y el archivo se quedaba en S3. El anterior sigue vigente |
| 400 | extensión inválida, campos faltantes, error de S3 al subir | sin cambio |
| 401 | `{"error": "No autorizado. Token invalido"}` | |
| **404** | `{"data": null, "msg": "El empleado 999 no tiene registro de nómina", "error": "None"}` | **nuevo**: el empleado no tiene fila en `payroll`, o la BD no respondió al leer el índice (`error` trae el motivo). No se sube nada |

**Gotcha**: el 404 no debería salir en la pantalla de Nómina, porque `useNominasPeriodo` llama a `GET /payroll/update/employees` antes de listar. Si sale, volver a sincronizar y reintentar.

### `DELETE /payroll/files`

Mismo contrato. Caso nuevo: si la llave borrada del índice la sigue usando otro `key` del mes, responde **200** con `"s3_deleted": false`, `"error": null` y el `msg` termina en `(se conserva en S3: otra nómina del índice lo usa)`. Es informativo, no es un fallo.

## Al modificar

- **Toda escritura que combine S3 e índice** sigue este orden: leer el índice antes de subir, guardar el índice antes de borrar y retirar solo lo que el request creó. El `DELETE` ya iba BD primero y S3 después.
- **Antes de borrar una llave de S3**, revisar que no la use otra entrada (`_payroll_index_keys`). Mientras `P-177` siga abierto, una llave puede estar en dos `key` del mes, y también en otra BD; esto último no se puede ver desde el request.
- **Borrar huérfanos**: el script no borra. Un modo de borrado debe correr las 3 BDs, saltarse los recientes y pedir confirmación por lista (`P-176`).
- Si cambia la forma de la llave (`P-177`), la conciliación sigue sirviendo, porque compara llaves completas.

## Verificación

[`Tests/tester_nomina_huerfanos.py`](../Tests/tester_nomina_huerfanos.py) (gitignored), contra BD dev con `boto3.client` parcheado (no toca el bucket). Escribe en el índice del emp 34 bajo el año 2099 y lo restaura byte a byte al final. **36/36**:

- Sin fila → 404 sin subir. Lectura del índice caída → 404 sin subir y sin escribir.
- Alta (el resto del índice queda intacto). Reemplazo: borra el anterior después de guardar.
- `UPDATE` caído con nombre nuevo: 400, retira el nuevo y conserva el anterior en S3 y en el índice, con línea en el log. Con nombre existente: no borra.
- Mismo nombre en dos `key`: el reemplazo y el `DELETE` no borran la llave compartida; el último `DELETE` sí la borra y limpia el año.
- S3 falla al borrar el anterior: 201 con `error`. pdf y xml en el mismo `key`.
- Rutas con `app.test_client()`: la carpeta temporal se borra en la subida (también con excepción) y en `extract`.

`pyrefly`: sin errores nuevos en los archivos tocados.

## Pendientes

- ~~`P-175` **[back]** Subida/borrado sin huérfanos + conciliación (solo reporte)~~ — hecho (2026-10-23).
- ~~`P-176` **[usuario → back]** Borrar los 7 huérfanos cuando RH use nómina al 100 %~~ — hecho (2026-10-28): borrados por llave exacta (ver Notas posteriores).
- ~~`P-177` **[back, decisión]** La llave S3 no lleva entorno ni `key`~~ — hecho (2026-10-27): `payroll/<entorno>/<año>/<mes>/<emp_id>/<quincena>/<archivo>`, y dev/test ya no borran llaves viejas ni ajenas; la conciliación cruza cada prefijo con su BD → [`s3_rutas_por_entorno.md`](s3_rutas_por_entorno.md).
- `P-141`: criterio nuevo del 2026-10-28 (solo lo anterior a agosto de 2026 y lo que no está en S3); ya no toca los recibos reales. Ver la nota de ese día en [`nomina_descarga_recibo.md`](nomina_descarga_recibo.md).

## Notas posteriores

### 2026-10-27: segunda conciliación y decisión sobre `P-176`

Se corrió con la versión del script que agrega el campo `entorno` (`P-177`). Hay 9 objetos bajo `payroll/`, los mismos que en la primera corrida:

- Prod sigue indexando solo 2: el recibo del emp 21, `2026-10-Q2` (pdf y xml).
- Los **7 huérfanos son los mismos de la primera corrida**. No apareció ninguno nuevo, y hay 0 recientes, 0 compartidos y 0 índices ilegibles.
- Los 7 tienen la ruta vieja, sin entorno (`entorno: sin_entorno`).
- Los de los emp 85 y 87 son el mismo PDF (296 203 bytes, el mismo tamaño que el del emp 21 en `2026/09`).

**Decisión del usuario**: los 7 son subidas de pruebas hechas durante el desarrollo, antes de `P-177`, cuando dev, test y prod compartían la llave. No hace falta buscar la causa en los logs del servidor. Se quedan en el bucket (1.44 MB) y se borran cuando RH use nómina al 100 %. Al borrarlos:

- **Borrar por la lista del reporte, no por prefijo.** Los 2 recibos reales de prod también tienen la ruta vieja, porque se subieron el 2026-10-23, antes de `P-177`.
- Si más adelante aparece un huérfano bajo `payroll/prod/...`, ese sí obliga a revisar el permiso `s3:DeleteObject` y los logs (`Error al borrar de S3`).

**Índices**: cada BD (dev, test y prod) tiene 238 llaves de SharePoint sin objeto en S3. Prod tiene 240 en total, contando las 2 reales. Esto confirma que el DML de `P-141` no se ha corrido en ninguna BD, y que tal como está también sacaría del índice los 2 recibos reales de prod.

### 2026-10-28: tercera conciliación y borrado de los 7 huérfanos (`P-176`)

- La conciliación (bucket + índices de las 3 BDs en transacciones `READ ONLY`) da 94 objetos bajo `payroll/`. Los **7 huérfanos son los mismos** de las dos corridas anteriores: ruta vieja sin entorno, ninguno referenciado. Además, 1 objeto reciente de dev, y prod ya indexa **86 recibos en S3**: 84 de `payroll/prod/2026/08` y los 2 del emp 21 de octubre. RH ya usa nómina.
- **Decisión del usuario:** borrar los 7. El bucket no tiene versionado (`get-bucket-versioning` vacío), así que el borrado es definitivo. Se borraron uno por uno, por llave exacta, con `aws s3api delete-object`: `payroll/2026/01/21/` (xml y pdf), `payroll/2026/09/21/FF8D85D2-…2121.pdf`, `payroll/2026/10/21/` (xml y pdf de pruebas), `payroll/2026/10/85/…2130.pdf` y `payroll/2026/10/87/…2130.pdf`.
- Después quedan **87** objetos: los 84 de agosto, los 2 reales del emp 21 de octubre y el de dev. `P-176` cerrado.

