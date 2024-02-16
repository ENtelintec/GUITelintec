import time
import re
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from templates.controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview


class OrdersScreen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._products = self.fetch_products()
        self._table = Tableview(self)
        self._orders = self._data._order.get_all_orders()
        self._products = self._data._product.get_all_products()
        self._clients = self._data._customer.get_all_customers()
        self.customer_id = None
        # self._complete_order = list(filter(lambda x: x[2] == "complete", self._orders))
        # self._incomplete_order = list(filter(lambda x: x[2] == "pending", self._orders))
        # self._shipped_order = list(filter(lambda x: x[2] == "processing", self._orders))
        self._complete_order = 0
        self._incomplete_order = 0
        self._shipped_order = 0
        self._products_entries = []
        self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the Orders screen, includes the table of orders and the inputs to modify an order"""

        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        content.columnconfigure(0, weight=1)
        ttk.Label(
            content, text="Inventario", style="bg.TLabel", font=("Arial Black", 25)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.grid(row=1, column=0, sticky="nswe")
        table.columnconfigure(0, weight=1)
        ttk.Label(
            table, text="Tabla de Ordenes", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        self.col_data = [
            {"text": "ID Orden", "stretch": True},
            {"text": "ID Cliente", "stretch": True},
            {"text": "Nombre del Cliente", "stretch": True},
            {"text": "Fecha", "stretch": True},
            {"text": "Estatus", "stretch": True},
            {"text": "Productos", "stretch": True},
        ]

        self.table = Tableview(
            master=table,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
        )
        self.table.build_table_data(self.col_data, self._orders)
        self.table.grid(row=1, column=0, sticky="nswe", padx=15, pady=5)
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.grid(row=2, column=0, sticky="nswe")
        inputs.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Label(
            inputs, text="Agregar nuevo producto", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10)

        # dividir el frame en 2, izq y derecha para los inputs
        self.inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        self.inputs_left.grid(row=1, column=0, sticky="nswe")

        self.inputs_right = ttk.Frame(inputs, style="bg.TFrame")
        self.inputs_right.grid(row=1, column=1, sticky="nswe")

        # Inputs left
        ttk.Label(self.inputs_left, text="Id de la Orden", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.input_order_id = ttk.Entry(self.inputs_left, style="bg.TEntry")
        self.input_order_id.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(self.inputs_left, text="Id del Cliente", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.input_client_id = ttk.Combobox(self.inputs_left, values=self._clients)
        self.input_client_id.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(self.inputs_left, text="Estatus", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.input_order_status = ttk.Combobox(
            self.inputs_left, values=["pending", "urgent", "processing", "complete"]
        )
        self.input_order_status.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # inputs right
        ttk.Label(self.inputs_right, text="ID del producto", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_id = ttk.Combobox(self.inputs_right, values=self._products)
        self.input_product_id.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Button(
            self.inputs_right,
            text="Agregar Producto",
            style="bg.TButton",
            width=25,
            command=self.add_product_entry,
        ).grid(row=3, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            self.inputs_right,
            text="Eliminar Producto",
            style="bg.TButton",
            width=25,
            command=self.remove_product_entry,
        ).grid(row=3, column=1, sticky="w", ipady=5, pady=(16, 0), padx=10)

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.grid(row=3, column=0, sticky="w")
        buttons.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(
            buttons,
            text="Agregar",
            style="bg.TButton",
            width=25,
            command=self.create_order,
        ).grid(row=0, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Editar",
            style="bg.TButton",
            width=25,
            command=self.update_order,
        ).grid(row=0, column=1, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Eliminar",
            style="bg.TButton",
            width=25,
            command=self.delete_order,
        ).grid(row=0, column=2, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Limpiar",
            style="bg.TButton",
            width=25,
            command=self.clear_fields,
        ).grid(row=0, column=3, sticky="w", ipady=5, pady=(16, 0), padx=10)

    def add_product_entry(self):
        row_index = len(self._products_entries) + 4
        selected_product = self.input_product_id.get()

        # validar que el producto no esté ya en la lista
        for product_entry, _ in self._products_entries:
            if product_entry.get() == selected_product:
                return

        if self._products_entries == []:
            product_entry = ttk.Entry(self.inputs_right)
            product_entry.grid(row=row_index, column=1, sticky="w", padx=5, pady=5)
            product_entry.insert(0, selected_product)
            product_entry.state(["readonly"])

            quantity_entry = ttk.Entry(self.inputs_right)
            quantity_entry.grid(row=row_index, column=3, sticky="w", padx=5, pady=5)
            quantity_entry.insert(0, "1")
        else:
            product_entry = ttk.Entry(self.inputs_right)
            product_entry.grid(row=row_index + 1, column=1, sticky="w", padx=5, pady=5)
            product_entry.insert(0, selected_product)
            product_entry.state(["readonly"])

            quantity_entry = ttk.Entry(self.inputs_right)
            quantity_entry.grid(row=row_index + 1, column=3, sticky="w", padx=5, pady=5)
            quantity_entry.insert(0, "1")

        self._products_entries.append((product_entry, quantity_entry))

    def remove_product_entry(self):
        if self._products_entries:
            product_entry, quantity_entry = self._products_entries.pop()
            product_entry.grid_forget()
            product_entry.destroy()
            quantity_entry.grid_forget()
            quantity_entry.destroy()

    def get_product_entries(self):
        products = [
            (product_entry.get(), quantity_entry.get())
            for product_entry, quantity_entry in self._products_entries
        ]
        return products

    def fetch_products(self):
        return self._data._product.get_all_products()

    def events(self, event):
        self.clear_fields()
        data = self.table.view.item(self.table.view.focus())["values"]
        self.input_order_id.insert(0, data[0])
        self.input_client_id.insert(0, str(data[1]) + " " + str(data[2]))
        self.input_order_status.insert(0, data[4])
        products = data[5].split("; ")
        self._products_entries = []
        for product in products:
            self.add_product_entry_from_event(
                (product.split(" : ")[0] + " " + product.split(" : ")[1]),
                product.split(" : ")[2],
            )

    def add_product_entry_from_event(self, product, quantity):
        row_index = len(self._products_entries) + 4
        selected_product = product

        product_entry = ttk.Entry(self.inputs_right)
        product_entry.grid(row=row_index, column=1, sticky="w", padx=5, pady=5)
        product_entry.insert(0, selected_product)
        product_entry.state(["readonly"])

        quantity_entry = ttk.Entry(self.inputs_right)
        quantity_entry.grid(row=row_index, column=3, sticky="w", padx=5, pady=5)
        quantity_entry.insert(0, "1")

        self._products_entries.append((product_entry, quantity_entry))

    def update_table(self):
        self._orders = self._data._order.get_all_orders()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._orders)
        self.table.autofit_columns()

    def clear_fields(self):
        self.input_order_id.delete(0, "end")
        self.input_client_id.delete(0, "end")
        self.input_order_status.delete(0, "end")
        self.input_product_id.delete(0, "end")
        lengt_entries = len(self._products_entries)
        for i in range(lengt_entries):
            self.remove_product_entry()

    def create_order(self):
        customer_id = self.input_client_id.get().split(" ")[0]
        status = self.input_order_status.get()
        products_ids = self.get_product_entries()
        self._data._order.create_order(customer_id, status, products_ids)
        self.clear_fields()
        self.update_table()

    def update_order(self):
        order_id = self.input_order_id.get()
        customer_id = self.input_client_id.get().split(" ")[0]
        status = self.input_order_status.get()
        products_list = self.get_product_entries()
        self._data._order.update_order(order_id, customer_id, status, products_list)
        self.clear_fields()
        self.update_table()

    def delete_order(self):
        order_id = self.input_order_id.get()
        self._data._order.delete_order(order_id)
        self.clear_fields()
        self.update_table()
