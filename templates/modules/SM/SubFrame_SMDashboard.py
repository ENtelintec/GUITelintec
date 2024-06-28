# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/abr./2024  at 16:56 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview

from static.extensions import ventanasApp_path, status_dic
from templates.misc.Functions_AuxFiles import get_all_sm_entries
from templates.Functions_AuxPlots import get_data_sm_per_range
from templates.Functions_Utils import create_label, create_Combobox, create_notification_permission
from templates.controllers.material_request.sm_controller import finalize_status_sm
from templates.modules.Misc.SubFrame_Plots import FramePlot
permissions_supper_SM = json.load(open(ventanasApp_path, encoding="utf-8"))["permissions_supper_SM"]


def create_plots(master, range_selected, data_chart=None):
    data_chart = get_data_sm_per_range(range_selected, "normal") if data_chart is None else data_chart
    plot1_1 = FramePlot(master, data_chart, "normal")
    plot1_1.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
    return plot1_1


class SMDashboard(ttk.Frame):
    def __init__(self, master=None, data=None, data_emp=None, *args, **kwargs):
        super().__init__(master)
        self.emp_creation = None
        self._id_sm_to_modify = None
        self.permissions = data_emp["permissions"]
        self._id_emp = data_emp["id"]
        self.is_supper_user = self.check_permissions()
        self.history = None
        self.data_sm = None
        self.status_sm = None
        self.columns_sm = data["sm"]["columns_sm"]
        self.columnconfigure(0, weight=1)
        self.rowconfigure((0, 1), weight=1)
        self.style_gui = kwargs["style_gui"]
        # ----------------------variables-------------------------------------
        self.svar_info_history = ttk.StringVar(value="************Selecciones un item de la tabla*********************")
        self.svar_range_selector = ttk.StringVar(value="day")
        #  --------------------------graphs-----------------------------------
        self.frame_graphs = ttk.Frame(self)
        self.frame_graphs.grid(row=0, column=0, padx=(10, 25), pady=10, sticky="nswe", columnspan=1)
        self.frame_graphs.columnconfigure(0, weight=1)
        frame_selector = ttk.Frame(self.frame_graphs)
        frame_selector.grid(row=0, column=0, sticky="nswe")
        frame_selector.columnconfigure(0, weight=1)
        self.range_selector = create_Combobox(master=frame_selector, row=0, column=0, values=["day", "month", "year"], 
                                              width=10, textvariable=self.svar_range_selector, sticky="w")
        self.range_selector.bind("<<ComboboxSelected>>", self.change_plot_type)
        # create_Combobox(master=frame_selector, row=0, column=1, values=["normal", "all"],
        #                 command=self.change_plot_type, width=10)
        self.plots = create_plots(self.frame_graphs, self.svar_range_selector.get(), data["data_dashboard"]["sm"]["data_chart"])
        # --------------------------table SMs---------------------+--------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        create_label(self.frame_table, 0, 0, text="SMs en la base de datos", font=("Arial", 24, "bold"), columnspan=2)
        ttk.Button(self.frame_table, text="Marca de recibido", command=self._on_recieved_sm).grid(row=1, column=0, sticky="n")
        if self.is_supper_user:
            self.table_events = self.create_table(
                self.frame_table, data=data["sm"]["data_sm"], columns=data["sm"]["columns_sm"])
        else:
            self.table_events = self.create_table(
                self.frame_table, data=data["sm"]["data_sm_not_supper"], columns=data["sm"]["columns_sm"])
        # ----------------------- history sm-----------------------------------
        self.info_history = ScrolledText(self.frame_table, padding=5, height=10, autohide=True)
        self.info_history.grid(row=2, column=1, padx=5, pady=10, sticky="n")
        # create_label(self.frame_table, 2, 1, textvariable=self.svar_info_history, sticky="nswe")

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
        self.on_reset_widgets_click()
        row = event.widget.item(event.widget.selection()[0], "values")
        data_dic = self.get_sm_values_row(row)
        self.status_sm = data_dic["status"]
        self._id_sm_to_modify = int(data_dic["id"])
        self.history = json.loads(data_dic["history"])
        self.emp_creation = int(row[8])
        tag_names = ["line1", "line2"]
        for i, item in enumerate(self.history):
            self.info_history.text.insert(ttk.END, f"Evento de {item['event']} por el usuario {item['user']} en la fecha: {item['date']}\n", tag_names[i % 2])
            # msg += f"Evento de {item['event']} por el usuario {item['user']} en la fecha: {item['date']}\n"
        # self.svar_info_history.set(msg)
        self.info_history.text.tag_config("line1", foreground=self.style_gui.colors.get("warning"))
        self.info_history.text.tag_config("line2", foreground=self.style_gui.colors.get("fg"))

    def on_reset_widgets_click(self):
        self.svar_info_history.set("************Selecciones un item de la tabla*********************")
        self.info_history.text.delete("1.0", "end")

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
            msg = f"SM con ID-{self._id_sm_to_modify} marcada como recibida"
            create_notification_permission(msg, ["sm", "almacen"], "SM marcada como recibida", self._id_emp, self.emp_creation)

    def change_plot_type(self, event):
        range_selected = self.svar_range_selector.get()
        if isinstance(self.plots, tuple):
            for plot in self.plots:
                plot.destroy()
        else:
            self.plots.destroy()
        self.plots = create_plots(self.frame_graphs, range_selected)
