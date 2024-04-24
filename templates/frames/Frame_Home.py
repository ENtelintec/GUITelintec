# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 23/abr./2024  at 15:34 $'

import asyncio

import python_weather
from python_weather.forecast import Forecast, DailyForecast, HourlyForecast
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.Funtions_Utils import create_label
from templates.frames.Frame_EmployeeDetail import EmployeeDetails
from templates.frames.SubFrame_SMDashboard import SMDashboard
from templates.screens.Home import HomeScreen

avaliable_dashboards = {
    "sm": [SMDashboard],
    "almacen": [HomeScreen],
    "rrhh": [EmployeeDetails],
    "administracion": [SMDashboard]
}
days_of_week = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
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
        for index, dashboard in enumerate(self.dashboard_key):
            if dashboard not in avaliable_dashboards.keys():
                continue
            for window in avaliable_dashboards[dashboard]:
                frame = window(self, **kwargs)
                frame.grid(row=2+index, column=0, sticky="we", padx=(0, 10))
                indexes.append(2+index)
        print(indexes)
        self.rowconfigure(indexes, weight=1)


class WeatherFrame(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure((0, 1), weight=1)
        self.weather = None
        self.daily_forecasts = None
        self.hourly_forecasts = None
        self.city = "Monterrey"
        frame_weather = ttk.Frame(self)
        frame_weather.grid(row=1, column=0, sticky="nsew")
        asyncio.run(self.create_widgets(frame_weather))

    async def getweather(self):
        # declare the client. the measuring unit used defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(unit=python_weather.METRIC) as client:
            # fetch a weather forecast from a city
            self.weather = await client.get(self.city)
            # get the weather forecast for a few days
            self.hourly_forecasts = []
            self.daily_forecasts = []
            for daily in self.weather.daily_forecasts:
                self.daily_forecasts.append(daily)
                # hourly forecasts
                for hourly in daily.hourly_forecasts:
                    self.hourly_forecasts.append(hourly)

    async def create_widgets(self, master):
        await self.getweather()
        # -----------------------Title-----------------
        create_label(self, 0, 0, text=f"Clima en: {self.weather.location}", font=("Helvetica", 14, "bold"), columnspan=2)
        # -----------------------Frames---------------------------
        create_label(master, 1, 0, text=f"Hoy: ", font=("Helvetica", 10, "bold"))
        create_label(master, 1, 1, text=f"{self.weather.temperature} ", font=("Helvetica", 10, "bold"))
        indexes = []
        for day, daily in enumerate(self.daily_forecasts):
            create_label(master, 2, day*2, text=f"{days_of_week[daily.date.weekday()]}: ", font=("Helvetica", 10, "bold"))
            create_label(master, 2, day*2 + 1, text=f"{daily.temperature} ", font=("Helvetica", 10, "bold"))
            indexes.append(day)
        master.columnconfigure(indexes, weight=1)
