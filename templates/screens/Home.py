from ttkbootstrap.scrolled import ScrolledFrame
from PIL import Image
from templates.widgets import *
from templates.controllers.index import DataHandler

Image.CUBIC = Image.BICUBIC


class HomeScreen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure((0, 1), weight=1)
        self._data = DataHandler()
        self._total_profit = self._data._order.get_profit()
        self._total_orders = len(self._data._order.get_all_orders())
        self._total_returns = 0
        self.create_content(self)

    def create_content(self, parent):
        """
        Creates the content of the home screen, includes only graphics charts
        """
        ttk.Label(
            self, text="Inicio", style="bg.TLabel", font=("Arial Black", 25)
        ).grid(row=0, column=0, sticky="w")

        # chart 1
        chart_profit = ttk.Meter(
            self,
            bootstyle="success",
            amountused=int(self._total_profit[0][0]),
            amounttotal=int("500000"),
            textleft="$",
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Ingresos",
        )
        chart_profit.grid(row=1, column=0, sticky="nsew")

        # chart 2
        chart_orders = ttk.Meter(
            self,
            bootstyle="info",
            amountused=int(self._total_orders),
            amounttotal=int("500000"),
            textleft="$",
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Pedidos",
        )
        chart_orders.grid(row=1, column=1, sticky="nsew")

        # chart 3
        chart_returns = ttk.Meter(
            self,
            bootstyle="danger",
            amountused=0,
            amounttotal=int("500000"),
            textleft="$",
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Devoluciones",
        )
        chart_returns.grid(row=2, column=0, sticky="nsew")
        # Chart 4
        chart_profit = ttk.Meter(
            self,
            bootstyle="success",
            amountused=0,
            amounttotal=int("500000"),
            textleft="$",
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Egresos",
        )
        chart_profit.grid(row=2, column=1, sticky="nsew")
