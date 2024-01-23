from tkinter import filedialog
import pandas as pd
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from templates.controllers.index import DataHandler


class SettingsScreen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
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

        # # Theme selector
        # ttk.Label(content, text="Tema", style="bg.TLabel").grid(
        #     row=1, column=0, sticky="w", pady=(16, 0), padx=10
        # )
        # ttk.Combobox(content, values=["Dark", "Light"]).grid(
        #     row=2, column=0, sticky="w", pady=(16, 0), padx=10
        # )

        # # Language selector
        # ttk.Label(content, text="Idioma", style="bg.TLabel").grid(
        #     row=1, column=1, sticky="w", pady=(16, 0), padx=10
        # )
        # ttk.Combobox(content, values=["Español", "Ingles"]).grid(
        #     row=2, column=1, sticky="w", pady=(16, 0), padx=10
        # )
        ttk.Label(
            content,
            text="Importar registros multiples",
            style="bg.TLabel",
            font=("Arial", 18),
        ).grid(row=2, column=0, sticky="nswe", pady=(16, 0), padx=10)

        # Grid for upload files
        upload_file = ttk.Frame(content, style="bg.TFrame")
        upload_file.grid(row=3, column=0, sticky="nsew")
        upload_file.columnconfigure((0, 1), weight=1)

        # Button for upload clients
        ttk.Label(upload_file, text="Insertar Clientes", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", pady=(16, 0), padx=10
        )
        ttk.Button(
            upload_file, text="Seleccionar archivo", command=self.load_clients
        ).grid(row=1, column=0, sticky="w", pady=(16, 0), padx=10)

        # Button for upload products
        ttk.Label(upload_file, text="Insertar Productos", style="bg.TLabel").grid(
            row=0, column=1, sticky="w", pady=(16, 0), padx=10
        )
        ttk.Button(
            upload_file, text="Seleccionar archivo", command=self.load_products
        ).grid(row=1, column=1, sticky="w", pady=(16, 0), padx=10)

        # Button for upload orders
        # ttk.Label(upload_file, text="Insertar Ordenes", style="bg.TLabel").grid(
        #     row=0, column=2, sticky="w", pady=(16, 0), padx=10
        # )
        # ttk.Button(
        #     upload_file, text="Seleccionar archivo", command=self.load_orders
        # ).grid(row=1, column=2, sticky="w", pady=(16, 0), padx=10)

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

    #     content = ScrolledFrame(parent, style="bg.TFrame", autohide=True)
    #     content.pack(side="left", fill="both", expand=True)
    #     ttk.Label(content, text="Configuracion", style="bg.TLabel").pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
    #     # Theme
    #     theme = ttk.Frame(content, style="bg.TFrame")
    #     theme.pack(side="top", fill="both", expand=True)
    #     ttk.Label(theme, text="Tema", style="bg.TLabel").pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
    #     ttk.Combobox(theme, values=["Dark", "Light"]).pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    #     # Language
    #     language = ttk.Frame(content, style="bg.TFrame")
    #     language.pack(side="top", fill="both", expand=True)
    #     ttk.Label(language, text="Idioma", style="bg.TLabel").pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
    #     ttk.Combobox(language, values=["Español", "Ingles"]).pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    #     # Upload file for clients
    #     upload_file = ttk.Frame(content, style="bg.TFrame")
    #     upload_file.pack(side="top", fill="both", expand=True)
    #     ttk.Label(upload_file, text="Cargar archivo de clientes",
    #               style="bg.TLabel").pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
    #     ttk.Button(upload_file, text="Cargar archivo", command=self.load_clients).pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    #     # Upload file for products
    #     upload_file = ttk.Frame(content, style="bg.TFrame")
    #     upload_file.pack(side="top", fill="both", expand=True)
    #     ttk.Label(upload_file, text="Cargar archivo de productos",
    #               style="bg.TLabel").pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
    #     ttk.Button(upload_file, text="Cargar archivo", command=self.load_products).pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    #     # Upload file for orders
    #     upload_file = ttk.Frame(content, style="bg.TFrame")
    #     upload_file.pack(side="top", fill="both", expand=True)
    #     ttk.Label(upload_file, text="Cargar archivo de ordenes",
    #               style="bg.TLabel").pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
    #     ttk.Button(upload_file, text="Cargar archivo", command=self.load_orders).pack(
    #         side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    def load_clients(self):
        file = filedialog.askopenfilename(
            parent=self, initialdir="/", title="Please select a directory"
        )

        if not file:
            self._message_box("Clientes", "No se selecciono ningun archivo")
            return

        if file.split(".")[-1] != "clientes.csv":
            self._message_box(
                "Clientes", "El archivo debe ser un .csv y llamarse clientes.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 6:
            self._message_box(
                "Clientes",
                "El archivo debe contener 6 columnas: nombre, email, telefono, calle, ciudad, codigo postal",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data._customer.create_customer(
                fila[0], fila[1], fila[2], fila[3], fila[4], fila[5]
            )
        self._message_box("Clientes", "Clientes cargados correctamente")

    def load_products(self):
        file = filedialog.askopenfilename(
            parent=self, initialdir="/", title="Please select a directory"
        )

        if not file:
            self._message_box("Productos", "No se selecciono ningun archivo")
            return

        if file.split(".")[-1] != "productos.csv":
            self._message_box(
                "Productos", "El archivo debe ser un .csv y llamarse productos.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 6:
            self._message_box(
                "Productos",
                "El archivo debe contener 6 columnas: nombre, descripcion, precio, stock, id_categoria, id_proveedor",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data._product.create_product(
                fila[0], fila[1], fila[2], fila[3], fila[4], fila[5]
            )
        self._message_box("Productos", "Productos cargados correctamente")

    # def load_orders(self):
    #     file = filedialog.askopenfilename(
    #         parent=self, initialdir="/", title="Please select a directory"
    #     )
    #     if not file:
    #         return
    #     df = pd.read_csv(file, header=None)
    #     for indice, fila in enumerate(df.values):
    #         if indice == 0:
    #             continue
    #         # self.fetching_data.orders.create_order(
    #         #     fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
    #         # self.fetching_data.order.close_connection()
    #         print(fila)
