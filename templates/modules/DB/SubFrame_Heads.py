# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:54 $'

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from templates.Functions_Utils import create_widget_input_DB, create_btns_DB, create_visualizer_treeview, \
    set_entry_value, clean_entries
from templates.controllers.departments.heads_controller import insert_head, update_head_DB, delete_head_DB


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
        flag, e, out = insert_head(name, department, employee)
        if flag:
            self.data.append([out, name, department, employee])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Head inserted")
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
        flag, e, out = update_head_DB(name, department, employee, self._id_heads_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_heads_update:
                    self.data[index] = [self._id_heads_update, name, department, employee]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Head updated")
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
        flag, e, out = delete_head_DB(self._id_heads_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_heads_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Head deleted")
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
