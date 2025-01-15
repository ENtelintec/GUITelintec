# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 12/nov/2024  at 13:47 $"

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.modules.Administration.SubFrame_Clients import ClientsScreen
from templates.modules.Administration.SubFrame_Providers import ProvidersScreen


class AdminDBFrame(ScrolledFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, autohide=True)
        self.columnconfigure(0, weight=1)
        nb = ttk.Notebook(self)
        nb.grid(row=0, column=0, sticky="nswe", padx=(5, 20))
        frame_1 = ClientsScreen(self, **kwargs)
        nb.add(frame_1, text="Clientes")
        frame_2 = ProvidersScreen(self, **kwargs)
        nb.add(frame_2, text="Proveedores")
