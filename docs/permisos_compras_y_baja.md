# Permisos exactos en Compras y aviso de baja (`permissions=`, `/admin/collections/*`, `DELETE /rrhh/employee/terminate`)

Fecha: 2026-10-27 · **Estado: hecho y verificado contra dev (113/113 `Tests/tester_permisos_compras_baja.py`; regresión en verde: `tester_po_match_cantidades` 41/41, `tester_balance_movement` 31/31, `tester_remission_pdf_ocd` 17/17). Sin DDL (el de la tabla de permisos va aparte, `P-193`).** Cierra `P-191`.

Primera implementación del [`permisos_plan.md`](permisos_plan.md): D6 (comparación exacta), D8 (aviso de baja), D12 (Compras como primera área) y D13 (textos que no corresponden a ningún permiso).

## Qué cambia

- **Parámetro nuevo `permissions=[...]`** en `token_verification_procedure` ([`Functions_Aux_Login.py`](../templates/resources/methods/Functions_Aux_Login.py), `verify_exact_permission`):
  - recibe nombres completos del catálogo y compara **exacto, con mayúsculas**: `App.Department.ALMACEN` no deja pasar a `ALMACEN-VISUAL`;
  - `App.Department.Administrator` pasa siempre;
  - es un OR con `department=` y `emp_id=`, que no cambian;
  - sigue leyendo solo el token, sin consultas a la BD.
- **Compras migrada a `permissions=`** ([`rs_Admin_collections.py`](../templates/resources/rs_Admin_collections.py), constantes `_PO_*`). Son 24 endpoints, que antes pedían `administracion` más `orders`/`purchases` (que no correspondían a ningún permiso), o solo `administracion`.
  - **Acceso nuevo:** `adminCompras` entra a OC, solicitudes, bitácora de compras y lista de compra, y `comprasCreate` lista, crea y edita solicitudes.
  - **Acceso que se pierde:** `comprasCreate` ya no descarga el PDF de la OC; lo había ganado en la mañana con `P-185`, que pedía la subcadena `compras`.
- **Textos que no corresponden a ningún permiso, fuera** (D13). No cambia quién entra:
  - `purchases` en 15 endpoints que no son de Compras: remisiones, cotizaciones de actividad, control de saldos y control de entregas;
  - `remission` en `GET /admin/presales/products/contracts`;
  - `iaotros` y `respe` en `GET /admin/DB/heads`.
- **Aviso de baja a los administradores** (D8, [`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py)):
  - **cuándo:** un empleado pasa de `activo` a `inactivo`, por `DELETE /rrhh/employee/terminate` o por el `PUT` del empleado con `status`, y tiene usuario en `users_system`;
  - **qué:** una notificación con `app: ["administrator"]`, título "Usuario pendiente de baja" y mensaje "Dar de baja del sistema de usuarios a `<usuario>` (empleado N, baja por `<motivo>`)…";
  - **no avisa** si el empleado ya estaba inactivo o no tiene usuario;
  - no es fatal y RH sigue recibiendo su aviso;
  - el usuario se borra a mano en la app de usuarios (T2 de [`gui_system_tareas.md`](gui_system_tareas.md)).

## Capas tocadas

```
methods     Functions_Aux_Login.py          ADMINISTRATOR_PERMISSION · verify_exact_permission · verify_token(..., permissions)
                                            · token_verification_procedure lee kwargs["permissions"]
rs          rs_Admin_collections.py         _PO_PERMS / _PO_APPLICATION_PERMS / _PURCHASE_LIST_PERMS en 24 endpoints;
                                            "purchases" fuera de 13 listas y de _BC_READ/_DC_READ
rs          rs_Admin_presales.py            GET /products/contracts sin "remission"
rs          rs_Admin_DB.py                  GET /heads sin "iaotros"/"respe"
midleware   Functions_midleware_RRHH.py     _employee_status · _notify_user_offboarding · _departure_reason;
                                            terminate_employee_from_api y update_employee_db avisan en activo -> inactivo
```

Controllers reusados: `test_id_employee` (estado previo) y `get_user_by_emp_id`.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**.
- **Request y response no cambian** en ningún endpoint: solo cambia quién pasa. Sin permiso → **401** `{"error": "No autorizado. Token invalido"}`; sin token → **401** `{"error": "Token not found"}`.
- **Base** `/GUI/api/v1/admin/collections`. Permisos exactos (Administrator pasa siempre):

| Endpoint | Permisos exactos |
|---|---|
| `GET /orders/<status>` · `POST·PUT·DELETE /order` · `PUT /order/status` | `App.Department.Administracion`, `App.Department.adminCompras` |
| `GET /application/orderstoApprove` · `DELETE /application/order` · `PUT /application/order/status` | `Administracion`, `adminCompras` |
| `GET /application/orders/<status>` · `POST·PUT /application/order` | `Administracion`, `adminCompras`, `comprasCreate` |
| `GET /POItemsFoDelivery` · `GET /APOItemsFastOrder` | `Administracion`, `adminCompras` |
| `GET /purchase/download/pdf/<po_id>` · `GET /purchase/folio/<folio>` · `GET /purchase/movements/match` | `Administracion`, `adminCompras` |
| `GET·POST·PUT·DELETE /purchaseManagement` · `PUT /purchaseManagement/cancel` · `GET /purchaseManagement/catalogs` · `GET /purchaseManagement/<id>` | `Administracion`, `adminCompras` |
| `GET /purchase/download/pdfItemsPurchaseStorage` | `Administracion`, `adminCompras`, `ALMACEN`, `ALMACEN-VISUAL` |

(Todos con prefijo `App.Department.`.) Los demás endpoints del módulo no cambian de permisos.

- **Notificación nueva** para quien tenga `App.Department.Administrator`: título `Usuario pendiente de baja`, por el mismo endpoint de notificaciones de siempre.

### Gotchas

- El front decide qué pantallas mostrar con su propia lista (`route-permissions.ts`), que no tiene `adminCompras` ni `comprasCreate`: hasta `P-192`, esos usuarios pasan el API pero no ven las pantallas.
- Comparación exacta: `App.Department.admincompras` (con minúscula) **no** pasa.
- Las listas de OC y de solicitudes siguen filtrando por quien las creó, salvo administradores y gerentes: un usuario con `adminCompras` que no es gerente ve solo las suyas, igual que uno de `Administracion`.

## Al modificar

- **Endpoint nuevo de Compras**: usar `_PO_PERMS` / `_PO_APPLICATION_PERMS`, no `department=`.
- **Migrar otra área**: misma receta. Constantes con nombres completos del catálogo junto al namespace y `permissions=` en cada endpoint. Revisar qué permisos dejaba pasar la subcadena de antes para no quitar acceso sin decidirlo.
- **Un permiso que no existe** va primero a [`gui_system_tareas.md`](gui_system_tareas.md) (regla D4 de `CLAUDE.md`).
- El aviso de baja usa `app: ["administrator"]`: los lectores de notificaciones comparan la última parte de cada permiso (`administrator`) con un `REGEXP` sobre `app`.

## Verificación (2026-10-27, dev)

- `Tests/tester_permisos_compras_baja.py`, 113/113:
  - `verify_exact_permission`: visual contra completo, Administrator, mayúsculas y token vacío;
  - matriz HTTP de los 24 endpoints con `Administracion`, `adminCompras`, `Administrator`, `comprasCreate`, `ALMACEN`, `ALMACEN-VISUAL`, `Operaciones`, `SM`, `admincompras` y `adminComprasX`;
  - acceso sin cambio en remisiones, saldos, entregas, `/heads` y `/products/contracts`;
  - baja con usuario (1 aviso), repetida (sin aviso), sin usuario (sin aviso), `PUT` de activo a inactivo (1 aviso con el motivo) y de inactivo a inactivo (sin aviso).
  - Empleados y usuarios temporales borrados al final.
- **Incidente en dev, limpiado.** La primera corrida mandó `{}` a `PUT /order/status`, `PUT /application/order/status` y `POST /purchaseManagement`, que aceptan un body vacío y escriben. Dejó 3 registros en `purchase_management` y 9 notificaciones; ya se borraron (`purchase_management` volvió a 0 filas). El hueco de validación quedó en `P-197`.

## Pendientes

- `P-192` **[front]**: `adminCompras` y `comprasCreate` en `route-permissions.ts` para las pantallas de Compras.
- `P-197` **[back]**: `PUT /order/status` y `PUT /application/order/status` aceptan un body sin `id` y responden 200, con un aviso "ID None". `POST /purchaseManagement` crea un registro vacío.
