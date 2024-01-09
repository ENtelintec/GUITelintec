from tkinter import filedialog
import pandas as pd
from ttkbootstrap.scrolled import ScrolledFrame
from templates.widgets import *
from controllers.index import DataHandler


class SettingsScreen(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self, style="bg.TFrame")
        self.pack(side="top", fill="both", expand=True)
        self._data = DataHandler()
        self.create_content(self)

    def create_content(self, parent):
        content = ScrolledFrame(parent, style="bg.TFrame", autohide=True)
        content.pack(side="left", fill="both", expand=True)
        ttk.Label(content, text="Configuracion", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        # Theme
        theme = ttk.Frame(content, style="bg.TFrame")
        theme.pack(side="top", fill="both", expand=True)
        ttk.Label(theme, text="Tema", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Combobox(theme, values=["Dark", "Light"]).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # Language
        language = ttk.Frame(content, style="bg.TFrame")
        language.pack(side="top", fill="both", expand=True)
        ttk.Label(language, text="Idioma", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Combobox(language, values=["Español", "Ingles"]).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # Upload file for clients
        upload_file = ttk.Frame(content, style="bg.TFrame")
        upload_file.pack(side="top", fill="both", expand=True)
        ttk.Label(upload_file, text="Cargar archivo de clientes",
                  style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(upload_file, text="Cargar archivo", command=self.load_clients).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # Upload file for products
        upload_file = ttk.Frame(content, style="bg.TFrame")
        upload_file.pack(side="top", fill="both", expand=True)
        ttk.Label(upload_file, text="Cargar archivo de productos",
                  style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(upload_file, text="Cargar archivo", command=self.load_products).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

        # Upload file for orders
        upload_file = ttk.Frame(content, style="bg.TFrame")
        upload_file.pack(side="top", fill="both", expand=True)
        ttk.Label(upload_file, text="Cargar archivo de ordenes",
                  style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)
        ttk.Button(upload_file, text="Cargar archivo", command=self.load_orders).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10)

    def load_clients(self):
        file = filedialog.askopenfilename(
            parent=self, initialdir="/", title='Please select a directory')
        if not file:
            return
        df = pd.read_csv(file, header=None)
        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data._customer.create_customer(
                fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
        self._data._customer.close_connection()

    def load_products(self):
        file = filedialog.askopenfilename(
            parent=self, initialdir="/", title='Please select a directory')
        if not file:
            return
        df = pd.read_csv(file, header=None)
        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            # self.fetching_data.products.create_product(
            #     fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            # self.fetching_data.order.close_connection()
            print(fila)

    def load_orders(self):
        file = filedialog.askopenfilename(
            parent=self, initialdir="/", title='Please select a directory')
        if not file:
            return
        df = pd.read_csv(file, header=None)
        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            # self.fetching_data.orders.create_order(
            #     fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            # self.fetching_data.order.close_connection()
            print(fila)
