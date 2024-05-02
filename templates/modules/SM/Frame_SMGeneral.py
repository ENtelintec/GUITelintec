# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/abr./2024  at 17:11 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from static.extensions import ventanasApp_path
from templates.Functions_AuxFiles import get_all_sm_entries, get_all_sm_products
from templates.Functions_SQL import get_sm_clients, get_sm_employees
from templates.modules.SM.SubFrame_SMCreate import FrameSMCreate

permissions_supper_SM = json.load(open(ventanasApp_path, encoding="utf-8"))["permissions_supper_SM"]


def load_data(is_super=False, emp_id=None):
    data_sm, columns_sm = get_all_sm_entries(filter_status=False, is_supper=True, emp_id=emp_id)
    data_sm_not_supper = []
    if not is_super:
        data_sm_not_supper = [data for data in data_sm if data[7] == emp_id]
    flag, error, employees = get_sm_employees()
    flag, error, clients = get_sm_clients()
    products, columns_products = get_all_sm_products()
    data_dic = {
        'data_sm': data_sm,
        'columns_sm': columns_sm,
        'employees': employees,
        'clients': clients,
        'products': products,
        'columns_products': columns_products,
        'data_sm_not_supper': data_sm_not_supper
    }
    return data_dic


class SMFrame(ScrolledFrame):
    def __init__(self, master=None, settings=None, department=None, id_emp=None, data_emp=None, *args, **kwargs):
        super().__init__(master)
        self.permissions = data_emp["permissions"]
        self.is_supper_user = self.check_permissions()
        self.columnconfigure(0, weight=1)
        self.id_emp = id_emp
        self.data_emp = data_emp
        self.department = department
        self.settings = settings
        data_dic = load_data(self.is_supper_user, self.id_emp)
        nb = ttk.Notebook(self)
        # frame_1 = SMDashboard(nb, data=data_dic, data_emp=data_emp)
        frame_2 = FrameSMCreate(nb, id_emp=self.id_emp, permissions=data_emp["permissions"], settings=self.settings, data=data_dic)
        # nb.add(frame_1, text='Dashboard')
        nb.add(frame_2, text='Crear-Editar-Eliminar')
        nb.grid(row=0, column=0, sticky="nswe", padx=(5, 20), pady=15)

    def check_permissions(self):
        for item in self.permissions.values():
            if item in permissions_supper_SM:
                return True
        return False
