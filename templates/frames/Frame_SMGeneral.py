# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/abr./2024  at 17:11 $'

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.Functions_AuxFiles import get_all_sm_entries, get_all_sm_products
from templates.Functions_SQL import get_sm_clients, get_sm_employees
from templates.frames.Frame_SMCreate import FrameSMCreate
from templates.frames.Frame_SMDashboard import SMDashboard


def load_data():
    data_sm, columns_sm = get_all_sm_entries(filter_status=False)
    flag, error, employees = get_sm_employees()
    flag, error, clients = get_sm_clients()
    products, columns_products = get_all_sm_products()
    data_dic = {
        'data_sm': data_sm,
        'columns_sm': columns_sm,
        'employees': employees,
        'clients': clients,
        'products': products,
        'columns_products': columns_products
    }
    return data_dic


class SMFrame(ScrolledFrame):
    def __init__(self, master=None, settings=None, department=None, id_emp=None, **kw):
        super().__init__(master, **kw)
        self.columnconfigure(0, weight=1)
        self.id_emp = id_emp
        self.department = department
        self.settings = settings
        data_dic = load_data()
        nb = ttk.Notebook(self)
        frame_1 = SMDashboard(nb, data=data_dic["data_sm"], columns=data_dic["columns_sm"])
        frame_2 = FrameSMCreate(nb, id_emp=self.id_emp, department=self.department, settings=self.settings, data=data_dic)
        nb.add(frame_1, text='Dashboard')
        nb.add(frame_2, text='Crear-editar-eliminar')
        nb.grid(row=0, column=0, sticky="nswe", padx=(5, 20), pady=15)


