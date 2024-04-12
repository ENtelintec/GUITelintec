# -*- coding: utf-8 -*-
__author__ = 'Edisson'
__date__ = '$ October 12, 2023 09:17 $'

import json
import re

import customtkinter as ctk
import ttkbootstrap as ttk
from templates.Functions_SQL import get_chats_w_limit
from templates.frames.SubFrame_DisplayChatSubframe import ChatsDisplay


class ScrollableChats(ctk.CTkScrollableFrame):
    def __init__(self, master, chats=None, command=None, images=None, **kwargs):
        super().__init__(master, **kwargs, fg_color="#040546")
        self.images = images
        self.command = command
        self.radiobutton_variable = ctk.StringVar()
        self.label_list = []
        self.radiobutton_list = []
        self.chats = [] if chats is None else chats
        for i in self.chats:  # chat
            match i[1]:
                case "telegram":
                    self.add_item(f"Chat: {i[0]}", image=images[i[1]])
                case "whatsapp":
                    self.add_item(f"Chat: {i[0]}", image=images[i[1]])
                case "facebook":
                    self.add_item(f"Chat: {i[0]}", image=images[i[1]])
                case _:
                    self.add_item(f"Chat: {i[0]}", image=images[i[1]])

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


class ChatFrame(ttk.Frame):
    def __init__(self, master, chats_to_show, images, chats=None, setting: dict = None, **kwargs):
        # noinspection PyArgumentList
        super().__init__(master, **kwargs)
        # -------------variables and config----------------------------
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.chats_to_show = chats_to_show
        self.images = images
        # --------------widgets--------------
        self.chats = get_chats_w_limit(limit=(0, self.chats_to_show)) if chats is None else chats
        self.chats_selections = ScrollableChats(self,
                                                chats=self.chats,
                                                images=self.images,
                                                command=self.checked_chat_event,
                                                corner_radius=0,
                                                width=220, height=685)
        self.chats_selections.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.chats_selections.grid_columnconfigure(1, weight=1)
        self.chats_selections.grid_rowconfigure(0, weight=1)
        self.chat_display = ChatsDisplay(self,
                                         self.get_chat_id(str(self.chats[0][0])))
        self.chat_display.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.chat_display.grid_columnconfigure(1, weight=1)
        self.chat_display.grid_rowconfigure(0, weight=1)

    def checked_chat_event(self):
        checked_chat = self.chats_selections.get_checked_item()
        # print(checked_chat)
        chat_id = re.findall(r'(\d+)', checked_chat)
        chat_id = chat_id[0] if len(chat_id) > 0 else str(self.chats[0][0])
        self.chat_display.grid_forget()
        self.chat_display = ChatsDisplay(self,
                                         self.get_chat_id(chat_id),
                                         corner_radius=0, fg_color="#02021A")
        self.chat_display.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    def get_chat_id(self, chat_id: str) -> list[dict | None]:
        out = None
        for item in self.chats:
            if str(item[0]) == chat_id:
                out = json.loads(item[2])
                break
        return out
