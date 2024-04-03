# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/abr./2024  at 15:59 $'

import time
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from templates.Functions_AuxFiles import get_all_sm_entries, get_all_sm_products
from templates.Functions_SQL import get_sm_employees, get_sm_clients, insert_sm_db, update_sm_db, delete_sm_db
from templates.Funtions_Utils import create_label, create_button, create_stringvar, create_Combobox, create_entry, \
    create_date_entry

import json


def search_employee(emps_data, emp_key: int | str):
    if isinstance(emp_key, str):
        employee_out = None
        for emp in emps_data:
            emp_name = emp[1].lower() + " " + emp[2].lower()
            if emp_name in emp_key.lower():
                employee_out = emp[0]
                break
    elif isinstance(emp_key, int):
        employee_out = None
        for emp in emps_data:
            if emp[0] == emp_key:
                employee_out = emp[1].title() + " " + emp[2].title()
                break
    else:
        employee_out = None
    return employee_out


def search_client(clients_data, client_key: int | str):
    if isinstance(client_key, str):
        client_out = None
        for client in clients_data:
            client_name = client[1].lower()
            if client_name in client_key.lower():
                client_out = client[0]
                break
    elif isinstance(client_key, int):
        client_out = None
        for client in clients_data:
            if client[0] == client_key:
                client_out = client[1]
                break
    else:
        client_out = None
    return client_out


def create_dict_sm(info, products):
    id_sm, code, folio, contract, plant, location, client, employee, date, date_limit, status = info
    dict_data = {
        "info": {
            "id": id_sm,
            "sm_code": code,
            "folio": folio,
            "contract": contract,
            "facility": plant,
            "location": location,
            "client_id": client,
            "emp_id": employee,
            "date": date,
            "limit_date": date_limit,
            "status": status,
        }
    }
    products_list = []
    for item in products:
        products_list.append({
            "id": int(item[0]),
            "quantity": float(item[1]),
            "comment": item[2]
        })
    dict_data["items"] = products_list
    return dict_data


class FrameSM(ScrolledFrame):
    def __init__(self, master=None, department="default", settings=None, id_emp=None, **kw):
        super().__init__(master, **kw)
        self.columnconfigure((0, 1), weight=1)
        """----------------------------variables-----------------------------"""
        self.settings = settings
        self.department = department
        self._id_sm_to_edit = None
        self.data_sm = None
        self._id_emp = id_emp
        self.svar_info, svar_test = create_stringvar(2, "")
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
        self.frame_inputs.grid(row=0, column=0, padx=(5, 1), pady=1, sticky="nswe")
        self.frame_inputs.columnconfigure((0, 1), weight=1)
        self.entries = self.create_inputs(self.frame_inputs)
        self.frame_products = FrameSMProdcuts(frame_input_general)
        self.frame_products.grid(row=0, column=1, padx=(2, 5), pady=5, sticky="nswe")
        create_label(self, 2, 0, textvariable=self.svar_info, sticky="n", font=("Helvetica", 15, "bold"))
        """------------------------buttons-----------------------------------"""
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=3, column=0, padx=5, pady=5, sticky="nswe")
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
        create_label(master, 0, 0, text="Informacion", sticky="n", font=("Helvetica", 12, "bold"), columnspan=2)
        create_label(master, 1, 0, text="SM:", sticky="w")
        create_label(master, 2, 0, text="SM code:", sticky="w")
        create_label(master, 3, 0, text="Folio:", sticky="w")
        create_label(master, 4, 0, text="Contrato:", sticky="w")
        create_label(master, 5, 0, text="Planta:", sticky="w")
        create_label(master, 6, 0, text="Ubicación:", sticky="w")
        create_label(master, 7, 0, text="Cliente:", sticky="w")
        create_label(master, 8, 0, text="Empleado:", sticky="w")
        create_label(master, 9, 0, text="Fecha:", sticky="w")
        create_label(master, 10, 0, text="Fecha limite:", sticky="w")
        create_label(master, 11, 0, text="Estatus: ", sticky="w")
        # entries
        emp_list = [emp[1].title() + " " + emp[2].title() for emp in self.employees]
        client_list = [client[1] for client in self.clients]
        entries.append(create_entry(master, row=1, column=1, padx=3, pady=5, sticky="w"))
        entries.append(create_entry(master, row=2, column=1, padx=3, pady=5, sticky="w"))
        entries.append(create_entry(master, row=3, column=1, padx=3, pady=5, sticky="w"))
        entries.append(create_entry(master, row=4, column=1, padx=3, pady=5, sticky="w"))
        entries.append(create_entry(master, row=5, column=1, padx=3, pady=5, sticky="w"))
        entries.append(create_entry(master, row=6, column=1, padx=3, pady=5, sticky="w"))
        entries.append(create_Combobox(master, client_list, 25, row=7, column=1, sticky="w", padx=3, pady=5))
        entries.append(create_Combobox(master, emp_list, 25, row=8, column=1, sticky="w", padx=3, pady=5))
        entries.append(create_date_entry(master, firstweekday=0, dateformat="%Y-%m-%d", row=9, column=1, padx=3, pady=5,
                                         sticky="w"))
        entries.append(
            create_date_entry(master, firstweekday=0, dateformat="%Y-%m-%d", row=10, column=1, padx=3, pady=5,
                              sticky="w"))
        entries.append(
            create_Combobox(master, ["pendiente", "completado"], 15, row=11, column=1, sticky="w", padx=3, pady=5))
        return entries

    def create_buttons(self, master):
        btn_add = create_button(
            master, 0, 0, "Agregar SM", command=self.on_add_click,
            sticky="n", width=15, bootstyle="success")
        btn_update_data = create_button(
            master, 0, 1, "Actualizar SM", command=self.on_update_sm_event,
            sticky="n", width=15)
        btn_reset = create_button(
            master, 0, 2, "Reset", command=self.on_reset_widgets_click,
            sticky="n", width=15)
        btn_update_table = create_button(
            master, 0, 3, "Recargar tablas", command=self.update_table_visual,
            sticky="n", width=15)
        btn_erase_event = create_button(
            master, 0, 4, "Borrar SM", command=self.on_erase_click,
            sticky="n", width=15, bootstyle="danger")
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

    def formart_values_info(self, info, action=0):
        id_sm = info[0] if action != 0 else None
        code = info[1]
        folio = info[2]
        contract = info[3]
        plant = info[4]
        location = info[5]
        client = info[6]
        employee = info[7]
        date = info[8]
        date_limit = info[9]
        status = info[10]
        try:
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") if len(date) > 10 else datetime.strptime(
                date, "%Y-%m-%d")
            date_limit = datetime.strptime(date_limit,
                                           "%Y-%m-%d %H:%M:%S") if len(date_limit) > 10 else datetime.strptime(
                date_limit, "%Y-%m-%d")
            if date > date_limit:
                raise Exception("La fecha de inicio no puede ser mayor a la fecha de fin")
            date = date.strftime("%Y-%m-%d %H:%M:%S") if action != 1 else date
            date_limit = date_limit.strftime("%Y-%m-%d %H:%M:%S") if action != 1 else date_limit
        except Exception as e:
            print(e)
            print("!!!Error con el formato o valores de la fecha¡¡¡")
            return
        try:
            self._id_sm_to_edit = int(id_sm) if action != 0 else None
            status = int(status) if action == 1 else status
            client = int(info[6]) if action == 1 else client
            employee = int(info[7]) if action == 1 else employee
        except ValueError:
            self._id_sm_to_edit = None
            print("!!!Error con los datos ingresados para convertir a ids¡¡¡")
            return
        status_int = 1 if status == "completado" else 0
        employee_out = search_employee(self.employees, employee)
        if employee_out is None:
            self.svar_info.set("!!!Revise los datos del empleado¡¡¡")
            return
        client_out = search_client(self.clients, client)
        if client_out is None:
            self.svar_info.set("!!!Revise los datos del cliente¡¡¡")
            return
        return (self._id_sm_to_edit, code, folio, contract, plant, location, client_out, employee_out, date, date_limit,
                status_int)

    def on_add_click(self):
        out_info, data_products = self.get_entries_values()
        out_info = self.formart_values_info(out_info, action=0)
        if len(data_products) == 0:
            self.svar_info.set("!!!Debe agregar productos¡¡¡")
            return
        dict_data = create_dict_sm(out_info, data_products)
        msg = f"Esto por igresar un nuevo registro. Esta de acuerdo con los datos?"
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, error, result = insert_sm_db(dict_data)
        if flag:
            if error is not None:
                self.svar_info.set(f"{error}")
            else:
                self.svar_info.set(f"SM {result} agregado correctamente")
            time.sleep(1)
            self.update_table_visual()
            self.on_reset_widgets_click()
        else:
            self.svar_info.set(error)

    def on_update_sm_event(self):
        out_info, data_products = self.get_entries_values()
        out_info = self.formart_values_info(out_info, action=2)
        if len(data_products) == 0:
            self.svar_info.set("!!!Debe agregar productos¡¡¡")
            return
        dict_data = create_dict_sm(out_info, data_products)
        dict_data['id_sm'] = dict_data["info"]['id']
        msg = f"Esto por actualizar un registro con id: {dict_data['id_sm']}. Esta de acuerdo con los datos?"
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, error, result = update_sm_db(dict_data)
        if flag:
            if error is not None:
                self.svar_info.set(f"{error}")
            else:
                self.svar_info.set(f"SM actualizado correctamente")
            time.sleep(1)
            self.update_table_visual()
            self.on_reset_widgets_click()
        else:
            self.svar_info.set(error)

    def on_erase_click(self):
        sm_code = self.entries[1].get()
        if self._id_sm_to_edit is None:
            self.svar_info.set("!!!Debe seleccionar un registro¡¡¡")
            return
        msg = f"Esto por eliminar un registro con id: {self._id_sm_to_edit}. Esta de acuerdo con los datos?"
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, error, result = delete_sm_db(self._id_sm_to_edit, sm_code)
        if flag:
            if error is not None:
                self.svar_info.set(f"{error}")
            else:
                self.svar_info.set(f"SM eliminado correctamente")
            time.sleep(1)
            self.update_table_visual()
            self.on_reset_widgets_click()

    def update_table_visual(self):
        self.frame_products.reload_table_products()
        self.table_events.destroy()
        self.table_events = self.create_table(self.frame_table)

    def on_reset_widgets_click(self):
        for item in self.entries:
            if isinstance(item, ttk.Combobox):
                item.set("")
            elif isinstance(item, ttk.Entry):
                item.delete(0, "end")
        self.frame_products.on_reset_click()

    def on_double_click_table_sm(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        id_sm, code, folio, contract, plant, location, client, employee, date, date_limit, items, status = row

        self.on_reset_widgets_click()
        items = json.loads(items)
        items_table = []
        for product in items:
            items_table.append((product["id"], product["quantity"], product["comment"],))
        self.frame_products.put_data_resumen(items_table)
        data_info = self.formart_values_info(
            (id_sm, code, folio, contract, plant, location, client, employee, date, date_limit, status), action=1)
        for index, item in enumerate(self.entries):
            if isinstance(item, ttk.Combobox):
                item.set(data_info[index])
            elif isinstance(item, ttk.Entry):
                item.insert(0, data_info[index])
            elif isinstance(item, ttk.DateEntry):
                self.entries[index].destroy()
                self.entries[index] = create_date_entry(self.frame_inputs, firstweekday=0,
                                                        dateformat="%Y-%m-%d", startdate=data_info[index],
                                                        row=index + 1, column=1, padx=3, pady=5, sticky="w")

    def get_entries_values(self):
        data_products = self.frame_products.get_resumen_table_data()
        out = []
        for entry in self.entries:
            if isinstance(entry, ttk.DateEntry):
                out.append(entry.entry.get())
            else:
                out.append(entry.get())
        return out, data_products


class FrameSMProdcuts(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.columnconfigure((0, 1), weight=1)
        self.svar_info = create_stringvar(1, "")
        self.products, self.columns_products = get_all_sm_products()
        """-------------------------title------------------------------------"""
        create_label(self, 0, 0, text="Editar Productos",
                     font=("Helvetica", 14, "bold"), columnspan=2)
        """-------------------------table------------------------------------"""
        self.frame_tabla_products = ttk.Frame(self)
        self.frame_tabla_products.grid(row=1, column=0, padx=1, pady=5, sticky="nswe")
        self.frame_tabla_products.columnconfigure(0, weight=1)
        create_label(self.frame_tabla_products, 0, 0, text="Productos BD",
                     font=("Helvetica", 11, "bold"))
        self.table_products = self.create_table(self.frame_tabla_products, type_table=1)
        self.frame_resumen = ttk.Frame(self)
        self.frame_resumen.grid(row=2, column=0, padx=1, pady=5, sticky="nswe")
        self.frame_resumen.columnconfigure(0, weight=1)
        create_label(self.frame_resumen, 0, 0, text="Resumen",
                     font=("Helvetica", 12, "bold"))
        self.table_resumen = self.create_table(self.frame_resumen, type_table=2)
        """-------------------Widgets input----------------------------------"""
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=1, padx=1, pady=20, sticky="nswe")
        self.entries = self.create_inputs(frame_inputs)
        """-------------------Widgets buttons--------------------------------"""
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=1, padx=1, pady=20, sticky="nswe")
        frame_buttons.columnconfigure(0, weight=1)
        self.create_buttons(frame_buttons)

    def create_table(self, master, type_table=1, data_resumen=None):
        if type_table == 1:
            table = Tableview(
                master, coldata=self.columns_products,
                rowdata=self.products, paginated=True,
                searchable=True, autofit=True,
                height=5, pagesize=5)
            table.grid(row=1, column=0, padx=10, pady=5, sticky="n")
            table.view.bind("<Double-1>", self.on_double_click_table_products)
        else:
            columns = ["ID", "Cantidad", "Comentario"]
            data_resume = data_resumen if data_resumen is not None else []
            table = Tableview(
                master, coldata=columns,
                rowdata=data_resume, paginated=True,
                searchable=True, autofit=True,
                height=5, pagesize=5)
            table.grid(row=1, column=0, padx=10, pady=5, sticky="n")
            table.view.bind("<Double-1>", self.on_double_click_table_resumen)
        return table

    def on_double_click_table_products(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self.clean_everyting()
        self.entries[0].insert(0, row[0])

    def on_double_click_table_resumen(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        for i, item in enumerate(self.entries):
            item.delete(0, "end")
            item.insert(0, row[i])

    def clean_table_resumen(self):
        self.table_resumen = self.create_table(self.frame_resumen, type_table=2)

    def reload_table_products(self):
        self.table_products.destroy()
        self.products, self.columns_products = get_all_sm_products()
        self.table_products = self.create_table(self.frame_tabla_products, type_table=1)

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
            sticky="n", width=15, bootstyle="success")
        create_button(
            master, 0, 1, "Eliminar", command=self.on_erase_click,
            sticky="n", width=15, bootstyle="danger")
        create_button(
            master, 1, 0, "Actualizar", command=self.on_update_click,
            sticky="n", width=15, columnspan=2)
        create_button(
            master, 2, 0, "Limpiar lista", command=self.on_reset_click,
            sticky="n", width=15, columnspan=2)

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
        self.table_resumen = self.create_table(self.frame_resumen, type_table=2)
        self.clean_everyting()

    def clean_everyting(self):
        for item in self.entries:
            item.delete(0, "end")

    def on_erase_click(self):
        item = self.table_resumen.view.selection()
        if len(item) > 0:
            self.table_resumen.view.delete(self.table_resumen.view.selection()[0])
        self.clean_everyting()

    def get_resumen_table_data(self):
        data = []
        for item in self.table_resumen.view.get_children():
            id_p, quantity, comment = self.table_resumen.view.item(item, "values")
            data.append((id_p, quantity, comment))
        return data

    def put_data_resumen(self, data):
        self.table_resumen.destroy()
        self.table_resumen = self.create_table(self.frame_resumen, type_table=2, data_resumen=data)
