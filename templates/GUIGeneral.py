import os
from tkinter import PhotoImage

import customtkinter as ctk
import ttkbootstrap as ttk
from PIL import Image

import templates.LoginGUI as Login
import templates.cb_functions as cb
from templates.DBFrame import DBFrame
from templates.DisplayPedidos import PedidosFrame
from templates.FichajeFilesGUI import FichajesFilesGUI
from templates.Functions_SQL import get_chats_w_limit
from templates.ScrollabeChats import ChatFrame
from templates.notifications import Notifications
from templates.settings import ChatSettingsApp

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
        self.permissions = {"1": "App.Deparment.Default"}
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
        self.chats = get_chats_w_limit(limit=(0, chats_to_show))
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
        print("side menu widgets created")
        # ------------------------login frame-------------------------------
        self.login_frame = Login.LoginGUI(self)
        self.login_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=5, columnspan=2)
        # create other frames
        self.windows_frames = self.create_side_menu_windows()
        self.select_frame_by_name("none")

    def update_side_menu(self):
        self.buttons_side_menu, self.names_side_menu = self.create_side_menu_widgets()

    def update_side_menu_windows(self):
        self.windows_frames = self.create_side_menu_windows()

    def select_frame_by_name(self, name):
        # set button color for selected button
        print("Button clicked", name)
        for button in self.buttons_side_menu:
            if button.cget("text") == name:
                button.configure(fg_color=("gray75", "gray25"))
            else:
                button.configure(fg_color="transparent")
        match name:
            case "none":
                for txt in self.names_side_menu:
                    self.windows_frames[txt].grid_forget()
            case _:
                for txt in self.names_side_menu:
                    if txt == name:
                        self.windows_frames[name].grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
                    else:
                        self.windows_frames[txt].grid_forget()

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
            case "Horarios":
                return self.suppliers_img
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
                    command=lambda x=window: self.select_frame_by_name(x)))
        return widgets, windows_names

    def create_side_menu_windows(self):
        windows = {}
        for i, window in enumerate(self.names_side_menu):
            match window:
                case "DB":
                    windows[window] = DBFrame(self)
                    print("DB frame created")
                case "Notificaciones":
                    windows[window] = Notifications(self, self.data_notifications,
                                                    filepath_notifications)
                    print("notifications frame created")
                case "Chats":
                    windows[window] = ChatFrame(self, self.chats_to_show, self.images, self.chats)
                    print("chats frame created")
                case "Settings":
                    windows[window] = ChatSettingsApp(self)
                    print("settings frame created")
                case "Tickets":
                    windows[window] = PedidosFrame(self, self.images, self.chats)
                case "Horarios":
                    windows[window] = FichajesFilesGUI(self)
                case _:
                    pass
        return windows
