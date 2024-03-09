# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 04/mar./2024  at 13:32 $'

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from static.extensions import log_file_bitacora_path
from templates.Functions_AuxFiles import get_data_employees, get_data_employees_ids, update_bitacora, get_events_date, \
    erase_value_bitacora, split_commment, update_bitacora_value
from templates.Functions_Files import write_log_file
from templates.Functions_SQL import get_employess_op_names
from templates.Funtions_Utils import create_label, create_var_none, create_stringvar, create_button, \
    set_dateEntry_new_value


class BitacoraEditFrame(ScrolledFrame):
    def __init__(self, master, username="default", contrato="default", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        # --------------------------variables----------------------------------
        self.username = username
        self.contrato = contrato
        self.emp_id, self.data_emp, self.events = create_var_none(3)
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
         self.label_valor, self.valor_entry, self.label_comment,
         self.comment_entry, self.prima_selector, self.emp_sel_contract,
         self.label_incidencia, self.incidencia_selector) = self.create_inputs(self.frame_inputs)
        create_label(self, 2, 0, textvariable=self.svar_info, sticky="n")
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
        self.table, self.table_events = self.create_table(self.frame_table)

    def create_inputs(self, master):
        # ----data -----------
        emp_data = get_employess_op_names()
        emp_ids = [i[0] for i in emp_data]
        contratos = [i[3] for i in emp_data]
        contratos_display = list(set(contratos))
        emp_names = [i[1].upper() + " " + i[2].upper() for i in emp_data]
        emp_name_contract = [i[1].upper() + " " + i[2].upper() for i in emp_data if i[3] == self.contrato]
        # --------widgets------------
        create_label(master, 0, 0, text="Empleado (c)", sticky="w")
        emp_selector_contract = ttk.Combobox(
            master, values=emp_name_contract, state="readonly", width=35)
        emp_selector_contract.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        emp_selector_contract.bind("<<ComboboxSelected>>", self.on_emp_selected)
        create_label(master, 0, 2, text="Empleados (g)", sticky="w")
        emp_selector = ttk.Combobox(master, values=emp_names, state="readonly", width=35)
        emp_selector.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        emp_selector.bind("<<ComboboxSelected>>", self.on_emp_selected)
        create_label(master, 1, 0, text="Contrato", sticky="w")
        contract_selector = ttk.Combobox(master, values=contratos_display, state="readonly", width=15)
        contract_selector.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        create_label(master, 2, 0, text="Fecha", sticky="w")
        date_selector = ttk.DateEntry(master,
                                      dateformat="%d-%m-%Y")
        date_selector.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        create_label(master, 3, 0, text="Evento", sticky="w")
        event_selector = ttk.Combobox(
            master, values=["falta", "atraso", "prima", "extra"],
            state="readonly", width=15)
        event_selector.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        event_selector.bind("<<ComboboxSelected>>", self.on_event_selected)
        # toogle button
        prima_selector = ttk.Checkbutton(
            master, text="Aplica prima", variable=self.bvar_prima,
            onvalue=True, offvalue=False, bootstyle="success, round-toggle")
        incidencias = ["acuerdo", "permiso sin goce", "festivo", "vacaciones", "incapacidad", "suspension"]
        label_incidencia = create_label(master, 3, 4, text="Incidencia:", sticky="w")
        incidencia_selector = ttk.Combobox(
            master, values=incidencias, state="readonly", width=20)
        incidencia_selector.grid(row=3, column=5, padx=10, pady=10, sticky="w")
        label_valor = create_label(master, 4, 0, text="Valor", sticky="w")
        valor_entry = ttk.Entry(master, width=5)
        valor_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        create_label(master, 4, 2, text="Actividad", sticky="w")
        ttk.Entry(master, width=35, textvariable=self.svar_activity).grid(
            row=4, column=3, padx=10, pady=10, sticky="w")
        create_label(master, 4, 4, text="Lugar", sticky="w")
        ttk.Entry(master, width=35, textvariable=self.location).grid(
            row=4, column=5, padx=10, pady=10, sticky="w")
        # ---- comments----
        label_comment = create_label(master, 5, 0, text="Comentario", sticky="w")
        comment_entry = ttk.Entry(master, width=100)
        comment_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w", columnspan=5)
        return (emp_selector, emp_ids, contratos, emp_names, contract_selector, date_selector,
                event_selector, label_valor, valor_entry, label_comment, comment_entry,
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
            self.valor_entry.grid_remove()
            self.prima_selector.grid_remove()
            self.label_incidencia.grid()
            self.incidencia_selector.grid()
        elif txt == "prima":
            self.prima_selector.grid_remove()
            self.label_valor.grid_remove()
            self.valor_entry.grid_remove()
            self.label_incidencia.grid_remove()
            self.incidencia_selector.grid_remove()
        elif txt == "extra":
            self.prima_selector.grid(row=3, column=2)
            self.label_valor.grid()
            self.valor_entry.grid()
            self.label_incidencia.grid_remove()
            self.incidencia_selector.grid_remove()
        else:
            self.prima_selector.grid_remove()
            self.label_valor.grid()
            self.valor_entry.grid()
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
        value = float(self.valor_entry.get()) if self.valor_entry.get() != "" else 0
        comment = self.comment_entry.get()
        include_prima = self.bvar_prima.get()
        incidencia = self.incidencia_selector.get()
        activity = self.svar_activity.get()
        location = self.location.get()
        if event == "":
            self.svar_info.set("Llene todos los datos")
            return
        elif event == "prima":
            value = 1.0
        elif event == "falta":
            value = 1.0
            comment += f"\nincidencia-->{incidencia}"
            comment += f"\nactividad-->{activity}"
            comment += f"\nlugar-->{location}"
        return name, contract, date, event, value, comment, include_prima, incidencia, activity, location

    def on_add_click(self):
        if self.emp_id is None:
            self.svar_info.set("Seleccione un empleado")
            return
        (name, contract, date, event, value, comment, include_prima, incidencia,
         activity, location) = self.prepare_data_to_send_DB()
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
                self.update_table()
                self.on_reset_click()
            else:
                self.svar_info.set(error)
                return
        else:
            flag, error, result = update_bitacora(self.emp_id, event, (date, value, comment, contract))
            if flag:
                msg = f"Record inserted--> Empleado: {name}, Contrato: {contract}, Fecha: {date}, Evento: {event}, Valor: {value}, Comentario: {comment}--> by {self.username}"
                write_log_file(log_file_bitacora_path, msg)
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
        self.valor_entry.delete(0, "end")
        self.comment_entry.delete(0, "end")
        self.svar_info.set("Seleccione un empleado")
        self.svar_activity.set("")
        self.location.set("")
        self.incidencia_selector.set("")

    def on_double_click_table(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        (id_emp, name, contract, event, timestamp, value, comment) = row
        timestamp = datetime.strptime(timestamp, "%d-%m-%Y %H:%M:%S")
        comment_dict = split_commment(comment)
        self.emp_id = int(id_emp)
        self.emp_selector.set(name)
        self.emp_sel_contract.set(name)
        self.contract_selector.set(contract)
        self.event_selector.set(event)
        self.valor_entry.delete(0, "end")
        self.valor_entry.insert(0, value)
        self.comment_entry.delete(0, "end")
        self.comment_entry.insert(0, comment_dict["comment"])
        self.svar_info.set(f"Empleado: {name}, ID: {self.emp_id}")
        self.svar_activity.set(comment_dict["activity"])
        self.location.set(comment_dict["place"])
        self.incidencia_selector.set(comment_dict["incidence"])
        self.date_selector = set_dateEntry_new_value(
            self.frame_inputs, self.date_selector,
            timestamp, row=2, column=1, padx=10, pady=10, sticky="w", date_format="%d-%m-%Y")

    def on_erase_event(self):
        if self.emp_id is None:
            self.svar_info.set("Seleccione un empleado")
            return
        name = self.emp_selector.get()
        contract = self.contract_selector.get()
        date = self.date_selector.entry.get()
        event = self.event_selector.get()
        flag, error, result = erase_value_bitacora(self.emp_id, event, (date, contract))
        if flag:
            msg = f"Record deleted--> Empleado: {name}, Contrato: {contract}, Fecha: {date}, Evento: {event}--> by {self.username}"
            write_log_file(log_file_bitacora_path, msg)
            self.update_table()
            self.on_reset_click()
        else:
            self.svar_info.set(error)

    def on_update_data_event(self):
        if self.emp_id is None:
            return
        (name, contract, date, event, value, comment, include_prima, incidencia,
         activity, location) = self.prepare_data_to_send_DB()
        flag, error, result = update_bitacora_value(self.emp_id, event, (date, value, comment, contract))
        if flag:
            msg = (f"Record updated--> Empleado: {name}, "
                   f"Contrato: {contract}, Fecha: {date}, "
                   f"Evento: {event}, Valor: {value}, "
                   f"Comentario: {comment}--> by {self.username}")
            write_log_file(log_file_bitacora_path, msg)
            self.update_table()
            self.on_reset_click()
        else:
            self.svar_info.set(error)

    def create_table(self, master, hard_update=False):
        # label title
        ttk.Label(
            master, text='Eventos del mes', font=("Helvetica", 22, "bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=10)
        # tableview de eventos
        date = self.date_selector.entry.get()
        date = datetime.strptime(date, "%d-%m-%Y")
        self.events, columns = get_events_date(date, hard_update)
        table_events = Tableview(master,
                                 coldata=columns,
                                 rowdata=self.events,
                                 paginated=True,
                                 searchable=True,
                                 autofit=True)
        table_events.grid(row=1, column=0, padx=20, pady=10, sticky="nswe")
        table_events.view.bind("<Double-1>", self.on_double_click_table)
        ttk.Label(
            master, text='Resumen general de empleados', font=("Helvetica", 22, "bold")).grid(
            row=2, column=0, columnspan=4, padx=10, pady=10)
        # tableview de empleados
        self.data_emp, columns = get_data_employees_ids(self.emp_ids)
        table_resume = Tableview(master,
                                 coldata=columns,
                                 rowdata=self.data_emp,
                                 paginated=True,
                                 searchable=True,
                                 autofit=True)
        table_resume.grid(row=3, column=0, padx=20, pady=10)
        return table_resume, table_events

    def update_table(self):
        self.table.destroy()
        self.table_events.destroy()
        self.table, self.table_events = self.create_table(self.frame_table, hard_update=True)
