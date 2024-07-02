# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 18/oct./2023  at 10:25 $'

import ttkbootstrap as ttk

from static.extensions import windows_names_db_frame
from templates.Functions_AuxFilesGUI import get_image_side_menu
from templates.Functions_GUI_Utils import create_button_side_menu
from templates.modules.DB.SubFrame_Chats import ChatsFrame
from templates.modules.DB.SubFrame_Customer import CustomersFrame
from templates.modules.DB.SubFrame_Departments import DepartmentsFrame
from templates.modules.DB.SubFrame_Employees import EmployeesFrame
from templates.modules.DB.SubFrame_Heads import HeadsFrame
from templates.modules.DB.SubFrame_Orders import OrdersFrame, VOrdersFrame
from templates.modules.DB.SubFrame_Products import ProductsFrame
from templates.modules.DB.SubFrame_Suppliers import SuppliersFrame
from templates.modules.DB.SubFrame_Tickets import TicketsFrame


class DBFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        # --------------------------variables-----------------------------------
        self.settings = setting
        self._active_window = None
        self.names_side_menu = windows_names_db_frame
        kwargs["settings"] = self.settings
        self.kwargs = kwargs
        frame_side_menu = ttk.Frame(self)
        frame_side_menu.grid(row=0, column=0, sticky="nsew")
        self.widgets = self._create_side_menu_widgets(frame_side_menu)
        self.windows_frames = self._create_side_menu_windows()

    def _create_side_menu_widgets(self, master):
        widgets = []
        if len(self.names_side_menu) >= 12:
            scrollbar = ttk.Scrollbar(master, orient="vertical")
            scrollbar.grid(row=0, column=2, sticky="ns")
        for i, window in enumerate(self.names_side_menu):
            widgets.append(
                create_button_side_menu(
                    master, i, 0,
                    text=window,
                    image=get_image_side_menu(window),
                    command=lambda x=window: self._select_frame_by_name(x),
                    columnspan=1)
            )
        return widgets

    def _select_frame_by_name(self, name):
        match name:
            case "none":
                for txt in self.names_side_menu:
                    self.windows_frames[txt].grid_forget()
                self._active_window = None
            case _:
                if self._active_window != name:
                    self.windows_frames[self._active_window].grid_forget() if self._active_window is not None else None
                    self._active_window = name
                    self.windows_frames[name].grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    def _create_side_menu_windows(self):
        windows = {}
        for i, window in enumerate(self.names_side_menu):
            match window:
                case "Encargados":
                    windows[window] = HeadsFrame(self, setting=self.settings, **self.kwargs)
                    print("heads frame created")
                case "Clientes":
                    windows[window] = CustomersFrame(self, setting=self.settings, **self.kwargs)
                    print("customers frame created")
                case "Empleados":
                    windows[window] = EmployeesFrame(self, setting=self.settings, **self.kwargs)
                    print("employees frame created")
                case "Departamentos":
                    windows[window] = DepartmentsFrame(self, setting=self.settings, **self.kwargs)
                    print("departments frame created")
                case "Proveedores":
                    windows[window] = SuppliersFrame(self, setting=self.settings, **self.kwargs)
                    print("suppliers frame created")
                case "Productos":
                    windows[window] = ProductsFrame(self, setting=self.settings, **self.kwargs)
                    print("products frame created")
                case "Ordenes":
                    windows[window] = OrdersFrame(self, setting=self.settings, **self.kwargs)
                    print("orders frame created")
                case "O. Virtuales":
                    windows[window] = VOrdersFrame(self, setting=self.settings, **self.kwargs)
                    print("virtual orders frame created")
                case "Chats":
                    windows[window] = ChatsFrame(self, setting=self.settings, **self.kwargs)
                    print("chats frame created")
                case "Tickets":
                    windows[window] = TicketsFrame(self, setting=self.settings, **self.kwargs)
                    print("tickets frame created")
                case _:
                    pass
        return windows
