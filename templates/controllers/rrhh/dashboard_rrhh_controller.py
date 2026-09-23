# -*- coding: utf-8 -*-
"""
Dashboard de RH — lecturas agregadas (docs/dashboard_rrhh.md).

Todas son SELECT sin efectos; los agregados son chicos (~100 empleados), así
que las reglas de negocio (parseo de fechas de baja, buckets de vencimiento,
días pendientes de vacaciones) viven en el midleware MD_DashboardRRHH.py y
aquí solo se traen las filas. Sin caché (plan_mes_2.md, Anexo D).
"""
__author__ = "Edisson Naula"
__date__ = "$ 10/sep./2026  at 12:00 $"

from templates.database.connection import execute_sql

# Catálogo de departamentos (labels estables para el group_by=department).
DEPARTMENT_COLUMNS = ("department_id", "name")

# Ciclo de vida de TODOS los empleados (activos e inactivos): con esto el
# midleware arma altas/bajas por mes, cumpleaños y el headcount histórico.
EMPLOYEE_LIFECYCLE_COLUMNS = (
    "employee_id",
    "name",
    "l_name",
    "department_id",
    "department",
    "status",
    "date_admission",
    "departure_date",  # departure->>'$.date' crudo: formatos mezclados, se parsea en Python
    "birthday",
)

# Exámenes médicos de los empleados ACTIVOS (LEFT JOIN: sin examen → NULLs).
MEDICAL_COLUMNS = (
    "employee_id",
    "name",
    "l_name",
    "examen_id",
    "aptitude_actual",
    "renovacion",  # JSON lista de timestamps "YYYY-MM-DD HH:MM:SS"
)

# Vacaciones de los empleados ACTIVOS.
VACATION_COLUMNS = ("emp_id", "name", "l_name", "date_admission", "seniority")

# Encuestas: un renglón por modelo con conteos de sus tasks.
QUIZZ_STATS_COLUMNS = (
    "type_q",
    "name",
    "model_status",
    "assigned",
    "answered",
    "assigned_in_period",
)


def get_departments_db(data_token):
    sql = "SELECT department_id, name FROM sql_telintec.departments ORDER BY department_id"
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_employees_lifecycle_db(data_token):
    sql = (
        "SELECT e.employee_id, e.name, e.l_name, e.department_id, d.name, "
        "e.status, e.date_admission, e.departure->>'$.date', e.birthday "
        "FROM sql_telintec.employees e "
        "LEFT JOIN sql_telintec.departments d ON d.department_id = e.department_id "
        "ORDER BY e.employee_id"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_active_medical_db(data_token):
    sql = (
        "SELECT e.employee_id, e.name, e.l_name, em.examen_id, em.aptitude_actual, em.renovacion "
        "FROM sql_telintec.employees e "
        "LEFT JOIN sql_telintec_mod_rrhh.examenes_med em ON em.empleado_id = e.employee_id "
        "WHERE e.status = 'activo' "
        "ORDER BY e.employee_id, em.examen_id"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_active_vacations_db(data_token):
    sql = (
        "SELECT v.emp_id, e.name, e.l_name, e.date_admission, v.seniority "
        "FROM sql_telintec_mod_rrhh.vacations v "
        "INNER JOIN sql_telintec.employees e ON e.employee_id = v.emp_id "
        "WHERE e.status = 'activo' "
        "ORDER BY v.emp_id"
    )
    flag, error, result = execute_sql(sql, None, 5, data_token)
    return flag, error, result


def get_quizz_stats_db(date_from, date_to, data_token):
    """Un renglón por modelo de encuesta (todos los status) con: tasks
    asignadas, contestadas (data_raw no vacío, mismo criterio que la
    migración de versiones) y asignadas dentro del periodo [date_from,
    date_to] inclusivo. Las tasks de CONTROL de eva 360 no son encuestas a
    contestar y se excluyen."""
    sql = (
        "SELECT qm.type_q, qm.name, qm.status, "
        "COUNT(t.id), "
        "COALESCE(SUM(JSON_LENGTH(t.data_raw) > 0), 0), "
        "COALESCE(SUM(DATE(t.timestamp) BETWEEN %s AND %s), 0) "
        "FROM sql_telintec_mod_rrhh.quizz_models qm "
        "LEFT JOIN sql_telintec_mod_rrhh.quizz_tasks t "
        "ON CAST(t.body->>'$.metadata.type_quizz' AS UNSIGNED) = qm.type_q "
        "AND COALESCE(t.body->>'$.metadata.eva360_kind', '') <> 'control' "
        "GROUP BY qm.type_q, qm.name, qm.status "
        "ORDER BY qm.type_q"
    )
    val = (date_from, date_to)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result
