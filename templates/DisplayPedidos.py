import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from templates.VisualPedidos import VisualPedidos


class DisplayPedidos(ctk.CTkFrame):
    def __init__(self, master, chat, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        if chat is None:
            chat = []
        else:
            chat = chat
        self.chat = chat

        # Chat unificado:
        self.unificado = tk.Text(self, font=("Helvetica", 12))
        self.unificado.config(bg="#040530")
        self.unificado.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        for mensaje in self.chat:
            content = mensaje["content"]
            role = mensaje["role"]
            if role == "user":
                # Agregar un tag "user" para la alineación a la derecha
                self.unificado.tag_configure("user", justify="left",
                                             foreground="white",
                                             font=("Helvetica", 12, "bold"))
                self.unificado.insert(tk.END,
                                      f'USER: {content}\n',
                                      "user")
                self.unificado.insert(ctk.END, "\n")
            elif role == "assistant":
                # Agregar un tag "assistant" para la alineación a la izquierda
                # self.unificado.tag_add("assistant", "1.0", "1.4")
                self.unificado.tag_configure("assistant", justify="left",
                                             foreground="#0859ff",
                                             font=("Helvetica", 12, "bold"))
                self.unificado.insert(tk.END,
                                      f'Asistente: {content}\n',
                                      "assistant")
                self.unificado.insert(ctk.END, "\n")
        self.visual_pedidos = VisualPedidos(self)
        self.visual_pedidos.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
