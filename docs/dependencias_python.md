# Dependencias del API y versión de Python objetivo

> 2026-10-26. [`requirements.txt`](../requirements.txt) depurado contra lo que el API importa de verdad y **fijado a las versiones que corren en prod** (venv `envg`); las transitivas van en [`constraints.txt`](../constraints.txt). Objetivo de compatibilidad: **Python 3.11**, el de prod (Amazon Linux 2023); dev corre 3.12.10. 3.11 deja de recibir parches de seguridad en **octubre de 2027** → `P-178`. Ningún endpoint ni contrato cambia; el único cambio de código quita la cadena muerta de Dropbox. Lo que hay en `development` es lo que corre en prod, así que el venv de prod se depura igual (`P-182`).

## Qué cambió

| Archivo | Cambio |
|---|---|
| [`requirements.txt`](../requirements.txt) | 23 paquetes del API con `==` a la versión de `envg`, más `gunicorn==22.0.0` solo fuera de Windows (`; sys_platform != "win32"`). Agrupado por uso con comentarios ASCII (pip en Windows decodifica con la página de códigos local). Primera línea útil: `-c constraints.txt`. Salen 16 paquetes (tabla de abajo); entra `python-dateutil`, que [`MD_Kardex.py`](../templates/resources/midleware/MD_Kardex.py) importa directo. |
| [`constraints.txt`](../constraints.txt) (nuevo) | 64 versiones exactas de `envg`: las 62 que instala `requirements.txt` en Windows más `gunicorn` y `packaging` (Linux). Solo restringe, no instala. **Sin él no se reproduce prod**: un install limpio trae `httpx` 0.28 y `openai` 1.22 truena al importar `app` (`Client.__init__() got an unexpected keyword argument 'proxies'`; prod tiene `httpx==0.27.0`). `pip` resuelve el `-c` relativo al archivo, no al cwd. |
| [`Functions_Files.py`](../templates/misc/Functions_Files.py) | Fuera `import dropbox`, `secrets` del import de `constants` y la cadena muerta `save_directory_index` → `map_dropbox_folders` → `get_files_foldes_dropbox` → `check_only_read_conflict` (nadie llamaba a la primera). Se quedan `DirectoryDbp` y `load_directory_file`, que leen los `.pkl` de carpetas. |
| [`pyrefly.toml`](../pyrefly.toml) (local: está en `.gitignore`; pyrefly es herramienta de dev, no va a prod) | `python-version = "3.11"`: `pyrefly check` marca sintaxis y stdlib de 3.12+ aunque el venv sea 3.12. En otra copia del repo: `pyrefly check --python-version 3.11`. |
| [`CLAUDE.md`](../CLAUDE.md) | *Run / lint*: Python objetivo y cómo se verifica; *Dependencies*: versiones fijadas, `constraints.txt`, sin stack de ML; `files/Pmodels/` marcado como huérfano. |

## Qué salió y por qué

Método: grafo de imports por AST desde [`wsgi.py`](../wsgi.py) (incluye los imports dentro de funciones) → 134 archivos alcanzados; más grep en todo el repo, [`scripts_db_handle/`](../scripts_db_handle/) y `Tests/` de usos indirectos (engines de `pd.read_excel`/`to_excel`, `pkg_resources`, `pd.read_sql`, `.plot(`).

| Paquete | Por qué sale |
|---|---|
| `tensorflow~=2.16.1`, `keras`, `scikit-learn~=1.5.0`, `matplotlib` | Decisión del usuario: el API no los importa. Los tres primeros solo los usa [`Functions_Pmodels.py`](../templates/Functions_Pmodels.py) (modelo Keras + scalers de `files/Pmodels/`), que nadie importa; `matplotlib` no tiene ni `import` ni `.plot(`. Prod nunca tuvo tensorflow, keras ni scikit-learn. |
| `dropbox` | Decisión del usuario ("ya no se usa"): solo lo usaba la cadena muerta de `Functions_Files.py`, eliminada. |
| `Flask-SQLAlchemy~=3.1.1`, `SQLAlchemy~=2.0.23` | Cero imports y ningún `pd.read_sql`; todo va por `execute_sql`. |
| `ttkbootstrap`, `customtkinter` | Herencia de la GUI tkinter; nadie los importa, ni el código muerto. |
| `pyserial` | Solo [`daemons/Peripherals.py`](../templates/daemons/Peripherals.py) y [`misc/PortsSearcher.py`](../templates/misc/PortsSearcher.py), que el API no carga. |
| `bardapi` | Solo [`Functions_Observer.py`](../templates/Functions_Observer.py), huérfano. La API de Bard ya no existe (la reemplazó Gemini). |
| `requests` | Solo `Functions_Observer.py`. Se sigue instalando como dependencia de `Office365-REST-Python-Client` (queda fijo en `constraints.txt`). |
| `Unidecode` | Cero imports; el código usa `unicodedata`. |
| `pyxlsb` | Ningún endpoint acepta `.xlsb` ni pide `engine="pyxlsb"`. (`xlrd` **se queda**: [`get_data_encuesta`](../templates/misc/Functions_Files.py) y los fichajes de [`Functions_midleware_RRHH.py`](../templates/resources/midleware/Functions_midleware_RRHH.py) aceptan `.xls`.) |
| `Flask-WTF` | Cero imports de `flask_wtf`; las forms son `WTForms` + `WTForms-JSON` directo. |
| `setuptools` | Nadie la importa directo. Lo único que la necesitaba era `dropbox` 11.36.2 (la de prod), que hace `import pkg_resources`: los venvs de 3.12+ no traen `setuptools` y `setuptools` ≥ 81 ya no trae `pkg_resources`. Con `dropbox` fuera ya no hace falta. |

Código muerto que **no** se tocó (importarlo hoy daría `ModuleNotFoundError`, pero nadie lo importa): `Functions_Pmodels.py` (y los modelos de `files/Pmodels/`), `Functions_Observer.py` (+ `controllers/chatbot/`), `daemons/Peripherals.py`, `misc/PortsSearcher.py`.

## Prod: servidor, venvs y depuración

### El servidor (datos del usuario, 2026-10-26)

- **SO: Amazon Linux 2023** (`aws --version` → `aws-cli/2.32.1 Python/3.9.25 Linux/6.1.41-63.114.amzn2023.x86_64 source/x86_64.amzn.2023`). AL2023 tiene soporte hasta el **2029-06-30**: estándar hasta 2027-06-30 y después solo seguridad y fallos críticos ([release cadence](https://docs.aws.amazon.com/linux/al2023/ug/release-cadence.html)) → `P-180`.
- **Python del sistema: `/usr/bin/python3` = 3.9** toda la vida de AL2023. Lo usan `dnf` y el `aws-cli` del repo, que reporta 3.9.25, el paquete vigente. AWS: *"Do not change what the `/usr/bin/python3` symlink points to because this might break the core functionality of AL2023."* ([Python in AL2023](https://docs.aws.amazon.com/linux/al2023/ug/python.html)). Un Python nuevo se instala **al lado** (`/usr/bin/python3.X`) y el API lo usa desde su venv.
- **Python del API: 3.11.4.** El paquete `python3.11` de AL2023 va en **3.11.16** (lista de paquetes de la release 2023.12.20261021) y el `python3.9` del servidor sí está al día. El 3.11.4, entonces, probablemente **no** viene de `dnf` (compilado o pyenv) y no recibe parches: le faltan 12 versiones de corrección. Por confirmar en `P-179`.
- **Kernel: falta reiniciar.** `rpm -q kernel` da 6.1.41 (en ejecución) y 6.1.158 (instalado). `sudo dnf needs-restarting -r` reporta `glibc`, `kernel`, `microcode_ctl` y `systemd` actualizados desde el arranque → `P-181`.

### Los dos venvs del checkout

- **`envg` es el del API** (confirmado por el usuario). Tiene los 23 paquetes con las versiones que ahora fija `requirements.txt`, más 21 que el API no usa: `bardapi`, `Flask-SQLAlchemy`, `SQLAlchemy`, `greenlet`, `Flask-WTF`, `matplotlib`, `contourpy`, `cycler`, `fonttools`, `kiwisolver`, `pyparsing`, `pyserial`, `ttkbootstrap`, `Unidecode`, `pypdf`, `dropbox`, `stone`, `ply`, `h2`, `hpack` y `hyperframe`.
- **`env` es viejo** (época GUI/chatbot: `customtkinter`, `bardapi`, `python-gemini-api`, `heyoo`, `pymessenger`) y **no puede** importar el código actual. Le faltan `WTForms`, `WTForms-JSON`, `reportlab`, `PyMuPDF`, `PyPDF2`, `openpyxl`, `xlsxwriter` y `Office365-REST-Python-Client`, y trae `openai` 0.28 (el código usa `from openai import OpenAI`, que existe desde 1.0). Se borra en `P-182`.

### Depurar `envg` (`P-182`)

Venv nuevo junto al actual, nunca `pip uninstall` en caliente (no deja rollback y deja huérfanas las dependencias):

1. Desplegar primero el código sin Dropbox (este cambio). Corre igual en el `envg` actual y es requisito del venv nuevo, que ya no trae `dropbox`.
2. En el checkout: `$(grep '^home' envg/pyvenv.cfg | cut -d' ' -f3)/python3.11 -m venv envg2` (mismo Python base que `envg`) y `envg2/bin/pip install -r requirements.txt`.
3. `envg2/bin/python -c "import app"` desde el checkout y `diff <(envg/bin/pip freeze) <(envg2/bin/pip freeze)`: solo deben faltar los 21 de arriba, sin versiones distintas.
4. Cambiar en el `ExecStart` del systemd la ruta de `envg` por `envg2`, luego `sudo systemctl daemon-reload` y `restart`. Comprobar `curl 127.0.0.1:<puerto>/GUI/health` y un PDF/Excel. Rollback: regresar el `ExecStart` a `envg`.
5. Tras unos días estables: borrar `envg` y `env`. Se puede hacer en la misma ventana que el reinicio de `P-181`.

Mientras siga vivo `envg`: **no** correr `pip install -U` sueltos ahí. Por ejemplo, `setuptools` ≥ 81 rompía `import dropbox` mientras el código lo importaba.

## Verificación (2026-10-26)

- **Versiones de prod** (`requirements.txt` + `constraints.txt`) en un venv limpio de 3.12.10, sin `setuptools` ni `dropbox`: `import app` sin errores, `GET /GUI/health` → 200 y `GET /swagger.json` → 200. También `.xlsx` con openpyxl y con `engine="xlsxwriter"`, y un PDF de reportlab abierto con PyMuPDF y leído con PyPDF2. La resolución desde otro cwd da exactamente los 62 paquetes y versiones de `envg`.
- **Versiones últimas** (lista sin pins, antes de fijar) en 3.12.10, 3.13.5 y 3.15.2: mismas pruebas en verde. Sirve para `P-178`: el código ya corre con Flask 3.1, pandas 3.1, PyMuPDF 2.0 y openai 3.x.
- **3.11**: prod corre esas versiones exactas en 3.11.4; ruff `--target-version py311` y pyrefly `--python-version 3.11` sin sintaxis ni stdlib de 3.12.
- **No verificado**: correr el API en un 3.11 local, y que el `ExecStart` apunte a `envg` (`P-140`).

## Versión destino — datos para `P-178`

Cada versión upstream recibe correcciones 2 años (18 meses antes de 3.13) y luego solo seguridad hasta los 5 años ([devguide.python.org/versions](https://devguide.python.org/versions/), consultado 2026-10-26). AL2023 publica `python3.11` a `python3.14` como paquetes instalables a la vez y actualizados por `dnf`; **3.15 todavía no**. AWS les da el soporte de upstream, **recortado por el fin de AL2023**:

| Versión | Fin upstream | Paquete AL2023 (release 2026-10-21) | Fin efectivo en AL2023 | Lista **sin pins** (ruedas Linux) | Probada aquí |
|---|---|---|---|---|---|
| 3.11 (prod) | 2027-10 | `python3.11` 3.11.16 | 2027-10-01 | completa | es la de prod |
| 3.12 (dev) | 2028-10 | `python3.12` 3.12.14 | 2028-10-01 | completa | sí, 3.12.10 |
| 3.13 | 2029-10 | `python3.13` 3.13.15 | **2029-06-30** (fin de AL2023) | completa | sí, 3.13.5 |
| 3.14 | 2030-10 | `python3.14` 3.14.7 | **2029-06-30** (fin de AL2023) | completa | dry-run |
| 3.15 (salió 2026-10-09) | 2031-10 | no existe | solo compilado o Docker | completa, pero `PyMuPDF` retrocede a 1.28.2 (`onnxruntime` sin rueda cp315) | sí, 3.15.2 |

**Con las versiones de prod fijadas**, cp314 no tiene rueda de `numpy` 1.26.4, `pandas` 2.1.4, `Pillow` 10.3.0, `MarkupSafe` 2.1.5, `cffi` 1.16.0 ni `pydantic_core` 2.18.4. `WTForms-JSON` 0.3.5 solo publica sdist, pero es Python puro e instala igual. Migrar implica subir esos paquetes (numpy 2 obliga a subir pandas, porque 2.1 no es compatible con numpy 2) y regenerar `constraints.txt`. Dos saltos mayores a decidir en ese momento:

- **`pandas` 3.x**: copy-on-write y `str` como dtype por defecto.
- **`PyMuPDF` 2.0**: trae como dependencias obligatorias `onnxruntime` (≈ 48 MB instalado), `pymupdf-layout`, `pymupdf4llm`, `networkx`, `pyyaml`, `psutil` y `tabulate`, nada de lo cual usa el API. Además `import fitz` (4 lugares: [`BarCodeGenerator.py`](../templates/forms/BarCodeGenerator.py), [`MD_Admin_Collections.py`](../templates/resources/midleware/MD_Admin_Collections.py), [`MD_SGI.py`](../templates/resources/midleware/MD_SGI.py) ×2) avisa: *"The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead."* Opciones: quedarse en 1.x o pasar a 2.x con `import pymupdf`.

Lectura (la decisión es de `P-178`):

- En AL2023 **el techo lo pone el SO (2029-06-30), no Python**: 3.13 y 3.14 duran lo mismo ahí y 3.12 acaba antes (2028-10).
- **Recomendado: `python3.14` de `dnf`.** Recibe parches de AWS por `dnf` hasta 2029-06 (el 3.11.4 de hoy, al parecer, no). La lista ya corre con versiones recientes y, si en 2029 se cambia de SO o se pasa a Docker, 3.14 aún tiene soporte upstream hasta 2030-10, cosa que 3.13 no.
- **3.15** solo tiene sentido con Docker (`python:3.15-slim`, `P-139`). Compilarlo en el host repetiría el problema actual: un Python sin parches automáticos.
- Dev debe ir en la misma versión: hoy la máquina tiene 3.12, 3.13 y 3.15, pero no 3.14.

## `P-178` — elegir versión destino y subir prod de Python 3.11

1. Confirmar los datos del servidor (`P-179`) y **elegir destino**; recomendado `python3.14` de AL2023. Decisión del usuario.
2. ~~`pip freeze` de prod y fijar versiones~~ — hecho (2026-10-26): `requirements.txt` + `constraints.txt` = `envg`.
3. Subir para la versión nueva los paquetes sin rueda (lista de arriba), decidir pandas 3 / PyMuPDF 2 y regenerar `constraints.txt` (receta abajo).
4. Prod: `sudo dnf install python3.14`, venv nuevo **junto** al actual (mismo procedimiento que `P-182`, sin tocar `/usr/bin/python3`) y apuntar el systemd de gunicorn al venv nuevo. Rollback = regresar al venv viejo.
5. Dev: `.venv` en 3.14, `python-version` en el `pyrefly.toml` local y la línea 1 de `requirements.txt`. Probar en test con la batería de `Tests/` y desplegar. Plazo: **antes de octubre de 2027**.

### Regenerar `constraints.txt`

Al subir o agregar un paquete: cambiar su `==` en `requirements.txt`. Luego, en un venv limpio del Python de prod (Linux, así salen `gunicorn` y sus dependencias):

```bash
grep -v '^-c ' requirements.txt > /tmp/req.txt      # sin las restricciones viejas
python -m venv /tmp/v && /tmp/v/bin/pip install -r /tmp/req.txt
/tmp/v/bin/pip freeze                               # → cuerpo nuevo de constraints.txt (conservar el encabezado)
```

Probar `import app`, `/GUI/health` y un PDF/Excel con ese venv antes de commitear los dos archivos.

## Al modificar

- **Dependencia nueva o versión nueva** → `==` en `requirements.txt` y regenerar `constraints.txt`; que instale en 3.11 (revisar `Requires-Python` en PyPI). Si `P-139` llega a crear `requirements-api.txt`, en ambos.
- **Código nuevo** → `pyrefly check` (con el `pyrefly.toml` local, o `--python-version 3.11`) marca lo exclusivo de 3.12+: f-strings que reutilizan la comilla de fuera (`f"{d["k"]}"`), `type X = ...`, genéricos PEP 695 (`def f[T]()`), `itertools.batched`, `typing.override`. No subir `python-version` hasta que prod suba (`P-178`).
- **Revivir un módulo huérfano** (`Functions_Pmodels`, `Peripherals`, …) → su dependencia regresa a `requirements.txt` (tensorflow/keras/scikit-learn, pyserial). `bardapi` ya no sirve.
- **Dev local**: un `.venv` instalado con la lista sin pins (como el del 2026-10-26: Flask 3.1, pandas 3.1, PyMuPDF 2.0) no es prod. Recrearlo con `pip install -r requirements.txt` sobre un venv limpio.
