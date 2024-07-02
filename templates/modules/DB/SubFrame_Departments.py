# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:53 $'

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from templates.Functions_GUI_Utils import create_widget_input_DB, create_btns_DB, create_visualizer_treeview, \
    set_entry_value, clean_entries
from templates.controllers.departments.department_controller import insert_department, update_department_DB, \
    delete_department_DB


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
        flag, e, out = insert_department(name, location)
        if flag:
            self.data.append([out, name, location])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Department inserted")
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
        flag, e, out = update_department_DB(name, location, self._id_dep_update)
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
        flag, e, out = delete_department_DB(self._id_dep_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_dep_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Department deleted")
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
