import time
from datetime import datetime
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from templates.controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview


class InScreen(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._products = self._data._product.get_all_products()
        self._ins = self._data._product_movements.get_ins()
        self._table = Tableview(self)
        self.create_content(self)
        self.movetement_id = None

    def create_content(self, parent):
        """Creates the content of the Inputs screen, includes the table of inputs and the inputs to add a new entrs"""
        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        content.columnconfigure(0, weight=1)
        ttk.Label(content, text="Entradas", font=("Arial Black", 25)).grid(
            row=0, column=0, sticky="nswe", padx=5, pady=10
        )

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.grid(row=1, column=0, sticky="nswe")
        table.columnconfigure(0, weight=1)
        ttk.Label(
            table, text="Tabla de Entradas", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)
        self.col_data = [
            {"text": "ID Movimiento", "stretch": True},
            {"text": "ID Producto", "stretch": True},
            {"text": "Tipo de Movimiento", "stretch": True},
            {"text": "Cantidad", "stretch": True},
            {"text": "Fecha", "stretch": False},
            {"text": "Nombre producto", "stretch": False},
        ]
        self.table = Tableview(
            master=table,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
        )
        self.table.build_table_data(self.col_data, self._ins)
        self.table.grid(row=1, column=0, sticky="nswe", padx=15, pady=5, columnspan=2)
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.grid(row=2, column=0, sticky="nswe")
        inputs.columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Label(
            inputs, text="Agregar nueva entrada", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        inputs_left.grid(row=1, column=0, sticky="nswe")

        # Inputs left
        ttk.Label(inputs_left, text="Producto", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.products_selector = ttk.Combobox(inputs_left, values=self._products)
        self.products_selector.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Cantidad", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.quantity = ttk.Entry(inputs_left)
        self.quantity.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Fecha de entrada", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.date = ttk.Entry(inputs_left)
        self.date.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        current_date = datetime.now()
        self.date.insert(0, current_date)

        # Buttons
        button_frame = ttk.Frame(self, style="bg.TFrame")
        button_frame.grid(row=7, column=0, sticky="w", padx=5, pady=5, columnspan=2)
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(
            button_frame,
            text="Agregar Entrada",
            style="bg.TButton",
            width=25,
            command=self.add_in_item,
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Button(
            button_frame,
            text="Actualizar Entrada",
            style="bg.TButton",
            width=25,
            command=self.update_in_item,
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(
            button_frame,
            text="Eliminar Entrada",
            style="bg.TButton",
            width=25,
            command=self.delete_in_item,
        ).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Button(
            button_frame,
            text="Limpiar Campos",
            style="bg.TButton",
            width=25,
            command=self.clear_fields,
        ).grid(row=0, column=3, sticky="w", padx=5, pady=5)

    def clear_fields(self):
        self.products_selector.set("")
        self.quantity.delete(0, "end")
        current_date = datetime.now()
        self.date.delete(0, "end")
        self.date.insert(0, current_date)

    def events(self, event):
        data = self.table.view.item(self.table.view.focus())["values"]
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
            self.movetement_id, quantity, new_date
        )
        self.update_table()
        self.clear_fields()

    def add_in_item(self):
        self.movetement_id = self.products_selector.get().split()[0]
        if self.movetement_id is None:
            return
        id_product = self.products_selector.get().split()[0]
        id_movement_type = "entrada"
        quantity = self.quantity.get()
        movement_date = self.date.get()
        self._data._product_movements.create_in_movement(
            id_product, id_movement_type, quantity, movement_date
        )
        self.update_table()
        self.clear_fields()

    def delete_in_item(self):
        if self.movetement_id is None:
            return
        self._data._product_movements.delete_in_movement(self.movetement_id)
        self.update_table()
        self.clear_fields()
