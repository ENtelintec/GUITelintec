# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 23/abr./2024  at 15:34 $'

from ttkbootstrap.scrolled import ScrolledFrame

from templates.Funtions_Utils import create_label
from templates.modules.RRHH.Frame_EmployeeDetail import EmployeeDetails
from templates.modules.Home.Frame_Wheather import WeatherFrame
from templates.modules.SM.SubFrame_SMDashboard import SMDashboard
from templates.screens.Home import HomeScreen

avaliable_dashboards = {
    "sm": [SMDashboard],
    "almacen": [HomeScreen],
    "rrhh": [EmployeeDetails],
    "administracion": [SMDashboard]
}


class HomeFrame(ScrolledFrame):
    def __init__(self, master=None, data=None, data_emp=None, *args, **kwargs):
        super().__init__(master, autohide=True)
        self.columnconfigure(0, weight=1)
        self.master = master
        self.data = data if data is not None else None
        self.data_emp = data_emp if data_emp is not None else None
        kwargs["data"] = self.data
        kwargs["data_emp"] = self.data_emp
        # -----------------Title-------------------------------
        create_label(self, 0, 0, text="Inicio", font=("Helvetica", 30, "bold"), columnspan=2)
        frame_wather = WeatherFrame(self)
        frame_wather.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        # -----------------Check permissions--------------------------------
        self.permissions = data_emp["permissions"]
        self.dashboard_key = []
        for permission in self.permissions.values():
            txt = permission.split(".")
            self.dashboard_key.append(txt[-1].lower())
        
        indexes = []
        created_windows = []
        for index, dashboard in enumerate(self.dashboard_key):
            if dashboard not in avaliable_dashboards.keys():
                continue
            for window in avaliable_dashboards[dashboard]:
                if window in created_windows:
                    continue
                created_windows.append(window)
                frame = window(self, **kwargs)
                frame.grid(row=2+index, column=0, sticky="we", padx=(0, 10))
                indexes.append(2+index)
        self.rowconfigure(indexes, weight=1)
