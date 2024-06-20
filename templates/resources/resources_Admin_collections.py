# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 20/jun./2024  at 15:06 $'

from flask_restx import Namespace, Resource


ns = Namespace('GUI/api/v1/admin/presales')


@ns.route('/quotation/<string:id>')
class Movements(Resource):
    @ns.marshal_with(movements_output_model)
    def get(self, type_m):
        data, code = get_all_movements(type_m)
        data_out = {"data": data,
                    "msg": "Ok" if code == 200 else "Error"}
        return data_out, code