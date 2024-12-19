# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 25/abr./2024  at 14:51 $"

from datetime import datetime
from tkinter.filedialog import asksaveasfilename

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview

from static.constants import (
    files_fichaje_path,
    patterns_files_fichaje,
    cache_file_emp_fichaje,
    cache_file_resume_fichaje_path,
    format_date,
)
from templates.misc.Functions_AuxFiles import get_events_op_date
from templates.misc.Functions_Files import (
    get_info_f_file_name,
    get_info_bitacora,
    unify_data_employee,
    get_info_t_file_name,
    get_list_files,
    extract_fichajes_file,
    check_names_employees_in_cache,
    update_fichajes_resume_cache,
    get_dic_from_list_fichajes,
)
from templates.Functions_GUI_Utils import (
    create_var_none,
    create_Combobox,
    create_label,
    create_stringvar,
    update_stringvars,
    create_spinboxes_time,
)
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
        (
            self.dft,
            self.days_late,
            self.days_extra,
            self.absences_bit,
            self.contract_emp,
            self.lates_bit,
            self.extras_bit,
            self.total_extra2,
            self.primes_bit,
            self.files,
            self.max_date_g,
            self.min_date_g,
            self.dff,
            self.date_file,
            self.events_bitacora,
            self.dfb,
            self.days_absence,
            self.worked_days_f,
        ) = create_var_none(18)
        self.files_names_pairs = [[], []]
        self.files_names_main = []
        self.table_display = None
        # ----------------string vars-------------
        (
            self.svar_absence_days_f,
            self.svar_late_days_f,
            self.svar_extra_days_f,
            self.svar_primes_days_f,
            self.svar_late_hours_f,
            self.svar_extra_hours_f,
            self.svar_worked_days_f,
        ) = create_stringvar(7, value="")
        # -------------------create title-----------------
        create_label(
            self,
            text="Telintec Software Fichajes",
            row=0,
            column=0,
            columnspan=5,
            padx=0,
            pady=0,
            font=("Helvetica", 32, "bold"),
        )
        # -------------------create entry for file selector-----------------
        create_label(self, text="Archivos Principales: ", row=1, column=0)
        create_label(self, text="Archivos Secundarios: ", row=1, column=2)
        # -------------------file selectors-----------------
        self.files_main_cb = create_Combobox(
            self,
            values=self.files_names_main,
            state="readonly",
            row=1,
            column=1,
            padx=0,
            pady=0,
        )
        self.files_sec_t_cb = create_Combobox(
            self,
            values=self.files_names_pairs[1],
            state="readonly",
            row=1,
            column=3,
            padx=0,
            pady=0,
        )
        self.files_main_cb.bind("<<ComboboxSelected>>", self.on_selected_file_fun)
        self.files_sec_t_cb.bind("<<ComboboxSelected>>", self.on_selected_file_fun)
        # -------------------create buttons-----------------
        self.frame_buttons = ttk.Frame(self)
        self.frame_buttons.grid(row=3, column=0, columnspan=5, sticky="nswe")
        self.frame_buttons.columnconfigure(0, weight=1)
        self.btn_update_files = ttk.Button(
            self.frame_buttons,
            text="Actualizar Archivos",
            command=self.read_files,
            width=25,
        )
        self.btn_update_files.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        # -------------------create collapsing frame-----------------
        self.frame_collapse = CollapsingFrame(self)
        self.frame_collapse.grid(row=4, column=0, columnspan=6, sticky="nsew")
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
        (
            self.clocks,
            self.window_time_in,
            self.window_time_out,
            self.label_time_in,
            self.label_time_out,
            self.name_emp_selector,
        ) = self.create_inputs(frame_inputs)
        # -------------------init read files-----------------
        self.read_files()
        # ------------------------create display data employee----------------
        self.frame_info_file_1 = ttk.Frame(group_1)
        self.frame_info_file_1.grid(row=2, column=0, sticky="nswe")
        self.frame_info_file_1.columnconfigure((0, 1), weight=1)
        self.table_display = self.create_table_display()
        create_label(
            self.frame_info_file_1,
            text="Información resumida Sist. Fichaje",
            row=0,
            column=0,
            font=("Arial", 14, "bold"),
            columnspan=2,
        )
        (self.txt_details) = self.create_info_display_file1(self.frame_info_file_1)
        # ------------------------create collapsable-----------------
        self.frame_collapse.add(group_1, title="Informacion")
        self.frame_collapse.add(self.group_2, title="Tablas")

    def create_inputs(self, master):
        create_label(master, text="Empleado: ", row=0, column=1)
        name_emp_selector = create_Combobox(
            master, values=["no file selected"], state="readonly", row=1, column=1
        )
        name_emp_selector.bind("<<ComboboxSelected>>", self.on_name_emp_sel_action)
        create_label(master, text="Hora de entrada: ", row=0, column=2, sticky="w")
        clocks = []
        clock1, dict_c = create_spinboxes_time(
            master, self, 1, 2, mins_defaul=0, hours_default=8, title="entrada"
        )
        clocks.append(dict_c)
        window_time_in = ttk.Scale(
            master,
            from_=0,
            to=60,
            orient=ttk.HORIZONTAL,
            length=100,
            command=self.change_time_grace,
        )
        window_time_in.set(15)
        label_time_in = create_label(
            master,
            text=f"Gracia entrada: {int(window_time_in.get())} mins",
            row=1,
            column=3,
        )
        create_label(master, text="Hora de salida: ", row=0, column=4, sticky="w")
        clock2, dict_c = create_spinboxes_time(
            master, self, 1, 4, mins_defaul=0, hours_default=18, title="salida"
        )
        clocks.append(dict_c)
        window_time_out = ttk.Scale(
            master,
            from_=0,
            to=60,
            orient=ttk.HORIZONTAL,
            length=100,
            command=self.change_time_grace,
        )
        window_time_out.set(15)
        label_time_out = create_label(
            master,
            text=f"Gracia salida: {int(window_time_out.get())} mins",
            row=1,
            column=5,
        )
        return (
            clocks,
            window_time_in,
            window_time_out,
            label_time_in,
            label_time_out,
            name_emp_selector,
        )

    def create_info_display_file1(self, master, row_offset=1):
        comment_text_extra_days = ScrolledText(master, height=10, autohide=True)
        comment_text_extra_days.grid(
            row=0 + row_offset, column=1, sticky="nswe", padx=2, pady=5
        )
        return comment_text_extra_days

    def change_time_grace(self, event):
        if self.file_selected_1:
            self.label_time_in.configure(
                text=f"Gracia: {int(self.window_time_in.get())} mins"
            )
            self.label_time_out.configure(
                text=f"Gracia: {int(self.window_time_out.get())} mins"
            )

    def update_info_displayed(self, name):
        if name == "reset":
            update_stringvars(
                [
                    (self.svar_worked_days_f, "Numero de dias trabajados: NA."),
                    (self.svar_absence_days_f, "Numero de faltas: NA."),
                    (self.svar_primes_days_f, "Numero de dias con prima: NA."),
                    (self.svar_late_days_f, "Numero de dias tarde: NA."),
                    (self.svar_extra_days_f, "Numero de dias con horas extras: NA."),
                    (self.svar_late_hours_f, "Total horas tarde:"),
                    (self.svar_extra_hours_f, "Total horas extras:"),
                ]
            )
        else:
            df_name = self.dff[self.dff["name"] == name]
            id_emp = df_name["ID"].values[0]
            date_max = self.dff["Fecha"].max()
            # -----------file fichaje------------
            (
                worked_days_f,
                days_absence,
                count_l_f,
                count_e_f,
                days_late,
                days_extra,
                early_dic_f,
            ) = get_info_f_file_name(
                self.dff,
                name,
                self.clocks,
                self.window_time_in,
                self.window_time_out,
                self.file_selected_1,
                date_max=date_max,
            )
            date_example = pd.to_datetime(worked_days_f[0][0])
            # ------------file ternium-----------
            (
                worked_days_t,
                worked_intime_t,
                count_l_t,
                count_e_t,
                days_late_t,
                days_extra_t,
                days_worked_t,
                days_not_worked_t,
                days_early_t,
            ) = get_info_t_file_name(
                self.dft,
                self.name_emp_selector.get(),
                self.clocks,
                self.window_time_in,
                self.window_time_out,
                self.file_selected_3,
                month=date_example.month,
                date_max=date_max,
            )
            # ------------info bitacora-----------
            (
                days_absence_bit,
                days_extra_bit,
                days_primes_bit,
                days_lates_bit,
                absences_bit,
                extras_bit,
                primes_bit,
                lates_bit,
                normals_bit,
                early_bit,
                pasive_bit,
                contract,
            ) = get_info_bitacora(
                self.dfb,
                name=self.name_emp_selector.get(),
                id_emp=id_emp,
                flag=self.file_selected_2,
                date_limit=date_max,
            )
            (
                self.normal_data_emp,
                self.absence_data_emp,
                self.prime_data_emp,
                self.late_data_emp,
                self.extra_data_emp,
                self.early_data_emp,
                self.pasive_data_emp,
            ) = unify_data_employee(
                [worked_days_f, days_worked_t, normals_bit],
                [days_absence, None, absences_bit],
                [None, None, primes_bit],
                [days_late, days_late_t, lates_bit],
                [days_extra, days_extra_t, extras_bit],
                [early_dic_f, days_early_t, early_bit],
                [None, None, pasive_bit],
            )
            # update vars for fichaje file
            self.table_display = self.create_table_display(date_max, is_first=False)

    def on_name_emp_sel_action(self, event):
        if event.widget.get() != "no file selected":
            self.update_info_displayed("reset")
            self.update_info_displayed(event.widget.get())

    def read_files(self):
        # check files in the directory
        flag, self.files = check_fichajes_files_in_directory(
            files_fichaje_path, patterns_files_fichaje
        )
        self.files_names_pairs, self.files_names_main = get_list_files(self.files)
        self.files_main_cb.configure(values=self.files_names_main)
        self.files_sec_t_cb.configure(values=self.files_names_pairs[1])

    def read_file_ternium(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.dft = extract_fichajes_file(filename)
            coldata = []
            for i, col in enumerate(self.dft.columns.tolist()):
                coldata.append({"text": col, "stretch": True})
            self.table_3 = Tableview(
                self.group_2,
                bootstyle="primary",
                coldata=coldata,
                rowdata=self.dft.values.tolist(),
                paginated=True,
                searchable=True,
                autofit=True,
            )
            self.table_3.grid(row=2, column=0, sticky="nsew", padx=50, pady=10)
            self.file_selected_3 = True
            names_list = self.dft["name"].unique().tolist()
            names_and_ids = check_names_employees_in_cache(
                names_list, cache_file_emp_fichaje
            )
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
                    coldata.append({"text": col, "stretch": True})
                self.table_1 = Tableview(
                    self.group_2,
                    bootstyle="primary",
                    coldata=coldata,
                    rowdata=self.dff.values.tolist(),
                    paginated=True,
                    searchable=True,
                    autofit=True,
                )
                self.table_1.grid(row=0, column=0, sticky="nsew", padx=50, pady=10)
                self.file_selected_1 = True
                names_list = self.dff["name"].unique().tolist()
                names_and_ids = check_names_employees_in_cache(
                    names_list, cache_file_emp_fichaje
                )
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
            filename_sec_2 = (
                self.files_names_pairs[1][0]
                if len(self.files_names_pairs[1]) > 0
                else "No pair avaliable"
            )
            if filename_sec_2 != "No pair avaliable":
                self.read_file_ternium(self.files[filename_sec_2]["path"])
                self.file_selected_3 = True
            self.name_emp_selector.configure(state="readonly")
            self.read_bitacora(self.files[filename]["date"])
            self.read_file_fichaje(self.files[filename]["path"])
            self.update_info_displayed("reset")

    def create_buttons(self, master):
        btn_export = ttk.Button(
            master, text="Exportar", command=self.button_export_click
        )
        btn_export.grid(row=0, column=0, sticky="n", padx=5, pady=5)
        return btn_export

    def button_export_click(self):
        data_resume = []
        id_list_f = self.dff["ID"].unique().tolist()
        id_list_t = self.dft["ID"].unique().tolist() if self.file_selected_3 else []
        id_list_b = self.dfb["ID"].unique().tolist() if self.file_selected_2 else []
        id_list = list(set(id_list_f + id_list_t + id_list_b))
        for id_emp in id_list:
            name = (
                self.dff[self.dff["ID"] == id_emp]["name"].to_list()[0]
                if len(self.dff[self.dff["ID"] == id_emp]["name"].to_list()) > 0
                else None
            )
            if name is None:
                name = (
                    self.dft[self.dft["ID"] == id_emp]["name"].to_list()[0]
                    if len(self.dft[self.dft["ID"] == id_emp]["name"].to_list()) > 0
                    else None
                )
            if name is None:
                name = (
                    self.dfb[self.dfb["ID"] == id_emp]["Nombre"].to_list()[0]
                    if len(self.dfb[self.dfb["ID"] == id_emp]["Nombre"].to_list()) > 0
                    else None
                )
            if name is None:
                continue
            contract_emp = "otros"
            # get data for an employee
            (
                worked_days_f,
                worked_intime_f,
                count_l_f,
                count_e_f,
                days_late,
                days_extra,
                early_dic_f,
            ) = get_info_f_file_name(
                self.dff,
                name,
                self.clocks,
                self.window_time_in,
                self.window_time_out,
                self.file_selected_1,
            )
            (
                worked_days_t,
                worked_intime_t,
                count_l_t,
                count_e_t,
                days_late_t,
                days_extra_t,
                days_early_t,
            ) = get_info_t_file_name(
                self.dft,
                name,
                self.clocks,
                self.window_time_in,
                self.window_time_out,
                self.file_selected_3,
            )
            if id_emp is not None:
                (
                    days_absence_bit,
                    days_extra_bit,
                    days_primes_bit,
                    days_lates_bit,
                    absences_bit,
                    extras_bit,
                    primes_bit,
                    lates_bit,
                    normals_bit,
                    early_bit,
                    pasive_bit,
                    contract_emp,
                ) = get_info_bitacora(
                    self.dfb,
                    name=self.name_emp_selector.get(),
                    id_emp=id_emp,
                    flag=self.file_selected_2,
                )
            else:
                (
                    days_absence_bit,
                    days_extra_bit,
                    days_primes_bit,
                    days_lates_bit,
                    absences_bit,
                    extras_bit,
                    primes_bit,
                    normals_bit,
                    lates_bit,
                    early_bit,
                    pasive_bit,
                ) = (None, None, None, None, None, None, None, None, None, None, None)
            # convert data in dictionaries
            (
                dict_faltas,
                dict_late,
                dict_extra,
                dict_prima,
                dict_normal,
                dict_early,
                dict_pasive,
            ) = get_dic_from_list_fichajes(
                (None, days_late, days_extra, None, None, early_dic_f, None),
                oct_file=(
                    absences_bit,
                    lates_bit,
                    extras_bit,
                    primes_bit,
                    normals_bit,
                    early_bit,
                    pasive_bit,
                ),
                ternium_file=(
                    None,
                    days_late_t,
                    days_extra_t,
                    None,
                    None,
                    days_early_t,
                    None,
                ),
            )

            absences_bit = ["0", "0"] if absences_bit is None else absences_bit
            days_late = ["0", "0"] if days_late is None else days_late
            days_extra = ["0", "0"] if days_extra is None else days_extra
            primes_bit = ["0", "0"] if primes_bit is None else primes_bit
            normal_bit = ["0", "0"] if normals_bit is None else normals_bit
            early_bit = ["0", "0"] if early_bit is None else early_bit
            pasive_bit = ["0", "0"] if pasive_bit is None else pasive_bit
            row = (
                id_emp,
                name,
                contract_emp,
                days_absence_bit[0],
                days_lates_bit[0],
                days_lates_bit[1],
                days_extra_bit[0],
                days_extra_bit[1],
                days_primes_bit[0],
                dict_faltas,
                dict_late,
                dict_extra,
                dict_prima,
                dict_normal,
                dict_early,
                dict_pasive,
            )
            data_resume.append(row)
        columns = [
            "ID",
            "Nombre",
            "Contrato",
            "Faltas",
            "Tardanzas",
            "Total horas tarde",
            "Dias Extra",
            "Total horas extras",
            "Primas",
            "Detalles Faltas",
            "Detalles Tardanzas",
            "Detalles Extras",
            "Detalles Primas",
            "Detalles normal",
            "Detalles Early",
            "Detalles Pasivo",
        ]
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in data_resume:
                data_f[column].append(row[i])
        df = pd.DataFrame.from_dict(data_f)
        # export csv
        path = asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        df.to_csv(path, index=False)
        update_fichajes_resume_cache(cache_file_resume_fichaje_path, data_resume)
        Messagebox.show_info(title="Info", message=f"Archivo exportado:\n{path}")

    def read_bitacora(self, date: str):
        self.date_file = datetime.strptime(date, "%d-%m-%Y")
        self.events_bitacora, columns = get_events_op_date(self.date_file, True)
        self.table_2 = Tableview(
            self.group_2,
            coldata=columns,
            rowdata=self.events_bitacora,
            paginated=True,
            searchable=True,
            autofit=False,
        )
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

    def create_table_display(
        self, date_max=None, is_first=True, row_offset=1, col_offset=0
    ):
        self.table_display.destroy() if self.table_display is not None else None
        days_month = range(1, 32)
        columns = [
            "Dia",
            "Retardos",
            "Extras",
            "Salidas Temprano",
            "Faltas",
            "Primas",
            "Comentario",
            "timestamp",
        ]
        coldata = []
        for column in columns:
            if "Comentario" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "Dia" in column:
                coldata.append({"text": column, "stretch": False, "width": 30})
            elif "Extras" in column:
                coldata.append({"text": column, "stretch": False, "width": 65})
            elif "Retardos" in column:
                coldata.append({"text": column, "stretch": False, "width": 65})
            elif "Salidas Temprano" in column:
                coldata.append({"text": column, "stretch": False, "width": 105})
            elif "Faltas" in column:
                coldata.append({"text": column, "stretch": False, "width": 65})
            elif "Primas" in column:
                coldata.append({"text": column, "stretch": False, "width": 65})
            else:
                coldata.append({"text": column, "stretch": True})
        data = (
            self.generate_data_table_display(days_month, columns, date_max)
            if not is_first
            else []
        )
        master = self.frame_info_file_1
        table = Tableview(
            master,
            bootstyle="primary",
            coldata=coldata,
            rowdata=data,
            paginated=False,
            searchable=True,
            autofit=False,
            height=32,
        )
        table.grid(row=0 + row_offset, column=0 + col_offset, sticky="nswe")
        table.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table.get_columns()
        for item in columns_header:
            if item.headertext in ["timestamp"]:
                item.hide()
        return table

    def generate_data_table_display(self, days, columns, date_max=None):
        # (self.normal_data_emp, self.absence_data_emp, self.prime_data_emp,
        #  self.late_data_emp, self.extra_data_emp, self.early_data_emp)
        data = []
        date_max = datetime.now() if date_max is None else date_max
        month = date_max.month
        year = date_max.year
        for day in days:
            row = []
            comment = ""
            for header in columns:
                match header:
                    case "Retardos":
                        date_row = datetime(year, month, day).strftime(format_date)
                        dates_keys = self.late_data_emp.keys()
                        if date_row in dates_keys:
                            row.append(self.late_data_emp[date_row][0])
                            comment += self.late_data_emp[date_row][1] + "\n"
                            comment += f"{self.late_data_emp[date_row][2]}\n"
                        else:
                            row.append("")
                    case "Extras":
                        date_row = datetime(year, month, day).strftime(format_date)
                        dates_keys = self.extra_data_emp.keys()
                        if date_row in dates_keys:
                            row.append(self.extra_data_emp[date_row][0])
                            comment += self.extra_data_emp[date_row][1] + "\n"
                            comment += f"{self.extra_data_emp[date_row][2]}\n"
                        else:
                            row.append("")
                    case "Salidas Temprano":
                        date_row = datetime(year, month, day).strftime(format_date)
                        dates_keys = self.early_data_emp.keys()
                        if date_row in dates_keys:
                            row.append(self.early_data_emp[date_row][0])
                            comment += self.early_data_emp[date_row][1] + "\n"
                            comment += f"{self.early_data_emp[date_row][2]}\n"
                        else:
                            row.append("")
                    case "Faltas":
                        date_row = datetime(year, month, day).strftime(format_date)
                        dates_keys = self.absence_data_emp.keys()
                        if date_row in dates_keys:
                            row.append(self.absence_data_emp[date_row][0])
                            comment += self.absence_data_emp[date_row][1] + "\n"
                            comment += f"{self.absence_data_emp[date_row][2]}\n"
                        else:
                            row.append("")
                    case "Primas":
                        date_row = datetime(year, month, day).strftime(format_date)
                        dates_keys = self.prime_data_emp.keys()
                        if date_row in dates_keys:
                            row.append(self.prime_data_emp[date_row][0])
                            comment += self.prime_data_emp[date_row][1] + "\n"
                            comment += f"{self.prime_data_emp[date_row][2]}\n"
                        else:
                            row.append("")
                    case "timestamp":
                        (row.append(datetime.now().strftime(format_date)),)
                    case "Dia":
                        row.append(day)
                    case "Comentario":
                        row.append(comment)
                    case _:
                        row.append("")
            data.append(row)
        return data

    def _on_double_click_table(self, event):
        item = event.widget.selection()[0]
        column = event.widget.identify_column(event.x)
        col_index = int(column[1:]) - 1
        item_data = event.widget.item(item, "values")
        self.display_content_info(item_data, col_index)

    def display_content_info(self, data, column):
        value = float(data[column]) if data[column] != "" and column < 6 else 0
        event = ""
        match column:
            case 1:
                event = "Retardo"
                value_txt = (
                    f"Horas: {int(value)}, {int(value%1*60)} minutos"
                    if value != 0
                    else ""
                )
            case 2:
                event = "Horas Extras"
                value_txt = (
                    f"Horas: {int(value)}, {int(value%1*60)} minutos"
                    if value != 0
                    else ""
                )
            case 3:
                event = "Salida Temprano"
                value_txt = (
                    f"Horas: {int(value)}, {int(value%1*60)} minutos"
                    if value != 0
                    else ""
                )
            case 4:
                value_txt = f"Dias: {1}" if data[column] != "" else ""
            case 5:
                value_txt = f"Dias: {1}" if data[column] != "" else ""
            case _:
                event = ""
                value_txt = ""
        self.txt_details.delete("1.0", "end")
        if event != "":
            self.txt_details.insert("end", f"{event}--> {value_txt}\n")
        self.txt_details.insert("end", f"---Comentarios y detalles---\n {data[6]}\n")
