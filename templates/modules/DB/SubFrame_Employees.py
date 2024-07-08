# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:46 $'

import json
from datetime import datetime

import ttkbootstrap as ttk

from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from templates.controllers.employees.employees_controller import new_employee, update_employee, delete_employee
from static.extensions import format_date, dict_deps
from templates.Functions_GUI_Utils import create_widget_input_DB, create_btns_DB, create_visualizer_treeview, \
    set_entry_value, set_dateEntry_new_value, clean_entries


class EmployeesFrame(ScrolledFrame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._id_emp_update = None
        self.data = kwargs["data"]["data_emps_gen"] if "data_emps_gen" in kwargs["data"] else None
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
            pad_x=25, pad_y=10, data=self.data)
        self.employee_insert.view.bind("<Double-1>", self._emp_selected_table)

    def _emp_selected_table(self, event):
        data = event.widget.item(event.widget.selection()[0], "values")
        try:
            self._id_emp_update = int(data[0])
        except ValueError:
            print("Error ID db")
            return
        for index, entry in enumerate(self.entries):
            if isinstance(entry, ttk.Combobox):
                entry.set(data[index + 1])
            elif isinstance(entry, ttk.Entry):
                if index == 13:
                    departure = json.loads(data[index])
                    value_update = departure["reason"] if departure["reason"] != "None" else ""
                elif index in [16, 17]:
                    emails = data[16].split(",") if data[16] != "None" or data[16] == "" else ["", ""]
                    emails.append("")
                    value_update = emails[index - 16]
                elif index in [18, 19]:
                    emergency = json.loads(data[17])
                    values = [emergency["name"], emergency["phone_number"]]
                    value_update = values[index - 18] if values[index - 18] is not None else ""
                elif index >= 14:
                    value_update = data[index] if data[index] != "None" else ""
                else:
                    value_update = data[index + 1]
                set_entry_value(entry, str(value_update).upper())
            elif isinstance(entry, ttk.DateEntry):
                if index == 7:
                    entry_date = datetime.strptime(data[index + 1],
                                                   format_date) if data[index + 1] != "None" else datetime.now()
                    self.entries[index] = set_dateEntry_new_value(
                        self.insert_frame, self.entries[index], entry_date.date(),
                        row=3, column=3, padx=5, pady=1, date_format=format_date)
                elif index == 12:
                    if len(data[index + 1]) > 0 and data[index + 1] != "None":
                        departure = json.loads(data[index + 1])
                        entry_date = datetime.strptime(departure["date"],
                                                       format_date) if departure["date"] != "None" else datetime.now()
                        self.entries[index] = set_dateEntry_new_value(
                            self.insert_frame, self.entries[index], entry_date.date(),
                            row=7, column=0, padx=5, pady=1, date_format=format_date)
                    else:
                        self.entries[index] = set_dateEntry_new_value(
                            self.insert_frame, self.entries[index], datetime.now().date(),
                            row=7, column=0, padx=5, pady=1, date_format=format_date)
                elif index == 14:
                    entry_date = datetime.strptime(data[index],
                                                   format_date) if data[index] != "None" else datetime.now()
                    self.entries[index] = set_dateEntry_new_value(
                        self.insert_frame, self.entries[index], entry_date.date(),
                        row=7, column=2, padx=5, pady=1, date_format=format_date)

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
        if values[0] == "" or values[1] == "":
            Messagebox.show_error(title="Error", message="Por favor rellenar la información.")
            return
        if status == "inactivo":
            msg = (f"Are you sure you want to insert the following employee:\n"
                   f"Name: {values[0].upper()}\nLastname: {values[1].upper()}")
        else:
            departure = {"date": "None", "reason": ""}
            msg = "Are you sure you want to insert the following employee:\n"
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
        flag, e, out = new_employee(
            values[0], values[1], values[2], values[3], values[4], dict_deps[values[5]], values[6], values[7],
            values[8], values[9], values[10], values[11], json.dumps(departure), values[14], values[15], email,
            json.dumps(emergency))
        if flag:
            row = [out, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7],
                   values[8], values[9], values[10], values[11], json.dumps(departure), values[14], values[15],
                   email, json.dumps(emergency)]
            self.data.append(row)
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message=f"New employee created:\n{out}")
        else:
            Messagebox.show_error(title="Error", message=f"Error creating employee:\n{e}")

    def _update_employee(self):
        if self._id_emp_update is None:
            Messagebox.show_error(title="Error", message="Please select a employee to update.")
            return
        values = self.get_entries_values()
        status = values[11]
        if status == "inactivo":
            msg = (f"Are you sure you want to update the following employee to inactive:\n"
                   f"Name: {values[0].upper()}\nLastname: {values[1].upper()}")
        else:
            departure = {"date": "None", "reason": ""}
            msg = (f"Are you sure you want to update the following employee:\n"
                   f"Name: {values[0].upper()}\nLastname: {values[1].upper()}\n")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        departure = {"date": values[12], "reason": values[13]}
        email = values[16] + "," + values[17]
        emergency = {"name": values[18], "phone_number": values[19]}
        flag, e, out = update_employee(
            self._id_emp_update, values[0], values[1], values[2], values[3], values[4], dict_deps[values[5]], values[6], values[7],
            values[8], values[9], values[10], values[11], json.dumps(departure), values[14], values[15], email,
            json.dumps(emergency))
        if flag:
            for index, item in enumerate(self.data):
                if int(item[0]) == self._id_emp_update:
                    self.data[index] = [
                        self._id_emp_update, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7],
                        values[8], values[9], values[10], values[11], json.dumps(departure), values[14], values[15],
                        email, json.dumps(emergency)]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Employee updated")
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
        flag, e, out = delete_employee(self._id_emp_update)
        if flag:
            for index, item in enumerate(self.data):
                if int(item[0]) == self._id_emp_update:
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
