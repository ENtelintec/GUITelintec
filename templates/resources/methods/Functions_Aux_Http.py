# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/oct./2026  at 20:00 $"

"""ETag débil + 304 para GET de JSON (P-128 kardex; P-202 / P-204 catálogos).
Docs: docs/almacen_kardex_etag.md y docs/almacen_catalogos_etag_y_reservas.md.

La huella es el cuerpo completo, así que es exacta sin columna de versión: la
consulta se sigue haciendo y el ahorro está en la red (un refresco sin cambios
responde 304 sin cuerpo y el navegador reusa el 200 que tenía). El front no
cambia: `fetch` con caché por defecto manda If-None-Match solo.
"""

import hashlib
import json

from werkzeug.datastructures import ETags
from werkzeug.http import quote_etag


def etag_conditional(data_out: dict, code: int, if_none_match: ETags) -> tuple:
    """Solo a los 200: `ETag: W/"<blake2b-128 del JSON>"` + `Cache-Control:
    private, no-cache`; si `if_none_match` (= `request.if_none_match`) coincide
    en comparación débil, (None, 304, headers). Cualquier otro código pasa
    intacto y sin cabeceras. -> (body, code, headers) para devolver desde el
    Resource. No meter en el cuerpo nada que cambie en cada llamada."""
    if code != 200:
        return data_out, code, {}
    body = json.dumps(data_out, separators=(",", ":"), default=str).encode()
    digest = hashlib.blake2b(body, digest_size=16).hexdigest()
    headers = {"ETag": quote_etag(digest, weak=True), "Cache-Control": "private, no-cache"}
    if if_none_match.contains_weak(digest):
        return None, 304, headers
    return data_out, code, headers
