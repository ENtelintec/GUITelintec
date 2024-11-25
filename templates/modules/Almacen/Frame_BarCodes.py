# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 25/nov/2024  at 16:24 $"

import json
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.modules.Almacen.SubFrameBarcode import BarcodeFrame
from templates.modules.Almacen.SubFrameBarcodeMultiple import BarcodeMultipleFrame


class BarcodeSubFrameSelector(ttk.Toplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.title("Código de barras")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        frame_notebook = ScrolledFrame(self, autohide=True)
        frame_notebook.grid(row=0, column=0, sticky="nswe")
        frame_notebook.columnconfigure(0, weight=1)
        nb = ttk.Notebook(frame_notebook)
        nb.grid(row=0, column=0, sticky="nswe", padx=(5, 20), pady=5)
        nb.columnconfigure(0, weight=1)
        frame_individual = BarcodeFrame(nb, **kwargs)
        nb.add(frame_individual, text="Individual")
        frame_multiple = BarcodeMultipleFrame(nb, **kwargs)
        nb.add(frame_multiple, text="Multiple")
