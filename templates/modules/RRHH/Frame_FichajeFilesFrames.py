# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 14/nov./2023  at 17:12 $'

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.modules.RRHH.SubFrame_FichajesAuto import FichajesAuto
from templates.modules.RRHH.SubFrame_FichajesManual import FichajesManual


class FichajesFilesGUI(ScrolledFrame):
    def __init__(self, master=None, setting: dict = None, **kwargs):
        super().__init__(master, autohide=True)
        # noinspection PyTypeChecker
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # ----------------------variables-------------------------
        nb = ttk.Notebook(self)
        frame_1 = FichajesAuto(nb)
        frame_2 = FichajesManual(nb)
        nb.add(frame_1, text='Automatico')
        nb.add(frame_2, text='Manual')
        nb.grid(row=0, column=0, sticky="nswe", padx=(5, 25), pady=5)


