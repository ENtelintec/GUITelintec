import os
from tkinter import filedialog
import pandas as pd
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from templates.controllers.index import DataHandler


class SettingsScreen(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self.create_content()

    def create_content(self):
        content = ttk.Frame(self, style="bg.TFrame")
        content.columnconfigure(0, weight=1)
        content.grid(row=0, column=0, sticky="nswe")

        ttk.Label(
            content, text="Configuracion", style="bg.TLabel", font=("Arial Black", 25)
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            content,
            text="Importar registros multiples",
            style="bg.TLabel",
            font=("Arial", 18),
        ).grid(row=2, column=0, sticky="nswe", pady=(16, 0), padx=10)

        # Grid for upload files
        upload_file = ttk.Frame(content, style="bg.TFrame")
        upload_file.grid(row=3, column=0, sticky="nsew")
        upload_file.columnconfigure((0, 1, 2, 3), weight=1)

        # Button for upload clients
        ttk.Label(upload_file, text="Insertar Clientes", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", pady=(16, 0), padx=10
        )
        ttk.Button(
            upload_file, text="Seleccionar archivo", command=self.load_clients
        ).grid(row=1, column=0, sticky="w", pady=(16, 0), padx=10)

        # Button for upload products
        ttk.Label(upload_file, text="Insertar Inventario", style="bg.TLabel").grid(
            row=0, column=1, sticky="w", pady=(16, 0), padx=10
        )
        ttk.Button(
            upload_file, text="Seleccionar archivo", command=self.load_products
        ).grid(row=1, column=1, sticky="w", pady=(16, 0), padx=10)

        # Button for upload providers
        ttk.Label(upload_file, text="Insertar Proveedores", style="bg.TLabel").grid(
            row=0, column=2, sticky="w", pady=(16, 0), padx=10
        )
        ttk.Button(
            upload_file, text="Seleccionar archivo", command=self.load_providers
        ).grid(row=1, column=2, sticky="w", pady=(16, 0), padx=10)

        # Button for upload categories
        ttk.Label(
            upload_file,
            text="Insertar Categorias",
            style="bg.TLabel",
        ).grid(row=0, column=3, sticky="w", pady=(16, 0), padx=10)
        ttk.Button(
            upload_file,
            text="Seleccionar archivo",
            command=self.load_cateogires,
        ).grid(row=1, column=3, sticky="w", pady=(16, 0), padx=10)

        # Frame for message box
        message_box = ttk.Frame(content, style="bg.TFrame")
        message_box.grid(row=4, column=0, sticky="nsew")
        message_box.columnconfigure(0, weight=1)
        ttk.Label(message_box, text="Mensajes", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", pady=(16, 0), padx=10
        )
        self.message_box = ttk.Label(message_box, text="", style="bg.TLabel")
        self.message_box.grid(row=1, column=0, sticky="w", pady=(16, 0), padx=10)

    def _message_box(self, title, message):
        self.message_box.config(text=f"{title}: {message}")

    def load_cateogires(self):
        file = filedialog.askopenfilename(
            parent=self,
            initialdir=os.getcwd(),
            title="Please select a directory",
            filetypes=[("CSV files", "*.csv")],
        )

        if not file:
            self._message_box("Categorias", "No se selecciono ningun archivo")
            return

        if (
            not file.lower().endswith(".csv")
            or os.path.basename(file) != "categorias.csv"
        ):
            self._message_box(
                "Categorias", "El archivo debe ser un .csv y llamarse categorias.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 1:
            self._message_box(
                "Categorias",
                "El archivo debe contener 1 columna: nombre",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data._product_categories.create_category(fila[0])
        self._message_box("Categorias", "Categorias cargadas correctamente")

    def load_clients(self):
        file = filedialog.askopenfilename(
            parent=self,
            initialdir=os.getcwd(),
            title="Please select a directory",
            filetypes=[("CSV files", "*.csv")],
        )

        if not file:
            self._message_box("Clientes", "No se selecciono ningun archivo")
            return

        if (
            not file.lower().endswith(".csv")
            or os.path.basename(file) != "clientes.csv"
        ):
            self._message_box(
                "Clientes", "El archivo debe ser un .csv y llamarse clientes.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 5:
            self._message_box(
                "Clientes",
                "El archivo debe contener 6 columnas: nombre, email, telefono, rfc, direccion",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data._customer.create_customer(
                fila[0], fila[1], fila[2], fila[3], fila[4]
            )
        self._message_box("Clientes", "Clientes cargados correctamente")

    def load_products(self):
        file = filedialog.askopenfilename(
            parent=self,
            initialdir=os.getcwd(),
            title="Please select a directory",
            filetypes=[("CSV files", "*.csv")],
        )

        if not file:
            self._message_box("Inventario", "No se selecciono ningun archivo")
            return

        if (
            not file.lower().endswith(".csv")
            or os.path.basename(file) != "inventario.csv"
        ):
            self._message_box(
                "Inventario", "El archivo debe ser un .csv y llamarse inventario.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 9:
            self._message_box(
                "Inventario",
                "El archivo debe contener 9 columnas: sku, nombre, udm, stock, minstock, maxstock, reorderPoint id_categoria, id_proveedor",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data._product.create_product(
                fila[0],
                fila[1],
                fila[2],
                fila[3],
                fila[4],
                fila[5],
                fila[6],
                fila[7],
                fila[8],
            )
        self._message_box("Inventario", "Inventario cargados correctamente")

    def load_providers(self):
        file = filedialog.askopenfilename(
            parent=self,
            initialdir=os.getcwd(),
            title="Please select a directory",
            filetypes=[("CSV files", "*.csv")],
        )

        if not file:
            self._message_box("Proveedores", "No se selecciono ningun archivo")
            return

        if (
            not file.lower().endswith(".csv")
            or os.path.basename(file) != "proveedores.csv"
        ):
            self._message_box(
                "Proveedores", "El archivo debe ser un .csv y llamarse proveedores.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 7:
            self._message_box(
                "Proveedores",
                "El archivo debe contener 7 columnas: nombre, vendedor, email, telefono, direccion, web, tipo",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data._supplier.create_supplier(
                fila[0], fila[1], fila[2], fila[3], fila[4], fila[5], fila[6]
            )
        self._message_box("Proveedores", "Proveedores cargados correctamente")
