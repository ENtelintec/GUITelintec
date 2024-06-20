# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:58 $'

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from static.extensions import format_timestamps, format_date
from templates.Functions_Utils import create_visualizer_treeview, create_widget_input_DB, create_btns_DB, \
    set_entry_value, set_dateEntry_new_value
from templates.controllers.order.orders_controller import update_order_db, delete_order_db, insert_vorder_db, \
    update_vorder_db, delete_vorder_db, insert_order


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
        date_order = datetime.strptime(date_order, format_timestamps) if date_order != "None" else datetime.now()
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
        flag, e, out = insert_order(
            id_order, id_product, quantity, date_order, id_customer, id_employee)
        if flag:
            self.data.append([id_order, id_product, quantity, date_order, id_customer, id_employee])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Order inserted")
            self.clean_widgets_orders()
            self._id_order_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting order:\n{e}")
            return

    def _update_order(self):
        (id_order, id_product, quantity, date_order, id_customer, id_employee) = self.get_entries_values()
        if self._id_order_update is None:
            return
        date_order = datetime.strptime(date_order, format_timestamps) if date_order != "None" else datetime.now()
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
        flag, e, out = update_order_db(
            id_order, id_product, quantity, date_order, id_customer, id_employee)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_order_update:
                    self.data[index] = [id_order, id_product, quantity, date_order, id_customer, id_employee]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Order updated")
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
        flag, e, out = delete_order_db(self._id_order_update)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == self._id_order_update:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Order deleted")
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
                    1, 3, 5, 1, date_format=format_date)

    def _update_table_show(self, data):
        self.order_insert.destroy()
        self.order_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "orders", row=1, column=0, style="success", data=data)
        self.order_insert.view.bind("<Double-1>", self._get_data_order)

    def clean_widgets_orders(self):
        for item in self.entries:
            if isinstance(item, ttk.Entry):
                item.delete(0, ttk.END)
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
        date_vorder = datetime.strptime(date_vorder, format_timestamps) if date_vorder != "None" else datetime.now()
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
        flag, e, out = insert_vorder_db(
            id_vorder, products, date_vorder, id_customer, id_employee, chat_id)
        if flag:
            self.data.append([id_vorder, products, date_vorder, id_customer, id_employee, chat_id])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Virtual order inserted")
            self.clean_widgets_orders()
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting virtual order:\n{e}")
            return

    def _update_vorder(self):
        (id_vorder, products, date_vorder, id_customer, id_employee, chat_id) = self.get_entries_values()

        if self._id_vorder_update is None:
            return
        id_vorder = self._id_vorder_update
        date_vorder = datetime.strptime(date_vorder, format_timestamps) if date_vorder != "None" else datetime.now()
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
        flag, e, out = update_vorder_db(
            id_vorder, products, date_vorder, id_customer, id_employee, chat_id)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_vorder:
                    self.data[index] = [id_vorder, products, date_vorder, id_customer, id_employee, chat_id]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Virtual order updated")
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
        date_vorder = datetime.strptime(date_vorder, format_timestamps) if date_vorder != "None" else datetime.now()
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
        flag, e, out = delete_vorder_db(
            id_vorder)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_vorder:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Virtual order deleted")
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
                item.delete(0, ttk.END)
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
                    1, 2, 5, 1, date_format=format_date)
