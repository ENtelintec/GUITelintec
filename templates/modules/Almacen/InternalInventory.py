import time
from templates.controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview
import ttkbootstrap as ttk

class InternalInventoryScreen(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._products = self.fetch_internal_stock()
        self._table = Tableview(self)
        self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the Inventory screen, includes the table of products and the inputs to add a new product"""
        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        content.columnconfigure(0, weight=1)
        ttk.Label(
            content,
            text="Inventario Interno",
            style="bg.TLabel",
            font=("Arial Black", 25),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.grid(row=1, column=0, sticky="nswe")
        table.columnconfigure(0, weight=1)
        ttk.Label(
            table, text="Tabla de Productos", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        self.col_data = [
            {"text": "ID Producto", "stretch": True},
            {"text": "SKU", "stretch": True},
            {"text": "Nombre", "stretch": True},
            {"text": "Contrato", "stretch": True},
            {"text": "stock", "stretch": True},
        ]

        self.table = Tableview(
            master=table,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
        )
        self.table.build_table_data(self.col_data, self._products)
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
        inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        inputs_left.grid(row=1, column=0, sticky="nswe")

        # Inputs left
        ttk.Label(inputs_left, text="ID", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_id = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_product_id.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="SKU", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_sku = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_product_sku.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Nombre", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.input_produt_name = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_produt_name.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="stock", style="bg.TLabel").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_stock = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_product_stock.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Contrato", style="bg.TLabel").grid(
            row=4, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_contract = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_product_contract.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.grid(row=3, column=0, sticky="w")
        buttons.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(
            buttons,
            text="Agregar Producto",
            style="bg.TButton",
            width=25,
            command=self.add_product,
        ).grid(row=0, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Actualizar Producto",
            style="bg.TButton",
            width=25,
            command=self.update_product,
        ).grid(row=0, column=1, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Eliminar Producto",
            style="bg.TButton",
            width=25,
            command=self.delete_product,
        ).grid(row=0, column=2, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Limpiar Campos",
            style="bg.TButton",
            width=25,
            command=self.clear_fields,
        ).grid(row=0, column=3, sticky="w", ipady=5, pady=(16, 0), padx=10)

    def fetch_internal_stock(self):
        return self._data._internal_stock.fetch_internal_stock()

    def events(self, event):
        data = self.table.view.item(self.table.view.focus())["values"]
        self.input_product_id.delete(0, "end")
        self.input_product_id.insert(0, data[0])
        self.input_product_sku.delete(0, "end")
        self.input_product_sku.insert(0, data[1])
        self.input_produt_name.delete(0, "end")
        self.input_produt_name.insert(0, data[2])
        self.input_product_stock.delete(0, "end")
        self.input_product_stock.insert(0, data[3])
        self.input_product_contract.delete(0, "end")
        self.input_product_contract.insert(0, data[4])

    def update_table(self):
        self._products = self.fetch_internal_stock()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._products)
        self.table.autofit_columns()

    def update_product(self):
        product_id = self.input_product_id.get()
        product_sku = self.input_product_sku.get()
        product_name = self.input_produt_name.get()
        product_stock = self.input_product_stock.get()
        product_contract = self.input_product_contract.get()

        self._data._internal_stock.update_product_internal(
            product_id,
            product_sku,
            product_name,
            product_contract,
            product_stock,
        )
        time.sleep(0.5)
        self.clear_fields()
        time.sleep(0.5)
        self.update_table()

    def clear_fields(self):
        self.input_product_id.delete(0, "end")
        self.input_product_sku.delete(0, "end")
        self.input_produt_name.delete(0, "end")
        self.input_product_stock.delete(0, "end")
        self.input_product_contract.delete(0, "end")

    def add_product(self):
        product_id = self.input_product_id.get()
        product_name = self.input_produt_name.get()
        product_stock = self.input_product_stock.get()
        product_sku = self.input_product_sku.get()
        product_contract = self.input_product_contract.get()

        if product_name == "" or product_stock == "" or product_sku == "":
            print("Error")
            return

        if product_id == "":
            self._data._internal_stock.create_product_internal(
                product_sku,
                product_name,
                product_contract,
                product_stock,
            )
            time.sleep(0.5)
            self.clear_fields()
            time.sleep(0.5)
            self.update_table()

    def delete_product(self):
        product_id = self.input_product_id.get()
        if product_id == "":
            return
        self._data._internal_stock.delete_product_internal(product_id)
        time.sleep(0.5)
        self.clear_fields()
        time.sleep(0.5)
        self.update_table()
