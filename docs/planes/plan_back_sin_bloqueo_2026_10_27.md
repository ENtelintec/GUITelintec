# Plan — pendientes de back sin bloqueo (grill del 2026-10-27)

> Estado: propuesta (grill cerrado el 2026-10-27: todas las ramas decididas). Decisiones del grill del **2026-10-27** sobre los pendientes de back que no esperan a nadie: `P-177`, `P-017`, `P-016`, `P-115`, `P-114`, `P-128`, `P-129`, `P-178` y `P-139`. **Nada está implementado aún.** Cada ítem produce su doc en `docs/` (con "Contrato mínimo para el front" si toca un endpoint) y cierra su `P-NNN` en [`pendientes.md`](../pendientes.md). Términos del dominio en [`GLOSSARY.md`](../../GLOSSARY.md).

## Avance

- **2026-10-27 — `P-177` hecho** (44/44 nómina contra dev, 24/24 lógica de rutas y borrado, regresión en verde) → [`s3_rutas_por_entorno.md`](../s3_rutas_por_entorno.md).
- **2026-10-27 — `P-017` hecho** (13/13 contra dev, páginas revisadas) → [`eva360_pdf.md`](../eva360_pdf.md).
- **2026-10-27 — `P-016` hecho** (16/16 contra dev, páginas revisadas) → [`norma035_pdf.md`](../norma035_pdf.md).
- **2026-10-27 — `P-115` hecho** (41/41 contra dev) → [`po_match_cantidades.md`](../po_match_cantidades.md). La revisión de `insert_purchase_order_item_from_applications` encontró el error en `update_po_application_api`, que guardaba la partida nueva de una solicitud con `purchase_id`; quedó arreglado. Front en `P-183`. Sigue `P-114`.
- **2026-10-27 — `P-114` hecho** (PDFs renderizados y revisados; descarga por HTTP; `tester_iso_formats` 48/48) → [`po_pdf_cuadricula.md`](../po_pdf_cuadricula.md). Un segundo grill amplió la decisión de abajo: encabezado con el formato propio **FO-COM-04** (id 16, SQL en `P-184`), columna UM del producto ligado, duración y moneda condicionales, totales por moneda, marca de cancelada y fecha de emisión desde el `history`. De paso, la descarga pide `administracion` o `compras` (`P-185`; antes solo descargaban los administradores). Sigue `P-128`.
- **2026-10-28 — `P-128` hecho** (54/54 contra dev; la huella de la ventana por defecto cuesta ~5 ms) → [`almacen_kardex_etag.md`](../almacen_kardex_etag.md). Sigue `P-129`.

## Orden

1. `P-177`: es el único riesgo activo sobre datos (una prueba en dev o test puede sobrescribir un recibo real de prod).
2. `P-017` → `P-016` → `P-115` → `P-114` (orden del [plan de acción](plan_accion_2026_10.md)).
3. `P-128` → `P-129`.
4. `P-178` → `P-139`: Docker depende de la versión de Python y los dos piden ventana en prod.

## `P-177` — rutas S3 separadas por entorno

Hechos (2026-10-27): la BD guarda la **ruta S3 completa** de cada archivo (nómina: `files_data[año][mes][quincena] = {pdf, xml}`), y descarga, borrado, reemplazo y correo leen esa ruta; no la reconstruyen. Cambiar la ruta de las subidas nuevas no rompe lo que ya está en S3. No hay bucket por entorno (`S3_RH_BUCKET`, `S3_ADMIN_BUCKET`, `S3_CH_BUCKET` son los mismos en los 3).

Decisiones:

- **Ruta de nómina:** `payroll/<entorno>/<año>/<mes>/<emp_id>/<quincena>/<archivo>`. `<entorno>` = `test` si el token es de tester; si no, `environment` de [`constants.py`](../../static/constants.py) (`dev` | `prod`). Mismo criterio que [`MD_BalanceAlerts.py`](../../templates/resources/midleware/MD_BalanceAlerts.py). **Prod también lleva prefijo explícito.**
- **Quincena en la ruta**, limpia con `secure_filename` (es texto libre del form). Quita el choque Q1/Q2 con el mismo nombre de archivo.
- **Alcance: todos los módulos que suben a S3**, con una función compartida que da el prefijo de entorno, y solo para subidas nuevas: nómina, fotos de check-in, fotos de CDA, anexos de remisión, anexos de SM y vales. Antes de tocar cada módulo se verifica que ninguno busque archivos listando S3 en vez de leer la ruta guardada.
- **SM gana su id en la ruta**: hoy es `smData/<Y/m/d>/<archivo>`, así que dos SMs del mismo día con un anexo del mismo nombre se sobrescriben, incluso en prod.
- **Reemplazo por nombre, no por ruta** (CDA, remisiones, vales): "mismo archivo" = mismo nombre dentro del mismo registro; la entrada vieja sale de la lista aunque su ruta sea la antigua (así se siguen corrigiendo firmas). Nómina ya reemplaza por quincena y tipo.
- **Quién borra qué objeto**: cada entorno borra solo los de su prefijo; los de ruta vieja (sin entorno) solo los borra **prod**; un prefijo ajeno, nunca. Dev y test quitan la entrada de su lista y dejan el objeto (lo reporta la conciliación). Aplica a reemplazos y borrados de nómina, CDA, remisiones y vales.
- **Conciliación** (`scripts_db_handle/nomina_s3_conciliacion.py`, local): cruza `payroll/dev/` contra dev, `payroll/test/` contra test y `payroll/prod/` contra prod; los objetos viejos sin prefijo, contra las 3 BDs.

## `P-017` — PDF del proceso eva 360

- **Lector: solo RH**, con nombres de los evaluadores. Una versión para el evaluado se deriva **solo si RH la pide** (no es pendiente).
- **Endpoint:** `GET /GUI/api/v1/rrhh/eva360/<evaluation_id>/pdf`, permiso `rrhh`. 200 = PDF; 404 proceso inexistente, 400 sin rúbrica o con 0 perspectivas respondidas (envelope JSON). Mismo cálculo que `/result`.
- **Proceso abierto:** marca "PRELIMINAR — X de Y perspectivas respondidas". **Cerrado** por RH aunque falte alguna: sin marca, con "Cerrado — X de Y respondidas".
- **Contenido:** datos del proceso (evaluado, puesto, fecha límite, estado, X de Y); evaluadores (rol, nombre, puesto, respondió); resultado general /100 y por perspectiva (/100 y crudo /45); radar de las 9 competencias (escala 1–5, una línea por perspectiva respondida, color y trazo distintos por rol para impresión en B/N); tabla competencia × rol con promedio. **Sin** la distribución de frecuencias.
- **Nombre y puesto del evaluador:** del catálogo de empleados según el empleado asignado; lo tecleado en la pregunta 0 del cuestionario se ignora.
- **Pregunta 3 mal etiquetada** ("Nivel de Puesto del Evaluado", con opciones de rol del evaluador): el PDF la ignora; se anota en el doc para que RH la corrija o la quite al editar el modelo. No se toca el modelo en BD.
- Etiquetas de rol: Autoevaluación, Jefe Inmediato, Colega, Subordinado (las del cuestionario).

## `P-016` — PDF de Norma 035 desde `evaluation`

Hechos (2026-10-27): `_legacy_shape_from_evaluation` corre para todo tipo con rúbrica, y `display_result`/`display_recommendations` (los que leen `results`/`recommendations`) también los usan clima (3), la perspectiva de eva 360 (4) y salida (0, con los valores por defecto). El PDF actual imprime el cuerpo en Times, la fecha en lugar del entrevistador, una etiqueta en inglés y siempre las acciones de la primera categoría. El front no lee `results` ni `recommendations` (solo llama a `POST /rrhh/download/quizz/report`).

Decisiones:

- **Norma 035 (tipos 1 y 2): PDF nuevo dedicado** que lee `evaluation`. Página 1: datos del trabajador (con entrevistador), resultado total con nivel y sus acciones. Desglose categoría → dominio → dimensión con puntaje y nivel (las dimensiones no tienen nivel) y las acciones de **cada** categoría según su nivel. Anexo: respuestas en tabla Pregunta | Respuesta (evidencia), en vez de la matriz de X/O.
- **Clima (3), perspectiva de eva 360 (4) y salida (0) pasan al PDF genérico** ([`QuizzGenericReport.py`](../../templates/forms/QuizzGenericReport.py)); salida, como tabla Pregunta | Respuesta.
- **Se borra:** el shim, sus valores por defecto, `display_result`/`display_recommendations`, los generadores viejos de esos tipos y el Excel `report_norm35.xlsx` (`create_report_encuesta`, sin llamadas).
- **`results` y `recommendations` se dejan de escribir** en `data_raw`; las encuestas que ya los tienen se quedan así, sin DML.

## `P-114` — PDFs legacy a cuadrícula

Hechos (2026-10-27): solo la **orden de compra** (`FilePoPDF`, `GET /admin/collections/purchase/download/pdf/<po_id>`) tiene endpoint. Vale EPP/herramienta (`FileVoucherPDF`), cotización (`QuotationForm`) y las dos devoluciones (`ReturnMaterials`, `ReturnMaterialsForm`/`MaterialsRequest`) no tienen quién las llame.

Decisiones:

- **Solo la orden de compra** pasa a cuadrícula, con el mismo contenido y estos arreglos: el folio impreso (hoy lee `"Folio"` y la llave es `"folio"`), encabezado y títulos de columna en cada página, subtotal/IVA/total en la cuadrícula. Sin campos nuevos ni firmas.
- **Se borran los cuatro generadores sin uso** y los helpers que solo ellos usan. Un PDF de vale o de devolución, si SGI o almacén lo piden, se hace nuevo sobre la cuadrícula.

## `P-115` — conciliación de OC por cantidades

Hechos (2026-10-27): `GET /admin/collections/purchase/movements/match` casa la referencia de la entrada con el folio de la OC (o su folio de proveedor) y nunca suma cantidades. Las partidas de OC traen `extra_info.id_inventory` = id de `products_amc` (0 o -1 = sin ligar) y no traen unidad de medida. Las entradas se editan y se borran en duro; la consulta de entradas lee todo el historial en cada llamada y el filtro de fechas de las OCs se aplica en Python.

Decisiones:

- **Solo las coincidencias exactas suman.** Por partida ligada: `pendiente` (0), `parcial`, `completa` o `excedente`. Las coincidencias "parciales" (el folio contenido en la referencia) se muestran, pero no suman.
- **Partidas sin ligar → `sin_ligar`**, sin adivinar por número de parte ni descripción.
- **Mismo producto en varias partidas**: lo recibido se reparte en orden; el sobrante final deja `excedente` la última.
- **Una entrada que casa con dos OCs** cuenta una vez, para la OC con la que casó por folio propio; si aun así hay empate, no suma y sale marcada como ambigua.
- **Estado de recepción calculado** (`sin_entradas` | `parcial` | `completa` | `excedente`); el estado "recibido" de la OC lo sigue poniendo administración a mano. El endpoint sigue siendo de solo lectura.
- **Consulta acotada**: entradas desde la fecha de la OC más vieja de la respuesta; el filtro de fechas de las OCs pasa al SQL.
- Antes de programar, revisar en solo lectura `insert_purchase_order_item_from_applications` (inserta en `order_id`; los demás usan `purchase_id`).

## `P-128` — ETag del kardex

- **ETag débil (`W/`) a partir de una huella del cuerpo** + `Cache-Control: private, no-cache`; sin DDL, siempre exacto. Sigue costando la consulta; un refresco sin cambios responde 304 sin cuerpo.
- **El front no cambia**: el navegador manda solo `If-None-Match` y entrega a JS el 200 guardado.
- Aplica a `GET /almacen/kardex`, `GET /almacen/kardex/epp` y `GET /sucursal/movements/<type_m>`.

## `P-129` — auditoría de lecturas completas

Hechos (2026-10-27): los "49" son todos los SELECT de `controllers/product`; sin `WHERE` ni `LIMIT` hay 7, y otro grupo lleva un `WHERE` que no acota (`LIKE '%'`, todo el historial). Seis funciones con SELECT no tienen quién las llame.

Decisiones:

- **Entregables**: doc con la auditoría completa y los arreglos sin cambio de contrato: `get_last_sku` lee una fila en vez de la tabla; las entradas de la conciliación se acotan (con `P-115`); se borran las 6 funciones sin llamadas y las dos auxiliares sin llamadas (`Aux_Inventory.fetch_all_movements`, `Functions_AuxFiles.get_all_sm_products`).
- **Pendientes nuevos, con su ítem de front**, para los listados que cambiarían contrato: reservas con todo el historial, inventario con `LIKE '%'`, consolidado, productos de SM.
- **No se tocan** las funciones que solo usa el chatbot (archivos de OpenAI congelados).

## `P-178` — Python de prod

- **Destino: `python3.14` de `dnf`** ([`dependencias_python.md`](../dependencias_python.md)).
- **Paquetes:** los que no tienen rueda para 3.14 (numpy 2, Pillow, MarkupSafe, cffi, pydantic) suben a su última versión; **pandas a la última 2.x** y **PyMuPDF a la última 1.x** (sin `onnxruntime`, `import fitz` se queda); el resto sin tocar salvo lo que arrastre la instalación. pandas 3 y PyMuPDF 2, como cambios aparte. Verificar las ruedas antes de fijar.
- **Dev:** instalar 3.14 con el gestor de Python de la máquina (`py install 3.14`) y recrear `.venv`; el `pyrefly.toml` local sube a 3.14 solo cuando prod esté en 3.14.

## `P-139` — Docker

- **Congelado hasta `P-180`**: `envg2` y el 3.14 de `dnf` resuelven hasta 2029-06 lo que motivaba Docker (Python compilado sin parches, versión libre). Se retoma al elegir el SO sucesor. Lo desactualizado del plan queda anotado en [`despliegue_docker.md`](../despliegue_docker.md).
