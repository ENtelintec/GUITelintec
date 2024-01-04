# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 14/nov./2023  at 17:12 $'

from datetime import timedelta
from tkinter import StringVar
from tkinter.filedialog import asksaveasfilename

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.dialogs.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

import templates.FunctionsFiles as cb
from templates.CollapsingFrame import CollapsingFrame
from templates.FunctionsSQL import get_id_employee
from templates.FunctionsText import compare_employee_name


def create_stringvar(number: int):
    """
    Create a stringvar with the number provided initialized with ""
    :param number: number to create the stringvar
    :return: tuple
    """
    var_string = []
    for i in range(number):
        var_string.append(StringVar(value=""))
    return tuple(var_string)


def create_var_none(number: int):
    """
    Create a tuple with the number provided
    :param number: number of values to create
    :return: tuple
    """
    var_none = []
    for i in range(number):
        var_none.append(None)
    return tuple(var_none)


class FichajesFilesGUI(ScrolledFrame):
    def __init__(self, master=None):
        super().__init__(master, autohide=True)
        # noinspection PyTypeChecker
        self.columnconfigure((0, 1, 2, 3, 4), weight=1)
        # ----------------------variables-------------------------
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.contracts = {}
        (self.df, self.days_late, self.days_extra, self.days_faltas,
         self.data_contract_emp, self.days_late2, self.days_extra2,
         self.total_extra2, self.days_prima, self.files, self.max_date_g,
         self.min_date_g) = create_var_none(12)
        self.files_names_t = []
        self.files_names_o = []
        # -------------------create title-----------------
        self.label_title = ttk.Label(self, text='Telintec Software Fichajes',
                                     font=('Helvetica', 32, 'bold'))
        self.label_title.grid(row=0, column=0, columnspan=5)
        # -------------------create entry for file selector-----------------
        label1 = ttk.Label(self, text='Archivos de ternium: ')
        label1.grid(row=1, column=0)
        label2 = ttk.Label(self, text='Archivos de operaciones: ')
        label2.grid(row=1, column=2)
        label3 = ttk.Label(self, text='Rango de fechas: ')
        label3.grid(row=1, column=4)
        # -------------------create combobox for file selector-----------------
        self.files_ternium_cb = ttk.Combobox(self, values=self.files_names_t, state="readonly")
        self.files_ternium_cb.grid(row=1, column=1)
        self.files_operaciones_cb = ttk.Combobox(self, values=self.files_names_o, state="readonly")
        self.files_operaciones_cb.grid(row=1, column=3)
        self.date_ranges = ttk.Combobox(self, values=[""], state="readonly")
        self.date_ranges.grid(row=1, column=5)
        # self.files_ternium_cb.bind("<<ComboboxSelected>>", self.select_file)
        # self.files_operaciones_cb.bind("<<ComboboxSelected>>", self.select_file_2)
        # -------------------create collapsing frame-----------------
        self.frame_collapse = CollapsingFrame(self)
        self.frame_collapse.grid(row=4, column=0, columnspan=6, sticky='nsew')
        # -------------------create tableview for data-----------------
        self.group_2 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_2.columnconfigure(0, weight=1)
        self.table_1 = Tableview(self.group_2)
        self.table_2 = Tableview(self.group_2)
        # ---------------------grupo filtrado por nombre------------------------------
        group_1 = ttk.Frame(self.frame_collapse, padding=5)
        # noinspection PyTypeChecker
        group_1.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        # ---------------filter by name widgets-------------
        label_name = ttk.Label(group_1, text='Empleado: ')
        label_name.grid(row=0, column=0)
        self.names = ttk.Combobox(group_1, values=["no file selected"], state="readonly")
        self.names.grid(row=0, column=1)
        self.names.bind("<<ComboboxSelected>>", self.select_name)
        label_in_time = ttk.Label(group_1, text='Hora de entrada: ')
        label_in_time.grid(row=0, column=2, sticky="w")
        self.clocks = []
        self.clock1 = cb.create_spinboxes_time(group_1, self, 1, 2,
                                               mins_defaul=0, hours_default=8, title="entrada")

        self.window_time_in = ttk.Scale(group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                        command=self.change_time_grace)
        self.window_time_in.set(15)
        self.label_time_in = ttk.Label(group_1,
                                       text=f'Gracia entrada: {int(self.window_time_in.get())} mins')
        self.label_time_in.grid(row=1, column=3)
        label_out_time = ttk.Label(group_1, text='Hora de salida: ')
        label_out_time.grid(row=0, column=4, sticky="w")
        self.clock2 = cb.create_spinboxes_time(group_1, self, 1, 4,
                                               mins_defaul=0, hours_default=18, title="salida")
        self.window_time_out = ttk.Scale(group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                         command=self.change_time_grace)
        self.window_time_out.set(15)
        self.label_time_out = ttk.Label(group_1,
                                        text=f'Gracia salida: {int(self.window_time_out.get())} mins')
        self.label_time_out.grid(row=1, column=5)
        # ----------------string vars-------------
        (self.wd, self.late, self.extra, self.wd_w, self.late_hours,
         self.extra_hours, self.late_hours_day, self.late_hours_day_out,
         self.extra_hours_day, self.extra_hours_day_in, self.puerta_out,
         self.puerta_in, self.faltas, self.late_hours2, self.extra_hours2,
         self.primas, self.comment_f, self.comment_t, self.comment_e,
         self.comment_p) = create_stringvar(20)
        # -------init read files-------
        self.read_files()
        # ------------------------create display data employee----------------
        # -------labels result file 1-------
        label_subtitle = ttk.Label(group_1, text='Información resumida archivo 1',
                                   font=('Helvetica', 10, 'bold'))
        label_subtitle.grid(row=2, column=0)
        label_faltas = ttk.Label(group_1, textvariable=self.wd)
        label_faltas.grid(row=3, column=0)
        label_wd_w = ttk.Label(group_1, textvariable=self.wd_w)
        label_wd_w.grid(row=4, column=0)
        # late hours
        label_late = ttk.Label(group_1, textvariable=self.late)
        label_late.grid(row=5, column=0)
        label_tot_late_hours = ttk.Label(group_1, textvariable=self.late_hours)
        label_tot_late_hours.grid(row=5, column=1)
        self.days_late_selector = ttk.Combobox(group_1, values=["no file selected"], state=ttk.DISABLED)
        self.days_late_selector.grid(row=5, column=2)
        self.days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late)
        label_late_hours_day = ttk.Label(group_1, textvariable=self.late_hours_day)
        label_late_hours_day.grid(row=5, column=3)
        label_puerta_in = ttk.Label(group_1, textvariable=self.puerta_in)
        label_puerta_in.grid(row=5, column=4)
        label_late_hours_day_out = ttk.Label(group_1, textvariable=self.late_hours_day_out)
        label_late_hours_day_out.grid(row=5, column=5)
        # extra hours
        label_extra = ttk.Label(group_1, textvariable=self.extra)
        label_extra.grid(row=6, column=0)
        label_tot_extra_hours = ttk.Label(group_1, textvariable=self.extra_hours)
        label_tot_extra_hours.grid(row=6, column=1)
        self.days_extra_selector = ttk.Combobox(group_1, values=["no file selected"], state=ttk.DISABLED)
        self.days_extra_selector.grid(row=6, column=2)
        self.days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra)
        label_extra_hours_day = ttk.Label(group_1, textvariable=self.extra_hours_day)
        label_extra_hours_day.grid(row=6, column=3)
        label_puerta_out = ttk.Label(group_1, textvariable=self.puerta_out)
        label_puerta_out.grid(row=6, column=4)
        label_extra_hours_day_in = ttk.Label(group_1, textvariable=self.extra_hours_day_in)
        label_extra_hours_day_in.grid(row=6, column=5)
        # -------labels result file 2-------
        label_subtitle2 = ttk.Label(group_1, text='Información resumida archivo 2',
                                    font=('Helvetica', 10, 'bold'))
        label_subtitle2.grid(row=7, column=0)
        label_faltas = ttk.Label(group_1, textvariable=self.faltas)
        label_faltas.grid(row=8, column=0)
        self.days_missing_selector2 = ttk.Combobox(group_1, values=["no file selected"], state="readonly")
        self.days_missing_selector2.grid(row=8, column=1)
        self.days_missing_selector2.bind("<<ComboboxSelected>>", self.select_day_faltas)
        label_late2 = ttk.Label(group_1, textvariable=self.late_hours2)
        label_late2.grid(row=9, column=0)
        self.days_late_selector2 = ttk.Combobox(group_1, values=["no file selected"], state="readonly")
        self.days_late_selector2.grid(row=9, column=1)
        self.days_late_selector2.bind("<<ComboboxSelected>>", self.select_day_late2)
        label_extra2 = ttk.Label(group_1, textvariable=self.extra_hours2)
        label_extra2.grid(row=10, column=0)
        self.days_extra_selector2 = ttk.Combobox(group_1, values=["no file selected"], state="readonly")
        self.days_extra_selector2.grid(row=10, column=1)
        self.days_extra_selector2.bind("<<ComboboxSelected>>", self.select_day_extra2)
        label_primas = ttk.Label(group_1, textvariable=self.primas)
        label_primas.grid(row=11, column=0)
        self.days_primas_selector = ttk.Combobox(group_1, values=["no file selected"], state="readonly")
        self.days_primas_selector.grid(row=11, column=1)
        self.days_primas_selector.bind("<<ComboboxSelected>>", self.select_day_primas)
        # coments label
        label_comments_1 = ttk.Label(group_1, textvariable=self.comment_f,
                                     font=('Helvetica', 8))
        label_comments_1.grid(row=8, column=2, columnspan=4)
        label_comments_2 = ttk.Label(group_1, textvariable=self.comment_t,
                                     font=('Helvetica', 8))
        label_comments_2.grid(row=9, column=2, columnspan=4)
        label_comments_3 = ttk.Label(group_1, textvariable=self.comment_e,
                                     font=('Helvetica', 8))
        label_comments_3.grid(row=10, column=2, columnspan=4)
        label_comments_4 = ttk.Label(group_1, textvariable=self.comment_p,
                                     font=('Helvetica', 8))
        label_comments_4.grid(row=11, column=2, columnspan=4)

        # ------------------------create expor button----------------
        self.btn_export = ttk.Button(group_1, text="Exportar",
                                     command=self.button_export_click)
        self.btn_export.grid(row=12, column=0, sticky="nsew", padx=5, pady=5)
        self.btn_export_2 = ttk.Button(group_1, text="Exportar/empleado",
                                       command=self.button_export_emp_click)
        self.btn_export_2.grid(row=12, column=1, sticky="nsew", padx=5, pady=5)

        self.frame_collapse.add(group_1, title="Filtrado por nombre")
        self.frame_collapse.add(self.group_2, title="Tablas")

    def button_export_emp_click(self):
        table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in table_data:
                data_f[column].append(row[i])
        df = pd.DataFrame.from_dict(data_f)
        if self.names.get() != "no file selected" and self.names.get() != "":
            id_n = get_id_employee(self.names.get())
            df = df[df["ID"] == id_n]
            # select path to save file
            path = asksaveasfilename(defaultextension=".csv",
                                     filetypes=[("CSV", "*.csv")])
            df.to_csv(path, index=False)
            Messagebox.show_info(title="Info", message="archivo exportado")
        else:
            Messagebox.show_error(title="Alert", message="primero seleccione un empleado")

    def button_export_click(self):
        table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
        data_f = {}
        for i, column in enumerate(columns):
            data_f[column] = []
            for row in table_data:
                data_f[column].append(row[i])
        df = pd.DataFrame.from_dict(data_f)
        # select path to save file
        path = asksaveasfilename(defaultextension=".csv",
                                 filetypes=[("CSV", "*.csv")])
        df.to_csv(path, index=False)

    def select_day_faltas(self, event):
        date = self.days_missing_selector2.get()
        for day, comment in self.days_faltas:
            if day == date:
                self.comment_f.set(comment)
                break

    def select_day_late2(self, event):
        date = self.days_late_selector2.get()
        for day, comment in self.days_late2:
            if day == date:
                self.comment_t.set(comment)
                break

    def select_day_extra2(self, event):
        date = self.days_extra_selector2.get()
        for day, comment, value in self.days_extra2:
            if day == date:
                self.comment_e.set(str(value) + " horas. " + comment)
                break

    def select_day_primas(self, event):
        date = self.days_primas_selector.get()
        for day, comment in self.days_prima:
            if day == date:
                self.comment_p.set(comment)
                break

    def update_string_vars(self, wd, late, extra, wd_w, faltas, late2, extra2, primas):
        self.wd.set(wd)
        self.late.set(late)
        self.extra.set(extra)
        self.wd_w.set(wd_w)
        self.faltas.set(faltas)
        self.late_hours2.set(late2)
        self.extra_hours2.set(extra2)
        self.primas.set(primas)

    def update_extra_late_hours(self, late_hours, extra_hours):
        self.late_hours.set(late_hours)
        self.extra_hours.set(extra_hours)

    def change_time_grace(self, event):
        if self.file_selected_1:
            self.label_time_in.configure(text=f'Gracia: {int(self.window_time_in.get())} mins')
            self.label_time_out.configure(text=f'Gracia: {int(self.window_time_out.get())} mins')

    def select_day_late(self, event):
        if self.days_late_selector.get() != "no file selected":
            date = pd.Timestamp(self.days_late_selector.get())
            aux = self.days_late[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.late_hours_day.set(f'Horas tarde: \n{int(hours)} con {int(minutes)} minutos.')
            self.puerta_in.set(f'Puerta de entrada: \n{self.days_late[date][1]}')
            name = self.names.get()
            df_name = self.df[self.df["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            getawey = df_name[(df_name["Fecha/hora"] > limit_hour_down) &
                              (df_name["Fecha/hora"] < limit_hour_up) &
                              (df_name["in_out"] == "FUERA")]
            self.late_hours_day_out.set(
                f'Hora de salida: \n{getawey["Fecha/hora"].to_list()[0]}\nPuerta: {getawey["Puerta"].to_list()[0]}')
        else:
            print("no file selected")

    def select_day_extra(self, event):
        if self.days_extra_selector.get() != "no file selected":
            date = pd.Timestamp(self.days_extra_selector.get())
            aux = self.days_extra[date][0].seconds
            hours, minutes = divmod(aux / 60, 60)
            self.extra_hours_day.set(f'Horas extras: \n{int(hours)} con {int(minutes)} minutos.')
            self.puerta_out.set(f'Puerta de salida: \n{self.days_extra[date][1]}')
            name = self.names.get()
            df_name = self.df[self.df["name"] == name]
            limit_hour_down = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                           hour=0, minute=0, second=0)
            limit_hour_up = pd.Timestamp(year=date.year, month=date.month, day=date.day,
                                         hour=23, minute=59, second=59)
            entrance = df_name[(df_name["Fecha/hora"] > limit_hour_down) &
                               (df_name["Fecha/hora"] < limit_hour_up) &
                               (df_name["in_out"] == "DENTRO")]
            self.extra_hours_day_in.set(
                f'Hora de entrada: \n{entrance["Fecha/hora"].to_list()[0]}\nPuerta: {entrance["Puerta"].to_list()[0]}')
        else:
            print("no file selected")

    def update_late_extra_days(self):
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
        self.days_late_selector.configure(values=late_keys)
        self.days_extra_selector.configure(values=extra_keys)
        self.days_late_selector.configure(state="readonly")
        self.days_extra_selector.configure(state="readonly")

        self.update_extra_late_hours(f'Total horas tarde: \n{round(total_late / 3600, 2)}',
                                     f'Total horas extras: \n{round(total_extra / 3600, 2)}')
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
        self.days_missing_selector2.configure(values=faltas_keys)
        self.days_late_selector2.configure(values=late_keys2)
        self.days_extra_selector2.configure(values=extra_keys2)
        self.days_primas_selector.configure(values=primas_keys)

    def select_name(self, event):
        if self.names.get() != "no file selected":
            (worked_days, worked_intime, count, count2,
             self.days_late, self.days_extra) = self.get_days_worked_late_extra(self.names.get())
            (self.data_contract_emp, self.days_faltas, self.days_late2,
             self.days_extra2, total_extra2, self.days_prima) = self.get_data_from_name_contract(self.names.get())
            self.update_string_vars(f'Numero de dias trabajados: {worked_days}.',
                                    f'Numero de dias tarde: {count}.',
                                    f'Numero de dias con horas extras: {count2}.',
                                    f'Numero de dias dentro de horario: {worked_intime}.',
                                    f'Dias con falta: {len(self.days_faltas)}.',
                                    f'Dias tarde: {len(self.days_late2)}.',
                                    f'Dias con horas extra: {len(self.days_extra2)}.\nTotal de horas extra: {total_extra2}',
                                    f'Dias con prima: {len(self.days_prima)}.')
            self.update_late_extra_days()
        else:
            print("no file selected")

    def read_files(self):
        # check files in the directory
        flag, self.files = cb.check_fichajes_files_in_directory("files/", "OCTreport", "Ternium")
        for k, v in self.files.items():
            if "Ternium" in v["report"]:
                self.files_names_t.append(k)
            elif "OCTreport" in v["report"]:
                self.files_names_o.append(k)
        self.files_ternium_cb.configure(values=self.files_names_t)
        self.files_operaciones_cb.configure(values=self.files_names_o)
        if len(self.files_names_t) > 0:
            self.files_ternium_cb.set(self.files_names_t[0])
        if len(self.files_names_o) > 0:
            self.files_operaciones_cb.set(self.files_names_o[0])
        self.button_file_click(self.files[self.files_names_t[0]]["path"])
        self.button_file_2_click(self.files[self.files_names_o[0]]["path"])
        # check if date are the same
        self.check_dates_ranges()

    def check_dates_ranges(self):
        # max and min dates from dataframe
        df_dates = self.df.copy()
        max_date = df_dates["Fecha/hora"].max()
        min_date = df_dates["Fecha/hora"].min()
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
        print(list_fortnights)
        list_display = []
        for item in list_fortnights:
            list_display.append(f"{item[0].date()} - {item[1].date()}")
        self.date_ranges.configure(values=list_display)
        # self.date_ranges.configure(values=list_fortnights)

    def button_file_2_click(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.contracts = cb.extract_data_file_contracts(filename)
            if len(self.contracts) != 0:
                table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
                self.table_2 = Tableview(self.group_2, bootstyle="primary",
                                         coldata=columns,
                                         rowdata=table_data,
                                         paginated=False,
                                         searchable=True)
                self.table_2.grid(row=1, column=0, sticky='nsew', padx=50, pady=10)
                self.file_selected_2 = True

    def button_file_click(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.df = cb.extract_fichajes_file(filename)
            coldata = []
            for i, col in enumerate(self.df.columns.tolist()):
                coldata.append(
                    {"text": col, "stretch": True}
                )
            self.table_1 = Tableview(self.group_2, bootstyle="primary",
                                     coldata=coldata,
                                     rowdata=self.df.values.tolist(),
                                     paginated=False,
                                     searchable=True)
            self.table_1.grid(row=0, column=0, sticky='nsew', padx=50, pady=10)
            self.names.configure(values=self.df["name"].unique().tolist())
            # enables scales
            self.window_time_in.grid(row=0, column=3)
            self.window_time_out.grid(row=0, column=5)
            self.file_selected_1 = True

    def get_days_worked_late_extra(self, name: str):
        if self.file_selected_1:
            df_name = self.df[self.df["name"] == name]
            df_name_entrada = df_name[df_name["in_out"] == "DENTRO"]
            df_name_salida = df_name[df_name["in_out"] == "FUERA"]
            worked_days = len(df_name["name"].to_list())
            min_in = self.clocks[0]["entrada"][0].get()
            hour_in = self.clocks[0]["entrada"][1].get()
            min_out = self.clocks[1]["salida"][0].get()
            hour_out = self.clocks[1]["salida"][1].get()
            # filter worked days
            df_name.set_index('Fecha/hora', inplace=True)
            worked_intime = len(
                df_name.between_time(start_time=f"{hour_in}:{min_in}:00", end_time=f"{hour_out}:{min_out}:00"))
            # filter late days and extra hours
            # set entrance hour
            aux_hour = int(hour_in) + int(self.window_time_in.get() / 60)
            aux_min = int(min_in) + int(self.window_time_in.get() % 60)
            limit_hour = pd.Timestamp(year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0)
            # count the number of rows where the person is late
            late_name = df_name_entrada[df_name_entrada["Fecha/hora"].dt.time > limit_hour.time()]
            count = len(late_name)
            # calculate the time difference between the entrance hour and the late hour
            time_late = {}
            for i in late_name[["Fecha/hora", "Puerta"]].values:
                time_str = pd.Timestamp(year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=i[0].second)
                diff = time_str - limit_hour
                time_late[i[0]] = (diff, i[1])
            # calculate the number of days when the person worked extra hours
            aux_hour = int(hour_out) + int(self.window_time_out.get() / 60)
            aux_min = int(min_out) + int(self.window_time_out.get() % 60)
            limit_hour2 = pd.Timestamp(year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0)
            extra_name = df_name_salida[df_name_salida["Fecha/hora"].dt.time > limit_hour2.time()]
            count2 = len(extra_name)
            extra_time = {}
            for i in extra_name[["Fecha/hora", "Puerta"]].values:
                time_str = pd.Timestamp(year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=i[0].second)
                diff = time_str - limit_hour2
                extra_time[i[0]] = (diff, i[1])
            return worked_days, worked_intime, count, count2, time_late, extra_time

    def get_data_from_name_contract(self, name: str) -> tuple[dict, list, list, list, float, list] | None:
        if self.file_selected_2:
            id_2 = get_id_employee(name)
            if id_2 is not None:
                for contract in self.contracts.keys():
                    ids = []
                    for emp_name in self.contracts[contract].keys():
                        ids.append((self.contracts[contract][emp_name]["id"], emp_name))
                    emp, id_emp, flag = compare_employee_name(ids, id_2)
                    if flag:
                        faltas = []
                        retardos = []
                        extras = []
                        primas = []
                        for i, state in enumerate(self.contracts[contract][emp]["status"]):
                            if state == "FALTA":
                                faltas.append((self.contracts[contract][emp]["fechas"][i],
                                               self.contracts[contract][emp]["comments"][i]))
                            elif state == "RETARDO":
                                retardos.append((self.contracts[contract][emp]["fechas"][i],
                                                 self.contracts[contract][emp]["comments"][i]))
                        total_extra = 0.0
                        for i, val in enumerate(self.contracts[contract][emp]["extras"]):
                            if val != 0 and i <= 30:
                                extras.append((self.contracts[contract][emp]["fechas"][i],
                                               self.contracts[contract][emp]["comments"][i],
                                               val))
                                total_extra += val
                        for i, txt_prima in enumerate(self.contracts[contract][emp]["primas"]):
                            if "PRIMA" in txt_prima:
                                primas.append((self.contracts[contract][emp]["fechas"][i],
                                               self.contracts[contract][emp]["comments"][i]))
                        return self.contracts[contract][emp], faltas, retardos, extras, total_extra, primas
            else:
                print("user not registered")
                return None
        else:
            print("no file selected")
            return None
