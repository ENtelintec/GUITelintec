# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 25/abr./2024  at 14:51 $'

from datetime import datetime
from tkinter.filedialog import asksaveasfilename

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview

from static.extensions import files_fichaje_path, patterns_files_fichaje, cache_file_emp_fichaje, \
    cache_file_resume_fichaje_path
from templates.misc.Functions_AuxFiles import get_events_op_date
from templates.misc.Functions_Files import get_info_f_file_name, get_info_bitacora, \
    unify_data_employee, get_info_t_file_name, get_list_files, extract_fichajes_file, \
    check_names_employees_in_cache, update_fichajes_resume_cache, get_dic_from_list_fichajes
from templates.Functions_GUI_Utils import create_var_none, create_Combobox, create_label, create_stringvar, \
    update_stringvars, create_spinboxes_time
from templates.misc.Functions_Files_RH import check_fichajes_files_in_directory
from templates.modules.Misc.Frame_CollapsingFrame import CollapsingFrame


class FichajesAuto(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # noinspection PyTypeChecker
        self.columnconfigure((0, 1, 2, 3, 4), weight=1)
        # ----------------------variables-------------------------
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.file_selected_3 = False
        self.master = master
        self.contracts = {}
        (self.dft, self.days_late, self.days_extra, self.absences_bit,
         self.contract_emp, self.lates_bit, self.extras_bit,
         self.total_extra2, self.primes_bit, self.files, self.max_date_g,
         self.min_date_g, self.dff, self.date_file, self.events_bitacora,
         self.dfb, self.days_absence, self.worked_days_f) = create_var_none(18)
        self.files_names_pairs = [[], []]
        self.files_names_main = []
        # ----------------string vars-------------
        (self.svar_absence_days_f, self.svar_late_days_f, self.svar_extra_days_f,
         self.svar_primes_days_f, self.svar_late_hours_f, self.svar_extra_hours_f,
         self.svar_worked_days_f) = create_stringvar(7, value="")
        # -------------------create title-----------------
        create_label(self, text='Telintec Software Fichajes',
                     row=0, column=0, columnspan=5, padx=0, pady=0,
                     font=('Helvetica', 32, 'bold'))
        # -------------------create entry for file selector-----------------
        create_label(self, text='Archivos Principales: ', row=1, column=0)
        create_label(self, text='Archivos Secundarios: ', row=1, column=2)
        # -------------------file selectors-----------------
        self.files_main_cb = create_Combobox(
            self, values=self.files_names_main, state="readonly", row=1, column=1, padx=0, pady=0)
        self.files_sec_t_cb = create_Combobox(
            self, values=self.files_names_pairs[1], state="readonly", row=1, column=3, padx=0, pady=0)
        self.files_main_cb.bind("<<ComboboxSelected>>", self.on_selected_file_fun)
        self.files_sec_t_cb.bind("<<ComboboxSelected>>", self.on_selected_file_fun)
        # -------------------create buttons-----------------
        self.frame_buttons = ttk.Frame(self)
        self.frame_buttons.grid(row=3, column=0, columnspan=5, sticky="nswe")
        self.frame_buttons.columnconfigure(0, weight=1)
        self.btn_update_files = ttk.Button(self.frame_buttons, text="Actualizar Archivos",
                                           command=self.read_files,
                                           width=25)
        self.btn_update_files.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        # -------------------create collapsing frame-----------------
        self.frame_collapse = CollapsingFrame(self)
        self.frame_collapse.grid(row=4, column=0, columnspan=6, sticky='nsew')
        # -------------------create tableview for data-----------------
        self.group_2 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_2.columnconfigure(0, weight=1)
        self.table_1 = Tableview(self.group_2)
        self.table_2 = Tableview(self.group_2)
        self.table_3 = Tableview(self.group_2)
        # ---------------------grupo filtrado por nombre------------------------------
        group_1 = ttk.Frame(self.frame_collapse, padding=5)
        # noinspection PyTypeChecker
        group_1.columnconfigure(0, weight=1)
        # ------------------------create expor button----------------
        frame_btns = ttk.Frame(group_1)
        frame_btns.grid(row=0, column=0, sticky="nswe")
        frame_btns.columnconfigure(0, weight=1)
        self.create_buttons(frame_btns)
        # ---------------filter by name widgets-------------
        frame_inputs = ttk.Frame(group_1)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure((1, 2, 3, 4, 5), weight=1)
        (self.clocks, self.window_time_in, self.window_time_out,
         self.label_time_in, self.label_time_out,
         self.name_emp_selector) = self.create_inputs(frame_inputs)
        # -------------------init read files-----------------
        self.read_files()
        # ------------------------create display data employee----------------
        frame_info_file_1 = ttk.Frame(group_1)
        frame_info_file_1.grid(row=2, column=0, sticky="nswe")
        frame_info_file_1.columnconfigure((0, 1, 2, 3, 4), weight=1)
        (self.days_normal_selector_f, self.days_absence_selector_f, self.days_prime_selector_f,
         self.days_late_selector_f, self.days_extra_selector_f,
         self.txt_c_normal, self.txt_c_absence, self.txt_c_prime,
         self.txt_c_late, self.txt_c_extra) = self.create_info_display_file1(frame_info_file_1)

        # ------------------------create collapsable-----------------
        self.frame_collapse.add(group_1, title="Informacion")
        self.frame_collapse.add(self.group_2, title="Tablas")

    def create_inputs(self, master):
        create_label(master, text='Empleado: ', row=0, column=1)
        name_emp_selector = create_Combobox(
            master, values=["no file selected"], state="readonly",
            row=1, column=1)
        name_emp_selector.bind("<<ComboboxSelected>>", self.on_name_emp_sel_action)
        create_label(master, text='Hora de entrada: ', row=0, column=2, sticky="w")
        clocks = []
        clock1, dict_c = create_spinboxes_time(master, self, 1, 2,
                                               mins_defaul=0, hours_default=8, title="entrada")
        clocks.append(dict_c)
        window_time_in = ttk.Scale(master, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                   command=self.change_time_grace)
        window_time_in.set(15)
        label_time_in = create_label(
            master, text=f'Gracia entrada: {int(window_time_in.get())} mins', row=1, column=3)
        create_label(master, text='Hora de salida: ', row=0, column=4, sticky="w")
        clock2, dict_c = create_spinboxes_time(master, self, 1, 4,
                                               mins_defaul=0, hours_default=18, title="salida")
        clocks.append(dict_c)
        window_time_out = ttk.Scale(master, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                    command=self.change_time_grace)
        window_time_out.set(15)
        label_time_out = create_label(
            master, text=f'Gracia salida: {int(window_time_out.get())} mins', row=1, column=5)
        return (clocks, window_time_in, window_time_out, label_time_in,
                label_time_out, name_emp_selector)

    def create_info_display_file1(self, master):
        create_label(
            master, text='Información resumida Sist. Fichaje', row=0, column=0,
            font=("Arial", 14, "bold"), columnspan=6)
        # labels days for employee
        create_label(master, textvariable=self.svar_worked_days_f, row=1, column=0, sticky="we")
        create_label(master, textvariable=self.svar_absence_days_f, row=2, column=0, sticky="we")
        create_label(master, textvariable=self.svar_primes_days_f, row=3, column=0, sticky="we")
        create_label(master, textvariable=self.svar_late_days_f, row=4, column=0, sticky="we")
        create_label(master, textvariable=self.svar_late_hours_f, row=4, column=1, sticky="we")
        create_label(master, textvariable=self.svar_extra_days_f, row=5, column=0, sticky="we")
        create_label(master, textvariable=self.svar_extra_hours_f, row=5, column=1, sticky="we")
        # comments
        comment_text_normal_days = ScrolledText(master, height=6, autohide=True)
        comment_text_normal_days.grid(row=1, column=3, sticky="nswe", padx=2, pady=5)
        comment_text_absence_days = ScrolledText(master, height=6, autohide=True)
        comment_text_absence_days.grid(row=2, column=3, sticky="nswe", padx=2, pady=5)
        comment_text_primes_days = ScrolledText(master, height=6, autohide=True)
        comment_text_primes_days.grid(row=3, column=3, sticky="nswe", padx=2, pady=5)
        comment_text_late_days = ScrolledText(master, height=6, autohide=True)
        comment_text_late_days.grid(row=4, column=3, sticky="nswe", padx=2, pady=5)
        comment_text_extra_days = ScrolledText(master, height=6, autohide=True)
        comment_text_extra_days.grid(row=5, column=3, sticky="nswe", padx=2, pady=5)

        # days selectors
        days_normal_selector = create_Combobox(
            master, values=["no data"], state="readonly", row=1, column=2, sticky="we")
        days_normal_selector.bind("<<ComboboxSelected>>", self.select_day_normal_fun_f)
        days_absence_selector = create_Combobox(
            master, values=["no data"], state="readonly", row=2, column=2, sticky="we")
        days_absence_selector.bind("<<ComboboxSelected>>", self.select_day_absence_fun_f)
        days_primes_selector = create_Combobox(
            master, values=["no data"], state="readonly", row=3, column=2, sticky="we")
        days_primes_selector.bind("<<ComboboxSelected>>", self.select_day_prime_fun_f)
        days_late_selector = create_Combobox(
            master, values=["no data"], state="readonly", row=4, column=2, sticky="we")
        days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late_fun_f)
        days_extra_selector = create_Combobox(
            master, values=["no data"], state="readonly", row=5, column=2, sticky="we")
        days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra_fun_f)
        return (
            days_normal_selector, days_absence_selector, days_primes_selector, days_late_selector, days_extra_selector,
            comment_text_normal_days, comment_text_absence_days, comment_text_primes_days, comment_text_late_days,
            comment_text_extra_days)

    def select_day_normal_fun_f(self, event):
        if "no data" in event.widget.get() :
            print("no data", event.widget.get())
            return
        if event.widget.get() != "no data":
            # date = pd.Timestamp(event.widget.get())
            date = event.widget.get()
            for day_key in self.normal_data_emp.keys():
                if date in day_key:
                    self.txt_c_normal.text.delete('1.0', 'end')
                    self.txt_c_normal.text.insert(ttk.END, "Horas trabajadas: \n", "keys")
                    self.txt_c_normal.text.insert(ttk.END, f"{self.normal_data_emp[day_key][0]}", "values")
                    self.txt_c_normal.text.insert(ttk.END, "\nDetalle: \n", "keys")
                    self.txt_c_normal.text.insert(ttk.END, f"{self.normal_data_emp[day_key][1]}", "values")
                    self.txt_c_normal.text.insert(ttk.END, "\nTimestamp: ", "keys")
                    self.txt_c_normal.text.insert(ttk.END, f"{self.normal_data_emp[day_key][2]}", "values")
                    self.txt_c_normal.text.tag_config("keys", foreground="green")
                    self.txt_c_normal.text.tag_config("values", foreground="black")
                    break

    def select_day_absence_fun_f(self, event):
        if "no data" in event.widget.get() :
            print("no data", event.widget.get())
            return
        date = event.widget.get()
        for day_key in self.absence_data_emp.keys():
            if date in day_key:
                self.txt_c_absence.text.delete('1.0', 'end')
                self.txt_c_absence.text.insert(ttk.END, "Detalle: \n", "keys")
                self.txt_c_absence.text.insert(ttk.END, f"{self.absence_data_emp[day_key][1]}", "values")
                self.txt_c_absence.text.insert(ttk.END, "\nTimestamp: ", "keys")
                for i, timestamp in enumerate(self.absence_data_emp[day_key][2]):
                    self.txt_c_absence.text.insert(ttk.END, f"{timestamp}", "values")
                    if i != len(self.absence_data_emp[day_key][2]) - 1:
                        self.txt_c_absence.text.insert(ttk.END, ", ", "values")
                self.txt_c_absence.text.tag_config("keys", foreground="green")
                self.txt_c_absence.text.tag_config("values", foreground="black")
                break

    def select_day_prime_fun_f(self, event):
        if "no data" in event.widget.get() :
            print("no data", event.widget.get())
            return
        date = event.widget.get()
        for day_key in self.prime_data_emp.keys():
            if date in day_key:
                self.txt_c_prime.text.delete('1.0', 'end')
                self.txt_c_prime.text.insert(ttk.END, "Detalle: \n", "keys")
                self.txt_c_prime.text.insert(ttk.END, f"{self.prime_data_emp[day_key][1]}", "values")
                self.txt_c_prime.text.insert(ttk.END, "\nTimestamp: ", "keys")
                for i, timestamp in enumerate(self.prime_data_emp[day_key][2]):
                    self.txt_c_prime.text.insert(ttk.END, f"{timestamp}", "values")
                    if i != len(self.prime_data_emp[day_key][2]) - 1:
                        self.txt_c_prime.text.insert(ttk.END, ", ", "values")
                self.txt_c_prime.text.tag_config("keys", foreground="green")
                self.txt_c_prime.text.tag_config("values", foreground="black")
                break

    def select_day_late_fun_f(self, event):
        if event.widget.get() == "no data":
            return
        date = event.widget.get()
        for day_key in self.late_data_emp.keys():
            if date in day_key:
                horas_float = self.late_data_emp[day_key][0]
                self.txt_c_late.text.delete('1.0', 'end')
                self.txt_c_late.text.insert(ttk.END, "Horas tarde: \n", "keys")
                self.txt_c_late.text.insert(ttk.END, f"{int(horas_float)} horas y {int(horas_float * 60 % 60)} minutos",
                                            "values")
                self.txt_c_late.text.insert(ttk.END, "\nDetalle: \n", "keys")
                self.txt_c_late.text.insert(ttk.END, f"{self.late_data_emp[day_key][1]}", "values")
                self.txt_c_late.text.insert(ttk.END, "\nTimestamp: ", "keys")
                for i, timestamp in enumerate(self.late_data_emp[day_key][2]):
                    self.txt_c_late.text.insert(ttk.END, f"{timestamp}", "values")
                    if i != len(self.late_data_emp[day_key][2]) - 1:
                        self.txt_c_late.text.insert(ttk.END, ", ", "values")
                self.txt_c_late.text.tag_config("keys", foreground="green")
                self.txt_c_late.text.tag_config("values", foreground="black")
                break

    def select_day_extra_fun_f(self, event):
        if "no data" in event.widget.get() :
            print("no data", event.widget.get())
            return
        date = event.widget.get()
        for day_key in self.extra_data_emp.keys():
            if date in day_key:
                horas_float = self.extra_data_emp[day_key][0]
                self.txt_c_extra.text.delete('1.0', 'end')
                self.txt_c_extra.text.insert(ttk.END, "Horas extra: \n", "keys")
                self.txt_c_extra.text.insert(ttk.END,
                                             f"{int(horas_float)} horas y {int(horas_float * 60 % 60)} minutos",
                                             "values")
                self.txt_c_extra.text.insert(ttk.END, "\nDetalle: \n", "keys")
                self.txt_c_extra.text.insert(ttk.END, f"{self.extra_data_emp[day_key][1]}", "values")
                self.txt_c_extra.text.insert(ttk.END, "\nTimestamp: ", "keys")
                for i, timestamp in enumerate(self.extra_data_emp[day_key][2]):
                    self.txt_c_extra.text.insert(ttk.END, f"{timestamp}", "values")
                    if i != len(self.extra_data_emp[day_key][2]) - 1:
                        self.txt_c_extra.text.insert(ttk.END, ", ", "values")
                self.txt_c_extra.text.tag_config("keys", foreground="green")
                self.txt_c_extra.text.tag_config("values", foreground="black")
                break

    def change_time_grace(self, event):
        if self.file_selected_1:
            self.label_time_in.configure(text=f'Gracia: {int(self.window_time_in.get())} mins')
            self.label_time_out.configure(text=f'Gracia: {int(self.window_time_out.get())} mins')

    def update_days_selectors(self):
        # -------------file 1---------------
        late_keys = []
        extra_keys = []
        absence_keys = []
        prime_keys = []
        total_late = 0
        total_extra = 0
        normal_keys = []
        for i in self.late_data_emp.keys():
            late_keys.append(str(i))
            total_late += self.late_data_emp[i][0]
        for i in self.extra_data_emp.keys():
            extra_keys.append(str(i))
            total_extra += self.extra_data_emp[i][0]
        for i in self.absence_data_emp.keys():
            absence_keys.append(str(i))
        for i in self.prime_data_emp.keys():
            prime_keys.append(str(i))
        for i in self.normal_data_emp.keys():
            normal_keys.append(str(i))
        late_keys = late_keys if len(late_keys) > 0 else ["no data"]
        extra_keys = extra_keys if len(extra_keys) > 0 else ["no data"]
        absence_keys = absence_keys if len(absence_keys) > 0 else ["no data"]
        prime_keys = prime_keys if len(prime_keys) > 0 else ["no data"]
        normal_keys = normal_keys if len(normal_keys) > 0 else ["no data"]
        self.days_normal_selector_f.configure(values=normal_keys)
        self.days_late_selector_f.configure(values=late_keys)
        self.days_extra_selector_f.configure(values=extra_keys)
        self.days_absence_selector_f.configure(values=absence_keys)
        self.days_prime_selector_f.configure(values=prime_keys)
        self.days_late_selector_f.configure(state="readonly")
        self.days_extra_selector_f.configure(state="readonly")
        self.days_absence_selector_f.configure(state="readonly")
        self.days_prime_selector_f.configure(state="readonly")
        self.days_normal_selector_f.configure(state="readonly")
        update_stringvars([
            (self.svar_late_hours_f, f'Total horas tarde: \n{round(total_late , 2)}'),
            (self.svar_extra_hours_f, f'Total horas extras: \n{round(total_extra , 2)}')
        ])

    def update_info_displayed(self, name):
        if name == "reset":
            update_stringvars(
                [(self.svar_worked_days_f, 'Numero de dias trabajados: NA.'),
                 (self.svar_absence_days_f, 'Numero de faltas: NA.'),
                 (self.svar_primes_days_f, 'Numero de dias con prima: NA.'),
                 (self.svar_late_days_f, 'Numero de dias tarde: NA.'),
                 (self.svar_extra_days_f, 'Numero de dias con horas extras: NA.'),
                 (self.svar_late_hours_f, 'Total horas tarde:'),
                 (self.svar_extra_hours_f, 'Total horas extras:')
                 ]
            )
            self.txt_c_normal.text.delete("1.0", "end")
            self.txt_c_absence.text.delete("1.0", "end")
            self.txt_c_prime.text.delete("1.0", "end")
            self.txt_c_late.text.delete("1.0", "end")
            self.txt_c_extra.text.delete("1.0", "end")
        else:
            df_name = self.dff[self.dff["name"] == name]
            id_emp = df_name["ID"].values[0]
            date_max = self.dff["Fecha"].max()
            # -----------file fichaje------------
            (worked_days_f, days_absence, count_l_f, count_e_f,
             days_late, days_extra) = get_info_f_file_name(
                self.dff, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_1, date_max=date_max)
            date_example = pd.to_datetime(worked_days_f[0][0])
            # ------------file ternium-----------
            (worked_days_t, worked_intime_t, count_l_t, count_e_t,
             days_late_t, days_extra_t, days_worked_t, days_not_worked_t) = get_info_t_file_name(
                self.dft, self.name_emp_selector.get(), self.clocks, self.window_time_in, self.window_time_out,
                self.file_selected_3, month=date_example.month, date_max=date_max)
            # ------------info bitacora-----------
            (days_absence_bit, days_extra_bit, days_primes_bit, days_lates_bit,
             absences_bit, extras_bit, primes_bit, lates_bit, normals_bit, early_bit,
             contract) = get_info_bitacora(
                self.dfb, name=self.name_emp_selector.get(), id_emp=id_emp, flag=self.file_selected_2, date_limit=date_max)
            (self.normal_data_emp, self.absence_data_emp, self.prime_data_emp,
             self.late_data_emp, self.extra_data_emp, self.early_data_emp) = unify_data_employee(
                [worked_days_f, days_worked_t, normals_bit],
                [days_absence, None, absences_bit],
                [None, None, primes_bit],
                [days_late, days_late_t, lates_bit],
                [days_extra, days_extra_t, extras_bit],
                [None, None, early_bit]
            )
            # update vars for fichaje file
            update_stringvars(
                [(self.svar_worked_days_f, f'# dias trabajados: \n{len(self.normal_data_emp.keys())}.'),
                 (self.svar_absence_days_f, f'# faltas: \n{len(self.absence_data_emp.keys())}.'),
                 (self.svar_late_days_f, f'# dias con atraso: \n{len(self.late_data_emp.keys())}.'),
                 (self.svar_extra_days_f, f'# dias con horas extras: \n{len(self.extra_data_emp.keys())}.'),
                 (self.svar_primes_days_f, f'# dias con prima: \n{len(self.prime_data_emp.keys())}.')])
            self.update_days_selectors()

    def on_name_emp_sel_action(self, event):
        if event.widget.get() != "no file selected":
            self.update_info_displayed("reset")
            self.update_info_displayed(event.widget.get())

    def read_files(self):
        # check files in the directory
        flag, self.files = check_fichajes_files_in_directory(files_fichaje_path, patterns_files_fichaje)
        self.files_names_pairs, self.files_names_main = get_list_files(self.files)
        self.files_main_cb.configure(values=self.files_names_main)
        self.files_sec_t_cb.configure(values=self.files_names_pairs[1])

    def read_file_ternium(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.dft = extract_fichajes_file(filename)
            coldata = []
            for i, col in enumerate(self.dft.columns.tolist()):
                coldata.append(
                    {"text": col, "stretch": True}
                )
            self.table_3 = Tableview(self.group_2, bootstyle="primary",
                                     coldata=coldata,
                                     rowdata=self.dft.values.tolist(),
                                     paginated=True,
                                     searchable=True,
                                     autofit=True)
            self.table_3.grid(row=2, column=0, sticky='nsew', padx=50, pady=10)
            self.file_selected_3 = True
            names_list = self.dft["name"].unique().tolist()
            names_and_ids = check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
            for name in names_and_ids.keys():
                name_db = names_and_ids[name]["name_db"]
                id_db = names_and_ids[name]["id"]
                self.dft.loc[self.dft["name"] == name, "name"] = name_db
                self.dft.loc[self.dft["name"] == name, "ID"] = id_db

    def read_file_fichaje(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.dff = extract_fichajes_file(filename)
            if len(self.dff) != 0:
                coldata = []
                for i, col in enumerate(self.dff.columns.tolist()):
                    coldata.append(
                        {"text": col, "stretch": True}
                    )
                self.table_1 = Tableview(self.group_2, bootstyle="primary",
                                         coldata=coldata,
                                         rowdata=self.dff.values.tolist(),
                                         paginated=True,
                                         searchable=True,
                                         autofit=True)
                self.table_1.grid(row=0, column=0, sticky='nsew', padx=50, pady=10)
                self.file_selected_1 = True
                names_list = self.dff["name"].unique().tolist()
                names_and_ids = check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
                for name in names_and_ids.keys():
                    name_db = names_and_ids[name]["name_db"]
                    id_db = names_and_ids[name]["id"]
                    self.dff.loc[self.dff["name"] == name, "name"] = name_db
                    self.dff.loc[self.dff["name"] == name_db, "ID"] = id_db
                # enables scales
                names_list = self.dff["name"].unique().tolist()
                self.name_emp_selector.configure(values=names_list)
                self.window_time_in.grid(row=0, column=3)
                self.window_time_out.grid(row=0, column=5)

    def on_selected_file_fun(self, event):
        filename = event.widget.get()
        if "Ternium" in filename:
            self.read_file_ternium(self.files[filename]["path"])
            self.update_info_displayed("reset")
        elif "Fichaje" in filename:
            self.files_names_pairs, files_names_f = get_list_files(self.files, filename)
            self.file_selected_3 = False
            self.files_sec_t_cb.configure(values=self.files_names_pairs[1])
            self.files_sec_t_cb.set(self.files_names_pairs[1][0])
            filename_sec_2 = self.files_names_pairs[1][0] if len(self.files_names_pairs[1]) > 0 else "No pair avaliable"
            if filename_sec_2 != "No pair avaliable":
                self.read_file_ternium(self.files[filename_sec_2]["path"])
                self.file_selected_3 = True
            self.name_emp_selector.configure(state="readonly")
            self.read_bitacora(self.files[filename]["date"])
            self.read_file_fichaje(self.files[filename]["path"])
            self.update_info_displayed("reset")

    def create_buttons(self, master):
        btn_export = ttk.Button(
            master, text="Exportar", command=self.button_export_click)
        btn_export.grid(row=0, column=0, sticky="n", padx=5, pady=5)
        return btn_export

    def button_export_click(self):
        data_resume = []
        id_list_f = self.dff["ID"].unique().tolist()
        id_list_t = self.dft["ID"].unique().tolist() if self.file_selected_3 else []
        id_list_b = self.dfb["ID"].unique().tolist() if self.file_selected_2 else []
        id_list = list(set(id_list_f + id_list_t + id_list_b))
        for id_emp in id_list:
            name = self.dff[self.dff["ID"] == id_emp]["name"].to_list()[0] if len(
                self.dff[self.dff["ID"] == id_emp]["name"].to_list()) > 0 else None
            if name is None:
                name = self.dft[self.dft["ID"] == id_emp]["name"].to_list()[0] if len(
                    self.dft[self.dft["ID"] == id_emp]["name"].to_list()) > 0 else None
            if name is None:
                name = self.dfb[self.dfb["ID"] == id_emp]["Nombre"].to_list()[0] if len(
                    self.dfb[self.dfb["ID"] == id_emp]["Nombre"].to_list()) > 0 else None
            if name is None:
                continue
            contract_emp = "otros"
            # get data for an employee
            (worked_days_f, worked_intime_f, count_l_f, count_e_f,
             days_late, days_extra) = get_info_f_file_name(
                self.dff, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_1)
            (worked_days_t, worked_intime_t, count_l_t, count_e_t,
             days_late_t, days_extra_t) = get_info_t_file_name(
                self.dft, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_3)
            if id_emp is not None:
                (days_absence_bit, days_extra_bit, days_primes_bit, days_lates_bit,
                 absences_bit, extras_bit, primes_bit, lates_bit, normals_bit, contract_emp) = get_info_bitacora(
                    self.dfb, name=self.name_emp_selector.get(), id_emp=id_emp, flag=self.file_selected_2)
            else:
                (days_absence_bit, days_extra_bit, days_primes_bit, days_lates_bit,
                 absences_bit, extras_bit, primes_bit, normals_bit, lates_bit) = (
                    None, None, None, None, None, None, None, None, None)
            # convert data in dictionaries
            dict_faltas, dict_late, dict_extra, dict_prima, dict_normal = get_dic_from_list_fichajes(
                (None, days_late, days_extra, None, None),
                oct_file=(absences_bit, lates_bit, extras_bit, primes_bit, normals_bit),
                ternium_file=(None, days_late_t, days_extra_t, None, None)
            )

            absences_bit = ["0", "0"] if absences_bit is None else absences_bit
            days_late = ["0", "0"] if days_late is None else days_late
            days_extra = ["0", "0"] if days_extra is None else days_extra
            primes_bit = ["0", "0"] if primes_bit is None else primes_bit
            normal_bit = ["0", "0"] if normals_bit is None else normals_bit
            row = (id_emp, name, contract_emp,
                   days_absence_bit[0], days_lates_bit[0], days_lates_bit[1], days_extra_bit[0], days_extra_bit[1],
                   days_primes_bit[0], dict_faltas, dict_late, dict_extra, dict_prima, dict_normal)
            data_resume.append(row)
        columns = ["ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Total horas tarde", "Dias Extra",
                   "Total horas extras", "Primas",
                   "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas", "Detalles normal"]
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in data_resume:
                data_f[column].append(row[i])
        df = pd.DataFrame.from_dict(data_f)
        # export csv
        path = asksaveasfilename(defaultextension=".csv",
                                 filetypes=[("CSV", "*.csv")])
        df.to_csv(path, index=False)
        update_fichajes_resume_cache(cache_file_resume_fichaje_path, data_resume)
        Messagebox.show_info(title="Info", message=f"Archivo exportado:\n{path}")

    def read_bitacora(self, date: str):
        self.date_file = datetime.strptime(date, "%d-%m-%Y")
        self.events_bitacora, columns = get_events_op_date(self.date_file, True)
        self.table_2 = Tableview(self.group_2,
                                 coldata=columns,
                                 rowdata=self.events_bitacora,
                                 paginated=True,
                                 searchable=True,
                                 autofit=True)
        self.table_2.grid(row=1, column=0, padx=20, pady=10, sticky="n")
        # create dataframe pandas
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in self.events_bitacora:
                if column == "Nombre":
                    data_f[column].append(row[i].upper())
                else:
                    data_f[column].append(row[i])
        self.dfb = pd.DataFrame.from_dict(data_f)
        self.file_selected_2 = True
