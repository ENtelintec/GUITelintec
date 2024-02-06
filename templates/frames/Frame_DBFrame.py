# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 18/oct./2023  at 10:25 $'

import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import Misc
from tkinter.ttk import Treeview, Style

import customtkinter as ctk
import ttkbootstrap as ttk
from PIL import Image
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

import templates.Functions_SQL as fsql

from static.extensions import IMG_PATH_COLLAPSING
from templates.Functions_AuxFiles import get_image_side_menu


def set_entry_value(entry1_emp, param: str):
    entry1_emp.delete(0, tk.END)
    entry1_emp.insert(0, param)


def create_visualizer_treeview(master: Misc, table: str, rows: int,
                               pad_x: int = 5, pad_y: int = 10,
                               row: int = 0, column: int = 0,
                               style: str = 'primary', data=None) -> Tableview | None:
    match table:
        case "employees":
            columns = ["Id", "Name", "Lastname", "Phone", "Dep.", "Modality", "Email", "Contrato",
                       "Ingreso", "RFC", "CURP", "NSS", "Emg. Info.", "Puesto", "Estatus"]
            data = fsql.get_employees() if data is None else data
        case "customers":
            columns = ["Id", "Name", "Lastname", "Phone", "City", "Email"]
            data = fsql.get_customers() if data is None else data
        case "departments":
            columns = ["Id", "Name", "Location"]
            data = fsql.get_departments() if data is None else data
        case "heads":
            columns = ["Name", "Lastname", "Phone", "City", "Email"]
            data = fsql.get_heads() if data is None else data
        case "supplier":
            columns = ["Id", "Name", "Location"]
            data = fsql.get_supplier() if data is None else data
        case "p_and_s":
            columns = ["ID", "Name", "Model", "Brand", "Description", "Price retail",
                       "Quantity", "Price Provider", "Support", "Is_service", "Category",
                       "Img URL"]
            data = fsql.get_p_and_s() if data is None else data
        case "orders":
            columns = ["Id", "Product ID", "Quantity", "Date", "Customer", "Employee"]
            data = fsql.get_orders() if data is None else data
        case "v_orders":
            columns = ["Id", "Products", "Date", "Customer", "Employee", "Chat ID"]
            data = fsql.get_v_orders() if data is None else data
        case "purchases":
            columns = ["Id", "Product ID", "Quantity", "Date", "Supplier"]
            data = fsql.get_purchases() if data is None else data
        case "tickets":
            columns = ["Id", "Content", "Is review?", "Is answered?", "Timestamp"]
            data = fsql.get_tickets() if data is None else data
        case "users":
            columns = ["Id", "Username", "Permissions", "Expiration", "Timestamp"]
            data = fsql.get_users() if data is None else data
        case "chats":
            columns = ["ID", "Context", "Start", "End", "Receiver", "Sender", "Platform", "Is alive?", "Is reviewed?"]
            data = fsql.get_chats() if data is None else data
        case _:
            columns = []
            data = []
            print("Error in create_visualizer_treeview")
    column_span = len(columns)
    treeview = Tableview(master,
                         coldata=columns,
                         rowdata=data,
                         paginated=True,
                         searchable=True,
                         autofit=True,
                         bootstyle=style)
    treeview.grid(row=row, column=column, padx=pad_x, pady=pad_y,
                  columnspan=column_span, sticky="nswe")
    return treeview, data


def create_button_side_menu(master, row, column, text, image=None, command=None):
    button = ttk.Button(master, text=text, image=image, command=command)
    button.grid(row=row, column=column, sticky="nsew", pady=5, padx=30)
    return button


def load_default_images(path=IMG_PATH_COLLAPSING):
    """
        Load the default images for the buttons.
        :return: a list of images.
        :rtype: list of images.
        """
    return (ctk.CTkImage(light_image=Image.open(os.path.join(path, "customers_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "employees_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "departments_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "heads_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "suppliers_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "products_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "orders_img.png")), size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "purchases_img.png")), size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "ticket_img.png")), size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "chats_img.png")), size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "v_orders_img.png")), size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(path, "add_user_light.png")), size=(20, 20)),

            )


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


def set_dateEntry_new_value(master, entry, value, row, column, padx, pady):
    entry.destroy()
    entry = ttk.DateEntry(master,
                          startdate=value)
    entry.grid(row=row, column=column, padx=padx, pady=pady)
    return entry


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
        self.label1_emp = ttk.Label(self.insert_frame, text="Name", font=("Helvetica", 12, "bold"))
        self.label2_emp = ttk.Label(self.insert_frame, text="LastName", font=("Helvetica", 12, "bold"))
        self.label3_emp = ttk.Label(self.insert_frame, text="CURP", font=("Helvetica", 12, "bold"))
        self.label4_emp = ttk.Label(self.insert_frame, text="Phone", font=("Helvetica", 12, "bold"))
        self.label5_emp = ttk.Label(self.insert_frame, text="Email", font=("Helvetica", 12, "bold"))
        self.label6_emp = ttk.Label(self.insert_frame, text="Department", font=("Helvetica", 12, "bold"))
        self.label7_emp = ttk.Label(self.insert_frame, text="Modality", font=("Helvetica", 12, "bold"))
        self.label8_emp = ttk.Label(self.insert_frame, text="Contrato", font=("Helvetica", 12, "bold"))
        self.label9_emp = ttk.Label(self.insert_frame, text="Ingreso", font=("Helvetica", 12, "bold"))
        self.label10_emp = ttk.Label(self.insert_frame, text="RFC", font=("Helvetica", 12, "bold"))
        self.label11_emp = ttk.Label(self.insert_frame, text="Emg. Info.", font=("Helvetica", 12, "bold"))
        self.label12_emp = ttk.Label(self.insert_frame, text="NSS", font=("Helvetica", 12, "bold"))
        self.label13_emp = ttk.Label(self.insert_frame, text="Puesto", font=("Helvetica", 12, "bold"))
        self.label14_emp = ttk.Label(self.insert_frame, text="Estatus", font=("Helvetica", 12, "bold"))
        self.label1_emp.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2_emp.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3_emp.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        self.label4_emp.grid(row=0, column=3, padx=1, pady=1, sticky="nsew")
        self.label5_emp.grid(row=2, column=2, padx=1, pady=1, sticky="nsew")
        self.label6_emp.grid(row=2, column=1, padx=1, pady=1, sticky="nsew")
        self.label7_emp.grid(row=2, column=0, padx=1, pady=1, sticky="nsew")
        self.label8_emp.grid(row=2, column=3, padx=1, pady=1, sticky="nsew")
        self.label9_emp.grid(row=4, column=0, padx=1, pady=1, sticky="nsew")
        self.label10_emp.grid(row=4, column=1, padx=1, pady=1, sticky="nsew")
        self.label11_emp.grid(row=4, column=2, padx=1, pady=1, sticky="nsew")
        self.label12_emp.grid(row=4, column=3, padx=1, pady=1, sticky="nsew")
        self.label13_emp.grid(row=6, column=0, padx=1, pady=1, sticky="nsew")
        self.label14_emp.grid(row=6, column=1, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1_emp = ttk.Entry(self.insert_frame, width=16)
        self.entry2_emp = ttk.Entry(self.insert_frame, width=16)
        self.entry3_emp = ttk.Entry(self.insert_frame, width=21)
        self.entry4_emp = ttk.Entry(self.insert_frame, width=10)
        self.entry5_emp = ttk.Entry(self.insert_frame, width=21)
        self.entry6_emp = ttk.Entry(self.insert_frame, width=5)
        self.entry8_emp = ttk.Entry(self.insert_frame, width=10)
        self.entry9_emp = ttk.DateEntry(self.insert_frame)
        self.entry10_emp = ttk.Entry(self.insert_frame, width=13)
        self.entry11_emp = ttk.Entry(self.insert_frame, width=21)
        self.entry12_emp = ttk.Entry(self.insert_frame, width=10)
        self.entry13_emp = ttk.Entry(self.insert_frame, width=15)
        self.entry1_emp.grid(row=1, column=0, padx=5, pady=1, sticky="nswe")
        self.entry2_emp.grid(row=1, column=1, padx=5, pady=1, sticky="nswe")
        self.entry3_emp.grid(row=1, column=2, padx=5, pady=1, sticky="nswe")
        self.entry4_emp.grid(row=1, column=3, padx=5, pady=1, sticky="nswe")
        self.entry5_emp.grid(row=3, column=2, padx=5, pady=1, sticky="nswe")
        self.entry6_emp.grid(row=3, column=1, padx=5, pady=1, sticky="nswe")
        self.entry8_emp.grid(row=3, column=3, padx=5, pady=1, sticky="nswe")
        self.entry9_emp.grid(row=5, column=0, padx=5, pady=1, sticky="nswe")
        self.entry10_emp.grid(row=5, column=1, padx=5, pady=1, sticky="nswe")
        self.entry11_emp.grid(row=5, column=2, padx=5, pady=1, sticky="nswe")
        self.entry12_emp.grid(row=5, column=3, padx=5, pady=1, sticky="nswe")
        self.entry13_emp.grid(row=7, column=0, padx=5, pady=1, sticky="nswe")
        # combobox
        self.combobox_1 = ttk.Combobox(self.insert_frame, values=["In person", "Online", "Hybrid", "normal", "externo"],
                                       state="readonly")
        self.combobox_1.grid(row=3, column=0, pady=1, padx=1, sticky="nswe")
        self.combobox_2 = ttk.Combobox(self.insert_frame, values=["activo", "inactivo"],
                                       state="readonly")
        self.combobox_2.grid(row=7, column=1, pady=1, padx=1, sticky="nswe")
        # -----------------------insert button-----------------------
        btns_frame = ttk.Frame(self)
        btns_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        btns_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert = ttk.Button(
            btns_frame, text="Insertar", width=20, command=self._insert_employee)
        self.btn_insert.grid(row=0, column=0, pady=10, padx=1)
        self.btn_update = ttk.Button(
            btns_frame, text="Actualizar", width=20, command=self._update_employee)
        self.btn_update.grid(row=0, column=1, pady=10, padx=1)
        self.btn_delete = ttk.Button(
            btns_frame, text="Eliminar", width=20, command=self._delete_employee)
        self.btn_delete.grid(row=0, column=2, pady=10, padx=1)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ScrolledFrame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table Employees")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.employee_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "employees", 14,
            row=1, column=0, style="primary",
            pad_x=25, pad_y=10)
        self.employee_insert.view.bind("<Double-1>", self._emp_selected)
        self.label_table_show = ttk.Label(self.visual_frame,
                                          text="See the next table for available departments")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        create_visualizer_treeview(self.visual_frame, "departments", 7,
                                   row=3, column=0, style="info", pad_x=25, pad_y=10)

    def _emp_selected(self, event):
        data = event.widget.item(event.widget.selection()[0], "values")
        (id_emp, name, lastname, phone, department, modality, email,
         contract, entry_date, rfc, curp, nss, emergency, puesto, status) = data
        self._id_emp_update = int(id_emp)
        set_entry_value(self.entry1_emp, name.title())
        set_entry_value(self.entry2_emp, lastname.title())
        set_entry_value(self.entry3_emp, curp)
        set_entry_value(self.entry4_emp, phone)
        set_entry_value(self.entry5_emp, email)
        set_entry_value(self.entry6_emp, department)
        set_entry_value(self.entry13_emp, puesto)
        self.combobox_1.set(modality)
        set_entry_value(self.entry8_emp, contract)
        entry_date = datetime.strptime(entry_date, "%Y-%m-%d %H:%M:%S") if entry_date != "None" else datetime.now()
        self.entry9_emp = set_dateEntry_new_value(
            self.insert_frame, self.entry9_emp, entry_date.date(),
            row=5, column=0, padx=5, pady=1)
        set_entry_value(self.entry10_emp, rfc)
        set_entry_value(self.entry12_emp, nss)
        set_entry_value(self.entry11_emp, emergency)
        self.combobox_2.set(status)

    def _update_table_show(self, data):
        self.employee_insert.grid_forget()
        self.employee_insert, data = create_visualizer_treeview(
            self.visual_frame, "employees", 14,
            row=1, column=0, style="primary",
            pad_x=25, pad_y=10, data=data)
        self.employee_insert.view.bind("<Double-1>", self._emp_selected)

    def get_entries_values(self):
        name = self.entry1_emp.get()
        lastname = self.entry2_emp.get()
        curp = self.entry3_emp.get()
        phone = self.entry4_emp.get()
        email = self.entry5_emp.get()
        department = self.entry6_emp.get()
        contract = self.entry8_emp.get()
        entry_date = self.entry9_emp.entry.get()
        rfc = self.entry10_emp.get()
        nss = self.entry12_emp.get()
        emergency = self.entry11_emp.get()
        modality = self.combobox_1.get()
        puesto = self.entry13_emp.get()
        status = self.combobox_2.get()
        return (name, lastname, curp, phone, email, department, contract,
                entry_date, rfc, nss, emergency, modality, puesto, status)

    def _insert_employee(self):
        (name, lastname, curp, phone, email, department, contract,
         entry_date, rfc, nss, emergency, modality, puesto, status) = self.get_entries_values()
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=f"Are you sure you want to insert the following employee:\n"
            f"Name: {name}\nLastname: {lastname}\nCurp: {curp}\nPhone: {phone}\n"
            f"Email: {email}\nDepartment: {department}\nContract: {contract}\n"
            f"Entry date: {entry_date}\nRfc: {rfc}\nNss: {nss}\n"
            f"Emergency: {emergency}\nModality: {modality}\nPuesto: {puesto}"
        )
        if answer == "No":
            return
        flag, e, out = fsql.new_employee(
            name, lastname, curp, phone, email, department, contract, entry_date,
            rfc, nss, emergency, modality, puesto, status)
        if flag:
            self.data.append(
                (out, name, lastname, phone, department, modality, email,
                 contract, entry_date, rfc, curp, nss, emergency, puesto, "activo"))
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"New employee created:\n{out}")
        else:
            Messagebox.show_error(title="Error", message=f"Error creating employee:\n{e}")

    def _update_employee(self):
        (name, lastname, curp, phone, email, department, contract,
         entry_date, rfc, nss, emergency, modality, puesto, status) = self.get_entries_values()
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=f"Are you sure you want to update the following employee:\n"
            f"Name: {name}\nLastname: {lastname}\nCurp: {curp}\nPhone: {phone}\n"
            f"Email: {email}\nDepartment: {department}\nContract: {contract}\n"
            f"Entry date: {entry_date}\nRfc: {rfc}\nNss: {nss}\n"
            f"Emergency: {emergency}\nModality: {modality}\nPuesto: {puesto}"
            f"\nEmployee ID: {self._id_emp_update}\nEstatus: {status}"
        )
        if answer == "No":
            return
        flag, e, out = fsql.update_employee(
            self._id_emp_update, name, lastname, curp, phone, email, department,
            contract, entry_date, rfc, nss, emergency, modality, puesto, status)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_emp_update:
                    self.data[index] = (
                        self._id_emp_update, name, lastname, phone, department,
                        modality, email, contract, entry_date, rfc, curp,
                        nss, emergency, puesto, status)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"Employee updated")
        else:
            Messagebox.show_error(title="Error", message=f"Error updating employee:\n{e}")

    def _delete_employee(self):
        self._id_emp_update = int(self.entry1_emp.get()) if self._id_emp_update is None \
            else self._id_emp_update
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
        self.entry1_emp.delete(0, tk.END)
        self.entry2_emp.delete(0, tk.END)
        self.entry3_emp.delete(0, tk.END)
        self.entry4_emp.delete(0, tk.END)
        self.entry5_emp.delete(0, tk.END)
        self.entry6_emp.delete(0, tk.END)
        self.entry8_emp.delete(0, tk.END)
        self.entry10_emp.delete(0, tk.END)
        self.entry11_emp.delete(0, tk.END)
        self.entry12_emp.delete(0, tk.END)
        self.entry13_emp.delete(0, tk.END)
        self._id_emp_update = None


class CustomersFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Customers Table",
                                  font=("Helvetica", 32, "bold"))
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # subframe on content frame
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        self.insert_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # widgets on left_frame
        self.label1_emp = ttk.Label(self.insert_frame, text="Name", font=("Helvetica", 12, "bold"))
        self.label2_emp = ttk.Label(self.insert_frame, text="LastName", font=("Helvetica", 12, "bold"))
        self.label3_emp = ttk.Label(self.insert_frame, text="Phone", font=("Helvetica", 12, "bold"))
        self.label5_emp = ttk.Label(self.insert_frame, text="Email", font=("Helvetica", 12, "bold"))
        self.label4_emp = ttk.Label(self.insert_frame, text="City", font=("Helvetica", 12, "bold"))
        self.label1_emp.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2_emp.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3_emp.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        self.label4_emp.grid(row=0, column=3, padx=1, pady=1, sticky="nsew")
        self.label5_emp.grid(row=2, column=0, padx=1, pady=1, sticky="nsew", columnspan=2)
        # inputs
        self.entry1_emp = ttk.Entry(self.insert_frame,
                                    width=15)
        self.entry2_emp = ttk.Entry(self.insert_frame,
                                    width=15)
        self.entry4_emp = ttk.Entry(self.insert_frame,
                                    width=13)
        self.entry3_emp = ttk.Entry(self.insert_frame,
                                    width=9)
        self.entry5_emp = ttk.Entry(self.insert_frame,
                                    width=21)
        self.entry1_emp.grid(row=1, column=0, padx=5, pady=1)
        self.entry2_emp.grid(row=1, column=1, padx=5, pady=1)
        self.entry3_emp.grid(row=1, column=2, padx=5, pady=1)
        self.entry4_emp.grid(row=1, column=3, padx=5, pady=1)
        self.entry5_emp.grid(row=3, column=0, padx=5, pady=1, columnspan=2)
        # insert button customer
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)

        # subframe on content frame
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(1, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                      text="Table Customers")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.subframe_table1 = ScrolledFrame(self.visual_frame,
                                             orientation="horizontal")
        self.subframe_table1.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.subframe_table1.columnconfigure(0, weight=1)
        self.subframe_table1.rowconfigure(0, weight=1)
        employee_insert = create_visualizer_treeview(self.subframe_table1, "customers", 30,
                                                     row=0, column=0, style="success")


class DepartmentsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
        self.label1_emp = ttk.Label(self.insert_frame, text="Name", font=("Helvetica", 12, "bold"))
        self.label2_emp = ttk.Label(self.insert_frame, text="Location", font=("Helvetica", 12, "bold"))
        self.label1_emp.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2_emp.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1_emp = ttk.Entry(self.insert_frame, width=15)
        self.entry2_emp = ttk.Entry(self.insert_frame, width=15)
        self.entry1_emp.grid(row=1, column=0, padx=5, pady=1)
        self.entry2_emp.grid(row=1, column=1, padx=5, pady=1)
        # ----------------insert btn_employees---------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(1, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table Departments")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        table_insert = create_visualizer_treeview(self.visual_frame, "departments", 10,
                                                  row=1, column=0, style="success")


class HeadsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Departments Table", font=("Helvetica", 32, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # ---------------subframe on content frame------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2), weight=1)
        # ---------------widgets for insert-----------------------
        self.label1 = ttk.Label(self.insert_frame, text="Name",
                                font=ttk.Font(size=12, weight="bold"))
        self.label2 = ttk.Label(self.insert_frame, text="Employee",
                                font=ttk.Font(size=12, weight="bold"))
        self.label3 = ttk.Label(self.insert_frame, text="Department",
                                font=ttk.Font(size=12, weight="bold"))
        self.label1.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        # ------------inputs--------------
        self.entry1 = ttk.Entry(self.insert_frame, placeholder_text="Position",
                                   height=25, width=150)
        self.entry2 = ttk.Entry(self.insert_frame, placeholder_text="Employee",
                                   height=25, width=150)
        self.entry3 = ttk.Entry(self.insert_frame, placeholder_text="Department",
                                   height=25, width=150)
        self.entry1.grid(row=1, column=0, padx=5, pady=1)
        self.entry2.grid(row=1, column=1, padx=5, pady=1)
        self.entry3.grid(row=1, column=2, padx=5, pady=1)
        # ---------------insert btn_employees-------------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # ---------------subframe on content frame---------------
        self.visual_frame = ttk.ScrollableFrame(self, fg_color="transparent",
                                                   border_color="#656565",
                                                   border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                         text="Table for head of departments",
                                         text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        table_insert = create_visualizer_treeview(self.visual_frame, "heads", 10,
                                                  row=1, column=0, style="success")
        # ---------------subframe for help frame---------------
        self.label_help = ttk.Label(self.visual_frame,
                                       text="See the next table for available departments",
                                       text_color="#fff")
        self.label_help.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        dep_tab_v = create_visualizer_treeview(self.visual_frame, "departments", 7,
                                               row=3, column=0, style="info")
        self.subframe_help = ttk.ScrollableFrame(self.visual_frame, fg_color="transparent",
                                                    orientation="horizontal")
        self.subframe_help.grid(row=4, column=0, sticky="nsew")
        self.subframe_help.columnconfigure(0, weight=1)
        emp_tab_v = create_visualizer_treeview(self.subframe_help, "employees", 7,
                                               row=0, column=0, style="info")


class SuppliersFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Suppliers Table",
                                  font=ttk.Font(size=30, weight="bold"),
                                  text_color="#fff")
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe for insert--------------------------
        self.insert_frame = ttk.Frame(self, fg_color="#02021A")
        self.insert_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1), weight=1)
        # --------------------widgets insert-----------------------
        self.label1_emp = ttk.Label(self.insert_frame, text="Name",
                                       font=ttk.Font(size=12, weight="bold"),
                                       text_color="#fff")
        self.label2_emp = ttk.Label(self.insert_frame, text="Location",
                                       font=ttk.Font(size=12, weight="bold"),
                                       text_color="#fff")
        self.label1_emp.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2_emp.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1_emp = ttk.Entry(self.insert_frame, placeholder_text="name",
                                       height=25, width=150)
        self.entry2_emp = ttk.Entry(self.insert_frame, placeholder_text="location",
                                       height=25, width=150)
        self.entry1_emp.grid(row=1, column=0, padx=5, pady=1)
        self.entry2_emp.grid(row=1, column=1, padx=5, pady=1)
        # ----------------insert btn_employees---------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # ----------------subframe visual-----------------------
        self.visual_frame = ttk.ScrollableFrame(self, fg_color="transparent",
                                                   border_color="#656565",
                                                   border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(1, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame, text="Table Suppliers",
                                         text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        table_insert = create_visualizer_treeview(self.visual_frame, "supplier", 20,
                                                  row=1, column=0, style="success")


class ProductsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs, fg_color="#02021A")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.label = ttk.Label(self, text="Products and Services table",
                                  font=ttk.Font(size=30, weight="bold"),
                                  text_color="#fff")
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self, fg_color="#02021A")
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.label1 = ttk.Label(self.insert_frame, text="Name", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label2 = ttk.Label(self.insert_frame, text="Model", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label3 = ttk.Label(self.insert_frame, text="Brand", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label5 = ttk.Label(self.insert_frame, text="Price Retail", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label4 = ttk.Label(self.insert_frame, text="Available", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label6 = ttk.Label(self.insert_frame, text="Price Provider", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label7 = ttk.Label(self.insert_frame, text="Support?", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label8 = ttk.Label(self.insert_frame, text="Is service?", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label9 = ttk.Label(self.insert_frame, text="Category", font=ttk.Font(size=12, weight="bold"),
                                   text_color="#fff")
        self.label10 = ttk.Label(self.insert_frame, text="IMG URL", font=ttk.Font(size=12, weight="bold"),
                                    text_color="#fff")
        self.label11 = ttk.Label(self.insert_frame, text="Description", font=ttk.Font(size=12, weight="bold"),
                                    text_color="#fff")
        self.label1.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        self.label2.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        self.label3.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        self.label4.grid(row=0, column=3, padx=1, pady=1, sticky="nsew")
        self.label5.grid(row=2, column=0, padx=1, pady=1, sticky="nsew")
        self.label6.grid(row=2, column=1, padx=1, pady=1, sticky="nsew")
        self.label7.grid(row=2, column=2, padx=1, pady=1, sticky="nsew")
        self.label8.grid(row=2, column=3, padx=1, pady=1, sticky="nsew")
        self.label9.grid(row=4, column=0, padx=1, pady=1, sticky="nsew")
        self.label10.grid(row=4, column=1, padx=1, pady=1, sticky="nsew")
        self.label11.grid(row=4, column=2, padx=1, pady=1, sticky="nsew")
        # -----------------------inputs-----------------------
        self.entry1 = ttk.Entry(self.insert_frame, placeholder_text="name",
                                   height=25, width=150)
        self.entry2 = ttk.Entry(self.insert_frame, placeholder_text="model",
                                   height=25, width=150)
        self.entry3 = ttk.Entry(self.insert_frame, placeholder_text="brand",
                                   height=25, width=130)
        self.entry5 = ttk.Entry(self.insert_frame, placeholder_text="price_retail",
                                   height=25, width=90)
        self.entry4 = ttk.Entry(self.insert_frame, placeholder_text="#",
                                   height=25, width=70)
        self.entry6 = ttk.Entry(self.insert_frame, placeholder_text="price_provider",
                                   height=25, width=90)
        switch_var_support = ctk.StringVar(value="True")
        self.entry7 = ttk.Switch(self.insert_frame, variable=switch_var_support,
                                    onvalue="True", offvalue="False",
                                    textvariable=switch_var_support)
        switch_var_service = ctk.StringVar(value="True")
        self.entry8 = ttk.Switch(self.insert_frame, variable=switch_var_service,
                                    onvalue="True", offvalue="False",
                                    textvariable=switch_var_service)
        self.entry9 = ttk.Entry(self.insert_frame, placeholder_text="##,##,##",
                                   height=25, width=150)
        self.entry10 = ttk.Entry(self.insert_frame, placeholder_text="https//...",
                                    height=25, width=150)
        self.entry11 = ttk.Entry(self.insert_frame, placeholder_text="description",
                                    height=25, width=150)
        self.entry1.grid(row=1, column=0, padx=5, pady=1)
        self.entry2.grid(row=1, column=1, padx=5, pady=1)
        self.entry3.grid(row=1, column=2, padx=5, pady=1)
        self.entry4.grid(row=1, column=3, padx=5, pady=1)
        self.entry5.grid(row=3, column=0, padx=5, pady=1)
        self.entry6.grid(row=3, column=1, padx=5, pady=1)
        self.entry7.grid(row=3, column=2, padx=5, pady=1)
        self.entry8.grid(row=3, column=3, padx=5, pady=1)
        self.entry9.grid(row=5, column=0, padx=5, pady=1)
        self.entry10.grid(row=5, column=1, padx=5, pady=1)
        self.entry11.grid(row=5, column=2, padx=5, pady=1)
        # -----------------------insert button-----------------------
        self.btn_insert = ttk.Button(self, text="Insert", width=200)
        self.btn_insert.grid(row=2, column=0, pady=10, padx=1)
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self, fg_color="transparent",
                                         border_color="#656565",
                                         border_width=2)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(1, weight=1)
        self.label_table1 = ttk.Label(self.visual_frame,
                                         text="Table products and services",
                                         text_color="#fff")
        self.label_table1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.subframe_table1 = ttk.ScrollableFrame(self.visual_frame, fg_color="transparent",
                                                      orientation="horizontal")
        self.subframe_table1.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.subframe_table1.columnconfigure(0, weight=1)
        self.subframe_table1.rowconfigure(0, weight=1)
        ps_insert = create_visualizer_treeview(self.subframe_table1, "p_and_s", 15,
                                               row=0, column=0, style="success")


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
        self.entry2 = ttk.Entry(self.insert_frame, placeholder_text="####",
                                   height=25, width=150)
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
        order_insert = create_visualizer_treeview(self.visual_frame, "orders", 10,
                                                  row=1, column=0, style="success")
        self.label_table_show = ttk.Label(self.visual_frame,
                                             text="See the next table for available customers and employees",
                                             text_color="#fff")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cus_tab_v = create_visualizer_treeview(self.visual_frame, "customers", 7,
                                               row=3, column=0, style="info")
        self.subframe_table1 = ttk.ScrollableFrame(self.visual_frame, fg_color="transparent",
                                                      orientation="horizontal",
                                                      width=750, height=200, )
        self.subframe_table1.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        self.subframe_table1.columnconfigure(0, weight=1)
        emp_tab_v = create_visualizer_treeview(self.subframe_table1, "employees", 7,
                                               row=4, column=0, style="info")


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
        ps_insert = create_visualizer_treeview(self.visual_frame, "v_orders", 10,
                                               row=1, column=0, style="success")
        self.label_table_show = ttk.Label(self.visual_frame,
                                             text="See the next table for available departments",
                                             text_color="#fff")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cus_tab_v = create_visualizer_treeview(self.visual_frame, "customers", 7,
                                               row=3, column=0, style="info")
        self.subframe_table1 = ttk.ScrollableFrame(self.visual_frame, fg_color="transparent",
                                                      orientation="horizontal")
        self.subframe_table1.grid(row=4, column=0, sticky="nsew")
        self.subframe_table1.columnconfigure(0, weight=1)
        emp_tab_v = create_visualizer_treeview(self.subframe_table1, "employees", 7,
                                               row=4, column=0, style="info")


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
        ps_insert = create_visualizer_treeview(self.visual_frame, "purchases", 10,
                                               row=1, column=0, style="success")
        self.label_table_show = ttk.Label(self.visual_frame,
                                             text="See the next table for available departments", text_color="#fff")
        self.label_table_show.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cus_tab_v = create_visualizer_treeview(self.visual_frame, "supplier", 7,
                                               row=3, column=0, style="info")


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
        ps_insert = create_visualizer_treeview(self.visual_frame, "users", 20,
                                               row=1, column=0, style="success")


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
        ps_insert = create_visualizer_treeview(self.visual_frame, "tickets", 20,
                                               row=1, column=0, style="success")


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
        ps_insert = create_visualizer_treeview(self.visual_frame, "chats", 40,
                                               row=0, column=0, style="success")


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
        self.table_frame = ttk.ScrollableFrame(self, fg_color="#02021A",
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
