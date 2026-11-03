# -*- coding: utf-8 -*-
from datetime import timedelta

__author__ = "Edisson Naula"
__date__ = "$ 28/jun./2024  at 16:28 $"

import io
import json
import os
import uuid
import zipfile
from datetime import datetime

import boto3
import pytz
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from werkzeug.utils import secure_filename

from static.constants import (
    format_date,
    format_timestamps,
    log_file_rh,
    log_file_users,
    quizz_out_path,
    secrets,
    timezone_software,
)
from templates.controllers.employees.em_controller import (
    get_all_examenes,
    get_employees_without_records,
    insert_new_exam_med,
    update_aptitud_renovacion,
)
from templates.controllers.employees.employees_controller import (
    find_employee_for_payroll,
    get_employee_info,
    new_employee,
    terminate_employee_db,
    update_employee,
    test_id_employee,
)
from templates.controllers.employees.us_controller import (
    disable_users_by_emp_id,
    get_user_by_emp_id,
    get_users_by_emp_id,
)
from templates.resources.methods.Functions_Aux_RH import join_emails, last_medical_date, medical_due, normalize_emails, split_emails
from templates.resources.methods.Functions_Aux_S3 import s3_can_delete, s3_env_key
from templates.controllers.notifications.Notifications_controller import (
    insert_notification,
)
from templates.controllers.employees.vacations_controller import (
    get_vacations_data_emp,
    insert_vacation,
    update_registry_vac,
)
from templates.controllers.misc.tasks_controller import (
    get_all_tasks_by_status,
    get_task_by_id_emp,
    update_task,
)
from templates.controllers.rrhh.quizz_models_controller import get_quizz_model_names_db
from templates.controllers.payroll.payroll_controller import (
    get_payrolls,
    update_payroll,
    update_payroll_employees,
)
from templates.Functions_Utils import create_notification_permission
from templates.misc.Functions_Mail import is_ses_configured, send_email_ses
from templates.misc.Functions_AuxFiles import get_data_xml_file_nomina
from templates.misc.Functions_Files import write_log_file


def _employee_email_column(info: dict):
    """Correos del alta/edicion -> (string para employees.email, envelope 400 | None).
    Toma `emails` (lista) si viene con algo; si no, `email` (string, puede traer comas).
    Sin correos es valido (cadena vacia); un token que no es correo -> 400 listandolo."""
    raw = info.get("emails") or info.get("email") or ""
    valid, invalid = normalize_emails(raw)
    if invalid:
        return None, {"data": None, "msg": "Correo inválido", "error": [f"emails: {tok} no es un correo válido" for tok in invalid]}
    return join_emails(valid), None


def create_new_employee_db(data, data_token):
    email_column, err = _employee_email_column(data["info"])
    if err:
        return err, 400
    flag, error, result = new_employee(
        data["info"]["name"],
        data["info"]["lastname"],
        data["info"]["curp"],
        data["info"]["phone"],
        data["info"]["modality"],
        data["info"]["dep"],
        data["info"]["contract"],
        data["info"]["admission"],
        data["info"]["rfc"],
        data["info"]["nss"],
        data["info"]["position"],
        data["info"]["status"],
        data["info"]["departure"],
        data["info"]["birthday"],
        data["info"]["legajo"],
        email_column,
        data["info"]["emergency"],
        data_token,
        data["info"]["id_leader"],
    )
    if flag:
        return {"data": {"id_employee": result}, "msg": f"Empleado creado correctamente (ID {result})", "error": None}, 201
    else:
        return {"data": None, "msg": "No se pudo crear el empleado", "error": error}, 400


def _employee_status(emp_id, data_token) -> str:
    """status actual del empleado en minúsculas ("" si no existe o falla)."""
    flag, _error, row = test_id_employee(int(emp_id), data_token)
    if not flag or not isinstance(row, (list, tuple)) or len(row) < 2 or row[1] is None:
        return ""
    return str(row[1]).strip().lower()


def _usernames_with_state(rows, is_active: int) -> list:
    """usernames de las filas (usernames, is_active) con ese estado."""
    return [str(row[0]) for row in rows if int(row[1]) == is_active]


def _disable_employee_users(emp_id, reason, data_token):
    """
    La baja del empleado deshabilita todos sus usuarios y avisa a los administradores
    (docs/baja_deshabilita_usuarios.md). No fatal: la baja ya quedó guardada; si esto falla,
    el aviso pide hacerlo a mano. Solo corta los inicios de sesión nuevos: una sesión abierta
    sigue hasta que venza su token, porque el API no consulta la BD (docs/permisos_plan.md, D8).
    """
    flag, error, rows = get_users_by_emp_id(emp_id, data_token)
    if flag and isinstance(rows, list):
        names = _usernames_with_state(rows, 1)
        if not names:
            return False
        users = ", ".join(names)
        flag, error, _count = disable_users_by_emp_id(emp_id, data_token)
    else:
        flag, users = False, f"los usuarios del empleado {emp_id}"
    if flag:
        title = "Usuario deshabilitado"
        msg = f"{users}: deshabilitado por la baja del empleado {emp_id} (motivo: {reason}). Si reingresa, se reactiva a mano."
    else:
        title = "Usuario sin deshabilitar"
        msg = (
            f"No se pudo deshabilitar a {users} tras la baja del empleado {emp_id} (motivo: {reason}): {error}. "
            "Hay que deshabilitarlo a mano en la app de usuarios; mientras tanto puede iniciar sesión."
        )
    write_log_file(log_file_users, msg, data_token)
    return create_notification_permission(
        msg, data_token, ["administrator"], title, data_token.get("emp_id"), 0
    )


def _notify_user_rehire(emp_id, data_token):
    """
    Un reingreso no reactiva solo (docs/planes/login_y_usuarios_plan.md, U3): si el empleado
    tiene usuarios deshabilitados, se avisa a los administradores para que los revisen.
    """
    flag, _error, rows = get_users_by_emp_id(emp_id, data_token)
    if not flag or not isinstance(rows, list):
        return False
    names = _usernames_with_state(rows, 0)
    if not names:
        return False
    users = ", ".join(names)
    msg = f"{users}: sigue deshabilitado y el empleado {emp_id} reingresó. Reactívalo a mano y revisa sus permisos."
    write_log_file(log_file_users, msg, data_token)
    return create_notification_permission(
        msg, data_token, ["administrator"], "Usuario por reactivar", data_token.get("emp_id"), 0
    )


def _departure_reason(departure) -> str:
    """Motivo de baja del campo departure del PUT (dict o JSON {date, reason})."""
    if isinstance(departure, str):
        try:
            departure = json.loads(departure)
        except ValueError:
            return departure.strip() or "sin motivo"
    if isinstance(departure, dict) and departure.get("reason"):
        return str(departure["reason"])
    return "sin motivo"


def update_employee_db(data, data_token):
    email_column, err = _employee_email_column(data["info"])
    if err:
        return err, 400
    previous_status = _employee_status(data["id"], data_token)
    flag, error, result = update_employee(
        data["id"],
        data["info"]["name"],
        data["info"]["lastname"],
        data["info"]["curp"],
        data["info"]["phone"],
        data["info"]["modality"],
        data["info"]["dep"],
        data["info"]["contract"],
        data["info"]["admission"],
        data["info"]["rfc"],
        data["info"]["nss"],
        data["info"]["position"],
        data["info"]["status"],
        data["info"]["departure"],
        data["info"]["birthday"],
        data["info"]["legajo"],
        email_column,
        data["info"]["emergency"],
        data_token,
        data["info"]["id_leader"],
    )
    if flag:
        new_status = str(data["info"]["status"] or "").strip().lower()
        if previous_status != "inactivo" and new_status == "inactivo":
            _disable_employee_users(data["id"], _departure_reason(data["info"]["departure"]), data_token)
        elif previous_status == "inactivo" and new_status == "activo":
            _notify_user_rehire(data["id"], data_token)
        return {"data": {"id_employee": result}, "msg": f"Empleado actualizado correctamente (ID {result})", "error": None}, 200
    else:
        return {"data": None, "msg": "No se pudo actualizar el empleado", "error": error}, 400


def terminate_employee_from_api(data, data_token):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone)
    date = timestamp.strftime(format_timestamps)
    departure = {"date": date, "reason": data["reason"]}
    previous_status = _employee_status(data["id"], data_token)
    flag, error, result = terminate_employee_db(data["id"], json.dumps(departure), data_token)
    if not flag:
        return {
            "data": None,
            "msg": "No se pudo dar de baja al empleado",
            "error": error,
        }, 400
    msg = (
        f"Empleado con id: {data['id']} dado de baja por {data['reason']}. "
        f"Realizado por el empleado con id: {data_token['emp_id']} "
    )
    write_log_file(log_file_rh, msg, data_token)
    create_notification_permission(
        msg, data_token, ["rrhh"], "Empleado dato de baja", data_token.get("emp_id"), 0
    )
    if previous_status != "inactivo":
        _disable_employee_users(data["id"], data["reason"], data_token)
    return {"data": {"id_employee": data["id"]}, "msg": f"Empleado dado de baja correctamente (ID {data['id']})", "error": None}, 200


def _payroll_index_keys(files_data) -> set:
    """Todas las keys S3 (hojas str) del indice files_data de un empleado."""
    keys, stack = set(), [files_data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            stack.extend(node.values())
        elif isinstance(node, str) and node:
            keys.add(node)
    return keys


def download_nomina_docs(data, data_token):
    """POST /common/payroll/employee/file: zip en memoria con el pdf y/o el xml
    de un recibo (keys S3, ej. payroll/<year>/<month>/<emp_id>/<filename>).
    Basta uno de los dos. Cada key debe estar en el indice del `emp_id` pedido:
    el token solo prueba que quien pide es ese empleado o RH, no que la key sea
    suya. -> (BytesIO, 200) | (envelope, 4xx). Ver docs/nomina_descarga_recibo.md."""
    requested = []
    for key in (data.get("pdf"), data.get("xml")):
        key = (key or "").strip()
        if key and key not in requested:
            requested.append(key)
    if not requested:
        return {"data": None, "msg": "Indica el pdf o el xml del recibo", "error": "pdf y xml vacíos"}, 400
    files_data, error = _load_payroll_index(data["emp_id"], data_token)
    if files_data is None:
        return {"data": None, "msg": f"El empleado {data['emp_id']} no tiene registro de nómina", "error": error}, 404
    owned = _payroll_index_keys(files_data)
    foreign = [key for key in requested if key not in owned]
    if foreign:
        return {
            "data": None,
            "msg": "El archivo no está entre los recibos del empleado (pudo haberse reemplazado o eliminado)",
            "error": foreign,
        }, 404
    bucket_name = secrets.get("S3_RH_BUCKET")
    s3_client = boto3.client("s3")
    buffer = io.BytesIO()
    written = 0
    with zipfile.ZipFile(buffer, "w") as zipf:
        for key in requested:
            try:
                obj = s3_client.get_object(Bucket=str(bucket_name), Key=key)
                zipf.writestr(os.path.basename(key), obj["Body"].read())
                written += 1
            except (NoCredentialsError, ClientError, BotoCoreError) as e:
                print(f"Error al descargar nomina desde S3 (key {key}): {e}")
    if written == 0:
        return {"data": None, "msg": "No se pudieron descargar los archivos de nómina", "error": "Ningún archivo descargado desde S3"}, 400
    buffer.seek(0)
    return buffer, 200


def get_files_list_nomina_RH(emp_id, data_token):
    flag, error, result = get_payrolls(emp_id, data_token)
    dicts_data = []
    for item in result:
        emp_id = int(item[0])
        name = f"{item[2].upper()} {item[3].upper()}"
        dict_data = json.loads(item[1])
        dicts_data.append({"id": emp_id, "name": name, "data": dict_data})
    return 200, dicts_data


def get_files_list_nomina(emp_id, data_token):
    flag, error, result = get_payrolls(emp_id, data_token)
    if not flag:
        return {"data": None, "msg": "Error al obtener nóminas", "error": error}, 400
    files = []
    dicts_data = []
    for item in result:
        emp_id = int(item[0])
        name = f"{item[2].upper()} {item[3].upper()}"
        dict_data = json.loads(item[1])
        for year in dict_data.keys():
            for month in dict_data[year].keys():
                for file in dict_data[year][month].keys():
                    files.append(
                        {
                            "year": year,
                            "month": month,
                            "files": dict_data[year][month][file],
                            "name": file,
                            "emp_id": emp_id,
                        }
                    )
        dicts_data.append({"id": emp_id, "name": name, "data": dict_data})
    return {"data": files, "msg": None, "error": None}, 200


def insert_medical_db(data, data_token):
    allergies = data["info"]["allergies"]
    observations = data["info"]["observations"]
    extra_info = {"allergies": allergies, "observations": observations}
    flag, error, result = insert_new_exam_med(
        data["info"]["name"],
        data["info"]["blood"],
        data["info"]["status"],
        data["info"]["aptitudes"],
        data["info"]["dates"],
        data["info"]["apt_actual"],
        data["info"]["emp_id"],
        extra_info,
        data_token,
    )
    if flag:
        return {"data": {"id_exam": result}, "msg": f"Registro médico creado correctamente (ID {result})", "error": None}, 201
    else:
        return {"data": None, "msg": "No se pudo crear el registro médico", "error": error}, 400


def update_medical_db(data, data_token):
    apt_actual = data["info"]["aptitudes"][-1] if len(data["info"]["aptitudes"]) > 0 else 0
    allergies = data["info"]["allergies"]
    observations = data["info"]["observations"]
    extra_info = {"allergies": allergies, "observations": observations}
    flag, error, result = update_aptitud_renovacion(
        data["info"]["aptitudes"],
        data["info"]["dates"],
        apt_actual,
        exam_id=data["id"],
        extra_info=extra_info,
        data_token=data_token,
    )
    if flag:
        return {"data": {"id_exam": result}, "msg": f"Registro médico actualizado correctamente (ID {result})", "error": None}, 200
    else:
        return {"data": None, "msg": "No se pudo actualizar el registro médico", "error": error}, 400


def _seniority_from_form(items: list) -> dict:
    # Mismo shape para alta y edicion: los GET de vacaciones leen `prima` de
    # cada periodo (antes el alta la descartaba).
    seniority_dict = {}
    for item in items:
        seniority_dict[str(item["year"])] = {
            "status": item["status"],
            "comentarios": item["comentarios"],
            "prima": item["prima"],
            "dates": item.get("dates", []),
        }
    return seniority_dict


def insert_new_vacation(data, data_token):
    seniority_dict = _seniority_from_form(data["seniority"])
    if not len(seniority_dict) > 0:
        return {"data": None, "msg": "No hay informacion que insertar", "error": None}, 400
    emp_id = data["emp_id"]
    flag, error, result = insert_vacation(emp_id, seniority_dict, data_token=data_token)
    if not flag:
        if "Duplicate entry" in error:
            return {
                "data": None,
                "msg": "El empleado ya tiene registro de vacaciones; usa PUT para actualizarlo",
                "error": error,
            }, 409
        return {"data": None, "msg": "No se pudieron registrar las vacaciones", "error": error}, 400
    # `vacations` no tiene autoincremental (PK = emp_id): lastrowid siempre es 0.
    return {
        "data": {"id_vacation": emp_id},
        "msg": f"Vacaciones registradas correctamente (ID {emp_id})",
        "error": None,
    }, 201


def update_vacation(data, data_token):
    seniority_dict = _seniority_from_form(data["seniority"])
    if not len(seniority_dict) > 0:
        return {
            "data": None,
            "msg": "No hay informacion que actualizar o corrupcion de info.",
            "error": None,
        }, 400
    emp_id = data["emp_id"]
    # rowcount 0 no distingue "no existe" de "sin cambios": se consulta antes.
    flag, error, current = get_vacations_data_emp(emp_id, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron actualizar las vacaciones", "error": error}, 400
    if not current:
        return {
            "data": None,
            "msg": f"No existe registro de vacaciones para el empleado {emp_id}",
            "error": None,
        }, 404
    flag, error, result = update_registry_vac(emp_id, seniority_dict, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron actualizar las vacaciones", "error": error}, 400
    return {
        "data": {"id_vacation": emp_id},
        "msg": f"Vacaciones actualizadas correctamente (ID {emp_id})",
        "error": None,
    }, 200


def get_all_quizzes(data_token):
    flag, error, tasks = get_all_tasks_by_status(status=-1, title="quizz", data_token=data_token)
    if not flag:
        return False, error, []
    data_out = []
    for item in tasks:
        data_out.append(
            {
                "id": item[0],
                "body": json.loads(item[1]),
                "data_raw": json.loads(item[2]),
                "timestamp": item[3].strftime(format_timestamps)
                if isinstance(item[3], datetime)
                else item[3],
            }
        )
    return True, "", data_out


def _quizz_names_by_type(data_token) -> dict:
    """{type_q: name} de quizz_models (cualquier status). Vacio si falla la lectura."""
    flag, _error, rows = get_quizz_model_names_db(data_token)
    if not flag or not isinstance(rows, list):
        return {}
    names = {}
    for row in rows:
        try:
            names[int(row[0])] = row[1]
        except (TypeError, ValueError):
            continue
    return names


def get_task_by_id_employee(id_emp: int, data_token):
    """GET /rrhh/task/<emp_id>. Enriquece `body.metadata.quizz_name` en lectura
    con el nombre del modelo (`quizz_models.name` por `type_quizz`): el empleado
    no tiene permiso para el catalogo de modelos y el front solo conocia de
    memoria los tipos 0-4 (docs/quizz_models_versionado.md, Notas posteriores).
    `null` si el modelo ya no existe o la tarea no trae type_quizz."""
    flag, error, result = get_task_by_id_emp(id_emp, data_token)
    if not flag:
        return {"data": None, "msg": "Error al obtener las tareas", "error": error}, 400
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": None, "msg": "Formato de datos inválido", "error": f"no tasks {result}"}, 400
    names = _quizz_names_by_type(data_token) if result else {}
    data_out = []
    for item in result:
        body = json.loads(item[1])
        if isinstance(body, dict):
            metadata = body.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
                body["metadata"] = metadata
            try:
                type_q = int(metadata.get("type_quizz"))  # pyrefly: ignore
            except (TypeError, ValueError):
                type_q = None
            metadata["quizz_name"] = names.get(type_q) if type_q is not None else None
        data_out.append(
            {
                "id": item[0],
                "body": body,
                "data_raw": json.loads(item[2]),
                "timestamp": item[3].strftime(format_timestamps)
                if isinstance(item[3], datetime)
                else item[3],
            }
        )
    return {"data": data_out, "msg": None, "error": None}, 200


def get_quizz_evaluation(id_task, data_token):
    """Evalua una encuesta por su id (task) con el motor config-driven y
    devuelve el resultado uniforme. Determinista desde `data_raw` + rubrica
    (siempre fresco); no persiste ni genera PDF. Devuelve (envelope, code).
    """
    from templates.resources.midleware.quizz_eval_engine import evaluate_task

    flag, error, result = get_all_tasks_by_status(
        status=-1, data_token=data_token, id_task=id_task, title=None
    )
    if not flag:
        return {"data": None, "msg": "No se pudo obtener la encuesta", "error": error}, 400
    rows = result if isinstance(result, list) else []
    if not rows:
        return {"data": None, "msg": f"Encuesta {id_task} no encontrada", "error": None}, 404
    row = rows[0]
    body = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    data_raw = json.loads(row[2]) if isinstance(row[2], str) else row[2]
    tipo_q = (body or {}).get("metadata", {}).get("type_quizz")
    if tipo_q is None:
        return {
            "data": None,
            "msg": f"La tarea {id_task} no es una encuesta (sin type_quizz)",
            "error": None,
        }, 400
    evaluation = evaluate_task(data_raw, tipo_q, data_token)
    if evaluation is None:
        return {
            "data": None,
            "msg": f"No hay rubrica para el tipo de encuesta {tipo_q} (pendiente de migracion)",
            "error": None,
        }, 200
    return {"data": evaluation, "msg": None, "error": None}, 200


def get_quizz_group_evaluation(type_q, data_token, date_from=None, date_to=None):
    """Resultado organizacional de una encuesta: agrega TODAS las encuestas
    contestadas del tipo por conteo agrupado (motor `evaluate_group`), con
    filtro opcional por fecha del task (`YYYY-MM-DD`, ambos limites
    inclusivos). En clima (3) esto es la tabla de % por categoria + total.
    Determinista y on-read (no persiste). Devuelve (envelope, code).
    """
    from templates.resources.midleware.quizz_eval_engine import (
        evaluate_group,
        load_rubric,
    )

    rubric = load_rubric(type_q, data_token)
    if rubric is None:
        return {
            "data": None,
            "msg": f"No hay rubrica para el tipo de encuesta {type_q} (pendiente de migracion)",
            "error": None,
        }, 200
    if rubric.get("mode") == "qualitative":
        return {
            "data": None,
            "msg": f"La encuesta tipo {type_q} es cualitativa: no tiene agregado numerico",
            "error": None,
        }, 200

    limits = {}
    for name, raw in (("date_from", date_from), ("date_to", date_to)):
        if raw in (None, ""):
            limits[name] = None
            continue
        try:
            limits[name] = datetime.strptime(raw, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return {
                "data": None,
                "msg": f"Fecha invalida en {name} (formato YYYY-MM-DD): {raw}",
                "error": None,
            }, 400
    dt_from, dt_to = limits["date_from"], limits["date_to"]

    flag, error, tasks = get_all_tasks_by_status(status=-1, title="quizz", data_token=data_token)
    if not flag:
        return {"data": None, "msg": "No se pudieron obtener las encuestas", "error": error}, 400

    data_raws = []
    for row in tasks if isinstance(tasks, list) else []:
        try:
            body = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            tipo_row = int((body or {}).get("metadata", {}).get("type_quizz"))
        except (TypeError, ValueError):
            continue
        if tipo_row != int(type_q):
            continue
        if dt_from or dt_to:
            ts = row[3]
            if isinstance(ts, str):
                try:
                    ts = datetime.strptime(ts, format_timestamps)
                except ValueError:
                    continue
            if not isinstance(ts, datetime):
                continue
            if (dt_from and ts.date() < dt_from) or (dt_to and ts.date() > dt_to):
                continue
        data_raws.append(row[2])

    evaluation = evaluate_group(data_raws, rubric)
    msg = None
    if evaluation is not None and evaluation.get("respondents") == 0:
        msg = f"Sin encuestas contestadas del tipo {type_q} en el rango solicitado"
    return {"data": evaluation, "msg": msg, "error": None}, 200


NORMA035_TYPES = (1, 2)


def _report_value(value):
    """Valor de metadata para el PDF; vacio si viene "None" (asi lo guarda el front)."""
    return None if value in (None, "", "None") else value


def generate_pdf_from_json(data, data_token):
    """PDF de una encuesta contestada (POST /rrhh/download/quizz/report).
    Norma 035 (tipos 1 y 2) tiene PDF dedicado; el resto usa el generico de
    resumen. Los dos leen el resultado del motor (`evaluation`), que se guarda
    en el data_raw del task; ya no se escriben results/recommendations (P-016,
    docs/norma035_pdf.md). -> (201, ruta) o (400, mensaje)."""
    from templates.controllers.rrhh.quizz_models_controller import get_quizz_model_template_db
    from templates.forms.QuizzGenericReport import create_generic_quizz_report
    from templates.forms.QuizzNorm35 import FileNorma035PDF
    from templates.resources.midleware.quizz_eval_engine import answered_sections, evaluate, load_rubric

    json_dict = data["body"]
    metadata = json_dict.get("metadata") or {}
    tipo_op = metadata["type_quizz"]
    data_raw = (
        json.loads(data["data_raw"]) if isinstance(data["data_raw"], str) else data["data_raw"]
    )
    rubric = load_rubric(tipo_op, data_token)
    if rubric is None:
        return 400, f"No hay rubrica para el tipo de encuesta {tipo_op}"
    # Evaluacion via el motor config-driven (fuente de verdad, shape uniforme).
    evaluation = evaluate(data_raw, rubric)
    if evaluation.get("mode") == "scored":
        data_raw["evaluation"] = evaluation
        # Persistir solo con un id valido (evita pisar la fila 0 por el default del form).
        if data.get("id"):
            flag, error, _ = update_task(
                data["id"], data["body"], data_raw=data_raw, data_token=data_token
            )
            if not flag:
                write_log_file(
                    log_file_rh, f"No se pudo actualizar el task de quizz: {error}", data_token
                )

    # Archivo temporal unico por request (evita el clobber del temp compartido).
    file_out = os.path.join(quizz_out_path, f"quiz_report_{uuid.uuid4().hex}.pdf")
    flag_model, _, model_row = get_quizz_model_template_db(tipo_op, data_token)
    model_name = (
        model_row[0]  # pyrefly: ignore
        if flag_model and model_row
        else f"Tipo {tipo_op}"
    )
    folio = f"Encuesta {data.get('id') or 's/n'} / tipo {tipo_op}"
    try:
        is_norma035 = int(tipo_op) in NORMA035_TYPES
    except (TypeError, ValueError):
        is_norma035 = False
    try:
        if is_norma035 and evaluation.get("mode") == "scored":
            FileNorma035PDF(
                {
                    "path_file": file_out,
                    "title": model_name,
                    "folio": folio,
                    "metadata": [
                        ("Trabajador", _report_value(metadata.get("name_emp"))),
                        ("Puesto", _report_value(metadata.get("position"))),
                        ("Fecha de aplicación", _report_value(metadata.get("date"))),
                        ("Entrevistador", _report_value(metadata.get("interviewer"))),
                        ("Fecha de ingreso", _report_value(metadata.get("admision"))),
                        ("Encuesta", folio),
                    ],
                    "evaluation": evaluation,
                    "levels": rubric.get("levels") or {},
                    "answers": answered_sections(data_raw),
                }
            )
        else:
            create_generic_quizz_report(
                {
                    "path_file": file_out,
                    "title": model_name,
                    "folio": folio,
                    "metadata": {
                        "Empleado": _report_value(metadata.get("name_emp")),
                        "Puesto": _report_value(metadata.get("position")),
                        "Fecha": _report_value(metadata.get("date")),
                        "Entrevistador": _report_value(metadata.get("interviewer")),
                        "Fecha de ingreso": _report_value(metadata.get("admision")),
                        "Fecha de baja": _report_value(metadata.get("departure")),
                        "Modelo": f"{model_name} (tipo {tipo_op})",
                    },
                    "evaluation": evaluation,
                }
            )
        return 201, file_out
    except Exception as e:
        write_log_file(log_file_rh, f"Error al generar el pdf de quizz: {e}", data_token)
        return 400, "Error al generar el pdf"


def create_payroll_file_attachment_api(data, data_token):
    """Sube un archivo de nomina (pdf o xml) al bucket S3 de RH bajo
    payroll/<entorno>/<year>/<month>/<emp_id>/<quincena>/<filename> y registra la ruta en el
    indice files_data del empleado (files_data[year][month][key][pdf|xml]).
    Orden para no dejar huerfanos ni llaves rotas: indice leido antes de subir,
    indice guardado antes de borrar el anterior y, si el indice no se guarda,
    se retira el objeto que subio este request (docs/nomina_s3_huerfanos.md)."""
    filename = data["filename"]
    filepath_down = data["filepath"]
    key = data["key"]
    # year/month normalizados: month a dos digitos 01-12
    try:
        emp_id = int(data["emp_id"])
        year = str(int(data["year"]))
        month = f"{int(data['month']):02d}"
    except (ValueError, TypeError) as e:
        return {"data": None, "msg": "year, month o emp_id invalidos", "error": str(e)}, 400
    # reconocer el tipo de archivo: solo pdf o xml
    file_extension = filename.split(".")[-1].lower()
    valid_extension = ["pdf", "xml"]
    if file_extension not in valid_extension:
        return {"data": None, "msg": "Formato de archivo no válido (solo pdf o xml)", "error": None}, 400
    # Indice ANTES de subir: sin fila de nomina o con la BD caida no se sube
    # nada (antes se tomaba como indice vacio y el UPDATE pisaba todo el
    # files_data del empleado, o tocaba 0 filas y respondia 201 sin indexar).
    files_data, error = _load_payroll_index(emp_id, data_token)
    if files_data is None:
        return {
            "data": None,
            "msg": f"El empleado {emp_id} no tiene registro de nómina",
            "error": error,
        }, 404
    # subir a S3: payroll/<entorno>/<year>/<month>/<emp_id>/<quincena>/<filename>
    # (P-177): con la quincena, el mismo nombre en Q1 y Q2 ya no comparte objeto.
    key_segment = secure_filename(key) or "sin_quincena"
    path_aws = s3_env_key("payroll", f"{year}/{month}/{emp_id}/{key_segment}/{filename}", data_token)
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_RH_BUCKET")
    # Si la llave ya existia (mismo nombre: S3 la pisa) no la creo este
    # request y no se retira aunque falle el indice.
    existed = _payroll_s3_exists(s3_client, str(bucket_name), path_aws)
    try:
        s3_client.upload_file(Filename=filepath_down, Bucket=str(bucket_name), Key=path_aws)
    except FileNotFoundError:
        return {"data": None, "msg": "Local file not found"}, 400
    except NoCredentialsError:
        return {"data": None, "msg": "AWS credentials not found"}, 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {"data": None, "msg": f"Bucket does not exist: {bucket_name}"}, 400
        elif error_code == "AccessDenied":
            return {"data": None, "msg": f"Access denied to bucket: {bucket_name}"}, 400
        else:
            return {"data": None, "msg": f"AWS error: {str(e)}"}, 400
    # registrar la ruta en el indice del empleado, agrupando pdf y xml por 'key'
    entry = files_data.setdefault(year, {}).setdefault(month, {}).setdefault(key, {})
    previous = entry.get(file_extension)
    entry[file_extension] = path_aws
    flag, error, _ = update_payroll(files_data, emp_id, data_token)
    if not flag:
        # El indice no cambio (el anterior sigue vigente): se retira lo que
        # subio este request para no dejarlo huerfano.
        detail = "la llave ya existía en S3, se conserva"
        if not existed:
            _, detail, _ = _payroll_s3_delete([path_aws], data_token)
        msg = (
            f"No se pudo guardar el índice de nómina del empleado {emp_id}; "
            f"{filename} no quedó registrado ({detail})"
        )
        write_log_file(log_file_rh, f"{msg}: {error}", data_token)
        return {"data": None, "msg": msg, "error": error}, 400
    # Reemplazo (mismo key+kind, otro nombre): el anterior se borra de S3 ya
    # con el indice guardado, y solo si ninguna otra nomina del indice lo usa
    # (mismo nombre de archivo en otro key del mes = misma llave S3). Con el
    # mismo nombre, S3 ya lo piso en el upload.
    replaced_detail = ""
    error_out = None
    if previous and previous != path_aws:
        if previous in _payroll_index_keys(files_data):
            detail = "se conserva en S3: otra nómina del índice lo usa"
        else:
            _, detail, error_out = _payroll_s3_delete([previous], data_token)
        replaced_detail = f"; reemplaza a {previous} ({detail})"
    msg = (
        f"Archivo de nomina {filename} ({file_extension}) subido para el empleado "
        f"{emp_id} en {year}/{month} (key {key}){replaced_detail}"
    )
    write_log_file(log_file_rh, msg, data_token)
    return {"data": path_aws, "msg": msg, "error": error_out}, 201


def _load_payroll_index(emp_id, data_token):
    """Indice files_data del empleado. -> (dict | None si no tiene fila en
    payroll, error). El dict va vacio si la fila existe sin archivos."""
    flag, error, result = get_payrolls(emp_id, data_token)
    has_record = (
        flag and isinstance(result, (list, tuple)) and len(result) > 0 and result[0]
    )
    if not has_record:
        return None, error
    raw = result[0][1]  # pyrefly: ignore
    try:
        files_data = json.loads(raw) if isinstance(raw, str) else (raw or {})
    except (ValueError, TypeError):
        files_data = {}
    return files_data if isinstance(files_data, dict) else {}, None


def _payroll_s3_exists(s3_client, bucket_name: str, key: str) -> bool:
    """True si el objeto ya esta en S3. Ante un error que no sea 404 responde
    True: quien pregunta solo borra lo que sabe que creo."""
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError as e:
        return e.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey", "NotFound")
    except (NoCredentialsError, BotoCoreError):
        return True


def _payroll_s3_delete(keys, data_token):
    """Borra objetos del bucket de RH best-effort (nunca fatal: la BD ya
    quedo consistente). -> (deleted: bool, detail: str, error: str | None).
    Solo borra las llaves que este entorno puede borrar (s3_can_delete, P-177):
    una llave vieja compartida con prod se queda en S3."""
    keys = [k for k in keys if k]
    if not keys:
        return False, "Sin llave en S3 que eliminar", None
    kept = [k for k in keys if not s3_can_delete(k, data_token)]
    keys = [k for k in keys if k not in kept]
    if kept:
        write_log_file(log_file_rh, f"S3 sin borrar (llave de otro entorno o sin entorno): {kept}", data_token)
    if not keys:
        return False, "se conserva en S3: la ruta es de otro entorno o anterior a P-177 (solo prod la borra)", None
    s3_client = boto3.client("s3")
    bucket_name = secrets.get("S3_RH_BUCKET")
    try:
        for key in keys:
            s3_client.delete_object(Bucket=str(bucket_name), Key=key)
        return True, "Objeto eliminado de S3", None
    except (ClientError, NoCredentialsError, BotoCoreError) as e:
        write_log_file(log_file_rh, f"Error al borrar de S3 {keys}: {e}", data_token)
        return False, "No se pudo borrar el objeto de S3 (queda huérfano)", str(e)


def _normalize_payroll_period(data):
    """emp_id/year/month del body -> (emp_id:int, year:str, month:'MM', key:str)
    o (None, msg) si vienen mal. Misma normalizacion que la subida."""
    try:
        emp_id = int(data["emp_id"])
        year = str(int(data["year"]))
        month = f"{int(data['month']):02d}"
    except (ValueError, TypeError, KeyError) as e:
        return None, f"year, month o emp_id invalidos ({e})"
    key = str(data.get("key") or "").strip()
    if not key:
        return None, "key es obligatorio"
    return (emp_id, year, month, key), None


def delete_payroll_file_api(data, data_token):
    """DELETE /payroll/files: quita del indice el pdf, el xml o ambos de un
    `key` y borra el objeto de S3 best-effort (BD primero: si S3 falla el
    indice ya no apunta al objeto -> 200 con s3_deleted False + motivo en
    error). El key/mes/anio se limpian si quedan vacios."""
    period, err = _normalize_payroll_period(data)
    if period is None:
        return {"data": None, "msg": err, "error": None}, 400
    emp_id, year, month, key = period
    kind = str(data.get("kind") or "both").strip().lower()
    if kind not in ("pdf", "xml", "both"):
        return {"data": None, "msg": "kind debe ser pdf, xml o both", "error": None}, 400

    files_data, error = _load_payroll_index(emp_id, data_token)
    if files_data is None:
        return {
            "data": None,
            "msg": f"El empleado {emp_id} no tiene registro de nómina",
            "error": error,
        }, 404
    entry = files_data.get(year, {}).get(month, {}).get(key)
    if not isinstance(entry, dict) or not entry:
        return {
            "data": None,
            "msg": f"No existe la nómina {key} de {month}/{year} para el empleado {emp_id}",
            "error": None,
        }, 400
    kinds = ["pdf", "xml"] if kind == "both" else [kind]
    to_delete = [entry[k] for k in kinds if entry.get(k)]
    if not to_delete:
        return {
            "data": None,
            "msg": f"La nómina {key} de {month}/{year} no tiene archivo {kind}",
            "error": None,
        }, 400
    for k in kinds:
        entry.pop(k, None)
    if not entry:
        files_data[year][month].pop(key, None)
    if not files_data[year][month]:
        files_data[year].pop(month, None)
    if not files_data[year]:
        files_data.pop(year, None)

    flag, error, _ = update_payroll(files_data, emp_id, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo actualizar el índice de nómina", "error": error}, 400
    # Una llave que otra nomina del indice sigue usando (mismo nombre de
    # archivo en otro key del mes = misma llave S3) no se borra.
    still_used = _payroll_index_keys(files_data)
    to_purge = [k for k in to_delete if k not in still_used]
    if to_purge:
        s3_deleted, detail, s3_error = _payroll_s3_delete(to_purge, data_token)
    else:
        s3_deleted, detail, s3_error = False, "se conserva en S3: otra nómina del índice lo usa", None
    msg = (
        f"Nómina {key} de {month}/{year} del empleado {emp_id}: "
        f"{kind} eliminado del índice ({detail})"
    )
    write_log_file(log_file_rh, msg, data_token)
    return {
        "data": {
            "emp_id": emp_id,
            "year": year,
            "month": month,
            "key": key,
            "deleted": to_delete,
            "s3_deleted": s3_deleted,
            "files_data": files_data,
        },
        "msg": msg,
        "error": s3_error,
    }, 200


_PAYROLL_NOTIFY_CHANNELS = ("app", "email")


def notify_payroll_file_api(data, data_token):
    """POST /payroll/notify: avisa al empleado dentro del sistema que su
    recibo (pdf/xml del `key`) ya esta disponible -> notificacion in-app con
    receiver_id = emp_id (la ve en GET /misc/notifications/employee/<id>&0 y
    la baja con POST /common/payroll/employee/file). Sin usuario en el
    sistema no hay a quien notificar -> 200 con notified False y motivo.
    `channels`: 'app' (in-app) y 'email' (SES, Docs/nomina_correo_ses.md:
    correo al employees.email con el pdf/xml adjuntos desde S3). Sin
    SES_SENDER en .env el correo se reporta en channels_pending; sin email
    del empleado o con fallo de SES/S3, en channels_failed con motivo."""
    period, err = _normalize_payroll_period(data)
    if period is None:
        return {"data": None, "msg": err, "error": None}, 400
    emp_id, year, month, key = period
    # Solo empleados activos (junta 2026-10-22): un inactivo o con status NULL no se notifica
    # por ningun canal; la subida de archivos si sigue aceptandolos.
    flag_e, _err_e, emp_row = test_id_employee(int(emp_id), data_token)
    if not flag_e or not isinstance(emp_row, (list, tuple)) or len(emp_row) == 0:
        return {"data": None, "msg": f"No existe el empleado {emp_id}", "error": "empleado no encontrado"}, 404
    emp_status = str(emp_row[1]).strip().lower() if emp_row[1] is not None else ""
    if emp_status != "activo":
        return {
            "data": {"emp_id": emp_id, "status": emp_row[1]},
            "msg": f"El empleado {emp_id} está inactivo (status {emp_row[1]!r}); la nómina solo se notifica a activos",
            "error": ["empleado inactivo"],
        }, 400
    channels = data.get("channels") or ["app"]
    channels = [str(c).strip().lower() for c in channels if str(c).strip()]
    invalid = [c for c in channels if c not in _PAYROLL_NOTIFY_CHANNELS]
    if invalid or not channels:
        return {
            "data": None,
            "msg": f"channels inválidos: {invalid or channels} (válidos: {', '.join(_PAYROLL_NOTIFY_CHANNELS)})",
            "error": None,
        }, 400

    files_data, error = _load_payroll_index(emp_id, data_token)
    if files_data is None:
        return {
            "data": None,
            "msg": f"El empleado {emp_id} no tiene registro de nómina",
            "error": error,
        }, 404
    entry = files_data.get(year, {}).get(month, {}).get(key)
    if not isinstance(entry, dict) or not any(entry.get(k) for k in ("pdf", "xml")):
        return {
            "data": None,
            "msg": f"La nómina {key} de {month}/{year} del empleado {emp_id} no tiene archivos que notificar",
            "error": None,
        }, 400

    flag, error, user_row = get_user_by_emp_id(emp_id, data_token)
    if not flag:
        return {"data": None, "msg": "No se pudo verificar el usuario del empleado", "error": error}, 400
    has_user = bool(user_row)
    title = "Recibo de nómina disponible"
    message = (data.get("message") or "").strip() or (
        f"Tu recibo de nómina {key} ({month}/{year}) ya está disponible en el sistema."
    )
    sent, pending = [], []
    id_notification = None
    reason = None
    if "app" in channels:
        if has_user:
            time_zone = pytz.timezone(timezone_software)
            timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
            body = {
                "id": 0,
                "status": 0,
                "title": title,
                "msg": message,
                "timestamp": timestamp,
                "sender_id": data_token.get("emp_id", 0),
                "receiver_id": emp_id,
                "app": [],
                "extra_emps": [],
                "payload": {"kind": "payroll", "year": year, "month": month, "key": key, "files": entry},
            }
            flag, error, id_notification = insert_notification(body, data_token)
            if not flag:
                return {"data": None, "msg": "No se pudo crear la notificación", "error": error}, 400
            sent.append("app")
        else:
            reason = f"El empleado {emp_id} no tiene usuario en el sistema: no puede recibir la notificación"
    failed = []
    email_to = None
    if "email" in channels:
        if not is_ses_configured():
            pending.append("email")
        else:
            email_to, err_mail = _send_payroll_email(emp_id, key, month, year, entry, message, data_token)
            if err_mail:
                failed.append({"channel": "email", "reason": err_mail})
            else:
                sent.append("email")
    notified = bool(sent)
    msg = (
        f"Empleado {emp_id} notificado de la nómina {key} ({month}/{year})"
        if notified
        else f"Nómina {key} ({month}/{year}) del empleado {emp_id}: sin notificar"
    )
    if reason:
        msg += f". {reason}"
    if pending:
        msg += f". Canal(es) pendiente(s) de configurar: {', '.join(pending)} (falta SES_SENDER en .env)"
    if failed:
        msg += ". " + "; ".join(f"{f['channel']}: {f['reason']}" for f in failed)
    write_log_file(log_file_rh, msg, data_token)
    return {
        "data": {
            "emp_id": emp_id,
            "year": year,
            "month": month,
            "key": key,
            "notified": notified,
            "id_notification": id_notification if notified else None,
            "reason": reason,
            "channels_sent": sent,
            "channels_pending": pending,
            "channels_failed": failed,
            "email_to": email_to,
        },
        "msg": msg,
        "error": None,
    }, 201


def _send_payroll_email(emp_id, key, month, year, entry: dict, message: str, data_token):
    """Correo SES al empleado con el pdf/xml del recibo adjuntos (leidos de
    S3_RH_BUCKET), a TODOS sus correos. -> (email_to: list | None, error | None). Nunca truena."""
    flag, error, row, _cols = get_employee_info(emp_id, data_token)
    if not flag:
        return None, f"no se pudo consultar el empleado ({error})"
    # Todos los correos del empleado (lista en employees.email; junta 2026-10-22).
    email_to = split_emails(row[7] if isinstance(row, (list, tuple)) and len(row) > 7 else None)  # pyrefly: ignore
    if not email_to:
        return None, f"el empleado {emp_id} no tiene correo registrado"
    attachments = []
    s3_client = boto3.client("s3")
    bucket = str(secrets.get("S3_RH_BUCKET"))
    for kind in ("pdf", "xml"):
        s3_key = entry.get(kind)
        if not s3_key:
            continue
        try:
            obj = s3_client.get_object(Bucket=bucket, Key=s3_key)
            attachments.append((os.path.basename(s3_key), obj["Body"].read()))
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            return email_to, f"no se pudo leer {kind} de S3 ({s3_key}): {e}"
    if not attachments:
        return email_to, "sin archivos que adjuntar"
    subject = f"Recibo de nómina {key} ({month}/{year}) — Telintec"
    body = (
        f"{message}\n\nSe adjuntan los archivos de tu recibo de nómina {key} ({month}/{year}).\n"
        "Este correo se genera automáticamente desde el sistema de Telintec; no respondas a este mensaje."
    )
    ok, error, _message_id = send_email_ses(email_to, subject, body, attachments)
    return email_to, (None if ok else error)


def extract_payroll_xml_api(data, data_token):
    """POST /payroll/files/extract: lee un XML de CFDI de nomina y devuelve
    los datos para SUGERIR la asignacion archivo->empleado/periodo en la
    carga por periodo del front (RFC, numero de empleado, nombre, fechas del
    periodo y un emp_id sugerido por RFC, CURP o nombre). No sube ni guarda nada."""
    filename = str(data.get("filename") or "")
    if not filename.lower().endswith(".xml"):
        return {"data": None, "msg": "Solo se puede extraer de un archivo xml", "error": None}, 400
    try:
        parsed = get_data_xml_file_nomina(data["filepath"])
    except Exception as e:  # ParseError, KeyError, OSError... el XML no es un CFDI de nomina legible
        write_log_file(log_file_rh, f"XML de nomina no reconocido ({filename}): {e}", data_token)
        return {"data": None, "msg": "El XML no se reconoce como CFDI de nómina", "error": str(e)}, 400
    receptor = parsed.get("receptor") if isinstance(parsed.get("receptor"), dict) else {}
    nomina = parsed.get("Nomina") if isinstance(parsed.get("Nomina"), dict) else {}
    fecha_pago = nomina.get("FechaPago") or parsed.get("date_pay")
    year = month = None
    if isinstance(fecha_pago, str) and len(fecha_pago) >= 7:
        try:
            year, month = int(fecha_pago[0:4]), int(fecha_pago[5:7])
        except ValueError:
            year = month = None
    emp_id, match_by, name_db = find_employee_for_payroll(
        receptor.get("Rfc"), receptor.get("Curp"), receptor.get("Nombre"), data_token
    )
    out = {
        "filename": filename,
        "rfc": receptor.get("Rfc"),
        "curp": receptor.get("Curp"),
        "num_empleado": receptor.get("NumEmpleado"),
        "nombre": receptor.get("Nombre"),
        "periodo": {
            "inicio": nomina.get("FechaInicialPago"),
            "fin": nomina.get("FechaFinalPago"),
            "pago": fecha_pago,
            "dias": nomina.get("NumDiasPagados"),
            "tipo": nomina.get("TipoNomina"),
        },
        "year_sugerido": year,
        "month_sugerido": month,
        "emp_id_sugerido": emp_id,
        "match_by": match_by,
        "nombre_sugerido": name_db,
    }
    msg = (
        f"XML {filename}: {out['nombre'] or 'sin receptor'}"
        + (f" -> empleado sugerido {out['emp_id_sugerido']}" if out["emp_id_sugerido"] else " (sin coincidencia de empleado)")
    )
    return {"data": out, "msg": msg, "error": None}, 200


def update_payroll_list_employees(data_token):
    # (2026-09-07) Sin el guard de flags_daemons["update_files_nomina"]: el
    # daemon de SharePoint ya no existe y el flag bloqueaba la sincronizacion.
    # (2026-10-28) Un SELECT + un INSERT de varias filas (antes, un INSERT por empleado).
    flag, error, added = update_payroll_employees(data_token)
    if not flag:
        return 400, f"No se pudo sincronizar la lista de nómina: {error}"
    msg = f"Se han agregado correctamente:\n{len(added)} empleados"
    if added:
        msg += "\n" + ", ".join(str(emp_id) for emp_id in added)
    return 200, msg


def update_data_employee(data, data_token):
    data_dict = json.loads(data["data_dict"])
    flag, error, result = update_payroll(data_dict, data["id"], data_token)
    if flag:
        return 200, {"data": result, "msg": "Datos de nómina actualizados correctamente", "error": None}
    return 400, {"data": None, "msg": "No se pudieron actualizar los datos de nómina", "error": error}


def fetch_employees_without_records(data_token):
    # name, l_name, status, birthday, date_admission, employee_id
    flag, error, result = get_employees_without_records(data_token)
    if not flag:
        return 400, {"data": None, "msg": "No se pudieron obtener los empleados sin registros", "error": error}
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return 400, {"data": [], "msg": "No hay empleados sin registros", "error": None}
    out = []
    for item in result:
        birthday = (
            item[3]
            if isinstance(item[3], str) or item[3] is None or item[4] == "None"
            else item[3].strftime(format_date)
        )
        admission = (
            item[4]
            if isinstance(item[4], str) or item[4] is None or item[4] == "None"
            else item[4].strftime(format_date)
        )
        out.append(
            {
                "name": item[0].upper() + " " + item[1].upper(),
                "status": item[2],
                "birthday": birthday,
                "date_admission": admission,
                "emp_id": item[5],
            }
        )
    return 200, {"data": out, "msg": None, "error": None}


def fetch_medicals(data_token) -> tuple[dict, int]:
    """Registros médicos de todos los empleados + alertas de vencimiento.

    La periodicidad sale de `medical_due` (Functions_Aux_RH: 12/6/3 meses según
    `aptitude_actual` 1/2/3, 4 = NO APTO), la misma regla que el dashboard de
    RH y el daemon de notificaciones. Cada registro trae `alert`, `last_date`,
    `due_date`, `days_left` y `period_days` ya calculados; `error` conserva la
    lista de mensajes [CRÍTICO]/[AVISO] solo de empleados ACTIVOS (contrato
    previo del endpoint)."""
    flag, e, result = get_all_examenes(data_token)
    if not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": [], "msg": "No hay registros médicos", "error": None}, 400
    if not flag:
        return {"data": [], "msg": "No se pudieron obtener los registros médicos", "error": None}, 400

    today = datetime.now(pytz.utc).astimezone(pytz.timezone(timezone_software)).date()
    data_out = []
    messages = []

    for row in result:
        (
            id_exam,
            nombre,
            sangre,
            status,
            aptitud,
            fechas,
            apt_actual,
            emp_id,
            extra_info,
        ) = row

        try:
            extra_info = json.loads(extra_info) if isinstance(extra_info, str) else (extra_info or {})
        except (TypeError, ValueError):
            extra_info = {}
        try:
            aptitudes = json.loads(aptitud) if isinstance(aptitud, str) else (aptitud or [])
        except (TypeError, ValueError):
            aptitudes = []
        try:
            dates = json.loads(fechas) if isinstance(fechas, str) else (fechas or [])
        except (TypeError, ValueError):
            dates = []

        last_date = last_medical_date(dates)
        due = medical_due(apt_actual, last_date, today)
        status_out = status if status is not None else "INACTIVO"

        exam_data = {
            "exist": True,
            "id_exam": id_exam,
            "name": nombre,
            "blood": sangre,
            "status": status_out,
            "aptitudes": aptitudes,
            "dates": dates,
            "apt_last": apt_actual,
            "emp_id": emp_id,
            "allergies": extra_info.get("allergies", ""),
            "observations": extra_info.get("observations", ""),
            "alert": due["alert"],
            "last_date": last_date.isoformat() if last_date else None,
            "due_date": due["due_date"].isoformat() if due["due_date"] else None,
            "days_left": due["days_left"],
            "period_days": due["period_days"],
        }
        data_out.append(exam_data)

        if str(status_out).upper() != "ACTIVO":
            continue
        if due["alert"] == "vencido":
            messages.append(
                f"[CRÍTICO] El empleado {nombre} requiere revisión: aptitud {apt_actual}, "
                f"última fecha {exam_data['last_date']}, venció el {exam_data['due_date']} "
                f"(hace {-due['days_left']} días, límite de {due['period_days']} días)."
            )
        elif due["alert"] == "por_vencer":
            messages.append(
                f"[AVISO] El empleado {nombre} está próximo a revisión: aptitud {apt_actual}, "
                f"última fecha {exam_data['last_date']}, vence el {exam_data['due_date']} "
                f"(faltan {due['days_left']} días, límite de {due['period_days']} días)."
            )
        elif due["alert"] == "no_apto":
            messages.append(f"[CRÍTICO] El empleado {nombre} (ID {id_exam}) está marcado como NO APTO.")

    return {"data": data_out, "msg": None, "error": messages if messages else None}, 200


def fetch_medical_employee(id_emp, data_token):
    flag, e, result = get_all_examenes(data_token)
    if not flag or not (isinstance(result, list) or isinstance(result, tuple)):
        return {"data": None, "msg": "No se pudo obtener el registro médico", "error": None}, 400
    for row in result:
        id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id, _extra = row
        if str(emp_id) == id_emp:
            return {
                "data": {
                    "exist": True,
                    "id_exam": id_exam,
                    "name": nombre,
                    "blood": sangre,
                    "status": status,
                    "aptitudes": aptitud,
                    "dates": fechas,
                    "apt_last": apt_actual,
                    "emp_id": emp_id,
                },
                "msg": None,
                "error": None,
            }, 200
    return {"data": {"exist": False}, "msg": None, "error": None}, 200
