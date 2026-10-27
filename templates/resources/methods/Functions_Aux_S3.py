# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 27/oct./2026  at 12:00 $"

"""Llaves S3 separadas por entorno (P-177, docs/s3_rutas_por_entorno.md).

dev, test y prod comparten los buckets, asi que toda llave NUEVA lleva el
entorno justo despues de su carpeta raiz: "<raiz>/<entorno>/<resto>". El
entorno es "test" con token de tester (BD de pruebas) y, si no, el
`environment` de static/constants.py ("dev" | "prod"); mismo criterio que
MD_BalanceAlerts.

Las llaves viejas (sin entorno) siguen validas: cada registro guarda la ruta
completa del objeto y nadie la reconstruye ni lista el bucket.
"""

from static.constants import environment

S3_ENVIRONMENTS = ("dev", "test", "prod")


def s3_environment(data_token) -> str:
    """Entorno de las llaves que escribe este request."""
    if isinstance(data_token, dict) and data_token.get("is_tester"):
        return "test"
    return environment


def s3_env_key(root: str, rest: str, data_token) -> str:
    """Llave nueva "<root>/<entorno>/<rest>"."""
    return f"{root}/{s3_environment(data_token)}/{rest.lstrip('/')}"


def s3_key_environment(key) -> str | None:
    """Entorno de una llave ("dev" | "test" | "prod"), o None si es una llave
    vieja sin entorno."""
    parts = str(key or "").split("/")
    return parts[1] if len(parts) > 2 and parts[1] in S3_ENVIRONMENTS else None


def s3_can_delete(key, data_token) -> bool:
    """True si este request puede borrar el objeto de S3. Cada entorno borra
    solo las llaves con su prefijo; las viejas (sin entorno) pueden estar
    compartidas entre dev, test y prod, asi que solo las borra prod. Quien no
    puede borrar solo quita la entrada de su indice (el objeto queda para la
    conciliacion)."""
    key_env = s3_key_environment(key)
    current = s3_environment(data_token)
    if key_env is None:
        return current == "prod"
    return key_env == current
