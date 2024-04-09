# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/abr./2024  at 16:56 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_AuxFiles import get_all_sm_entries
from templates.Funtions_Utils import create_label


class SMDashboard(ttk.Frame):
    def __init__(self, master=None, data=None, columns=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._id_emp = None
        self.history = None
        self.master = master
        self.data_sm = None
        self.columnconfigure((0, 1), weight=1)
        #  --------------------------title-----------------------------------
        create_label(self, 0, 0, text="Solicitudes de material",
                     font=("Helvetica", 30, "bold"), columnspan=2)
        # --------------------------table SMs---------------------+--------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.frame_table.rowconfigure(1, weight=1)
        self.table_events = self.create_table(self.frame_table, data=data, columns=columns)

    def create_table(self, master, data=None, columns=None):
        if data is None:
            self.data_sm, columns = get_all_sm_entries(filter_status=False)
        else:
            self.data_sm = data
        table = Tableview(master,
                          coldata=columns,
                          rowdata=self.data_sm,
                          paginated=True,
                          searchable=False,
                          autofit=True,
                          height=11,
                          pagesize=10)
        table.grid(row=1, column=0, padx=50, pady=10, sticky="nswe")
        table.view.bind("<Double-1>", self.on_double_click_table_sm)
        return table

    def on_double_click_table_sm(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        data_dic = self.get_sm_values_row(row)
        self.history = json.loads(data_dic["history"])
        print(self.history)
        self.on_reset_widgets_click()

    def on_reset_widgets_click(self):
        print("on_reset_widgets_click")

    def get_sm_values_row(self, row):
        (id_sm, code, folio, contract, plant, location, client, employee, order_quotation,
         date, date_limit, items, status, history, comment) = row
        dict_data = {"id": id_sm, "code": code, "folio": folio, "contract": contract, "plant": plant,
                     "location": location, "client": client, "employee": self._id_emp, "date": date,
                     "date_limit": date_limit, "items": items, "status": status, "history": history,
                     "order_quotation": order_quotation, "comment": comment}
        return dict_data
