# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/jun./2024  at 17:07 $"

import json
from datetime import date, datetime, timedelta

from static.constants import cache_file_nominas


def write_file_cache_nominas(data: dict):
    """
    writes a JSON file with the data of the payrolls
    :param data:
    :return:
    """
    json.dump(data, open(cache_file_nominas, "w"))
    return 200, "OK"


# --- Exámenes médicos: periodicidad por aptitud ------------------------------
# Única fuente de la regla (la usan el dashboard de RH, GET /rrhh/employees/medical/all
# y el daemon de notificaciones médicas). Espeja el catálogo
# sql_telintec_mod_rrhh.aptitude: 0 no determinado, 1 12 meses, 2 6 meses,
# 3 3 meses, 4 no apto. `aptitude_actual` se guarda como entero, pero se
# tolera "APTO N" y numéricos en texto/float por si el front lo manda así.
MEDICAL_PERIOD_DAYS = {1: 365, 2: 180, 3: 90}
MEDICAL_NO_APTO = 4
MEDICAL_WARNING_DAYS = 30  # "por vencer" = faltan 0..30 días

_DATE_FORMATS_MEDICAL = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y")


def normalize_aptitude(value) -> int | None:
    """1..4 (o 0) a partir de int, float, '2', 'APTO 2', 'apto 2'; None si no se entiende."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().upper()
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def parse_medical_date(raw):
    """date | None desde los timestamps de `renovacion` ('YYYY-MM-DD HH:MM:SS')."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    if not text or text.lower() in ("none", "null", "nat", "nan"):
        return None
    for fmt in _DATE_FORMATS_MEDICAL:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def last_medical_date(dates) -> date | None:
    """Última fecha legible de la lista `renovacion` (JSON ya cargado o crudo)."""
    if isinstance(dates, str):
        try:
            dates = json.loads(dates)
        except (TypeError, ValueError):
            dates = []
    parsed = [d for d in (parse_medical_date(x) for x in (dates or [])) if d is not None]
    return max(parsed) if parsed else None


def medical_due(aptitude, last_date, today) -> dict:
    """Estado de vencimiento del examen médico.

    Devuelve {alert, period_days, due_date, days_left}:
      alert ∈ 'no_apto' (aptitud 4) · 'sin_fecha' (sin examen legible) ·
              'sin_periodo' (aptitud 0/desconocida) · 'vencido' (days_left < 0) ·
              'por_vencer' (0..MEDICAL_WARNING_DAYS) · 'al_dia'.
    due_date/days_left solo vienen cuando hay periodo y fecha."""
    apt = normalize_aptitude(aptitude)
    out: dict = {"alert": "sin_fecha", "period_days": None, "due_date": None, "days_left": None}
    if apt == MEDICAL_NO_APTO:
        out["alert"] = "no_apto"
        return out
    if last_date is None:
        return out
    period = MEDICAL_PERIOD_DAYS.get(apt) if apt is not None else None
    if period is None:
        out["alert"] = "sin_periodo"
        return out
    due = last_date + timedelta(days=period)
    days_left = (due - today).days
    out.update({"period_days": period, "due_date": due, "days_left": days_left})
    if days_left < 0:
        out["alert"] = "vencido"
    elif days_left <= MEDICAL_WARNING_DAYS:
        out["alert"] = "por_vencer"
    else:
        out["alert"] = "al_dia"
    return out
