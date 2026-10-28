# Permisos exactos en SM (`/sm/*`)

Fecha: 2026-10-27 · **Estado: hecho y verificado contra dev** (`Tests/tester_permisos_sm.py` 10/10: matriz de 28 endpoints por 13 permisos sin diferencias, con los midlewares y controllers reemplazados por stubs para no tocar la BD; regresión: `tester_sm_firma_entrega` 30/30). Sin DDL.

Tercera área de `P-198`, después de Compras ([`permisos_compras_y_baja.md`](permisos_compras_y_baja.md)) y Almacén ([`permisos_almacen.md`](permisos_almacen.md)). Decisiones del grill del 2026-10-27, en [`permisos_plan.md`](permisos_plan.md) (Notas posteriores).

## Qué cambia

Hoy la subcadena `sm` abría las 28 rutas a seis permisos: `SM`, `SM-URGENT`, `smControl`, `smCreate`, `smDespachar` y `smEntregasAdmin`. Con la comparación exacta (`permissions=`):

- **`SM` y `SM-URGENT`** son el grupo base: crear, editar, cancelar y borrar SM, catálogos (empleados, clientes, productos), alta de cliente y producto, gráficas, PDF/Excel, tabla de control y actualización de ítems.
- **Urgentes solo para `SM-URGENT`**: `POST /sm/add/urgent` deja de estar abierto a `SM`. El front ya mostraba esa pantalla solo a `SM-URGENT`.
- **`smControl`, `smCreate`, `smDespachar` y `smEntregasAdmin` no abren nada.** No los usaba ningún código y en dev nadie los tiene. Reemplazarlos por `SM` en prod y retirarlos es la tarea T5 de [`gui_system_tareas.md`](gui_system_tareas.md) (`P-199`).
- **Almacén**:
  - `ALMACEN` conserva sus 10 endpoints de SM: listados, folios, ítems por estado, cambio de estado, aprobación, actualización de ítems, despacho y adjuntos;
  - `ALMACEN-VISUAL` solo conserva las 4 lecturas (`GET /sm/all`, `/sm/permission`, `/sm/folioSmAll`, `/sm/items/state-<n>`), igual que en Almacén;
  - el despacho sigue siendo solo de almacén.
- **Administración y Operaciones sin cambios**: `Administracion` en `PUT /sm/item`, `PUT /sm/items/bulk` y `POST /sm/attachment`; `Operaciones` en `POST /sm/attachment`.
- El alcance de datos dentro del midleware no cambia: qué contratos y folios ve cada quien según sea administrador, almacén, líder o auxiliar.

## Capas tocadas

```
rs   rs_SM.py   _SM / _SM_URGENT / _SM_READ_ALMACEN / _SM_WRITE_ALMACEN / _SM_ITEMS / _SM_DISPATCH / _SM_ATTACHMENT en los 28 endpoints
```

## Contrato mínimo para el front

- **Base** `/GUI/api/v1/sm` · **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Request y response no cambian; solo cambia quién pasa. Sin permiso → **401** `{"error": "No autorizado. Token invalido"}`; sin token → **401** `{"error": "Token not found"}`.
- Permisos exactos (prefijo `App.Department.`; Administrator pasa siempre):

| Endpoints | Permisos |
|---|---|
| `GET /employees`, `GET /clients`, `GET /products/<contract>`, `GET /employee`, `POST·PUT·DELETE /add`, `POST /cancel`, `POST /newclient`, `POST /newproduct`, `GET /plot/<range>`, `GET /almacen/employees`, `GET /download/{pdf,excel}/<id>`, `PUT /control/table`, `GET /control/table/all`, `PUT /item/inventory` | `SM`, `SM-URGENT` |
| `POST /add/urgent` | `SM-URGENT` |
| `GET /all`, `GET /permission`, `GET /folioSmAll`, `GET /items/state-<n>` | `SM`, `SM-URGENT`, `ALMACEN`, `ALMACEN-VISUAL` |
| `POST /item/stateUpdate`, `POST /item/approveRequired` | `SM`, `SM-URGENT`, `ALMACEN` |
| `PUT /item`, `PUT /items/bulk` | `SM`, `SM-URGENT`, `ALMACEN`, `Administracion` |
| `POST /manage/dispatch` | `ALMACEN` |
| `POST /attachment-<id_sm>` | `Administracion`, `Operaciones`, `ALMACEN` |

### Gotchas

- Un usuario con solo `SM` que llame `POST /sm/add/urgent` recibe 401. Desde el front no pasa, porque esa pantalla ya era solo de `SM-URGENT`.
- Quien tenga solo un permiso granular (`smCreate`…) ya no entra a SM hasta que se le asigne `SM` (T5).

## Al modificar

- Endpoint nuevo de SM: usar `_SM` para lo del solicitante; `_SM_READ_ALMACEN` / `_SM_WRITE_ALMACEN` si almacén también lo usa; urgentes con `_SM_URGENT`.
- Si un permiso granular vuelve a hacer falta, primero se define qué abre (doc + `gui_system_tareas.md`) y luego se agrega a la constante: hoy no tienen significado.

## Verificación (2026-10-27, dev)

- `Tests/tester_permisos_sm.py` 10/10:
  - matriz de los 28 endpoints, leídos del código, contra `SM`, `SM-URGENT`, los 4 granulares, `ALMACEN`, `ALMACEN-VISUAL`, `Administracion`, `Operaciones`, `Epp`, `sm` y `Administrator`;
  - casos del grill: urgentes, granulares, despacho y adjuntos;
  - stubs en lugar de midlewares y controllers, sin escrituras.
- Regresión: `tester_sm_firma_entrega` 30/30, que hace el flujo real de entregas y firmas con S3 falso.
- `import app` sin errores; pyrefly sin errores en `rs_SM.py`.

## Notas posteriores

- **2026-10-27 — granulares pendientes de asignación** (decisión del usuario): `smControl`, `smCreate`, `smDespachar` y `smEntregasAdmin` se usarán más adelante, así que **no se retiran** del catálogo. Hasta que se defina qué abre cada uno, siguen sin abrir nada. T5 queda solo como revisión de quién los tiene en prod sin `SM` (`P-199`).
