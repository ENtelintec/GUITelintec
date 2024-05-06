from flask import send_file

# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:29 $'

from flask_restx import Namespace, Resource

from static.Models.api_employee_models import employees_info_model, employee_model, employee_model_insert, \
    employee_model_update, employee_model_delete, examenes_medicos_model, employees_examenes_model, \
    employee_exam_model_insert, employee_exam_model_delete, employee_exam_model_update, employees_vacations_model, \
    vacations_model, employee_vacation_model_insert, employee_vacation_model_delete
from static.Models.api_models import employees_resume_model, resume_model
from static.extensions import cache_file_resume_fichaje
from templates.Functions_DB_midleware import get_info_employees_with_status, get_info_employee_id, get_all_vacations, \
    get_vacations_employee, create_csv_file_employees
from templates.Functions_Files import get_fichajes_resume_cache
from templates.Functions_Text import parse_data
from templates.controllers.employees.em_controller import get_all_examenes, insert_new_exam_med, \
    update_aptitud_renovacion, delete_exam_med
from templates.controllers.employees.employees_controller import new_employee, update_employee, delete_employee
from templates.controllers.employees.vacations_controller import insert_vacation, update_registry_vac, delete_vacation, \
    get_vacations_data

ns = Namespace('GUI/api/v1/rrhh')


@ns.route('/employee')
class Employee(Resource):
    @ns.expect(employee_model_insert)
    def post(self):
        code, data = parse_data(ns.payload, 14)
        if code == 400:
            return {"data": None}, code
        flag, error, result = new_employee(data["info"]["name"], data["info"]["lastname"], data["info"]["curp"],
                                           data["info"]["phone"], data["info"]["modality"], data["info"]["dep"],
                                           data["info"]["contract"], data["info"]["admission"], data["info"]["rfc"],
                                           data["info"]["nss"], data["info"]["position"], data["info"]["status"],
                                           data["info"]["departure"], data["info"]["birthday"], data["info"]["legajo"],
                                           data["info"]["email"], data["info"]["emergency"])
        if flag:
            return {"data": str(result)}, 201
        else:
            return {"error": str(error)}, 400

    @ns.expect(employee_model_update)
    def put(self):
        code, data = parse_data(ns.payload, 14)
        if code == 400:
            return {"data": None}, code
        flag, error, result = update_employee(data["id"], data["info"]["name"], data["info"]["lastname"],
                                              data["info"]["curp"],
                                              data["info"]["phone"], data["info"]["modality"], data["info"]["dep"],
                                              data["info"]["contract"], data["info"]["admission"], data["info"]["rfc"],
                                              data["info"]["nss"], data["info"]["position"], data["info"]["status"],
                                              data["info"]["departure"], data["info"]["birthday"],
                                              data["info"]["legajo"],
                                              data["info"]["email"], data["info"]["emergency"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400

    @ns.expect(employee_model_delete)
    def delete(self):
        code, data = parse_data(ns.payload, 14)
        if code == 400:
            return {"data": None}, code
        flag, error, result = delete_employee(data["id"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400


@ns.route('/employee/info/<string:id_emp>')
class EmployeeInfo(Resource):
    @ns.marshal_with(employee_model)
    def get(self, id_emp):
        data_out, code = get_info_employee_id(id_emp)
        return data_out, code


@ns.route('/employees/info/<string:status>')
class EmployeesInfo(Resource):

    @ns.marshal_with(employees_info_model)
    def get(self, status):
        data_out, code = get_info_employees_with_status(status)
        return {"data": data_out}, code


@ns.route('/employee/medical/<string:id_emp>')
class EmployeesEMResume(Resource):
    @ns.marshal_with(examenes_medicos_model)
    def get(self, id_emp):
        flag, e, result = get_all_examenes()
        out = {"exist": False}
        if flag:
            code = 200
            for row in result:
                id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = row
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
                        "emp_id": emp_id
                    }
                    break
        else:
            out = {"exist": False}
            code = 400
        return out, code


@ns.route('/employees/medical/all')
class EmployeesEMResume(Resource):  # noqa: F811
    @ns.marshal_with(employees_examenes_model)
    def get(self):
        flag, e, result = get_all_examenes()
        out = {"data": None}
        if flag:
            code = 200
            data_out = []
            for row in result:
                id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = row
                data_out.append({
                    "exist": True,
                    "id_exam": id_exam,
                    "name": nombre,
                    "blood": sangre,
                    "status": status,
                    "aptitudes": aptitud,
                    "dates": fechas,
                    "apt_last": apt_actual,
                    "emp_id": emp_id
                })
            out["data"] = data_out
        else:
            out = {"exist": False}
            code = 400
        return out, code


@ns.route('/employee/medical')
class EmployeesEMRegistry(Resource):
    @ns.expect(employee_exam_model_insert)
    def post(self):
        code, data = parse_data(ns.payload, 15)
        flag, error, result = insert_new_exam_med(data["info"]["name"], data["info"]["blood"], data["info"]["status"],
                                                  data["info"]["aptitudes"], data["info"]["dates"],
                                                  data["info"]["apt_actual"], data["info"]["emp_id"])
        if flag:
            return {"data": str(result)}, 201
        else:
            return {"error": str(error)}, 400

    @ns.expect(employee_exam_model_update)
    def put(self):
        code, data = parse_data(ns.payload, 15)
        flag, error, result = update_aptitud_renovacion(data["info"]["aptitudes"], data["info"]["dates"],
                                                        data["info"]["apt_actual"], data["id"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400

    @ns.expect(employee_exam_model_delete)
    def delete(self):
        code, data = parse_data(ns.payload, 15)
        flag, error, result = delete_exam_med(data["id"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400


@ns.route('/employees/vacations/all')
class EmployeesVacations(Resource):
    @ns.marshal_with(employees_vacations_model)
    def get(self):
        data, code = get_all_vacations()
        if code == 200:
            return {"data": data}, code
        else:
            return {"data": None}, code


@ns.route('/employee/vacations/<string:id_emp>')
class EmployeesVacationsID(Resource):
    @ns.marshal_with(vacations_model)
    def get(self, id_emp):
        data, code = get_vacations_employee(id_emp)
        if code == 200:
            return data, code
        else:
            return data, code


@ns.route('/employee/vacation')
class EmployeesVacationRegistry(Resource):
    @ns.expect(employee_vacation_model_insert)
    def post(self):
        code, data = parse_data(ns.payload, 16)
        if data["seniority"] is None:
            return {"data": "Error en la estructura del diccionario seniority"}, 400
        flag, error, result = insert_vacation(data["emp_id"], data["seniority"])
        if flag:
            return {"data": str(result)}, 201
        else:
            return {"error": str(error)}, 400

    @ns.expect(employee_vacation_model_insert)
    def put(self):
        code, data = parse_data(ns.payload, 16)
        if data["seniority"] is None:
            return {"data": "Error en la estructura del diccionario seniority"}, 400
        flag, error, result = update_registry_vac(data["emp_id"], data["seniority"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400

    @ns.expect(employee_vacation_model_delete)
    def delete(self):
        code, data = parse_data(ns.payload, 16)
        flag, error, result = delete_vacation(data["emp_id"])
        if flag:
            return {"data": str(result)}, 200
        else:
            return {"error": str(error)}, 400


@ns.route('/employees/fichaje/all')
class EmployeesResume(Resource):
    @ns.marshal_with(employees_resume_model)
    def get(self):
        fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje)
        print(fichajes_resume)
        if flag:
            out_aux = []
            for item in fichajes_resume:
                out_aux.append({
                    "id": item[0],
                    "name": item[1],
                    "contract": item[2],
                    "absences": item[3],
                    "late": item[4],
                    "extra": item[5],
                    "total_h_extra": item[6],
                    "primes": item[7],
                    "absences_details": item[8],
                    "late_details": item[9],
                    "extra_details": item[10],
                    "primes_details": item[11]
                })
            out = {
                "data": out_aux
            }
            code = 200
        else:
            out = {
                "data": [None]
            }
            code = 400
        return out, code


@ns.route('/employee/fichaje/<string:id_emp>')
class EmployeesResume(Resource):  # noqa: F811
    @ns.marshal_with(resume_model)
    def get(self, id_emp):
        fichajes_resume, flag = get_fichajes_resume_cache(cache_file_resume_fichaje)
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
                        "extra": item[5],
                        "total_h_extra": item[6],
                        "primes": item[7],
                        "absences_details": item[8],
                        "late_details": item[9],
                        "extra_details": item[10],
                        "primes_details": item[11]
                    }
                    code = 200
                    break
        else:
            out = None
            code = 400
        return out, code


@ns.route('/download/employees/<string:status>')
class DownloadFileEMPs(Resource):
    def get(self, status):
        filepath = create_csv_file_employees(status)
        return send_file(filepath, as_attachment=True)


@ns.route('/download/employees/medical')
class DownloadFileMedical(Resource):
    def get(self):
        flag, e, result = get_all_examenes()
        filepath = "files/medical.csv"
        with (open(filepath, "w")) as file:
            file.write("id_exam,nombre,sangre,estatus,aptitudes,fechas,apt_actual,emp_id\n")
            for item in result:
                id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = item
                fechas = fechas.replace(",", ";")
                aptitud = aptitud.replace(",", ";")
                file.write(f"{id_exam},{nombre},{sangre},{status},{aptitud},{fechas},{apt_actual},{emp_id}\n")
        return send_file(filepath, as_attachment=True)


@ns.route('/download/employees/vacations')
class DownloadFileVacations(Resource):
    def get(self):
        flag, error, data = get_vacations_data()
        filepath = "files/vacations.csv"
        with (open(filepath, "w")) as file:
            file.write("emp_id, Nombre, Apellido, fecha_inicio, body\n")
            for item in data:
                emp_id, name, l_name, date_admission, seniority = item
                seniority = seniority.replace(",", ";")
                file.write(f"{emp_id}, {name}, {l_name}, {date_admission}, {seniority}\n")
        return send_file(filepath, as_attachment=True)
