# -*- coding: utf-8 -*-
"""
Dashboard de RH — orquestación (docs/dashboard_rrhh.md, plan_mes_2.md Anexo D).

`get_rrhh_summary_api`  → todos los tiles en un JSON para un mes (default el
                          actual): headcount, altas/bajas, exámenes médicos
                          por vencer, vacaciones pendientes, encuestas y
                          cumpleaños. Cada tile trae los ids para que el
                          click del front lleve a la lista filtrada.
`get_rrhh_series_api`   → una serie por `metric` (altas_bajas | headcount)
                          agrupada por mes o por departamento. KPI nuevo =
                          `metric` nuevo aquí, mismo shape para el front.

Los agregados son chicos (~100 empleados) y se calculan en Python sobre las
filas crudas del controller; sin caché. Fichajes quedan fuera del dashboard.
"""
__author__ = "Edisson Naula"
__date__ = "$ 10/sep./2026  at 12:00 $"

import calendar
import json
import re
from datetime import date, datetime, timedelta

import pytz

from static.constants import timezone_software
from templates.resources.methods.Functions_Aux_RH import (
    MEDICAL_PERIOD_DAYS,
    last_medical_date,
    medical_due,
)
from templates.controllers.rrhh.dashboard_rrhh_controller import (
    DEPARTMENT_COLUMNS,
    EMPLOYEE_LIFECYCLE_COLUMNS,
    MEDICAL_COLUMNS,
    QUIZZ_STATS_COLUMNS,
    VACATION_COLUMNS,
    get_active_medical_db,
    get_active_vacations_db,
    get_departments_db,
    get_employees_lifecycle_db,
    get_quizz_stats_db,
)

# Periodicidad del examen médico: regla compartida en Functions_Aux_RH
# (`medical_due`, la misma de GET /rrhh/employees/medical/all y del daemon).
# Aquí solo se afina el "por vencer" en buckets (días restantes inclusivos).
MEDICAL_BUCKETS = (("d30", 30), ("d60", 60), ("d90", 90))

# Vacaciones: el `status` de cada periodo es texto libre capturado por RH.
# Pendiente = "<n> PTE" / "PTES" / "PTS" (con o sin número) o un número solo.
_VAC_PENDING_RE = re.compile(r"^\s*(\d+)?\s*PT[ES]\w*\s*$", re.IGNORECASE)
_VAC_DIGITS_RE = re.compile(r"^\s*(\d+)\s*$")
VACATIONS_UPCOMING_DAYS = 30

SERIES_METRICS = ("altas_bajas", "headcount")
SERIES_GROUP_BY = ("month", "department")
SERIES_MAX_MONTHS = 120

_EMPTY_DATE_TOKENS = ("", "none", "null", "nan", "nat")
_DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y")
_NO_DEPARTMENT = "Sin departamento"


# --- helpers ----------------------------------------------------------------
def _today() -> date:
    return datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software)).date()


def _parse_any_date(raw):
    """date | None a partir de date/datetime/str con formatos mezclados
    ('YYYY-MM-DD', 'YYYY-MM-DD HH:MM:SS', 'DD/MM/YYYY'); vacío/'None' → None."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    if text.lower() in _EMPTY_DATE_TOKENS:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_month(raw, today: date):
    """(year, month) de 'YYYY-MM'; ausente → mes actual. ValueError si es inválido."""
    if raw is None or str(raw).strip() == "":
        return today.year, today.month
    text = str(raw).strip()
    if not re.fullmatch(r"\d{4}-\d{2}", text):
        raise ValueError("month debe tener el formato YYYY-MM")
    year, month = int(text[:4]), int(text[5:7])
    if not 1 <= month <= 12:
        raise ValueError("month fuera de rango (01..12)")
    return year, month


def _month_bounds(year: int, month: int):
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _months_between(date_from: date, date_to: date):
    """Lista de (year, month) desde el mes de date_from hasta el de date_to."""
    out = []
    year, month = date_from.year, date_from.month
    while (year, month) <= (date_to.year, date_to.month):
        out.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def _full_name(name, l_name) -> str:
    return " ".join(p for p in (str(name or "").strip(), str(l_name or "").strip()) if p)


def _iso(d) -> str | None:
    return d.isoformat() if isinstance(d, date) else None


def _rows(result) -> list:
    return list(result) if isinstance(result, (list, tuple)) else []


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _load_employees(data_token):
    """Empleados con fechas ya parseadas: admission (date|None), departure
    (date|None) y departure_unparsed (texto crudo que no se pudo leer)."""
    flag, error, result = get_employees_lifecycle_db(data_token)
    if not flag:
        return None, error
    employees = []
    for row in _rows(result):
        emp = dict(zip(EMPLOYEE_LIFECYCLE_COLUMNS, row))
        emp["is_active"] = str(emp.get("status") or "").strip().lower() == "activo"
        emp["full_name"] = _full_name(emp.get("name"), emp.get("l_name"))
        emp["department"] = emp.get("department") or _NO_DEPARTMENT
        emp["admission"] = _parse_any_date(emp.get("date_admission"))
        raw_departure = emp.get("departure_date")
        emp["departure"] = _parse_any_date(raw_departure)
        has_text = raw_departure is not None and str(raw_departure).strip().lower() not in _EMPTY_DATE_TOKENS
        emp["departure_unparsed"] = str(raw_departure).strip() if has_text and emp["departure"] is None else None
        emp["birth"] = _parse_any_date(emp.get("birthday"))
        employees.append(emp)
    return employees, None


def _emp_brief(emp: dict, **extra) -> dict:
    out = {
        "emp_id": emp["employee_id"],
        "name": emp["full_name"],
        "department_id": emp.get("department_id"),
        "department": emp["department"],
    }
    out.update(extra)
    return out


# --- tiles ------------------------------------------------------------------
def _headcount_block(employees: list) -> dict:
    active = [e for e in employees if e["is_active"]]
    by_dep: dict = {}
    for emp in active:
        key = (emp.get("department_id"), emp["department"])
        by_dep[key] = by_dep.get(key, 0) + 1
    by_department = [
        {"department_id": dep_id, "department": dep, "count": count}
        for (dep_id, dep), count in sorted(by_dep.items(), key=lambda kv: (-kv[1], kv[0][1]))
    ]
    return {"total": len(active), "by_department": by_department}


def _is_baja(emp: dict) -> bool:
    """Baja real = status distinto de activo con fecha de baja legible. Un
    activo con fecha de baja vieja (reingreso sin limpiar) sigue en plantilla."""
    return (not emp["is_active"]) and emp["departure"] is not None


def _movements_block(employees: list, date_from: date, date_to: date) -> dict:
    altas = [e for e in employees if e["admission"] is not None and date_from <= e["admission"] <= date_to]
    bajas = [e for e in employees if _is_baja(e) and date_from <= e["departure"] <= date_to]
    altas.sort(key=lambda e: (e["admission"], e["employee_id"]))
    bajas.sort(key=lambda e: (e["departure"], e["employee_id"]))
    return {
        "altas": len(altas),
        "bajas": len(bajas),
        "altas_ids": [e["employee_id"] for e in altas],
        "bajas_ids": [e["employee_id"] for e in bajas],
        "altas_items": [_emp_brief(e, date=_iso(e["admission"])) for e in altas],
        "bajas_items": [_emp_brief(e, date=_iso(e["departure"]), status=e.get("status")) for e in bajas],
    }


def _birthdays_block(employees: list, year: int, month: int) -> list:
    out = []
    for emp in employees:
        birth = emp["birth"]
        if not emp["is_active"] or birth is None or birth.month != month:
            continue
        day = min(birth.day, calendar.monthrange(year, month)[1])
        out.append(_emp_brief(emp, day=birth.day, date=_iso(date(year, month, day)), age=year - birth.year))
    out.sort(key=lambda item: (item["day"], item["name"]))
    return out


def _data_quality_block(employees: list) -> dict:
    unparsed = [
        {"emp_id": e["employee_id"], "name": e["full_name"], "status": e.get("status"), "departure_raw": e["departure_unparsed"]}
        for e in employees
        if e["departure_unparsed"]
    ]
    no_admission = [e["employee_id"] for e in employees if e["admission"] is None]
    no_birthday = [e["employee_id"] for e in employees if e["is_active"] and e["birth"] is None]
    stale_departure = [
        {"emp_id": e["employee_id"], "name": e["full_name"], "departure": _iso(e["departure"])}
        for e in employees
        if e["is_active"] and e["departure"] is not None
    ]
    inactive_no_departure = [e["employee_id"] for e in employees if not e["is_active"] and e["departure"] is None]
    return {
        "departures_unparsed": unparsed,
        "active_with_departure": stale_departure,
        "inactive_without_departure_ids": inactive_no_departure,
        "without_admission_ids": no_admission,
        "active_without_birthday_ids": no_birthday,
    }


def _medical_block(today: date, data_token):
    flag, error, result = get_active_medical_db(data_token)
    if not flag:
        return None, f"Exámenes médicos: {error}"
    # Un renglón por empleado: si hubiera más de un examen, gana el de fecha más reciente.
    per_emp: dict = {}
    for row in _rows(result):
        rec = dict(zip(MEDICAL_COLUMNS, row))
        rec["last_date"] = last_medical_date(rec.get("renovacion"))
        current = per_emp.get(rec["employee_id"])
        if current is None or (rec["last_date"] or date.min) > (current["last_date"] or date.min):
            per_emp[rec["employee_id"]] = rec

    buckets: dict = {
        key: {"count": 0, "ids": [], "items": []}
        for key in ("vencidos", "d30", "d60", "d90", "al_dia", "no_apto", "sin_periodo", "sin_examen")
    }

    def _put(key, rec, **extra):
        item = {
            "emp_id": rec["employee_id"],
            "name": _full_name(rec.get("name"), rec.get("l_name")),
            "examen_id": rec.get("examen_id"),
            "aptitude": rec.get("aptitude_actual"),
            "last_date": _iso(rec.get("last_date")),
        }
        item.update(extra)
        buckets[key]["ids"].append(rec["employee_id"])
        buckets[key]["items"].append(item)

    for rec in per_emp.values():
        if rec.get("examen_id") is None:
            _put("sin_examen", rec, due_date=None, days_left=None)
            continue
        due = medical_due(rec.get("aptitude_actual"), rec["last_date"], today)
        alert = due["alert"]
        if alert == "no_apto":
            _put("no_apto", rec, due_date=None, days_left=None)
            continue
        if alert == "sin_fecha":
            _put("sin_examen", rec, due_date=None, days_left=None)
            continue
        if alert == "sin_periodo":
            _put("sin_periodo", rec, due_date=None, days_left=None)
            continue
        days_left = due["days_left"]
        if days_left < 0:
            key = "vencidos"
        else:
            key = "al_dia"
            for bucket_key, top in MEDICAL_BUCKETS:
                if days_left <= top:
                    key = bucket_key
                    break
        _put(key, rec, due_date=_iso(due["due_date"]), days_left=days_left, period_days=due["period_days"])

    for bucket in buckets.values():
        bucket["items"].sort(key=lambda it: (it.get("days_left") if it.get("days_left") is not None else 10**6, it["name"]))
        bucket["ids"] = [it["emp_id"] for it in bucket["items"]]
        bucket["count"] = len(bucket["ids"])
    buckets["as_of"] = today.isoformat()
    buckets["total_activos"] = len(per_emp)
    buckets["period_days"] = {str(k): v for k, v in MEDICAL_PERIOD_DAYS.items()}
    return buckets, None


def _vacation_pending_days(status) -> tuple[bool, int | None]:
    """(es_pendiente, días) a partir del status libre del periodo."""
    text = str(status or "").strip()
    if not text:
        return False, None
    m = _VAC_PENDING_RE.match(text)
    if m:
        return True, (int(m.group(1)) if m.group(1) else None)
    m = _VAC_DIGITS_RE.match(text)
    if m:
        return True, int(m.group(1))
    return False, None


def _vacations_block(today: date, data_token):
    flag, error, result = get_active_vacations_db(data_token)
    if not flag:
        return None, f"Vacaciones: {error}"
    horizon = today + timedelta(days=VACATIONS_UPCOMING_DAYS)
    pending_items = []
    upcoming_items = []
    total_days = 0
    for row in _rows(result):
        rec = dict(zip(VACATION_COLUMNS, row))
        raw = rec.get("seniority")
        try:
            seniority = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except (TypeError, ValueError):
            seniority = {}
        if not isinstance(seniority, dict):
            seniority = {}
        name = _full_name(rec.get("name"), rec.get("l_name"))
        periods = []
        emp_days = 0
        days_unknown = False
        emp_upcoming = []
        for year_key, period in seniority.items():
            if not isinstance(period, dict):
                continue
            is_pending, days = _vacation_pending_days(period.get("status"))
            if is_pending:
                periods.append({"year": year_key, "status": period.get("status"), "days": days})
                if days is None:
                    days_unknown = True
                else:
                    emp_days += days
            for d in period.get("dates") or []:
                parsed = _parse_any_date(d)
                if parsed is not None and today <= parsed <= horizon:
                    emp_upcoming.append(parsed)
        if periods:
            total_days += emp_days
            pending_items.append(
                {
                    "emp_id": rec["emp_id"],
                    "name": name,
                    "date_admission": _iso(_parse_any_date(rec.get("date_admission"))),
                    "pending_days": emp_days,
                    "days_unknown": days_unknown,
                    "periods": periods,
                }
            )
        if emp_upcoming:
            upcoming_items.append({"emp_id": rec["emp_id"], "name": name, "dates": sorted(_iso(d) for d in emp_upcoming)})
    pending_items.sort(key=lambda it: (-it["pending_days"], it["name"]))
    upcoming_items.sort(key=lambda it: (it["dates"][0], it["name"]))
    return {
        "employees_with_pending": len(pending_items),
        "pending_days_total": total_days,
        "ids": [it["emp_id"] for it in pending_items],
        "items": pending_items,
        "next_30_days": {
            "count": len(upcoming_items),
            "ids": [it["emp_id"] for it in upcoming_items],
            "items": upcoming_items,
            "until": horizon.isoformat(),
        },
    }, None


def _quizzes_block(date_from: date, date_to: date, data_token):
    flag, error, result = get_quizz_stats_db(date_from.isoformat(), date_to.isoformat(), data_token)
    if not flag:
        return None, f"Encuestas: {error}"
    out = []
    for row in _rows(result):
        rec = dict(zip(QUIZZ_STATS_COLUMNS, row))
        assigned = _int(rec.get("assigned"))
        answered = _int(rec.get("answered"))
        out.append(
            {
                "type_q": rec.get("type_q"),
                "name": rec.get("name"),
                "model_status": rec.get("model_status"),
                "assigned": assigned,
                "answered": answered,
                "pending": max(assigned - answered, 0),
                "assigned_in_period": _int(rec.get("assigned_in_period")),
            }
        )
    return out, None


# --- API --------------------------------------------------------------------
def get_rrhh_summary_api(month_raw, data_token):
    today = _today()
    try:
        year, month = _parse_month(month_raw, today)
    except ValueError as e:
        return {"data": None, "msg": str(e), "error": None}, 400
    date_from, date_to = _month_bounds(year, month)

    employees, error = _load_employees(data_token)
    if employees is None:
        return {"data": None, "msg": "No se pudieron leer los empleados", "error": error}, 400

    errors = []
    medical, err = _medical_block(today, data_token)
    if err:
        errors.append(err)
    vacations, err = _vacations_block(today, data_token)
    if err:
        errors.append(err)
    quizzes, err = _quizzes_block(date_from, date_to, data_token)
    if err:
        errors.append(err)

    headcount = _headcount_block(employees)
    movements = _movements_block(employees, date_from, date_to)
    data = {
        "period": {"month": _month_key(date_from), "date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "as_of": today.isoformat()},
        "headcount": headcount,
        "movements_month": movements,
        "medical_expiring": medical,
        "vacations": vacations,
        "quizzes": quizzes,
        "birthdays_month": _birthdays_block(employees, year, month),
        "data_quality": _data_quality_block(employees),
    }
    msg = (
        f"Resumen RH {_month_key(date_from)}: {headcount['total']} activos, "
        f"{movements['altas']} altas y {movements['bajas']} bajas en el mes"
    )
    return {"data": data, "msg": msg, "error": errors or None}, 200


def _active_at(emp: dict, day: date) -> bool:
    """Empleado en plantilla al cierre de `day`: ingresó en o antes y, si hoy
    está inactivo, su fecha de baja es posterior. El status manda: un activo
    cuenta aunque arrastre una fecha de baja vieja; un inactivo sin fecha de
    baja legible no se puede ubicar y no cuenta."""
    admission = emp["admission"]
    if admission is None or admission > day:
        return False
    if emp["is_active"]:
        return True
    departure = emp["departure"]
    return departure is not None and departure > day


def _department_labels(employees: list, data_token):
    flag, error, result = get_departments_db(data_token)
    labels = []
    if flag:
        for row in _rows(result):
            rec = dict(zip(DEPARTMENT_COLUMNS, row))
            labels.append((rec["department_id"], rec["name"]))
    known = {dep_id for dep_id, _ in labels}
    for emp in employees:
        key = (emp.get("department_id"), emp["department"])
        if key[0] not in known:
            labels.append(key)
            known.add(key[0])
    return labels


def get_rrhh_series_api(data, data_token):
    metric = str(data.get("metric") or "").strip().lower()
    group_by = str(data.get("group_by") or "month").strip().lower()
    if metric not in SERIES_METRICS:
        return {"data": None, "msg": f"metric inválida: {metric or '(vacía)'}", "error": f"metric ∈ {list(SERIES_METRICS)}"}, 400
    if group_by not in SERIES_GROUP_BY:
        return {"data": None, "msg": f"group_by inválido: {group_by}", "error": f"group_by ∈ {list(SERIES_GROUP_BY)}"}, 400
    date_from = _parse_any_date(data.get("date_from"))
    date_to = _parse_any_date(data.get("date_to"))
    if date_from is None or date_to is None:
        return {"data": None, "msg": "date_from y date_to son obligatorias en formato YYYY-MM-DD", "error": None}, 400
    if date_from > date_to:
        return {"data": None, "msg": "date_from no puede ser posterior a date_to", "error": None}, 400
    months = _months_between(date_from, date_to)
    if len(months) > SERIES_MAX_MONTHS:
        return {"data": None, "msg": f"Rango demasiado amplio: máximo {SERIES_MAX_MONTHS} meses", "error": None}, 400

    employees, error = _load_employees(data_token)
    if employees is None:
        return {"data": None, "msg": "No se pudieron leer los empleados", "error": error}, 400

    labels: list = []
    series: list = []
    if group_by == "month":
        labels = [f"{y:04d}-{m:02d}" for y, m in months]
        if metric == "altas_bajas":
            altas = [0] * len(months)
            bajas = [0] * len(months)
            index = {key: i for i, key in enumerate(labels)}
            for emp in employees:
                adm, dep = emp["admission"], emp["departure"]
                if adm is not None and date_from <= adm <= date_to:
                    altas[index[_month_key(adm)]] += 1
                if _is_baja(emp) and date_from <= dep <= date_to:
                    bajas[index[_month_key(dep)]] += 1
            series = [{"name": "altas", "values": altas}, {"name": "bajas", "values": bajas}]
        else:
            values = []
            for y, m in months:
                _, month_end = _month_bounds(y, m)
                values.append(sum(1 for e in employees if _active_at(e, month_end)))
            series = [{"name": "activos", "values": values}]
    else:
        dep_labels = _department_labels(employees, data_token)
        labels = [name for _, name in dep_labels]
        index = {dep_id: i for i, (dep_id, _) in enumerate(dep_labels)}
        if metric == "altas_bajas":
            altas = [0] * len(labels)
            bajas = [0] * len(labels)
            for emp in employees:
                pos = index.get(emp.get("department_id"))
                if pos is None:
                    continue
                adm, dep = emp["admission"], emp["departure"]
                if adm is not None and date_from <= adm <= date_to:
                    altas[pos] += 1
                if _is_baja(emp) and date_from <= dep <= date_to:
                    bajas[pos] += 1
            series = [{"name": "altas", "values": altas}, {"name": "bajas", "values": bajas}]
        else:
            values = [0] * len(labels)
            for emp in employees:
                pos = index.get(emp.get("department_id"))
                if pos is not None and _active_at(emp, date_to):
                    values[pos] += 1
            series = [{"name": "activos", "values": values}]

    data_out = {
        "metric": metric,
        "group_by": group_by,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "labels": labels,
        "series": series,
    }
    msg = f"{metric} por {'mes' if group_by == 'month' else 'departamento'}, {date_from} → {date_to} ({len(labels)} puntos)"
    return {"data": data_out, "msg": msg, "error": None}, 200
