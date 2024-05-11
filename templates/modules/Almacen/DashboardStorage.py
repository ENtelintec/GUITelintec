import ttkbootstrap as ttk
from PIL import Image

from templates.controllers.index import DataHandler

Image.CUBIC = Image.BICUBIC


class StorageDashboard(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.master = master
        self.columnconfigure((0, 1), weight=1)
        self._data = DataHandler()
        self._total_orders = 100
        self.create_content(self)

    def create_content(self, parent):
        """
        Creates the content of the home screen, includes only graphics charts
        """
        content_frame = ttk.Frame(parent, style="bg.TFrame")
        content_frame.grid(row=0, column=0, sticky="nswe")
        content_frame.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Label(content_frame, text="Inicio", font=("Arial Black", 25)).grid(
            row=0, column=0, sticky="nswe", padx=5, pady=10
        )
        # most valuable product chart
        product_chart_frame = ttk.Frame(content_frame, style="bg.TFrame")
        product_chart_frame.grid(row=0, column=0, sticky="nswe")
        ttk.Label(product_chart_frame, text="Producto más Vendido", style="bg.TLabel", font=("Arial", 20)).grid(
            row=0, column=0, sticky="w", padx=5, pady=10)
        chart_profit = ttk.Meter(product_chart_frame, bootstyle="success", amountused=1300, metertype="full",
                                 padding=10, stripethickness=10, subtext="Productos Vendidos")
        chart_profit.grid(row=1, column=0, sticky="nswe")
