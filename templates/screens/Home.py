import ttkbootstrap as ttk
from PIL import Image

from templates.controllers.index import DataHandler

Image.CUBIC = Image.BICUBIC


class HomeScreen(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.master = master
        self.columnconfigure((0, 1), weight=1)
        self._data = DataHandler()
        self._total_profit = int(len(self._data._order.get_total_products()))
        self._total_orders = int(len(self._data._order.get_all_orders()))
        self.create_content(self)

    def create_content(self, parent):
        """
        Creates the content of the home screen, includes only graphics charts
        """
        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        content.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Label(content, text="Inicio", font=("Arial Black", 25)).grid(
            row=0, column=0, sticky="nswe", padx=5, pady=10
        )
        # most valuable product chart
        product_chart = ttk.Frame(content, style="bg.TFrame")
        product_chart.grid(row=0, column=0, sticky="nswe")
        ttk.Label(
            product_chart,
            text="Producto más Vendido",
            style="bg.TLabel",
            font=("Arial", 20),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)
        chart_profit = ttk.Meter(
            product_chart,
            bootstyle="success",
            amountused=1300,
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Productos Vendidos",
        )
        chart_profit.grid(row=1, column=0, sticky="nswe")
        ttk.Label(
            product_chart,
            text=f"Nombre del producto: {'Producto 1'}",
            style="bg.TLabel",
            font=("Arial", 15),
        ).grid(row=2, column=0, sticky="w", padx=5, pady=10)

        # less valuable product chart
        less_valuable_chart = ttk.Frame(content, style="bg.TFrame")
        less_valuable_chart.grid(row=0, column=1, sticky="nswe")
        ttk.Label(
            less_valuable_chart,
            text="Producto menos Vendido",
            style="bg.TLabel",
            font=("Arial", 20),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)
        chart_profit = ttk.Meter(
            less_valuable_chart,
            bootstyle="success",
            amountused=5,
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Productos Vendidos",
        )
        chart_profit.grid(row=1, column=0, sticky="nswe")
        ttk.Label(
            less_valuable_chart,
            text=f"Nombre del producto: {'Producto 5'}",
            style="bg.TLabel",
            font=("Arial", 15),
        ).grid(row=2, column=0, sticky="w", padx=5, pady=10)

        # most valuable provider chart
        provider_chart = ttk.Frame(content, style="bg.TFrame")
        provider_chart.grid(row=0, column=2, sticky="nswe")
        ttk.Label(
            provider_chart,
            text="Proveedor más Valioso",
            style="bg.TLabel",
            font=("Arial", 20),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)
        chart_profit = ttk.Meter(
            provider_chart,
            bootstyle="success",
            amountused=12000,
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Unidades Vendidas",
        )
        chart_profit.grid(row=1, column=0, sticky="nswe")
        ttk.Label(
            provider_chart,
            text=f"Nombre del Prvoeedor: {'Proveedor 1'}",
            style="bg.TLabel",
            font=("Arial", 15),
        ).grid(row=2, column=0, sticky="w", padx=5, pady=10)
