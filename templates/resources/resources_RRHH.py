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
)
from static.constants import (
    cache_file_resume_fichaje_path,
    quizzes_RRHH,
    path_contract_files,
)
from templates.resources.methods.Functions_Aux_Login import token_verification_procedure
from templates.resources.midleware.Functions_DB_midleware import (
    get_info_employees_with_status,
    get_info_employee_id,
    get_all_vacations,
    get_vacations_employee,
    create_csv_file_employees,
)
from templates.misc.Functions_Files import get_fichajes_resume_cache
from templates.controllers.employees.em_controller import (
    get_all_examenes,
    insert_new_exam_med,
    update_aptitud_renovacion,
    delete_exam_med,
)
from templates.controllers.employees.employees_controller import (
    new_employee,
    update_employee,
    delete_employee,
)
from templates.controllers.employees.vacations_controller import (
    delete_vacation,
    get_vacations_data,
)
from templates.resources.midleware.Functions_midleware_RRHH import (
    get_files_fichaje,
    get_fichaje_data,
    get_files_list_nomina,
    insert_new_vacation,
    update_vacation,
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
        if not flag:
            return {"error": data_token}, 400
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
            data["info"]["email"],
            data["info"]["emergency"],
        )
        if flag:
            return {"data": str(result)}, 201
        else:
            return {"error": str(error)}, 400

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
            data["info"]["email"],
            data["info"]["emergency"],
        )
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400

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
class EmployeesEMResume(Resource):
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, e, result = get_all_examenes()
        out = {"exist": False}
        if flag:
            code = 200
            for row in result:
                id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = (
                    row
                )
                if str(emp_id) == id_emp:
                    out = {
                        "exist": True,
                        "id_exam": id_exam,
                        "name": nombre,
                        "blood": sangre,
                        "status": status,
                        "aptitudes": aptitud,
                        "dates": fechas,
                        "apt_last": apt_actual,
                        "emp_id": emp_id,
                    }
                    break
        else:
            out = {"exist": False}
            code = 400
        return out, code


@ns.route("/employees/medical/all")
class EmployeesEMResume(Resource):  # noqa: F811
    @ns.marshal_with(employees_examenes_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        flag, e, result = get_all_examenes()
        out = {"data": None}
        if flag:
            code = 200
            data_out = []
            for row in result:
                id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = (
                    row
                )
                data_out.append(
                    {
                        "exist": True,
                        "id_exam": id_exam,
                        "name": nombre,
                        "blood": sangre,
                        "status": status,
                        "aptitudes": json.loads(aptitud),
                        "dates": json.loads(fechas),
                        "apt_last": apt_actual,
                        "emp_id": emp_id,
                    }
                )
            out["data"] = data_out
        else:
            out = {"data": []}
            code = 400
        return out, code


@ns.route("/employee/medical")
class EmployeesEMRegistry(Resource):
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
        flag, error, result = insert_new_exam_med(
            data["info"]["name"],
            data["info"]["blood"],
            data["info"]["status"],
            data["info"]["aptitudes"],
            data["info"]["dates"],
            data["info"]["apt_actual"],
            data["info"]["emp_id"],
        )
        if flag:
            return {"data": str(result)}, 201
        else:
            return {"error": str(error)}, 400

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
        flag, error, result = update_aptitud_renovacion(
            data["info"]["aptitudes"],
            data["info"]["dates"],
            data["info"]["apt_actual"],
            data["id"],
        )
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400

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
class EmployeesVacations(Resource):
    @ns.marshal_with(employees_vacations_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        data, code = get_all_vacations()
        if code == 200:
            return {"data": data}, code
        else:
            return {"data": None}, code


@ns.route("/employee/vacations/<string:id_emp>")
class EmployeesVacationsID(Resource):
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
class EmployeesVacationRegistry(Resource):
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


@ns.route("/employees/fichaje/all")
class EmployeesResume(Resource):
    @ns.marshal_with(employees_resume_model)
    @ns.expect(expected_headers_per)
    def get(self):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        fichajes_resume, flag = get_fichajes_resume_cache(
            cache_file_resume_fichaje_path, is_hard_update=True
        )
        if flag:
            out_aux = []
            for item in fichajes_resume:
                out_aux.append(
                    {
                        "id": item[0],
                        "name": item[1],
                        "contract": item[2],
                        "absences": item[3],
                        "late": item[4],
                        "total_late": item[5],
                        "extra": item[6],
                        "total_h_extra": item[7],
                        "primes": item[8],
                        "absences_details": item[9],
                        "late_details": item[10],
                        "extra_details": item[11],
                        "primes_details": item[12],
                        "normals_details": item[13],
                        "earlies_details": item[14],
                        "pasiva_details": item[15],
                    }
                )
            out = {"data": out_aux}
            code = 200
        else:
            out = {"data": [None]}
            code = 400
        return out, code


@ns.route("/employee/fichaje/<string:id_emp>")
class EmployeesResume(Resource):  # noqa: F811
    @ns.expect(expected_headers_per)
    def get(self, id_emp):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        fichajes_resume, flag = get_fichajes_resume_cache(
            cache_file_resume_fichaje_path, is_hard_update=True
        )
        if flag:
            out = {}
            code = 404
            for item in fichajes_resume:
                if str(item[0]) == id_emp:
                    out = {
                        "id": item[0],
                        "name": item[1],
                        "contract": item[2],
                        "absences": item[3],
                        "late": item[4],
                        "total_late": item[5],
                        "extra": item[6],
                        "total_h_extra": item[7],
                        "primes": item[8],
                        "absences_details": item[9],
                        "late_details": item[10],
                        "extra_details": item[11],
                        "primes_details": item[12],
                        "normals_details": item[13],
                        "earlies_details": item[14],
                        "pasiva_details": item[15],
                    }
                    code = 200
                    break
        else:
            out = None
            code = 400
        return out, code


@ns.route("/payroll/files/list/<int:emp_id>")
class DownloadFilesPayroll(Resource):
    @ns.expect(expected_headers_per)
    def get(self, emp_id):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        code, data_out = get_files_list_nomina(emp_id)
        if code != 200:
            return {"data": None, "msg": "No files"}, code
        return {"data": data_out, "msg": "ok"}, code


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


@ns.route("/download/quizz/<int:type_q>")
class DownloadFileQuizz(Resource):
    @ns.expect(expected_headers_per)
    def get(self, type_q):
        flag, data_token, msg = token_verification_procedure(request, department="rrhh")
        if not flag:
            return {"error": msg if msg != "" else "No autorizado. Token invalido"}, 401
        try:
            quizz = quizzes_RRHH[str(type_q)]
            return send_file(quizz["path"], as_attachment=True)
        except Exception as e:
            return {"data": f"Error en el tipo de quizz: {str(e)}"}, 400
