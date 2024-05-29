# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 04/mar./2024  at 13:32 $'

import calendar
from datetime import datetime, timedelta

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from static.extensions import log_file_bitacora_path, delta_bitacora_edit, format_date
from templates.Functions_AuxFiles import update_bitacora, get_events_op_date, \
    erase_value_bitacora, split_commment, update_bitacora_value
from templates.Functions_Files import write_log_file
from templates.Funtions_Utils import create_label, create_var_none, create_stringvar, create_button, \
    set_dateEntry_new_value, create_notification_permission
from templates.controllers.employees.employees_controller import get_employees_op_names


def check_date_difference(date_modify, delta):
    flag = True
    date_now = datetime.now()
    date_modify = datetime.strptime(date_modify, "%Y-%m-%d")
    date_modify = date_modify.date()
    # week of the month
    week_modify = date_modify.isocalendar()[1]
    date_now = date_now.date()
    week_now = date_now.isocalendar()[1]
    date_modify = date_modify + timedelta(days=delta)
    if week_now-week_modify > 1:
        flag = False
    return flag


class BitacoraEditFrame(ScrolledFrame):
    def __init__(self, master, username="default", contrato="default", delta=delta_bitacora_edit, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        # --------------------------variables----------------------------------
        self.username = username
        self.contrato = contrato
        self.delta = delta
        self.emps_names = kwargs["data"]["bitacora"]["emp_data"] if "bitacora" in kwargs["data"] else None
        self.events = kwargs["data"]["bitacora"]["events"] if "bitacora" in kwargs["data"] else None
        self.columns = kwargs["data"]["bitacora"]["columns"] if "bitacora" in kwargs["data"] else None
        self.emp_id, self.data_emp = create_var_none(2)
        self.svar_info, self.svar_out, self.svar_activity, self.location = create_stringvar(4, "")
        self.bvar_prima = ttk.BooleanVar()
        # ----------------------------title------------------------------------
        create_label(self, 0, 0, text="Bitacora",
                     font=("Helvetica", 30, "bold"), columnspan=2)
        self.frame_inputs = ttk.Frame(self)
        self.frame_inputs.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_inputs.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        (self.emp_selector, self.emp_ids, self.contratos, self.emp_names,
         self.contract_selector, self.date_selector, self.event_selector,
         self.label_valor, self.valor_entry_hora, self.valor_entry_mins, self.frame_valor,
         self.label_comment, self.comment_entry, self.prima_selector, self.emp_sel_contract,
         self.label_incidencia, self.incidencia_selector) = self.create_inputs(self.frame_inputs)
        create_label(self, 2, 0, textvariable=self.svar_info, sticky="n", font=("Helvetica", 15, "bold"))
        # --------------------------buttons-----------------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=3, column=0, padx=10, pady=10, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2, 3, 4), weight=1)
        (self.btn_add, self.btn_update_event, self.btn_cancel,
         self.btn_update, self.btn_erase) = self.create_buttons(frame_buttons)
        # -----------------------------tableview----------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=4, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.frame_table.rowconfigure(1, weight=1)
        self.table_events = self.create_table(self.frame_table)

    def create_inputs(self, master):
        # ----data -----------
        flag, error, emp_data = get_employees_op_names() if self.emps_names is None else (True, "", self.emps_names)
        emp_ids = [i[0] for i in emp_data]
        contratos = [i[3] for i in emp_data]
        contratos_display = list(set(contratos))
        emp_names = [i[1].upper() + " " + i[2].upper() for i in emp_data]
        emp_name_contract = [i[1].upper() + " " + i[2].upper() for i in emp_data if i[3] == self.contrato]
        emp_name_extra = [name for name in emp_names if name not in emp_name_contract]
        # --------widgets------------
        create_label(master, 0, 0, text="Empleado (c)", sticky="w")
        emp_selector_contract = ttk.Combobox(
            master, values=emp_name_contract, state="readonly", width=35)
        emp_selector_contract.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        emp_selector_contract.bind("<<ComboboxSelected>>", self.on_emp_selected)
        create_label(master, 0, 2, text="Empleados (extra)", sticky="w")
        emp_selector = ttk.Combobox(master, values=emp_name_extra, state="readonly", width=35)
        emp_selector.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        emp_selector.bind("<<ComboboxSelected>>", self.on_emp_selected)
        create_label(master, 1, 0, text="Contrato", sticky="w")
        contract_selector = ttk.Combobox(master, values=contratos_display, state="readonly", width=15)
        contract_selector.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        create_label(master, 2, 0, text="Fecha", sticky="w")
        date_selector = ttk.DateEntry(master,
                                      dateformat="%Y-%m-%d", firstweekday=0)
        date_selector.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        create_label(master, 3, 0, text="Evento", sticky="w")
        event_selector = ttk.Combobox(
            master, values=["falta", "atraso", "extra", "normal"],
            state="readonly", width=15)
        event_selector.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        event_selector.bind("<<ComboboxSelected>>", self.on_event_selected)
        # toogle button
        # noinspection PyArgumentList
        prima_selector = ttk.Checkbutton(
            master, text="Aplica prima", variable=self.bvar_prima,
            onvalue=True, offvalue=False, bootstyle="success, round-toggle")
        incidencias = ["acuerdo", "permiso sin goce", "festivo", "vacaciones", "incapacidad", "suspension"]
        label_incidencia = create_label(master, 3, 4, text="Incidencia:", sticky="w")
        incidencia_selector = ttk.Combobox(
            master, values=incidencias, state="readonly", width=20)
        incidencia_selector.grid(row=3, column=5, padx=10, pady=10, sticky="w")
        label_incidencia.grid_remove()
        incidencia_selector.grid_remove()
        label_valor = create_label(master, 4, 0, text="Valor", sticky="w")
        frame_valor = ttk.Frame(master)
        frame_valor.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        valor_entry_hora = ttk.Entry(frame_valor, width=3)
        valor_entry_hora.grid(row=0, column=0, padx=1, pady=10, sticky="w")
        create_label(frame_valor, 0, 1, text="horas", sticky="w", padx=1, pady=10)
        valor_entry_min = ttk.Entry(frame_valor, width=3)
        valor_entry_min.grid(row=0, column=2, padx=1, pady=10, sticky="w")
        create_label(frame_valor, 0, 3, text="minutos", sticky="w", padx=1, pady=10)
        create_label(master, 4, 2, text="Actividad", sticky="w")
        ttk.Entry(master, width=35, textvariable=self.svar_activity).grid(
            row=4, column=3, padx=10, pady=10, sticky="w")
        create_label(master, 4, 4, text="Lugar", sticky="w")
        place_list = ["GUERRERO", "UNIVERSIDAD", "ALMACEN", "CURUBUSCO", "MITRAS",
                      "LARGOS NORTE", "JUVENTUD", "PESQUERIA", "CSI", "CSC", "EDIFICIO METALICOS",
                      "NOVA", "PUEBLA", "SAN LUIS", "OTROS"]
        place_selector = ttk.Combobox(
            master, values=place_list, state="readonly", width=20, textvariable=self.location)
        place_selector.grid(row=4, column=5, padx=10, pady=10, sticky="w")
        # ttk.Entry(master, width=35, textvariable=self.location).grid(
        #     row=4, column=5, padx=10, pady=10, sticky="w")
        # ---- comments----
        label_comment = create_label(master, 5, 0, text="Comentario", sticky="w")
        comment_entry = ttk.Entry(master, width=100)
        comment_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w", columnspan=5)
        return (emp_selector, emp_ids, contratos, emp_names, contract_selector, date_selector,
                event_selector, label_valor, valor_entry_hora, valor_entry_min, frame_valor, label_comment,
                comment_entry,
                prima_selector, emp_selector_contract, label_incidencia, incidencia_selector)

    def on_emp_selected(self, event):
        name_emp = event.widget.get()
        self.emp_selector.set(name_emp)
        self.emp_sel_contract.set(name_emp)
        for i, name in enumerate(self.emp_names):
            if name_emp in name:
                self.emp_id = self.emp_ids[i]
                contract = self.contratos[i]
                self.contract_selector.set(contract)
                self.svar_info.set(f"Empleado: {name_emp}, ID: {self.emp_id}")
                break

    def on_event_selected(self, event):
        txt = event.widget.get()
        if txt == "falta":
            self.label_valor.grid_remove()
            self.frame_valor.grid_remove()
            self.prima_selector.grid_remove()
            self.label_incidencia.grid()
            self.incidencia_selector.grid()
        elif txt == "prima":
            self.prima_selector.grid_remove()
            self.label_valor.grid_remove()
            self.frame_valor.grid_remove()
            self.label_incidencia.grid_remove()
            self.incidencia_selector.grid_remove()
        elif txt == "extra":
            self.prima_selector.grid(row=3, column=2)
            self.label_valor.grid()
            self.frame_valor.grid()
            self.label_incidencia.grid_remove()
            self.incidencia_selector.grid_remove()
        elif txt == "normal":
            self.prima_selector.grid_remove()
            self.label_valor.grid_remove()
            self.frame_valor.grid_remove()
            self.label_incidencia.grid_remove()
            self.incidencia_selector.grid_remove()
        else:
            self.prima_selector.grid_remove()
            self.label_valor.grid()
            self.frame_valor.grid()
            self.label_incidencia.grid_remove()
            self.incidencia_selector.grid_remove()

    def create_buttons(self, master):
        btn_add = create_button(
            master, 0, 0, "Agregar evento", command=self.on_add_click,
            sticky="n", width=15)
        btn_update_data = create_button(
            master, 0, 1, "Actualizar datos", command=self.on_update_data_event,
            sticky="n", width=15)
        btn_reset = create_button(
            master, 0, 2, "Reset", command=self.on_reset_click,
            sticky="n", width=15)
        btn_update_table = create_button(
            master, 0, 3, "Actualizar tabla", command=self.update_table,
            sticky="n", width=15)
        btn_erase_event = create_button(
            master, 0, 4, "Borrar evento", command=self.on_erase_event,
            sticky="n", width=15)
        return btn_add, btn_update_data, btn_reset, btn_update_table, btn_erase_event

    def prepare_data_to_send_DB(self):
        name = self.emp_selector.get()
        contract = self.contract_selector.get()
        date = self.date_selector.entry.get()
        event = self.event_selector.get()
        value = float(self.valor_entry_hora.get()) if self.valor_entry_hora.get() != "" else 0
        value += float(self.valor_entry_mins.get()) / 60 if self.valor_entry_mins.get() != "" else 0
        comment = self.comment_entry.get()
        include_prima = self.bvar_prima.get()
        incidencia = self.incidencia_selector.get()
        activity = self.svar_activity.get()
        location = self.location.get()
        if event == "":
            self.svar_info.set("Llene todos los datos")
            return None, None, None, None, None, None, None, None, None, None
        elif event == "prima":
            value = 1.0
        elif event == "falta":
            value = 1.0
            comment += f"\nincidencia-->{incidencia}"
        elif event == "normal":
            value = 1.0
        comment += f"\nactividad-->{activity}"
        comment += f"\nlugar-->{location}"
        comment += f"\ncontrato-->{contract}"
        return name, contract, date, event, value, comment, include_prima, incidencia, activity, location

    def on_add_click(self):
        if self.emp_id is None:
            self.svar_info.set("Seleccione un empleado")
            return
        (name, contract, date, event, value, comment, include_prima, incidencia,
         activity, location) = self.prepare_data_to_send_DB()
        out = check_date_difference(date, self.delta)
        if not out:
            self.svar_info.set("No se puede añadir un evento pasado el tiempo limite de modificaciones.")
            return

        if include_prima and event == "extra":
            flag, error, result = update_bitacora(self.emp_id, event, (date, value, comment, contract))
            if flag:
                msg = f"Record inserted--> Empleado: {name}, Contrato: {contract}, Fecha: {date}, Evento: {event}, Valor: {value}, Comentario: {comment}--> by {self.username}"
                write_log_file(log_file_bitacora_path, msg)
            else:
                self.svar_info.set(error)
                return
            event = "prima"
            value = 1.0
            flag, error, result = update_bitacora(self.emp_id, event, (date, value, comment, contract))
            if flag:
                msg = f"Record inserted--> Empleado: {name}, Contrato: {contract}, Fecha: {date}, Evento: {event}, Valor: {value}, Comentario: {comment}--> by {self.username}"
                write_log_file(log_file_bitacora_path, msg)
                create_notification_permission(msg, ["bitacora", "operaciones"], "Nuevo evento bitacora", self.emp_id, 0)
                self.update_table()
                self.on_reset_click()
            else:
                self.svar_info.set(error)
                return
        else:
            print(self.emp_id, event)
            flag, error, result = update_bitacora(self.emp_id, event, (date, value, comment, contract))
            if flag:
                msg = f"Record inserted--> Empleado: {name}, Contrato: {contract}, Fecha: {date}, Evento: {event}, Valor: {value}, Comentario: {comment}--> by {self.username}"
                write_log_file(log_file_bitacora_path, msg)
                create_notification_permission(msg, ["bitacoras", "operaciones"], "Nuevo evento bitacora", self.emp_id,
                                               0)
                self.update_table()
                self.on_reset_click()
            else:
                self.svar_info.set(error)

    def on_reset_click(self):
        self.emp_selector.set("")
        self.emp_sel_contract.set("")
        self.contract_selector.set("")
        self.emp_id = None
        self.event_selector.set("")
        self.valor_entry_hora.delete(0, "end")
        self.valor_entry_mins.delete(0, "end")
        self.comment_entry.delete(0, "end")
        self.svar_info.set("Seleccione un empleado")
        self.svar_activity.set("")
        self.location.set("")
        self.incidencia_selector.set("")
        self.prima_selector.grid_remove()
        self.incidencia_selector.grid_remove()
        self.label_incidencia.grid_remove()

    def on_double_click_table(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        (id_emp, name, contract, event, place, activity, timestamp, value, comment) = row
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        value = float(value)
        comment_dict = split_commment(comment)
        self.emp_id = int(id_emp)
        self.emp_selector.set(name)
        self.emp_sel_contract.set(name)
        self.contract_selector.set(contract) if comment_dict["contract"] is None else self.contract_selector.set(comment_dict["contract"])
        self.event_selector.set(event)
        self.valor_entry_hora.delete(0, "end")
        self.valor_entry_hora.insert(0, str(int(value)))
        self.valor_entry_mins.delete(0, "end")
        self.valor_entry_mins.insert(0, str(int((value - int(value)) * 60)))
        self.comment_entry.delete(0, "end")
        self.comment_entry.insert(0, comment_dict["comment"])
        self.svar_info.set(f"Empleado: {name}, ID: {self.emp_id}")
        self.svar_activity.set(comment_dict["activity"])
        self.location.set(comment_dict["place"])
        self.incidencia_selector.set(comment_dict["incidence"])
        self.date_selector = set_dateEntry_new_value(
            self.frame_inputs, self.date_selector,
            timestamp, row=2, column=1, padx=10, pady=10, sticky="w",
            date_format="%Y-%m-%d", firstweekday=0)

    def on_erase_event(self):
        if self.emp_id is None:
            self.svar_info.set("Seleccione un empleado")
            return
        date = self.date_selector.entry.get()
        out = check_date_difference(date, self.delta)
        if not out:
            self.svar_info.set("No se puede eliminar en esta fecha.")
            return
        name = self.emp_selector.get()
        contract = self.contract_selector.get()
        event = self.event_selector.get()
        flag, error, result = erase_value_bitacora(self.emp_id, event, (date, contract))
        if flag:
            msg = f"Record deleted--> Empleado: {name}, Contrato: {contract}, Fecha: {date}, Evento: {event}--> by {self.username}"
            write_log_file(log_file_bitacora_path, msg)
            create_notification_permission(msg, ["bitacoras", "operaciones"], "Evento borrado bitacora", self.emp_id, 0)
            self.update_table()
            self.on_reset_click()
        else:
            self.svar_info.set(error)

    def on_update_data_event(self):
        if self.emp_id is None:
            return
        (name, contract, date, event, value, comment, include_prima, incidencia,
         activity, location) = self.prepare_data_to_send_DB()
        out = check_date_difference(date, self.delta)
        if not out:
            self.svar_info.set("No se puede modificar estas fechas")
            return
        flag, error, result = update_bitacora_value(self.emp_id, event, (date, value, comment, contract))
        if flag:
            msg = (f"Record updated--> Empleado: {name}, "
                   f"Contrato: {contract}, Fecha: {date}, "
                   f"Evento: {event}, Valor: {value}, "
                   f"Comentario: {comment}--> by {self.username}")
            write_log_file(log_file_bitacora_path, msg)
            create_notification_permission(msg, ["bitacoras", "operaciones"], "Evento actualizado bitacora", self.emp_id, 0)
            self.update_table()
            self.on_reset_click()
        else:
            self.svar_info.set(error)

    def create_table(self, master, hard_update=False):
        # label title
        date = self.date_selector.entry.get()
        date = datetime.strptime(date, format_date)
        month = date.month
        # month name
        month_name = calendar.month_name[month]
        ttk.Label(
            master, text=f'Eventos del mes de {month_name}', font=("Helvetica", 22, "bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=10)
        # tableview de eventos
        date = self.date_selector.entry.get()
        date = datetime.strptime(date, format_date)
        self.events, self.columns = get_events_op_date(date, hard_update) if self.events is None else (self.events, self.columns)
        table_events = Tableview(master,
                                 coldata=self.columns,
                                 rowdata=self.events,
                                 paginated=True,
                                 searchable=True,
                                 autofit=True,
                                 height=21,
                                 pagesize=20)
        table_events.grid(row=1, column=0, padx=20, pady=10, sticky="n")
        table_events.view.bind("<Double-1>", self.on_double_click_table)
        return table_events

    def update_table(self):
        # self.table.destroy()
        self.table_events.destroy()
        self.table_events = self.create_table(self.frame_table, hard_update=True)
