# Permisos exactos en Almacén (`/almacen/*`, `/sucursal/*`, dashboards de inventario)

Fecha: 2026-10-27 · **Estado: hecho y verificado contra dev** (`Tests/tester_permisos_almacen.py` 18/18: matriz de 55 endpoints por 12 permisos sin diferencias, con los midlewares reemplazados por stubs para no tocar la BD; regresión: `tester_multisede_resolve` 64/64 y `tester_transfer_over_receive` 10/10). Sin DDL.

Segunda área de `P-198` después de Compras ([`permisos_compras_y_baja.md`](permisos_compras_y_baja.md)). Decisiones del grill del 2026-10-27, en [`permisos_plan.md`](permisos_plan.md) (Notas posteriores).

## Qué cambia

Hoy la subcadena `almacen` dejaba que `ALMACEN-VISUAL` hiciera todo lo de `ALMACEN`, y `epp` dejaba que `eppVisual` y `eppApprove` registraran movimientos. Con la comparación exacta (`permissions=`):

- **`ALMACEN-VISUAL` queda en solo lectura**: todos los `GET` y las descargas (PDF y Excel de inventario y de movimientos, códigos de barras). Pierde las escrituras de movimientos, productos, cargas de archivo, traspasos, sedes y reservas. Su única pantalla en el front ya era la consulta de inventario.
- **EPP**:
  - lecturas de EPP: `Epp`, `eppVisual` y `eppApprove`, como antes;
  - `POST`/`PUT /almacen/movement`: `ALMACEN` y `Epp`, así que `eppVisual` y `eppApprove` dejan de escribir. La pantalla de aprobación de vales EPP no llama a este endpoint, porque la aprobación vive en `/sgi`;
  - `ALMACEN` sigue sin leer los endpoints exclusivos de EPP.
- **Sedes y reservas**: las lecturas para `Administracion`, `ALMACEN` y `ALMACEN-VISUAL`; las escrituras para `Administracion` y `ALMACEN`.
- **`/sucursal`, la excepción**:
  - El permiso de sede lleva el id (`Sucursal-<id>`), así que estos endpoints conservan `department="sucursal"` solo como puerta. El id lo sigue validando `_resolve_warehouse` / `verify_warehouse_permission`, y una sede nueva no requiere código.
  - Las lecturas del principal van exactas: `ALMACEN`, `ALMACEN-VISUAL` y `Administracion`, en la lista `SEDE_MAIN_READERS`. `_is_main_reader`, que decide quién del principal puede leer cualquier sede, usa esa misma lista en vez de la subcadena.
  - Las escrituras siguen siendo solo de la sede.
- **Dashboards de inventario** (`POST /dashboard/inventory/movements`, `GET /dashboard/inventory/sm/...`): `ALMACEN` y `ALMACEN-VISUAL`, como antes.
- Un nombre fuera del catálogo como `DemoALMACEN`, o con otra capitalización (`App.Department.almacen`), ya no pasa (D15).

## Capas tocadas

```
rs          rs_Almacen.py      _ALM_READ / _ALM_WRITE / _ALM_ADMIN_READ / _ALM_ADMIN_WRITE / _EPP_READ / _MOVEMENT_WRITE en los 43 endpoints
rs          rs_Sucursal.py     _SEDE = "sucursal" (puerta de sede) + permissions=SEDE_MAIN_READERS en las 6 lecturas; escrituras solo _SEDE
rs          rs_Dashboards.py   _INVENTORY_DASH en los 2 dashboards de inventario (los demás dashboards no cambian)
midleware   MD_Sucursal.py     SEDE_MAIN_READERS; _is_main_reader -> verify_exact_permission
```

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Request y response no cambian; solo cambia quién pasa. Sin permiso → **401** `{"error": "No autorizado. Token invalido"}`; sin token → **401** `{"error": "Token not found"}`.
- Permisos exactos (prefijo `App.Department.`; Administrator pasa siempre):

| Endpoints | Permisos |
|---|---|
| `/almacen`: `GET /kardex`, `GET /movements/<type_m>`, `GET /inventory/products/<type_p>`, `GET /inventory/consolidated`, `GET /inventory/categories/all`, `GET /inventory/suppliers/allSuppliers`, `GET /codes/generate`, `GET /transfers`, `GET /transfer/<id>`, descargas `GET /file/download/products/{pdf,excel}`, `POST /file/download/movements/{pdf,excel}`, `POST /file/download/barcode`, `POST /file/download/barcode/multiple` | `ALMACEN`, `ALMACEN-VISUAL` |
| `/almacen`: `DELETE /movement`, `POST /multiple/movements`, `POST·PUT·DELETE /inventory/product`, `POST /inventory/multiple/products`, `POST /transfer`, `PUT /transfer/cancel`, `PUT /transfer/<id>/resolve`, `POST /file/upload/{regular,tool,internal}` | `ALMACEN` |
| `/almacen`: `POST·PUT /movement` | `ALMACEN`, `Epp` |
| `/almacen`: `GET /kardex/epp`, `GET /inventory/epp`, `GET /movements/epp/<type_m>`, `POST /file/download/eppmovements/{pdf,excel}` | `Epp`, `eppVisual`, `eppApprove` |
| `/almacen`: `GET /warehouses`, `GET /warehouses/catalogs`, `GET /warehouse/<id>`, `GET /reservations` | `ALMACEN`, `ALMACEN-VISUAL`, `Administracion` |
| `/almacen`: `POST·PUT /warehouse`, `POST·PUT·DELETE /reservation` | `ALMACEN`, `Administracion` |
| `/sucursal`: `GET /inventory`, `GET /inventory/main`, `GET /movements/<type_m>`, `GET /movement/<id>`, `GET /transfers`, `GET /transfer/<id>` | cualquier `Sucursal-<id>` (su sede), `ALMACEN`, `ALMACEN-VISUAL`, `Administracion` (cualquier sede) |
| `/sucursal`: `POST·PUT·DELETE /movement`, `PUT /transfer/receive` | solo `Sucursal-<id>` (su sede) |
| `/dashboard`: `POST /inventory/movements`, `GET /inventory/sm/<range>/<type>` | `ALMACEN`, `ALMACEN-VISUAL` |

### Gotchas

- El front ya muestra a `ALMACEN-VISUAL` solo la consulta de inventario. Si alguna pantalla le ofrecía botones de escritura, ahora reciben 401.
- `eppVisual` y `eppApprove` siguen viendo el inventario y los movimientos de EPP, pero ya no registran movimientos.
- `EppVisual`/`EppApprove` con mayúscula en el front no coinciden con el catálogo (`P-187`): esos usuarios no ven sus pantallas, aunque el API les responde.

## Al modificar

- Endpoint nuevo de almacén: usar las constantes `_ALM_*` / `_EPP_READ` / `_MOVEMENT_WRITE` según sea lectura o escritura; las descargas cuentan como lectura.
- Sede nueva: no hay cambio de código; basta el permiso `Sucursal-<id>` en el catálogo y asignárselo a su personal.
- Si cambian quiénes pueden leer cualquier sede, editar `SEDE_MAIN_READERS` en `MD_Sucursal.py`: lo usan el namespace y `_is_main_reader`.

## Verificación (2026-10-27, dev)

- `Tests/tester_permisos_almacen.py` 18/18:
  - lee los endpoints del código y prueba los 55 por 12 permisos (`ALMACEN`, `ALMACEN-VISUAL`, `Epp`, `eppVisual`, `eppApprove`, `Administracion`, `Sucursal-2`, `SM`, `adminCompras`, `DemoALMACEN`, `almacen` y `Administrator`) contra lo esperado;
  - los midlewares responden con stubs, así que no hay escrituras;
  - casos del grill y `_is_main_reader`;
  - una sede futura (`Sucursal-3`) pasa la puerta.
- Regresión con flujos reales de sede y traslados: `tester_multisede_resolve` 64/64 y `tester_transfer_over_receive` 10/10.
- `import app` sin errores; pyrefly sin errores en los archivos tocados.

## Notas posteriores

- **2026-10-28** — `GET /movements/<type_m>` y `GET /movements/epp/<type_m>` de `/almacen` ya no existen: se retiraron con `P-126` y la matriz baja de 43 a 41 endpoints de `/almacen`. `GET /sucursal/movements/<type_m>` sigue igual. → [`almacen_kardex_ventana.md`](almacen_kardex_ventana.md)
- **2026-10-28** — Los dos dashboards de inventario también dejan pasar a `App.Department.Director` (D14: `Director` ve todos los dashboards en lectura). → [`permisos_rrhh_bitacoras_cda_comun.md`](permisos_rrhh_bitacoras_cda_comun.md)
- **2026-10-28 — `P-209`.** `GET /inventory/suppliers/allSuppliers` abre también a SM, Compras y EPP en lectura (`_SUPPLIERS_READ`). Detalle → [`permisos_administracion.md`](permisos_administracion.md) (Notas posteriores 2026-10-28).
