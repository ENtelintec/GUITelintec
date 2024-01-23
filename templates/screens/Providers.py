import time
from templates.widgets import *
from templates.controllers.index import DataHandler
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.scrolled import ScrolledFrame


class ProvidersScreen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._providers = self._data._supplier.get_all_suppliers()
        self._table = Tableview(self)
        self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the providers screen, includes the table of providers and the inputs to add a new client"""
        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        content.columnconfigure(0, weight=1)
        ttk.Label(
            content, text="Proveedores", style="bg.TLabel", font=("Arial Black", 25)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.grid(row=1, column=0, sticky="nswe")
        table.columnconfigure(0, weight=1)
        ttk.Label(
            table, text="Tabla de Proveedores", style="bg.TLabel", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        self.col_data = [
            {"text": "ID Proveedor"},
            {"text": "Nombre"},
            {"text": "Direccion"},
            {"text": "Telefono"},
        ]

        self.table = Tableview(
            master=table,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True
        )
        self.table.build_table_data(self.col_data, self._providers)
        self.table.grid(row=1, column=0, sticky="nswe",  padx=15, pady=5)
        self.table.view.bind("<Double-1>", self.events)

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.grid(row=2, column=0, sticky="nswe")
        inputs.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Label(
            inputs,
            text="Agregar nuevo proveedor",
            style="bg.TLabel",
            font=("Arial", 20),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)

        # dividir el frame en 2, izq y derecha para los inputs
        inputs_left = ttk.Frame(inputs, style="bg.TFrame")
        inputs_left.grid(row=1, column=0, sticky="nswe")

        inputs_right = ttk.Frame(inputs, style="bg.TFrame")
        inputs_right.grid(row=1, column=1, sticky="nswe")

        # Inputs left
        ttk.Label(inputs_left, text="ID Proveedor", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        self.id_provider = ttk.Entry(inputs_left, style="bg.TEntry")

        self.id_provider.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_left, text="Nombre", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )

        self.name_provider = ttk.Entry(inputs_left, style="bg.TEntry")

        self.name_provider.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Inputs right
        ttk.Label(inputs_right, text="Direccion", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        self.address_provider = ttk.Entry(inputs_right, style="bg.TEntry")

        self.address_provider.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(inputs_right, text="Telefono", style="bg.TLabel").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )

        self.phone_provider = ttk.Entry(inputs_right, style="bg.TEntry")

        self.phone_provider.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.grid(row=3, column=0, sticky="nswe")
        buttons.columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Button(
            buttons,
            text="Agregar",
            style="bg.TButton",
            width=25,
            command=self.create_provider,
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Button(
            buttons,
            text="Editar",
            style="bg.TButton",
            width=25,
            command=self.update_provider,
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(
            buttons,
            text="Eliminar",
            style="bg.TButton",
            width=25,
            command=self.delete_provider,
        ).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Button(
            buttons,
            text="Limpiar",
            style="bg.TButton",
            width=25,
            command=self.clear_fields,
        ).grid(row=0, column=3, sticky="w", padx=5, pady=5)

    def events(self, event):
        """Events for the table of clients"""
        data = self.table.view.item(self.table.view.focus())["values"]
        self.name_provider.delete(0, "end")
        self.address_provider.delete(0, "end")
        self.phone_provider.delete(0, "end")
        self.id_provider.insert(0, data[0])
        self.name_provider.insert(0, data[1])
        self.address_provider.insert(0, data[2])
        self.phone_provider.insert(0, data[3])

    def update_table(self):
        """Updates the table of providers"""
        self._providers = self._data._supplier.get_all_providers()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._providers)
        self.table.autofit_columns()

    def clear_fields(self):
        """Clears all the inputs"""
        self.id_provider.delete(0, "end")
        self.name_provider.delete(0, "end")
        self.address_provider.delete(0, "end")
        self.phone_provider.delete(0, "end")

    def create_provider(self):
        """Creates a new providers"""
        id_provider = self.id_provider.get()
        name_provider = self.name_provider.get()
        address_provider = self.address_provider.get()
        phone_provider = self.phone_provider.get()
        self._data._supplier.create_supplier(
            id_provider, name_provider, address_provider, phone_provider
        )
        self.update_table()
        self.clear_fields()

    def update_provider(self):
        """Updates a client"""
        id_provider = self.id_provider.get()
        name_provider = self.name_provider.get()
        address_provider = self.address_provider.get()
        phone_provider = self.phone_provider.get()
        self._data._supplier.update_supplier(
            id_provider, name_provider, address_provider, phone_provider
        )
        self.update_table()
        self.clear_fields()

    def delete_provider(self):
        """Deletes a client"""
        id_provider = self.id_provider.get()
        self._data._supplier.delete_supplier(id_provider)
        self.update_table()
        self.clear_fields()
