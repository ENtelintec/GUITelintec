import time
import re
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview


class OrdersScreen(ScrolledFrame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, style="bg.TFrame")
        self.master = master
        self.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._table = Tableview(self)
        self._orders = self._data._order.get_all_orders()
        self._products = self._data._product.get_all_products()
        self._clients = self._data._customer.get_all_customers()
        self.customer_id = None
        self._complete_order = list(filter(lambda x: x[2] == "complete", self._orders))
        self._incomplete_order = list(filter(lambda x: x[2] == "pending", self._orders))
        self._shipped_order = list(filter(lambda x: x[2] == "processing", self._orders))

        self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the Orders screen, includes the table of orders and the inputs to modify an order"""

        content = ttk.Frame(parent, style="bg.TFrame")
        content.pack(side="left", fill="both", expand=True)
        ttk.Label(
            content, text="Ordenes", style="bg.TLabel", font=("Arial Black", 25)
        ).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.pack(side="top", fill="both", expand=True)
        ttk.Label(
            table, text="Tabla de Ordenes", style="bg.TLabel", font=("Arial", 20)
        ).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        self.col_data = [
            {"text": "ID Orden", "stretch": True},
            {"text": "Fecha", "stretch": True},
            {"text": "Estatus", "stretch": True},
            {"text": "Nombre Cliente", "stretch": True},
            {"text": "Direccion Cliente", "stretch": False},
            {"text": "Ciudad Cliente", "stretch": True},
            {"text": "Codigo Postal Cliente", "stretch": True},
            {"text": "ID Detalle", "stretch": True},
            {"text": "Cantidad Producto", "stretch": True},
            {"text": "ID Producto", "stretch": True},
            {"text": "Nombre Producto", "stretch": False},
        ]

        self.table = Tableview(
            master=table,
            bootstyle="primary",
            coldata=self.col_data,
            rowdata=self._orders,
            paginated=True,
            pagesize=10,
            searchable=True,
        )
        self.table.autofit_columns()
        self.table.pack()
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ScrolledFrame(content, style="bg.TFrame", height=500)
        inputs.pack(side="top", fill="both", expand=True)
        ttk.Label(
            inputs,
            text="Agregar nueva orden",
            style="bg.TLabel",
            font=("Arial", 20),
        ).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        ttk.Label(
            inputs,
            text="Nota: Debes de hacer scroll para ver todos los inputs.",
            style="bg.TLabel",
            font=("Arial", 10),
        ).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # dividir el frame en 2, izq y derecha para los inputs
        inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        inputs_left.pack(side="left", fill="both", expand=True)
        inputs_right = ttk.Frame(inputs, style="bg.TFrame")
        inputs_right.pack(side="right", fill="both", expand=True)

        # Inputs left
        ttk.Label(inputs_left, text="ID de la orden", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.order_id = ttk.Entry(inputs_left)
        self.order_id.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs_left, text="Status de la orden", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.order_status = ttk.Combobox(
            inputs_left, values=["complete", "processing", "pending"]
        )
        self.order_status.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs_left, text="Nombre del cliente", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.customer_name = ttk.Combobox(inputs_left, values=self._clients)
        self.customer_name.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs_left, text="Dirección del cliente", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.customer_address = ttk.Entry(inputs_left, state="readonly")
        self.customer_address.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs_left, text="Ciudad del cliente", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.customer_city = ttk.Entry(inputs_left, state="readonly")
        self.customer_city.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(
            inputs_right, text="Código postal del cliente", style="bg.TLabel"
        ).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.customer_postal_code = ttk.Entry(inputs_right, state="readonly")
        self.customer_postal_code.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        self.customer_name.bind("<<ComboboxSelected>>", self.customer_event)

        ttk.Label(
            inputs_right, text="ID del detalle de la orden", style="bg.TLabel"
        ).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.order_detail_id = ttk.Entry(inputs_right)
        self.order_detail_id.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs_right, text="Cantidad del producto", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.product_quantity = ttk.Entry(inputs_right)
        self.product_quantity.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs_right, text="ID del producto", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.product_id = ttk.Combobox(inputs_right, values=self._products)
        self.product_id.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs_right, text="Nombre del producto", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.product_name = ttk.Entry(inputs_right, state="readonly")
        self.product_name.pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        self.product_id.bind(
            "<<ComboboxSelected>>",
            lambda event: self.product_name.configure(state="normal")
            or self.product_name.delete(0, "end")
            or self.product_name.insert(0, self.product_id.get())
            or self.product_name.configure(state="readonly"),
        )

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.pack(side="top", fill="y", expand=True)
        ttk.Button(
            buttons,
            text="Agregar",
            style="bg.TButton",
            width=25,
            command=self.create_order,
        ).pack(side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Editar",
            style="bg.TButton",
            width=25,
            command=self.update_order,
        ).pack(side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Eliminar",
            style="bg.TButton",
            width=25,
            command=self.delete_order,
        ).pack(side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(
            buttons,
            text="Limpiar",
            style="bg.TButton",
            width=25,
            command=self.clear_fields,
        ).pack(side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    def customer_event(self, event):
        data = self.customer_name.get()
        data = re.split(r"\s|(\{\w+\})", data)
        data = [segment.strip("{}") for segment in data if segment]
        if len(data) == 11:
            self.customer_address.configure(state="normal")
            self.customer_address.delete(0, "end")
            self.customer_address.insert(0, data[5])
            self.customer_address.insert("end", data[6])
            self.customer_address.insert("end", data[7])
            self.customer_address.configure(state="readonly")

            self.customer_city.configure(state="normal")
            self.customer_city.delete(0, "end")
            self.customer_city.insert(0, data[8])
            self.customer_city.insert("end", data[9])
            self.customer_city.configure(state="readonly")

            self.customer_postal_code.configure(state="normal")
            self.customer_postal_code.delete(0, "end")
            self.customer_postal_code.insert(0, data[10])
            self.customer_postal_code.configure(state="readonly")
            self.customer_id = data[0]
        else:
            self.customer_address.configure(state="normal")
            self.customer_address.delete(0, "end")
            self.customer_address.insert(0, data[5])
            self.customer_address.insert("end", data[6])
            self.customer_address.insert("end", data[7])
            self.customer_address.configure(state="readonly")

            self.customer_city.configure(state="normal")
            self.customer_city.delete(0, "end")
            self.customer_city.insert(0, data[8])
            self.customer_city.configure(state="readonly")

            self.customer_postal_code.configure(state="normal")
            self.customer_postal_code.delete(0, "end")
            self.customer_postal_code.insert(0, data[9])
            self.customer_postal_code.configure(state="readonly")
            self.customer_id = data[0]

    def events(self, event):
        data = self.table.view.item(self.table.view.focus())["values"]
        self.order_id.delete(0, "end")
        self.order_id.insert(0, data[0])
        self.order_status.delete(0, "end")
        self.order_status.insert(0, data[2])
        self.customer_name.delete(0, "end")
        self.customer_name.insert(0, data[3])
        self.customer_id = data[0]
        self.customer_address.delete(0, "end")
        self.customer_address.insert(0, data[4])
        self.customer_city.delete(0, "end")
        self.customer_city.insert(0, data[5])
        self.customer_postal_code.delete(0, "end")
        self.customer_postal_code.insert(0, data[6])
        self.order_detail_id.delete(0, "end")
        self.order_detail_id.insert(0, data[7])
        self.product_quantity.delete(0, "end")
        self.product_quantity.insert(0, data[8])
        self.product_id.delete(0, "end")
        self.product_id.insert(0, data[9])
        self.product_name.delete(0, "end")
        self.product_name.configure(state="normal")
        self.product_name.insert(0, data[10])
        self.product_name.configure(state="readonly")

    def update_table(self):
        self._orders = self._data._order.get_all_orders()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._orders)
        self.table.autofit_columns()

    def clear_fields(self):
        self.order_id.delete(0, "end")
        self.order_status.delete(0, "end")
        self.customer_name.delete(0, "end")
        self.customer_address.delete(0, "end")
        self.customer_city.delete(0, "end")
        self.customer_postal_code.delete(0, "end")
        self.order_detail_id.delete(0, "end")
        self.product_quantity.delete(0, "end")
        self.product_id.set("")
        self.product_name.configure(state="normal")
        self.product_name.delete(0, "end")
        self.product_name.configure(state="readonly")
        self.customer_id = None

    def create_order(self):
        order_status = self.order_status.get()
        customer_name = self.customer_name.get()
        customer_address = self.customer_address.get()
        customer_city = self.customer_city.get()
        customer_postal_code = self.customer_postal_code.get()
        product_quantity = self.product_quantity.get()
        product_id = self.product_id.get()
        print(
            order_status,
            customer_name,
            customer_address,
            customer_city,
            customer_postal_code,
            product_quantity,
            product_id,
        )

    def update_order(self):
        order_id = self.order_id.get()
        customer_id = self.customer_id
        order_status = self.order_status.get()
        order_detail_id = self.order_detail_id.get()
        product_id = self.product_id.get()
        product_quantity = self.product_quantity.get()
        self._data._order.update_order(
            order_id,
            customer_id,
            order_status,
            order_detail_id,
            product_id,
            product_quantity,
        )
        self.update_table()

    def delete_order(self):
        order_id = self.order_id.get()
        self._data._order.delete_order(order_id)
        self.update_table()
