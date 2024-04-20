import tkinter as tk
from tkinter import PhotoImage

import ttkbootstrap as ttk

import templates.frames.Frame_LoginFrames as Login
from static.extensions import filepath_settings, permissions_allowed_AV
from templates import AlmacenGUI
from templates.Functions_AuxFiles import carpeta_principal, get_image_side_menu, read_setting_file
from templates.Functions_Files import read_file_not
from templates.Functions_SQL import get_chats_w_limit, get_username_data
from templates.Funtions_Utils import create_button_side_menu, compare_permissions_windows
from templates.frames.Frame_Bitacora import BitacoraEditFrame
from templates.frames.Frame_ChatsFrame import ChatFrame
from templates.frames.Frame_DBFrame import DBFrame, EmployeesFrame
from templates.frames.Frame_EmployeeDetail import EmployeeDetails
from templates.frames.Frame_ExamenesMedicos import ExamenesMedicos
from templates.frames.Frame_FichajeFilesFrames import FichajesFilesGUI
from templates.frames.Frame_NotificationsFrame import Notifications
from templates.frames.Frame_PedidosFrame import PedidosFrame
from templates.frames.Frame_Quizzes import FrameEncuestas
from templates.frames.Frame_SMGeneral import SMFrame
from templates.frames.Frame_SettingsFrame import SettingsFrameGUI
from templates.frames.Frame_Vacations import VacationsFrame
from templates.frames.Frame_vAssistantGUI import AssistantGUI
from templates.screens.Clients import ClientsScreen
from templates.screens.Home import HomeScreen
from templates.screens.In import InScreen
from templates.screens.InternalInventory import InternalInventoryScreen
from templates.screens.Inventory import InventoryScreen
from templates.screens.Orders import OrdersScreen
from templates.screens.Out import OutScreen
from templates.screens.Providers import ProvidersScreen
from templates.screens.Settings import SettingsScreen
from templates.screens.Supplies import SuppliesScreen

filepath_notifications = 'files/notifications.txt'
default_values_settings = {"max_chats": "40", "start_date": "19/oct./2023", "end_date": "19/oct./2023",
                           "sampling_time": 15}
chats_to_show = 40  # number of chats to show at the beginning


class GUIAsistente(ttk.Window):
    def __init__(self, master=None, *args, **kwargs):
        # -----------------------window setup------------------------------
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.style_gui = ttk.Style()
        self.style_gui.theme_use("vapor")
        self.title("Admin-Chatbot.py")
        p1 = PhotoImage(file=carpeta_principal + "/robot_1.png")
        self.iconphoto(False, p1)
        # self.after(0, lambda: self.state('zoomed'))
        # self.state('zoomed')
        # self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        # -----------------------Variables-----------------------
        self.permissions = {"1": "App.Deparment.Default"}
        self.settings = read_setting_file(filepath_settings)
        self.username = "default"
        self.department = "default"
        self.contrato = "default"
        self.username_data = None
        self.windows_frames = None
        self.data_notifications = read_file_not(filepath_notifications)
        self.chats_to_show = int(default_values_settings["max_chats"])
        self.sample_time = default_values_settings["sampling_time"]
        self.time_window = 5
        self.chats = get_chats_w_limit(limit=(0, chats_to_show))
        self.virtual_assistant_window = None
        self.VA_frame = None
        self._active_window = None
        # -----------------------load images -----------------------
        self.images = {
            "facebook": get_image_side_menu("facebook"),
            "whatsapp": get_image_side_menu("whatsapp"),
            "telegram": get_image_side_menu("telegram"),
            "webchat": get_image_side_menu("webchat")
        }
        # -----------------------Create side menu frame-----------------------
        self.navigation_frame = ttk.Frame(self)
        self.navigation_frame.grid(row=0, column=0, sticky="nswe", pady=10, padx=5)
        self.navigation_frame.columnconfigure((0, 1), weight=1)
        self.navigation_frame.rowconfigure(2, weight=1)
        # --------------------------------title-------------------------------
        self.btnTeli = LogoFrame(self.navigation_frame)
        self.btnTeli.grid(row=0, column=0, sticky="we", columnspan=2)
        theme_names = self.style_gui.theme_names()
        ttk.Label(self.navigation_frame, text="Theme:").grid(row=1, column=0, sticky="nsew")
        self.theme_selector = ttk.Combobox(self.navigation_frame, values=theme_names,
                                           state="readonly")
        self.theme_selector.current(theme_names.index('vapor'))
        self.theme_selector.grid(row=1, column=1, sticky="nsew")
        self.theme_selector.bind('<<ComboboxSelected>>', lambda event: self.style_gui.theme_use(self.theme_selector.get()))
        # --------------------widgets side menu -----------------------
        self.side_menu_frame = ttk.Frame(self.navigation_frame)
        self.side_menu_frame.grid(row=2, column=0, sticky="nsew", pady=5, padx=1,
                                  columnspan=2)
        self.side_menu_frame.columnconfigure(0, weight=1)
        self.buttons_side_menu, self.names_side_menu = self._create_side_menu_widgets(self.side_menu_frame)
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
        self.username_data["permissions"] = self.permissions

    def update_side_menu(self):
        print(f"side menu for: {self.username} with {self.permissions}")
        self.buttons_side_menu, self.names_side_menu = self._create_side_menu_widgets(self.side_menu_frame)

    def update_side_menu_windows(self):
        self.get_username_data()
        self.windows_frames = self._create_side_menu_windows()
        department = self.username_data["department_name"] if self.username_data is not None else "default"
        for k, v in self.permissions.items():
            if "ALMACEN" in v:
                department = "almacen"
                break
        for k, v in self.permissions.items():
            if v in permissions_allowed_AV:
                self.create_AV_window(department)
                break

    def create_AV_window(self, department):
        self.VA_frame = ttk.Frame(self, width=150)
        self.VA_frame.rowconfigure(0, weight=1)
        self.VA_frame.grid(row=0, column=2, sticky="nsew", pady=10, padx=5)
        self.virtual_assistant_window = AssistantGUI(self.VA_frame, department=department, width=150)
        self.virtual_assistant_window.grid(row=0, column=0, sticky="nsew")
        self.department = department
        self.update_style_department()

    def _select_frame_by_name(self, name):
        match name:
            case "none":
                for txt in self.names_side_menu:
                    self.windows_frames[txt].grid_forget()
                if self.VA_frame is not None:
                    self.VA_frame.grid_forget()
                self._active_window = None
            case _:
                if self._active_window != name:
                    self.windows_frames[self._active_window].grid_forget() if self._active_window is not None else None
                    self._active_window = name
                    self.windows_frames[name].grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    def _create_side_menu_widgets(self, master):
        flag, windows_names = compare_permissions_windows(list(self.permissions.values()))
        windows_names = windows_names if windows_names is not None else ["Cuenta"]
        widgets = []
        if flag or windows_names is not None:
            if len(windows_names) >= 12:
                scrollbar = ttk.Scrollbar(master, orient="vertical")
                scrollbar.grid(row=0, column=2, sticky="ns")
            for i, window in enumerate(windows_names):
                widgets.append(
                    create_button_side_menu(
                        master, i, 0,
                        text=window,
                        image=get_image_side_menu(window),
                        command=lambda x=window: self._select_frame_by_name(x),
                        columnspan=1)
                )
        return widgets, windows_names

    def _create_side_menu_windows(self):
        windows = {}
        for i, window in enumerate(self.names_side_menu):
            match window:
                case "DB":
                    windows[window] = DBFrame(self, setting=self.settings)
                    print("DB frame created")
                case "Notificaciones":
                    windows[window] = Notifications(
                        self, self.data_notifications, filepath_notifications)
                    print("notifications frame created")
                case "Chats":
                    windows[window] = ChatFrame(self, self.chats_to_show, self.images, self.chats)
                    print("chats frame created")
                case "Settings":
                    windows[window] = SettingsFrameGUI(self, department=self.department, style_gui=self.style_gui)
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
                    windows[window] = ExamenesMedicos(self)
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
                case "Suministros Diarios":
                    windows[window] = SuppliesScreen(self)
                    print("diary supplies frame created")
                case "Configuraciones (A)":
                    windows[window] = SettingsScreen(self)
                    print("settings frame created")
                case "Entradas":
                    windows[window] = InScreen(self)
                    print("in frame created")
                case "Salidas":
                    windows[window] = OutScreen(self)
                    print("out frame created")
                case "Ordenes (A)":
                    windows[window] = OrdersScreen(self)
                    print("orders frame created")
                case "Proveedores (A)":
                    windows[window] = ProvidersScreen(self)
                    print("providers frame created")
                case "Inventario Int.":
                    windows[window] = InternalInventoryScreen(self)
                    print("inventory internal frame created")
                case "Empleados":
                    windows[window] = EmployeesFrame(self)
                    print("employees frame created")
                case "Vacaciones":
                    windows[window] = VacationsFrame(self)
                    print("vacations frame created")
                case "Encuestas":
                    windows[window] = FrameEncuestas(self)
                    print("encuestas frame created")
                case "Bitacora":
                    windows[window] = BitacoraEditFrame(self, self.username, self.username_data["contract"])
                    print("bitacora frame created")
                case "SM":
                    windows[window] = SMFrame(self, self.settings, department=self.department, id_emp=self.username_data["id"], data_emp=self.username_data)
                    print("SM frame created")
                case _:
                    pass
        return windows

    def _destroy_side_menu_widgets(self):
        for widget in self.buttons_side_menu:
            widget.destroy()

    def update_style_department(self):
        if self.department in self.settings["gui"]:
            self.style_gui.theme_use(self.settings["gui"][self.department]["theme"])


class LogoFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        img_logo = get_image_side_menu("logo")
        width = 100
        height = 80
        canva = tk.Canvas(self, width=width, height=height)
        canva.grid(row=0, column=0, sticky="nswe", columnspan=2, padx=20)
        canva.create_image(width / 2, height / 2, anchor='center', image=img_logo)
        canva.image = img_logo
