import json
import os

from flask import send_file, request

# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/nov./2023  at 17:29 $"

from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from static.Models.api_employee_models import (
    employees_info_model,
    employee_model_insert,
    employee_model_update,
    employee_model_delete,
    employees_examenes_model,
    employee_exam_model_insert,
    employee_exam_model_delete,
    employee_exam_model_update,
    employees_vacations_model,
    employee_vacation_model_insert,
    employee_vacation_model_delete,
    EmployeeInsertForm,
    EmployeeUpdateForm,
    EmployeeDeleteForm,
    EmployeeMedInsertForm,
    EmployeeMedUpdateForm,
    EmployeeMedDeleteForm,
    EmployeeVacInsertForm,
    DeleteVacationForm,
)
from static.Models.api_fichajes_models import (
    answer_files_fichajes_model,
    request_data_fichaje_files_model,
    answer_fichajes_model,
    expected_files,
    DataFichajesFileForm,
)
from static.Models.api_models import (
    employees_resume_model,
    expected_headers_per,
    RequestFileReportQuizzForm,
    request_file_report_quizz_model,
)
from static.Models.api_payroll_models import (
    update_files_model,
    UpdateFilesForm,
    create_mail_model,
    CreateMailForm,
    UpdateDataPayrollForm,
    update_data_payroll_model,
)
from static.constants import (
    path_contract_files,
    filepath_daemons,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_DB_midleware import (
    get_info_employees_with_status,
    get_info_employee_id,
    get_all_vacations,
    get_vacations_employee,
    create_csv_file_employees,
)
from templates.controllers.employees.em_controller import (
    get_all_examenes,
    delete_exam_med,
)
from templates.controllers.employees.employees_controller import (
    delete_employee,
)
from templates.controllers.employees.vacations_controller import (
    delete_vacation,
    get_vacations_data,
)
from templates.resources.midleware.Functions_midleware_RRHH import (
    get_files_fichaje,
    get_fichaje_data,
    insert_new_vacation,
    update_vacation,
    get_all_quizzes,
    generate_pdf_from_json,
    update_files_payroll,
    create_mail_payroll,
    update_payroll_list_employees,
    update_data_employee,
    get_files_list_nomina_RH,
    fetch_employees_without_records,
    fetch_medicals,
    fetch_medical_employee,
    create_new_employee_db,
    update_employee_db,
    insert_medical_db,
    update_medical_db,
    fetch_fichajes_all_employees,
    fetch_fichaje_employee,
)

ns = Namespace("GUI/api/v1/rrhh")


@ns.route("/employee")
class Employee(Resource):
    @ns.expect(expected_headers_per, employee_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_out, code = create_new_employee_db(data)
        return data_out, code

    @ns.expect(expected_headers_per, employee_model_update)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeUpdateForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_out, code = update_employee_db(data)
        return data_out, code

    @ns.expect(expected_headers_per, employee_model_delete)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = delete_employee(data["id"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400


@ns.route("/employee/info/<string:id_emp>")
class EmployeeInfo(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_info_employee_id(id_emp)
        return data_out, code


@ns.route("/employees/info/<string:status>")
class EmployeesInfo(Resource):
    @ns.marshal_with(employees_info_model)
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data_out, code = get_info_employees_with_status(status)
        return {"data": data_out}, code


@ns.route("/employee/medical/<string:id_emp>")
class EMResumeEmployees(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = fetch_medical_employee(id_emp)
        return out, code


@ns.route("/employees/medical/all")
class EMResumeAll(Resource):  # noqa: F811
    @ns.marshal_with(employees_examenes_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = fetch_medicals()
        return out, code


@ns.route("/medical/employes/less")
class EMEmployeesListLess(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        code, data_out = fetch_employees_without_records()
        return data_out, code


@ns.route("/employee/medical")
class EMRegistry(Resource):
    @ns.expect(expected_headers_per, employee_exam_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeMedInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_out, code = insert_medical_db(data)
        return data_out, code

    @ns.expect(expected_headers_per, employee_exam_model_update)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeMedUpdateForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        data_out, code = update_medical_db(data)
        return data_out, code

    @ns.expect(expected_headers_per, employee_exam_model_delete)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeMedDeleteForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = delete_exam_med(data["id"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400


@ns.route("/employees/vacations/all")
class VacationsAll(Resource):
    @ns.marshal_with(employees_vacations_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_all_vacations()
        if code == 200:
            return {"data": data, "msg": "ok"}, code
        else:
            return {"data": None, "msg": str(data)}, code


@ns.route("/employee/vacations/<string:id_emp>")
class VacationsEmployeesID(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_vacations_employee(id_emp)
        if code == 200:
            return data, code
        else:
            return data, code


@ns.route("/employee/vacation")
class VacationRegistry(Resource):
    @ns.expect(expected_headers_per, employee_vacation_model_insert)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeVacInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = insert_new_vacation(data)
        if flag:
            return {"data": str(result)}, 201
        else:
            return {"error": str(error)}, 400

    @ns.expect(expected_headers_per, employee_vacation_model_insert)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = EmployeeVacInsertForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = update_vacation(data)
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400

    @ns.expect(expected_headers_per, employee_vacation_model_delete)
    def delete(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = DeleteVacationForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flag, error, result = delete_vacation(data["emp_id"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400


@ns.route("/quizzes")
class TaskQuizzes(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, error, data_out = get_all_quizzes()
        if flag:
            return {"data": data_out, "msg": "ok"}, 200
        else:
            return {"data": [], "msg": "Error"}, 400


@ns.route("/employees/fichaje/all")
class EmployeesResume(Resource):
    @ns.marshal_with(employees_resume_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        out, code = fetch_fichajes_all_employees()
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
    @ns.expect(expected_headers_per, update_files_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = UpdateFilesForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        flags_daemons = json.load(open(filepath_daemons, "r"))
        if flags_daemons.get("update_files_nomina", False):
            msg = "Accion no permitida mientras se actualizan los datos."
            return {"data": None, "msg": msg}, 400
        code, msg = update_files_payroll(data)
        return {"data": None, "msg": msg}, code


@ns.route("/payroll/mail")
class CreateMailPayroll(Resource):
    @ns.expect(expected_headers_per, create_mail_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = CreateMailForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        code, msg = create_mail_payroll(data)
        return {"data": None, "msg": str(msg)}, code


@ns.route("/payroll/files/list/<int:emp_id>")
class DownloadFilesPayroll(Resource):
    @ns.expect(expected_headers_per)
    def get(self, emp_id):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        code, dicts_data = get_files_list_nomina_RH(emp_id)
        if code != 200:
            return {"data_raw": None, "msg": "No files"}, code
        return {"data_raw": dicts_data, "msg": "ok"}, code


@ns.route("/payroll/data/update")
class UpdatePayroll(Resource):
    @ns.expect(expected_headers_per, update_data_payroll_model)
    def put(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = UpdateDataPayrollForm.from_json(ns.payload)
        if not validator.validate():
            return {"errors": validator.errors}, 400
        data = validator.data
        code, data_out = update_data_employee(data)
        return data_out, code


@ns.route("/payroll/update/employees")
class UpdateEmployees(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        code, msg = update_payroll_list_employees()
        return {"data": None, "msg": str(msg)}, code


@ns.route("/fichajes/files")
class FilesFichaje(Resource):
    @ns.marshal_with(answer_files_fichajes_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, files = get_files_fichaje()
        if flag:
            return {"data": files, "msg": "ok"}, 200
        else:
            return {"data": None, "msg": "No files"}, 400


@ns.route("/fichajes/data/fromfiles")
class DataFichajeFiles(Resource):
    @ns.expect(expected_headers_per, request_data_fichaje_files_model)
    @ns.marshal_with(answer_fichajes_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = DataFichajesFileForm.from_json(ns.payload)
        if not validator.validate():
            return {"data": None, "msg": validator.errors}, 400
        data = validator.data
        code, out = get_fichaje_data(data)
        if code == 400:
            return {"data": None, "msg": out}, code
        else:
            return {"data": out, "msg": "ok"}, code


@ns.route("/upload/fichaje/file")
class UploadFicahjeFile(Resource):
    @ns.expect(expected_headers_per, expected_files)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        if "file" not in request.files:
            return {"data": "No se detecto un archivo"}, 401
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(path_contract_files, filename))
            return {"data": "Archivo subido correctamente"}, 200
        else:
            return {"data": "No se subio el archivo"}, 401


@ns.route("/download/employees/<string:status>")
class DownloadFileEMPs(Resource):
    @ns.expect(expected_headers_per)
    def get(self, status):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        filepath = create_csv_file_employees(status)
        return send_file(filepath, as_attachment=True)


@ns.route("/download/employees/medical")
class DownloadFileMedical(Resource):
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, e, result = get_all_examenes()
        filepath = "files/medical.csv"
        with open(filepath, "w") as file:
            file.write(
                "id_exam,nombre,sangre,estatus,aptitudes,fechas,apt_actual,emp_id\n"
            )
            for item in result:
                id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = (
                    item
                )
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
        flag, error, data = get_vacations_data()
        filepath = "files/vacations.csv"
        with open(filepath, "w") as file:
            file.write("emp_id, Nombre, Apellido, fecha_inicio, body\n")
            for item in data:
                emp_id, name, l_name, date_admission, seniority = item
                seniority = seniority.replace(",", ";")
                file.write(
                    f"{emp_id}, {name}, {l_name}, {date_admission}, {seniority}\n"
                )
        return send_file(filepath, as_attachment=True)


@ns.route("/download/quizz/report")
class DownloadFileQuizzReport(Resource):
    @ns.expect(expected_headers_per, request_file_report_quizz_model)
    def post(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        # noinspection PyUnresolvedReferences
        validator = RequestFileReportQuizzForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        code, data_out = generate_pdf_from_json(data)
        if code == 400:
            return {"data": None, "msg": data_out}, code
        else:
            return send_file(data_out, as_attachment=True)
