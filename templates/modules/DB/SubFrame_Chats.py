# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 21:03 $'

import ttkbootstrap as ttk

from templates.Functions_GUI_Utils import create_visualizer_treeview


class ChatsFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.label = ttk.Label(self, text="Chats table", font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        ps_chats = create_visualizer_treeview(self.visual_frame, "chats", row=0, column=0, style="success")
