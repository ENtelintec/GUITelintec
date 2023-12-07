import json
import os
import re
import tkinter as tk
from tkinter import PhotoImage

import customtkinter as ctk
import ttkbootstrap as ttk
from PIL import Image

import templates.LoginGUI as Login
from templates.Functions_SQL import get_chats_w_limit
from templates.DBFrame import DBFrame
from templates.DisplayChat import ChatsDisplay
from templates.ScrollabeChats import ScrollableChats
from templates.ScrollPedidosTicket import ScrollPedidosTicket
from templates.notifications import Notifications
from templates.settings import ChatSettingsApp
from templates.DisplayPedidos import DisplayPedidos
import templates.cb_functions as cb

# from interface.VisualPedidos import VisualPedidos
carpeta_principal = "./img"

filepath_notifications = 'files/notifications.txt'
default_values_settings = {"max_chats": "40", "start_date": "19/oct./2023", "end_date": "19/oct./2023",
                           "sampling_time": 15}
chats_to_show = 40  # number of chats to show at the beginning

value = [['Employees', 'Customers', 'Departments', 'heads', 'Suppliers', 'Products', 'Name'],
         [1, 2, 3, 4, 5, 6, 7],
         [1, 2, 3, 4, 5, 6, 7],
         [1, 2, 3, 4, 5, 6, 7],
         [1, 2, 3, 4, 5, 6, 7]]

ctk.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"


def read_file(filepath) -> list[tuple]:
    """
    Read the file and return a list of tuples with the data of the file.
    :return: list of tuples with the data of the file.
    :rtype: list of tuples.
    """
    out = []
    with open(filepath, 'r') as file:
        content = file.readlines()
        for item in content:
            out.append(tuple(item.split(',;')))
    return out


def load_default_images():
    """
    Load the default images for the buttons.
    :return: a list of images.
    :rtype: list of images.
    """
    image_path = carpeta_principal
    return (ctk.CTkImage(Image.open(os.path.join(image_path, "telintec-500.png")), size=(90, 90)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "bd_img_col_!.png")),
                         size=(30, 30)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "not_img_col_re.png")),
                         size=(30, 30)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "departments_dark.png")),
                         dark_image=Image.open(os.path.join(image_path, "departments_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "settings.png")),
                         size=(40, 40)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "suppliers_dark.png")),
                         dark_image=Image.open(os.path.join(image_path, "suppliers_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "products_dark.png")),
                         dark_image=Image.open(os.path.join(image_path, "products_ligth.png")),
                         size=(20, 20)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "messenger.png")),
                         dark_image=Image.open(os.path.join(image_path, "messenger.png")),
                         size=(30, 30)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "whatsapp.png")),
                         dark_image=Image.open(os.path.join(image_path, "whatsapp.png")),
                         size=(30, 30)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "telegram.png")),
                         dark_image=Image.open(os.path.join(image_path, "telegram.png")),
                         size=(30, 30)),
            # revisar image webchat
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "chats_img.png")),
                         dark_image=Image.open(os.path.join(image_path, "chats_img.png")),
                         size=(30, 30)),
            ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "pedido_img.png")),
                         size=(30, 30)),

            )


class GUIAsistente(ttk.Window):
    def __init__(self, master=None, *args, **kwargs):
        # -----------------------window setup------------------------------
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.permissions = {"1" : "App.Deparment.Default"}
        self.title("Admin-Chatbot.py")
        p1 = PhotoImage(file=carpeta_principal + "/robot_1.png")
        self.iconphoto(False, p1)
        self.after(0, lambda: self.state('zoomed'))
        # self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        # -----------------------Variables-----------------------
        self.data_notifications = read_file(filepath_notifications)
        self.chats_to_show = int(default_values_settings["max_chats"])
        self.sample_time = default_values_settings["sampling_time"]
        self.time_window = 5
        # -----------------------load images -----------------------
        self.images = {}
        (self.logo_image, self.employees_img, self.customers_img, self.departments_img,
         self.settings_img, self.suppliers_img, self.products_img,
         self.images["facebook"], self.images["whatsapp"], self.images["telegram"],
         self.images["webchat"], self.pedido_img) = load_default_images()
        print("images and variables loaded")
        # -----------------------Create side menu frame-----------------------
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#040530")
        self.navigation_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=5)
        self.navigation_frame.grid_columnconfigure(0, weight=1)
        self.navigation_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        # --------------------------------title-------------------------------
        self.btnTeli = ctk.CTkButton(self.navigation_frame, image=self.logo_image,
                                     height=30, text="", hover=False,
                                     corner_radius=0, fg_color="transparent")
        self.btnTeli.grid(row=0, column=0, sticky="nsew")
        # --------------------widgets side menu -----------------------
        self.buttons_side_menu, self.names_side_menu = self.create_side_menu_widgets()
        # self.btn_DB = cb.create_button_side_menu(self.navigation_frame, 1, 0, text="DB",
        #                                          image=self.employees_img,
        #                                          command=lambda: self.select_frame_by_name("btn1"))
        # self.btn_notification = cb.create_button_side_menu(self.navigation_frame, 2, 0, text="Notifications",
        #                                                    image=self.customers_img,
        #                                                    command=lambda: self.select_frame_by_name("btn2"))
        # self.btn_chats = cb.create_button_side_menu(self.navigation_frame, 3, 0, text="Chats",
        #                                             image=self.departments_img,
        #                                             command=lambda: self.select_frame_by_name("btn3"))
        # self.btn_settings = cb.create_button_side_menu(self.navigation_frame, 4, 0, text="Settings",
        #                                                image=self.settings_img,
        #                                                command=lambda: self.select_frame_by_name("btn4"))
        # self.btn_ticket = cb.create_button_side_menu(self.navigation_frame, 5, 0, text="Pedidos",
        #                                              image=self.pedido_img,
        #                                              command=lambda: self.select_frame_by_name("btn5"))
        print("side menu widgets created")
        # ------------------------login frame-------------------------------
        self.login_frame = Login.LoginGUI(self)
        self.login_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=5, columnspan=2)
        # -----------------------DBFrame-----------------------
        self.db_frame = DBFrame(self)
        print("DB frame created")
        # -----------------------notifications frame-----------------------
        self.main_frame_notifications = Notifications(self, self.data_notifications,
                                                      filepath_notifications)
        print("notifications frame created")
        # -----------------------frame chat-----------------------
        self.main_frame_chat = ctk.CTkFrame(self, fg_color="#02021A")
        self.main_frame_chat.grid_columnconfigure(1, weight=1)
        self.main_frame_chat.grid_rowconfigure(0, weight=1)
        self.chats = get_chats_w_limit(limit=(0, chats_to_show))
        self.chats_selections = ScrollableChats(master=self.main_frame_chat,
                                                chats=self.chats,
                                                images=self.images,
                                                command=self.checked_chat_event,
                                                corner_radius=0,
                                                width=220, height=685)
        self.chats_selections.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.chats_selections.grid_columnconfigure(1, weight=1)
        self.chats_selections.grid_rowconfigure(0, weight=1)
        self.chat_display = ChatsDisplay(self.main_frame_chat,
                                         self.get_chat_id(str(self.chats[0][0])))
        self.chat_display.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.chat_display.grid_columnconfigure(1, weight=1)
        self.chat_display.grid_rowconfigure(0, weight=1)
        print("chats frame created")
        # -----------------------frame settings-----------------------
        self.main_frame_settings = tk.Frame(self, bg="#02021A")
        self.main_frame_settings.columnconfigure(0, weight=1)
        self.settings_display = ChatSettingsApp(self.main_frame_settings, self)
        self.settings_display.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        print("settings frame created")
        # -----------------------frame PedidosTickets-----------------------
        self.main_frame_ticket = ctk.CTkFrame(self, fg_color="#02021A")
        self.main_frame_ticket.columnconfigure(1, weight=1)
        self.main_frame_ticket.rowconfigure(0, weight=1)
        self.display_tickets = ScrollPedidosTicket(self.main_frame_ticket,
                                                   chats=self.chats,
                                                   images=self.images,
                                                   command=self.checked_chat_event,
                                                   corner_radius=0)
        self.display_tickets.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.pedidos_display = DisplayPedidos(self.main_frame_ticket,
                                              self.get_chat_id(str(self.chats[0][0])),
                                              corner_radius=0)
        self.pedidos_display.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.btn_process = tk.Button(self.main_frame_ticket, text="Process", width=100)
        self.btn_process.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.select_frame_by_name("none")

    def update_side_menu(self):
        self.buttons_side_menu, self.names_side_menu = self.create_side_menu_widgets()

    def checked_chat_event(self):
        checked_chat = self.chats_selections.get_checked_item()
        # print(checked_chat)
        chat_id = re.findall(r'(\d+)', checked_chat)
        chat_id = chat_id[0] if len(chat_id) > 0 else str(self.chats[0][0])
        self.chat_display.grid_forget()
        self.chat_display = ChatsDisplay(self.main_frame_chat,
                                         self.get_chat_id(chat_id),
                                         corner_radius=0, fg_color="#02021A")
        self.chat_display.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    def select_frame_by_name(self, name):
        # set button color for selected button
        print("Button clicked", name)
        for button in self.buttons_side_menu:
            if button.cget("text") == name:
                button.configure(fg_color=("gray75", "gray25"))
            else:
                button.configure(fg_color="transparent")
        # self.btn_DB.configure(fg_color=("gray75", "gray25") if name == "btn1" else "transparent")
        # self.btn_notification.configure(fg_color=("gray75", "gray25") if name == "btn2" else "transparent")
        # self.btn_chats.configure(fg_color=("gray75", "gray25") if name == "btn3" else "transparent")
        # self.btn_settings.configure(fg_color=("gray75", "gray25") if name == "btn4" else "transparent")
        # self.btn_ticket.configure(fg_color=("gray75", "gray25") if name == "btn5" else "transparent")
        # show selected frame
        match name:
            case "DB":
                self.hide_all_frame(1)
                self.db_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "Notificaciones":
                self.hide_all_frame(2)
                self.main_frame_notifications.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
                print("Notifications showed")
            case "Chats":
                self.hide_all_frame(3)
                self.main_frame_chat.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "Settings":
                self.hide_all_frame(4)
                self.main_frame_settings.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case "Tickets":
                self.hide_all_frame(5)
                self.main_frame_ticket.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
            case _:
                self.hide_all_frame(0)

    def hide_all_frame(self, val: int):
        self.db_frame.grid_forget() if val != 1 else None
        self.main_frame_notifications.grid_forget() if val != 2 else None
        self.main_frame_chat.grid_forget() if val != 3 else None
        self.main_frame_settings.grid_forget() if val != 4 else None
        self.main_frame_ticket.grid_forget() if val != 5 else None

    def get_chat_id(self, chat_id: str) -> list[dict | None]:
        out = None
        for item in self.chats:
            if str(item[0]) == chat_id:
                out = json.loads(item[2])
                break
        return out

    def checked_chat_event_1(self):
        checked_chat = self.chats_selections.get_checked_item()
        chat_id = re.findall(r'(\d+)', checked_chat)
        chat_id = chat_id[0] if len(chat_id) > 0 else str(self.chats[0][0])
        self.chat_display = ChatsDisplay(self.main_frame_chat,
                                         self.get_chat_id(chat_id))
        self.chat_display.grid(row=0, column=1, sticky="nsew")

    def get_image_side_menu(self, name):
        match name:
            case "DB":
                return self.employees_img
            case "Notificaciones":
                return self.customers_img
            case "Chats":
                return self.departments_img
            case "Settings":
                return self.settings_img
            case "Tickets":
                return self.pedido_img
            case _:
                return self.customers_img

    def create_side_menu_widgets(self):
        flag, windows_names = cb.compare_permissions_windows(list(self.permissions.values()))
        windows_names = windows_names if windows_names is not None else ["Notificaciones", "Settings"]
        widgets = []
        if flag or windows_names is not None:
            for i, window in enumerate(windows_names):
                widgets.append(cb.create_button_side_menu(
                    self.navigation_frame,
                    i, 0,
                    text=window,
                    image=self.get_image_side_menu(window),
                    command=lambda x=window:  self.select_frame_by_name(x)))
        return widgets, windows_names

