import json
import tkinter as tk
from tkinter import PhotoImage

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

import templates.modules.Sesion.Frame_LoginFrames as Login
from static.extensions import filepath_settings, ventanasApp_path
from templates.Functions_AuxFiles import carpeta_principal, get_image_side_menu, read_setting_file, get_all_sm_entries, \
    get_all_sm_products
from templates.Functions_Files import read_file_not
from templates.Funtions_Utils import create_button_side_menu, compare_permissions_windows
from templates.controllers.chatbot.chatbot_controller import get_chats_w_limit
from templates.controllers.customer.customers_controller import get_sm_clients
from templates.controllers.employees.employees_controller import get_sm_employees
from templates.controllers.employees.us_controller import get_username_data
from templates.controllers.product.p_and_s_controller import get_ins_db
from templates.modules.Almacen.Frame_Movements import MovementsFrame
from templates.modules.Bitacora.Frame_Bitacora import BitacoraEditFrame
from templates.modules.Chatbot.Frame_ChatsFrame import ChatFrame
from templates.modules.DB.Frame_DBFrame import DBFrame, EmployeesFrame
from templates.modules.RRHH.Frame_EmployeeDetail import EmployeeDetailsScrolled
from templates.modules.RRHH.Frame_Encuestas import EncuestasFrame
from templates.modules.RRHH.Frame_ExamenesMedicos import ExamenesMedicos
from templates.modules.RRHH.Frame_FichajeFilesFrames import FichajesFilesGUI
from templates.modules.Home.Frame_Home import HomeFrame
from templates.modules.Home.Frame_Notifications import NotificationsFrame
from templates.modules.Chatbot.Frame_PedidosFrame import PedidosFrame
from templates.modules.SM.Frame_SMGeneral import SMFrame
from templates.modules.Misc.Frame_SettingsFrame import SettingsFrameGUI
from templates.modules.RRHH.Frame_Vacations import VacationsFrame
from templates.modules.Assistant.Frame_vAssistantGUI import AssistantGUI
from templates.modules.SM.SubFrame_SMManagement import SMManagement
from templates.modules.Almacen.Clients import ClientsScreen
from templates.modules.Almacen.Inventory import InventoryScreen
from templates.modules.Almacen.Providers import ProvidersScreen
from templates.modules.Almacen.Supplies import SuppliesScreen

filepath_notifications = 'files/notifications.txt'
default_values_settings = {"max_chats": "40", "start_date": "19/oct./2023", "end_date": "19/oct./2023",
                           "sampling_time": 15}
chats_to_show = 40  # number of chats to show at the beginning
permissions_supper_SM = json.load(open(ventanasApp_path, encoding="utf-8"))["permissions_supper_SM"]
available_frames = {
    "Inicio": HomeFrame,
    "Chats": ChatFrame,
    "Bitacora": BitacoraEditFrame,
    "Notificaciones": NotificationsFrame,
    "Vacaciones": VacationsFrame,
    "Encuestas": EncuestasFrame,
    "Exámenes": ExamenesMedicos,
    "Fichajes": FichajesFilesGUI,
    "DB": DBFrame,
    "Empleados": EmployeesFrame,
    "Pedidos": PedidosFrame,
    "Configuración": SettingsFrameGUI,
    "SM": SMFrame,
    "Clientes": ClientsScreen,
    "Proveedores": ProvidersScreen,
    "Inventario": InventoryScreen,
    "Suministros Diarios": SuppliesScreen,
    "Ventana Asistente": AssistantGUI,
    "Examenes":  ExamenesMedicos,
    "Emp. Detalles": EmployeeDetailsScrolled,
    "Cuenta":  Login.LogOptionsFrame,
    "Procesar SM": SMManagement,
    "Movimientos": MovementsFrame,
    "Settings":  SettingsFrameGUI
}


def load_data(is_super=False, emp_id=None):
    data_sm, columns_sm = get_all_sm_entries(filter_status=False, is_supper=True, emp_id=emp_id)
    data_sm_not_supper = []
    if not is_super:
        data_sm_not_supper = [data for data in data_sm if data[7] == emp_id]
    flag, error, employees = get_sm_employees()
    flag, error, clients = get_sm_clients()
    products, columns_products = get_all_sm_products()
    data_movements = get_ins_db()
    data_dic = {
        'data_sm': data_sm,
        'columns_sm': columns_sm,
        'employees': employees,
        'clients': clients,
        'products': products,
        'columns_products': columns_products,
        'data_sm_not_supper': data_sm_not_supper,
        'data_movements': data_movements
    }
    return data_dic


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
        self.state('zoomed')
        # self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.data_dic = None
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
        
        # -----------------------Create side menu frame-----------------------
        self.navigation_frame = ttk.Frame(self)
        self.navigation_frame.grid(row=0, column=0, sticky="nswe", pady=10, padx=5)
        self.navigation_frame.columnconfigure(0, weight=1)
        self.navigation_frame.rowconfigure(2, weight=1)
        # --------------------------------title-------------------------------
        self.btnTeli = LogoFrame(self.navigation_frame)
        self.btnTeli.grid(row=0, column=0, sticky="nswe")
        theme_names = self.style_gui.theme_names()
        frame_theme = ttk.Frame(self.navigation_frame)
        frame_theme.grid(row=1, column=0, sticky="nsew")
        ttk.Label(frame_theme, text="Theme:").grid(row=1, column=0, sticky="nsew")

        self.theme_selector = ttk.Combobox(frame_theme, values=theme_names,
                                           state="readonly", width=15)
        self.theme_selector.current(theme_names.index('vapor'))
        self.theme_selector.grid(row=1, column=1, sticky="w")
        self.theme_selector.bind('<<ComboboxSelected>>',
                                 lambda event: self.style_gui.theme_use(self.theme_selector.get()))
        # --------------------widgets side menu -----------------------
        self.side_menu_frame = ttk.Frame(self.navigation_frame)
        self.side_menu_frame.grid(row=2, column=0, sticky="nsew", pady=5, padx=(0, 5))
        self.side_menu_frame.columnconfigure(0, weight=1)
        self.side_menu_frame.rowconfigure(0, weight=1)
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
        for widget in self.buttons_side_menu:
            widget.destroy()
        self.buttons_side_menu, self.names_side_menu = self._create_side_menu_widgets(self.side_menu_frame)

    def update_side_menu_windows(self):
        self.get_username_data()
        self.windows_frames = self._create_side_menu_windows()
        department = self.username_data["department_name"] if self.username_data is not None else "default"
        permissions_allowed_av = json.load(open(ventanasApp_path, encoding="utf-8"))["permissions_allowed_AV"]
        for k, v in self.permissions.items():
            if "ALMACEN" in v:
                department = "almacen"
                break
        for k, v in self.permissions.items():
            if v in permissions_allowed_av:
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
        if len(windows_names) >= 12:
            side_menu = SideMenuFrameScrollable(master, windows_names, flag, self._select_frame_by_name, width=200)
            side_menu.grid(row=0, column=0, sticky="ns", pady=10, padx=(0, 5))
        else:
            side_menu = SideMenuFrame(master, windows_names, flag, self._select_frame_by_name, width=200)
            side_menu.grid(row=0, column=0, sticky="nswe", pady=10, padx=(0, 5))
        widgets = side_menu.get_widgets()
        return widgets, windows_names

    def _destroy_side_menu_widgets(self):
        for widget in self.buttons_side_menu:
            widget.destroy()

    def update_style_department(self):
        if self.department in self.settings["gui"]:
            self.style_gui.theme_use(self.settings["gui"][self.department]["theme"])

    def _create_side_menu_windows(self):
        windows = {}
        data_dic = load_data(self.check_permissions(), self.username_data["id"])
        for i, window in enumerate(self.names_side_menu):
            window_to_create = available_frames[window]
            arguments = {
                "master":  self, "data": data_dic, "style_gui": self.style_gui, "settings": self.settings,
                "chats_to_show": self.chats_to_show, "images": None, "chats": self.chats,
                "department": self.department, "username": self.username,
                "permissions": self.permissions,
                "username_data": self.username_data,
                "data_emp": self.username_data,
                "id_emp": self.username_data["id"]
            }
            windows[window] = window_to_create(**arguments)
            print(f"{window} frame created")
        return windows

    def check_permissions(self):
        for item in self.permissions.values():
            if item in permissions_supper_SM:
                return True
        return False


class LogoFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        img_logo = get_image_side_menu("logo")
        width = 200
        height = 100
        width_img = 100
        height_img = 100
        ratio = 1
        canva = tk.Canvas(self, width=width, height=height)
        canva.grid(row=0, column=0, sticky="nswe", padx=10)
        canva.create_image(width_img / ratio, height_img / ratio, anchor='s', image=img_logo)
        canva.image = img_logo


class SideMenuFrame(ttk.Frame):
    def __init__(self, master, windows_names, is_allowed, command, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.widgets = []
        if is_allowed or windows_names is not None:
            for i, window in enumerate(windows_names):
                self.widgets.append(
                    create_button_side_menu(
                        self, i, 0,
                        text=window,
                        image=get_image_side_menu(window),
                        command=lambda x=window: command(x),
                        columnspan=1, padx=(1, 15))
                )

    def get_widgets(self):
        return self.widgets


class SideMenuFrameScrollable(ScrolledFrame):
    def __init__(self, master, windows_names, is_allowed, command, *args, **kwargs):
        super().__init__(master, autohide=True, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        indexes = [i for i in range(len(windows_names))]
        self.rowconfigure(indexes, weight=1)
        self.widgets = []
        if is_allowed or windows_names is not None:
            for i, window in enumerate(windows_names):
                self.widgets.append(
                    create_button_side_menu(
                        self, i, 0,
                        text=window,
                        image=get_image_side_menu(window),
                        command=lambda x=window: command(x),
                        columnspan=1, padx=(1, 15))
                )

    def get_widgets(self):
        return self.widgets
