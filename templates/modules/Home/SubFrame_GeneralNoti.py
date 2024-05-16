# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 26/abr./2024  at 17:21 $'

import json
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview

from templates.Funtions_Utils import create_label, Reverse
from templates.controllers.notifications.Notifications_controller import get_notifications_by_user, \
    update_status_notification

dict_status = {0: "Pendiente", 1: "Leido"}


def get_notifications_tables(data):
    complete = [key for key in data if key[1] == dict_status[1]]
    complete = Reverse(complete)
    pending = [key for key in data if key[1] == dict_status[0]]
    pending = Reverse(pending)
    return complete, pending


def check_status(item):
    if item[1] == dict_status[1]:
        return True
    else:
        return False


def load_notifications(user_id: int):
    columns = ["Fecha", "Estado", "Mensaje", "id"]
    flag, error, result = get_notifications_by_user(user_id)
    if not flag:
        return {"data": [], "columns": columns, "raw": []}
    data = []
    raw_data = []
    for item in result:
        date_modify, id_not, body = item
        body = json.loads(body)
        status = dict_status[body["status"]]
        message = body["msg"]
        timestamp = body["timestamp"]
        data.append([timestamp, status, message, id_not])
        raw_data.append([id_not, item])
    return {"data": data, "columns": columns, "raw": raw_data} 


class NotificationsUser(ttk.Frame):
    def __init__(self, master, settings=None, username_data=None, **kwargs):
        super().__init__(master)
        self.coldata = None
        self.columnconfigure(0, weight=1)
        self.settings = settings
        self.user_data = username_data if username_data is not None else kwargs["data_emp"]
        self.filepath_cache = settings["sm"]["cache"]
        self.data_dict = load_notifications(self.user_data["id"])
        self.data = self.data_dict["data"]
        self.columns = self.data_dict["columns"]
        self.svar_pending = ttk.StringVar()
        self.svar_complete = ttk.StringVar()
        self.svar_info = ttk.StringVar()
        self.table_not = None
        # ------------------------------title label------------------------
        title_label = ttk.Label(self, text="Notificaciones",
                                font=("Helvetica", 22, "bold"))
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        # ------------------- change the data initial for a read file.-----------
        self.notifications_complete, self.notifications_pending = get_notifications_tables(self.data)
        self.svar_pending.set(f"Pendientes: {len(self.notifications_pending)}")
        self.svar_complete.set(f"Revisadas: {len(self.notifications_complete)}")
        # ---------------------------------widgets info-------------------------
        frame_info_widgets = ttk.Frame(self)
        frame_info_widgets.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        frame_info_widgets.columnconfigure((0, 1), weight=1)
        # Create a Counter text that shows the number of pending notifications
        create_label(frame_info_widgets, 0, 0, textvariable=self.svar_pending,
                     font=("Helvetica", 18, "normal"))
        create_label(frame_info_widgets, 0, 1, textvariable=self.svar_complete,
                     font=("Helvetica", 18, "normal"))
        create_label(frame_info_widgets, 1, 0, textvariable=self.svar_info, font=("Helvetica", 18, "normal"),
                     columnspan=2)
        # ----------------------------tables----------------------------------
        self.frame_tables = ttk.Frame(self)
        self.frame_tables.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_tables.columnconfigure((0, 1), weight=1)
        self.table_not = self.create_tables(self.frame_tables, data=self.notifications_pending+self.notifications_complete)     
        self.text_info = ScrolledText(self.frame_tables, width=20, height=10, 
                                      wrap=ttk.WORD, autohide=True,
                                      font=("Helvetica", 18, "normal"))
        self.text_info.grid(row=1, column=1, sticky="nsew", padx=(10, 10))

    def create_tables(self, master, data):
        self.table_not.destroy() if self.table_not is not None else None
        coldata = []
        for column in self.columns:
            if "Fecha" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "Estado" in column:
                coldata.append({"text": column, "stretch": False, "width": 85})
            else:
                coldata.append({"text": column, "stretch": True})
        self.coldata = coldata
        table_notifications = Tableview(master, 
                                        coldata=coldata, 
                                        autofit=False, 
                                        paginated=False,
                                        searchable=False,
                                        rowdata=data,
                                        height=15)
        table_notifications.grid(row=1, column=0, sticky="nswe", padx=(5, 30))
        table_notifications.view.tag_configure("complete", font=("Arial", 10, "normal"), background="white")
        table_notifications.view.tag_configure("incomplete", font=("Arial", 11, "bold"), background="#98F5FF")
        items_t = table_notifications.view.get_children()
        for item_t in items_t:
            if check_status(table_notifications.view.item(item_t, "values")):
                table_notifications.view.item(item_t, tags="complete")
            else:
                table_notifications.view.item(item_t, tags="incomplete")
        table_notifications.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table_notifications.get_columns()
        for item in columns_header:
            if item.headertext == "id":
                item.hide()
        return table_notifications

    def _on_double_click_table(self, event):
        item = event.widget.selection()[0]
        item_data = event.widget.item(item, "values")
        id_not = int(item_data[3])
        self.svar_info.set(f"Mensaje: {item_data[2]}")
        self.text_info.text.delete("1.0", "end")
        self.text_info.text.insert("1.0", item_data[2])
        if not check_status(item_data):
            item_to_add = list(item_data)
            item_to_add[1] = dict_status[1]
            self.notifications_complete.insert(0, item_to_add)
            # eliminate row from the pending not
            for index, noti in enumerate(self.notifications_pending):
                if int(noti[3]) == id_not:
                    flag, error, result = update_status_notification(id_not, 1)
                    self.notifications_pending.pop(index) if flag else None
                    break
            self.create_tables(self.frame_tables, data=self.notifications_pending+self.notifications_complete)
            self.svar_pending.set(f"Pendientes: {len(self.notifications_pending)}")
            self.svar_complete.set(f"Revisadas: {len(self.notifications_complete)}")
