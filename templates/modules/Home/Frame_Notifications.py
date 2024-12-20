# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 26/abr./2024  at 16:42 $"

import ttkbootstrap as ttk

from static.constants import filepath_settings
from templates.misc.Functions_Files import open_file_settings


class NotificationsFrame(ttk.Frame):
    def __init__(self, master, data_emp=None, **kw):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.notifications_frames = []
        flag, self.settings = open_file_settings(filepath_settings)
        self.data_emp = data_emp
        self.permissions = self.data_emp["permissions"]
        apps = (
            kw["data"]["data_notifications"]["apps"]
            if "data_notifications" in kw["data"]
            else []
        )
        for value in self.permissions.values():
            apps.append(value.split(".")[-1].lower())
        self.create_widgets(apps, kw)

    def create_widgets(self, apps, kw):
        index = 0
        kw["settings"] = self.settings
        kw["data_emp"] = self.data_emp
        created_frames_names = []
        for frame in apps:
            from static.FramesClasses import frames_notifications_avaliable

            if (
                frame in frames_notifications_avaliable.keys()
                and frame not in created_frames_names
            ):
                frame_created = frames_notifications_avaliable[frame](self, **kw)
                frame_created.grid(row=index, column=0, sticky="nsew", padx=(0, 10))
                index += 1
                created_frames_names.append(frame)
                self.notifications_frames.append(frame_created)

    def update_procedure(self, **events):
        for frame in self.notifications_frames:
            frame.update_procedure(**events)
