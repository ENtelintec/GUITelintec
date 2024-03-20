import time
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from templates.controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview
import os
import pandas as pd
from tkinter import filedialog


class OrdersScreen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._products = self.fetch_products()
        self._table = Tableview(self)
        self._orders = self._data._order.get_all_orders_sm()
        self._products = self._data._product.get_all_products()
        self._clients = self._data._customer.get_all_customers()
        self.customer_id = None
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
            content, text="Ordenes", style="bg.TLabel", font=("Arial Black", 25)
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
            {"text": "Fecha Solicitud", "stretch": True},
            {"text": "SM", "stretch": True},
            {"text": "Contrato", "stretch": True},
            {"text": "Numero Orden", "stretch": True},
            {"text": "Planta", "stretch": True},
            {"text": "Ubicacion", "stretch": True},
            {"text": "Solicitante", "stretch": True},
            {"text": "Personal", "stretch": True},
            {"text": "Fecha Critica", "stretch": True},
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
            inputs, text="Agregar nueva Orden", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", ipady=5, pady=(16, 0), padx=10)

        # Button for upload orders from file
        ttk.Label(inputs, text="Insertar Ordenes", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", pady=(16, 0), padx=10
        )
        ttk.Button(inputs, text="Seleccionar archivo", command=self.load_orders).grid(
            row=2, column=0, sticky="w", pady=(16, 0), padx=10
        )

        # Button for delete orders and entry for order id
        ttk.Label(inputs, text="Id Orden a eliminar", style="bg.TLabel").grid(
            row=3, column=0, sticky="w", pady=(16, 0), padx=10
        )
        self.order_id = ttk.Entry(inputs)
        self.order_id.grid(row=4, column=0, sticky="w", pady=(16, 0), padx=10)
        ttk.Button(inputs, text="Eliminar Orden", command=self.delete_order).grid(
            row=5, column=0, sticky="w", pady=(16, 0), padx=10
        )

    def load_orders(self):
        file = filedialog.askopenfilename(
            parent=self,
            initialdir=os.getcwd(),
            title="Please select a directory",
            filetypes=[("Excel files", "*.xlsx")],
        )
        df = pd.read_excel(file, header=None)

        data = pd.DataFrame(df)
        order_date = data.iloc[1][2]
        sm_code = data.iloc[1][5]
        contract = data.iloc[4][2]
        order_number = data.iloc[5][2]
        plant = data.iloc[6][2]
        ubication = data.iloc[7][2]
        requester = data.iloc[8][2]
        telintec_personal = data.iloc[9][2]
        delivery_date = data.iloc[10][2]

        indice_item_start = data[data[0] == "ITEM"].index[0]
        indice_item_end = data.isin(["Personal que entrega "]).any(axis=1).idxmax()
        items = data.iloc[indice_item_start + 1 : indice_item_end - 1, [0, 1, 4, 5, 6]]
        filter_items = items[items[0].notnull()]
        final_items = filter_items.to_dict(orient="list")

        self.create_order(
            order_date,
            sm_code,
            contract,
            order_number,
            plant,
            ubication,
            requester,
            telintec_personal,
            delivery_date,
            filter_items,
            final_items,
        )

    def create_order(
        self,
        order_date,
        sm_code,
        contract,
        order_number,
        plant,
        ubication,
        requester,
        telintec_personal,
        delivery_date,
        filter_items,
        final_items,
    ):

        order_date_str = str(order_date) if not pd.isnull(order_date) else None
        sm_code_str = str(sm_code) if not pd.isnull(sm_code) else None
        contract_str = str(contract) if not pd.isnull(contract) else None
        order_number_str = str(order_number) if not pd.isnull(order_number) else None
        plant_str = str(plant) if not pd.isnull(plant) else None
        ubication_str = str(ubication) if not pd.isnull(ubication) else None
        requester_str = str(requester) if not pd.isnull(requester) else None
        telintec_personal_str = (
            str(telintec_personal) if not pd.isnull(telintec_personal) else None
        )
        delivery_date_str = str(delivery_date) if not pd.isnull(delivery_date) else None

        self._data._order.create_sm(
            order_date_str,
            sm_code_str,
            contract_str,
            order_number_str,
            plant_str,
            ubication_str,
            requester_str,
            telintec_personal_str,
            delivery_date_str,
            filter_items,
            final_items,
        )
        self.update_table()

    def delete_order(self):
        order_id = self.order_id.get()
        self._data._order.delete_order_sm(order_id)
        self.update_table()

    def fetch_products(self):
        return self._data._product.get_all_products()

    def clear_fields(self):
        self.order_id.delete(0, "end")

    def events(self, event):
        self.clear_fields()
        data = self.table.view.item(self.table.view.focus())["values"]
        self.order_id.insert(0, data[0])

    def add_product_entry_from_event(self, product, quantity):
        row_index = len(self._products_entries) + 4
        selected_product = product

        # product_entry = ttk.Entry(self.inputs_right)
        # product_entry.grid(row=row_index, column=1, sticky="w", padx=5, pady=5)
        # product_entry.insert(0, selected_product)
        # product_entry.state(["readonly"])

        # quantity_entry = ttk.Entry(self.inputs_right)
        # quantity_entry.grid(row=row_index, column=3, sticky="w", padx=5, pady=5)
        # quantity_entry.insert(0, "1")

        # self._products_entries.append((product_entry, quantity_entry))

    def update_table(self):
        self._orders = self._data._order.get_all_orders_sm()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._orders)
        self.table.autofit_columns()
