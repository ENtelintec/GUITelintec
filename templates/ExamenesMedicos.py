# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/dic./2023  at 17:12 $'

from datetime import datetime
from tkinter import BooleanVar, messagebox
from tkinter import filedialog
from tkinter.ttk import Style

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from templates.FunctionsSQL import insert_new_exam_med, get_id_employee, update_aptitud_renovacion, \
    get_aptitud_renovacion, update_aptitud, update_renovacion, get_renovacion, execute_sql


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


class ExamenesMedicosFrame(ScrolledFrame):

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # self.pack(fill=ttk.BOTH, expand=True)
        self.columnconfigure((0, 1, 2, 3), weight=1)
        # self.rowconfigure(0, weight=1)

        current_style = ttk.Style()
        current_style.configure("TButton.Color.TButton", background="#040530", foreground="#FFFFFF")
        theme = ttk.Style()
        theme.configure("Checkbutton.Color.Checbutton", background="#040530", foreground="#FFFFFF")
        # -------------------create title-----------------
        ttk.Label(self, text='Examenes Medicos', font=("Helvetica", 32, "bold")).grid(row=0, column=0, columnspan=4,
                                                                                      padx=20, pady=50)

        # -------------------create varaibles-----------------
        (self.var_name, self.var_blood, self.var_status, self.var_aptitud, self.var_renovacion,
         self.var_apt_actual, self.var_last_date, self.emp_id) = create_booleanvar(8)
        self.var_label_id_name = ttk.StringVar(value="")
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
        self.entry_name.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.entry_blood = ttk.Combobox(self, bootstyle="info", state="readonly")
        self.entry_blood["values"] = ("A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-")
        self.entry_blood.current(0)
        self.entry_blood.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.entry_status = ttk.Combobox(self, bootstyle="info", state="readonly")
        self.entry_status["values"] = ("Activo", "Inactivo")
        self.entry_status.current(0)
        self.entry_status.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.entry_aptitud = ttk.Combobox(self, bootstyle="info", state="readonly")
        self.entry_aptitud["values"] = ("1", "2", "3", "4")
        self.entry_aptitud.current(0)
        self.entry_aptitud.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        self.entry_last_date = ttk.DateEntry(self, bootstyle="info")
        self.entry_last_date.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        self.entry_emp_id = ttk.Entry(self, bootstyle="info")
        self.entry_emp_id.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        # -------------------create buttons-----------------
        btn_insert = ttk.Button(self, text="Insertar", command=self.insert_data_to_db, style="TButton.Color.TButton")
        btn_insert.grid(row=8, column=0, columnspan=3, padx=5, pady=40, )
        # button for search id from name
        btn_search_id = ttk.Button(self, text="Buscar ID", command=self.search_id_from_name,
                                   style="TButton.Color.TButton")
        btn_search_id.grid(row=1, column=2, sticky="ns", padx=5, pady=5)
        label_id_name = ttk.Label(self, textvariable=self.var_label_id_name)
        label_id_name.grid(row=1, column=3, sticky="nsew", padx=5, pady=5)
        # -------------------export medical examination report-----------------
        self.all_medicalExam = ExamenesMedicosMain(self)
        self.all_medicalExam.grid(row=9, column=0, columnspan=4, sticky='nsew')
        self.all_medicalExam.loadTable()
        label_report = ttk.Label(self, text="Exportar reporte de los examenes medicos",
                                 font=("Helvetica", 16, "normal"))
        label_report.grid(row=10, column=0, sticky="nswe", padx=5, pady=50)
        btn_export = ttk.Button(self, text="Exportar", style="TButton.Color.TButton", command=self.export_medical_exam)
        btn_export.grid(row=10, column=1, columnspan=3, padx=5, pady=40, )

    def search_id_from_name(self):
        """
        Search the id from the name
        :return:
        """
        name = self.entry_name.get() if self.var_name.get() else None
        if name is None or name == "":
            self.var_label_id_name.set("Por favor, ingrese el nombre")
        else:
            emp_id = get_id_employee(name)
            if emp_id is None:
                self.var_label_id_name.set("No se encontro el ID")
            else:
                self.var_label_id_name.set(f"Id: {emp_id}")

    def insert_data_to_db(self):
        """
        Insert data to the database
        :return:
        """
        # Obtener la fecha desde el widget DateEntry
        # date_entry_value = self.entry_last_date.get()

        # retrieve data from entrys
        name = self.entry_name.get() if self.var_name.get() else None
        blood = self.entry_blood.get() if self.var_blood.get() else None
        status = self.entry_status.get() if self.var_status.get() else None
        aptitud = int(self.entry_aptitud.get()) if self.var_aptitud.get() else None
        last_date = self.entry_last_date.entry.get() if self.var_last_date.get() else None
        last_date_formatted = datetime.strptime(last_date, '%m/%d/%Y').strftime('%Y-%m-%d') if last_date else None
        # last_date_formatted = datetime.last_date.strftime('%Y-%m-%d') if last_date else None

        # last_date = self.entry_last_date.entry.get() if self.var_last_date.get() else None
        # Formatear la fecha como 'YYYY-MM-DD'
        # last_date = date_entry_value.strftime('%Y-%m-%d') if date_entry_value and self.var_last_date.get() else None
        # last_date = self.entry_last_date.get() if self.var_last_date.get() else None  # Corregido aquí
        # last_date = datetime.strptime(date_entry_value, '%m/%d/%y').strftime('%Y-%m-%d') if date_entry_value and self.var_last_date.get() else None

        emp_id = int(self.entry_emp_id.get()) if self.emp_id.get() else None
        # Inicializar apt_list como una lista vacía
        apt_list = []
        renovacion = []

        # insert data to database
        if (
                name is not None
                and blood is not None
                and status is not None
                and aptitud is not None
                and last_date is not None
                and emp_id is not None
        ):
            # new register
            apt_list = [aptitud]
            renovacion = [last_date]
            flag, error, out = insert_new_exam_med(
                name, blood, status, apt_list, renovacion, aptitud, last_date, emp_id
            )
        elif name is not None and aptitud is not None and last_date is not None and emp_id:
            # update aptitude and renovacion
            print("update option 2")  # Fix typo here

            flag, error, out = get_aptitud_renovacion(emp_id)
            apt_list, renovacion = out
            if not isinstance(apt_list, list):
                apt_list = [apt_list]
            if not isinstance(renovacion, list):
                renovacion = [renovacion]
            apt_list.append(aptitud)
            renovacion.append(last_date)
            flag, error, out = update_aptitud_renovacion(
                apt_list, renovacion, aptitud, last_date_formatted, emp_id
            )
        elif name is not None and aptitud is not None and emp_id is not None:
            # update aptitude
            print("update option 3")
            # flag, error, out = get_aptitud(emp_id)
            # apt_list = out
            out = None
            # apt_list = [out] if isinstance(out, int) else list(out)
            apt_list = [out] if (isinstance(out, int) or out is None) else list(out)
            # apt_list.append(aptitud)
            apt_list.append(aptitud)
            flag, error, out = update_aptitud(apt_list, aptitud, emp_id)
        elif name is not None and last_date is not None and emp_id:
            # update renovacion
            flag, error, out = get_renovacion(emp_id)
            # out = None
            renovacion = [out] if (isinstance(out, str) or out is None) else list(out)
            # renovacion = out
            renovacion.append(last_date)
            flag, error, out = update_renovacion(
                renovacion, last_date_formatted, emp_id
            )
        else:
            print("No válido")

    def export_medical_exam(self):
        """
        Exporta la tabla de examenes médicos a un archivo Excel (.xlsx).
        """
        # Obtener la ruta del archivo seleccionada por el usuario
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])

        if file_path:
            try:
                # Obtener los datos de la tabla
                # table_data = self.loadTable()
                table_data = self.all_medicalExam.loadTable()

                # Crear un DataFrame con los datos de la tabla
                df = pd.DataFrame(table_data, columns=[
                    "ID", "EMPLEADOS", "BLOOD", "STATUS", "APTITUD",
                    "RENOVACION", "APTITUDE_ACTUAL", "FECHA_ULTIMA_RENOVACION", "EMPLEADO_ID"
                ])

                # Exportar el DataFrame a un archivo Excel (.xlsx)
                df.to_excel(file_path, index=False, engine='openpyxl')

                print(f"Tabla de examenes médicos exportada a: {file_path}")
            except Exception as e:
                print(f"Error al exportar la tabla de examenes médicos: {e}")

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


class ExamenesMedicosMain(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.columnconfigure((0, 1, 2), weight=1)
        self.style = Style()
        # Crear un estilo con un borde azul
        self.style.configure("Blue.TFrame", borderwidth=5, relief="solid", bordercolor="#040530")
        # Marco principal
        frame_all = ttk.Frame(self, style="Blue.TFrame", padding=10)
        frame_all.grid(row=1, column=0, columnspan=3, sticky="nsew")

        self.label_1 = ttk.Label(self, text="Empleados con examenes medicos", font=("Helvetica", 18, "normal"))
        self.label_1.grid(row=0, column=0, columnspan=3)
        data_for_tableview = None
        self.df = None
        # -------------------create tableview for data-----------------
        self.grouped_table = Tableview(self)
        self.loadTable()

        self.names = ttk.Combobox(self, values=self.get_names())
        self.names.grid(row=5, column=1)
        self.names.bind("<<ComboboxSelected>>", self.detalles_emp_medicalexam)
        self.detalles_emp = ttk.LabelFrame(self, text="Detalles del Examen medico del empleado")
        self.detalles_emp.grid(row=6, column=0, columnspan=3)
        self.name_emp = ttk.StringVar()
        self.aptitud_act = ttk.StringVar()
        self.examen_prox = ttk.StringVar()
        self.label_name_emp = ttk.Label(self.detalles_emp, textvariable=self.name_emp)
        self.label_name_emp.grid(row=7, column=0)
        self.label_aptitud_act = ttk.Label(self.detalles_emp, textvariable=self.aptitud_act)
        self.label_aptitud_act.grid(row=7, column=1)
        self.examen_prox_label = ttk.Label(self.detalles_emp, textvariable=self.examen_prox)
        self.examen_prox_label.grid(row=7, column=2)

    def loadTable(self, limit=(0, 100)):
        # Consulta SQL para obtener datos de la base de datos
        # sql = "SELECT * FROM sql_telintec.examenes_med LIMIT "
        sql = "SELECT * FROM sql_telintec.examenes_med "
        flag, e, resultados = execute_sql(sql, type_sql=5)  # type_sql=5 para obtener todos los resultados
        val = (limit[0], limit[1])
        try:
            # Ejecutar la consulta SQL
            flag, e, my_result = execute_sql(sql, val, 5)  # Cambia el type_sql a 5 para obtener todos los resultados
            # Verificar si se obtuvieron resultados
            # if my_result is None:
            #     return
            my_result = my_result

            # Transformar los resultados en un formato adecuado para Tableview
            data_for_tableview = {
                "ID": [],
                "EMPLEADOS": [],
                "BLOOD": [],
                "STATUS": [],
                "APTITUD": [],
                "RENOVACION": [],
                "APTITUDE_ACTUAL": [],
                "FECHA_ULTIMA_RENOVACION": [],
                "EMPLEADO_ID": []

            }

            for row in my_result:
                # Asegúrate de que los índices numéricos coincidan con el orden de las columnas en tu consulta SQL
                data_for_tableview["ID"].append(row[0])
                data_for_tableview["EMPLEADOS"].append(row[1])
                data_for_tableview["BLOOD"].append(row[2])
                data_for_tableview["STATUS"].append(row[3])
                data_for_tableview["APTITUD"].append(row[4])
                data_for_tableview["RENOVACION"].append(row[5])
                data_for_tableview["APTITUDE_ACTUAL"].append(row[6])
                data_for_tableview["FECHA_ULTIMA_RENOVACION"].append(row[7])
                data_for_tableview["EMPLEADO_ID"].append(row[8])

            # Destruir el Tableview existente si existe
            if hasattr(self, 'grouped_table'):
                self.grouped_table.destroy()

            # Crear y mostrar el nuevo Tableview
            self.grouped_table = Tableview(self, searchable=True, bootstyle="primary", coldata=[
                {"text": "ID", "stretch": True},
                {"text": "EMPLEADOS", "stretch": True},
                {"text": "BLOOD", "stretch": True},
                {"text": "STATUS", "stretch": True},
                {"text": "APTITUD", "stretch": True},
                {"text": "RENOVACION", "stretch": True},
                {"text": "APTITUDE_ACTUAL", "stretch": True},
                {"text": "FECHA_ULTIMA_RENOVACION", "stretch": True},
                {"text": "EMPLEADO_ID", "stretch": True}
            ], rowdata=list(zip(
                data_for_tableview["ID"],
                data_for_tableview["EMPLEADOS"],
                data_for_tableview["BLOOD"],
                data_for_tableview["STATUS"],
                data_for_tableview["APTITUD"],
                data_for_tableview["RENOVACION"],
                data_for_tableview["APTITUDE_ACTUAL"],
                data_for_tableview["FECHA_ULTIMA_RENOVACION"],
                data_for_tableview["EMPLEADO_ID"]
            )))

            self.grouped_table.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=20, pady=10)
            # Vincular el evento de selección a la función get_selected_employee_id
            # self.grouped_table.bind('<<TreeviewSelect>>', self.get_selected_employee_id)

        except Exception as e:
            print(f"Error al cargar la tabla: {e}")
            my_result = []
        return my_result

    def get_names(self):
        # Llamada a loadTable para obtener los nombres
        names_result = self.loadTable()
        # Asumiendo que el resultado es una lista de nombres (ajusta según tu lógica)
        names = [row[1] for row in names_result] if names_result else []
        return names

    def detalles_emp_medicalexam(self, event=None):
        # Obtener el nombre del empleado seleccionado
        selected_name = self.names.get()
        if not selected_name:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un empleado.")
            return
        # Consulta MySQL para recuperar aptitude_actual y renovacion para el empleado seleccionado
        sql = "SELECT aptitude_actual,fecha_ultima_renovacion FROM sql_telintec.examenes_med WHERE name = %s"
        val = (selected_name,)
        flag, e, my_result = execute_sql(sql, val, type_sql=3)
        try:
            # Ejecutar la consulta SQL
            flag, e, my_result = execute_sql(sql, val, 3)
            if my_result:
                # Actualizar las etiquetas con los datos recuperados
                self.name_emp.set(selected_name)
                self.aptitud_act.set(my_result)
                self.examen_prox.set(my_result)
                # self.examen_prox.set(my_result[0][1])
            else:
                # Manejar el caso en el que no se encuentran datos para el empleado seleccionado
                messagebox.showwarning("Advertencia", f"No se encontraron datos para {selected_name}")

        except Exception as e:
            print(f"Error al obtener detalles: {e}")
            messagebox.showerror("Error", f"Error al obtener detalles: {e}")
