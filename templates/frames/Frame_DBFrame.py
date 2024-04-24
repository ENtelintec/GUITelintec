# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 18/oct./2023  at 10:25 $'

import json
import tkinter as tk
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

import templates.Functions_SQL as fsql
from static.extensions import windows_names_db_frame
from templates.Functions_AuxFiles import get_image_side_menu
from templates.Funtions_Utils import set_dateEntry_new_value, create_widget_input_DB, create_visualizer_treeview, \
    create_btns_DB, set_entry_value, create_button_side_menu, clean_entries


class DBFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        # --------------------------variables-----------------------------------
        self.settings = setting
        self._active_window = None
        self.names_side_menu = windows_names_db_frame
        frame_side_menu = ttk.Frame(self)
        frame_side_menu.grid(row=0, column=0, sticky="nsew")
        self.widgets = self._create_side_menu_widgets(frame_side_menu)
        self.windows_frames = self._create_side_menu_windows()

    def _create_side_menu_widgets(self, master):
        widgets = []
        if len(self.names_side_menu) >= 12:
            scrollbar = ttk.Scrollbar(master, orient="vertical")
            scrollbar.grid(row=0, column=2, sticky="ns")
        for i, window in enumerate(self.names_side_menu):
            widgets.append(
                create_button_side_menu(
                    master, i, 0,
                    text=window,
                    image=get_image_side_menu(window),
                    command=lambda x=window: self._select_frame_by_name(x),
                    columnspan=1)
            )
        return widgets

    def _select_frame_by_name(self, name):
        match name:
            case "none":
                for txt in self.names_side_menu:
                    self.windows_frames[txt].grid_forget()
                self._active_window = None
            case _:
                if self._active_window != name:
                    self.windows_frames[self._active_window].grid_forget() if self._active_window is not None else None
                    self._active_window = name
                    self.windows_frames[name].grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    def _create_side_menu_windows(self):
        windows = {}
        for i, window in enumerate(self.names_side_menu):
            match window:
                case "Encargados":
                    windows[window] = HeadsFrame(self, setting=self.settings)
                    print("heads frame created")
                case "Clientes":
                    windows[window] = CustomersFrame(self, setting=self.settings)
                    print("customers frame created")
                case "Empleados":
                    windows[window] = EmployeesFrame(self, setting=self.settings)
                    print("employees frame created")
                case "Departamentos":
                    windows[window] = DepartmentsFrame(self, setting=self.settings)
                    print("departments frame created")
                case "Proveedores":
                    windows[window] = SuppliersFrame(self, setting=self.settings)
                    print("suppliers frame created")
                case "Productos":
                    windows[window] = ProductsFrame(self, setting=self.settings)
                    print("products frame created")
                case "Ordenes":
                    windows[window] = OrdersFrame(self, setting=self.settings)
                    print("orders frame created")
                case "O. Virtuales":
                    windows[window] = VOrdersFrame(self, setting=self.settings)
                    print("virtual orders frame created")
                case "Chats":
                    windows[window] = ChatsFrame(self, setting=self.settings)
                    print("chats frame created")
                case "Tickets":
                    windows[window] = TicketsFrame(self, setting=self.settings)
                    print("tickets frame created")
                case _:
                    pass
        return windows


class EmployeesFrame(ScrolledFrame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._id_emp_update = None
        # -----------------------label-----------------------
        self.label = ttk.Label(self, text="Employees Table",
                               font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=(5, 20), pady=10, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame, "employees")
        # -----------------------insert button-----------------------
        btns_frame = ttk.Frame(self)
        btns_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        btns_frame.columnconfigure((0, 1, 2, 3), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btns_frame, 1, self._insert_employee,
            self._update_employee, self._delete_employee, self.clean_widgets_emp, width=20)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table Employees")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.employee_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "employees",
            row=1, column=0, style="primary",
            pad_x=25, pad_y=10)
        self.employee_insert.view.bind("<Double-1>", self._emp_selected_table)

    def _emp_selected_table(self, event):
        data = event.widget.item(event.widget.selection()[0], "values")
        print(len(data), data)
        for index, entry in enumerate(self.entries):
            print(index, entry)
            if isinstance(entry, ttk.Combobox):
                entry.set(data[index + 1])
            elif isinstance(entry, ttk.Entry):
                set_entry_value(entry, data[index + 1].upper())
            elif isinstance(entry, ttk.DateEntry):
                if index == 7:
                    entry_date = datetime.strptime(data[index + 1],
                                                   "%Y-%m-%d %H:%M:%S") if data[index + 1] != "None" else datetime.now()
                    self.entries[index + 1] = set_dateEntry_new_value(
                        self.insert_frame, self.entries[index + 1], entry_date.date(),
                        row=3, column=3, padx=5, pady=1, date_format="%Y-%m-%d")
                elif index == 12:
                    print(data[index + 1])
                    if len(data[index + 1]) > 0 and data[index + 1] != "None":
                        departure = json.loads(data[index + 1])
                        entry_date = datetime.strptime(departure["date"],
                                                       "%Y-%m-%d %H:%M:%S") if departure["date"] != "None" else datetime.now()
                        self.entries[index + 1] = set_dateEntry_new_value(
                            self.insert_frame, self.entries[index + 1], entry_date.date(),
                            row=9, column=0, padx=5, pady=1, date_format="%Y-%m-%d")
                        set_entry_value(self.entries[13], departure["reason"])
                    else:
                        self.entries[index + 1] = set_dateEntry_new_value(
                            self.insert_frame, self.entries[index + 1], datetime.now().date(),
                            row=9, column=0, padx=5, pady=1, date_format="%Y-%m-%d")
                        set_entry_value(self.entries[13], "")
                elif index == 14:
                    entry_date = datetime.strptime(data[index + 1],
                                                   "%Y-%m-%d") if data[index + 1] != "None" else datetime.now()
                    self.entries[index + 1] = set_dateEntry_new_value(
                        self.insert_frame, self.entries[index + 1], entry_date.date(),
                        row=9, column=2, padx=5, pady=1, date_format="%Y-%m-%d")

    def _update_table_show(self, data):
        self.employee_insert.grid_forget()
        self.employee_insert, data = create_visualizer_treeview(
            self.visual_frame, "employees", row=1, column=0, style="primary",
            pad_x=25, pad_y=10, data=data)
        self.employee_insert.view.bind("<Double-1>", self._emp_selected_table)

    def get_entries_values(self):
        values = []
        for entry in self.entries:
            if isinstance(entry, ttk.DateEntry):
                values.append(entry.entry.get())
            else:
                values.append(entry.get())
        return values

    def _insert_employee(self):
        values = self.get_entries_values()
        status = values[11]
        if status == "inactivo":
            msg = (f"Are you sure you want to insert the following employee:\n"
                   f"Name: {values[0].upper()}\nLastname: {values[1].upper()}")
        else:
            departure = {"date": "None", "reason": ""}
            msg = f"Are you sure you want to insert the following employee:\n"
            for item in values:
                msg += f"{item.upper()}\n"
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        departure = {"date": values[12], "reason": values[13]}
        email = values[16] + "," + values[17]
        emergency = {"name": values[18], "phone_number": values[19]}
        dict_deps = {"Dirección": 1, "Operaciones": 2, "Administración": 3, "RRHH": 4, "REPSE": 5, "IA": 6, "Otros": 7}
        flag, e, out = fsql.new_employee(
            values[0], values[1], values[2], values[3], values[4], dict_deps[values[5]], values[6], values[7],
            values[8], values[9], values[10], values[11], json.dumps(departure), values[14], values[15], email,
            emergency)
        if flag:
            row = [out, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7],
                   values[8], values[9], values[10], values[11], json.dumps(departure)]
            self.data.append(row)
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"New employee created:\n{out}")
        else:
            Messagebox.show_error(title="Error", message=f"Error creating employee:\n{e}")

    def _update_employee(self):
        (name, lastname, curp, phone, email, department, contract,
         entry_date, rfc, nss, emergency, modality, puesto, status, departure) = self.get_entries_values()
        baja = departure["date"]
        reason = departure["reason"]
        if status == "inactivo":
            msg = (f"Are you sure you want to update the following employee:\n"
                   f"Name: {name}\nLastname: {lastname}\nCurp: {curp}\nPhone: {phone}\n"
                   f"Email: {email}\nDepartment: {department}\nContract: {contract}\n"
                   f"Entry date: {entry_date}\nRfc: {rfc}\nNss: {nss}\n"
                   f"Emergency: {emergency}\nModality: {modality}\nPuesto: {puesto}\n"
                   f"Fecha de baja: {baja}\nComentarios: {reason}")
        else:
            departure = {"date": "None", "reason": ""}
            msg = (f"Are you sure you want to update the following employee:\n"
                   f"Name: {name}\nLastname: {lastname}\nCurp: {curp}\nPhone: {phone}\n"
                   f"Email: {email}\nDepartment: {department}\nContract: {contract}\n"
                   f"Entry date: {entry_date}\nRfc: {rfc}\nNss: {nss}\n"
                   f"Emergency: {emergency}\nModality: {modality}\nPuesto: {puesto}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_employee(
            self._id_emp_update, name, lastname, curp, phone, email, department,
            contract, entry_date, rfc, nss, emergency, modality, puesto, status, departure)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_emp_update:
                    self.data[index] = [
                        self._id_emp_update, name, lastname, phone, department,
                        modality, email, contract, entry_date, rfc, curp,
                        nss, emergency, puesto, status, json.dumps(departure)]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Employee updated")
        else:
            Messagebox.show_error(title="Error", message=f"Error updating employee:\n{e}")

    def _delete_employee(self):
        if self._id_emp_update is None:
            Messagebox.show_error(
                title="Error",
                message="No ha escogido un empleado"
            )
            return
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=f"Are you sure you want to delete the following employee:\n"
                    f"Employee ID: {self._id_emp_update}"
        )
        if answer == "No":
            return
        flag, e, out = fsql.delete_employee(self._id_emp_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_emp_update:
                    self.data.pop(index)
            self._update_table_show(self.data)
            Messagebox.show_info(
                title="Informacion",
                message=f"Employee deleted:\n{out}")
            self.clean_widgets_emp()
        else:
            Messagebox.show_error(
                title="Error",
                message=f"Error deleting employee:\n{e}")

    def clean_widgets_emp(self):
        clean_entries(self.entries)
        self._id_emp_update = None


class CustomersFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._id_cus_update = None
        # -----------------Title---------------
        self.label = ttk.Label(self, text="Customers Table",
                               font=("Helvetica", 32, "bold"))
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # subframe on content frame
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        self.insert_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # widgets on left_frame
        self.entries = create_widget_input_DB(
            self.insert_frame, "customers")
        # insert button customer
        btns_frame = ttk.Frame(self)
        btns_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        btns_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btns_frame,
            table_type=1,
            _command_insert=self._insert_customer,
            _command_update=self._update_customer,
            _command_delete=self._delete_customer,
            width=20
        )
        # subframe on content frame
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(1, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table Customers")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.table_customers, self.data = create_visualizer_treeview(
            self.visual_frame, "customers",
            row=1, column=0)
        self.table_customers.view.bind("<Double-1>", self._get_data_customer)

    def _insert_customer(self):
        name, lastname, phone, email, ciudad = self.get_entries_values()
        msg = (f"Are you sure you want to insert the following customer:\n"
               f"Name: {name}\nLastname: {lastname}\nPhone: {phone}\n"
               f"Email: {email}\nCity: {ciudad}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.insert_customer(name, lastname, phone, email, ciudad)
        if flag:
            self.data.append([out, name, lastname, phone, email, ciudad])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Customer inserted")
            self.clean_widgets_cus()
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting customer:\n{e}")

    def _update_customer(self):
        if self._id_cus_update is None:
            Messagebox.show_error(title="Error", message="Select a customer to update")
            return
        name, lastname, phone, email, ciudad = self.get_entries_values()
        msg = (f"Are you sure you want to update the following customer:\n"
               f"Name: {name}\nLastname: {lastname}\nPhone: {phone}\n"
               f"Email: {email}\nCity: {ciudad}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_customer_DB(
            name, lastname, phone, email, ciudad, self._id_cus_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_cus_update:
                    self.data[index] = [
                        self._id_cus_update, name, lastname, phone, email, ciudad]
                    break
            self._update_table_show(self.data)
        else:
            Messagebox.show_error(title="Error", message=f"Error updating customer:\n{e}")

    def _delete_customer(self):
        if self._id_cus_update is None:
            Messagebox.show_error(title="Error", message="Select a customer to delete")
            return
        msg = (f"Are you sure you want to delete the following customer:\n"
               f"Customer ID: {self._id_cus_update}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.delete_customer_DB(self._id_cus_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_cus_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Customer deleted")
            self.clean_widgets_cus()
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting customer:\n{e}")

    def get_entries_values(self):
        return (self.entries[0].get(), self.entries[1].get(),
                self.entries[2].get(), self.entries[3].get(),
                self.entries[4].get())

    def _update_table_show(self, data):
        self.table_customers.destroy()
        self.table_customers, _ = create_visualizer_treeview(
            self.visual_frame, "customers", row=1, column=0,
            style="success", data=data)
        self.table_customers.bind("<Double-1>", self._get_data_customer)

    def clean_widgets_cus(self):
        clean_entries(self.entries)
        self._id_cus_update = None

    def _get_data_customer(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_cus_update = int(row[0])
        set_entry_value(self.entries[0], row[1])
        set_entry_value(self.entries[1], row[2])
        set_entry_value(self.entries[2], row[3])
        set_entry_value(self.entries[3], row[4])
        set_entry_value(self.entries[4], row[5])


class DepartmentsFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self._id_dep_update = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Departments Table",
                               font=("Helvetica", 32, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe for insert--------------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        self.insert_frame.grid_columnconfigure((0, 1), weight=1)
        # --------------------widgets insert-----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame, "departments")
        # ----------------insert btn_employees---------------
        btns_frame = ttk.Frame(self)
        btns_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        btns_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btns_frame,
            table_type=1,
            _command_insert=self._insert_department,
            _command_update=self._update_department,
            _command_delete=self._delete_department,
            width=20
        )
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(1, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table Departments")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.table_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "departments",
            row=1, column=0, style="success")
        self.table_insert.view.bind("<Double-1>", self._get_data_department)

    def _insert_department(self):
        name, location = self.get_entries_values()
        msg = (f"Are you sure you want to insert the following department:\n"
               f"Name: {name}\nLocation: {location}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.insert_department(name, location)
        if flag:
            self.data.append([out, name, location])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Department inserted")
            self.clean_widgets_dep()
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting department:\n{e}")
        pass

    def _update_department(self):
        name, location = self.get_entries_values()
        msg = (f"Are you sure you want to update the following department:\n"
               f"Name: {name}\nLocation: {location}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_department_DB(name, location, self._id_dep_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_dep_update:
                    self.data[index] = [self._id_dep_update, name, location]
                    break
            self._update_table_show(self.data)
        else:
            Messagebox.show_error(title="Error", message=f"Error updating department:\n{e}")
        self.clean_widgets_dep()
        self._id_dep_update = None

    def _delete_department(self):
        if self._id_dep_update is None:
            Messagebox.show_error(title="Error", message="Select a department to delete")
            return
        msg = (f"Are you sure you want to delete the following department:\n"
               f"Department ID: {self._id_dep_update}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.delete_department_DB(self._id_dep_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_dep_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Department deleted")
            self.clean_widgets_dep()
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting department:\n{e}")
            self.clean_widgets_dep()
            self._id_dep_update = None

    def _update_table_show(self, data):
        self.table_insert.destroy()
        self.table_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "departments", row=1, column=0,
            style="success", data=data)
        self.table_insert.view.bind("<Double-1>", self._get_data_department)

    def clean_widgets_dep(self):
        clean_entries(self.entries)

    def get_entries_values(self):
        return self.entries[0].get(), self.entries[1].get()

    def _get_data_department(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_dep_update = int(row[0])
        set_entry_value(self.entries[0], row[1])
        set_entry_value(self.entries[1], row[2])


class HeadsFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Tabla de Jefes de Departamento", font=("Helvetica", 32, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self._id_heads_update = None
        # ---------------subframe on content frame------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2), weight=1)
        # ---------------widgets for insert-----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame, "heads")
        # ---------------insert btn_employees-------------------
        btns_frame = ttk.Frame(self)
        btns_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        btns_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btns_frame,
            table_type=1,
            _command_insert=self._insert_head,
            _command_update=self._update_head,
            _command_delete=self._delete_head,
            width=20
        )
        # ---------------subframe on content frame---------------
        self.visual_frame = ScrolledFrame(self, autohide=True)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.table_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "heads", row=1, column=0, style="success")
        self.table_insert.view.bind("<Double-1>", self._get_data_head)
        # ---------------subframe for help frame---------------
        self.label_help = ttk.Label(
            self.visual_frame, text="Mirar las sisguientes tablas para referencias de los IDs.")
        self.label_help.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        create_visualizer_treeview(
            self.visual_frame, "departments", row=3, column=0, style="info")
        create_visualizer_treeview(
            self.visual_frame, "employees", row=4, column=0, style="info")

    def _insert_head(self):
        name, department, employee = self.get_entries_values()
        msg = (f"Are you sure you want to insert the following head:\n"
               f"Name: {name}\nEmployee: {employee}\nDepartment: {department}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.insert_head(name, department, employee)
        if flag:
            self.data.append([out, name, department, employee])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Head inserted")
            self.clean_widgets_heads()
            self._id_heads_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting head:\n{e}")
            self.clean_widgets_heads()
            self._id_heads_update = None

    def _update_head(self):
        if self._id_heads_update is None:
            Messagebox.show_error(title="Error", message="Select a head to update")
            return
        name, department, employee = self.get_entries_values()
        msg = (f"Are you sure you want to update the following head:\n"
               f"Name: {name}\nEmployee: {employee}\nDepartment: {department}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_head_DB(name, department, employee, self._id_heads_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_heads_update:
                    self.data[index] = [self._id_heads_update, name, department, employee]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Head updated")
        else:
            Messagebox.show_error(title="Error", message=f"Error updating head:\n{e}")
            self.clean_widgets_heads()
            self._id_heads_update = None

    def _delete_head(self):
        if self._id_heads_update is None:
            Messagebox.show_error(title="Error", message="Select a head to delete")
            return
        msg = (f"Are you sure you want to delete the following head:\n"
               f"Name: {self.entries[1].get()}\nEmployee: {self.entries[2].get()}\n"
               f"Department: {self.entries[0].get()}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.delete_head_DB(self._id_heads_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_heads_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Head deleted")
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting head:\n{e}")
        self.clean_widgets_heads()
        self._id_heads_update = None

    def _get_data_head(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_heads_update = row[0]
        set_entry_value(self.entries[0], row[1])
        set_entry_value(self.entries[1], row[2])
        set_entry_value(self.entries[2], row[3])

    def get_entries_values(self):
        return (self.entries[0].get(), self.entries[1].get(),
                self.entries[2].get())

    def clean_widgets_heads(self):
        clean_entries(self.entries)
        self._id_heads_update = None

    def _update_table_show(self, data):
        self.table_insert.destroy()
        self.table_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "heads", row=1, column=0,
            style="success", data=data)
        self.table_insert.view.bind("<Double-1>", self._get_data_head)


class SuppliersFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._id_supplier_update = None
        self.label = ttk.Label(self, text="Tabla de Proveedores",
                               font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe for insert--------------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1), weight=1)
        # --------------------widgets insert-----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame,
            "suppliers",
        )
        # ----------------insert btn_employees---------------
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nswe")
        btn_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btn_frame,
            table_type=1,
            _command_insert=self._insert_supplier,
            _command_update=self._update_supplier,
            _command_delete=self._delete_supplier,
            width=20
        )
        # ----------------subframe visual-----------------------
        self.visual_frame = ScrolledFrame(self, autohide=True)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(1, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table Suppliers")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.table_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "supplier", row=1, column=0, style="success")
        self.table_insert.view.bind("<Double-1>", self._get_data_supplier)

    def _insert_supplier(self):
        name, location = self.get_entries_values()
        msg = (f"Are you sure you want to insert the following supplier:\n"
               f"Name: {name}\nLocation: {location}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.insert_supplier(name, location)
        if flag:
            self.data.append([out, name, location])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Supplier inserted")
            self.clean_widgets_suppliers()
            self._id_supplier_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting supplier:\n{e}")

    def _update_supplier(self):
        name, location = self.get_entries_values()
        msg = (f"Are you sure you want to update the following supplier:\n"
               f"Name: {name}\nLocation: {location}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_supplier_DB(name, location, self._id_supplier_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_supplier_update:
                    self.data[index] = [self._id_supplier_update, name, location]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Supplier updated")
            self.clean_widgets_suppliers()
            self._id_supplier_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error updating supplier:\n{e}")

    def _delete_supplier(self):
        if self._id_supplier_update is None:
            Messagebox.show_error(title="Error", message="No supplier selected")
            return
        msg = (f"Are you sure you want to delete the following supplier:\n"
               f"Name: {self.entries[0].get()}\nLocation: {self.entries[1].get()}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.delete_supplier_DB(self._id_supplier_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_supplier_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Supplier deleted")
            self.clean_widgets_suppliers()
            self._id_supplier_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting supplier:\n{e}")

    def _get_data_supplier(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_supplier_update = int(row[0])
        set_entry_value(self.entries[0], row[1])
        set_entry_value(self.entries[1], row[2])

    def clean_widgets_suppliers(self):
        for item in self.entries:
            set_entry_value(item, "")

    def get_entries_values(self):
        name = self.entries[0]
        location = self.entries[1]
        return name, location

    def _update_table_show(self, data):
        self.table_insert.destroy()
        self.table_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "supplier", row=1, column=0,
            style="success", data=data)
        self.table_insert.view.bind("<Double-1>", self._get_data_supplier)


class ProductsFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._id_product_update = None
        self.label = ttk.Label(self, text="Tabla de Servicios y Productos",
                               font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame,
            "products",
        )
        # -----------------------insert button-----------------------
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nswe")
        btn_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btn_frame,
            table_type=1,
            _command_insert=self._insert_product,
            _command_update=self._update_product,
            _command_delete=self._delete_product,
            width=20
        )
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(0, weight=1)
        self.ps_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "p_and_s", row=0, column=0,
            style="success")
        self.ps_insert.view.bind("<Double-1>", self._get_data_product)

    def _insert_product(self):
        (name, model, brand, description, price_retail, stock, price_provider,
         support, service, categories, img_url, id_ps) = self.get_entries_values()
        id_ps = int(id_ps) if id_ps != "" else None
        support = int(support)
        service = int(service)
        if id_ps is None:
            return
        msg = (f"Are you sure you want to insert the following product:\n"
               f"Name: {name}\nModel: {model}\nBrand: {brand}\n"
               f"Description: {description}\nPrice retail: {price_retail}\n"
               f"Stock: {stock}\nPrice provider: {price_provider}\n"
               f"Support: {support}\nService: {service}\n"
               f"Categories: {categories}\nImg url: {img_url}\n"
               f"Id PS: {id_ps}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.insert_product_and_service(
            id_ps, name, model, brand, description, price_retail, stock,
            price_provider, support, service, categories, img_url)
        if flag:
            out = [id_ps, name, model, brand, description, price_retail, stock,
                   price_provider, support, service, categories, img_url]
            self.data.append(out)
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Product inserted")
            self.clean_widgets_products()
            self._id_product_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting product:\n{e}")

    def _update_product(self):
        (name, model, brand, description, price_retail, stock, price_provider,
         support, service, categories, img_url, id_ps) = self.get_entries_values()
        id_ps = int(id_ps) if id_ps != "" else None
        support = int(support)
        service = int(service)
        if id_ps is None:
            return
        msg = (f"Are you sure you want to update the following product:\n"
               f"Name: {name}\nModel: {model}\nBrand: {brand}\n"
               f"Description: {description}\nPrice retail: {price_retail}\n"
               f"Stock: {stock}\nPrice provider: {price_provider}\n"
               f"Support: {support}\nService: {service}\n"
               f"Categories: {categories}\nImg url: {img_url}\n"
               f"Id PS: {id_ps}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_product_and_service(
            id_ps, name, model, brand, description, price_retail, stock,
            price_provider, support, service, categories, img_url)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_ps:
                    self.data[index] = [id_ps, name, model, brand, description, price_retail, stock,
                                        price_provider, support, service, categories, img_url]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Product updated")
            self.clean_widgets_products()
            self._id_product_update = None

    def _delete_product(self):
        if self._id_product_update is None:
            return
        id_ps = self._id_product_update
        msg = (f"Are you sure you want to delete the following product:\n"
               f"Id PS: {id_ps}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.delete_product_and_service(id_ps)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_ps:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Product deleted")
            self.clean_widgets_products()
            self._id_product_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting product:\n{e}")
            return

    def _get_data_product(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_product_update = int(row[0])
        set_entry_value(self.entries[0], row[1])
        set_entry_value(self.entries[1], row[2])
        set_entry_value(self.entries[2], row[3])
        set_entry_value(self.entries[3], row[4])
        set_entry_value(self.entries[4], row[5])
        set_entry_value(self.entries[5], row[6])
        set_entry_value(self.entries[6], row[7])
        self.entries[7].set(int(row[8]))
        self.entries[8].set(int(row[9]))
        set_entry_value(self.entries[9], row[10])
        set_entry_value(self.entries[10], row[11])
        set_entry_value(self.entries[11], row[0])

    def get_entries_values(self):
        out = []
        for item in self.entries:
            out.append(item.get())
        return out

    def clean_widgets_products(self):
        for index, item in self.entries:
            if index in [7, 8]:
                item.set(0)
            else:
                set_entry_value(item, "")

    def _update_table_show(self, data):
        self.ps_insert.destroy()
        self.ps_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "p_and_s", row=0, column=0,
            style="success", data=data)
        self.ps_insert.view.bind("<Double-1>", self._get_data_product)


class OrdersFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Orders table",
                               font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self._id_order_update = None
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame,
            "orders",
        )
        # -----------------------buttons-----------------------
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nswe")
        btn_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btn_frame,
            table_type=1,
            _command_insert=self._insert_order(),
            _command_update=self._update_order(),
            _command_delete=self._delete_order(),
            width=20
        )
        # -----------------------subframe visual-----------------------
        self.visual_frame = ScrolledFrame(self, autohide=True)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table of orders")
        self.label_table1.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.order_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "orders", row=1, column=0, style="success")
        self.order_insert.view.bind("<Double-1>", self._get_data_order)
        ttk.Label(self.visual_frame,
                  text="See the next table for available customers and employees").grid(
            row=2, column=0, padx=10, pady=10, sticky="w")
        create_visualizer_treeview(
            self.visual_frame, "customers", row=3, column=0, style="info")
        create_visualizer_treeview(
            self.visual_frame, "employees", row=4, column=0, style="info")

    def _insert_order(self):
        (id_order, id_product, quantity, date_order, id_customer, id_employee) = self.get_entries_values()
        id_order = int(id_order) if id_order != "" else None
        if id_order is None:
            return
        date_order = datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S") if date_order != "None" else datetime.now()
        msg = (f"Are you sure you want to insert the following order:\n"
               f"Id order: {id_order}\n"
               f"Id product: {id_product}\n"
               f"Quantity: {quantity}\n"
               f"Date order: {date_order}\n"
               f"Id customer: {id_customer}\n"
               f"Id employee: {id_employee}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.insert_order(
            id_order, id_product, quantity, date_order, id_customer, id_employee)
        if flag:
            self.data.append([id_order, id_product, quantity, date_order, id_customer, id_employee])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Order inserted")
            self.clean_widgets_orders()
            self._id_order_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting order:\n{e}")
            return

    def _update_order(self):
        (id_order, id_product, quantity, date_order, id_customer, id_employee) = self.get_entries_values()
        if self._id_order_update is None:
            return
        date_order = datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S") if date_order != "None" else datetime.now()
        msg = (f"Are you sure you want to update the following order:\n"
               f"Id order: {id_order}\n"
               f"Id product: {id_product}\n"
               f"Quantity: {quantity}\n"
               f"Date order: {date_order}\n"
               f"Id customer: {id_customer}\n"
               f"Id employee: {id_employee}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_order_db(
            id_order, id_product, quantity, date_order, id_customer, id_employee)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_order_update:
                    self.data[index] = [id_order, id_product, quantity, date_order, id_customer, id_employee]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Order updated")
            self.clean_widgets_orders()
            self._id_order_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error updating order:\n{e}")
            return

    def _delete_order(self):
        if self._id_order_update is None:
            return
        msg = (f"Are you sure you want to delete the following order:\n"
               f"Id order: {self._id_order_update}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = fsql.delete_order_db(self._id_order_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_order_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Order deleted")
            self.clean_widgets_orders()
            self._id_order_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting order:\n{e}")
            return
        pass

    def get_entries_values(self):
        out = []
        for item in self.entries:
            if isinstance(item, ttk.Entry) or isinstance(item, ttk.IntVar):
                out.append(item.get())
            elif isinstance(item, ttk.DateEntry):
                out.append(item.entry.get())
        return out

    def _get_data_order(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_order_update = int(row[0])
        for index, item in enumerate(self.entries):
            if isinstance(item, ttk.Entry):
                set_entry_value(item, row[index])
            elif isinstance(item, ttk.IntVar):
                item.set(int(row[index]))
            elif isinstance(item, ttk.DateEntry):
                set_dateEntry_new_value(
                    self.insert_frame, item, datetime.now(),
                    1, 3, 5, 1, date_format="%Y-%m-%d")

    def _update_table_show(self, data):
        self.order_insert.destroy()
        self.order_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "orders", row=1, column=0, style="success", data=data)
        self.order_insert.view.bind("<Double-1>", self._get_data_order)

    def clean_widgets_orders(self):
        for item in self.entries:
            if isinstance(item, ttk.Entry):
                item.delete(0, tk.END)
            elif isinstance(item, ttk.IntVar):
                item.set(0)
        self._id_order_update = None


class VOrdersFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Virtual Orders table",
                               font=("Helvetica", 30, "bold"), )
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self._id_vorder_update = None
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.entries = create_widget_input_DB(self.insert_frame, "vorders")
        # -----------------------insert button-----------------------
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nswe")
        btn_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btn_frame,
            table_type=1,
            _command_insert=self._insert_vorder(),
            _command_update=self._update_vorder(),
            _command_delete=self._delete_vorder(),
            width=20
        )
        # -----------------------subframe visual-----------------------
        self.visual_frame = ScrolledFrame(self, autohide=True)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table of virtual orders")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.vorders_insert, self.data = create_visualizer_treeview(self.visual_frame, "v_orders", row=1, column=0,
                                                                    style="success")
        self.vorders_insert.view.bind("<Double-1>", self._get_data_vorder)

    def _insert_vorder(self):
        (id_vorder, products, date_vorder, id_customer, id_employee, chat_id) = self.get_entries_values()
        id_vorder = int(id_vorder) if id_vorder != "" else None
        if id_vorder is None:
            return
        date_vorder = datetime.strptime(date_vorder, "%Y-%m-%d %H:%M:%S") if date_vorder != "None" else datetime.now()
        msg = (f"Are you sure you want to insert the following virtual order:\n"
               f"Id virtual order: {id_vorder}\n"
               f"Id product: {products}\n"
               f"Date virtual order: {date_vorder}\n"
               f"Id customer: {id_customer}\n"
               f"Id employee: {id_employee}\n"
               f"Chat ID: {chat_id}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, e, out = fsql.insert_vorder_db(
            id_vorder, products, date_vorder, id_customer, id_employee, chat_id)
        if flag:
            self.data.append([id_vorder, products, date_vorder, id_customer, id_employee, chat_id])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Virtual order inserted")
            self.clean_widgets_orders()
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting virtual order:\n{e}")
            return

    def _update_vorder(self):
        (id_vorder, products, date_vorder, id_customer, id_employee, chat_id) = self.get_entries_values()

        if self._id_vorder_update is None:
            return
        id_vorder = self._id_vorder_update
        date_vorder = datetime.strptime(date_vorder, "%Y-%m-%d %H:%M:%S") if date_vorder != "None" else datetime.now()
        msg = (f"Are you sure you want to update the following virtual order:\n"
               f"Id virtual order: {id_vorder}\n"
               f"Id product: {products}\n"
               f"Date virtual order: {date_vorder}\n"
               f"Id customer: {id_customer}\n"
               f"Id employee: {id_employee}\n"
               f"Chat ID: {chat_id}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, e, out = fsql.update_vorder_db(
            id_vorder, products, date_vorder, id_customer, id_employee, chat_id)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_vorder:
                    self.data[index] = [id_vorder, products, date_vorder, id_customer, id_employee, chat_id]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Virtual order updated")
            self.clean_widgets_orders()
            self._id_vorder_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error updating virtual order:\n{e}")
            return

    def _delete_vorder(self):
        (id_vorder, products, date_vorder, id_customer, id_employee, chat_id) = self.get_entries_values()
        if self._id_vorder_update is None:
            return
        id_vorder = self._id_vorder_update
        date_vorder = datetime.strptime(date_vorder, "%Y-%m-%d %H:%M:%S") if date_vorder != "None" else datetime.now()
        msg = (f"Are you sure you want to delete the following virtual order:\n"
               f"Id virtual order: {id_vorder}\n"
               f"Id product: {products}\n"
               f"Date virtual order: {date_vorder}\n"
               f"Id customer: {id_customer}\n"
               f"Id employee: {id_employee}\n"
               f"Chat ID: {chat_id}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, e, out = fsql.delete_vorder_db(
            id_vorder)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_vorder:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Virtual order deleted")
            self.clean_widgets_orders()
            self._id_vorder_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting virtual order:\n{e}")
            return

    def get_entries_values(self):
        out = []
        for item in self.entries:
            if isinstance(item, ttk.Entry) or isinstance(item, ttk.IntVar):
                out.append(item.get())
            elif isinstance(item, ttk.DateEntry):
                out.append(item.entry.get())
        return out

    def _update_table_show(self, data):
        self.vorders_insert.destroy()
        self.vorder_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "v_orders", row=1, column=0, style="success", data=data)
        self.vorder_insert.view.bind("<Double-1>", self._get_data_vorder)

    def clean_widgets_orders(self):
        for item in self.entries:
            if isinstance(item, ttk.Entry):
                item.delete(0, tk.END)
            elif isinstance(item, ttk.IntVar):
                item.set(0)
        self._id_vorder_update = None

    def _get_data_vorder(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_vorder_update = int(row[0])
        for index, item in enumerate(self.entries):
            if isinstance(item, ttk.Entry):
                set_entry_value(item, row[index])
            elif isinstance(item, ttk.IntVar):
                item.set(int(row[index]))
            elif isinstance(item, ttk.DateEntry):
                set_dateEntry_new_value(
                    self.insert_frame, item, datetime.now(),
                    1, 2, 5, 1, date_format="%Y-%m-%d")


class TicketsFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Tickets table", font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self._id_ticket_update = None
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        # -----------------widgets on left_frame----------------------
        self.entries = create_widget_input_DB(self.insert_frame,
                                              "tickets")
        # -----------------------buttons-----------------------
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nswe")
        btn_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btn_frame,
            table_type=1,
            _command_insert=self._insert_tickets,
            _command_update=self._update_tickets,
            _command_delete=self._delete_tickets,
            width=20
        )
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table of tickets")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.tickets_insert, self.data = create_visualizer_treeview(self.visual_frame, "tickets", row=1, column=0,
                                                                    style="success")
        self.tickets_insert.view.bind("<Double-1>", self._get_data_ticket)

    def _insert_tickets(self):
        (id_t, content, is_retrieved, is_answered, timestamp) = self.get_entries_values()
        id_t = int(id_t) if id_t != "" else None
        if id_t is None:
            return
        is_retrieved = int(is_retrieved)
        is_answered = int(is_answered)
        msg = (f"Are you sure you want to insert the following ticket:\n"
               f"Id ticket: {id_t}\n"
               f"Content: {content}\n"
               f"Is retrieved: {is_retrieved}\n"
               f"Is answered: {is_answered}\n"
               f"Timestamp: {timestamp}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, e, out = fsql.insert_ticket_db(
            id_t, content, is_retrieved, is_answered, timestamp)
        if flag:
            self.data.append([id_t, content, is_retrieved, is_answered, timestamp])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Ticket inserted")
            self.clean_widgets_orders()
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting ticket:\n{e}")
            return

    def _update_tickets(self):
        (id_t, content, is_retrieved, is_answered, timestamp) = self.get_entries_values()
        if self._id_ticket_update is None:
            return
        id_t = self._id_ticket_update
        is_retrieved = int(is_retrieved)
        is_answered = int(is_answered)
        msg = (f"Are you sure you want to update the following ticket:\n"
               f"Id ticket: {id_t}\n"
               f"Content: {content}\n"
               f"Is retrieved: {is_retrieved}\n"
               f"Is answered: {is_answered}\n"
               f"Timestamp: {timestamp}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, e, out = fsql.update_ticket_db(
            id_t, content, is_retrieved, is_answered, timestamp)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_t:
                    self.data[index] = [id_t, content, is_retrieved, is_answered, timestamp]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Ticket updated")
            self.clean_widgets_orders()
            self._id_ticket_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error updating ticket:\n{e}")
            return

    def _delete_tickets(self):
        if self._id_ticket_update is None:
            return
        id_t = self._id_ticket_update
        msg = (f"Are you sure you want to delete the following ticket:\n"
               f"Id ticket: {id_t}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, e, out = fsql.delete_ticket_db(id_t)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_t:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Ticket deleted")
            self.clean_widgets_orders()
            self._id_ticket_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting ticket:\n{e}")
            return

    def get_entries_values(self):
        out = []
        for item in self.entries:
            if isinstance(item, ttk.Entry) or isinstance(item, ttk.IntVar):
                out.append(item.get())
            elif isinstance(item, ttk.DateEntry):
                out.append(item.entry.get())
        return out

    def _update_table_show(self, data):
        self.tickets_insert.destroy()
        self.tickets_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "tickets", row=1, column=0, style="success", data=data)
        self.tickets_insert.view.bind("<Double-1>", self._get_data_ticket)

    def clean_widgets_orders(self):
        for item in self.entries:
            if isinstance(item, ttk.Entry):
                item.delete(0, tk.END)
            elif isinstance(item, ttk.IntVar):
                item.set(0)
        self._id_ticket_update = None

    def _get_data_ticket(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_ticket_update = int(row[0])
        for index, item in enumerate(self.entries):
            if isinstance(item, ttk.Entry):
                set_entry_value(item, row[index])
            elif isinstance(item, ttk.IntVar):
                item.set(int(row[index]))
            elif isinstance(item, ttk.DateEntry):
                set_dateEntry_new_value(
                    self.insert_frame, item, datetime.now(),
                    1, 2, 5, 1, date_format="%Y-%m-%d")


class ChatsFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.label = ttk.Label(self, text="Chats table", font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        ps_chats = create_visualizer_treeview(self.visual_frame, "chats", row=0, column=0, style="success")
