# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/ene./2024  at 15:22 $'

import json
from datetime import datetime
from tkinter import BooleanVar
from tkinter import filedialog
from tkinter.ttk import Style

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from templates.Functions_Files import get_ExMed_cache_file, update_ExMed_cache_file
from templates.Functions_SQL import insert_new_exam_med, get_id_employee, update_aptitud_renovacion, \
    get_aptitud_renovacion, update_aptitud, update_renovacion, get_renovacion, get_all_examenes, get_aptitud, \
    update_status_EM, get_vacations_data, get_name_employee
from templates.Funtions_Utils import create_label, create_Combobox
from static.extensions import cache_file_EM_path


def load_data_vacations(option=1):
    columns = ["emp_id", "name", "l_name", "date_admission", "seniority"]
    flag, error, data = get_vacations_data()
    print(data)
    return data, columns


def get_aptitud_from_data(data, id_emp):
    for index, entry in enumerate(data):
        id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = entry
        if emp_id == id_emp:
            return id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id, index
    return None, None, None, None, None, None, None, None, None


def get_entry_from_data(data, id_emp):
    for index, entry in enumerate(data):
        id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = entry
        if emp_id == id_emp:
            return id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id, index
    return None, None, None, None, None, None, None, None, None


def set_dateEntry_new_value(master, entry, value, row, column, padx, pady, sticky):
    entry.destroy()
    entry = ttk.DateEntry(master,
                          startdate=value)
    entry.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)
    return entry


class VacationsFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # self.pack(fill=ttk.BOTH, expand=True)
        self.seniority_dict = None
        self.columnconfigure((0, 1), weight=1)
        # self.rowconfigure(0, weight=1)
        # -------------------create title-----------------
        ttk.Label(self, text='Vacaciones', font=("Helvetica", 32, "bold")).grid(
            row=0, column=0, columnspan=2, padx=20, pady=30)
        # -------------------create varaibles-----------------
        self.var_label_id_name = ttk.StringVar(value="")
        self.data, columns = load_data_vacations(1)
        self.name_emp = ttk.StringVar()
        self.aptitud_act = ttk.StringVar()
        self.examen_prox = ttk.StringVar()
        self.antiguedad = ttk.StringVar(value="")
        self.seniority_string = ttk.StringVar(value="")
        self.pagoprima_string = ttk.StringVar(value="")
        self.names_emp = []
        self.df = None
        self.table_data = []
        #  -------------------create input widgets-----------------
        (self.wentry_emp_id, self.wentry_year, self.wentry_pendientes,
         self.wentry_prima, self.wentry_prima_pago, self.wentry_comentarios) = self.create_input_widgets()
        # -------------------create buttons-----------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, columnspan=2, padx=20, pady=20)
        frame_buttons.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(frame_buttons, text="Probar ID", command=self._test_id).grid(
            row=0, column=0, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Insertar nuevo registro", command=self._update_registry_to_emp).grid(
            row=0, column=1, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Borrar registro", command=self._delete_registry_from_emp).grid(
            row=0, column=2, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Actualizar empleados", command=self._update_emps).grid(
            row=0, column=3, padx=5, pady=0)
        # -------------------table and info data-----------------
        self.frame_info = ttk.Frame(self)
        self.frame_info.grid(row=3, column=0, columnspan=2, sticky='nsew')
        self.frame_info.columnconfigure(0, weight=1)
        ttk.Label(self.frame_info, text="Vacaciones", font=("Helvetica", 18, "normal")).grid(
            row=0, column=0)
        # -------------------create tableview for data-----------------
        self.grouped_table = Tableview(self.frame_info)
        self.loadTable(self.data)
        detalles_emp = ttk.LabelFrame(self.frame_info, text="Detalles del Examen medico del empleado")
        detalles_emp.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(detalles_emp, textvariable=self.name_emp).grid(
            row=4, column=0, sticky="w")
        ttk.Label(detalles_emp, textvariable=self.aptitud_act).grid(
            row=5, column=0, sticky="w")
        ttk.Label(detalles_emp, textvariable=self.examen_prox).grid(
            row=6, column=0, sticky="w")
        # self.all_medicalExam = ExamenesMedicosMain(self, self.data)
        # self.all_medicalExam.grid(row=3, column=0, columnspan=2, sticky='nsew')
        # -------------------export medical examination report-----------------

    def _delete_registry_from_emp(self):
        emp_id = self.wentry_emp_id.get()
        for item in self.data:
            id_emp, name, lastname, date_admission, seniority = item
            if emp_id == id_emp:
                self.data.remove(item)
                break
        self.loadTable(self.data)
        self.wentry_emp_id.delete(0, 'end')
        self.name_emp.set("")
        self.aptitud_act.set("")
        self.examen_prox.set("")
        self.antiguedad.set("")
        self.seniority_string.set("")
        self.pagoprima_string.set("")
        self.wentry_pendientes.delete(0, 'end')
        self.wentry_prima.delete(0, 'end')
        self.wentry_prima_pago.delete(0, 'end')
        self.wentry_comentarios.delete(0, 'end')

    def _update_emps(self):
        emp_id = self.wentry_emp_id.get()
        for item in self.data:
            id_emp, name, lastname, date_admission, seniority = item
            if emp_id == id_emp:
                self.data.remove(item)
                break
        self.loadTable(self.data)
        self.wentry_emp_id.delete(0, 'end')
        self.name_emp.set("")
        self.aptitud_act.set("")
        self.examen_prox.set("")
        self.antiguedad.set("")
        self.seniority_string.set("")
        self.pagoprima_string.set("")
        self.wentry_pendientes.delete(0, 'end')
        self.wentry_prima.delete(0, 'end')
        self.wentry_prima_pago.delete(0, 'end')
        self.wentry_comentarios.delete(0, 'end')
        self.loadTable(self.data)

    def _test_id(self):
        columns = ["emp_id", "name", "l_name", "date_admission", "seniority"]
        emp_id = self.wentry_emp_id.get()
        name = None
        for item in self.data:
            id_emp, name, lastname, date_admission, seniority = item
            if emp_id == emp_id:
                name = name.upper() + " " + lastname.upper()
                break
        if name is not None:
            Messagebox.show_info(
                title="Exito",
                message=f"El id del empleado es correcto."
            )
            self.name_emp.set(f"ID: {emp_id} - Nombre: {name}")
        else:
            Messagebox.show_error(
                title="Error",
                message=f"El id del empleado es incorrecto."
            )

    def _update_registry_to_emp(self):
        """
        update data to the database
        :return:
        """
        # Obtener la fecha desde el widget DateEntry
        # date_entry_value = self.entry_last_date.get()
        year = int(self.wentry_year.get())
        print(type(year))
        if len(self.seniority_dict) == 0:
            Messagebox.show_info(
                title="Warning",
                message=f"Se creara un nuevo registro para el año: {year}."
            )
            key_0 = str(year - 1)
            status = self.wentry_pendientes.get() + " " + "PTES" if int(self.wentry_pendientes.get()) > 0 else "Tomadas"
            self.seniority_dict = {
                key_0: {
                    "prima": {
                        "status": self.wentry_prima.get(),
                        "fecha_pago": self.wentry_prima_pago.get()
                    },
                    "status": self.wentry_pendientes.get() + " " + "PTES",
                    "comentarios": self.wentry_comentarios.get(0.0, 'end')
                }
            }
        else:
            for item in self.seniority_dict.keys():
                if int(item) == year - 1:
                    status = self.wentry_pendientes.get() + " " + "PTES" if int(
                        self.wentry_pendientes.get()) > 0 else "Tomadas"
                    self.seniority_dict[item] = {
                        "prima": {
                            "status": self.wentry_prima.get(),
                            "fecha_pago": self.wentry_prima_pago.get()
                        },
                        "status": self.wentry_pendientes.get() + " " + "PTES",
                        "comentarios": self.wentry_comentarios.get(0.0, 'end')
                    }
                    break
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=f"Esta seguro que desea insertar el registro:\n"
                    f"Nombre: {name}\n"
                    f"ID: {emp_id}\n"
                    f"Sangre: {blood}\n"
                    f"Status: {status}\n"
                    f"Aptitud: {aptitud}\n"
                    f"Fecha de renovacion: {last_date}\n"
                    f"Esta accion no se puede deshacer.\n"
                    f"Esta accion es irreversible.",
            buttons=["No:secondary", "Yes:primary"]
        )
        if answer == "No" or None:
            return
        flag, error, out = insert_new_exam_med(
            name, blood, status, apt_list, renovacion, aptitud, last_date, emp_id
        )
        if flag:
            Messagebox.show_info(
                title="Exito",
                message=f"Se inserto el registro correctamente"
            )
            self.data.append((out, name, blood, status, json.dumps(apt_list), json.dumps(renovacion),
                              int(aptitud), last_date_formatted, int(emp_id)))
            self.loadTable(self.data)
            self.entry_name.delete(0, 'end')
            self.wentry_emp_id.delete(0, 'end')
            update_ExMed_cache_file(cache_file_EM_path, self.data)
        else:
            Messagebox.show_error(
                title="Error",
                message=f"Error al insertar el registro:\n{error}"
            )

    def create_input_widgets(self):
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="nswe")
        frame_inputs.columnconfigure((0, 1, 2, 3, 4), weight=1)
        # -------------------create check btns-----------------
        create_label(frame_inputs, text='ID Empleado: ',
                     row=0, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'), sticky="w")
        create_label(frame_inputs, text="Año: ",
                     row=0, column=1, padx=0, pady=0,
                     font=('Arial', 14, 'normal'), sticky="w")
        create_label(frame_inputs, text='Pendientes: ',
                     row=0, column=2, padx=0, pady=0,
                     font=('Arial', 14, 'normal'), sticky="w")
        create_label(frame_inputs, text='Pago prima: ',
                     row=0, column=3, padx=0, pady=0,
                     font=('Arial', 14, 'normal'), sticky="w")
        create_label(frame_inputs, text='Comentarios: ',
                     row=0, column=4, padx=0, pady=0,
                     font=('Arial', 14, 'normal'), sticky="w")
        create_label(frame_inputs, textvariable=self.name_emp,
                     row=2, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'), sticky="w", columnspan=2)
        # -------------------create entrys-----------------
        entry_emp_id = ttk.Entry(frame_inputs)
        entry_emp_id.grid(row=1, column=0, sticky="w", padx=7, pady=5)
        entry_year = ttk.Spinbox(frame_inputs, from_=0, to=80, state="readonly")
        entry_year.grid(row=1, column=1, sticky="w", padx=7, pady=5)
        entry_pendientes = ttk.Spinbox(frame_inputs, from_=0, to=22, state="readonly")
        entry_pendientes.grid(row=1, column=2, sticky="w", padx=7, pady=5)
        entry_pendientes.set(0)
        entry_prima = create_Combobox(frame_inputs, ["No", "Si"],
                                      row=1, column=3, sticky="w", padx=7, pady=5)
        entry_prima_pago = ttk.Entry(frame_inputs, textvariable=self.pagoprima_string)
        entry_prima_pago.grid(row=2, column=3, sticky="w", padx=7, pady=5)
        entry_comentarios = ttk.ScrolledText(frame_inputs, height=5)
        entry_comentarios.grid(row=1, column=4, sticky="nsew", padx=5, pady=5, rowspan=2)
        return entry_emp_id, entry_year, entry_pendientes, entry_prima, entry_prima_pago, entry_comentarios

    def loadTable(self, data):
        result = data
        columns = ["ID", "EMPLEADOS", "ESTATUS", "FECHA DE INGRESO", "ANTIGUEDAD"]
        # update tableview
        self.grouped_table = Tableview(self.frame_info,
                                       coldata=columns,
                                       rowdata=result,
                                       paginated=True,
                                       searchable=True,
                                       autofit=True)
        self.grouped_table.grid(row=1, column=0, sticky="nswe",
                                padx=25, pady=5)
        self.grouped_table.view.bind("<Double-1>", self.on_double_click)

    def on_double_click(self, event):
        selected_row = event.widget.item(event.widget.selection()[0], "values")
        id_emp, name, lastname, date_admission, seniority = selected_row
        self.wentry_emp_id.delete(0, 'end')
        self.wentry_emp_id.insert(0, id_emp)
        date_admission = datetime.strptime(date_admission, "%Y-%m-%d %H:%M:%S")
        time_at_company = (datetime.now() - date_admission).days
        anios = time_at_company // 365
        self.name_emp.set(f"Nombre: {name} {lastname}\nAntigüedad: {anios} años y {time_at_company % 365} dias")
        seniority_dict = json.loads(seniority)
        self.wentry_year.config(to=anios) if anios > 0 else self.wentry_year.config(to=1)
        if len(seniority_dict) > 0:
            self.seniority_dict = seniority_dict
            # self.wentry_year.configure(state="readonly")
            # self.wentry_pendientes.configure(state="readonly")
            # self.wentry_prima.configure(state="readonly")
            self.wentry_comentarios.delete(0.0, "end")
            self.wentry_comentarios.insert(0.0, seniority_dict["0"]["comentarios"])
            self.wentry_year.configure(to=len(seniority_dict.keys()))
            self.wentry_prima.set("Si") if seniority_dict["0"]["prima"][
                                               "status"].lower() == "si" else self.wentry_prima.set("No")
            txt_pendientes = seniority_dict["0"]["status"]
            self.wentry_pendientes.set(int(
                txt_pendientes.split(" ")[0])) if txt_pendientes.lower() != "tomadas" else self.wentry_pendientes.set(0)
            self.wentry_year.set(1)
            self.pagoprima_string.set(f"{seniority_dict['0']['prima']['fecha_pago']}")
        # else:
        #     self.seniority_dict = {}
        #     self.wentry_year.configure(state="disabled")
        #     self.wentry_pendientes.configure(state="disabled")
        #     self.wentry_prima.configure(state="disabled")
        #     self.wentry_comentarios.delete(0.0, "end")
        #     self.wentry_prima_pago.configure(state="disabled")
