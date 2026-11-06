# Plan — Guías de la webapp por pantalla (base de conocimiento del asistente)

> Plan nacido de la decisión del usuario del **2026-11-06**: las guías de `knowledge/help/` del repo `telintec_agents` se generan **a partir de las ventanas que tiene el front en producción** (rama `main` de `telintec_webapp`), en **grupos**: un grupo por día mientras se completa el inventario y, después, **por evento** (cada pantalla nueva o modificada trae su guía). Extiende la F3 del asistente ([`asistente_webapp.md`](../asistente_webapp.md), `P-243`) y sigue la regla de ese día: **las guías y el asistente dicen qué puede hacer la persona en cada módulo y cómo; nada de rutas del API, configuraciones ni nombres técnicos**. Formato y reglas de redacción: `knowledge/help/README.md` del repo de agentes.

## Estado

- **Estado:** aprobada, en curso. Hecho: 11 de 15 guías en borrador (`almacen` el 2026-11-06). Abiertos: Fase 1 y Fase 2 (back, `P-243`), Fase 3 (front, `P-256` y `P-257`), paso de las guías del front a producción (usuario, `P-258`).
- **Repo de las guías:** `https://github.com/EdissonTelintec/telintec_agents.git`, carpeta `knowledge/help/`. **Ejemplo de referencia para el front: `almacen.md`**, ajustada a `main` el 2026-11-06 (permisos de Procesamiento SM y pantalla de Reservaciones como en prod). Pasos para el front en la sección "Para el equipo de front" del README de esa carpeta; el usuario le pasa el repo al front **solo como referencia**: el front redacta en su propio repo.
- **Fuente de verdad:** la rama `main` del front (lo que está en prod). Inventario tomado el 2026-11-06: 166 rutas, unas 70 pantallas principales. La rama de trabajo del front (`cotizaciones_sin_contract`, 83 commits adelante) trae pantallas que aún no están en prod: Preventa (`/dashboard/preventa/*`), SGI (`/dashboard/sgi/formatos-iso`), Control de entregas, formato de remisión y movimientos de un control de saldos. Entran a su guía **cuando lleguen a `main`** (Fase 3). `preventa.md` y `sgi.md` ya están en borrador desde esa rama: se quedan cargadas porque el asistente solo las muestra a quien tiene el permiso **(por confirmar por el usuario: si prefiere retirarlas hasta que salgan a prod, basta mover los dos archivos fuera de `knowledge/help/`)**.

## Reglas del plan

1. **Unidad de archivo = módulo del menú; unidad de trabajo = pantalla.** Una guía por módulo (15 archivos, tabla del README de `help/`) y dentro una sección `## <Pantalla> (/ruta)` por pantalla; las subpantallas (`/nuevo`, `/editar`, `/[id]`) van dentro de su sección. No se crean archivos por pantalla: cada archivo suma una línea al índice que va en el prompt de cada turno.
2. **Un grupo por sesión, nunca varias.** Un grupo = un módulo (o medio módulo si pasa de ~8 pantallas). El back lo hace con un solo agente `redactor` (modelo barato); el front, en una sola sesión corta por grupo. El objetivo es que el consumo de tokens sea predecible: nunca "todas las guías" en una sesión.
3. **Contenido:** qué puede hacer la persona en esa pantalla y cómo (botones, pestañas, estados y mensajes con su texto exacto, quién entra por permiso del catálogo). Sin rutas del API, configuraciones, llaves, nombres de componentes ni ids `P-NNN`. Lo no verificado lleva **(por confirmar)** y lo revisa el usuario.
4. **Dónde escribe cada quien (decisión del usuario, 2026-11-06):** el front escribe **solo en su propio repositorio**, en una carpeta dedicada y versionada (p. ej. `guias-asistente/` en la raíz; no dentro de `docs/`, que está en su `.gitignore`), con los mismos nombres de archivo que `knowledge/help/`; **no modifica el repo de agentes ni ningún otro**. El usuario toma esos archivos y actualiza las guías en producción (`knowledge/help/` de `telintec_agents`): copiar, `pytest tests/test_knowledge.py`, `sync_kb.py` si aplica, reiniciar el servicio (`P-258`).
5. **Validación de cada entrega:** en el repo de agentes, `pytest tests/test_knowledge.py` (encabezado, rutas, permisos) y, si el vector store está activo, `python scripts/sync_kb.py`. El servicio carga las guías al arrancar: reiniciarlo tras subirlas.
6. **Por evento (permanente, Fase 3):** todo pendiente del front que cree o modifique una pantalla incluye la sección de esa pantalla en la guía de su módulo, y si cambia la ruta, el `rutas:` del encabezado. Es parte de la definición de "hecho" del pendiente.

## Inventario de pantallas en `main` (2026-11-06) y grupos

Nombres como aparecen en el menú de la webapp; "fuera del menú" = la pantalla existe en prod pero no tiene entrada en el menú (se documenta en una línea o se decide retirarla). Las rutas van sin el prefijo `/dashboard`.

| Grupo | Guía | Pantallas (rutas) | Estado |
|---|---|---|---|
| F1-1 | `administracion` (parte 1) | Catálogo de Clientes (`/administracion/db-management`, `/[id]`, `/nuevo`) · Catálogo Proveedores (`/administracion/catalogo-proveedores`, `/[id]`, `/nuevo`) · Contratos (`/administracion/contratos`, `/nuevo`, `/editar/[id]`) · Control de Gastos Varios (`/administracion/control-gastos-varios`) · Estado de contratos (`/administracion/estado-contratos`) y Estado de cuenta (`/administracion/estado-cuenta`), ambas fuera del menú | pendiente |
| F1-2 | `administracion` (parte 2) | Cobranza Remision (`/administracion/cobranza-remision`, `/nueva`, `/nueva-diseno`, `/editar-diseno/[id]`, `/ver/[id]`, `/adjuntos/[id]`, `/anexos`) · Entregas de SM (`/administracion/entregas-de-sm`) · fuera del menú: Reportes de material (`/administracion/reportes-material`), Remisiones plantilla vieja (`/administracion/remisiones`, `/nueva`, `/editar/[id]`), Licitación cerrada (`/administracion/licitacion-cerrada`), `/administracion/controllerSms` | pendiente |
| F1-3 | `compras` | Solicitudes de OC (`/administracion/purchases/solicitudes`) · Órdenes de Compra (`/administracion/purchases/ordenes`) · `/administracion/purchases/pos` y `/pos/fast-order` (fuera del menú) · Conciliación OC–Almacén (`/administracion/conciliacion-oc-almacen`) · Gestión de Compras (`/administracion/gestion-compras`, `/nueva`, `/[idPm]/editar`) · Pedido a proveedor (`/administracion/pedido-proveedor`, fuera del menú) · Compras → Solicitudes de compra (`/purchases/applications`, `/nuevo`, `/editar/[id]`) · Operaciones → Aprobar S.C. (`/operations/purchases/approve`) | pendiente |
| F1-4 | `cobranza` | Cobranza → Control de saldos (`/administracion/control-saldos/cobranza`: `/controles`, `/nuevo`, `/editar/[id]`, `/control/[id]`, `/control/[id]/editar`, `/control/[id]/remisiones`, `/remisiones`) · `/administracion/control-saldos` (vista anterior, fuera del menú) | pendiente |
| F1-5 | `inicio` | Iniciar sesión (`/login`) · Inicio (`/dashboard`: menú por permisos, notificaciones, cierre de sesión, y el botón del asistente cuando el front entregue `P-244`) | pendiente |
| F2-1 | `sm` | Solicitudes · Solicitudes Urgentes · Control de SM (`/edit/[id]`, `/pdf/[id]`) · Entregas de SM · Operaciones → Aprobar SM-Herramientas (`/operations/sm-approve`) · fuera del menú: `/sm/aprobar`, `/sm/controlador_sms` | borrador; falta `/sm/aprobar` |
| F2-2 | `rrhh` | Dashboard · Personal (`/nuevo`, `/editar/[id]`) · Detalles Personal · Check-ins (`/nuevo`) · Nómina · Examenes Medicos · Administrar vacaciones · Encuestas (`/nuevo`, `/clima`, `/resultados/[id]`, `/eva360`, `/modelos`) · fuera del menú: `/rrhh/fichajes` (oculto), `/rrhh/payroll` y `/payroll-v2` (redirigen a Nómina), `/rrhh/vacaciones-info` | borrador; cotejar las 4 fuera del menú |
| F2-3 | `control_activos` | Base de Datos de Activos · Control de Estado de Vehículos (`/nuevo`, `/editar/[id]`, llantas, multas, pólizas, compras y servicios por vehículo) · Checklist Vehicular y Aprobar checklist vehicular (bajo `/checklist` y, duplicadas, bajo `/control-activos`) | borrador |
| F2-4 | `lideres` | Cotización de Actividad (`/nueva`, `/[id]`, `/[id]/editar`) · Reporte de Actividad (`/nueva`, `/[id]`, `/[id]/editar`; **sigue en prod**, la rama de trabajo la retira por `P-217`) · Tabla de remitos/Control de Reportes (`/nueva`, `/[id]/editar`, `/[id]/administracion`) · `/lideres/control-reportes/[id]` · `/administracion/control-reportes` (`/[id]`, `/visual`; oculto del menú) | borrador; cotejar Reporte de Actividad |
| F2-5 | `comun` | Check-in · Tareas (`/comun/encuestas`) · Mi nómina · `/comun/vacaciones` (fuera del menú) | borrador; cotejar vacaciones |
| F2-6 | `vales_y_epp` | Vales: Vales de EPP (`/nuevo`, `/editar/[id]`), Vales de herramientas (`/nuevoTool`, `/editarTool/[id]`), Herramientas prestadas, Aprobar vales · Almacén EPP: Inventario EPP, Aprobar vales · Operaciones → Aprobar Vales | borrador |
| F2-7 | `operaciones` + `usuarios_y_cargos` | Confirmacion de horas extra (`/confirmaciones`) · Cargos (`/roles`) · Usuarios del Sistema (`/usuarios-sistema`) · Bitácoras (`/bitacoras`, oculta del menú) | borrador |
| F2-8 | `almacen` | Inventario · Entradas · Salidas · Procesamiento SM (`/firmas/[id]`) · Entregas de SM · Despachar vales · Reservaciones · Proveedores · Traslados a sedes · Sucursal (3) · Inventario de Almacén · fuera del menú: `/almacen/movimientos`, `/almacen/controllerSmsAl` | hecho 2026-11-06 y ajustada a `main`; **ejemplo de referencia**; falta `controllerSmsAl` |
| F3 | `preventa`, `sgi` y pantallas nuevas | Preventa (`/preventa/cotizaciones`, `/cotizaciones-cisco`, `/licitaciones`), SGI (`/sgi/formatos-iso`), Control de entregas, formato de remisión, movimientos de control de saldos: hoy solo en la rama de trabajo; en `main` Preventa es `/administracion/cotizaciones` | por evento, al salir a prod |

## Fases

### Fase 1 — back: las 4 guías que faltan (un grupo por día, `P-243`)

Orden F1-1 → F1-5 (Administración en dos días por su tamaño). Cada día: brief al agente `redactor` con el README de `help/`, `sm.md` como ejemplo de estilo, `nav.ts` y `route-permissions.ts` de `main`, los componentes del módulo y las docs del API solo para reglas de negocio; luego `pytest tests/test_knowledge.py`, revisión de jerga y reporte al usuario con las marcas "(por confirmar)". Igual que `almacen` el 2026-11-06.

### Fase 2 — back: barrido de las 11 en borrador contra `main` (un grupo por día, `P-243`)

Las 11 se redactaron desde la rama de trabajo del front. Orden F2-1 → F2-8: agregar las pantallas que están en prod y no en la guía (columna "Estado" de la tabla), marcar como "(aún no en producción)" lo que solo está en la rama, y quitar cualquier detalle técnico que haya quedado. El redactor solo lee código; lo que exige abrir la pantalla queda "(por confirmar)" y lo cierra el front en `P-257`.

### Fase 3 — front: por pantalla y por evento (`P-256`, `P-257`)

- **Barrido inicial (`P-257`, una vez):** el front abre cada pantalla en test, coteja la sección de su guía (nombres de botones, pestañas, estados, mensajes, quién entra), corrige y resuelve las marcas "(por confirmar)" que le toquen. **Un grupo por sesión**, en el orden de la tabla (F2-1 → F2-8 y luego las de Fase 1 conforme se entreguen); nunca varias guías en una sesión.
- **Permanente (`P-256`):** cada pendiente que cree o modifique una pantalla actualiza la sección de esa pantalla (y el `rutas:` si cambia la dirección) en el mismo pendiente, antes de reportarlo como hecho. Pantalla nueva en un módulo que no tiene guía → se crea el archivo con el encabezado del README. Las pantallas que hoy solo están en su rama (Preventa, SGI, Control de entregas, formato de remisión) entran así cuando salgan a `main`.
- **Entrega:** el `.md` en la carpeta dedicada de su propio repo y una línea en su reporte de avance con el grupo cubierto. El usuario copia los archivos a `knowledge/help/`, corre las pruebas, sincroniza el vector store si está activo y reinicia el servicio (`P-258`).

## Riesgos

- **Rama de trabajo vs prod:** una guía escrita desde la rama describe botones que el usuario de prod no ve. Por eso la fuente es `main` y lo demás espera a su despliegue.
- **Consumo de tokens:** el 2026-11-05 cuatro agentes en paralelo gastaron el 34 % del uso de la cuenta. La regla "un grupo por sesión" aplica al back y al front.
- **Guías que envejecen:** sin la regla por evento (`P-256`), cada cambio de pantalla deja la guía mintiendo. El asistente no distingue una guía vieja de una buena.

## Al modificar

- Nueva pantalla o cambio de ruta → sección en la guía del módulo y `rutas:` del encabezado; después `pytest tests/test_knowledge.py` y `sync_kb.py` si aplica.
- Nuevo módulo del menú → archivo nuevo en `knowledge/help/` + fila en la tabla del README de esa carpeta + fila en la tabla de este plan.
- Cambios de reglas de redacción → `knowledge/help/README.md` (es lo que lee el redactor y el front) y, si tocan al asistente, `build_instructions` en `agents_service/agents/assistant.py`.
- Al cerrar una fase → actualizar "Estado" de este plan y `pendientes.md`; cuando todo esté por evento, este plan se archiva en `planes/archivo/`.
