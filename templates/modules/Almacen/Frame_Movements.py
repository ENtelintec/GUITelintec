# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 08/may./2024  at 15:14 $'

import ttkbootstrap as ttk

from templates.modules.Almacen.In import InScreen
from templates.modules.Almacen.Out import OutScreen


class MovementsFrame(ttk.Notebook):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        frame_1 = InScreen(self, **kwargs)
        self.add(frame_1, text='Entradas')
        frame_2 = OutScreen(self, **kwargs)
        self.add(frame_2, text='Salidas')
