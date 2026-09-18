# CDA: alertas y recordatorios de vehículos + fotos del expediente

Fecha: 2026-09-17 · **Estado: hecho y verificado contra dev (43/43 checks HTTP con S3 simulado, `Tests/tester_cda_alertas_fotos.py`). Sin DDL** (las fotos van en `vehicles.extra_info.photos`).

Cierra dos pendientes de [`control_vehiculos_cda.md`](control_vehiculos_cda.md): **recordatorios programados** (hoy solo se notificaba alta/baja de vehículo) y **captura de foto real del vehículo** (pedida al acordar el PDF del checklist, cuyas siluetas son genéricas — [`checklist_vehicular_pdf.md`](checklist_vehicular_pdf.md)).

## Alertas (`GET /cda/alerts`)

Todo **calculado on-read** sobre las mismas vistas del módulo (`fetch_policies_view`, `fetch_maintenance_view`, `fetch_refrendos_view`, `fetch_tires_view`): no hay tabla de alertas ni estado que se desincronice. Solo vehículos activos por default.

| `kind` | `severity` | Cuándo |
|---|---|---|
| `sin_poliza` | `sin_registro` | sin póliza activa |
| `poliza_vencida` | `vencido` | `date_end < hoy` |
| `poliza_por_vencer` | `proximo` | `hoy ≤ date_end ≤ hoy + days` |
| `pago_poliza_vencido` | `vencido` | slot de `payments` con `overdue` (uno por slot) |
| `mantenimiento_pendiente` | `vencido` | `requires_maintenance` de la vista: sin registro, por km (`current_km ≥ último km + intervalo`) o por fecha (`> 6 meses`) |
| `mantenimiento_proximo` | `proximo` | `0 ≤ days_remaining ≤ days` |
| `refrendo_vencido` | `vencido` | `refrendo_status = VENCIDO` (último pago de un año anterior) |
| `refrendo_sin_registro` | `sin_registro` | sin `refrendo_last_paid` |
| `llanta_vencida` | `vencido` | llanta registrada con `expired` |
| `llanta_cambio` | `proximo` | llanta con `needs_change = 1` |

Orden: `vencido` → `sin_registro` → `proximo`, y dentro por `days_left` ascendente. `days` (horizonte de "por vencer") default **30**, query `?days=N`; `?all=1` incluye vehículos dados de baja.

## Recordatorios (`GET /cda/notifications`)

No hay scheduler en el repo; se sigue **el mismo patrón que los avisos médicos** (`GET /dashboard/notifications/medicals`, [`notificaciones_medicas_fix.md`](notificaciones_medicas_fix.md)): la **primera llamada del día** lanza un hilo (`NotificationsSearch(type_n="cda")` → `CDANotifications`) que arma **una notificación de sistema** para los permisos `sgi` + `administracion` con una línea por alerta (`[Póliza vencida] TC-01: la póliza … venció el …`). Sin alertas → no crea nada. Flags en `files/flags_daemons.json`: `flag_cda` (en curso) y `last_date_cda` (última corrida); el `finally` del hilo restablece `flag_cda` aunque truene. El front del dashboard de CDA debe llamarlo al abrir, como hace RH.

## Fotos del vehículo

| Tema | Decisión |
|---|---|
| Almacenamiento | S3 `S3_ADMIN_BUCKET`, key `cda/vehicles/<id_vehicle>/<filename>`; índice en `vehicles.extra_info.photos = [{filename, path, title, timestamp, user}]`, aplanado como `photos[]` en el vehículo (`GET /vehicle/<id>` y listados). |
| Formatos | `jpg`, `jpeg`, `png`, `webp`; una por request (multipart `file` + `title` opcional, default `Foto N`). Tope **20** por vehículo. |
| Mismo nombre | Reemplaza la entrada (y el objeto en S3), `replaced: true`. Único camino para corregir una foto. |
| Borrado | BD primero, S3 best-effort: si S3 falla → `200` con `s3_deleted: false` + motivo en `error` (nunca queda un `path` muerto). |
| Descarga | binario en `200`, envelope JSON en `4xx`. |
| `history` del vehículo | entrada `action: "Foto"` por alta/reemplazo/baja. |

## Las capas tocadas

```
controller  vehicles/vehicles_controller.py   update_vehicle_extra_info (nuevo: solo extra_info + history)
midleware   MD_CDA.py                          build_cda_alerts · get_cda_alerts_api · build_cda_notification_lines · ALERT_KINDS
                                               upload/download/delete_vehicle_photo_api · _vehicle_to_dict expone photos[]
daemon      daemons/NotificationsSearch.py     CDANotifications + rama "cda" (flag_cda)
models      api_cda_models.py                  expected_files_vehicle_photo (parser) · cda_vehicle_photo_model · CdaVehiclePhotoForm
routes      rs_CDA.py                          GET /alerts · GET /notifications · POST /vehicle/photo-<id> · GET|DELETE /vehicle/photo
```

## Contrato mínimo para el front

- **Auth**: header `Authorization` con el **JWT crudo** (sin `Bearer `). Permisos `administracion` / `sgi` (todo el namespace).
- **Base**: `/GUI/api/v1/cda`.
- **Respuesta**: `{data, msg, error}`; la descarga de foto devuelve **blob en 200** y JSON en 4xx.

### `GET /alerts?days=30&all=0`

```json
{"data": {
  "days_ahead": 30,
  "alerts": [
    {"vehicle_id": 3, "code": "TC-01", "plate": "ABC-123", "kind": "poliza_vencida", "kind_label": "Póliza vencida",
     "severity": "vencido", "message": "TC-01: la póliza Qualitas venció el 2026-08-13 (hace 35 días)",
     "due_date": "2026-08-13", "days_left": -35, "policy_id": 7},
    {"vehicle_id": 3, "code": "TC-01", "plate": "ABC-123", "kind": "mantenimiento_pendiente", "kind_label": "Mantenimiento pendiente",
     "severity": "vencido", "message": "TC-01: mantenimiento pendiente por kilometraje (56000 km ≥ 55000 km)",
     "due_date": "2027-03-07", "days_left": 171, "next_km": 55000},
    {"vehicle_id": 5, "code": "TC-03", "plate": null, "kind": "llanta_vencida", "kind_label": "Llanta vencida (DOT)",
     "severity": "vencido", "message": "TC-03: llanta Delantera izquierda vencida (DOT 1019, vence 2026-09-16)", "due_date": "2026-09-16", "days_left": null, "position": 1}
  ],
  "summary": {"total": 3, "vehicles_with_alerts": 2, "by_kind": {"poliza_vencida": 1, "mantenimiento_pendiente": 1, "llanta_vencida": 1}, "by_severity": {"vencido": 3}},
  "kinds": {"sin_poliza": "Sin póliza vigente", "...": "..."}
 }, "msg": "3 alertas en 2 vehículos", "error": null}
```

Campos extra por `kind`: `policy_id` (pólizas), `payment` (índice del slot), `next_km` (mantenimiento), `position` (llantas). `days_left` negativo = vencido hace N días; `null` cuando no aplica. `error` trae una lista si alguna vista falló (las demás sí se calculan).

### `GET /notifications`

`201` "Buscando alertas de vehículos" la primera vez del día · `200` "Ya se realizó…" después · `200` "Se está ya realizando…" si el hilo corre. La notificación aparece en la bandeja de `sgi`/`administracion` (`GET /misc/notifications/...`).

### Fotos

| Método y ruta | Body | Éxito |
|---|---|---|
| `POST /vehicle/photo-<id_vehicle>` | multipart `file` (jpg/jpeg/png/webp) + `title?` | `201` `data: {id_vehicle, photo: {filename, path, title, timestamp, user}, replaced, photos: [...]}` |
| `GET /vehicle/photo?id_vehicle=3&filename=frente.jpg` | — | `200` blob (`Content-Disposition: attachment`) · `400` JSON si no existe · `404` vehículo |
| `DELETE /vehicle/photo` | `{id_vehicle, filename}` | `200` `data: {id_vehicle, s3_deleted, photos}` (`error` con motivo si S3 falló) · `400` foto inexistente |

Errores del POST: `400` "Formato no válido (pdf); se aceptan jpg, jpeg, png, webp" · `400` "El vehículo ya tiene 20 fotos…" · `404` vehículo · `400` S3 (`msg` "Error al subir la foto a S3" / "Credenciales AWS no configuradas") — en ese caso **no** se indexa nada.

### Gotchas

- `photos[]` viene en el vehículo ya aplanado; no hay que leer `extra_info.photos`. Tras `POST`/`DELETE`, `data.photos` es la lista completa para repintar sin re-`GET`.
- `filename` del `GET`/`DELETE` acepta también el `path` completo.
- Las alertas no se "cierran": desaparecen solas cuando el dato cambia (renovar póliza = fila nueva, registrar servicio, pagar refrendo, `needs_change = 0`).

## Al modificar

- **Tipo de alerta nuevo**: entrada en `ALERT_KINDS` + rama en `build_cda_alerts` (a partir de una vista existente; si el dato no está en ninguna vista, primero exponerlo ahí).
- **Horizonte default**: `ALERT_DAYS_AHEAD` en `MD_CDA.py`.
- **Correo/WhatsApp en vez de in-app**: cambiar `CDANotifications` (el barrido ya entrega `alerts` estructuradas).
- Las fotos **no** se incrustan en el PDF del checklist (siguen las siluetas); si se pide, `checklist_vehicular_pdf` puede tomar `photos[0]` con el mismo mecanismo de firmas desde S3.

## Pendientes

- **[front]** Tile de alertas en el dashboard de CDA (`/alerts` + llamar `/notifications` al abrir) y galería de fotos en el expediente del vehículo.
- **[back]** Foto real en el PDF del checklist (`?photo=1`), si CDA lo pide.
