import time
from templates.widgets import *
from controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.scrolled import ScrolledFrame


class ClientsScreen(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self, style="bg.TFrame")
        self.pack(side="top", fill="both", expand=True)
        self._data = DataHandler()
        self._clients = self._data._customer.get_all_customers()
        self._table = Tableview(self)
        self.create_content(self)

    def create_content(self, parent):
        '''Creates the content of the Clients screen, includes the table of clients and the inputs to add a new client'''
        content = ttk.Frame(parent, style="bg.TFrame")
        content.pack(side="left", fill="both", expand=True)
        ttk.Label(content, text="Clientes", style="bg.TLabel", font=(
            "Arial Black", 25)).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # Table
        table = ScrolledFrame(content, style="bg.TFrame", autohide=True)
        table.pack(side="top", fill="both", expand=True)
        ttk.Label(table, text="Tabla de clientes", style="bg.TLabel", font=(
            "Arial", 20)).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        self.col_data = [{"text": "ID Cliente", "stretch": False},
                         {"text": "Nombre", "stretch": True},
                         {"text": "Email", "stretch": True},
                         {"text": "Telefono", "stretch": False},
                         {"text": "Calle", "stretch": False},
                         {"text": "Ciudad", "stretch": False},
                         {"text": "Codigo Postal", "stretch": False}]

        self.table = Tableview(master=table, bootstyle="primary",
                               coldata=self.col_data,
                               rowdata=self._clients,
                               paginated=True,
                               pagesize=10,
                               searchable=True)
        self.table.autofit_columns()
        self.table.pack()
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.pack(side="top", fill="both", expand=True)
        ttk.Label(inputs, text="Agregar nuevo cliente",
                  style="bg.TLabel", font=(
                      "Arial", 20)).pack(side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # dividir el frame en 2, izq y derecha para los inputs
        inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        inputs_left.pack(side="left", fill="both", expand=True)
        inputs_right = ttk.Frame(inputs, style="bg.TFrame")
        inputs_right.pack(side="right", fill="both", expand=True)

        # Inputs left
        ttk.Label(inputs_left, text="ID Cliente", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.input_client_id = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_client_id.pack(side="top", fill="x", anchor="center",
                                  ipady=5, pady=(16, 0), padx=10)

        ttk.Label(inputs_left, text="Nombre", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.input_client_name = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_client_name.pack(side="top", fill="x", anchor="center",
                                    ipady=5, pady=(16, 0), padx=10)

        ttk.Label(inputs_left, text="Email", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.input_client_email = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_client_email.pack(side="top", fill="x", anchor="center",
                                     ipady=5, pady=(16, 0), padx=10)

        ttk.Label(inputs_left, text="Telefono", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.input_client_phone = ttk.Entry(inputs_left, style="bg.TEntry")
        self.input_client_phone.pack(side="top", fill="x", anchor="center",
                                     ipady=5, pady=(16, 0), padx=10)

        # Inputs right
        ttk.Label(inputs_right, text="Calle", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.input_client_street = ttk.Entry(inputs_right, style="bg.TEntry")
        self.input_client_street.pack(side="top", fill="x", anchor="center",
                                      ipady=5, pady=(16, 0), padx=10)

        ttk.Label(inputs_right, text="Ciudad", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.input_client_city = ttk.Entry(inputs_right, style="bg.TEntry")
        self.input_client_city.pack(side="top", fill="x", anchor="center",
                                    ipady=5, pady=(16, 0), padx=10)

        ttk.Label(inputs_right, text="Codigo Postal", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        self.input_client_zip = ttk.Entry(inputs_right, style="bg.TEntry")
        self.input_client_zip.pack(side="top", fill="x", anchor="center",
                                   ipady=5, pady=(16, 0), padx=10)

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.pack(side="top", fill="y", expand=True)
        ttk.Button(buttons, text="Agregar", style="bg.TButton", width=25, command=self.create_client).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(buttons, text="Editar", style="bg.TButton", width=25, command=self.update_client).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(buttons, text="Eliminar", style="bg.TButton", width=25, command=self.delete_client).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(buttons, text="Limpiar", style="bg.TButton", width=25, command=self.clear_fields).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    def events(self, event):
        data = self.table.view.item(self.table.view.focus())['values']
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
            name, email, phone, street, city, postal_code)
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
            id_customer, name, email, phone, street, city, postal_code)
        self.update_table()
        self.clear_fields()

    def delete_client(self):
        id_customer = self.input_client_id.get()
        self._data._customer.delete_customer(id_customer)
        self.update_table()
        self.clear_fields()
