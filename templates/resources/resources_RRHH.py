# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:29 $'

from flask_restx import Namespace, Resource

from static.api_models import employees_info_model, employees_resume_model, resume_model, examenes_medicos_model, \
    employes_examenes_model
from static.extensions import cache_file_resume_fichaje
from templates.Functions_Files import get_fichajes_resume_cache
from templates.Functions_SQL import get_all_data_employees, get_all_examenes

ns = Namespace('GUI/api/v1/rrhh')


@ns.route('/employees/info/<string:status>')
class EmployeesInfo(Resource):

    @ns.marshal_with(employees_info_model)
    def get(self, status):
        flag, error, result = get_all_data_employees(status)
        columns = ("ID", "Nombre", "Apellido", "Teléfono",
                   "Dep_Id", "Modalidad", "Email", "Contrato", "Admisión",
                   "RFC", "CURP", "NSS", "C. Emergencia", " Departamento",
                   "Exam_id")
        if flag:
            return {"columns": columns, "data": result}, 200
        else:
            return {"error": error}, 400


@ns.route('/employees/resume')
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
                    "contract":  item[2],
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
                "data":  out_aux
            }
            code = 200
        else:
            out = {
                "data": [None]
            }
            code = 400
        return out, code


@ns.route('/employees/resume/<string:id_emp>')
class EmployeesResume(Resource):
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


@ns.route('/employees/em/<string:id_emp>')
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


@ns.route('/employees/em')
class EmployeesEMResume(Resource):
    @ns.marshal_with(employes_examenes_model)
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
