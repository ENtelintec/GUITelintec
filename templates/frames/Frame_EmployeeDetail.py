# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 15/ene./2024  at 11:06 $'

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from templates.Functions_Files import get_fichajes_resume_cache
from templates.frames.SubFrame_Plots import FramePlot


def create_stringvar(number: int, value: str):
    return [ttk.StringVar(value=value) for _ in range(number)]


def get_data_employees(status="ACTIVO"):
    columns = ("ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Dias Extra", "Total", "Primas",
               "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas")
    fichajes_resume, flag = get_fichajes_resume_cache("files/fichajes_resume_cache.pkl")
    print(fichajes_resume)
    if flag:
        return fichajes_resume, columns
    else:
        print("error at getting data resume")
        return None, None


class EmployeeDetails(ScrolledFrame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, autohide=True, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        # variables
        (self.emp_details, self.emp_lastname, self.emp_phone,
         self.emp_dep_id, self.emp_modality, self.emp_email, self.emp_contract,
         self.emp_admission, self.emp_rfc, self.emp_curp, self.emp_nss,
         self.emp_emergency, self.emp_department,
         self.emp_exam_id) = create_stringvar(number=14, value="")
        # label title
        ttk.Label(self, text='Detalles de Empleados',
                  font=("Helvetica", 32, "bold")).grid(row=0, column=0,
                                                       columnspan=4,
                                                       padx=10, pady=10)
        self.data_emp, columns = get_data_employees(status="ACTIVO")
        # tableview de empleados
        self.table = Tableview(self,
                               coldata=columns,
                               rowdata=self.data_emp,
                               paginated=True,
                               searchable=True,
                               autofit=True)
        self.table.grid(row=1, column=0, columnspan=10, padx=20, pady=10)
        self.table.view.bind("<Double-1>", self.on_double_click)
        ttk.Label(self, text="Detalles de empleado",
                  font=("Helvetica", 16, "bold")).grid(row=2, column=0,
                                                       columnspan=4, padx=20, pady=10)
        ttk.Label(self, textvariable=self.emp_details,
                  font=("Helvetica", 12, "normal")).grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        self.frame_plot = ttk.Frame(self)

    def on_double_click(self, event):
        (emp_id, emp_name, emp_contract, emp_absense, emp_late, emp_extra, emp_tot_extra,
         emp_primes, emp_det_abs, emp_det_late, emp_det_extra,
         emp_det_primes) = self.table.view.item(event.widget.selection()[0], "values")
        self.emp_details.set(f"ID: {emp_id} \n{emp_name.title()} \n"
                             f"Contrato: {emp_contract}\n"
                             f"Faltas: {emp_absense}\t Tardanzas: {emp_late}\n"
                             f"Dias Extra: {emp_extra}\t Total Extra: {emp_tot_extra}\n"
                             f"Primas: {emp_primes}\n")
        data = {
            "data": {"Faltas": emp_absense,
                     "Tardanzas": emp_late,
                     "Extra": emp_extra,
                     "Primas": emp_primes
                     },
            "title": f"Historial {emp_name.title()}",
            "ylabel": "Dias"
        }
        self.frame_plot = FramePlot(self, data, type_chart="bar")
        self.frame_plot.grid(row=4, column=0, columnspan=4, padx=20, pady=10)


if __name__ == '__main__':
    print('Hello World')
