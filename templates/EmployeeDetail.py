# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 15/ene./2024  at 11:06 $'

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.FunctionsSQL import get_all_data_employees


def create_stringvar(number: int, value: str):
    return [ttk.StringVar(value=value) for _ in range(number)]


class EmployeeDetails(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
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
        self.data_emp, columns = self.get_data_employees(status="ACTIVO")
        # tableview de empleados
        self.table = Tableview(self,
                               coldata=columns,
                               rowdata=self.data_emp,
                               paginated=False,
                               searchable=True,
                               autofit=True)
        self.table.grid(row=1, column=0, columnspan=4, padx=20, pady=10)
        self.table.view.bind("<Double-1>", self.on_double_click)
        ttk.Label(self, text="Detalles de empleado",
                  font=("Helvetica", 16, "bold")).grid(row=2, column=0,
                                                       columnspan=4, padx=20, pady=10)
        ttk.Label(self, textvariable=self.emp_details,
                  font=("Helvetica", 12, "normal")).grid(row=3, column=0, sticky="w", padx=20, pady=5)

    def on_double_click(self, event):
        print("selected", event.widget.selection())
        print(self.table.view.item(event.widget.selection()[0], "values"))
        (emp_id, emp_name, emp_lastname, emp_phone, emp_dep_id, emp_modality,
         emp_email, emp_contract, emp_admission, emp_rfc, emp_curp, emp_nss,
         emp_emergency, emp_department, emp_exam_id) = self.table.view.item(
            event.widget.selection()[0], "values")
        self.emp_details.set(f"ID: {emp_id} - {emp_name.title()} {emp_lastname.title()}\n"
                             f"Department: {emp_department}\t Dep. ID: {emp_dep_id}\t Contrato: {emp_contract}\n"
                             f"Modalidad: {emp_modality}\t Telefono: {emp_phone}\t email: {emp_email}\n"
                             f"C. Emergencia: {emp_emergency}\t Examen medico: {emp_exam_id}")

    def get_data_employees(self, status="ACTIVO"):
        flag, error, result = get_all_data_employees(status)
        columns = ("ID", "Nombre", "Apellido", "Telefono",
                   "Dep_Id", "Modalidad", "Email", "Contrato", "Admision",
                   "RFC", "CURP", "NSS", "C. Emergencia", " Departamento",
                   "Exam_id")
        if flag:
            return result, columns
        else:
            print(error)
            return None, None


if __name__ == '__main__':
    print('Hello World')
