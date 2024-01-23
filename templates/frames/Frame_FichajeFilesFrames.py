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

import templates.Functions_Files as cb
from templates.frames.Frame_CollapsingFrame import CollapsingFrame
from templates.Functions_SQL import get_id_employee
from templates.Functions_Text import compare_employee_name


def update_stringvars(stringvar_list: list[tuple[StringVar, str]]):
    """
    Update the stringvar list with the new value
    :param stringvar_list: list of stringvars
    :return: None
    """
    for stringvar, value in stringvar_list:
        stringvar.set(value)


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


def create_Combobox(master, values, width=None, row=0, column=0,
                    state="readonly", padx=5, pady=5):
    """
    Create a combobox with the values provided
    :param master: parent of the combobox
    :param values: values of the combobox
    :param row: row to place the widget
    :param column: Column to place the widget
    :param state: state of the combobox
    :param padx:
    :param pady:
    :param width:
    :return: Placed combobox in the grid
    """
    combobox = ttk.Combobox(master, values=values, state=state)
    if len(values) > 0:
        combobox.current(0)
    combobox.grid(row=row, column=column, padx=padx, pady=pady)
    return combobox


def create_label(master, row, column, padx=5, pady=5, text=None, textvariable=None,
                 font=('Helvetica', 10, 'bold'), columnspan=1, sticky=None):
    """
    Create a label with the text-provided
    :param sticky:
    :param columnspan:
    :param text: If None, a label with textvariable is created
    :param font:
    :param master: Parent of the label
    :param textvariable: textvariable of the label
    :param row: row to place the widget
    :param column: Column to place the widget
    :param padx:
    :param pady:
    :return: Placed label in the grid
    """
    if text is not None:
        label = ttk.Label(master, text=text, font=font)
    else:
        label = ttk.Label(master, textvariable=textvariable, font=font)
    if sticky is None:
        label.grid(row=row, column=column, padx=padx, pady=pady, columnspan=columnspan)
    else:
        label.grid(row=row, column=column, padx=padx, pady=pady, columnspan=columnspan, sticky=sticky)
    return label


def get_days_worked_late_extra(df, name: str, clocks, window_time_in, window_time_out, flag):
    if flag:
        df_name = df[df["name"] == name]
        df_name_entrada = df_name[df_name["in_out"] == "DENTRO"]
        df_name_salida = df_name[df_name["in_out"] == "FUERA"]
        worked_days = len(df_name["name"].to_list())
        min_in = clocks[0]["entrada"][0].get()
        hour_in = clocks[0]["entrada"][1].get()
        min_out = clocks[1]["salida"][0].get()
        hour_out = clocks[1]["salida"][1].get()
        # filter worked days
        df_name.set_index('Fecha/hora', inplace=True)
        worked_intime = len(
            df_name.between_time(start_time=f"{hour_in}:{min_in}:00", end_time=f"{hour_out}:{min_out}:00"))
        # filter late days and extra hours
        # set entrance hour
        aux_hour = int(hour_in) + int(window_time_in.get() / 60)
        aux_min = int(min_in) + int(window_time_in.get() % 60)
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
        aux_hour = int(hour_out) + int(window_time_out.get() / 60)
        aux_min = int(min_out) + int(window_time_out.get() % 60)
        limit_hour2 = pd.Timestamp(year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0)
        extra_name = df_name_salida[df_name_salida["Fecha/hora"].dt.time > limit_hour2.time()]
        count2 = len(extra_name)
        extra_time = {}
        for i in extra_name[["Fecha/hora", "Puerta"]].values:
            time_str = pd.Timestamp(year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=i[0].second)
            diff = time_str - limit_hour2
            extra_time[i[0]] = (diff, i[1])
        return worked_days, worked_intime, count, count2, time_late, extra_time


def get_data_from_name_contract(contracts, name: str, id_2=None, flag=False) -> tuple[dict, list, list, list, float, list]|tuple[None, None, None, None, None, None]:
    if flag:
        id_2 = get_id_employee(name) if id_2 is None else id_2
        if id_2 is not None:
            for contract in contracts.keys():
                ids = []
                for emp_name in contracts[contract].keys():
                    ids.append((contracts[contract][emp_name]["id"], emp_name))
                emp, id_emp, flag = compare_employee_name(ids, id_2)
                if flag:
                    faltas = []
                    retardos = []
                    extras = []
                    primas = []
                    for i, state in enumerate(contracts[contract][emp]["status"]):
                        if state == "FALTA":
                            faltas.append((contracts[contract][emp]["fechas"][i],
                                           contracts[contract][emp]["comments"][i]))
                        elif state == "RETARDO":
                            retardos.append((contracts[contract][emp]["fechas"][i],
                                             contracts[contract][emp]["comments"][i]))
                    total_extra = 0.0
                    for i, val in enumerate(contracts[contract][emp]["extras"]):
                        if val != 0 and i <= 30:
                            extras.append((contracts[contract][emp]["fechas"][i],
                                           contracts[contract][emp]["comments"][i],
                                           val))
                            total_extra += val
                    for i, txt_prima in enumerate(contracts[contract][emp]["primas"]):
                        if "PRIMA" in txt_prima:
                            primas.append((contracts[contract][emp]["fechas"][i],
                                           contracts[contract][emp]["comments"][i]))
                    return contracts[contract][emp], faltas, retardos, extras, total_extra, primas
        else:
            print("user not registered")
            return None, None, None, None, None, None
    else:
        print("no file selected")
        return None, None, None, None, None, None


class FichajesFilesGUI(ScrolledFrame):
    def __init__(self, master=None):
        super().__init__(master, autohide=True)
        # noinspection PyTypeChecker
        self.columnconfigure(0, weight=1)
        # ----------------------variables-------------------------
        nb = ttk.Notebook(self)
        # frame_1 = FichajesAuto(nb)
        frame_2 = FichajesManual(nb)
        # nb.add(frame_1, text='Automatico')
        nb.add(frame_2, text='Manual')
        nb.grid(row=0, column=0, sticky="nsew", padx=15, pady=5)


class FichajesAuto(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # noinspection PyTypeChecker
        self.columnconfigure((0, 1, 2, 3, 4), weight=1)
        # ----------------------variables-------------------------
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.master = master
        self.contracts = {}
        (self.df, self.days_late, self.days_extra, self.days_faltas,
         self.data_contract_emp, self.days_late2, self.days_extra2,
         self.total_extra2, self.days_prima, self.files, self.max_date_g,
         self.min_date_g) = create_var_none(12)
        self.files_names_t = []
        self.files_names_o = []
        # -------------------create title-----------------
        label_title = create_label(self, text='Telintec Software Fichajes',
                                   row=0, column=0, columnspan=5, padx=0, pady=0,
                                   font=('Helvetica', 32, 'bold'))
        # -------------------create entry for file selector-----------------
        label1 = create_label(self, text='Archivos de ternium: ', row=1, column=0)
        label2 = create_label(self, text='Archivos de operaciones: ', row=1, column=2)
        label3 = create_label(self, text='Rango de fechas: ', row=1, column=4)
        # -------------------create combobox for file selector-----------------
        self.files_ternium_cb = create_Combobox(
            self, values=self.files_names_t, state="readonly", row=1, column=1, padx=0, pady=0)
        self.files_operaciones_cb = create_Combobox(
            self, values=self.files_names_o, state="readonly", row=1, column=3, padx=0, pady=0)
        self.date_ranges = create_Combobox(
            self, values=[""], state="readonly", row=1, column=5, padx=0, pady=0)
        self.files_ternium_cb.bind("<<ComboboxSelected>>", self.name_select_file)
        self.files_operaciones_cb.bind("<<ComboboxSelected>>", self.name_select_file)
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
        label_name = create_label(group_1, text='Empleado: ', row=0, column=0)
        self.names = create_Combobox(group_1, values=["no file selected"], state="readonly", row=0, column=1)
        self.names.bind("<<ComboboxSelected>>", self.select_name)
        label_in_time = create_label(group_1, text='Hora de entrada: ', row=0, column=2, sticky="w")
        self.clocks = []
        self.clock1 = cb.create_spinboxes_time(group_1, self, 1, 2,
                                               mins_defaul=0, hours_default=8, title="entrada")
        self.window_time_in = ttk.Scale(group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                        command=self.change_time_grace)
        self.window_time_in.set(15)
        self.label_time_in = create_label(
            group_1, text=f'Gracia entrada: {int(self.window_time_in.get())} mins', row=1, column=3)
        label_out_time = create_label(group_1, text='Hora de salida: ', row=0, column=4, sticky="w")
        self.clock2 = cb.create_spinboxes_time(group_1, self, 1, 4,
                                               mins_defaul=0, hours_default=18, title="salida")
        self.window_time_out = ttk.Scale(group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                         command=self.change_time_grace)
        self.window_time_out.set(15)
        self.label_time_out = create_label(
            group_1, text=f'Gracia salida: {int(self.window_time_out.get())} mins', row=1, column=5)
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
        self.create_info_display_file1(group_1)
        self.days_late_selector = create_Combobox(
            group_1, values=["no file selected"], state="readonly", row=5, column=2)
        self.days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late)
        self.days_extra_selector = create_Combobox(
            group_1, values=["no file selected"], state=ttk.DISABLED, row=6, column=2)
        self.days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra)
        # -------labels result file 2-------
        self.create_info_display_file2(group_1)
        self.days_missing_selector2 = create_Combobox(
            group_1, values=["no file selected"], state="readonly", row=8, column=1)
        self.days_missing_selector2.bind("<<ComboboxSelected>>", self.select_day_faltas)
        self.days_late_selector2 = create_Combobox(
            group_1, values=["no file selected"], state="readonly", row=9, column=1)
        self.days_late_selector2.bind("<<ComboboxSelected>>", self.select_day_late2)
        self.days_extra_selector2 = create_Combobox(
            group_1, values=["no file selected"], state="readonly", row=10, column=1)
        self.days_extra_selector2.bind("<<ComboboxSelected>>", self.select_day_extra2)
        self.days_primas_selector = create_Combobox(
            group_1, values=["no file selected"], state="readonly", row=11, column=1)
        self.days_primas_selector.bind("<<ComboboxSelected>>", self.select_day_primas)
        # ------------------------create expor button----------------
        self.btn_export = ttk.Button(group_1, text="Exportar",
                                     command=self.button_export_click)
        self.btn_export.grid(row=12, column=0, sticky="nsew", padx=5, pady=5)
        self.btn_export_2 = ttk.Button(group_1, text="Exportar/empleado",
                                       command=self.button_export_emp_click)
        self.btn_export_2.grid(row=12, column=1, sticky="nsew", padx=5, pady=5)

        self.frame_collapse.add(group_1, title="Filtrado por nombre")
        self.frame_collapse.add(self.group_2, title="Tablas")

    def create_info_display_file1(self, master):
        label_subtitle = create_label(
            master, text='Información resumida archivo 1', row=2, column=0)
        label_faltas = create_label(master, textvariable=self.wd, row=3, column=0)
        label_wd_w = create_label(master, textvariable=self.wd_w, row=4, column=0)
        # late hours
        label_late = create_label(master, textvariable=self.late, row=5, column=0)
        label_tot_late_hours = create_label(master, textvariable=self.late_hours, row=5, column=1)
        label_late_hours_day = create_label(master, textvariable=self.late_hours_day, row=5, column=3)
        label_puerta_in = create_label(master, textvariable=self.puerta_in, row=5, column=4)
        label_late_hours_day_out = create_label(master, textvariable=self.late_hours_day_out, row=5, column=5)
        # extra hours
        label_extra = create_label(master, textvariable=self.extra, row=6, column=0)
        label_tot_extra_hours = create_label(master, textvariable=self.extra_hours, row=6, column=1)
        label_extra_hours_day = create_label(master, textvariable=self.extra_hours_day, row=6, column=3)
        label_puerta_out = create_label(master, textvariable=self.puerta_out, row=6, column=4)
        label_extra_hours_day_in = create_label(master, textvariable=self.extra_hours_day_in, row=6, column=5)

    def create_info_display_file2(self, master):
        label_subtitle2 = create_label(
            master, text='Información resumida archivo 2', row=7, column=0)
        label_faltas = create_label(master, textvariable=self.faltas, row=8, column=0)
        label_late2 = create_label(master, textvariable=self.late2, row=9, column=0)
        label_extra2 = create_label(master, textvariable=self.extra_hours2, row=10, column=0)
        label_primas = create_label(master, textvariable=self.primas, row=11, column=0)
        # coments label
        label_comments_1 = create_label(
            master, textvariable=self.comment_f, row=8, column=2, font=('Helvetica', 8),
            columnspan=4)
        label_comments_2 = create_label(
            master, textvariable=self.comment_t, row=9, column=2, font=('Helvetica', 8),
            columnspan=4)
        label_comments_3 = create_label(
            master, textvariable=self.comment_e, row=10, column=2, font=('Helvetica', 8),
            columnspan=4)
        label_comments_4 = create_label(
            master, textvariable=self.comment_p, row=11, column=2, font=('Helvetica', 8),
            columnspan=4)

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
            # select a path to save file
            path = asksaveasfilename(defaultextension=".csv",
                                     filetypes=[("CSV", "*.csv")])
            df.to_csv(path, index=False)
            Messagebox.show_info(title="Info", message=f"Archivo exportado:\n{path}")
        else:
            Messagebox.show_error(title="Alert", message="primero seleccione un empleado")

    def button_export_click(self):
        data_resume = []
        for con_name in self.contracts.keys():
            for emp_name in self.contracts[con_name].keys():
                if self.contracts[con_name][emp_name]["id"] is None:
                    continue
                (data_contract_emp, days_faltas, days_late2,
                 days_extra2, total_extra2, days_prima) = get_data_from_name_contract(
                    contracts=self.contracts, name=emp_name,
                    id_2=self.contracts[con_name][emp_name]["id"], flag=self.file_selected_2)
                dict_faltas, dict_late2, dict_extra2, dict_prima = cb.get_dic_from_list_fichajes(
                    [days_faltas, days_late2, days_extra2, days_prima])
                row = (self.contracts[con_name][emp_name]["id"],
                       emp_name, con_name, len(days_faltas), len(days_late2), len(days_extra2), total_extra2,
                       len(days_prima),
                       dict_faltas, dict_late2, dict_extra2, dict_prima)
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
        cb.update_fichajes_resume_cache('files/fichajes_resume_cache.pkl', data_resume)
        Messagebox.show_info(title="Info", message=f"Archivo exportado:\n{path}")

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
        if len(late_keys) == 0:
            late_keys.append("no data")
        if len(extra_keys) == 0:
            extra_keys.append("no data")
        self.days_late_selector.configure(values=late_keys)
        self.days_extra_selector.configure(values=extra_keys)
        self.days_late_selector.configure(state="readonly")
        self.days_extra_selector.configure(state="readonly")
        self.days_late_selector.current(0)
        self.days_extra_selector.current(0)
        update_stringvars([
            (self.late_hours, f'Total horas tarde: \n{round(total_late / 3600, 2)}'),
            (self.extra_hours, f'Total horas extras: \n{round(total_extra / 3600, 2)}')
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
            faltas_keys.append("no file selected")
        if len(late_keys2) == 0:
            late_keys2.append("no file selected")
        if len(extra_keys2) == 0:
            extra_keys2.append("no file selected")
        if len(primas_keys) == 0:
            primas_keys.append("no file selected")
        self.days_missing_selector2.configure(values=faltas_keys)
        self.days_missing_selector2.current(0)
        self.days_late_selector2.configure(values=late_keys2)
        self.days_late_selector2.current(0)
        self.days_extra_selector2.configure(values=extra_keys2)
        self.days_extra_selector2.current(0)
        self.days_primas_selector.configure(values=primas_keys)
        self.days_primas_selector.current(0)

    def select_name(self, event):
        if self.names.get() != "no file selected":
            (worked_days, worked_intime, count, count2,
             self.days_late, self.days_extra) = get_days_worked_late_extra(
                self.df, self.names.get(), self.clocks, self.window_time_in, self.window_time_out,
                self.file_selected_1)
            (self.data_contract_emp, self.days_faltas, self.days_late2,
             self.days_extra2, total_extra2, self.days_prima) = get_data_from_name_contract(
                contracts=self.contracts, name=self.names.get(), flag=self.file_selected_2)
            update_stringvars(
                [(self.wd, f'Numero de dias trabajados: {worked_days}.'),
                 (self.late, f'Numero de dias tarde: {count}.'),
                 (self.extra, f'Numero de dias con horas extras: {count2}.'),
                 (self.wd_w, f'Numero de dias dentro de horario: {worked_intime}.'),
                 (self.faltas, f'Dias con falta: {len(self.days_faltas)}.'),
                 (self.late_hours2, f'Dias tarde: {len(self.days_late2)}.'),
                 (self.extra_hours2,
                  f'Dias con horas extra: {len(self.days_extra2)}.\nTotal de horas extra: {total_extra2}'),
                 (self.primas, f'Dias con prima: {len(self.days_prima)}.')])
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
        # check if the date is the same
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
                                         searchable=True,
                                         autofit=True)
                self.table_2.grid(row=1, column=0, sticky='nsew', padx=50, pady=10)
                self.file_selected_2 = True

    def name_select_file(self, event):
        filename = event.widget.get()
        if "Ternium" in filename:
            print(self.files[filename]["pairs"])
            self.button_file_click(self.files[filename]["path"])
        else:
            self.button_file_2_click(self.files[filename]["path"])
        self.check_dates_ranges()

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
                                     searchable=True,
                                     autofit=True)
            self.table_1.grid(row=0, column=0, sticky='nsew', padx=50, pady=10)
            self.names.configure(values=self.df["name"].unique().tolist())
            # enables scales
            self.window_time_in.grid(row=0, column=3)
            self.window_time_out.grid(row=0, column=5)
            self.file_selected_1 = True


class FichajesManual(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        # variables
        flag, self.files = cb.check_fichajes_files_in_directory("files/", "OCTreport", "Ternium")
        print(flag, self.files)
        self.file_selected_1 = False
        self.file_selected_2 = False
        self.contracts = None
        files_ternium, files_oct = self.list_files_type()
        (self.df, self.days_late, self.days_extra, self.days_faltas,
         self.data_contract_emp, self.days_late2, self.days_extra2,
         self.total_extra2, self.days_prima, self.max_date_g,
         self.min_date_g) = create_var_none(11)
        (self.wd, self.late, self.extra, self.wd_w, self.late_hours,
         self.extra_hours, self.late_hours_day, self.late_hours_day_out,
         self.extra_hours_day, self.extra_hours_day_in, self.puerta_out,
         self.puerta_in, self.faltas, self.late_hours2, self.extra_hours2,
         self.primas, self.comment_f, self.comment_t, self.comment_e,
         self.comment_p) = create_stringvar(20)
        # widgets
        self.frame_collapse = CollapsingFrame(self)
        self.frame_collapse.grid(row=0, column=0, sticky='nsew')
        self.frame_collapse.columnconfigure(0, weight=1)

        # group 1 frame
        self.group_1 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_1.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        create_label(self.group_1, text='Archivos de ternium: ', row=0, column=0)
        self.file_ternium_selector = create_Combobox(self.group_1, values=files_ternium, row=0, column=1)
        self.file_ternium_selector.bind("<<ComboboxSelected>>", self.on_file_selected)
        create_label(self.group_1, text='Resumen por empleado', row=1, column=0)
        label_name = create_label(self.group_1, text='Empleado: ', row=2, column=0)
        self.names = create_Combobox(self.group_1, values=["no file selected"], state="readonly", row=2, column=1)
        self.names.bind("<<ComboboxSelected>>", self.select_name)
        label_in_time = create_label(self.group_1, text='Hora de entrada: ', row=2, column=2, sticky="w")
        self.clocks = []
        self.clock1 = cb.create_spinboxes_time(self.group_1, self, 3, 2,
                                               mins_defaul=0, hours_default=8, title="entrada")
        self.window_time_in = ttk.Scale(self.group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                        command=self.change_time_grace)
        self.window_time_in.set(15)
        self.window_time_in.grid(row=3, column=3)
        self.label_time_in = create_label(
            self.group_1, text=f'Gracia entrada: {int(self.window_time_in.get())} mins', row=2, column=3)
        label_out_time = create_label(self.group_1, text='Hora de salida: ', row=2, column=4, sticky="w")
        self.clock2 = cb.create_spinboxes_time(self.group_1, self, 3, 4,
                                               mins_defaul=0, hours_default=18, title="salida")
        self.window_time_out = ttk.Scale(self.group_1, from_=0, to=60, orient=ttk.HORIZONTAL, length=100,
                                         command=self.change_time_grace)
        self.window_time_out.set(15)
        self.window_time_out.grid(row=3, column=5)
        self.label_time_out = create_label(
            self.group_1, text=f'Gracia salida: {int(self.window_time_out.get())} mins', row=2, column=5)
        # resume info
        self.create_info_display_file1(self.group_1)
        self.days_late_selector = create_Combobox(
            self.group_1, values=["no file selected"], state="readonly", row=8, column=2)
        self.days_late_selector.bind("<<ComboboxSelected>>", self.select_day_late)
        self.days_extra_selector = create_Combobox(
            self.group_1, values=["no file selected"], state=ttk.DISABLED, row=9, column=2)
        self.days_extra_selector.bind("<<ComboboxSelected>>", self.select_day_extra)
        self.table_1 = Tableview(self.group_1)
        # group 2 frame
        self.group_2 = ttk.Frame(self.frame_collapse, padding=5)
        self.group_2.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        create_label(self.group_2, text='Archivos de OCT: ', row=0, column=0)
        self.file_oct_selector = create_Combobox(self.group_2, values=files_oct, row=0, column=1)
        self.file_oct_selector.bind("<<ComboboxSelected>>", self.on_file_selected)
        create_label(self.group_2, text='Resumen por empleado', row=1, column=0)
        label_name = create_label(self.group_2, text='Empleado: ', row=2, column=0)
        self.names_oct = create_Combobox(self.group_2, values=["no file selected"], state="readonly", row=2, column=1)
        self.names_oct.bind("<<ComboboxSelected>>", self.select_name_oct)
        # -------labels result file 2-------
        self.create_info_display_file2(self.group_2)
        self.days_missing_selector2 = create_Combobox(
            self.group_2, values=["no file selected"], state="readonly", row=4, column=1)
        self.days_missing_selector2.bind("<<ComboboxSelected>>", self.select_day_faltas)
        self.days_late_selector2 = create_Combobox(
            self.group_2, values=["no file selected"], state="readonly", row=5, column=1)
        self.days_late_selector2.bind("<<ComboboxSelected>>", self.select_day_late2)
        self.days_extra_selector2 = create_Combobox(
            self.group_2, values=["no file selected"], state="readonly", row=6, column=1)
        self.days_extra_selector2.bind("<<ComboboxSelected>>", self.select_day_extra2)
        self.days_primas_selector = create_Combobox(
            self.group_2, values=["no file selected"], state="readonly", row=7, column=1)
        self.days_primas_selector.bind("<<ComboboxSelected>>", self.select_day_primas)
        self.table_2 = Tableview(self.group_2)
        self.frame_collapse.add(self.group_1, title="Archivos Ternium")
        self.frame_collapse.add(self.group_2, title="Archivos OCT")

    def on_file_selected(self, event):
        filename = event.widget.get()
        if "Ternium" in filename:
            print(self.files)
            self.data_files_ternium(self.files[filename]["path"])
            self.file_selected_1 = True
        else:
            self.data_files_oct(self.files[filename]["path"])
            self.file_selected_2 = True

    def list_files_type(self):
        files_ternium = []
        files_oct = []
        if len(self.files) > 0:
            for file in self.files.keys():
                if "Ternium" in file:
                    files_ternium.append(file)
                else:
                    files_oct.append(file)
        return files_ternium, files_oct

    def data_files_ternium(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.df = cb.extract_fichajes_file(filename)
            coldata = []
            for i, col in enumerate(self.df.columns.tolist()):
                coldata.append(
                    {"text": col, "stretch": True}
                )
            self.table_1 = Tableview(self.group_1, bootstyle="primary",
                                     coldata=coldata,
                                     rowdata=self.df.values.tolist(),
                                     paginated=False,
                                     searchable=True,
                                     autofit=True)
            self.table_1.grid(row=11, column=0, sticky='nsew', padx=50, pady=10, columnspan=6)
            self.names.configure(values=self.df["name"].unique().tolist())
            # enables scales
            self.window_time_in.grid(row=0, column=3)
            self.window_time_out.grid(row=0, column=5)
            self.file_selected_1 = True

    def data_files_oct(self, filename):
        if ".xls" in filename or ".xlsx" in filename or ".csv" in filename:
            self.contracts = cb.extract_data_file_contracts(filename)
            if len(self.contracts) != 0:
                table_data, columns = cb.generate_table_from_dict_contracts(self.contracts)
                self.table_2 = Tableview(self.group_2, bootstyle="primary",
                                         coldata=columns,
                                         rowdata=table_data,
                                         paginated=False,
                                         searchable=True,
                                         autofit=True)
                self.table_2.grid(row=8, column=0, sticky='nsew', padx=50, pady=10, columnspan=6)
                self.file_selected_2 = True
                names_oct = []
                for row in table_data:
                    # row[1]=name_employee, create list of employees
                    name =  row[1]
                    if name not in names_oct:
                        names_oct.append(name)
                self.names_oct.configure(values=names_oct)

    def create_info_display_file1(self, master):
        label_subtitle = create_label(
            master, text='Información resumida archivo 1', row=5, column=0)
        label_faltas = create_label(master, textvariable=self.wd, row=6, column=0)
        label_wd_w = create_label(master, textvariable=self.wd_w, row=7, column=0)
        # late hours
        label_late = create_label(master, textvariable=self.late, row=8, column=0)
        label_tot_late_hours = create_label(master, textvariable=self.late_hours, row=8, column=1)
        label_late_hours_day = create_label(master, textvariable=self.late_hours_day, row=8, column=3)
        label_puerta_in = create_label(master, textvariable=self.puerta_in, row=8, column=4)
        label_late_hours_day_out = create_label(master, textvariable=self.late_hours_day_out, row=8, column=5)
        # extra hours
        label_extra = create_label(master, textvariable=self.extra, row=9, column=0)
        label_tot_extra_hours = create_label(master, textvariable=self.extra_hours, row=9, column=1)
        label_extra_hours_day = create_label(master, textvariable=self.extra_hours_day, row=9, column=3)
        label_puerta_out = create_label(master, textvariable=self.puerta_out, row=9, column=4)
        label_extra_hours_day_in = create_label(master, textvariable=self.extra_hours_day_in, row=9, column=5)

    def create_info_display_file2(self, master):
        label_subtitle2 = create_label(
            master, text='Información resumida archivo 2', row=3, column=0)
        label_faltas = create_label(master, textvariable=self.faltas, row=4, column=0)
        label_late2 = create_label(master, textvariable=self.late_hours2, row=5, column=0)
        label_extra2 = create_label(master, textvariable=self.extra_hours2, row=6, column=0)
        label_primas = create_label(master, textvariable=self.primas, row=7, column=0)
        # coments label
        label_comments_1 = create_label(
            master, textvariable=self.comment_f, row=4, column=2, font=('Helvetica', 8),
            columnspan=4)
        label_comments_2 = create_label(
            master, textvariable=self.comment_t, row=5, column=2, font=('Helvetica', 8),
            columnspan=4)
        label_comments_3 = create_label(
            master, textvariable=self.comment_e, row=6, column=2, font=('Helvetica', 8),
            columnspan=4)
        label_comments_4 = create_label(
            master, textvariable=self.comment_p, row=7, column=2, font=('Helvetica', 8),
            columnspan=4)

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

    def select_name(self, event):
        if self.names.get() != "no file selected":
            (worked_days, worked_intime, count, count2,
             self.days_late, self.days_extra) = get_days_worked_late_extra(
                self.df, self.names.get(), self.clocks, self.window_time_in, self.window_time_out,
                self.file_selected_1)
            update_stringvars(
                [(self.wd, f'Numero de dias trabajados: {worked_days}.'),
                 (self.late, f'Numero de dias tarde: {count}.'),
                 (self.extra, f'Numero de dias con horas extras: {count2}.'),
                 (self.wd_w, f'Numero de dias dentro de horario: {worked_intime}.')])
            self.update_late_extra_days()
        else:
            print("no file selected")

    def select_name_oct(self, event):
        if event.widget.get() != "no file selected":
            (self.data_contract_emp, self.days_faltas, self.days_late2, self.days_extra2,
             total_extra2, self.days_prima) = get_data_from_name_contract(
                contracts=self.contracts, name=event.widget.get(), flag=self.file_selected_2)
            update_stringvars(
                [(self.faltas, f'Dias con falta: {len(self.days_faltas)}.'),
                 (self.late_hours2, f'Dias tarde: {len(self.days_late2)}.'),
                 (self.extra_hours2,
                  f'Dias con horas extra: {len(self.days_extra2)}.\nTotal de horas extra: {total_extra2}'),
                 (self.primas, f'Dias con prima: {len(self.days_prima)}.')])
            self.update_late_extra_days_oct()
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
        if  len(late_keys) == 0:
            late_keys.append("no data")
        if len(extra_keys) == 0:
            extra_keys.append("no data")
        self.days_late_selector.configure(values=late_keys)
        self.days_extra_selector.configure(values=extra_keys)
        self.days_late_selector.configure(state="readonly")
        self.days_extra_selector.configure(state="readonly")
        self.days_late_selector.current(0)
        self.days_extra_selector.current(0)
        update_stringvars([
            (self.late_hours, f'Total horas tarde: \n{round(total_late / 3600, 2)}'),
            (self.extra_hours, f'Total horas extras: \n{round(total_extra / 3600, 2)}')
        ])

    def update_late_extra_days_oct(self):
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
        if self.file_selected_1:
            self.label_time_in.configure(text=f'Gracia: {int(self.window_time_in.get())} mins')
            self.label_time_out.configure(text=f'Gracia: {int(self.window_time_out.get())} mins')
