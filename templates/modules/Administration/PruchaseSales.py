# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/nov/2024  at 10:38 $"

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.modules.Administration.SubFrame_Purchases import RequestPurchaseFrame


class PurchasesFrame(ScrolledFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, autohide=True)
        self.columnconfigure(0, weight=1)
        nb = ttk.Notebook(self)
        nb.grid(row=0, column=0, sticky="nswe", padx=(5, 20), pady=15)
        frame_1 = RequestPurchaseFrame(nb, **kwargs)
        nb.add(frame_1, text="Solicitudes")
