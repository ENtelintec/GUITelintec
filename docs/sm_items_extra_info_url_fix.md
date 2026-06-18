# Fix: pérdida de `url` / `is_tool` en `extra_info` de ítems de SM

Al **despachar** una SM (`dispatch_sm`) se borraba el campo `url` (y se reseteaba
`is_tool`) que vive dentro del `extra_info` de cada ítem. La causa estaba en
[`update_items_sm`](../templates/controllers/material_request/sm_controller.py),
que leía `url`/`is_tool` desde el **primer nivel** del ítem — clave que no existe
cuando los ítems vienen crudos de `get_sm_by_id`.

## Dónde vive el `url`

El `url` de un ítem se guarda **dentro** de `smi.extra_info` en la BD, no como
columna propia:

```
sm_items.extra_info = { "url": "...", "is_tool": 0, "approve_required": 0, ... }
```

En la pantalla de edición, [`extract_extra_info_sm_item`](../templates/resources/midleware/MD_SM.py)
**sube** ese valor a primer nivel para que el front lo pueda editar:

```python
item["url"] = extra_info.get("url", "")   # extra_info["url"] -> item["url"]
```

Por eso, cuando el front guarda, el ítem **sí** trae `item["url"]` de primer
nivel.

## La causa del bug

`update_items_sm` reconstruía el `extra_info` a guardar leyendo del **primer
nivel** del ítem:

```python
extra_info = item.get("extra_info", {})
is_tool = item.get("is_tool", 0)          # <- primer nivel
extra_info["is_tool"] = is_tool ...
extra_info["url"] = item.get("url", "")   # <- primer nivel: si no existe, queda ""
```

Esto funciona para el **flujo de edición** (el front manda `url`/`is_tool` en
primer nivel), pero **rompe el flujo de despacho**:

`dispatch_sm` toma los ítems directo de `get_sm_by_id`
(`products_sm = json.loads(result[10])`) **sin** pasar por
`extract_extra_info_sm_item`. El [`JSON_OBJECT` de la query](../templates/controllers/material_request/sm_controller.py)
incluye la clave `extra_info` (con el `url` adentro) pero **no** una clave `url`
ni `is_tool` de primer nivel. Resultado:

```
item.get("url", "")     -> ""   (no hay primer nivel)  => pisa el url real con ""
item.get("is_tool", 0)  -> 0    (no hay primer nivel)  => resetea is_tool a 0
```

### Flujo del bug

```
dispatch_sm  (MD_SM.py:499)
  → get_sm_by_id            # items con url SOLO dentro de item["extra_info"]
  → update_items_sm(...)    # lee item["url"] (no existe) -> "" -> sobre-escribe
  → update_history_status_sm  # persiste extra_info con url = ""   ❌
```

## El fix

[`sm_controller.py`](../templates/controllers/material_request/sm_controller.py),
en `update_items_sm`: hacer *fallback* al valor que ya está dentro de
`extra_info` cuando la clave de primer nivel **no existe**.

```python
extra_info = item.get("extra_info") or {}
is_tool = item.get("is_tool", extra_info.get("is_tool", 0))
extra_info["is_tool"] = is_tool if is_tool is not None else 0
...
extra_info["url"] = item.get("url", extra_info.get("url", ""))
```

Se usa el **default-por-clave-ausente** de `dict.get`, no `or`, a propósito:

- **Flujo de edición**: el front manda `url` de primer nivel (incluso `""` para
  limpiarlo a propósito) → la clave existe → se respeta tal cual. Comportamiento
  idéntico al anterior; sigues pudiendo borrar el `url`.
- **Flujo de despacho**: no hay `url` de primer nivel → la clave falta → cae al
  `extra_info.get("url", "")` existente → **se preserva** el `url` real.

También se cambió `item.get("extra_info", {})` por `item.get("extra_info") or {}`
para tolerar `extra_info = None` (ahora que dependemos de `.get()` sobre él).

## Impacto en los callers

Tres callers de `update_items_sm`; el fix es seguro para todos:

| Caller | Origen de ítems | `url` en primer nivel | Efecto |
|---|---|---|---|
| `dispatch_sm` ([MD_SM.py:664](../templates/resources/midleware/MD_SM.py)) | crudos de `get_sm_by_id` | No | **Arreglado** |
| `update_sm_from_api` ([MD_SM.py:1208](../templates/resources/midleware/MD_SM.py)) | `data["items"]` del front | Sí | Sin cambio |
| `update_items_sm_from_api` ([MD_SM.py:1426](../templates/resources/midleware/MD_SM.py)) | `data["items"]` crudo | Depende del cliente | Solo mejora (preserva) |

Ningún caller dependía del comportamiento viejo de resetear `url` a `""`.

## Al modificar

- Si agregas más campos que se "suben" a primer nivel en
  `extract_extra_info_sm_item`, aplica el mismo patrón de *fallback* en
  `update_items_sm` para que no se pierdan en el flujo de despacho.
- El `url` es la fuente de verdad **dentro** de `extra_info`; el `item["url"]`
  de primer nivel es solo una conveniencia para el front.
