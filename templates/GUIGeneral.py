from tkinter import PhotoImage

import customtkinter as ctk
import ttkbootstrap as ttk

import templates.Functions_Observer as cb
import templates.frames.Frame_LoginFrames as Login
from templates.screens.Clients import ClientsScreen
from templates.screens.Home import HomeScreen
from templates.screens.In import InScreen
from templates.screens.Inventory import InventoryScreen
from templates.screens.Orders import OrdersScreen
from templates.screens.Out import OutScreen
from templates.screens.Providers import ProvidersScreen
from templates.screens.Returns import ReturnsScreen
from templates.screens.Settings import SettingsScreen
from templates import AlmacenGUI
from templates.Functions_AuxFiles import carpeta_principal, get_image_side_menu
from templates.Functions_Files import read_file_not
from templates.Functions_SQL import get_chats_w_limit, get_username_data
from templates.frames.Frame_ChatsFrame import ChatFrame
from templates.frames.Frame_DBFrame import DBFrame
from templates.frames.Frame_EmployeeDetail import EmployeeDetails
from templates.frames.Frame_ExamenesMedicos import ExamenesMedicosFrame
from templates.frames.Frame_FichajeFilesFrames import FichajesFilesGUI
from templates.frames.Frame_NotificationsFrame import Notifications
from templates.frames.Frame_PedidosFrame import PedidosFrame
from templates.frames.Frame_SettingsFrame import ChatSettingsApp
from templates.frames.Frame_vAssistantGUI import AssistantGUI

# from interface.VisualPedidos import VisualPedidos


filepath_notifications = 'files/notifications.txt'
default_values_settings = {"max_chats": "40", "start_date": "19/oct./2023", "end_date": "19/oct./2023",
                           "sampling_time": 15}
chats_to_show = 40  # number of chats to show at the beginning


class GUIAsistente(ttk.Window):
    def __init__(self, master=None, *args, **kwargs):
        # -----------------------window setup------------------------------
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.title("Admin-Chatbot.py")
        p1 = PhotoImage(file=carpeta_principal + "/robot_1.png")
        self.iconphoto(False, p1)
        self.after(0, lambda: self.state('zoomed'))
        # self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        # -----------------------Variables-----------------------
        self.permissions = {"1": "App.Deparment.Default"}
        self.username = "default"
        self.username_data = None
        self.windows_frames = None
        self.data_notifications = read_file_not(filepath_notifications)
        self.chats_to_show = int(default_values_settings["max_chats"])
        self.sample_time = default_values_settings["sampling_time"]
        self.time_window = 5
        self.chats = get_chats_w_limit(limit=(0, chats_to_show))
        self.virtual_assistant_window = None
        self.VA_frame = None
        # -----------------------load images -----------------------
        self.images = {
            "facebook": get_image_side_menu("facebook"),
            "whatsapp": get_image_side_menu("whatsapp"),
            "telegram": get_image_side_menu("telegram"),
            "webchat": get_image_side_menu("webchat")
        }
        print("images and variables loaded")
        # -----------------------Create side menu frame-----------------------
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#040530")
        self.navigation_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=5, rowspan=2)
        self.navigation_frame.grid_columnconfigure(0, weight=1)
        self.navigation_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        # --------------------------------title-------------------------------
        self.btnTeli = ctk.CTkButton(self.navigation_frame, image=get_image_side_menu("logo"),
                                     height=30, text="", hover=False,
                                     corner_radius=0, fg_color="transparent")
        self.btnTeli.grid(row=0, column=0, sticky="nsew")
        # --------------------widgets side menu -----------------------
        self.buttons_side_menu, self.names_side_menu = self._create_side_menu_widgets()
        print("side menu widgets created")
        # ------------------------login frame-------------------------------
        self.login_frame = Login.LoginGUI(self)
        self.login_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=5, columnspan=2)

    def logOut(self):
        self._select_frame_by_name("none")
        self._destroy_side_menu_widgets()
        self.login_frame = Login.LoginGUI(self)
        self.login_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=5, columnspan=2)

    def get_username_data(self):
        self.username_data = get_username_data(self.username)

    def update_side_menu(self):
        print(f"side menu for: {self.username} with {self.permissions}")
        self.buttons_side_menu, self.names_side_menu = self._create_side_menu_widgets()

    def update_side_menu_windows(self):
        print(f"windows menu for: {self.username} with {self.permissions}")
        self.windows_frames = self._create_side_menu_windows()
        department = "default"  # default department if no department permissions are found
        for k, v in self.permissions.items():
            if "App.Deparment" in v:
                department = v.split(".")[-1]
                break
        self.VA_frame = ttk.Frame(self, width=150)
        self.VA_frame.rowconfigure(0, weight=1)
        self.VA_frame.grid(row=0, column=2, sticky="nsew", pady=10, padx=5)
        self.virtual_assistant_window = AssistantGUI(self.VA_frame, department=department, width=150)
        self.virtual_assistant_window.grid(row=0, column=0)

    def _select_frame_by_name(self, name):
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
                self.VA_frame.grid_forget()
            case _:
                for txt in self.names_side_menu:
                    if txt == name:
                        self.windows_frames[name].grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
                    else:
                        self.windows_frames[txt].grid_forget()

    def _create_side_menu_widgets(self):
        flag, windows_names = cb.compare_permissions_windows(list(self.permissions.values()))
        windows_names = windows_names if windows_names is not None else ["Notificaciones", "Settings"]
        widgets = []
        if flag or windows_names is not None:
            for i, window in enumerate(windows_names):
                widgets.append(cb.create_button_side_menu(
                    self.navigation_frame,
                    i + 1, 0,
                    text=window,
                    image=get_image_side_menu(window),
                    command=lambda x=window: self._select_frame_by_name(x)))
        return widgets, windows_names

    def _create_side_menu_windows(self):
        windows = {}
        for i, window in enumerate(self.names_side_menu):
            match window:
                case "DB":
                    windows[window] = DBFrame(self)
                    print("DB frame created")
                case "Notificaciones":
                    windows[window] = Notifications(
                        self, self.data_notifications, filepath_notifications)
                    print("notifications frame created")
                case "Chats":
                    windows[window] = ChatFrame(self, self.chats_to_show, self.images, self.chats)
                    print("chats frame created")
                case "Settings":
                    windows[window] = ChatSettingsApp(self)
                    print("settings frame created")
                case "Tickets":
                    windows[window] = PedidosFrame(self, self.images, self.chats)
                    print("tickets frame created")
                case "Fichajes":
                    windows[window] = FichajesFilesGUI(self)
                    print("Fichajes frame created")
                case "Cuenta":
                    windows[window] = Login.LogOptionsFrame(self)
                    print("cuenta frame created")
                case "Examenes":
                    windows[window] = ExamenesMedicosFrame(self)
                    print("examenes frame created")
                case "Almacen":
                    windows[window] = AlmacenGUI.App(self)
                    print("almacen frame created")
                case "Emp. Detalles":
                    windows[window] = EmployeeDetails(self)
                    print("Employee details frame created")
                case "Home":
                    windows[window] = HomeScreen(self)
                    print("home frame created")
                case "Clients (A)":
                    windows[window] = ClientsScreen(self)
                    print("clients frame created")
                case "Inventario":
                    windows[window] = InventoryScreen(self)
                    print("inventory frame created")
                case "Configuraciones (A)":
                    windows[window] = SettingsScreen(self)
                    print("settings frame created")
                case "Entradas":
                    windows[window] = InScreen(self)
                    print("in frame created")
                case "Salidas":
                    windows[window] = OutScreen(self)
                    print("out frame created")
                case "Devoluciones":
                    windows[window] = ReturnsScreen(self)
                    print("returns frame created")
                case "Ordenes (A)":
                    windows[window] = OrdersScreen(self)
                    print("orders frame created")
                case "Proveedores (A)":
                    windows[window] = ProvidersScreen(self)
                    print("providers frame created")
                case _:
                    pass
        return windows

    def _destroy_side_menu_widgets(self):
        for widget in self.buttons_side_menu:
            widget.destroy()
