# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 23/abr./2024  at 15:34 $'

from ttkbootstrap.scrolled import ScrolledFrame
from templates.Functions_GUI_Utils import create_label
from templates.modules.Home.Frame_Notifications import NotificationsFrame


class HomeFrame(ScrolledFrame):
    def __init__(self, master=None, data_emp=None, *args, **kwargs):
        super().__init__(master, autohide=True)
        self.columnconfigure(0, weight=1)
        self.master = master
        self.data_emp = data_emp if data_emp is not None else None
        kwargs["data_emp"] = self.data_emp
        # -----------------Title-------------------------------
        create_label(self, 0, 0, text="Inicio", font=("Helvetica", 30, "bold"), columnspan=2)
        # frame_wather = WeatherFrame(self)
        # frame_wather.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        frame_notifications = NotificationsFrame(self, **kwargs)
        frame_notifications.grid(row=2, column=0, sticky="we", padx=(0, 10))
        # -----------------Check permissions--------------------------------
        self.permissions = data_emp["permissions"]
        self.dashboard_key = []
        for permission in self.permissions.values():
            txt = permission.split(".")
            self.dashboard_key.append(txt[-1].lower())
        index_offset = 3
        indexes = [index_offset]
        created_windows = []
        for index, dashboard in enumerate(self.dashboard_key):
            from static.FramesClasses import avaliable_dashboards
            if dashboard not in avaliable_dashboards.keys():
                continue
            for window in avaliable_dashboards[dashboard]:
                if window in created_windows:
                    continue
                created_windows.append(window)
                frame = window(self, **kwargs)
                frame.grid(row=index_offset+index, column=0, sticky="we", padx=(0, 10))
                indexes.append(index_offset+index)
        self.rowconfigure(indexes, weight=1)
