# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 06/feb./2024  at 9:14 $"

import tkinter as tk
from ttkbootstrap import Style, Window
from templates.frames.Frame_Quizzes import FrameEncuestas

if __name__ == "__main__":
    root = Window()
    root.title("Encuestas")
    style = Style(theme="minty")

    app = FrameEncuestas(root)

    # dict_quizz = new_dict

    app.pack(fill="both", expand=True)

    root.mainloop()
