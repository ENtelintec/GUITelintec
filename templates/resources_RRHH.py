# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:29 $'

from flask_restx import Namespace, Resource

from static.api_models import employees_indo_model
from templates.FunctionsSQL import get_all_data_employees

ns = Namespace('GUI/api/rrhh')


@ns.route('/employees/info/<string:status>')
class EmployeesInfo(Resource):

    @ns.marshal_with(employees_indo_model)
    def get(self, status):
        flag, error, result = get_all_data_employees(status)
        columns = ("ID", "Nombre", "Apellido", "Telefono",
                   "Dep_Id", "Modalidad", "Email", "Contrato", "Admision",
                   "RFC", "CURP", "NSS", "C. Emergencia", " Departamento",
                   "Exam_id")
        if flag:
            return {"columns": columns, "data": result}
        else:
            return {"error": error}