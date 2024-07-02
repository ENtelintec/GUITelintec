# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 21:02 $'

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from static.extensions import format_date
from templates.Functions_GUI_Utils import set_dateEntry_new_value, create_widget_input_DB, create_visualizer_treeview, \
    create_btns_DB, set_entry_value
from templates.controllers.tickets.tickets_controller import insert_ticket_db, update_ticket_db, delete_ticket_db


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
        flag, e, out = insert_ticket_db(
            id_t, content, is_retrieved, is_answered, timestamp)
        if flag:
            self.data.append([id_t, content, is_retrieved, is_answered, timestamp])
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Ticket inserted")
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
        flag, e, out = update_ticket_db(
            id_t, content, is_retrieved, is_answered, timestamp)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_t:
                    self.data[index] = [id_t, content, is_retrieved, is_answered, timestamp]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Ticket updated")
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
        flag, e, out = delete_ticket_db(id_t)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_t:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Ticket deleted")
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
                item.delete(0, ttk.END)
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
                    1, 2, 5, 1, date_format=format_date)
