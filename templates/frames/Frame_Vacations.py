# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/ene./2024  at 15:22 $'

import json
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from templates.Functions_SQL import get_vacations_data, update_registry_vac, get_all_employees_active, insert_vacation
from templates.Funtions_Utils import create_label, create_Combobox


def get_data_small_from_table(data):
    columns = ["ID Emp.", "Nombre", "Apellido", "Fecha de Ingreso",
               "1 año \n(12 dias)", "Prima", "Fecha pago", "Comentarios",
               "2 años \n(14 dias)", "Prima", "Fecha pago", "Comentarios",
               "3 años \n(16 dias)", "Prima", "Fecha pago", "Comentarios",
               "4 años \n(18 dias)", "Prima", "Fecha pago", "Comentarios",
               "5 años \n(20 dias)", "Prima", "Fecha pago", "Comentarios",
               "6-10 años \n(22 dias)", "Prima", "Fecha pago", "Comentarios"]
    id_emp = data[0]
    name = data[1]
    lastname = data[2]
    date_admission = data[3]
    seniority = data[-1]
    return id_emp, name, lastname, date_admission, seniority


def fill_empty_with_None(number: int, list_data: tuple):
    list_out = []
    for index, item in enumerate(list_data):
        list_out.append(item + [None] * (number - len(item)))
    return tuple(list_out)


def tranform_data_vacations_db_display(data):
    data_display = []
    columns = ["ID Emp.", "Nombre", "Apellido", "Fecha de Ingreso",
               "1 año (12 dias)", "Prima", "Fecha pago", "Comentarios",
               "2 años (14 dias)", "Prima", "Fecha pago", "Comentarios",
               "3 años (16 dias)", "Prima", "Fecha pago", "Comentarios",
               "4 años (18 dias)", "Prima", "Fecha pago", "Comentarios",
               "5 años (20 dias)", "Prima", "Fecha pago", "Comentarios",
               "6-10 años (22 dias)", "Prima", "Fecha pago", "Comentarios"]
    for entry in data:
        id_exam, name, lname, date_entry, seniority = entry
        seniority_dict = json.loads(seniority)
        prima = []
        prima_pago = []
        comentarios = []
        status = []
        for year in seniority_dict.keys():
            prima.append(seniority_dict[year]["prima"]["status"])
            prima_pago.append(seniority_dict[year]["prima"]["fecha_pago"])
            comentarios.append(seniority_dict[year]["comentarios"])
            status.append(seniority_dict[year]["status"])
        prima, prima_pago, comentarios, status = fill_empty_with_None(6, (prima, prima_pago, comentarios, status))
        new_row = [id_exam, name, lname, date_entry]
        for index, value in enumerate(status):
            new_row.append(value)
            new_row.append(prima[index])
            new_row.append(prima_pago[index])
            new_row.append(comentarios[index])
        data_display.append(new_row)
    return data_display, columns


class VacationsFrame(ScrolledFrame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master, autohide=True, *args, **kwargs)
        # self.pack(fill=ttk.BOTH, expand=True)
        self.seniority_dict = None
        self.columnconfigure((0, 1), weight=1)
        # -------------------create title-----------------
        ttk.Label(self, text='Vacaciones', font=("Helvetica", 32, "bold")).grid(
            row=0, column=0, columnspan=2, padx=20, pady=30)
        # -------------------create varaibles-----------------
        self.var_label_id_name = ttk.StringVar(value="")
        self.data, columns = self.load_data_vacations(1)
        self.name_emp = ttk.StringVar()
        self.aptitud_act = ttk.StringVar()
        self.examen_prox = ttk.StringVar()
        self.antiguedad = ttk.StringVar(value="")
        self.seniority_string = ttk.StringVar(value="")
        self.pagoprima_string = ttk.StringVar(value="")
        self.year_var_info = ttk.StringVar(value="")
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
        ttk.Button(frame_buttons, text="Actualizar registro", command=self._update_registry_to_emp).grid(
            row=0, column=1, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Borrar registro", command=self._delete_registry_from_emp).grid(
            row=0, column=2, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Actualizar empleados", command=self._update_emps).grid(
            row=0, column=3, padx=5, pady=0)
        ttk.Button(frame_buttons, text="Exportar", command=self._export_table()).grid(
            row=0, column=4, padx=5, pady=0)
        # -------------------table and info data-----------------
        self.frame_info = ttk.Frame(self)
        self.frame_info.grid(row=3, column=0, columnspan=2, sticky='nsew')
        self.frame_info.columnconfigure(0, weight=1)
        ttk.Label(self.frame_info, text="Tabla de información", font=("Helvetica", 18, "normal")).grid(
            row=0, column=0)
        # -------------------create tableview for data-----------------
        self.grouped_table = Tableview(self.frame_info)
        self.loadTable(self.data)
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
        flag, error, data = get_all_employees_active()
        if flag:
            ids_vac = [item[0] for item in self.data]
            ids_emp = [item[0] for item in data]
            # list of item not in ids_vac
            ids_not_vac = [item for item in ids_emp if item not in ids_vac]
            if len(ids_not_vac) == 0:
                Messagebox.show_info(
                    title="Exito",
                    message=f"Todos los empleados estan en la tabla de vacaciones."
                )
                return
            complete_name_of_not_vac = [item[1].upper() + " " + item[2].upper() for item in data if
                                        item[0] in ids_not_vac]
            answer = Messagebox.show_question(
                title="Confirmacion",
                message=f"Esta por actualizar la informacion de los empleados.\n"
                        f"Los empleados que no estan en la tabla de vacaciones son:\n"
                        f"{ids_not_vac}\n"
                        f"{complete_name_of_not_vac}\n"
                        f"Desea continuar?",
                buttons=["Yes:secondary", "No:primary"]
            )
            if answer == "No":
                return
            for item in ids_not_vac:
                for row in data:
                    ids_emp, name, lastname, date_admission = row
                    if ids_emp == item:
                        flag, error, out = insert_vacation(ids_emp, {})
                        if not flag:
                            print(error)
                        else:
                            self.data.append((ids_emp, name, lastname, date_admission, json.dumps({})))
                            print(f"Nuevo registro creado para el empleado: {ids_emp}")
                        break
        self.loadTable(self.data)

    def _test_id(self):
        emp_id = self.wentry_emp_id.get()
        name = None
        if emp_id == "":
            Messagebox.show_error(
                title="Error",
                message=f"El id del empleado esta vacio."
            )
            return
        for item in self.data:
            id_emp, fname, lastname, date_admission, seniority = item
            if emp_id == emp_id:
                name = fname.upper() + " " + lastname.upper()
                break
        if name is not None:
            Messagebox.show_info(
                title="Exito",
                message=f"El id del empleado es correcto."
            )
            self.name_emp.set(f"ID: {emp_id}\nNombre: {name}")
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
        id_emp = self.wentry_emp_id.get()
        year = int(self.wentry_year.get())
        for row in self.data:
            id_emp, name, lastname, date_admission, seniority = row
            diff = datetime.now() - date_admission
            anios = diff.days / 365
            if anios <= year:
                answer = Messagebox.show_question(
                    title="Confirmacion",
                    message=f"Esta por agregar informacion de un nuevo año. Desea continuar?",
                    buttons=["No:secondary", "Yes:primary"]
                )
                if answer == "No" or None:
                    return
                break
        seniority_dict = self.seniority_dict
        if len(seniority_dict) == 0:
            Messagebox.show_info(
                title="Warning",
                message=f"Se creara un nuevo registro para el año: {year}."
            )
            key_0 = str(year - 1)
            status = self.wentry_pendientes.get() + " " + "PTES" if int(self.wentry_pendientes.get()) > 0 else "Tomadas"
            seniority_dict = {
                key_0: {
                    "prima": {
                        "status": self.wentry_prima.get(),
                        "fecha_pago": self.wentry_prima_pago.get()
                    },
                    "status": status,
                    "comentarios": self.wentry_comentarios.get(0.0, 'end')
                }
            }
        else:
            for item in seniority_dict.keys():
                if int(item) == year - 1:
                    status = self.wentry_pendientes.get() + " " + "PTES" if int(
                        self.wentry_pendientes.get()) > 0 else "Tomadas"
                    seniority_dict[item] = {
                        "prima": {
                            "status": self.wentry_prima.get(),
                            "fecha_pago": self.wentry_prima_pago.get()
                        },
                        "status": status,
                        "comentarios": self.wentry_comentarios.get(0.0, 'end')
                    }
                    break
        try:
            flag, error, out = update_registry_vac(int(id_emp), seniority_dict)
            if flag:
                Messagebox.show_info(
                    title="Exito",
                    message=f"Se inserto el registro correctamente, \npara el año: {year} del empleado {self.wentry_emp_id.get()}."
                )
                self.seniority_dict = seniority_dict
                self.loadTable(self.data)
            else:
                Messagebox.show_error(
                    title="Error",
                    message=f"Error al insertar el registro:\n{error}"
                )
        except Exception as e:
            print(e)

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
                     font=('Arial', 14, 'normal'), sticky="w", columnspan=3)
        create_label(frame_inputs, textvariable=self.year_var_info,
                     row=3, column=0, padx=0, pady=0,
                     font=('Arial', 14, 'bold'), sticky="n", columnspan=5)
        # -------------------create entrys-----------------
        entry_emp_id = ttk.Entry(frame_inputs)
        entry_emp_id.grid(row=1, column=0, sticky="w", padx=7, pady=5)
        entry_year = ttk.Spinbox(frame_inputs, from_=1, to=80, state="readonly",
                                 command=self._test_year)
        # entry_year.bind("<ButtonRelease>", self._test_year)
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
        data, columns = tranform_data_vacations_db_display(data)
        # update tableview
        self.grouped_table = Tableview(self.frame_info,
                                       coldata=columns,
                                       rowdata=data,
                                       paginated=True,
                                       searchable=True,
                                       autofit=True)
        self.grouped_table.grid(row=1, column=0, sticky="nswe",
                                padx=25, pady=5)
        self.grouped_table.view.bind("<Double-1>", self.on_double_click)

    def on_double_click(self, event):
        self.clean_widgets_year()
        selected_row = event.widget.item(event.widget.selection()[0], "values")
        id_emp = selected_row[0]
        name = selected_row[1]
        lastname = selected_row[2]
        date_admission = selected_row[3]
        for row in self.data:
            if int(row[0]) == int(id_emp):
                seniority = row[-1]
                break
        self.wentry_emp_id.delete(0, 'end')
        self.wentry_emp_id.insert(0, id_emp)
        date_admission = datetime.strptime(date_admission, "%Y-%m-%d %H:%M:%S")
        time_at_company = (datetime.now() - date_admission).days
        anios = time_at_company // 365
        self.name_emp.set(f"Nombre: {name} {lastname}\nAntigüedad: {anios} años y {time_at_company % 365} dias")
        seniority_dict = json.loads(seniority)
        if len(seniority_dict) > 0:
            self.seniority_dict = seniority_dict
            self.wentry_comentarios.insert(0.0, seniority_dict["0"]["comentarios"]) if seniority_dict["0"][
                                                                                           "comentarios"] is not None else self.wentry_comentarios.insert(
                0.0, "")
            self.wentry_prima.set("Si") if seniority_dict["0"]["prima"][
                                               "status"].lower() == "si" else self.wentry_prima.set("No")
            txt_pendientes = seniority_dict["0"]["status"]
            self.wentry_pendientes.set(int(
                txt_pendientes.split(" ")[0])) if txt_pendientes.lower() != "tomadas" else self.wentry_pendientes.set(0)
            self.wentry_pendientes.configure(
                bootstyle="success") if txt_pendientes.lower() == "tomadas" else self.wentry_pendientes.configure(
                bootstyle="danger")
            self.wentry_year.set(1)
            self.pagoprima_string.set(f"{seniority_dict['0']['prima']['fecha_pago']}")
        else:
            self.wentry_pendientes.configure(bootstyle="success")

    def load_data_vacations(self, option=1, data=None):
        columns = ["emp_id", "name", "l_name", "date_admission", "seniority"]
        if option == 1:
            flag, error, data = get_vacations_data()
        else:
            for index, row in enumerate(data):
                id_emp, name, l_name, status, date_admission, seniority = row
                if id_emp == self.wentry_emp_id.get():
                    data[index] = (id_emp, name, l_name, status, date_admission, seniority)
                    break
        return data, columns

    def _test_year(self):
        self.clean_widgets_year()
        if self.wentry_year.get() == "" or self.wentry_emp_id.get() == "":
            self.year_var_info.set("No puede haber informacion vacia en el ID")
        else:
            if self.wentry_year.get() == "0":
                self.year_var_info.set("No puede haber informacion para el año 0")
            else:
                year = int(self.wentry_year.get())
                try:
                    id_emp = self.wentry_emp_id.get()
                    id_emp = int(id_emp)
                except ValueError:
                    Messagebox.show_error(
                        title="Error",
                        message="El ID del empleado debe ser un numero"
                    )
                    self.year_var_info.set("El ID del empleado debe ser un numero")
                    return
                flag_found = False
                seniority = None
                for item in self.data:
                    emp_id, name, l_name, date_admission, seniority = item
                    if emp_id == id_emp:
                        flag_found = True
                        break
                if flag_found:
                    seniority_dict = json.loads(seniority)
                    self.seniority_dict = seniority_dict
                    if len(seniority_dict) > 0:
                        for item in seniority_dict.keys():
                            if int(item) == year - 1 and year > 0:
                                self.clean_widgets_year()
                                self.wentry_comentarios.insert(0.0, seniority_dict[item]["comentarios"]) if \
                                    seniority_dict[item][
                                        "comentarios"] is not None else self.wentry_comentarios.insert(0.0, "")
                                self.wentry_prima.set("Si") if seniority_dict[item]["prima"][
                                                                   "status"].lower() == "si" else self.wentry_prima.set(
                                    "No")
                                txt_pendientes = seniority_dict[item]["status"]
                                self.wentry_pendientes.set(int(
                                    txt_pendientes.split(" ")[
                                        0])) if txt_pendientes.lower() != "tomadas" else self.wentry_pendientes.set(0)
                                self.pagoprima_string.set(f"{seniority_dict[item]['prima']['fecha_pago']}")
                                self.year_var_info.set(f"Año: {year}")
                                self.wentry_pendientes.configure(
                                    bootstyle="success") if txt_pendientes.lower() == "tomadas" else self.wentry_pendientes.configure(
                                    bootstyle="danger")
                                return
                        workey_days = datetime.now() - date_admission
                        self.year_var_info.set(
                            f"Año: {year} sin informacion (El empleado lleva {workey_days.days % 365} dias trabajando del ultimo año.")
                        self.clean_widgets_year()
                    else:
                        self.year_var_info.set(f"No hay registro de vacaciones del empleado")
                        self.clean_widgets_year()
                else:
                    self.year_var_info.set("No se encontro el empleado")

    def clean_widgets_year(self):
        self.wentry_comentarios.delete(0.0, "end")
        self.wentry_prima.set("No")
        self.wentry_pendientes.set(0)
        self.pagoprima_string.set("")

    def _export_table(self):
        data = self.data
        columns = ["ID", "NOMBRE", "APELLIDO", "FECHA DE INGRESO", "ANTIGUEDAD"]
