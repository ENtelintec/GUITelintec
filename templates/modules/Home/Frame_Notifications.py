# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 26/abr./2024  at 16:42 $'

import ttkbootstrap as ttk

from static.extensions import filepath_settings
from templates.Functions_Files import open_file_settings
from templates.modules.Home.SubFrame_GeneralNoti import NotificationsUser
from templates.modules.Home.SubFrame_NotificationsChatbot import NotificationsChatbot

frames_notifications_avaliable = {
    "chatbot": NotificationsChatbot,
    "administracion": NotificationsUser
}


class NotificationsFrame(ttk.Frame):
    def __init__(self, master, data_emp=None, **kw):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        flag, self.settings = open_file_settings(filepath_settings)
        self.data_emp = data_emp
        self.permissions = self.data_emp["permissions"]
        apps = []
        for value in self.permissions.values():
            print(value)
            apps.append(value.split(".")[-1].lower())
        self.create_widgets(apps, kw)

    def create_widgets(self, apps, kw):
        index = 0
        kw["settings"] = self.settings
        kw["data_emp"] = self.data_emp
        for frame in apps:
            if frame in frames_notifications_avaliable.keys():
                frame_created = frames_notifications_avaliable[frame](self, **kw)
                frame_created.grid(row=index, column=0, sticky="nsew", padx=(0, 10))
                index += 1                
