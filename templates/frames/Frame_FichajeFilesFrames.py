# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 14/nov./2023  at 17:12 $'

from datetime import timedelta
from tkinter.filedialog import asksaveasfilename

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.dialogs.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

import templates.Functions_Files as cb
from static.extensions import cache_file_resume_fichaje, cache_file_emp_fichaje
from templates.Functions_SQL import get_id_employee
from templates.Funtions_Utils import create_var_none, create_label, create_Combobox, update_stringvars, create_stringvar
from templates.frames.Frame_CollapsingFrame import CollapsingFrame
from templates.frames.SubFrame_Plots import FramePlot


class FichajesFilesGUI(ScrolledFrame):
    def __init__(self, master=None):
        super().__init__(master, autohide=True)
        # noinspection PyTypeChecker
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # ----------------------variables-------------------------
        nb = ttk.Notebook(self)
        frame_1 = FichajesAuto(nb)
        frame_2 = FichajesManual(nb)
        nb.add(frame_1, text='Automatico')
        nb.add(frame_2, text='Manual')
        nb.grid(row=0, column=0, sticky="nswe", padx=15, pady=5)


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
        (self.dft, self.days_late, self.days_extra, self.days_faltas,
         self.contract_emp, self.days_late2, self.days_extra2,
         self.total_extra2, self.days_prima, self.files, self.max_date_g,
         self.min_date_g, self.dff) = create_var_none(13)
        self.files_names_pairs = [[], []]
        self.files_names_main = []
        # ----------------string vars-------------
        (self.svar_worked_days_t, self.svar_late_days_t, self.svar_extra_days_t,
         self.svar_worked_days_within_t, self.svar_late_hours_t, self.svar_extra_hours_t,
         self.svar_nlate_hours_day_t, self.svar_late_hours_comment_t,
         self.svar_extra_hours_day_t, self.svar_extra_hours_comment_t,
         self.svar_puerta_out_t, self.svar_puerta_in_t,
         self.svar_worked_days_f, self.svar_late_days_f, self.svar_extra_days_f,
         self.svar_worked_days_within_f, self.svar_late_hours_f, self.svar_extra_hours_f,
         self.svar_nlate_hours_day_f, self.svar_late_hours_comment_f,
         self.svar_extra_hours_day_f, self.svar_extra_hours_comment_f,
         self.svar_puerta_out_f, self.svar_puerta_in_f, self.svar_faltas, self.svar_late_days_op,
         self.svar_extra_days_op, self.svar_primas_op, self.svar_com_missed,
         self.svar_com_late, self.svar_com_extra, self.svar_com_prima) = create_stringvar(32, value="")
        # -------------------create title-----------------
        create_label(self, text='Telintec Software Fichajes',
                     row=0, column=0, columnspan=5, padx=0, pady=0,
                     font=('Helvetica', 32, 'bold'))
        # -------------------create entry for file selector-----------------
        create_label(self, text='Archivos Principales: ', row=1, column=0)
        create_label(self, text='Archivos Secundarios: ', row=1, column=2)
        create_label(self, text='Rango: ', row=2, column=0)
        # -------------------file selectors-----------------
        self.files_main_cb = create_Combobox(
            self, values=self.files_names_main, state="readonly", row=1, column=1, padx=0, pady=0)
        self.files_sec_o_cb = create_Combobox(
            self, values=self.files_names_pairs[0], state="readonly", row=1, column=3, padx=0, pady=0)
        self.files_sec_t_cb = create_Combobox(
            self, values=self.files_names_pairs[1], state="readonly", row=1, column=4, padx=0, pady=0)
        self.files_sec_o_cb.bind("<<ComboboxSelected>>", self._select_file_fun)
        self.files_main_cb.bind("<<ComboboxSelected>>", self._select_file_fun)
        self.files_sec_t_cb.bind("<<ComboboxSelected>>", self._select_file_fun)
        # -------------------create date range selector-----------------
        self.date_ranges = create_Combobox(
            self, values=[""], state="readonly", row=2, column=1, padx=0, pady=0, columnspan=3, sticky="nswe")
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
        # ---------------filter by name widgets-------------
        frame_inputs = ttk.Frame(group_1)
        frame_inputs.grid(row=0, column=0, sticky="nswe")
        frame_inputs.columnconfigure((1, 2, 3, 4, 5), weight=1)
        (self.clocks, self.window_time_in, self.window_time_out,
         self.label_time_in, self.label_time_out,
         self.name_emp_selector) = self.create_inputs(frame_inputs)
        # -------------------init read files-----------------
        self.read_files()
        # ------------------------create display data employee----------------
        # -------labels result file 1-------
        frame_info_file_1 = ttk.Frame(group_1)
        frame_info_file_1.grid(row=1, column=0, sticky="nswe")
        frame_info_file_1.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.days_late_selector_f, self.days_extra_selector_f = self.create_info_display_file1(frame_info_file_1)
        # -------labels result file 2-------
        frame_info_file_2 = ttk.Frame(group_1)
        frame_info_file_2.grid(row=2, column=0, sticky="nswe")
        frame_info_file_2.columnconfigure((0, 1, 2), weight=1)
        (self.days_missing_selector2, self.days_late_selector2,
         self.days_extra_selector2, self.days_primas_selector) = self.create_info_display_file2(frame_info_file_2)
        # -------labels result file 3-------
        frame_info_file_3 = ttk.Frame(group_1)
        frame_info_file_3.grid(row=3, column=0, sticky="nswe")
        frame_info_file_3.columnconfigure((0, 1, 2, 3), weight=1)
        self.days_late_selector_t, self.days_extra_selector_t = self.create_info_display_file3(frame_info_file_3)
        # ------------------------create expor button----------------
        frame_btns = ttk.Frame(group_1)
        frame_btns.grid(row=4, column=0, sticky="nswe")
        frame_btns.columnconfigure(0, weight=1)
        self.create_buttons(frame_btns)
        # ------------------------create collapsable-----------------
        self.frame_collapse.add(group_1, title="Informacion")
        self.frame_collapse.add(self.group_2, title="Tablas")

    def create_inputs(self, master):
        create_label(master, text='Empleado: ', row=0, column=1)
        name_emp_selector = create_Combobox(
            master, values=["no file selected"], state="readonly",
            row=1, column=1)
        name_emp_selector.bind("<<ComboboxSelected>>", self.name_emp_sel_action)
        create_label(master, text='Hora de entrada: ', row=0, column=2, sticky="w")
        clocks = []
        clock1, dict_c = cb.create_spinboxes_time(master, self, 1, 2,
                                                  mins_defaul=0, hours_default=8, title="entrada")
        clocks.append(dict_c)
        window_time_in = ttk.Scale(master, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                   command=self.change_time_grace)
        window_time_in.set(15)
        label_time_in = create_label(
            master, text=f'Gracia entrada: {int(window_time_in.get())} mins', row=1, column=3)
        create_label(master, text='Hora de salida: ', row=0, column=4, sticky="w")
        clock2, dict_c = cb.create_spinboxes_time(master, self, 1, 4,
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
            master, text='Información resumida archivo principal', row=2, column=0,
            font=("Arial", 12, "bold"), columnspan=6)
        create_label(master, textvariable=self.svar_worked_days_f, row=3, column=0, sticky="w")
        create_label(master, textvariable=self.svar_worked_days_within_f, row=4, column=0, sticky="w")
        # late hours
        create_label(master, textvariable=self.svar_late_days_f, row=5, column=0, sticky="w")
        create_label(master, textvariable=self.svar_late_hours_f, row=5, column=1)
        create_label(master, textvariable=self.svar_nlate_hours_day_f, row=5, column=3)
        create_label(master, textvariable=self.svar_puerta_in_f, row=5, column=4)
        create_label(master, textvariable=self.svar_late_hours_comment_f, row=5, column=5)
        # extra hours
        create_label(master, textvariable=self.svar_extra_days_f, row=6, column=0, sticky="w")
        create_label(master, textvariable=self.svar_extra_hours_f, row=6, column=1)
        create_label(master, textvariable=self.svar_extra_hours_day_f, row=6, column=3)
        create_label(master, textvariable=self.svar_puerta_out_f, row=6, column=4)
        create_label(master, textvariable=self.svar_extra_hours_comment_f, row=6, column=5)
        days_late_selector = create_Combobox(
            master, values=["no data selected"], state="readonly", row=5, column=2)
        days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late_fun_f)
        days_extra_selector = create_Combobox(
            master, values=["no data selected"], state=ttk.DISABLED, row=6, column=2)
        days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra_fun_f)
        return days_late_selector, days_extra_selector

    def create_info_display_file2(self, master):
        create_label(
            master, text='Información archivo Operaciones', row=0, column=0,
            font=("Arial", 12, "bold"), columnspan=6)
        create_label(master, textvariable=self.svar_faltas,
                     row=1, column=0, sticky="w")
        create_label(master, textvariable=self.svar_late_days_op,
                     row=2, column=0, sticky="w")
        create_label(master, textvariable=self.svar_extra_days_op,
                     row=3, column=0, sticky="w")
        create_label(master, textvariable=self.svar_primas_op,
                     row=4, column=0, sticky="w")
        # coments label
        create_label(
            master, textvariable=self.svar_com_missed,
            row=1, column=2, font=('Helvetica', 8))
        create_label(
            master, textvariable=self.svar_com_late,
            row=2, column=2, font=('Helvetica', 8))
        create_label(
            master, textvariable=self.svar_com_extra,
            row=3, column=2, font=('Helvetica', 8))
        create_label(
            master, textvariable=self.svar_com_prima,
            row=4, column=2, font=('Helvetica', 8))
        days_missing_selector2 = create_Combobox(
            master, values=["no data selected"], state="readonly",
            row=1, column=1)
        days_missing_selector2.bind("<<ComboboxSelected>>", self.select_day_faltas)
        days_late_selector2 = create_Combobox(
            master, values=["no data selected"], state="readonly",
            row=2, column=1)
        days_late_selector2.bind("<<ComboboxSelected>>", self.select_day_late2)
        days_extra_selector2 = create_Combobox(
            master, values=["no data selected"], state="readonly",
            row=3, column=1)
        days_extra_selector2.bind("<<ComboboxSelected>>", self.select_day_extra2)
        days_primas_selector = create_Combobox(
            master, values=["no data selected"], state="readonly",
            row=4, column=1)
        days_primas_selector.bind("<<ComboboxSelected>>", self.select_day_primas)
        return days_missing_selector2, days_late_selector2, days_extra_selector2, days_primas_selector

    def select_day_faltas(self, event):
        date = event.widget.get()
        if not self.file_selected_2:
            return
        # date = self.days_missing_selector2.get()
        for day, comment in self.days_faltas:
            if day == date:
                self.svar_com_missed.set(comment)
                break

    def select_day_late2(self, event):
        date = event.widget.get()
        if not self.file_selected_2:
            return
        for day, comment in self.days_late2:
            if day == date:
                self.svar_com_late.set(comment)
                break

    def select_day_extra2(self, event):
        date = event.widget.get()
        if not self.file_selected_2:
            return
        for day, comment, value in self.days_extra2:
            if day == date:
                self.svar_com_extra.set(str(value) + " horas. " + comment)
                break

    def select_day_primas(self, event):
        date = event.widget.get()
        if not self.file_selected_2:
            return
        for day, comment in self.days_prima:
            if day == date:
                self.svar_com_prima.set(comment)
                break

    def change_time_grace(self, event):
        if self.file_selected_1:
            self.label_time_in.configure(text=f'Gracia: {int(self.window_time_in.get())} mins')
            self.label_time_out.configure(text=f'Gracia: {int(self.window_time_out.get())} mins')

    def update_late_extra_days_selectors(self):
        # -------------file 1---------------
        late_keys = []
        extra_keys = []
        total_late = 0
        total_extra = 0
        for i in self.days_late.keys():
            late_keys.append(str(i))
            total_late += self.days_late[i][0].seconds
        for i in self.days_extra.keys():
            extra_keys.append(str(i))
            total_extra += self.days_extra[i][0].seconds
        if len(late_keys) == 0:
            late_keys.append("no data")
        if len(extra_keys) == 0:
            extra_keys.append("no data")
        self.days_late_selector_f.configure(values=late_keys)
        self.days_extra_selector_f.configure(values=extra_keys)
        self.days_late_selector_f.configure(state="readonly")
        self.days_extra_selector_f.configure(state="readonly")
        self.days_late_selector_f.current(0)
        self.days_extra_selector_f.current(0)
        update_stringvars([
            (self.svar_late_hours_f, f'Total horas tarde: \n{round(total_late / 3600, 2)}'),
            (self.svar_extra_hours_f, f'Total horas extras: \n{round(total_extra / 3600, 2)}')
        ])
        # -------------file 2---------------
        faltas_keys = []
        late_keys2 = []
        extra_keys2 = []
        primas_keys = []
        for date, comment in self.days_faltas:
            faltas_keys.append(str(date))
        for date, comment in self.days_late2:
            late_keys2.append(str(date))
        for date, comment, value in self.days_extra2:
            extra_keys2.append(str(date))
        for date, comment in self.days_prima:
            primas_keys.append(str(date))
        if len(faltas_keys) == 0:
            faltas_keys.append("no data selected")
        if len(late_keys2) == 0:
            late_keys2.append("no data selected")
        if len(extra_keys2) == 0:
            extra_keys2.append("no data selected")
        if len(primas_keys) == 0:
            primas_keys.append("no data selected")
        self.days_missing_selector2.configure(values=faltas_keys)
        self.days_missing_selector2.current(0)
        self.days_late_selector2.configure(values=late_keys2)
        self.days_late_selector2.current(0)
        self.days_extra_selector2.configure(values=extra_keys2)
        self.days_extra_selector2.current(0)
        self.days_primas_selector.configure(values=primas_keys)
        self.days_primas_selector.current(0)

    def update_info_displayed(self, name):
        if name == "reset":
            update_stringvars(
                [(self.svar_worked_days_f, f'Numero de dias trabajados: NA.'),
                 (self.svar_late_days_f, f'Numero de dias tarde: NA.'),
                 (self.svar_extra_days_f, f'Numero de dias con horas extras: NA.'),
                 (self.svar_worked_days_within_f, f'Numero de dias dentro de horario: NA.'),
                 (self.svar_faltas, f'Dias con falta: NA.'),
                 (self.svar_late_days_op, f'Dias tarde: NA.'),
                 (self.svar_extra_days_op,
                  f'Dias con horas extra: NA.\nTotal de horas extra: NA'),
                 (self.svar_primas_op, f'Dias con prima: NA.'),
                 (self.svar_late_hours_f, f'Total horas tarde:'),
                 (self.svar_extra_hours_f, f'Total horas extras:')
                 ])
        else:
            # -----------file fichaje------------
            (worked_days_f, worked_intime_f, count_l_f, count_e_f,
             self.days_late, self.days_extra) = cb.get_info_f_file_name(
                self.dff, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_1)
            # ------------file ternium-----------
            (worked_days_t, worked_intime_t, count_l_t, count_e_t,
             self.days_late_t, self.days_extra_t) = cb.get_info_t_file_name(
                self.dft, self.name_emp_selector.get(), self.clocks, self.window_time_in, self.window_time_out,
                self.file_selected_3)
            # ------------file oct-----------
            (self.contract_emp, self.days_faltas, self.days_late2,
             self.days_extra2, total_extra2, self.days_prima) = cb.get_info_o_file_name(
                contracts=self.contracts, name=self.name_emp_selector.get(), flag=self.file_selected_2)
            # update vars for fichaje file
            update_stringvars(
                [(self.svar_worked_days_f, f'Numero de dias trabajados: {worked_days_f}.'),
                 (self.svar_late_days_f, f'Numero de dias tarde: {count_l_f}.'),
                 (self.svar_extra_days_f, f'Numero de dias con horas extras: {count_e_f}.'),
                 (self.svar_worked_days_within_f, f'Numero de dias dentro de horario: {worked_intime_f}.')])
            # update vars for ternium file
            update_stringvars(
                [(self.svar_worked_days_t, f'Numero de dias trabajados: {worked_days_t}.'),
                 (self.svar_late_days_t, f'Numero de dias tarde: {count_l_t}.'),
                 (self.svar_extra_days_t, f'Numero de dias con horas extras: {count_e_t}.'),
                 (self.svar_worked_days_within_t, f'Numero de dias dentro de horario: {worked_intime_t}.')])
            # update vars for oct file
            update_stringvars(
                [(self.svar_faltas, f'Dias con falta: {len(self.days_faltas)}.'),
                 (self.svar_late_days_op, f'Dias tarde: {len(self.days_late2)}.'),
                 (self.svar_extra_days_op,
                  f'Dias con horas extra: {len(self.days_extra2)}.\nTotal de horas extra: {total_extra2}'),
                 (self.svar_primas_op, f'Dias con prima: {len(self.days_prima)}.')])

    def name_emp_sel_action(self, event):
        if event.widget.get() != "no file selected":
            self.update_info_displayed(event.widget.get())
            self.update_late_extra_days_selectors()

    def read_files(self):
        # check files in the directory
        flag, self.files = cb.check_fichajes_files_in_directory("files/", ["Fichaje", "OCTreport", "Ternium"])
        self.files_names_pairs, self.files_names_main = cb.get_list_files(self.files)
        self.files_main_cb.configure(values=self.files_names_main)
        self.files_sec_o_cb.configure(values=self.files_names_pairs[0])
        self.files_sec_t_cb.configure(values=self.files_names_pairs[1])

    def check_dates_ranges(self):
        # max and min dates from dataframe
        return
        df_dates = self.dff.copy()
        max_date = df_dates["Fecha/hora_in"].max()
        min_date = df_dates["Fecha/hora_in"].min()
        print(f"max date: {max_date}")
        print(f"min date: {min_date}")
        # max and min dates from contracts
        table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in table_data:
                data_f[column].append(row[i])
        df_contracts = pd.DataFrame.from_dict(data_f)
        df_contracts["Fecha"] = pd.to_datetime(df_contracts["Fecha"], format='mixed')
        max_date_c = df_contracts["Fecha"].max()
        min_date_c = df_contracts["Fecha"].min()
        print(f"max date c: {max_date_c}")
        print(f"min date c: {min_date_c}")
        # check the max and min dates general
        self.max_date_g = max_date if max_date <= max_date_c else max_date_c
        self.min_date_g = min_date if min_date >= min_date_c else min_date_c
        fortnights = self.max_date_g - self.min_date_g
        print(f"fortnights: {fortnights.days}")
        print(f"max date g: {self.max_date_g}", f"day: {self.max_date_g.weekday()}")
        print(f"min date g: {self.min_date_g}", f"day: {self.min_date_g.weekday()}")
        fort_options = fortnights.days / 15
        list_fortnights = []
        if fort_options >= 2:
            for i in range(int(fort_options)):
                if i == 0:
                    list_fortnights.append((self.min_date_g, self.min_date_g + timedelta(days=15)))
                elif i == int(fort_options) - 1:
                    list_fortnights.append((self.min_date_g + timedelta(days=i * 15), self.max_date_g))
                else:
                    list_fortnights.append((self.min_date_g + timedelta(days=i * 15),
                                            self.min_date_g + timedelta(days=i * 15) + timedelta(days=14)))
        else:
            list_fortnights.append((self.min_date_g, self.max_date_g))
        list_display = []
        for item in list_fortnights:
            diff = item[1] - item[0]
            list_display.append(f"{diff.days} days - {item[0].date()} - {item[1].date()}")
        list_display = list_display if len(list_display) > 0 else ["no ranges avaliable"]
        self.date_ranges.configure(values=list_display)
        self.date_ranges.current(0)
        # self.date_ranges.configure(values=list_fortnights)

    def read_file_oct(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.contracts = cb.extract_data_file_contracts(filename)
            if len(self.contracts) != 0:
                table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
                self.table_2 = Tableview(self.group_2, bootstyle="primary",
                                         coldata=columns,
                                         rowdata=table_data,
                                         paginated=True,
                                         searchable=True,
                                         autofit=True)
                self.table_2.grid(row=1, column=0, sticky='nsew', padx=50, pady=10)
                self.file_selected_2 = True

    def read_file_ternium(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.dft = cb.extract_fichajes_file(filename)
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
            names_and_ids = cb.check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
            for name in names_and_ids.keys():
                name_db = names_and_ids[name]["name_db"]
                id_db = names_and_ids[name]["id"]
                self.dft.loc[self.dft["name"] == name, "name"] = name_db
                self.dft.loc[self.dft["name"] == name, "ID"] = id_db

    def read_file_fichaje(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.dff = cb.extract_fichajes_file(filename)
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
                names_and_ids = cb.check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
                for name in names_and_ids.keys():
                    name_db = names_and_ids[name]["name_db"]
                    id_db = names_and_ids[name]["id"]
                    self.dff.loc[self.dff["name"] == name, "name"] = name_db
                    self.dff.loc[self.dff["name"] == name, "ID"] = id_db
                # enables scales
                names_list = self.dff["name"].unique().tolist()
                self.name_emp_selector.configure(values=names_list)
                self.window_time_in.grid(row=0, column=3)
                self.window_time_out.grid(row=0, column=5)

    def _select_file_fun(self, event):
        filename = event.widget.get()
        if "Ternium" in filename:
            self.read_file_ternium(self.files[filename]["path"])
            self.update_info_displayed("reset")
        elif "OCTreport" in filename:
            self.read_file_oct(self.files[filename]["path"])
            self.update_info_displayed("reset")
        elif "Fichaje" in filename:
            self.files_names_pairs, files_names_o = cb.get_list_files(self.files, filename)
            self.files_sec_o_cb.configure(values=self.files_names_pairs)
            self.files_sec_o_cb.set(self.files_names_pairs[0])
            filename_sec_1 = self.files_names_pairs[0][0] if len(self.files_names_pairs[0]) > 0 else "No pair avaliable"
            self.file_selected_2 = False
            self.file_selected_3 = False
            if filename_sec_1 != "No pair avaliable":
                if "OCT" in filename_sec_1:
                    self.read_file_oct(self.files[filename_sec_1]["path"])
                    self.file_selected_2 = True
                else:
                    self.read_file_ternium(self.files[filename_sec_1]["path"])
            filename_sec_2 = self.files_names_pairs[0][0] if len(self.files_names_pairs[1]) > 0 else "No pair avaliable"
            if filename_sec_2 != "No pair avaliable":
                if "OCT" in filename_sec_2:
                    self.read_file_oct(self.files[filename_sec_2]["path"])
                else:
                    self.read_file_ternium(self.files[filename_sec_2]["path"])
            self.name_emp_selector.configure(state="readonly")
            self.read_file_fichaje(self.files[filename]["path"])
            self.update_info_displayed("reset")

    def create_buttons(self, master):
        btn_export = ttk.Button(
            master, text="Exportar", command=self.button_export_click)
        btn_export.grid(row=0, column=0, sticky="n", padx=5, pady=5)
        # btn_export_2 = ttk.Button(
        #     master, text="Exportar/empleado", command=self.button_export_emp_click)
        # btn_export_2.grid(row=0, column=1, sticky="n", padx=5, pady=5)
        return btn_export

    def create_info_display_file3(self, master):
        create_label(
            master, text='Información archivo Ternium', row=2, column=0,
            font=("Arial", 12, "bold"), columnspan=6)
        create_label(master, textvariable=self.svar_worked_days_t, row=3, column=0, sticky="w")
        create_label(master, textvariable=self.svar_worked_days_within_t, row=4, column=0, sticky="w")
        # late hours
        create_label(master, textvariable=self.svar_late_days_t, row=5, column=0, sticky="w")
        create_label(master, textvariable=self.svar_late_hours_t, row=5, column=1)
        create_label(master, textvariable=self.svar_nlate_hours_day_t, row=5, column=3)
        create_label(master, textvariable=self.svar_puerta_in_f, row=5, column=4)
        create_label(master, textvariable=self.svar_late_hours_comment_t, row=5, column=5)
        # extra hours
        create_label(master, textvariable=self.svar_extra_days_t, row=6, column=0, sticky="w")
        create_label(master, textvariable=self.svar_extra_hours_t, row=6, column=1)
        create_label(master, textvariable=self.svar_extra_hours_day_t, row=6, column=3)
        create_label(master, textvariable=self.svar_puerta_out_t, row=6, column=4)
        create_label(master, textvariable=self.svar_extra_hours_comment_t, row=6, column=5)
        days_late_selector = create_Combobox(
            master, values=["no data selected"], state="readonly", row=5, column=2)
        days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late_fun_t)
        days_extra_selector = create_Combobox(
            master, values=["no data selected"], state=ttk.DISABLED, row=6, column=2)
        days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra_fun_t)
        return days_late_selector, days_extra_selector

    def select_day_late_fun_f(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(event.widget.get())
            aux = self.days_late[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_nlate_hours_day_f.set(f'Horas tarde: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_puerta_in_f.set(f'Puerta de entrada: \n{self.days_late[date][1]}')
            name = self.name_emp_selector.get()
            df_name = self.dff[self.dff["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            getawey = df_name[(df_name["Fecha/hora_out"] > limit_hour_down) &
                              (df_name["Fecha/hora_out"] < limit_hour_up)]
            self.svar_late_hours_comment_f.set(
                f'Hora de salida: \n{getawey["Fecha/hora_out"].to_list()[0]}\nPuerta: {getawey["Fuente de fichaje de salida"].to_list()[0]}')
        else:
            print("no data selected")

    def select_day_extra_fun_f(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(event.widget.get())
            aux = self.days_extra[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_extra_hours_day_f.set(f'Horas extras: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_puerta_out_f.set(f'Puerta de salida: \n{self.days_extra[date][1]}')
            name = self.name_emp_selector.get()
            df_name = self.dff[self.dff["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            entrance = df_name[(df_name["Fecha/hora_in"] > limit_hour_down) &
                               (df_name["Fecha/hora_in"] < limit_hour_up)]
            self.svar_extra_hours_comment_f.set(
                f'Hora de entrada: \n{entrance["Fecha/hora_in"].to_list()[0]}\nPuerta: {entrance["Fuente de fichaje de entrada"].to_list()[0]}')
        else:
            print("no data selected")

    def select_day_late_fun_t(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(event.widget.get())
            aux = self.days_late[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_late_hours_t.set(f'Horas tarde: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_puerta_in_t.set(f'Puerta de entrada: \n{self.days_late[date][1]}')
            name = self.name_emp_selector.get()
            df_name = self.dft[self.dft["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            getawey = df_name[(df_name["Fecha/hora"] > limit_hour_down) &
                              (df_name["Fecha/hora"] < limit_hour_up) &
                              (df_name["in_out"] == "FUERA")]
            self.svar_late_hours_comment_t.set(
                f'Hora de salida: \n{getawey["Fecha/hora"].to_list()[0]}\nPuerta: {getawey["Puerta"].to_list()[0]}')
        else:
            print("no data selected")

    def select_day_extra_fun_t(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(event.widget.get())
            aux = self.days_extra[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_extra_hours_day_t.set(f'Horas extras: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_puerta_out_t.set(f'Puerta de salida: \n{self.days_extra[date][1]}')
            name = self.name_emp_selector.get()
            df_name = self.dft[self.dft["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            entrance = df_name[(df_name["Fecha/hora"] > limit_hour_down) &
                               (df_name["Fecha/hora"] < limit_hour_up) &
                               (df_name["in_out"] == "DENTRO")]
            self.svar_extra_hours_comment_t.set(
                f'Hora de entrada: \n{entrance["Fecha/hora"].to_list()[0]}\nPuerta: {entrance["Puerta"].to_list()[0]}')
        else:
            print("no data selected")

    def button_export_emp_click(self):
        name = self.name_emp_selector.get()
        id_emp = self.dff[self.dff["name"] == name]["ID"].to_list()[0] if len(
            self.dff[self.dff["name"] == name]["ID"].to_list()) > 0 else None
        if id_emp is None:
            if self.file_selected_3:
                id_emp = self.dft[self.dft["name"] == name]["ID"].to_list()[0] if len(
                    self.dft[self.dft["name"] == name]["ID"].to_list()) > 0 else None
        else:
            id_emp = None
        # get data for an employee
        (worked_days_f, worked_intime_f, count_l_f, count_e_f,
         days_late, days_extra) = cb.get_info_f_file_name(
            self.dff, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_1)
        (worked_days_t, worked_intime_t, count_l_t, count_e_t,
         days_late_t, days_extra_t) = cb.get_info_t_file_name(
            self.dft, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_3)
        if id_emp is not None:
            (contract_emp, days_faltas, days_late_o,
             days_extra_o, total_extra2, days_prima) = cb.get_info_o_file_name(
                contracts=self.contracts, name=name, id_2=id_emp, flag=self.file_selected_2)
        else:
            (contract_emp, days_faltas, days_late_o,
             days_extra_o, total_extra2, days_prima) = (None, None, None, None, None, None)
        # convert data in dictionaries
        dict_faltas, dict_late, dict_extra, dict_prima = cb.get_dic_from_list_fichajes(
            (None, days_late, days_extra, None),
            oct_file=(days_faltas, days_late_o, days_extra_o, days_prima),
            ternium_file=(None, days_late_t, days_extra_t, None)
        )
        days_faltas = [] if days_faltas is None else days_faltas
        days_late = [] if days_late is None else days_late
        days_extra = [] if days_extra is None else days_extra
        days_prima = [] if days_prima is None else days_prima
        row = (id_emp, name, contract_emp,
               len(days_faltas), len(days_late), len(days_extra), total_extra2,
               len(days_prima), dict_faltas, dict_late, dict_extra, dict_prima)
        table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in table_data:
                data_f[column].append(row[i])
        df = pd.DataFrame.from_dict(data_f)
        if self.name_emp_selector.get() != "no name selected" and self.name_emp_selector.get() != "":
            id_n = get_id_employee(self.name_emp_selector.get())
            df = df[df["ID"] == id_n]
            # select a path to save file
            path = asksaveasfilename(defaultextension=".csv",
                                     filetypes=[("CSV", "*.csv")])
            df.to_csv(path, index=False)
            Messagebox.show_info(title="Info", message=f"Archivo exportado:\n{path}")
        else:
            Messagebox.show_error(title="Alert", message="primero seleccione un empleado")

    def button_export_click(self):
        data_resume = []
        name_list_f = self.dff["name"].unique().tolist()
        name_list_t = self.dft["name"].unique().tolist() if self.file_selected_3 else []
        name_list_o = []
        for contract in self.contracts.keys():
            for emp in self.contracts[contract].values():
                if emp["id"] is not None:
                    name_list_o.append(emp["name_db"])
        name_list = list(set(name_list_f + name_list_o + name_list_t))
        for name in name_list:
            id_emp = self.dff[self.dff["name"] == name]["ID"].to_list()[0] if len(
                self.dff[self.dff["name"] == name]["ID"].to_list()) > 0 else None
            if id_emp is None:
                if self.file_selected_3:
                    id_emp = self.dft[self.dft["name"] == name]["ID"].to_list()[0] if len(
                        self.dft[self.dft["name"] == name]["ID"].to_list()) > 0 else None
            else:
                id_emp = None
            # get data for an employee
            (worked_days_f, worked_intime_f, count_l_f, count_e_f,
             days_late, days_extra) = cb.get_info_f_file_name(
                self.dff, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_1)
            (worked_days_t, worked_intime_t, count_l_t, count_e_t,
             days_late_t, days_extra_t) = cb.get_info_t_file_name(
                self.dft, name, self.clocks, self.window_time_in, self.window_time_out, self.file_selected_3)
            if id_emp is not None:
                (contract_emp, days_faltas, days_late_o,
                 days_extra_o, total_extra2, days_prima) = cb.get_info_o_file_name(
                    contracts=self.contracts, name=name, id_2=id_emp, flag=self.file_selected_2)
            else:
                (contract_emp, days_faltas, days_late_o,
                 days_extra_o, total_extra2, days_prima) = (None, None, None, None, None, None)
            # convert data in dictionaries
            dict_faltas, dict_late, dict_extra, dict_prima = cb.get_dic_from_list_fichajes(
                (None, days_late, days_extra, None),
                oct_file=(days_faltas, days_late_o, days_extra_o, days_prima),
                ternium_file=(None, days_late_t, days_extra_t, None)
            )
            days_faltas = [] if days_faltas is None else days_faltas
            days_late = [] if days_late is None else days_late
            days_extra = [] if days_extra is None else days_extra
            days_prima = [] if days_prima is None else days_prima
            row = (id_emp, name, contract_emp,
                   len(days_faltas), len(days_late), len(days_extra), total_extra2,
                   len(days_prima), dict_faltas, dict_late, dict_extra, dict_prima)
            data_resume.append(row)
        columns = ["ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Dias Extra", "Total horas extras", "Primas",
                   "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas"]
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
        cb.update_fichajes_resume_cache(cache_file_resume_fichaje, data_resume)
        Messagebox.show_info(title="Info", message=f"Archivo exportado:\n{path}")


class FichajesManual(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        # variables
        flag, self.files = cb.check_fichajes_files_in_directory("files/", ["Fichaje", "OCTreport", "Ternium"])
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.file_selected_3 = False
        self.contracts = None
        self.files_ternium, self.files_oct, self.files_fichaje = self.list_files_type()
        (self.dff, self.days_late_f, self.days_extra_f,
         self.dft, self.days_late_t, self.days_extra_t,
         self.days_faltas_op, self.data_con_emp_op, self.days_late_op,
         self.days_extra_op, self.days_prima_op,
         self.max_date_g, self.min_date_g) = create_var_none(13)
        (self.svar_wd_f, self.svar_late_f, self.svar_nday_extra_f, self.svar_wd_intime_f,
         self.svar_late_hours_f, self.svar_tot_extra_hours_f, self.svar_late_h_by_day_f,
         self.svar_late_hday_comment_f, self.svar_extra_h_by_day_f,
         self.svar_extra_hday_comment_f, self.svar_out_door_f,
         self.svar_in_door_f,
         self.svar_missed_days, self.svar_late_op, self.svar_extra_hours_op,
         self.svar_primas_op, self.svar_com_missed_days, self.svar_com_late_op,
         self.svar_com_extra_op, self.svar_com_primas_op,
         self.svar_wd_t, self.svar_late_t, self.svar_nday_extra_t, self.svar_wd_intime_t,
         self.svar_late_hours_t, self.svar_tot_extra_hours_t, self.svar_late_h_by_day_t,
         self.svar_late_hday_comment_t, self.svar_extra_h_by_day_t,
         self.svar_extra_hday_comment_t, self.svar_out_door_t,
         self.svar_in_door_t,
         ) = create_stringvar(32, value="")
        # widgets
        self.frame_collapse = CollapsingFrame(self)
        self.frame_collapse.grid(row=0, column=0, sticky='nsew')
        self.frame_collapse.columnconfigure(0, weight=1)

        # -----------------------group 1 frame----------------------------------
        self.group_1 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_1.columnconfigure(0, weight=1)
        frame_inputs1 = ttk.Frame(self.group_1, padding=5)
        frame_inputs1.grid(row=3, column=0, sticky="nswe")
        frame_inputs1.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        (self.clocks_f, self.window_time_in_f, self.window_time_out_f,
         self.label_time_in_f, self.label_time_out_f,
         self.name_emp_selector_f) = self.create_inputs_f(frame_inputs1)
        # -------------------resume info
        frame_info1 = ttk.Frame(self.group_1, padding=5)
        frame_info1.grid(row=4, column=0, sticky="nswe")
        frame_info1.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.days_late_selector_f, self.days_extra_selector_f = self.create_info_display_file1(
            frame_info1, 0)
        self.plot1_1 = FramePlot(self.group_1)
        # --------------------------group 2 frame-------------------------------
        self.group_2 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_2.columnconfigure(0, weight=1)
        frame_inputs2 = ttk.Frame(self.group_2, padding=5)
        frame_inputs2.grid(row=0, column=0, sticky="nswe")
        # frame_inputs2.columnconfigure((0, 1), weight=1)
        self.name_oct_selector = self.create_inputs_o(frame_inputs2)
        # -------labels result file 2-------
        frame_info2 = ttk.Frame(self.group_2, padding=5)
        frame_info2.grid(row=1, column=0, sticky="nswe")
        frame_info2.columnconfigure((0, 1, 2), weight=1)
        (self.days_missing_selector2, self.days_late_selector2,
         self.days_extra_selector2, self.days_primas_selector) = self.create_info_display_file2(frame_info2)
        self.plot2_1 = FramePlot(self.group_2)
        # -----------------------group 3 frame----------------------------------
        self.group_3 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_3.columnconfigure(0, weight=1)
        frame_inputs3 = ttk.Frame(self.group_3, padding=5)
        frame_inputs3.grid(row=3, column=0, sticky="nswe")
        frame_inputs3.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        (self.clocks_t, self.window_time_in_t, self.window_time_out_t,
         self.label_time_in_t, self.label_time_out_t,
         self.name_emp_selector_t) = self.create_inputs_f(frame_inputs3, True)
        # -------------------resume info
        frame_info3 = ttk.Frame(self.group_3, padding=5)
        frame_info3.grid(row=4, column=0, sticky="nswe")
        frame_info3.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.days_late_selector_t, self.days_extra_selector_t = self.create_info_display_file1(
            frame_info3, 1)
        self.plot1_1 = FramePlot(self.group_3)

        self.frame_collapse.add(self.group_1, title="Archivos Fichaje")
        self.frame_collapse.add(self.group_2, title="Archivos OCT")
        self.frame_collapse.add(self.group_3, title="Archivos Ternium")

    def on_file_selected(self, event):
        filename = event.widget.get()
        if "OCT" in filename:
            self.generate_data_files_oct(self.files[filename]["path"])
            self.file_selected_2 = True
        else:
            self.data_files_fichaje(self.files[filename]["path"])

    def list_files_type(self):
        files_ternium = []
        files_oct = []
        files_f = []
        if len(self.files) > 0:
            for file in self.files.keys():
                if "Ternium" in file:
                    files_ternium.append(file)
                elif "OCT" in file:
                    files_oct.append(file)
                else:
                    files_f.append(file)
        return files_ternium, files_oct, files_f

    def data_files_fichaje(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            if "Ternium" in filename:
                self.dft = cb.extract_fichajes_file(filename)
                names_list = self.dft["name"].unique().tolist()
                names_and_ids = cb.check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
                for name in names_and_ids.keys():
                    name_db = names_and_ids[name]["name_db"]
                    id_db = names_and_ids[name]["id"]
                    self.dft.loc[self.dft["name"] == name, "name"] = name_db
                    self.dft.loc[self.dft["name"] == name, "ID"] = id_db
                names_list = self.dft["name"].unique().tolist()
                self.name_emp_selector_t.configure(values=names_list)
                # enables scales
                self.window_time_in_t.grid(row=3, column=1)
                self.window_time_out_t.grid(row=3, column=3)
                self.file_selected_3 = True
            elif "Fichaje" in filename:
                self.dff = cb.extract_fichajes_file(filename)
                names_list = self.dff["name"].unique().tolist()
                names_and_ids = cb.check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
                for name in names_and_ids.keys():
                    name_db = names_and_ids[name]["name_db"]
                    id_db = names_and_ids[name]["id"]
                    self.dff.loc[self.dff["name"] == name, "name"] = name_db
                    self.dff.loc[self.dff["name"] == name, "ID"] = id_db
                # enables scales
                names_list = self.dff["name"].unique().tolist()
                self.name_emp_selector_f.configure(values=names_list)
                # enables scales
                self.window_time_in_f.grid(row=3, column=1)
                self.window_time_out_f.grid(row=3, column=3)
                self.file_selected_1 = True

    def generate_data_files_oct(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.contracts = cb.extract_data_file_contracts(filename)
            if len(self.contracts) != 0:
                table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
                self.file_selected_2 = True
                names_oct = []
                for row in table_data:
                    name = row[1]
                    if name not in names_oct:
                        names_oct.append(name)
                self.name_oct_selector.configure(values=names_oct)

    def create_info_display_file1(self, master, type_i=0):
        svars = [
            [self.svar_wd_f, self.svar_wd_intime_f, self.svar_late_f,
             self.svar_late_hours_f, self.svar_late_h_by_day_f,
             self.svar_in_door_f, self.svar_late_hday_comment_f,
             self.svar_nday_extra_f, self.svar_tot_extra_hours_f,
             self.svar_extra_h_by_day_f, self.svar_out_door_f,
             self.svar_extra_hday_comment_f],
            [self.svar_wd_t, self.svar_wd_intime_t, self.svar_late_t,
             self.svar_late_hours_t, self.svar_late_h_by_day_t,
             self.svar_in_door_t, self.svar_late_hday_comment_t,
             self.svar_nday_extra_t, self.svar_tot_extra_hours_t,
             self.svar_extra_h_by_day_t, self.svar_out_door_t,
             self.svar_extra_hday_comment_t]
        ]
        create_label(
            master, text='Información resumida archivo principal', row=5, column=0, columnspan=6)
        create_label(master, textvariable=svars[type_i][0], row=6, column=0)
        create_label(master, textvariable=svars[type_i][1], row=7, column=0)
        # late hours
        create_label(master, textvariable=svars[type_i][2], row=8, column=0)
        create_label(master, textvariable=svars[type_i][3], row=8, column=1)
        create_label(master, textvariable=svars[type_i][4], row=8, column=3)
        create_label(master, textvariable=svars[type_i][5], row=8, column=4)
        create_label(master, textvariable=svars[type_i][6], row=8, column=5)
        # extra hours
        create_label(master, textvariable=svars[type_i][7], row=9, column=0)
        create_label(master, textvariable=svars[type_i][8], row=9, column=1)
        create_label(master, textvariable=svars[type_i][9], row=9, column=3)
        create_label(master, textvariable=svars[type_i][10], row=9, column=4)
        create_label(master, textvariable=svars[type_i][11], row=9, column=5)
        days_late_selector = create_Combobox(
            master, values=["no data selected"], state="readonly", row=8, column=2)
        days_extra_selector = create_Combobox(
            master, values=["no data selected"], state=ttk.DISABLED, row=9, column=2)
        if type_i == 0:
            days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late_fun_f)
            days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra_fun_f)
        else:
            days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late)
            days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra)
        return days_late_selector, days_extra_selector

    def create_info_display_file2(self, master):
        create_label(
            master, text='Información resumida archivos secundario', row=3, column=0, columnspan=6)
        create_label(master, textvariable=self.svar_missed_days, row=4, column=0)
        create_label(master, textvariable=self.svar_late_op, row=5, column=0)
        create_label(master, textvariable=self.svar_extra_hours_op, row=6, column=0)
        create_label(master, textvariable=self.svar_primas_op, row=7, column=0)
        # coments label
        create_label(
            master, textvariable=self.svar_com_missed_days, row=4, column=2, font=('Helvetica', 8),
            columnspan=4)
        create_label(
            master, textvariable=self.svar_com_late_op, row=5, column=2, font=('Helvetica', 8),
            columnspan=4)
        create_label(
            master, textvariable=self.svar_com_extra_op, row=6, column=2, font=('Helvetica', 8),
            columnspan=4)
        create_label(
            master, textvariable=self.svar_com_primas_op, row=7, column=2, font=('Helvetica', 8),
            columnspan=4)
        days_missing_selector2 = create_Combobox(
            master, values=["no data selected"], state="readonly", row=4, column=1)
        days_missing_selector2.bind("<<ComboboxSelected>>", self.select_day_faltas)
        days_late_selector2 = create_Combobox(
            master, values=["no data selected"], state="readonly", row=5, column=1)
        days_late_selector2.bind("<<ComboboxSelected>>", self.select_day_late2)
        days_extra_selector2 = create_Combobox(
            master, values=["no data selected"], state="readonly", row=6, column=1)
        days_extra_selector2.bind("<<ComboboxSelected>>", self.select_day_extra2)
        days_primas_selector = create_Combobox(
            master, values=["no data selected"], state="readonly", row=7, column=1)
        days_primas_selector.bind("<<ComboboxSelected>>", self.select_day_primas)
        return days_missing_selector2, days_late_selector2, days_extra_selector2, days_primas_selector

    def select_day_faltas(self, event):
        date = event.widget.get()
        # date = self.days_missing_selector.get()
        for day, comment in self.days_faltas_op:
            if day == date:
                self.svar_com_missed_days.set(comment)
                break

    def select_day_late2(self, event):
        date = event.widget.get()
        # date = self.days_late_selector2.get()
        for day, comment in self.days_late_op:
            if day == date:
                self.svar_com_late_op.set(comment)
                break

    def select_day_extra2(self, event):
        date = event.widget.get()
        # date = self.days_extra_selector2.get()
        for day, comment, value in self.days_extra_op:
            if day == date:
                self.svar_com_extra_op.set(str(value) + " horas. " + comment)
                break

    def select_day_primas(self, event):
        date = event.widget.get()
        # date = self.days_primas_selector.get()
        for day, comment in self.days_prima_op:
            if day == date:
                self.svar_com_primas_op.set(comment)
                break

    def select_day_late_fun_f(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(event.widget.get())
            aux = self.days_late_f[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_late_h_by_day_f.set(f'Horas tarde: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_in_door_f.set(f'Puerta de entrada: \n{self.days_late_f[date][1]}')
            name = self.name_emp_selector_f.get()
            df_name = self.dff[self.dff["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            getawey = df_name[(df_name["Fecha/hora_out"] > limit_hour_down) &
                              (df_name["Fecha/hora_out"] < limit_hour_up)]
            self.svar_late_hday_comment_f.set(
                f'Hora de salida: \n{getawey["Fecha/hora_out"].to_list()[0]}\nPuerta: {getawey["Fuente de fichaje de salida"].to_list()[0]}')
        else:
            print("no data selected")

    def select_day_extra_fun_f(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(event.widget.get())
            aux = self.days_extra_f[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_extra_h_by_day_f.set(f'Horas extras: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_out_door_f.set(f'Puerta de salida: \n{self.days_extra_f[date][1]}')
            name = self.name_emp_selector_f.get()
            df_name = self.dff[self.dff["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            entrance = df_name[(df_name["Fecha/hora_in"] > limit_hour_down) &
                               (df_name["Fecha/hora_in"] < limit_hour_up)]
            self.svar_extra_hday_comment_f.set(
                f'Hora de entrada: \n{entrance["Fecha/hora_in"].to_list()[0]}\nPuerta: {entrance["Fuente de fichaje de entrada"].to_list()[0]}')
        else:
            print("no data selected")

    def select_day_late(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(self.days_late_selector_t.get())
            aux = self.days_late_t[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_late_h_by_day_t.set(f'Horas tarde: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_in_door_t.set(f'Puerta de entrada: \n{self.days_late_t[date][1]}')
            name = self.name_emp_selector_t.get()
            df_name = self.dft[self.dft["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            getawey = df_name[(df_name["Fecha/hora"] > limit_hour_down) &
                              (df_name["Fecha/hora"] < limit_hour_up) &
                              (df_name["in_out"] == "FUERA")]
            self.svar_late_hday_comment_t.set(
                f'Hora de salida: \n{getawey["Fecha/hora"].to_list()[0]}\nPuerta: {getawey["Puerta"].to_list()[0]}')
        else:
            print("no data selected")

    def select_day_extra(self, event):
        if event.widget.get() != "no data selected":
            date = pd.Timestamp(self.days_extra_selector_t.get())
            aux = self.days_extra_t[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.svar_extra_h_by_day_t.set(f'Horas extras: \n{int(hours)} con {int(minutes)} minutos.')
            self.svar_out_door_t.set(f'Puerta de salida: \n{self.days_extra_t[date][1]}')
            name = self.name_emp_selector_t.get()
            df_name = self.dft[self.dft["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            entrance = df_name[(df_name["Fecha/hora"] > limit_hour_down) &
                               (df_name["Fecha/hora"] < limit_hour_up) &
                               (df_name["in_out"] == "DENTRO")]
            self.svar_extra_hday_comment_t.set(
                f'Hora de entrada: \n{entrance["Fecha/hora"].to_list()[0]}\nPuerta: {entrance["Puerta"].to_list()[0]}')
        else:
            print("no data selected")

    def select_name_emp_f(self, event):
        if event.widget.get() != "no name selected":
            (worked_days, worked_intime, count, count2,
             self.days_late_f, self.days_extra_f) = cb.get_info_f_file_name(
                self.dff, self.name_emp_selector_f.get(), self.clocks_f,
                self.window_time_in_f, self.window_time_out_f,
                self.file_selected_1)
            update_stringvars(
                [(self.svar_wd_f, f'Numero de dias trabajados: {worked_days}.'),
                 (self.svar_late_f, f'Numero de dias tarde: {count}.'),
                 (self.svar_nday_extra_f, f'Numero de dias con horas extras: {count2}.'),
                 (self.svar_wd_intime_f, f'Numero de dias dentro de horario: {worked_intime}.')])
            self.update_late_extra_days()
            data_chart = {"data": {'Tarde': count, 'Extras': count2,
                                   'A tiempo': worked_intime, "Trabajado": worked_days},
                          "title": f"Datos de {event.widget.get()}",
                          "ylabel": "Dias"
                          }
            self.plot1_1 = FramePlot(self.group_1, data_chart, "bar")
            self.plot1_1.grid(row=5, column=0, padx=10, pady=10, columnspan=6)
        else:
            print("no data selected")

    def select_name_emp_t(self, event):
        if event.widget.get() != "no name selected":
            (worked_days, worked_intime, count, count2,
             self.days_late_t, self.days_extra_t) = cb.get_info_t_file_name(
                self.dft, self.name_emp_selector_t.get(), self.clocks_t, self.window_time_in_t, self.window_time_out_t,
                self.file_selected_3)
            update_stringvars(
                [(self.svar_wd_t, f'Numero de dias trabajados: {worked_days}.'),
                 (self.svar_late_t, f'Numero de dias tarde: {count}.'),
                 (self.svar_nday_extra_t, f'Numero de dias con horas extras: {count2}.'),
                 (self.svar_wd_intime_t, f'Numero de dias dentro de horario: {worked_intime}.')])
            self.update_late_extra_days()
            data_chart = {"data": {'Tarde': count, 'Extras': count2,
                                   'A tiempo': worked_intime, "Trabajado": worked_days},
                          "title": f"Datos de {event.widget.get()}",
                          "ylabel": "Dias"
                          }
            self.plot1_1 = FramePlot(self.group_1, data_chart, "bar")
            self.plot1_1.grid(row=5, column=0, padx=10, pady=10, columnspan=6)
        else:
            print("no data selected")

    def select_name_oct(self, event):
        if event.widget.get() != "no name selected":
            (self.data_con_emp_op, self.days_faltas_op, self.days_late_op, self.days_extra_op,
             total_extra2, self.days_prima_op) = cb.get_info_o_file_name(
                contracts=self.contracts, name=event.widget.get(), flag=self.file_selected_2)
            update_stringvars(
                [(self.svar_missed_days, f'Dias con falta: {len(self.days_faltas_op)}.'),
                 (self.svar_late_op, f'Dias tarde: {len(self.days_late_op)}.'),
                 (self.svar_extra_hours_op,
                  f'Dias con horas extra: {len(self.days_extra_op)}.\nTotal de horas extra: {total_extra2}'),
                 (self.svar_primas_op, f'Dias con prima: {len(self.days_prima_op)}.'),
                 (self.svar_com_missed_days, ""),
                 (self.svar_com_late_op, ""),
                 (self.svar_com_extra_op, ""),
                 (self.svar_com_primas_op, "")])
            self.update_late_extra_days_oct()
            data_chart = {"data": {'Faltas': len(self.days_faltas_op), 'Tarde': len(self.days_late_op),
                                   'Extras': len(self.days_extra_op), 'Primas': len(self.days_prima_op)},
                          "title": f"Datos de {event.widget.get()}",
                          "ylabel": "Dias"
                          }
            self.plot2_1 = FramePlot(self.group_2, data_chart, "bar")
            self.plot2_1.grid(row=8, column=0, padx=10, pady=10, columnspan=3)
        else:
            print("no name selected")

    def update_late_extra_days(self):
        if self.file_selected_1:
            late_keys = []
            extra_keys = []
            total_late = 0
            total_extra = 0
            for i in self.days_late_f.keys():
                late_keys.append(str(i))
                total_late += self.days_late_f[i][0].seconds
            for i in self.days_extra_f.keys():
                extra_keys.append(str(i))
                total_extra += self.days_extra_f[i][0].seconds
            if len(late_keys) == 0:
                late_keys.append("no data")
            if len(extra_keys) == 0:
                extra_keys.append("no data")
            self.days_late_selector_f.configure(values=late_keys)
            self.days_extra_selector_f.configure(values=extra_keys)
            self.days_late_selector_f.configure(state="readonly")
            self.days_extra_selector_f.configure(state="readonly")
            self.days_late_selector_f.current(0)
            self.days_extra_selector_f.current(0)
            update_stringvars([
                (self.svar_late_hours_f, f'Total horas tarde: \n{round(total_late / 3600, 2)}'),
                (self.svar_tot_extra_hours_f, f'Total horas extras: \n{round(total_extra / 3600, 2)}')
            ])
        if self.file_selected_3:
            late_keys = []
            extra_keys = []
            total_late = 0
            total_extra = 0
            for i in self.days_late_t.keys():
                late_keys.append(str(i))
                total_late += self.days_late_t[i][0].seconds
            for i in self.days_extra_t.keys():
                extra_keys.append(str(i))
                total_extra += self.days_extra_t[i][0].seconds
            if len(late_keys) == 0:
                late_keys.append("no data")
            if len(extra_keys) == 0:
                extra_keys.append("no data")
            self.days_late_selector_t.configure(values=late_keys)
            self.days_extra_selector_t.configure(values=extra_keys)
            self.days_late_selector_t.configure(state="readonly")
            self.days_extra_selector_t.configure(state="readonly")
            self.days_late_selector_t.current(0)
            self.days_extra_selector_t.current(0)
            update_stringvars([
                (self.svar_late_hours_t, f'Total horas tarde: \n{round(total_late / 3600, 2)}'),
                (self.svar_tot_extra_hours_t, f'Total horas extras: \n{round(total_extra / 3600, 2)}')
            ])

    def update_late_extra_days_oct(self):
        faltas_keys = []
        late_keys2 = []
        extra_keys2 = []
        primas_keys = []
        for date, comment in self.days_faltas_op:
            faltas_keys.append(str(date))
        for date, comment in self.days_late_op:
            late_keys2.append(str(date))
        for date, comment, value in self.days_extra_op:
            extra_keys2.append(str(date))
        for date, comment in self.days_prima_op:
            primas_keys.append(str(date))
        if len(faltas_keys) == 0:
            faltas_keys.append("no data")
        if len(late_keys2) == 0:
            late_keys2.append("no data")
        if len(extra_keys2) == 0:
            extra_keys2.append("no data")
        if len(primas_keys) == 0:
            primas_keys.append("no data")
        self.days_missing_selector2.configure(values=faltas_keys)
        self.days_missing_selector2.current(0)
        self.days_late_selector2.configure(values=late_keys2)
        self.days_late_selector2.current(0)
        self.days_extra_selector2.configure(values=extra_keys2)
        self.days_extra_selector2.current(0)
        self.days_primas_selector.configure(values=primas_keys)
        self.days_primas_selector.current(0)

    def change_time_grace(self, event):
        if self.file_selected_1 or self.file_selected_3:
            self.label_time_in_f.configure(text=f'Gracia: {int(self.window_time_in_f.get())} mins')
            self.label_time_out_f.configure(text=f'Gracia: {int(self.window_time_out_f.get())} mins')
        if self.file_selected_3:
            self.label_time_in_t.configure(text=f'Gracia: {int(self.window_time_in_t.get())} mins')
            self.label_time_out_t.configure(text=f'Gracia: {int(self.window_time_out_t.get())} mins')

    def create_inputs_f(self, master, typet=False):
        create_label(master, text='Archivo: ', row=0, column=0)
        create_label(master, text='Nombre: ', row=1, column=0)
        name_emp_selector = create_Combobox(
            master, values=["no name selected"], state="readonly", row=1, column=1)
        if typet:
            file_fichaje_selector = create_Combobox(master, values=self.files_ternium, row=0, column=1)
            name_emp_selector.bind("<<ComboboxSelected>>", self.select_name_emp_t)
        else:
            file_fichaje_selector = create_Combobox(master, values=self.files_fichaje, row=0, column=1)
            name_emp_selector.bind("<<ComboboxSelected>>", self.select_name_emp_f)
        file_fichaje_selector.bind("<<ComboboxSelected>>", self.on_file_selected)
        create_label(master, text='Hora de entrada: ', row=2, column=0, sticky="w")
        clocks = []
        clock1, dict_c = cb.create_spinboxes_time(
            master, self, 3, 0,
            mins_defaul=0, hours_default=8, title="entrada")
        window_time_in = ttk.Scale(
            master, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
            command=self.change_time_grace)
        window_time_in.set(15)
        window_time_in.grid(row=3, column=1)
        label_time_in = create_label(
            master, text=f'Gracia entrada: {int(window_time_in.get())} mins', row=2, column=1)
        create_label(master, text='Hora de salida: ', row=2, column=2, sticky="w")
        clocks.append(dict_c)
        clock2, dict_c = cb.create_spinboxes_time(
            master, self, 3, 2,
            mins_defaul=0, hours_default=18, title="salida")
        window_time_out = ttk.Scale(
            master, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
            command=self.change_time_grace)
        window_time_out.set(15)
        window_time_out.grid(row=3, column=3)
        label_time_out = create_label(
            master, text=f'Gracia salida: {int(window_time_out.get())} mins', row=2, column=3)
        clocks.append(dict_c)
        return (clocks, window_time_in, window_time_out,
                label_time_in, label_time_out, name_emp_selector)

    def create_inputs_o(self, master):
        create_label(master, text='Archivos: ', row=0, column=0, sticky="n", width=10)
        file_oct_selector = create_Combobox(
            master, values=self.files_oct, state="readonly",
            row=0, column=1, width=30, sticky="n")
        file_oct_selector.bind("<<ComboboxSelected>>", self.on_file_selected)
        create_label(master, text='Empleado: ', row=1, column=0, sticky="n", width=10)
        names_oct = create_Combobox(
            master, values=["no name selected"], state="readonly",
            row=1, column=1, width=30, sticky="n")
        names_oct.bind("<<ComboboxSelected>>", self.select_name_oct)
        return names_oct
