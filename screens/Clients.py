import time
from templates.widgets import *
from controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.scrolled import ScrolledFrame


class ClientsScreen(ScrolledFrame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, style="bg.TFrame")
        self.master = master
        self.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._clients = self._data._customer.get_all_customers()
        self._table = Tableview(self)
        self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the Clients screen, includes the table of clients and the inputs to add a new client"""
        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        ttk.Label(
            content, text="Clientes", style="bg.TLabel", font=("Arial Black", 25)
        ).grid(row=0, column=0, sticky="w")

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.grid(row=1, column=0, sticky="nswe")
        ttk.Label(
            table, text="Tabla de clientes", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w")

        self.col_data = [
            {"text": "ID Cliente", "stretch": True},
            {"text": "Nombre", "stretch": False},
            {"text": "Email", "stretch": True},
            {"text": "Telefono", "stretch": True},
            {"text": "Calle", "stretch": True},
            {"text": "Ciudad", "stretch": True},
            {"text": "Codigo Postal", "stretch": True},
        ]

        self.table = Tableview(
            master=table,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
        )
        self.table.build_table_data(self.col_data, self._clients)
        self.table.autofit_columns()
        self.table.grid(row=1, column=0, sticky="nswe")
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.grid(row=2, column=0, sticky="nswe")
        ttk.Label(
            inputs, text="Agregar nuevo cliente", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w")

        # dividir el frame en 2, izq y derecha para los inputs
        inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        inputs_left.grid(row=1, column=0, sticky="nswe")
        inputs_right = ttk.Frame(inputs, style="bg.TFrame")
        inputs_right.grid(row=1, column=1, sticky="nswe")

        # Inputs left
        ttk.Label(inputs_left, text="ID Cliente", style="bg.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        self.input_client_id = ttk.Entry(inputs_left, style="bg.TEntry")

        self.input_client_id.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Nombre", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )

        self.input_client_name = ttk.Entry(inputs_left, style="bg.TEntry")

        self.input_client_name.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Email", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )

        self.input_client_email = ttk.Entry(inputs_left, style="bg.TEntry")

        self.input_client_email.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Telefono", style="bg.TLabel").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )

        self.input_client_phone = ttk.Entry(inputs_left, style="bg.TEntry")

        self.input_client_phone.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # Inputs right
        ttk.Label(inputs_right, text="Calle", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        self.input_client_street = ttk.Entry(inputs_right, style="bg.TEntry")

        self.input_client_street.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_right, text="Ciudad", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )

        self.input_client_city = ttk.Entry(inputs_right, style="bg.TEntry")

        self.input_client_city.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_right, text="Codigo Postal", style="bg.TLabel").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )

        self.input_client_zip = ttk.Entry(inputs_right, style="bg.TEntry")

        self.input_client_zip.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.grid(row=3, column=0, sticky="nswe")

        ttk.Button(
            buttons,
            text="Agregar",
            style="bg.TButton",
            width=25,
            command=self.create_client,
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Button(
            buttons,
            text="Editar",
            style="bg.TButton",
            width=25,
            command=self.update_client,
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(
            buttons,
            text="Eliminar",
            style="bg.TButton",
            width=25,
            command=self.delete_client,
        ).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Button(
            buttons,
            text="Limpiar",
            style="bg.TButton",
            width=25,
            command=self.clear_fields,
        ).grid(row=0, column=3, sticky="w", padx=5, pady=5)

    def events(self, event):
        data = self.table.view.item(self.table.view.focus())["values"]
        print(data)
        self.input_client_id.delete(0, "end")
        self.input_client_name.delete(0, "end")
        self.input_client_email.delete(0, "end")
        self.input_client_phone.delete(0, "end")
        self.input_client_street.delete(0, "end")
        self.input_client_city.delete(0, "end")
        self.input_client_zip.delete(0, "end")
        self.input_client_id.insert(0, data[0])
        self.input_client_name.insert(0, data[1])
        self.input_client_email.insert(0, data[2])
        self.input_client_phone.insert(0, data[3])
        self.input_client_street.insert(0, data[4])
        self.input_client_city.insert(0, data[5])
        self.input_client_zip.insert(0, data[6])

    def update_table(self):
        self._clients = self._data._customer.get_all_customers()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._clients)
        self.table.autofit_columns()

    def clear_fields(self):
        self.input_client_id.delete(0, "end")
        self.input_client_name.delete(0, "end")
        self.input_client_email.delete(0, "end")
        self.input_client_phone.delete(0, "end")
        self.input_client_street.delete(0, "end")
        self.input_client_city.delete(0, "end")
        self.input_client_zip.delete(0, "end")

    def create_client(self):
        name = self.input_client_name.get()
        email = self.input_client_email.get()
        phone = self.input_client_phone.get()
        street = self.input_client_street.get()
        city = self.input_client_city.get()
        postal_code = self.input_client_zip.get()
        self._data._customer.create_customer(
            name, email, phone, street, city, postal_code
        )
        self.update_table()
        self.clear_fields()

    def update_client(self):
        id_customer = self.input_client_id.get()
        name = self.input_client_name.get()
        email = self.input_client_email.get()
        phone = self.input_client_phone.get()
        street = self.input_client_street.get()
        city = self.input_client_city.get()
        postal_code = self.input_client_zip.get()
        self._data._customer.update_customer(
            id_customer, name, email, phone, street, city, postal_code
        )
        self.update_table()
        self.clear_fields()

    def delete_client(self):
        id_customer = self.input_client_id.get()
        self._data._customer.delete_customer(id_customer)
        self.update_table()
        self.clear_fields()
