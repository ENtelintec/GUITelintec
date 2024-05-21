# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/dic./2023  at 17:12 $'

import json
from datetime import datetime
from tkinter import filedialog

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from static.extensions import cache_file_EM_path, format_date, format_timestamps
from templates.Functions_Files import get_ExMed_cache_file, update_ExMed_cache_file
from templates.Funtions_Utils import create_label, set_dateEntry_new_value
from templates.controllers.employees.em_controller import get_all_examenes, update_status_EM, update_aptitud, \
    update_renovacion, insert_new_exam_med
from templates.controllers.employees.employees_controller import get_id_employee


def load_data_EM(option=1):
    columns = ["Id_EM", "Nombre", "Sangre", "Estado", "Aptitudes",
               "Renovaciones", "Apt. Actual", "Id_emp"]
    if option == 1:
        flag, e, out = get_all_examenes()
        if flag:
            data = out
            update_ExMed_cache_file(cache_file_EM_path, data)
        else:
            Messagebox.show_error(
                title="Error", message=f"Error con la base de datos.\n{e}\nTomando datos del cache local."
            )
            flag, data = get_ExMed_cache_file(cache_file_EM_path)
            if not flag:
                Messagebox.show_error(
                    title="Error", message="Error con el cache local.\n"
                )
                data = []
    else:
        flag, data = get_ExMed_cache_file(cache_file_EM_path)
        if not flag:
            Messagebox.show_error(
                title="Error", message="Error con el cache local.\n"
            )
            data = []
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


class ExamenesMedicos(ScrolledFrame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master, autohide=True)
        # self.pack(fill=ttk.BOTH, expand=True)
        self.columnconfigure((0, 1), weight=1)
        # self.rowconfigure(0, weight=1)
        # -------------------create title-----------------
        ttk.Label(self, text='Examenes Medicos', font=("Helvetica", 32, "bold")).grid(
            row=0, column=0, columnspan=2, padx=20, pady=30)
        # -------------------create varaibles-----------------
        self.var_label_id_name = ttk.StringVar(value="")
        self.data, columns = load_data_EM(1)
        self.name_emp = ttk.StringVar()
        self.aptitud_act = ttk.StringVar()
        self.examen_prox = ttk.StringVar()
        self.names_emp = []
        self.df = None
        self.table_data = []
        #  -------------------create input widgets-----------------
        (self.entry_name, self.entry_blood, self.entry_status, self.entry_aptitud,
         self.entry_last_date, self.entry_emp_id) = self.create_input_widgets()
        # -------------------create buttons-----------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, columnspan=2, padx=20, pady=20)
        frame_buttons.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(frame_buttons, text="Insertar nuevo registro", command=self._insert_data_to_db).grid(
            row=0, column=0, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Nueva Fecha", command=self._update_date_to_db).grid(
            row=0, column=1, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Nueva Aptitud", command=self._update_aptitud_to_db).grid(
            row=0, column=2, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Cambiar Status", command=self._update_status_to_db).grid(
            row=0, column=3, padx=5, pady=0)
        # -------------------table and info data-----------------
        self.frame_info = ttk.Frame(self)
        self.frame_info.grid(row=3, column=0, columnspan=2, sticky='nsew')
        self.frame_info.columnconfigure(0, weight=1)
        ttk.Label(self.frame_info, text="Empleados con examenes medicos", font=("Helvetica", 18, "normal")).grid(
            row=0, column=0)
        # -------------------create tableview for data-----------------
        self.grouped_table = Tableview(self.frame_info)
        self.loadTable(self.data)
        self.names = ttk.Combobox(self.frame_info, values=self.names_emp,
                                  state="readonly")
        self.names.grid(row=2, column=0, padx=50, pady=10, sticky="nsew")
        self.names.bind("<<ComboboxSelected>>", self.detalles_emp_medicalexam)
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
        ttk.Label(self, text="Exportar reporte de los examenes medicos",
                  font=("Helvetica", 16, "normal")).grid(
            row=4, column=0, columnspan=4, padx=10, pady=10)
        ttk.Button(self, text="Exportar", command=self.export_medical_exam).grid(
            row=5, column=0, columnspan=4, padx=10, pady=10)

    def _update_status_to_db(self):
        status = self.entry_status.get()
        try:
            emp_id = int(self.entry_emp_id.get())
            (id_exam, nombre, sangre, status, aptitud,
             fechas, apt_actual, emp_id, index) = get_entry_from_data(self.data, emp_id)
            answer = Messagebox.show_question(
                title="Confirmacion",
                message=f"Esta seguro que desea cambiar el status del empleado {emp_id} a {status}?"
                        f"\nEsta accion no se puede deshacer."
                        f"\nEsta accion es irreversible.",
                buttons=["No:secondary", "Yes:primary"]
            )
            if answer == "No" or None:
                return
            flag, e, out = update_status_EM(status, emp_id)
            if flag:
                Messagebox.show_info(
                    title="Exito",
                    message=f"Se actualizo el status correctamente para el empleado {emp_id}."
                )
                self.data[index] = (id_exam, nombre, sangre, status, aptitud,
                                    fechas, apt_actual, emp_id)
                self.loadTable(self.data)
            else:
                Messagebox.show_error(
                    title="Error",
                    message=f"No se pudo actualizar el status para el empleado {emp_id}.\n"
                            f"Revise que sea el id correcto."
                )
        except ValueError:
            Messagebox.show_error(
                title="Error",
                message="El ID debe ser un numero entero"
            )

    def _update_aptitud_to_db(self):
        aptitud = self.entry_aptitud.get()
        try:
            aptitud = int(aptitud)
            emp_id = int(self.entry_emp_id.get())
            (id_exam, nombre, sangre, status, aptitudes,
             fechas, apt_actual, emp_id, index) = get_entry_from_data(self.data, emp_id)
            if aptitudes is not None:
                apt_actual = aptitud
                aptitudes = json.loads(aptitudes)
                aptitudes.append(aptitud)
                answer = Messagebox.show_question(
                    title="Confirmacion",
                    message=f"Esta seguro que desea cambiar la aptitud del empleado {emp_id} a {aptitud}?"
                            f"\nEsta accion no se puede deshacer."
                            f"\nEsta accion es irreversible.",
                    buttons=["No:secondary", "Yes:primary"]
                )
                if answer == "No" or None:
                    return
                flag, e, out = update_aptitud(aptitudes, aptitud, emp_id)
                if flag:
                    Messagebox.show_info(
                        title="Exito",
                        message=f"Se actualizo la aptitud correctamente para el empleado {emp_id}."
                    )
                    self.data[index] = (id_exam, nombre, sangre, status, json.dumps(aptitudes),
                                        fechas, apt_actual, emp_id)
                    self.loadTable(self.data)
                else:
                    Messagebox.show_error(
                        title="Error",
                        message=f"No se pudo actualizar la aptitud para el empleado {emp_id}.\n"
                                f"Revise que sea el id correcto."
                    )
        except ValueError:
            Messagebox.show_error(
                title="Error",
                message="El ID debe ser un numero entero"
            )

    def _update_date_to_db(self):
        date = self.entry_last_date.entry.get()
        try:
            emp_id = int(self.entry_emp_id.get())
            (id_exam, nombre, sangre, status, aptitud,
             renovaciones, apt_actual, emp_id, index) = get_aptitud_from_data(self.data, emp_id)
            if renovaciones is not None:
                renovaciones = json.loads(renovaciones)
                renovaciones.append(date)
                answer = Messagebox.show_question(
                    title="Confirmacion",
                    message=f"Esta seguro que desea cambiar la fecha de renovacion del empleado {emp_id} a {date}?"
                            f"\nEsta accion no se puede deshacer."
                            f"\nEsta accion es irreversible.",
                    buttons=["No:secondary", "Yes:primary"]
                )
                if answer == "No" or None:
                    return
                flag, e, out = update_renovacion(renovaciones, date, emp_id)
                if flag:
                    Messagebox.show_info(
                        title="Exito",
                        message=f"Se actualizo la fecha de renovacion correctamente para el empleado {emp_id}."
                    )
                    self.data[index] = (id_exam, nombre, sangre, status, aptitud,
                                        json.dumps(renovaciones), apt_actual, emp_id)
                    self.loadTable(self.data)
                    self.entry_emp_id.delete(0, 'end')
                    update_ExMed_cache_file(cache_file_EM_path, self.data)
                else:
                    Messagebox.show_error(
                        title="Error",
                        message=f"No se pudo actualizar la fecha de renovacion para el empleado {emp_id}.\n"
                                f"Revise que sea el id correcto."
                    )
            else:
                Messagebox.show_error(
                    title="Error",
                    message="Revise el ID o cree un nuevo registro primero."
                )
        except ValueError:
            Messagebox.show_error(
                title="Error",
                message="El ID debe ser un numero entero"
            )
            return

    def search_id_from_name(self):
        """
        Search the id from the name
        :return:
        """
        name = self.entry_name.get()
        if name is None or name == "":
            self.var_label_id_name.set("Por favor, ingrese el nombre")
        else:
            emp_id = get_id_employee(name)
            if emp_id is None:
                self.var_label_id_name.set("No se encontro el ID")
            else:
                self.var_label_id_name.set(f"Id: {emp_id}")

    def _insert_data_to_db(self):
        """
        Insert data to the database
        :return:
        """
        # Obtener la fecha desde el widget DateEntry
        # date_entry_value = self.entry_last_date.get()

        # retrieve data from entrys
        name = self.entry_name.get()
        blood = self.entry_blood.get()
        status = self.entry_status.get()
        aptitud = int(self.entry_aptitud.get())
        last_date = self.entry_last_date.entry.get()
        last_date_formatted = datetime.strptime(last_date, format_date)
        emp_id = int(self.entry_emp_id.get())
        # insert data to database
        if name != "" or emp_id != "":
            # new register
            apt_list = [int(aptitud)]
            renovacion = [last_date]
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
                name, blood, status, apt_list, renovacion, aptitud, emp_id
            )
            if flag:
                Messagebox.show_info(
                    title="Exito",
                    message="Se inserto el registro correctamente"
                )
                self.data.append((out, name, blood, status, json.dumps(apt_list), json.dumps(renovacion),
                                  int(aptitud), last_date_formatted, int(emp_id)))
                self.loadTable(self.data)
                self.entry_name.delete(0, 'end')
                self.entry_emp_id.delete(0, 'end')
                update_ExMed_cache_file(cache_file_EM_path, self.data)
            else:
                Messagebox.show_error(
                    title="Error",
                    message=f"Error al insertar el registro:\n{error}"
                )
        else:
            Messagebox.show_error(
                title="Error",
                message="Por favor, complete todos los campos"
            )

    def export_medical_exam(self):
        """
        Exporta la tabla de examenes médicos a un archivo Excel (.xlsx).
        """
        # Obtener la ruta del archivo seleccionada por el usuario
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])

        if file_path:
            try:
                # Obtener los datos de la tabla

                table_data = self.table_data
                df = pd.DataFrame(table_data, columns=[
                    "ID", "EMPLEADOS", "BLOOD", "STATUS", "APTITUD",
                    "RENOVACION", "APTITUDE_ACTUAL", "EMPLEADO_ID"
                ])

                # Exportar el DataFrame a un archivo Excel (.xlsx)
                df.to_excel(file_path, index=False, engine='openpyxl')

                print(f"Tabla de examenes médicos exportada a: {file_path}")
            except Exception as e:
                print(f"Error al exportar la tabla de examenes médicos: {e}")

    def create_input_widgets(self):
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="nswe")
        frame_inputs.columnconfigure((0, 1, 2, 3), weight=1)
        # -------------------create check btns-----------------
        create_label(frame_inputs, text='Nombre: ',
                     row=1, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'))
        create_label(frame_inputs, text='Tipo Sangre: ',
                     row=2, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'))
        create_label(frame_inputs, text='Estado: ',
                     row=3, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'))
        create_label(frame_inputs, text='Aptitud: ',
                     row=4, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'))
        create_label(frame_inputs, text='Fecha: ',
                     row=5, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'))
        create_label(frame_inputs, text='ID Empleado: ',
                     row=6, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'normal'))
        # -------------------create entrys-----------------
        entry_name = ttk.Entry(frame_inputs, width=40)
        entry_name.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        entry_blood = ttk.Combobox(frame_inputs, state="readonly")
        entry_blood["values"] = ("A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-")
        entry_blood.current(0)
        entry_blood.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        entry_status = ttk.Combobox(frame_inputs, state="readonly")
        entry_status["values"] = ("ACTIVO", "INACTIVO")
        entry_status.current(0)
        entry_status.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        entry_aptitud = ttk.Combobox(frame_inputs, state="readonly")
        entry_aptitud["values"] = ("1", "2", "3", "4")
        entry_aptitud.current(0)
        entry_aptitud.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        entry_last_date = ttk.DateEntry(frame_inputs, bootstyle="info", dateformat=format_date)
        entry_last_date.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        entry_emp_id = ttk.Entry(frame_inputs)
        entry_emp_id.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        # button for search id from name
        ttk.Button(frame_inputs, text="Buscar ID", command=self.search_id_from_name).grid(
            row=1, column=2, sticky="ns", padx=5, pady=5)
        ttk.Label(frame_inputs, textvariable=self.var_label_id_name).grid(
            row=1, column=3, sticky="nsew", padx=5, pady=5)
        return entry_name, entry_blood, entry_status, entry_aptitud, entry_last_date, entry_emp_id

    def loadTable(self, data):
        dict_employees = {}
        result = data
        max_len_fechas = 0
        max_len_aptitud = 0
        for row in result:
            id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = row
            self.names_emp.append(nombre)
            aptitud = json.loads(aptitud)
            fechas = json.loads(fechas)
            max_len_fechas = len(fechas) if len(fechas) > max_len_fechas else max_len_fechas
            max_len_aptitud = len(aptitud) if len(aptitud) > max_len_aptitud else max_len_aptitud
            dict_employees[nombre] = {
                "id_exam": id_exam,
                "nombre": nombre,
                "sangre": sangre,
                "status": status,
                "aptitudes": aptitud,
                "fechas": fechas,
                "emp_id": emp_id
            }
        self.df = dict_employees
        self.table_data = []
        columns = ["ID", "ID Empleado", "Nombre", "Sangre", "Status"]
        for i in range(max_len_fechas):
            columns.append(f"Fecha {i + 1}")
            columns.append(f"Aptitud {i + 1}")
        for row in result:
            id_exam, nombre, sangre, status, aptitud, fechas, apt_actual, emp_id = row
            aptitud = json.loads(aptitud)
            fechas = json.loads(fechas)
            aux = [id_exam, emp_id, nombre, sangre, status]
            for i in range(max_len_fechas):
                if i < len(fechas):
                    aux.append(fechas[i])
                    aux.append(aptitud[i])
                else:
                    aux.append("")
                    aux.append("")
            self.table_data.append(aux)
        # update tableview
        self.grouped_table = Tableview(self.frame_info,
                                       coldata=columns,
                                       rowdata=self.table_data,
                                       paginated=True,
                                       searchable=True,
                                       autofit=True)
        self.grouped_table.grid(row=1, column=0, sticky="nswe",
                                padx=25, pady=5)
        self.grouped_table.view.bind("<Double-1>", self.on_double_click)

    def on_double_click(self, event):
        selected_row = event.widget.item(event.widget.selection()[0], "values")
        id_exam = selected_row[0]
        id_emp = selected_row[1]
        name = selected_row[2]
        blood = selected_row[3]
        status = selected_row[4]
        aptitudes = []
        fechas = []
        for row in self.data:
            if row[0] == int(id_exam):
                aptitudes = json.loads(row[4])
                fechas = json.loads(row[5])
                break
        # modify inputs
        self.entry_name.delete(0, ttk.END)
        self.entry_name.insert(0, name)
        self.entry_emp_id.delete(0, ttk.END)
        self.entry_emp_id.insert(0, id_emp)
        self.entry_blood.set(blood)
        self.entry_status.set(status)
        self.entry_aptitud.set(str(int(aptitudes[-1])))
        print(fechas)
        date = datetime.strptime(fechas[-1], format_timestamps)
        set_dateEntry_new_value(self.entry_last_date.master, self.entry_last_date, date.date(),
                                5, 1, 5, 5, "w", date_format=format_date)
        # info display
        self.name_emp.set(f"Nombre: {name}")
        self.aptitud_act.set(f"Aptitud actual: {aptitudes[-1]}")
        self.examen_prox.set(f"Ultima fecha: {fechas[-1]}")

    def detalles_emp_medicalexam(self, event=None):
        # Obtener el nombre del empleado seleccionado
        selected_name = self.names.get()
        aptitudes = self.df[selected_name]["aptitudes"]
        fechas = self.df[selected_name]["fechas"]
        self.name_emp.set(f"Nombre: {selected_name}")
        self.aptitud_act.set(f"Aptitud actual: {aptitudes[-1]}")
        self.examen_prox.set(f"Ultima fecha: {fechas[-1]}")
