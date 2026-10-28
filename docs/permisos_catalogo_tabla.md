# Catálogo de permisos desde la tabla (`GET /UserSystem/permissions`)

Fecha: 2026-10-27 · **Estado: hecho y verificado contra dev y test (`test_client`).** Cierra `P-193` (DDL corrido por el usuario en las 3 BDs, verificado en solo lectura) y `P-194`. Decisiones D1/D11 de [`permisos_plan.md`](permisos_plan.md).

## Qué cambia

- **La tabla `sql_telintec.permissions` existe en dev, test y prod**, con 32 permisos activos (ids 1 a 31 = orden de la app de usuarios, 32 = `Sucursal-2`). DDL: `scripts_db_handle/permissions_catalog.sql`.
- **`GET /UserSystem/permissions` lee la tabla**: solo activos, en orden de `id`, y respeta la BD de prueba con `testerUser`.
  - Antes leía `static/permissions_models.json`, una copia del API que ya había divergido de la app de usuarios (traía `Sucursal-2` y no `testerUser`). Ese archivo y la constante `filepath_permission` se borraron.
- **Permiso del endpoint**: pedía `department=["credentials", "RRHH"]`, y `credentials` no corresponde a ningún permiso. Ahora pide `permissions=["App.Department.RRHH"]`, exacto. Entra el mismo grupo de antes (más Administrator); un nombre fuera del catálogo como `DemoRRHH` ya no.

## Capas tocadas

```
rs          rs_login.py            GET /permissions: permissions=["App.Department.RRHH"], pasa data_token
midleware   MD_UserSystem.py       fetch_permissions_from_api(data_token) lee la tabla; fuera read_permissions_file e import json
controller  us_controller.py       get_permissions_catalog (SELECT id, name, description, area ... WHERE is_active = 1 ORDER BY id)
static      constants.py           fuera filepath_permission · static/permissions_models.json borrado
```

## Contrato mínimo para el front

- **Base** `/GUI/api/v1/UserSystem` · **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Permiso exacto: `App.Department.RRHH` (Administrator siempre).
- **Request**: `GET /permissions`, sin body ni query.
- **200**: el envelope de siempre; cada elemento suma `id` y `area` a los `name` y `description` que ya traía.

  ```json
  {"data": [{"id": 1, "name": "App.Department.Director", "description": "the director permission", "area": "general"},
            {"id": 32, "name": "App.Department.Sucursal-2", "description": "the warehouse permission for branch 2 (sede de almacén id 2)", "area": "almacen"}],
   "msg": null, "error": null}
  ```

- **401**: `{"error": "No autorizado. Token invalido"}` (sin permiso) o `{"error": "Token not found"}`.
- **400**: `{"data": null, "msg": "Error al obtener los permisos", "error": "..."}` si falla la lectura en BD.
- `area` vale uno de `rrhh`, `almacen`, `administracion`, `compras`, `sgi`, `cda`, `sm`, `operaciones` o `general`.

## Al modificar

- Un permiso nuevo se da de alta en la tabla desde la app de usuarios (T3 de [`gui_system_tareas.md`](gui_system_tareas.md)), nunca en un archivo del API.
- Retirar = `is_active = 0`: deja de salir aquí, pero los usuarios que lo tengan lo conservan hasta que se re-guarden sus permisos.
