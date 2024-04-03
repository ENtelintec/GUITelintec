# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/abr./2024  at 15:59 $'

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from templates.Functions_AuxFiles import get_all_sm_entries, get_all_sm_products
from templates.Functions_SQL import get_sm_employees, get_sm_clients
from templates.Funtions_Utils import create_label, create_button, create_stringvar, create_Combobox

import json


class FrameSM(ScrolledFrame):
    def __init__(self, master=None, department="default", settings=None, **kw):
        super().__init__(master, **kw)
        self.columnconfigure((0, 1), weight=1)
        """----------------------------variables-----------------------------"""
        self.settings = settings
        self.department = department
        self._id_sm_to_update = None
        self.data_sm = None
        self.svar_info = create_stringvar(1, "")
        flag, error, self.employees = get_sm_employees()
        flag, error, self.clients = get_sm_clients()
        """-------------------------title------------------------------------"""
        create_label(self, 0, 0, text="Solicitudes de material",
                     font=("Helvetica", 30, "bold"), columnspan=2)
        """-------------------Widgets input----------------------------------"""
        frame_input_general = ttk.Frame(self)
        frame_input_general.grid(row=1, column=0, padx=2, pady=5, sticky="nswe")
        frame_input_general.columnconfigure((0, 1), weight=1)
        self.frame_inputs = ttk.Frame(frame_input_general)
        self.frame_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_inputs.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.entries = self.create_inputs(self.frame_inputs)
        self.frame_products = FrameSMProdcuts(frame_input_general)
        self.frame_products.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")
        create_label(self, 2, 0, textvariable=self.svar_info, sticky="n", font=("Helvetica", 15, "bold"))
        """------------------------buttons-----------------------------------"""
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=3, column=0, padx=10, pady=10, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2, 3, 4), weight=1)
        (self.btn_add, self.btn_update_event, self.btn_cancel,
         self.btn_update, self.btn_erase) = self.create_buttons(frame_buttons)
        """-----------------------------tableview----------------------------"""
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=4, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.frame_table.rowconfigure(1, weight=1)
        self.table_events = self.create_table(self.frame_table)

    def create_inputs(self, master):
        entries = []
        # info inputs---------
        create_label(master, 0, 0, text="SM: ", sticky="w")
        create_label(master, 1, 0, text="SM code: ", sticky="w")
        create_label(master, 2, 0, text="Folio: ", sticky="w")
        create_label(master, 3, 0, text="Contrato: ", sticky="w")
        create_label(master, 4, 0, text="Planta: ", sticky="w")
        create_label(master, 5, 0, text="Ubicación: ", sticky="w")
        create_label(master, 6, 0, text="Cliente: ", sticky="w")
        create_label(master, 7, 0, text="Empleado: ", sticky="w")
        create_label(master, 8, 0, text="Fecha: ", sticky="w")
        create_label(master, 9, 0, text="Fecha limite: ", sticky="w")
        create_label(master, 10, 0, text="Estatus: ", sticky="w")
        # entries
        emp_list = [emp[1].title() + " " + emp[2].title() for emp in self.employees]
        client_list = [client[1] for client in self.clients]
        entries.append(ttk.Entry(master).grid(row=0, column=1, padx=10, pady=10, sticky="w"))
        entries.append(ttk.Entry(master).grid(row=1, column=1, padx=10, pady=10, sticky="w"))
        entries.append(ttk.Entry(master).grid(row=2, column=1, padx=10, pady=10, sticky="w"))
        entries.append(ttk.Entry(master).grid(row=3, column=1, padx=10, pady=10, sticky="w"))
        entries.append(ttk.Entry(master).grid(row=4, column=1, padx=10, pady=10, sticky="w"))
        entries.append(ttk.Entry(master).grid(row=5, column=1, padx=10, pady=10, sticky="w"))
        entries.append(create_Combobox(master, emp_list, 25, row=6, column=1, sticky="w"))
        entries.append(create_Combobox(master, client_list, 25, row=7, column=1, sticky="w"))
        entries.append(
            ttk.DateEntry(master, firstweekday=0, dateformat="%Y-%m-%d").grid(row=8, column=1, padx=10, pady=10,
                                                                              sticky="n"))
        entries.append(
            ttk.DateEntry(master, firstweekday=0, dateformat="%Y-%m-%d").grid(row=9, column=1, padx=10, pady=10,
                                                                              sticky="n"))
        entries.append(create_Combobox(master, ["pendiente", "completado"], 15, row=10, column=1, sticky="n"))
        return entries

    def create_buttons(self, master):
        btn_add = create_button(
            master, 0, 0, "Agregar SM", command=self.on_add_click,
            sticky="n", width=15)
        btn_update_data = create_button(
            master, 0, 1, "Actualizar SM", command=self.on_update_sm_event,
            sticky="n", width=15)
        btn_reset = create_button(
            master, 0, 2, "Reset", command=self.on_reset_widgets_click,
            sticky="n", width=15)
        btn_update_table = create_button(
            master, 0, 3, "Actualizar tabla", command=self.update_table_visual,
            sticky="n", width=15)
        btn_erase_event = create_button(
            master, 0, 4, "Borrar SM", command=self.on_erase_click,
            sticky="n", width=15)
        return btn_add, btn_update_data, btn_reset, btn_update_table, btn_erase_event

    def create_table(self, master):
        self.data_sm, columns = get_all_sm_entries()
        table = Tableview(master,
                          coldata=columns,
                          rowdata=self.data_sm,
                          paginated=True,
                          searchable=True,
                          autofit=True,
                          height=21,
                          pagesize=20)
        table.grid(row=1, column=0, padx=20, pady=10, sticky="n")
        table.view.bind("<Double-1>", self.on_double_click_table_sm)
        return table

    def on_add_click(self):
        data_products = self.get_entries_values()
        print(data_products)

    def on_update_sm_event(self):
        pass

    def on_reset_widgets_click(self):
        pass

    def update_table_visual(self):
        pass

    def on_erase_click(self):
        pass

    def on_double_click_table_sm(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        id_sm, code, folio, contract, plant, location, client, employee, date, date_limit, items, status = row
        items = json.loads(items)
        items_table = []
        for product in items:
            items_table.append((product["id"], product["quantity"], product["comment"],))
        self.frame_products.put_data_resumen(items_table)
        print(row)

    def get_entries_values(self):
        data_products = self.frame_products.get_resumen_table_data()
        return data_products


class FrameSMProdcuts(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.columnconfigure((0, 1), weight=1)
        self.svar_info = create_stringvar(1, "")
        self.products, self.columns_products = get_all_sm_products()
        """-------------------------title------------------------------------"""
        create_label(self, 0, 0, text="Lista de Productos",
                     font=("Helvetica", 14, "bold"))
        """-------------------------table------------------------------------"""
        frame_tabla_products = ttk.Frame(self)
        frame_tabla_products.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        frame_tabla_products.columnconfigure(0, weight=1)
        create_label(frame_tabla_products, 0, 0, text="Productos BD",
                     font=("Helvetica", 11, "bold"))
        self.table_products = self.create_table(frame_tabla_products, type_table=1)
        self.frame_resumen = ttk.Frame(self)
        self.frame_resumen.grid(row=2, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_resumen.columnconfigure(0, weight=1)
        create_label(self.frame_resumen, 0, 0, text="Resumen",
                     font=("Helvetica", 12, "bold"))
        self.table_resumen = self.create_table(self.frame_resumen, type_table=2)
        """-------------------Widgets input----------------------------------"""
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=1, padx=10, pady=10, sticky="nswe")
        self.entries = self.create_inputs(frame_inputs)
        """-------------------Widgets buttons--------------------------------"""
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=1, padx=10, pady=10, sticky="nswe")
        frame_buttons.columnconfigure(0, weight=1)
        self.create_buttons(frame_buttons)

    def create_table(self, master, type_table=1, data_resumen=None):
        if type_table == 1:
            table = Tableview(
                master, coldata=self.columns_products,
                rowdata=self.products, paginated=True,
                searchable=True, autofit=True,
                height=5, pagesize=5)
            table.grid(row=1, column=0, padx=20, pady=10, sticky="n")
            table.view.bind("<Double-1>", self.on_double_click_table_products)
        else:
            columns = ["ID", "Cantidad", "Comentario"]
            data_resume = data_resumen if data_resumen is not None else []
            table = Tableview(
                master, coldata=columns,
                rowdata=data_resume, paginated=True,
                searchable=True, autofit=True,
                height=5, pagesize=5)
            table.grid(row=1, column=0, padx=20, pady=10, sticky="n")
            table.view.bind("<Double-1>", self.on_double_click_table_resumen)
        return table

    def on_double_click_table_products(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self.on_reset_click()
        self.entries[0].insert(0, row[0])

    def on_double_click_table_resumen(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        for i, item in enumerate(self.entries):
            item.delete(0, "end")
            item.insert(0, row[i])

    def clean_table_resumen(self):
        self.table_resumen = self.create_table(self.frame_resumen, type_table=2)

    def create_inputs(self, master) -> list[ttk.Entry] | list[None]:
        create_label(master, 0, 0, text="ID: ", sticky="w")
        create_label(master, 1, 0, text="Cantidad: ", sticky="w")
        create_label(master, 2, 0, text="Comentario: ", sticky="w")
        entry1 = ttk.Entry(master, width=5)
        entry1.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        entry2 = ttk.Entry(master, width=5)
        entry2.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        entry3 = ttk.Entry(master)
        entry3.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        return [entry1, entry2, entry3]

    def create_buttons(self, master):
        create_button(
            master, 0, 0, "Agregar", command=self.on_add_click,
            sticky="n", width=15)
        create_button(
            master, 1, 0, "Actualizar", command=self.on_update_click,
            sticky="n", width=15)
        create_button(
            master, 2, 0, "Reset", command=self.on_reset_click,
            sticky="n", width=15)
        create_button(
            master, 3, 0, "Eliminar", command=self.on_erase_click,
            sticky="n", width=15)

    def on_add_click(self):
        values = []
        for item in self.entries:
            values.append(item.get())
        data_table = self.table_resumen.view.get_children()
        flag_update = False
        for item in data_table:
            id_p, quantity, comment = self.table_resumen.view.item(item, "values")
            if id_p == values[0] and comment == values[2]:
                self.table_resumen.view.item(item, values=values)
                flag_update = True
                break
        if not flag_update:
            self.table_resumen.view.insert("", "end", values=values)

    def on_update_click(self):
        values = []
        for item in self.entries:
            values.append(item.get())
        self.table_resumen.view.item(self.table_resumen.view.selection()[0], values=values)

    def on_reset_click(self):
        for item in self.entries:
            item.delete(0, "end")

    def on_erase_click(self):
        item = self.table_resumen.view.selection()
        if len(item) > 0:
            self.table_resumen.view.delete(self.table_resumen.view.selection()[0])
        self.on_reset_click()

    def get_resumen_table_data(self):
        data = []
        for item in self.table_resumen.view.get_children():
            id_p, quantity, comment = self.table_resumen.view.item(item, "values")
            data.append((id_p, quantity, comment))
        return data

    def put_data_resumen(self, data):
        self.table_resumen.destroy()
        self.table_resumen = self.create_table(self.frame_resumen, type_table=2, data_resumen=data)
