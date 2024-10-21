import time
import ttkbootstrap as ttk

from templates.controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview


class InventoryScreen(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.table = None
        self.col_data = None
        self.id_to_modify = None
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._ivar_tool = ttk.IntVar(value=0)
        self._ivar_internal = ttk.IntVar(value=0)
        self._products = (
            self.fetch_products()
            if "data_products_gen" not in kwargs["data"]
            else kwargs["data"]["data_products_gen"]
        )
        self._table = Tableview(self)
        self.entries = self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the Inventory screen, includes the table of products and the inputs to add a new product"""
        content = ttk.Frame(parent)
        content.grid(row=0, column=0, sticky="nswe")
        content.columnconfigure(0, weight=1)
        ttk.Label(content, text="Inventario", font=("Arial Black", 25)).grid(
            row=0, column=0, sticky="nswe", padx=5, pady=10
        )

        # Table
        table = ttk.Frame(content)
        table.grid(row=1, column=0, sticky="nswe")
        table.columnconfigure(0, weight=1)
        ttk.Label(
            table, text="Tabla de Productos", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        self.col_data = [
            {"text": "ID Producto", "stretch": True},
            {"text": "SKU", "stretch": True},
            {"text": "Nombre", "stretch": True},
            {"text": "UDM", "stretch": True},
            {"text": "Stock", "stretch": True},
            {"text": "Categoría", "stretch": True},
            {"text": "Proveedor", "stretch": True},
            {"text": "Herramienta", "stretch": True},
            {"text": "Interno", "stretch": True},
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
        inputs = ttk.Frame(content)
        inputs.grid(row=2, column=0, sticky="nswe")
        inputs.columnconfigure((0, 1, 2, 3, 4), weight=1)
        ttk.Label(
            inputs, text="Agregar nuevo producto", style="bg.TLabel", font=("Arial", 20)
        ).grid(
            row=0, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10, columnspan=5
        )

        # Inputs left
        ttk.Label(inputs, text="ID", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_id = ttk.Entry(inputs, style="bg.TEntry")
        self.input_product_id.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs, text="SKU", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_name = ttk.Entry(inputs, style="bg.TEntry")
        self.input_product_name.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs, text="Nombre", style="bg.TLabel").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.input_produt_description = ttk.Entry(inputs, style="bg.TEntry")
        self.input_produt_description.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs, text="UDM", style="bg.TLabel").grid(
            row=4, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_udm = ttk.Entry(inputs, style="bg.TEntry")
        self.input_product_udm.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # inputs right
        ttk.Label(inputs, text="Stock", style="bg.TLabel").grid(
            row=1, column=2, sticky="w", padx=5, pady=5
        )
        self.input_product_stock = ttk.Entry(inputs, style="bg.TEntry")
        self.input_product_stock.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(inputs, text="Categoría", style="bg.TLabel").grid(
            row=2, column=2, sticky="w", padx=5, pady=5
        )
        self.values_cat = self._data.get_all_categories()
        # self.values_cat_filter = [name for _, name in self.values_cat]
        self.dropdown_category_selector = ttk.Combobox(
            inputs, values=self.values_cat, style="bg.TCombobox"
        )
        self.dropdown_category_selector.grid(
            row=2, column=3, sticky="w", padx=5, pady=5
        )

        ttk.Label(inputs, text="Proveedor", style="bg.TLabel").grid(
            row=3, column=2, sticky="w", padx=5, pady=5
        )
        self.values_supp = self._data.get_all_suppliers()
        self.dropdown_supplier_selector = ttk.Combobox(
            inputs, values=self.values_supp, style="bg.TCombobox"
        )
        self.dropdown_supplier_selector.grid(
            row=3, column=3, sticky="w", padx=5, pady=5
        )

        ttk.Checkbutton(
            inputs,
            text="Es herramienta?",
            variable=self._ivar_tool,
            onvalue=1,
            offvalue=0,
            bootstyle="success, round-toggle",
        ).grid(row=1, column=4, sticky="w", padx=5, pady=5, columnspan=2)
        ttk.Checkbutton(
            inputs,
            text="Es interno?",
            variable=self._ivar_internal,
            onvalue=1,
            offvalue=0,
            bootstyle="success, round-toggle",
        ).grid(row=2, column=4, sticky="w", padx=5, pady=5, columnspan=2)

        # Buttons
        buttons = ttk.Frame(content)
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
        return [
            self.input_product_id,
            self.input_product_name,
            self.input_produt_description,
            self.input_product_udm,
            self.input_product_stock,
            self.dropdown_category_selector.set(""),
            self.dropdown_supplier_selector.set(""),
            self._ivar_tool,
            self._ivar_internal,
        ]

    def fetch_products(self):
        return self._data.get_all_products()

    def events(self, event):
        item = event.widget.item(event.widget.selection()[0])
        data = item["values"]
        self.clear_fields()
        self.input_product_id.insert(0, data[0])
        self.input_product_name.insert(0, data[1])
        self.input_produt_description.insert(0, data[2])
        self.input_product_udm.insert(0, data[3])
        self.input_product_stock.insert(0, data[4])
        self.dropdown_category_selector.set(data[5])
        self.dropdown_supplier_selector.set(data[6])
        self._ivar_tool.set(data[7])
        self._ivar_internal.set(data[8])

    def update_table(self):
        self._products = self.fetch_products()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._products)
        self.table.autofit_columns()

    def get_inputs_valus(self):
        product_id = self.input_product_id.get()
        product_name = self.input_product_name.get()
        product_description = self.input_produt_description.get()
        product_price = self.input_product_udm.get()
        product_stock = self.input_product_stock.get()
        product_category = self.dropdown_category_selector.get().split(" ")[0]
        product_supplier = self.dropdown_supplier_selector.get().split(" ")[0]
        is_tool = self._ivar_tool.get()
        is_internal = self._ivar_internal.get()
        return (
            product_id,
            product_name,
            product_description,
            product_price,
            product_stock,
            product_category,
            product_supplier,
            is_tool,
            is_internal,
        )

    def update_product(self):
        (
            product_id,
            product_name,
            product_description,
            product_price,
            product_stock,
            product_category,
            product_supplier,
            is_tool,
            is_internal,
        ) = self.get_inputs_valus()

        if product_category.__contains__(" "):
            product_category = product_category.split(" ")[0]
        else:
            for item in self.values_cat:
                if item[1] == product_category:
                    product_category = item[0]
        if product_supplier.__len__() > 11:
            product_supplier = product_supplier.split(" ")[0]
        else:
            for item in self.values_supp:
                if item[1] == product_supplier:
                    product_supplier = item[0]

        self._data.update_product(
            product_id,
            product_name,
            product_description,
            product_price,
            product_stock,
            product_category,
            product_supplier,
            is_tool,
            is_internal,
        )
        self.clear_fields()
        self.update_table()

    def clear_fields(self):
        for entry in self.entries:
            if isinstance(entry, ttk.Entry):
                entry.delete(0, "end")
            elif isinstance(entry, ttk.Combobox):
                entry.set(0)
        self.id_to_modify = None

    def add_product(self):
        (
            product_id,
            product_name,
            product_description,
            product_price,
            product_stock,
            product_category,
            product_supplier,
            is_tool,
            is_internal,
        ) = self.get_inputs_valus()
        if (
            product_name == ""
            or product_description == ""
            or product_price == ""
            or product_stock == ""
            or product_category == ""
            or product_supplier == ""
        ):
            print("Error")
            return

        if product_id == "":
            self._data.create_product(
                product_name,
                product_description,
                product_price,
                product_stock,
                product_category[0],
                product_supplier[0],
                is_tool,
                is_internal,
            )
            self.clear_fields()
            self.update_table()

    def delete_product(self):
        product_id = self.input_product_id.get()
        if product_id == "":
            return
        self._data.delete_product(product_id)
        self.clear_fields()
        self.update_table()
