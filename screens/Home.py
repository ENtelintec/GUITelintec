from ttkbootstrap.scrolled import ScrolledFrame
from PIL import Image
from templates.widgets import *
from controllers.index import DataHandler

Image.CUBIC = Image.BICUBIC


class HomeScreen(ScrolledFrame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, style="bg.TFrame")
        self.master = master
        self.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self._total_profit = self._data._order.get_profit()
        self._total_orders = len(self._data._order.get_all_orders())
        self._total_returns = 0
        self.create_content(self)

    def create_content(self, parent):
        """
        Creates the content of the home screen, includes only graphics charts
        """
        content = ttk.Frame(parent, style="bg.TFrame")
        content.grid(row=0, column=0, sticky="nswe")
        content.columnconfigure((0, 1, 2, 3), weight=1)
        content.rowconfigure(1, weight=1)
        ttk.Label(
            content, text="Inicio", style="bg.TLabel", font=("Arial Black", 25)
        ).grid(row=0, column=0, sticky="w")
        # chart 1
        chart_profit = ttk.Meter(
            content,
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
            content,
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
            content,
            bootstyle="danger",
            amountused=0,
            amounttotal=int("500000"),
            textleft="$",
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Devoluciones",
        )
        chart_returns.grid(row=1, column=2, sticky="nsew")

        # Chart 4
        chart_profit = ttk.Meter(
            content,
            bootstyle="success",
            amountused=0,
            amounttotal=int("500000"),
            textleft="$",
            metertype="full",
            padding=10,
            stripethickness=10,
            subtext="Ingresos",
        )
        chart_profit.grid(row=1, column=3, sticky="nsew")
