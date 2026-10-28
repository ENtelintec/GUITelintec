# `environment` desde `API_ENVIRONMENT` (`.env` o variable del sistema)

> 2026-10-28. **Sin cambio de contrato**: ningún endpoint cambia. Reemplaza el `environment = "dev"` escrito en [`constants.py`](../static/constants.py), que había que commitear en `"prod"` para desplegar y regresar a `"dev"` después.

## Antes

- `environment` era una constante del código. Decidía qué `.env` leer (`.env` en dev, `../.env` en prod), dónde estaba `domain.pem`, qué llaves de BD usar (`*_AWS` en prod), el guard del correo SES de [`MD_BalanceAlerts.py`](../templates/resources/midleware/MD_BalanceAlerts.py) y el prefijo de las llaves S3 de [`Functions_Aux_S3.py`](../templates/resources/methods/Functions_Aux_S3.py).
- Para desplegar: commit con `"prod"`, deploy, commit con `"dev"`. Mientras el repo estaba en `"prod"`, un tester local pegaba a la BD de prod y abría el correo SES ([`avisos_saldos_correo.md`](avisos_saldos_correo.md)).
- Cualquier valor distinto de `"prod"` contaba como dev, sin aviso.
- `.env` y `../.env` eran relativos al working directory.

## Ahora

Todo vive en el bloque de arriba de [`constants.py`](../static/constants.py) y corre al importarse:

1. **Busca el `.env`**: primero `<repo>/.env`; si no existe, `<repo>/../.env`. `<repo>` sale de la ruta de `constants.py`, no del working directory: un script corrido desde una subcarpeta encuentra el mismo `.env`.
2. **`domain.pem`** se lee de la misma carpeta que el `.env` encontrado.
3. **`environment`** = la variable del sistema `API_ENVIRONMENT` si existe y no está vacía; si no, la llave `API_ENVIRONMENT` de ese `.env`.
4. **Valida**: si no es exactamente `dev` o `prod` (falta, vacía, `Prod`, `production`…), lanza `RuntimeError` al importar y el API no arranca. Igual si no hay `.env` en ninguna de las dos carpetas.

| Situación | Resultado |
|---|---|
| dev: `<repo>/.env` con `API_ENVIRONMENT=dev` | `dev`, llaves `HOST_DB`/`USER_SQL`/`PASS_SQL`, `<repo>/domain.pem` |
| prod: sin `.env` en el checkout, `/home/ec2-user/opt/.env` con `API_ENVIRONMENT=prod` | `prod`, llaves `*_AWS`, `/home/ec2-user/opt/domain.pem` |
| `.env` en el repo **y** en `../` | gana el del repo |
| Variable del sistema `API_ENVIRONMENT=dev` | `dev` aunque el `.env` diga `prod` |
| Falta la llave, vacía o mal escrita | no arranca: `RuntimeError: API_ENVIRONMENT debe ser 'dev' o 'prod' (vale '…', leido de <ruta del .env>)` |
| Ningún `.env` | no arranca: `RuntimeError: No se encontro .env en <repo> ni en <padre>` |

**Por qué no hay default:** con `"dev"` por default, un `.env` de prod sin la llave arrancaría con las llaves de dev sin avisar. Que gunicorn no levante se ve de inmediato; apuntar a la BD equivocada, no.

**Por qué gana la variable del sistema:** deja lista la decisión 4 de [`despliegue_docker.md`](despliegue_docker.md) (el compose pone `API_ENVIRONMENT=prod`) y permite forzar `dev` para un tester sin editar el `.env`: `API_ENVIRONMENT=dev python Tests/tester_x.py`.

**Sin cambios:** los consumidores ([`MD_BalanceAlerts.py`](../templates/resources/midleware/MD_BalanceAlerts.py), [`Functions_Aux_S3.py`](../templates/resources/methods/Functions_Aux_S3.py), `HOST_DB_DEFAULT`/`USER_DB_DEFAULT`/`PASS_DB_DEFAULT`, [`Functions_Sharepoint.py`](../templates/Functions_Sharepoint.py)) siguen importando `environment`, `secrets` y `domain_path` de `constants.py`. Las rutas de `files/` siguen relativas al working directory: el API se corre desde la raíz del repo, igual que antes.

## Verificación (2026-10-28, dev)

- Copia de `constants.py` en una carpeta temporal con la forma de prod (`opt/.env` + `opt/repo/static/`): los casos de la tabla dan lo esperado, también con el working directory dentro de `static/`.
- `constants` real con `API_ENVIRONMENT=dev`: `dev`, `HOST_DB`, `.env` y `domain.pem` del repo; `import app` arranca.
- `pyrefly check --python-version 3.11` sin errores en `constants.py`, `Functions_Aux_S3.py` y `MD_BalanceAlerts.py`.

## Deploy (`P-212`)

Orden en el servidor:

1. Agregar `API_ENVIRONMENT=prod` a `/home/ec2-user/opt/.env` **antes** del `git pull`. Si falta, los workers mueren al importar y el servicio no levanta: no hay riesgo de usar la BD equivocada, pero sí de una caída.
2. Confirmar que **no** hay `.env` dentro de `/home/ec2-user/opt/GUITelintec/`: si lo hay, se lee ese y no el de `../`.
3. `git pull` + `sudo systemctl restart guitelintec`.
4. `GET /GUI/health` y una lectura autenticada (p. ej. `GET /GUI/api/v1/almacen/kardex`) para confirmar que tomó la BD de AWS. Si no levanta, `journalctl -u guitelintec` muestra el `RuntimeError` con la ruta que leyó.

Cada máquina de dev necesita `API_ENVIRONMENT=dev` en su `.env`.

## Al modificar

- **Nuevo valor de `environment`** (p. ej. `test`): agregarlo a la tupla de la validación en `constants.py` y revisar todos los `environment != "prod"` (llaves de BD, guard de SES) y `S3_ENVIRONMENTS` en [`Functions_Aux_S3.py`](../templates/resources/methods/Functions_Aux_S3.py).
- **Nuevo archivo de secretos fuera del repo** (otro `.pem`): leerlo de `_env_dir`, como `domain_path`, no con un `../` fijo.
- **No** volver a escribir `environment` en el código para desplegar ni para probar: el valor vive en el `.env` de cada máquina.
- Cambiar el `.env` requiere reiniciar el API (se lee una vez al importar).
