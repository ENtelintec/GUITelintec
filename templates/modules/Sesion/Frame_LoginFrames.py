# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/nov./2023  at 15:22 $"

import hashlib
import json
import os

import requests
import ttkbootstrap as ttk
from ttkbootstrap import Style
import customtkinter as ctk
import tkinter as tk
from PIL import Image

from static.constants import ventanasApp_path, filepath_settings, secrets
from templates.Functions_GUI_Utils import compare_permissions_windows
from templates.Functions_Utils import unpack_token
from templates.LoadData import DataLoader
from templates.controllers.employees.us_controller import get_username_data

carpeta_principal = "./img"


def call_authApi(user, pass_key, url=None):
    """
    Call API to authenticate user.
    :param url:
    :param user:
    :param pass_key:
    :return:
    """
    settings = json.load(open(filepath_settings))
    url = url if url is not None else settings["url_auth_api"]
    data = {"username": user, "password": pass_key}
    token = secrets["KEY_WEBAPP"]
    headers = {
        "Authorization": hashlib.md5(token.encode()).hexdigest(),
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        out = False
        permissions_out = {}
        print(f"Error: {response.status_code}, response: {response}")
    else:
        out = response.json()["verified"]
        data_token = unpack_token(response.json()["token"])
        permissions = data_token["permissions"]
        print(data_token)
        if isinstance(permissions, list):
            permissions_out = {}
            for index, item in enumerate(permissions):
                permissions_out[index] = item["role"]
        else:
            permissions_out = permissions
    return out, permissions_out


def image_load():
    """
    Load image from file
    :return:
    """
    image_path = carpeta_principal
    return (
        ctk.CTkImage(
            Image.open(os.path.join(image_path, "LogoTelintec.png")), size=(90, 90)
        ),
        ctk.CTkImage(
            light_image=Image.open(os.path.join(image_path, "DB.png")), size=(30, 30)
        ),
        ctk.CTkImage(
            dark_image=Image.open(os.path.join(image_path, "iso_claro.png")),
            size=(350, 180),
        ),
    )


class LoginGUI(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.columnconfigure(1, weight=1)
        self.style_gui = kwargs.get("style_gui")
        self.images = {}
        self.permissions = None
        self.username_data = None
        (self.logo_image, self.employees_img, self.iso_claro) = image_load()
        self.frame_login = ttk.Frame(self)
        self.frame_login.place(
            relx=0.5, rely=0.5, anchor="center"
        )  # Centrar el nuevo frame
        self._svar_info_login = ttk.StringVar(value="")
        self.get_username_data = kwargs.get("get_username_data_callback")
        self.update_side_menu_data = kwargs.get("update_side_menu_data_callback")
        self.update_side_menu = kwargs.get("update_side_menu_callback")
        # ----------------Agregar imagen -----------------=
        # noinspection PyTypeChecker
        imagen = ctk.CTkButton(
            self.frame_login,
            image=self.iso_claro,
            fg_color="transparent",
            text=None,
            hover=None,
        )
        imagen.grid(row=0, column=0, columnspan=2)
        self.label_init = ttk.Label(
            self.frame_login, text="Bienvenido a Telintec Software"
        )
        self.label_init.grid(row=1, column=0, columnspan=2, sticky="n")
        # -------------------create entry for user and pass-----------------
        self.label_user = ttk.Label(
            self.frame_login, text="User", font=("Helvetica", 18), justify="center"
        )
        self.label_user.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.user_entry = ttk.Entry(self.frame_login, width=50)
        self.user_entry.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self.label_pass = ttk.Label(
            self.frame_login,
            text="Password ",
            font=("Helvetica", 18),
            justify="center",
            width=len("Password: "),
        )
        self.label_pass.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)
        self.pass_entry = ttk.Entry(
            self.frame_login,
            show="*",
            width=50,
        )
        self.pass_entry.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        self.pass_entry.bind("<Return>", lambda event: self.button_login_click())
        # -------------------create button for login-----------------
        self.button = ttk.Button(
            self.frame_login, text="Login", command=self.button_login_click, width=50
        )

        self.button.grid(row=6, column=0, sticky="nsew", padx=50, pady=30)
        # -------------------create message----------------
        self.message = ttk.Label(
            self, text="", font=("Helvetica", 36), textvariable=self._svar_info_login
        )
        self.message.grid(row=7, column=1)
        self.message["foreground"] = self.style_gui.colors.get("secondary")

    def button_login_click(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        # hash password
        pass_key = hashlib.md5(password.encode()).hexdigest()
        # call API
        verified, permissions = call_authApi(username, pass_key)
        if verified or len(permissions) > 0:
            self.permissions = permissions
            self.username_data = get_username_data(username)
            self.message["text"] = f"Welcome! **{username}**"
            self.master.permissions = permissions
            self.master.username = username
            self.get_username_data(self.username_data, self.permissions)
            flag, windows_names = compare_permissions_windows(
                list(self.permissions.values())
            )
            windows_names = windows_names if windows_names is not None else ["Cuenta"]
            self.update_side_menu(windows_names)
            data_loader = DataLoader(
                self.check_permissions(),
                self.username_data["id"],
                windows_names,
                permissions,
                self,
            )
            # data_dic = load_data(self.check_permissions(), self.username_data["id"], self.names_side_menu, self.permissions)
            data_loader.daemon = True
            data_loader.start()
        else:
            print("Invalid user or password")
            self._svar_info_login.set("Invalid user or password")
            self.message["foreground"] = "red"
            self.pass_entry.delete(0, "end")
            self.user_entry.delete(0, "end")
            self.user_entry.focus()
            self.pass_entry.focus()

    def update_info_loading(self, loaded, total):
        percentage_loaded = (loaded / total) * 100
        self._svar_info_login.set(f"Cargando {percentage_loaded:.2f}%")

    def close_login_frame(self, data_dic):
        self.update_side_menu_data(data_dic)
        self.destroy()
        # self.quit()

    def check_permissions(self):
        permissions_supper_sm = json.load(open(ventanasApp_path, encoding="utf-8"))[
            "permissions_supper_SM"
        ]
        for item in self.permissions.values():
            if item in permissions_supper_sm:
                return True
        return False


class LogOptionsFrame(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.columnconfigure(1, weight=1)
        self.username = kwargs.get("username")
        self.username_data = kwargs.get("username_data")
        self.permissions = kwargs.get("permissions")
        self.logOut = kwargs.get("log_out_callback")
        #  -------------------create title-----------------
        self.label_title = ttk.Label(
            self, text=f"Usuario actual: {self.username}", font=("Helvetica", 18)
        )
        self.label_title.grid(
            row=0, column=0, columnspan=2, sticky="n", padx=10, pady=20
        )

        # -------------------create message----------------
        if self.username_data is not None:
            txt = f"Usuario: {self.username}"
            txt += "\nPermisos:"
            for permission in self.permissions.values():
                txt += f"\n{permission}"
            if self.username_data["exp"] is not None:
                txt += f"\nToken expira en: {self.username_data['exp']}"
                txt += f"\nCreado en: {self.username_data['timestamp']}"
            txt += f"\nEmpleado: {self.username_data['name'].upper()} {self.username_data['lastname'].upper()}"
            txt += f"\nDepartamento: {self.username_data['department_id']}. {self.username_data['department_name']}"
        else:
            txt = "No se pudo obtener los datos del usuario"
        self.message = ttk.Label(
            self, text=txt, font=("Helvetica", 14), justify=tk.LEFT
        )
        self.message.grid(row=1, column=1, pady=10, padx=5, columnspan=2)
        # -------------------create button for logout-----------------
        style = Style()
        style.configure("custom.TButton", font=("Helvetica", 16))
        self.button = ttk.Button(
            self,
            text="Logout",
            command=self.button_logout_click,
            style="custom.TButton",
        )
        self.button.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)

    def button_logout_click(self):
        self.logOut()
