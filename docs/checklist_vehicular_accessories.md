# Checklist vehicular: `accessories` sin doble codificación

Fecha: 2026-10-09 · **Estado: hecho y verificado contra dev (9/9 checks, `Tests/tester_voucher_vehicle_accessories.py`).** DML de normalización entregado ([`voucher_vehicle_accessories_normalize.sql`](../scripts_db_handle/voucher_vehicle_accessories_normalize.sql)), **pendiente de que el usuario lo corra**.

Cierra el pendiente de [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md).

## Qué estaba mal

`POST` y `PUT /sgi/voucher/vehicle` hacían `json.dumps(accessories)` en el midleware **y** otra vez en el controller. La columna `voucher_vehicle.accessories` (tipo `JSON`) terminaba guardando un **string** con el arreglo adentro: `"[{\"label\": …}]"`. Los lectores lo toleraban decodificando dos veces.

Conteo en solo lectura (2026-10-09): **dev 1 fila, test 2, prod 0**. Prod todavía no tiene checklists vehiculares.

## Capas tocadas

```
mid      MD_SGI.py   create_/update_voucher_vehicle_api pasan la lista tal cual (el controller hace el único json.dumps);
                     get_vouchers_vehicle_api lee con _chv_json_field (tolera las filas viejas)
datos    scripts_db_handle/voucher_vehicle_accessories_normalize.sql   STRING -> ARRAY (idempotente)
```

Rutas, forms y controllers sin cambios.

## Contrato mínimo para el front

- **Base**: `/GUI/api/v1/sgi`. **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Sin cambios de request ni de respuesta.** `accessories` se sigue mandando como `[{"label": str, "value": "Bien|Mal|N/A"}]`, y `GET /voucher/vehicle/<año>&<mes>&<día>` lo sigue devolviendo como **lista** (antes también, porque el back decodificaba dos veces).
- Si alguien lee la BD directo (reportes, BI): desde este cambio y tras correr el DML, `accessories` es un arreglo JSON, ya no un string.

## Al modificar

- Un campo JSON se codifica **una sola vez**, en el controller. El midleware pasa estructuras de Python.
- `_chv_json_field` (decodifica hasta 2 veces) puede quedarse como defensa aunque el DML ya haya corrido.

## Verificación

Contra BD dev (2026-10-09), [`Tests/tester_voucher_vehicle_accessories.py`](../Tests/tester_voucher_vehicle_accessories.py) (gitignored), **9/9**:

- `POST` y `PUT` dejan `JSON_TYPE = ARRAY` con el contenido exacto.
- El GET del listado devuelve la lista.
- El PDF sale bien tanto de la fila nueva como de la fila vieja doble-codificada de dev.
- El voucher temporal se borra al final.

`pyrefly`: 0 errores en `MD_SGI.py`.

## Pendientes

- **[back] DML** [`voucher_vehicle_accessories_normalize.sql`](../scripts_db_handle/voucher_vehicle_accessories_normalize.sql) en dev, test y prod (usuario). No bloquea el deploy: los lectores toleran ambas formas.
- **[back] Alta sin rollback** (hallazgo de la prueba): `create_voucher_vehicle_api` inserta `vouchers_general` y después `voucher_vehicle`. Si el segundo falla (p. ej. `model` > 100 caracteres → 1406 `Data too long`), el primero queda **huérfano**. El huérfano de la prueba se borró a mano.
