# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 13/may./2024  at 15:12 $'

import ttkbootstrap as ttk

from templates.modules.RRHH.SubFrame_CrearQuiz import FrameEncuestas
from templates.modules.RRHH.SubFrame_ReviewQuizz import ViewQuizz


class EncuestasFrame(ttk.Notebook):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)

        frame_1 = FrameEncuestas(self, **kwargs)
        self.add(frame_1, text='Crear')
        frame_2 = ViewQuizz(self, **kwargs)
        self.add(frame_2, text='Resultados')
