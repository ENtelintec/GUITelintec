# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 18/oct./2023  at 10:25 $'

import json
import tkinter as tk
from datetime import datetime

import customtkinter as ctk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

import templates.Functions_SQL as fsql
from templates.Functions_AuxFiles import get_image_side_menu
from templates.Funtions_Utils import set_dateEntry_new_value, create_widget_input_DB, create_visualizer_treeview, \
    create_btns_DB, set_entry_value, create_button_side_menu, clean_entries


def load_data_tables(names: list[str]):
    out = []
    for name in names:
        match name:
            case "customers":
                my_result = fsql.get_customers()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "employees":
                my_result = fsql.get_employees()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "departments":
                my_result = fsql.get_departments()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "heads":
                my_result = fsql.get_heads()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "suppliers":
                my_result = fsql.get_supplier()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "products":
                my_result = fsql.get_p_and_s()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "chats":
                my_result = fsql.get_chats_w_limit()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "Users":
                my_result = fsql.get_users()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "orders":
                my_result = fsql.get_orders()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "v_orders":
                my_result = fsql.get_v_orders()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "tickets":
                my_result = fsql.get_tickets()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case "purchases":
                my_result = fsql.get_purchases()
                out.append(my_result) if len(my_result) > 0 else out.append([])
            case _:
                pass
    return out


class EmployeesFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._id_emp_update = None
        # -----------------------label-----------------------
        self.label = ttk.Label(self, text="Employees Table",
                               font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame, "employees")
        # -----------------------insert button-----------------------
        btns_frame = ttk.Frame(self)
        btns_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        btns_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btns_frame, 1, self._insert_employee,
            self._update_employee, self._delete_employee, width=20)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ScrolledFrame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table Employees")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.employee_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "employees",
            row=1, column=0, style="primary",
            pad_x=25, pad_y=10)
        self.employee_insert.view.bind("<Double-1>", self._emp_selected)
        self.label_table_show = ttk.Label(self.visual_frame,
                                          text="See the next table for available departments")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        create_visualizer_treeview(self.visual_frame, "departments", row=3, column=0, style="info", pad_x=25, pad_y=10)

    def _emp_selected(self, event):
        data = event.widget.item(event.widget.selection()[0], "values")
        (id_emp, name, lastname, phone, department, modality, email,
         contract, entry_date, rfc, curp, nss, emergency, puesto, status, baja) = data
        self._id_emp_update = int(id_emp)
        set_entry_value(self.entries[0], name.title())
        set_entry_value(self.entries[1], lastname.title())
        set_entry_value(self.entries[2], curp)
        set_entry_value(self.entries[3], phone)
        set_entry_value(self.entries[4], email)
        set_entry_value(self.entries[5], department)
        set_entry_value(self.entries[12], puesto)
        self.entries[6].set(modality)
        set_entry_value(self.entries[7], contract)
        entry_date = datetime.strptime(entry_date, "%Y-%m-%d %H:%M:%S") if entry_date != "None" else datetime.now()
        self.entries[8] = set_dateEntry_new_value(
            self.insert_frame, self.entries[8], entry_date.date(),
            row=5, column=0, padx=5, pady=1)
        set_entry_value(self.entries[9], rfc)
        set_entry_value(self.entries[11], nss)
        set_entry_value(self.entries[10], emergency)
        self.entries[13].set(status)
        if len(baja) > 0 and baja != "None":
            baja = json.loads(baja)
            set_dateEntry_new_value(
                self.insert_frame, self.entries[14],
                datetime.strptime(baja["date"], "%Y-%m-%d %H:%M:%S"),
                row=7, column=2, padx=5, pady=5)
            set_entry_value(self.entries[15], baja["reason"])
        else:
            set_dateEntry_new_value(
                self.insert_frame, self.entries[14],
                datetime.now(),
                row=7, column=2, padx=5, pady=5
            )
            self.entries[15].delete(0, "end")

    def _update_table_show(self, data):
        self.employee_insert.grid_forget()
        self.employee_insert, data = create_visualizer_treeview(
            self.visual_frame, "employees", row=1, column=0, style="primary",
            pad_x=25, pad_y=10, data=data)
        self.employee_insert.view.bind("<Double-1>", self._emp_selected)

    def get_entries_values(self):
        name = self.entries[0].get()
        lastname = self.entries[1].get()
        curp = self.entries[2].get()
        phone = self.entries[3].get()
        email = self.entries[4].get()
        department = self.entries[5].get()
        contract = self.entries[8].get()
        entry_date = self.entries[8].entry.get()
        rfc = self.entries[9].get()
        nss = self.entries[11].get()
        emergency = self.entries[10].get()
        modality = self.entries[6].get()
        puesto = self.entries[12].get()
        status = self.entries[13].get()
        baja = self.entries[14].entry.get()
        reason = self.entries[15].get()
        departure = {"date": baja, "reason": reason}
        return (name, lastname, curp, phone, email, department, contract,
                entry_date, rfc, nss, emergency, modality, puesto, status, departure)

    def _insert_employee(self):
        (name, lastname, curp, phone, email, department, contract,
         entry_date, rfc, nss, emergency, modality, puesto, status,
         departure) = self.get_entries_values()
        baja = departure["date"]
        reason = departure["reason"]
        if status == "inactivo":
            msg = (f"Are you sure you want to insert the following employee:\n"
                   f"Name: {name}\nLastname: {lastname}\nCurp: {curp}\nPhone: {phone}\n"
                   f"Email: {email}\nDepartment: {department}\nContract: {contract}\n"
                   f"Entry date: {entry_date}\nRfc: {rfc}\nNss: {nss}\n"
                   f"Emergency: {emergency}\nModality: {modality}\nPuesto: {puesto}\n"
                   f"Fecha de baja: {baja}\nComentarios: {reason}")
        else:
            departure = {"date": "None", "reason": ""}
            msg = (f"Are you sure you want to insert the following employee:\n"
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
        flag, e, out = fsql.new_employee(
            name, lastname, curp, phone, email, department, contract, entry_date,
            rfc, nss, emergency, modality, puesto, status, departure)
        if flag:
            row = [out, name, lastname, phone, department, modality, email,
                   contract, entry_date, rfc, curp, nss, emergency, puesto, "activo",
                   json.dumps(departure)]
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
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
            _command_insert=self._insert_product(),
            _command_update=self._update_product(),
            _command_delete=self._delete_product(),
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
        flag, e, out = fsql.insert_product_DB(
            name, model, brand, description, price_retail, stock, price_provider,
            support, service, categories, img_url, id_ps)
        if flag:
            self.data.append(out)
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Product inserted")
            self.clean_widgets_products()
            self._id_product_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting product:\n{e}")

    def _update_product(self):
        pass

    def _delete_product(self):
        pass

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


class OrdersFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Orders table",
                               text_color="#fff",
                               font=ttk.Font(size=30, weight="bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self, fg_color="#02021A")
        self.insert_frame.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.label1 = ttk.Label(self.insert_frame, text="ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label2 = ttk.Label(self.insert_frame, text="Product ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label3 = ttk.Label(self.insert_frame, text="Quantity", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label4 = ttk.Label(self.insert_frame, text="Date order", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label5 = ttk.Label(self.insert_frame, text="Customer ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label6 = ttk.Label(self.insert_frame, text="Employee ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label1.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        self.label4.grid(row=0, column=3, padx=1, pady=1, sticky="nsew")
        self.label5.grid(row=2, column=0, padx=1, pady=1, sticky="nsew")
        self.label6.grid(row=2, column=1, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1 = ttk.Entry(self.insert_frame, placeholder_text="ID",
                                height=25, width=150)
        self.entry2 = ttk.Entry(self.insert_frame, width=150)
        self.entry3 = ttk.Entry(self.insert_frame, placeholder_text="1",
                                height=25, width=130)
        self.entry4 = ttk.DateEntry(self.insert_frame)
        self.entry5 = ttk.Entry(self.insert_frame, placeholder_text="#",
                                height=25, width=70)
        self.entry6 = ttk.Entry(self.insert_frame, placeholder_text="#",
                                height=25, width=90)
        self.entry1.grid(row=1, column=0, padx=5, pady=1)
        self.entry2.grid(row=1, column=1, padx=5, pady=1)
        self.entry3.grid(row=1, column=2, padx=5, pady=1)
        self.entry4.grid(row=1, column=3, padx=5, pady=1)
        self.entry5.grid(row=3, column=0, padx=5, pady=1)
        self.entry6.grid(row=3, column=1, padx=5, pady=1)
        # -----------------------insert button-----------------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.ScrollableFrame(self, fg_color="transparent",
                                                width=750, height=400,
                                                border_color="#656565",
                                                border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table of orders",
                                      text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        order_insert = create_visualizer_treeview(self.visual_frame, "orders", row=1, column=0, style="success")
        self.label_table_show = ttk.Label(self.visual_frame,
                                          text="See the next table for available customers and employees",
                                          text_color="#fff")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cus_tab_v = create_visualizer_treeview(self.visual_frame, "customers", row=3, column=0, style="info")
        self.subframe_table1 = ttk.ScrollableFrame(self.visual_frame, fg_color="transparent",
                                                   orientation="horizontal",
                                                   width=750, height=200, )
        self.subframe_table1.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        self.subframe_table1.columnconfigure(0, weight=1)
        emp_tab_v = create_visualizer_treeview(self.subframe_table1, "employees", row=4, column=0, style="info")


class VOrdersFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Virtual Orders table",
                               text_color="#fff",
                               font=ttk.Font(size=30, weight="bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self, fg_color="#02021A")
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.label1 = ttk.Label(self.insert_frame, text="ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label2 = ttk.Label(self.insert_frame, text="Product ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label3 = ttk.Label(self.insert_frame, text="Quantity", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label4 = ttk.Label(self.insert_frame, text="Date order", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label5 = ttk.Label(self.insert_frame, text="Customer ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label6 = ttk.Label(self.insert_frame, text="Employee ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label7 = ttk.Label(self.insert_frame, text="Chat ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label1.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        self.label4.grid(row=0, column=3, padx=1, pady=1, sticky="nsew")
        self.label5.grid(row=2, column=0, padx=1, pady=1, sticky="nsew")
        self.label6.grid(row=2, column=1, padx=1, pady=1, sticky="nsew")
        self.label7.grid(row=2, column=2, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1 = ttk.Entry(self.insert_frame, placeholder_text="ID",
                                height=25, width=150)
        self.entry2 = ttk.Entry(self.insert_frame, placeholder_text="json text",
                                height=25, width=150)
        self.entry3 = ttk.Entry(self.insert_frame, placeholder_text="1",
                                height=25, width=130)
        self.entry4 = ttk.DateEntry(self.insert_frame)
        self.entry5 = ttk.Entry(self.insert_frame, placeholder_text="#",
                                height=25, width=70)
        self.entry6 = ttk.Entry(self.insert_frame, placeholder_text="#",
                                height=25, width=90)
        self.entry7 = ttk.Entry(self.insert_frame, placeholder_text="#",
                                height=25, width=90)
        self.entry1.grid(row=1, column=0, padx=5, pady=1)
        self.entry2.grid(row=1, column=1, padx=5, pady=1)
        self.entry3.grid(row=1, column=2, padx=5, pady=1)
        self.entry4.grid(row=1, column=3, padx=5, pady=1)
        self.entry5.grid(row=3, column=0, padx=5, pady=1)
        self.entry6.grid(row=3, column=1, padx=5, pady=1)
        self.entry7.grid(row=3, column=2, padx=5, pady=1)
        # -----------------------insert button-----------------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.ScrollableFrame(self, fg_color="transparent",
                                                border_color="#656565",
                                                border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table of virtual orders",
                                      text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ps_insert = create_visualizer_treeview(self.visual_frame, "v_orders", row=1, column=0, style="success")
        self.label_table_show = ttk.Label(self.visual_frame,
                                          text="See the next table for available departments",
                                          text_color="#fff")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cus_tab_v = create_visualizer_treeview(self.visual_frame, "customers", row=3, column=0, style="info")
        self.subframe_table1 = ttk.ScrollableFrame(self.visual_frame, fg_color="transparent",
                                                   orientation="horizontal")
        self.subframe_table1.grid(row=4, column=0, sticky="nsew")
        self.subframe_table1.columnconfigure(0, weight=1)
        emp_tab_v = create_visualizer_treeview(self.subframe_table1, "employees", row=4, column=0, style="info")


class PurchasesFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Purchases table",
                               text_color="#fff",
                               font=ttk.Font(size=30, weight="bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self, fg_color="#02021A")
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2), weight=1)
        # -----------------widgets on left_frame----------------------
        self.label1 = ttk.Label(self.insert_frame, text="ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label2 = ttk.Label(self.insert_frame, text="Product ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label3 = ttk.Label(self.insert_frame, text="Quantity", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label4 = ttk.Label(self.insert_frame, text="Date purchase", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label5 = ttk.Label(self.insert_frame, text="Supplier ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label1.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        self.label4.grid(row=2, column=0, padx=1, pady=1, sticky="nsew")
        self.label5.grid(row=2, column=1, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1 = ttk.Entry(self.insert_frame, placeholder_text="ID",
                                height=25, width=150)
        self.entry2 = ttk.Entry(self.insert_frame, placeholder_text="####",
                                height=25, width=150)
        self.entry3 = ttk.Entry(self.insert_frame, placeholder_text="1",
                                height=25, width=130)
        self.entry4 = ttk.DateEntry(self.insert_frame)
        self.entry5 = ttk.Entry(self.insert_frame, placeholder_text="#",
                                height=25, width=70)

        self.entry1.grid(row=1, column=0, padx=5, pady=1)
        self.entry2.grid(row=1, column=1, padx=5, pady=1)
        self.entry3.grid(row=1, column=2, padx=5, pady=1)
        self.entry4.grid(row=3, column=0, padx=5, pady=1)
        self.entry5.grid(row=3, column=1, padx=5, pady=1)
        # -----------------------insert button-----------------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.ScrollableFrame(self, fg_color="transparent",
                                                width=750, height=400,
                                                border_color="#656565",
                                                border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table Purchases", text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ps_insert = create_visualizer_treeview(self.visual_frame, "purchases", row=1, column=0, style="success")
        self.label_table_show = ttk.Label(self.visual_frame,
                                          text="See the next table for available departments", text_color="#fff")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cus_tab_v = create_visualizer_treeview(self.visual_frame, "supplier", row=3, column=0, style="info")


class UsersFrame(ttk.Frame):

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Users table", text_color="#fff",
                               font=ttk.Font(size=30, weight="bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self, fg_color="transparent",
                                      border_color="#656565",
                                      border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table of system users", text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ps_insert = create_visualizer_treeview(self.visual_frame, "users", row=1, column=0, style="success")


class TicketsFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Tickets table", text_color="#fff",
                               font=ttk.Font(size=30, weight="bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self, fg_color="#02021A")
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        # -----------------widgets on left_frame----------------------
        self.label1 = ttk.Label(self.insert_frame, text="ID", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label5 = ttk.Label(self.insert_frame, text="Content", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label2 = ttk.Label(self.insert_frame, text="Is retrieved?", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label3 = ttk.Label(self.insert_frame, text="Is answered?", font=ttk.Font(size=12, weight="bold"),
                                text_color="#fff")
        self.label4 = ttk.Label(self.insert_frame, text="Timestamp Creation",
                                font=ttk.Font(size=12, weight="bold"), text_color="#fff")
        self.label1.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        self.label4.grid(row=2, column=0, padx=1, pady=1, sticky="nsew")
        self.label5.grid(row=2, column=1, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1 = ttk.Entry(self.insert_frame, placeholder_text="ID",
                                height=25, width=150)
        switch_var_retrieved = ctk.StringVar(value="True")
        self.entry2 = ttk.Switch(self.insert_frame, variable=switch_var_retrieved,
                                 onvalue="True", offvalue="False",
                                 textvariable=switch_var_retrieved)
        switch_var_answered = ctk.StringVar(value="True")
        self.entry3 = ttk.Switch(self.insert_frame, variable=switch_var_answered,
                                 onvalue="True", offvalue="False",
                                 textvariable=switch_var_answered)
        self.entry4 = ttk.DateEntry(self.insert_frame)
        self.entry5 = ttk.Entry(self.insert_frame, placeholder_text="Content...",
                                height=25, width=300)

        self.entry1.grid(row=1, column=0, padx=5, pady=1)
        self.entry2.grid(row=1, column=1, padx=5, pady=1)
        self.entry3.grid(row=1, column=2, padx=5, pady=1)
        self.entry4.grid(row=3, column=0, padx=5, pady=1)
        self.entry5.grid(row=3, column=1, padx=5, pady=1, columnspan=2)
        # -----------------------insert button-----------------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self, fg_color="transparent",
                                      border_color="#656565",
                                      border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table of tickets",
                                      text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ps_insert = create_visualizer_treeview(self.visual_frame, "tickets", row=1, column=0, style="success")


class ChatsFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.label = ttk.Label(self, text="Chats table", text_color="#fff",
                               font=ttk.Font(size=30, weight="bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.visual_frame = ttk.ScrollableFrame(self, fg_color="transparent",
                                                border_color="#656565",
                                                border_width=2,
                                                orientation="horizontal")
        self.visual_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        ps_insert = create_visualizer_treeview(self.visual_frame, "chats", row=0, column=0, style="success")


class DBFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        # --------------------------variables-----------------------------------
        (self.data_costumers, self.data_employees, self.data_departments,
         self.data_heads, self.data_suppliers, self.data_products) = (
            load_data_tables(['customers', 'employees', 'departments',
                              'heads', 'suppliers', 'products']))
        print("data db loaded")
        # -------------------frame selector table------------------------
        self.table_frame = ScrolledFrame(self, fg_color="#02021A",
                                         scrollbar_fg_color="transparent",
                                         scrollbar_button_color="#02021A")
        self.table_frame.grid(row=0, column=0, pady=10, padx=10, sticky="nswe")
        self.btn_employees = (
            create_button_side_menu(self.table_frame, 0, 0,
                                    text="Employees", image=get_image_side_menu("Empleados"),
                                    command=lambda: self.select_frame_by_name("btn1")))
        self.btn_customers = (
            create_button_side_menu(self.table_frame, 1, 0,
                                    text="Customers", image=get_image_side_menu("Clientes"),
                                    command=lambda: self.select_frame_by_name("btn2")))
        self.btn_departments = (
            create_button_side_menu(self.table_frame, 2, 0,
                                    text="Departments", image=get_image_side_menu("Departamentos"),
                                    command=lambda: self.select_frame_by_name("btn3")))
        self.btn_heads = (
            create_button_side_menu(self.table_frame, 3, 0,
                                    text="Heads", image=get_image_side_menu("Encargados"),
                                    command=lambda: self.select_frame_by_name("btn4")))
        self.btn_suppliers = (
            create_button_side_menu(self.table_frame, 4, 0,
                                    text="Suppliers", image=get_image_side_menu("Proveedores"),
                                    command=lambda: self.select_frame_by_name("btn5")))
        self.btn_products = (
            create_button_side_menu(self.table_frame, 5, 0,
                                    text="Products and services", image=get_image_side_menu("Productos"),
                                    command=lambda: self.select_frame_by_name("btn6")))
        self.btn_orders = (
            create_button_side_menu(self.table_frame, 6, 0,
                                    text="Orders", image=get_image_side_menu("Ordenes"),
                                    command=lambda: self.select_frame_by_name("btn7")))
        self.btn_purchases = (
            create_button_side_menu(self.table_frame, 7, 0,
                                    text="Purchases", image=get_image_side_menu("Compras"),
                                    command=lambda: self.select_frame_by_name("btn8")))
        self.btn_users = (
            create_button_side_menu(self.table_frame, 8, 0,
                                    text="Users", image=get_image_side_menu("Usuarios"),
                                    command=lambda: self.select_frame_by_name("btn9")))
        self.btn_tickets = (
            create_button_side_menu(self.table_frame, 9, 0,
                                    text="Tickets", image=get_image_side_menu("Tickets"),
                                    command=lambda: self.select_frame_by_name("btn10")))
        self.btn_chats = (
            create_button_side_menu(self.table_frame, 10, 0,
                                    text="Chats", image=get_image_side_menu("Chats"),
                                    command=lambda: self.select_frame_by_name("btn11")))
        self.btn_v_orders = (
            create_button_side_menu(self.table_frame, 11, 0,
                                    text="V_Orders", image=get_image_side_menu("O. Virtuales"),
                                    command=lambda: self.select_frame_by_name("btn12")))
        print("side menu widgets created")
        # -------------------------Frame Employees--------------------------
        self.employees = ttk.Frame(self)
        print("employees frame DB created")
        # -------------------------Frame  Customers-------------------------
        self.customers_frame = ttk.Frame(self)
        print("customers frame DB created")
        # -------------------------Frame  departments-------------------------
        self.departments_frame = ttk.Frame(self)
        print("departments frame DB created")
        # -------------------------Frame heads-------------------------
        self.heads_frame = ttk.Frame(self)
        print("heads frame DB created")
        # -------------------------Frame  suppliers-------------------------
        self.suppliers_frame = ttk.Frame(self)
        print("suppliers frame DB created")
        # -------------------------Frame  p and s-------------------------
        self.products_frame = ttk.Frame(self)
        print("products frame DB created")
        # -------------------------Frame Orders-------------------------
        self.orders_frame = ttk.Frame(self)
        print("orders frame DB created")
        # -------------------------Frame V_Orders-------------------------
        self.v_orders_frame = ttk.Frame(self)
        print("v_orders frame DB created")
        # -------------------------Frame purchases-------------------------
        self.purchases_frame = ttk.Frame(self)
        print("purchases frame DB created")
        # -------------------------Frame UsersS-------------------------
        self.users_frame = ttk.Frame(self)
        print("users frame DB created")
        # -------------------------Frame Tickets------------------------
        self.tickets_frame = ttk.Frame(self)
        print("tickets frame DB created")
        # -------------------------Frame  Chats-------------------------
        self.chats_frame = ttk.Frame(self)
        print("chats frame DB created")
        self.select_frame_by_name("none")

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.btn_employees.configure(fg_color=("gray75", "gray25") if name == "btn1" else "transparent")
        self.btn_customers.configure(fg_color=("gray75", "gray25") if name == "btn2" else "transparent")
        self.btn_departments.configure(fg_color=("gray75", "gray25") if name == "btn3" else "transparent")
        self.btn_heads.configure(fg_color=("gray75", "gray25") if name == "btn4" else "transparent")
        self.btn_suppliers.configure(fg_color=("gray75", "gray25") if name == "btn5" else "transparent")
        self.btn_products.configure(fg_color=("gray75", "gray25") if name == "btn6" else "transparent")
        self.btn_orders.configure(fg_color=("gray75", "gray25") if name == "btn7" else "transparent")
        self.btn_purchases.configure(fg_color=("gray75", "gray25") if name == "btn8" else "transparent")
        self.btn_users.configure(fg_color=("gray75", "gray25") if name == "btn9" else "transparent")
        self.btn_tickets.configure(fg_color=("gray75", "gray25") if name == "btn10" else "transparent")
        self.btn_chats.configure(fg_color=("gray75", "gray25") if name == "btn11" else "transparent")
        self.btn_v_orders.configure(fg_color=("gray75", "gray25") if name == "btn12" else "transparent")
        # show selected frame
        match name:
            case "btn1":
                self.hide_all_frame(1)
                self.employees = EmployeesFrame(self)
                self.employees.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn2":
                self.hide_all_frame(2)
                self.customers_frame = CustomersFrame(self)
                self.customers_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn3":
                self.hide_all_frame(3)
                self.departments_frame = DepartmentsFrame(self)
                self.departments_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn4":
                self.hide_all_frame(4)
                self.heads_frame = HeadsFrame(self)
                self.heads_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn5":
                self.hide_all_frame(5)
                self.suppliers_frame = SuppliersFrame(self)
                self.suppliers_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn6":
                self.hide_all_frame(6)
                self.products_frame = ProductsFrame(self)
                self.products_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn7":
                self.hide_all_frame(7)
                self.orders_frame = OrdersFrame(self)
                self.orders_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn8":
                self.hide_all_frame(8)
                self.purchases_frame = PurchasesFrame(self)
                self.purchases_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn9":
                self.hide_all_frame(9)
                self.users_frame = UsersFrame(self)
                self.users_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn10":
                self.hide_all_frame(10)
                self.tickets_frame = TicketsFrame(self)
                self.tickets_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn11":
                self.hide_all_frame(11)
                self.chats_frame = ChatsFrame(self)
                self.chats_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "btn12":
                self.hide_all_frame(12)
                self.v_orders_frame = VOrdersFrame(self)
                self.v_orders_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case _:
                self.hide_all_frame(0)

    def hide_all_frame(self, val: int):
        self.employees.grid_forget() if val != 1 else None
        self.customers_frame.grid_forget() if val != 2 else None
        self.departments_frame.grid_forget() if val != 3 else None
        self.heads_frame.grid_forget() if val != 4 else None
        self.suppliers_frame.grid_forget() if val != 5 else None
        self.products_frame.grid_forget() if val != 6 else None
        self.orders_frame.grid_forget() if val != 6 else None
        self.purchases_frame.grid_forget() if val != 8 else None
        self.users_frame.grid_forget() if val != 9 else None
        self.tickets_frame.grid_forget() if val != 10 else None
        self.chats_frame.grid_forget() if val != 11 else None
        self.v_orders_frame.grid_forget() if val != 12 else None


if __name__ == '__main__':
    app = tk.Tk()
    app.geometry("1300x700")
    db_frame = DBFrame(app, data_tables=load_data_tables(["customers", "employees"]))
    db_frame.grid(row=0, column=1, sticky="nsew", pady=10, padx=10)
    app.mainloop()
