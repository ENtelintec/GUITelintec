# Permisos exactos en RRHH, Bitácoras, CDA, Common, Misc y Dashboards — `/rrhh/*` · `/bitacora/*` · `/cda/*` · `/common/*` · `/misc/*` · `/dashboard/*`

> `P-198`, paquete "directo" (2026-10-28), siguiendo D6 de [`permisos_plan.md`](permisos_plan.md) y el mismo patrón de [`permisos_almacen.md`](permisos_almacen.md), [`permisos_sm.md`](permisos_sm.md) y [`permisos_sgi.md`](permisos_sgi.md). Los seis namespaces dejan `department=` (comparación por subcadena) y pasan a `permissions=[...]` (nombre exacto del catálogo). Son **129 llamadas de autorización**, y ya no queda ningún `department=` en esos archivos.
>
> **Nadie del catálogo pierde acceso.** Cada texto parcial de estos namespaces coincidía con un solo permiso del catálogo, salvo `"almacen"`, que también deja pasar a `ALMACEN-VISUAL` y se conservó. Los únicos que dejan de entrar son permisos fuera del catálogo. En dev y test aparecen dos, `DemoRRHH` y `DemoALMACEN`, con un usuario cada uno, y se quitan en prod con `P-196` (D15).
>
> Quedan para después Administración (remisiones, cotizaciones, saldos, entregas, BD), que necesita su propio grill, y `/UserSystem` con `credentials`, que va con `P-188`.

## Decisiones (mini-grill del 2026-10-28)

| Decisión | Resultado |
|---|---|
| `Director` (D14) | Ve **todos los dashboards en lectura**: los 4 de RRHH y los 2 de inventario. Nada de otras áreas. |
| CDA | **Igual que hoy**: `Administracion` y `SGI` leen y escriben. `checkvehicular` y `checkvApprove` se quedan solo en el checklist vehicular, ya ligados en [`permisos_sgi.md`](permisos_sgi.md). |
| Asistente virtual (`/misc/AV/*`) | Conserva a todos los que entraban por subcadena, `ALMACEN-VISUAL` incluido. Su POST le hace una pregunta al asistente; no escribe datos. |
| `emp_id=` | Sin cambio: el propio empleado sigue entrando a sus recibos de nómina y a sus encuestas asignadas, aunque no tenga el permiso del área. |

## Qué cambió (4 capas)

| Capa | Archivo | Cambio |
|---|---|---|
| **HTTP** | [`rs_RRHH.py`](../templates/resources/rs_RRHH.py) | `_RRHH`, `_RRHH_COMMON`; 58 llamadas. |
| | [`rs_Bitacora.py`](../templates/resources/rs_Bitacora.py) | `_BITACORAS`, `_RRHH`, `_BITACORAS_RRHH`; 15 llamadas. |
| | [`rs_CDA.py`](../templates/resources/rs_CDA.py) | `_DEPARTMENTS` → `_PERMISSIONS` en `_auth()`, que usan los 32 endpoints. |
| | [`rs_Common.py`](../templates/resources/rs_Common.py) | `_COMMON`, `_COMMON_BASIC` (`_CK_EMP` lo reutiliza) y `_RRHH`; 9 llamadas. |
| | [`rs_Misc.py`](../templates/resources/rs_Misc.py) | `_BASIC`, `_BASIC_COMMON`, `_AV`; 8 llamadas. |
| | [`rs_Dashboards.py`](../templates/resources/rs_Dashboards.py) | `_RRHH_DASH` (nuevo) y `_INVENTORY_DASH`, ambos con `Director`; 6 llamadas. |
| **Orquestación / DB / Modelos** | — | Sin cambios. |

`GET /rrhh/task/<emp_id>` sigue solo con `emp_id=`: lo abre el propio empleado o `Administrator`.

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer`; `jwt.decode` sobre el header tal cual). Sin permiso → `401` con `{"error": "No autorizado. Token invalido"}` (en `/rrhh` y `/cda` también puede venir el mensaje del token). Request y respuestas no cambian.
- **Permisos exactos por endpoint** (nombres completos del catálogo; `App.Department.Administrator` siempre pasa):

| Base | Endpoints | Permisos que abren |
|---|---|---|
| `/GUI/api/v1/rrhh` | todos, salvo los de abajo | `App.Department.RRHH` |
| | `PUT /task/quizz`, `GET /download/quizz/<type_q>` | `App.Department.RRHH`, `App.Department.Common` |
| | `GET /task/<emp_id>` | el propio empleado (`emp_id` del token) |
| `/GUI/api/v1/bitacora` | fichajes, reportes, extras, `GET /employees`, `GET /rh/all`, `POST /rh/date` | `App.Department.Bitacoras` |
| | `POST·PUT·DELETE /rh/event` | `App.Department.RRHH` |
| | `GET /contract_list` | `App.Department.Bitacoras`, `App.Department.RRHH` |
| `/GUI/api/v1/cda` | los 32 (vehículos, pólizas, servicios, llantas, multas, compras, vistas, alertas, avisos, fotos) | `App.Department.Administracion`, `App.Department.SGI` |
| `/GUI/api/v1/common` | `GET /vacations/events`, `POST /checkin`, `GET /checkin/me`, `GET /checkin/catalogs`, `GET /checkin/<id>/photo` | `App.Department.Common`, `App.Department.Basic` |
| | `GET /employees/<status>`, `GET /contracts` | `App.Department.Common` |
| | `GET /payroll/employee/<emp_id>`, `POST /payroll/employee/file` | `App.Department.RRHH` o el propio empleado |
| `/GUI/api/v1/misc` | notificaciones (`GET`, `POST`, `PUT`) y `GET /download/gui/settings` | `App.Department.Basic` |
| | `POST /AV/response`, `GET /AV/files/<department>` | `App.Department.ALMACEN`, `App.Department.ALMACEN-VISUAL`, `App.Department.Operaciones`, `App.Department.RRHH`, `App.Department.Administracion` |
| | `GET /dashboard` | `App.Department.Basic`, `App.Department.Common` |
| `/GUI/api/v1/dashboard` | `POST /fichaje/emp`, `GET /notifications/medicals`, `GET /rrhh/summary`, `POST /rrhh/series` | `App.Department.RRHH`, `App.Department.Director` |
| | `POST /inventory/movements`, `GET /inventory/sm/<range>/<type>` | `App.Department.ALMACEN`, `App.Department.ALMACEN-VISUAL`, `App.Department.Director` |

```json
// 401: token sin el permiso exacto (por ejemplo DemoRRHH en /rrhh/employees/info/all)
{"error": "No autorizado. Token invalido"}
```

- **Gotchas**:
  - El front compara nombres exactos, igual que el API ahora. `Director` ya entra a `GET /dashboard/rrhh/summary` y `POST /dashboard/rrhh/series`, pero `route-permissions.ts` le cierra la pantalla `/dashboard/rrhh/dashboard`, porque `/dashboard/rrhh` solo admite `RRHH` y `Administrator` (`P-206`).
  - Ninguna pantalla consume los dashboards de inventario.

## Verificación

Dev (2026-10-28):

- `Tests/tester_permisos_rrhh_comun.py` da **12/12**. Lee del código los 128 endpoints de los 6 namespaces (todos salvo `GET /rrhh/task/<emp_id>`) y confirma que no queda ningún `department=`. La matriz de 128 endpoints × 16 permisos no tiene diferencias; incluye `DemoRRHH`, `DemoALMACEN`, `Director`, `checkvehicular` y permisos de otras áreas, con los midleware reemplazados por stubs.
- Casos puntuales, todos como se esperaba:

  | Caso | Resultado |
  |---|---|
  | `Director` en `GET /dashboard/rrhh/summary` | pasa |
  | `Director` en `GET /rrhh/employees/info/all` | 401 |
  | `DemoRRHH` | 401 |
  | El propio empleado: recibos de nómina (`GET` y `POST`) y `GET /rrhh/task/<id>` | pasa |
  | Otro empleado en los mismos endpoints | 401 |
  | `checkvehicular` en `/cda/vehicles` | 401 |
  | `ALMACEN-VISUAL` en `POST /misc/AV/response` | pasa |

- Permisos actuales en dev y test: de 92 usuarios cada uno, los únicos permisos fuera del catálogo que dejaban pasar estos textos son `DemoRRHH` y `DemoALMACEN`, con un usuario cada uno.
- Regresión de permisos: Almacén 18/18 (su matriz ahora incluye a `Director` en los dashboards), SM 10/10, SGI 12/12, Compras 113/113.
- Regresión funcional contra la BD de dev: check-in 37/37, CDA alertas y fotos 43/43, descarga de nómina 19/19, PDF de eva 360 13/13, CSV de vacaciones 30/30, PDF de encuestas 16/16, correos de empleados 23/23.
- `pyrefly check --python-version 3.11`: 166 errores, igual que antes. El de `rs_Bitacora.py` (`from_json` sin `# pyrefly: ignore`) ya existía; solo cambió de línea.

## Al modificar

- Un endpoint nuevo en estos namespaces usa la constante de su grupo. Si necesita otra combinación, se crea una constante con nombres del catálogo, nunca `department=`.
- Un permiso nuevo para estas áreas se da de alta primero en el catálogo, desde la app de usuarios ([`gui_system_tareas.md`](gui_system_tareas.md)).
- Si `Director` debe ver algo más que dashboards, se agrega por endpoint de lectura en su área y se anota aquí.
