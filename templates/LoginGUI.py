# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 08/nov./2023  at 15:22 $'

import hashlib

import requests
import ttkbootstrap as ttk
from dotenv import dotenv_values

secrets = dotenv_values(".env")
url_api = "http://127.0.0.1:5000/AuthAPI/api/v1/auth/loginUP"


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
        self.label_title.grid(row=0, column=0, columnspan=2,  sticky="n",  padx=10, pady=20)
        # -------------------create entry for user and pass-----------------
        self.label_user = ttk.Label(self, text='User:',
                                    font=('Helvetica', 14))
        self.label_user.grid(row=1, column=0, sticky="nsew",  padx=10, pady=5)
        self.label_pass = ttk.Label(self, text='Password: ',
                                    font=('Helvetica', 14))
        self.label_pass.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.user_entry = ttk.Entry(self)
        self.user_entry.grid(row=1, column=1,  sticky="nsew",  padx=10, pady=5)
        self.pass_entry = ttk.Entry(self, show='*')
        self.pass_entry.grid(row=2, column=1, sticky="nsew",  padx=10, pady=5)
        # -------------------create button for login-----------------
        self.button = ttk.Button(self, text='Login', command=self.button_login_click)
        self.button.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        # -------------------create message----------------
        self.message = ttk.Label(self, text='')
        self.message.grid(row=4, column=0)

    def button_login_click(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        # hash password
        pass_key = hashlib.md5(password.encode()).hexdigest()
        # call API
        verified, permissions = call_authApi(username, pass_key, url=url_api)
        if verified or permissions is not None:
            self.message['text'] = 'Welcome!'
            self.message['foreground'] = 'green'
            self.master.permissions = permissions
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


if __name__ == '__main__':
    app = ttk.Window()
    main = LoginGUI(app)
    main.pack()
    app.mainloop()
