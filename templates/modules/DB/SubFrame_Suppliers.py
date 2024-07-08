# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:56 $'

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from templates.Functions_GUI_Utils import create_widget_input_DB, create_btns_DB, create_visualizer_treeview, \
    set_entry_value
from templates.controllers.supplier.suppliers_controller import insert_supplier, update_supplier_DB, delete_supplier_DB


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
        flag, e, out = insert_supplier(name, location)
        if flag:
            self.data.append([out, name, location])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Supplier inserted")
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
        flag, e, out = update_supplier_DB(name, location, self._id_supplier_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_supplier_update:
                    self.data[index] = [self._id_supplier_update, name, location]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Supplier updated")
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
        flag, e, out = delete_supplier_DB(self._id_supplier_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_supplier_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Supplier deleted")
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
