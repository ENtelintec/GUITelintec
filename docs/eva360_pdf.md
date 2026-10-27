# PDF del proceso eva 360 (`P-017`)

> 2026-10-27. Decisiones del grill del mismo día → [`plan_back_sin_bloqueo_2026_10_27.md`](planes/plan_back_sin_bloqueo_2026_10_27.md). Sin DDL. Endpoint nuevo de solo lectura sobre el proceso de [`eva360_evaluation.md`](eva360_evaluation.md).

`GET /rrhh/eva360/<evaluation_id>/pdf` arma el reporte del **proceso completo** (no el cuestionario de una perspectiva). Lo lee **RH**: lleva los nombres de los evaluadores. Una versión para entregar al evaluado se hará solo si RH la pide; no es pendiente.

## Qué trae

Una hoja con el proceso cerrado; con el proceso abierto, la tabla de competencias pasa a la segunda hoja. El formato es el de la casa: cuadrícula celeste, Helvetica, encabezado FO-GRH-08 y pie con página y `Eva 360 <8 caracteres del id>`.

1. **Aviso** "PRELIMINAR — X de Y perspectivas respondidas", solo mientras el proceso esté **abierto**. Cerrado por RH (aunque falte alguna) no lleva aviso.
2. **Datos del proceso:** evaluado, puesto, fecha límite, estado (Abierto (preliminar) | Cerrado), X de Y respondidas, fecha de emisión, id del proceso y resultado general /100.
3. **Evaluadores y resultado por perspectiva:**
   - Columnas: rol, evaluador, puesto, respondió (Sí | Pendiente), puntaje /100 y crudo /45.
   - Nombre y puesto salen del **catálogo de empleados** según el empleado asignado; lo tecleado en la pregunta 0 del cuestionario se ignora.
   - Al pie, el resultado general: promedio de las respondidas, igual que `/result`.
4. **Radar** de las 9 competencias:
   - Escala fija 1 a 5, con anillos.
   - Una línea por perspectiva respondida, cada rol con color, trazo y marcador distintos (sólido/círculo, guiones/cuadro, puntos/triángulo, guion-punto/rombo), para que se lea impreso en blanco y negro.
   - Leyenda a la derecha.
5. **Competencias por perspectiva:** competencia × rol (valores 1–5; "-" = pendiente) y promedio de las respondidas.

Etiquetas de rol: Autoevaluación, Jefe Inmediato, Colega, Subordinado (las del cuestionario). Un parcial (menos de 9 competencias) cuenta como pendiente, igual que en `/result`. Sin la distribución de frecuencias: con 4 evaluadores como máximo, repite la tabla.

**Pregunta 3 del cuestionario mal etiquetada:** dice "Nivel de Puesto del Evaluado", pero sus opciones (Autoevaluación, Jefe Inmediato, Colega, Subordinado) son el rol de quien evalúa, que el proceso ya asigna. El PDF la ignora. Cuando RH edite el modelo de encuesta tipo 4, conviene corregir la etiqueta o quitar la pregunta. El modelo en BD no se tocó.

## Capas tocadas

| Capa | Archivo | Cambio |
|---|---|---|
| HTTP | [`rs_RRHH.py`](../templates/resources/rs_RRHH.py) | `GET /eva360/<evaluation_id>/pdf` (permiso `rrhh`), `send_file` en 200 |
| Midleware | [`MD_Eva360.py`](../templates/resources/midleware/MD_Eva360.py) | `_build_result` (el agregado, compartido con `get_eva360_result`), `download_eva360_pdf`, `_employees_brief` |
| Controller | [`employees_controller.py`](../templates/controllers/employees/employees_controller.py) | `get_employees_name_puesto(ids)`: nombre, apellidos y puesto por lista de ids |
| PDF (nuevo) | [`Eva360ProcessReport.py`](../templates/forms/Eva360ProcessReport.py) | `FileEva360ProcessPDF(dict_data)`: helpers `_e3_*`, radar dibujado a mano (el `SpiderChart` de reportlab escala contra el máximo, no 1–5) |

El generador viejo [`Eva360.py`](../templates/forms/Eva360.py) (cuestionario de una perspectiva) sigue en `POST /rrhh/download/quizz/report` hasta `P-016`, que lo pasa al PDF genérico.

## Contrato mínimo para el front

**Auth:** header `Authorization` con el **JWT crudo (NO `Bearer <token>`)**. Departamento `rrhh`.
**Base:** `/GUI/api/v1/rrhh`.

### `GET /eva360/<evaluation_id>/pdf`

Sin body ni query. `evaluation_id` es el que devuelve `POST /eva360`.

| Status | Content-Type | Cuerpo |
|---|---|---|
| **200** | `application/pdf` | blob; `Content-Disposition: attachment; filename=eva360_<evaluado>_<AAAAMMDD>.pdf` |
| **404** | JSON | `{"data": null, "msg": "Proceso eva 360 <id> no encontrado", "error": null}` |
| **400** | JSON | 0 perspectivas respondidas: `{"data": null, "msg": "El proceso eva 360 <id> no tiene perspectivas respondidas; no hay nada que reportar", "error": null}` · sin rúbrica: `"msg": "No hay rubrica para eva 360 (files/rubrics/4.json)"` |
| **401** | JSON | `{"error": "No autorizado. Token invalido"}` |

**Gotchas:**
- Pedirlo con `responseType: "blob"` y decidir por status: 200 = PDF; 4xx = leer el blob como texto y parsear el JSON (`msg`).
- Se puede descargar con el proceso abierto. Sale marcado PRELIMINAR hasta que RH lo cierre con `PUT /eva360/<id>/complete`.
- El botón conviene deshabilitarlo con 0 perspectivas respondidas: `answered` de `GET /eva360/<id>/result` o los `raters[].answered` del detalle. Si no, el back responde 400.

## Verificación

`Tests/tester_eva360_pdf.py` (gitignored) contra la BD dev, **13/13**. El tester:
1. Crea un proceso real de 4 roles con empleados activos, con las notificaciones simuladas.
2. Pide el PDF por la ruta con `app.test_client()` y comprueba:
   - 404 si el proceso no existe; 400 con 0 respondidas.
   - Abierto con 3 de 4 (el subordinado contestó 8 de 9): 200 PDF adjunto con PRELIMINAR, las 4 etiquetas de rol, "Pendiente" y el general igual al de `/result`.
   - Cerrado con 4 de 4: sin PRELIMINAR y en una hoja.
3. Borra las tasks al final.

Las páginas se revisaron renderizadas (PyMuPDF a PNG). `pyrefly check --python-version 3.11`: 0 errores en los archivos tocados.

## Al modificar

- **Cambia el agregado** (`evaluate_eva360`): el PDF y `/result` comparten `_build_result`, así que no hay que duplicar el cálculo.
- **Rol nuevo:** agregarlo a `EVA360_ROLES` (midleware) y a `E3_ROLES` (PDF), con etiqueta, color, trazo y marcador propios.
- **Más competencias en la rúbrica:** el radar se ajusta solo (un rayo por competencia); con muchas más de 9 las etiquetas se amontonan.
- **Versión para el evaluado** (si RH la pide): otro generador o un flag que quite la columna de evaluador y el puesto; el lector de este es RH.
