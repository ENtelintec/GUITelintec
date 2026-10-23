# Despliegue del API con Docker en el servidor de prod

> Grill 2026-10-15. **Estado: propuesta** (solo plan; los archivos se escriben al aprobar, `P-139`). Pregunta de origen: "¿cómo uso Docker para desplegar el proyecto en otros sistemas?". El destino acordado es **únicamente el servidor Linux de prod**, donde hoy el API corre con **nginx (host) + gunicorn (systemd, 1 master, 3 workers sync, 1 thread)** contra la BD de AWS. Docker reemplaza el servicio de gunicorn; nginx, los certificados TLS y la BD no se tocan.

## Lo que el repo ya fija (no fue decisión)

- No existe nada de Docker (ni `Dockerfile`, ni compose, ni `.dockerignore`).
- [`wsgi.py`](../wsgi.py) expone `app`; en prod lo sirve gunicorn, así que la imagen **no** usa el `app.run(debug=True)` de ese archivo.
- [`constants.py`](../static/constants.py) decide por la constante `environment` qué `.env` y qué `domain.pem` leer (`../` en prod) y qué llaves de BD usar (`*_AWS`). `dotenv_values` lee **un archivo**, no `os.environ`: un `env_file` de compose no serviría.
- `domain.pem` solo lo usa [`Functions_Sharepoint.py`](../templates/Functions_Sharepoint.py) (certificado de app de SharePoint).
- [`requirements.txt`](../requirements.txt) fija `tensorflow~=2.16.1`, que **no instala en Python 3.13** (el venv de dev es 3.13.5 y no tiene tensorflow ni keras). Nadie importa [`Functions_Pmodels.py`](../templates/Functions_Pmodels.py); `ttkbootstrap`, `customtkinter` y `pyserial` son herencia de la GUI tkinter y el API tampoco los importa. Un `pip install -r requirements.txt` limpio en la imagen fallaría.
- Estado en disco bajo `files/` (rutas en `constants.py`): logs por área en `files/logs/`, contratos en `files/contracts/`, salidas en `files/quizz_out/` y `files/files_fichaje/`, tres JSON que se **escriben** en runtime (`settings.json`, `flags_daemons.json`, `size_pages.json`), caches `.pkl` y temporales `*_temp.pdf|xlsx` en la raíz de `files/`. Los JSON de seed/tools (`quizz_*.json`, `rubrics/`, `tools_AV_*.json`) solo se leen.
- Ningún daemon de [`templates/daemons/`](../templates/daemons/) se arranca desde el API; no hay hilos que cuidar al cambiar de proceso.
- Pool MySQL por proceso ([`db_connection_pool.md`](db_connection_pool.md)): con 3 workers el peor caso sigue siendo 24 conexiones; no cambia con Docker mientras no cambien los workers.
- `GET /GUI/health` en [`app.py`](../app.py) sirve de healthcheck.

## Decisiones del grill

| # | Decisión | Elegido | Por qué / descartado |
|---|---|---|---|
| 1 | Destino | Solo el servidor Linux de prod | Dev reproducible con MySQL y PCs Windows quedan fuera (si se quieren después, compose aparte sobre la misma imagen). |
| 2 | nginx | Se queda en el host | Cambio mínimo: solo cambia el `proxy_pass` al puerto que publique el contenedor. Rollback = parar el contenedor y rearrancar el systemd de gunicorn. |
| 3 | Base image y deps | `python:3.13-slim` + **`requirements-api.txt`** nuevo | Mismo Python que dev. El archivo nuevo es `requirements.txt` sin `tensorflow`, `keras`, `ttkbootstrap`, `customtkinter`, `pyserial` (+ `gunicorn`). `requirements.txt` queda intacto (CLAUDE.md pide no quitar las deps de ML). Imagen ≈ 800 MB en vez de ≈ 3 GB con 3.12 + tensorflow. |
| 4 | `environment` | `environment = os.getenv("API_ENVIRONMENT", "dev")` | Una línea en `constants.py`; sin la variable todo sigue igual en dev. El compose pone `API_ENVIRONMENT=prod`. Descartado `sed`/`ARG` en el build: si la línea cambia de forma el reemplazo no hace nada y prod arrancaría en `dev` contra la BD local. Hay que actualizar la nota de CLAUDE.md que dice que no hay override por variable. |
| 5 | Secretos | Bind mount **read-only** respetando la forma `../` | `WORKDIR /srv/api`; el host monta `/opt/telintec/.env → /srv/.env` y `/opt/telintec/domain.pem → /srv/domain.pem`. El código de prod sigue leyendo `../.env` y `../domain.pem` sin cambios. Nunca se copian a la imagen. |
| 6 | Persistencia de `files/` | Solo lo que se escribe, por subcarpeta | Bind mounts de `files/logs`, `files/contracts`, `files/quizz_out`, `files/files_fichaje` y de los 3 JSON de estado. Seed/tools salen de la imagen (se actualizan con cada deploy); caches `.pkl` y `*_temp.*` efímeros (`files/` debe ser escribible por el usuario del contenedor). |
| 7 | gunicorn | `gunicorn.conf.py` versionado, copiando los flags del systemd actual | `gunicorn -c gunicorn.conf.py wsgi:app`, bind `0.0.0.0:5000`. Los flags exactos los revisa el usuario en el host (`P-140`); mientras, 3 workers sync × 1 thread (lo documentado en `db_connection_pool.md`), `timeout 120` (PDF/Excel), `graceful_timeout 30`, access/error log a stdout. |
| 8 | Entrega | `git pull` + `docker compose up -d --build` en el host | Sin registry ni credenciales nuevas; el servidor ya tiene el repo. Rollback por `git checkout <tag>` + rebuild (cache de capas). Registry/`docker save` descartados por ahora. |
| 9 | Usuario | No root, UID fijo (`USER api`, UID = el del usuario que hoy corre gunicorn) | Las carpetas montadas quedan con ese dueño en el host; un `chown` inicial. |
| 10 | Logs de gunicorn | stdout/stderr (`docker logs`, driver `json-file` con rotación) | Los logs de área siguen en `files/logs/` (mount del punto 6). |
| 11 | Timezone | `TZ=America/Monterrey` + `tzdata` en la imagen | Nombres de log y `date.today()` siguen coincidiendo con el host. |

## Archivos a crear / tocar (al implementar `P-139`)

| Archivo | Contenido |
|---|---|
| `Dockerfile` | `FROM python:3.13-slim`; `apt-get install tzdata` (+ `libgl1`/`libglib2.0-0` solo si PyMuPDF/Pillow lo piden en el build); usuario `api`; `WORKDIR /srv/api`; `COPY requirements-api.txt` + `pip install --no-cache-dir`; `COPY . .`; `ENV API_ENVIRONMENT=prod TZ=America/Monterrey`; `EXPOSE 5000`; `HEALTHCHECK` con `GET /GUI/health`; `CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]`. |
| `.dockerignore` | `.venv`, `.git`, `__pycache__`, `.env*`, `*.pem/*.crt/*.pfx`, `Tests/`, `tester*.py`, `*test.py`, `files/logs/*.txt`, `files/*cache*`, `files/*.pdf|xlsx|csv`, `scripts_db_handle/`, `docs/`, `img/` (si el API no lo sirve), `.idea`, `.vscode`. |
| `requirements-api.txt` | `requirements.txt` menos `tensorflow`, `keras`, `ttkbootstrap`, `customtkinter`, `pyserial`; más `gunicorn`. Comentario arriba apuntando a este doc. |
| `gunicorn.conf.py` | `bind`, `workers`, `threads`, `timeout`, `graceful_timeout`, `accesslog = "-"`, `errorlog = "-"`, `preload_app = False` (el pool se crea por proceso tras el fork, ver `db_connection_pool.md`). |
| `docker-compose.yml` | servicio `api`: `build: .`, `ports: "127.0.0.1:5000:5000"`, `environment: API_ENVIRONMENT=prod, TZ=America/Monterrey`, `volumes` de los puntos 5 y 6 (`:ro` para `.env` y `domain.pem`), `restart: unless-stopped`, `logging: json-file max-size 10m max-file 5`, `healthcheck`. |
| [`static/constants.py`](../static/constants.py) | `environment = os.getenv("API_ENVIRONMENT", "dev")`. |
| `CLAUDE.md` | Sección "Environment & secrets": decir que `API_ENVIRONMENT` sobreescribe la constante. |

Opcional en la misma tanda: `docker-compose.dev.yml` que monte el repo y use `.env` local (no acordado; fuera del alcance de `P-139`).

## Corte en el servidor (orden propuesto)

1. En el host: `docker` + plugin compose instalados; `/opt/telintec/.env` y `/opt/telintec/domain.pem` (los mismos que hoy lee el systemd desde `../`); `mkdir` de las carpetas de `files/` a montar con `chown` al UID del contenedor.
2. `git pull` de la rama con los archivos; `docker compose build`.
3. Parar el servicio systemd de gunicorn (**no** deshabilitarlo todavía); `docker compose up -d`.
4. `curl 127.0.0.1:5000/GUI/health` → `OK`; `docker logs` sin trazas; una lectura autenticada contra la BD de AWS (p. ej. `GET /GUI/api/v1/almacen/kardex`) para confirmar que tomó `HOST_DB_AWS`.
5. nginx: si el upstream ya apuntaba a `127.0.0.1:5000` no cambia nada; si era un socket unix, cambiar a `proxy_pass http://127.0.0.1:5000` y `nginx -s reload`.
6. Tras unos días estables: `systemctl disable` del servicio viejo. Rollback en cualquier momento: `docker compose down` + `systemctl start` del viejo.

## Verificación antes de tocar prod

- Build local en Docker Desktop (Windows) con `API_ENVIRONMENT` sin poner (= `dev`) y el `.env` local montado en `/srv/api/.env`: `GET /GUI/health` y un endpoint con BD local.
- Dentro del contenedor: `python -c "import app"` arranca sin `ModuleNotFoundError` (confirma que el recorte de `requirements-api.txt` no quitó nada que el API importe).
- Generar un PDF (p. ej. una remisión) y un Excel desde el contenedor: valida reportlab/PyMuPDF/openpyxl en slim y los permisos de `files/`.
- `date` dentro del contenedor en hora de Monterrey; el log del día aparece en `files/logs/` del host con el dueño correcto.

## Al modificar

- Si cambian `workers`/`threads` en `gunicorn.conf.py`, revisar `POOL_SIZE` en [`connection.py`](../templates/database/connection.py) (regla de [`db_connection_pool.md`](db_connection_pool.md)).
- Nueva dependencia que importe el API → va en **ambos** `requirements.txt` y `requirements-api.txt`.
- Nueva ruta escribible bajo `files/` en `constants.py` → agregar su mount en `docker-compose.yml`, o se pierde al recrear el contenedor.
- Nuevo archivo que lea el código fuera del repo (otro `.pem`, etc.) → mount `:ro` nuevo; nunca `COPY`.
- `.env` cambia → `docker compose restart api` (se lee una vez al importar, igual que antes).

## Notas posteriores

- **2026-10-22 — `P-139` en pausa** por decisión del usuario ("todavía no"); `P-140` (flags de gunicorn) igual. Al retomarlo, revisar la decisión 4: para desplegar, `static/constants.py` se commitea con `environment = "prod"` y luego se regresa a `"dev"` (commits `0d553b6` "prod update" y `5a7e4b0` "update dev mode" del 2026-10-22). Si el `os.getenv("API_ENVIRONMENT", "dev")` llega a prod antes que el contenedor, el systemd arrancaría en `dev`, salvo que defina `API_ENVIRONMENT=prod`. Se resuelve junto con la forma de desplegar; de paso se acaba el ir y venir de commits.
