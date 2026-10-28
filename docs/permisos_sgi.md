# Permisos exactos en SGI (`/sgi/voucher/*`, `/sgi/format*`)

Fecha: 2026-10-27 · **Estado: hecho y verificado contra dev** (`Tests/tester_permisos_sgi.py` 12/12: matriz de 32 endpoints por 17 permisos sin diferencias, con midleware y controllers reemplazados por stubs para no tocar la BD; regresión con S3 simulado: `tester_iso_formats` 48/48, `tester_vales_put_anexos` 49/49, `tester_voucher_files_epp_tools` 29/29, `tester_voucher_vehicle_attachments` 31/31, `tester_checklist_full_pdf` 15/15, `tester_voucher_vehicle_accessories` 7/7). Sin DDL.

Cuarta área de `P-198`, después de Compras, Almacén y SM. Decisiones del grill del 2026-10-27, en [`permisos_plan.md`](permisos_plan.md) (Notas posteriores).

## Qué cambia

Antes, todo `/sgi/voucher*` pedía `sgi` o `voucher`. Por la subcadena, cualquiera de los 4 permisos de vales entraba a todo. Y quedaban fuera usuarios a los que el front sí les muestra la pantalla:
- quien solo tiene `Epp` o `eppApprove` y aprueba vales EPP;
- `ALMACEN` en su lista de vales;
- `checkvehicular`, `Operaciones`, `Administracion` y `RRHH` en el checklist vehicular.

Con la comparación exacta (`permissions=`):

- **Vales de herramienta**:
  - crear, editar, borrar, listar y anexos: `SGI`, `Voucher` y `voucherTool`;
  - el listado y el cambio de estado (`PUT /voucher/toolsState`) además para `voucherApprove` y `ALMACEN`.
- **Vales de EPP**:
  - crear, editar, borrar, listar y anexos: `SGI`, `Voucher` y `voucherSafe`;
  - el listado y la aprobación (`PUT /voucher/safetyState`) además para `voucherApprove`, `Epp`, `eppApprove` y `ALMACEN`.
- **Checklist vehicular**:
  - listar, crear, editar (incluye aprobar), PDF y anexos: `SGI`, `Voucher`, `checkvehicular`, `checkvApprove`, `Operaciones`, `Administracion` y `RRHH`. Es lo que el front ya mostraba;
  - borrar: `SGI`, `Voucher` y `checkvApprove`;
  - con esto se ligan `checkvehicular` y `checkvApprove` (D14).
- **Formatos ISO, sin cambios**: lecturas `SGI` y `Administracion`; alta, edición, borrado y estatus solo `SGI`.
- **Acceso nuevo:** `Epp`, `eppApprove`, `ALMACEN`, `voucherApprove`, `checkvehicular`, `checkvApprove`, `Operaciones`, `Administracion` y `RRHH`, cada uno en lo suyo.
- **Acceso que se pierde:** `voucherTool` deja de entrar a los vales de EPP, `voucherSafe` a los de herramienta y `voucherApprove` a crear o editar vales; ninguno de los tres entra al checklist.
- La descarga duplicada `POST /admin/collections/voucher/vehicle/attachment/download` usa el mismo grupo que el checklist (el front usa la de `/sgi`).
- El catálogo del control de saldos (`GET /admin/collections/balanceControl/catalogs`, que también pide `sgi`) se migra con Administración.

## Capas tocadas

```
rs          rs_SGI.py               _TOOLS / _TOOLS_STATE / _SAFETY / _SAFETY_STATE / _VEHICLE / _VEHICLE_DELETE en 15 endpoints;
                                    _voucher_attachment_{upload,delete,download}(..., permissions) por tipo en los 9 anexos;
                                    _FMT_READ / _FMT_WRITE con nombres exactos en los 7 de formatos
rs          rs_Admin_collections.py descarga duplicada de anexos del checklist -> VEHICLE_CHECKLIST_PERMS
midleware   MD_SGI.py               VEHICLE_CHECKLIST_PERMS (grupo compartido del checklist)
```

## Contrato mínimo para el front

- **Base** `/GUI/api/v1/sgi` · **Auth**: header `Authorization` con el **JWT crudo, NO `Bearer <token>`**. Request y response no cambian; solo cambia quién pasa. Sin permiso → **401** `{"error": "No autorizado. Token invalido"}`; sin token → **401** `{"error": "Token not found"}`.
- Permisos exactos (prefijo `App.Department.`; Administrator pasa siempre):

| Endpoints | Permisos |
|---|---|
| `POST·PUT·DELETE /voucher/tools`, anexos `POST·DELETE /voucher/tools/attachment-<id>`, `POST /voucher/tools/attachment/download` | `SGI`, `Voucher`, `voucherTool` |
| `GET /voucher/tools/<y>&<m>&<d>`, `PUT /voucher/toolsState` | `SGI`, `Voucher`, `voucherTool`, `voucherApprove`, `ALMACEN` |
| `POST·PUT·DELETE /voucher/safety`, anexos `POST·DELETE /voucher/epp/attachment-<id>`, `POST /voucher/epp/attachment/download` | `SGI`, `Voucher`, `voucherSafe` |
| `GET /voucher/safety/<y>&<m>&<d>`, `PUT /voucher/safetyState` | `SGI`, `Voucher`, `voucherSafe`, `voucherApprove`, `Epp`, `eppApprove`, `ALMACEN` |
| `GET /voucher/vehicle/<y>&<m>&<d>`, `POST·PUT /voucher/vehicle`, `GET /voucher/vehicle/download/pdf/<id>`, anexos `POST·DELETE /voucher/vehicle/attachment-<id>`, `POST /voucher/vehicle/attachment/download` (y la duplicada en `/admin/collections`) | `SGI`, `Voucher`, `checkvehicular`, `checkvApprove`, `Operaciones`, `Administracion`, `RRHH` |
| `DELETE /voucher/vehicle` | `SGI`, `Voucher`, `checkvApprove` |
| `GET /formats`, `GET /formats/catalogs`, `GET /format/<id>` | `SGI`, `Administracion` |
| `POST·PUT·DELETE /format`, `PUT /format/status` | `SGI` |

### Gotchas

- Lo que antes daba 401 y ahora pasa:
  - la pantalla de aprobación de vales EPP con `Epp` o `eppApprove`;
  - la lista de vales de almacén con `ALMACEN`;
  - el checklist vehicular con `checkvehicular`, `Operaciones`, `Administracion` o `RRHH`.
- El front escribe `EppApprove` con mayúscula (`P-187`): hasta corregirlo, quien solo tenga `eppApprove` no ve la pantalla, aunque el API ya le responde.
- Las pantallas de vales del front piden solo `Voucher`: quien tenga solo `voucherTool`, `voucherSafe` o `voucherApprove` pasa el API pero no ve esas pantallas (`P-200`).

## Al modificar

- Endpoint nuevo de vales: `_TOOLS` / `_SAFETY` para el ciclo de vida de cada tipo; `_TOOLS_STATE` / `_SAFETY_STATE` para listar y cambiar el estado.
- Endpoint nuevo del checklist: `VEHICLE_CHECKLIST_PERMS` (en `MD_SGI.py`), así `rs_SGI` y `/collections` no se separan.
- Anexos: los helpers `_voucher_attachment_*` reciben la lista de permisos del tipo de vale; un tipo nuevo pasa su propia lista.

## Verificación (2026-10-27, dev)

- `Tests/tester_permisos_sgi.py` 12/12:
  - matriz de 32 endpoints, leídos del código incluidos los anexos por helper, contra 17 permisos;
  - casos del grill: aprobación EPP, almacén, checklist, borrado y formatos.
- Regresión con S3 simulado: ISO 48/48, anexos y `PUT` de vales 49/49 y 29/29, anexos del checklist 31/31, PDF completo del checklist 15/15, accesorios 7/7.
- `import app` sin errores; pyrefly sin errores en los archivos tocados.
