import json
import re
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from templates.modules.Chatbot.SubFrame_DisplayChatSubframe import ChatsDisplay


class DisplayPedidos(ctk.CTkFrame):
    def __init__(self, master, pedido=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        self.pedido = pedido if pedido is None else pedido

        # Chat unificado:
        self.unificado = tk.Text(self, font=("Helvetica", 12))
        self.unificado.config(bg="#040530")
        self.unificado.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        for mensaje in self.pedido:
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


class PedidosFrame(ttk.Frame):
    def __init__(self, parent, images, pedidos=None, setting: dict = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.pedidos = [] if pedidos is None else pedidos
        self.images = images
        self.display_tickets = ScrollPedidosTicket(self,
                                                   chats=self.pedidos,
                                                   images=self.images,
                                                   command=self.checked_chat_event,
                                                   corner_radius=0)
        self.display_tickets.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.pedidos_display = DisplayPedidos(self,
                                              self.get_pedido_id(str(self.pedidos[0][0])),
                                              corner_radius=0)
        self.pedidos_display.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.btn_process = tk.Button(self, text="Process", width=100)
        self.btn_process.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

    def checked_chat_event(self):
        checked_chat = self.display_tickets.get_checked_item()
        # print(checked_chat)
        chat_id = re.findall(r'(\d+)', checked_chat)
        chat_id = chat_id[0] if len(chat_id) > 0 else str(self.pedidos[0][0])
        self.pedidos_display.grid_forget()
        self.pedidos_display = ChatsDisplay(self,
                                            self.get_pedido_id(chat_id),
                                            corner_radius=0, fg_color="#02021A")
        self.pedidos_display.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    def get_pedido_id(self, chat_id: str) -> list[dict | None]:
        out = None
        for item in self.pedidos:
            if str(item[0]) == chat_id:
                out = json.loads(item[2])
                break
        return out


class ScrollPedidosTicket(ctk.CTkScrollableFrame):
    def __init__(self, master, chats=None, command=None, images=None, **kwargs):
        super().__init__(master, fg_color="#040546", **kwargs)
        self.rowconfigure(0, weight=1)
        self.images = images
        self.command = command
        self.radiobutton_variable = ctk.StringVar()
        self.label_list = []
        self.radiobutton_list = []
        self.chats = [] if chats is None else chats
        for i in self.chats:  # chat
            match i[1]:
                case "telegram":
                    self.add_item(f"Pedido: {i[0]}", image=images[i[1]])
                case "whatsapp":
                    self.add_item(f"Pedido: {i[0]}", image=images[i[1]])
                case "facebook":
                    self.add_item(f"Pedido: {i[0]}", image=images[i[1]])
                case _:
                    self.add_item(f"Pedido: {i[0]}", image=images[i[1]])

    def add_item(self, txt, image=None):
        label = ctk.CTkLabel(self, text="", image=image,
                             compound="left", padx=1,
                             width=5, height=30, anchor="w")
        radiobutton = ctk.CTkRadioButton(self, text=txt, text_color="#fff", value=txt,
                                         radiobutton_height=1, radiobutton_width=1,
                                         width=170, height=40,
                                         font=ctk.CTkFont(size=25, weight="normal"),
                                         variable=self.radiobutton_variable)
        if self.command is not None:
            radiobutton.configure(command=self.command)
        radiobutton.grid(row=len(self.radiobutton_list), column=1, pady=(0, 10), padx=5)
        self.radiobutton_list.append(radiobutton)
        label.grid(row=len(self.label_list), column=0, pady=(0, 2), padx=1, sticky="w")
        self.label_list.append(label)

    def remove_item(self, item):
        for label, button in zip(self.label_list, self.radiobutton_list):
            if item == button.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.radiobutton_list.remove(button)
                return

    def get_checked_item(self):
        return self.radiobutton_variable.get()

    def update_chats(self, new_chats):

        for i in self.chats:  # chat
            self.remove_item(f"Chat: {i[0]}")
            print("removed ", f"Chat: {i[0]}")
        self.chats = new_chats
        for i in self.chats:  # chat
            match i[1]:
                case "telegram":
                    self.add_item(f"Chat: {i[0]}", image=self.images[i[1]])
                case "whatsapp":
                    self.add_item(f"Chat: {i[0]}", image=self.images[i[1]])
                case "facebook":
                    self.add_item(f"Chat: {i[0]}", image=self.images[i[1]])
                case _:
                    self.add_item(f"Chat: {i[0]}", image=self.images[i[1]])


class ScrollableLabelFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs, fg_color="#02021A")
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.radiobutton_variable = ctk.StringVar()
        self.label_list = []
        self.button_list = []

    def add_item(self, txt, row, colum, height, width, image=None):
        label = ctk.CTkLabel(self, text=txt, image=image, compound="left", padx=5, anchor="w")
        self.label_list.append(label)

    def remove_item(self, item):
        for label in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                self.label_list.remove(label)
                return


class VisualPedidos(ttk.Treeview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # tk.Frame.__init__(self, master, **kwargs)
        # Crear el Treeview
        self.tree = ttk.Treeview(self, columns=("Nombre", "Edad"))
        self.tree.heading("#1", text="Nombre")
        self.tree.heading("#2", text="Edad")

        # Agregar algunos datos ficticios
        self.tree.insert("", "end", values=("Juan", 30))
        self.tree.insert("", "end", values=("María", 25))
        self.tree.insert("", "end", values=("Carlos", 35))
        self.tree.insert("", "end", values=("Laura", 28))
