# Pool de conexiones MySQL en `execute_sql`

> Grill 2026-10-12 (junto con [`almacen_kardex_ventana.md`](almacen_kardex_ventana.md)). `execute_sql` y `execute_sql_multiple` abrían y cerraban una conexión `mysql.connector` **por consulta**: cada endpoint con 3 o 4 consultas pagaba 3 o 4 handshakes TCP + autenticación. Ahora toman la conexión de un pool. Cambio transversal en un solo archivo; **ningún controlador ni endpoint cambia** y el contrato `(flag, error, result)` es el mismo.

## Qué cambió (1 capa)

| Capa | Archivo | Cambio |
|---|---|---|
| **Driver** | [`connection.py`](../templates/database/connection.py) | `_credentials(data_token)` (misma lógica `is_tester` → BD de test), `_get_pool(host, user, pass)` (un `MySQLConnectionPool` por destino y por proceso, creado perezosamente bajo lock), `_connect(data_token)` (pool → conexión; `PoolError` → conexión directa como antes), `_log_db` (log propio en `files/logs/db_log_<fecha>.txt`, porque `Functions_Files` importa controladores y haría ciclo). `execute_sql*` solo cambian `mysql.connector.connect(...)` por `_connect(data_token)`; el `close()` del `finally` devuelve la conexión al pool (o cierra la directa). |

### Reglas

- **`POOL_SIZE = 4` por pool y por proceso.** Dimensionado para el WSGI de prod (3 workers × 1 thread): 1 request + hilos de daemons + margen. Peor caso 3 procesos × 2 pools × 4 = 24 conexiones. Si cambian workers/threads, revisar (`P-130`); tope del conector: 32.
- **Dos pools**: BD normal y BD de test (`data_token["is_tester"]`), por clave `usuario@host`. El de test solo nace en el proceso donde un tester haga su primera consulta.
- **Por proceso, nunca al importar**: `_pools` se vacía si cambia el `os.getpid()` (un pool heredado por `fork` compartiría sockets entre workers).
- **`pool_reset_session=True`**: al devolver la conexión el conector hace rollback y limpia la sesión; una transacción implícita de un `SELECT` (autocommit apagado) no deja un snapshot viejo al siguiente request. Las consultas del repo califican todas las tablas con `sql_telintec.`, así que no hay `USE` que se filtre.
- **Pool agotado no espera, falla** (`PoolError` inmediato). `_connect` entonces abre una conexión directa (comportamiento histórico) y anota `pool: agotado (...)` en el log de `db`. Si el pool no se puede crear (BD caída) también va directa y el error sale por el mismo `(False, str(e), [])` de siempre.
- **Conexiones muertas**: `get_connection()` verifica `is_connected()` y reconecta; el `wait_timeout` de MySQL no produce "server has gone away".
- `.env` sigue leyéndose una vez al importar: cambiar credenciales exige reiniciar (igual que antes).

## Verificación

Dev (2026-10-12, BD local): `SELECT 1` en caliente **0.4–0.6 ms** por consulta contra **7.2 ms** con conexión directa (en prod, con la BD remota, el handshake pesa más). Crear el pool (4 conexiones) cuesta una vez ≈ 150 ms por proceso. Tomadas las 4 conexiones, la quinta consulta responde por la ruta directa y queda la línea en `files/logs/db_log_2026-10-12.txt`. Batería completa del kardex (31 checks, lecturas + descargas) y `pyrefly check` sin errores nuevos corriendo sobre el pool.

## Al modificar

- No llamar `mysql.connector.connect` desde fuera de `connection.py`; cualquier consulta nueva pasa por `execute_sql` y hereda el pool y el cambio de BD por `is_tester`.
- Si un endpoint necesita una transacción de varias consultas, hoy no existe: cada `execute_sql` toma y devuelve su conexión (y el reset hace rollback). Habría que añadir una función que preste la misma conexión a varias consultas.
- Si aparecen líneas `pool: agotado` seguidas en el log, subir `POOL_SIZE` o revisar hilos (daemons) que retengan conexiones.
