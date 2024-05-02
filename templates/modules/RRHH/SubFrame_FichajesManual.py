# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 25/abr./2024  at 14:57 $'

from datetime import datetime

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap import DateEntry
from ttkbootstrap.tableview import Tableview

from static.extensions import files_fichaje_path, patterns_files_fichaje, cache_file_emp_fichaje
from templates.Functions_AuxFiles import get_events_op_date
from templates.Functions_Files import create_spinboxes_time, get_info_f_file_name, get_info_bitacora, \
    get_info_t_file_name, check_fichajes_files_in_directory, extract_fichajes_file, \
    check_names_employees_in_cache, extract_data_file_contracts, generate_table_from_dict_contracts
from templates.Funtions_Utils import create_var_none, create_Combobox, create_label, create_stringvar, update_stringvars
from templates.modules.Frame_CollapsingFrame import CollapsingFrame
from templates.modules.SubFrame_Plots import FramePlot


class FichajesManual(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        # variables
        flag, self.files = check_fichajes_files_in_directory(files_fichaje_path, patterns_files_fichaje)
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.file_selected_3 = False
        self.svar_date_file = ttk.StringVar()
        self.dfb = None
        self.files_ternium, self.files_oct, self.files_fichaje = self.list_files_type()
        (self.dff, self.days_late_f, self.days_extra_f,
         self.dft, self.days_late_t, self.days_extra_t,
         self.absences_bit, self.data_con_emp_op, self.lates_bit,
         self.extras_bit, self.primes_bit,
         self.max_date_g, self.min_date_g, self.contracts) = create_var_none(14)
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
        # --------------button update files -----------------------------
        self.frame_buttons = ttk.Frame(self, padding=5)
        self.frame_buttons.grid(row=0, column=0, sticky="nswe")
        self.frame_buttons.columnconfigure(0, weight=1)
        self.btn_update_files = ttk.Button(self.frame_buttons, text="Actualizar archivos",
                                           command=self.read_files_from_directory,
                                           width=25)
        self.btn_update_files.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        # --------------------collapsables--------------------------------
        self.frame_collapse = CollapsingFrame(self)
        self.frame_collapse.grid(row=1, column=0, sticky='nsew')
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
        self.name_oct_selector, self.date_selector_bit = self.create_inputs_b(frame_inputs2)
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
        self.plot3_1 = FramePlot(self.group_3)

        self.frame_collapse.add(self.group_1, title="Archivos Fichaje")
        self.frame_collapse.add(self.group_2, title="Bitacora")
        self.frame_collapse.add(self.group_3, title="Archivos Ternium")

    def read_files_from_directory(self):
        flag, self.files = check_fichajes_files_in_directory(files_fichaje_path, patterns_files_fichaje)
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.file_selected_3 = False
        self.files_ternium, self.files_oct, self.files_fichaje = self.list_files_type()

    def on_date_selected_bitacora(self, *args):
        date = self.svar_date_file.get()
        if date == "":
            return
        print("date", date)
        date = datetime.strptime(date, "%Y-%m-%d")
        events_bitacora, columns = get_events_op_date(date, True, False)
        # create dataframe pandas
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in events_bitacora:
                if column == "Nombre":
                    data_f[column].append(row[i].upper())
                else:
                    data_f[column].append(row[i])
        self.dfb = pd.DataFrame.from_dict(data_f)
        names_list = self.dfb["Nombre"].unique().tolist()
        self.name_oct_selector.configure(values=names_list)
        self.file_selected_2 = True
        data_b, columns = get_events_op_date(date, True)
        table_bitacora = Tableview(self.group_2,
                                   coldata=columns,
                                   rowdata=data_b,
                                   paginated=True,
                                   searchable=True,
                                   autofit=True)
        table_bitacora.grid(row=9, column=0, padx=30, pady=10, sticky="n")

    def on_file_selected(self, event):
        filename = event.widget.get()
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
                self.dft = extract_fichajes_file(filename)
                names_list = self.dft["name"].unique().tolist()
                names_and_ids = check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
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
                self.dff = extract_fichajes_file(filename)
                names_list = self.dff["name"].unique().tolist()
                names_and_ids = check_names_employees_in_cache(names_list, cache_file_emp_fichaje)
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
            self.contracts = extract_data_file_contracts(filename)
            if len(self.contracts) != 0:
                table_data, columns = generate_table_from_dict_contracts(self.contracts)
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
            master, values=["no data"], state="readonly", row=8, column=2)
        days_extra_selector = create_Combobox(
            master, values=["no data"], state=ttk.DISABLED, row=9, column=2)
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
            master, textvariable=self.svar_com_missed_days, row=4, column=2, font=('Helvetica', 11),
            columnspan=4)
        create_label(
            master, textvariable=self.svar_com_late_op, row=5, column=2, font=('Helvetica', 11),
            columnspan=4)
        create_label(
            master, textvariable=self.svar_com_extra_op, row=6, column=2, font=('Helvetica', 11),
            columnspan=4)
        create_label(
            master, textvariable=self.svar_com_primas_op, row=7, column=2, font=('Helvetica', 11),
            columnspan=4)
        days_missing_selector2 = create_Combobox(
            master, values=["no data"], state="readonly", row=4, column=1)
        days_missing_selector2.bind("<<ComboboxSelected>>", self.select_day_faltas)
        days_late_selector2 = create_Combobox(
            master, values=["no data"], state="readonly", row=5, column=1)
        days_late_selector2.bind("<<ComboboxSelected>>", self.select_day_late2)
        days_extra_selector2 = create_Combobox(
            master, values=["no data"], state="readonly", row=6, column=1)
        days_extra_selector2.bind("<<ComboboxSelected>>", self.select_day_extra2)
        days_primas_selector = create_Combobox(
            master, values=["no data"], state="readonly", row=7, column=1)
        days_primas_selector.bind("<<ComboboxSelected>>", self.select_day_primas)
        return days_missing_selector2, days_late_selector2, days_extra_selector2, days_primas_selector

    def select_day_faltas(self, event):
        date = event.widget.get()
        # date = self.days_missing_selector.get()
        for day, comment, value in self.absences_bit:
            if day == date:
                self.svar_com_missed_days.set(comment)
                break

    def select_day_late2(self, event):
        date = event.widget.get()
        # date = self.days_late_selector2.get()
        for day, comment, value in self.lates_bit:
            if day == date:
                self.svar_com_late_op.set(str(value) + " horas. " + comment)
                break

    def select_day_extra2(self, event):
        date = event.widget.get()
        # date = self.days_extra_selector2.get()
        for day, comment, value in self.extras_bit:
            if day == date:
                self.svar_com_extra_op.set(str(value) + " horas. " + comment)
                break

    def select_day_primas(self, event):
        date = event.widget.get()
        # date = self.days_primas_selector.get()
        for day, comment, value in self.primes_bit:
            if day == date:
                self.svar_com_primas_op.set(comment)
                break

    def select_day_late_fun_f(self, event):
        if event.widget.get() != "no data":
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
        if event.widget.get() != "no data":
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
        if event.widget.get() != "no data":
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
        if event.widget.get() != "no data":
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
             self.days_late_f, self.days_extra_f) = get_info_f_file_name(
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
             self.days_late_t, self.days_extra_t) = get_info_t_file_name(
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
            self.plot3_1 = FramePlot(self.group_3, data_chart, "bar")
            self.plot3_1.grid(row=5, column=0, padx=10, pady=10, columnspan=6)
        else:
            print("no data selected")

    def on_name_selected_bitacora(self, event):
        df_name = self.dfb[self.dfb["Nombre"] == event.widget.get()]
        id_emp = df_name["ID"].to_list()[0]
        if event.widget.get() != "no name selected":
            (days_absence_bit, days_extra_bit, days_primes_bit, days_lates_bit,
             self.absences_bit, self.extras_bit, self.primes_bit, self.lates_bit, normals_bit,
             contract) = get_info_bitacora(
                self.dfb, name=event.widget.get(), id_emp=id_emp, flag=self.file_selected_2)
            update_stringvars(
                [(self.svar_missed_days, f'Dias con falta: {days_absence_bit[0]}.'),
                 (self.svar_late_op, f'Dias tarde: {days_lates_bit[0]}.\nTotal de horas tarde: {days_lates_bit[1]}'),
                 (self.svar_extra_hours_op,
                  f'Dias con horas extra: {days_extra_bit[0]}.\nTotal de horas extra: {days_extra_bit[1]}'),
                 (self.svar_primas_op, f'Dias con prima: {days_primes_bit[0]}.'),
                 (self.svar_com_missed_days, ""),
                 (self.svar_com_late_op, ""),
                 (self.svar_com_extra_op, ""),
                 (self.svar_com_primas_op, "")])
            self.update_late_extra_days_bitacora()
            data_chart = {"data": {'Tarde': days_lates_bit[0], 'Extras': days_extra_bit[0],
                                   'Faltas': days_absence_bit[0], 'Primas': days_primes_bit[0]},
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

    def update_late_extra_days_bitacora(self):
        faltas_keys = []
        late_keys2 = []
        extra_keys2 = []
        primas_keys = []
        for date, comment, value in self.absences_bit:
            faltas_keys.append(str(date))
        for date, comment, value in self.lates_bit:
            late_keys2.append(str(date))
        for date, comment, value in self.extras_bit:
            extra_keys2.append(str(date))
        for date, comment, value in self.primes_bit:
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
        clock1, dict_c = create_spinboxes_time(
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
        clock2, dict_c = create_spinboxes_time(
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

    def create_inputs_b(self, master):
        create_label(master, text='Fecha: ', row=0, column=0, sticky="n", width=10)
        self.svar_date_file.set(datetime.now().strftime("%Y-%m-%d"))
        date_selector = DateEntry(master, dateformat="%Y-%m-%d", firstweekday=0)
        date_selector.entry.configure(textvariable=self.svar_date_file)
        date_selector.grid(row=0, column=1, sticky="n")
        self.svar_date_file.trace("w", self.on_date_selected_bitacora)
        create_label(master, text='Empleado: ', row=1, column=0, sticky="n", width=10)
        names_oct = create_Combobox(
            master, values=["no name selected"], state="readonly",
            row=1, column=1, width=30, sticky="n")
        names_oct.bind("<<ComboboxSelected>>", self.on_name_selected_bitacora)
        return names_oct, date_selector
