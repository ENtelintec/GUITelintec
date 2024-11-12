# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 12/nov/2024  at 13:47 $"

import ttkbootstrap as ttk

from templates.modules.Administration.Clients import ClientsScreen
from templates.modules.Administration.Providers import ProvidersScreen


class AdminDBFrame(ttk.Notebook):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.frame_1 = ClientsScreen(self, **kwargs)
        self.add(self.frame_1, text="Clientes")
        self.frame_2 = ProvidersScreen(self, **kwargs)
        self.add(self.frame_2, text="Proveedores")