# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 12/nov/2024  at 16:07 $"

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.modules.Administration.SubFrame_ContractCreate import (
    ContractsCreateFrame,
)
from templates.modules.Administration.SubFrame_ContractDocs import ContractsDocsFrame


class MainContractFrame(ScrolledFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, autohide=True)
        self.columnconfigure(0, weight=1)
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nswe", padx=(5, 20))
        self.frame_1 = ContractsCreateFrame(self, **kwargs)
        notebook.add(self.frame_1, text="Desde Datos")
        self.frame_2 = ContractsDocsFrame(self, **kwargs)
        notebook.add(self.frame_2, text="Desde Documento")
