# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 14/nov./2023  at 17:12 $'

from tkinter import StringVar
from tkinter.filedialog import askopenfilename

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.scrolled import ScrolledFrame

import templates.FunctionsFiles as cb
from templates.CollapsingFrame import CollapsingFrame
from templates.FunctionsText import compare_employee_name


class FichajesFilesGUI(ScrolledFrame):
    def __init__(self, master=None):
        super().__init__(master, autohide=True)
        # noinspection PyTypeChecker
        self.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.df = None
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.days_late = None
        self.days_extra = None
        self.contracts = {}
        # -------------------create title-----------------
        self.label_title = ttk.Label(self, text='Telintec Software Fichajes',
                                     font=('Helvetica', 32, 'bold'))
        self.label_title.grid(row=0, column=0, columnspan=5)
        # -------------------create entry for file selector-----------------
        self.label_file = ttk.Label(self, text='File: ')
        self.label_file.grid(row=1, column=0)
        self.file_entry = ttk.Button(self, text='Seleccione un archivo', command=self.button_file_click)
        self.file_entry.grid(row=1, column=1)
        self.label_filename = ttk.Label(self, text='')
        self.label_filename.grid(row=1, column=2)
        # other file selector
        self.label_other_file = ttk.Label(self, text='Seleccione el otro archivo: ')
        self.label_other_file.grid(row=1, column=2)
        self.file_entry_2 = ttk.Button(self, text='Seleccione un archivo', command=self.button_file_2_click)
        self.file_entry_2.grid(row=1, column=3)
        self.label_filename_2 = ttk.Label(self, text='')
        self.label_filename_2.grid(row=1, column=4)

        # -------------------create collapsing frame-----------------
        self.frame_collapse = CollapsingFrame(self)
        self.frame_collapse.grid(row=4, column=0, columnspan=5, sticky='nsew')
        # -------------------create tableview for data-----------------
        self.group_2 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_2.columnconfigure(0, weight=1)
        self.table_1 = Tableview(self.group_2)
        self.table_2 = Tableview(self.group_2)
        self.frame_collapse.add(self.group_2, title="Tablas")
        # ----grupo filtrado por nombre
        group_1 = ttk.Frame(self.frame_collapse, padding=5)
        # noinspection PyTypeChecker
        group_1.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        # filter by name
        label_name = ttk.Label(group_1, text='Empleado: ')
        label_name.grid(row=0, column=0)
        self.names = ttk.Combobox(group_1, values=["no file selected"])
        self.names.grid(row=0, column=1)
        self.names.bind("<<ComboboxSelected>>", self.select_name)
        label_in_time = ttk.Label(group_1, text='Hora de entrada: ')
        label_in_time.grid(row=0, column=2, sticky="w")
        self.clocks = []
        self.clock1 = cb.create_spinboxes_time(group_1, self, 1, 2,
                                               mins_defaul=0, hours_default=8, title="entrada")

        self.window_time_in = ttk.Scale(group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=200,
                                        command=self.change_time_grace)
        self.window_time_in.set(15)
        self.label_time_in = ttk.Label(group_1,
                                       text=f'Tiempo de gracia entrada: {int(self.window_time_in.get())} minutos')
        self.label_time_in.grid(row=1, column=3)
        label_out_time = ttk.Label(group_1, text='Hora de salida: ')
        label_out_time.grid(row=0, column=4, sticky="w")
        self.clock2 = cb.create_spinboxes_time(group_1, self, 1, 4,
                                               mins_defaul=0, hours_default=18, title="salida")
        self.window_time_out = ttk.Scale(group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=200,
                                         command=self.change_time_grace)
        self.window_time_out.set(15)
        self.label_time_out = ttk.Label(group_1,
                                        text=f'Tiempo de gracia salida: {int(self.window_time_out.get())} minutos')
        self.label_time_out.grid(row=1, column=5)
        # create display data employee
        label_subtitle = ttk.Label(group_1, text='Información resumida')
        label_subtitle.grid(row=2, column=0)
        self.wd = StringVar()
        self.late = StringVar()
        self.extra = StringVar()
        self.wd_w = StringVar()
        self.late_hours = StringVar()
        self.extra_hours = StringVar()
        self.late_hours_day = StringVar()
        self.late_hours_day_out = StringVar()
        self.extra_hours_day = StringVar()
        self.extra_hours_day_in = StringVar()
        self.puerta_out = StringVar()
        self.puerta_in = StringVar()
        self.init_string_vars()
        # labels result
        label_wd = ttk.Label(group_1, textvariable=self.wd)
        label_wd.grid(row=3, column=0)
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
        self.frame_collapse.add(group_1, title="Filtrado por nombre")

    def init_string_vars(self):
        self.wd.set("")
        self.late.set("")
        self.extra.set("")
        self.wd_w.set("")
        self.late_hours.set("")
        self.extra_hours.set("")
        self.late_hours_day.set("")
        self.extra_hours_day.set("")
        self.puerta_in.set("")
        self.puerta_out.set("")
        self.late_hours_day_out.set("")
        self.extra_hours_day_in.set("")

    def update_string_vars(self, wd, late, extra, wd_w):
        self.wd.set(wd)
        self.late.set(late)
        self.extra.set(extra)
        self.wd_w.set(wd_w)

    def update_extra_late_hours(self, late_hours, extra_hours):
        self.late_hours.set(late_hours)
        self.extra_hours.set(extra_hours)

    def change_time_grace(self, event):
        if self.file_selected_1:
            self.label_time_in.configure(text=f'Tiempo de gracia: {int(self.window_time_in.get())} minutos')
            self.label_time_out.configure(text=f'Tiempo de gracia: {int(self.window_time_out.get())} minutos')

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
        self.days_late_selector.configure(state=ttk.NORMAL)
        self.days_extra_selector.configure(state=ttk.NORMAL)
        self.update_extra_late_hours(f'Total horas tarde: \n{round(total_late / 3600, 2)}',
                                     f'Total horas extras: \n{round(total_extra / 3600, 2)}')

    def select_name(self, event):
        if self.names.get() != "no file selected":

            (worked_days, worked_intime, count, count2,
             self.days_late, self.days_extra) = self.get_days_worked_late_extra(self.names.get())
            data = self.get_data_from_name_contract(self.names.get())
            self.update_string_vars(f'Numero de dias trabajados: {worked_days}.',
                                    f'Numero de dias tarde: {count}.',
                                    f'Numero de dias con horas extras: {count2}.',
                                    f'Numero de dias dentro de horario: {worked_intime}.')
            self.update_late_extra_days()
        else:
            print("no file selected")

    def button_file_2_click(self):
        try:
            filename = askopenfilename(filetypes=[('Excel Files', '*.xlsx'), ('Excel Files', '*.xls')])
            print("Archivo: ", filename)
        except Exception as e:
            filename = e
        self.label_filename_2.configure(text=filename)
        self.file_entry_2.configure(text='File Selected')
        if ".xls" in filename or ".xlsx" in filename:
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

    def button_file_click(self):
        try:
            filename = askopenfilename(filetypes=[('Excel Files', '*.xlsx'), ('Excel Files', '*.xls')])
            print("Archivo: ", filename)
        except Exception as e:
            filename = e
        self.label_filename.configure(text=filename)
        self.file_entry.configure(text='File Selected')
        if ".xls" in filename or ".xlsx" in filename:
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

    def get_data_from_name_contract(self, name):
        if self.file_selected_2:
            for contract in self.contracts.keys():
                emp, flag = compare_employee_name(list(self.contracts[contract].keys()), name)
                if flag:
                    print(self.contracts[contract][emp]["extras"])
                    print(self.contracts[contract][emp]["primas"])
                    print(self.contracts[contract][emp]["fechas"])
                    print(self.contracts[contract][emp]["status"])
                    print(self.contracts[contract][emp]["comments"])
                    print(self.contracts[contract][emp]["in_door"])
                    print(self.contracts[contract][emp]["out_door"])
                    return self.contracts[contract][emp]
        else:
            print("no file selected")
            return None
