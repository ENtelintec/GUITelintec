import time
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from widgets import *
from controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview


class InScreen(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self, style="bg.TFrame")
        self.pack(side="top", fill="both", expand=True)
        self._data = DataHandler()
        self._products = self._data._product.get_all_products()
        self._ins = self._data._product_movements.get_ins()
        self._table = Tableview(self)
        self.create_content(self)
        self.movetement_id = None

    def create_content(self, parent):
        '''Creates the content of the Inputs screen, includes the table of inputs and the inputs to add a new entrs'''
        content = ScrolledFrame(parent, style="bg.TFrame", autohide=True)
        content.pack(side="left", fill="both", expand=True)
        ttk.Label(content, text="Entradas", style="bg.TLabel", font=(
            "Arial Black", 25)).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.pack(side="top", fill="both", expand=True)
        ttk.Label(table, text="Tabla de Entradas", style="bg.TLabel",
                  font=("Arial", 20)).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        self.col_data = [{"text": "ID Movimiento", "stretch": True},
                         {"text": "ID Producto", "stretch": True},
                         {"text": "Tipo de Movimiento", "stretch": True},
                         {"text": "Cantidad", "stretch": True},
                         {"text": "Fecha", "stretch": False},
                         {"text": "Nombre producto", "stretch": False}]

        self.table = Tableview(master=table, bootstyle="primary",
                               coldata=self.col_data,
                               rowdata=self._ins,
                               paginated=True,
                               pagesize=10,
                               searchable=True)
        self.table.autofit_columns()
        self.table.pack()
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.pack(side="top", fill="both", expand=True)
        ttk.Label(inputs, text="Agregar nueva entrada",
                  style="bg.TLabel",  font=(
                      "Arial", 20)).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Label(inputs, text="Producto", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.products_selector = ttk.Combobox(inputs, values=self._products)
        self.products_selector.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Label(inputs, text="Cantidad", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.quantity = ttk.Entry(inputs)
        self.quantity.pack(side="top", fill="x", anchor="center", ipady=5,
                           pady=(16, 0), padx=10)
        ttk.Label(inputs, text="Fecha de entrada",
                  style="bg.TLabel").pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.date = ttk.Entry(inputs)
        self.date.pack(side="top", fill="x", anchor="center", ipady=5,
                       pady=(16, 0), padx=10)
        current_date = datetime.now()
        self.date.insert(0, current_date)

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.pack(side="top", fill="y", expand=True)
        ttk.Button(buttons, text="Agregar", style="bg.TButton", width=25, command=self.add_in_item).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(buttons, text="Editar", style="bg.TButton", width=25, command=self.update_in_item).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(buttons, text="Eliminar", style="bg.TButton", width=25, command=self.delete_in_item).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(buttons, text="Limpiar", style="bg.TButton", width=25, command=self.clear_fields).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    def clear_fields(self):
        self.products_selector.set('')
        self.quantity.delete(0, "end")
        current_date = datetime.now()
        self.date.delete(0, "end")
        self.date.insert(0, current_date)

    def events(self, event):
        data = self.table.view.item(self.table.view.focus())['values']
        self.products_selector.delete(0, "end")
        self.products_selector.insert(0, data[1])
        self.movetement_id = data[0]

    def update_table(self):
        self._ins = self._data._product_movements.get_ins()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._ins)
        self.table.autofit_columns()

    def update_in_item(self):
        if self.movetement_id is None:
            return
        new_date = datetime.now()
        quantity = self.quantity.get()
        self._data._product_movements.update_in_movement(
            self.movetement_id, quantity, new_date)
        self.update_table()
        self.clear_fields()

    def add_in_item(self):
        self.movetement_id = self.products_selector.get().split()[0]
        if self.movetement_id is None:
            return
        id_product = self.products_selector.get().split()[0]
        id_movement_type = 'entrada'
        quantity = self.quantity.get()
        movement_date = self.date.get()
        self._data._product_movements.create_in_movement(
            id_product, id_movement_type, quantity, movement_date)
        self.update_table()
        self.clear_fields()

    def delete_in_item(self):
        if self.movetement_id is None:
            return
        self._data._product_movements.delete_in_movement(self.movetement_id)
        self.update_table()
        self.clear_fields()
