# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 26/abr./2024  at 17:21 $'

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_Files import get_cache_notifications
from templates.Funtions_Utils import Reverse, create_label


def get_notifications_tables(data):
    complete = [key for key in data if int(key[1]) == 1]
    complete = Reverse(complete)
    pending = [key for key in data if int(key[1]) == 0]
    pending = Reverse(pending)
    return complete, pending


def check_status(item):
    if int(item[1]) == 1:
        return True
    else:
        return False


class NotificationsSm(ttk.Frame):
    def __init__(self, master, settings=None, username_data=None, **kwargs):
        super().__init__(master)
        self.coldata = None
        self.columnconfigure(0, weight=1)
        self.settings = settings
        self.user_data = username_data
        self.filepath_cache = settings["chatbot"]["cache"]
        print(self.filepath_cache)
        data_dic_chatbot = get_cache_notifications(self.filepath_cache)
        self.data = data_dic_chatbot["chatbot"]["data"]
        self.columns = data_dic_chatbot["chatbot"]["columns"]
        self.svar_pending = ttk.StringVar()
        self.svar_complete = ttk.StringVar()
        self.svar_info = ttk.StringVar()
        self.table_not = None
        # ------------------------------title label------------------------
        title_label = ttk.Label(self, text="Notificaciones de Solicitudes de Material",
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
        self.frame_tables.columnconfigure(0, weight=1)
        self.table_not = self.create_tables(self.frame_tables, data=self.notifications_pending+self.notifications_complete)        

    def create_tables(self, master, data):
        self.table_not.destroy() if self.table_not is not None else None
        coldata = []
        for column in self.columns:
            if "Items" in column:
                coldata.append({"text": column, "stretch": False, "width": 50})
            elif "Id" in column:
                coldata.append({"text": column, "stretch": False, "width": 35})
            elif "Estado" in column:
                coldata.append({"text": column, "stretch": False, "width": 50})
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
        return table_notifications

    def _on_double_click_table(self, event):
        item = event.widget.selection()[0]
        item_data = event.widget.item(item, "values")
        self.svar_info.set(f"Mensaje: {item_data[4]}")
        if not check_status(item_data):
            item_to_add = list(item_data)
            item_to_add[1] = "1"
            self.notifications_complete.insert(0, item_to_add)
            # eliminate row from the pending not
            self.notifications_pending.remove(list(item_data))
            self.create_tables(self.frame_tables, data=self.notifications_pending+self.notifications_complete)
            self.svar_pending.set(f"Pendientes: {len(self.notifications_pending)}")
            self.svar_complete.set(f"Revisadas: {len(self.notifications_complete)}")
