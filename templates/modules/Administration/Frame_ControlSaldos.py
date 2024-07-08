# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/jul./2024  at 17:16 $'

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_GUI_Utils import create_label, create_button


class ControlSaldos(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.coldata = None
        self.table_contracts = None
        self.contracts = kwargs.get("data")["contracts"]
        # ----------------------------title---------------------------------
        create_label(self, 0, 0, text="Control de saldos", font=("Lora", 30, "bold"))
        # -----------------------------btns-----------------------------------
        self.frame_btns = ttk.Frame(self)
        self.frame_btns.grid(row=1, column=0, sticky="nswe")
        self.frame_btns.columnconfigure((0, 1, 2), weight=1)
        self.create_button_widgets(self.frame_btns)
        # --------------------------- table-----------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=2, column=0, sticky="nswe")
        self.frame_table.rowconfigure(0, weight=1)
        self.table_contracts = self.create_table()
    
    def create_table(self):
        self.table_contracts.destroy() if self.table_contracts is not None else None
        coldata = []
        columns = ["ID", "# Pedido", "Remitos", "Fecha Solicitud", "Coord. CECO/FAP", "Planta", "Area", "Descripción", "Estatus", "# SGD", 
                   "Fecha SGD", "Estatus Remision", "Fecha Remitos Enviados", "Estatus HES", "# HES", "Fecha Liberación", 
                   "Proyeccion de Saldo/pedido", "Remisión MXN", "Saldo Comprometido", "Saldo HES", "Saldo Facturado", "Observaciones"]
        for column in columns:
            if "Observaciones" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "#" in column:
                coldata.append({"text": column, "stretch": False, "width": 55})
            elif "ID" in column:
                coldata.append({"text": column, "stretch": False, "width": 45})
            else:
                coldata.append({"text": column, "stretch": True})
        data = self.contracts
        self.coldata = coldata
        table_notifications = Tableview(self.frame_table,
                                        coldata=coldata,
                                        autofit=False,
                                        paginated=False,
                                        searchable=False,
                                        rowdata=data,
                                        height=15)
        table_notifications.grid(row=0, column=0, sticky="nswe", padx=(5, 30))
        table_notifications.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table_notifications.get_columns()
        for item in columns_header:
            if item.headertext in ["id"]:
                item.hide()
        return table_notifications

    def _on_double_click_table(self, event):
        data = event.widget.item(event.widget.selection(), "values")
        print(data)

    def create_button_widgets(self, master):
        create_button(master, 0, 0, text="Generar PDF", command=self.generate_pdf_contract, bootstyle="primary", sticky="n")
        create_button(master, 0, 1, text="Editar", command=self.edit_contract, bootstyle="secondary", sticky="n")
        create_button(master, 0, 2, text="Eliminar", command=self.delete_contract, bootstyle="danger", sticky="n")
        
    def generate_pdf_contract(self):
        print("pdf")
    
    def edit_contract(self):
        print("edit")
        
    def delete_contract(self):
        print("delete")
        