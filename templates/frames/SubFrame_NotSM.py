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


class NotificationsSm(ttk.Frame):
    def __init__(self, master, settings=None, username_data=None, **kwargs):
        super().__init__(master)
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
        # ----------------------------tables----------------------------------
        frame_tables = ttk.Frame(self)
        frame_tables.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        frame_tables.columnconfigure(0, weight=1)
        self.create_tables(frame_tables,
                           data=self.data)

    def create_tables(self, master, data):
        table_notifications = Tableview(master, 
                                        coldata=self.columns, 
                                        autofit=True, 
                                        autoalign=True, 
                                        paginated=False,
                                        searchable=False,
                                        rowdata=data)
        table_notifications.grid(row=0, column=0, sticky="nsew")
        table_notifications.view.tag_configure("complete", font=("Arial", 10, "normal"), background="gray")
        table_notifications.view.tag_configure("incomplete", font=("Arial", 11, "bold"), background="white")
        # for item in data:
        #     if int(item[1]) == 1:
        #         table_notifications.insert_row("end", item)
        #         # get the last item 
        #         # table_notifications.view.item(item_t, tags="complete")
        #         # table_notifications.view.insert("", "end", values=item, tags="complete")
        #     else:
        #         # table_notifications.view.insert("", "end", values=item, tags="incomplete")
        #         table_notifications.insert_row("end", item)
        # table_notifications.load_table_data()
        # table_notifications.autofit_columns()
        # table_notifications.autoalign_columns()
        items_t = table_notifications.view.get_children()
        print(items_t)
        for item_t in items_t:
            if int(table_notifications.view.item(item_t, "values")[1]) == 1:
                table_notifications.view.item(item_t, tags="complete")
            else:
                table_notifications.view.item(item_t, tags="incomplete")
        
