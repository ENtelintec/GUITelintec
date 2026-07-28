# -*- coding: utf-8 -*-
import os
import tempfile

from flask import request, send_file
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.constants import (
    path_contract_files,
)
from static.Models.api_employee_models import (
    DeleteVacationForm,
    EmployeeDeleteForm,
    EmployeeInsertForm,
    EmployeeMedDeleteForm,
    EmployeeMedInsertForm,
    EmployeeMedUpdateForm,
    EmployeeTerminateForm,
    EmployeeUpdateForm,
    EmployeeVacInsertForm,
    employee_exam_model_delete,
    employee_exam_model_insert,
    employee_exam_model_update,
    employee_model_delete,
    employee_model_insert,
    employee_model_terminate,
    employee_model_update,
    employee_vacation_model_delete,
    employee_vacation_model_insert,
)
from static.Models.api_fichajes_models import (
    DataFichajesFileForm,
    expected_files,
    request_data_fichaje_files_model,
)
from static.Models.api_models import (
    RequestFileReportQuizzForm,
    expected_headers_per,
    request_file_report_quizz_model,
)
from static.Models.api_payroll_models import (
    CreateMailForm,
    UpdateDataPayrollForm,
    create_mail_model,
    update_data_payroll_model,
    update_files_parser,
)
from templates.controllers.employees.em_controller import (
    delete_exam_med,
    get_all_examenes,
)
from templates.controllers.employees.employees_controller import (
    delete_employee,
)
from templates.controllers.employees.vacations_controller import (
    delete_vacation,
    get_vacations_data,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_DB_midleware import (
    create_csv_file_employees,
    get_all_vacations,
    get_info_employee_id,
    get_info_employees_with_status,
    get_vacations_employee,
)
from templates.resources.midleware.Functions_midleware_RRHH import (
    create_mail_payroll,
    create_new_employee_db,
    create_payroll_file_attachment_api,
    fetch_employees_without_records,
    fetch_fichaje_employee,
    fetch_fichajes_all_employees,
    fetch_medical_employee,
    fetch_medicals,
    generate_pdf_from_json,
    get_all_quizzes,
    get_fichaje_data,
    get_files_fichaje,
    get_files_list_nomina_RH,
    get_quizz_evaluation,
    insert_medical_db,
    insert_new_vacation,
    terminate_employee_from_api,
    update_data_employee,
    update_employee_db,
    update_medical_db,
    update_payroll_list_employees,
    update_vacation,
)

__author__ = "Edisson Naula"
__date__ = "$ 02/nov./2023  at 17:29 $"

ns = Namespace("GUI/api/v1/rrhh")


@ns.route("/employee")
class Employee(Resource):
    @ns.expect(expected_headers_per, employee_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = create_new_employee_db(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, employee_model_update)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = update_employee_db(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, employee_model_delete)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        flag, error, result = delete_employee(data["id"], data_token)
        if flag:
            return {
                "data": {"id_employee": result},
                "msg": f"Empleado eliminado correctamente (ID {result})",
                "error": None,
            }, 200
        else:
            return {"data": None, "msg": "No se pudo eliminar el empleado", "error": error}, 400


@ns.route("/employee/info/<string:id_emp>")
class EmployeeGet(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_info_employee_id(id_emp, data_token)
        if code != 200:
            return {"data": None, "msg": "No se encontró el empleado", "error": str(data_out)}, code
        return {"data": data_out, "msg": None, "error": None}, code


@ns.route("/employee/terminate")
class EmployeeTerminate(Resource):
    @ns.expect(expected_headers_per, employee_model_terminate)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeTerminateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = terminate_employee_from_api(data, data_token)
        return data_out, code


@ns.route("/employees/info/<string:status>")
class EmployeesInfo(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(
            request, department=["rrhh", "operaciones", "administracion"]
        )
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_info_employees_with_status(status)
        if code != 200:
            return {"data": [], "msg": "No se encontraron empleados", "error": None}, code
        return {"data": data_out, "msg": None, "error": None}, code


@ns.route("/employee/medical/<string:id_emp>")
class EMResumeEmployees(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = fetch_medical_employee(id_emp, data_token)
        return out, code


@ns.route("/employees/medical/all")
class EMResumeAll(Resource):  # noqa: F811
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = fetch_medicals(data_token)
        return out, code


@ns.route("/medical/employes/less")
class EMEmployeesListLess(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        code, data_out = fetch_employees_without_records(data_token)
        return data_out, code


@ns.route("/employee/medical")
class EMRegistry(Resource):
    @ns.expect(expected_headers_per, employee_exam_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeMedInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = insert_medical_db(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, employee_exam_model_update)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeMedUpdateForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = update_medical_db(data, data_token)
        return data_out, code

    @ns.expect(expected_headers_per, employee_exam_model_delete)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeMedDeleteForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        flag, error, result = delete_exam_med(data["id"], data_token)
        if flag:
            return {
                "data": {"id_exam": result},
                "msg": f"Registro médico eliminado correctamente (ID {result})",
                "error": None,
            }, 200
        else:
            return {
                "data": None,
                "msg": "No se pudo eliminar el registro médico",
                "error": error,
            }, 400


@ns.route("/employees/vacations/all")
class VacationsAll(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_all_vacations(data_token)
        if code == 200:
            return {"data": data, "msg": None, "error": None}, code
        else:
            return {"data": [], "msg": "No se pudieron obtener las vacaciones", "error": None}, code


@ns.route("/employee/vacations/<string:id_emp>")
class VacationsEmployeesID(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_vacations_employee(id_emp, data_token)
        if code == 200:
            return {"data": data, "msg": None, "error": None}, code
        else:
            return {
                "data": None,
                "msg": "No se encontraron vacaciones para el empleado",
                "error": None,
            }, code


@ns.route("/employee/vacation")
class VacationRegistry(Resource):
    @ns.expect(expected_headers_per, employee_vacation_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeVacInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        flag, error, result = insert_new_vacation(data, data_token)
        if flag:
            return {
                "data": {"id_vacation": result},
                "msg": f"Vacaciones registradas correctamente (ID {result})",
                "error": None,
            }, 201
        else:
            return {
                "data": None,
                "msg": "No se pudieron registrar las vacaciones",
                "error": error,
            }, 400

    @ns.expect(expected_headers_per, employee_vacation_model_insert)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeVacInsertForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        flag, error, result = update_vacation(data, data_token)
        if flag:
            return {
                "data": {"id_vacation": result},
                "msg": f"Vacaciones actualizadas correctamente (ID {result})",
                "error": None,
            }, 200
        else:
            return {
                "data": None,
                "msg": "No se pudieron actualizar las vacaciones",
                "error": error,
            }, 400

    @ns.expect(expected_headers_per, employee_vacation_model_delete)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = DeleteVacationForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        flag, error, result = delete_vacation(data["emp_id"], data_token)
        if flag:
            return {
                "data": {"id_vacation": result},
                "msg": f"Vacaciones eliminadas correctamente (ID {result})",
                "error": None,
            }, 200
        else:
            return {
                "data": None,
                "msg": "No se pudieron eliminar las vacaciones",
                "error": error,
            }, 400


@ns.route("/quizzes")
class TaskQuizzes(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, error, data_out = get_all_quizzes(data_token)
        if flag:
            return {"data": data_out, "msg": None, "error": None}, 200
        else:
            return {"data": [], "msg": "No se pudieron obtener los quizzes", "error": error}, 400


@ns.route("/quizz/<int:id_task>/evaluation")
class QuizzEvaluation(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_task):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = get_quizz_evaluation(id_task, data_token)
        return out, code


@ns.route("/employees/fichaje/all")
class EmployeesResume(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = fetch_fichajes_all_employees(data_token)
        return out, code


@ns.route("/employee/fichaje/<string:id_emp>")
class FichajeResume(Resource):  # noqa: F811
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = fetch_fichaje_employee(id_emp)
        return out, code


@ns.route("/payroll/files/update")
class FilesPayroll(Resource):
    @ns.expect(expected_headers_per, update_files_parser)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": None}, 400
        file = request.files["file"]
        year = request.form.get("year")
        month = request.form.get("month")
        emp_id = request.form.get("emp_id")
        key = request.form.get("key")
        if not all([year, month, emp_id, key]):
            return {
                "data": None,
                "msg": "Faltan campos requeridos: year, month, emp_id, key",
                "error": None,
            }, 400
        if not (file and file.filename):
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400
        filename = secure_filename(file.filename)
        filepath_download = os.path.join(tempfile.mkdtemp(), filename)
        file.save(filepath_download)
        data_out, code = create_payroll_file_attachment_api(
            {
                "filepath": filepath_download,
                "filename": filename,
                "year": year,
                "month": month,
                "emp_id": emp_id,
                "key": key,
            },
            data_token,
        )
        return data_out, code


@ns.route("/payroll/mail")
class CreateMailPayroll(Resource):
    @ns.expect(expected_headers_per, create_mail_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = CreateMailForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        code, msg_out = create_mail_payroll(data)
        return {"data": None, "msg": str(msg_out), "error": None}, code


@ns.route("/payroll/files/list/<int:emp_id>")
class DownloadFilesPayroll(Resource):
    @ns.expect(expected_headers_per)
    def get(self, emp_id):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        code, dicts_data = get_files_list_nomina_RH(emp_id, data_token)
        if code != 200:
            return {
                "data": None,
                "msg": "No se encontraron archivos de nómina",
                "error": None,
            }, code
        return {"data": dicts_data, "msg": None, "error": None}, code


@ns.route("/payroll/data/update")
class UpdatePayroll(Resource):
    @ns.expect(expected_headers_per, update_data_payroll_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = UpdateDataPayrollForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        code, data_out = update_data_employee(data, data_token)
        return data_out, code


@ns.route("/payroll/update/employees")
class UpdateEmployees(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        code, msg_out = update_payroll_list_employees(data_token)
        return {"data": None, "msg": msg_out, "error": None}, code


@ns.route("/fichajes/files")
class FilesFichaje(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, files = get_files_fichaje(data_token)
        if flag:
            return {"data": files, "msg": None, "error": None}, 200
        else:
            return {
                "data": [],
                "msg": "No se pudieron obtener los archivos de fichaje",
                "error": None,
            }, 400


@ns.route("/fichajes/data/fromfiles")
class DataFichajeFiles(Resource):
    @ns.expect(expected_headers_per, request_data_fichaje_files_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = DataFichajesFileForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        data_out, code = get_fichaje_data(data)
        return data_out, code


@ns.route("/upload/fichaje/file")
class UploadFicahjeFile(Resource):
    @ns.expect(expected_headers_per, expected_files)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": None, "msg": "No se detectó un archivo", "error": None}, 400
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(path_contract_files, filename))
            return {
                "data": {"filename": filename},
                "msg": "Archivo subido correctamente",
                "error": None,
            }, 200
        else:
            return {"data": None, "msg": "No se subió el archivo", "error": None}, 400


@ns.route("/download/employees/<string:status>")
class DownloadFileEMPs(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        filepath = create_csv_file_employees(status)
        return send_file(str(filepath), as_attachment=True)


@ns.route("/download/employees/medical")
class DownloadFileMedical(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, e, result = get_all_examenes(data_token)
        if not (isinstance(result, list) or isinstance(result, tuple)):
            return {
                "data": None,
                "msg": "Error al obtener los datos del empleado",
                "error": None,
            }, 400
        filepath = "files/medical.csv"
        with open(filepath, "w") as file:
            file.write("id_exam,nombre,sangre,estatus,aptitudes,fechas,apt_actual,emp_id\n")
            for item in result:
                id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = item
                fechas = fechas.replace(",", ";")
                aptitud = aptitud.replace(",", ";")
                file.write(
                    f"{id_exam},{nombre},{sangre},{status},{aptitud},{fechas},{apt_actual},{emp_id}\n"
                )
        return send_file(filepath, as_attachment=True)


@ns.route("/download/employees/vacations")
class DownloadFileVacations(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, error, data = get_vacations_data(data_token)
        filepath = "files/vacations.csv"
        if not (isinstance(data, list) or isinstance(data, tuple)):
            return {
                "data": None,
                "msg": "Error al obtener los datos del empleado",
                "error": None,
            }, 400
        with open(filepath, "w") as file:
            file.write("emp_id, Nombre, Apellido, fecha_inicio, body\n")
            for item in data:
                emp_id, name, l_name, date_admission, seniority = item
                seniority = seniority.replace(",", ";")
                file.write(f"{emp_id}, {name}, {l_name}, {date_admission}, {seniority}\n")
        return send_file(filepath, as_attachment=True)


@ns.route("/download/quizz/report")
class DownloadFileQuizzReport(Resource):
    @ns.expect(expected_headers_per, request_file_report_quizz_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = RequestFileReportQuizzForm.from_json(ns.payload)  # pyrefly: ignore
        if not validator.validate():
            return {
                "data": None,
                "msg": "Estructura de datos inválida",
                "error": validator.errors,
            }, 400
        data = validator.data
        code, data_out = generate_pdf_from_json(data, data_token)
        if code == 400:
            return {"data": None, "msg": data_out, "error": None}, code
        else:
            return send_file(data_out, as_attachment=True)
