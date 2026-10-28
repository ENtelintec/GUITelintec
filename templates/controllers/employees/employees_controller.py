# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/may./2024  at 18:20 $"

import json

from templates.database.connection import execute_sql, execute_sql_multiple


def get_employees( data_token,limit=(0, 100)):
    sql = (
        "SELECT "
        "employees.employee_id, "
        "UPPER(employees.name), "
        "UPPER(employees.l_name), "
        "employees.curp, "
        "employees.phone_number, "
        "employees.modality, "
        "departments.name, "
        "employees.contrato, "
        "employees.date_admission, "
        "employees.rfc, "
        "employees.nss, "
        "employees.puesto, "
        "employees.status, "
        "employees.departure, "
        "employees.birthday, "
        "employees.legajo, "
        "employees.email, "
        "employees.emergency_contact "
        "FROM sql_telintec.employees "
        "INNER JOIN sql_telintec.departments ON employees.department_id = departments.department_id "
        "ORDER BY employees.employee_id "
        "LIMIT  %s "
    )
    val = (limit[1],)
    flag, e, my_result = execute_sql(sql, val, 2, data_token)
    out = my_result if my_result is not None else []
    if not (isinstance(out, list) or isinstance(out, tuple)):
        return []
    return out


def new_employee(
    name,
    lastname,
    curp,
    phone,
    modality,
    department,
    contract,
    entry_date,
    rfc,
    nss,
    puesto,
    estatus,
    departure,
    birthday,
    legajo,
    email,
    emergency, data_token,
    id_leader=0,
):
    extra_info = {"id_leader": id_leader}
    sql = (
        "INSERT INTO sql_telintec.employees (name, l_name, curp, phone_number, email, department_id,"
        " contrato, date_admission, rfc, nss, emergency_contact, modality, puesto, status, "
        " departure, birthday, legajo, extra_info) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    values = (
        name.upper(),
        lastname.upper(),
        curp,
        phone,
        email,
        department,
        contract,
        entry_date,
        rfc,
        nss,
        emergency,
        modality,
        puesto,
        estatus,
        departure,
        birthday,
        legajo,
        json.dumps(extra_info),
    )
    flag, e, out = execute_sql(sql, values, 4, data_token)
    return flag, e, out


def update_employee(
    employee_id,
    name,
    lastname,
    curp,
    phone,
    modality,
    department,
    contract,
    entry_date,
    rfc,
    nss,
    puesto,
    estatus,
    departure,
    birthday,
    legajo,
    email,
    emergency, data_token,
    id_leader=0,
):
    sql = (
        "UPDATE sql_telintec.employees SET name = %s, l_name = %s, curp = %s, phone_number = %s, email = %s, department_id = %s,"
        "contrato = %s, date_admission = %s, rfc = %s, nss = %s, emergency_contact = %s, modality = %s , "
        "puesto = %s, status = %s, departure = %s, birthday = %s, legajo = %s, extra_info = JSON_REPLACE(extra_info, '$.id_leader', %s) "
        "WHERE employee_id = %s"
    )
    values = (
        name.upper(),
        lastname.upper(),
        curp,
        phone,
        email,
        department,
        contract,
        entry_date,
        rfc,
        nss,
        emergency,
        modality,
        puesto,
        estatus,
        departure,
        birthday,
        legajo,
        id_leader,
        employee_id,
    )
    flag, e, out = execute_sql(sql, values, 3, data_token)
    return flag, e, out


def delete_employee(employee_id: int, data_token):
    try:
        employee_id = int(employee_id)
    except ValueError:
        return False, None, None
    sql = "DELETE FROM sql_telintec.employees WHERE employee_id = %s"
    values = (employee_id,)
    flag, e, out = execute_sql(sql, values, 3, data_token)
    return flag, e, out


def terminate_employee_db(employee_id: int, departure: str, data_token):
    sql = "UPDATE sql_telintec.employees SET status = 'inactivo', departure = %s WHERE employee_id = %s"
    values = (departure, employee_id)
    flag, e, out = execute_sql(sql, values, 3, data_token)
    return flag, e, out


def get_employee_id_name(name: str, data_token) -> tuple[None, str] | tuple[int, str]:
    """
    Get the id of the employee
    :param name: name of the employee
    :return: id of the employee
    """
    sql = (
        "SELECT employee_id, name, l_name "
        "FROM sql_telintec.employees "
        "WHERE "
        "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) AND "
        "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )"
    )
    name = name.upper()
    values = (name, name)
    flag, e, out = execute_sql(sql, values, 1, data_token)
    if not isinstance(out, tuple):
        return None, "Not data found or error"
    # execute_sql devuelve el error como str ("None" cuando no hay error):
    # comparar con `is not None` hacia que esta funcion SIEMPRE devolviera
    # None (corregido 2026-09-07, lo destapo el extract de nomina).
    if (e not in (None, "None", "")) or len(out) == 0:
        return None, e
    else:
        return out[0], f"{str(out[1]).title()} {str(out[2]).title()}"


def get_employees_w_status(status: str, quantity: int, date: str, data_token):
    columns = ("employee_id", "name", "l_name", "date_admission", "status")
    sql = (
        "SELECT employee_id, name, l_name, date_admission, status "
        "FROM sql_telintec.employees "
        "WHERE status LIKE %s "
    )
    if date is not None:
        sql = sql + " AND date_admission >= %s "
    sql = sql + " ORDER BY date_admission  LIMIT %s "
    val = (status, date, quantity)
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result, columns


def get_employees_name_puesto(ids, data_token):
    """(employee_id, name, l_name, puesto) de una lista de ids; ids vacios ->
    lista vacia sin ir a la BD."""
    ids = sorted({int(i) for i in ids if i})
    if not ids:
        return True, None, []
    placeholders = ", ".join(["%s"] * len(ids))
    sql = (
        "SELECT employee_id, name, l_name, puesto "
        "FROM sql_telintec.employees "
        f"WHERE employee_id IN ({placeholders})"
    )
    flag, error, result = execute_sql(sql, tuple(ids), 2, data_token)
    return flag, error, result


def get_employee_info(id_e: int, data_token):
    columns = (
        "employee_id",
        "name",
        "l_name",
        "date_admission",
        "status",
        "department",
        "phone",
        "email",
        "contrato",
    )
    sql = (
        "SELECT employee_id, name, l_name, date_admission, status, department_id, phone_number, email, contrato "
        "FROM sql_telintec.employees "
        "WHERE employee_id = %s"
    )
    val = (id_e,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result, columns


_PAYROLL_MATCH_SQL = {
    "rfc": (
        "SELECT employee_id, name, l_name, status = 'activo' FROM sql_telintec.employees "
        "WHERE UPPER(TRIM(RFC)) = %s ORDER BY (status = 'activo') DESC, employee_id DESC"
    ),
    "curp": (
        "SELECT employee_id, name, l_name, status = 'activo' FROM sql_telintec.employees "
        "WHERE UPPER(TRIM(CURP)) = %s ORDER BY (status = 'activo') DESC, employee_id DESC"
    ),
}


def find_employee_for_payroll(rfc, curp, full_name, data_token):
    """Resuelve el empleado de un CFDI de nomina para SUGERIRLO en la carga
    por periodo (docs/nomina_gestion_archivos_y_notificacion.md, 2026-10-28):
    1) RFC exacto; 2) CURP exacta (en ambos gana el activo; dos activos con el
    mismo dato no deciden); 3) nombre del receptor, fulltext solo entre
    activos, el de mayor relevancia y sin empate. El NumEmpleado del CFDI es
    el numero del proveedor de nomina, no el employee_id: no se usa.
    -> (emp_id | None, match_by | None, nombre_en_bd | None). Nunca truena."""
    for match_by, value in (("rfc", rfc), ("curp", curp)):
        value = str(value or "").strip().upper()
        if not value:
            continue
        flag, _, out = execute_sql(_PAYROLL_MATCH_SQL[match_by], (value,), 2, data_token)
        if not (flag and isinstance(out, list) and out):
            continue
        if len([row for row in out if row[3]]) > 1:
            continue
        return int(out[0][0]), match_by, f"{str(out[0][1]).title()} {str(out[0][2]).title()}"
    name = str(full_name or "").strip().upper()
    if not name:
        return None, None, None
    sql = (
        "SELECT employee_id, name, l_name, "
        "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE) "
        "+ MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE) AS score "
        "FROM sql_telintec.employees "
        "WHERE MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE) "
        "AND MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE) "
        "AND status = 'activo' "
        "ORDER BY score DESC, employee_id DESC LIMIT 2"
    )
    flag, _, out = execute_sql(sql, (name, name, name, name), 2, data_token)
    if not (flag and isinstance(out, list) and out):
        return None, None, None
    if len(out) > 1 and float(out[0][3]) == float(out[1][3]):
        return None, None, None
    return int(out[0][0]), "nombre", f"{str(out[0][1]).title()} {str(out[0][2]).title()}"


def get_id_employee(name: str) -> None | int:
    """
    Get the id of the employee
    :param name: name of the employee
    :return: id of the employee
    """
    sql = (
        "SELECT employee_id "
        "FROM sql_telintec.employees "
        "WHERE "
        "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) AND "
        "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )"
    )
    name = name.upper()
    values = (name, name)
    flag, e, out = execute_sql(sql, values, 1)
    if not isinstance(out, tuple):
        return None
    if (e not in (None, "None", "")) or len(out) == 0:  # e es str ("None" sin error)
        return None
    else:
        return out[0]


def get_name_employee(id_employee: int) -> None | str:
    """
    Get the name of the employee
    :param id_employee: id of the employee
    :return: name of the employee
    """
    sql = "SELECT name, l_name FROM sql_telintec.employees WHERE employee_id = %s"
    values = (id_employee,)
    flag, e, out = execute_sql(sql, values, 1)
    if not isinstance(out, tuple):
        return None
    if e is not None or len(out) == 0:
        return None
    else:
        return f"{out[0].upper()} {out[1].upper()}"


def get_id_name_employee(department: int, is_all=False):
    """
    :param department:
    :param is_all:
    :return:
    """
    sql = (
        "SELECT employee_id, name, l_name, puesto, date_admission, departure "
        "FROM sql_telintec.employees "
        "WHERE department_id = %s"
    )
    if is_all:
        sql = (
            "SELECT employee_id, name, l_name, puesto, date_admission, departure "
            "FROM sql_telintec.employees"
        )
        flag, e, out = execute_sql(sql, None, 5)
    else:
        values = (department,)
        flag, e, out = execute_sql(sql, values, 5)
    return flag, e, out


def get_employees_op_names():
    sql = (
        "SELECT employee_id, name, l_name, contrato "
        "FROM sql_telintec.employees "
        "WHERE  department_id = 2 and status = 'activo' "
    )
    flag, e, out = execute_sql(sql, None, 5)
    if e is not None:
        return False, e, None
    else:
        return flag, e, out


def get_ids_employees(names: list):
    """
    Get the id of the employee
    :param names: list name of the employee
    :return: id of the employee
    """
    sql = (
        "SELECT employee_id "
        "FROM sql_telintec.employees "
        "WHERE "
        "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) AND "
        "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )"
    )
    for i, name in enumerate(names):
        names[i] = name.upper()
    values = [names, names]
    flag, e, out = execute_sql_multiple(sql, values, 1)
    if e is not None:
        return None
    else:
        return out


def get_sm_employees():
    sql = (
        "SELECT employee_id, name, l_name "
        "FROM sql_telintec.employees "
        "WHERE status = 'activo' "
    )
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_employees_active():
    sql = (
        "SELECT employee_id, name, l_name, date_admission "
        "FROM sql_telintec.employees "
        "WHERE status = 'activo'"
    )
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result


def get_all_data_employees(status: str, data_token=None):
    if "all" in status.lower():
        status = "%"
    elif "inactivo" in status.lower():
        status = "inactivo"
    else:
        status = "activo"
    sql = """
    SELECT 
        e.employee_id,
        e.name,
        e.l_name,
        e.phone_number,
        d.name AS department_name,
        e.modality,
        e.email,
        e.contrato,
        e.date_admission,
        e.rfc,
        e.curp,
        e.nss,
        e.emergency_contact,
        e.puesto,
        e.status,
        e.departure,
        em.examen_id, 
        e.birthday,
        e.legajo,
        e.extra_info,
        e.department_id,
        GROUP_CONCAT(u.usernames) AS usernames -- todos los usuarios en una sola columna
    FROM sql_telintec.employees e
    LEFT JOIN sql_telintec.departments d
        ON e.department_id = d.department_id
    LEFT JOIN sql_telintec_mod_rrhh.examenes_med em
        ON e.employee_id = em.empleado_id
    LEFT JOIN sql_telintec.users_system u
        ON e.employee_id = u.emp_id
    WHERE e.status LIKE %s
    GROUP BY e.employee_id, e.name, e.l_name, e.phone_number, d.name,
            e.modality, e.email, e.contrato, e.date_admission, e.rfc, e.curp,
            e.nss, e.emergency_contact, e.puesto, e.status, e.departure,
            e.birthday, e.legajo, e.extra_info, e.department_id
    ORDER BY e.name, e.l_name;

    """
    val = (status,)
    flag, error, result = execute_sql(sql, val, type_sql=2, data_token=data_token)
    return flag, error, result


def get_employees_directory(status: str, data_token):
    """Directorio de empleados con datos no confidenciales (permiso Common)."""
    if "all" in status.lower():
        status = "%"
    elif "inactivo" in status.lower():
        status = "inactivo"
    else:
        status = "activo"
    sql = """
    SELECT
        e.employee_id,
        e.name,
        e.l_name,
        e.phone_number,
        d.name AS department_name,
        e.modality,
        e.email,
        e.contrato,
        e.puesto,
        e.status,
        e.extra_info,
        e.department_id,
        GROUP_CONCAT(u.usernames) AS usernames
    FROM sql_telintec.employees e
    LEFT JOIN sql_telintec.departments d
        ON e.department_id = d.department_id
    LEFT JOIN sql_telintec.users_system u
        ON e.employee_id = u.emp_id
    WHERE e.status LIKE %s
    GROUP BY e.employee_id, e.name, e.l_name, e.phone_number, d.name,
            e.modality, e.email, e.contrato, e.puesto, e.status,
            e.extra_info, e.department_id
    ORDER BY e.name, e.l_name;
    """
    val = (status,)
    flag, error, result = execute_sql(sql, val, type_sql=2, data_token=data_token)
    return flag, error, result


def get_all_data_employee(id_employee: int, data_token):
    sql = (
        "SELECT "
        "employees.employee_id, "
        "employees.name, "
        "employees.l_name, "
        "employees.phone_number, "
        "sql_telintec.departments.name, "
        "employees.modality, "
        "employees.email, "
        "employees.contrato, "
        "employees.date_admission, "
        "employees.rfc, "
        "employees.curp, "
        "employees.nss, "
        "employees.emergency_contact, "
        "employees.puesto, "
        "employees.status, "
        "employees.departure, "
        "sql_telintec_mod_rrhh.examenes_med.examen_id, "
        "employees.birthday, "
        "employees.legajo, "
        "employees.department_id "
        "FROM sql_telintec.employees "
        "LEFT JOIN sql_telintec.departments "
        "ON sql_telintec.employees.department_id = sql_telintec.departments.department_id "
        "LEFT JOIN sql_telintec_mod_rrhh.examenes_med "
        "ON (sql_telintec.employees.employee_id = sql_telintec_mod_rrhh.examenes_med.empleado_id)"
        "WHERE employee_id = %s"
    )
    val = (id_employee,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def get_contract_employes(emp_id, data_token):
    sql = "SELECT contrato FROM sql_telintec.employees WHERE employee_id = %s"
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def get_emp_contract(contract: str, data_token):
    sql = (
        "SELECT employee_id, name, l_name "
        "FROM sql_telintec.employees "
        "WHERE UPPER(contrato) LIKE %s OR LOWER(contrato) LIKE %s"
    )
    val = (contract.upper(), contract.lower())
    flag, error, result = execute_sql(sql, val, 2, data_token)
    if not isinstance(result, list):
        return False, "No contract found or error", []
    return flag, error, result


def get_emp_mail(emp_id, data_token):
    sql = "SELECT email FROM sql_telintec.employees WHERE employee_id = %s"
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result


def get_active_employees_by_puesto(department_id: int, puesto_prefixes: tuple, data_token):
    """Empleados activos del departamento cuyo puesto empieza con alguno de los
    prefijos (sin distinguir mayusculas): (employee_id, name, l_name, puesto, email)."""
    conditions = " OR ".join(["UPPER(TRIM(puesto)) LIKE %s"] * len(puesto_prefixes))
    sql = (
        "SELECT employee_id, name, l_name, puesto, email FROM sql_telintec.employees "
        f"WHERE status = 'activo' AND department_id = %s AND ({conditions}) ORDER BY employee_id"
    )
    val = (department_id, *[f"{prefix.upper()}%" for prefix in puesto_prefixes])
    flag, error, result = execute_sql(sql, val, 2, data_token)
    return flag, error, result


def get_contracts_operaciones(data_token):
    sql = "SELECT contrato FROM sql_telintec.employees WHERE department_id = 2"
    flag, error, result = execute_sql(sql, type_sql=5, data_token=data_token)
    return flag, error, result


def test_id_employee(emp_id: int, data_token):
    sql = (
        "SELECT employee_id, status, contrato "
        "FROM sql_telintec.employees "
        "WHERE employee_id = %s"
    )
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, 1, data_token)
    return flag, error, result
