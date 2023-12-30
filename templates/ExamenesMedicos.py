# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/dic./2023  at 17:12 $'

from tkinter import BooleanVar

import ttkbootstrap as ttk

from templates.FunctionsSQL import insert_new_exam_med


def create_booleanvar(number: int):
    """
    Create a stringvar with the number provided initialized with ""
    :param number: number to create the stringvar
    :return: tuple
    """
    var = []
    for i in range(number):
        var.append(BooleanVar(value=True))
    return tuple(var)


class ExamenesMedicosFrame(ttk.Frame):

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=ttk.BOTH, expand=True)
        # -------------------create title-----------------
        ttk.Label(self, text='Examenes Medicos', font=('Arial', 24)).grid(row=0, column=0, sticky="nswe")
        # -------------------create varaibles-----------------
        (self.var_name, self.var_blood, self.var_status, self.var_aptitud, self.var_renovacion,
         self.var_apt_actual, self.var_last_date, self.emp_id) = create_booleanvar(8)
        # -------------------create check btns-----------------
        btn_check_name = ttk.Checkbutton(self, text="Nombre: ", variable=self.var_name,
                                         bootstyle="round-toggle",
                                         command=self.change_vars_inputs)
        btn_check_name.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)
        btn_check_blood = ttk.Checkbutton(self, text="Tipo Sangre: ", variable=self.var_blood,
                                          bootstyle="round-toggle",
                                          command=self.change_vars_inputs)
        btn_check_blood.grid(row=2, column=0, sticky="nswe", padx=5, pady=5)
        btn_check_status = ttk.Checkbutton(self, text="Estado: ", variable=self.var_status,
                                           bootstyle="round-toggle",
                                           command=self.change_vars_inputs)
        btn_check_status.grid(row=3, column=0, sticky="nswe", padx=5, pady=5)
        btn_check_aptitud = ttk.Checkbutton(self, text="Aptitud actual: ", variable=self.var_aptitud,
                                            bootstyle="round-toggle",
                                            command=self.change_vars_inputs)
        btn_check_aptitud.grid(row=4, column=0, sticky="nswe", padx=5, pady=5)
        btn_check_last_date = ttk.Checkbutton(self, text="Ultima Fecha: ", variable=self.var_last_date,
                                              bootstyle="round-toggle",
                                              command=self.change_vars_inputs)
        btn_check_last_date.grid(row=5, column=0, sticky="nswe", padx=5, pady=5)
        btn_check_emp_id = ttk.Checkbutton(self, text="ID Empleado: ", variable=self.emp_id,
                                           bootstyle="round-toggle",
                                           command=self.change_vars_inputs)
        btn_check_emp_id.grid(row=6, column=0, sticky="nswe", padx=5, pady=5)
        # -------------------create entrys-----------------
        self.entry_name = ttk.Entry(self, bootstyle="info")
        self.entry_name.grid(row=1, column=1, sticky="nswe", padx=5, pady=5)
        self.entry_blood = ttk.Combobox(self, bootstyle="info", state="readonly")
        self.entry_blood["values"] = ("A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-")
        self.entry_blood.current(0)
        self.entry_blood.grid(row=2, column=1, sticky="nswe", padx=5, pady=5)
        self.entry_status = ttk.Combobox(self, bootstyle="info", state="readonly")
        self.entry_status["values"] = ("Activo", "Inactivo")
        self.entry_status.current(0)
        self.entry_status.grid(row=3, column=1, sticky="nswe", padx=5, pady=5)
        self.entry_aptitud = ttk.Combobox(self, bootstyle="info", state="readonly")
        self.entry_aptitud["values"] = ("1", "2", "3", "4")
        self.entry_aptitud.current(0)
        self.entry_aptitud.grid(row=4, column=1, sticky="nswe", padx=5, pady=5)
        self.entry_last_date = ttk.DateEntry(self, bootstyle="info")
        self.entry_last_date.grid(row=5, column=1, sticky="nswe", padx=5, pady=5)
        self.entry_emp_id = ttk.Entry(self, bootstyle="info")
        self.entry_emp_id.grid(row=6, column=1, sticky="nswe", padx=5, pady=5)
        # -------------------create buttons-----------------
        btn_insert = ttk.Button(self, text="Insertar", bootstyle="info",  command=self.insert_data_to_db)
        btn_insert.grid(row=7, column=0, sticky="nswe", padx=5, pady=5)

    def insert_data_to_db(self):
        """
        Insert data to the database
        :return:
        """
        # retrieve data from entrys
        name = self.entry_name.get() if self.var_name.get() else None
        blood = self.entry_blood.get() if self.var_blood.get() else None
        status = self.entry_status.get() if self.var_status.get() else None
        aptitud = int(self.entry_aptitud.get()) if self.var_aptitud.get() else None
        last_date = self.entry_last_date.entry.get() if self.var_last_date.get() else None
        emp_id = int(self.entry_emp_id.get()) if self.emp_id.get() else None
        # insert data to database
        if (name is not None and blood is not None and status is not None and aptitud is not None
                and last_date is not None and emp_id is not None):
            apt_list = [aptitud]
            renovacion = [last_date]
            flag, error, out = insert_new_exam_med(name, blood, status, apt_list, renovacion,
                                                   aptitud, last_date, emp_id)

    def change_vars_inputs(self):
        """
        Change the state of the entrys depending on the checkbuttons
        :return:
        """
        if self.var_name.get():
            self.entry_name.configure(state="normal")
        else:
            self.entry_name.configure(state="disabled")
        if self.var_blood.get():
            self.entry_blood.configure(state="normal")
        else:
            self.entry_blood.configure(state="disabled")
        if self.var_status.get():
            self.entry_status.configure(state="normal")
        else:
            self.entry_status.configure(state="disabled")
        if self.var_aptitud.get():
            self.entry_aptitud.configure(state="normal")
        else:
            self.entry_aptitud.configure(state="disabled")
        if self.var_last_date.get():
            self.entry_last_date.configure(state="normal")
        else:
            self.entry_last_date.configure(state="disabled")
        if self.emp_id.get():
            self.entry_emp_id.configure(state="normal")
        else:
            self.entry_emp_id.configure(state="disabled")


if __name__ == '__main__':
    print('Hello World')
