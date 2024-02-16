from templates.widgets import *
from templates.screens.Clients import ClientsScreen
from templates.screens.Home import HomeScreen
from templates.screens.In import InScreen
from templates.screens.Inventory import InventoryScreen
from templates.screens.Supplies import SuppliesScreen
from templates.screens.InternalInventory import InternalInventoryScreen
from templates.screens.Orders import OrdersScreen
from templates.screens.Out import OutScreen
from templates.screens.Providers import ProvidersScreen
from templates.screens.Settings import SettingsScreen


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._current_frame = None
        self._home = HomeScreen
        self._clients = ClientsScreen
        self._inventory = InventoryScreen
        self._daily_supplies = SuppliesScreen
        self._internal_inventory = InternalInventoryScreen
        self._settings = SettingsScreen
        self._in = InScreen
        self._out = OutScreen
        self._orders = OrdersScreen
        self._providers = ProvidersScreen

        ttk.Style().configure(
            "primary.TFrame",
            background="#04053A",
            foreground="white",
            bordercolor="#04053A",
            lightcolor="#04053A",
            darkcolor="#04053A",
            padding=4,
        )
        ttk.Style().configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=6,
            bordercolor="#04053A",
            borderwidth=2,
        )

        self.menu = create_menu(self)
        self.menu.grid(row=0, column=0, sticky="nsew")
        self.switch_screen(self._home)
        # create_footer(self)

    def switch_screen(self, new_frame):
        if self._current_frame:
            self._current_frame.grid_forget()
        self._current_frame = new_frame(self)
        self._current_frame.grid(row=0, column=1, sticky="nsew")
