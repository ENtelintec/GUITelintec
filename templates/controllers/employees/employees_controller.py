# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 18:20 $'

from templates.database.connection import execute_sql, execute_sql_multiple


def get_employees(limit=(0, 100)) -> list[list]:
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
        "LIMIT  %s ")
    val = (limit[1],)
    flag, e, my_result = execute_sql(sql, val, 2)
    out = my_result if my_result is not None else []
    return out


def new_employee(name, lastname, curp, phone, modality, department, contract, entry_date,
                 rfc, nss, puesto, estatus, departure, birthday, legajo, email, emergency):
    sql = ("INSERT INTO sql_telintec.employees (name, l_name, curp, phone_number, email, department_id,"
           " contrato, date_admission, rfc, nss, emergency_contact, modality, puesto, status, "
           " departure, birthday, legajo) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    values = (name.lower(), lastname.lower(), curp, phone, email, department,
              contract, entry_date, rfc, nss, emergency, modality, puesto, estatus,
              departure, birthday, legajo)
    flag, e, out = execute_sql(sql, values, 4)
    return flag, e, out


def update_employee(employee_id, name, lastname, curp, phone, modality, department, contract, entry_date,
                    rfc, nss, puesto, estatus, departure, birthday, legajo, email, emergency):
    sql = ("UPDATE sql_telintec.employees SET name = %s, l_name = %s, curp = %s, phone_number = %s, email = %s, department_id = %s,"
           "contrato = %s, date_admission = %s, rfc = %s, nss = %s, emergency_contact = %s, modality = %s , "
           "puesto = %s, status = %s, departure = %s, birthday = %s, legajo = %s "
           "WHERE employee_id = %s")
    values = (name.lower(), lastname.lower(), curp, phone, email, department,
              contract, entry_date, rfc, nss, emergency, modality, puesto,
              estatus, departure, birthday, legajo, employee_id)
    flag, e, out = execute_sql(sql, values, 3)
    return flag, e, out


def delete_employee(employee_id: int):
    try:
        employee_id = int(employee_id)
    except ValueError:
        return False, None, None
    sql = "DELETE FROM sql_telintec.employees WHERE employee_id = %s"
    values = (employee_id,)
    flag, e, out = execute_sql(sql, values, 3)
    return flag, e, out


def get_employee_id_name(name: str) -> tuple[None, str] | tuple[int, str]:
    """
        Get the id of the employee
        :param name: name of the employee
        :return: id of the employee
        """
    sql = ("SELECT employee_id, name, l_name "
           "FROM sql_telintec.employees "
           "WHERE "
           "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) AND "
           "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )")
    # lowercase names
    name = name.lower()
    values = (name, name)
    flag, e, out = execute_sql(sql, values, 1)
    if e is not None or len(out) == 0:
        return None, str(e)
    else:
        return out[0], f"{out[1].title()} {out[2].title()}"


def get_employees_w_status(status: str, quantity: int, date: str):
    columns = ("employee_id", "name", "l_name", "date_admission", "status")
    sql = ("SELECT employee_id, name, l_name, date_admission, status "
           "FROM sql_telintec.employees "
           "WHERE status LIKE %s ")
    if date is not None:
        sql = sql + " AND date_admission >= %s "
    sql = sql + " ORDER BY date_admission  LIMIT %s "
    val = (status, date, quantity)
    flag, error, result = execute_sql(sql, val, 2)
    return flag, error, result, columns


def get_employee_info(id_e: int):
    columns = ("employee_id", "name", "l_name", "date_admission", "status", "department", "phone", "email", "contrato")
    sql = ("SELECT employee_id, name, l_name, date_admission, status, department_id, phone_number, email, contrato "
           "FROM sql_telintec.employees "
           "WHERE employee_id = %s")
    val = (id_e,)
    flag, error, result = execute_sql(sql, val, 1)
    return flag, error, result, columns


def get_id_employee(name: str) -> None | int:
    """
    Get the id of the employee
    :param name: name of the employee
    :return: id of the employee
    """
    sql = ("SELECT employee_id "
           "FROM sql_telintec.employees "
           "WHERE "
           "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) AND "
           "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )")
    # lowercase names
    name = name.lower()
    values = (name, name)
    flag, e, out = execute_sql(sql, values, 1)
    # print(name, flag, e, out)
    if e is not None or len(out) == 0:
        return None
    else:
        return out[0]


def get_name_employee(id_employee: int) -> None | str:
    """
    Get the name of the employee
    :param id_employee: id of the employee
    :return: name of the employee
    """
    sql = ("SELECT name, l_name "
           "FROM sql_telintec.employees "
           "WHERE employee_id = %s")
    values = (id_employee,)
    flag, e, out = execute_sql(sql, values, 1)
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
    sql = ("SELECT employee_id, name, l_name, puesto, date_admission, departure "
           "FROM sql_telintec.employees "
           "WHERE department_id = %s")
    if is_all:
        sql = ("SELECT employee_id, name, l_name, puesto, date_admission, departure "
               "FROM sql_telintec.employees")
        flag, e, out = execute_sql(sql, None, 5)
    else:
        values = (department,)
        flag, e, out = execute_sql(sql, values, 5)
    return flag, e, out


def get_employees_op_names():
    sql = ("SELECT employee_id, name, l_name, contrato "
           "FROM sql_telintec.employees "
           "WHERE  department_id = 2 and status = 'activo' ")
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
    sql = ("SELECT employee_id "
           "FROM sql_telintec.employees "
           "WHERE "
           "MATCH(l_name) AGAINST (%s IN NATURAL LANGUAGE MODE ) AND "
           "MATCH(name) AGAINST (%s IN NATURAL LANGUAGE MODE )")
    # lowercase names
    for i, name in enumerate(names):
        names[i] = name.lower()
    values = [names, names]
    flag, e, out = execute_sql_multiple(sql, values, 1)
    if e is not None:
        return None
    else:
        return out


def get_sm_employees():
    sql = ("SELECT employee_id, name, l_name "
           "FROM sql_telintec.employees "
           "WHERE status = 'activo' ")
    flag, error, result = execute_sql(sql, None, 5)
    return flag, error, result


def get_all_employees_active():
    sql = ("SELECT employee_id, name, l_name, date_admission "
           "FROM sql_telintec.employees "
           "WHERE status = 'activo'")
    flag, error, result = execute_sql(sql, type_sql=5)
    return flag, error, result


def get_all_data_employees(status: str):
    if "all" in status.lower():
        status = "%"
    elif "inactivo" in status.lower():
        status = "inactivo"
    else:
        status = "activo"
    sql = ("SELECT "
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
           "sql_telintec.examenes_med.examen_id, "
           "employees.birthday, "
           "employees.legajo "
           "FROM sql_telintec.employees "
           "LEFT JOIN sql_telintec.departments "
           "ON sql_telintec.employees.department_id = sql_telintec.departments.department_id "
           "LEFT JOIN sql_telintec.examenes_med "
           "ON (sql_telintec.employees.employee_id = sql_telintec.examenes_med.empleado_id) "
           "WHERE employees.status LIKE %s ")
    val = (status,)
    flag, error, result = execute_sql(sql, val, type_sql=2)
    return flag, error, result


def get_all_data_employee(id_employee: int):
    sql = ("SELECT "
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
           "sql_telintec.examenes_med.examen_id, "
           "employees.birthday, "
           "employees.legajo "
           "FROM sql_telintec.employees "
           "LEFT JOIN sql_telintec.departments "
           "ON sql_telintec.employees.department_id = sql_telintec.departments.department_id "
           "LEFT JOIN sql_telintec.examenes_med "
           "ON (sql_telintec.employees.employee_id = sql_telintec.examenes_med.empleado_id)"
           "WHERE employee_id = %s")
    val = (id_employee,)
    flag, error, result = execute_sql(sql, val, type_sql=1)
    return flag, error, result


def get_contract_employes(emp_id):
    sql = ("SELECT contrato "
           "FROM sql_telintec.employees "
           "WHERE employee_id = %s")
    val = (emp_id,)
    flag, error, result = execute_sql(sql, val, type_sql=1)
    return flag, error, result
