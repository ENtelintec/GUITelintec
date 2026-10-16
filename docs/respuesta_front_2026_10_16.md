# Respuesta al avance del front del 2026-10-15

Fecha: 2026-10-16 · **Estado: back hecho y verificado contra dev** (todo lo de código; el DML lo corre el usuario). Responde al reporte `docs/avance-plan-accion-2026-10.md` del repo del front (estado al 2026-10-15) tras el grill del 2026-10-16 con el usuario. Cada pieza tiene su doc con el "Contrato mínimo para el front"; aquí solo el resumen, las decisiones y la respuesta a cada duda. Estado por ítem: [`pendientes.md`](pendientes.md).

## 1. Bloqueos reportados → corregidos

| Bloqueo del front | Causa confirmada | Qué cambió | Doc |
|---|---|---|---|
| **Guardar un vale EPP o de herramientas borra sus anexos** (bloqueaba `P-125`) | `update_voucher_tools`/`update_voucher_safety` hacían `SET extra_info = '{}'`; el midleware nunca pasaba `extra_info` | El `PUT` **no toca `extra_info`** y el history crece en BD con `JSON_ARRAY_APPEND` (el `history` del body **se ignora**; mandarlo o no da igual). Ya no hace falta "guardar primero y subir anexos al final" | [`vales_anexos_descarga_borrado.md`](vales_anexos_descarga_borrado.md) |
| **Faltaban descarga y borrado de anexos** en EPP/herramientas | Solo existía el alta (y la descarga del vehicular) | `POST /sgi/voucher/<kind>/attachment/download` (blob en 200) y `DELETE /sgi/voucher/<kind>/attachment-<id>` `{filename, reason?}` para `vehicle`, `epp` y `tools`; firmas (`firma-*`) → 400; 404 vale/archivo; 409 = repetir. El 200 del DELETE trae `data.files` restantes | idem |
| **El empleado no ve el nombre de encuestas nuevas** | `GET /rrhh/task/<emp_id>` devolvía el body crudo sin nombre del modelo | `body.metadata.quizz_name` enriquecido en lectura para **toda** tarea (`null` si el modelo ya no existe). Nada que pedir aparte | [`quizz_models_versionado.md`](quizz_models_versionado.md) · Notas posteriores |
| **Recibos de nómina históricos sin archivo en S3** | Llaves de la época de SharePoint en `files_data` | **Decisión: nómina arranca limpia, no se migra.** DML `P-141` vacía el índice de todos y borra los avisos `payload.kind = payroll` (lo corre el usuario en dev/test/prod). Hasta entonces el aviso ámbar del front está bien | [`nomina_descarga_recibo.md`](nomina_descarga_recibo.md) · Notas posteriores |

## 2. Requerimientos → endpoints nuevos

| Pedido | Endpoint | Resumen del contrato | Doc |
|---|---|---|---|
| Editar la fecha de autorización de un movimiento de saldo (Cobranza) | **`PUT /admin/collections/balanceControl/movement`** | `{id_movement, movement_date?: "YYYY-MM-DD", reason?}` (al menos uno); **solo** fecha y motivo, el resto se ignora (monto/tipo/vigencia inmutables); 200 = la fila con el shape de `movements[]` + `control_id`; 400 nada que corregir / fecha inválida / control cancelado; 404. History del control con `changes` solo de lo que cambió | [`control_saldos_movimientos.md`](control_saldos_movimientos.md) · Notas posteriores 2026-10-16 · `P-142` |
| Resolver diferencias de un traslado (`P-047`) | **`PUT /almacen/transfer/<id>/resolve`** | `{items: [{id_product, action: "reingreso" \| "merma", comment?}], comment?}` con **todos** los productos faltantes; solo en status 2; `reingreso` = entrada al kardex del principal por la diferencia (ligada al folio), `merma` = solo registro; status nuevo **4 DIFERENCIA RESUELTA**; 200 = el traslado completo (shape de `GET /transfer/<id>`) con `items[].resolution` | [`almacen_multisede_resolve.md`](almacen_multisede_resolve.md) · `P-145` |
| `GET /sucursal/movement/<id>` | **nuevo** | `data {warehouse, movement, product}`; `movement` con las mismas llaves que una fila del kardex de sede; 403 sede ajena, 404, 400 si es del principal | idem |
| Traslados sin aviso de recorte | `GET /almacen/transfers` · `GET /sucursal/transfers` | `meta {limit, returned, truncated}` (default 200, máx 2000), como el kardex | idem |
| Formatos de traslados/sede | — | fechas `YYYY-MM-DD HH:MM:SS` en todo (adiós la "T"), `udm` sin espacios; los ids de usuario **siguen siendo ids** (el front los resuelve con Common) | idem |
| Firma de "quien entrega" en la SM (`P-045`) | `POST /sm/attachment-<id>` | Nombres `<id>-firma-recibido-<marca>.png` (+`title`, mueve status) y `<id>-firma-entrega-<marca>.png` (opcional, **no** mueve status); misma `<marca>` (epoch ms) en los dos = misma entrega; la de entrega se dibuja en la 3ª columna de esa fila; sin pareja se guarda y no se dibuja | [`sm_pdf_delivery_signatures.md`](sm_pdf_delivery_signatures.md) · Notas posteriores 2026-10-16 |

## 3. Respuesta a cada duda

**Dashboard RH (`P-043`)**: (1) `error` del summary ahora es `[{key, msg}]` con `key` ∈ `medical_expiring | vacations | quizzes` (la llave de `data` que viene `null`). (2) Series con el mes del navegador vs summary en `America/Mexico_City`: se acepta, solo difiere el día del cambio de mes.

**CDA (`P-109`)**: (1) miniaturas → pendiente nuevo `P-144`, no ahora. (2) Sin endpoint de título de foto; se queda "Foto N". (3) `days_left` en `mantenimiento_pendiente` ahora es `null` cuando venció por km (solo el vencido por fecha lo trae). (4) `secure_filename` confirmado; `replaced` de la respuesta es la fuente de verdad. (5) **Todo** `/cda` exige `administracion`/`sgi`, no solo alertas.

**Multisede (lote 5)**: (1, 2) El administrador escribe y recibe en cualquier sede **a propósito** (mismo criterio que el resto del API); se corrigieron los docs F2/F3, no el código. (3) `GET /sucursal/movement/<id>` hecho. (4) Fechas y `udm` normalizados; nombres de usuario no se resuelven en el back. (5) `meta.truncated` hecho. (6) Decimales valen para cualquier producto. (7) `comment` por renglón opcional. (8) Diferencias: sí era intencional que no hubiera movimiento; ahora existe el `resolve` (reingreso | merma); **quién** lo captura lo decide administración (`P-145`); el botón "Resolver diferencia" va en el front.

**Control de saldos (lote 3)**: (1) `P-137` hecho: **prod y test no tienen ninguna remisión ni control** (el módulo de remisiones aún no se usa en prod); Cobranza crea el control de cada contrato al capturar su primera remisión; 0 controles sin formato. (2) `?expiring_days=` se queda, sin uso del front. (3) **Sin contrato**: el back se queda como está (remisión y control sin contrato siguen aceptados) y **el front no hace nada** (`P-079` cerrado): no se construyen pantallas ni se vuelve a ofrecer el control sin contrato; el paso B3 se prueba con contrato. (4) Fecha de autorización: hecho (`PUT /balanceControl/movement`, incluye `reason`).

**Firma de "quien entrega"**: SM aceptada tal cual la propuesta (nombres y marca compartida), back hecho. **Remisión (`P-054`): no lleva firma** — cerrado por decisión del usuario (el reporte anexo ya trae la firma del líder y Control de saldos/administración confirman la entrega); se retoma solo con petición explícita de administración.

**Anexos de vales (`P-125`, punto 3 "para qué se usan")**: lo define Almacén/SGI con la usuaria; el back no restringe tipos de documento.

**Otros**: `P-126` hecho en el front, pero `GET /movements/<type_m>` y `/movements/epp/<type_m>` **no se retiran hasta que el usuario confirme el despliegue**; siguen deprecados e intactos. `P-070` recibió la marca 🧪 que faltaba. Doc desactualizado del front (`pendientes-control-saldos.md` §14.2): corregirlo allá, el cruce es por `balance_control_id`.

## 4. Qué se marcó en `pendientes.md`

- `[x]`: `P-133`, `P-109`, `P-043`, `P-030`, `P-134`, `P-137`, `P-047` (back), `P-054` (decisión).
- **Siguen 🧪** `P-057`, `P-068`, `P-073`, `P-074`, `P-088`, `P-093`: la prueba local de la usuaria con cuenta Administrador quedó anotada, pero el `[x]` es con el visto bueno de **Cobranza en test** (`P-094`), como se acordó el 2026-10-13.
- `P-049` abierto solo por prod (`P-048`); `P-125` abierto por los botones; `P-045` con back hecho; `P-126` abierto hasta el deploy.
- Nuevos: `P-141` DML nómina limpia (usuario) · `P-142` lápiz por movimiento (front) · `P-143` `quizz_name` en Tareas (front) · `P-144` miniaturas CDA (back, después) · `P-145` resolver diferencias: quién captura (admin) + botón (front).

## 5. Qué sigue en el front (en este orden)

1. `P-125` botones **Descargar** y **Eliminar** en Anexos de vale y retirar el aviso "guarda primero el formulario".
2. `P-143` pintar `metadata.quizz_name` en Comun → Tareas.
3. `P-142` lápiz de fecha/motivo en el historial de inyecciones.
4. `P-045` segundo pad "Firma de quien entrega" en la pantalla de firmas de la SM.
5. `P-145` botón "Resolver diferencia" en el detalle del traslado (reingreso | merma por renglón) y mostrar `items[].resolution` / status 4; consumir `meta.truncated` en traslados.
6. Dashboard RH: leer `error[].key`; CDA: `days_left` null en vencidos por km.
7. Terminar la prueba de `P-070` y la sesión de Cobranza en test cuando exista `P-094`.

## 6. Verificación (dev, 2026-10-16)

| Tester (gitignored) | Checks |
|---|---|
| `Tests/tester_vales_put_anexos.py` | 49/49 (+ regresión `tester_voucher_files_epp_tools.py` 29/29, `tester_voucher_vehicle_attachments.py` 31/31) |
| `Tests/tester_front_fixes_2026_10_16.py` | 12/12 (`quizz_name`, `days_left`, `error` del dashboard) |
| `Tests/tester_balance_movement_put.py` | 34/34 (+ regresión `tester_balance_movement.py` 31/31) |
| `Tests/tester_multisede_resolve.py` | 64/64 |
| `Tests/tester_sm_firma_entrega.py` | 30/30 (PDF renderizado y revisado) |

`pyrefly check` completo: 178 errores, los mismos 178 de `HEAD` (0 nuevos). `P-137` en solo lectura contra dev, test y prod. Sin DDL; un DML (`P-141`) pendiente de correr por el usuario.
