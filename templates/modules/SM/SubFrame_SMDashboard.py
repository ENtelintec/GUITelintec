# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/abr./2024  at 16:56 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tableview import Tableview

from static.extensions import ventanasApp_path, status_dic
from templates.Functions_AuxFiles import get_all_sm_entries
from templates.Funtions_Utils import create_label
from templates.controllers.material_request.sm_controller import finalize_status_sm
from templates.modules.SubFrame_Plots import FramePlot
permissions_supper_SM = json.load(open(ventanasApp_path, encoding="utf-8"))["permissions_supper_SM"]


def create_plots(master):
    data_chart = {"data": {'2024-03_1': [10, 8, 2], '2024-03_2': [15, 2, 13],
                           '2024-03_3': [10, 2, 8], '2024-03_4': [3, 2, 1]},
                  "title": "SMs por semana",
                  "ylabel": "# de SMs",
                  "legend": ("Creadas", "Procesadas", "Pendientes")
                  }
    plot1_1 = FramePlot(master, data_chart, "bar")
    plot1_1.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
    data_chart = {
        "val_x": [1, 2, 3, 4, 5, 6, 7],
        "val_y": [[10, 1], [2, 1], [15, 12], [12, 5], [3, 3], [1, 1], [10, 8]],
        "title": "SMs por dia de la ultima semana",
        "ylabel": "# de SMs",
        "legend": ("Creadas", "Procesadas")
    }
    plot1_2 = FramePlot(master, data_chart)
    plot1_2.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")


class SMDashboard(ttk.Frame):
    def __init__(self, master=None, data=None, data_emp=None, *args, **kwargs):
        super().__init__(master)
        self._id_sm_to_modify = None
        self.permissions = data_emp["permissions"]
        self._id_emp = data_emp["id"]
        self.is_supper_user = self.check_permissions()
        self.history = None
        self.data_sm = None
        self.status_sm = None
        self.columns_sm = data["columns_sm"]
        self.columnconfigure(0, weight=1)
        self.rowconfigure((0, 1), weight=1)
        # ----------------------variables-------------------------------------
        self.svar_info_history = ttk.StringVar(value="************Selecciones un item de la tabla*********************")
        #  --------------------------graphs-----------------------------------
        self.frame_graphs = ttk.Frame(self)
        self.frame_graphs.grid(row=0, column=0, padx=10, pady=10, sticky="nswe", columnspan=1)
        self.frame_graphs.columnconfigure((0, 1), weight=1)
        create_plots(self.frame_graphs)
        # --------------------------table SMs---------------------+--------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, padx=20, pady=20, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        create_label(self.frame_table, 0, 0, text="SMs en la base de datos", font=("Arial", 24, "bold"), columnspan=2)
        ttk.Button(self.frame_table, text="Marca de recibido", command=self._on_recieved_sm).grid(row=1, column=0, sticky="n")
        if self.is_supper_user:
            self.table_events = self.create_table(self.frame_table, data=data["data_sm"], columns=data["columns_sm"])
        else:
            self.table_events = self.create_table(self.frame_table, data=data["data_sm_not_supper"], columns=data["columns_sm"])
        # ----------------------- history sm-----------------------------------
        create_label(self.frame_table, 2, 1, textvariable=self.svar_info_history, sticky="nswe")

    def create_table(self, master, data=None, columns=None):
        if data is None:
            self.data_sm, columns = get_all_sm_entries(filter_status=False, is_supper=self.is_supper_user, emp_id=self._id_emp)
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
        
        table = Tableview(master,
                          coldata=columns,
                          rowdata=self.data_sm,
                          paginated=True,
                          searchable=False,
                          autofit=True,
                          height=11,
                          pagesize=10)
        table.grid(row=2, column=0, padx=(10, 40), pady=10, sticky="nswe")
        table.view.bind("<Double-1>", self.on_double_click_table_sm)
        return table

    def on_double_click_table_sm(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        data_dic = self.get_sm_values_row(row)
        self.status_sm = data_dic["status"]
        self._id_sm_to_modify = int(data_dic["id"])
        self.history = json.loads(data_dic["history"])
        msg = ""
        for item in self.history:
            msg += f"Evento de {item['event']} por el usuario {item['user']} en la fecha: {item['date']}\n"
        self.svar_info_history.set(msg)
        self.on_reset_widgets_click()

    def on_reset_widgets_click(self):
        print("on_reset_widgets_click")

    def get_sm_values_row(self, row):
        (status, id_sm, code, folio, contract, plant, location, client, employee, order_quotation,
         date, date_limit, items, history, comment) = row
        dict_data = {"id": id_sm, "code": code, "folio": folio, "contract": contract, "plant": plant,
                     "location": location, "client": client, "employee": self._id_emp, "date": date,
                     "date_limit": date_limit, "items": items, "status": status, "history": history,
                     "order_quotation": order_quotation, "comment": comment}
        return dict_data

    def check_permissions(self):
        for item in self.permissions.values():
            if item in permissions_supper_SM:
                return True
        return False

    def _on_recieved_sm(self):
        if self._id_sm_to_modify is None:
            return
        if "Finalizado" in self.status_sm:
            Messagebox.show_error(title="Error", message="El material_request no esta en estado procesado")
            return
        msg = f"El material_request {self._id_sm_to_modify} se marcará como recibido, esta seguro?"
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg)
        if answer == "No":
            return
        flag, error, result = finalize_status_sm(self._id_sm_to_modify)
        if not flag:
            Messagebox.show_error(title="Error", message=error)
            return
        else:
            # get data from tableview
            rows = self.table_events.view.get_children()
            for item in rows:
                row = self.table_events.view.item(item, "values")
                if int(row[1]) == self._id_sm_to_modify:
                    self.table_events.view.item(item, values=(status_dic[3], row[1], row[2], row[3], row[4], row[5], row[6],
                                                              row[7], row[8], row[9], row[10], row[11], row[12],
                                                              row[13], row[14]))
                    break
