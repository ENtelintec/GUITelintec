from templates.widgets import *
from screens.Home import HomeScreen


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # variables
        self.master = master
        self.columnconfigure((0, 1), weight=1)
        self._current_frame = None
        self._home = HomeScreen(self)
        # self._clients = ClientsScreen
        # self._settings = SettingsScreen
        # self._ins = InScreen
        # self._outs = OutScreen
        # self._inventory = InventoryScreen
        # self._orders = OrdersScreen
        # self._returns = ReturnsScreen

        ttk.Style().configure("primary.TFrame",
                              background="#04053A",
                              foreground="white",
                              bordercolor="#04053A",
                              lightcolor="#04053A",
                              darkcolor="#04053A",
                              padding=4)
        ttk.Style().configure("TButton", font=(
            "Segoe UI", 10), padding=6, bordercolor="#04053A", borderwidth=2)

        self.menu = create_menu(self)
        self.menu.grid(row=0, column=0, sticky="nsew")
        #self.switch_screen(self._home)
        # create_footer(self)

    def switch_screen(self, new_frame):
        if self._current_frame:
            self._current_frame.grid_forget()
        self._current_frame = new_frame
        self._current_frame.grid(row=0, column=0, sticky="nsew")
