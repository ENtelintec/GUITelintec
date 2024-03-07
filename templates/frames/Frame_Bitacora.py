# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 04/mar./2024  at 13:32 $'

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from static.extensions import log_file_bitacora_path
from templates.Functions_AuxFiles import get_data_employees, get_data_employees_ids, update_bitacora, get_events_date
from templates.Functions_Files import write_log_file
from templates.Functions_SQL import get_employess_op_names
from templates.Funtions_Utils import create_label, create_var_none, create_stringvar, create_button, \
    set_dateEntry_new_value


class BitacoraEditFrame(ScrolledFrame):
    def __init__(self, master, username="default", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        # --------------------------variables----------------------------------
        self.username = username
        self.emp_id, self.data_emp, self.events = create_var_none(3)
        self.svar_info, self.svar_out = create_stringvar(2, "")
        # ----------------------------title------------------------------------
        create_label(self, 0, 0, text="Bitacora",
                     font=("Helvetica", 30, "bold"), columnspan=2)
        self.frame_inputs = ttk.Frame(self)
        self.frame_inputs.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_inputs.columnconfigure((0, 1), weight=1)
        (self.emp_selector, self.emp_ids, self.contratos, self.emp_names,
         self.contract_selector, self.date_selector, self.event_selector,
         self.label_valor, self.valor_entry, self.label_comment,
         self.comment_entry) = self.create_inputs(self.frame_inputs)
        create_label(self, 2, 0, textvariable=self.svar_info, sticky="n")
        # --------------------------buttons-----------------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=3, column=0, padx=10, pady=10, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2), weight=1)
        (self.btn_add, self.btn_cancel) = self.create_buttons(frame_buttons)
        # -----------------------------tableview----------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=4, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.table, self.table_events = self.create_table(self.frame_table)

    def create_inputs(self, master):
        create_label(master, 0, 0, text="Empleado", sticky="w")
        emp_data = get_employess_op_names()
        emp_ids = [i[0] for i in emp_data]
        contratos = [i[3] for i in emp_data]
        emp_names = [i[1].upper() + " " + i[2].upper() for i in emp_data]
        emp_selector = ttk.Combobox(master, values=emp_names, state="readonly", width=35)
        emp_selector.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        emp_selector.bind("<<ComboboxSelected>>", self.on_emp_selected)
        create_label(master, 1, 0, text="Contrato", sticky="w")
        contract_selector = ttk.Combobox(master, values=contratos, state="readonly", width=15)
        contract_selector.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        create_label(master, 2, 0, text="Fecha", sticky="w")
        date_selector = ttk.DateEntry(master)
        date_selector.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        create_label(master, 3, 0, text="Evento", sticky="w")
        event_selector = ttk.Combobox(
            master, values=["falta", "atraso", "prima", "extra"],
            state="readonly", width=15)
        event_selector.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        event_selector.bind("<<ComboboxSelected>>", self.on_event_selected)
        label_valor = create_label(master, 4, 0, text="Valor", sticky="w")
        valor_entry = ttk.Entry(master, width=5)
        valor_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        label_comment = create_label(master, 5, 0, text="Comentario", sticky="w")
        comment_entry = ttk.Entry(master, width=35)
        comment_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")
        return (emp_selector, emp_ids, contratos, emp_names, contract_selector, date_selector,
                event_selector, label_valor, valor_entry, label_comment, comment_entry)

    def on_emp_selected(self, event):
        name_emp = event.widget.get()
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
        else:
            self.label_valor.grid()
            self.valor_entry.grid()

    def create_buttons(self, master):
        btn_add = create_button(
            master, 0, 0, "Agregar evento", command=self.on_add_click,
            sticky="n", width=15)
        btn_reset = create_button(
            master, 0, 1, "Reset", command=self.on_reset_click,
            sticky="n", width=15)
        btn_update_table = create_button(
            master, 0, 2, "Actualizar tabla", command=self.update_table,
            sticky="n", width=15)
        return btn_add, btn_reset

    def on_add_click(self):
        if self.emp_id is None:
            self.svar_info.set("Seleccione un empleado")
            return
        name = self.emp_selector.get()
        contract = self.contract_selector.get()
        date = self.date_selector.entry.get()
        event = self.event_selector.get()
        value = self.valor_entry.get()
        comment = self.comment_entry.get()
        flag, error, result = update_bitacora(self.emp_id, event, (date, value, comment, contract))
        if flag:
            msg = f"Record inserted--> Empleado: {name}, Contrato: {contract}, Fecha: {date}, Evento: {event}, Valor: {value}, Comentario: {comment}--> by {self.username}"
            write_log_file(log_file_bitacora_path, msg)
        else:
            self.svar_info.set(error)

    def on_reset_click(self):
        self.emp_selector.set("")
        self.contract_selector.set("")
        self.emp_id = None
        self.event_selector.set("")
        self.valor_entry.delete(0, "end")
        self.comment_entry.delete(0, "end")

    def on_double_click_table(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        (id_emp, name, contract, event, timestamp, value, comment) = row
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        self.emp_id = int(id_emp)
        self.emp_selector.set(name)
        self.contract_selector.set(contract)
        self.event_selector.set(event)
        self.valor_entry.delete(0, "end")
        self.valor_entry.insert(0, value)
        self.comment_entry.delete(0, "end")
        self.comment_entry.insert(0, comment)
        self.svar_info.set(f"Empleado: {name}, ID: {self.emp_id}")
        self.date_selector = set_dateEntry_new_value(
            self.frame_inputs, self.date_selector,
            timestamp, row=2, column=1, padx=10, pady=10, sticky="w")

    def create_table(self, master):
        # label title
        ttk.Label(
            master, text='Eventos del mes', font=("Helvetica", 22, "bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=10)
        # tableview de eventos
        date = self.date_selector.entry.get()
        date = datetime.strptime(date, '%d/%b/%Y')
        self.events, columns = get_events_date(date)
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
        self.table, self.table_events = self.create_table(self.frame_table)
