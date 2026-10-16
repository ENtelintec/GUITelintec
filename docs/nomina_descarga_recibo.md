# Descarga del recibo de nómina: solo llaves del empleado, basta pdf o xml, zip por request

Fecha: 2026-10-13 · **Estado: hecho y verificado contra dev con S3 simulado (19/19 checks, `Tests/tester_nomina_descarga.py`; regresión `tester_nomina_ses` 17/17).** Sin DDL. Pendientes `P-132` (back, hecho) y `P-134` (front).

`POST /common/payroll/employee/file` (`download_nomina_docs`) tenía tres problemas. El front reportó dos al hacer la pantalla de nómina (`P-032`); el tercero apareció al revisarlos:

1. **Un empleado podía bajar el recibo de otro.** El token se validaba contra el `emp_id` del body, pero las llaves `pdf`/`xml` se descargaban de S3 tal cual llegaban, sin revisar que fueran de ese empleado. Con su propio `emp_id` y la llave de otro (`payroll/<año>/<mes>/<otro_emp>/<archivo>`), cualquier usuario con token bajaba el recibo ajeno.
2. **Exigía `pdf` y `xml`** (`InputRequired` en los dos): una quincena con un solo archivo no se podía bajar. El front mandaba la misma llave en ambos campos para pasar la validación.
3. **Zip en una ruta compartida** (`files/docs.zip`): dos descargas al mismo tiempo podían pisarse y entregar el zip de otra persona. Además, la carpeta temporal de cada descarga no se borraba nunca.

## Capas tocadas

```
modelos  api_payroll_models.py         RequestFileForm: pdf/xml sin InputRequired (default "");
                                       request_file_model: required=False + ejemplos
mid      Functions_midleware_RRHH.py   download_nomina_docs: dedup de llaves, 400 si no viene ninguna,
                                       404 si alguna no está en el índice del emp_id, zip en BytesIO
                                       con get_object (sin disco); _payroll_index_keys nuevo;
                                       fuera los imports tempfile y file_temp_zip
rs       rs_Common.py                  send_file del BytesIO: mimetype application/zip, download_name docs.zip
```

La constante `file_temp_zip` sigue en `static/constants.py` (ya nadie la usa).

## Contrato mínimo para el front

- **Ruta**: `POST /GUI/api/v1/common/payroll/employee/file`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Pasa el empleado dueño (`emp_id` del token = `emp_id` del body) o cualquier token con permiso `rrhh`.
- **Body JSON**:

  ```json
  {"emp_id": 77, "pdf": "payroll/2026/10/77/recibo.pdf", "xml": "payroll/2026/10/77/recibo.xml"}
  ```

  `pdf` y `xml` son **llaves S3 del índice del empleado**: las que traen `GET /common/payroll/employee/<emp_id>` (`data[].files.pdf|xml`), el `files_data` de RH o el `payload.files` del aviso. **Basta una de las dos**: la otra puede ir ausente, `null` o `""`. Si llega la misma llave en ambos campos, el zip la trae una sola vez.
- **Respuestas** (el front decide por el status):

  | Status | Cuerpo | Cuándo |
  |---|---|---|
  | **200** | **blob `application/zip`** (`docs.zip`) con 1 o 2 archivos | al menos uno se bajó de S3. Si uno falla, el zip trae solo el otro |
  | 400 | `{"data": null, "msg": "Indica el pdf o el xml del recibo", "error": "pdf y xml vacíos"}` | no vino ninguna llave |
  | 400 | `{"data": null, "msg": "Estructura de datos inválida", "error": {...}}` | `emp_id` falta o no es entero |
  | 400 | `{"data": null, "msg": "No se pudieron descargar los archivos de nómina", "error": "Ningún archivo descargado desde S3"}` | S3 no entregó ninguno |
  | 401 | `{"error": "No autorizado. Token invalido"}` | el token no es del empleado ni de RH |
  | **404** | `{"data": null, "msg": "El archivo no está entre los recibos del empleado (pudo haberse reemplazado o eliminado)", "error": ["payroll/2026/10/78/recibo.pdf"]}` | alguna llave no está en el índice del `emp_id`. **Todo o nada**: no se baja ninguna. `error` lista las llaves rechazadas |
  | 404 | `{"data": null, "msg": "El empleado 107 no tiene registro de nómina", "error": "..."}` | el empleado no tiene fila en `payroll` |

- **Gotcha, avisos viejos**: el `payload.files` de un aviso guarda las llaves del momento en que se notificó. Si después RH **reemplazó** el archivo con otro nombre o lo **eliminó**, esa llave ya no está en el índice y la descarga da **404**. Antes daba 400 al no encontrarla en S3. El front puede ofrecer "ver mis recibos" (`GET /common/payroll/employee/<emp_id>`) con las llaves vigentes.
- **Ya no hace falta** mandar la misma llave en `pdf` y `xml`: mandar solo la que exista.

## Al modificar

- **Cualquier endpoint nuevo que entregue archivos por llave S3 recibida en el request** debe validar la llave contra el índice del dueño, como `_payroll_index_keys`. El token prueba quién pide, no de quién es la llave.
- El índice `files_data` es `{año: {mes: {key: {pdf, xml}}}}` (ver [`nomina_gestion_archivos_y_notificacion.md`](nomina_gestion_archivos_y_notificacion.md)). `_payroll_index_keys` recorre todas las hojas de texto, así que también acepta llaves de registros viejos con otra forma.
- El zip se arma en memoria. Los recibos son de KB; si algún día se empaquetan periodos completos, usar un temporal por request (`tempfile`) y borrarlo después de `send_file`. **Nunca** volver a una ruta fija.

## Verificación

Contra BD dev (2026-10-13) con S3 simulado (`boto3.client` parcheado; no toca el bucket), [`Tests/tester_nomina_descarga.py`](../Tests/tester_nomina_descarga.py) (gitignored), **19/19**. Inyecta un recibo `TST-DL-Q1` en el índice de 2 empleados reales y lo restaura al final. Cubre:

- Dueño con pdf+xml (zip con 2 y `application/zip` + `docs.zip`), solo pdf, solo xml con `pdf: null`, misma llave dos veces (1 entrada), ninguna (400, ausentes o vacías).
- Llaves de otro empleado con el `emp_id` propio → 404 **sin llamar a S3**. Mezcla propia + ajena → 404. Llave inventada con el prefijo propio → 404. `emp_id` ajeno en el body → 401. Empleado sin fila en `payroll` → 404.
- RH baja el de otro empleado (200). RH con la llave de E1 bajo `emp_id` E2 → 404.
- S3 falla en uno (200 con el otro) y en los dos (400).
- Dos descargas seguidas: cada zip trae su propio contenido, y `files/docs.zip` ya no se escribe.

`pyrefly`: sin errores nuevos en los archivos tocados.

## Notas posteriores

- **2026-10-16** (prueba del front, recibos históricos): los recibos de la época de SharePoint siguen en `payroll.files_data` pero no están en S3, así que esta descarga responde 400 "No se pudieron descargar los archivos de nómina". **Decisión del usuario: nómina arranca limpia, no se migra nada.** DML `scripts_db_handle/nomina_limpieza_inicio.sql` (`P-141`, lo corre el usuario en dev/test/prod): `files_data = '{}'` para todos los empleados (las filas se conservan para `GET /payroll/update/employees`) y borra los avisos in-app con `payload.kind = 'payroll'`. S3 no se toca. Mientras no corra, el front muestra el aviso ámbar "No encontramos tu recibo… pídeselo a RH".
