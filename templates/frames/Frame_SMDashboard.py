# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/abr./2024  at 16:56 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_AuxFiles import get_all_sm_entries
from templates.Funtions_Utils import create_label
from templates.frames.SubFrame_Plots import FramePlot


class SMDashboard(ttk.Frame):
    def __init__(self, master=None, data=None, columns=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._id_emp = None
        self.history = None
        self.data_sm = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure((0, 1), weight=1)
        # ----------------------variables-------------------------------------
        self.svar_info_history = ttk.StringVar(value="************Selecciones un item de la tabla*********************")
        #  --------------------------graphs-----------------------------------
        self.frame_graphs = ttk.Frame(self)
        self.frame_graphs.grid(row=0, column=0, padx=10, pady=10, sticky="nswe", columnspan=1)
        self.frame_graphs.columnconfigure((0, 1), weight=1)
        self.create_plots(self.frame_graphs)
        # --------------------------table SMs---------------------+--------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, padx=20, pady=20, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.table_events = self.create_table(self.frame_table, data=data, columns=columns)
        # ----------------------- history sm-----------------------------------
        create_label(self.frame_table, 0, 1, text="Historial de la SMs", sticky="nswe", font=("Helvetica", 14, "bold"))
        create_label(self.frame_table, 1, 1, textvariable=self.svar_info_history, sticky="nswe")

    def create_plots(self, master):
        data_chart = {"data": {'2024-03_1': [10, 8, 2], '2024-03_2': [15, 2, 13],
                               '2024-03_3': [10, 2, 8], '2024-03_4': [3, 2, 1]},
                      "title": f"SMs por semana",
                      "ylabel": "# de SMs",
                      "legend": ("Creadas", "Procesadas", "Pendientes")
                      }
        plot1_1 = FramePlot(master, data_chart, "bar")
        plot1_1.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        data_chart = {
            "val_x": [1, 2, 3, 4, 5, 6, 7],
            "val_y": [[10, 1], [2, 1], [15, 12], [12, 5], [3, 3], [1, 1], [10, 8]],
            "title": f"SMs por dia de la ultima semana",
            "ylabel": "# de SMs",
            "legend": ("Creadas", "Procesadas")
        }
        plot1_2 = FramePlot(master, data_chart)
        plot1_2.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")

    def create_table(self, master, data=None, columns=None):
        if data is None:
            self.data_sm, columns = get_all_sm_entries(filter_status=False)
        else:
            self.data_sm = data
        if columns is not None:
            columns = ["Estado", "ID", "Codigo", "Folio", "Contrato", "Planta", "Ubicación", "Cliente", "Empleado",
                       "Orden/Cotización", "Fecha", "Fecha Limite", "Items", "Historial", "Comentario"]
        new_data = []
        for row in self.data_sm:
            id_sm, code, folio, contract, plant, location, client, employee, order, date, date_limit, items, status, history, comment = row
            new_data.append((status, id_sm, code, folio, contract, plant, location, client, employee, order, date,
                             date_limit, items, history, comment))
        self.data_sm = new_data
        create_label(master, 0, 0, text="SMs en la base de datos", font=("Arial", 24, "bold"))
        table = Tableview(master,
                          coldata=columns,
                          rowdata=self.data_sm,
                          paginated=True,
                          searchable=False,
                          autofit=True,
                          height=11,
                          pagesize=10)
        table.grid(row=1, column=0, padx=(10, 70), pady=10, sticky="nswe")
        table.view.bind("<Double-1>", self.on_double_click_table_sm)
        return table

    def on_double_click_table_sm(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        data_dic = self.get_sm_values_row(row)
        self.history = json.loads(data_dic["history"])
        msg = ""
        for item in self.history:
            msg += f"Evento de {item['event']} por el usuario {item['user']} en la fecha: {item['date']}\n"
        self.svar_info_history.set(msg)
        print(msg)
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
