# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 08/nov./2023  at 15:22 $'

import hashlib

import requests
import ttkbootstrap as ttk
from dotenv import dotenv_values
from ttkbootstrap import Style

import tkinter as tk

secrets = dotenv_values(".env")
url_api = "https://ec2-3-144-117-149.us-east-2.compute.amazonaws.com/AuthAPI/api/v1/auth/loginUP"


def call_authApi(user, pass_key, url=None):
    """
    Call API to authenticate user.
    :param url:
    :param user:
    :param pass_key:
    :return:
    """
    url = url if url is not None else secrets.get("API_AUTH_UP_URL")
    data = {"username": user, "password": pass_key}
    response = requests.post(url, json=data)
    permissions = None
    if response.status_code != 200:
        out = False
    else:
        out = response.json()['verified']
        permissions = response.json()['permissions']
    # print(f"Verified: {out} with {permissions}")
    return out, permissions


class LoginGUI(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(1, weight=1)
        
        # -------------------create title-----------------
        self.label_title = ttk.Label(self, text='Telintec Software',
                                     font=('Helvetica', 18))
        self.label_title.grid(row=0, column=0, columnspan=2, sticky="n", padx=10, pady=20)
        # -------------------create entry for user and pass-----------------
        self.label_user = ttk.Label(self, text='User:',
                                    font=('Helvetica', 14))
        self.label_user.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.label_pass = ttk.Label(self, text='Password: ',
                                    font=('Helvetica', 14))
        self.label_pass.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.user_entry = ttk.Entry(self)
        self.user_entry.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        self.pass_entry = ttk.Entry(self, show='*')
        self.pass_entry.grid(row=2, column=1, sticky="nsew", padx=10, pady=5)
        # -------------------create button for login-----------------
        self.button = ttk.Button(self, text='Login', command=self.button_login_click)
        self.button.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        # -------------------create message----------------
        self.message = ttk.Label(self, text='')
        self.message.grid(row=3, column=1)

    def button_login_click(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        # hash password
        pass_key = hashlib.md5(password.encode()).hexdigest()
        # call API
        verified, permissions = call_authApi(username, pass_key, url=url_api)
        if verified or permissions is not None:
            self.message['text'] = f'Welcome! **{username}**'
            self.message['foreground'] = 'white'
            self.message['font'] = ('Helvetica', 16)
            self.master.permissions = permissions
            self.master.username = username
            self.master.get_username_data()
            self.master.update_side_menu()
            self.master.update_side_menu_windows()
            # print(f"Permissions: {self.master.permissions}")
            self.destroy()
            # self.quit()
        else:
            self.message['text'] = 'Invalid user or password'
            self.message['foreground'] = 'red'
            self.pass_entry.delete(0, 'end')
            self.user_entry.delete(0, 'end')
            self.user_entry.focus()
            self.pass_entry.focus()


class LogOptionsFrame(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(1, weight=1)
        self.master = master
        #  -------------------create title-----------------
        self.label_title = ttk.Label(self, text=f'Usuario actual: {self.master.username}',
                                     font=('Helvetica', 18))
        self.label_title.grid(row=0, column=0, columnspan=2, sticky="n", padx=10, pady=20)

        # -------------------create message----------------
        if self.master.username_data is not None:
            txt = f"Usuario: {self.master.username}"
            txt += f"\nPermisos: {self.master.permissions}"
            if self.master.username_data['exp'] is not None:
                txt += f"\nToken expira en: {self.master.username_data['exp']}"
                txt += f"\nCreado en: {self.master.username_data['timestamp']}"
            txt += f"\nEmpleado: {self.master.username_data['name']} {self.master.username_data['lastname']}"
            txt += f"\nDepartamento: {self.master.username_data['department_id']}. {self.master.username_data['department_name']}"
        else:
            txt = "No se pudo obtener los datos del usuario"
        self.message = ttk.Label(self, text=txt, font=('Helvetica', 14), justify=tk.LEFT)
        self.message.grid(row=1, column=1, pady=10, padx=5, columnspan=2)
        # -------------------create button for logout-----------------
        style = Style()
        style.configure('custom.TButton', font=('Helvetica', 16))
        self.button = ttk.Button(self, text='Logout', command=self.button_logout_click,
                                 style='custom.TButton')
        self.button.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)

    def button_logout_click(self):
        self.master.logOut()
