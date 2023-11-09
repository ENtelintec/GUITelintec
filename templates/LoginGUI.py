# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 08/nov./2023  at 15:22 $'

import hashlib

import requests
import ttkbootstrap as ttk
from dotenv import dotenv_values

secrets = dotenv_values("../.env")
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
    if response.status_code != 200:
        out = False
    else:
        out = response.json()['verified']
    print(f"Verified: {out}")
    return out


class LoginGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # -------------------create title-----------------
        self.label_title = ttk.Label(self, text='Telintec Software')
        self.label_title.grid(row=0, column=0, columnspan=2)
        # -------------------create entry for user and pass-----------------
        self.label_user = ttk.Label(self, text='User:')
        self.label_user.grid(row=1, column=0)
        self.label_pass = ttk.Label(self, text='Password: ')
        self.label_pass.grid(row=2, column=0)
        self.user_entry = ttk.Entry(self)
        self.user_entry.grid(row=1, column=1)
        self.pass_entry = ttk.Entry(self, show='*')
        self.pass_entry.grid(row=2, column=1)
        # -------------------create button for login-----------------
        self.button = ttk.Button(self, text='Login', command=self.button_login_click)
        self.button.grid(row=3, column=0)
        # -------------------create message----------------
        self.message = ttk.Label(self, text='')
        self.message.grid(row=3, column=1)

    def button_login_click(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        # hash password
        pass_key = hashlib.md5(password.encode()).hexdigest()
        # call API
        verified = call_authApi(username, pass_key, url=url_api)
        if verified:
            self.message['text'] = 'Welcome!'
            self.message['foreground'] = 'green'
            self.master.destroy()
            self.master.quit()
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
