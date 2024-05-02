# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 26/abr./2024  at 16:42 $'

from ttkbootstrap.scrolled import ScrolledFrame

from templates.modules.Home.SubFrame_NotSM import NotificationsUser
from templates.modules.Home.SubFrame_NotificationsChatbot import NotificationsChatbot

frames_notifications_avaliable = {
    "chatbot": NotificationsChatbot,
    "administracion": NotificationsUser
}


class Notifications(ScrolledFrame):
    def __init__(self, master, settings=None, data_emp=None, **kw):
        super().__init__(master, autohide=True)
        self.columnconfigure(0, weight=1)
        self.settings = settings
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
                frame_created.grid(row=index, column=0, sticky="nsew")
                index += 1                
