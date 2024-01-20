import time
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview


class InventoryScreen(ScrolledFrame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, style="bg.TFrame")
        self.master = master
        self.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._products = self.fetch_products()
        self._table = Tableview(self)
        self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the Inventory screen, includes the table of products and the inputs to add a new product"""
        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        ttk.Label(
            content, text="Productos", style="bg.TLabel", font=("Arial Black", 25)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.grid(row=1, column=0, sticky="nswe")
        ttk.Label(
            table, text="Tabla de Productos", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        self.col_data = [
            {"text": "ID Producto", "stretch": True},
            {"text": "Nombre", "stretch": True},
            {"text": "Descripción", "stretch": False},
            {"text": "Precio", "stretch": True},
            {"text": "Stock", "stretch": True},
            {"text": "MinStock", "stretch": True},
            {"text": "MaxStock", "stretch": True},
            {"text": "ReorderPoint", "stretch": True},
            {"text": "Categoría", "stretch": False},
            {"text": "Proveedor", "stretch": False},
        ]

        self.table = Tableview(
            master=table,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
        )
        self.table.build_table_data(self.col_data, self._products)
        self.table.autofit_columns()
        self.table.grid(row=1, column=0, sticky="nswe")
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.grid(row=2, column=0, sticky="nswe")
        ttk.Label(
            inputs, text="Agregar nuevo cliente", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10)

        # dividir el frame en 2, izq y derecha para los inputs
        inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        inputs_left.grid(row=1, column=0, sticky="nswe")

        inputs_right = ttk.Frame(inputs, style="bg.TFrame")
        inputs_right.grid(row=1, column=1, sticky="nswe")

        extra_inputs = ttk.Frame(inputs, style="bg.TFrame")
        extra_inputs.grid(row=1, column=2, sticky="nswe")

        # Inputs left

        ttk.Label(inputs_left, text="ID", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_id = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_product_id.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Nombre", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_name = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_product_name.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Descripción", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.input_produt_description = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_produt_description.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Precio", style="bg.TLabel").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_price = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_product_price.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # inputs right
        ttk.Label(inputs_right, text="Stock", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_stock = ttk.Entry(inputs_right, style="bg.TEntry")
        self.input_product_stock.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_right, text="MinStock", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_minStock = ttk.Entry(inputs_right, style="bg.TEntry")
        self.input_product_minStock.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_right, text="MaxStock", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_maxStock = ttk.Entry(inputs_right, style="bg.TEntry")
        self.input_product_maxStock.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_right, text="ReorderPoint", style="bg.TLabel").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.input_product_reorderPoint = ttk.Entry(inputs_right, style="bg.TEntry")
        self.input_product_reorderPoint.grid(
            row=3, column=1, sticky="w", padx=5, pady=5
        )

        ttk.Label(extra_inputs, text="Categoría", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.values_cat = self._data._product_categories.get_all_categories()
        self.dropdown_category_selector = ttk.Combobox(
            extra_inputs, values=self.values_cat, style="bg.TCombobox"
        )
        self.dropdown_category_selector.grid(
            row=0, column=1, sticky="w", padx=5, pady=5
        )

        ttk.Label(extra_inputs, text="Proveedor", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.values_supp = self._data._supplier.get_all_suppliers()
        self.dropdown_supplier_selector = ttk.Combobox(
            extra_inputs, values=self.values_supp, style="bg.TCombobox"
        )
        self.dropdown_supplier_selector.grid(
            row=1, column=1, sticky="w", padx=5, pady=5
        )

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.grid(row=3, column=0, sticky="nswe")

        ttk.Button(
            buttons,
            text="Agregar",
            style="bg.TButton",
            width=25,
            command=self.add_product,
        ).grid(row=0, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Editar",
            style="bg.TButton",
            width=25,
            command=self.update_product,
        ).grid(row=0, column=1, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Eliminar",
            style="bg.TButton",
            width=25,
            command=self.delete_product,
        ).grid(row=0, column=2, sticky="w", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Limpiar",
            style="bg.TButton",
            width=25,
            command=self.clear_fields,
        ).grid(row=0, column=3, sticky="w", ipady=5, pady=(16, 0), padx=10)

    def fetch_products(self):
        return self._data._product.get_all_products()

    def events(self, event):
        data = self.table.view.item(self.table.view.focus())["values"]
        self.input_product_id.delete(0, "end")
        self.input_product_id.insert(0, data[0])

        self.input_product_name.delete(0, "end")
        self.input_product_name.insert(0, data[1])

        self.input_produt_description.delete(0, "end")
        self.input_produt_description.insert(0, data[2])

        self.input_product_price.delete(0, "end")
        self.input_product_price.insert(0, data[3])

        self.input_product_stock.delete(0, "end")
        self.input_product_stock.insert(0, data[4])

        self.input_product_minStock.delete(0, "end")
        self.input_product_minStock.insert(0, data[5])

        self.input_product_maxStock.delete(0, "end")
        self.input_product_maxStock.insert(0, data[6])

        self.input_product_reorderPoint.delete(0, "end")
        self.input_product_reorderPoint.insert(0, data[7])

        self.dropdown_category_selector.set(data[8])

        self.dropdown_supplier_selector.set(data[9])

    def update_table(self):
        self._products = self.fetch_products()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._products)
        self.table.autofit_columns()

    def update_product(self):
        product_id = self.input_product_id.get()
        product_name = self.input_product_name.get()
        product_description = self.input_produt_description.get()
        product_price = self.input_product_price.get()
        product_stock = self.input_product_stock.get()
        product_minStock = self.input_product_minStock.get()
        product_maxStock = self.input_product_maxStock.get()
        product_reorderPoint = self.input_product_reorderPoint.get()
        product_category = self.dropdown_category_selector.get()
        product_supplier = self.dropdown_supplier_selector.get()

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

        self._data._product.update_product(
            product_id,
            product_name,
            product_description,
            product_price,
            product_stock,
            product_minStock,
            product_maxStock,
            product_reorderPoint,
            product_category,
            product_supplier,
        )
        time.sleep(0.5)
        self.clear_fields()
        time.sleep(0.5)
        self.update_table()

    def clear_fields(self):
        self.input_product_id.delete(0, "end")
        self.input_product_name.delete(0, "end")
        self.input_produt_description.delete(0, "end")
        self.input_product_price.delete(0, "end")
        self.input_product_stock.delete(0, "end")
        self.input_product_minStock.delete(0, "end")
        self.input_product_maxStock.delete(0, "end")
        self.input_product_reorderPoint.delete(0, "end")
        self.dropdown_category_selector.set("")
        self.dropdown_supplier_selector.set("")

    def add_product(self):
        product_id = self.input_product_id.get()
        product_name = self.input_product_name.get()
        product_description = self.input_produt_description.get()
        product_price = self.input_product_price.get()
        product_stock = self.input_product_stock.get()
        product_minStock = self.input_product_minStock.get()
        product_maxStock = self.input_product_maxStock.get()
        product_reorderPoint = self.input_product_reorderPoint.get()
        product_category = self.dropdown_category_selector.get()
        product_supplier = self.dropdown_supplier_selector.get()

        if (
            product_name == ""
            or product_description == ""
            or product_price == ""
            or product_stock == ""
            or product_minStock == ""
            or product_maxStock == ""
            or product_reorderPoint == ""
            or product_category == ""
            or product_supplier == ""
        ):
            print("Error")
            return

        if product_id == "":
            self._data._product.create_product(
                product_name,
                product_description,
                product_price,
                product_stock,
                product_minStock,
                product_maxStock,
                product_reorderPoint,
                product_category[0],
                product_supplier[0],
            )
            time.sleep(0.5)
            self.clear_fields()
            time.sleep(0.5)
            self.update_table()

    def delete_product(self):
        product_id = self.input_product_id.get()
        if product_id == "":
            return
        self._data._product.delete_product(product_id)
        time.sleep(0.5)
        self.clear_fields()
        time.sleep(0.5)
        self.update_table()
