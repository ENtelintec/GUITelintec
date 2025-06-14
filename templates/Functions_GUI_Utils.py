# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 29/ene./2024  at 15:31 $"

import json
from datetime import datetime
from tkinter import StringVar, Misc, filedialog
from typing import Any

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.constants import (
    conversion_quizzes_path,
    ventanasApp_path,
    format_timestamps,
    format_date,
)
from static.constants import filepath_recommendations
from templates.controllers.chatbot.chatbot_controller import get_chats
from templates.controllers.customer.customers_controller import get_customers
from templates.controllers.departments.department_controller import get_departments
from templates.controllers.departments.heads_controller import get_heads_db
from templates.controllers.employees.employees_controller import get_employees
from templates.controllers.employees.us_controller import get_users
from templates.controllers.notifications.Notifications_controller import (
    insert_notification,
)
from templates.controllers.order.orders_controller import get_orders, get_v_orders
from templates.controllers.product.p_and_s_controller import get_p_and_s
from templates.controllers.purchases.purchases_controller import get_purchases
from templates.controllers.supplier.suppliers_controller import get_supplier
from templates.controllers.tickets.tickets_controller import get_tickets


class ComboBoxSearch(ttk.Combobox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._values = kwargs.get("values", [])
        self._counter_keys_pressed = 0
        self.bind("<KeyRelease>", self._on_key_release)
        # self.bind("<<ComboboxSelected>>", self._on_combobox_selected)

    def _on_key_release(self, event):
        # self._counter_keys_pressed += 1
        # if self._counter_keys_pressed <= 2:
        #     return
        self._counter_keys_pressed = 0
        value = self.get()
        if value == "":
            self.config(values=self._values)
            return
        values = []
        for item in self._values:
            if value.lower() in item.lower():
                values.append(item)
        self["values"] = values
        # self.event_generate("<Down>")
        # self.focus_set()

    def set_values(self, new_values):
        self._values = new_values
        self.config(values=self._values)


def create_label(
    master,
    row,
    column,
    padx=5,
    pady=5,
    text=None,
    textvariable=None,
    font=("Helvetica", 11, "normal"),
    columnspan=1,
    sticky=None,
    rowspan=1,
    **kwargs,
) -> ttk.Label:
    """
    Create a label with the text-provided
    :param rowspan:
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
        label = ttk.Label(master, text=text, font=font, **kwargs)
    else:
        label = ttk.Label(master, textvariable=textvariable, font=font, **kwargs)
    if sticky is None:
        label.grid(
            row=row,
            column=column,
            padx=padx,
            pady=pady,
            columnspan=columnspan,
            rowspan=rowspan,
        )
    else:
        label.grid(
            row=row,
            column=column,
            padx=padx,
            pady=pady,
            columnspan=columnspan,
            rowspan=rowspan,
            sticky=sticky,
        )
    return label


def create_Combobox(
    master,
    values,
    width=None,
    row=0,
    column=0,
    state="readonly",
    padx=5,
    pady=5,
    columnspan=1,
    sticky="nswe",
    *args,
    **kwargs,
):
    """
    Create a combobox with the values provided
    :param sticky:
    :param columnspan:
    :param master: Parent of the combobox
    :param values: values of the combobox
    :param row: row to place the widget
    :param column: Column to place the widget
    :param state: state of the combobox
    :param padx:
    :param pady:
    :param width:
    :return: Placed combobox in the grid
    """
    combobox = ttk.Combobox(
        master, values=values, state=state, width=width, *args, **kwargs
    )
    if len(values) > 0:
        combobox.current(0)
    combobox.grid(
        row=row,
        column=column,
        padx=padx,
        pady=pady,
        columnspan=columnspan,
        sticky=sticky,
    )
    return combobox


def create_ComboboxSearch(master, **kwargs):
    """
    Create a combobox with the values provided
    :return: Placed combobox in the grid
    """
    # kwargs for gripd statement
    kwargs_grid = {
        "row": kwargs.get("row", 0),
        "column": kwargs.get("column", 0),
        "padx": kwargs.get("padx", 5),
        "pady": kwargs.get("pady", 5),
        "columnspan": kwargs.get("columnspan", 1),
        "sticky": kwargs.get("sticky", "nswe"),
    }
    kwargs.pop("row", None)
    kwargs.pop("column", None)
    kwargs.pop("padx", None)
    kwargs.pop("pady", None)
    kwargs.pop("columnspan", None)
    kwargs.pop("sticky", None)
    combobox = ComboBoxSearch(master, **kwargs)
    combobox.grid(**kwargs_grid)
    return combobox


def create_entry(
    master,
    width=10,
    row=0,
    column=0,
    state="normal",
    padx=5,
    pady=5,
    columnspan=1,
    sticky="nswe",
    *args,
    **kwargs,
):
    """
    Create an entry with the values provided
    :param sticky:
    :param columnspan:
    :param master: Parent of the entry
    :param row: row to place the widget
    :param column: Column to place the widget
    :param state: state of the entry
    :param padx:
    :param pady:
    :param width:
    :return: Placed entry in the grid
    """
    entry = ttk.Entry(master, state=state, width=width, *args, **kwargs)
    entry.grid(
        row=row,
        column=column,
        padx=padx,
        pady=pady,
        columnspan=columnspan,
        sticky=sticky,
    )
    return entry


def create_date_entry(
    master,
    row=0,
    column=0,
    padx=5,
    pady=5,
    columnspan=1,
    sticky="nswe",
    *args,
    **kwargs,
):
    """
    Create a date entry with the values provided
    :param sticky:
    :param columnspan:
    :param master: Parent of the entry
    :param row: row to place the widget
    :param column: Column to place the widget
    :param padx:
    :param pady:
    :return: Placed entry in the grid
    """
    entry = ttk.DateEntry(master, *args, **kwargs)
    entry.grid(
        row=row,
        column=column,
        padx=padx,
        pady=pady,
        columnspan=columnspan,
        sticky=sticky,
    )
    return entry


def compare_permissions_windows(
    user_permissions: list,
) -> tuple[bool, Any] | tuple[bool, None]:
    """
    This method is used to compare the permissions of a user.
    :param user_permissions: List of permissions of the user
    :return: bool with the result of the comparison
    """
    ventanas = []
    ventanas_app = json.load(open(ventanasApp_path, encoding="utf-8"))["ventanasApp"]
    ventanas_keys = list(ventanas_app.keys())
    ventanas_keys = [item.lower() for item in ventanas_keys]
    for permission in user_permissions:
        if permission.lower() in ventanas_keys:
            ventanas += ventanas_app[permission]
    if len(ventanas) > 0:
        ventanas = list(set(ventanas))
        ventanas.sort()
        if "Home" in ventanas:
            ventanas.remove("Home")
            ventanas.insert(0, "Home")
        if "Inicio" in ventanas:
            ventanas.remove("Inicio")
            ventanas.insert(0, "Inicio")
        if "Settings" in ventanas:
            ventanas.remove("Settings")
            ventanas.append("Settings")
        if "Cuenta" in ventanas:
            ventanas.remove("Cuenta")
            ventanas.append("Cuenta")
        return True, ventanas
    return False, None


def create_button_side_menu(
    master,
    row,
    column,
    text,
    image=None,
    command=None,
    padx=(5, 5),
    pady=(5, 5),
    columnspan=1,
):
    """
    This method is used to create a button in the side menu.
    :param pady:
    :param padx:
    :param columnspan:
    :param image: image for the button
    :param command: command for the button
    :param master: father for the button
    :param row: row for the button
    :param column: column for the button
    :param text: text for the button
    """
    button = ttk.Button(
        master, text=text, image=image, compound="left", command=command
    )
    button.grid(
        row=row,
        column=column,
        sticky="nsew",
        pady=pady,
        padx=padx,
        columnspan=columnspan,
    )
    button.image = image
    # button.configure(text=text, command=command)
    return button


def create_button(
    master,
    row,
    column,
    text,
    image=None,
    columnspan=1,
    sticky="nswe",
    pady=5,
    padx=5,
    *args,
    **kwargs,
):
    """
    This method is used to create a button in the side menu.
    :param padx:
    :param pady:
    :param sticky:
    :param columnspan:
    :param image: image for the button
    :param master: father for the button
    :param row: row for the button
    :param column: column for the button
    :param text: text for the button
    """
    button = ttk.Button(master, text=text, image=image, *args, **kwargs)
    button.grid(
        row=row,
        column=column,
        sticky=sticky,
        pady=pady,
        padx=padx,
        columnspan=columnspan,
    )
    button.image = image
    return button


def update_stringvars(stringvar_list: list[tuple[StringVar, str]]):
    """
    Update the stringvar list with the new value
    :param stringvar_list: list of stringvars
    :return: None
    """
    for stringvar, value in stringvar_list:
        stringvar.set(value)


def create_stringvar(number: int, value: str):
    """
    Create a stringvar with the number provided initialized with ""
    :param value: Starting value of the stringvar
    :param number: number to create the stringvar
    :return: tuple
    """
    return tuple([ttk.StringVar(value=value) for _ in range(number)])


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


def set_dateEntry_new_value(
    master,
    entry,
    value,
    row,
    column,
    padx,
    pady,
    sticky="nswe",
    date_format=None,
    firstweekday=1,
):
    entry.destroy()
    if date_format is not None:
        entry = ttk.DateEntry(
            master, startdate=value, dateformat=date_format, firstweekday=firstweekday
        )
    else:
        entry = ttk.DateEntry(master, startdate=value)
    entry.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)
    return entry


def set_entry_value(entry, param: str):
    entry.delete(0, ttk.END)
    entry.insert(0, param)


def clean_entries(entries: list[ttk.Entry]):
    for entry in entries:
        if isinstance(entry, ttk.Entry):
            entry.delete(0, ttk.END)
        elif isinstance(entry, ttk.Combobox):
            entry.current(0)
    return entries


def create_visualizer_treeview(
    master: Misc,
    table: str,
    pad_x: int = 5,
    pad_y: int = 5,
    row: int = 0,
    column: int = 0,
    style: str = "primary",
    data=None,
) -> tuple[Tableview, list[Any] | list[list] | Any]:
    match table:
        case "employees":
            columns = [
                "Id",
                "Nombre",
                "Apellido",
                "CURP",
                "Telefono",
                "Modalidad",
                "Departamento",
                "Contrato",
                "Ingreso",
                "RFC",
                "NSS",
                "Puesto",
                "Estatus",
                "Baja",
                "Cumpleaños",
                "# de Legajo",
                "Email",
                "Emg. Info.",
            ]
            # columns = ["Id", "Nombre", "Apellido", "Telefono", "Dep. ID.", "Modalidad", "Email", "Contrato",
            #            "Ingreso", "RFC", "CURP", "NSS", "Emg. Info.", "Puesto", "Estatus", "Baja", "Cumpleaños", "# de Legajo"]
            data = get_employees() if data is None else data
        case "customers":
            columns = ["Id", "Nombre", "Apellido", "Telefono", "Ciudad", "Email"]
            data = get_customers() if data is None else data
        case "departments":
            columns = ["Id", "Name", "Location"]
            data = get_departments() if data is None else data
        case "heads":
            columns = ["Cargo", "Empleado", "Dep.ID", "Dep. Name", "Nombre", "Email"]
            flag, error, data = get_heads_db() if data is None else data
        case "supplier":
            columns = ["Id", "Name", "Location"]
            data = get_supplier() if data is None else data
        case "p_and_s":
            columns = [
                "ID",
                "Name",
                "Model",
                "Brand",
                "Description",
                "Price retail",
                "Quantity",
                "Price Provider",
                "Support",
                "Is_service",
                "Category",
                "Img URL",
            ]
            data = get_p_and_s() if data is None else data
        case "orders":
            columns = ["Id", "Product ID", "Quantity", "Date", "Customer", "Employee"]
            data = get_orders() if data is None else data
        case "v_orders":
            columns = ["Id", "Products", "Date", "Customer", "Employee", "Chat ID"]
            data = get_v_orders() if data is None else data
        case "purchases":
            columns = ["Id", "Product ID", "Quantity", "Date", "Supplier"]
            data = get_purchases() if data is None else data
        case "tickets":
            columns = ["Id", "Content", "Is review?", "Is answered?", "Timestamp"]
            data = get_tickets() if data is None else data
        case "users":
            columns = ["Id", "Username", "Permissions", "Expiration", "Timestamp"]
            data = get_users() if data is None else data
        case "chats":
            columns = [
                "ID",
                "Context",
                "Start",
                "End",
                "Receiver",
                "Sender",
                "Platform",
                "Is alive?",
                "Is reviewed?",
            ]
            data = get_chats() if data is None else data
        case _:
            columns = []
            data = []
            print("Error in create_visualizer_treeview")
    column_span = len(columns)
    treeview = Tableview(
        master,
        coldata=columns,
        rowdata=data,
        paginated=True,
        searchable=True,
        autofit=True,
        bootstyle=style,
    )
    treeview.grid(
        row=row,
        column=column,
        padx=pad_x,
        pady=pad_y,
        columnspan=column_span,
        sticky="nswe",
    )
    return treeview, data


def create_widget_input_DB(master, table) -> list:
    match table:
        case "employees":
            ttk.Label(master, text="Nombre", font=("Helvetica", 11, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Apellido", font=("Helvetica", 11, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="CURP", font=("Helvetica", 11, "bold")).grid(
                row=0, column=2, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Telefono", font=("Helvetica", 11, "bold")).grid(
                row=0, column=3, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Modalidad", font=("Helvetica", 11, "bold")).grid(
                row=2, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Departamento", font=("Helvetica", 11, "bold")).grid(
                row=2, column=1, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Contrato", font=("Helvetica", 11, "bold")).grid(
                row=2, column=2, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Ingreso", font=("Helvetica", 11, "bold")).grid(
                row=2, column=3, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="RFC", font=("Helvetica", 11, "bold")).grid(
                row=4, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="NSS", font=("Helvetica", 11, "bold")).grid(
                row=4, column=1, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Puesto", font=("Helvetica", 11, "bold")).grid(
                row=4, column=2, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Estatus", font=("Helvetica", 11, "bold")).grid(
                row=4, column=3, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Baja", font=("Helvetica", 11, "bold")).grid(
                row=6, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Comentario", font=("Helvetica", 11, "bold")).grid(
                row=6, column=1, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(
                master, text="Fecha de nacimiento: ", font=("Helvetica", 11, "bold")
            ).grid(row=6, column=2, padx=1, pady=1, sticky="nsew")
            ttk.Label(
                master, text="# de Legajo: ", font=("Helvetica", 11, "bold")
            ).grid(row=6, column=3, padx=1, pady=1, sticky="nsew")
            ttk.Label(master, text="Email", font=("Helvetica", 11, "bold")).grid(
                row=8, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(
                master, text="Contacto Emergencia: ", font=("Helvetica", 11, "bold")
            ).grid(row=8, column=1, padx=1, pady=1, sticky="nsew")
            # -----------------------inputs-----------------------
            entry1_emp = ttk.Entry(master, width=16)
            entry1_emp.grid(row=1, column=0, padx=5, pady=1, sticky="nswe")
            entry2_emp = ttk.Entry(master, width=16)
            entry2_emp.grid(row=1, column=1, padx=5, pady=1, sticky="nswe")
            entry3_emp = ttk.Entry(master, width=21)
            entry3_emp.grid(row=1, column=2, padx=5, pady=1, sticky="nswe")
            entry4_emp = ttk.Entry(master, width=10)
            entry4_emp.grid(row=1, column=3, padx=5, pady=1, sticky="nswe")
            entry5_emp = ttk.Combobox(
                master, values=["Telintec", "REPSE"], state="readonly"
            )
            entry5_emp.grid(row=3, column=0, pady=1, padx=1, sticky="nswe")
            entry6_emp = ttk.Combobox(
                master,
                values=[
                    "Dirección",
                    "Operaciones",
                    "Administración",
                    "RRHH",
                    "REPSE",
                    "IA",
                    "Otros",
                ],
                state="readonly",
            )
            entry6_emp.grid(row=3, column=1, padx=5, pady=1, sticky="nswe")
            entry7_emp = ttk.Entry(master, width=10)
            entry7_emp.grid(row=3, column=2, padx=5, pady=1, sticky="nswe")
            entry8_emp = ttk.DateEntry(master, dateformat=format_date)
            entry8_emp.grid(row=3, column=3, padx=5, pady=1, sticky="nswe")
            entry9_emp = ttk.Entry(master, width=13)
            entry9_emp.grid(row=5, column=0, padx=5, pady=1, sticky="nswe")
            entry10_emp = ttk.Entry(master, width=10)
            entry10_emp.grid(row=5, column=1, padx=5, pady=1, sticky="nswe")
            entry11_emp = ttk.Entry(master, width=15)
            entry11_emp.grid(row=5, column=2, padx=5, pady=1, sticky="nswe")
            entry12_emp = ttk.Combobox(
                master, values=["activo", "inactivo"], state="readonly"
            )
            entry12_emp.grid(row=5, column=3, pady=1, padx=1, sticky="nswe")
            entry13_emp = ttk.DateEntry(master, dateformat=format_date)
            entry13_emp.grid(row=7, column=0, padx=5, pady=1, sticky="nswe")
            entry14_emp = ttk.Entry(master, width=21)
            entry14_emp.grid(row=7, column=1, padx=5, pady=1, sticky="nswe")
            entry15_emp = ttk.DateEntry(master, dateformat=format_date)
            entry15_emp.grid(row=7, column=2, padx=5, pady=1, sticky="nswe")
            entry16_emp = ttk.Entry(master, width=21)
            entry16_emp.grid(row=7, column=3, padx=5, pady=1, sticky="nswe")
            frame_email = ttk.Frame(master)
            frame_email.grid(row=9, column=0, padx=5, pady=1, sticky="nswe")
            frame_emergency = ttk.Frame(master)
            frame_emergency.grid(row=9, column=1, padx=5, pady=1, sticky="nswe")
            ttk.Label(
                frame_email, text="Email Telintec: ", font=("Helvetica", 11, "bold")
            ).grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
            ttk.Label(
                frame_email, text="Email 2: ", font=("Helvetica", 11, "bold")
            ).grid(row=1, column=0, padx=1, pady=1, sticky="nsew")
            entry17_emp = ttk.Entry(frame_email, width=31)
            entry17_emp.grid(row=0, column=1, padx=5, pady=1, sticky="nswe")
            entry18_emp = ttk.Entry(frame_email, width=31)
            entry18_emp.grid(row=1, column=1, padx=5, pady=1, sticky="nswe")
            ttk.Label(
                frame_emergency, text="Nombre: ", font=("Helvetica", 11, "bold")
            ).grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
            ttk.Label(
                frame_emergency, text="Número: ", font=("Helvetica", 11, "bold")
            ).grid(row=1, column=0, padx=1, pady=1, sticky="nsew")
            entry19_emp = ttk.Entry(frame_emergency, width=31)
            entry19_emp.grid(row=0, column=1, padx=5, pady=1, sticky="nswe")
            entry20_emp = ttk.Entry(frame_emergency, width=31)
            entry20_emp.grid(row=1, column=1, padx=5, pady=1, sticky="nswe")
            return [
                entry1_emp,
                entry2_emp,
                entry3_emp,
                entry4_emp,
                entry5_emp,
                entry6_emp,
                entry7_emp,
                entry8_emp,
                entry9_emp,
                entry10_emp,
                entry11_emp,
                entry12_emp,
                entry13_emp,
                entry14_emp,
                entry15_emp,
                entry16_emp,
                entry17_emp,
                entry18_emp,
                entry19_emp,
                entry20_emp,
            ]
        case "customers":
            ttk.Label(master, text="Nombre:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Apellido:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Telefono:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=2, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Email:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=3, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Ciudad:", font=("Helvetica", 12, "bold")).grid(
                row=2, column=0, padx=1, pady=1, sticky="n"
            )
            # inputs
            entry1_emp = ttk.Entry(master, width=15)
            entry2_emp = ttk.Entry(master, width=15)
            entry4_emp = ttk.Entry(master, width=13)
            entry3_emp = ttk.Entry(master, width=9)
            entry5_emp = ttk.Entry(master, width=21)
            entry1_emp.grid(row=1, column=0, padx=5, pady=1, sticky="nswe")
            entry2_emp.grid(row=1, column=1, padx=5, pady=1, sticky="nswe")
            entry3_emp.grid(row=1, column=2, padx=5, pady=1, sticky="nswe")
            entry4_emp.grid(row=1, column=3, padx=5, pady=1, sticky="nswe")
            entry5_emp.grid(row=3, column=0, padx=5, pady=1, sticky="nswe")
            return [entry1_emp, entry2_emp, entry3_emp, entry4_emp, entry5_emp]
        case "departments":
            ttk.Label(master, text="Nombre:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Localizacón:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="n"
            )
            # inputs
            entry1_emp = ttk.Entry(master, width=25)
            entry2_emp = ttk.Entry(master, width=25)
            entry1_emp.grid(row=1, column=0, padx=5, pady=1, sticky="n")
            entry2_emp.grid(row=1, column=1, padx=5, pady=1, sticky="n")
            return [entry1_emp, entry2_emp]
        case "heads":
            ttk.Label(
                master, text="Nombre (cargo):", font=("Helvetica", 12, "bold")
            ).grid(row=0, column=0, padx=1, pady=1, sticky="n")
            ttk.Label(master, text="Empleado:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="n"
            )
            ttk.Label(
                master, text="Departamento:", font=("Helvetica", 12, "bold")
            ).grid(row=0, column=2, padx=1, pady=1, sticky="n")
            # inputs
            entry1_emp = ttk.Entry(master, width=10)
            entry2_emp = ttk.Entry(master, width=10)
            entry3_emp = ttk.Entry(master, width=10)
            entry1_emp.grid(row=1, column=0, padx=5, pady=1, sticky="n")
            entry2_emp.grid(row=1, column=1, padx=5, pady=1, sticky="n")
            entry3_emp.grid(row=1, column=2, padx=5, pady=1, sticky="n")
            return [entry1_emp, entry2_emp, entry3_emp]
        case "suppliers":
            ttk.Label(master, text="Nombre:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Telefono:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="n"
            )
            # inputs
            entry1_emp = ttk.Entry(master, width=35)
            entry2_emp = ttk.Entry(master, width=15)
            entry1_emp.grid(row=1, column=0, padx=5, pady=1, sticky="n")
            entry2_emp.grid(row=1, column=1, padx=5, pady=1, sticky="n")
            return [entry1_emp, entry2_emp]
        case "products":
            ttk.Label(master, text="Nombre:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Modelo:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Marca:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=2, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Descripcion:", font=("Helvetica", 12, "bold")).grid(
                row=0, column=3, padx=1, pady=1, sticky="n"
            )
            ttk.Label(
                master, text="Precio de venta:", font=("Helvetica", 12, "bold")
            ).grid(row=2, column=0, padx=1, pady=1, sticky="n")
            ttk.Label(master, text="Disponible:", font=("Helvetica", 12, "bold")).grid(
                row=2, column=1, padx=1, pady=1, sticky="n"
            )
            ttk.Label(
                master, text="Precio de proveedor:", font=("Helvetica", 12, "bold")
            ).grid(row=2, column=2, padx=1, pady=1, sticky="n")
            ttk.Label(master, text="Soporte:", font=("Helvetica", 12, "bold")).grid(
                row=2, column=3, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Es servicio:", font=("Helvetica", 12, "bold")).grid(
                row=4, column=0, padx=1, pady=1, sticky="n"
            )
            ttk.Label(master, text="Categoria:", font=("Helvetica", 12, "bold")).grid(
                row=4, column=1, padx=1, pady=1, sticky="n"
            )
            ttk.Label(
                master, text="URL de imagen:", font=("Helvetica", 12, "bold")
            ).grid(row=4, column=2, padx=1, pady=1, sticky="n")
            ttk.Label(master, text="ID:", font=("Helvetica", 12, "bold")).grid(
                row=4, column=3, padx=1, pady=1, sticky="n"
            )
            # -----------------------inputs-----------------------
            entry1 = ttk.Entry(master, width=15)
            entry2 = ttk.Entry(master, width=15)
            entry3 = ttk.Entry(master, width=13)
            entry4 = ttk.Entry(master, width=15)
            entry5 = ttk.Entry(master, width=9)
            entry6 = ttk.Entry(master, width=7)
            entry7 = ttk.Entry(master, width=9)
            var8 = ttk.IntVar()
            entry8 = ttk.Checkbutton(
                master,
                onvalue=1,
                offvalue=0,
                variable=var8,
                bootstyle="succes, round-toggle",
            )
            var9 = ttk.IntVar()
            entry9 = ttk.Checkbutton(
                master,
                onvalue=1,
                offvalue=0,
                variable=var9,
                bootstyle="succes, round-toggle",
            )
            entry10 = ttk.Entry(master, width=15)
            entry11 = ttk.Entry(master, width=15)
            entry12 = ttk.Entry(master, width=10)
            entry1.grid(row=1, column=0, padx=5, pady=1, sticky="n")
            entry2.grid(row=1, column=1, padx=5, pady=1, sticky="n")
            entry3.grid(row=1, column=2, padx=5, pady=1, sticky="n")
            entry4.grid(row=1, column=3, padx=5, pady=1, sticky="n")
            entry5.grid(row=3, column=0, padx=5, pady=1)
            entry6.grid(row=3, column=1, padx=5, pady=1)
            entry7.grid(row=3, column=2, padx=5, pady=1)
            entry8.grid(row=3, column=3, padx=5, pady=1)
            entry9.grid(row=5, column=0, padx=5, pady=1)
            entry10.grid(row=5, column=1, padx=5, pady=1)
            entry11.grid(row=5, column=2, padx=5, pady=1)
            entry12.grid(row=5, column=3, padx=5, pady=1)
            return [
                entry1,
                entry2,
                entry3,
                entry4,
                entry5,
                entry6,
                entry7,
                var8,
                var9,
                entry10,
                entry11,
                entry12,
            ]
        case "orders":
            ttk.Label(master, text="ID", font=("Helvetica", 12, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Product ID", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Quantity", font=("Helvetica", 12, "bold")).grid(
                row=0, column=2, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Date order", font=("Helvetica", 12, "bold")).grid(
                row=0, column=3, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Customer ID", font=("Helvetica", 12, "bold")).grid(
                row=2, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Employee ID", font=("Helvetica", 12, "bold")).grid(
                row=2, column=1, padx=1, pady=1, sticky="nsew"
            )
            # -----------------------inputs-----------------------
            entry1 = ttk.Entry(master, width=15)
            entry2 = ttk.Entry(master, width=15)
            entry3 = ttk.Entry(master, width=13)
            entry4 = ttk.DateEntry(master, dateformat=format_date)
            entry5 = ttk.Entry(master, width=7)
            entry6 = ttk.Entry(master, width=9)
            entry1.grid(row=1, column=0, padx=5, pady=1)
            entry2.grid(row=1, column=1, padx=5, pady=1)
            entry3.grid(row=1, column=2, padx=5, pady=1)
            entry4.grid(row=1, column=3, padx=5, pady=1)
            entry5.grid(row=3, column=0, padx=5, pady=1)
            entry6.grid(row=3, column=1, padx=5, pady=1)
            return [entry1, entry2, entry3, entry4, entry5, entry6]
        case "vorders":
            ttk.Label(master, text="ID", font=("Helvetica", 12, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Products", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Date order", font=("Helvetica", 12, "bold")).grid(
                row=0, column=2, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Customer ID", font=("Helvetica", 12, "bold")).grid(
                row=2, column=3, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Employee ID", font=("Helvetica", 12, "bold")).grid(
                row=2, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Chat ID", font=("Helvetica", 12, "bold")).grid(
                row=2, column=1, padx=1, pady=1, sticky="nsew"
            )
            # -----------------------inputs-----------------------
            entry1 = ttk.Entry(master, width=15)
            entry2 = ttk.Entry(master, width=15)
            entry4 = ttk.DateEntry(master, dateformat=format_date)
            entry5 = ttk.Entry(master, width=7)
            entry6 = ttk.Entry(master, width=9)
            entry7 = ttk.Entry(master, width=9)
            entry1.grid(row=1, column=0, padx=5, pady=1)
            entry2.grid(row=1, column=1, padx=5, pady=1)
            entry4.grid(row=1, column=2, padx=5, pady=1)
            entry5.grid(row=3, column=3, padx=5, pady=1)
            entry6.grid(row=3, column=0, padx=5, pady=1)
            entry7.grid(row=3, column=1, padx=5, pady=1)
            return [entry1, entry2, entry4, entry5, entry6, entry7]
        case "tickets":
            ttk.Label(master, text="ID", font=("Helvetica", 12, "bold")).grid(
                row=0, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(master, text="Content", font=("Helvetica", 12, "bold")).grid(
                row=0, column=1, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(
                master, text="Is retrieved?", font=("Helvetica", 12, "bold")
            ).grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
            ttk.Label(master, text="Is answered?", font=("Helvetica", 12, "bold")).grid(
                row=2, column=0, padx=1, pady=1, sticky="nsew"
            )
            ttk.Label(
                master, text="Timestamp Creation", font=("Helvetica", 12, "bold")
            ).grid(row=2, column=1, padx=1, pady=1, sticky="nsew")
            # -----------------------inputs-----------------------
            entry1 = ttk.Entry(master, width=15)
            var2 = ttk.IntVar(value=1)
            entry2 = ttk.Checkbutton(
                master,
                onvalue=1,
                offvalue=0,
                variable=var2,
                bootstyle="succes, round-toggle",
            )
            var3 = ttk.IntVar(value=1)
            entry3 = ttk.Checkbutton(
                master,
                onvalue=1,
                offvalue=0,
                variable=var3,
                bootstyle="succes, round-toggle",
            )
            entry4 = ttk.Entry(master)
            entry5 = ttk.Entry(master, width=30)
            entry1.grid(row=1, column=0, padx=5, pady=1)
            entry2.grid(row=1, column=1, padx=5, pady=1)
            entry3.grid(row=1, column=2, padx=5, pady=1)
            entry4.grid(row=3, column=0, padx=5, pady=1)
            entry5.grid(row=3, column=1, padx=5, pady=1)
            return [entry1, var2, var3, entry4, entry5]
        case _:
            pass


def create_btns_DB(
    master,
    table_type=1,
    _command_insert=None,
    _command_update=None,
    _command_delete=None,
    _command_reset=None,
    *args,
    **kwargs,
) -> tuple | None:
    match table_type:
        case 1:
            btn_insert = ttk.Button(
                master,
                text="Insertar",
                command=_command_insert,
                bootstyle="success",
                *args,
                **kwargs,
            )
            btn_insert.grid(row=0, column=0, pady=10, padx=1)
            btn_update = ttk.Button(
                master, text="Actualizar", command=_command_update, *args, **kwargs
            )
            btn_update.grid(row=0, column=1, pady=10, padx=1)
            btn_reset = ttk.Button(
                master,
                text="Limpiar",
                command=_command_reset,
                bootstyle="info",
                *args,
                **kwargs,
            )
            btn_reset.grid(row=0, column=2, pady=10, padx=1)
            btn_delete = ttk.Button(
                master,
                text="Eliminar",
                command=_command_delete,
                bootstyle="warning",
                *args,
                **kwargs,
            )
            btn_delete.grid(row=0, column=3, pady=10, padx=1)
            return btn_insert, btn_update, btn_delete
        case _:
            return None


def calculate_results_quizzes(dict_quizz: dict, tipo_q: int):
    dict_results = {"c_final": 0, "c_dom": 0, "c_cat": 0, "detail": {}}
    dict_conversions = json.load(open(conversion_quizzes_path, encoding="utf-8"))
    match tipo_q:
        case 1:
            dict_values = dict_conversions["norm035"]["v1"]["conversion"]
            c_final = 0
            c_dom = 0
            c_cat = 0
            for question in dict_quizz.values():
                if question["items"] != "":
                    upper_limit = question["items"][1]
                    lower_limit = question["items"][0]
                    answers = question["answer"]
                    for q in range(lower_limit, upper_limit + 1):
                        for group in dict_values.values():
                            items = group["items"]
                            values = group["values"]
                            if q in items:
                                res = values[answers[q - lower_limit][1]]
                                dict_results["detail"][str(q)] = res
                                c_final += res
                                break
            dict_results["c_final"] = c_final
            dict_cat_doms = dict_conversions["norm035"]["v1"]["categorias"]
            dict_results["c_dom"] = {}
            dict_results["c_cat"] = {}

            for cat_dic in dict_cat_doms.values():
                cat_name = cat_dic["categoria"]
                dict_results["c_cat"][cat_name] = 0
                for dom_name, dom_dic in cat_dic["dominio"].items():
                    dict_results["c_dom"][dom_name] = 0
                    for dim_dic in dom_dic["dimensiones"]:
                        dim_name = dim_dic["dimension"]
                        items = dim_dic["item"]
                        for q, val in dict_results["detail"].items():
                            if int(q) in items:
                                dict_results["c_dom"][dom_name] += val
                                dict_results["c_cat"][cat_name] += val
        case 2:
            dict_values = dict_conversions["norm035"]["v2"]["conversion"]
            c_final = 0
            for question in dict_quizz.values():
                if question["items"] != "":
                    upper_limit = question["items"][1]
                    lower_limit = question["items"][0]
                    answers = question["answer"]
                    for q in range(lower_limit, upper_limit + 1):
                        for group in dict_values.values():
                            items = group["items"]
                            values = group["values"]
                            if q in items:
                                res = values[answers[q - lower_limit][1]]
                                dict_results["detail"][str(q)] = res
                                c_final += res
                                break
            dict_results["c_final"] = c_final
            dict_cat_doms = dict_conversions["norm035"]["v2"]["categorias"]
            dict_results["c_dom"] = {}
            dict_results["c_cat"] = {}
            dict_results["c_dim"] = {}
            for cat_dic in dict_cat_doms.values():
                cat_name = cat_dic["categoria"]
                dict_results["c_cat"][cat_name] = 0
                for dom_name, dom_dic in cat_dic["dominio"].items():
                    dict_results["c_dom"][dom_name] = 0
                    for dim_dic in dom_dic["dimensiones"]:
                        dim_name = dim_dic["dimension"]
                        items = dim_dic["item"]
                        dict_results["c_dim"][dim_name] = 0
                        for q, val in dict_results["detail"].items():
                            if int(q) in items:
                                # print("calculate: ", q, items)
                                dict_results["c_dom"][dom_name] += val
                                dict_results["c_cat"][cat_name] += val
                                dict_results["c_dim"][dim_name] += val
        case _:
            pass
    return dict_results


def recommendations_results_quizzes(dict_results: dict, tipo_q: int):
    # Asumiendo que tienes la ruta correcta en filepath_recommendations
    dict_conversions_recomen = json.load(
        open(filepath_recommendations, encoding="utf-8")
    )
    dict_recommendations = {
        "c_final_r": "",
        "c_dom_r": "",
        "c_cat_r": "",
    }

    # Asumiendo que dict_results contiene las claves 'c_final', 'c_dom', 'c_cat'
    # y que pueden tener valores como 'MUY ALTO', 'ALTO', 'MEDIO', 'BAJO', 'NULO'.

    # Acceder a las recomendaciones basadas en el resultado final, dominio, y categoría
    final_score = dict_results.get(
        "c_final", "NULO"
    )  # Usar NULO como valor por defecto si no se encuentra
    dom_score = dict_results.get("c_dom", "default_dom")  # Usar un valor por defecto
    cat_score = dict_results.get("c_cat", "default_cat")  # Usar un valor por defecto

    # Acceder a las recomendaciones finales
    dict_recommendations["c_final_r"] = dict_conversions_recomen["c_final_r"].get(
        final_score, ["No hay recomendaciones específicas."]
    )

    # Aquí necesitas modificar el código según cómo desees manejar las recomendaciones de dominio y categoría
    # dado que en tu JSON 'c_dom_r' es solo una cadena, puedes necesitar un enfoque diferente o más información
    # Si 'c_dom_r' debería ser una estructura similar a 'c_final_r', ajusta tu JSON y tu código en consecuencia

    # Acceder a las recomendaciones de categoría
    if cat_score in dict_conversions_recomen["c_cat_r"]:
        dict_recommendations["c_cat_r"] = dict_conversions_recomen["c_cat_r"][cat_score]
    else:
        dict_recommendations["c_cat_r"] = [
            "No hay recomendaciones específicas para esta categoría."
        ]

    return dict_recommendations


def Reverse(lst):
    new_lst = lst[::-1]
    return new_lst


def hex_to_item_tableview(hex_num: str, digits: int):
    hex_num = hex_num.replace("0x", "")
    hex_num = int(hex_num, 16)
    hex_num = hex(hex_num)
    hex_num = hex_num.replace("0x", "")
    hex_num = hex_num.zfill(digits)
    return hex_num


def list_hex_numbers(n: int):
    hex_numbers = []
    for i in range(1, n + 1):
        hex_numbers.append(hex(i))
    return hex_numbers


def select_path():
    """
    Función para seleccionar una carpeta de archivos
    :return:
    """
    path = filedialog.askdirectory()
    print(path)
    return path


def create_notification_permission(
    msg: str, permissions: list, title: str, sender_id: int, recierver_id=0
):
    """
    Función para crear una notificación de permiso
    :param recierver_id:
    :param sender_id:
    :param title:
    :param msg:
    :param permissions:
    :return:
    """
    permissions = [item.lower() for item in permissions]
    date = datetime.now()
    timestamp = date.strftime(format_timestamps)
    body = {
        "id": 0,
        "status": 0,
        "title": title,
        "msg": msg,
        "timestamp": timestamp,
        "sender_id": sender_id,
        "receiver_id": recierver_id,
        "app": permissions,
    }
    flag, error, result = insert_notification(body)
    return flag


def validate_digits_numbers(new_value) -> bool:
    """
    Validates that the new value is a number.
    This function is called when the user types in a new value in the
    spinbox.
    It checks if the new value is a number and returns True or
    False accordingly.
    :param new_value: New value to be validated
    :return: True if the new value is a number, False otherwise
    """
    return new_value.isdigit()


def create_spinboxes_time(
    master: Misc,
    father,
    row: int,
    column: int,
    pad_x: int = 5,
    pad_y: int = 5,
    style: str = "primary",
    title: str = "",
    mins_defaul=0,
    hours_default=8,
) -> tuple:
    """Creates a clock with two spinboxes for minutes and hours
    :param title:
    :param father:
    :param master: <Misc> father instance where the object is created
    :param row: <int> row to be placed
    :param column: <int> column to be placed
    :param pad_x: <int> pad in x for the group, not for individual object
    :param pad_y: <int> pad in y for the group, not for individual object
    :param style: <str> bootstrap style selected
    :param mins_defaul: <int> default value for minutes
    :param hours_default: <int> deafult value for hours
    :return: Frame tkinter frame containing the spinboxes
    """
    clock = ttk.Frame(master)
    clock.grid(row=row, column=column, padx=pad_x, pady=pad_y, sticky="w")
    # minutes spinboxes
    # noinspection PyArgumentList
    minutes_spinbox = ttk.Spinbox(
        clock, from_=0, to=59, bootstyle=style, width=2, justify="center"
    )
    minutes_spinbox.grid(row=0, column=1, padx=1, pady=1, sticky="w")
    # hours spinbox
    # noinspection PyArgumentList
    hours_spinbox = ttk.Spinbox(
        clock, from_=0, to=23, bootstyle=style, width=2, justify="center"
    )
    hours_spinbox.grid(row=0, column=0, padx=1, pady=1, sticky="w")
    # add valitation to spinbox
    vcmd_mins = (master.register(validate_digits_numbers), "%P")
    minutes_spinbox.configure(validate="key", validatecommand=vcmd_mins)
    vcmd_hours = (master.register(validate_digits_numbers), "%P")
    hours_spinbox.configure(validate="key", validatecommand=vcmd_hours)
    # set default values
    minutes_spinbox.set(mins_defaul)
    hours_spinbox.set(hours_default)
    # father.clocks.append({title: [minutes_spinbox, hours_spinbox]})
    return clock, {title: [minutes_spinbox, hours_spinbox]}
