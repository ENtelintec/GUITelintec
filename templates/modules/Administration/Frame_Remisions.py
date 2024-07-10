# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/jul./2024  at 17:30 $'

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_GUI_Utils import create_label, create_button


def create_input_widgets(master, data_remisiones):
    entries = []
    return entries


class RemisionsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.id_product = None
        self.coldata = None
        self.table_widgets = None
        self.data_remisiones = kwargs["data"]["remisions"] if "remisions" in kwargs["data"] else []
        # -----------------Title-------------------------------
        create_label(self, 0, 0, text="Cotizaciones", font=("Helvetica", 30, "bold"), columnspan=1)
        # -----------------Inputs------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure(0, weight=1)
        self.entries = create_input_widgets(frame_inputs, self.data_remisiones)
        # -----------------Buttons-----------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.create_button_widgets(frame_buttons)
        # -----------------Table-------------------------------
        frame_table = ttk.Frame(self)
        frame_table.grid(row=3, column=0, sticky="nswe")
        frame_table.rowconfigure(0, weight=1)
        self.table_widgets = self.create_table_widgets(frame_table)
        # # -----------------btns procces------------------------------
        # frame_procces = ttk.Frame(self)
        # frame_procces.grid(row=4, column=0, sticky="nswe")
        # frame_procces.columnconfigure((0, 1, 2, 3), weight=1)
        # self.create_procces_btns(frame_procces)

    def create_button_widgets(self, frame_buttons):
        create_button(frame_buttons, 0, 0, sticky="n", text="Insertar", command=self.insert_remision)
        create_button(frame_buttons, 0, 1, sticky="n", text="Actualizar", command=self.update_remision)
        create_button(frame_buttons, 0, 2, sticky="n", text="Eliminar", command=self.delete_remision)
        create_button(frame_buttons, 0, 3, sticky="n", text="Limpiar", command=self.clear_inputs)
        create_button(frame_buttons, 0, 4, sticky="n", text="Nuevo", command=self.new_product)

    def get_data_entries(self):
        data = [item.get() for item in self.entries]
        return data

    def insert_remision(self):
        data = self.get_data_entries()
        name = self.entries[7].get()
        quantity = self.entries[8].get()
        udm = self.entries[9].get()
        price = self.entries[10].get()
        price = price if price != "" else 0.0
        items = self.table_widgets.view.get_children()
        number = len(items) + 1
        data = [number, self.id_product, name, quantity, udm, price, float(quantity) * float(price)]
        self.table_widgets.insert_row(values=data)

    def update_remision(self):
        items = self.table_widgets.view.get_children()
        for item in items:
            values = self.table_widgets.view.item(item, "values")
            if values[0] == self._number_product:
                data = self.get_data_entries()
                name = self.entries[7].get()
                quantity = self.entries[8].get()
                udm = self.entries[9].get()
                price = self.entries[10].get()
                data = [self._number_product, self.id_product, name, quantity, udm, price,
                        float(quantity) * float(price)]
                self.table_widgets.view.item(item, values=data)
                break

    def delete_remision(self):
        items = self.table_widgets.view.get_children()
        for item in items:
            values = self.table_widgets.view.item(item, "values")
            if values[0] == self._number_product:
                self.table_widgets.view.delete(item)
                break

    def clear_inputs(self):
        for item in self.entries:
            if isinstance(item, ttk.Combobox):
                item.set("")
            else:
                item.delete(0, 'end')

    def new_product(self):
        pass

    def create_table_widgets(self, master):
        self.table_widgets.destroy() if self.table_widgets is not None else None
        coldata = []
        columns = ["#", "ID", "Descripcion", "Cantidad", "UDM", "Precio unitario", "Total"]
        for column in columns:
            if "Descripcion" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "#" in column:
                coldata.append({"text": column, "stretch": False, "width": 25})
            else:
                coldata.append({"text": column, "stretch": True})
        self.coldata = coldata
        data = []
        table_notifications = Tableview(master,
                                        coldata=coldata,
                                        autofit=False,
                                        paginated=False,
                                        searchable=False,
                                        rowdata=data,
                                        height=15)
        table_notifications.grid(row=1, column=0, sticky="nswe", padx=(5, 30))
        table_notifications.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table_notifications.get_columns()
        for item in columns_header:
            if item.headertext in ["id"]:
                item.hide()
        return table_notifications

    def _on_double_click_table(self, event):
        data = event.widget.item(event.widget.selection(), "values")
        self._number_product = data[0]
        print(data)

